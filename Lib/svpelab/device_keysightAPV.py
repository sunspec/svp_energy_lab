"""
Copyright (c) 2019, Sandia National Laboratories, SunSpec Alliance, and Tecnalia
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

import sys
import time
import socket

SAS_CURVE = 'SAS CURVE'
SVP_CURVE = 'SVP CURVE'

STATUS_PROFILE_RUNNING = 64
STATUS_PROFILE_PAUSED = 128
STATUS_PROFILE_IN_PROGRESS = STATUS_PROFILE_RUNNING + STATUS_PROFILE_PAUSED

class KeysightAPVError(Exception):
    pass

class KeysightAPV(object):

    def __init__(self, ipaddr='127.0.0.1', ipport=5025, timeout=5):
        self.ipaddr = ipaddr
        self.ipport = ipport
        self.timeout = timeout
        self.buffer_size = 1024
        self.conn = None

    def _cmd(self, cmd_str):
        try:
            if self.conn is None:
                self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.conn.settimeout(self.timeout)
                self.conn.connect((self.ipaddr, self.ipport))

            # print 'cmd> %s' % (cmd_str)
            self.conn.send(cmd_str)
        except Exception as e:
            raise

    def _query(self, cmd_str):
        resp = ''
        more_data = True

        self._cmd(cmd_str)

        while more_data:
            try:
                data = self.conn.recv(self.buffer_size)
                if len(data) > 0:
                    for d in data:
                        resp += d
                        if d == '\n':
                            more_data = False
                            break
            except Exception as e:
                raise KeysightAPVError('Timeout waiting for response')

        return resp

    def cmd(self, cmd_str):
        try:
            self._cmd(cmd_str)
            resp = self._query('SYST:ERR?\n')

            if len(resp) > 0:
                if resp[1] != '0':
                    raise KeysightAPVError(resp)
        except Exception as e:
            raise KeysightAPVError(str(e))
        finally:
            self.close()

    def query(self, cmd_str):
        try:
            resp = self._query(cmd_str).strip()
        except Exception as e:
            raise KeysightAPVError(str(e))
        finally:
            self.close()

        return resp

    def info(self):
        return self.query('*IDN?\n')

    def reset(self):
        self.cmd('*RST\r')

    def scan(self):
        self.idn = self.info()
        self.channels = [None]
        count = int(self.query('SYSTem:CHANnel:COUNt?\n'))

        for c in range(1, count + 1):
            self.channels.append(Channel(self, c))

        for c in self.channels[1:]:
            pass

    def close(self):
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception as e:
            pass
        finally:
            self.conn = None

    def curve_SAS(self, mode='CURVe', imp=6.6, vmp=100, isc=7, voc=120):
        self.cmd('SAS:CURV:IMP %s; ISC %s; VMP %s; VOC %s\n' % (imp,isc,vmp,voc))
        self.cmd('SOURce:SASimulator:MODE %s\n' % (mode))

    def curve_SAS_read(self):
        response=self.query('SAS:CURV:IMP?; ISC?; VMP?; VOC?\n')
        data=response.split(';');
        return data


class Channel(object):

    def __init__(self, ksas, index):
        self.ksas = ksas
        self.index = index
        self.curve = None
        self.profile = None
        self.irradiance = 1000
        self.channels = []
        self.group_index = None

    def group(self, channels):
        self.channels = channels
        self.group_index = channels[0]

    def irradiance_set(self, irradiance):
        self.imp_red = (irradiance/10)
        self.ksas.cmd('SAS:SCAL:CURR %f\n' % self.imp_red)
        # All previously programmed curve parameters are calculated and transferred to the PV simulator(s).

    def output_is_on(self):
        state = self.ksas.query('OUTPut:STATe?\n')
        if state == 1:
            return True
        return False

    def output_set_off(self):
        self.ksas.cmd('OUTPut:STATe 0\n')

    def output_set_on(self):
        self.ksas.cmd('OUTPut:STATe 1\n')

    def status(self):
        return self.ksas.query('STATus:OPERation:CONDition?\n')

    def overvoltage_protection_set(self, voltage=330):
        self.ksas.cmd('SOURce:VOLTage:PROTection:LEVel %s\n' % voltage)
        #[SOURce:]CURRent:PROTection[:LEVel] <value> [,(@chanlist)]

if __name__ == "__main__":

    try:
        ksas = KeysightAPV(ipaddr='127.0.0.1')
        # ksas = KeysightAPV(ipaddr='192.168.0.196')
        # ksas = KeysightAPV(ipaddr='10.10.10.10')

        ksas.scan()

        ksas.reset()

        ksas.curve_en50530(pmp=3000, vmp=460)
        ksas.curve('BP Solar - BP 3230T (60 cells)')

        ksas.profile('STPsIrradiance')
        ksas.profile('Cloudy day')

        print('groups =', ksas.groups_get())
        print('profiles =', ksas.profiles_get())
        print('curves =', ksas.curves_get())

        channel = ksas.channels[1]
        print('is on =', channel.output_is_on())

        channel.profile_set('STPsIrradiance')
        channel.curve_set(EN_50530_CURVE)
        channel.profile_start()
        channel.output_set_on()

        print('channel curve =', channel.curve_get())
        print('channel profile =', channel.profile_get())
        print('is on =', channel.output_is_on())

        time.sleep(10)
        print('is on =', channel.output_is_on())
        channel.profile_abort()
        channel.profile_set('Cloudy day')
        channel.curve_set('BP Solar - BP 3230T (60 cells)')

        channel.profile_start()

        print('channel curve =', channel.curve_get())
        print('channel profile =', channel.profile_get())
        print('is on =', channel.output_is_on())

        ksas.close()

    except Exception as e:
        raise
        print('Error running KeysightAPV setup: %s' % (str(e)))
