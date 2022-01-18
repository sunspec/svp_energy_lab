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

from . import gridsim

pass_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Pass'
}

def gridsim_info():
    return pass_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = pass_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('v_nom'), label='Nominal voltage for all phases', default=240.)
    info.param(pname('v_max'), label='Max Voltage', default=600.0)
    info.param(pname('i_max'), label='Max Current', default=100.0)
    info.param(pname('freq'), label='Frequency', default=60.0)

GROUP_NAME = 'pass'


class GridSim(gridsim.GridSim):

    def __init__(self, ts, group_name, params=None):
        gridsim.GridSim.__init__(self, ts, group_name, params)

        self.v_nom = self._param_value('v_nom')
        self.v_max = self._param_value('v_max')
        self.i_max = self._param_value('i_max')
        self.freq_param = self._param_value('freq')
        self.relay_state = gridsim.RELAY_OPEN
        self.regen_state = gridsim.REGEN_OFF

        if self.auto_config == 'Enabled':
            self.config()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        if self.ts.confirm('Configure grid simulator to following settings:\n'
                           ' \nVoltage = %s\nMax voltage = %s\nMax current = %s\nFrequency = %s' %
                           (self.v_nom, self.v_max, self.i_max, self.freq_param)) is False:
            raise gridsim.GridSimError('Aborted grid simulation')

    def current_max(self, current=None):
        """
        Set the value for max current if provided. If none provided, obtains
        the value for max current.
        """
        if current is not None:
            if self.ts.confirm('Set grid simulator maximum current to %s' % (current)) is False:
                raise gridsim.GridSimError('Aborted grid simulation')
        else:
            current = self.i_max
        return current

    def freq(self, freq=None):
        """
        Set the value for frequency if provided. If none provided, obtains
        the value for frequency.
        """
        if freq is not None:
            pass
        else:
            freq = self.freq_param
        return freq

    def profile_load(self, profile_name, v_step=100, f_step=100, t_step=None):
        """
        Load the profile either in list format or from a file.

        Each entry in the profile contains:
            time offset in seconds, voltage 1, voltage 2, voltage 3, frequency
        The voltage is applied to all phases.

        The profile param specifies the profile as a list of tuples in the form:
        (time, v1, v2, v3, frequency)

        The filename param specifies the profile as a csv file with the first
        line specifying the elements order of the elements and subsequent lines
        containing each profile entry:
        time, voltage 1, voltage 2, voltage 3, frequency
        t0, v1, v2, v3, f
        t1, v1, v2, v3, f
        """
        if self.ts.confirm('Load grid simulator profile') is False:
            raise gridsim.GridSimError('Aborted grid simulation')

    def profile_start(self):
        """
        Start the loaded profile.
        """
        if self.ts.confirm('Start grid simulator profile') is False:
            raise gridsim.GridSimError('Aborted grid simulation')

    def profile_stop(self):
        """
        Stop the running profile.
        """
        if self.ts.confirm('Stop grid simulator profile') is False:
            raise gridsim.GridSimError('Aborted grid simulation')

    def regen(self, state=None):
        """
        Set the state of the regen mode if provided. Valid states are: REGEN_ON,
        REGEN_OFF. If none is provided, obtains the state of the regen mode.
        """
        if state is not None:
            self.regen_state = state
        else:
            state = self.regen_state
        return state

    def relay(self, state=None):
        """
        Set the state of the relay if provided. Valid states are: RELAY_OPEN,
        RELAY_CLOSED. If none is provided, obtains the state of the relay.
        """
        if state is not None:
            self.relay_state = state
            if self.ts.confirm('Set grid simulator relay to %s' % (state)) is False:
                raise gridsim.GridSimError('Aborted grid simulation')
        else:
            state = self.relay_state
        return state

    def voltage(self, voltage=None):
        """
        Set the value for voltage 1, 2, 3 if provided. If none provided, obtains
        the value for voltage. Voltage is a tuple containing a voltage value for
        each phase.
        """
        if voltage is not None:
            pass
        else:
            voltage = (self.v_nom, self.v_nom, self.v_nom)
        return voltage

    def voltage_max(self, voltage=None):
        """
        Set the value for max voltage if provided. If none provided, obtains
        the value for max voltage.
        """
        if voltage is not None:
            self.v_max = voltage[0]
            if self.ts.confirm('Set grid simulator maximum voltage to %s' % (voltage)) is False:
                raise gridsim.GridSimError('Aborted grid simulation')
        else:
            voltage = (self.v_max, self.v_max, self.v_max)
        return voltage
