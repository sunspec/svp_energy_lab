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

try:
    import typhoon.api.hil as cp  # control panel
except Exception as e:
    print(('Typhoon HIL API not installed. %s' % e))

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

    info.param(pname('waveform_names'), label='Waveform Names',
               default="V_source_phase_A, V_source_phase_B, V_source_phase_C")

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

        # for asymettric voltage tests
        self.v1 = self.v_nom
        self.v2 = self.v_nom
        self.v3 = self.v_nom

        self.f_nom = self._param_value('f_nom')
        self.f = self.f_nom

        try:
            tempstring = self._param_value('waveform_names').strip().split(',')
            self.waveform_source_list = [i .rstrip(' ').lstrip(' ')for i in tempstring]
        except Exception as e:
            ts.log("Failed waveform_names: %s" % e)
            raise e

        self.ts.log_debug('Grid Sources: %s.' % self.waveform_source_list)

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
        if len(self.waveform_source_list) == 1:  # single phase
            cp.set_source_sine_waveform(self.waveform_source_list[0], phase=0.0)
        elif len(self.waveform_source_list) == 2:  # split phase
            cp.set_source_sine_waveform(self.waveform_source_list[0], phase=0.0)
            cp.set_source_sine_waveform(self.waveform_source_list[1], phase=180.0)
        elif len(self.waveform_source_list) == 3:  # three phase
            cp.set_source_sine_waveform(self.waveform_source_list[0], phase=0.0)
            cp.set_source_sine_waveform(self.waveform_source_list[1], phase=-120.0)
            cp.set_source_sine_waveform(self.waveform_source_list[2], phase=120.0)
        else:
            self.ts.log_warning('Phase angles not set for simulation because the number of grid simulation '
                                'waveforms is not 1, 2, or 3.')

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
            for wave in self.waveform_source_list:
                cp.prepare_source_sine_waveform(wave, frequency=self.f)
            cp.update_sources(self.waveform_source_list, executeAt=None)

            # For setting sine source in Anti-islanding component you can use:
            # cp.set_source_sine_waveform('Anti-islanding1.Vgrid', rms=50.0, frequency=50.0)

        freq = self.f
        return freq

    def profile_load(self, profile_name=None, v_step=100, f_step=100, t_step=None, profile=None):
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
            # self.ts.log_debug('waveforms: %s' % self.waveform_source_list)
            if type(voltage) is not list and type(voltage) is not tuple:
                self.v = voltage
                # self.ts.log_debug('        Setting Typhoon AC voltage to %s' % self.v)
                for wave in self.waveform_source_list:
                    # self.ts.log_debug('Source: %s set to %s V.' % (wave, self.v))
                    cp.prepare_source_sine_waveform(name=wave, rms=self.v)
                # cp.update_sources(self.waveform_source_list, executeAt=None)
                cp.update_sources(self.waveform_source_list, executeAt=None)
                # cp.wait_msec(100.0)
                self.v1 = self.v
                self.v2 = self.v
                self.v3 = self.v

            else:
                # self.ts.log('Creating asymmetric voltage condition with voltages: %s, %s, %s' %
                #             (voltage[0], voltage[1], voltage[2]))
                phase = 0
                for wave in self.waveform_source_list:
                    phase += 1
                    self.v = voltage[phase-1]
                    cp.prepare_source_sine_waveform(name=wave, rms=voltage[phase-1])
                    if phase == 1:
                        v1 = voltage[phase-1]
                    if phase == 2:
                        v2 = voltage[phase-1]
                    if phase == 3:
                        v3 = voltage[phase-1]

                cp.update_sources(self.waveform_source_list, executeAt=None)
                # cp.wait_msec(100.0)
                self.v = (v1 + v2 + v3)/3
                self.v1 = v1
                self.v2 = v2
                self.v3 = v3

        return self.v1, self.v2, self.v3

    def voltage_max(self, voltage=None):
        """
        Set the value for max voltage if provided. If none provided, obtains
        the value for max voltage.
        """
        if voltage is not None:
            # set max voltage on all phases
            pass
        return self.v, self.v, self.v

    def config_asymmetric_phase_angles(self, mag=None, angle=None):
        """
        :param mag: list of voltages for the imbalanced test, e.g., [277.2, 277.2, 277.2]
        :param angle: list of phase angles for the imbalanced test, e.g., [0, 120, -120]

        :returns: voltage list and phase list
        """
        if mag is not None:
            if type(mag) is not list:
                raise gridsim.GridSimError('Waveform magnitudes were not provided as list. "mag" type: %s' % type(mag))

        if angle is not None:
            if type(angle) is list:
                cp.set_source_sine_waveform(self.waveform_source_list[0], rms=mag[0], phase=angle[0])
                cp.set_source_sine_waveform(self.waveform_source_list[1], rms=mag[1], phase=angle[1])
                cp.set_source_sine_waveform(self.waveform_source_list[2], rms=mag[2], phase=angle[2])
                cp.update_sources(self.waveform_source_list, executeAt=None)
                # cp.wait_msec(100.0)
                self.v = (v1 + v2 + v3)/3
                self.v1 = v1
                self.v2 = v2
                self.v3 = v3

            else:
                raise gridsim.GridSimError('Waveform angles were not provided as list.')

        voltages = [self.v1, self.v2, self.v3]
        phases = angle
        return voltages, phases

    def i_max(self):
        return self.v/self.p_nom

    def v_max(self):
        return self.v

    def v_nom(self):
        return self.v_nom

    def meas_voltage(self, ph_list=(1, 2, 3)):
        v1 = float(cp.read_analog_signal(name='V( Vrms1 )'))
        v2 = float(cp.read_analog_signal(name='V( Vrms2 )'))
        v3 = float(cp.read_analog_signal(name='V( Vrms3 )'))
        return v1, v2, v3

    def meas_current(self, ph_list=(1, 2, 3)):
        # for use during anti-islanding testing to determine the current to the utility
        try:
            i1 = float(cp.read_analog_signal(name='I( Anti-islanding1.Irms1_utility )'))
            i2 = float(cp.read_analog_signal(name='I( Anti-islanding1.Irms2_utility )'))
            i3 = float(cp.read_analog_signal(name='I( Anti-islanding1.Irms3_utility )'))
            print(('Utility currents are %s, %s, %s' % (i1, i2, i3)))
        except Exception as e:
            i1 = i2 = i3 = None
        return i1, i2, i3

