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

Documentation: http://www.programmablepower.com/custom-power-supply/ETS/downloads/M609155-01_revH.pdf
"""

import sys
import time
import socket

EN_50530_CURVE = 'EN 50530 CURVE'
SVP_CURVE = 'SVP CURVE'

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
            cmd_str = cmd_str.encode('utf-8')
            self.conn.send(cmd_str)
        except Exception as e:
            raise

    def _query(self, cmd_str):
        resp = ''
        more_data = True

        self._cmd(cmd_str)

        while more_data:
            try:
                data = self.conn.recv(self.buffer_size).decode('utf-8')
                if len(data) > 0:
                    for d in data:
                        resp += d
                        if d == '\r':
                            more_data = False
                            break
            except Exception as e:
                raise TerraSASError('Timeout waiting for response')

        return resp

    def cmd(self, cmd_str):
        try:
            self._cmd(cmd_str)
            resp = self._query('SYSTem:ERRor?\r')

            if len(resp) > 0:
                if resp[0] != '0':
                    raise TerraSASError(resp)
        except Exception as e:
            raise TerraSASError(str(e))
        finally:
            self.close()

    def query(self, cmd_str):
        try:
            resp = self._query(cmd_str).strip()
        except Exception as e:
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
        except Exception as e:
            pass
        finally:
            self.conn = None

    def curves_get(self):
        return self.query('CURVe:CATalog?\r').strip().split(',')

    def curve(self, filename=None, voc=None, isc=None, vmp=None, imp=None, form_factor=None,
              beta_v=None, beta_p=None, kfactor_voltage=None, kfactor_irradiance=None):

        curve_name = SVP_CURVE

        if filename is not None:
            try:
                self.cmd('CURVe:DELEte "%s"\r' % filename)  # Must delete the curve from GUI
            except Exception as e:
                print(('Curve not found: %s' % e))
            self.cmd('CURVe:READFile "%s"\r' % (filename))  # Read it from disk
        else:
            try:
                self.cmd('CURVe:DELEte "%s"\r' % SVP_CURVE)  # Must delete the previous curve
            except Exception as e:
                print(('Curve not found: %s' % e))

            if voc is not None and isc is not None:
                self.cmd('CURVe:VIparms %s, %s\r' % (voc, isc))
            if vmp is not None and imp is not None:
                self.cmd('CURVe:MPPparms %s, %s\r' % (vmp, imp))
            if form_factor is not None:
                self.cmd('CURVe:FORMfactor %s\r' % (form_factor))

            if beta_v is not None and beta_p is not None:
                self.cmd('CURVe:BETAparms %s, %s\r' % (beta_v, beta_p))
                # Sets the voltage and power temperature coefficients, expressed in percent values per
                # degree Kelvin. Some manufacturers report the voltage coefficient in mV/K.
                # Divide by Voc to obtain a percentage. Allowed range is +1.99 to -1.99.

            if kfactor_voltage is not None and kfactor_irradiance is not None:
                self.cmd('CURVe:KFactor %s, %s\r' % (kfactor_voltage, kfactor_irradiance))
                # Sets the irradiance correction factor by entering parameters V1 and E1.
                # See "Photovoltaic curve > Create" for more details. The voltage must be
                # equal to or less than Voc. The irradiance must be between 100 and 800 W/m2.

            import datetime
            # Not possible to make new IV Curves using a name saved on the hard drive, so a new file is generated
            curve_name = str(datetime.datetime.utcnow())
            curve_name = curve_name.translate(None, ':')  # remove invalid characters
            self.cmd('CURVe:ADD "%s"\r' % curve_name)  # Save new curve to disk and add to graphic pool

        return curve_name  # return IV curve name

    def curve_en50530(self, tech='CSI', sim_type='DYN', pmp=1000, vmp=100):
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
        if name is not None:
            self.tsas.cmd('SOURce:CURVe "%s", (@%s)\r' % (name, self.index))
        else:  # if no name provided, use the latest SVP curve
            self.tsas.cmd('SOURce:CURVe "%s", (@%s)\r' % (SVP_CURVE, self.index))
        # self.tsas.cmd('SOURce:IRRadiance 1000, (@%s)\r' % self.index)
        # self.tsas.cmd('SOURce:TEMPerature 25, (@%s)\r' % self.index)
        self.tsas.cmd('SOURce:EXECute (@%s)\r' % (self.index))
        # The indicated curve is applied on the selected channels. If the name is blank, curve 0 is
        # applied. Specify name "EN 50530 CURVE" to execute the EN50530 curve.

    def group(self, channels):
        self.channels = channels
        self.group_index = channels[0]

    def irradiance_set(self, irradiance):
        self.irradiance = irradiance
        self.tsas.cmd('SOURce:IRRadiance %d, (@%s)\r' % (self.irradiance, self.index))
        self.tsas.cmd('SOURce:EXECute (@%s)\r' % (self.index))
        # All previously programmed curve parameters are calculated and transferred to the PV simulator(s).

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

    def overvoltage_protection_set(self, voltage=330):
        self.tsas.cmd('SOURce:VOLTage:PROTection %s, (@%s)\r' % (voltage, self.index))
        #[SOURce:]CURRent:PROTection[:LEVel] <value> [,(@chanlist)]

    def measurements_get(self):
        """
        Measure the voltage, current, and power of the channel
        :return: dictionary with power data with keys: 'DC_V', 'DC_I', and 'DC_P'
        """
        meas = {'DC_V': float(self.tsas.query('MEASure:SCALar:VOLTage:DC? (@%s)\r' % self.index)),
                'DC_I': float(self.tsas.query('MEASure:SCALar:CURRent:DC? (@%s)\r' % self.index)),
                # 'MPPT_Accuracy': float(self.tsas.query('MEASure:SCALar:MPPaccuracy:DC? (@%s)\r' % self.index)),
                'DC_P': float(self.tsas.query('MEASure:SCALar:POWer:DC? (@%s)\r' % self.index))}
        return meas

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

        print('groups =', tsas.groups_get())
        print('profiles =', tsas.profiles_get())
        print('curves =', tsas.curves_get())

        channel = tsas.channels[1]
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

        tsas.close()

    except Exception as e:
        raise
        print('Error running TerraSAS setup: %s' % (str(e)))
