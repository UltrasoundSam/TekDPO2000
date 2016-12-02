#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  TekScope.py
#  
#  Copyright 2016 Samuel Hill <samuel.hill@warwick.ac.uk>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
import visa
import time
import numpy as np

class QueryException(Exception):
	'''
	Custom exception for showing that query to scope formatted
	incorrectly
	'''
	pass

class DPOScope(object):
    '''
    Control class for Tektronix DPO2014 oscilloscopes, allowing for
    computer control of the scope (setting parameters, etc) and for 
    reading data from scope.
    '''
    def __init__(self, scopeIdent=None):
        '''
        Initiates connections with scope, given a scope identification
        string, such as "USB0::1689::883::C000489::0::INSTR" obtained
        from visa.ResourceManager.list_resources().
        
        If no scopeIdent is given, it just takes the first instrument
        in the resources list
        '''
        rm = visa.ResourceManager('@py')
        if not scopeIdent:
            scopeIdent = rm.list_resources()[0]
        
        self.visa = rm.open_resource(scopeIdent)
        self.visa.read_termination = '\n'
        
        # Get Make and model
        make, model = self.get_param('*IDN?').split(',')[:2]
        self.make = str(make)
        self.model = str(model)
        
        # Set scope running
        self.set_param('ACQuire:STAte RUN')
    
    def __repr__(self):
        desc = ('This is a {0} {1} oscilloscope'.format(self.make, self.model))
        return desc
    
    def close(self):
        '''
        Closes object and shuts down connection to scope
        '''
        self.visa.close()
    
    def open(self):
        '''
        Opens connection to scope
        '''
        try:
            self.visa.open()
        except Exception:
            print('Scope already open!')
    
    def set_param(self, message):
        '''
        Sends message to scope to change parameter
        '''
        try:
            self.visa.write(message)
        except AttributeError:
            print('Can only send strings as a command')
    
    def get_param(self, message):
        '''
        Queries scope for parameter value and returns it as a string.
        For some reason, scope can only handle one read request before
        it needs to be closed and then opened - quirk of DPO2000 series,
        I think
        '''
        try:
            # Check to see if valid query request
            if not message.endswith('?'):
                raise QueryException('Query must finish with ?')
            
            # Send query, and reset scope
            ans = self.visa.query(message)
            self.visa.close()
            self.visa.open()
            return ans
        except AttributeError:
            print('Can only send strings as a command')
    
    def get_data(self, channel):
        '''
        Gets data from oscilloscope for a given channel (CH1, CH2, etc)
        and returns it as a (time, data) tuple.
        '''
        # Annoyingly, cannot get data in average mode (see self.average)
        if self.get_param('ACQuire:MODe?') == 'AVE':
            self.set_param('ACQuire:MODe SAMple')
            time.sleep(1.)
        
        self.set_param("SELect:{0} 1".format(channel))
        
        # Select Data source and define format (RIBinary - big endian signed 'short' type)
        self.set_param('DATa:SOUrce {0};:ENCdg RIBinary'.format(channel))
        self.set_param('WFMOutpre:BYT_Nr 2')
        
        # Find out length of signal
        rcdlen = int(self.get_param('WFMOutpre:RECOrdlength?'))
        
        # Requesting all the data out
        self.set_param('DATa:STARt 1')
        self.set_param('DATa:STOP {0}'.format(rcdlen))
        self.set_param('DATa:WIDth 2')
        
        # Process all metadata information
        self.info = self.preamble()
        
        # Now getting data from scope (C&O to avoid timeout errors)
        data = self.visa.query_binary_values('CURVe?', container=np.array, is_big_endian=True, datatype='h')
        self.close()
        self.open()
        
        # Reconstructing time information
        t = self.info['XOffset'] + np.arange(0, self.info['Record_Len'])*self.info['XIncr']
        return (t, data * self.info['YMult'])
    
    def preamble(self):
        '''
        Processes all scope metainformation/preamble so all setting values
        are known.
        '''
        # Read in the preamble and turn each value into a list
        Pre = self.get_param('WFMOutpre?').split(';')
        
        # Headers for each value
        hdr = ['Byte_Nr', 'Bit_Nr', 'Encoding', 'Bin_Fmt', 'Byte_Ord',
                'Params', 'Points_Requested', 'Point_Fmt', 'XUnit', 
                'XIncr', 'XOffset', 'CHoff', 'YUnit', 'YMult', 
                'YOffset', 'YZero', 'Composition', 'Record_Len', 'FilterFreq']
        
        metainfo = dict(zip(hdr, Pre))
        
        # Some values are better expressed as floats or integers
        intvals = ['Byte_Nr', 'Bit_Nr', 'Record_Len', 'Points_Requested']
        floatvals = ['YOffset', 'YZero', 'YMult', 'XIncr', 'XOffset']
        
        for key in intvals:
            metainfo[key] = int(metainfo[key])
        
        for key in floatvals:
            metainfo[key] = float(metainfo[key])
        
        return metainfo
    
    def average(self, channel, averages=4):
        '''
        Annoyingly, it doesn't seem like we can get data from the scope
        if in averaging mode - so have to implement it ourselves. Use
        read data averages number of times to get the data, and then
        average it. Consequency, it is very slow!
        
        For more info on this, see
        https://forum.tek.com/viewtopic.php?t=136577#p274677
        
        Returns (time, data) tuple
        '''
        # Round averages up to next power of two
        averages = int(2**np.ceil(np.log2(averages)))
        
        # Use self.get_data once to get first data
        t, buff = self.get_data(channel)
        
        # Create numpy array with right shape to hold all data
        values = np.zeros([averages, len(t)])
        values[0] = buff
        
        # Now loop and repeat measurements (not using self.get_data to minimise # queries
        for i in xrange(averages-1):
            buff = self.visa.query_binary_values('CURVe?', container=np.array, is_big_endian=True, datatype='h')
            values[i+1] = buff * self.info['YMult']
            self.close()
            self.open()
        
        return (t, values.mean(axis=0))
    
    def reset(self):
        '''
        Resets scope to default settings
        '''
        self.set_param('*RST')

