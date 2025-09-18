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
':NUMERIC:NORMAL:ITEM1 URMS,1;'
':NUMERIC:NORMAL:ITEM2 IRMS,1;'
':NUMERIC:NORMAL:ITEM3 P,1;'
':NUMERIC:NORMAL:ITEM4 S,1;'
':NUMERIC:NORMAL:ITEM5 Q,1;'
':NUMERIC:NORMAL:ITEM6 LAMBDA,1;'
':NUMERIC:NORMAL:ITEM7 FU,1;'
':NUMERIC:NORMAL:ITEM8 URMS,2;'
':NUMERIC:NORMAL:ITEM9 IRMS,2;'
':NUMERIC:NORMAL:ITEM10 P,2;'
':NUMERIC:NORMAL:ITEM11 S,2;'
':NUMERIC:NORMAL:ITEM12 Q,2;'
':NUMERIC:NORMAL:ITEM13 LAMBDA,2;'
':NUMERIC:NORMAL:ITEM14 FU,2;'
':NUMERIC:NORMAL:ITEM15 URMS,3;'
':NUMERIC:NORMAL:ITEM16 IRMS,3;'
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
        self.vx = None
        self.params = params
        self.channels = params.get('channels')
        self.data_points = ['TIME']
        self.pf_points = []

        # create query string for configured channels
        query_chan_str = ''
        item = 0
        for i in range(1,5):
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

        pf_scan(self.data_points, self.pf_points)

        self.vx = vxi11.Instrument(self.params['ip_addr'])

        # clear any error conditions
        self.cmd('*CLS')

    def open(self):
        pass

    def close(self):
        if self.vx is not None:
            self.vx.close()
            self.vx = None

    def cmd(self, cmd_str):
        try:
            self.vx.write(cmd_str)
            resp = self.query('STAT:ERRor?')

            if len(resp) > 0:
                if resp[0] != '0':
                    raise DeviceError(resp)
        except Exception as e:
            raise DeviceError('PX8000 communication error: %s' % str(e))

    def query(self, cmd_str):
        try:
            resp = self.vx.ask(cmd_str)
        except Exception as e:
            raise DeviceError('PX8000 communication error: %s' % str(e))

        return resp

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

    points_default = {
        'AC': ('VRMS', 'IRMS', 'P', 'S', 'Q', 'PF', 'FREQ'),
        'DC': ('V', 'I', 'P')
    }
    points = dict(points_default)

    channels = [None]
    for i in range(1, 5):
        chan_type = self._param_value('chan_%d' % (i))
        chan_label = self._param_value('chan_%d_label' % (i))
        if chan_label == 'None':
            chan_label = ''
        chan = {'type': chan_type, 'points': self.points.get(chan_type), 'label': chan_label}
        channels.append(chan)

    d = Device(params=params)
    print(d.info())

    # initialize temp directory
    d.cmd('FILE:DRIV SD')
    path = d.query('FILE:PATH?')
    if path != ':FILE:PATH "Path = SD"':
        print('Drive not found: %s' % 'SD')
    try:
        d.cmd('FILE:DEL "SVP_WAVEFORM";*WAI')
        print('deleted SVP temp directory')
    except:
        pass
    '''
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
    '''

    # capture waveform
    # POS 50?
    d.cmd('TRIG:MODE SING;HYST LOW;LEV 6.00000E-03;SLOP FALL;SOUR P2')
    print(d.query('TRIG:MODE?'))
    print(d.query('TRIG:SIMP?'))
    print(d.query('ACQ?'))
    d.cmd('ACQ:CLOC INT; COUN INF; MODE NORM; RLEN 250000')
    print(d.query('ACQ?'))
    d.cmd('TIM:SOUR INT; TDIV 500.0E-03')
    print(d.query('TIM?'))
    d.cmd(':STAR')
    running = True
    while running:
        cond = int(d.query('STAT:COND?'))
        if cond & COND_RUNNING == COND_RUNNING:
            print('still waiting (%s) ...\r' % cond, end=' ')
            time.sleep(1)
        else:
            running = False
            d.cmd(':STOP')

    # save waveform
    d.cmd('FILE:SAVE:ANAM OFF;NAME "svp_waveform"')
    print('saving')
    d.cmd('FILE:SAVE:ASC:EXEC')

    # transfer waveform

    '''
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


