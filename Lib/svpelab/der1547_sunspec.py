'''
DER1547 methods defined for SunSpec Modbus devices
'''

import os
import sunspec2.modbus.client as client
import sunspec2.file.client as file_client
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
    info.param(pname('ifc_type'), label='Interface Type', default=client.RTU,
               values=[client.RTU, client.TCP, client.MAPPED])
    info.param(pname('slave_id'), label='Slave Id', default=1)
    # RTU parameters
    info.param(pname('ifc_name'), label='Interface Name', default='COM3',  active=pname('ifc_type'),
               active_value=[client.RTU],
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
    info.param(pname('cafile'), label='CA Certificate', default=None, active=pname('ifc_type'),
               active_value=[client.TCP],
               desc='Path to certificate authority (CA) certificate to use for validating server certificates.')
    info.param(pname('certfile'), label='Client TLS Certificate', default=None, active=pname('ifc_type'),
               active_value=[client.TCP], desc='Path to client TLS certificate to use for client authentication.')
    info.param(pname('keyfile'), label='Client TLS Key', default=None, active=pname('ifc_type'),
               active_value=[client.TCP], desc='Path to client TLS key to use for client authentication.')
    info.param(pname('insecure_skip_tls_verify'), label='Skip TLS Verification', default=False,
               active=pname('ifc_type'), active_value=[client.TCP], desc='Skip Verification of Server TLS Certificate.')
    # Mapped parameters
    info.param(pname('map_name'), label='Map File', default='device_1547.json', active=pname('ifc_type'),
               active_value=[client.MAPPED], ptype=script.PTYPE_FILE)



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
        self.ifc_type = None
        self.ts = ts

    def param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):
        self.open()

    def open(self):
        self.ifc_type = self.param_value('ifc_type')
        slave_id = self.param_value('slave_id')

        if self.ifc_type == client.TCP:
            ipaddr = self.param_value('ipaddr')
            ipport = self.param_value('ipport')

            tls = self.param_value('tls')
            cafile = self.param_value('cafile')
            certfile = self.param_value('certfile')
            keyfile = self.param_value('keyfile')
            skip_verify = self.param_value('insecure_skip_tls_verify')

            try:  # attempt to use pysunspec2 that supports TLS encryption
                self.inv = client.SunSpecClientDeviceTCP(self.ifc_type, slave_id=slave_id, ipaddr=ipaddr, ipport=ipport,
                                                         tls=tls, cafile=cafile, certfile=certfile, keyfile=keyfile,
                                                         insecure_skip_tls_verify=skip_verify)
            except Exception as e:  # fallback to old version
                if self.ts is not None:
                    self.ts.log('Could not create Modbus client with TLS encryption: %s. Attempted unencrypted option.')
                else:
                    print('Could not create Modbus client with TLS encryption: %s.  Attempted unencrypted option.')
                self.inv = client.SunSpecClientDeviceTCP(self.ifc_type, slave_id=slave_id, ipaddr=ipaddr, ipport=ipport)

        elif self.ifc_type == client.MAPPED:
            ifc_name = self.param_value('map_name')
            self.inv = file_client.FileClientDevice(ifc_name)
        elif self.ifc_type == client.RTU:
            ifc_name = self.param_value('ifc_name')
            baudrate = self.param_value('baudrate')
            parity = self.param_value('parity')
            self.inv = client.SunSpecClientDeviceTCP(self.ifc_type, slave_id=slave_id, name=ifc_name,
                                                     baudrate=baudrate, parity=parity)
        else:
            raise der1547.DER1547Error('Unknown connection type. Not MAPPED, RTU, or TCP.')

        self.inv.scan()

        # self.ts.log('device models = %s' % self.inv.models)

    def close(self):
        if self.inv is not None and self.ifc_type != client.MAPPED:
            self.inv.close()
            self.inv = None

    def info(self):
        info = 'SunSpec Device'
        if self.inv is not None:
            common = self.inv.common[0]
            info = 'SunSpec Device, Mn: %s, Md: %s, Opt: %s, Vr: %s, SN: %s' % \
                   (common.Mn.cvalue, common.Md.cvalue, common.Opt.cvalue, common.Vr.cvalue, common.SN.cvalue)
        return info

    def get_models(self):
        """ Get SunSpec Models

        :return: list of models

        """
        if self.inv is None:
            raise der1547.DER1547Error('DER not initialized')

        model_dict = self.inv.models
        models = []
        for k in model_dict.keys():
            if not isinstance(k, int) and k is not None:
                models.append(k)

        return models

    def print_modbus_map(self, models=None, w_labels=None):
        """
        Prints the modbus map of the DER device

        :param models: model or models to read, if None read all
        :param w_labels: if True, print the modbus points with labels included
        :return: None
        """

        model_list = []
        if models is None:
            model_list = self.get_models()
        elif isinstance(models, str):
            model_list = [models]
        elif isinstance(models, list):
            model_list = models
        else:
            der1547.DER1547Error('Incorrect model format for printing modbus map.')

        if not w_labels:
            for m in model_list:
                mod = eval('self.inv.%s[0]' % m)
                self.ts.log('%s' % mod)
        else:
            for m in model_list:
                self.ts.log('-'*50)
                self.ts.log('Model: %s' % m)
                self.ts.log('')
                for pt in eval('self.inv.%s[0].points.keys()' % m):
                    # self.ts.log_debug('pt: %s' % pt)
                    if pt != 'Pad':
                        label = eval('self.inv.%s[0].points[pt].pdef["label"]' % m)
                        val = eval('self.inv.%s[0].points[pt].cvalue' % m)
                        self.ts.log('%s [%s]: %s' % (label, pt, val))

    def get_nameplate(self):
        """
        Get Nameplate information - See IEEE 1547-2018 Table 28
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                         Units
        ______________________________________________________________________________________________________________
        Active power rating at unity power factor               np_p_max                                kW
            (nameplate active power rating)
        Active power rating at specified over-excited           np_p_max_over_pf                        kW
            power factor
        Specified over-excited power factor                     np_over_pf                              Decimal
        Active power rating at specified under-excited          np_p_max_under_pf                       kW
            power factor
        Specified under-excited power factor                    np_under_pf                             Decimal
        Apparent power maximum rating                           np_va_max                               kVA
        Normal operating performance category                   np_normal_op_cat                        str
            e.g., CAT_A-CAT_B
        Abnormal operating performance category                 np_abnormal_op_cat                      str
            e.g., CAT_II-CAT_III
        Intentional Island  Category (optional)                 np_intentional_island_cat               str
            e.g., UNCAT-INT_ISLAND_CAP-BLACK_START-ISOCH
        Reactive power injected maximum rating                  np_q_max_inj                            kVAr
        Reactive power absorbed maximum rating                  np_q_max_abs                            kVAr
        Active power charge maximum rating                      np_p_max_charge                         kW
        Apparent power charge maximum rating                    np_apparent_power_charge_max            kVA
        AC voltage nominal rating                               np_ac_v_nom                             Vac
        AC voltage maximum rating                               np_ac_v_max_er_max                      Vac
        AC voltage minimum rating                               np_ac_v_min_er_min                      Vac
        Supported control mode functions                        np_supported_modes                      dict
            e.g., {'CONST_PF': True 'QV': False} with keys:
            Supports Low Voltage Ride-Through Mode: 'UV'
            Supports High Voltage Ride-Through Mode: 'OV'
            Supports Low Freq Ride-Through Mode: 'UF'
            Supports High Freq Ride-Through Mode: 'OF'
            Supports Active Power Limit Mode: 'P_LIM'
            Supports Volt-Watt Mode: 'PV'
            Supports Frequency-Watt Curve Mode: 'PF'
            Supports Constant VArs Mode: 'CONST_Q'
            Supports Fixed Power Factor Mode: 'CONST_PF'
            Supports Volt-VAr Control Mode: 'QV'
            Supports Watt-VAr Mode: 'QP'
        Reactive susceptance that remains connected to          np_reactive_susceptance                 Siemens
            the Area EPS in the cease to energize and trip
            state
        Maximum resistance (R) between RPA and POC.             np_remote_meter_resistance              Ohms
            (unsupported in 1547)
        Maximum reactance (X) between RPA and POC.              np_remote_meter_reactance               Ohms
            (unsupported in 1547)
        Manufacturer                                            np_manufacturer                         str
        Model                                                   np_model                                str
        Serial number                                           np_serial_num                           str
        Version                                                 np_fw_ver                               str

        :return: dict with keys shown above.
        """

        if self.inv is None:
            raise der1547.DER1547Error('DER not initialized')

        params = {}
        self.inv.DERCapacity[0].read()
        der_capacity = self.inv.DERCapacity[0]
        # self.ts.log('der_capacity: %s' % der_capacity)
        if der_capacity.WMaxRtg.cvalue is not None:
            params['np_p_max'] = der_capacity.WMaxRtg.cvalue / 1000.
        if der_capacity.WOvrExtRtg.cvalue is not None:
            params['np_p_max_over_pf'] = der_capacity.WOvrExtRtg.cvalue / 1000.
        if der_capacity.PFOvrExtRtg.cvalue is not None:
            params['np_over_pf'] = der_capacity.PFOvrExtRtg.cvalue

        if der_capacity.WUndExtRtg.cvalue is not None:
            params['np_p_max_under_pf'] = der_capacity.WUndExtRtg.cvalue / 1000.
        if der_capacity.PFUndExtRtg.cvalue is not None:
            params['np_under_pf'] = der_capacity.PFUndExtRtg.cvalue

        if der_capacity.VAMaxRtg.cvalue is not None:
            params['np_va_max'] = der_capacity.VAMaxRtg.cvalue / 1000.

        if der_capacity.NorOpCatRtg.cvalue is not None:
            params['np_normal_op_cat'] = der_capacity.NorOpCatRtg.cvalue
        if der_capacity.AbnOpCatRtg.cvalue is not None:
            params['np_abnormal_op_cat'] = der_capacity.AbnOpCatRtg.cvalue
        if der_capacity.IntIslandCatRtg.cvalue is not None:
            params['np_intentional_island_cat'] = der_capacity.IntIslandCatRtg.cvalue

        if der_capacity.VarMaxInjRtg.cvalue is not None:
            params['np_q_max_inj'] = der_capacity.VarMaxInjRtg.cvalue / 1000.
        if der_capacity.VarMaxAbsRtg.cvalue is not None:
            params['np_q_max_abs'] = der_capacity.VarMaxAbsRtg.cvalue / 1000.
        if der_capacity.WChaRteMaxRtg.cvalue is not None:
            params['np_p_max_charge'] = der_capacity.WChaRteMaxRtg.cvalue / 1000.
        if der_capacity.WDisChaRteMaxRtg.cvalue is not None:  # not in 1547
            params['np_p_max_discharge'] = der_capacity.WDisChaRteMaxRtg.cvalue / 1000.

        if der_capacity.VAChaRteMaxRtg.cvalue is not None:
            params['np_apparent_power_charge_max'] = der_capacity.VAChaRteMaxRtg.cvalue / 1000.
        if der_capacity.VADisChaRteMaxRtg.cvalue is not None:  # not in 1547
            params['np_apparent_power_discharge_max'] = der_capacity.VADisChaRteMaxRtg.cvalue / 1000.

        if der_capacity.VNomRtg.cvalue is not None:
            params['np_ac_v_nom'] = der_capacity.VNomRtg.cvalue
        if der_capacity.VMaxRtg.cvalue is not None:
            params['np_ac_v_max_er_max'] = der_capacity.VMaxRtg.cvalue
        if der_capacity.VMinRtg.cvalue is not None:
            params['np_ac_v_min_er_min'] = der_capacity.VMinRtg.cvalue

        if der_capacity.CtrlModes.cvalue is not None:
            params['np_supported_modes'] = der_capacity.CtrlModes.cvalue
        if der_capacity.ReactSusceptRtg.cvalue is not None:
            params['np_reactive_susceptance'] = der_capacity.ReactSusceptRtg.cvalue

        params['np_remote_meter_resistance'] = None
        params['np_remote_meter_reactance'] = None

        self.inv.common[0].read()
        common = self.inv.common[0]
        if common.Mn.cvalue is not None:
            params['np_manufacturer'] = common.Mn.cvalue
        if common.Md.cvalue is not None:
            params['np_model'] = common.Md.cvalue
        if common.SN.cvalue is not None:
            params['np_serial_num'] = common.SN.cvalue
        if common.Vr.cvalue is not None:
            params['np_fw_ver'] = common.Vr.cvalue

        return params

        # 'DERMeasureAC', 'DERCapacity', 'DEREnterService', 'DERCtlAC', 'DERVoltVar', 'DERVoltWatt', 'DERTripLV', \
        # 'DERTripHV', 'DERTripLF', 'DERTripHF', 'DERFreqDroop', 'DERWattVar', 'DERMeasureDC'

    def get_configuration(self):
        """
        Get configuration information in the 1547 DER. Each rating in Table 28 may have an associated configuration
        setting that represents the as-configured value. If a configuration setting value is different from the
        corresponding nameplate value, the configuration setting value shall be used as the rating within the DER.

        :return: params dict with keys shown in nameplate.
        """

        if self.inv is None:
            raise der1547.DER1547Error('DER not initialized')

        # self.ts.log(self.get_models())

        params = {}
        self.inv.DERCapacity[0].read()
        der_capacity = self.inv.DERCapacity[0]
        # self.ts.log('der_capacity: %s' % der_capacity)
        if der_capacity.WMax.cvalue is not None:
            params['np_p_max'] = der_capacity.WMax.cvalue / 1000.
        if der_capacity.WMaxOvrExt.cvalue is not None:
            params['np_p_max_over_pf'] = der_capacity.WMaxOvrExt.cvalue / 1000.
        # if der_capacity.PFOvrExt.cvalue is not None:
        #     params['np_over_pf'] = der_capacity.PFOvrExt.cvalue

        if der_capacity.WMaxUndExt.cvalue is not None:
            params['np_p_max_under_pf'] = der_capacity.WMaxUndExt.cvalue / 1000.
        # if der_capacity.PFUndExt.cvalue is not None:
        #     params['np_under_pf'] = der_capacity.PFUndExt.cvalue

        if der_capacity.VAMax.cvalue is not None:
            params['np_va_max'] = der_capacity.VAMax.cvalue / 1000.

        if der_capacity.VarMaxInj.cvalue is not None:
            params['np_q_max_inj'] = der_capacity.VarMaxInj.cvalue / 1000.
        if der_capacity.VarMaxAbs.cvalue is not None:
            params['np_q_max_abs'] = der_capacity.VarMaxAbs.cvalue / 1000.
        if der_capacity.WChaRteMax.cvalue is not None:
            params['np_p_max_charge'] = der_capacity.WChaRteMax.cvalue / 1000.
        if der_capacity.WDisChaRteMax.cvalue is not None:  # not in 1547
            params['np_p_max_discharge'] = der_capacity.WDisChaRteMax.cvalue / 1000.

        if der_capacity.VAChaRteMax.cvalue is not None:
            params['np_apparent_power_charge_max'] = der_capacity.VAChaRteMax.cvalue / 1000.
        if der_capacity.VADisChaRteMax.cvalue is not None:  # not in 1547
            params['np_apparent_power_discharge_max'] = der_capacity.VADisChaRteMax.cvalue / 1000.

        if der_capacity.Vnom.cvalue is not None:
            params['np_ac_v_nom'] = der_capacity.Vnom.cvalue
        if der_capacity.VMax.cvalue is not None:
            params['np_ac_v_max_er_max'] = der_capacity.VMax.cvalue
        if der_capacity.VMin.cvalue is not None:
            params['np_ac_v_min_er_min'] = der_capacity.VMin.cvalue

        if der_capacity.CtrlModes.cvalue is not None:
            params['np_supported_modes'] = der_capacity.CtrlModes.cvalue
        if der_capacity.ReactSusceptRtg.cvalue is not None:
            params['np_reactive_susceptance'] = der_capacity.ReactSusceptRtg.cvalue

        params['np_remote_meter_resistance'] = None
        params['np_remote_meter_reactance'] = None

        self.inv.common[0].read()
        common = self.inv.common[0]
        if common.Mn.cvalue is not None:
            params['np_manufacturer'] = common.Mn.cvalue
        if common.Md.cvalue is not None:
            params['np_model'] = common.Md.cvalue
        if common.SN.cvalue is not None:
            params['np_serial_num'] = common.SN.cvalue
        if common.Vr.cvalue is not None:
            params['np_fw_ver'] = common.Vr.cvalue

        return params

    def set_configuration(self, params=None):
        """
        Set configuration information. params are those in get_configuration().
        """

        der_capacity = self.inv.DERCapacity[0]
        der_capacity.read()

        if params.get('np_p_max') is not None:
            der_capacity.WMax.cvalue = params.get('np_p_max') * 1000.
        if params.get('np_p_max_over_pf') is not None:
            der_capacity.WMaxOvrExt.cvalue = params.get('np_p_max_over_pf') * 1000.
        if params.get('np_p_max_under_pf') is not None:
            der_capacity.WMaxUndExt.cvalue = params.get('np_p_max_under_pf') * 1000.

        if params.get('np_va_max') is not None:
            der_capacity.VAMax.cvalue = params.get('np_va_max') * 1000.

        if params.get('np_q_max_inj') is not None:
            der_capacity.VarMaxInj.cvalue = params.get('np_q_max_inj') * 1000.
        if params.get('np_q_max_abs') is not None:
            der_capacity.VarMaxAbs.cvalue = params.get('np_q_max_abs') * 1000.
        if params.get('np_p_max_charge') is not None:
            der_capacity.WChaRteMax.cvalue = params.get('np_p_max_charge') * 1000.
        if params.get('np_p_max_discharge') is not None:
            der_capacity.WDisChaRteMax.cvalue = params.get('np_p_max_discharge') * 1000.

        if params.get('np_apparent_power_charge_max') is not None:
            der_capacity.VAChaRteMax.cvalue = params.get('np_apparent_power_charge_max') * 1000.
        if params.get('np_apparent_power_discharge_max') is not None:
            der_capacity.VADisChaRteMax.cvalue = params.get('np_apparent_power_discharge_max') * 1000.

        if params.get('np_ac_v_nom') is not None:
            der_capacity.Vnom.cvalue = params.get('np_ac_v_nom')
        if params.get('np_ac_v_max_er_max') is not None:
            der_capacity.VMax.cvalue = params.get('np_ac_v_max_er_max')
        if params.get('np_ac_v_min_er_min') is not None:
            der_capacity.VMin.cvalue = params.get('np_ac_v_min_er_min')

        if params.get('np_supported_modes') is not None:
            der_capacity.CtrlModes.cvalue = params.get('np_supported_modes')
        if params.get('np_reactive_susceptance') is not None:
            der_capacity.ReactSusceptRtg.cvalue = params.get('np_reactive_susceptance')
        der_capacity.write()

        common = self.inv.common[0]
        common.read()
        if params.get('np_manufacturer') is not None:
            common.Mn.cvalue = params.get('np_manufacturer')
        if params.get('np_model') is not None:
            common.Md.cvalue = params.get('np_model')
        if params.get('np_serial_num') is not None:
            common.SN.cvalue = params.get('np_serial_num')
        if params.get('np_fw_ver') is not None:
            common.Vr.cvalue = params.get('np_fw_ver')
        common.write()

    def get_settings(self):
        """
        Get configuration information in the 1547 DER. Each rating in Table 28 may have an associated configuration
        setting that represents the as-configured value. If a configuration setting value is different from the
        corresponding nameplate value, the configuration setting value shall be used as the rating within the DER.

        :return: params dict with keys shown in nameplate.
        """
        return self.get_configuration()

    def set_settings(self, params=None):
        """
        Set configuration information. params are those in get_configuration().
        """
        return self.set_configuration(params)

    def get_monitoring(self):
        """
        This information is indicative of the present operating conditions of the
        DER. This information may be read.

        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                    units
        ______________________________________________________________________________________________________________
        Active Power                                                mn_w                               kW
        Reactive Power                                              mn_var                             kVAr
        Voltage (list)                                              mn_v                               V-N list
            Single phase devices: [V]
            3-phase devices: [V1, V2, V3]
        Frequency                                                   mn_hz                              Hz

        Operational State                                           mn_st                              dict of bools
            {'mn_op_local': System in local/maintenance state
             'mn_op_lockout': System locked out
             'mn_op_starting': Start command has been received
             'mn_op_stopping': Emergency Stop command has been received
             'mn_op_started': Started
             'mn_op_stopped': Stopped
             'mn_op_permission_to_start': Start Permission Granted
             'mn_op_permission_to_stop': Stop Permission Granted}

        Connection State                                            mn_conn                            dict of bools
            {'mn_conn_connected_idle': Idle-Connected
             'mn_conn_connected_generating': On-Connected
             'mn_conn_connected_charging': On-Charging-Connected
             'mn_conn_off_available': Off-Available
             'mn_conn_off_not_available': Off-Not-Available
             'mn_conn_switch_closed_status': Switch Closed
             'mn_conn_switch_closed_movement': Switch Moving}

        Alarm Status                                                mn_alrm                            dict of bools
            Reported Alarm Status matches the device
            present alarm condition for alarm and no
            alarm conditions. For test purposes only, the
            DER manufacturer shall specify at least one
            way an alarm condition that is supported in
            the protocol being tested can be set and
            cleared.
            {'mn_alm_system_comm_error': System Communication Error
             'mn_alm_priority_1': System Has Priority 1 Alarms
             'mn_alm_priority_2': System Has Priority 2 Alarms
             'mn_alm_priority_3': System Has Priority 3 Alarms
             'mn_alm_storage_chg_max': Storage State of Charge at Maximum. Maximum Usable State of Charge reached.
             'mn_alm_storage_chg_high': Storage State of Charge is Too High. Maximum Reserve reached.
             'mn_alm_storage_chg_low': Storage State of Charge is Too Low. Minimum Reserve reached.
             'mn_alm_storage_chg_depleted': Storage State of Charge is Depleted. Minimum Usable State of Charge Reached.
             'mn_alm_internal_temp_high': Storage Internal Temperature is Too High
             'mn_alm_internal_temp_low': Storage External (Ambient) Temperature is Too High}

        Operational State of Charge (not required in 1547)          mn_soc_pct                         pct

        :return: dict with keys shown above.
        """

        if self.inv is None:
            raise der1547.DER1547Error('DER not initialized')

        params = {}
        self.inv.DERMeasureAC[0].read()
        der_pts = self.inv.DERMeasureAC[0]

        if der_pts.W.cvalue is not None:
            params['mn_w'] = der_pts.W.cvalue / 1000.
        if der_pts.Var.cvalue is not None:
            params['mn_var'] = der_pts.Var.cvalue / 1000.

        if der_pts.ACType.cvalue is not None:
            phases = der_pts.ACType.cvalue
        else:
            phases = 1  # assume single/split phase DER
        if phases == 1:
            params['mn_v'] = [der_pts.LNV.cvalue]
        else:  # phases == 3
            params['mn_v'] = []
            params['mn_v'].append(der_pts.VL1.cvalue)
            params['mn_v'].append(der_pts.VL2.cvalue)
            params['mn_v'].append(der_pts.VL3N.cvalue)

        if der_pts.Hz.cvalue is not None:
            params['mn_hz'] = der_pts.Hz.cvalue

        # need to convert values to dict up with example
        if der_pts.St.cvalue is not None:
            params['mn_st'] = der_pts.St.cvalue

        if der_pts.ConnSt.cvalue is not None:
            params['mn_st'] = der_pts.ConnSt.cvalue

        if der_pts.MnAlrmInfo.cvalue is not None:
            params['mn_alrm'] = der_pts.MnAlrmInfo.cvalue

        return params

    def get_const_pf(self):
        """
        Get Constant Power Factor Mode control settings. IEEE 1547-2018 Table 30.
        ________________________________________________________________________________________________________________
        Parameter                                               params dict key                     units
        ________________________________________________________________________________________________________________
        Constant Power Factor Mode Select                       const_pf_mode_enable_as             bool (True=Enabled)
        Constant Power Factor Excitation                        const_pf_excitation_as              str ('inj', 'abs')
        Constant Power Factor Absorbing Setting                 const_pf_abs_as                     decimal
        Constant Power Factor Injecting Setting                 const_pf_inj_as                     decimal

        SunSpec Points:
            Power Factor Enable (W Inj) Enable [PFWInjEna]: 0
            Power Factor Reversion Enable (W Inj) [PFWInjRvrtEna]: None
            PF Reversion Time (W Inj) [PFWInjRvrtTms]: None
            PF Reversion Time Rem (W Inj) [PFWInjRvrtRem]: None

            Power Factor Enable (W Abs) Enable [PFWAbsEna]: 0
            Power Factor Reversion Enable (W Abs) [PFWAbsRvrtEna]: None
            PF Reversion Time (W Abs) [PFWAbsRvrtTms]: None
            PF Reversion Time Rem (W Abs) [PFWAbsRvrtRem]: None

        :return: dict with keys shown above.
        """

        params = {}
        der_pts = self.inv.DERCtlAC[0]
        der_pts.read()

        if der_pts.PFWInjEna.cvalue is not None:
            if der_pts.PFWInjEna.cvalue == 1:
                params['const_pf_mode_enable_as'] = True
            else:
                params['const_pf_mode_enable_as'] = False

        if der_pts.WMaxLim.cvalue is not None:
            params['const_pf_abs_as'] = der_pts.WMaxLim.cvalue / 100.
        if der_pts.WMaxLim.cvalue is not None:
            params['const_pf_inj_as'] = der_pts.WMaxLim.cvalue / 100.

        if der_pts.WMaxLim.cvalue is not None:
            params['p_lim_w_as'] = der_pts.WMaxLim.cvalue / 100.
        if der_pts.WMaxLim.cvalue is not None:
            params['p_lim_w_as'] = der_pts.WMaxLim.cvalue / 100.


        return params

    def set_const_pf(self, params=None):
        """
        Set Constant Power Factor Mode control settings.
        """
        pass

    def get_qv(self):
        """
        Get Q(V) parameters. [Volt-Var]
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Voltage-Reactive Power Mode Enable                          qv_mode_enable_as               bool (True=Enabled)
        Vref Min (RofA not specified in 1547)                       qv_vref_er_min                  V p.u.
        Vref (0.95-1.05)                                            qv_vref_as                      V p.u.
        Vref Max (RofA not specified in 1547)                       qv_vref_er_max                  V p.u.

        Autonomous Vref Adjustment Enable                           qv_vref_auto_mode_as            str
        Vref adjustment time Constant (RofA not specified           qv_vref_olrt_er_min             s
            in 1547)
        Vref adjustment time Constant (300-5000)                    qv_vref_olrt_as                 s
        Vref adjustment time Constant (RofA not specified           qv_vref_olrt_er_max             s
            in 1547)

        Q(V) Curve Point V1-4 Range of Adjustability (Min)          qv_curve_v_er_min               V p.u.
            (RofA not specified in 1547) (list)
        Q(V) Curve Point V1-4 (list, e.g., [95, 99, 101, 105])      qv_curve_v_pts                  V p.u.
        Q(V) Curve Point V1-4 Range of Adjustability (Max)          qv_curve_v_er_max               V p.u.
            (RofA not specified in 1547) (list)

        Q(V) Curve Point Q1-4 Range of Adjustability (Min)          qv_curve_q_er_min               VAr p.u.
            (RofA not specified in 1547) (list)
        Q(V) Curve Point Q1-4 (list)                                qv_curve_q_pts                  VAr p.u.
        Q(V) Curve Point Q1-4 Range of Adjustability (Max)          qv_curve_q_er_max               VAr p.u.
            (RofA not specified in 1547) (list)

        Q(V) Open Loop Response Time (RofA not specified in 1547)   qv_olrt_er_min                  s
        Q(V) Open Loop Response Time Setting  (1-90)                qv_olrt_as                      s
        Q(V) Open Loop Response Time (RofA not specified in 1547)   qv_olrt_er_max                  s

        :return: dict with keys shown above.
        """
        return None

    def set_qv(self, params=None):
        """
        Set Q(V) parameters. [Volt-Var]
        """
        pass

    def get_qp(self):
        """
        Get Q(P) parameters. [Watt-Var] - IEEE 1547 Table 32
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        Active Power-Reactive Power (Watt-VAr) Enable               qp_mode_enable_as                   bool
        P-Q curve P1-3 Generation (RofA not Specified in 1547)      qp_curve_p_gen_pts_er_min           P p.u.
        P-Q curve P1-3 Generation Setting (list)                    qp_curve_p_gen_pts_as               P p.u.
        P-Q curve P1-3 Generation (RofA not Specified in 1547)      qp_curve_p_gen_pts_er_max           P p.u.

        P-Q curve Q1-3 Generation (RofA not Specified in 1547)      qp_curve_q_gen_pts_er_min           VAr p.u.
        P-Q curve Q1-3 Generation Setting (list)                    qp_curve_q_gen_pts_as               VAr p.u.
        P-Q curve Q1-3 Generation (RofA not Specified in 1547)      qp_curve_q_gen_pts_er_max           VAr p.u.

        P-Q curve P1-3 Load (RofA not Specified in 1547)            qp_curve_p_load_pts_er_min          P p.u.
        P-Q curve P1-3 Load Setting (list)                          qp_curve_p_load_pts_as              P p.u.
        P-Q curve P1-3 Load (RofA not Specified in 1547)            qp_curve_p_load_pts_er_max          P p.u.

        P-Q curve Q1-3 Load (RofA not Specified in 1547)            qp_curve_q_load_pts_er_min          VAr p.u.
        P-Q curve Q1-3 Load Setting (list)                          qp_curve_q_load_pts_as              VAr p.u.
        P-Q curve Q1-3 Load (RofA not Specified in 1547)            qp_curve_q_load_pts_er_max          VAr p.u.

        QP Open Loop Response Time (RofA not specified in 1547)     qp_olrt_er_min                      s
        QP Open Loop Response Time Setting                          qp_olrt_as                          s
        QP Open Loop Response Time (RofA not specified in 1547)     qp_olrt_er_max                      s

        :return: dict with keys shown above.
        """
        return None

    def set_qp(self, params=None):
        """
        Set Q(P) parameters. [Watt-Var]
        """
        pass

    def get_pv(self):
        """
        Get P(V), Voltage-Active Power (Volt-Watt), Parameters
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                         units
        ______________________________________________________________________________________________________________
        Voltage-Active Power Mode Enable                            pv_mode_enable_as                       bool
        P(V) Curve Point V1-2 Min (RofA not specified in 1547)      pv_curve_v_pts_er_min                   V p.u.
        P(V) Curve Point V1-2 Setting (list)                        pv_curve_v_pts_as                       V p.u.
        P(V) Curve Point V1-2 Max (RofA not specified in 1547)      pv_curve_v_pts_er_max                   V p.u.

        P(V) Curve Point P1-2 Min (RofA not specified in 1547)      pv_curve_p_pts_er_min                   P p.u.
        P(V) Curve Point P1-2 Setting (list)                        pv_curve_p_pts_as                       P p.u.
        P(V) Curve Point P1-2 Max (RofA not specified in 1547)      pv_curve_p_pts_er_max                   P p.u.

        P(V) Curve Point P1-P'2 Min (RofA not specified in 1547)    pv_curve_p_bidrct_pts_er_min            P p.u.
        P(V) Curve Point P1-P'2 Setting (list)                      pv_curve_p_bidrct_pts_as                P p.u.
        P(V) Curve Point P1-P'2 Max (RofA not specified in 1547)    pv_curve_p_bidrct_pts_er_max            P p.u.

        P(V) Open Loop Response time min (RofA not specified        pv_olrt_er_min                          s
            in 1547)
        P(V) Open Loop Response time Setting (0.5-60)               pv_olrt_as                              s
        P(V) Open Loop Response time max (RofA not specified        pv_olrt_er_max                          s
            in 1547)

        :return: dict with keys shown above.
        """
        return None

    def set_pv(self, params=None):
        """
        Set P(V), Voltage-Active Power (Volt-Watt), Parameters
        """
        pass

    def get_const_q(self):
        """
        Get Constant Reactive Power Mode
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                     units
        ______________________________________________________________________________________________________________
        Constant Reactive Power Mode Enable                     const_q_mode_enable_as              bool (True=Enabled)
        Constant Reactive Power Excitation (not specified in    const_q_mode_excitation_as          str ('inj', 'abs')
            1547)
        Constant Reactive power setting (See Table 7)           const_q_as                          VAr p.u.
        Maximum Response Time to maintain constant reactive     const_q_olrt_as                     s
            power (not specified in 1547)

        :return: dict with keys shown above.

        SunSpec Points:
            Set Reactive Power Enable [VarSetEna]: None
            Set Reactive Power Mode [VarSetMod]: None
            Reactive Power Priority [VarSetPri]: None
            Reactive Power Setpoint (Vars) [VarSet]: None
            Reversion Reactive Power (Vars) [VarSetRvrt]: None
            Reactive Power Setpoint (Pct) [VarSetPct]: None
            Reversion Reactive Power (Pct) [VarSetPctRvrt]: None
            Reversion Reactive Power Enable [VarSetRvrtEna]: None
            Reactive Power Reversion Time [VarSetRvrtTms]: None
            Reactive Power Rev Time Rem [VarSetRvrtRem]: None

        """
        params = {}
        der_pts = self.inv.DERCtlAC[0]
        der_pts.read()

        if der_pts.VarSetEna.cvalue is not None:
            if der_pts.VarSetEna.cvalue == 1:
                params['const_q_mode_enable_as'] = True
            else:
                params['const_q_mode_enable_as'] = False

        if der_pts.VarSetPct.cvalue is not None:
            # use positive Q value with excitation indicating directionality
            params['const_q_as'] = abs(der_pts.VarSetPct.cvalue / 100.)

            if der_pts.VarSetPct.cvalue > 0:
                params['const_q_mode_excitation_as'] = 'inj'
            else:
                params['const_q_mode_excitation_as'] = 'abs'

        return params

    def set_const_q(self, params=None):
        """
        Set Constant Reactive Power Mode
        """

        der_pts = self.inv.DERCtlAC[0]
        der_pts.read()

        if params.get('const_q_mode_enable_as') is not None:
            if params.get('const_q_mode_enable_as'):
                der_pts.VarSetEna.cvalue = 1
            else:
                der_pts.VarSetEna.cvalue = 0

            # todo
            # der_pts.VarSetMod.cvalue = 'Pct'
            # der_pts.VarSetPri.cvalue = 'Reactive Powere Priority'

        if params.get('const_q_as') is not None:
            if params.get('const_q_mode_excitation_as') is not None:
                if params.get('const_q_mode_excitation_as') == 'inj':
                    der_pts.VarSetPct.cvalue = params.get('const_q_as') / 100.
                else:
                    der_pts.VarSetPct.cvalue = -1 * params.get('const_q_as') / 100.
            else:
                raise der1547.DER1547Error('No excitation provided to set_const_q() method.')

        return params

    def get_p_lim(self):
        """
        Get Limit maximum active power - IEEE 1547 Table 40
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          p_lim_mode_enable_as            bool (True=Enabled)
        Maximum Active Power                                        p_lim_w_as                     P p.u.

        SunSpec Points:
            Limit Max Active Power Enable [WMaxLimEna]: 0
            Limit Max Power Setpoint [WMaxLim]: 100.0
            Reversion Limit Max Power [WMaxLimRvrt]: None
            Reversion Limit Max Power Enable [WMaxLimRvrtEna]: None
            Limit Max Power Reversion Time [WMaxLimRvrtTms]: None
            Limit Max Power Rev Time Rem [WMaxLimRvrtRem]: None

            Set Active Power Enable [WSetEna]: None
            Set Active Power Mode [WSetMod]: None
            Active Power Setpoint (W) [WSet]: None
            Reversion Active Power (W) [WSetRvrt]: None
            Active Power Setpoint (Pct) [WSetPct]: None
            Reversion Active Power (Pct) [WSetPctRvrt]: None
            Reversion Active Power Enable [WSetRvrtEna]: None
            Active Power Reversion Time [WSetRvrtTms]: None
            Active Power Rev Time Rem [WSetRvrtRem]: None

        """
        params = {}
        der_pts = self.inv.DERCtlAC[0]
        der_pts.read()

        if der_pts.WMaxLimEna.cvalue is not None:
            if der_pts.WMaxLimEna.cvalue == 1:
                params['p_lim_mode_enable_as'] = True
            else:
                params['p_lim_mode_enable_as'] = False
        if der_pts.WMaxLim.cvalue is not None:
            params['p_lim_w_as'] = der_pts.WMaxLim.cvalue / 100.

        # todo for non-DER
        # if der_pts.WSetEna.cvalue is not None:
        #     params['p_lim_mode_enable_as'] = der_pts.WSetEna.cvalue
        # if der_pts.WSet.cvalue is not None:
        #     params['p_lim_mode_enable_as'] = der_pts.WSet.cvalue

        return params

    def set_p_lim(self, params=None):
        """
        Get Limit maximum active power.
        """
        der_pts = self.inv.DERCtlAC[0]
        der_pts.read()

        if params.get('p_lim_mode_enable_as') is not None:
            if params.get('p_lim_mode_enable_as'):
                der_pts.WMaxLimEna.cvalue = 1
            else:
                der_pts.WMaxLimEna.cvalue = 0
        if params.get('p_lim_w_as') is not None:
            der_pts.WMaxLim.cvalue = params.get('p_lim_w_as') * 100.

        # todo for non-DER
        # if params.get('p_lim_mode_enable_as') is not None:
        #     der_pts.WSetEna.cvalue = params.get('p_lim_mode_enable_as')
        # if params.get('p_lim_mode_enable_as') is not None:
        #     der_pts.WSet.cvalue = params.get('p_lim_mode_enable_as')

        return params

    def get_pf(self):
        """
        Get P(f), Frequency-Active Power Mode Parameters - IEEE 1547 Table 38
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          pf_mode_enable_as               bool (True=Enabled)
        P(f) Overfrequency Droop dbOF RofA min                      pf_dbof_er_min                  Hz
        P(f) Overfrequency Droop dbOF Setting                       pf_dbof_as                      Hz
        P(f) Overfrequency Droop dbOF RofA max                      pf_dbof_er_max                  Hz

        P(f) Underfrequency Droop dbUF RofA min                     pf_dbuf_er_min                  Hz
        P(f) Underfrequency Droop dbUF Setting                      pf_dbuf_as                      Hz
        P(f) Underfrequency Droop dbUF RofA max                     pf_dbuf_er_max                  Hz

        P(f) Overfrequency Droop kOF RofA min                       pf_kof_er_min                   unitless
        P(f) Overfrequency Droop kOF  Setting                       pf_kof_as                       unitless
        P(f) Overfrequency Droop kOF RofA max                       pf_kof_er_max                   unitless

        P(f) Underfrequency Droop kUF RofA min                      pf_kuf_er_min                   unitless
        P(f) Underfrequency Droop kUF Setting                       pf_kuf_as                       unitless
        P(f) Underfrequency Droop kUF RofA Max                      pf_kuf_er_max                   unitless

        P(f) Open Loop Response Time RofA min                       pf_olrt_er_min                  s
        P(f) Open Loop Response Time Setting                        pf_olrt_as                      s
        P(f) Open Loop Response Time RofA max                       pf_olrt_er_max                  s

        :return: dict with keys shown above.
        """
        pass

    def set_freq_watt(self, params=None):
        """
        Set P(f), Frequency-Active Power Mode Parameters
        """
        pass

    def get_es_permit_service(self):
        """
        Get Permit Service Mode Parameters - IEEE 1547 Table 39
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                 units
        ______________________________________________________________________________________________________________
        Permit service                                          es_permit_service_as            bool (True=Enabled)
        ES Voltage Low (RofA not specified in 1547)             es_v_low_er_min                 V p.u.
        ES Voltage Low Setting                                  es_v_low_as                     V p.u.
        ES Voltage Low (RofA not specified in 1547)             es_v_low_er_max                 V p.u.
        ES Voltage High (RofA not specified in 1547)            es_v_high_er_min                V p.u.
        ES Voltage High Setting                                 es_v_high_as                    V p.u.
        ES Voltage High (RofA not specified in 1547)            es_v_high_er_max                V p.u.
        ES Frequency Low (RofA not specified in 1547)           es_f_low_er_min                 Hz
        ES Frequency Low Setting                                es_f_low_as                     Hz
        ES Frequency Low (RofA not specified in 1547)           es_f_low_er_max                 Hz
        ES Frequency Low (RofA not specified in 1547)           es_f_high_er_min                Hz
        ES Frequency High Setting                               es_f_high_as                    Hz
        ES Frequency Low (RofA not specified in 1547)           es_f_high_er_max                Hz
        ES Randomized Delay                                     es_randomized_delay_as          bool (True=Enabled)
        ES Delay (RofA not specified in 1547)                   es_delay_er_min                 s
        ES Delay Setting                                        es_delay_as                     s
        ES Delay (RofA not specified in 1547)                   es_delay_er_max                 s
        ES Ramp Rate Min (RofA not specified in 1547)           es_ramp_rate_er_min             %/s
        ES Ramp Rate Setting                                    es_ramp_rate_as                 %/s
        ES Ramp Rate Min (RofA not specified in 1547)           es_ramp_rate_er_max             %/s

        :return: dict with keys shown above.
        """
        pass

    def set_es_permit_service(self, params=None):
        """
        Set Permit Service Mode Parameters
        """
        pass

    def get_ui(self):
        """
        Get Unintentional Islanding Parameters
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        Unintentional Islanding Mode (enabled/disabled). This       ui_mode_enable_as                   bool
            function is enabled by default, and disabled only by
            request from the Area EPS Operator.
            UI is always on in 1547 BUT 1547.1 says turn it off
            for some testing
        Unintential Islanding methods supported. Where multiple     ui_capability_er                    list str
            modes are supported place in a list.
            UI BLRC = Balanced RLC,
            UI PCPST = Powerline conducted,
            UI PHIT = Permissive Hardware-input,
            UI RMIP = Reverse/min relay. Methods other than UI
            BRLC may require supplemental comissioning tests.
            e.g., ['UI_BLRC', 'UI_PCPST', 'UI_PHIT', 'UI_RMIP']

        :return: dict with keys shown above.
        """
        pass

    def set_ui(self):
        """
        Get Unintentional Islanding Parameters
        """

    def get_ov(self, params=None):
        """
        Get Overvoltage Trip Parameters - IEEE 1547 Table 35
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        HV Trip Curve Point OV_V1-3 (see Tables 11-13)              ov_trip_v_pts_er_min                V p.u.
            (RofA not specified in 1547)
        HV Trip Curve Point OV_V1-3 Setting                         ov_trip_v_pts_as                    V p.u.
        HV Trip Curve Point OV_V1-3 (RofA not specified in 1547)    ov_trip_v_pts_er_max                V p.u.
        HV Trip Curve Point OV_T1-3 (see Tables 11-13)              ov_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        HV Trip Curve Point OV_T1-3 Setting                         ov_trip_t_pts_as                    s
        HV Trip Curve Point OV_T1-3 (RofA not specified in 1547)    ov_trip_t_pts_er_max                s

        :return: dict with keys shown above.
        """
        pass

    def set_ov(self, params=None):
        """
        Set Overvoltage Trip Parameters - IEEE 1547 Table 35
        """
        pass

    def get_uv(self, params=None):
        """
        Get Overvoltage Trip Parameters - IEEE 1547 Table 35
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        LV Trip Curve Point UV_V1-3 (see Tables 11-13)              uv_trip_v_pts_er_min                V p.u.
            (RofA not specified in 1547)
        LV Trip Curve Point UV_V1-3 Setting                         uv_trip_v_pts_as                    V p.u.
        LV Trip Curve Point UV_V1-3 (RofA not specified in 1547)    uv_trip_v_pts_er_max                V p.u.
        LV Trip Curve Point UV_T1-3 (see Tables 11-13)              uv_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        LV Trip Curve Point UV_T1-3 Setting                         uv_trip_t_pts_as                    s
        LV Trip Curve Point UV_T1-3 (RofA not specified in 1547)    uv_trip_t_pts_er_max                s

        :return: dict with keys shown above.
        """
        pass

    def set_uv(self, params=None):
        """
        Set Undervoltage Trip Parameters - IEEE 1547 Table 35
        """
        pass

    def get_of(self, params=None):
        """
        Get Overfrequency Trip Parameters - IEEE 1547 Table 37
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        OF Trip Curve Point OF_F1-3 (see Tables 11-13)              of_trip_f_pts_er_min                Hz
            (RofA not specified in 1547)
        OF Trip Curve Point OF_F1-3 Setting                         of_trip_f_pts_as                    Hz
        OF Trip Curve Point OF_F1-3 (RofA not specified in 1547)    of_trip_f_pts_er_max                Hz
        OF Trip Curve Point OF_T1-3 (see Tables 11-13)              of_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        OF Trip Curve Point OF_T1-3 Setting                         of_trip_t_pts_as                    s
        OF Trip Curve Point OF_T1-3 (RofA not specified in 1547)    of_trip_t_pts_er_max                s

        :return: dict with keys shown above.
        """
        pass

    def set_of(self, params=None):
        """
        Set Overfrequency Trip Parameters - IEEE 1547 Table 37
        """
        pass

    def get_uf(self, params=None):
        """
        Get Underfrequency Trip Parameters - IEEE 1547 Table 37
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        UF Trip Curve Point UF_F1-3 (see Tables 11-13)              uf_trip_f_pts_er_min                Hz
            (RofA not specified in 1547)
        UF Trip Curve Point UF_F1-3 Setting                         uf_trip_f_pts_as                    Hz
        UF Trip Curve Point UF_F1-3 (RofA not specified in 1547)    uf_trip_f_pts_er_max                Hz
        UF Trip Curve Point UF_T1-3 (see Tables 11-13)              uf_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        UF Trip Curve Point UF_T1-3 Setting                         uf_trip_t_pts_as                    s
        UF Trip Curve Point UF_T1-3 (RofA not specified in 1547)    uf_trip_t_pts_er_max                s

        :return: dict with keys shown above.
        """
        pass

    def set_uf(self, params=None):
        """
        Set Underfrequency Trip Parameters - IEEE 1547 Table 37
        """
        pass

    def get_ov_mc(self, params=None):
        """
        Get Overvoltage Momentary Cessation (MC) Parameters - IEEE 1547 Table 36
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        HV MC Curve Point OV_V1-3 (see Tables 11-13)                ov_mc_v_pts_er_min                  V p.u.
            (RofA not specified in 1547)
        HV MC Curve Point OV_V1-3 Setting                           ov_mc_v_pts_as                      V p.u.
        HV MC Curve Point OV_V1-3 (RofA not specified in 1547)      ov_mc_v_pts_er_max                  V p.u.
        HV MC Curve Point OV_T1-3 (see Tables 11-13)                ov_mc_t_pts_er_min                  s
            (RofA not specified in 1547)
        HV MC Curve Point OV_T1-3 Setting                           ov_mc_t_pts_as                      s
        HV MC Curve Point OV_T1-3 (RofA not specified in 1547)      ov_mc_t_pts_er_max                  s

        :return: dict with keys shown above.
        """
        pass

    def set_ov_mc(self, params=None):
        """
        Set Overvoltage Momentary Cessation (MC) Parameters - IEEE 1547 Table 36
        """
        pass

    def get_uv_mc(self, params=None):
        """
        Get Overvoltage Momentary Cessation (MC) Parameters - IEEE 1547 Table 36
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                   units
        _______________________________________________________________________________________________________________
        LV MC Curve Point UV_V1-3 (see Tables 11-13)                uv_mc_v_pts_er_min                V p.u.
            (RofA not specified in 1547)
        LV MC Curve Point UV_V1-3 Setting                           uv_mc_v_pts_as                    V p.u.
        LV MC Curve Point UV_V1-3 (RofA not specified in 1547)      uv_mc_v_pts_er_max                V p.u.
        LV MC Curve Point UV_T1-3 (see Tables 11-13)                uv_mc_t_pts_er_min                s
            (RofA not specified in 1547)
        LV MC Curve Point UV_T1-3 Setting                           uv_mc_t_pts_as                    s
        LV MC Curve Point UV_T1-3 (RofA not specified in 1547)      uv_mc_t_pts_er_max                s

        :return: dict with keys shown above.
        """
        pass

    def set_uv_mc(self, params=None):
        """
        Set Undervoltage Momentary Cessation (MC) Parameters - IEEE 1547 Table 36
        """
        pass

    def set_cease_to_energize(self, params=None):
        """

        A DER can be directed to cease to energize and trip by changing the Permit service setting to “disabled” as
        described in IEEE 1574 Section 4.10.3.
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                 units
        ______________________________________________________________________________________________________________
        Cease to energize and trip                              cease_to_energize               bool (True=Enabled)

        """
        return self.set_es_permit_service(params={'es_permit_service_as': params['cease_to_energize']})

    # Additional functions outside of IEEE 1547-2018
    def get_conn(self):
        """
        Get Connection - DER Connect/Disconnect Switch
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Connect/Disconnect Enable                                   conn_as                     bool (True=Enabled)
        """
        pass

    def set_conn(self, params=None):
        """
        Set Connection
        """
        pass

    def set_error(self, params=None):
        """
        Set Error, for testing Monitoring Data in DER

        error_as = set error
        """
        pass

