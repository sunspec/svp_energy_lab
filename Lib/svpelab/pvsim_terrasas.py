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
from svpelab import device_terrasas as terrasas
from . import pvsim

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
    info.param(pname('curve_type'), label='IV Curve Type', default='EN50530',
               values=['EN50530', 'Name', 'Fill Factor', 'Vmp/Imp'])

    info.param(pname('overvoltage'), label='Overvoltage Protection Level (V)', default=660.0)

    info.param(pname('pmp'), label='EN50530 MPP Power (W)', default=3000.0,
               active=pname('curve_type'),  active_value='EN50530')
    info.param(pname('vmp'), label='EN50530 MPP Voltage (V)', default=460.0,
               active=pname('curve_type'),  active_value='EN50530')

    info.param(pname('filename'), label='IV Curve Name', default='BP Solar - BP 3230T (60 cells)',
               active=pname('curve_type'),  active_value='Name')

    info.param(pname('voc'), label='Voc (V)', default=65.0,
               active=pname('curve_type'),  active_value=['Vmp/Imp', 'Fill Factor'])
    info.param(pname('isc'), label='Isc (A)', default=2.5,
               active=pname('curve_type'),  active_value=['Vmp/Imp', 'Fill Factor'])

    # can choose between Vmp/Imp or Fill Factor
    info.param(pname('vmp2'), label='MPP Voltage (V)', default=50.0,
               active=pname('curve_type'),  active_value='Vmp/Imp')
    info.param(pname('imp'), label='MPP Current (A)', default=2.3,
               active=pname('curve_type'),  active_value='Vmp/Imp')

    info.param(pname('form_factor'), label='Form Factor (Fill Factor)', default=0.71,
               active=pname('curve_type'),  active_value=['Fill Factor'])

    info.param(pname('beta_v'), label='Beta V (%/K)', default=-0.36,
               active=pname('curve_type'),  active_value=['Vmp/Imp', 'Fill Factor'])
    info.param(pname('beta_p'), label='Beta P (%/K)', default=-0.5,
               active=pname('curve_type'),  active_value=['Vmp/Imp', 'Fill Factor'])
    info.param(pname('kfactor_voltage'), label='K Factor V1 (V)', default=60.457,
               active=pname('curve_type'),  active_value=['Vmp/Imp', 'Fill Factor'])
    info.param(pname('kfactor_irradiance'), label='K Factor E1 (W/m^2)', default=200,
               active=pname('curve_type'),  active_value=['Vmp/Imp', 'Fill Factor'])

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
            self.curve_type = self._param_value('curve_type')
            self.v_overvoltage = self._param_value('overvoltage')
            self.pmp = self._param_value('pmp')
            self.vmp = self._param_value('vmp')
            if self.vmp is None:
                self.vmp = self._param_value('vmp2')  # it can only be one of the vmp's
            self.imp = self._param_value('imp')
            self.filename = self._param_value('filename')
            if self.filename is None:
                self.filename = terrasas.SVP_CURVE
            self.voc = self._param_value('voc')
            self.isc = self._param_value('isc')
            self.form_factor = self._param_value('form_factor')
            self.beta_v = self._param_value('beta_v')
            self.beta_p = self._param_value('beta_p')
            self.kfactor_voltage = self._param_value('kfactor_voltage')
            self.kfactor_irradiance = self._param_value('kfactor_irradiance')

            self.channel = []
            self.irr_start = self._param_value('irr_start')
            chans = str(self._param_value('channel')).split(',')
            for c in chans:
                try:
                    self.channel.append(int(c))
                except ValueError:
                    raise pvsim.PVSimError('Invalid channel number: %s' % c)

            self.profile_name = None
            self.tsas = terrasas.TerraSAS(ipaddr=self.ipaddr)
            self.tsas.scan()

            for c in self.channel:
                channel = self.tsas.channels[c]
                if channel.profile_is_active():
                    channel.profile_abort()

                if self.curve_type == 'EN50530':
                    # re-add EN50530 curve with active parameters
                    self.ts.log('Initializing PV Simulator with Pmp = %d and Vmp = %d.' % (self.pmp, self.vmp))
                    self.tsas.curve_en50530(pmp=self.pmp, vmp=self.vmp)
                    channel.curve_set(terrasas.EN_50530_CURVE)
                elif self.curve_type == 'Name':
                    self.tsas.curve(filename=self.filename)
                    channel.curve_set(self.filename)
                elif self.curve_type == 'Fill Factor':
                    curve_name = self.tsas.curve(voc=self.voc, isc=self.isc, form_factor=self.form_factor,
                                    beta_v=self.beta_v, beta_p=self.beta_p, kfactor_voltage=self.kfactor_voltage,
                                    kfactor_irradiance=self.kfactor_irradiance)
                    self.ts.log('Created and saved new IV curve with filename: "%s"' % curve_name)
                    channel.curve_set(curve_name)  # Add new IV curve to the channel
                elif self.curve_type == 'Vmp/Imp':
                    curve_name = self.tsas.curve(voc=self.voc, isc=self.isc, vmp=self.vmp, imp=self.imp,
                                    beta_v=self.beta_v, beta_p=self.beta_p, kfactor_voltage=self.kfactor_voltage,
                                    kfactor_irradiance=self.kfactor_irradiance)
                    self.ts.log('Created and saved new IV curve with filename: "%s"' % curve_name)
                    channel.curve_set(curve_name)  # Add new IV curve to the channel
                else:
                    raise pvsim.PVSimError('Invalid curve type: %s' % self.curve_type)

                channel.overvoltage_protection_set(voltage=self.v_overvoltage)

        except Exception:
            if self.tsas is not None:
                self.tsas.close()
            raise

    def iv_curve_config(self, pmp, vmp):
        if self.tsas is not None:
            count = len(self.channel)
            if count > 1:
                pmp = pmp/count
            for c in self.channel:
                channel = self.tsas.channels[c]
                if channel.profile_is_active():
                    channel.profile_abort()

                if self.curve_type == 'EN50530':
                    # re-add EN50530 curve with active parameters
                    self.ts.log('Initializing PV Simulator (Channel %s) with Pmp = %d and Vmp = %d.' %
                                (c, self.pmp, self.vmp))
                    self.tsas.curve_en50530(pmp=pmp, vmp=vmp)
                    channel.curve_set(terrasas.EN_50530_CURVE)
                else:
                    raise pvsim.PVSimError('Invalid curve type: %s' % self.curve_type)

                channel.overvoltage_protection_set(voltage=self.v_overvoltage)

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
            for c in self.channel:
                if c is not None:
                    channel = self.tsas.channels[c]
                    channel.irradiance_set(irradiance=irradiance)
                    self.ts.log('TerraSAS irradiance changed to %0.2f on channel %d.' % (irradiance, c))
                else:
                    raise pvsim.PVSimError('Simulation irradiance not specified because there is no channel specified.')
        else:
            raise pvsim.PVSimError('Irradiance was not changed.')

    def measurements_get(self):
        """
        Measure the voltage, current, and power of all channels - calculate the average voltage, total current, and
        total power

        :return: dictionary with dc power data with keys: 'DC_V', 'DC_I', and 'DC_P'
        """

        voltage = 0.
        current = 0.
        power = 0.
        n_channels = 0

        if self.tsas is not None:
            # spread across active channels
            for c in self.channel:
                n_channels += 1
                if c is not None:
                    channel = self.tsas.channels[c]
                    meas = channel.measurements_get()
                    voltage += meas['DC_V']
                    current += meas['DC_I']
                    power += meas['DC_P']
                else:
                    raise pvsim.PVSimError('No measurement data because there is no channel specified.')
            avg_voltage = voltage/float(n_channels)
        else:
            raise pvsim.PVSimError('Could not collect the current, voltage, or power from the TerraSAS.')

        total_meas = {'DC_V': avg_voltage, 'DC_I': current, 'DC_P': power}
        return total_meas

    def power_set(self, power):
        if self.tsas is not None:
            # spread across active channels
            count = len(self.channel)
            if count > 1:
                power = power/count
            if power > self.pmp:
                self.ts.log_warning('Requested power > Pmp so irradiance will be > 1000 W/m^2)')
            # convert to irradiance for now
            irradiance = (power * 1000)/self.pmp
            for c in self.channel:
                if c is not None:
                    channel = self.tsas.channels[c]
                    channel.irradiance_set(irradiance=irradiance)
                    self.ts.log('TerraSAS power output changed to %0.2f on channel %d.' % (power, c))
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
                    self.ts.log('TerraSAS Profile is configured on Channel %d' % c)
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
                    self.ts.log('Starting PV profile on Channel %d' % c)
        else:
            raise pvsim.PVSimError('PV Sim not initialized')

    def profile_stop(self):
        if self.tsas is not None:
            for c in self.channel:
                channel = self.tsas.channels[c]
                if channel.profile_is_active():
                    channel.profile_abort()
                    self.ts.log('Stopping PV profile on Channel %d' % c)
                else:
                    self.ts.log('Did not stop PV profile because it was not running on Channel %d' % c)
        else:
            raise pvsim.PVSimError('PV Sim not initialized')

    def measure_power(self):
        """
        Get the current, voltage, and power from the TerraSAS
        returns: dictionary with power data with keys: 'DC_V', 'DC_I', and 'DC_P'
        """
        dc_power_data = {'DC_I': 0., 'DC_V': 0., 'DC_P': 0.}
        if self.tsas is not None:
            for c in self.channel:
                channel = self.tsas.channels[c]
                chan_data = channel.measurements_get()
                # self.ts.log_debug('chan_data: %s' % chan_data)
                dc_power_data['DC_I'] += chan_data['DC_I']
                dc_power_data['DC_V'] += chan_data['DC_V']
                dc_power_data['DC_P'] += chan_data['DC_P']

            return dc_power_data
        else:
            raise pvsim.PVSimError('PV Sim not initialized')

if __name__ == "__main__":
    pass