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

import gridsim

try:
    import typhoon.api.hil_control_panel as cp
except Exception, e:
    print('Typhoon HIL API not installed. %s' % e)

typhoon_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Typhoon'
}

def gridsim_info():
    return typhoon_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = typhoon_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('v_nom'), label='EUT nominal voltage for all 3 phases (V)', default=230.)
    info.param(pname('f_nom'), label='EUT nominal frequency', default=50.)
    info.param(pname('p_nom'), label='EUT nominal power (W)', default=34500.)

GROUP_NAME = 'typhoon'


class GridSim(gridsim.GridSim):
    """
    Typhoon grid simulation implementation.

    Valid parameters:
      mode - 'Typhoon'
      auto_config - ['Enabled', 'Disabled']
      v_nom
      v_max
      i_max
      freq
      profile_name
    """
    def __init__(self, ts, group_name):
        gridsim.GridSim.__init__(self, ts, group_name)

        self.ts = ts
        self.p_nom = self._param_value('p_nom')
        self.v_nom = self._param_value('v_nom')
        self.v = self.v_nom
        self.f_nom = self._param_value('f_nom')
        self.f = self.f_nom

        if self.auto_config == 'Enabled':
            ts.log('Configuring the Typhoon HIL Emulated Grid Simulator.')
            self.config()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        self.config_phase_angles()
        self.freq(freq=self.f_nom)
        self.voltage(voltage=self.v_nom)

    def config_phase_angles(self):
        # set the phase angles for the 3 phases
        cp.set_source_sine_waveform('V_source_phase_A', phase=0.0)
        cp.set_source_sine_waveform('V_source_phase_B', phase=-120.0)
        cp.set_source_sine_waveform('V_source_phase_C', phase=120.0)

    def current(self, current=None):
        """
        Set the value for current if provided. If none provided, obtains
        the value for current.
        """
        return self.v/self.p_nom

    def current_max(self, current=None):
        """
        Set the value for max current if provided. If none provided, obtains
        the value for max current.
        """
        return self.v/self.p_nom

    def freq(self, freq=None):
        """
        Set the value for frequency if provided. If none provided, obtains
        the value for frequency.
        """
        if freq is not None:
            self.f = freq
            cp.prepare_source_sine_waveform('V_source_phase_A', frequency=self.f)
            cp.prepare_source_sine_waveform('V_source_phase_B', frequency=self.f)
            cp.prepare_source_sine_waveform('V_source_phase_C', frequency=self.f)
            cp.update_sources(["V_source_phase_A", "V_source_phase_B", "V_source_phase_C"], executeAt=None)
        freq = self.f
        return freq

    def profile_load(self, profile_name, v_step=100, f_step=100, t_step=None):
        pass
        # if profile_name is None:
        #     raise gridsim.GridSimError('Profile not specified.')
        #
        # if profile_name == 'Manual':  # Manual reserved for not running a profile.
        #     self.ts.log_warning('"Manual" simulation profile reserved for not autonomously running a profile.')
        #     return
        #
        # v_nom = self.v_nom_param
        # freq_nom = self.freq_param
        #
        # # for simple transient steps in voltage or frequency, use v_step, f_step, and t_step
        # if profile_name is 'Transient_Step':
        #     if t_step is None:
        #         raise gridsim.GridSimError('Transient profile did not have a duration.')
        #     else:
        #         # (time offset in seconds, % nominal voltage, % nominal frequency)
        #         profile = [(0, v_step, f_step),(t_step, v_step, f_step),(t_step, 100, 100)]
        #
        # else:
        #     # get the profile from grid_profiles
        #     profile = grid_profiles.profiles.get(profile_name)
        #     if profile is None:
        #         raise gridsim.GridSimError('Profile Not Found: %s' % profile_name)


    def profile_start(self):
        """
        Start the loaded profile.
        """
        pass

    def profile_stop(self):
        """
        Stop the running profile.
        """
        pass

    def relay(self, state=None):
        """
        Set the state of the relay if provided. Valid states are: RELAY_OPEN,
        RELAY_CLOSED. If none is provided, obtains the state of the relay.
        """
        pass

    def voltage(self, voltage=None):
        """
        Set the value for voltage 1, 2, 3 if provided. If none provided, obtains
        the value for voltage. Voltage is a tuple containing a voltage value for
        each phase.
        """
        if voltage is not None:
            # set output voltage on all phases
            if type(voltage) is not list and type(voltage) is not tuple:
                self.v = voltage
                self.ts.log_debug('        Setting Typhoon AC voltage to %s' % self.v)
                cp.prepare_source_sine_waveform('V_source_phase_A', rms=self.v)
                cp.prepare_source_sine_waveform('V_source_phase_B', rms=self.v)
                cp.prepare_source_sine_waveform('V_source_phase_C', rms=self.v)
                cp.update_sources(["V_source_phase_A", "V_source_phase_B", "V_source_phase_C"], executeAt=None)
                # cp.wait_msec(100.0)

            else:
                self.v = voltage[0]  # currently don't support asymmetric voltages.
                cp.prepare_source_sine_waveform('V_source_phase_A', rms=self.v)
                cp.prepare_source_sine_waveform('V_source_phase_B', rms=self.v)
                cp.prepare_source_sine_waveform('V_source_phase_C', rms=self.v)
                cp.update_sources(["V_source_phase_A", "V_source_phase_B", "V_source_phase_C"], executeAt=None)
                # cp.wait_msec(100.0)

        v1 = self.v
        v2 = self.v
        v3 = self.v
        return v1, v2, v3

    def voltage_max(self, voltage=None):
        """
        Set the value for max voltage if provided. If none provided, obtains
        the value for max voltage.
        """
        if voltage is not None:
            # set max voltage on all phases
            pass
        return self.v, self.v, self.v

    def i_max(self):
        return self.v/self.p_nom

    def v_max(self):
        return self.v

    def v_nom(self):
        return self.v_nom

if __name__ == "__main__":
    pass
