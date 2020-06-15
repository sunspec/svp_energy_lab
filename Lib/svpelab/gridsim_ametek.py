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
import time
import socket
import serial
from . import grid_profiles
from . import gridsim

ametek_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Ametek'
}

def gridsim_info():
    return ametek_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = ametek_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('phases'), label='Phases', default=1, values=[1, 2, 3])
    info.param(pname('v_nom'), label='Nominal voltage for all phases', default=277.2)
    info.param(pname('v_max'), label='Max Voltage', default=300.0)
    info.param(pname('i_max'), label='Max Current', default=100.0)
    info.param(pname('freq'), label='Frequency', default=60.0)
    info.param(pname('comm'), label='Communications Interface', default='Serial', values=['Serial', 'TCP/IP'])
    info.param(pname('serial_port'), label='Serial Port',
               active=pname('comm'),  active_value=['Serial'], default='com1')
    info.param(pname('ip_addr'), label='IP Address',
               active=pname('comm'),  active_value=['TCP/IP'], default='192.168.1.10')
    info.param(pname('ip_port'), label='IP Port',
               active=pname('comm'),  active_value=['TCP/IP'], default=5025)


GROUP_NAME = 'ametek'


class GridSim(gridsim.GridSim):
    """
    Ametek grid simulation implementation.

    Valid parameters:
      mode - 'Ametek'
      auto_config - ['Enabled', 'Disabled']
      v_nom
      v_max
      i_max
      freq
      profile_name
      serial_port
      baudrate
      timeout
      write_timeout
      ip_addr
      ip_port
    """
    def __init__(self, ts, group_name):
        self.buffer_size = 1024
        self.conn = None

        gridsim.GridSim.__init__(self, ts, group_name)

        self.phases_param = self._param_value('phases')
        self.v_nom_param = float(self._param_value('v_nom'))
        self.v_max_param = self._param_value('v_max')
        self.i_max_param = self._param_value('i_max')
        self.freq_param = self._param_value('freq')
        self.comm = self._param_value('comm')
        self.serial_port = self._param_value('serial_port')
        self.ipaddr = self._param_value('ip_addr')
        self.ipport = self._param_value('ip_port')
        self.baudrate = 115200
        self.timeout = 5
        self.write_timeout = 2
        self.cmd_str = ''
        self._cmd = None
        self._query = None
        self.profile_name = ts.param_value('profile.profile_name')

        if self.comm == 'Serial':
            self.open()  # open communications
            self._cmd = self.cmd_serial
            self._query = self.query_serial
        elif self.comm == 'TCP/IP':
            self._cmd = self.cmd_tcp
            self._query = self.query_tcp

        self.cmd('*CLS\n')
        # self.cmd('*RST\n')  # Reset the entire system
        self.profile_stop()

        if self.auto_config == 'Enabled':
            ts.log('Configuring the Grid Simulator.')
            self.config()

        state = self.relay()
        if state != gridsim.RELAY_CLOSED:
            if self.ts.confirm('Would you like to close the grid simulator relay and ENERGIZE the system?') is False:
                raise gridsim.GridSimError('Aborted grid simulation')
            else:
                self.ts.log('Turning on grid simulator.')
                self.relay(state=gridsim.RELAY_CLOSED)

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def cmd_serial(self, cmd_str):
        self.cmd_str = cmd_str
        try:
            if self.conn is None:
                raise gridsim.GridSimError('Communications port not open')

            self.conn.flushInput()
            self.conn.write(cmd_str)
        except Exception as e:
             raise gridsim.GridSimError(str(e))

    def query_serial(self, cmd_str):
        resp = ''
        more_data = True

        self.cmd_serial(cmd_str)

        while more_data:
            try:
                count = self.conn.inWaiting()
                if count < 1:
                    count = 1
                data = self.conn.read(count)
                if len(data) > 0:
                    for d in data:
                        resp += d
                        if d == '\n':
                            more_data = False
                            break
                else:
                    raise gridsim.GridSimError('Timeout waiting for response')
            except gridsim.GridSimError:
                raise
            except Exception as e:
                raise gridsim.GridSimError('Timeout waiting for response - More data problem')

        return resp

    def cmd_tcp(self, cmd_str):
        try:
            if self.conn is None:
                self.ts.log('ipaddr = %s  ipport = %s' % (self.ipaddr, self.ipport))
                self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.conn.settimeout(self.timeout)
                self.conn.connect((self.ipaddr, self.ipport))

            # print 'cmd> %s' % (cmd_str)
            self.conn.send(cmd_str)
        except Exception as e:
            raise gridsim.GridSimError(str(e))

    def query_tcp(self, cmd_str):
        resp = ''
        more_data = True

        self._cmd(cmd_str)

        while more_data:
            try:
                data = self.conn.recv(self.buffer_size)
                if len(data) > 0:
                    for d in data:
                        resp += d
                        if d == '\n': #\r
                            more_data = False
                            break
            except Exception as e:
                raise gridsim.GridSimError('Timeout waiting for response')

        return resp

    def cmd(self, cmd_str):
        self.cmd_str = cmd_str
        try:
            self._cmd(cmd_str)
            resp = self._query('SYSTem:ERRor?\n') #\r

            if len(resp) > 0:
                if resp[0] != '0':
                    raise gridsim.GridSimError(resp + ' ' + self.cmd_str)
        except Exception as e:
            raise gridsim.GridSimError(str(e))

    def query(self, cmd_str):
        try:
            resp = self._query(cmd_str).strip()
        except Exception as e:
            raise gridsim.GridSimError(str(e))

        return resp

    def info(self):
        return self.query('*IDN?\n')

    def config_phase_angles(self, config=False):
        if config:
            if self.phases_param == 1:
                self.cmd('inst:coup none;:inst:nsel 1;:phas 0.0\n')
                self.cmd('inst:coup none;:inst:nsel 1;:phas 0.0\n')
                self.cmd('inst:coup none;:inst:nsel 2;:phas 180.0\n')
                self.cmd('inst:coup none;:inst:nsel 2;:phas 180.0\n')
                self.cmd('inst:coup none;:inst:nsel 1;:func sin\n')
                self.cmd('inst:coup none;:inst:nsel 2;:func sin\n')
            elif self.phases_param == 3:
                # set the phase angles for the 3 phases
                self.cmd('inst:coup none;:inst:nsel 1;:phas 0.0\n')
                self.cmd('inst:coup none;:inst:nsel 1;:phas 0.0\n')
                self.cmd('inst:coup none;:inst:nsel 2;:phas 120.0\n')
                self.cmd('inst:coup none;:inst:nsel 2;:phas 120.0\n')
                self.cmd('inst:coup none;:inst:nsel 3;:phas 240.0\n')
                self.cmd('inst:coup none;:inst:nsel 3;:phas 240.0\n')
                self.cmd('inst:coup none;:inst:nsel 1;:func sin\n')
                self.cmd('inst:coup none;:inst:nsel 2;:func sin\n')
                self.cmd('inst:coup none;:inst:nsel 3;:func sin\n')
            elif self.phases_param == 2:
                # set the phase angles for the 2 phases
                self.cmd('inst:coup none;:inst:nsel 1;:phas 0.0\n')
                self.cmd('inst:coup none;:inst:nsel 1;:phas 0.0\n')
                self.cmd('inst:coup none;:inst:nsel 2;:phas 180.0\n')
                self.cmd('inst:coup none;:inst:nsel 2;:phas 180.0\n')
                self.cmd('inst:coup none;:inst:nsel 3;:phas 0.0\n')
                self.cmd('inst:coup none;:inst:nsel 3;:phas 0.0\n')
                self.cmd('inst:coup none;:inst:nsel 1;:func sin\n')
                self.cmd('inst:coup none;:inst:nsel 2;:func sin\n')
                self.cmd('inst:coup none;:inst:nsel 3;:func sin\n')
            else:
                raise gridsim.GridSimError('Unsupported phase parameter: %s' % (self.phases_param))

        ph1 = float(self.query('inst:coup none;:inst:nsel 1;:phas?\n'))
        ph2 = float(self.query('inst:coup none;:inst:nsel 2;:phas?\n'))
        ph3 = float(self.query('inst:coup none;:inst:nsel 3;:phas?\n'))
        return ph1, ph2, ph3

    def config_asymmetric_phase_angles(self, mag=None, angle=None):
        """
        :param mag: list of voltages for the imbalanced test, e.g., [277.2, 277.2, 277.2]
        :param angle: list of phase angles for the imbalanced test, e.g., [0, 120, -120]

        :returns: voltage list and phase list
        """
        voltages = []
        phases = []

        if mag is not None:
            if type(mag) is not list:
                raise gridsim.GridSimError('Waveform magnitudes were not provided as list. "mag" type: %s' % type(mag))

        if angle is not None:
            if type(angle) is list:
                if angle[2] < 0:  # make positive for Ametek
                    angle[2] += 360.
                self.cmd('inst:coup none;:inst:nsel 1;:phas %0.1f;:volt:ac %0.1f;'
                         ':inst:coup none;:inst:nsel 2;:phas %0.1f;:volt:ac %0.1f;'
                         ':inst:coup none;:inst:nsel 3;:phas %0.1f;:volt:ac %0.1f\n' % (angle[0], mag[0], angle[1],
                                                                                       mag[1], angle[2], mag[2]))

                # get phase and voltage measurements to return
                phases = self.config_phase_angles()
                voltages = self.voltage()
            else:
                raise gridsim.GridSimError('Waveform angles were not provided as list.')

        return voltages, phases

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        self.ts.log('Grid simulator model: %s' % self.info().strip())

        # put simulator in regenerative mode
        state = self.regen()
        if state != gridsim.REGEN_ON:
            if self.relay() == gridsim.RELAY_CLOSED:
                self.relay(state=gridsim.RELAY_OPEN)
            state = self.regen(gridsim.REGEN_ON)
        self.ts.log('Grid sim regenerative mode is: %s' % state)

        # set frequency
        self.freq(self.freq_param)

        # set the phase angles for the active phases
        ph1, ph2, ph3 = self.config_phase_angles(config=True)
        self.ts.log('Grid sim phase angles are: phase1 = %s, phase2 = %s, phase3 = %s' % (ph1, ph2, ph3))

        # set voltage range
        v_max = self.v_max_param
        v1, v2, v3 = self.voltage_max()
        if v1 != v_max or v2 != v_max or v3 != v_max:
            self.voltage_max(voltage=(v_max, v_max, v_max))
            v1, v2, v3 = self.voltage_max()
        self.ts.log('Grid sim max voltage settings: v1 = %s, v2 = %s, v3 = %s' % (v1, v2, v3))

        # set nominal voltage
        v_nom = self.v_nom_param
        v1, v2, v3 = self.voltage()
        if v1 != v_nom or v2 != v_nom or v3 != v_nom:
            self.voltage(voltage=(v_nom, v_nom, v_nom))
            v1, v2, v3 = self.voltage()
        self.ts.log('Grid sim nominal voltage settings: v1 = %s, v2 = %s, v3 = %s' % (v1, v2, v3))

        # set max current if it's not already at gridsim_Imax
        i_max = self.i_max_param
        current = self.current()
        if current != i_max:
            self.current(i_max)
            current = self.current()
        self.ts.log('Grid sim max current: %s Amps' % current)

    def open(self):
        """
        Open the communications resources associated with the grid simulator.
        """
        try:
            self.conn = serial.Serial(port=self.serial_port, baudrate=self.baudrate, bytesize=8, stopbits=1, xonxoff=0,
                                      timeout=self.timeout, writeTimeout=self.write_timeout)
            time.sleep(2)
        except Exception as e:
            raise gridsim.GridSimError(str(e))

    def close(self):
        """
        Close any open communications resources associated with the grid
        simulator.
        """
        if self.conn:
            self.conn.close()

    def current(self, current=None):
        """
        Set the value for current if provided. If none provided, obtains
        the value for current.
        """
        if current is not None:
            self.cmd('inst:coup all;:curr %0.2f\n' % current)
        curr_str = self.query('inst:nsel 1;:curr?\n')
        return float(curr_str[:-1])

    def current_max(self, current=None):
        """
        Set the value for max current if provided. If none provided, obtains
        the value for max current.
        """
        if current is not None:
            self.cmd('inst:coup all;:curr %0.2f\n' % current)
        curr_str = self.query('inst:nsel 1;:curr? max\n')
        return float(curr_str[:-1])

    def freq(self, freq=None):
        """
        Set the value for frequency if provided. If none provided, obtains
        the value for frequency.
        """
        if freq is not None:
            self.cmd('freq %0.2f\n' % freq)
        freq = self.query('freq?\n')
        return freq

    def profile_load(self, profile_name=None, v_step=100, f_step=100, t_step=None, profile=None):
        v_nom = self.v_nom_param
        freq_nom = self.freq_param

        if profile is None:
            if profile_name is None:
                raise gridsim.GridSimError('Profile not specified.')

            if profile_name == 'Manual':  # Manual reserved for not running a profile.
                self.ts.log_warning('Manual reserved for not running a profile')
                return

            # for simple transient steps in voltage or frequency, use v_step, f_step, and t_step
            if profile_name is 'Transient_Step':
                if t_step is None:
                    raise gridsim.GridSimError('Transient profile did not have a duration.')
                else:
                    # (time offset in seconds, % nominal voltage, % nominal frequency)
                    profile = [(0, v_step, f_step), (t_step, v_step, f_step), (t_step, 100, 100)]

            else:
                # get the profile from grid_profiles
                profile = grid_profiles.profiles.get(profile_name)
                if profile is None:
                    raise gridsim.GridSimError('Profile Not Found: %s' % profile_name)

        dwell_list = ''
        v1_list = ''
        v2_list = ''
        v3_list = ''
        v_slew_list = ''
        freq_list = ''
        freq_slew_list = ''
        func_list = ''
        rep_list = ''
        for i in range(1, len(profile)):
            v1 = float(profile[i - 1][1])
            v2 = float(profile[i - 1][2])
            v3 = float(profile[i - 1][3])
            freq = float(profile[i - 1][4])
            t_delta = float(profile[i][0]) - float(profile[i - 1][0])
            v_delta = max(abs(float(profile[i][1]) - v1), abs(float(profile[i][2]) - v2),
                          abs(float(profile[i][3]) - v3))
            freq_delta = abs(float(profile[i][4]) - freq)

            v_slew = 'MAX'
            freq_slew = 'MAX'
            # if t_delta == 0:
            #     t_delta = 0.001
            if t_delta > 0:
                if i > 1:
                    dwell_list += ','
                    v1_list += ','
                    v2_list += ','
                    v3_list += ','
                    v_slew_list += ','
                    freq_list += ','
                    freq_slew_list += ','
                    func_list += ','
                    rep_list += ','
                if v_delta > 0:
                    v_slew = '%0.3f' % (((v_delta/t_delta)/100.) * float(v_nom))
                    v1 = float(profile[i][1])  # look at next voltage
                    v2 = float(profile[i][2])
                    v3 = float(profile[i][3])
                if freq_delta > 0:
                    freq_slew = '%0.3f' % (((freq_delta/t_delta)/100.) * float(freq_nom))
                    freq = float(profile[i][4])  # look at next frequency
                dwell_list += '%0.3f' % t_delta
                v1_list += '%0.3f' % ((v1/100.) * float(v_nom))
                v2_list += '%0.3f' % ((v2/100.) * float(v_nom))
                v3_list += '%0.3f' % ((v3/100.) * float(v_nom))
                v_slew_list += v_slew
                freq_list += '%0.3f' % ((freq/100.) * float(freq_nom))
                freq_slew_list += freq_slew
                func_list += 'SINE'
                rep_list += '0'

        cmd_list = []
        cmd_list.append('trig:tran:sour imm\n')
        cmd_list.append('list:step auto\n')
        cmd_list.append('abort\n')
        cmd_list.append('abort;:inst:coup none;:list:coun 1;:freq:mode list;:freq:slew:mode list\n')
        cmd_list.append(':inst:nsel 1;:volt:mode list;:volt:slew:mode list;:func:mode list\n')
        cmd_list.append(':inst:nsel 2;:volt:mode list;:volt:slew:mode list;:func:mode list\n')
        cmd_list.append(':inst:nsel 3;:volt:mode list;:volt:slew:mode list;:func:mode list\n')
        cmd_list.append('inst:coup all\n')
        cmd_list.append(':list:dwel %s\n' % dwell_list)
        cmd_list.append(':list:freq %s\n' % freq_list)
        cmd_list.append(':list:freq:slew %s\n' % freq_slew_list)
        cmd_list.append(':inst:nsel 1;:list:volt %s\n' % v1_list)
        cmd_list.append(':list:volt:slew %s\n' % v_slew_list)
        cmd_list.append(':list:func %s\n' % func_list)
        cmd_list.append(':inst:nsel 2;:list:volt %s\n' % v2_list)
        cmd_list.append(':list:volt:slew %s\n' % v_slew_list)
        cmd_list.append(':list:func %s\n' % func_list)
        cmd_list.append(':inst:nsel 3;:list:volt %s\n' % v3_list)
        cmd_list.append(':list:volt:slew %s\n' % v_slew_list)
        cmd_list.append(':list:func %s\n' % func_list)
        cmd_list.append(':list:rep %s\n' % rep_list)
        cmd_list.append('*esr?\n')
        cmd_list.append('trig:sync:sour imm\n')
        cmd_list.append(':init\n')

        self.profile = cmd_list

        self.ts.log(cmd_list)

    def profile_start(self):
        """
        Start the loaded profile.
        """
        if self.profile is not None:
            for entry in self.profile:
                self.cmd(entry)

    def profile_stop(self):
        """
        Stop the running profile.
        """
        self.cmd('abort\n')

    def regen(self, state=None):
        """
        Set the state of the regen mode if provided. Valid states are: REGEN_ON,
        REGEN_OFF. If none is provided, obtains the state of the regen mode.
        """
        if state == gridsim.REGEN_ON:
            self.cmd('REGenerate:STATe ON\n')
            self.query('*esr?\n')
            self.cmd('INST:COUP ALL\n')
            self.query('*esr?\n')
            self.cmd('INST:COUP none;:inst:nsel 1;\n')
        elif state == gridsim.REGEN_OFF:
            self.cmd('REGenerate:STATe OFF\n')
            self.query('*esr?\n')
            self.cmd('INST:COUP ALL\n')
            self.query('*esr?\n')
            self.cmd('INST:COUP none;:inst:nsel 1;\n')
        elif state is None:
            current_state = self.query('REGenerate:STATe?\n')
            ### translate state
        else:
            raise gridsim.GridSimError('Unknown regen state: %s', state)
        return state

    def relay(self, state=None):
        """
        Set the state of the relay if provided. Valid states are: RELAY_OPEN,
        RELAY_CLOSED. If none is provided, obtains the state of the relay.
        """
        if state is not None:
            if state == gridsim.RELAY_OPEN:
                self.cmd('abort;:outp off\n')
            elif state == gridsim.RELAY_CLOSED:
                self.cmd('abort;:outp on\n')
            else:
                raise gridsim.GridSimError('Invalid relay state. State = "%s"', state)
        else:
            relay = self.query('outp?\n').strip()
            # self.ts.log(relay)
            if relay == '0':
                state = gridsim.RELAY_OPEN
            elif relay == '1':
                state = gridsim.RELAY_CLOSED
            else:
                state = gridsim.RELAY_UNKNOWN
        return state

    def voltage(self, voltage=None):
        """
        Set the value for voltage 1, 2, 3 if provided. If none provided, obtains
        the value for voltage. Voltage is a tuple containing a voltage value for
        each phase.
        """
        if voltage is not None:
            # set output voltage on all phases
            # self.ts.log_debug('voltage: %s, type: %s' % (voltage, type(voltage)))
            if type(voltage) is not list and type(voltage) is not tuple:
                self.cmd('inst:coup all;:volt:ac %0.1f\n' % voltage)
            else:
                self.cmd('inst:coup all;:volt:ac %0.1f\n' % voltage[0])  # use the first value in the 3 phase list
        v1 = self.query('inst:coup none;:inst:nsel 1;:volt:ac?\n')
        v2 = self.query('inst:nsel 2;:volt:ac?\n')
        v3 = self.query('inst:nsel 3;:volt:ac?\n')
        return float(v1[:-1]), float(v2[:-1]), float(v3[:-1])

    def voltage_max(self, voltage=None):
        """
        Set the value for max voltage if provided. If none provided, obtains
        the value for max voltage.
        """
        if voltage is not None:
            voltage = max(voltage)  # voltage is a triplet but Ametek only takes one value
            if voltage == 150 or voltage == 300 or voltage == 600:
                self.cmd('volt:rang %0.0f\n' % voltage)
            else:
                raise gridsim.GridSimError('Invalid Max Voltage %s, must be 150, 300 or 600 V.' % str(voltage))
        v1 = self.query('inst:coup none;:inst:nsel 1;:volt:ac? max\n')
        v2 = self.query('inst:nsel 2;:volt:ac? max\n')
        v3 = self.query('inst:nsel 3;:volt:ac? max\n')
        return float(v1[:-1]), float(v2[:-1]), float(v3[:-1])

    def i_max(self):
        return self.i_max_param

    def v_max(self):
        return self.v_max_param

    def v_nom(self):
        return self.v_nom_param

    # Measurements from the grid simulator.
    # MEASure triggers the acquisition of new measurement data before returning a reading.
    # FETCh returns a reading computed from previously acquired data.
    def meas_current(self, ph_list=(1, 2, 3)):
        if 1 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 1\n')
            i1 = self.query('meas:curr:ac?\n')
            i1 = float(i1[:-1])
        else:
            i1 = None
        if 2 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 2\n')
            i2 = self.query('meas:curr:ac?\n')
            i2 = float(i2[:-1])
        else:
            i2 = None
        if 3 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 3\n')
            i3 = self.query('meas:curr:ac?\n')
            i3 = float(i3[:-1])
        else:
            i3 = None
        return i1, i2, i3

    def meas_voltage(self, ph_list=(1, 2, 3)):
        if 1 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 1\n')
            v1 = self.query('meas:volt:ac?\n')
            v1 = float(v1[:-1])
        else:
            v1 = None
        if 2 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 2\n')
            v2 = self.query('meas:volt:ac?\n')
            v2 = float(v2[:-1])
        else:
            v2 = None
        if 3 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 3\n')
            v3 = self.query('meas:volt:ac?\n')
            v3 = float(v3[:-1])
        else:
            v3 = None
        return v1, v2, v3

    def meas_freq(self):
        freq = self.query('meas:FREQ?\n')
        return freq

    def meas_power(self, ph_list=(1, 2, 3)):
        if 1 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 1\n')
            p1 = self.query('meas:pow:ac?\n')
            p1 = float(p1[:-1])*1000.
        else:
            p1 = None
        if 2 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 2\n')
            p2 = self.query('meas:pow:ac?\n')
            p2 = float(p2[:-1])*1000.
        else:
            p2 = None
        if 3 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 3\n')
            p3 = self.query('meas:pow:ac?\n')
            p3 = float(p3[:-1])*1000.
        else:
            p3 = None
        return p1, p2, p3

    def meas_va(self, ph_list=(1, 2, 3)):
        if 1 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 1\n')
            va1 = self.query('meas:pow:ac:app?\n')
            va1 = float(va1[:-1])*1000.
        else:
            va1 = None
        if 2 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 2\n')
            va2 = self.query('meas:pow:ac:app?\n')
            va2 = float(va2[:-1])*1000.
        else:
            va2 = None
        if 3 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 3\n')
            va3 = self.query('meas:pow:ac:app?\n')
            va3 = float(va3[:-1])*1000.
        else:
            va3 = None
        return va1, va2, va3

    def meas_pf(self, ph_list=(1, 2, 3)):
        if 1 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 1\n')
            pf1 = self.query('meas:pow:pfac?\n')
            pf1 = float(pf1[:-1])
        else:
            pf1 = None
        if 1 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 2\n')
            pf2 = self.query('meas:pow:pfac?\n')
            pf2 = float(pf2[:-1])
        else:
            pf2 = None
        if 1 in ph_list:
            self.cmd('inst:coup none;:inst:nsel 3\n')
            pf3 = self.query('meas:pow:pfac?\n')
            pf3 = float(pf3[:-1])
        else:
            pf3 = None
        return pf1, pf2, pf3

    def fetch_current(self):
        self.cmd('inst:coup none;:inst:nsel 1\n')
        i1 = self.query('fetc:curr:ac?\n')
        self.cmd('inst:coup none;:inst:nsel 2\n')
        i2 = self.query('fetc:curr:ac?\n')
        self.cmd('inst:coup none;:inst:nsel 3\n')
        i3 = self.query('fetc:curr:ac?\n')
        return float(i1[:-1]), float(i2[:-1]), float(i3[:-1])

    def fetch_voltage(self):
        self.cmd('inst:coup none;:inst:nsel 1\n')
        v1 = self.query('fetc:volt:ac?\n')
        self.cmd('inst:coup none;:inst:nsel 2\n')
        v2 = self.query('fetc:volt:ac?\n')
        self.cmd('inst:coup none;:inst:nsel 3\n')
        v3 = self.query('fetc:volt:ac?\n')
        return float(v1[:-1]), float(v2[:-1]), float(v3[:-1])

    def fetch_freq(self):
        freq = self.query('fetc:FREQ?\n')
        return freq

    def fetch_power(self):
        self.cmd('inst:coup none;:inst:nsel 1\n')
        p1 = self.query('fetc:pow:ac?\n')
        self.cmd('inst:coup none;:inst:nsel 2\n')
        p2 = self.query('fetc:pow:ac?\n')
        self.cmd('inst:coup none;:inst:nsel 3\n')
        p3 = self.query('fetc:pow:ac?\n')
        return float(p1[:-1])*1000., float(p2[:-1])*1000., float(p3[:-1])*1000.  # convert to watts

    def fetch_va(self):
        self.cmd('inst:coup none;:inst:nsel 1\n')
        va1 = self.query('fetc:pow:ac:app?\n')
        self.cmd('inst:coup none;:inst:nsel 2\n')
        va2 = self.query('fetc:pow:ac:app?\n')
        self.cmd('inst:coup none;:inst:nsel 3\n')
        va3 = self.query('fetc:pow:ac:app?\n')
        return float(va1[:-1])*1000., float(va2[:-1])*1000., float(va3[:-1])*1000.    # convert to VA

    def fetch_pf(self):
        self.cmd('inst:coup none;:inst:nsel 1\n')
        pf1 = self.query('fetc:pow:pfac?\n')
        self.cmd('inst:coup none;:inst:nsel 2\n')
        pf2 = self.query('fetc:pow:pfac?\n')
        self.cmd('inst:coup none;:inst:nsel 3\n')
        pf3 = self.query('fetc:pow:pfac?\n')
        return float(pf1[:-1]), float(pf2[:-1]), float(pf3[:-1])

if __name__ == "__main__":

    grid = GridSim(ts=None, group_name=None)

    grid.config_asymmetric_phase_angles(mag=[276., 277., 278.], angle=[0., 121., 243.])

    print(grid.meas_current())
    print(grid.meas_voltage())
    print(grid.meas_freq())
    print(grid.meas_power())
    print(grid.meas_va())
    print(grid.meas_pf())
