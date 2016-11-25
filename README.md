Python TekDPO2000

Class for controlling and obtaining data from Tektronix DPO2k range
of oscilloscopes.

- [INSTALLATION](#installation)
- [DESCRIPTION](#description)

# INSTALLATION

===================
Requirements
===================

Before installing, make sure that you have installed all of the prerequiste dependancies:

[Python](https://www.python.org/) 				- (Tested on 2.6 and 2.7)
[PyVISA](http://pyvisa.readthedocs.io/en/stable/)		- For handling the connection to the oscilloscope	
[PyVISA-py](https://pyvisa-py.readthedocs.io/en/latest/)	- Pure Python backend for PyVISA					

# DESCRIPTION

A python class for controlling the DPO2k series of scopes that we have in the
lab. Uses pyvisa to establish a connection with the oscilloscope, which can then
be computer controlled. For a full list of commands for the scope, the [programmers guide is available](http://www.tek.com/oscilloscope/mso2000-dpo2000-manual/mso2000b-dpo2000b-mso2000-and-dpo2000-series). 

Also contains an example script showing how it can be used. 


