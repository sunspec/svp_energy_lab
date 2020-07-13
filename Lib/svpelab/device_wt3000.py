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

import time
from . import vxi11

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
            # If the WT3000 is not configured correctly, a connection cannot be made.

            # Read the WT3000 device asking for username
            self._query(None)

            # Provide the username
            resp = self.query(self.username)  # Read the WT3000 device asking for password, but ignore response
            self.ts.log('WT3000 response: %s' % resp)

            resp = self.query(self.password)  # Read the WT3000 device asking for password, but ignore response
            self.ts.log('WT3000 response: %s' % resp)  # Should print a password OK message

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
        """ low-level TCP/IP socket connection to WT3000 """
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
        """ low-level query to WT3000 """
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
            except Exception as e:
                raise DeviceError('Timeout waiting for response')
        return resp

    def cmd(self, cmd_str):
        if self.params['comm'] == 'Network':
            try:
                # self.vx.write(cmd_str)
                self._cmd(cmd_str)

            except Exception as e:
                raise DeviceError('WT3000 communication error: %s' % str(e))

        elif self.params['comm'] == 'VISA':
            try:
                # self.ts.log(self.conn.query(cmd_str))
                self.conn.write(cmd_str)
            except Exception as e:
                raise DeviceError('WT3000 communication error: %s' % str(e))

    def query(self, cmd_str):
        try:
            resp = ''
            if self.params.get('comm') == 'Network':
                # resp = self.vx.ask(cmd_str)
                resp = self._query(cmd_str).strip()
            elif self.params.get('comm') == 'VISA':
                resp = self.conn.query(cmd_str)
        except Exception as e:
            raise DeviceError('WT3000 communication error: %s' % str(e))

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

if __name__ == "__main__":

    import time
    import ftplib
    import visa

    '''
    params = {'ts': None, 'visa_id': "GPIB0::13::INSTR", 'comm': "visa", 'comm': "visa"}
    device = Device(params)
    device.info()
    '''
    visa_device = "GPIB0::13::INSTR"
    rm = visa.ResourceManager()
    conn = rm.open_resource(visa_device)

    print((conn.query('*IDN?')))

    '''   

    COND_RUN = 0x1000
    COND_TRG = 0x0004
    COND_CAP = 0x0001

    COND_RUNNING = (COND_RUN | COND_CAP)

    params = {}

    params['ip_addr'] = '192.168.0.100'
    params['channels'] = [None, None, None, None, None]

    ftp = ftplib.FTP('192.168.0.100')
    ftp.login()
    ftp.cwd('SD-1')
    try:
        ftp.delete('SVP_WAVEFORM.CSV')
    except:
        pass

    d = Device(params=params)
    print(d.info())

    
    # initialize temp directory
    d.cmd('FILE:DRIV SD')
    path = d.query('FILE:PATH?')
    if path != ':FILE:PATH "Path = SD"':
        print 'Drive not found: %s' % 'SD'
    try:
        d.cmd('FILE:DEL "SVP_WAVEFORM";*WAI')
        print 'deleted SVP temp directory'
    except:
        pass

    print path
    if path == ':FILE:PATH "Path = SD/SVPTEMP"':
        d.cmd('FILE:DRIV SD')
        try:
            d.cmd('FILE:DEL "SVPTEMP";*WAI')
        except:
            pass
        print 'deleted SVP temp directory'
    d.cmd('FILE:MDIR "SVPTEMP";*WAI')
    d.cmd('FILE:CDIR "SVPTEMP"')
    path = d.query('FILE:PATH?')
    if path != ':FILE:PATH "Path = SD/SVPTEMP"':
        print 'Error creating SVP temp directory: %s' % path

    # capture waveform
    # POS 50?
    d.cmd('TRIG:MODE SING;HYST LOW;LEV 6.00000E-03;SLOP FALL;SOUR P2')
    print d.query('TRIG:MODE?')
    print d.query('TRIG:SIMP?')
    print d.query('ACQ?')
    d.cmd('ACQ:CLOC INT; COUN INF; MODE NORM; RLEN 250000')
    print d.query('ACQ?')
    d.cmd('TIM:SOUR INT; TDIV 500.0E-03')
    print d.query('TIM?')
    d.cmd(':STAR')
    running = True
    while running:
        cond = int(d.query('STAT:COND?'))
        if cond & COND_RUNNING == COND_RUNNING:
            print 'still waiting (%s) ...\r' % cond,
            time.sleep(1)
        else:
            running = False
            d.cmd(':STOP')

    # save waveform
    d.cmd('FILE:SAVE:ANAM OFF;NAME "svp_waveform"')
    print 'saving'
    d.cmd('FILE:SAVE:ASC:EXEC')

    # transfer waveform

    print d.query('waveform:length?')
    print d.query('waveform:format?')
    print d.query('waveform:trigger?')
    print d.query('WAV:FORM?')
    print d.query('WAV:SRAT?')
    print d.query('status:condition?')
    d.cmd('FILE:DRIV USB,0')
    d.cmd('FILE:CDIR "SVPWAV"')
    d.cmd('FILE:DEL "SVPWAV"')
    print d.query('FILE:PATH?')
    d.cmd('FILE:DRIV USB,0')
    print d.query('FILE:PATH?')
    d.cmd('FILE:DEL "SVPWAV"')
    '''
    # d.cmd('FILE:MDIR "SVPWAV"')


