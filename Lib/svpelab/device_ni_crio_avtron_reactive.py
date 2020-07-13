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
import visa

TERMINATOR = '\n'

def LoadBankError(Exception):
    pass

class AvtronReactive(object):
    """
    Communications to an Avtron 55 kVar load bank via a NI cRIO-9073
    """

    def __init__(self, visa_device=None, visa_path=None):
        self.rm = None      # Resource Manager for VISA
        self.conn = None    # Connection to instrument for VISA-GPIB
        self.visa_device = visa_device
        self.visa_path = visa_path
        self.data_query = ''

        self.open()  # open communications, not the relay

    def open(self):

        try:
            self.rm = visa.ResourceManager(self.visa_path)
            self.conn = self.rm.open_resource(self.visa_device)
            self.conn.write_termination = TERMINATOR

        except Exception as e:
            raise LoadBankError('Cannot open VISA connection to %s\n\t%s' % (self.visa_device, str(e)))

    def close(self):
        try:
            if self.rm is not None:
                if self.conn is not None:
                    self.conn.close()
                self.rm.close()
                time.sleep(1)
        except Exception as e:
            raise LoadBankError(str(e))

    def info(self):
        return self._query('*IDN?')

    def cmd(self, cmd_str):

        try:
            cmd_str = cmd_str.strip()
            self._write(cmd_str)
            resp = self._query('SYSTem:ERRor?')  #\r
            if len(resp) > 0:
                if resp[0] != '0':
                    raise LoadBankError(resp + ' ' + cmd_str)
        except Exception as e:
            raise LoadBankError(str(e))

    def _query(self, cmd_str):
        try:
            cmd_str.strip()
            if self.conn is None:
                raise LoadBankError('Connection not open')
            return self.conn.query(cmd_str)

        except Exception as e:
            raise LoadBankError(str(e))

    def _write(self, cmd_str):
        try:
            if self.conn is None:
                raise LoadBankError('Connection not open')
            return self.conn.write(cmd_str)
        except Exception as e:
            raise LoadBankError(str(e))

    def voltset(self, v):
        self.volts = v

    def freqset(self, f):
        self.freq = f

    def resistance(self, ph=None, r=None):
        b = 0.0
        if r is not None:
            # Calculate resistance.
            if r == 0:
                self._write('PHASE%s:RLOAD 000' % (ph))
            else:
                b = (1 / float(r))
                b = BASE_RESISTANCE*b
                b = int(round(b,0))
                b = format(b, '011b')
                b = b[::-1]
                r_value = int(b,2)
                self.cmd('PHASE%s:RLOAD %s' % (ph,r_value))

    def inductance(self, ph, i):
        if i is not None:
            self._write('PHASE%s:LLOAD %s' % (ph, calcL (i, self.freq, self.volts)))

    def capacitance(self, ph, i):
        if i is not None:
            self._write('PHASE%s:CLOAD %s' % (ph, calcC (i, self.freq, self.volts)))

    def capacitor_q(self, q=None):
        raise NotImplementedError('capacitor_q() is not implemented')

    def inductor_q(self, q=None):
        raise NotImplementedError('inductor_q() is not implemented')

    def resistance_p(self, p=None, v=None, i=None):
        # P=V^2*R, P = I^2*R
        raise NotImplementedError('resistance_p() is not implemented')

    def tune_current(self, i=None):
        raise NotImplementedError('tune_current() is not implemented')

if __name__ == "__main__":

    # rio://192.168.1.231/RIO0
    # visa://192.168.1.231/ASRL1::INSTR

    loadbank = AvtronReactive('//192.168.1.231/ASRL1::INSTR', 'C:/Windows/System32/visa32.dll')
    # print loadbank.info()
    loadbank.close()

