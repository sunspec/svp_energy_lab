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
SVP_CURVE = 'SVP CURVE'

STATUS_PROFILE_RUNNING = 64
STATUS_PROFILE_PAUSED = 128
STATUS_PROFILE_IN_PROGRESS = STATUS_PROFILE_RUNNING + STATUS_PROFILE_PAUSED

class SPSError(Exception):
    pass

class SPS(object):

    def __init__(self, comm='VISA', visa_id='GPIB1::19::INSTR', ipaddr='127.0.0.1', ipport=4944, timeout=5):
        self.comm = comm  # 'Network' or 'VISA'

        # TCP/IP communications
        self.ipaddr = ipaddr
        self.ipport = ipport
        self.timeout = timeout
        self.buffer_size = 1024
        self.conn = None
        self.curve = None  # I-V Curve handle
        self.profile = None  # Irradiance/temperature vs time profile
        self.irradiance = 1000  # initial irradiance
        self.group_index = None

        # if using VISA, configure the connection
        if self.comm == 'VISA':
            try:
                import visa
                self.rm = visa.ResourceManager()
                self.conn = self.rm.open_resource(visa_id)
                # the default pyvisa write termination is '\r\n' which does not work with the SPS
                self.conn.write_termination = '\n'
                self.ts.sleep(1)
            except Exception as e:
                raise Exception('Cannot open VISA connection to %s\n\t%s' % (visa_id, str(e)))

    # TCP/IP command
    def _cmd(self, cmd_str):
        try:
            if self.conn is None or self.conn is 'Network':
                self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.conn.settimeout(self.timeout)
                self.conn.connect((self.ipaddr, self.ipport))

            # print 'cmd> %s' % (cmd_str)
            self.conn.send(cmd_str)
        except Exception as e:
            raise

    # TCP/IP query
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
            except Exception as e:
                raise SPSError('Timeout waiting for response')

        return resp

    def cmd(self, cmd_str):
        try:
            if self.comm == 'Network':
                self._cmd(cmd_str)
                resp = self._query('SYSTem:ERRor?\r')

                if len(resp) > 0:
                    if resp[0] != '0':
                        raise SPSError(resp)
            elif self.comm == 'VISA':
                self.conn.write(cmd_str)
        except Exception as e:
            raise SPSError(str(e))
        finally:
            self.close()

    def query(self, cmd_str):
        resp = None
        try:
            if self.comm == 'Network':
                resp = self._query(cmd_str).strip()
            elif self.comm == 'VISA':
                resp = self.conn.query(cmd_str)
        except Exception as e:
            raise SPSError(str(e))
        finally:
            self.close()

        return resp

    def info(self):
        return self.query('*IDN?\r')

    def reset(self):
        self.cmd('*RST\r')

    def scan(self):  # used to scan for channels on other pvsims
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

    def curve(self, voc=None, isc=None, vmp=None, imp=None, form_factor=None,
              beta_v=None, beta_p=None, kfactor_voltage=None, kfactor_irradiance=None):

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

    def curve_en50530(self, tech='CSI', sim_type='STA', pmp=1000, vmp=100):
        self.cmd('CURVe:EN50530:SIMtype %s, %s\r' % (tech, sim_type))
        self.cmd('CURVe:EN50530:MPPparms %s, %s\r' % (pmp, vmp))
        self.cmd('CURVe:EN50530:ADD\r')

    def profile(self, filename):
        self.cmd('PROFile:READFile "%s"\r' % filename)

    def profiles_get(self):
        plist = []
        profiles = self.query('PROFile:CATalog?\r').split(',')
        for p in profiles:
            plist.append(p.split('.')[0])
        return plist

    def groups_get(self):
        groups = self.query('SYSTem:GROup:CATalog?\r').split(',')
        return groups

    def curve_get(self):
        return self.query('SOURce:CURVe?\r')

    def curve_set(self, name):
        if name is not None:
            self.cmd('SOURce:CURVe "%s"\r' % name)
        else:  # if no name provided, use the latest SVP curve
            self.cmd('SOURce:CURVe "%s"\r' % SVP_CURVE)
        # self.cmd('SOURce:IRRadiance 1000, (@%s)\r' % self.index)
        # self.cmd('SOURce:TEMPerature 25, (@%s)\r' % self.index)
        self.cmd('SOURce:EXECute\r')
        # The indicated curve is applied on the selected channels. If the name is blank, curve 0 is
        # applied. Specify name "EN 50530 CURVE" to execute the EN50530 curve.

    def irradiance_set(self, irradiance):
        self.irradiance = irradiance
        self.cmd('SOURce:IRRadiance %d\r' % self.irradiance)
        self.cmd('SOURce:EXECute\r')
        # All previously programmed curve parameters are calculated and transferred to the PV simulator(s).

    def output_is_on(self):
        state = self.query('OUTPut:STATe?\r')
        if state == 'ON':
            return True
        return False

    def output_set_off(self):
        self.cmd('OUTPut:STATe OFF\r')

    def output_set_on(self):
        self.cmd('OUTPut:STATe ON\r')

    def profile_abort(self, timeout=2):
        try:
            self.cmd('ABORt\r')
        except SPSError:
            pass
        time_left = float(timeout)
        while time_left > 0:
            if self.profile_is_active():
                time.sleep(.2)
                time_left -= .2
            else:
                break

    def profile_get(self):
        return self.query('SOURce:PROFile?\r')

    def profile_is_active(self):
        if int(self.status()) & STATUS_PROFILE_IN_PROGRESS:
            return True
        return False

    def profile_pause(self):
        self.cmd('TRIGger:PAUse\r')

    def profile_set(self, name):
        self.profile = name
        self.cmd('SOURce:PROFile "%s"\r' % name)

    def profile_start(self):
        try:
            self.cmd('ABORt\r')
        except SPSError:
            pass
        self.cmd('TRIGger:RESet\r')
        self.cmd('TRIGger\r')

    def status(self):
        return self.query('STATus:OPERation:CONDition?\r')

    def overvoltage_protection_set(self, voltage=330):
        self.cmd('SOURce:VOLTage:PROTection %s\r' % voltage)

if __name__ == "__main__":

    try:
        sps = SPS(comm='VISA', visa_id='GPIB1::19::INSTR')
        sps.info()

        sps.curve_en50530(pmp=3000, vmp=460)
        sps.curve('BP Solar - BP 3230T (60 cells)')

        sps.profile('STPsIrradiance')
        sps.profile('Cloudy day')

        sps.close()

    except Exception as e:
        raise 'Error running SPS setup: %s' % (str(e))
