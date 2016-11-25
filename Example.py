#!/usr/bin/env python
# -*- coding: utf-8 -*-
from TekScope import DPOScope
import pylab as plt

# Connecting scope - no arguments needed if only scope connected
scope = DPOScope()

# Showing scope indentification number
print(scope.get_param('*IDN?'))

# Change some parameters
scope.set_param('HORizontal:SCAle 4e-6')
scope.set_param('HORizontal:DELay:TIMe 16e-6')
scope.set_param("SELect:CH1 0")
scope.set_param("SELect:CH3 0")
scope.set_param("SELect:CH4 0")
scope.set_param("SELect:CH2 1")
scope.set_param("CH2:PROBE:GAIN 1")
scope.set_param("CH2:SCAle 2")
scope.set_param("CH2:POSition 0")
scope.set_param('TRIGger:A:Type EDGE')
scope.set_param('TRIGger:A:EDGE:SOUrce CH4')
scope.set_param('TRIGger:A:MODe NORMal')
scope.set_param('TRIGger:A:LEVel 2')

# Get data (averaged 8 times)
time1, ave = scope.average('CH2', 8)

# Get 'raw' data
time2, data = scope.get_data('CH2')

# Plot results
plt.plot(1.e6*time2, data, 1.e6*time1, ave)
plt.xlabel('Time ($\mu$s)')
plt.ylabel('Amplitude (V)')
plt.show()
