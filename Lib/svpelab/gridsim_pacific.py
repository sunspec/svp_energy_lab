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
import re

import serial
import visa

from . import grid_profiles
from . import gridsim

pacific_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Pacific'
}

def gridsim_info():
    return pacific_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = pacific_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('phases'), label='Phases', default=1, values=[1, 2, 3])
    info.param(pname('v_nom'), label='Nominal voltage for all phases', default=240.0)
    info.param(pname('v_max'), label='Max Voltage', default=300.0)
    info.param(pname('i_max'), label='Max Current', default=100.0)
    info.param(pname('freq'), label='Frequency', default=60.0)
    info.param(pname('comm'), label='Communications Interface', default='REMOTE IP-GPIB', values=['Serial', 'TCP/IP','REMOTE IP-GPIB'])
    info.param(pname('serial_port'), label='Serial Port',
               active=pname('comm'),  active_value=['Serial'], default='com1')
    info.param(pname('ip_addr'), label='IP Address',
               active=pname('comm'),  active_value=['TCP/IP'], default='192.168.0.171')
    info.param(pname('ip_port'), label='IP Port',
               active=pname('comm'),  active_value=['TCP/IP'], default=1234)
    info.param(pname('remote_ip_addr'), label='REMOTE IP Address',
               active=pname('comm'),  active_value=['REMOTE IP-GPIB'], default='192.168.120.32')
    info.param(pname('gpib_addr'), label='GPIB Address',
               active=pname('comm'),  active_value=['REMOTE IP-GPIB'], default=2)			   
GROUP_NAME = 'pacific'


