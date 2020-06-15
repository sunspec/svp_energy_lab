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
import visa
from . import loadsim

chroma_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Chroma 63200'
}


def loadsim_info():
    return chroma_info


def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = chroma_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)

    # Constant current/voltage modes
    info.param(pname('i_v_mode'), label='CV CC Mode', default='Constant Current',
               values=['Constant Current', 'Constant Voltage', 'Constant Resistance'])
    info.param(pname('i'), label='Current', active=pname('i_v_mode'),
               active_value=['Constant Current'], default=10.)

    # Comms
    info.param(pname('comm'), label='Communications Interface', default='Serial',
               values=['VISA', 'Serial', 'TCP/IP', 'GPIB'])
    # Visa
    info.param(pname('visa_device'), label='VISA Device String', active=pname('comm'),
               active_value=['VISA'], default='GPIB0::0::INSTR')
    info.param(pname('visa_path'), label='VISA Path', active=pname('comm'),
               active_value=['VISA'], default='')
    # Serial
    info.param(pname('serial_port'), label='Serial Port', active=pname('comm'),
               active_value=['Serial'], default='com7')
    # IP
    info.param(pname('ip_addr'), label='IP Address', active=pname('comm'),
               active_value=['TCP/IP'], default='192.168.1.10')
    info.param(pname('ip_port'), label='IP Port', active=pname('comm'),
               active_value=['TCP/IP'], default=5025)
    # GPIB

    # parameters for tuning unintentional islanding tests
    # info.param(pname('volts'), label='Voltage', default=220)
    # info.param(pname('freq'), label='Frequency', default=50)

GROUP_NAME = 'chroma_63200'


class LoadSim(loadsim.LoadSim):

    """
    Implementation for Chroma DC electronic load 63206.

    Valid parameters:
      mode - 'Chroma 63200'
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
        self.conn = None

        loadsim.LoadSim.__init__(self, ts, group_name)

        # load bank parameters
        self.mode = self._param_value('i_v_mode')
        self.i = self._param_value('i')
        self.comm = self._param_value('comm')
        self.serial_port = self._param_value('serial_port')
        self.ipaddr = self._param_value('ip_addr')
        self.ipport = self._param_value('ip_port')
        self.baudrate = 115200
        self.timeout = 5
        self.write_timeout = 5
        self.cmd_str = ''
        self._cmd = None
        self._query = None

        # Establish communications with the load bank
        if self.comm == 'Serial':
            self.open()  # open communications
            self._cmd = self.cmd_serial
            self._query = self.query_serial
        elif self.comm == 'TCP/IP':
            self._cmd = self.cmd_tcp
            self._query = self.query_tcp

        if self.auto_config == 'Enabled':
            ts.log('Configuring the load...')
            self.config()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def cmd_serial(self, cmd_str):
        self.cmd_str = cmd_str
        try:
            if self.conn is None:
                raise loadsim.LoadSimError('Communications port to load not open')

            self.conn.flushInput()
            self.conn.write(cmd_str)
        except Exception as e:
             raise loadsim.LoadSimError(str(e))

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
                    raise loadsim.LoadSimError('Timeout waiting for response')
            except loadsim.LoadSimError:
                raise
            except Exception as e:
                raise loadsim.LoadSimError('Timeout waiting for response - More data problem')

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
            raise loadsim.LoadSimError(str(e))

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
                raise loadsim.LoadSimError('Timeout waiting for response')

        return resp

    # Commands for load
    def cmd(self, cmd_str):
        self.cmd_str = cmd_str
        # self.ts.log_debug('cmd_str = %s' % cmd_str)
        try:
            self._cmd(cmd_str)
        except Exception as e:
            raise loadsim.LoadSimError(str(e))

    # Queries for load
    def query(self, cmd_str):
        # self.ts.log_debug('query cmd_str = %s' % cmd_str)
        try:
            resp = self._query(cmd_str).strip()
        except Exception as e:
            raise loadsim.LoadSimError(str(e))

        return resp

    def info(self):
        """
        Return information string for the module test device.
        """
        return self.query('*IDN?\n')

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        self.ts.log('Load model: %s' % self.info().strip())

        # Setup the load bank
        self.prepare()
        mode = self.output_mode()
        if mode == 1:
            self.ts.log('Battery load bank mode is constant current with the high range.')
        else:
            self.output_mode(mode='CCH')
            self.ts.log('Battery load bank mode is %d (1 = constant current with the high range)' % mode)

        # set current
        i = self.i
        i_set = self.current()
        if i != i_set:
            i_set = self.current(current=i)
        self.ts.log('Battery load bank current settings: i = %s' % i_set)
        self.ts.log('Battery load bank configured!')

    def open(self):
        """
        Open the communications resources associated with the grid simulator.
        """
        try:
            self.conn = serial.Serial(port=self.serial_port, baudrate=self.baudrate,
                                      bytesize=8, stopbits=1,
                                      xonxoff=0, timeout=self.timeout,
                                      writeTimeout=self.write_timeout)
            time.sleep(2)

        except Exception as e:
            raise loadsim.LoadSimError(str(e))

    def close(self):
        """
        Close any open communications resources associated with the grid
        simulator.
        """
        if self.conn:
            if self.comm == 'Serial':
                self.cmd('CONFigure:REMote OFF\n')
            self.conn.close()

    def prepare(self):
        if self.conn:
            self.cmd('*RST\n')  # Reset
            self.cmd('CONF:REM ON\n')  # Turn on remote control
            self.cmd('CONF:VOLT:PROT 1\n')  # turn on voltage protection
            self.ts.log('Voltage protection is set to %s' % self.query('CONF:VOLT:PROT?\n'))

    def output(self, start=None):
        """
        Start/stop power supply output

        start: if False stop output, if True start output
        """
        if start is not None:
            if start is True:
                self.cmd('LOAD ON\n')
            else:
                self.cmd('LOAD OFF\n')
        output = self.query('LOAD?\n')
        return int(output)

    def output_mode(self, mode=None):
        """
        Start/stop power supply output

        mode: 0 = CCL (constant current low), 1 = CCH,  2 = CCDL, 3 = CCDL, etc.
        """
        if mode is not None:
            self.cmd('MODE %s\n' % mode)
        mode = self.query('MODE?\n')
        # self.ts.log_debug('mode is %s, %s, %s' % (mode, type(mode), int(mode)))
        return int(mode)

    def current(self, current=None):
        """
        Set the value for current if provided. If none provided, obtains the value for current.
        """
        if current is not None:
            self.cmd('CURR:STAT:L1 %0.1f\n' % current)
        i = self.query('CURR:STAT:L1?\n')
        return float(i)

    def current_max(self):
        """
        Read the value for max current available.
        """
        return float(self.query('CURR:STAT:L1? MAX\n'))

