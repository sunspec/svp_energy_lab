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
from . import device_das_sim
from . import das
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
                     active=gname('mode'),  active_value=mode)
    info.param(pname('data_file'), label='Data File (in SVP Files directory)', default='data.csv')
    info.param(pname('use_timestamp'), label='Use Data File Timestamp', default='Enabled', values=['Enabled',
                                                                                                   'Disabled'])
    info.param(pname('at_end'), label='At End of Data', default='Repeat last record', values=['Loop to start',
                                                                                              'Repeat last record',
                                                                                              'Return an error'])

GROUP_NAME = 'sim'


class DAS(das.DAS):
    def __init__(self, ts, group_name, points=None, sc_points=None):
        das.DAS.__init__(self, ts, group_name, points=points, sc_points=sc_points)
        data_file = self._param_value('data_file')
        if data_file and data_file != 'None':
            data_file = os.path.join(self.files_dir, data_file)
        self.params['points'] = self.points
        self.params['data_file'] = data_file
        self.params['use_timestamp'] = self._param_value('use_timestamp')
        self.params['at_end'] = self._param_value('at_end')
        self.params['ts'] = self.ts

        self.ts.log('results_dir = %s' % (ts._results_dir))

        self.device = device_das_sim.Device(self.params)
        self.data_points = self.device.data_points

        # initialize soft channel points
        self._init_sc_points()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)


if __name__ == "__main__":

    pass


