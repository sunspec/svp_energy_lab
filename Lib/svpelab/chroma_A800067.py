"""
Copyright (c) 2017, Sandia National Labs and SunSpec Alliance
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

Neither the names of the Sandia National Labs and SunSpec Alliance nor the names of its
contributors may be used to endorse or promote products derived from
this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Questions can be directed to support@sunspec.org
"""

import os
import sys
import math
import time

TERMINATOR = '\n'
BASE_RESISTANCE = 16133.3
BASE_LC_CURRENT = .013633
FNOM = 50
VNOM = 220

def ChromaRLCError(Exception):
    pass

class ChromaRLC(object):
    """
    Template for RLC load implementations. This class can be used as a base class or
    independent RLC load classes can be created containing the methods contained in this class.
    """

    def __init__(self, visa_device=None, visa_path=None, params=None, volts = 220, freq = 50):
        self.rm = None      # Resource Manager for VISA
        self.conn = None    # Connection to instrument for VISA-GPIB
        self.visa_device = visa_device
        self.visa_path = visa_path
        self.data_query = ''
        self.volts = volts
        self.freq = freq

        self.open()  # open communications, not the relay

        # initialize the load to a 0 state.
        self._write ('FUNCtion:S1 OFF')
        self._write ('FUNCtion:SLOAD OFF')
        phase = 1
        for phase in range(1, 4):
            self.resistance (phase, 0)
            self.inductance (phase, 0)
            self.capacitance (phase, 0)

            # Turn off all external loads.
            self.cmd('PHASE%s:RLOADE OFF' % (phase))
            self.cmd('PHASE%s:LLOADE OFF' % (phase))
            self.cmd('PHASE%s:CLOADE OFF' % (phase))

    def open(self):

        try:
            import visa
            self.rm = visa.ResourceManager(self.visa_path)
            self.conn = self.rm.open_resource(self.visa_device)
            self.conn.write_termination = TERMINATOR

        except Exception as e:
            raise ChromaRLCError('Cannot open VISA connection to %s\n\t%s' % (self.visa_device, str(e)))

    def close(self):
        try:
            if self.rm is not None:
                if self.conn is not None:
                    self.conn.close()
                self.rm.close()
                time.sleep(1)
        except Exception as e:
            raise ChromaRLCError(str(e))

    def info(self):
        return self._query ('*IDN?')

    def cmd(self, cmd_str):

        try:
            cmd_str = cmd_str.strip()
            self._write(cmd_str)
            resp = self._query('SYSTem:ERRor?') #\r
            if len(resp) > 0:
                if resp[0] != '0':
                    raise ChromaRLCError(resp + ' ' + cmd_str)
        except Exception as e:
            raise ChromaRLCError(str(e))

    def _query(self, cmd_str):
        """
        Performs an SCPI Querry
        :param cmd_str:
        :return:
        """
        try:
            cmd_str.strip()
            if self.conn is None:
                raise ChromaRLCError('GPIB connection not open')
            return self.conn.query(cmd_str)

        except Exception as e:
            raise ChromaRLCError(str(e))

    def _write(self, cmd_str):
        """
        Performs an SCPI Querry
        :param cmd_str:
        :return:
        """
        try:
            if self.conn is None:
                raise ChromaRLCError('GPIB connection not open')
            return self.conn.write(cmd_str)
        except Exception as e:
            raise ChromaRLCError(str(e))

    def voltset (self,v):
        self.volts = v

    def freqset (self,f):
        self.freq = f

    def resistance(self, ph=None, r=None):
        b = 0.0
        if r is not None:
            # Calculate resistance.
            if r == 0:
                self._write ('PHASE%s:RLOAD 000' % (ph))
            else:
                b = (1 / float(r))
                b = BASE_RESISTANCE*b
                b = int(round(b,0))
                b = format(b, '011b')
                b = b[::-1]
                r_value = int(b,2)
                self.cmd('PHASE%s:RLOAD %s' % (ph,r_value))

    def inductance (self, ph, i):
        if i is not None:
            self._write ('PHASE%s:LLOAD %s' % (ph, calcL (i, self.freq, self.volts)))

    def capacitance (self, ph, i):
        if i is not None:
            self._write ('PHASE%s:CLOAD %s' % (ph, calcC (i, self.freq, self.volts)))

    def capacitor_q(self, q=None):
        raise NotImplementedError('capacitor_q() is not implemented')

    def inductor_q(self, q=None):
        raise NotImplementedError('inductor_q() is not implemented')

    def resistance_p(self, p=None, v = None, i = None):
        # P=V^2*R, P = I^2*R
        raise NotImplementedError('resistance_p() is not implemented')

    def tune_current(self, i=None):
        raise NotImplementedError('tune_current() is not implemented')

def calcL (i, f, v):
    l_value = 0
    if i is not None:
        if (i == 0):
            b = 0
        else:
            # Convert based on Freq and Voltage
            b = float(BASE_LC_CURRENT)*(v*FNOM)/(f*VNOM)
            b = i / b
            b = round(b,0)
            b = int(b)
            b = format(b, '011b')
            b = b[::-1]
            l_value = int(b, 2)
    return int(l_value) #format (int(b),'03X')

def calcC (i, f, v):
    b = 0
    c_value = 0
    if i is not None:
        if (i == 0):
            b = 0
        else:
            # Convert based on Freq and Voltage
            b = float(BASE_LC_CURRENT * (v * f) / (FNOM * VNOM))
            b = i / b
            b = int(round(b, 0))
            b = format(b, '011b')
            b = b[::-1]
            c_value = int(b, 2)
    return int(c_value) #format(b, '03X')

if __name__ == "__main__":

    myRLC = ChromaRLC('GPIB0::3::INSTR',
                      'C:/Windows/System32/visa32.dll')
    print(myRLC.info())

    myRLC.resistance(2,120)
    time.sleep(4)

    myRLC.resistance (2,0)
    myRLC.capacitance(2,2.55)
    time.sleep(4)

    myRLC.capacitance(2,0)
    myRLC.inductance (2,2.55)
    time.sleep(4)

    myRLC.voltset(120)
    myRLC.inductance(2,6)
    time.sleep(4)

    myRLC.inductance (2,0)
    myRLC.capacitance (2,5)
    time.sleep(4)

    myRLC.freqset (60)
    myRLC.capacitance (2,5)
    time.sleep(4)

    myRLC.capacitance (2,0)
    myRLC.inductance (2,5)
    myRLC.close()



