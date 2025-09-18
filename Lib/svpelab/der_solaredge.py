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

import sunspec.core.client as client
import sunspec.core.util as util

from . import der
import script

solaredge_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'SolarEdge'
}

def der_info():
    return solaredge_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = solaredge_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('ifc_type'), label='Interface Type', default=client.RTU, values=[client.RTU, client.TCP, client.MAPPED])
    # RTU parameters
    info.param(pname('ifc_name'), label='Interface Name', default='COM3',  active=pname('ifc_type'), active_value=[client.RTU],
               desc='Select the communication port from the UMS computer to the EUT.')
    info.param(pname('baudrate'), label='Baud Rate', default=9600, values=[9600, 19200], active=pname('ifc_type'),
               active_value=[client.RTU])
    info.param(pname('parity'), label='Parity', default='N', values=['N', 'E'], active=pname('ifc_type'),
               active_value=[client.RTU])
    # TCP parameters
    info.param(pname('ipaddr'), label='IP Address', default='134.253.142.44', active=pname('ifc_type'),
               active_value=[client.TCP])
    info.param(pname('ipport'), label='IP Port', default=502, active=pname('ifc_type'), active_value=[client.TCP])
    # Mapped parameters
    info.param(pname('map_name'), label='Map File', default='mbmap.xml',active=pname('ifc_type'),
               active_value=[client.MAPPED], ptype=script.PTYPE_FILE)
    info.param(pname('slave_id'), label='Slave Id', default=1)

GROUP_NAME = 'solaredge'

