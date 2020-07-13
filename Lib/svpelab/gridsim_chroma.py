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
from . import grid_profiles
from . import chroma_61845

chroma_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Chroma'
}

def gridsim_info():
    return chroma_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = chroma_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('phases'), label='Phases', default=1, values=[1,2,3])
    info.param(pname('v_range'), label='Max voltage for all phases', default=300, values=[150,300])
    info.param(pname('v_max'), label='Max Voltage', default=300.0)
    info.param(pname('i_max'), label='Max Current', default=75.0)
    info.param(pname('freq'), label='Frequency', default=60.0)
    info.param(pname('comm'), label='Communications Interface', default='VISA', values=['VISA'])
    info.param(pname('visa_device'), label='VISA Device String', active=pname('comm'),
               active_value=['VISA'], default='USB0::0x0A69::0x086C::662040000329::0::INSTR')
    info.param(pname('visa_path'), label='VISA Path', active=pname('comm'),
               active_value=['VISA'], default='C:/Program Files (x86)/IVI Foundation/VISA/WinNT/agvisa/agbin/visa32.dll')

GROUP_NAME = 'chroma'

class GridSim(gridsim.GridSim):
    """
    Chroma grid simulation implementation.

    Valid parameters:
      mode - 'Chroma'
      v_nom
      v_max
      i_max
      freq
      profile_name
      GPIB Address
      Visa Path

    """
    def __init__(self, ts, group_name):

        gridsim.GridSim.__init__(self, ts, group_name)
        self.conn = None
        self.phases = ts._param_value('phases')
        self.v_range_param = ts._param_value('v_range')
        self.v_max_param = ts._param_value('v_max')
        self.i_max_param = ts._param_value('i_max')
        self.freq_param = ts._param_value('freq')
        self.comm = ts._param_value('comm')
        self.visa_device = ts._param_value('visa_device')
        self.visa_path = ts._param_value('visa_path')

        self.cmd_str = ''
        self._cmd = None
        self._query = None
        self.dev = chroma_61845.ChromaGridSim(visa_device=self.visa_device,
                                     visa_path=self.visa_path)
        self.dev.open()
        self.dev.config()
        self.profile_name = ts.param_value('profile.profile_name')

        state = self.relay()
        output_state = self.output()

        if state != gridsim.RELAY_CLOSED or output_state != gridsim.OUTPUT_ON:
            self.ts.log('Turning on grid simulator.')
            self.output(state=gridsim.OUTPUT_ON)
            self.relay(state=gridsim.RELAY_CLOSED)

        self.config()

    def cmd(self, cmd_str):
        self.cmd_str = cmd_str
        try:
            self.dev.cmd(cmd_str)
            resp = self.dev.query('SYSTem:ERRor?\n') #\r
            if len(resp) > 0:
                if resp[0] != '0':
                    raise gridsim.GridSimError(resp + ' ' + self.cmd_str)
        except Exception as e:
            raise gridsim.GridSimError(str(e))

    def query(self, cmd_str):
        try:
            resp = self.dev.query(cmd_str).strip()
        except Exception as e:
            raise gridsim.GridSimError(str(e))
        return resp

    def info(self):
        return self.query('*IDN?\n')

    def config_phase_angles(self):
        self.dev.config_phase_angles(self.phases)

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        self.ts.log('Grid simulator model: %s' % self.info().strip())

        # put simulator in regenerative mode
        state = self.regen()
        if state != gridsim.REGEN_ON:
            state = self.regen(gridsim.REGEN_ON)
        self.ts.log('Grid sim regenerative mode is: %s' % state)

        #Device Specific Configuration
        self.dev.config()

        # set the phase angles.
        self.config_phase_angles()

        # set voltage range
        self.dev.voltage_range(self.v_range_param)

        v_max = self.v_max_param
        v1, v2, v3 = self.voltage_max()
        if v1 != v_max or v2 != v_max or v3 != v_max:
            self.voltage_max(voltage=(v_max, v_max, v_max))
            v1, v2, v3 = self.voltage_max()
        self.ts.log('Grid sim max voltage settings: v1 = %s, v2 = %s, v3 = %s' % (v1, v2, v3))

        # set max current if it's not already at gridsim_Imax
        i_max = self.i_max_param
        current = self.current()
        if current != i_max:
            self.current(i_max)
            current = self.current()
        self.ts.log('Grid sim max current: %s Amps' % current)

    def open(self):
        """
        Open the communications resources associated with the device.
        """
        try:
           self.dev.open()

        except Exception as e:
            raise gridsim.GridSimError('Cannot open VISA connection to %s' % (self.visa_device))

    def close(self):
        """
        Close any open communications resources associated with the grid
        simulator.
        """
        if self.dev is not None:
            self.dev.close()

    def current(self, current=None):
        """
        Set the value for current if provided. If none provided, obtains
        the value for current.
        """
        return self.dev.current(current)

    def current_max(self, current=None):
        return self.current(current)

    def freq(self, freq=None):
        """
        Set the value for frequency if provided. If none provided, obtains
        the value for frequency.
        Chroma has CW or IMMediate options for the frequency.  Need to figure out what these are.
        """
        return self.dev.freq(freq)

    def profile_load(self, profile_name, v_step=100, f_step=100, t_step=None):
        if profile_name is None:
            raise gridsim.GridSimError('Profile not specified.')

        if profile_name == 'Manual':  # Manual reserved for not running a profile.
            self.ts.log_warning('Manual reserved for not running a profile')
            return

        v_nom = self.v_nom_param
        freq_nom = self.freq_param

        # for simple transient steps in voltage or frequency, use v_step, f_step, and t_step
        if profile_name is 'Transient_Step':
            if t_step is None:
                raise gridsim.GridSimError('Transient profile did not have a duration.')
            else:
                # (time offset in seconds, % nominal voltage, % nominal frequency)
                profile = [(0, v_step, f_step),(t_step, v_step, f_step),(t_step, 100, 100)]

        else:
            # get the profile from grid_profiles
            profile = grid_profiles.profiles.get(profile_name)
            if profile is None:
                raise gridsim.GridSimError('Profile Not Found: %s' % profile_name)

        dwell_list = ''
        v_start_list = ''
        v_end_list = ''
        freq_start_list = ''
        freq_end_list = ''
        func_list = ''
        shape_list= ''

        for i in range(1, len(profile)-1):
            v_start = float(profile[i - 1][1])
            v_end = float (profile[i])
            freq_start = float(profile[i - 1][2])
            freq_end = float(profile[i][2])
            dwelli = float(profile[i][0]) - float(profile[i - 1][0])
            dwelli = dwelli * 1000 #Chroma takes time in mS

            if i > 1:
                dwell_list += ','
                v_start_list += ','
                v_end_list += ','
                freq_start_list += ','
                freq_end_list += ','
                shape_list += ','

            v_start_list += v_start
            v_end_list += v_end
            freq_start_list += freq_start
            freq_end_list += freq_end
            dwell_list += dwelli
            shape_list += 'A'

        #Attempt to move all SCPI commands to separate file for testing and extensibility.
        cmd_list = self.dev.profile_load(dwell_list = dwell_list,
                                         freq_start_list = freq_start_list,
                                         freq_end_list = freq_end_list,
                                         v_start_list=v_start_list,
                                         v_end_list = v_end_list,
                                         shape_list = shape_list)
        self.profile = cmd_list

    # Loads the profile to instrument and starts.  Assumes the output relay is already closed.
    def profile_start(self):
        """
        Start the loaded profile.
        """
        if self.profile is not None:
            for entry in self.profile:
                self.dev.cmd(entry)
            self.dev.relay(gridsim.RELAY_CLOSED)

    def profile_stop(self):
        """
        Stop the running profile.
        """
        self.dev.profile_stop()

    def regen(self, state=None):
        """
        Set the state of the regen mode if provided. Valid states are: REGEN_ON,
        REGEN_OFF. If none is provided, obtains the state of the regen mode.
        Chroma has no option:  Always On
        """
        return gridsim.REGEN_ON

    def relay(self, state=None):
        """
        Set the state of the relay if provided. Valid states are: RELAY_OPEN,
        RELAY_CLOSED. If none is provided, obtains the state of the relay.
        """
        return self.dev.relay(state)

    def output(self,state=None):
        return self.dev.output(state)

    def voltage(self, voltage=None):
        """
        Set the value for voltage 1, 2, 3 if provided. If none provided, obtains
        the value for voltage. Voltage is a tuple containing a voltage value for
        each phase.
        """
        return self.dev.voltage(voltage)

    def voltage_max(self, voltage=None):
        """
        Set the value for max voltage if provided. If none provided, obtains
        the value for max voltage.
        """
        return self.dev.voltage_max(voltage)

    def voltage_slew(self,slew):
        return self.dev.voltage_slew(slew)

    def freq_slew(self,slew):
        return self.dev.voltage_slew(slew)

    def i_max(self):
        return self.i_max_param

    def v_max(self):
        return self.v_max_param

    def v_nom(self):
        return self.v_nom_param

if __name__ == "__main__":
    import script

    d = {'gridsim.chroma.phases':'3',
         'gridsim.chroma.v_nom':'120.0',
         'gridsim.chroma.visa_path':'C:/Program Files (x86)/IVI Foundation/VISA/WinNT/agvisa/agbin/visa32.dll',
         'gridsim.chroma.visa_device':'USB0::0x0A69::0x086C::662040000329::0::INSTR'}


    '''
    ts._param_value('phases')
    self.v_nom_param = ts._param_value('v_nom')
    self.v_max_param = ts._param_value('v_max')
    self.i_max_param = ts._param_value('i_max')
    self.freq_param = ts._param_value('freq')
    self.comm = ts._param_value('comm')
    self.visa_device = ts._param_value('visa_device')
    self.visa_path = ts._param_value('visa_path')
    '''

    ts = script.Script(params = d)

    GridSim(ts)
    GridSim.config()

    pass