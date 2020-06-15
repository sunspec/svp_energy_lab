"""
Copyright (c) 2017, Austrian Institute of Technology, Sandia National Labs and SunSpec Alliance
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
from collections import namedtuple
from . import grid_profiles
from . import gridsim

sps_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'SPS'
}

def gridsim_info():
    return sps_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = sps_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('v_nom'), label='EUT nominal voltage for all 3 phases', default=230.0)
    info.param(pname('v_max'), label='Max Voltage', default=270.0)
    info.param(pname('i_max'), label='Max Current', default=150.0)
    info.param(pname('freq'),  label='Frequency',   default=50.0)

    info.param(pname('comm'), label='Communications Interface', default='VISA',
               values=['Serial', 'GPIB', 'VISA'])

    info.param(pname('serial_port'), label='Serial Port',
               active=pname('comm'), active_value=['Serial'], default='com1')

    info.param(pname('gpib_bus_address'), label='GPIB Bus Address',
               active=pname('comm'), active_value=['GPIB'], default=6)
    info.param(pname('gpib_board'), label='GPIB Board Number',
               active=pname('comm'), active_value=['GPIB'], default=0)

    info.param(pname('visa_device'), label='VISA Device String', active=pname('comm'),
               active_value=['VISA'], default='GPIB0::6::INSTR')
    # info.param(pname('visa_path', label='VISA Module Path', active=pname('comm',
    #            active_value=['VISA'], default='C:\Python27\lib\site-packages', ptype=script.PTYPE_DIR)

GROUP_NAME = 'sps'


class GridSim(gridsim.GridSim):
    """
    Spitzenberger Spiess (SPS) grid simulation implementation.

    Valid parameters:
      mode - 'SPS'
      auto_config - ['Enabled', 'Disabled']
      v_nom
      v_max
      i_max
      freq
      profile_name
      serial_port
      gpib_bus_address
      gpib_board
      visa_device
      visa_path
    """

    def __init__(self, ts, group_name):
        self.rm = None      # Resource Manager for VISA
        self.conn = None    # Connection to instrument for VISA-GPIB

        self.dt_min = 0.02  # minimal delta t for amplitude pulses to avoid to fast amplitude changes
        self.ProfileEntry = namedtuple('ProfileEntry', 't v f ph')
        self.execution_time = 0.02
        self.eps = 0.01

        gridsim.GridSim.__init__(self, ts, group_name)

        self.v_nom_param = self._param_value('v_nom')
        self.v_max_param = self._param_value('v_max')
        self.i_max_param = self._param_value('i_max')
        self.freq_param = self._param_value('freq')
        self.profile_name = self._param_value('profile_name')
        self.comm = self._param_value('comm')
        self.serial_port = self._param_value('serial_port')

        self.gpib_bus_address = self._param_value('gpib_bus_address')
        self.gpib_board = self._param_value('gpib_board')

        self.visa_device = self._param_value('visa_device')
        self.visa_path = self._param_value('visa_path')

        self.open()  # open communications, not the relay
        self.profile_stop()

        if self.auto_config == 'Enabled':
            ts.log('Configuring the Grid Simulator.')
            self.config()   # sets the output voltage to v_nom

        state = self.relay()
        if state != gridsim.RELAY_CLOSED:
            if self.ts.confirm('Would you like to close the grid simulator relay and ENERGIZE the system?') is False:
                raise gridsim.GridSimError('Aborted grid simulation')
            else:
                self.ts.log('Turning on grid simulator.')
                self.relay(state=gridsim.RELAY_CLOSED)

        if self.profile_name is not None and self.profile_name != 'Manual':
            self.profile_load(self.v_nom_param, self.freq_param, self.profile_name)

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def info(self):
        """
        Returns the SCPI identification of the device
        :return: a string like "SPS SyCore V2.01.074"
        """

        return self._query('*IDN?')

    def _config_phase_angles(self):
        # set the phase angles for the 3 phases
        self._write('OSC:ANG 1,0')
        self._write('OSC:ANG 2,120')
        self._write('OSC:ANG 3,240')

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        self.ts.log('Grid simulator model: %s' % self.info().strip())

        # set the phase angles for the 3 phases
        self._config_phase_angles()

        # set voltage range
        v_max = self.v_max_param
        v1, v2, v3 = self.voltage_max()
        if v1 != v_max or v2 != v_max or v3 != v_max:
            self.voltage_max(v_max)
            v1, v2, v3 = self.voltage_max()
        self.ts.log('Grid sim max voltage settings: %.2fV' % v1)

        # set nominal voltage
        v_nom = self.v_nom_param
        v1, v2, v3 = self.voltage()
        if not (self._numeric_equal(v1, v_nom, self.eps) and self._numeric_equal(v2, v_nom, self.eps)
                and self._numeric_equal(v3, v_nom, self.eps)):
            # because of 229.995 equals 230 due to limited accuracy of SPS
            self.voltage(voltage=(v_nom, v_nom, v_nom))
            v1, v2, v3 = self.voltage()
        self.ts.log('Grid sim nominal voltage settings: %.2fV' % v1)

        # set max current if it's not already at gridsim_Imax
        i_max = self.i_max_param
        current = self.current_max()
        if i_max != max(current) and i_max != min(current):
            # TODO: discuss what to do, when max currents for single phases are not the same
            self.current_max(i_max)
            current = self.current_max(i_max)
        self.ts.log('Grid sim max current: %.2fA' % current[0])

        # set nominal frequency
        f_nom = self.freq_param
        f = self.freq()

        if not self._numeric_equal(f, f_nom, self.eps):  # f != f_nom:
            f = self.freq(f_nom)
        self.ts.log('Grid sim nominal frequency settings: %.2fHz' % f)

        # TODO: discuss what else should be configured here...
        # trigger angle, AMP mode (AC, DC)
        # current limitation mode, ...

    def open(self):
        """
        Open the communications resources associated with the grid simulator.
        """
        if self.comm == 'Serial':
            ''' Config according to th SyCore manual
                Baudrate:   9600 B/s
                Databit:    8
                Stopbit:    1
                Parity:     no
                Handshake:  none
                use CR at the end of a command
            '''
            raise NotImplementedError('The driver for serial connection (RS232/RS485) is not implemented yet. ' +
                                      'Please use VISA which supports also serial connection')
        elif self.comm == 'GPIB':
            raise NotImplementedError('The driver for plain GPIB is not implemented yet. ' +
                                      'Please use VISA which supports also GPIB devices')
        elif self.comm == 'VISA':
            try:
                # sys.path.append(os.path.normpath(self.visa_path))
                import visa
                self.rm = visa.ResourceManager()
                self.conn = self.rm.open_resource(self.visa_device)

                # the default pyvisa write termination is '\r\n' which does not work with the SPS
                self.conn.write_termination = '\n'

                self.ts.sleep(1)

            except Exception as e:
                raise gridsim.GridSimError('Cannot open VISA connection to %s\n\t%s' % (self.visa_device,str(e)))
        else:
            raise ValueError('Unknown communication type %s. Use Serial, GPIB or VISA' % self.comm)

    def close(self):
        """
        Close any open communications resources associated with the grid
        simulator.
        """

        if self.comm == 'Serial':
            raise NotImplementedError('The driver for serial connection (RS232/RS485) is not implemented yet')
        elif self.comm == 'GPIB':
            raise NotImplementedError('The driver for plain GPIB is not implemented yet.')
        elif self.comm == 'VISA':
            try:
                if self.rm is not None:
                    if self.conn is not None:
                        self.conn.close()
                    self.rm.close()

                self.ts.sleep(1)
            except Exception as e:
                raise gridsim.GridSimError(str(e))
        else:
            raise ValueError('Unknown communication type %s. Use Serial, GPIB or VISA' % self.comm)

    def current(self, current=None):
        """
        WARNING: the SPS cannot set the current, because it is only a voltage amplifier
        :param current: parameter just here because of base class. Anything != None will raise an Exception
        :return: Returns a measurement of the currents of the SPS

        """

        if current is not None:
            raise gridsim.GridSimError('SPS cannot set the current. Use this function only to get current measurements')
        else:
            # TODO: current measurements are not
            return [self._measure_current(1), self._measure_current(2), self._measure_current(3)]

    def current_max(self, current=None):
        """
        Set the value for max current if provided. If none provided, obtains
        the value for max current.
        :param current:
        :return:
        """

        if current is not None:
            i_max = self._create_3tuple(current)

            # activate current limitation
            self._write('curr:limitation:control 1')
            # set current limitation
            self._write('curr:limitation:level 1,%f' % i_max[0])
            self._write('curr:limitation:level 2,%f' % i_max[1])
            self._write('curr:limitation:level 3,%f' % i_max[2])

        else:
            i_max = [float(self._query('curr:limitation:level 1?')),
                     float(self._query('curr:limitation:level 2?')),
                     float(self._query('curr:limitation:level 3?'))]

        return i_max

    def freq(self, freq=None):
        """
        Set the value for frequency if provided. If none provided, obtains
        the value for frequency.

        :param freq: Frequency in Hertz as float
        """

        if freq is not None:
            self._write('OSC:FREQ %.2f' % freq)
        else:
            # measuring the frequency seems not to work. SPS only returns strange values
            # --> return the frequency set value instead
            freq = float(self._query('OSC:FREQ?'))

        return freq

    def profile_load(self, profile_name, v_step=100, f_step=100, t_step=None):
        """

        :param v_nom:
        :param freq_nom:
        :param profile_name:
        :param v_step:
        :param f_step:
        :param t_step:
        :return:
        """

        if profile_name is None:
            raise gridsim.GridSimError('Profile not specified')

        if profile_name == 'Manual':  # Manual reserved for not running a profile.
            self.ts.log_warning('Manual reserved for not running a profile')
            return

        v_nom = self.v_nom_param
        freq_nom = self.freq_param

        profile_entry = self.ProfileEntry    # t v f ph
        raw_profile = []
        profile = []
        dt_min = self.dt_min

        # for simple transient steps in voltage or frequency, use v_step, f_step, and t_step
        if profile_name is 'Transient_Step':
            if t_step is None:
                raise gridsim.GridSimError('Transient profile did not have a duration.')
            else:
                # (time offset in seconds, % nominal voltage, % nominal frequency)
                raw_profile.append(profile_entry(t=0, v=v_step, f=f_step, ph=123))
                raw_profile.append(profile_entry(t=t_step, v=v_step, f=f_step, ph=123))
                raw_profile.append(profile_entry(t=t_step, v=100, f=100, ph=123))
        else:
            # get the profile from grid_profiles
            input_profile = grid_profiles.profiles.get(profile_name)

            if input_profile is None:
                raise gridsim.GridSimError('Profile Not Found: %s' % profile_name)
            else:
                for entry in input_profile:
                    raw_profile.append(profile_entry(t=entry[0],
                                                     v=entry[1],
                                                     f=entry[2],
                                                     ph=123))

        if raw_profile[0].t == 0:
            first_dt = dt_min
            slew_rate_limited = True
        else:
            first_dt = raw_profile[0].t
            slew_rate_limited = False

        profile.append(profile_entry(t=first_dt,  # at least dt_min as rise time
                                     v=(raw_profile[0].v/100.0)*v_nom,
                                     f=(raw_profile[0].f/100.0)*freq_nom,
                                     ph=123))

        # TODO: possible bug: more than once a slew rate limitation --> time of sync for slew rate
        # possible solution: instead a bool-value, use a float for 'slew rate time offsync' that counts up and down
        for i in range(1, len(raw_profile)):
            dt = raw_profile[i].t - raw_profile[i-1].t
            if dt < self.dt_min:
                dt = self.dt_min
                slew_rate_limited = True
            else:
                if slew_rate_limited:   # limited slew rate the last change, so reduce the current duration by dt_min
                    dt -= self.dt_min
                    slew_rate_limited = False
                else:
                    pass

            profile.append(profile_entry(t=dt,
                                         v=(raw_profile[i].v/100.0)*v_nom,
                                         f=(raw_profile[i].f/100.0)*freq_nom,
                                         ph=123))

        self.profile = profile

    @staticmethod
    def _numeric_equal(x, y, eps):
        return abs(x-y) < eps

    def profile_start(self):
        """
        Start the loaded profile.
        """
        if self.profile is not None:
            self.ts.log('Starting profile: %s' % self.profile_name)
            prev_v = self.voltage()[0]
            prev_f = self.freq()

            for entry in self.profile:
                if not self._numeric_equal(prev_v, entry.v, self.eps):
                    if not self._numeric_equal(prev_f, entry.f, self.eps):
                        # change in voltage and frequency
                        self.ts.log('\tChange voltage from %0.1fV to %0.1fV and frequency from %0.1fHz to %0.1fHz in %0.2fs'
                              % (prev_v, entry.v, prev_f, entry.f, entry.t))
                        self.amplitude_frequency_ramp(amplitude_end_value=entry.v, end_frequency=entry.f,
                                                      ramp_time=entry.t, phases=entry.ph,
                                                      amplitude_start_value=prev_v, start_frequency=prev_f)
                    else:
                        # change in voltage
                        self.ts.log('\tChange voltage from %0.1fV to %0.1fV in %0.2fs' % (prev_v, entry.v, entry.t))
                        self.amplitude_ramp(end_value=entry.v, ramp_time=entry.t, phases=entry.ph, start_value=prev_v)

                elif not self._numeric_equal(prev_f, entry.f, self.eps):
                    # change in frequency
                    self.ts.log('\tChange frequency from %0.1fHz to %0.1fHz in %0.2fs' % (prev_f, entry.f, entry.t))
                    self.frequency_ramp(end_frequency=entry.f, ramp_time=entry.t, start_frequency=prev_f)

                else:
                    # wait, because no change in voltage or frequency
                    self.ts.log('\tWait %0.2fs' % entry.t)
                    self.ts.sleep(entry.t)

                prev_v = entry.v
                prev_f = entry.f

            self.ts.log('Finished profile')
        else:
            raise gridsim.GridSimError('You have to load a profile before starting it')

    def profile_stop(self):
        """
        Stop the running profile.
        """
        self.stop_command()
        # TODO: this will NOT stop the profile, but only the current ramp.
        # Also, at the moment the profile_start function will be executed until the profile is done

    def regen(self, state=None):
        """
        Set the state of the regen mode if provided. Valid states are: REGEN_ON,
        REGEN_OFF. If none is provided, obtains the state of the regen mode.
        :param state:
        :return:
        """
        if state == gridsim.REGEN_ON:
            # do nothing, because regen mode is always on
            pass
        elif state == gridsim.REGEN_OFF:
            raise gridsim.GridSimError('Cannot disable the regen mode. It is always ON for the SPS gridsim')
        elif state is None:
            state = gridsim.REGEN_ON    # Regeneration is always on for SPS
        else:
            raise gridsim.GridSimError('Unknown regen state: %s', state)

        return state

    def relay(self, state=None):
        """
        Set the state of the relay if provided. If none is provided, obtains the state of the relay.

        :param state: valid states are: RELAY_OPEN, RELAY_CLOSED
        """

        if state is not None:
            if state == gridsim.RELAY_OPEN:
                self._write('AMP:Output 0')
                self.ts.log('Opened Relay')
            elif state == gridsim.RELAY_CLOSED:
                self._write('AMP:Output 1')
                self.ts.log('Closed Relay')
            else:
                raise gridsim.GridSimError('Invalid relay state: %s' % state)
        else:
            state = int(self._query('AMP:Output?'))
            if state == 0:
                state = gridsim.RELAY_OPEN
            elif state == 1:
                state = gridsim.RELAY_CLOSED
            else:
                state = gridsim.RELAY_UNKNOWN
        return state

    def voltage(self, voltage=None):
        """
        Set the value for voltage phase 1 to 3 if provided. If none provided, obtains
        the set value for voltage. Voltage is a tuple containing a voltage value for
        each phase.

        :param voltage: Voltages in Volt as float
        """

        if voltage is not None:
            v = self._create_3tuple(voltage)

            # use ramp instead of setting voltages directly to limit slew rate
            if v[0] == v[1] == v[2]:
                # one ramp for all
                self.amplitude_ramp(v[0], self.dt_min, 123)
            else:
                # three consecutive ramps for each phase
                self.amplitude_ramp(v[0], self.dt_min, 1)
                self.amplitude_ramp(v[1], self.dt_min, 2)
                self.amplitude_ramp(v[2], self.dt_min, 3)
        else:
            # as discussed, return here the set value and not the measured voltage
            v = [self._get_voltage_set_value(1),
                 self._get_voltage_set_value(2),
                 self._get_voltage_set_value(3)]

        return v

    def voltage_max(self, voltage=None):
        """
        Set the value for max voltage if provided. If none provided, obtains
        the value for max voltage.
        :param voltage:
        :return:
        """

        if voltage is not None:
            # if voltage is a list or tuple, only take one value
            if type(voltage) is list or type(voltage) is tuple:
                voltage = float(max(voltage))

            if voltage <= 0:
                raise gridsim.GridSimError('Maximum Voltage must be greater than 0V')

            # get range values
            range_values = str(self._query('conf:amp:range?')).split(',')

            for i, rg in enumerate(range_values):
                self.ts.log_debug('Range is "%s"' % rg)
                self.ts.log_debug('rg[:-1] produces "%s"' % rg[:-1])
                self.ts.log_debug('rg[:-2] produces "%s"' % rg[:-2])
                value = float(rg[:-1])
                if voltage == value:
                    self._write('amp:range %i' % i)
                    return self._create_3tuple(voltage)

            # if code reaches this, the set value is not within the supported ranges
            raise gridsim.GridSimError(
                    'Invalid maximum voltage. SPS does not support %sV as maximum Voltage (Range)' % str(voltage))
        else:
            # return 270

            # get range
            act_range = int(self._query('amp:range?'))
            # get range values
            range_values = str(self._query('conf:amp:range?')).split(',')

            return self._create_3tuple(float(range_values[act_range - 1][:-1]))

    def i_max(self):
        return self.i_max_param

    def v_max(self):
        return self.v_max_param

    def v_nom(self):
        return self.v_nom_param

    def stop_command(self):
        """
        Stops the current command. Used to stop an amplitude pulse
        :return: None
        """

        self._write('BREAK')

    def setup_amplitude_pulse(self, start_value, pulse_value, end_value,
                              rise_time, duration, fall_time):
        """
        Times in seconds, 0-3600

        :param start_value:
        :param pulse_value:
        :param end_value:
        :param rise_time:
        :param duration:
        :param fall_time:
        :return:
        """

        # Amplitude values
        self._write('OSC:APuls:START %0.3fV' % start_value)
        self._write('OSC:APuls:PULS %0.3fV' % pulse_value)
        self._write('OSC:APuls:END %0.3fV' % end_value)

        # Times
        self._write('OSC:APuls:RISET %.3f' % rise_time)
        self._write('OSC:APuls:DURAT %.3f' % duration)
        self._write('OSC:APuls:FALLT %.3f' % fall_time)

    def start_amplitude_pulse(self, phases):
        """

        :param phases: string or int, 1,2,3,12,23,13, 123
        :return:
        """
        phases = self._phases2int(phases)
        self._write('OSC:APULS:GO %i' % phases)

    def start_amplitude_frequency_pulse(self, phases):
        """

        :param phases: string or int, 1,2,3,12,23,13, 123
        :return:
        """
        phases = self._phases2int(phases)
        self._write('OSC:AFPULS:GO %i' % phases)

    def amplitude_frequency_ramp(self, amplitude_end_value, end_frequency, ramp_time, phases,
                                 amplitude_start_value=None, start_frequency=None):

        self.amplitude_ramp(end_value=amplitude_end_value, ramp_time=ramp_time, phases=phases,
                            start_value=amplitude_start_value, start_ramp=False)
        self.frequency_ramp(end_frequency=end_frequency, ramp_time=ramp_time,
                            start_frequency=start_frequency, start_ramp=False)

        self.start_amplitude_frequency_pulse(phases)
        self.ts.sleep(max(0, ramp_time - 4 * self.execution_time))

    def amplitude_ramp(self, end_value, ramp_time, phases, start_value=None, start_ramp=True):
        """

        :param end_value:
        :param ramp_time:
        :param phases:
        :param start_value:
        :param start_ramp:
        :return:
        """

        """ equlas amplitude pulse with
         - start_value <-> current_value
         - pulse_value <-> end_value
         - end_value   <-> end_value
         - rise_time   <-> rise_time
         - duration    <-> 0
         - fall_time   <-> 0
        """

        phases = self._phases2int(phases)

        if start_value is None:
            if phases in (1, 2, 3):
                start_value = self._get_voltage_set_value(phases)
            elif phases in (12, 13, 123):
                # TODO: check if the phases have the same set value, if not, raise exception
                # by now, use value of phase 1 or 2
                start_value = self._get_voltage_set_value(1)
            elif phases == 23:
                start_value = self._get_voltage_set_value(2)
            else:
                raise ValueError('Invalid argument for phases: %i' % phases)

        self.setup_amplitude_pulse(start_value, end_value, end_value, ramp_time, 0, 0)

        if start_ramp:  # only start if start_ramp == True; False is needed for the AFPULS
            self.start_amplitude_pulse(phases)
            self.ts.sleep(max(0, ramp_time - 2 * self.execution_time))
        # TODO: improve timing accuracy by finding out the execution time

    def setup_frequency_pulse(self, start_frequency, pulse_frequency, end_frequency,
                              rise_time, duration, fall_time):
        """
        Times in seconds, 0-3600, Frequency in Hertz

        :param start_frequency:
        :param pulse_frequency:
        :param end_frequency:
        :param rise_time:
        :param duration:
        :param fall_time:
        :return:
        """

        # Frequency values
        self._write('OSC:FPuls:START %0.3f' % start_frequency)
        self._write('OSC:FPuls:PULS %0.3f' % pulse_frequency)
        self._write('OSC:FPuls:END %0.3f' % end_frequency)

        # Times
        self._write('OSC:FPuls:RISET %.3f' % rise_time)
        self._write('OSC:FPuls:DURAT %.3f' % duration)
        self._write('OSC:FPuls:FALLT %.3f' % fall_time)

    def start_frequency_pulse(self):
        """

        :return:
        """
        self._write('OSC:FPULS:GO')

    def frequency_ramp(self, end_frequency, ramp_time, start_frequency=None, start_ramp=True):
        if start_frequency is None:
            start_frequency = self.freq()

        self.setup_frequency_pulse(start_frequency, end_frequency, end_frequency, ramp_time, 0, 0)

        if start_ramp:  # only start if start_ramp == True; False is needed for the AFPULS
            self.start_frequency_pulse()
            self.ts.sleep(max(0, ramp_time - 2*self.execution_time))

    def _query(self, cmd_str):
        """
        Performs a SCPI query with the given cmd_str and returns the reply of the device
        :param cmd_str: the SCPI command which must be a valid command
        :return: the answer from the SPS
        """

        try:
            if self.conn is None:
                raise gridsim.GridSimError('GPIB connection not open')

            return self.conn.query(cmd_str).rstrip("\n\r")
        except Exception as e:
            raise gridsim.GridSimError(str(e))

    def _write(self, cmd_str):
        """
        Performs a SCPI write command with the given cmd_str
        :param cmd_str: the SCPI command which must be a valid command
        """
        try:
            if self.conn is None:
                raise gridsim.GridSimError('GPIB connection not open')

            num_written_bytes = self.conn.write(cmd_str)
            # TODO: check num_written_bytes to see if writing succeeded

            return num_written_bytes
        except Exception as e:
            raise gridsim.GridSimError(str(e))

    @staticmethod
    def _create_3tuple(value):
        """
        Checks whether value is a
        :param value:
        :return:
        """

        try:  # value is an array
            if len(value) == 1:
                return [value[0], value[0], value[0]]
            elif len(value) == 3:
                return [value[0], value[1], value[2]]
            else:
                raise ValueError('Value must be length 1 or 3')
        except (IndexError, TypeError):   # value is a scalar
            return [value, value, value]

    @staticmethod
    def _phases2int(phases):
        if isinstance(phases, (str, float)):
            try:
                phases = int(phases)  # "12" --> 12

            except ValueError:
                raise ValueError('String %s for phases has to represent a valid int' % phases)
        return phases

    def _measure_value(self, phase, what):
        """
        Returns a measurement value from the SPS
        :param phase: which phase, from 1 to 3
        :param what: which entity according to SPS manual. Currently supported: 'VOLT', 'CURR', 'S'
        :return: the measured value as float
        """

        phase = int(float(phase))  # convert if string '1' or 1.0 instead of int 1
        if phase < 1 or phase > 3:
            raise ValueError('Phase must be between 1 and 3')
        else:
            suffix = {'VOLT': -2, 'CURR': -2, 'S': -3}
            if what in list(suffix.keys()):
                self._write('CONF:MEAS:PH %i' % phase)
                value = self._query('MEAS:' + what + '?')
                # query returns the unit + '\n' which has to be removed before converting to float
                return float(value[:suffix[what]])
            else:
                raise ValueError('A query for the measurement of ' + what + ' is not possible or not implemented yet')

    def _measure_current(self, phase):
        """
        Measures the current of the given phase
        :param phase: which phase, from 1 to 3
        :return: the current in A as float
        """
        return self._measure_value(phase, 'CURR')

    def _measure_apparent_power(self, phase):
        """
        Measures the apparent power of the given phase
        :param phase: which phase, int from 1 to 3
        :return: the apparent power in VA as float
        """
        return self._measure_value(phase, 'S')

    def _measure_voltage(self, phase):
        """
        Measures the voltage of the given phase
        :param phase: which phase, int from 1 to 3
        :return: the voltage in V as float
        """
        return self._measure_value(phase, 'VOLT')

    def _get_voltage_set_value(self, phase):
        """

        :param phase:
        :return:
        """
        return float(self._query('OSC:AMP %i?' % phase))

if __name__ == "__main__":
    pass
