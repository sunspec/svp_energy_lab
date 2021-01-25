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
import math as m
import pandas as pd
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
                     active=gname('mode'), active_value=mode, glob=True)
    info.param(pname('phases'), label='Phases', default=1, values=[1, 2, 3])
    info.param(pname('v_nom'), label='Nominal voltage for all phases', default=120.0)
    info.param(pname('freq'), label='Frequency', default=60.0)

    info.param(pname('v_max'), label='Max Voltage', default=300.0)
    info.param(pname('f_max'), label='Max Frequency', default=70.0)
    info.param(pname('f_min'), label='Min Frequency', default=45.0)


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

    def __init__(self, ts, group_name, support_interfaces=None):
        gridsim.GridSim.__init__(self, ts, group_name, support_interfaces=support_interfaces)

        self.ts = ts
        self.p_nom = self._param_value('p_nom')
        self.v_nom = self._param_value('v_nom')
        self.v = self.v_nom

        # for asymmetric voltage tests
        self.v1 = self.v_nom
        self.v2 = self.v_nom
        self.v3 = self.v_nom

        self.f_nom = self._param_value('freq')
        self.phases = self._param_value('phases')

        self.v_max = self._param_value('v_max')
        self.f_max = self._param_value('f_max')
        self.f_min = self._param_value('f_min')

        # Hil configuration
        if self.hil is None:
            gridsim.GridSimError('GridSim config requires a Opal HIL object')
        else:
            self.ts.log_debug(f'Configuring gridsim with Opal hil parameters...using {self.hil.info()}')
            self.ts.log_debug(f'hil object : {self.hil}')
            self.model_name = self.hil.rt_lab_model
            self.rt_lab_model_dir = self.hil.rt_lab_model_dir

        if self.auto_config == 'Enabled':
            ts.log('Configuring the Grid Simulator.')
            self.config()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def gridsim_info(self):
        return opal_info

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        self.ts.log('Configuring phase angles, frequencies, and voltages for gridsim')
        self.config_phase_angles()
        self.freq(freq=self.f_nom)
        self.voltage(voltage=self.v_nom)

        # Saturation at the waveform level
        self.frequency_max(frequency=self.f_max)
        self.frequency_min(frequency=self.f_min)
        self.voltage_max(voltage=self.v_max)
        self.voltage_min(voltage=0.0)

    def config_phase_angles(self):

        """
        Set the phase angles for the simulation

        :return: None
        """

        parameters = []
        # set the phase angles for the 3 phases
        if self.phases == 1:
            parameters.append(("PHASE_PHA", 0))

        elif self.phases == 2:
            parameters.append(("PHASE_PHA", 0))
            parameters.append(("PHASE_PHB", 180))

        elif self.phases == 3:
            parameters.append(("PHASE_PHA", 0))
            parameters.append(("PHASE_PHB", -120))
            parameters.append(("PHASE_PHC", 120))

        else:
            raise gridsim.GridSimError('Unsupported phase parameter: %s' % self.phases)
        self.hil.set_matlab_variables(parameters)
        parameters = []
        parameters = self.hil.get_matlab_variables(["PHASE_PHA", "PHASE_PHB", "PHASE_PHC"])

        return parameters

    def config_asymmetric_phase_angles(self, mag=None, angle=None):
        """
        :param mag: list of voltages for the imbalanced test, e.g., [277.2, 277.2, 277.2]
        :param angle: list of phase angles for the imbalanced test, e.g., [0, 120, -120]
        :returns: voltage list and phase list
        """
        parameters = []
        i = 0
        # TODO : To be replace by sending a matlab variable list, else this code might create problems (current on neutral, etc.)
        for volt_block in self.voltage_block_list:
            # self.ts.log_debug('self.model_name = %s' % (self.model_name))
            # self.ts.log_debug('volt_block = %s' % (volt_block))
            parameters.append((self.model_name + '/SM_Source/SVP Commands/' + volt_block + '/Value', mag[i]))
            i = i + 1
            # Phase A Switching times and Phase Angles
        parameters.append((self.model_name + '/SM_Source/SVP Commands/phase_ph_a/Value', angle[0]))
        # Phase B Switching times and Phase Angles
        parameters.append((self.model_name + '/SM_Source/SVP Commands/phase_ph_b/Value', angle[1]))
        # Phase C Switching times and Phase Angles
        parameters.append((self.model_name + '/SM_Source/SVP Commands/phase_ph_c/Value', angle[2]))


        self.hil.set_parameters(parameters)

        return None, None

    def current(self, current=None):
        """
        Set the value for current if provided. If none provided, obtains
        the value for current.
        """
        return self.v / self.p_nom

    def current_max(self, current=None):
        """
        Set the value for max current if provided. If none provided, obtains
        the value for max current.
        """
        return self.v / self.p_nom

    def freq(self, freq):
        """
        Set the value for frequency if provided. If none provided, obtains
        the value for frequency.

        :param freq: float value of frequency (to set freq), None to read freq
        :return: frequency
        """
        if freq is not None:
            parameters = []
            parameters.append(("FREQUENCY", freq))
            self.hil.set_matlab_variables(parameters)
            parameters = []
            parameters = self.hil.get_matlab_variables(["FREQUENCY"])
            return parameters
        else:
            pass

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

    def rocof(self, param=None):
        """
        Set the rate of change of frequency (ROCOF) if provided. If none provided, obtains the ROCOF.
        :param : "ROCOF_ENABLE" is to enable (1) or disable (0). Default value 0
        :param : "ROCOF_VALUE" is for ROCOF in Hz/s. Default value 3
        :param : "ROCOF_INIT" is for ROCOF initialisation value. Default value 60
        """

        if param is not None:
            parameters = []
            parameters.append(("ROCOF_ENABLE", param["ROCOF_ENABLE"]))
            parameters.append(("ROCOF_VALUE", param["ROCOF_VALUE"]))
            parameters.append(("ROCOF_INIT", param["ROCOF_INIT"]))
            
        self.hil.set_matlab_variables(parameters)
        parameters = []
        parameters = self.hil.get_matlab_variables(["ROCOF_ENABLE", "ROCOF_VALUE", "ROCOF_INIT"])
        return parameters

    def rocom(self, param=None):
        """
        Set the rate of change of magnitude (ROCOM) if provided. If none provided, obtains the ROCOM.
        :param : "ROCOM_ENABLE" is to enable (1) or disable (0). Default value 0
        :param : "ROCOM_VALUE" is for ROCOF in V/s. Default value 3
        :param : "ROCOM_INIT" is for ROCOF initialisation value. Default value 60
        :param : "ROCOM_START_TIME" is for ROCOF initialisation value. Default value 60
        :param : "ROCOM_END_TIME" is for ROCOF initialisation value. Default value 60


        if param is not None:
            parameters = []
            parameters.append(("ROCOF_ENABLE", param["ROCOF_ENABLE"]))
            parameters.append(("ROCOF_VALUE", param["ROCOF_VALUE"]))
            parameters.append(("ROCOF_INIT", param["ROCOF_INIT"]))
            parameters.append(("ROCOM_START_TIME", param["ROCOM_START_TIME"]))
            parameters.append(("ROCOM_END_TIME", param["ROCOM_END_TIME"]))
            
        self.hil.set_matlab_variables(parameters)
        parameters = []
        parameters = self.hil.get_matlab_variables(["ROCOF_ENABLE", "ROCOF_VALUE", "ROCOF_INIT", "ROCOM_START_TIME",
                                                    "ROCOM_END_TIME"])
        return parameters

    def voltage(self, voltage=None):
        """
        Set the value for voltage if provided. If none provided, obtains the value for voltage.

        :param voltage: tuple of floats for voltages (to set voltage), None to read voltage
        :return: tuple of voltages
        """  
        parameters = []

        if voltage is not None and type(voltage) is not list:
            # single value case (not tuple voltages)
            voltage /= self.v_nom
            parameters = []
            # set the phase angles for the 3 phases
            if self.phases == 1:
                parameters.append(("VOLT_PHA", voltage))
                parameters.append(("VOLT_PHB", 0))
                parameters.append(("VOLT_PHC", 0))

            elif self.phases == 2:
                parameters.append(("VOLT_PHA", voltage))
                parameters.append(("VOLT_PHB", voltage))
                parameters.append(("VOLT_PHC", 0))

            elif self.phases == 3:
                parameters.append(("VOLT_PHA", voltage))
                parameters.append(("VOLT_PHB", voltage))
                parameters.append(("VOLT_PHC", voltage))


            else:
                raise gridsim.GridSimError('Unsupported voltage parameter: %s' % voltage)
        elif voltage is not None and type(voltage) is list and len(voltage) == 3:
            # This consider the list contains three elements
            # set the phase angles for the 3 phases
            parameters.append(("VOLT_PHA", voltage[0]))
            parameters.append(("VOLT_PHB", voltage[1]))
            parameters.append(("VOLT_PHC", voltage[2]))

        self.hil.set_matlab_variables(parameters)
        parameters = []
        parameters = self.hil.get_matlab_variables(["VOLT_PHA", "VOLT_PHB", "VOLT_PHC"])


        return parameters

    def voltage_max(self, voltage=None):
        """
        Set the value for max voltage if provided. If none provided, obtains
        the value for max voltage.
        """
        parameters = []
        parameters.append(("VOLTAGE_MAX_LIMIT", voltage / self.v_nom))
        self.hil.set_matlab_variables(parameters)
        parameters = []
        parameters = self.hil.get_matlab_variables(["VOLTAGE_MAX_LIMIT"])

        return parameters

    def voltage_min(self, voltage=None):
        """
        Set the value for min voltage if provided. If none provided, obtains
        the value for min voltage.
        """
        parameters = []
        # This is hard coded because the Grid simulator should be permitted to go as low as "0"
        parameters.append(("VOLTAGE_MIN_LIMIT", 0.0))
        self.hil.set_matlab_variables(parameters)
        parameters = []
        parameters = self.hil.get_matlab_variables(["VOLTAGE_MIN_LIMIT"])

        return parameters

    def frequency_max(self, frequency=None):
        """
        Set the value for max frequency if provided. If none provided, obtains
        the value for max frequency.
        """
        parameters = []
        parameters.append(("FREQUENCY_MAX_LIMIT", frequency))
        self.hil.set_matlab_variables(parameters)
        parameters = []
        parameters = self.hil.get_matlab_variables(["FREQUENCY_MAX_LIMIT"])

        return parameters

    def frequency_min(self, frequency=None):
        """
        Set the value for min frequency if provided. If none provided, obtains
        the value for min frequency.
        """
        parameters = []
        parameters.append(("FREQUENCY_MIN_LIMIT", frequency))
        self.hil.set_matlab_variables(parameters)
        parameters = []
        parameters = self.hil.get_matlab_variables(["FREQUENCY_MIN_LIMIT"])

        return parameters

    def i_max(self):
        return self.v / self.p_nom

    def v_nom(self):
        return self.v_nom

    def meas_voltage(self, ph_list=(1, 2, 3)):
        return self.v1, self.v2, self.v3

    def meas_current(self, ph_list=(1, 2, 3)):
        # for use during anti-islanding testing to determine the current to the utility
        return None, None, None


if __name__ == "__main__":
    pass
