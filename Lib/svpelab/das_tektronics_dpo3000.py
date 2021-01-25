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
from . import device_tektronix_dpo3000
from . import das

dpo3000_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Tektronix DPO3000'
}


def das_info():
    return dpo3000_info


def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = dpo3000_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'), active_value=mode, glob=True)
    info.param(pname('comm'), label='Communications Interface', default='Network', values=['VISA'])
    info.param(pname('visa_id'), label='visa_id',
               active=pname('comm'), active_value=['VISA'], default='TCPIP::10.1.2.87::INSTR')
    info.param(pname('sample_interval'), label='Sample Interval (ms)', default=0)

    info.param(pname('trigger_chan'), label='Trigger Channel', default='Chan 1',
               values=['Chan 1', 'Chan 2', 'Chan 3', 'Chan 4', 'Line'])
    info.param(pname('trigger_level'), label='Trigger Level', default=0.)
    info.param(pname('trigger_slope'), label='Rising or Falling Trigger', default='Rise', values=['Rise', 'Fall'])

    info.param(pname('chan_1'), label='Channel 1', default='Switch_Current',
               values=['Switch_Current', 'Switch_Voltage', 'Bus_Voltage', 'Bus_Current', 'None'])
    info.param(pname('chan_2'), label='Channel 2', default='Switch_Voltage',
               values=['Switch_Current', 'Switch_Voltage', 'Bus_Voltage', 'Bus_Current', 'None'])
    info.param(pname('chan_3'), label='Channel 3', default='Bus_Voltage',
               values=['Switch_Current', 'Switch_Voltage', 'Bus_Voltage', 'Bus_Current', 'None'])
    info.param(pname('chan_4'), label='Channel 4', default='None',
               values=['Switch_Current', 'Switch_Voltage', 'Bus_Voltage', 'Bus_Current', 'None'])

    info.param(pname('vert_1'), label='Vertical Scale, Chan 1 (V/div)', default=5.)
    info.param(pname('vert_2'), label='Vertical Scale, Chan 2 (V/div)', default=5.)
    info.param(pname('vert_3'), label='Vertical Scale, Chan 3 (V/div)', default=0.5)
    info.param(pname('vert_4'), label='Vertical Scale, Chan 4 (V/div)', default=0.5)
    info.param(pname('horiz'), label='Horizontal Scale (s/div)', default=20e-6)
    info.param(pname('sample_rate'), label='Sampling Rate (Hz)', default=2.5e9)
    info.param(pname('length'), label='Data Length', default='1k', values=['1k', '10k', '100k', '1M', '5M'])
    info.param(pname('save_wave'), label='Save Waveforms?', default='No', values=['Yes', 'No'])


GROUP_NAME = 'dpo3000'


class DAS(das.DAS):
    """
    Template for data acquisition (DAS) implementations. This class can be used as a base class or
    independent data acquisition classes can be created containing the methods contained in this class.
    """

    def __init__(self, ts, group_name, points=None, sc_points=None, support_interfaces=None):
        das.DAS.__init__(self, ts, group_name, points=points, sc_points=sc_points, support_interfaces=None)
        self.sample_interval = self._param_value('sample_interval')

        self.params['sample_interval'] = self.sample_interval
        self.params['visa_id'] = self._param_value('visa_id')
        self.params['comm'] = self._param_value('comm')
        self.params['ts'] = ts
        self.params['channel_types'] = []

        # create channel info for each channel from parameters
        for i in range(1, 5):
            self.params['channel_types'].append(self._param_value('chan_%d' % i))

        self.params['vertical_scale'] = [self._param_value('vert_1'),
                                         self._param_value('vert_2'),
                                         self._param_value('vert_3'),
                                         self._param_value('vert_4')]
        self.params['horiz_scale'] = self._param_value('horiz')
        self.params['sample_rate'] = self._param_value('sample_rate')
        self.params['save_wave'] = self._param_value('save_wave')

        if self._param_value('length') == '1k':
            self.params['length'] = 1000
        if self._param_value('length') == '10k':
            self.params['length'] = 10000
        if self._param_value('length') == '100k':
            self.params['length'] = 100000
        if self._param_value('length') == '1M':
            self.params['length'] = 1000000
        if self._param_value('length') == '5M':
            self.params['length'] = 5000000

        self.params['trig_chan'] = self._param_value('trigger_chan')
        self.params['trig_level'] = self._param_value('trigger_level')
        self.params['trig_slope'] = self._param_value('trigger_slope')

        self.device = device_tektronix_dpo3000.Device(self.params)
        self.data_points = self.device.data_points

        # initialize soft channel points
        self._init_sc_points()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)


if __name__ == "__main__":
    pass
