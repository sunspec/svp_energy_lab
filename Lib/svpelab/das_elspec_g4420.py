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
from . import device_elspec_g4420
from . import das

elspec_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Elspec G4420'
}

def das_info():
    return elspec_info

def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = elspec_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('comm'), label='Communications Interface', default='Modbus TCP', values=['Modbus TCP'])
    info.param(pname('ip_addr'), label='IP Address',
               active=pname('comm'),  active_value=['Modbus TCP'], default='1.1.1.39')
    info.param(pname('ip_port'), label='IP Port', active=pname('comm'),  active_value=['Modbus TCP'], default=502)
    info.param(pname('ip_timeout'), label='IP Timeout', active=pname('comm'),  active_value=['Modbus TCP'], default=5)
    info.param(pname('slave_id'), label='Slave Id', active=pname('comm'),  active_value=['Modbus TCP'], default=159)

    info.param(pname('sample_interval'), label='Sample Interval (ms)', default=1000)

GROUP_NAME = 'elspec_g4420'


class DAS(das.DAS):

    def __init__(self, ts, group_name, points=None, sc_points=None):
        das.DAS.__init__(self, ts, group_name, points=points, sc_points=sc_points)
        self.sample_interval = self._param_value('sample_interval')

        self.params['comm'] = self._param_value('comm')
        if self.params['comm'] == 'Modbus TCP':
            self.params['ip_addr'] = self._param_value('ip_addr')
            self.params['ip_port'] = self._param_value('ip_port')
            self.params['ip_timeout'] = self._param_value('ip_timeout')
            self.params['slave_id'] = self._param_value('slave_id')

        self.device = device_elspec_g4420.Device(self.params, ts)
        self.data_points = self.device.data_points

        # initialize soft channel points
        self._init_sc_points()

        if self.sample_interval < 50 and self.sample_interval is not 0:
            raise das.DASError('Parameter error: sample interval must be at least 50ms')

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)


if __name__ == "__main__":

    pass


