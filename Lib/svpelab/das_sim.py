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

import device_das_sim
import das

import script

sim_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'DAS Simulation'
}

def das_info():
    return sim_info

def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = sim_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('data_file'), label='Data File', default='data.csv', ptype=script.PTYPE_FILE)
    info.param(pname('sample_interval'), label='Sample Interval (ms)', default=1000)

    info.param(pname('chan_1'), label='Channel 1', default='AC', values=['AC', 'DC', 'Unused'])
    info.param(pname('chan_2'), label='Channel 2', default='AC', values=['AC', 'DC', 'Unused'])
    info.param(pname('chan_3'), label='Channel 3', default='AC', values=['AC', 'DC', 'Unused'])
    info.param(pname('chan_4'), label='Channel 4', default='DC', values=['AC', 'DC', 'Unused'])

    info.param(pname('chan_1_label'), label='Channel 1 Label', default='1', active=pname('chan_1'),
               active_value=['AC', 'DC'])
    info.param(pname('chan_2_label'), label='Channel 2 Label', default='2', active=pname('chan_2'),
               active_value=['AC', 'DC'])
    info.param(pname('chan_3_label'), label='Channel 3 Label', default='3', active=pname('chan_3'),
               active_value=['AC', 'DC'])
    info.param(pname('chan_4_label'), label='Channel 4 Label', default='', active=pname('chan_4'),
               active_value=['AC', 'DC'])

GROUP_NAME = 'sim'


class DAS(das.DAS):
    def __init__(self, ts, group_name, points=None):
        das.DAS.__init__(self, ts, group_name, points=points)
        self.device = device_das_sim.Device()
        self.data_file = self._param_value('data_file')
        self.sample_interval = self._param_value('sample_interval')

        if self.sample_interval < 50:
            raise das.DASError('Parameter error: sample interval must be at least 50 ms')

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)


if __name__ == "__main__":

    pass


