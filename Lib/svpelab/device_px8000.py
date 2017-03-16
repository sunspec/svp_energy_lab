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

import vxi11

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
    'ac_voltage': 'URMS',
    'ac_current': 'IRMS',
    'ac_watts': 'P',
    'ac_va': 'S',
    'ac_vars': 'Q',
    'ac_pf': 'LAMBDA',
    'ac_freq': 'FU',
    'dc_voltage': 'UDC',
    'dc_current': 'IDC',
    'dc_watts': 'P'
}


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
        self.query_info = []

        # create query string for configured channels
        query_chan_str = ''
        item = 0
        for i in range(1,5):
            query_info = None
            chan = self.channels[i]
            if chan is not None:
                chan_type = chan.get('type')
                points = chan.get('points')
                chan_label = chan.get('label')
                if chan_type is None:
                    raise DeviceError('No channel type specified')
                if points is None:
                    raise DeviceError('No points specified')
                chan_str = chan_type
                if chan_label:
                    chan_str += '_%s' % (chan_label)
                query_info = (chan_str, item, item + len(points))
                for p in points:
                    item += 1
                    chan_str = query_points.get('%s_%s' % (chan_type, p))
                    query_chan_str += ':NUMERIC:NORMAL:ITEM%d %s,%d;' % (item, chan_str, i)
                self.query_info.append(query_info)
        query_chan_str += '\n:NUMERIC:NORMAL:VALUE?'

        self.query_str = ':NUMERIC:FORMAT ASCII\nNUMERIC:NORMAL:NUMBER %d\n' % (item) + query_chan_str
        # print self.query_str
        # print self.query_info

        self.vx = vxi11.Instrument(self.params['ip_addr'])

    def open(self):
        pass

    def close(self):
        if self.vx is not None:
            self.vx.close()
            self.vx = None

    def cmd(self, cmd_str):
        try:
            self.vx.write(cmd_str)
            '''
            resp = self._query('SYSTem:ERRor?\r')

            if len(resp) > 0:
                if resp[0] != '0':
                    raise das.DASError(resp)
            '''
        except Exception, e:
            raise DeviceError('PX8000 communication error: %s' % str(e))

    def query(self, cmd_str):
        try:
            resp = self.vx.ask(cmd_str)
        except Exception, e:
            raise DeviceError('PX8000 communication error: %s' % str(e))

        return resp

    def info(self):
        return self.query('*IDN?')

    def data_read(self):
        rec = {'time': time.time()}
        data = [float(i) for i in self.query(self.query_str).split(',')]
        # extract points for each channel
        for info in self.query_info:
            rec[info[0]] = tuple(data[info[1]:info[2]])

        return rec

if __name__ == "__main__":

    pass
