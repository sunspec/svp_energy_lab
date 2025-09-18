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

import batt

chroma_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Chroma 62000P/63200'
}

def batt_info():
    return chroma_info

def params(info):
    info.param_add_value('batt.mode', chroma_info['mode'])

    info.param_group('batt.chroma_power', label='Chroma Power Supply Parameters',
                     active='batt.mode',  active_value=['Chroma 62000P/63200'], glob=True)
    info.param('batt.chroma_power.v_max', label='Max Voltage', default=300.0)
    info.param('batt.chroma_power.v', label='Voltage', default=50.0)
    info.param('batt.chroma_power.i_max', label='Max Current', default=100.0)
    info.param('batt.chroma_power.i', label='Power Supply Current', default=21.0)
    info.param('batt.chroma_power.comm', label='Communications Interface', default='Serial',
               values=['Serial', 'TCP/IP', 'GPIB', 'USB'])
    info.param('batt.chroma_power.serial_port', label='Serial Port',
               active='batt.chroma_power.comm',  active_value=['Serial'], default='com7')
    info.param('batt.chroma_power.ip_addr', label='IP Address',
               active='batt.chroma_power.comm',  active_value=['TCP/IP'], default='192.168.1.10')
    info.param('batt.chroma_power.usb_name', label='USB Name',
               active='batt.chroma_power.comm',  active_value=['USB'],
               default='USB0::0x1698::0x0837::008000000452::INSTR')

    info.param_group('batt.chroma_load', label='Chroma Load Parameters',
                     active='batt.mode',  active_value=['Chroma 62000P/63200'], glob=True)
    info.param('batt.chroma_load.mode', label='Mode', default='Constant Current',
               values=['Constant Current', 'Constant Voltage', 'Constant Resistance'])
    info.param('batt.chroma_load.i_load', label='Current', default=10.0,
               active='batt.chroma_load.mode',  active_value=['Constant Current'])
    info.param('batt.chroma_load.comm', label='Communications Interface', default='Serial',
               values=['Serial', 'TCP/IP', 'GPIB'])
    info.param('batt.chroma_load.serial_port', label='Serial Port',
               active='batt.chroma_load.comm',  active_value=['Serial'], default='com7')
    info.param('batt.chroma_load.ip_addr', label='IP Address',
               active='batt.chroma_load.comm',  active_value=['TCP/IP'], default='192.168.1.10')
    info.param('batt.chroma_load.ip_port', label='IP Port',
               active='batt.chroma_load.comm',  active_value=['TCP/IP'], default=5025)

