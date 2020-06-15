import os
import socket
import sys
import time
from . import vxi11
"""
data_query_str = (
':NUMERIC:FORMAT ASCII\n'
'NUMERIC:NORMAL:NUMBER 24\n'
':NUMERIC:NORMAL:ITEM1 U,1;'
':NUMERIC:NORMAL:ITEM2 I,1;'
':NUMERIC:NORMAL:ITEM3 P,1;'
':NUMERIC:NORMAL:ITEM4 S,1;'
':NUMERIC:NORMAL:ITEM5 Q,1;'
':NUMERIC:NORMAL:ITEM6 LAMBDA,1;'
':NUMERIC:NORMAL:ITEM7 FU,1;'
':NUMERIC:NORMAL:ITEM8 U,2;'
':NUMERIC:NORMAL:ITEM9 I,2;'
':NUMERIC:NORMAL:ITEM10 P,2;'
':NUMERIC:NORMAL:ITEM11 S,2;'
':NUMERIC:NORMAL:ITEM12 Q,2;'
':NUMERIC:NORMAL:ITEM13 LAMBDA,2;'
':NUMERIC:NORMAL:ITEM14 FU,2;'
':NUMERIC:NORMAL:ITEM15 U,3;'
':NUMERIC:NORMAL:ITEM16 I,3;'
':NUMERIC:NORMAL:ITEM17 P,3;'
':NUMERIC:NORMAL:ITEM18 S,3;'
':NUMERIC:NORMAL:ITEM19 Q,3;'
':NUMERIC:NORMAL:ITEM20 LAMBDA,3;'
':NUMERIC:NORMAL:ITEM21 FU,3;'
':NUMERIC:NORMAL:ITEM22 UDC,4;'
':NUMERIC:NORMAL:ITEM23 IDC,4;'
':NUMERIC:NORMAL:ITEM24 P,4;\n'
':NUMERIC:NORMAL:VALUE?'
)
"""
"""
data_config_str = (
':NUM:NORM:ITEM1 U,1;'
':NUM:NORM:ITEM2 I,1;'
':NUM:NORM:ITEM3 P,1;'
':NUM:NORM:ITEM4 S,1;'
':NUM:NORM:ITEM5 Q,1;'
':NUM:NORM:ITEM6 LAMBDA,1;'
':NUM:NORM:ITEM7 FU,1;'
':NUM:NORM:ITEM8 U,2;'
':NUM:NORM:ITEM9 I,2;'
':NUM:NORM:ITEM10 P,2;'
':NUM:NORM:ITEM11 S,2;'
':NUM:NORM:ITEM12 Q,2;'
':NUM:NORM:ITEM13 LAMBDA,2;'
':NUM:NORM:ITEM14 FU,2;'
':NUM:NORM:ITEM15 U,3;'
':NUM:NORM:ITEM16 I,3;'
':NUM:NORM:ITEM17 P,3;'
':NUM:NORM:ITEM18 S,3;'
':NUM:NORM:ITEM19 Q,3;'
':NUM:NORM:ITEM20 LAMBDA,3;'
':NUM:NORM:ITEM21 FU,3;'
':NUM:NORM:ITEM22 UDC,4;'
':NUM:NORM:ITEM23 IDC,4;'
':NUM:NORM:ITEM24 P,4;\n'
)
"""

# map data points to query points
query_points = {
    'AC_VRMS': 'URMS',
    'AC_IRMS': 'IRMS',
    'AC_P': 'P',
    'AC_S': 'S',
    'AC_Q': 'Q',
    'AC_PF': 'LAMBDA',
    'AC_FREQ': 'FU',
    'DC_V': 'UDC',
    'DC_I': 'IDC',
    'DC_P': 'P'
}


def pf_scan(points, pf_points):
    for i in range(len(points)):
        if points[i].startswith('AC_PF'):
            label = points[i][5:]
            try:
                p_index = points.index('AC_P%s' % (label))
                q_index = points.index('AC_Q%s' % (label))
                pf_points.append((i, p_index, q_index))
            except ValueError:
                pass

