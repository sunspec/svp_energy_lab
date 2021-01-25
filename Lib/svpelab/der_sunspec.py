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
from . import der
import script

sunspec_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'SunSpec'
}

def der_info():
    return sunspec_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = sunspec_info['mode']
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
    info.param(pname('ipaddr'), label='IP Address', default='127.0.0.1', active=pname('ifc_type'),
               active_value=[client.TCP])
    info.param(pname('ipport'), label='IP Port', default=502, active=pname('ifc_type'), active_value=[client.TCP])
    info.param(pname('tls'), label='TLS Client', default=False, active=pname('ifc_type'), active_value=[client.TCP],
               desc='Enable TLS (Modbus/TCP Security).')
    info.param(pname('cafile'), label='CA Certificate', default=None, active=pname('ifc_type'), active_value=[client.TCP],
               desc='Path to certificate authority (CA) certificate to use for validating server certificates.')
    info.param(pname('certfile'), label='Client TLS Certificate', default=None, active=pname('ifc_type'), active_value=[client.TCP],
               desc='Path to client TLS certificate to use for client authentication.')
    info.param(pname('keyfile'), label='Client TLS Key', default=None, active=pname('ifc_type'), active_value=[client.TCP],
               desc='Path to client TLS key to use for client authentication.')
    info.param(pname('insecure_skip_tls_verify'), label='Skip TLS Verification', default=False, active=pname('ifc_type'), active_value=[client.TCP],
               desc='Skip Verification of Server TLS Certificate.')
    # Mapped parameters
    info.param(pname('map_name'), label='Map File', default='mbmap.xml',active=pname('ifc_type'),
               active_value=[client.MAPPED], ptype=script.PTYPE_FILE)
    info.param(pname('slave_id'), label='Slave Id', default=1)

GROUP_NAME = 'sunspec'

volt_var_dept_ref = {
    'W_MAX_PCT': 1,
    'VAR_MAX_PCT': 2,
    'VAR_AVAL_PCT': 3,
    1: 'W_MAX_PCT',
    2: 'VAR_MAX_PCT',
    3: 'VAR_AVAL_PCT'
}

volt_watt_dept_ref = {
    'W_MAX_PCT': 1,
    'W_AVAL_PCT': 2,
    1: 'W_MAX_PCT',
    2: 'W_AVAL_PCT'
}

reactive_power_dept_ref = {
    'None': 0,
    'WMax': 1,
    'VArMax': 2,
    'VArAval': 3,
    0: 'None',
    1: 'WMax',
    2: 'VArMax',
    3: 'VArAval'
}

# connection state control enumeration as specified in SunSpec model 123
CONN_DISCONNECT = 0
CONN_CONNECT = 1

# pv connection state status bitmasks as specified in SunSpec model 122
PVCONN_CONNECTED = (1 << 0)
PVCONN_AVAILABLE = (1 << 1)
PVCONN_OPERATING = (1 << 2)
PVCONN_TEST = (1 << 3)

# storage connection state status bitmasks as specified in SunSpec model 122
STORCONN_CONNECTED = (1 << 0)
STORCONN_AVAILABLE = (1 << 0)
STORCONN_OPERATING = (1 << 0)
STORCONN_TEST = (1 << 0)

# ecp connection state status bitmasks as specified in SunSpec model 122
ECPCONN_CONNECTED = (1 << 0)

# Status Active Control bitmasks as specified in SunSpec model 122
STACTCTL_FIXED_W = (1 << 0)
STACTCTL_FIXED_VAR = (1 << 1)
STACTCTL_FIXED_PF = (1 << 2)
STACTCTL_VOLT_VAR = (1 << 3)
STACTCTL_FREQ_WATT_PARAM = (1 << 4)
STACTCTL_FREQ_WATT_CURVE = (1 << 5)
STACTCTL_DYN_REACTIVE_POWER = (1 << 6)
STACTCTL_LVRT = (1 << 7)
STACTCTL_HVRT = (1 << 8)
STACTCTL_WATT_PF = (1 << 9)
STACTCTL_VOLT_WATT = (1 << 10)
STACTCTL_SCHEDULED = (1 << 12)
STACTCTL_LFRT = (1 << 13)
STACTCTL_HFRT = (1 << 14)

VOLTVAR_WMAX = 1
VOLTVAR_VARMAX = 2
VOLTVAR_VARAVAL = 3