class DER(der.DER):

    def __init__(self, ts, group_name):
        der.DER.__init__(self, ts, group_name)
        self.inv = None

    def param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):
        self.open()

    def open(self):
        ifc_type = self.param_value('ifc_type')
        ifc_name = self.param_value('ifc_name')
        if ifc_type == client.MAPPED:
            ifc_name = self.param_value('map_name')
        baudrate = self.param_value('baudrate')
        parity = self.param_value('parity')
        ipaddr = self.param_value('ipaddr')
        ipport = self.param_value('ipport')
        slave_id = self.param_value('slave_id')

        self.inv = client.SunSpecClientDevice(ifc_type, slave_id=slave_id, name=ifc_name,
                                              baudrate=baudrate, parity=parity, ipaddr=ipaddr,
                                              ipport=ipport)

    def close(self):
        if self.inv is not None:
            self.inv.close()
            self.inv = None

    def info(self):
        """ Get DER device information.

        Params:
            Manufacturer
            Model
            Version
            Options
            SerialNumber

        :return: Dictionary of information elements.
        """

        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'common' in self.inv.models:
                params = {}
                self.inv.common[1].read()
                params['Manufacturer'] = self.inv.common[1].Mn
                params['Model'] = self.inv.common[1].Md
                params['Options'] = self.inv.common[1].Opt
                params['Version'] = self.inv.common[1].Vr
                params['SerialNumber'] = self.inv.common[1].SN
            else:
                params = None
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def nameplate(self):
        """ Get nameplate ratings.

        Params:
            WRtg - Active power maximum rating
            VARtg - Apparent power maximum rating
            VArRtgQ1, VArRtgQ2, VArRtgQ3, VArRtgQ4 - VAr maximum rating for each quadrant
            ARtg - Current maximum rating
            PFRtgQ1, PFRtgQ2, PFRtgQ3, PFRtgQ4 - Power factor rating for each quadrant
            WHRtg - Energy maximum rating
            AhrRtg - Amp-hour maximum rating
            MaxChaRte - Charge rate maximum rating
            MaxDisChaRte - Discharge rate maximum rating

        :return: Dictionary of nameplate ratings.
        """

        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'nameplate' in self.inv.models:
                params = {}
                self.inv.nameplate.read()
                params['WRtg'] = self.inv.nameplate.WRtg
                params['VARtg'] = self.inv.nameplate.VARtg
                params['VArRtgQ1'] = self.inv.nameplate.VArRtgQ1
                params['VArRtgQ2'] = self.inv.nameplate.VArRtgQ2
                params['VArRtgQ3'] = self.inv.nameplate.VArRtgQ3
                params['VArRtgQ4'] = self.inv.nameplate.VArRtgQ4
                params['ARtg'] = self.inv.nameplate.ARtg
                params['PFRtgQ1'] = self.inv.nameplate.PFRtgQ1
                params['PFRtgQ2'] = self.inv.nameplate.PFRtgQ2
                params['PFRtgQ3'] = self.inv.nameplate.PFRtgQ3
                params['PFRtgQ4'] = self.inv.nameplate.PFRtgQ4
                params['WHRtg'] = self.inv.nameplate.WHRtg
                params['AhrRtg'] = self.inv.nameplate.AhrRtg
                params['MaxChaRte'] = self.inv.nameplate.MaxChaRte
                params['MaxDisChaRte'] = self.inv.nameplate.MaxDisChaRte
            else:
                params = None
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def measurements(self):
        """ Get measurement data.

        Params:

        :return: Dictionary of measurement data.
        """

        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'inverter' in self.inv.models:
                params = {}
                self.inv.inverter.read()
                params['A'] = self.inv.inverter.A
                params['AphA'] = self.inv.inverter.AphA
                params['AphB'] = self.inv.inverter.AphB
                params['AphC'] = self.inv.inverter.AphC
                params['PPVphAB'] = self.inv.inverter.PPVphAB
                params['PPVphBC'] = self.inv.inverter.PPVphBC
                params['PPVphCA'] = self.inv.inverter.PPVphCA
                params['PhVphA'] = self.inv.inverter.PhVphA
                params['PhVphB'] = self.inv.inverter.PhVphB
                params['PhVphC'] = self.inv.inverter.PhVphC
                params['W'] = self.inv.inverter.W
                params['Hz'] = self.inv.inverter.Hz
                params['VA'] = self.inv.inverter.VA
                params['VAr'] = self.inv.inverter.VAr
                params['PF'] = self.inv.inverter.PF
                params['WH'] = self.inv.inverter.WH
                params['DCA'] = self.inv.inverter.DCA
                params['DCV'] = self.inv.inverter.DCV
                params['DCW'] = self.inv.inverter.DCW
                params['TmpCab'] = self.inv.inverter.TmpCab
                params['TmpSnk'] = self.inv.inverter.TmpSnk
                params['TmpTrns'] = self.inv.inverter.TmpTrns
                params['TmpOt'] = self.inv.inverter.TmpOt
                params['St'] = self.inv.inverter.St
                params['StVnd'] = self.inv.inverter.StVnd
                params['Evt1'] = self.inv.inverter.Evt1
                params['Evt2'] = self.inv.inverter.Evt2
                params['EvtVnd1'] = self.inv.inverter.EvtVnd1
                params['EvtVnd2'] = self.inv.inverter.EvtVnd2
                params['EvtVnd3'] = self.inv.inverter.EvtVnd3
                params['EvtVnd4'] = self.inv.inverter.EvtVnd4
            else:
                params = None
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def settings(self, params=None):
        """
        Get/set capability settings.

        Params:
            WMax - Active power maximum
            VRef - Reference voltage
            VRefOfs - Reference voltage offset
            VMax - Voltage maximum
            VMin - Voltage minimum
            VAMax - Apparent power maximum
            VArMaxQ1, VArMaxQ2, VArMaxQ3, VArMaxQ4 - VAr maximum for each quadrant
            WGra - Default active power ramp rate
            PFMinQ1, PFMinQ2, PFMinQ3, PFMinQ4
            VArAct

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for connect.
        """

        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                raise der.DERError('DER settings not supported.')
            else:
                params = {}
        except Exception as e:
            raise der.DERError(str(e))
        return params

    def conn_status(self, params=None):
        """ Get status of controls (binary True if active).
        :return: Dictionary of active controls.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            params = {}
        except Exception as e:
            raise der.DERError(str(e))
        return params


    def controls_status(self, params=None):
        """ Get status of controls (binary True if active).
        :return: Dictionary of active controls.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            params = {}
        except Exception as e:
            raise der.DERError(str(e))
        return params


    def connect(self, params=None):
        """ Get/set connect/disconnect function settings.

        Params:
            Conn - Connected (True/False)
            WinTms - Randomized start time delay in seconds
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for connect.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                raise der.DERError('DER settings not supported.')
            else:
                params = {}
        except Exception as e:
            raise der.DERError(str(e))
        return params


    def fixed_pf(self, params=None):
        """ Get/set fixed power factor control settings.

        Params:
            Ena - Enabled (True/False)
            PF - Power Factor set point
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for fixed factor.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        self.inv.device.write(0xf100, util.u16_to_data(1))  # F142 R/W AdvancedPwrControlEn Int32 0-1
                    else:
                        self.inv.device.write(0xf100, util.u16_to_data(0))  # F142 R/W AdvancedPwrControlEn Int32 0-1
                wmax = params.get('PF')
                if wmax is not None:
                    self.inv.device.write(0xf002, util.float32_to_data(params.get('PF')))
            else:
                params = {}
                if util.data_to_u16(self.inv.device.read(0xf142, 1)) == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['PF'] = util.data_to_float(self.inv.device.read(0xf002, 2))

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def limit_max_power(self, params=None):
        """ Get/set max active power control settings.

        Params:
            Ena - Enabled (True/False)
            WMaxPct - Active power maximum as percentage of WMax

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for limit max power.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        self.inv.device.write(0xf100, util.u16_to_data(1))  # F142 R/W AdvancedPwrControlEn Int32 0-1
                    else:
                        self.inv.device.write(0xf100, util.u16_to_data(0))  # F142 R/W AdvancedPwrControlEn Int32 0-1
                wmax = params.get('WMaxPct')
                if wmax is not None:
                    self.ts.log('Changing power to %d' % params.get('WMaxPct'))
                    self.inv.device.write(0xf002, util.u16_to_data(params.get('WMaxPct')))
            else:
                params = {}
                if util.data_to_u16(self.inv.device.read(0xf100, 1)) == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['WMaxPct'] = util.data_to_u16(self.inv.device.read(0xf001, 1))

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def volt_var(self, params=None):
        """ Get/set volt/var control

        Params:
            Ena - Enabled (True/False)
            ActCrv - Active curve number (0 - no active curve)
            NCrv - Number of curves supported
            NPt - Number of points supported per curve
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for volt/var control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'volt_var' in self.inv.models:
                if params is not None:
                    ena = params.get('Ena')
                    if ena is not None:
                        if ena is True:
                            self.inv.volt_var.ModEna = 1
                        else:
                            self.inv.volt_var.ModEna = 0
                    act_crv = params.get('ActCrv')
                    if act_crv is not None:
                        self.inv.volt_var.ActCrv = act_crv
                    else:
                        act_crv = 1
                    curve = params.get('curve')
                    if curve is not None:
                        self.volt_var_curve(id=act_crv, params=curve)
                    win_tms = params.get('WinTms')
                    if win_tms is not None:
                        self.inv.volt_var.WinTms = win_tms
                    rmp_tms = params.get('RmpTms')
                    if rmp_tms is not None:
                        self.inv.volt_var.RmpTms = rmp_tms
                    rvrt_tms = params.get('RvrtTms')
                    if rvrt_tms is not None:
                        self.inv.volt_var.RvrtTms = rvrt_tms
                    self.inv.volt_var.write()
                else:
                    params = {}
                    self.inv.volt_var.read()
                    if self.inv.volt_var.ModEna == 0:
                        params['Ena'] = False
                    else:
                        params['Ena'] = True
                    params['ActCrv'] = self.inv.volt_var.ActCrv
                    params['NCrv'] = self.inv.volt_var.NCrv
                    params['NPt'] = self.inv.volt_var.NPt
                    params['WinTms'] = self.inv.volt_var.WinTms
                    params['RmpTms'] = self.inv.volt_var.RmpTms
                    params['RvrtTms'] = self.inv.volt_var.RvrtTms
                    if self.inv.volt_var.ActCrv != 0:
                        params['curve'] = self.volt_var_curve(id=self.inv.volt_var.ActCrv)
            else:
                params = None
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def volt_var_curve(self, id, params=None):
        """ Get/set volt/var curve
            v [] - List of voltage curve points
            var [] - List of var curve points based on DeptRef
            DeptRef - Dependent reference type: 'VAR_MAX_PCT', 'VAR_AVAL_PCT', 'VA_MAX_PCT', 'W_MAX_PCT'
            RmpTms - Ramp timer
            RmpDecTmm - Ramp decrement timer
            RmpIncTmm - Ramp increment timer

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for volt/var curve control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'volt_var' in self.inv.models:
                self.inv.volt_var.read()
                if int(id) > int(self.inv.volt_var.NCrv):
                    raise der.DERError('Curve id out of range: %s' % (id))
                curve = self.inv.volt_var.curve[id]

                if params is not None:
                    dept_ref = params.get('DeptRef')
                    if dept_ref is not None:
                        dept_ref_id = volt_var_dept_ref.get(dept_ref)
                        if dept_ref_id is None:
                            raise der.DERError('Unsupported DeptRef: %s' % (dept_ref))

                        curve.DeptRef = dept_ref_id
                    rmp_tms = params.get('RmpTms')
                    if rmp_tms is not None:
                        curve.RmpTms = rmp_tms
                    rmp_dec_tmm = params.get('RmpDecTmm')
                    if rmp_dec_tmm is not None:
                        curve.RmpDecTmm = rmp_dec_tmm
                    rmp_inc_tmm = params.get('RmpIncTmm')
                    if rmp_inc_tmm is not None:
                        curve.RmpIncTmm = rmp_inc_tmm

                    n_pt = int(self.inv.volt_var.NPt)
                    # set voltage points
                    v = params.get('v')
                    if v is not None:
                        v_len = len(v)
                        if v_len > n_pt:
                            raise der.DERError('Voltage point count out of range: %d' % (v_len))
                        for i in range(v_len):  # SunSpec point index starts at 1
                            v_point = 'V%d' % (i + 1)
                            setattr(curve, v_point, v[i])
                    # set var points
                    var = params.get('var')
                    if var is not None:
                        var_len = len(var)
                        if var_len > n_pt:
                            raise der.DERError('VAr point count out of range: %d' % (var_len))
                        for i in range(var_len):  # SunSpec point index starts at 1
                            var_point = 'VAr%d' % (i + 1)
                            setattr(curve, var_point, var[i])

                    self.inv.volt_var.write()
                else:
                    params = {}
                    act_pt = curve.ActPt
                    dept_ref = volt_var_dept_ref.get(curve.DeptRef)
                    if dept_ref is None:
                        raise der.DERError('DeptRef out of range: %s' % (dept_ref))
                    params['DeptRef'] = dept_ref
                    params['RmpTms'] = curve.RmpTms
                    params['RmpDecTmm'] = curve.RmpDecTmm
                    params['RmpIncTmm'] = curve.RmpIncTmm
                    params['id'] = id  #also store the curve number

                    v = []
                    var = []
                    for i in range(1, act_pt + 1):  # SunSpec point index starts at 1
                        v_point = 'V%d' % i
                        var_point = 'VAr%d' % i
                        v.append(getattr(curve, v_point))
                        var.append(getattr(curve, var_point))
                    params['v'] = v
                    params['var'] = var
            else:
                params = None

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def freq_watt(self, params=None):
        """ Get/set freq/watt control

        Params:
            Ena - Enabled (True/False)
            ActCrv - Active curve number (0 - no active curve)
            NCrv - Number of curves supported
            NPt - Number of points supported per curve
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for freq/watt control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'freq_watt' in self.inv.models:
                if params is not None:
                    ena = params.get('Ena')
                    if ena is not None:
                        if ena is True:
                            self.inv.freq_watt.ModEna = 1
                        else:
                            self.inv.freq_watt.ModEna = 0
                    act_crv = params.get('ActCrv')
                    if act_crv is not None:
                        self.inv.freq_watt.ActCrv = act_crv
                    else:
                        act_crv = 1
                    curve = params.get('curve')
                    if curve is not None:
                        self.freq_watt_curve(id=act_crv, params=curve)
                    win_tms = params.get('WinTms')
                    if win_tms is not None:
                        self.inv.freq_watt.WinTms = win_tms
                    rmp_tms = params.get('RmpTms')
                    if rmp_tms is not None:
                        self.inv.freq_watt.RmpTms = rmp_tms
                    rvrt_tms = params.get('RvrtTms')
                    if rvrt_tms is not None:
                        self.inv.freq_watt.RvrtTms = rvrt_tms
                    self.inv.freq_watt.write()
                else:
                    params = {}
                    self.inv.freq_watt.read()
                    if self.inv.freq_watt.ModEna == 0:
                        params['Ena'] = False
                    else:
                        params['Ena'] = True
                    params['ActCrv'] = self.inv.freq_watt.ActCrv
                    params['NCrv'] = self.inv.freq_watt.NCrv
                    params['NPt'] = self.inv.freq_watt.NPt
                    params['WinTms'] = self.inv.freq_watt.WinTms
                    params['RmpTms'] = self.inv.freq_watt.RmpTms
                    params['RvrtTms'] = self.inv.freq_watt.RvrtTms
                    if self.inv.freq_watt.ActCrv != 0:
                        params['curve'] = self.freq_watt_curve(id=self.inv.freq_watt.ActCrv)
            else:
                params = None
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def freq_watt_curve(self, id, params=None):
        """ Get/set volt/var curve
            hz [] - List of frequency curve points
            w [] - List of power curve points
            CrvNam - Optional description for curve. (Max 16 chars)
            RmpPT1Tms - The time of the PT1 in seconds (time to accomplish a change of 95%).
            RmpDecTmm - Ramp decrement timer
            RmpIncTmm - Ramp increment timer
            RmpRsUp - The maximum rate at which the power may be increased after releasing the frozen value of
                      snap shot function.
            SnptW - 1=enable snapshot/capture mode
            WRef - Reference active power (default = WMax).
            WRefStrHz - Frequency deviation from nominal frequency at the time of the snapshot to start constraining
                        power output.
            WRefStopHz - Frequency deviation from nominal frequency at which to release the power output.
            ReadOnly - 0 = READWRITE, 1 = READONLY

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for freq/watt curve.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'freq_watt' in self.inv.models:
                self.inv.freq_watt.read()
                if int(id) > int(self.inv.freq_watt.NCrv):
                    raise der.DERError('Curve id out of range: %s' % (id))
                curve = self.inv.freq_watt.curve[id]

                if params is not None:
                    crv_nam = params.get('CrvNam')
                    if crv_nam is not None:
                        curve.CrvNam = crv_nam
                    rmp_tms = params.get('RmpPT1Tms')
                    if rmp_tms is not None:
                        curve.RmpPT1Tms = rmp_tms
                    rmp_dec_tmm = params.get('RmpDecTmm')
                    if rmp_dec_tmm is not None:
                        curve.RmpDecTmm = rmp_dec_tmm
                    rmp_inc_tmm = params.get('RmpIncTmm')
                    if rmp_inc_tmm is not None:
                        curve.RmpIncTmm = rmp_inc_tmm
                    rmp_rs_up = params.get('RmpRsUp')
                    if rmp_rs_up is not None:
                        curve.RmpRsUp = rmp_rs_up
                    snpt_w = params.get('SnptW')
                    if snpt_w is not None:
                        curve.SnptW = snpt_w
                    w_ref = params.get('WRef')
                    if w_ref is not None:
                        curve.WRef = w_ref
                    w_ref_str_hz = params.get('WRefStrHz')
                    if w_ref_str_hz is not None:
                        curve.WRefStrHz = w_ref_str_hz
                    w_ref_stop_hz = params.get('WRefStopHz')
                    if w_ref_stop_hz is not None:
                        curve.WRefStopHz = w_ref_stop_hz
                    read_only = params.get('ReadOnly')
                    if read_only is not None:
                        curve.ReadOnly = read_only

                    n_pt = int(self.inv.freq_watt.NPt)
                    # set freq points
                    hz = params.get('hz')
                    if hz is not None:
                        hz_len = len(hz)
                        if hz_len > n_pt:
                            raise der.DERError('Freq point count out of range: %d' % (hz_len))
                        for i in range(hz_len):  # SunSpec point index starts at 1
                            hz_point = 'Hz%d' % (i + 1)
                            setattr(curve, hz_point, hz[i])
                    # set watt points
                    w = params.get('w')
                    if w is not None:
                        w_len = len(w)
                        if w_len > n_pt:
                            raise der.DERError('Watt point count out of range: %d' % (w_len))
                        for i in range(w_len):  # SunSpec point index starts at 1
                            w_point = 'W%d' % (i + 1)
                            setattr(curve, w_point, w[i])

                    self.inv.freq_watt.write()
                else:
                    params = {}
                    act_pt = curve.ActPt
                    params['CrvNam'] = curve.CrvNam
                    params['RmpPT1Tms'] = curve.RmpPT1Tms
                    params['RmpDecTmm'] = curve.RmpDecTmm
                    params['RmpIncTmm'] = curve.RmpIncTmm
                    params['RmpRsUp'] = curve.RmpRsUp
                    params['SnptW'] = curve.SnptW
                    params['WRef'] = curve.WRef
                    params['WRefStrHz'] = curve.WRefStrHz
                    params['WRefStopHz'] = curve.WRefStopHz
                    params['ReadOnly'] = curve.ReadOnly
                    params['id'] = id  #also store the curve number
                    hz = []
                    w = []
                    for i in range(1, act_pt + 1):  # SunSpec point index starts at 1
                        hz_point = 'Hz%d' % i
                        w_point = 'VAr%d' % i
                        hz.append(getattr(curve, hz_point))
                        w.append(getattr(curve, w_point))
                    params['hz'] = hz
                    params['w'] = w
            else:
                params = None

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def freq_watt_param(self, params=None):
        """ Get/set frequency-watt with parameters

        Params:
            Ena - Enabled (True/False)
            HysEna - Enable hysterisis (True/False)
            WGra - The slope of the reduction in the maximum allowed watts output as a function of frequency.
            HzStr - The frequency deviation from nominal frequency (ECPNomHz) at which a snapshot of the instantaneous
                    power output is taken to act as the CAPPED power level (PM) and above which reduction in power
                    output occurs.
            HzStop - The frequency deviation from nominal frequency (ECPNomHz) at which curtailed power output may
                    return to normal and the cap on the power level value is removed.
            HzStopWGra - The maximum time-based rate of change at which power output returns to normal after having
                         been capped by an over frequency event.

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for frequency-watt with parameters control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'freq_watt' in self.inv.models:
                self.inv.freq_watt.read()
                if params is not None:
                    ena = params.get('Ena')
                    if ena is not None:
                        if ena is True:
                            self.inv.freq_watt_param.ModEna = 1
                        else:
                            self.inv.freq_watt_param.ModEna = 0
                    hysena = params.get('HysEna')
                    if hysena is not None:
                        if hysena is True:
                            self.inv.freq_watt_param.HysEna = 1
                        else:
                            self.inv.freq_watt_param.HysEna = 0

                    w_gra = params.get('WGra')
                    if w_gra is not None:
                        self.inv.freq_watt_param.WGra = w_gra
                    hz_str = params.get('HzStr')
                    if hz_str is not None:
                        self.inv.freq_watt_param.HzStr = hz_str
                    hz_stop = params.get('HzStop')
                    if hz_stop is not None:
                        self.inv.freq_watt_param.HzStop = hz_stop
                    hz_stop_w_gra = params.get('HzStopWGra')
                    if hz_stop_w_gra is not None:
                        self.inv.freq_watt_param.HzStopWGra = hz_stop_w_gra
                    self.inv.freq_watt_param.write()
                else:
                    params = {}
                    self.inv.hfrtc.read()
                    if self.inv.freq_watt_param.ModEna == 0:
                        params['Ena'] = False
                    else:
                        params['Ena'] = True
                    if self.inv.freq_watt_param.HysEna == 0:
                        params['HysEna'] = False
                    else:
                        params['HysEna'] = True
                    params['WGra'] = self.inv.freq_watt_param.WGra
                    params['HzStr'] = self.inv.freq_watt_param.HzStr
                    params['HzStop'] = self.inv.freq_watt_param.HzStop
                    params['HzStopWGra'] = self.inv.freq_watt_param.HzStopWGra
            else:
                params = None

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def frt_stay_connected_high(self, params=None):
        """ Get/set high frequency ride through (must stay connected curve)

        Params:
            Ena - Enabled (True/False)
            ActCrv - Active curve number (0 - no active curve)
            NCrv - Number of curves supported
            NPt - Number of points supported per curve
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds
            Tms# - Time point in the curve
            Hz# - Frequency point in the curve

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HFRT control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        self.inv.hfrtc.ModEna = 1
                    else:
                        self.inv.hfrtc.ModEna = 0
                act_crv = params.get('ActCrv')
                if act_crv is not None:
                    self.inv.hfrtc.ActCrv = act_crv
                win_tms = params.get('WinTms')
                if win_tms is not None:
                    self.inv.hfrtc.WinTms = win_tms
                rmp_tms = params.get('RmpTms')
                if rmp_tms is not None:
                    self.inv.hfrtc.RmpTms = rmp_tms
                rvrt_tms = params.get('RvrtTms')
                if rvrt_tms is not None:
                    self.inv.hfrtc.RvrtTms = rvrt_tms
                for i in range(1, params['NPt'] + 1):  # Uses the SunSpec indexing rules (start at 1)
                    time_point = 'Tms%d' % i
                    param_time_point = params.get(time_point)
                    if param_time_point is not None:
                        setattr(self.inv.hfrtc.l_curve[h_curve_num], time_point, param_time_point)
                    freq_point = 'F%d' % i
                    param_freq_point = params.get(freq_point)
                    if param_freq_point is not None:
                        setattr(self.inv.hfrtc.l_curve[h_curve_num], freq_point, param_freq_point)
                self.inv.hfrtc.write()
            else:
                params = {}
                self.inv.hfrtc.read()
                if self.inv.hfrtc.ModEna == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['ActCrv'] = self.inv.hfrtc.ActCrv
                params['NCrv'] = self.inv.hfrtc.NCrv
                params['NPt'] = self.inv.hfrtc.NPt
                params['WinTms'] = self.inv.hfrtc.WinTms
                params['RmpTms'] = self.inv.hfrtc.RmpTms
                params['RvrtTms'] = self.inv.hfrtc.RvrtTms

        except Exception as e:
            raise der.DERError(str(e))

        return params


    def frt_stay_connected_low(self, params=None):
        """ Get/set high frequency ride through (must stay connected curve)

        Params:
            Ena - Enabled (True/False)
            ActCrv - Active curve number (0 - no active curve)
            NCrv - Number of curves supported
            NPt - Number of points supported per curve
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds
            Tms# - Time point in the curve
            Hz# - Frequency point in the curve

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HFRT control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        self.inv.lfrtc.ModEna = 1
                    else:
                        self.inv.lfrtc.ModEna = 0
                act_crv = params.get('ActCrv')
                if act_crv is not None:
                    self.inv.lfrtc.ActCrv = act_crv
                win_tms = params.get('WinTms')
                if win_tms is not None:
                    self.inv.lfrtc.WinTms = win_tms
                rmp_tms = params.get('RmpTms')
                if rmp_tms is not None:
                    self.inv.lfrtc.RmpTms = rmp_tms
                rvrt_tms = params.get('RvrtTms')
                if rvrt_tms is not None:
                    self.inv.lfrtc.RvrtTms = rvrt_tms
                for i in range(1, params['NPt'] + 1):  # Uses the SunSpec indexing rules (start at 1)
                    time_point = 'Tms%d' % i
                    param_time_point = params.get(time_point)
                    if param_time_point is not None:
                        setattr(self.inv.hfrtc.l_curve[h_curve_num], time_point, param_time_point)
                    freq_point = 'F%d' % i
                    param_freq_point = params.get(freq_point)
                    if param_freq_point is not None:
                        setattr(self.inv.hfrtc.l_curve[h_curve_num], freq_point, param_freq_point)
                self.inv.hfrtc.write()
            else:
                params = {}
                self.inv.lfrtc.read()
                if self.inv.lfrtc.ModEna == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['ActCrv'] = self.inv.lfrtc.ActCrv
                params['NCrv'] = self.inv.lfrtc.NCrv
                params['NPt'] = self.inv.lfrtc.NPt
                params['WinTms'] = self.inv.lfrtc.WinTms
                params['RmpTms'] = self.inv.lfrtc.RmpTms
                params['RvrtTms'] = self.inv.lfrtc.RvrtTms

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def reactive_power(self, params=None):
        """ Set the reactive power

        Params:
            Ena - Enabled (True/False)
            Q - Reactive power as %Qmax (positive is overexcited, negative is underexcited)
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for Q control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        self.inv.volt_var.ModEna = 1
                    else:
                        self.inv.volt_var.ModEna = 0

                q = params.get('Q')
                if q is not None:
                    self.inv.volt_var.ActCrv = 1  # use curve 1
                    n_pt = int(self.inv.volt_var.NPt)
                    from numpy import linspace
                    v = linspace(90, 110, n_pt)
                    q = [q]*n_pt
                    # Meaning of dependent variable: 1=%WMax 2=%VArMax 3=%VArAval.
                    curve_params = {'DeptRef': 2, 'RmpTms': 0, 'RmpDecTmm': 0, 'RmpIncTmm': 0,
                                    'v': v, 'var': q}
                    if params.get('RmpTms') is not None:
                        curve_params['RmpTms'] = params.get('RmpTms')
                    if params.get('RmpTms') is not None:
                        curve_params['RmpDecTmm'] = params.get('RmpTms')
                        curve_params['RmpIncTmm'] = params.get('RmpTms')
                    self.volt_var_curve(id=self.inv.volt_var.ActCrv, params=curve_params)

                win_tms = params.get('WinTms')
                if win_tms is not None:
                    self.inv.volt_var.WinTms = win_tms
                rmp_tms = params.get('RmpTms')
                if rmp_tms is not None:
                    self.inv.volt_var.RmpTms = rmp_tms
                rvrt_tms = params.get('RvrtTms')
                if rvrt_tms is not None:
                    self.inv.volt_var.RvrtTms = rvrt_tms

                self.inv.volt_var.write()

            else:
                params = {}
                self.inv.volt_var.read()
                if self.inv.volt_var.ModEna == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['WinTms'] = self.inv.volt_var.WinTms
                params['RmpTms'] = self.inv.volt_var.RmpTms
                params['RvrtTms'] = self.inv.volt_var.RvrtTms
                if self.inv.volt_var.ActCrv != 0:
                    params['curve'] = self.volt_var_curve(id=self.inv.volt_var.ActCrv)
                params['Q'] = self.inv.volt_var_curve.var[0]

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def active_power(self, params=None):
        """ Get/set active power of EUT

        Params:
            Ena - Enabled (True/False)
            P - Active power in %Wmax (positive is exporting (discharging), negative is importing (charging) power)
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HFRT control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        # no enable for sunspec
                        pass
                    else:
                        # no enable for sunspec
                        pass

                storage_params = {}
                if params['P'] <= 0:  # "charging"
                    storage_params['InWRte'] = params['P']
                else:  # "discharging"
                    storage_params['OutWRte'] = params['P']

                storage_params['InOutWRte_WinTms'] = params['WinTms']
                storage_params['InOutWRte_RmpTms'] = params['RmpTms']
                storage_params['InOutWRte_RvrtTms'] = params['RvrtTms']

                self.inv.storage(params=storage_params)

            else:
                params = {}
                storage_params = self.inv.storage()
                if storage_params['ChaSt'] == 1:  # "off"
                    params['Ena'] = False
                else:
                    params['Ena'] = True

                if storage_params['StorCtl_Mod'] == 0:  # "charging"
                    params['P'] = storage_params['InWRte']
                else:  # "discharging"
                    params['P'] = storage_params['OutWRte']

                params['WinTms'] = storage_params['InOutWRte_WinTms']
                params['RmpTms'] = storage_params['InOutWRte_RmpTms']
                params['RvrtTms'] = storage_params['InOutWRte_RvrtTms']

        except Exception as e:
            raise der.DERError(str(e))

        return params


    def storage(self, params=None):
        """ Get/set storage parameters

        Params:
            WChaMax - Setpoint for maximum charge.
            WChaGra - Setpoint for maximum charging rate. Default is MaxChaRte.
            WDisChaGra - Setpoint for maximum discharge rate. Default is MaxDisChaRte.
            StorCtl_Mod - Activate hold/discharge/charge storage control mode. Bitfield value.
            VAChaMax - Setpoint for maximum charging VA.
            MinRsvPct - Setpoint for minimum reserve for storage as a percentage of the nominal maximum storage.
            ChaState (R) - Currently available energy as a percent of the capacity rating.
            StorAval (R) - State of charge (ChaState) minus storage reserve (MinRsvPct) times capacity rating (AhrRtg).
            InBatV (R) - Internal battery voltage.
            ChaSt (R) - Charge status of storage device. Enumerated value.
            OutWRte - Percent of max discharge rate.
            InWRte - Percent of max charging rate.
            InOutWRte_WinTms - Time window for charge/discharge rate change.
            InOutWRte_RvrtTms - Timeout period for charge/discharge rate.
            InOutWRte_RmpTms - Ramp time for moving from current setpoint to new setpoint.

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HFRT control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                w_cha_max = params.get('WChaMax')
                if w_cha_max is not None:
                    self.inv.storage.WChaMax = w_cha_max
                w_cha_gra = params.get('WChaGra')
                if w_cha_gra is not None:
                    self.inv.storage.WChaGra = w_cha_gra
                w_dis_cha_gra = params.get('WDisChaGra')
                if w_dis_cha_gra is not None:
                    self.inv.storage.WDisChaGra = w_dis_cha_gra
                stor_ctl_mod = params.get('StorCtl_Mod')
                if stor_ctl_mod is not None:
                    self.inv.storage.StorCtl_Mod = stor_ctl_mod
                va_cha_max = params.get('VAChaMax')
                if va_cha_max is not None:
                    self.inv.storage.VAChaMax = va_cha_max
                min_rsv_pct = params.get('MinRsvPct')
                if min_rsv_pct is not None:
                    self.inv.storage.MinRsvPct = min_rsv_pct
                out_w_rte = params.get('OutWRte')
                if out_w_rte is not None:
                    self.inv.storage.OutWRte = out_w_rte
                in_w_rte = params.get('InWRte')
                if in_w_rte is not None:
                    self.inv.storage.InWRte = in_w_rte
                in_out_w_rte_win_tms = params.get('InOutWRte_WinTms')
                if in_out_w_rte_win_tms is not None:
                    self.inv.storage.InOutWRte_WinTms = in_out_w_rte_win_tms
                in_out_w_rte_rvrt_tms = params.get('InOutWRte_RvrtTms')
                if in_out_w_rte_rvrt_tms is not None:
                    self.inv.storage.InOutWRte_RvrtTms = in_out_w_rte_rvrt_tms
                in_out_w_rte_rmp_tms = params.get('InOutWRte_RmpTms')
                if in_out_w_rte_rmp_tms is not None:
                    self.inv.storage.InOutWRte_RmpTms = in_out_w_rte_rmp_tms

                self.inv.storage.write()

            else:
                params = {}
                self.inv.storage.read()
                params['WChaMax'] = self.inv.volt_var.WChaMax
                params['WChaGra'] = self.inv.volt_var.WChaGra
                params['WDisChaGra'] = self.inv.volt_var.WDisChaGra
                params['StorCtl_Mod'] = self.inv.volt_var.StorCtl_Mod
                params['VAChaMax'] = self.inv.volt_var.VAChaMax
                params['MinRsvPct'] = self.inv.volt_var.MinRsvPct
                params['ChaState'] = self.inv.volt_var.ChaState
                params['StorAval'] = self.inv.volt_var.StorAval
                params['InBatV'] = self.inv.volt_var.InBatV
                params['ChaSt'] = self.inv.volt_var.ChaSt
                params['OutWRte'] = self.inv.volt_var.OutWRte
                params['InWRte'] = self.inv.volt_var.InWRte
                params['InOutWRte_WinTms'] = self.inv.volt_var.InOutWRte_WinTms
                params['InOutWRte_RvrtTms'] = self.inv.volt_var.InOutWRte_RvrtTms
                params['InOutWRte_RmpTms'] = self.inv.volt_var.InOutWRte_RmpTms

        except Exception as e:
            raise der.DERError(str(e))

        return params

