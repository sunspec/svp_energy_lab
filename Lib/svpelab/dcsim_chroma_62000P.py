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
from . import dcsim

chroma_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Chroma 62000P'
}

def dcsim_info():
    return chroma_info

def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = chroma_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)

    # Constant current/voltage modes
    info.param(pname('v_max'), label='Max Voltage', default=300.0)
    info.param(pname('v'), label='Voltage', default=50.0)
    info.param(pname('i_max'), label='Max Current', default=100.0)
    info.param(pname('i'), label='Power Supply Current', default=21.0)

    # Comms
    info.param(pname('comm'), label='Communications Interface', default='USB',
               values=['USB', 'Serial', 'TCP/IP', 'GPIB'])
    # USB
    info.param(pname('usb_name'), label='USB Device String', active=pname('comm'),
               active_value=['USB'], default='USB0::0x1698::0x0837::008000000452::INSTR')

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


GROUP_NAME = 'chroma_62000P'

class DCSim(dcsim.DCSim):

    """
    Implementation for Chroma Programmable DC power supply 62050P-100-100.

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
    def __init__(self, ts, group_name):
        self.buffer_size = 1024
        self.conn = None
        self.conn_load = None

        dcsim.DCSim.__init__(self, ts, group_name)

        # power supply parameters
        self.v_max_param = self._param_value('v_max')
        self.v_param = self._param_value('v')
        self.i_max_param = self._param_value('i_max')
        self.i_param = self._param_value('i')
        self.comm = self._param_value('comm')
        self.serial_port = self._param_value('serial_port')
        self.ipaddr = self._param_value('ip_addr')
        self.ipport = self._param_value('ip_port')
        self.usb_name = self._param_value('usb_name')
        self.baudrate = 115200
        self.timeout = 5
        self.write_timeout = 2
        self.cmd_str = ''
        self._cmd = None
        self._query = None

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

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    # Serial commands for power supply
    def cmd_serial(self, cmd_str):
        self.cmd_str = cmd_str
        try:
            if self.conn is None:
                raise dcsim.DCSimError('Communications port to power supply not open')

            self.conn.flushInput()
            self.conn.write(cmd_str)
        except Exception as e:
             raise dcsim.DCSimError(str(e))

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
                    raise dcsim.DCSimError('Timeout waiting for response')
            except dcsim.DCSimError:
                raise
            except Exception as e:
                raise dcsim.DCSimError('Timeout waiting for response - More data problem')

        return resp

    # TCP commands for power supply
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
            raise dcsim.DCSimError(str(e))

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
            except Exception as e:
                raise dcsim.DCSimError('Timeout waiting for response')

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

        except Exception as e:
            raise dcsim.DCSimError('Timeout waiting for response')
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
        except Exception as e:
            raise dcsim.DCSimError(str(e))

    # Commands for power supply
    def cmd(self, cmd_str):
        self.cmd_str = cmd_str
        # self.ts.log_debug('cmd_str = %s' % cmd_str)
        try:
            self._cmd(cmd_str)
            resp = self._query('SYSTem:ERRor?\n') #\r
            #self.ts.log_debug('error resp = %s' % resp)
            if len(resp) > 0:
                if resp[0] != '0':
                    raise dcsim.DCSimError(resp + ' ' + self.cmd_str)
        except Exception as e:
            raise dcsim.DCSimError(str(e))

    # Queries for power supply
    def query(self, cmd_str):
        # self.ts.log_debug('query cmd_str = %s' % cmd_str)
        try:
            resp = self._query(cmd_str).strip()
        except Exception as e:
            raise dcsim.DCSimError(str(e))
        return resp

    def info(self):
        """
        Return information string for the device.
        """
        return self.query('*IDN?\n')

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """

        # Setup the power supply
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

    # Power Supply Functions
    def open(self):
        """
        Open the communications resources associated with the grid simulator.
        """
        try:
            self.conn = serial.Serial(port=self.serial_port, baudrate=self.baudrate, bytesize=8, stopbits=1,
                                           xonxoff=0, timeout=self.timeout, writeTimeout=self.write_timeout)

            time.sleep(2)
            #self.cmd('CONFigure:REMote ON\n')
        except Exception as e:
            raise dcsim.DCSimError(str(e))

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
