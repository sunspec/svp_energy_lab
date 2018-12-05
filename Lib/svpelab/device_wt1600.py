import os
import socket
import sys
import time
import vxi11

'''
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
'''


# map data points to query points
query_points = {
    'AC_VRMS': 'U',
    'AC_IRMS': 'I',
    'AC_P': 'P',
    'AC_S': 'S',
    'AC_Q': 'Q',
    'AC_PF': 'LAMBDA',
    'AC_FREQ': 'FU',
    'DC_V': 'U',
    'DC_I': 'I',
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
                        query_chan_str += ':NUMERIC:NORMAL:ITEM%d %s,%d;' % (item, chan_str, i)
                        if chan_label:
                            point_str = '%s_%s' % (point_str, chan_label)
                        self.data_points.append(point_str)
        query_chan_str += '\n:NUMERIC:NORMAL:VALUE?'

        self.query_str = ':NUMERIC:FORMAT ASCII\nNUMERIC:NORMAL:NUMBER %d\n' % (item) + query_chan_str
        # self.ts.log(self.query_str)    #  plot command string
        pf_scan(self.data_points, self.pf_points)

        if self.params.get('comm') == 'Network':
            # self.vx = vxi11.Instrument(self.params['ip_addr'])
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.ip_addr, self.ip_port)
            self.sock.connect(server_address)
            self.sock.settimeout(2.0)

            # Enter the username "anoymous" and password "".
            # If the WT1600 is not configured correctly, a connection cannot be made.

            # Read the WT1600 device asking for username
            self._query(None)

            # Provide the username
            resp = self.query(self.username)  # Read the WT1600 device asking for password, but ignore response
            self.ts.log('WT1600 response: %s' % resp)

            resp = self.query(self.password)  # Read the WT1600 device asking for password, but ignore response
            self.ts.log('WT1600 response: %s' % resp)  # Should print a password OK message

        elif self.params.get('comm') == 'VISA':
            try:
                # sys.path.append(os.path.normpath(self.visa_path))
                import visa
                self.rm = visa.ResourceManager()
                self.conn = self.rm.open_resource(params.get('visa_id'))

                # the default pyvisa write termination is '\r\n' which does not work with the SPS
                self.conn.write_termination = '\n'

                self.ts.sleep(1)

            except Exception, e:
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

        except Exception, e:
            raise

    def _query(self, cmd_str):
        """ low-level query to WT1600 """
        resp = ''
        more_data = True

        if cmd_str is not None:
            self._cmd(cmd_str)

        while more_data:
            try:
                data = self.conn.recv(self.buffer_size)
                if len(data) > 0:
                    for d in data:
                        resp += d
                        if d == '\r':
                            more_data = False
                            break
            except Exception, e:
                raise DeviceError('Timeout waiting for response')
        return resp

    def cmd(self, cmd_str):
        if self.params['comm'] == 'Network':
            try:
                # self.vx.write(cmd_str)
                self._cmd(cmd_str)
            except Exception, e:
                raise DeviceError('WT1600 communication error: %s' % str(e))

        elif self.params['comm'] == 'VISA':
            try:
                # self.ts.log(self.conn.query(cmd_str))
                self.conn.write(cmd_str)
            except Exception, e:
                raise DeviceError('WT1600 communication error: %s' % str(e))

    def query(self, cmd_str):
        try:
            resp = ''
            if self.params.get('comm') == 'Network':
                # resp = self.vx.ask(cmd_str)
                resp = self._query(cmd_str).strip()
            elif self.params.get('comm') == 'VISA':
                resp = self.conn.query(cmd_str)
        except Exception, e:
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
        except Exception, e:
            pass
        finally:
            self.conn = None

    def info(self):
        return self.query('*IDN?')

    def data_capture(self, enable=True):
        self.capture(enable)

    def data_read(self):
        q = self.query(self.query_str)
        data = [float(i) for i in q.split(',')]
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
        cond = int(d.query('STAT:COND?'))
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


def build_frame(message):
    framesize = len(message)
    s_frame = chr(0x80) + chr(0x00) + chr((framesize >> 8) & 0xFF) + chr(framesize & 0xFF) + message
    return s_frame


def receive_func():
    amount_expected = 6
    amount_received = 0
    data = ''
    while amount_received < amount_expected:
        data = sock.recv(50)
        amount_received += len(data)
    return data


def menu():

    repeat_menu = True
    option = ''
    while repeat_menu:
        os.system('cls')
        print("Options:")
        print("1-Read Voltage")
        print("2-Exit")

        option = input("Insert option >> ")
        if int(option) < 1 or int(option) > 2:
            print("Not valid option")
            time.sleep(2)
        else:
            break
    return option    
    
if __name__ == '__main__':
    os.system('cls')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print('Enter IP Address: ')
    ip_address = input()
    print('Enter TCP Port:')
    tcp_port = int(input())
    server_address = (ip_address, tcp_port)

    sock.connect(server_address)
    sock.settimeout(2.0)

    print(receive_func())
    message = build_frame(input())
    sock.sendall(message)

    print(receive_func())
    message = build_frame(input())
    sock.sendall(message)

    print(receive_func())

    repeat_cycle = True
    while repeat_cycle:
        opt = menu()
        if opt == 2:
            repeat_cycle = False
        if opt == 1:
            message = build_frame(":NUMERIC:NORMAL:VALUE? 1")
            sock.sendall(message)
            dato = receive_func()
            print(dato)
        time.sleep(2)

    print >> sys.stderr, 'closing socket'
    sock.close()
