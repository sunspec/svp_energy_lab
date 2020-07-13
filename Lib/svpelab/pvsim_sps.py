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
from . import device_pvsim_sps as sps
from . import pvsim

sps_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'SPS'
}

def pvsim_info():
    return sps_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = sps_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)

    info.param(pname('comm'), label='Communication Interface', default='VISA', values=['Network', 'VISA'])
    info.param(pname('visa_id'), label='VISA ID', default='GPIB1::19::INSTR',
               active=pname('comm'),  active_value='VISA')
    info.param(pname('ipaddr'), label='IP Address', default='192.168.0.167',
               active=pname('comm'),  active_value='Network')

    info.param(pname('curve_type'), label='IV Curve Type', default='EN50530',
               values=['Diode Model', 'EN50530', 'Vmp/Imp'])

    info.param(pname('overvoltage'), label='Overvoltage Protection Level (V)', default=660.0)

    info.param(pname('pmp'), label='EN50530 MPP Power (W)', default=3000.0,
               active=pname('curve_type'),  active_value='EN50530')
    info.param(pname('vmp'), label='EN50530 MPP Voltage (V)', default=460.0,
               active=pname('curve_type'),  active_value='EN50530')

    info.param(pname('voc'), label='Voc (V)', default=65.0, active=pname('curve_type'),  active_value=['Vmp/Imp'])
    info.param(pname('isc'), label='Isc (A)', default=2.5, active=pname('curve_type'),  active_value=['Vmp/Imp'])

    # Vmp/Imp parameters
    info.param(pname('vmp2'), label='MPP Voltage (V)', default=50.0,
               active=pname('curve_type'),  active_value='Vmp/Imp')
    info.param(pname('imp'), label='MPP Current (A)', default=2.3,
               active=pname('curve_type'),  active_value='Vmp/Imp')

    info.param(pname('beta_v'), label='Beta V (%/K)', default=-0.36,
               active=pname('curve_type'),  active_value=['Vmp/Imp'])
    info.param(pname('beta_p'), label='Beta P (%/K)', default=-0.5,
               active=pname('curve_type'),  active_value=['Vmp/Imp'])
    info.param(pname('kfactor_voltage'), label='K Factor V1 (V)', default=60.457,
               active=pname('curve_type'),  active_value=['Vmp/Imp'])
    info.param(pname('kfactor_irradiance'), label='K Factor E1 (W/m^2)', default=200,
               active=pname('curve_type'),  active_value=['Vmp/Imp'])

GROUP_NAME = 'sps'


class PVSim(pvsim.PVSim):

    def __init__(self, ts, group_name):
        pvsim.PVSim.__init__(self, ts, group_name)

        self.ts = ts
        self.sps = None

        try:
            self.comm = self._param_value('comm')
            self.visa_id = self._param_value('visa_id')
            self.ipaddr = self._param_value('ipaddr')

            self.curve_type = self._param_value('curve_type')
            self.v_overvoltage = self._param_value('overvoltage')
            self.pmp = self._param_value('pmp')
            self.vmp = self._param_value('vmp')
            if self.vmp is None:
                self.vmp = self._param_value('vmp2')  # it can only be one of the vmp's
            self.imp = self._param_value('imp')

            self.voc = self._param_value('voc')
            self.isc = self._param_value('isc')
            self.form_factor = self._param_value('form_factor')
            self.beta_v = self._param_value('beta_v')
            self.beta_p = self._param_value('beta_p')
            self.kfactor_voltage = self._param_value('kfactor_voltage')
            self.kfactor_irradiance = self._param_value('kfactor_irradiance')

            self.profile_name = None
            self.sps = sps.SPS(comm=self.comm, visa_id=self.visa_id, ipaddr=self.ipaddr)

            if self.sps.profile_is_active():
                self.sps.profile_abort()

            if self.curve_type == 'Diode Model':  # Not implemented yet
                pass
            elif self.curve_type == 'EN50530':
                # re-add EN50530 curve with active parameters
                self.ts.log('Initializing PV Simulator with Pmp = %d and Vmp = %d.' % (self.pmp, self.vmp))
                self.sps.curve_en50530(pmp=self.pmp, vmp=self.vmp)
                self.sps.curve_set(sps.EN_50530_CURVE)
            elif self.curve_type == 'Vmp/Imp':
                curve_name = self.sps.curve(voc=self.voc, isc=self.isc, vmp=self.vmp, imp=self.imp,
                                beta_v=self.beta_v, beta_p=self.beta_p, kfactor_voltage=self.kfactor_voltage,
                                kfactor_irradiance=self.kfactor_irradiance)
                self.ts.log('Created and saved new IV curve with filename: "%s"' % curve_name)
                self.sps.curve_set(curve_name)  # Add new IV curve to the channel
            else:
                raise pvsim.PVSimError('Invalid curve type: %s' % self.curve_type)

            self.sps.overvoltage_protection_set(voltage=self.v_overvoltage)

        except Exception:
            if self.sps is not None:
                self.sps.close()
            raise

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def close(self):
        if self.sps is not None:
            self.sps.close()
            self.sps = None

    def info(self):
        return self.sps.info()

    def irradiance_set(self, irradiance=1000):
        if self.sps is not None:
            self.sps.irradiance_set(irradiance=irradiance)
            self.ts.log('SPS irradiance changed to %0.2f' % irradiance)
        else:
            raise pvsim.PVSimError('Irradiance was not changed.')

    def power_set(self, power):
        if self.sps is not None:
            if power > self.pmp:
                self.ts.log_warning('Requested power > Pmp so irradiance will be > 1000 W/m^2)')
            # convert to irradiance for now
            irradiance = (power * 1000.)/self.pmp
            self.sps.irradiance_set(irradiance=irradiance)
        else:
            raise pvsim.PVSimError('Power was not changed.')

    def profile_load(self, profile_name):
        if profile_name != 'None' and profile_name is not None:
            self.ts.log('Loading irradiance profile %s' % profile_name)
            self.profile_name = profile_name
            profiles = self.sps.profiles_get()
            if profile_name not in profiles:
                self.sps.profile(profile_name)

            if self.sps is not None:
                self.sps.profile_set(profile_name)
                self.ts.log('SPS Profile is configured.')
            else:
                raise pvsim.PVSimError('SPS Profile was not changed.')
        else:
            self.ts.log('No irradiance profile loaded')

    def power_on(self):
        if self.sps is not None:
            if not self.sps.output_is_on():
                self.sps.output_set_on()
            self.ts.log('SPS turned on')
        else:
            raise pvsim.PVSimError('Not initialized')

    def power_off(self):
        if self.sps is not None:
            if self.sps.output_is_on():
                self.sps.output_set_off()
            self.ts.log('SPS channel %d turned off')
        else:
            raise pvsim.PVSimError('Not initialized')

    def profile_start(self):
        if self.sps is not None:
            profile_name = self.profile_name
            if profile_name != 'None' and profile_name is not None:
                self.profile_start()
                self.ts.log('Starting PV profile')
        else:
            raise pvsim.PVSimError('PV Sim not initialized')

if __name__ == "__main__":
    pass