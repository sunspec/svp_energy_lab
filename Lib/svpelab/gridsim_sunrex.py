
import os
import time
import serial
import socket
from . import gridsim
from . import grid_profiles

sunrex_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Sunrex'
}

def gridsim_info():
    return sunrex_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = sunrex_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('phases'), label='Phases', default=1, values=[1, 2, 3])
    info.param(pname('comm'), label='Communications Interface', default='TCP/IP', values=['Serial', 'TCP/IP'])
    info.param(pname('ip_addr'), label='IP Address',
               active=pname('comm'),  active_value=['TCP/IP'], default='192.168.0.171')
    info.param(pname('ip_port'), label='IP Port',
               active=pname('comm'),  active_value=['TCP/IP'], default=1234)

GROUP_NAME = 'sunrex'

class GridSim(gridsim.GridSim):
    """
    Sunrex grid simulation implementation.

    Valid parameters:
      mode - 'SunrexGrd'
      auto_config - ['Enabled', 'Disabled']
      v_nom
      v_max
      i_max
      freq
      profile_name
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

        self.phases_param = ts.param_value('gridsim.sunrex.phases')
        self.auto_config = ts.param_value('gridsim.auto_config')
        self.freq_param = ts.param_value('gridsim.sunrex.freq')
        self.comm = ts.param_value('gridsim.sunrex.comm')
        self.ipaddr = ts.param_value('gridsim.sunrex.ip_addr')
        self.ipport = ts.param_value('gridsim.sunrex.ip_port')
        self.relay_state = gridsim.RELAY_OPEN
        self.regen_state = gridsim.REGEN_OFF
        self.timeout = 100
        self.cmd_str = ''
        self._cmd = None
        self._query = None
        self.profile_name = ts.param_value('profile.profile_name')

        if self.comm == 'TCP/IP':
            self._cmd = self.cmd_tcp
            self._query = self.query_tcp
        if self.auto_config == 'Enabled':
           ts.log('Configuring the Grid Simulator.')
           # self.config()

        state = self.relay()
        if state != gridsim.RELAY_CLOSED:
            if self.ts.confirm('Would you like to close the grid simulator relay and ENERGIZE the system?') is False:
                raise gridsim.GridSimError('Aborted grid simulation')
            else:
                self.ts.log('Turning on grid simulator.')
                self.relay(state=gridsim.RELAY_CLOSED)

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
        except Exception as e:
            raise gridsim.GridSimError(str(e))

    def query(self, cmd_str):
        try:
            resp = self._query(cmd_str).strip()
        except Exception as e:
            raise gridsim.GridSimError(str(e))
        return resp

    def freq(self, freq=None):
        """
        Set the value for frequency if provided. If none provided, obtains
        the value for frequency.
        """
        if freq is not None:
            self.cmd(':AC:SETB:FREQ %0.2f\n' % freq)
            self.freq_param = freq

        return freq

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
            relay = self.query(':AC:STAT:READ?\n').strip()
            #self.ts.log(relay)
            #if relay == '0':
            if relay == ':AC:STAT:READ 0':
                state = gridsim.RELAY_OPEN
            #elif relay == '1':
            elif relay == ':AC:STAT:READ 1':
                state = gridsim.RELAY_CLOSED

            else:
                state = gridsim.RELAY_UNKNOWN
        return state

    def cmd_run(self):
        relay = self.query(':AC:STAT:READ?\n').strip()
        if relay == ':AC:STAT:READ 1':
            self.cmd(':AC:CONT:RUN 1')

    def cmd_stop(self):
        self.cmd(':AC:CONT:RUN 0')

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
                self.cmd(':AC:SETB:VOLT PERC,%0.1f,%0.1f,%0.1f\n' % (voltage, voltage, voltage))
                v1 = voltage
                v2 = voltage
                v3 = voltage
            else:
                self.cmd(':AC:SETB:VOLT PERC,%0.1f,%0.1f,%0.1f\n' % (voltage[0], voltage[0], voltage[0])) # use the first value in the 3 phase list
                v1 = voltage[0]
                v2 = voltage[0]
                v3 = voltage[0]


if __name__ == "__main__":
    pass