if __name__ == "__main__":
    import sys
    import time
    import numpy as np
    import math
    sys.path.insert(0, r'C:/Typhoon HIL Control Center/python_portable/Lib/site-packages')
    sys.path.insert(0, r'C:/Typhoon HIL Control Center/python_portable')
    sys.path.insert(0, r'C:/Typhoon HIL Control Center')
    import typhoon.api.hil_control_panel as cp
    from typhoon.api.schematic_editor import model
    import os

    cp.set_debug_level(level=1)
    cp.stop_simulation()

    model.get_hw_settings()
    if not model.load(r'D:/SVP/SVP 1.4.3 Directories 5-2-17/svp_energy_lab-loadsim/Lib/svpelab/Typhoon/ASGC.tse'):
        print("Model did not load!")

    if not model.compile():
        print("Model did not compile!")

    # first we need to load model
    cp.load_model(file=r'D:/SVP/SVP 1.4.3 Directories 5-2-17/svp_energy_lab-loadsim/Lib'
                        r'/svpelab/Typhoon/ASGC Target files/ASGC.cpd')

    # we could also open existing settings file...
    cp.load_settings_file(file=r'D:/SVP/SVP 1.4.3 Directories 5-2-17/svp_energy_lab-loadsim/Lib/'
                                r'svpelab/Typhoon/settings2.runx')

    # after setting parameter we could start simulation
    cp.start_simulation()

    # let the inverter startup
    sleeptime = 15
    for i in range(1, sleeptime):
        print(("Waiting another %d seconds until the inverter starts. Power = %f." %
               ((sleeptime-i), cp.read_analog_signal(name='Pdc'))))
        time.sleep(1)

    print(('Sources: %s' % cp.available_sources()))

    waveform_source_list = ['V_source_phase_A', 'V_source_phase_B', 'V_source_phase_C']

    for voltage in range(210, 250, 1):
        for wave in waveform_source_list:
            cp.prepare_source_sine_waveform(name=wave, rms=voltage)
        cp.update_sources(waveform_source_list, executeAt=None)

        time.sleep(2)

        v1 = float(cp.read_analog_signal(name='V( Vrms1 )'))
        v2 = float(cp.read_analog_signal(name='V( Vrms2 )'))
        v3 = float(cp.read_analog_signal(name='V( Vrms3 )'))

        # print('Voltage Target: %s, Voltages: %s' % (voltage, [v1, v2, v3]))
        print(('%s, %s, %s, %s, %s' % (voltage, voltage, v1, v2, v3)))