class DER(der.DER):

    def __init__(self, ts, group_name):
        der.DER.__init__(self, ts, group_name)
        self.inv = None
        self.ts = ts

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
        tls = self.param_value('tls')
        cafile = self.param_value('cafile')
        certfile = self.param_value('certfile')
        keyfile = self.param_value('keyfile')
        skip_verify = self.param_value('insecure_skip_tls_verify')
        slave_id = self.param_value('slave_id')

        try:  # attempt to use pysunspec that supports TLS encryption
            self.inv = client.SunSpecClientDevice(ifc_type, slave_id=slave_id, name=ifc_name, baudrate=baudrate,
                                                  parity=parity, ipaddr=ipaddr, ipport=ipport,
                                                  tls=tls, cafile=cafile, certfile=certfile, keyfile=keyfile,
                                                  insecure_skip_tls_verify=skip_verify)
        except Exception as e:  # fallback to old version
            if self.ts is not None:
                self.ts.log('Could not create Modbus client with encryption: %s.  Attempted unencrypted option.')
            else:
                print('Could not create Modbus client with encryption: %s.  Attempted unencrypted option.')
            self.inv = client.SunSpecClientDevice(ifc_type, slave_id=slave_id, name=ifc_name, baudrate=baudrate,
                                                  parity=parity, ipaddr=ipaddr, ipport=ipport)

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
                self.inv.common.read()
                params['Manufacturer'] = self.inv.common.Mn
                params['Model'] = self.inv.common.Md
                params['Options'] = self.inv.common.Opt
                params['Version'] = self.inv.common.Vr
                params['SerialNumber'] = self.inv.common.SN
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
            if 'settings' in self.inv.models:
                if params is not None:
                    for key, value in params.items():
                        self.inv.settings[key] = value
                    self.inv.settings.write()
                else:
                    params = {}
                    self.inv.settings.read()
                    params['WMax'] = self.inv.settings.WMax
                    params['VRef'] = self.inv.settings.VRef
                    params['VRefOfs'] = self.inv.settings.VRefOfs
                    params['VMax'] = self.inv.settings.VMax
                    params['VMin'] = self.inv.settings.VMin
                    params['VAMax'] = self.inv.settings.VAMax
                    params['VArMaxQ1'] = self.inv.settings.VArMaxQ1
                    params['VArMaxQ2'] = self.inv.settings.VArMaxQ2
                    params['VArMaxQ3'] = self.inv.settings.VArMaxQ3
                    params['VArMaxQ4'] = self.inv.settings.VArMaxQ4
                    params['WGra'] = self.inv.settings.WGra
                    params['PFMinQ1'] = self.inv.settings.PFMinQ1
                    params['PFMinQ2'] = self.inv.settings.PFMinQ2
                    params['PFMinQ3'] = self.inv.settings.PFMinQ3
                    params['PFMinQ4'] = self.inv.settings.PFMinQ4
                    params['VArAct'] = self.inv.settings.VArAct
            else:
                params = None
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
            self.inv.status.read()
            pv_conn_bitfield = self.inv.status.PVConn
            stor_conn_bitfield = self.inv.status.StorConn
            ecp_conn_bitfield = self.inv.status.ECPConn

            params = {}
            if pv_conn_bitfield is not None:
                params['PV_Connected'] = (pv_conn_bitfield & PVCONN_CONNECTED) == PVCONN_CONNECTED
                params['PV_Available'] = (pv_conn_bitfield & PVCONN_AVAILABLE) == PVCONN_AVAILABLE
                params['PV_Operating'] = (pv_conn_bitfield & PVCONN_OPERATING) == PVCONN_OPERATING
                params['PV_Test'] = (pv_conn_bitfield & PVCONN_TEST) == PVCONN_TEST
            elif stor_conn_bitfield is not None:
                params['Storage_Connected'] = (stor_conn_bitfield & STORCONN_CONNECTED) == STORCONN_CONNECTED
                params['Storage_Available'] = (stor_conn_bitfield & STORCONN_AVAILABLE) == STORCONN_AVAILABLE
                params['Storage_Operating'] = (stor_conn_bitfield & STORCONN_OPERATING) == STORCONN_OPERATING
                params['Storage_Test'] = (stor_conn_bitfield & STORCONN_TEST) == STORCONN_TEST
            elif ecp_conn_bitfield is not None:
                params['EPC_Connected'] = (ecp_conn_bitfield & ECPCONN_CONNECTED) == ECPCONN_CONNECTED
            else:
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
            self.inv.status.read()
            status_bitfield = self.inv.status.StActCtl
            params = {}
            if status_bitfield is not None:
                params['Fixed_W'] = (status_bitfield & STACTCTL_FIXED_W) == STACTCTL_FIXED_W
                params['Fixed_Var'] = (status_bitfield & STACTCTL_FIXED_VAR) == STACTCTL_FIXED_VAR
                params['Fixed_PF'] = (status_bitfield & STACTCTL_FIXED_PF) == STACTCTL_FIXED_PF
                params['Volt_Var'] = (status_bitfield & STACTCTL_VOLT_VAR) == STACTCTL_VOLT_VAR
                params['Freq_Watt_Param'] = (status_bitfield & STACTCTL_FREQ_WATT_PARAM) == STACTCTL_FREQ_WATT_PARAM
                params['Freq_Watt_Curve'] = (status_bitfield & STACTCTL_FREQ_WATT_CURVE) == STACTCTL_FREQ_WATT_CURVE
                params['Dyn_Reactive_Power'] = (status_bitfield & STACTCTL_DYN_REACTIVE_POWER) == STACTCTL_DYN_REACTIVE_POWER
                params['LVRT'] = (status_bitfield & STACTCTL_LVRT) == STACTCTL_LVRT
                params['HVRT'] = (status_bitfield & STACTCTL_HVRT) == STACTCTL_HVRT
                params['Watt_PF'] = (status_bitfield & STACTCTL_WATT_PF) == STACTCTL_WATT_PF
                params['Volt_Watt'] = (status_bitfield & STACTCTL_VOLT_WATT) == STACTCTL_VOLT_WATT
                params['Scheduled'] = (status_bitfield & STACTCTL_SCHEDULED) == STACTCTL_SCHEDULED
                params['LFRT'] = (status_bitfield & STACTCTL_LFRT) == STACTCTL_LFRT
                params['HFRT'] = (status_bitfield & STACTCTL_HFRT) == STACTCTL_HFRT
            else:
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
            if 'controls' in self.inv.models:
                if params is not None:
                    conn = params.get('Conn')
                    if conn is not None:
                        if conn is True:
                            self.inv.controls.Conn = 1
                        else:
                            self.inv.controls.Conn = 0
                    win_tms = params.get('WinTms')
                    if win_tms is not None:
                        self.inv.controls.Conn_WinTms = win_tms
                    rvrt_tms = params.get('WinTms')
                    if rvrt_tms is not None:
                        self.inv.controls.Conn_RvrtTms = rvrt_tms
                    self.inv.controls.write()
                else:
                    params = {}
                    self.inv.controls.read()
                    if self.inv.controls.Conn == 0:
                        params['Conn'] = False
                    else:
                        params['Conn'] = True
                    params['WinTms'] = self.inv.controls.Conn_WinTms
                    params['RvrtTms'] = self.inv.controls.Conn_RvrtTms
            else:
                params = None
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
            if 'controls' in self.inv.models:
                if params is not None:
                    self.inv.controls.read()
                    ena = params.get('Ena')
                    if ena is not None:
                        if ena is True:
                            self.inv.controls.OutPFSet_Ena = 1
                        else:
                            self.inv.controls.OutPFSet_Ena = 0
                    pf = params.get('PF')
                    if pf is not None:
                        self.inv.controls.OutPFSet = pf
                    win_tms = params.get('WinTms')
                    if win_tms is not None:
                        self.inv.controls.OutPFSet_WinTms = win_tms
                    rmp_tms = params.get('RmpTms')
                    if rmp_tms is not None:
                        self.inv.controls.OutPFSet_RmpTms = rmp_tms
                    rvrt_tms = params.get('RvrtTms')
                    if rvrt_tms is not None:
                        self.inv.controls.OutPFSet_RvrtTms = rvrt_tms
                    self.inv.controls.write()
                else:
                    params = {}
                    self.inv.controls.read()
                    if self.inv.controls.OutPFSet_Ena == 0:
                        params['Ena'] = False
                    else:
                        params['Ena'] = True
                    params['PF'] = self.inv.controls.OutPFSet
                    params['WinTms'] = self.inv.controls.OutPFSet_WinTms
                    params['RmpTms'] = self.inv.controls.OutPFSet_RmpTms
                    params['RvrtTms'] = self.inv.controls.OutPFSet_RvrtTms
            else:
                params = None
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def limit_max_power(self, params=None):
        """ Get/set max active power control settings.

        Params:
            Ena - Enabled (True/False)
            WMaxPct - Active power maximum as percentage of WMax
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for limit max power.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'controls' in self.inv.models:
                if params is not None:
                    ena = params.get('Ena')
                    if ena is not None:
                        if ena is True:
                            self.inv.controls.WMaxLim_Ena = 1
                        else:
                            self.inv.controls.WMaxLim_Ena = 0
                    wmax = params.get('WMaxPct')
                    if wmax is not None:
                        self.inv.controls.WMaxLimPct = wmax
                    win_tms = params.get('WinTms')
                    if win_tms is not None:
                        self.inv.controls.WMaxLimPct_WinTms = win_tms
                    rmp_tms = params.get('WinTms')
                    if rmp_tms is not None:
                        self.inv.controls.WMaxLimPct_RmpTms = rmp_tms
                    rvrt_tms = params.get('WinTms')
                    if rvrt_tms is not None:
                        self.inv.controls.WMaxLimPct_RvrtTms = rvrt_tms
                    self.inv.controls.write()
                else:
                    params = {}
                    self.inv.controls.read()
                    if self.inv.controls.WMaxLim_Ena == 0:
                        params['Ena'] = False
                    else:
                        params['Ena'] = True
                    params['WMaxPct'] = self.inv.controls.WMaxLimPct
                    params['WinTms'] = self.inv.controls.WMaxLimPct_WinTms
                    params['RmpTms'] = self.inv.controls.WMaxLimPct_RmpTms
                    params['RvrtTms'] = self.inv.controls.WMaxLimPct_RvrtTms
            else:
                params = None
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
                self.inv.volt_var.read()
                if params is not None:
                    curve = params.get('curve')  # Must write curve first because there is a read() in volt_var_curve
                    act_crv = params.get('ActCrv')
                    if act_crv is None:
                        act_crv = 1
                    if curve is not None:
                        self.volt_var_curve(id=act_crv, params=curve)
                    ena = params.get('Ena')
                    if ena is not None:
                        if ena is True:
                            self.inv.volt_var.ModEna = 1
                        else:
                            self.inv.volt_var.ModEna = 0
                    if act_crv is not None:
                        self.inv.volt_var.ActCrv = act_crv
                    else:
                        self.inv.volt_var.ActCrv = 1
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
                    if self.inv.volt_var.ModEna == 0 or self.inv.volt_var.ModEna is None:
                        params['Ena'] = False
                    else:
                        params['Ena'] = True
                    params['ActCrv'] = self.inv.volt_var.ActCrv
                    params['NCrv'] = self.inv.volt_var.NCrv
                    params['NPt'] = self.inv.volt_var.NPt
                    params['WinTms'] = self.inv.volt_var.WinTms
                    params['RmpTms'] = self.inv.volt_var.RmpTms
                    params['RvrtTms'] = self.inv.volt_var.RvrtTms

                    act_crv = self.inv.volt_var.ActCrv
                    if act_crv != 0:
                        if act_crv is not None:
                            params['curve'] = self.volt_var_curve(id=act_crv)
                        else:
                            params['curve'] = self.volt_var_curve(id=1)  # use 1 as default

            else:
                params = None
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def validate_volt_var(self, params=None):
        """ validate volt/var curve data.
            v [] - List of voltage curve points
            var [] - List of var curve points based on DeptRef

        :param params: Dictionary of parameters; we only use the v[] and var[].
        """
        if params is None:
            return

        v = params['v']
        var = params['var']

        # Simple check to validate length correspondence betwee points.
        if len(v) != len(var):
            raise der.DERError('Unaligned v/var point totals; (%d) v and (%d) var' % (len(v), len(var)))

        # We validate quadrant of each v/var pair; the origin starts at (100, 0).
        for idx in range(len(v)):
            v_measure = v[idx]
            var_measure = var[idx]

            if (v_measure > 100 and var_measure > 0) or (v_measure < 100 and var_measure < 0):
                raise der.DERError(
                    'Unsecure quadrant location for power system operations @ index %d; (%d) v and (%d) var' 
                    % (idx, v_measure, var_measure)
                )

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
                n_crv = self.inv.volt_var.NCrv
                if n_crv is not None:
                    if int(id) > int(n_crv):
                        raise der.DERError('Curve id out of range: %s' % (id))
                curve = self.inv.volt_var.curve[id]

                if params is not None:
                    self.validate_volt_var(params=params)
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

                    n_pt = self.inv.volt_var.NPt
                    if n_pt is None:
                        n_pt = 4  # Assume 4 points in the curve
                    # set voltage points
                    v = params.get('v')
                    if v is not None:
                        v_len = len(v)
                        if v_len > int(n_pt):
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
                        der.DERError('DeptRef out of range: %s' % (dept_ref))
                    params['DeptRef'] = dept_ref
                    params['RmpTms'] = curve.RmpTms
                    params['RmpDecTmm'] = curve.RmpDecTmm
                    params['RmpIncTmm'] = curve.RmpIncTmm
                    params['id'] = id  #also store the curve number

                    v = []
                    var = []
                    if act_pt is not None:
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
            curve - dict of curve parameters:
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
        :return: Dictionary of active settings for freq/watt control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'freq_watt' in self.inv.models:
                if params is not None:
                    curve = params.get('curve')
                    act_crv = params.get('ActCrv')
                    if curve is not None:
                        self.freq_watt_curve(id=act_crv, params=curve)  ## do first b/c read() in freq_watt_curve()
                    ena = params.get('Ena')
                    if ena is not None:
                        if ena is True:
                            self.inv.freq_watt.ModEna = 1
                        else:
                            self.inv.freq_watt.ModEna = 0
                    # act_crv = params.get('ActCrv')  # reread in case freq_watt_curve wrote data
                    if act_crv is not None:
                        self.inv.freq_watt.ActCrv = act_crv
                    else:
                        self.inv.freq_watt.ActCrv = 1
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
        """ Get/set freq/watt curve
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
                        w_point = 'W%d' % i
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
            HysEna - Enable hysteresis (True/False)
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
                    self.inv.freq.read()
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

    def soft_start_ramp_rate(self, params=None):
        pass

    def ramp_rate(self, params=None):
        pass

    def volt_watt(self, params=None):
        """ Get/set volt/watt control

        Params:
            Ena - Enabled (True/False)
            ActCrv - Active curve number (0 - no active curve)
            NCrv - Number of curves supported
            NPt - Number of points supported per curve
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds
            curve - curve parameters in the repeating block in another dictionary with parameters:
                    v [] - List of voltage curve points
                    w [] - List of watt curve points based on DeptRef
                    DeptRef - Dependent reference type:  'W_MAX_PCT', 'W_AVAL_PCT'
                    RmpTms - Ramp timer
                    RmpDecTmm - Ramp decrement timer
                    RmpIncTmm - Ramp increment timer

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for volt/watt control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'volt_watt' in self.inv.models:
                if params is not None:
                    self.inv.volt_watt.read()
                    ena = params.get('Ena')
                    if ena is not None:
                        if ena is True:
                            self.inv.volt_watt.ModEna = 1
                        else:
                            self.inv.volt_watt.ModEna = 0
                    act_crv = params.get('ActCrv')
                    if act_crv is not None:
                        self.inv.volt_watt.ActCrv = act_crv
                    else:
                        self.inv.volt_watt.ActCrv = 1
                    win_tms = params.get('WinTms')
                    if win_tms is not None:
                        self.inv.volt_watt.WinTms = win_tms
                    rmp_tms = params.get('RmpTms')
                    if rmp_tms is not None:
                        self.inv.volt_watt.RmpTms = rmp_tms
                    rvrt_tms = params.get('RvrtTms')
                    if rvrt_tms is not None:
                        self.inv.volt_watt.RvrtTms = rvrt_tms

                    curve = params.get('curve')
                    if curve is not None:
                        # curve paramaters
                        id = self.inv.volt_watt.ActCrv
                        if int(id) > int(self.inv.volt_watt.NCrv):
                            raise der.DERError('Curve id out of range: %s' % (id))
                        curve = self.inv.volt_watt.curve[id]
                        dept_ref = params.get('DeptRef')
                        if dept_ref is not None:
                            dept_ref_id = volt_watt_dept_ref.get(dept_ref)
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

                        n_pt = int(self.inv.volt_watt.NPt)
                        # set voltage points
                        v = params.get('v')
                        if v is not None:
                            v_len = len(v)
                            if v_len > n_pt:
                                raise der.DERError('Voltage point count out of range: %d' % (v_len))
                            for i in range(v_len):  # SunSpec point index starts at 1
                                v_point = 'V%d' % (i + 1)
                                setattr(curve, v_point, v[i])
                        # set watt points
                        watt = params.get('w')
                        if watt is not None:
                            watt_len = len(watt)
                            if watt_len > n_pt:
                                raise der.DERError('W point count out of range: %d' % (watt_len))
                            for i in range(watt_len):  # SunSpec point index starts at 1
                                watt_point = 'W%d' % (i + 1)
                                setattr(curve, watt_point, watt[i])

                    self.inv.volt_watt.write()

                else:
                    params = {}
                    c_params = {}
                    self.inv.volt_watt.read()
                    id = self.inv.volt_watt.ActCrv
                    curve = self.inv.volt_watt.curve[id]
                    if self.inv.volt_watt.ModEna == 0:
                        params['Ena'] = False
                    else:
                        params['Ena'] = True
                    params['ActCrv'] = self.inv.volt_watt.ActCrv
                    params['NCrv'] = self.inv.volt_watt.NCrv
                    params['NPt'] = self.inv.volt_watt.NPt
                    params['WinTms'] = self.inv.volt_watt.WinTms
                    params['RmpTms'] = self.inv.volt_watt.RmpTms
                    params['RvrtTms'] = self.inv.volt_watt.RvrtTms

                    if self.inv.volt_watt.ActCrv != 0:
                        # curve parameters
                        act_pt = curve.ActPt
                        dept_ref = volt_watt_dept_ref.get(curve.DeptRef)
                        c_params['DeptRef'] = dept_ref
                        # c_params['RmpTms'] = curve.RmpTms
                        # c_params['RmpDecTmm'] = curve.RmpDecTmm
                        # c_params['RmpIncTmm'] = curve.RmpIncTmm
                        c_params['id'] = id  # also store the curve number
                        v = []
                        w = []
                        for i in range(1, act_pt + 1):  # SunSpec point index starts at 1
                            v_point = 'V%d' % i
                            w_point = 'W%d' % i
                            v.append(getattr(curve, v_point))
                            w.append(getattr(curve, w_point))
                        c_params['v'] = v
                        c_params['w'] = w
                        params['curve'] = c_params
            else:
                params = None

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def reactive_power(self, params=None):
        """ Set the reactive power

        Params:
            Ena - Enabled (True/False)
            VArPct_Mod - Reactive power mode
                    'None' : 0,
                    'WMax': 1,
                    'VArMax': 2,
                    'VArAval': 3,
            VArWMaxPct - Reactive power in percent of WMax.
            VArMaxPct - Reactive power in percent of VArMax.
            VArAvalPct - Reactive power in percent of VArAval.

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
                        self.inv.controls.VArPct_Ena = 1
                    else:
                        self.inv.controls.VArPct_Ena = 0

                var_pct_mod = params.get('VArPct_Mod')
                if var_pct_mod is not None:
                    self.inv.controls.VArPct_Mod = reactive_power_dept_ref[var_pct_mod]
                var_w_max_pct = params.get('VArWMaxPct')
                if var_w_max_pct is not None:
                    self.inv.controls.VArWMaxPct = var_w_max_pct
                var_max_pct = params.get('VArMaxPct')
                if var_max_pct is not None:
                    self.inv.controls.VArMaxPct = var_max_pct
                var_aval_pct = params.get('VArAvalPct')
                if var_aval_pct is not None:
                    self.inv.controls.VArAvalPct = var_aval_pct
                self.inv.controls.write()

            else:
                params = {}
                self.inv.controls.read()
                if self.inv.controls.VArPct_Ena == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['VArPct_Mod'] = reactive_power_dept_ref[self.inv.controls.VArPct_Mod]
                params['VArWMaxPct'] = self.inv.controls.VArWMaxPct
                params['VArMaxPct'] = self.inv.controls.VArMaxPct
                params['VArAvalPct'] = self.inv.controls.VArAvalPct

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def reactive_power_via_vv(self, params=None):
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
        :return: Dictionary of active settings.
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
        :return: Dictionary of active settings.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        self.inv.hfrt.ModEna = 1
                    else:
                        self.inv.hfrt.ModEna = 0
                act_crv = params.get('ActCrv')
                if act_crv is not None:
                    self.inv.hfrt.ActCrv = act_crv
                win_tms = params.get('WinTms')
                if win_tms is not None:
                    self.inv.hfrt.WinTms = win_tms
                rmp_tms = params.get('RmpTms')
                if rmp_tms is not None:
                    self.inv.hfrt.RmpTms = rmp_tms
                rvrt_tms = params.get('RvrtTms')
                if rvrt_tms is not None:
                    self.inv.hfrt.RvrtTms = rvrt_tms
                for i in range(1, params['NPt'] + 1):  # Uses the SunSpec indexing rules (start at 1)
                    time_point = 'Tms%d' % i
                    param_time_point = params.get(time_point)
                    curve_num = self.inv.hfrt.ActCrv  # assume the active curve is the one being changed
                    if curve_num is None:
                        curve_num = 1  # set default curve to 1
                    if param_time_point is not None:
                        setattr(self.inv.hfrt.h_curve[curve_num], time_point, param_time_point)
                    freq_point = 'Hz%d' % i
                    param_freq_point = params.get(freq_point)
                    if param_freq_point is not None:
                        setattr(self.inv.hfrt.h_curve[curve_num], freq_point, param_freq_point)
                self.inv.hfrt.write()
            else:
                params = {}
                self.inv.hfrt.read()
                if self.inv.hfrt.ModEna == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['ActCrv'] = self.inv.hfrt.ActCrv
                params['NCrv'] = self.inv.hfrt.NCrv
                params['NPt'] = self.inv.hfrt.NPt
                params['WinTms'] = self.inv.hfrt.WinTms
                params['RmpTms'] = self.inv.hfrt.RmpTms
                params['RvrtTms'] = self.inv.hfrt.RvrtTms

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def frt_stay_connected_low(self, params=None):
        """ Get/set low frequency ride through (must stay connected curve)

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
        :return: Dictionary of active settings.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        self.inv.lfrt.ModEna = 1
                    else:
                        self.inv.lfrt.ModEna = 0
                act_crv = params.get('ActCrv')
                if act_crv is not None:
                    self.inv.lfrt.ActCrv = act_crv
                win_tms = params.get('WinTms')
                if win_tms is not None:
                    self.inv.lfrt.WinTms = win_tms
                rmp_tms = params.get('RmpTms')
                if rmp_tms is not None:
                    self.inv.lfrt.RmpTms = rmp_tms
                rvrt_tms = params.get('RvrtTms')
                if rvrt_tms is not None:
                    self.inv.lfrt.RvrtTms = rvrt_tms
                for i in range(1, params['NPt'] + 1):  # Uses the SunSpec indexing rules (start at 1)
                    time_point = 'Tms%d' % i
                    param_time_point = params.get(time_point)
                    curve_num = self.inv.lfrt.ActCrv  # assume the active curve is the one being changed
                    if curve_num is None:
                        curve_num = 1  # set default curve to 1
                    if param_time_point is not None:
                        setattr(self.inv.lfrt.l_curve[curve_num], time_point, param_time_point)
                    freq_point = 'Hz%d' % i
                    param_freq_point = params.get(freq_point)
                    if param_freq_point is not None:
                        setattr(self.inv.lfrt.l_curve[curve_num], freq_point, param_freq_point)
                self.inv.lfrt.write()
            else:
                params = {}
                self.inv.lfrt.read()
                if self.inv.lfrt.ModEna == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['ActCrv'] = self.inv.lfrt.ActCrv
                params['NCrv'] = self.inv.lfrt.NCrv
                params['NPt'] = self.inv.lfrt.NPt
                params['WinTms'] = self.inv.lfrt.WinTms
                params['RmpTms'] = self.inv.lfrt.RmpTms
                params['RvrtTms'] = self.inv.lfrt.RvrtTms

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def frt_trip_high(self, params=None):
        """ Get/set high frequency ride through (must trip curve)

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
        :return: Dictionary of active settings.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                pass
            else:
                params = {}

        except Exception as e:
            raise der.DERError(str(e))

        return params


    def frt_trip_low(self, params=None):
        """ Get/set low frequency ride through (must trip curve)

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
        :return: Dictionary of active settings.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                pass
            else:
                params = {}

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def vrt_stay_connected_high(self, params=None):
        """ Get/set high voltage ride through (must stay connected curve)

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
        :return: Dictionary of active settings.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        self.inv.hvrtc.ModEna = 1
                    else:
                        self.inv.hvrtc.ModEna = 0
                act_crv = params.get('ActCrv')
                if act_crv is not None:
                    self.inv.hvrtc.ActCrv = act_crv
                win_tms = params.get('WinTms')
                if win_tms is not None:
                    self.inv.hvrtc.WinTms = win_tms
                rmp_tms = params.get('RmpTms')
                if rmp_tms is not None:
                    self.inv.hvrtc.RmpTms = rmp_tms
                rvrt_tms = params.get('RvrtTms')
                if rvrt_tms is not None:
                    self.inv.hvrtc.RvrtTms = rvrt_tms
                for i in range(1, params['NPt'] + 1):  # Uses the SunSpec indexing rules (start at 1)
                    time_point = 'Tms%d' % i
                    param_time_point = params.get(time_point)
                    curve_num = self.inv.hvrtc.ActCrv  # assume the active curve is the one being changed
                    if curve_num is None:
                        curve_num = 1  # set default curve to 1
                    if param_time_point is not None:
                        setattr(self.inv.hvrtc.h_curve[curve_num], time_point, param_time_point)
                    volt_point = 'V%d' % i
                    param_freq_point = params.get(volt_point)
                    if param_freq_point is not None:
                        setattr(self.inv.hvrtc.h_curve[curve_num], volt_point, param_freq_point)
                self.inv.hvrtc.write()
            else:
                params = {}
                self.inv.hvrtc.read()
                if self.inv.hvrtc.ModEna == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['ActCrv'] = self.inv.hvrtc.ActCrv
                params['NCrv'] = self.inv.hvrtc.NCrv
                params['NPt'] = self.inv.hvrtc.NPt
                params['WinTms'] = self.inv.hvrtc.WinTms
                params['RmpTms'] = self.inv.hvrtc.RmpTms
                params['RvrtTms'] = self.inv.hvrtc.RvrtTms

        except Exception as e:
            raise der.DERError(str(e))

        return params


    def vrt_stay_connected_low(self, params=None):
        """ Get/set low voltage ride through (must stay connected curve)

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
        :return: Dictionary of active settings.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        self.inv.lvrtc.ModEna = 1
                    else:
                        self.inv.lvrtc.ModEna = 0
                act_crv = params.get('ActCrv')
                if act_crv is not None:
                    self.inv.lvrtc.ActCrv = act_crv
                win_tms = params.get('WinTms')
                if win_tms is not None:
                    self.inv.lvrtc.WinTms = win_tms
                rmp_tms = params.get('RmpTms')
                if rmp_tms is not None:
                    self.inv.lvrtc.RmpTms = rmp_tms
                rvrt_tms = params.get('RvrtTms')
                if rvrt_tms is not None:
                    self.inv.lvrtc.RvrtTms = rvrt_tms
                for i in range(1, params['NPt'] + 1):  # Uses the SunSpec indexing rules (start at 1)
                    time_point = 'Tms%d' % i
                    param_time_point = params.get(time_point)
                    curve_num = self.inv.lvrtc.ActCrv  # assume the active curve is the one being changed
                    if curve_num is None:
                        curve_num = 1  # set default curve to 1
                    if param_time_point is not None:
                        setattr(self.inv.lvrtc.l_curve[curve_num], time_point, param_time_point)
                    volt_point = 'V%d' % i
                    param_freq_point = params.get(volt_point)
                    if param_freq_point is not None:
                        setattr(self.inv.lvrtc.l_curve[curve_num], volt_point, param_freq_point)
                self.inv.lvrtc.write()
            else:
                params = {}
                self.inv.lvrtc.read()
                if self.inv.lvrtc.ModEna == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['ActCrv'] = self.inv.lvrtc.ActCrv
                params['NCrv'] = self.inv.lvrtc.NCrv
                params['NPt'] = self.inv.lvrtc.NPt
                params['WinTms'] = self.inv.lvrtc.WinTms
                params['RmpTms'] = self.inv.lvrtc.RmpTms
                params['RvrtTms'] = self.inv.lvrtc.RvrtTms

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def vrt_trip_high(self, params=None):
        """ Get/set high voltage ride through (must trip curve)

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
        :return: Dictionary of active settings.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        self.inv.hvrtd.ModEna = 1
                    else:
                        self.inv.hvrtd.ModEna = 0
                act_crv = params.get('ActCrv')
                if act_crv is not None:
                    self.inv.hvrtd.ActCrv = act_crv
                win_tms = params.get('WinTms')
                if win_tms is not None:
                    self.inv.hvrtd.WinTms = win_tms
                rmp_tms = params.get('RmpTms')
                if rmp_tms is not None:
                    self.inv.hvrtd.RmpTms = rmp_tms
                rvrt_tms = params.get('RvrtTms')
                if rvrt_tms is not None:
                    self.inv.hvrtd.RvrtTms = rvrt_tms
                for i in range(1, params['NPt'] + 1):  # Uses the SunSpec indexing rules (start at 1)
                    time_point = 'Tms%d' % i
                    param_time_point = params.get(time_point)
                    curve_num = self.inv.hvrtd.ActCrv  # assume the active curve is the one being changed
                    if curve_num is None:
                        curve_num = 1  # set default curve to 1
                    if param_time_point is not None:
                        setattr(self.inv.hvrtd.h_curve[curve_num], time_point, param_time_point)
                    volt_point = 'V%d' % i
                    param_freq_point = params.get(volt_point)
                    if param_freq_point is not None:
                        setattr(self.inv.hvrtd.h_curve[curve_num], volt_point, param_freq_point)
                self.inv.hvrtd.write()
            else:
                params = {}
                self.inv.hvrtd.read()
                if self.inv.hvrtd.ModEna == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['ActCrv'] = self.inv.hvrtd.ActCrv
                params['NCrv'] = self.inv.hvrtd.NCrv
                params['NPt'] = self.inv.hvrtd.NPt
                params['WinTms'] = self.inv.hvrtd.WinTms
                params['RmpTms'] = self.inv.hvrtd.RmpTms
                params['RvrtTms'] = self.inv.hvrtd.RvrtTms

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def vrt_trip_low(self, params=None):
        """ Get/set low voltage ride through (must trip curve)

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
                        self.inv.lvrtd.ModEna = 1
                    else:
                        self.inv.lvrtd.ModEna = 0
                act_crv = params.get('ActCrv')
                if act_crv is not None:
                    self.inv.lvrtd.ActCrv = act_crv
                win_tms = params.get('WinTms')
                if win_tms is not None:
                    self.inv.lvrtd.WinTms = win_tms
                rmp_tms = params.get('RmpTms')
                if rmp_tms is not None:
                    self.inv.lvrtd.RmpTms = rmp_tms
                rvrt_tms = params.get('RvrtTms')
                if rvrt_tms is not None:
                    self.inv.lvrtd.RvrtTms = rvrt_tms
                for i in range(1, params['NPt'] + 1):  # Uses the SunSpec indexing rules (start at 1)
                    time_point = 'Tms%d' % i
                    param_time_point = params.get(time_point)
                    curve_num = self.inv.lvrtd.ActCrv  # assume the active curve is the one being changed
                    if curve_num is None:
                        curve_num = 1  # set default curve to 1
                    if param_time_point is not None:
                        setattr(self.inv.lvrtd.l_curve[curve_num], time_point, param_time_point)
                    volt_point = 'V%d' % i
                    param_freq_point = params.get(volt_point)
                    if param_freq_point is not None:
                        setattr(self.inv.lvrtd.l_curve[curve_num], volt_point, param_freq_point)
                self.inv.lvrtd.write()
            else:
                params = {}
                self.inv.lvrtd.read()
                if self.inv.lvrtd.ModEna == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['ActCrv'] = self.inv.lvrtd.ActCrv
                params['NCrv'] = self.inv.lvrtd.NCrv
                params['NPt'] = self.inv.lvrtd.NPt
                params['WinTms'] = self.inv.lvrtd.WinTms
                params['RmpTms'] = self.inv.lvrtd.RmpTms
                params['RvrtTms'] = self.inv.lvrtd.RvrtTms

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def ramp_rates(self, params=None):
        """ Get/set ramp rate control

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for ramp rate control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'ext_settings' in self.inv.models:
                if params is not None:
                    rr = params.get('ramp_rate')
                    ss = params.get('soft_start')
                    if rr is not None:
                        self.inv.ext_settings.NomRmpUpRte = rr
                    if ss is not None:
                        self.inv.ext_settings.ConnRmpUpRte = ss
                    self.inv.ext_settings.write()
                else:
                    params = {}
                    self.inv.ext_settings.read()
                    params['ramp_rate'] = self.inv.ext_settings.NomRmpUpRte
                    params['soft_start'] = self.inv.ext_settings.ConnRmpUpRte
            else:
                params = None
        except Exception as e:
            raise der.DERError(str(e))

        return params
