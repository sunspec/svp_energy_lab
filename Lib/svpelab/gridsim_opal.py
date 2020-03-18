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

opal_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Opal'
}


def gridsim_info():
    return opal_info


def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = opal_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('v_nom'), label='EUT nominal voltage for all 3 phases (V)', default=277.2)
    info.param(pname('f_nom'), label='EUT nominal frequency', default=60.)
    info.param(pname('p_nom'), label='EUT nominal power (W)', default=34000.)

    info.param(pname('freq_params'), label='Frequency Block Names in Opal',
               default="Frequency Phase A, Frequency Phase B, Frequency Phase C")
    info.param(pname('volt_params'), label='Voltage Block Names in Opal',
               default="Voltage RMS Phase A, Voltage RMS Phase B, Voltage RMS Phase C")

GROUP_NAME = 'opal'


class GridSim(gridsim.GridSim):
    """
    Opal grid simulation implementation.

    Valid parameters:
      mode - 'Opal'
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

        # for asymmetric voltage tests
        self.v1 = self.v_nom
        self.v2 = self.v_nom
        self.v3 = self.v_nom

        self.f_nom = self._param_value('f_nom')
        self.f = self.f_nom

        # To be populated using config()
        self.hil_object = None
        self.model_name = None
        self.rt_lab_model_dir = None

        try:
            tempstring = self._param_value('freq_params').strip().split(',')
            self.frequency_block_list = [entry.rstrip(' ').lstrip(' ') for entry in tempstring]
            tempstring = self._param_value('volt_params').strip().split(',')
            self.voltage_block_list = [entry.rstrip(' ').lstrip(' ') for entry in tempstring]
        except Exception as e:
            ts.log("Failed freq or voltage block names: %s" % e)
            raise e

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self, hil_object=None):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        if hil_object is None:
            gridsim.GridSimError('GridSim config requires a Opal HIL object')
        else:
            self.model_name = hil_object.rt_lab_model
            self.rt_lab_model_dir = hil_object.rt_lab_model_dir

        self.config_phase_angles()
        self.freq(freq=self.f_nom)
        self.voltage(voltage=self.v_nom)

    def set_parameters(self, parameters):
        """
        Sets the parameters in the RT-Lab Model

        :param parameters: tuple of (parameter, value) pairs
        :return: None
        """

        for p, v in parameters:
            self.ts.log_debug('Setting %s = %s' % (p, v))
            self.hil_object.set_params(p, v)

    def config_phase_angles(self):
        """
        Set the phase angles for the simulation

        :return: None
        """

        parameters = []
        # set the phase angles for the 3 phases
        if len(self.frequency_block_list) == 1:  # single phase
            # Phase A Switching times and Phase Angles
            parameters.append((self.model_name + '/SM_Source/Switch1/Threshold', 1e10))  # never conduct phase jump
            parameters.append((self.model_name + '/SM_Source/Switch2/Threshold', 1e10))  # never conduct phase jump
            parameters.append((self.model_name + '/SM_Source/Phase Angle Phase A0/Value', 0))
            parameters.append((self.model_name + '/SM_Source/Phase Angle Phase A1/Value', 0))
        elif len(self.frequency_block_list) == 2:  # split phase
            # Phase A Switching times and Phase Angles
            parameters.append((self.model_name + '/SM_Source/Switch1/Threshold', 1e10))  # never conduct phase jump
            parameters.append((self.model_name + '/SM_Source/Switch2/Threshold', 1e10))  # never conduct phase jump
            parameters.append((self.model_name + '/SM_Source/Phase Angle Phase A0/Value', 0))
            parameters.append((self.model_name + '/SM_Source/Phase Angle Phase A1/Value', 0))
            # Phase B Switching times and Phase Angles
            parameters.append((self.model_name + '/SM_Source/Switch3/Threshold', 1e10))  # never conduct phase jump
            parameters.append((self.model_name + '/SM_Source/Switch4/Threshold', 1e10))  # never conduct phase jump
            parameters.append((self.model_name + '/SM_Source/Phase Angle Phase B0/Value', 180))
            parameters.append((self.model_name + '/SM_Source/Phase Angle Phase B1/Value', 180))
        elif len(self.frequency_block_list) == 3:  # three phase
            # Phase A Switching times and Phase Angles
            parameters.append((self.model_name + '/SM_Source/Switch1/Threshold', 1e10))  # never conduct phase jump
            parameters.append((self.model_name + '/SM_Source/Switch2/Threshold', 1e10))  # never conduct phase jump
            parameters.append((self.model_name + '/SM_Source/Phase Angle Phase A0/Value', 0))
            parameters.append((self.model_name + '/SM_Source/Phase Angle Phase A1/Value', 0))
            # Phase B Switching times and Phase Angles
            parameters.append((self.model_name + '/SM_Source/Switch3/Threshold', 1e10))  # never conduct phase jump
            parameters.append((self.model_name + '/SM_Source/Switch4/Threshold', 1e10))  # never conduct phase jump
            parameters.append((self.model_name + '/SM_Source/Phase Angle Phase B0/Value', -120))
            parameters.append((self.model_name + '/SM_Source/Phase Angle Phase B1/Value', -120))
            # Phase C Switching times and Phase Angles
            parameters.append((self.model_name + '/SM_Source/Switch7/Threshold', 1e10))  # never conduct phase jump
            parameters.append((self.model_name + '/SM_Source/Switch8/Threshold', 1e10))  # never conduct phase jump
            parameters.append((self.model_name + '/SM_Source/Phase Angle Phase C0/Value', 120))
            parameters.append((self.model_name + '/SM_Source/Phase Angle Phase C1/Value', 120))
        else:
            self.ts.log_warning('Phase angles not set for simulation because the number of grid simulation '
                                'waveforms is not 1, 2, or 3.')

        self.set_parameters(parameters)

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

        :param freq: float value of frequency (to set freq), None to read freq
        :return: frequency
        """
        if freq is not None:
            self.f = freq
            parameters = []
            for freq_block in self.frequency_block_list:
                parameters.append((self.model_name + '/SM_Source/' + freq_block + '/Value', freq))

        freq = self.f
        return freq

    def profile_load(self, profile_name=None, v_step=100, f_step=100, t_step=None, profile=None):
        pass

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
        Set the value for voltage if provided. If none provided, obtains the value for voltage.

        :param voltage: tuple of floats for voltages (to set voltage), None to read voltage
        :return: tuple of voltages
        """
        if voltage is not None:
            # single value case (not tuple voltages)
            parameters = []
            if type(voltage) is not list and type(voltage) is not tuple:
                self.v = voltage
                # self.ts.log_debug('        Setting Typhoon AC voltage to %s' % self.v)
                for volt_block in self.voltage_block_list:
                    # self.ts.log_debug('Source: %s set to %s V.' % (wave, self.v))
                    parameters.append((self.model_name + '/SM_Source/' + volt_block + '/Value', voltage))
                self.v1 = self.v
                self.v2 = self.v
                self.v3 = self.v

            else:
                phase = 0
                v_sum = 0
                for volt_block in self.voltage_block_list:
                    phase += 1
                    v_sum += voltage[phase - 1]
                    eval('self.v%d = voltage[phase - 1]' % phase)
                    parameters.append((self.model_name + '/SM_Source/' + volt_block + '/Value', voltage[phase-1]))
                self.v = v_sum/phase

            # write the new voltages to the simulation blocks
            self.set_parameters(parameters)

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

    def i_max(self):
        return self.v/self.p_nom

    def v_max(self):
        return self.v

    def v_nom(self):
        return self.v_nom

    def meas_voltage(self, ph_list=(1, 2, 3)):
        return self.v1, self.v2, self.v3

    def meas_current(self, ph_list=(1, 2, 3)):
        # for use during anti-islanding testing to determine the current to the utility
        return None, None, None


if __name__ == "__main__":
    pass
