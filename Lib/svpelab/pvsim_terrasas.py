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

import os

import terrasas
import pvsim

terrasas_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'TerraSAS'
}

def pvsim_info():
    return terrasas_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = terrasas_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)

    info.param(pname('ipaddr'), label='IP Address', default='192.168.0.167')
    info.param(pname('pmp'), label='EN50530 MPP Power (W)', default=3000.0)
    info.param(pname('vmp'), label='EN50530 MPP Voltage (V)', default=460.0)
    info.param(pname('channel'), label='TerraSAS channel(s)', default='1',
               desc='Channels are a string: 1 or  1,2,4,5')

GROUP_NAME = 'terrasas'


class PVSim(pvsim.PVSim):

    def __init__(self, ts, group_name):
        pvsim.PVSim.__init__(self, ts, group_name)

        self.ts = ts
        self.tsas = None

        try:

            self.ipaddr = self._param_value('ipaddr')
            self.pmp = self._param_value('pmp')
            self.vmp = self._param_value('vmp')
            self.channel = []
            self.irr_start = self._param_value('irr_start')
            chans = str(self._param_value('channel')).split(',')
            for c in chans:
                try:
                    self.channel.append(int(c))
                except ValueError:
                    raise pvsim.PVSimError('Invalid channel number: %s' % c)

            self.profile_name = None
            self.ts.log('Initializing PV Simulator with Pmp = %d and Vmp = %d.' % (self.pmp, self.vmp))
            self.tsas = terrasas.TerraSAS(ipaddr=self.ipaddr)
            self.tsas.scan()

            for c in self.channel:
                channel = self.tsas.channels[c]
                if channel.profile_is_active():
                    channel.profile_abort()

                # re-add EN50530 curve with active parameters
                self.tsas.curve_en50530(pmp=self.pmp, vmp=self.vmp)
                channel.curve_set(terrasas.EN_50530_CURVE)

        except Exception:
            if self.tsas is not None:
                self.tsas.close()
            raise

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def close(self):
        if self.tsas is not None:
            self.tsas.close()
            self.tsas = None

    def info(self):
        return self.tsas.info()

    def irradiance_set(self, irradiance=1000):
        if self.tsas is not None:
            # spread across active channels
            count = len(self.channel)
            if count > 1:
                irradiance = irradiance/count
            for c in self.channel:
                if c is not None:
                    channel = self.tsas.channels[c]
                    channel.irradiance_set(irradiance=irradiance)
                    self.ts.log('TerraSAS irradiance changed to %0.2f on channel %d.' % (irradiance, c))
                else:
                    raise pvsim.PVSimError('Simulation irradiance not specified because there is no channel specified.')
        else:
            raise pvsim.PVSimError('Irradiance was not changed.')

    def power_set(self, power):
        if self.tsas is not None:
            # spread across active channels
            count = len(self.channel)
            self.ts.log('power_set = %s - %s' % (power, type(power)))
            if count > 1:
                power = power/count
                self.ts.log('power = %s - %s' % (power, type(power)))
            if power > self.pmp:
                self.ts.log_warning('Requested power > Pmp so irradiance will be > 1000 W/m^2)')
            # convert to irradiance for now
            irradiance = (power * 1000)/self.pmp
            for c in self.channel:
                if c is not None:
                    channel = self.tsas.channels[c]
                    channel.irradiance_set(irradiance=irradiance)
                    # self.ts.log('TerraSAS power output changed to %0.2f on channel %d.' % (power, c))
        else:
            raise pvsim.PVSimError('Power was not changed.')

    def profile_load(self, profile_name):
        if profile_name != 'None' and profile_name is not None:
            self.ts.log('Loading irradiance profile %s' % profile_name)
            self.profile_name = profile_name
            profiles = self.tsas.profiles_get()
            if profile_name not in profiles:
                self.tsas.profile(profile_name)

            if self.tsas is not None:
                for c in self.channel:
                    channel = self.tsas.channels[c]
                    channel.profile_set(profile_name)
                    self.ts.log('TerraSAS Profile is configured.')
            else:
                raise pvsim.PVSimError('TerraSAS Profile was not changed.')
        else:
            self.ts.log('No irradiance profile loaded')

    def power_on(self):
        if self.tsas is not None:
            for c in self.channel:
                channel = self.tsas.channels[c]
                # turn on output if off
                if not channel.output_is_on():
                    channel.output_set_on()
                self.ts.log('TerraSAS channel %d turned on' % c)
        else:
            raise pvsim.PVSimError('Not initialized')

    def power_off(self):
        if self.tsas is not None:
            for c in self.channel:
                channel = self.tsas.channels[c]
                # turn off output if on
                if channel.output_is_on():
                    channel.output_set_off()
                self.ts.log('TerraSAS channel %d turned off' % c)
        else:
            raise pvsim.PVSimError('Not initialized')

    def profile_start(self):
        if self.tsas is not None:
            profile_name = self.profile_name
            if profile_name != 'None' and profile_name is not None:
                for c in self.channel:
                    channel = self.tsas.channels[c]
                    channel.profile_start()
                    self.ts.log('Starting PV profile')
        else:
            raise pvsim.PVSimError('PV Sim not initialized')

if __name__ == "__main__":
    pass