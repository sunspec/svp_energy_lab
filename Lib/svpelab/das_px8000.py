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

from . import device_px8000
from . import das

px8000_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Yokogawa PX8000'
}

def das_info():
    return px8000_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = px8000_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('comm'), label='Communications Interface', default='Network', values=['Network'])
    info.param(pname('ip_addr'), label='IP Address',
               active=pname('comm'),  active_value=['Network'], default='192.168.0.10')
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

    '''
    info.param(pname('wiring_system'), label='Wiring System', default='1P2W', values=['1P2W', '1P3W', '3P3W',
                                                                                      '3P4W', '3P3W(3V3A)'])
    '''
    # info.param(pname('ip_port'), label='IP Port',
    #            active=pname('comm'),  active_value=['Network'], default=4944)
    # info.param(pname('ip_timeout'), label='IP Timeout',
    #            active=pname('comm'),  active_value=['Network'], default=5)

GROUP_NAME = 'px8000'


class DAS(das.DAS):
    """
    Template for data acquisition (DAS) implementations. This class can be used as a base class or
    independent data acquisition classes can be created containing the methods contained in this class.
    """

    def __init__(self, ts, group_name, points=None, sc_points=None):
        das.DAS.__init__(self, ts, group_name, points=points, sc_points=sc_points)
        self.sample_interval = self._param_value('sample_interval')

        self.params['ip_addr'] = self._param_value('ip_addr')
        self.params['ipport'] = self._param_value('ip_port')
        self.params['timeout'] = self._param_value('ip_timeout')

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

        self.device = device_px8000.Device(self.params)
        self.data_points = self.device.data_points

        # initialize soft channel points
        self._init_sc_points()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)


if __name__ == "__main__":

    pass


