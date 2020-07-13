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

import os
from . import device_keysightAPV as keysightAPV
from . import pvsim

keysightAPV_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'keysightAPV'
}

def pvsim_info():
    return keysightAPV_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = keysightAPV_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)

    info.param(pname('ipaddr'), label='IP Address', default='192.168.120.101')
    info.param(pname('curve_type'), label='IV Curve Type', default='SASCURVE',
               values=['SASCURVE', 'TABLE'])

    info.param(pname('overvoltage'), label='Overvoltage Protection Level (V)', default=660.0)


    info.param(pname('vmp'), label='SASCURVE MPP Voltage (V)', default=460.0,
               active=pname('curve_type'),  active_value='SASCURVE')

    info.param(pname('filename'), label='IV Curve Name', default='BP Solar - BP 3230T (60 cells)',
               active=pname('curve_type'),  active_value='TABLE')

    info.param(pname('voc'), label='Voc (V)', default=540,
               active=pname('curve_type'),  active_value='SASCURVE')
    info.param(pname('isc'), label='Isc (A)', default=7.3,
               active=pname('curve_type'),  active_value='SASCURVE')

    info.param(pname('imp'), label='MPP Current (A)', default=6.6,
               active=pname('curve_type'),  active_value='SASCURVE')

    info.param(pname('channel'), label='keysightAPV channel(s)', default='1',
               desc='Channels are a string: 1 or  1,2,4,5')

GROUP_NAME = 'keysightAPV'


class PVSim(pvsim.PVSim):

    def __init__(self, ts, group_name):
        pvsim.PVSim.__init__(self, ts, group_name)

        self.ts = ts
        self.ksas = None

        try:

            self.ipaddr = self._param_value('ipaddr')
            self.curve_type = self._param_value('curve_type')
            self.v_overvoltage = self._param_value('overvoltage')
            self.vmp = self._param_value('vmp')
            self.imp = self._param_value('imp')

            self.filename = self._param_value('filename')
            if self.filename is None:
                self.filename = keysightAPV.SVP_CURVE
            self.voc = self._param_value('voc')
            self.isc = self._param_value('isc')
            self.channel = []
            chans = str(self._param_value('channel')).split(',')
            for c in chans:
                try:
                    self.channel.append(int(c))
                except ValueError:
                    raise pvsim.PVSimError('Invalid channel number: %s' % c)

            self.profile_name = None
            self.ksas = keysightAPV.KeysightAPV(ipaddr=self.ipaddr)
            self.ksas.scan()

            for c in self.channel:
                channel = self.ksas.channels[c]
                if self.curve_type == 'SASCURVE':
                    # re-add SASCURVE curve with active parameters
                    self.ts.log('Initializing PV Simulator with imp = %d and Vmp = %d.' % (self.imp, self.vmp))
                    self.ksas.curve_SAS(imp=self.imp, vmp=self.vmp,isc=self.isc,voc=self.voc)
                    # channel.curve_set(keysightAPV.SAS_CURVE)
                elif self.curve_type == 'TABLE':
                    self.ksas.curve(filename=self.filename)
                    channel.curve_set(self.filename)
                else:
                    raise pvsim.PVSimError('Invalid curve type: %s' % self.curve_type)

                channel.overvoltage_protection_set(voltage=self.v_overvoltage)
                channel.irradiance_set(irradiance=700)
     

        except Exception:
            if self.ksas is not None:
                self.ksas.close()
            raise

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def close(self):
        if self.ksas is not None:
            self.ksas.close()
            self.ksas = None

    def info(self):
        return self.ksas.info()

    def irradiance_set(self, irradiance=1000):
        if self.ksas is not None:
            # spread across active channels
            count = len(self.channel)
            if count > 1:
                irradiance = irradiance/count
            for c in self.channel:
                if c is not None:
                    channel = self.ksas.channels[c]
                    channel.irradiance_set(irradiance=irradiance)
                    self.ts.log('KeysightSAS irradiance changed to %0.2f on channel %d.' % (irradiance, c))
                else:
                    raise pvsim.PVSimError('Simulation irradiance not specified because there is no channel specified.')
        else:
            raise pvsim.PVSimError('Irradiance was not changed.')

    def power_set(self, power):
        if self.ksas is not None:
            # spread across active channels
            count = len(self.channel)
            if count > 1:
                power = power/count
            channel=self.ksas.channels[0]
            data = self.ksas.curve_SAS_read()
            self.pmp = float(data[0])*float(data[2])
            self.ts.log('Maximum Power %d' % self.pmp)
            if power > self.pmp:
                self.ts.log_warning('Requested power > Pmp so irradiance will be > 1000 W/m^2)')
            # convert to irradiance for now
            irradiance = (power * 1000)/self.pmp
            self.ts.log('Irradiance %d' % irradiance)
            for c in self.channel:
                if c is not None:
                    channel = self.ksas.channels[c]
                    channel.irradiance_set(irradiance=irradiance)
                    # self.ts.log('TerraSAS power output changed to %0.2f on channel %d.' % (power, c))
        else:
            raise pvsim.PVSimError('Power was not changed.')

    def profile_load(self, profile_name):
        self.ts.log('Function not available. No irradiance profile loaded')

    def power_on(self):
        if self.ksas is not None:
            for c in self.channel:
                channel = self.ksas.channels[c]
                # turn on output if off
                if not channel.output_is_on():
                    channel.output_set_on()
                self.ts.log('KeysightAPV channel %d turned on' % c)
        else:
            raise pvsim.PVSimError('Not initialized')

    def power_off(self):
        if self.ksas is not None:
            for c in self.channel:
                channel = self.ksas.channels[c]
                # turn off output if on
                if channel.output_is_on():
                    channel.output_set_off()
                self.ts.log('KeysightAPV channel %d turned off' % c)
        else:
            raise pvsim.PVSimError('Not initialized')

    def profile_start(self):
        self.ts.log('Function not available. No irradiance profile started')

if __name__ == "__main__":
    pass
