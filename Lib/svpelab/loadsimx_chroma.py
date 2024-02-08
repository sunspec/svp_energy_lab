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
from . import loadsim
from . import chroma_A800067 as chroma

chroma_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Chroma'
}

def loadsim_info():
    return chroma_info

def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = chroma_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('comm'), label='Communications Interface', default='VISA', values=['VISA'])
    info.param(pname('visa_device'), label='VISA Device String', active=pname('comm'),
               active_value=['VISA'], default='GPIB0::0::INSTR')
    info.param(pname('visa_path'), label='VISA Path', active=pname('comm'),
               active_value=['VISA'], default='')
    info.param(pname('volts'), label='Voltage', default=220)
    info.param(pname('freq'), label='Frequency', default=50)

GROUP_NAME = 'chroma'


class LoadSim(loadsim.LoadSim):
    """
    Chroma loadsim class.
    """
    def __init__(self, ts, group_name):
        loadsim.LoadSim.__init__(self, ts, group_name)
        self.visa_device = self._param_value('visa_device')
        self.visa_path = self._param_value('visa_path')
        self.volts = self._param_value('volts')
        self.freq = self._param_value('freq')

        self.rlc = chroma.ChromaRLC(visa_device=self.visa_device, visa_path=self.visa_path, volts = self.volts,
                                    freq = self.freq)
        self.rlc.open()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def resistance(self, ph = None, r=None):
        self.rlc.resistance(ph,r)

    def voltset(self,v):
        return self.rlc.voltset(v)

    def freqset(self,f):
        return self.rlc.freqset(f)

    def inductance(self, ph,i=None):
        if i is not None:
            return self.rlc.inductance(ph,i)


    def capacitance(self, ph, i=None):
        if i is not None:
            return self.rlc.capacitance(ph,i)
        else:
            self.ts.log('Enter the capacitive load in F.')

    """def capacitor_q(self, q=None):
        if q is not None:
            self.ts.log('Adjust the capacitive load of the fundamental freq to %0.3f VAr.' % q)
        else:
            self.ts.log('Enter the capacitor reactive power in VAr.')

    def inductor_q(self, q=None):
        if q is not None:
            self.ts.log('Adjust the inductive load of the fundamental freq to %0.3f VAr.' % q)
        else:
            self.ts.log('Enter the inductor reactive power in VAr.')

    def resistance_p(self, p=None):
        if p is not None:
            self.ts.log('Adjust the resistive load of the fundamental freq to  %0.3f W.' % p)
        else:
            self.ts.log('Enter the resistor power in W.')

    def tune_current(self, i=None):
        if c is not None:
            self.ts.log('Adjust R, L, and C until the fundamental frequency current through switch S3 is '
                            'less than %0.2f' % i)
        else:
            pass
    """