class GridSim(gridsim.GridSim):
    """
    Pacific grid simulation implementation.

    Valid parameters:
      mode - 'Pacific'
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
        self.v_nom_param = self._param_value('v_nom')
        self.v_max_param = self._param_value('v_max')
        self.i_max_param = self._param_value('i_max')
        self.freq_param = self._param_value('freq')
        self.comm = self._param_value('comm')
        self.serial_port = self._param_value('serial_port')
        self.ipaddr = self._param_value('ip_addr')
        self.ipport = self._param_value('ip_port')
        self.remote_ipaddr = self._param_value('remote_ip_addr')
        self.gpib_addr = self._param_value('gpib_addr')
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
        elif self.comm == 'REMOTE IP-GPIB':
            self._cmd = self.cmd_remote_tcp
            self._query = self.query_remote_tcp
			
        if self.auto_config == 'Enabled':
            ts.log('Configuring the Grid Simulator.')
            self.config()

        state = self.relay()  # will always return 'unknown' because this isn't available
        if state != gridsim.RELAY_CLOSED:
            if self.ts.confirm('Would you like to ENERGIZE the system?') is False:
                gridsim.GridSimError('Grid simulation was not started.')
            else:
                self.ts.log('Turning on grid simulator output.')
                self.relay(state)

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """

        self.ts.log('Grid simulator model: %s' % self.info().strip())
        self.ts.log('Grid sim regenerative mode is not available  - ensure there is a properly sized resistive load.')

        # The Pacific Grid simulator can be configured with either programs or with direct commands.
        # Here we take the conservative approach of creating and executing a program and also sending direct commands.
        self.cmd('*CLS\n')  # Clear error/event queue
        self.ts.log('Device info: %s' % self.info())

        self.ts.log('Configuring the default settings into Program 0...')
        self.program(prog=0, config=True)

        self.ts.log('Configuring the operational program...')
        self.program(prog=1, config=True)
        self.ts.log('New settings: %s' % self.program(prog=1))

        # set voltage max
        v_max = self.v_max_param
        self.ts.log('Setting maximum voltage to %0.2f V.' % v_max)
        self.voltage_max(voltage=(v_max, v_max, v_max))

        # Note, max voltage must be set prior to program execution.
        self.ts.log('Executing program.')
        self.execute_program(prog=1)  # program 0 is default

        ''' Completed above
        # Direct commands to the equipment
        # set the transformer coupling and transformer ratio
        self.ts.log('Setting the coupling to "transformer" and the turns ratio to 2.88')
        self.coupling(coupling='XFMR')
        self.xfmr_ratio(ratio=2.88)

        # set max current
        self.ts.log('Setting grid sim max current to %s Amps' % self.i_max_param)
        self.current_max(self.i_max_param)

        # set the number of phases [This is completed in program() - must be 3 phase for this equipment anyway...]
        # self.ts.log('Adjusting the number of phases for the output.')
        # self.form(form=self.phases_param)

        # set the phase angles for the active phases
        self.ts.log('Configuring phase angles.')
        self.config_phase_angles()

        # set frequency
        self.ts.log('Setting nominal frequency to %0.2f Hz.' % self.freq_param)
        self.freq(self.freq_param)

        # set nominal voltage
        v_nom = self.v_nom_param
        self.voltage(voltage=(v_nom, v_nom, v_nom))
        self.ts.log('Grid sim nominal voltage settings: v1 = %s V, v2 = %s V, v3 = %s V' % (v_nom, v_nom, v_nom))
        '''

    def query_program(self, prog=1):
        """Gets program data."""
        self.select_program(prog=prog)
        return self.query(':PROG:DEFine?\n')

    def select_program(self, prog=1):
        """
        Selects Program prog for loading. prog in range 0 to 99
        Note program 0 is the manual operation and should not be used.
        """
        if 0 <= int(prog) < 100:
            self.cmd(':PROG:NAME %d\n' % int(prog))
        else:
            self.ts.log_warning('Program number is not between 0 and 99 inclusive. No program was loaded.')

    def program(self, prog=1, config=None):
        """Defines Program if config = True. If config = False, query program"""

        data_str = self.query_program(prog=prog)
        # Example data string:
        # 'FORM,3,COUPL,DIRECT,XFMRRATIO,2.88,FREQ,60,VOLT1,120,VOLT2,120,VOLT3,120,CURR:LIM,3998,
        # PHAS2,120,PHAS3,240,WAVEFORM1,1,WAVEFORM2,1,WAVEFORM3,1,EVENTS,1'

        # self.ts.log_debug('Inspecting program #%d' % prog)
        # self.ts.log_debug(data_str)

        if config is not True:  # query program

            settings = re.findall(r'[-+]?\d*\.\d+|\d+', data_str)
            # ['3', '2.88', '60', '1', '120', '2', '120', '3', '120', '3998', '2', '120', '3', '240', '1', '1', '2', '1', '3', '1', '1']
            #   0      1      2    3     4     5     6     7     8      9      10    11   12    13     14   15   16   17   18  19   20

            if data_str.find('DIRECT') > 0:
                coupling = 'DIRECT'
            elif data_str.find('XFMR,') > 0:
                coupling = 'XFMR'
            else:
                coupling = 'UNKNOWN'
                self.ts.log_warning('Could not find the coupling type from Program 0 (Manual Settings).')

            manual_settings = {'form': int(settings[0]), 'xfmrratio': float(settings[1]), 'freq': float(settings[2]),
                               'v1': float(settings[4]), 'v2': float(settings[6]), 'v3': float(settings[8]),
                               'i_lim': float(settings[9]),
                               'phase1': 0.0, 'phase2': float(settings[11]), 'phase3': float(settings[13]),
                               'wave1': int(settings[15]), 'wave2': int(settings[17]), 'wave3': int(settings[19]),
                               'events': int(settings[20]), 'coupling': coupling}
            return manual_settings
        else:
            self.ts.log_debug('Deleting program #%d, and uploading new parameters...' % prog)
            self.cmd(':PROG:DEL\n')  # delete program
            if self.phases_param == 1:
                self.ts.log_debug('Single phase not available for this equipment.')
                self.cmd(':PROG:DEFine FORM,1,COUPL,XFMR,XFMRRATIO,2.88,FREQ,' + str(self.freq_param) + ',VOLT,'
                         + str(self.v_nom_param) + ',CURR:LIM,' + str(self.i_max_param) + ',WAVEFORM,1\n')
            elif self.phases_param == 2:
                self.ts.log_debug('Split phase is created with a 3 phase system with Phase B 180 deg from Phase A.')
                # self.cmd(':PROG:DEFine FORM,2,COUPL,XFMR,XFMRRATIO,2.88,FREQ,' + str(self.freq_param) + ',VOLT,'
                #          + str(self.v_nom_param) + ',CURR:LIM,' + str(self.i_max_param) + ',PHAS2,180,'
                #          'WAVEFORM,1\n')
                self.cmd(':PROG:DEFine FORM,3,COUPL,XFMR,XFMRRATIO,2.88,FREQ,' + str(self.freq_param) + ',VOLT1,'
                         + str(self.v_nom_param) + ',VOLT2,' + str(self.v_nom_param) + ',VOLT3,' + str(0.0)
                         + ',CURR:LIM,' + str(self.i_max_param) + ',PHAS2,180,PHAS3,240,WAVEFORM1,1,'
                                                                  'WAVEFORM2,1,WAVEFORM3,1\n')
            elif self.phases_param == 3:
                self.cmd(':PROG:DEFine FORM,3,COUPL,XFMR,XFMRRATIO,2.88,FREQ,' + str(self.freq_param) + ',VOLT1,'
                         + str(self.v_nom_param) + ',VOLT2,' + str(self.v_nom_param) + ',VOLT3,' + str(self.v_nom_param)
                         + ',CURR:LIM,' + str(self.i_max_param) + ',PHAS2,120,PHAS3,240,WAVEFORM1,1,'
                                                                  'WAVEFORM2,1,WAVEFORM3,1\n')

    def execute_program(self, prog=1):
        """ Execute program"""
        self.cmd(':PROG:EXEC %d\n' % int(prog))

    def execute_trans_program(self, prog=1):
        """ Execute transient portion of given program, use with start_profile() """
        self.cmd(':PROG:EXEC:TRANS %d\n' % int(prog))

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
            self.ts.sleep(1)
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

    def cmd_remote_tcp(self, cmd_str):
        try:
            if self.conn is None:
                self.ts.log('remote_ipaddr = %s  gpib_addr = %s' % (self.remote_ipaddr, self.gpib_addr))
                rm = visa.ResourceManager('@py')
                rsc = "TCPIP::" + str(self.remote_ipaddr) + "::gpib0," + str(self.gpib_addr) + "::INSTR"
                self.conn = rm.open_resource(str(rsc))						
                print(("Success when opening remote GPIB resource " +  str(rsc)))
                self.conn.write('*IDN?')
                time.sleep(2)	
                self.conn.read()                            							
            # print 'cmd> %s' % (cmd_str)
            self.conn.write(cmd_str)
            self.ts.sleep(1)
        except Exception as e:
            raise gridsim.GridSimError(str(e))

    def query_remote_tcp(self, cmd_str):
        resp = ''
        more_data = True

        self._cmd(cmd_str)

        while more_data:
            try:
                data = self.conn.read()
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

    def reset(self):
        self.cmd('*RST\n')

    def waveform(self, wave_num=None):
        if wave_num is not None:
            self.cmd(':SOURce:WAVEFORM,%d\n' % wave_num)
        # wave numbers stored in program 0
        prog_settings = self.program(prog=1)
        return prog_settings['wave1'], prog_settings['wave2'], prog_settings['wave3']

    def config_phase_angles(self, read=False):
        if read is True:
            # phase angles stored in program 0
            prog_settings = self.program(prog=0)
            return prog_settings['phase1'], prog_settings['phase2'], prog_settings['phase3']
        else:
            if self.phases_param == 1:
                self.ts.log_debug('Configuring system for single phase.')
                # phase 1 always 'preconfigured' at 0 phase angle
                self.cmd(':SOURce:WAVEFORM,1\n')
                # self.form(1) - UNSUPPORTED
            elif self.phases_param == 2:
                # set the phase angles for split phase
                self.ts.log_debug('Configuring system for split phase on Phases A & B.')
                self.cmd(':SOURce:PHASe2,180.0\n')
                # self.form(2) - UNSUPPORTED
            elif self.phases_param == 3:
                # set the phase angles for the 3 phases
                self.ts.log_debug('Configuring system for three phase.')
                self.cmd(':SOURce:PHASe2,120.0\n')
                self.cmd(':SOURce:PHASe2,240.0\n')
                # self.form(3)  - UNNECESSARY BECAUSE IT IS THE DEFAULT
            else:
                raise gridsim.GridSimError('Unsupported phase parameter: %s' % (self.phases_param))

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
        self.relay(state=gridsim.RELAY_CLOSED)
        if self.conn:
            self.ts.log('Closing connection to grid simulator.')
            self.conn.close()

			
    def current(self, current=None):
        """
        Set the value for current if provided. If none provided, obtains
        the value for current.
        """
        if current is not None:
            self.ts.log_warning('Cannot set the current of the grid simulator.')
            # there is no capability to set the current
            return 0.
        else:
            i1_str = self.query('meas:curr1?\n')
            i2_str = self.query('meas:curr2?\n')
            i3_str = self.query('meas:curr3?\n')
            return float(i1_str[:-1])+float(i2_str[:-1])+float(i3_str[:-1])/3

    def current_max(self, current=None):
        """
        Set the value for max current if provided. If none provided, obtains
        the value for max current.
        """
        if current is not None:
            self.cmd(':SOURce:curr:lim %0.2f\n' % current)
        # max current stored in program 0
        prog_settings = self.program(prog=1)
        return prog_settings['i_lim']

    def form(self, form=None):
        # sets the number of phases used by the equipment
        # 1 = single phase, 2 = split phase, and 3 = 3 phase
        if form is not None:
            self.cmd(':SOURce:FORM %d\n' % form)
        # form stored in program 0
        prog_settings = self.program(prog=1)
        return prog_settings['form']

    def coupling(self, coupling=None):
        # sets the equipment coupling
        # 'DIRECT' = direct coupling, 'XFMR' = transformer coupling
        if coupling is not None:
            self.cmd(':SOURce:coupling %s\n' % coupling)
        prog_settings = self.program(prog=1)
        return prog_settings['coupling']

    def xfmr_ratio(self, ratio=None):
        # sets the transformer ratio as ratio:1 (range of ratio is 0.1 to 2.5)
        if ratio is not None:
            #self.cmd('xfmrratio,%0.1f\n' % ratio)
            self.ts.log_warning('Transformer ratio cannot be set through communications, because it is set with '
                                'DIP switches in the UPC.')
        prog_settings = self.program(prog=1)
        return prog_settings['xfmrratio']

    def freq(self, freq=None):
        """
        Set the value for frequency if provided. If none provided, obtains
        the value for frequency.
        """
        if freq is not None:
            self.cmd(':FREQ %0.2f\n' % freq)
        # freq = self.query(':MEAS:FREQ?\n')
        prog_settings = self.program(prog=1)
        return prog_settings['freq']

    def profile_load(self, profile_name, v_step=100, f_step=100, t_step=None):
        """
        Creates a profile for a given program. An example execution sequence is:

        :PROG:NAME 3;:PROG:DEF?

        :PROG:NAME 0;*STB?

        :PROG:NAME 3;:PROG:DEL;*STB?

        :PROG:NAME 3;:PROG:DEF FORM,3,COUPL,XFMR,XFMRRATIO,2.88,FREQ,60.000000,VOLT1,120.000000,VOLT2,115.000000,
        VOLT3,115.000000,CURR:LIM,40.000000,CURR:PROT:LEV,40.000000,CURR:PROT:TOUT,1,PHAS2,120,PHAS3,240,WAVEFORM1,1,
        WAVEFORM2,1,WAVEFORM3,1,EVENTS,1,AUTORMS,1;*STB?

        :PROG:DEF SEG,1,FSEG,58.000000,VSEG1,120.000000,VSEG2,115.000000,VSEG3,115.000000,WFSEG1,1,WFSEG2,1,WFSEG3,1,
        TSEG,0.100000,SEG,2,FSEG,62.000000,VSEG1,120.000000,VSEG2,115.000000,VSEG3,115.000000,WFSEG1,1,WFSEG2,1,
        WFSEG3,1,TSEG,0.300000,SEG,3,FSEG,60.000000,VSEG1,120.000000,VSEG2,115.000000,VSEG3,115.000000,WFSEG1,1,
        WFSEG2,1,WFSEG3,1,TSEG,0.100000,LAST;*STB?

        :PROG:EXEC?;:PROG:CRC?

        :PROG:NAME 3;:PROG:EXEC;:OUTP?;:PROG:EXEC?;*OPC;*STB?;:STAT:OPER:COND?;*OPC?

        :PROG:NAME 0;:PROG:DEF?
        """

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
                profile = [(0, v_step, f_step), (t_step, v_step, f_step), (t_step, 100, 100)]

        else:
            # get the profile from grid_profiles
            profile = grid_profiles.profiles.get(profile_name)
            if profile is None:
                raise gridsim.GridSimError('Profile Not Found: %s' % profile_name)

        # prepare the program for default operation after execution
        self.select_program(prog=1)  # select program 1
        self.program(prog=1, config=True)  # define program 1

        cmd_list = ':PROG:DEF '
        for i in range(1, len(profile)):
            freq = (float(profile[i - 1][2])/100.) * float(freq_nom)
            volt = (float(profile[i][1])/100.) * float(v_nom)
            t_delta = float(profile[i][0]) - float(profile[i - 1][0])
            cmd_list += 'SEG,%d' % i + ','  # segment number
            cmd_list += 'FSEG,%0.6f' % freq + ','  # segment frequency
            cmd_list += 'VSEG1,%0.6f' % volt + ','  # segment voltage
            cmd_list += 'VSEG2,%0.6f' % volt + ','  # segment voltage
            cmd_list += 'VSEG3,' + str(0.000000) + ','  # segment voltage
            cmd_list += 'WFSEG1,1,'  # waveform, phase 1
            cmd_list += 'WFSEG2,1,'  # waveform, phase 2
            cmd_list += 'WFSEG3,1,'  # waveform, phase 3
            cmd_list += 'TSEG,%0.6f' % t_delta + ','  # execution time (sec) to reach objective f,v (0=1 cycle)
        cmd_list += 'LAST\n'  # sets selected segment to be the last segment of selected program

        self.ts.log_debug('cmd_list:')
        self.ts.log_debug('%s' % cmd_list)
        self.profile = cmd_list

        # Put the profile in the program (...turns out this is unnecessary)
        # prog_str = self.query_program(prog=1).strip()
        # self.ts.log_debug('Program string from query: %s' % prog_str)
        # self.ts.log_debug('prog_str.find(SEG) = %d' % prog_str.find('SEG'))
        # if prog_str.find('SEG') > 0:
        #     self.ts.log('Program already has a profile. Reloading program...')
        #     head, sep, tail = prog_str.partition('EVENTS,')
        #     prog_str = head + sep + tail[0]
        # prog_str += ',' + self.profile
        # self.ts.log_debug('Program string with profile: %s' % prog_str)

        # Examples:
        # :PROG:DEF SEG,1,FSEG,58.000000,VSEG1,120.000000,VSEG2,115.000000,VSEG3,115.000000,WFSEG1,1,WFSEG2,1,WFSEG3,1,
        # TSEG,0.100000,SEG,2,FSEG,62.000000,VSEG1,120.000000,VSEG2,115.000000,VSEG3,115.000000,WFSEG1,1,WFSEG2,1,
        # WFSEG3,1,TSEG,0.300000,SEG,3,FSEG,60.000000,VSEG1,120.000000,VSEG2,115.000000,VSEG3,115.000000,WFSEG1,1,
        # WFSEG2,1,WFSEG3,1,TSEG,0.100000,LAST

        # :PROG:DEF SEG,1,FSEG,60.000000,VSEG1,96.000000,VSEG2,96.000000,VSEG3,96.000000,WFSEG1,1,WFSEG2,1,WFSEG3,1,
        # TSEG,0.000200,SEG,2,FSEG,60.000000,VSEG1,96.000000,VSEG2,96.000000,VSEG3,96.000000,WFSEG1,1,WFSEG2,1,
        # WFSEG3,1,TSEG,0.500000,SEG,3,FSEG,60.000000,VSEG1,120.000000,VSEG2,120.000000,VSEG3,120.000000,WFSEG1,1,
        # WFSEG2,1,WFSEG3,1,TSEG,0.000200,LAST

        self.cmd(':PROG:NAME 1\n')
        self.cmd(self.profile)
        self.ts.log_debug('Returned program string: %s' % self.query_program(prog=1))

        # Example returned program string:
        # FORM,3,COUPL,DIRECT,XFMRRATIO,2.00,FREQ,60.000000,
        # VOLT1,120.000000,VOLT2,120.000000,VOLT3,120.000000,CURR:LIM,40.000000,CURR:PROT:LEV,40.000000,
        # CURR:PROT:TOUT,1,PHAS2,120,PHAS3,240,WAVEFORM1,1,WAVEFORM2,1,WAVEFORM3,1,EVENTS,1,AUTORMS,1,
        # NSEGS,3,FSEG,60.000000,VSEG1,120.000000,VSEG2,120.000000,VSEG3,120.000000,WFSEG1,1,WFSEG2,1,
        # WFSEG3,1,TSEG,0.000200,LAST

    def profile_start(self):
        """
        Start the loaded profile.
        """
        if self.profile is not None:
            # self.execute_trans_program()

            self.cmd('*OPC;*TRG\n')  # execute transient program (same as ':PROG:EXECute:TRANS\n')
            # Executes pre-processed Transient portion of selected Program. Pre-processing is performed bne
            # executing a program. Transient terminates upon receipt of any data byte (DAB) from the IEEE-488 Bus,
            # Device Clear, or when the LAST segment of the last EVENT is executed. Steady-state values are then
            # restored. Immediately follow this command (in the same program message with *OPC to detect the
            # termination of the Transient events. An SQR will occur when the Transient is completed (if the ESB
            # bit is set in the SRE and the opc bit is set in the ESE. *OPC? may also be used in the same manner.

    def profile_stop(self):
        """
        Stop the running profile.
        """
        # no such command
        pass

    def op_complete(self):
        return self.query('*OPC?\n') == 1

    def regen(self, state=None):
        """
        Set the state of the regen mode if provided. Valid states are: REGEN_ON,
        REGEN_OFF. If none is provided, obtains the state of the regen mode.
        """
        self.ts.log_warning('This equipment does not have a regenerative mode.')
        state == gridsim.REGEN_OFF
        return state

    def relay(self, state=None):
        """
        Set the state of the relay if provided. Valid states are: RELAY_OPEN,
        RELAY_CLOSED. If none is provided, returns unknown relay state.

        Note: in the case of the Pacific there is no relay to be actuated, but rather the output is turned on or off
        """
        if state is not None:
            if state == gridsim.RELAY_OPEN:
                self.ts.log_debug("Energizando sistema")                 
                self.cmd(':OUTput ON\n')
            elif state == gridsim.RELAY_CLOSED:
                self.ts.log_debug("Desenergizando sistema") 
                self.cmd(':OUTput OFF\n')
            else:
                raise gridsim.GridSimError('Invalid relay state. State = "%s"', state)
        else:
            state = self.query(':OUTP?\n').strip()
            self.ts.log_debug('state: %s' % state)
            if state == '1':
                self.ts.log_debug("Sistema energizado")
                state = gridsim.RELAY_CLOSED
            elif state == '0':
                self.ts.log_debug("Sistema NO energizado")
                state = gridsim.RELAY_OPEN
            else:
                self.ts.log_debug("Sistema desconocido")                
                state = gridsim.RELAY_UNKNOWN
        return state

    def voltage(self, voltage=None):
        """
        Set the value for voltage 1, 2, 3 if provided. If none provided, obtains
        the value for voltage. Voltage is a tuple containing a voltage value for
        each phase.
        """
        if self.coupling() == 'DIRECT':
            # Based on the transformer ratio, we need to reduce the voltage command by this amount
            # (only if the device is in direct mode.
            xfmrratio = self.xfmr_ratio()
        else:
            xfmrratio = 1

        if voltage is not None:
            # set output voltage on all phases
            # self.ts.log_debug('voltage: %s, type: %s' % (voltage, type(voltage)))
            if type(voltage) is not list and type(voltage) is not tuple:
                #self.cmd(':SOURce:VOLTage1 %0.1f\n' % (voltage/xfmrratio))
                self.cmd(':SOURce:VOLTage1 %0.1f;VOLTage2 %0.1f;VOLTage3 %0.1f;\n' %
                         (voltage/xfmrratio, voltage/xfmrratio, voltage/xfmrratio))
            else:
                self.cmd(':SOURce:VOLTage1%0.1f;VOLTage2 %0.1f;VOLTage3 %0.1f;\n' %
                         (voltage[0]/xfmrratio, voltage[1]/xfmrratio, voltage[2]/xfmrratio))
        # v1 = self.query(':MEAS:VOLTage1?\n')
        # v2 = self.query(':MEAS:VOLTage2?\n')
        # v3 = self.query(':MEAS:VOLTage3?\n')
        # return float(v1[:-1]), float(v2[:-1]), float(v3[:-1])

        # Voltage settings are stored in the program
        prog_settings = self.program(prog=1)
        return prog_settings['v1']*xfmrratio, prog_settings['v2']*xfmrratio, prog_settings['v3']*xfmrratio

    def voltage_max(self, voltage=None):
        """
        Set the value for max voltage
        """
        if self.coupling() == 'DIRECT':
            # Based on the transformer ratio, we need to reduce the voltage command by this amount
            # (only if the device is in direct mode.
            xfmrratio = self.xfmr_ratio()
        else:
            xfmrratio = 1

        if voltage is not None:
            try:  # first assume the voltage is a tuple
                voltage = max(voltage)/xfmrratio  # voltage is a tuple but Pacific only takes one value
            except TypeError:
                voltage = voltage/xfmrratio  # voltage is a single value
            self.cmd(':SOUR:volt:lim:max %0.0f\n' % voltage)

        # v = self.query(':SOUR:volt:lim:max?\n') # Does not work.
        return self.v_max_param, self.v_max_param, self.v_max_param

    def voltage_min(self, voltage=None):
        """
        Set the value for min voltage
        """
        if self.coupling() == 'DIRECT':
            # Based on the transformer ratio, we need to reduce the voltage command by this amount
            # (only if the device is in direct mode.
            xfmrratio = self.xfmr_ratio()
        else:
            xfmrratio = 1

        if voltage is not None:
            voltage = max(voltage)/xfmrratio  # voltage is a triplet but Pacific only takes one value
            self.cmd(':SOUR:volt:lim:min %0.0f\n' % voltage)
        # v = self.query(':SOUR:volt:lim:min?\n')  # Does not work.
        return 0., 0., 0.

    def freq_max(self, freq=None):
        """
        Set the value for max freq
        """
        if freq is not None:
            self.cmd(':SOUR:FREQ:LIM:MAX %0.0f\n' % freq)
        return self.query(':SOUR:FREQ:LIM:MAX?\n')

    def freq_min(self, freq=None):
        """
        Set the value for min freq
        """
        if freq is not None:
            self.cmd(':SOUR:FREQ:LIM:MIN %0.0f\n' % freq)
        return self.query(':SOUR:FREQ:LIM:MIN?\n')

if __name__ == "__main__":
    pass

