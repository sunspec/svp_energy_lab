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

import sys
import time
import socket

EN_50530_CURVE = 'EN 50530 CURVE'

STATUS_PROFILE_RUNNING = 64
STATUS_PROFILE_PAUSED = 128
STATUS_PROFILE_IN_PROGRESS = STATUS_PROFILE_RUNNING + STATUS_PROFILE_PAUSED

class TerraSASError(Exception):
    pass

class TerraSAS(object):

    def __init__(self, ipaddr='127.0.0.1', ipport=4944, timeout=5):
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
        except Exception, e:
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
                        if d == '\r':
                            more_data = False
                            break
            except Exception, e:
                raise TerraSASError('Timeout waiting for response')

        return resp

    def cmd(self, cmd_str):
        try:
            self._cmd(cmd_str)
            resp = self._query('SYSTem:ERRor?\r')

            if len(resp) > 0:
                if resp[0] != '0':
                    raise TerraSASError(resp)
        except Exception, e:
            raise TerraSASError(str(e))
        finally:
            self.close()

    def query(self, cmd_str):
        try:
            resp = self._query(cmd_str).strip()
        except Exception, e:
            raise TerraSASError(str(e))
        finally:
            self.close()

        return resp

    def info(self):
        return self.query('*IDN?\r')

    def reset(self):
        self.cmd('*RST\r')

    def scan(self):
        self.idn = self.info()
        self.channels = [None]
        count = int(self.query('SYSTem:CHANnel:COUNt?\r'))

        for c in range(1, count + 1):
            self.channels.append(Channel(self, c))

        for c in self.channels[1:]:
            pass

    def close(self):
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception, e:
            pass
        finally:
            self.conn = None

    def curves_get(self):
        return self.query('CURVe:CATalog?\r').strip().split(',')

    def curve(self, filename=None, voc=None, isc=None, vmp=None, imp=None, form_factor=None,
              beta_v=None, beta_p=None, kfactor_voltage=None, kfactor_irradiance=None):

        if filename is not None:
            self.cmd('CURVe:READFile "%s"\r' % (filename))
        if voc is not None and isc is not None:
            self.cmd('CURVe:VIparms %s, %s\r' % (voc, isc))
        if vmp is not None and imp is not None:
            self.cmd('CURVe:MPPparms %s, %s\r' % (vmp, imp))
        if form_factor is not None:
            self.cmd('CURVe:FORMfactor %s\r' % (form_factor))
        if beta_v is not None and beta_p is not None:
            self.cmd('CURVe:BETAparms %s, %s\r' % (beta_v, beta_p))
        if kfactor_voltage is not None and kfactor_irradiance is not None:
            self.cmd('CURVe:KFactor %s, %s\r' % (kfactor_voltage, kfactor_irradiance))

    def curve_en50530(self, tech='CSI', sim_type='STA', pmp=1000, vmp=100):
        self.cmd('CURVe:EN50530:SIMtype %s, %s\r' % (tech, sim_type))
        self.cmd('CURVe:EN50530:MPPparms %s, %s\r' % (pmp, vmp))
        self.cmd('CURVe:EN50530:ADD\r')

    def profile(self, filename):
        self.cmd('PROFile:READFile "%s"\r' % (filename))

    def profiles_get(self):
        plist = []
        profiles = self.query('PROFile:CATalog?\r').split(',')
        for p in profiles:
            plist.append(p.split('.')[0])
        return plist

    def groups_get(self):
        groups = self.query('SYSTem:GROup:CATalog?\r').split(',')
        return groups


class Channel(object):

    def __init__(self, tsas, index):
        self.tsas = tsas
        self.index = index
        self.curve = None
        self.profile = None
        self.irradiance = 1000
        self.channels = []
        self.group_index = None

    def curve_get(self):
        return self.tsas.query('SOURce:CURVe? (@%s)\r' % (self.index))

    def curve_set(self, name):
        self.curve = name
        self.tsas.cmd('SOURce:CURVe "%s", (@%s)\r' % (name, self.index))
        self.tsas.cmd('SOURce:EXECute (@%s)\r' % (self.index))

    def group(self, channels):
        self.channels = channels
        self.group_index = channels[0]

    def irradiance_set(self, irradiance):
        self.irradiance = irradiance
        self.tsas.cmd('SOURce:IRRadiance %d, (@%s)\r' % (self.irradiance, self.index))
        self.tsas.cmd('SOURce:EXECute (@%s)\r' % (self.index))

    def output_is_on(self):
        state = self.tsas.query('OUTPut:STATe? (@%s)\r' % (self.index))
        if state == 'ON':
            return True
        return False

    def output_set_off(self):
        self.tsas.cmd('OUTPut:STATe OFF, (@%s)\r' % (self.index))

    def output_set_on(self):
        self.tsas.cmd('OUTPut:STATe ON, (@%s)\r' % (self.index))

    def profile_abort(self, timeout=2):
        try:
            self.tsas.cmd('ABORt (@%s)\r' % (self.index))
        except TerraSASError:
            pass
        time_left = float(timeout)
        while time_left > 0:
            if self.profile_is_active():
                time.sleep(.2)
                time_left -= .2
            else:
                break

    def profile_get(self):
        return self.tsas.query('SOURce:PROFile? (@%s)\r' % (self.index))

    def profile_is_active(self):
        if int(self.status()) & STATUS_PROFILE_IN_PROGRESS:
            return True
        return False

    def profile_pause(self):
        self.tsas.cmd('TRIGger:PAUse (@%s)\r' % (self.index))

    def profile_set(self, name):
        self.profile = name
        self.tsas.cmd('SOURce:PROFile "%s", (@%s)\r' % (name, self.index))

    def profile_start(self):
        try:
            self.tsas.cmd('ABORt (@%s)\r' % (self.index))
        except TerraSASError:
            pass
        self.tsas.cmd('TRIGger:RESet (@%s)\r' % (self.index))
        self.tsas.cmd('TRIGger (@%s)\r' % (self.index))

    def status(self):
        return self.tsas.query('STATus:OPERation:CONDition? (@%s)\r' % (self.index))


if __name__ == "__main__":

    try:
        tsas = TerraSAS(ipaddr='127.0.0.1')
        # tsas = TerraSAS(ipaddr='192.168.0.196')
        # tsas = TerraSAS(ipaddr='10.10.10.10')

        tsas.scan()

        tsas.reset()

        tsas.curve_en50530(pmp=3000, vmp=460)
        tsas.curve('BP Solar - BP 3230T (60 cells)')

        tsas.profile('STPsIrradiance')
        tsas.profile('Cloudy day')

        print 'groups =', tsas.groups_get()
        print 'profiles =', tsas.profiles_get()
        print 'curves =', tsas.curves_get()

        channel = tsas.channels[1]
        print 'is on =', channel.output_is_on()

        channel.profile_set('STPsIrradiance')
        channel.curve_set(EN_50530_CURVE)
        channel.profile_start()
        channel.output_set_on()

        print 'channel curve =', channel.curve_get()
        print 'channel profile =', channel.profile_get()
        print 'is on =', channel.output_is_on()

        time.sleep(10)
        print 'is on =', channel.output_is_on()
        channel.profile_abort()
        channel.profile_set('Cloudy day')
        channel.curve_set('BP Solar - BP 3230T (60 cells)')

        channel.profile_start()

        print 'channel curve =', channel.curve_get()
        print 'channel profile =', channel.profile_get()
        print 'is on =', channel.output_is_on()

        tsas.close()

    except Exception, e:
        raise
        print 'Error running TerraSAS setup: %s' % (str(e))
