'''
DER1547 methods defined for SunSpec Modbus devices
'''

import os
import sunspec.core.client as client
from . import der1547
import script

sunspec_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'SunSpec'
}


def der1547_info():
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
    info.param(pname('ipaddr'), label='IP Address', default='192.168.0.170', active=pname('ifc_type'),
               active_value=[client.TCP])
    info.param(pname('ipport'), label='IP Port', default=502, active=pname('ifc_type'), active_value=[client.TCP])
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


class DER1547(der1547.DER1547):

    def __init__(self, ts, group_name):
        der1547.DER1547.__init__(self, ts, group_name)
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
        slave_id = self.param_value('slave_id')

        self.inv = client.SunSpecClientDevice(ifc_type, slave_id=slave_id, name=ifc_name, baudrate=baudrate,
                                              parity=parity, ipaddr=ipaddr, ipport=ipport)

    def close(self):
        if self.inv is not None:
            self.inv.close()
            self.inv = None

    def get_nameplate(self, params=None):
        """ Get/set IEEE 1547 nameplate data

        :param params: dict with the following data
            Active power rating at unity power factor (nameplate active power rating) = 702.WMaxRtg *
            Active power rating at specified over-excited power factor = 702.WOvrExtRtg
            Specified over-excited power factor = 702.WOvrExtRtgPF
            Active power rating at specified under-excited power factor = 702.WUndExtRtg
            Specified under-excited power factor = 702.WUndExtRtgPF
            Apparent power maximum rating = 702.VAMaxRtg *
            Normal operating performance category = 702.NorOpCat
            Abnormal operating performance category = 702.AbnOpCat
            Reactive power injected maximum rating = 702.VarMaxInjRtg *
            Reactive power absorbed maximum rating = 702.VarMaxAbsRtg *
            Active power charge maximum rating = 702.WChaRteMaxRtg *
            Apparent power charge maximum rating = 702.VAChaRteMaxRtg *
            AC voltage nominal rating = 702.VNomRtg
            AC voltage maximum rating = 702.VMaxRtg
            AC voltage minimum rating = 702.VMinRtg
            Supported control mode functions = ?
            Reactive susceptance that remains connected to the area EPS in the cease-to-energize and trip state = ?
            Manufacturer = 1.Mn
            Model = 1.Md
            Serial number = 1.SN
            Version = 1.Vr
        * Parameters used in the IEEE 1547.1 Configuration information test (6.5)

        :return: Dictionary of values for the IEEE 1547 nameplate data

        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                if 'nameplate' in self.inv.models:
                    if params.get('WMaxRtg') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('WMaxRtg')
                    if params.get('WOvrExtRtg') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('WOvrExtRtg')
                    if params.get('WOvrExtRtgPF') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('WOvrExtRtgPF')
                    if params.get('WUndExtRtg') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('WUndExtRtg')
                    if params.get('WUndExtRtgPF') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('WUndExtRtgPF')
                    if params.get('VAMaxRtg') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('VAMaxRtg')
                    if params.get('NorOpCat') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('NorOpCat')
                    if params.get('AbnOpCat') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('AbnOpCat')
                    if params.get('VarMaxInjRtg') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('VarMaxInjRtg')
                    if params.get('VarMaxAbsRtg') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('VarMaxAbsRtg')
                    if params.get('WChaRteMaxRtg') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('WChaRteMaxRtg')
                    if params.get('VAChaRteMaxRtg') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('VAChaRteMaxRtg')
                    if params.get('VNomRtg') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('VNomRtg')
                    if params.get('VMinRtg') is not None:
                        self.inv.nameplate.WMaxRtg = params.get('VMinRtg')
                    self.inv.nameplate.write()
                if 'common' in self.inv.models:
                    if params.get('Mn') is not None:
                        self.inv.common.WMaxRtg = params.get('Mn')
                    if params.get('Md') is not None:
                        self.inv.common.WMaxRtg = params.get('Md')
                    if params.get('SN') is not None:
                        self.inv.common.WMaxRtg = params.get('SN')
                    if params.get('Vr') is not None:
                        self.inv.common.WMaxRtg = params.get('Vr')
                    self.inv.common.write()

            else:
                params = {}
                if 'nameplate' in self.inv.models:
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
                if 'common' in self.inv.models:
                    self.inv.common.read()
                    params['Manufacturer'] = self.inv.common.Mn
                    params['Model'] = self.inv.common.Md
                    params['SerialNumber'] = self.inv.common.SN
                    params['Version'] = self.inv.common.Vr
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def get_monitoring(self):
        """ Get IEEE 1547 monitoring information

            Active Power = 701.W
            Reactive Power = 701.VAR
            Voltage = 701.PPV, 701.PhV
            Frequency = 701.Hz
            Operational State = 701.St
            Connection Status = ?
            Alarm Status = 701.Alrm
            Operational State of Charge = ?

        :return: Dictionary of values for the IEEE 1547 monitoring data

        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            params = {}
            if 'monitoring' in self.inv.models:
                self.inv.monitoring.read()
                params['W'] = self.inv.nameplate.W
                params['VAR'] = self.inv.nameplate.VAR
                params['PPV'] = self.inv.nameplate.PPV
                params['PhV'] = self.inv.nameplate.PhV
                params['Hz'] = self.inv.nameplate.Hz
                params['St'] = self.inv.nameplate.St
                params['Alrm'] = self.inv.nameplate.Alrm
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def get_fixed_pf(self):
        """ Get IEEE 1547 Adjustable constant power factor (1547.1 6.8.1.4)

            Constant Power Factor Mode Enable = 704.PFWInjEna
            Constant Power Factor = 704.PFWInj.PF
            Constant Power Factor Excitation = 704.PFWInj.Ext

        :return: Dictionary of values for the IEEE 1547 monitoring data

        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            params = {}
            if 'pf' in self.inv.models:
                self.inv.pf.read()
                params['PFWInjEna'] = self.inv.pf.WRtg
                params['PF'] = self.inv.pf.VARtg
                params['Ext'] = self.inv.pf.VArRtgQ1
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def set_fixed_pf(self, params=None):
        """ Set IEEE 1547 Adjustable constant power factor (1547.1 6.8.1.4)

            Constant Power Factor Mode Enable = 704.PFWInjEna
            Constant Power Factor = 704.PFWInj.PF
            Constant Power Factor Excitation = 704.PFWInj.Ext

        :return: Dictionary of values for the IEEE 1547 monitoring data

        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                if 'pf' in self.inv.models:
                    if params.get('PFWInjEna') is not None:
                        self.inv.pf.WMaxRtg = params.get('PFWInjEna')
                    if params.get('WOvrExtRtg') is not None:
                        self.inv.pf.WMaxRtg = params.get('PF')
                    if params.get('Ext') is not None:
                        self.inv.pf.WMaxRtg = params.get('Ext')
                    self.pf.common.write()
            else:
                if self.ts is not None:
                    self.ts.log_warning('No params sent to set_fixed_pf')

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def get_volt_var(self):
        """ Get IEEE 1547 SunSpec Voltage-Reactive Power

            Voltage-Reactive Power Mode Enable = 705.Ena
            VRef = 705.VRef
            Autonomous VRef Adjustment Enable = 705.VRefAuto
            VRef Adjustment Time Constant = 705.VRefTms
            V/Q Curve Points = 705.VoltVar.Crv.Pt
            Open Loop Response Time = 705.RspTms

        :param params: Dictionary of values for the IEEE 1547 VV write
        :return: Dictionary of values for the IEEE 1547 VV read

        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            params = {}
            if 'vv' in self.inv.models:
                self.inv.vv.read()
                params['Ena'] = self.inv.vv.Ena
                params['VRef'] = self.inv.vv.VRef
                params['VRefAuto'] = self.inv.vv.VRefAuto
                params['VRefTms'] = self.inv.vv.VRefTms
                params['VRefAuto'] = self.inv.vv.VRefAuto
                params['VoltVar.Crv.Pt'] = self.inv.vv.VoltVar.Crv.Pt
                params['RspTms'] = self.inv.vv.RspTms

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def set_volt_var(self, params=None):
        """ Set IEEE 1547 SunSpec Voltage-Reactive Power

            Voltage-Reactive Power Mode Enable = 705.Ena
            VRef = 705.VRef
            Autonomous VRef Adjustment Enable = 705.VRefAuto
            VRef Adjustment Time Constant = 705.VRefTms
            V/Q Curve Points = 705.VoltVar.Crv.Pt
            Open Loop Response Time = 705.RspTms

        :param params: Dictionary of values for the IEEE 1547 VV write
        :return: Dictionary of values for the IEEE 1547 VV read

        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                if 'vv' in self.inv.models:
                    if params.get('Ena') is not None:
                        self.inv.vv.WMaxRtg = params.get('Ena')
                    if params.get('VRef') is not None:
                        self.inv.vv.WMaxRtg = params.get('VRef')
                    if params.get('VRefAuto') is not None:
                        self.inv.vv.WMaxRtg = params.get('VRefAuto')
                    if params.get('VRefTms') is not None:
                        self.inv.vv.WMaxRtg = params.get('VRefTms')
                    if params.get('VoltVar.Crv.Pt') is not None:
                        self.inv.vv.WMaxRtg = params.get('VoltVar.Crv.Pt')
                    if params.get('RspTms') is not None:
                        self.inv.vv.WMaxRtg = params.get('RspTms')

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
                            var_len = len(watt)
                            if var_len > n_pt:
                                raise der.DERError('W point count out of range: %d' % (var_len))
                            for i in range(var_len):  # SunSpec point index starts at 1
                                var_point = 'VAR%d' % (i + 1)
                                setattr(curve, var_point, var[i])

                    self.pf.common.write()

            else:
                if self.ts is not None:
                    self.ts.log_warning('No params sent to set_volt_var')

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def get_reactive_power(self):
        '''
        This information is used to update functional and mode settings for the
        Constant Reactive Power Mode. This information may be read.
        '''
        pass

    def set_reactive_power(self, params=None):
        '''
        This information is used to update functional and mode settings for the
        Constant Reactive Power Mode. This information may be written.
        '''
        pass

    def get_freq_watt(self):
        '''
        This information is used to update functional and mode settings for the
        Frequency-Active Power Mode. This information may be read.
        '''
        pass

    def set_freq_watt(self, params=None):
        """
        This information is used to update functional and mode settings for the
        Frequency-Active Power Mode. This information may be written.
        """
        pass

    def get_limit_max_power(self):
        '''
        This information is used to update functional and mode settings for the
        Limit Maximum Active Power Mode. This information may be read.
        '''
        pass

    def set_limit_max_power(self, params=None):
        '''
        This information is used to update functional and mode settings for the
        Limit Maximum Active Power Mode. This information may be written.
        '''
        pass

    def get_enter_service(self):
        '''
        This information is used to update functional and mode settings for the
        Enter Service Mode. This information may be read.
        '''
        pass

    def set_enter_service(self, params=None):
        '''
        This information is used to update functional and mode settings for the
        Enter Service Mode. This information may be written.
        '''
        pass

    def set_watt_var(self, params=None):
        """ Get/set IEEE 1547 SunSpec Active power-reactive power

            Active Power-Reactive Power Mode Enable = 712.Ena
            P/Q Curve Points = 712.WattVar.Crv.Pt

        :param params: Dictionary of values for the IEEE 1547 WV write
        :return: Dictionary of values for the IEEE 1547 WV read

        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                if 'wv' in self.inv.models:
                    if params.get('Ena') is not None:
                        self.inv.wv.WMaxRtg = params.get('Ena')
                    if params.get('VRef') is not None:
                        self.inv.wv.WMaxRtg = params.get('VRef')
                    if params.get('VRefAuto') is not None:
                        self.inv.wv.WMaxRtg = params.get('VRefAuto')
                    if params.get('VRefTms') is not None:
                        self.inv.wv.WMaxRtg = params.get('VRefTms')
                    if params.get('VoltVar.Crv.Pt') is not None:
                        self.inv.wv.WMaxRtg = params.get('VoltVar.Crv.Pt')
                    if params.get('RspTms') is not None:
                        self.inv.wv.WMaxRtg = params.get('RspTms')
                    self.pf.common.write()

            else:
                if self.ts is not None:
                    self.ts.log_warning('No params sent to set_watt_var')

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def get_watt_var(self, params=None):
        """ Get IEEE 1547 SunSpec Active power-reactive power

            Active Power-Reactive Power Mode Enable = 712.Ena
            P/Q Curve Points = 712.WattVar.Crv.Pt

        :param params: Dictionary of values for the IEEE 1547 WV write
        :return: Dictionary of values for the IEEE 1547 WV read

        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if 'wv' in self.inv.models:
                self.inv.vv.read()
                params['Ena'] = self.inv.wv.Ena
                params['VRef'] = self.inv.wv.VRef
                params['VRefAuto'] = self.inv.wv.VRefAuto
                params['VRefTms'] = self.inv.wv.VRefTms
                params['VRefAuto'] = self.inv.wv.VRefAuto
                params['VoltVar.Crv.Pt'] = self.inv.wv.VoltVar.Crv.Pt
                params['RspTms'] = self.inv.wv.RspTms

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def set_volt_watt(self, params=None):
        pass

    def set_volt_trip(self, params=None):
        pass

    def set_freq_trip(self, params=None):
        pass

    def set_volt_cessation(self, params=None):
        pass

    def get_curve_settings(self):
        pass