class Batt(batt.Batt):

    """
    Implementation for Chroma Programmable DC power supply 62050P-100-100 and the Chroma DC electronic load 63206.

    Valid parameters:
      mode - 'Chroma 62000P/63200'
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
    def __init__(self, ts):
        self.buffer_size = 1024
        self.conn = None
        self.conn_load = None

        batt.Batt.__init__(self, ts)

        self.auto_config = ts.param_value('batt.auto_config')

        # power supply parameters
        self.v_max_param = ts.param_value('batt.chroma_power.v_max')
        self.v_param = ts.param_value('batt.chroma_power.v')
        self.i_max_param = ts.param_value('batt.chroma_power.i_max')
        self.i_param = ts.param_value('batt.chroma_power.i')
        self.comm = ts.param_value('batt.chroma_power.comm')
        self.serial_port = ts.param_value('batt.chroma_power.serial_port')
        self.ipaddr = ts.param_value('batt.chroma_power.ip_addr')
        self.ipport = ts.param_value('batt.chroma_power.ip_port')
        self.usb_name = ts.param_value('batt.chroma_power.usb_name')
        self.baudrate = 115200
        self.timeout = 5
        self.write_timeout = 2
        self.cmd_str = ''
        self._cmd = None
        self._query = None

        # load bank parameters
        self.mode_load = ts.param_value('batt.chroma_load.mode')
        self.i_load = ts.param_value('batt.chroma_load.i_load')
        self.comm_load = ts.param_value('batt.chroma_load.comm')
        self.serial_port_load = ts.param_value('batt.chroma_load.serial_port')
        self.ipaddr_load = ts.param_value('batt.chroma_load.ip_addr')
        self.ipport_load = ts.param_value('batt.chroma_load.ip_port')
        self.baudrate_load = 115200
        self.timeout_load = 5
        self.write_timeout_load = 5
        self.cmd_str_load = ''
        self._cmd_load = None
        self._query_load = None

        # Establish communications with the DC power supply
        if self.comm == 'Serial':
            self.open()  # open communications
            self._cmd = self.cmd_serial
            self._query = self.query_serial
        elif self.comm == 'TCP/IP':
            self._cmd = self.cmd_tcp
            self._query = self.query_tcp
        elif self.comm == 'USB':
            # rm = visa.ResourceManager()
            # self.ts.log_debug(rm.list_resources())
            self._cmd = self.cmd_usb
            self._query = self.query_usb

        # Establish communications with the load bank
        if self.comm_load == 'Serial':
            self.open_load()  # open communications
            self._cmd_load = self.cmd_serial_load
            self._query_load = self.query_serial_load
        elif self.comm_load == 'TCP/IP':
            self._cmd_load = self.cmd_tcp_load
            self._query_load = self.query_tcp_load

        if self.auto_config == 'Enabled':
            ts.log('Configuring the Battery Simulator.')
            self.config()

    # Serial commands for power supply and load
    def cmd_serial(self, cmd_str):
        self.cmd_str = cmd_str
        try:
            if self.conn is None:
                raise batt.BattError('Communications port to power supply not open')

            self.conn.flushInput()
            self.conn.write(cmd_str)
        except Exception, e:
             raise batt.BattError(str(e))

    def cmd_serial_load(self, cmd_str):
        self.cmd_str_load = cmd_str
        try:
            if self.conn_load is None:
                raise batt.BattError('Communications port to load not open')

            self.conn_load.flushInput()
            self.conn_load.write(cmd_str)
        except Exception, e:
             raise batt.BattError(str(e))

    # Serial queries for power supply
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
                    raise batt.BattError('Timeout waiting for response')
            except batt.BattError:
                raise
            except Exception, e:
                raise batt.BattError('Timeout waiting for response - More data problem')

        return resp

    def query_serial_load(self, cmd_str):
        resp = ''
        more_data = True
        self.cmd_serial_load(cmd_str)
        while more_data:
            try:
                count = self.conn_load.inWaiting()
                if count < 1:
                    count = 1
                data = self.conn_load.read(count)
                if len(data) > 0:
                    for d in data:
                        resp += d
                        if d == '\n':
                            more_data = False
                            break
                else:
                    raise batt.BattError('Timeout waiting for response')
            except batt.BattError:
                raise
            except Exception, e:
                raise batt.BattError('Timeout waiting for response - More data problem')

        return resp

    # TCP commands for power supply and load
    def cmd_tcp(self, cmd_str):
        try:
            if self.conn is None:
                self.ts.log('ipaddr = %s  ipport = %s' % (self.ipaddr, self.ipport))
                self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.conn.settimeout(self.timeout)
                self.conn.connect((self.ipaddr, self.ipport))

            # print 'cmd> %s' % (cmd_str)
            self.conn.send(cmd_str)
        except Exception, e:
            raise batt.BattError(str(e))

    def cmd_tcp_load(self, cmd_str):
        try:
            if self.conn_load is None:
                self.ts.log('ipaddr = %s  ipport = %s' % (self.ipaddr_load, self.ipport_load))
                self.conn_load = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.conn_load.settimeout(self.timeout_load)
                self.conn_load.connect((self.ipaddr_load, self.ipport_load))

            # print 'cmd> %s' % (cmd_str)
            self.conn_load.send(cmd_str)
        except Exception, e:
            raise batt.BattError(str(e))

    # TCP queries for power supply and load
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
            except Exception, e:
                raise batt.BattError('Timeout waiting for response')

        return resp

    def query_tcp_load(self, cmd_str):
        resp = ''
        more_data = True

        self._cmd_load(cmd_str)

        while more_data:
            try:
                data = self.conn_load.recv(self.buffer_size_load)
                if len(data) > 0:
                    for d in data:
                        resp += d
                        if d == '\n': #\r
                            more_data = False
                            break
            except Exception, e:
                raise batt.BattError('Timeout waiting for response')

        return resp

    # USB queries for power supply
    def query_usb(self, cmd_str):
        # setup connection if not already established.
        try:
            if self.conn is None:
                self.ts.log('USB device = %s' % self.usb_name)
                rm = visa.ResourceManager()
                self.conn = rm.open_resource(self.usb_name)
            resp = self.conn.query(cmd_str)
            #self.ts.log_debug('cmd_str = %s, resp = %s' % (cmd_str, resp))

        except Exception, e:
            raise batt.BattError('Timeout waiting for response')
        return resp

    # USB commands for power supply
    def cmd_usb(self, cmd_str):
        try:
            if self.conn is None:
                self.ts.log('USB device = %s' % self.usb_name)
                rm = visa.ResourceManager()
                self.conn = rm.open_resource(self.usb_name)
            #self.conn.write('*RST\n')
            self.conn.write('*CLS\n')
            self.conn.write(cmd_str)
        except Exception, e:
            raise batt.BattError(str(e))

    # Commands for power supply and load
    def cmd(self, cmd_str):
        self.cmd_str = cmd_str
        # self.ts.log_debug('cmd_str = %s' % cmd_str)
        try:
            self._cmd(cmd_str)
            resp = self._query('SYSTem:ERRor?\n') #\r
            #self.ts.log_debug('error resp = %s' % resp)
            if len(resp) > 0:
                if resp[0] != '0':
                    raise batt.BattError(resp + ' ' + self.cmd_str)
        except Exception, e:
            raise batt.BattError(str(e))

    def cmd_load(self, cmd_str):
        self.cmd_str_load = cmd_str
        # self.ts.log_debug('cmd_str = %s' % cmd_str)
        try:
            self._cmd_load(cmd_str)
        except Exception, e:
            raise batt.BattError(str(e))

    # Queries for power supply and load
    def query(self, cmd_str):
        # self.ts.log_debug('query cmd_str = %s' % cmd_str)
        try:
            resp = self._query(cmd_str).strip()
        except Exception, e:
            raise batt.BattError(str(e))

        return resp

    def query_load(self, cmd_str):
        # self.ts.log_debug('query cmd_str = %s' % cmd_str)
        try:
            resp = self._query_load(cmd_str).strip()
        except Exception, e:
            raise batt.BattError(str(e))

        return resp

    def info(self):
        return self.query('*IDN?\n')

    def info_load(self):
        return self.query_load('*IDN?\n')

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        self.ts.log('Battery load model: %s' % self.info_load().strip())

        ### Setup the load bank first
        self.prepare_load()
        mode = self.output_mode_load()
        if mode == 1:
            self.ts.log('Battery load bank mode is constant current with the high range.')
        else:
            self.output_mode_load(mode='CCH')
            self.ts.log('Battery load bank mode is %d (1 = constant current with the high range)' % mode)

        # set current
        i = self.i_load
        i_set = self.current_load()
        if i != i_set:
            i_set = self.current_load(current=i)
        self.ts.log('Battery load bank current settings: i = %s' % i_set)
        self.ts.log('Battery load bank configured!')

        ### Setup the power supply
        self.ts.log('Battery power supply model: %s' % self.info().strip())

        # set voltage limits
        v_max_set = self.voltage_max()
        if v_max_set != self.v_max_param:
            v_max_set = self.voltage_max(voltage=v_max)
        v_min_set = self.voltage_min()
        if v_min_set != 0:
            v_min_set = self.voltage_min(voltage=20.)
        self.ts.log('Battery power supply voltage range: [%s, %s] volts' % (v_min_set, v_max_set))

        v_set = self.voltage()
        if v_set != self.v_param:
            self.ts.log_debug('Power supply voltage is %s, should be %s' % (self.v_param, v_set))
            v_set = self.voltage(voltage=self.v_param)
        self.ts.log('Battery power supply voltage: %s volts' % v_set)

        i_max_set = self.current_max()
        if i_max_set != self.i_max_param:
            i_max_set = self.current_max(self.i_max_param)
        self.ts.log('Battery power supply max current: %s Amps' % i_max_set)

        # set current
        self.current_min(current=0.)  # get the current limit out of the way.

        i = self.i_param
        i_set = self.current()
        self.ts.log_debug('Power supply current is %s, should be %s' % (i_set, i))
        if i != self.i_param:
            i_set = self.current(current=i)
            self.ts.log_debug('Power supply current is %0.3f, should be %0.3f' % (i, i_set))
            if i_set == 0.0:
                self.ts.log_warning('Make sure the DC switch is closed!')
        self.ts.log('Battery power supply current settings: i = %s' % i_set)

        ''' Not implemented
        output_mode_set = self.output_mode()
        self.ts.log('Battery power supply mode is %s' % output_mode_set)
        if output_mode_set == 'CVCC':
            self.output_mode(mode='CVCC')
        '''

        # set power supply output
        self.output(start=True)
        outputting = self.output()
        if outputting == 'ON':
            self.ts.log_warning('Battery power supply output is started!')

        self.output_load(start=True)
        outputting_load = self.output_load()
        if outputting_load == 1:
            self.ts.log_warning('Battery load bank output is on!')

    ### Power Supply Functions ###
    def open(self):
        """
        Open the communications resources associated with the grid simulator.
        """
        try:
            self.conn = serial.Serial(port=self.serial_port, baudrate=self.baudrate, bytesize=8, stopbits=1,
                                           xonxoff=0, timeout=self.timeout, writeTimeout=self.write_timeout)

            time.sleep(2)
            #self.cmd('CONFigure:REMote ON\n')
        except Exception, e:
            raise batt.BattError(str(e))

    def close(self):
        """
        Close any open communications resources associated with the grid
        simulator.
        """
        if self.conn:
            if self.comm == 'Serial':
                self.cmd('CONFigure:REMote OFF\n')
            self.conn.close()

    def output(self, start=None):
        """
        Start/stop power supply output

        start: if False stop output, if True start output
        """
        if start is not None:
            if start is True:
                self.cmd('CONF:OUTP ON\n')
            else:
                self.cmd('CONF:OUTP OFF\n')
        output = self.query('CONF:OUTP?\n')
        return output

    def output_mode(self, mode=None):
        """
        Start/stop power supply output

        mode: 'CVCC' constant voltage constant current
        """
        if mode is not None:
            self.cmd('OUTPut:MODE %s' % mode)
        mode = self.query('OUTPut:MODE?\n')
        return mode

    def current(self, current=None):
        """
        Set the value for current if provided. If none provided, obtains the value for current.
        """
        if current is not None:
            self.cmd('SOUR:CURR %0.1f\n' % current)
        i = self.query('SOUR:CURR?\n')
        return float(i)

    def current_max(self, current=None):
        """
        Set the value for max current if provided. If none provided, obtains the value for max current.
        """
        if current is not None:
            self.cmd('SOUR:CURR:LIMIT:HIGH %0.1f\n' % current)
            self.cmd('SOUR:CURR:PROT:HIGH %0.1f\n' % current)
        i1 = self.query('SOUR:CURR:LIMIT:HIGH?\n')
        i2 = self.query('SOUR:CURR:PROT:HIGH?\n')
        return float(min(i1, i2))

    def current_min(self, current=None):
        """
        Set the value for min current if provided. If none provided, obtains
        the value for min current.
        """
        if current is not None:
            self.cmd('SOUR:CURR:LIMIT:LOW %0.1f\n' % current)
        i = self.query('SOUR:CURR:LIMIT:LOW?\n')
        return float(i)

    def voltage(self, voltage=None):
        """
        Set the value for voltage. If none provided, obtains the value for voltage.
        """
        if voltage is not None:
            self.cmd('SOUR:VOLT %0.1f\n' % voltage)
        v = self.query('SOUR:VOLT?\n')
        return float(v)

    def voltage_max(self, voltage=None):
        """
        Set the value for max voltage if provided. If none provided, obtains
        the value for max voltage.
        """
        if voltage is not None:
            self.cmd('SOUR:VOLT:LIMIT:HIGH %0.1f\n' % voltage)
            self.cmd('SOUR:VOLT:PROT:HIGH %0.1f\n' % voltage)
        v1 = self.query('SOUR:VOLT:LIMIT:HIGH?\n')
        v2 = self.query('SOUR:VOLT:PROT:HIGH?\n')
        return min(float(v1), float(v2))

    def voltage_min(self, voltage=None):
        """
        Set the value for max voltage if provided. If none provided, obtains
        the value for max voltage.
        """
        if voltage is not None:
            self.cmd('SOUR:VOLT:LIMIT:LOW %0.1f\n' % voltage)
        v = self.query('SOUR:VOLT:LIMIT:LOW?\n')
        return float(v)

    ### Load Bank Functions ###
    def open_load(self):
        """
        Open the communications resources associated with the grid simulator.
        """
        try:
            self.conn_load = serial.Serial(port=self.serial_port_load, baudrate=self.baudrate_load,
                                           bytesize=8, stopbits=1,
                                           xonxoff=0, timeout=self.timeout_load,
                                           writeTimeout=self.write_timeout_load)
            time.sleep(2)

        except Exception, e:
            raise batt.BattError(str(e))

    def close_load(self):
        """
        Close any open communications resources associated with the grid
        simulator.
        """
        if self.conn_load:
            if self.comm_load == 'Serial':
                self.cmd_load('CONFigure:REMote OFF\n')
            self.conn_load.close()

    def prepare_load(self):
        if self.conn_load:
            self.cmd_load('*RST\n')  # Reset
            self.cmd_load('CONF:REM ON\n')  # Turn on remote control
            self.cmd_load('CONF:VOLT:PROT 1\n')  # turn on voltage protection
            self.ts.log('Voltage protection is set to %s' % self.query_load('CONF:VOLT:PROT?\n'))

    def output_load(self, start=None):
        """
        Start/stop power supply output

        start: if False stop output, if True start output
        """
        if start is not None:
            if start is True:
                self.cmd_load('LOAD ON\n')
            else:
                self.cmd_load('LOAD OFF\n')
        output = self.query_load('LOAD?\n')
        return int(output)

    def output_mode_load(self, mode=None):
        """
        Start/stop power supply output

        mode: 0 = CCL (constant current low), 1 = CCH,  2 = CCDL, 3 = CCDL, etc.
        """
        if mode is not None:
            self.cmd_load('MODE %s\n' % mode)
        mode = self.query_load('MODE?\n')
        #self.ts.log_debug('mode is %s, %s, %s' % (mode, type(mode), int(mode)))
        return int(mode)

    def current_load(self, current=None):
        """
        Set the value for current if provided. If none provided, obtains the value for current.
        """
        if current is not None:
            self.cmd_load('CURR:STAT:L1 %0.1f\n' % current)
        i = self.query_load('CURR:STAT:L1?\n')
        return float(i)

    def current_max_load(self):
        """
        Read the value for max current available.
        """
        return float(self.query_load('CURR:STAT:L1? MAX\n'))

