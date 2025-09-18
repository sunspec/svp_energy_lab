"""
Copyright (c) 2018, Austrian Institute of Technology
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

Neither the names of the Austrian Institute of Technology nor the names of its
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
from .device_das_dewetron import Device
from .das import DAS as MDAS

dewetron_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Dewetron'
}

def das_info():
    return dewetron_info

def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = dewetron_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'), active_value=mode, glob=True)
    info.param(pname('comm'), label='Communications Interface', default='Network', values=['Network'])
    info.param(pname('ip_addr'), label='DEWESoft NET IP Address',
               active=pname('comm'), active_value=['Network'], default='127.0.0.1')
    info.param(pname('ip_port'), label='DEWESoft NET Port',
               active=pname('comm'), active_value=['Network'], default=8999)

    info.param(pname('deweproxy_ip_addr'), label='Binary Server IP Address',
               active=pname('comm'), active_value=['Network'], default='127.0.0.1')
    info.param(pname('deweproxy_ip_port'), label='Binary Server Port',
               active=pname('comm'), active_value=['Network'], default=9000)

    info.param(pname('sample_interval'), label='SVP Sample Interval (ms)', default=1000)
    info.param(pname('sample_interval_dewe'), label='Dewetron Sample Frequency (Hz)', default=5000)

    info.param(pname('AC_VRMS_1'), label='L1 Voltage RMS (V)', default='EUT/U_rms_L1')
    info.param(pname('AC_VRMS_2'), label='L2 Voltage RMS (V)', default='EUT/U_rms_L2')
    info.param(pname('AC_VRMS_3'), label='L3 Voltage RMS (V)', default='EUT/U_rms_L3')
    info.param(pname('AC_IRMS_1'), label='L1 Current RMS (A)', default='EUT/I_rms_L1')
    info.param(pname('AC_IRMS_2'), label='L2 Current RMS (A)', default='EUT/I_rms_L2')
    info.param(pname('AC_IRMS_3'), label='L3 Current RMS (A)', default='EUT/I_rms_L3')
    info.param(pname('AC_FREQ_1'), label='L1 Frequency (Hz)', default='EUT/Frequency')
    info.param(pname('AC_FREQ_2'), label='L2 Frequency (Hz)', default='EUT/Frequency')
    info.param(pname('AC_FREQ_3'), label='L3 Frequency (Hz)', default='EUT/Frequency')
    info.param(pname('AC_P_1'), label='L1 Active Power (W)', default='EUT/P_L1')
    info.param(pname('AC_P_2'), label='L2 Active Power (W)', default='EUT/P_L2')
    info.param(pname('AC_P_3'), label='L3 Active Power (W)', default='EUT/P_L3')
    info.param(pname('AC_S_1'), label='L1 Apparent Power (VA)', default='EUT/S_L1')
    info.param(pname('AC_S_2'), label='L2 Apparent Power (VA)', default='EUT/S_L2')
    info.param(pname('AC_S_3'), label='L3 Apparent Power (VA)', default='EUT/S_L3')
    info.param(pname('AC_Q_1'), label='L1 Reactive Power (Var)', default='EUT/Q_L1')
    info.param(pname('AC_Q_2'), label='L2 Reactive Power (Var)', default='EUT/Q_L1')
    info.param(pname('AC_Q_3'), label='L3 Reactive Power (Var)', default='EUT/Q_L1')
    info.param(pname('AC_PF_1'), label='L1 Power factor', default='EUT/PF_L1')
    info.param(pname('AC_PF_2'), label='L2 Power factor', default='EUT/PF_L2')
    info.param(pname('AC_PF_3'), label='L3 Power factor', default='EUT/PF_L3')

    info.param(pname('DC_V'), label='DC Voltage (V)', default='PV/U_rms_L1')
    info.param(pname('DC_I'), label='DC Current (A)', default='PV/I_rms_L1')
    info.param(pname('DC_P'), label='DC Power (W)', default='PV/P_L1')




GROUP_NAME = 'dewetron'


class DAS(MDAS):
    """
    Template for data acquisition (DAS) implementations. This class can be used as a base class or
    independent data acquisition classes can be created containing the methods contained in this class.
    """

    def __init__(self, ts, group_name, points=None, sc_points=None):
        MDAS.__init__(self, ts, group_name, points=points, sc_points=sc_points)

        self.params['ts'] = ts

        self.params['sample_interval'] = self._param_value('sample_interval')
        self.sample_interval = self.params['sample_interval']

        self.params['ip_addr'] = self._param_value('ip_addr')
        self.params['ipport'] = self._param_value('ip_port')

        self.params['deweproxy_ip_addr'] = self._param_value('deweproxy_ip_addr')
        self.params['deweproxy_ip_port'] = self._param_value('deweproxy_ip_port')


        self.params['AC_VRMS_1'] = self._param_value('AC_VRMS_1')
        self.params['AC_VRMS_2'] = self._param_value('AC_VRMS_2')
        self.params['AC_VRMS_3'] = self._param_value('AC_VRMS_3')
        self.params['AC_IRMS_1'] = self._param_value('AC_IRMS_1')
        self.params['AC_IRMS_2'] = self._param_value('AC_IRMS_2')
        self.params['AC_IRMS_3'] = self._param_value('AC_IRMS_3')
        self.params['AC_FREQ_1'] = self._param_value('AC_FREQ_1')
        self.params['AC_FREQ_2'] = self._param_value('AC_FREQ_2')
        self.params['AC_FREQ_3'] = self._param_value('AC_FREQ_3')
        self.params['AC_P_1'] = self._param_value('AC_P_1')
        self.params['AC_P_2'] = self._param_value('AC_P_2')
        self.params['AC_P_3'] = self._param_value('AC_P_3')
        self.params['AC_S_1'] = self._param_value('AC_S_1')
        self.params['AC_S_2'] = self._param_value('AC_S_2')
        self.params['AC_S_3'] = self._param_value('AC_S_3')
        self.params['AC_Q_1'] = self._param_value('AC_Q_1')
        self.params['AC_Q_2'] = self._param_value('AC_Q_2')
        self.params['AC_Q_3'] = self._param_value('AC_Q_3')
        self.params['AC_PF_1'] = self._param_value('AC_PF_1')
        self.params['AC_PF_2'] = self._param_value('AC_PF_2')
        self.params['AC_PF_3'] = self._param_value('AC_PF_3')
        self.params['DC_V'] = self._param_value('DC_V')
        self.params['DC_I'] = self._param_value('DC_I')
        self.params['DC_P'] = self._param_value('DC_P')
        self.params['sample_interval_dewe'] = self._param_value('sample_interval_dewe')



        self.device = Device(self.params)
        self.data_points = self.device.data_points

        # initialize soft channel points
        self._init_sc_points()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)


if __name__ == "__main__":

    pass
