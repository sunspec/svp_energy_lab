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

from . import das
from . import device_chroma_dpm

chroma_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Chroma'
}

def das_info():
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

GROUP_NAME = 'chroma'


class DAS(das.DAS):
    def __init__(self, ts, group_name, points=None, sc_points=None):
        das.DAS.__init__(self, ts, group_name, points=points, sc_points=sc_points)
        self.params['visa_device'] = self._param_value('visa_device')
        visa_path = self._param_value('visa_path')
        if visa_path != 'None':
            self.params['visa_path'] = visa_path
        self.sample_interval = self._param_value('sample_interval')

        # create channel info for each channel from parameters
        channels = [None]
        for i in range(1, 5):
            chan_type = self._param_value('chan_%d' % (i))
            chan_label = self._param_value('chan_%d_label' % (i))
            if chan_label == 'None':
                chan_label = ''
            chan = {'type': chan_type, 'points': self.points.get(chan_type), 'label': chan_label}
            channels.append(chan)

        self.params['channels'] = channels

        self.device = device_chroma_dpm.Device(self.params)
        self.data_points = self.device.data_points

        # initialize soft channel points
        self._init_sc_points()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

if __name__ == "__main__":

    pass


