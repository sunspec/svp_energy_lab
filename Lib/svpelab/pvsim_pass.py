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
from . import pvsim

pass_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Pass'
}

def pvsim_info():
    return pass_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = pass_info['mode']
    info.param_add_value(gname('mode'), mode)

GROUP_NAME = 'pass'


class PVSim(pvsim.PVSim):

    def __init__(self, ts, group_name):
        pvsim.PVSim.__init__(self, ts, group_name)

    def irradiance_set(self, irradiance=1000):
        if self.ts.log('Please change the irradiance to %0.1f W/m^2.' % irradiance) is False:
            raise pvsim.PVSimError('Aborted PV simulation')

    def power_set(self, power):
        if self.ts.log('Please change the power to %0.1f W.' % power) is False:
            raise pvsim.PVSimError('Aborted PV simulation')

    def power_on(self):
        if self.ts.log('Please turn on PV simulator to give EUT DC power.') is False:
            raise pvsim.PVSimError('Aborted PV simulation')

    def profile_start(self):
        if self.ts.log('Please run the PV simulator profile.') is False:
            raise pvsim.PVSimError('Aborted PV simulation')

if __name__ == "__main__":
    pass