def pf_adjust_sign(data, pf_idx, p_idx, q_idx):
    """
    Power factor sign is the opposite sign of the product of active power and reactive power
    """
    pq = data[p_idx] * data[q_idx]
    # sign should be opposite of product of p and q
    pf = abs(data[pf_idx])
    if pq >= 0:
        pf = pf * -1
    return pf


class DeviceError(Exception):
    """
    Exception to wrap all das generated exceptions.
    """
    pass


class Device(object):

    def __init__(self, params):
        self.vx = None  # tcp implementation
        self.conn = None  # visa implementation
        self.params = params
        self.channels = params.get('channels')
        self.visa_id = params.get('visa_id')
        self.ip_addr = params.get('ip_addr')
        self.ip_port = params.get('ip_port')
        self.username = params.get('username')
        self.password = params.get('password')
        self.ts = params.get('ts')
        self.data_points = ['TIME']
        self.pf_points = []
        self.buffer_size=255
        self.config_array= []
        self.b_expct=6

        # create query string for configured channels
        query_chan_str = ''
        item = 0
        for i in range(1, 5):
            chan = self.channels[i]
            if chan is not None:
                chan_type = chan.get('type')
                points = chan.get('points')
                if points is not None:
                    chan_label = chan.get('label')
                    if chan_type is None:
                        raise DeviceError('No channel type specified')
                    if points is None:
                        raise DeviceError('No points specified')
                    for p in points:
                        item += 1
                        point_str = '%s_%s' % (chan_type, p)
                        chan_str = query_points.get(point_str)
                        self.config_array.append(':NUMERIC:NORMAL:ITEM%d %s,%d;' % (item, chan_str, i))
                        #query_chan_str += ':NUMERIC:NORMAL:ITEM%d %s,%d;' % (item, chan_str, i)
                        if chan_label:
                            point_str = '%s_%s' % (point_str, chan_label)
                        self.data_points.append(point_str)
        #query_chan_str += '\n:NUMERIC:NORMAL:VALUE?'
        # self.query_str = ':NUMERIC:FORMAT ASCII\nNUMERIC:NORMAL:NUMBER %d\n' % (item) + query_chan_str
        self.query_str = ':NUMERIC:NORMAL:VALUE?'
        self.config_array.insert(0,':NUMERIC:FORMAT ASCII\nNUMERIC:NORMAL:NUMBER %d\n' % item)
        pf_scan(self.data_points, self.pf_points)
        if self.params.get('comm') == 'Network':
            # self.vx = vxi11.Instrument(self.params['ip_addr'])
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.ip_addr, self.ip_port)
            self.conn.connect(server_address)
            self.conn.settimeout(2.0)
              
            self.ts.log_debug('WT1600 is Connected')

            # Enter the username "anoymous" and password "".
            # If the WT1600 is not configured correctly, a connection cannot be made.

            # Read the WT1600 device asking for username
            resp = self._query(None)
            self.ts.log_debug('WT1600 response: %s' % resp[4:len(resp)])

            # Provide the username
            resp = self.query(self.username)  # Read the WT1600 device asking for password, but ignore response
            self.ts.log_debug('WT1600 response: %s' % resp[4:len(resp)])

            resp = self.query(self.password)  # Read the WT1600 device asking for password, but ignore response
            self.ts.log_debug('WT1600 response: %s' % resp[4:len(resp)])  # Should print a password OK message

            self.b_expct = 4
            for n in range(1,24):
                resp = self.query(self.config_array[n])  # Send channel configuration
            self.b_expct = 6
            resp = self.query(':NUMERIC:NORMAL?')  # Read the WT1600 Channel configuration
            self.ts.log_debug('WT1600 Channel Configuration: %s' % resp[4:len(resp)])  # Print Channel Configuration

        elif self.params.get('comm') == 'VISA':
            try:
                # sys.path.append(os.path.normpath(self.visa_path))
                import visa
                self.rm = visa.ResourceManager()
                self.conn = self.rm.open_resource(params.get('visa_id'))

                # the default pyvisa write termination is '\r\n' which does not work with the SPS
                self.conn.write_termination = '\n'

                self.ts.sleep(1)

            except Exception as e:
                raise Exception('Cannot open VISA connection to %s\n\t%s' % (params.get('visa_id'), str(e)))

        # clear any error conditions
        self.cmd('*CLS')

    def _cmd(self, cmd_str):
        """ low-level TCP/IP socket connection to WT1600 """
        try:
            if self.conn is None:
                self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.conn.settimeout(self.timeout)
                self.conn.connect((self.ip_addr, self.ip_port))
            # print 'cmd> %s' % (cmd_str)

            framesize = len(cmd_str)
            frame = chr(0x80) + chr(0x00) + chr((framesize >> 8) & 0xFF) + chr(framesize & 0xFF) + cmd_str
            self.conn.send(frame)

        except Exception as e:
            raise

    def _query(self, cmd_str):
        """ low-level query to WT1600 """
        resp = ''
        more_data = True

        if cmd_str is not None:
            self._cmd(cmd_str)
        b_recv = 0
        b_expct = self.b_expct
        while b_recv < b_expct:
           # try:
            data = self.conn.recv(self.buffer_size)
            b_recv+= len(data)
            #except Exception, e:
             #   raise DeviceError('Timeout waiting for response')
        return data

    def cmd(self, cmd_str):
        if self.params['comm'] == 'Network':
            try:
                # self.vx.write(cmd_str)
                self._cmd(cmd_str)
            except Exception as e:
                raise DeviceError('WT1600 communication error: %s' % str(e))

        elif self.params['comm'] == 'VISA':
            try:
                # self.ts.log(self.conn.query(cmd_str))
                self.conn.sendall(cmd_str)
            except Exception as e:
                raise DeviceError('WT1600 communication error: %s' % str(e))

    def query(self, cmd_str):
        try:
            resp = ''
            if self.params.get('comm') == 'Network':
                # resp = self.vx.ask(cmd_str)
                resp = self._query(cmd_str).strip()
            elif self.params.get('comm') == 'VISA':
                resp = self.conn.query(cmd_str)
        except Exception as e:
            raise DeviceError('WT1600 communication error: %s' % str(e))

        return resp

    def open(self):
        pass

    def close(self):
        try:
            # if self.vx is not None:
            #     self.vx.close()
            #     self.vx = None
            if self.conn is not None:
                self.conn.close()
        except Exception as e:
            pass
        finally:
            self.conn = None

    def info(self):
        return self.query('*IDN?')

    def data_capture(self, enable=True):
        self.capture(enable)

    def data_read(self):
        q = self.query(self.query_str)
        #q = self.query(self.query_str2)
        m = q[4:len(q)]
        # self.ts.log(m)
        data = [float(i) for i in m.split(',')]
        data.insert(0, time.time())
        for p in self.pf_points:
            data[p[0]] = pf_adjust_sign(data, *p)
        return data

    def capture(self, enable=None):
        """
        Enable/disable capture.
        """
        if enable is not None:
            if enable is True:
                self.cmd('STAR')
            else:
                self.cmd('STOP')

    def trigger(self, value=None):
        """
        Create trigger event with provided value.
        """
        pass

    COND_RUN = 0x1000
    COND_TRG = 0x0004
    COND_CAP = 0x0001

    def status(self):
        """
        Returns dict with following entries:
            'trigger_wait' - waiting for trigger - True/False
            'capturing' - waveform capture is active - True/False
        """
        cond = int(d.query('STAT:COND?',6))
        result = {'trigger_wait': (cond & COND_TRG),
                  'capturing': (cond & COND_CAP),
                  'cond': cond}
        return result

    def waveform(self):
        """
        Return waveform (Waveform) created from last waveform capture.
        """
        pass

    def trigger_config(self, params):
        """
        slope - (rise, fall, both)
        level - (V, I, P)
        chan - (chan num)
        action - (memory save)
        position - (trigger % in capture)
        """

        """
        samples/sec
        secs pre/post

        rise/fall
        level (V, A)
        """

        pass

