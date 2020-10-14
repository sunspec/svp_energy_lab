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

                        if val is not None and eval('self.inv.%s[0].points[pt].pdef.get("symbols")' % m) is not None:
                            symbol = eval('self.inv.%s[0].points[pt].pdef.get("symbols")' % m)
                            # self.ts.log('Symbols: %s' % symbol)
                            symb = None
                            if symbol is not None:
                                if isinstance(symbol, list):
                                    for s in symbol:
                                        # self.ts.log('s: %s' % s)
                                        if val == s.get('value'):
                                            symb = s.get("label")
                                else:
                                    if symbol.get(val) is not None:
                                        symb = eval('self.inv.%s[0].points[pt].pdef["symbols"][val]["label"]' % m)
                            self.ts.log('%s [%s]: %s [%s]' % (label, pt, val, symb))
                        else:
                            self.ts.log('%s [%s]: %s' % (label, pt, val))

                # Cycle through groups
                self.print_group(group_obj=eval('self.inv.%s[0]' % m))

    def print_group(self, group_obj, tab_level=2):
        """
        Print out groups. Method calls itself for groups of groups

        :param group_obj: group object, must be a dict
        :param tab_level: print indention

        :return: None
        """
        if isinstance(group_obj.groups, dict):
            for group in group_obj.groups.keys():
                if isinstance(group_obj.groups[group], list):  # list of groups within the group
                    for i in range(len(group_obj.groups[group])):
                        self.ts.log('\t' * (tab_level - 1) + '-' * 50)
                        self.ts.log('\t' * (tab_level-1) + 'Group: %s (#%d)' % (group, i+1))

                        for pt in group_obj.groups[group][i].points.keys():
                            # self.ts.log_debug('pt: %s' % pt)
                            if pt != 'Pad':
                                try:
                                    label = group_obj.groups[group][i].points[pt].pdef["label"]
                                except Exception as e:
                                    label = group_obj.groups[group][i].points[pt].pdef["name"]
                                val = group_obj.groups[group][i].points[pt].cvalue

                                # symbol prints
                                if val is not None and \
                                        group_obj.groups[group][i].points[pt].pdef.get("symbols") is not None:
                                    symbol = group_obj.groups[group][i].points[pt].pdef.get("symbols")
                                    symb = None
                                    if isinstance(symbol, list):
                                        for s in symbol:
                                            # self.ts.log('s: %s' % s)
                                            if val == s.get('value'):
                                                symb = s.get("label")
                                    else:
                                        if group_obj.symbol.get(val) is not None:
                                            symb = symbol[val]['label']
                                    self.ts.log('\t' * tab_level + '%s [%s]: %s [%s]' % (label, pt, val, symb))
                                else:
                                    self.ts.log('\t' * tab_level + '%s [%s]: %s' % (label, pt, val))

                        # For cases of groups of groups, call this function again
                        new_obj = group_obj.groups[group][i]
                        # self.ts.log_debug('New Obj = %s' % new_obj)
                        self.print_group(group_obj=new_obj, tab_level=tab_level+1)
                else:
                    self.ts.log('\t' * (tab_level - 1) + '-' * 50)
                    self.ts.log('\t' * (tab_level - 1) + 'Group: %s' % group)
                    for pt in group_obj.groups[group].points.keys():
                        # self.ts.log_debug('pt: %s' % pt)
                        if pt != 'Pad':
                            label = group_obj.groups[group].points[pt].pdef["label"]
                            val = group_obj.groups[group].points[pt].cvalue

                            # symbol prints
                            if val is not None and group_obj.groups[group].points[pt].pdef.get("symbols") is not None:
                                symbol = group_obj.groups[group].points[pt].pdef.get("symbols")
                                symb = None
                                if isinstance(symbol, list):
                                    for s in symbol:
                                        # self.ts.log('s: %s' % s)
                                        if val == s.get('value'):
                                            symb = s.get("label")
                                else:
                                    if group_obj.symbol.get(val) is not None:
                                        symb = symbol[val]['label']
                                self.ts.log('\t' * tab_level + '%s [%s]: %s [%s]' % (label, pt, val, symb))
                            else:
                                self.ts.log('\t' * tab_level + '%s [%s]: %s' % (label, pt, val))

                    # For cases of groups of groups, call this function again
                    new_obj = group_obj.groups[group]
                    # self.ts.log_debug('New Obj = %s' % new_obj)
                    self.print_group(group_obj=new_obj, tab_level=tab_level + 1)
        else:
            self.ts.log_warning('group_obj was not dict')

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

            (Only for DER with storage and absorbing power)
            Power Factor Enable (W Abs) Enable [PFWAbsEna]: 0
            Power Factor Reversion Enable (W Abs) [PFWAbsRvrtEna]: None
            PF Reversion Time (W Abs) [PFWAbsRvrtTms]: None
            PF Reversion Time Rem (W Abs) [PFWAbsRvrtRem]: None

                --------------------------------------------------
                Group: PFWInj
                Power Factor (W Inj)  [PF]: 0.9500000000000001
                Power Factor Excitation (W Inj) [Ext]: 1
                --------------------------------------------------
                Group: PFWInjRvrt
                Reversion Power Factor (W Inj)  [PF]: None
                Reversion PF Excitation (W Inj) [Ext]: None
                --------------------------------------------------
                Group: PFWAbs
                Power Factor (W Abs)  [PF]: None
                Power Factor Excitation (W Abs) [Ext]: None
                --------------------------------------------------
                Group: PFWAbsRvrt
                Reversion Power Factor (W Abs)  [PF]: None
                Reversion PF Excitation (W Abs) [Ext]: None

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

        if der_pts.PFWInj.PF.cvalue is not None:
            params['const_pf_inj_as'] = der_pts.PFWInj.PF.cvalue
        if der_pts.PFWInj.Ext.cvalue is not None:
            if der_pts.PFWInj.Ext.cvalue == 0:  # todo check sign convension
                params['const_pf_excitation_as'] = 'inj'  # Over-excited
            else:
                params['const_pf_excitation_as'] = 'abs'

        if der_pts.PFWAbs.PF.cvalue is not None:
            params['const_pf_abs_as'] = der_pts.PFWAbs.PF.cvalue
        if der_pts.PFWAbs.Ext.cvalue is not None:
            if der_pts.PFWAbs.Ext.cvalue == 0:  # todo check sign convension
                params['const_pf_excitation_as'] = 'inj'  # Over-excited
            else:
                params['const_pf_excitation_as'] = 'abs'

        return params

    def set_const_pf(self, params=None):
        """
        Set Constant Power Factor Mode control settings.
        """
        der_pts = self.inv.DERCtlAC[0]
        der_pts.read()

        if params.get('const_pf_mode_enable_as') is not None:
            if params.get('const_pf_mode_enable_as') is True:
                der_pts.PFWInjEna.cvalue = 1
            else:
                der_pts.PFWInjEna.cvalue = 0

        if params.get('const_pf_inj_as') is not None:
            der_pts.PFWInj.PF.cvalue = params.get('const_pf_inj_as')
        if params.get('const_pf_excitation_as') is not None:
            if params.get('const_pf_excitation_as') == 'inj':  # todo check sign convension
                der_pts.PFWInj.Ext.cvalue = 0  # Over-excited
            else:
                der_pts.PFWInj.Ext.cvalue = 1  # Under-excited

        if params.get('const_pf_abs_as') is not None:
            der_pts.PFWAbs.PF.cvalue = params.get('const_pf_abs_as')
        if params.get('const_pf_excitation_as') is not None:
            if params.get('const_pf_excitation_as') == 'inj':  # todo check sign convension
                der_pts.PFWAbs.Ext.cvalue = 0  # Over-excited
            else:
                der_pts.PFWAbs.Ext.cvalue = 1  # Under-excited
        der_pts.write()

    def get_qv(self, group=1):
        """
        :param group: the numerical value of the volt-var curve. The python index is one less.

        Get Q(V) parameters. [Volt-Var]
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Voltage-Reactive Power Mode Enable                          qv_mode_enable_as               bool (True=Enabled)
        Vref (0.95-1.05)                                            qv_vref_as                      V p.u.
        Autonomous Vref Adjustment Enable                           qv_vref_auto_mode_as            bool (True=Enabled)
        Vref adjustment time Constant (300-5000)                    qv_vref_olrt_as                 s
        Q(V) Curve Point V1-4 (list, e.g., [95, 99, 101, 105])      qv_curve_v_pts                  V p.u.
        Q(V) Curve Point Q1-4 (list)                                qv_curve_q_pts                  VAr p.u.
        Q(V) Open Loop Response Time Setting  (1-90)                qv_olrt_as                      s

        :return: dict with keys shown above.

        SunSpec Points
            Model ID [ID]: 705
            Model Length [L]: 64
            Module Enable [Ena]: 1 [Enabled]
            Active Curve State [CrvSt]: 1 [Active Curve Enabled]
            Adopt Curve Request [AdptCrvReq]: 0
            Adopt Curve Result [AdptCrvRslt]: 0 [Update In Progress]
            Number Of Points [NPt]: 4
            Stored Curve Count [NCrv]: 3
            Reversion Timeout [RvrtTms]: 0
            Reversion Time Remaining [RvrtRem]: 0
            Reversion Curve [RvrtCrv]: 0
            Voltage Scale Factor [V_SF]: -2
            Var Scale Factor [DeptRef_SF]: -2
                --------------------------------------------------
                Group: Crv (#1)
                    Active Points [ActPt]: 4
                    Dependent Reference [DeptRef]: 1 [Percent Max Watts]
                    Pri [Pri]: 1 [Active Power Priority]
                    Vref Adjustment [VRef]: 1
                    Current Autonomous Vref [VRefAuto]: 0
                    Autonomous Vref Enable [VRefAutoEna]: None
                    Auto Vref Time Constant [VRefTms]: 5
                    Open Loop Response Time [RspTms]: 6
                    Curve Access [ReadOnly]: 1 [Read-Only Access]
                    --------------------------------------------------
                    Group: Pt (#1)
                        Voltage Point [V]: 92.0
                        Reactive Power Point [Var]: 30.0
                    --------------------------------------------------
                    Group: Pt (#2)
                        Voltage Point [V]: 96.7
                        Reactive Power Point [Var]: 0.0
                    --------------------------------------------------
                    Group: Pt (#3)
                        Voltage Point [V]: 103.0
                        Reactive Power Point [Var]: 0.0
                    --------------------------------------------------
                    Group: Pt (#4)
                        Voltage Point [V]: 107.0
                        Reactive Power Point [Var]: -30.0
        """
        params = {}
        der_pts = self.inv.DERVoltVar[0]
        der_pts.read()
        group -= 1  # convert to the python index

        if der_pts.Ena.cvalue is not None:
            if der_pts.Ena.cvalue == 1:
                params['qv_mode_enable_as'] = True
            else:
                params['qv_mode_enable_as'] = False

        if der_pts.CrvSt.cvalue is not None:
            params['qv_active_curve'] = der_pts.CrvSt.cvalue
        if der_pts.NPt.cvalue is not None:
            params['qv_n_points'] = der_pts.NPt.cvalue
        if der_pts.NCrv.cvalue is not None:
            params['qv_n_curves'] = der_pts.NCrv.cvalue

        # curve points
        if der_pts.Crv[group].VRefAutoEna.cvalue is not None:
            if der_pts.Crv[group].VRefAutoEna.cvalue == 1:
                params['qv_vref_auto_mode_as'] = True
            else:
                params['qv_vref_auto_mode_as'] = False
        if der_pts.Crv[group].VRefTms.cvalue is not None:
            params['qv_vref_olrt_as'] = der_pts.Crv[group].VRefTms.cvalue
        if der_pts.Crv[group].ActPt.cvalue is not None:
            params['qv_curve_n_active_pts'] = der_pts.Crv[group].ActPt.cvalue
        else:
            params['qv_curve_n_active_pts'] = 4
        params['qv_curve_v_pts'] = []
        params['qv_curve_q_pts'] = []
        for i in range(params['qv_curve_n_active_pts']):
            params['qv_curve_v_pts'].append(der_pts.Crv[group].Pt[i].V.cvalue / 100.)  # pu
            params['qv_curve_q_pts'].append(der_pts.Crv[group].Pt[i].Var.cvalue / 100.)

        if der_pts.Crv[group].RspTms.cvalue is not None:
            params['qv_olrt_as'] = der_pts.Crv[group].RspTms.cvalue

        return params

    def set_qv(self, params=None, group=1):
        """
        Set Q(V) parameters. [Volt-Var]
        """
        der_pts = self.inv.DERVoltVar[0]
        der_pts.read()
        group -= 1  # convert to python index

        if params.get('qv_mode_enable_as') is not None:
            if params.get('qv_mode_enable_as') is True:
                der_pts.Ena.cvalue = 1
            else:
                der_pts.Ena.cvalue = 0

        der_pts.CrvSt.cvalue = group

        if params.get('qv_vref_auto_mode_as') is not None:
            if params['qv_vref_auto_mode_as']:
                der_pts.Crv[group].VRefAutoEna.cvalue = 1
            else:
                der_pts.Crv[group].VRefAutoEna.cvalue = 0

        # curve points
        if params.get('qv_vref_olrt_as') is not None:
            der_pts.Crv[group].VRefTms.cvalue = params['qv_vref_olrt_as']

        if params.get('qv_curve_v_pts') is not None:
            if params.get('qv_curve_q_pts') is None:
                raise der1547.DER1547Error('Volt-Var curves must be writen in pairs. No Q points provided.')
        if params.get('qv_curve_q_pts') is not None:
            if params.get('qv_curve_v_pts') is None:
                raise der1547.DER1547Error('Volt-Var curves must be writen in pairs. No V points provided')

        if params.get('qv_curve_v_pts') is not None:
            if len(params['qv_curve_v_pts']) != len(params['qv_curve_q_pts']):
                raise der1547.DER1547Error('V and Q lists are not the same lengths')
            if len(params['qv_curve_v_pts']) > der_pts.NPt.cvalue:
                raise der1547.DER1547Error('Volt-Var curves require more points than are supported.')

            if len(params['qv_curve_v_pts']) != der_pts.Crv[group].ActPt.cvalue:
                der_pts.Crv[group].ActPt.cvalue = len(params['qv_curve_v_pts'])

            for i in range(len(params['qv_curve_v_pts'])):
                der_pts.Crv[group].Pt[i].V.cvalue = params['qv_curve_v_pts'][i]*100.  # convert pu to %
                der_pts.Crv[group].Pt[i].Var.cvalue = params['qv_curve_q_pts'][i]*100.

        if params.get('qv_olrt_as') is not None:
            der_pts.Crv[group].RspTms.cvalue = params['qv_olrt_as']

        der_pts.write()

        return params

    def get_qp(self, group=1):
        """
        Get Q(P) parameters. [Watt-Var] - IEEE 1547 Table 32
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        Active Power-Reactive Power (Watt-VAr) Enable               qp_mode_enable_as                   bool
        P-Q curve P1-3 Generation Setting (list)                    qp_curve_p_gen_pts_as               P p.u.
        P-Q curve Q1-3 Generation Setting (list)                    qp_curve_q_gen_pts_as               VAr p.u.
        P-Q curve P1-3 Load Setting (list), negative values         qp_curve_p_load_pts_as              P p.u.
        P-Q curve Q1-3 Load Setting (list)                          qp_curve_q_load_pts_as              VAr p.u.
        QP Open Loop Response Time Setting                          qp_olrt_as                          s

        :return: dict with keys shown above.

        SunSpec Points
            Model ID [ID]: 712
            Model Length [L]: 19
            Module Enable [Ena]: None
            Active Curve State [CrvSt]: None
            Set Active Curve Request [AdptCrvReq]: None
            Set Active Curve Result [AdptCrvRslt]: None
            Number Of Points [NPt]: 1
            Stored Curve Count [NCrv]: 1
            Reversion Timeout [RvrtTms]: 0
            Reversion Time Left [RvrtRem]: 0
            Reversion Curve [RvrtCrv]: 0
            Active Power Scale Factor [W_SF]: None
            Var Scale Factor [DeptRef_SF]: -2
            --------------------------------------------------
            Group: Crv (#1)
                Active Points [ActPt]: 1
                Dependent Reference [DeptRef]: None
                Pri [Pri]: None
                Curve Access [ReadOnly]: None
                --------------------------------------------------
                Group: Pt (#1)
                    Active Power Point [W]: None
                    Reactive Power Point [Var]: None

        """
        params = {}
        der_pts = self.inv.DERWattVar[0]
        der_pts.read()
        group -= 1  # convert to the python index

        if der_pts.Ena.cvalue is not None:
            if der_pts.Ena.cvalue == 1:
                params['qp_mode_enable_as'] = True
            else:
                params['qp_mode_enable_as'] = False

        if der_pts.CrvSt.cvalue is not None:
            params['qp_active_curve'] = der_pts.CrvSt.cvalue
        if der_pts.NPt.cvalue is not None:
            params['qp_n_points'] = der_pts.NPt.cvalue
        if der_pts.NCrv.cvalue is not None:
            params['qp_n_curves'] = der_pts.NCrv.cvalue

        # curve points
        if der_pts.Crv[group].ActPt.cvalue is not None:
            params['qp_curve_n_active_pts'] = der_pts.Crv[group].ActPt.cvalue
        else:
            params['qp_curve_n_active_pts'] = 6
        params['qp_curve_p_gen_pts_as'] = []
        params['qp_curve_q_gen_pts_as'] = []
        params['qp_curve_p_load_pts_as'] = []
        params['qp_curve_q_load_pts_as'] = []
        for i in range(params['qp_curve_n_active_pts']):
            # self.ts.log_debug('%s, Pt: %s' % (i, der_pts.Crv[group].Pt[i]))
            if der_pts.Crv[group].Pt[i].W.cvalue is not None:
                p_pu = der_pts.Crv[group].Pt[i].W.cvalue / 100.
                q_pu = der_pts.Crv[group].Pt[i].Var.cvalue / 100.
                # self.ts.log_debug('P = %s, Q: %s' % (p_pu, q_pu))
                if p_pu < 0:
                    params['qp_curve_p_load_pts_as'].append(p_pu)  # pu
                    params['qp_curve_q_load_pts_as'].append(q_pu)
                else:
                    params['qp_curve_p_gen_pts_as'].append(p_pu)  # pu
                    params['qp_curve_q_gen_pts_as'].append(q_pu)

        params['qp_curve_p_load_pts_as'].reverse()  # place P'1 next to axis and P'3 toward -100% P pu
        params['qp_curve_q_load_pts_as'].reverse()

        # if der_pts.Crv[group].RspTms.cvalue is not None:
        #     params['qp_olrt_as'] = der_pts.Crv[group].RspTms.cvalue

        return params

    def set_qp(self, params=None, group=1):
        """
        Set Q(P) parameters. [Watt-Var]
        """
        der_pts = self.inv.DERWattVar[0]
        der_pts.read()
        group -= 1  # convert to python index

        if params.get('qp_mode_enable_as') is not None:
            if params.get('qp_mode_enable_as') is True:
                der_pts.Ena.cvalue = 1
            else:
                der_pts.Ena.cvalue = 0

        der_pts.CrvSt.cvalue = group

        if params.get('qp_curve_p_gen_pts_as') is not None:
            p_gen_points = params.get('qp_curve_p_gen_pts_as')
            if params.get('qp_curve_q_gen_pts_as') is None:
                raise der1547.DER1547Error('Watt-Var curves must be writen in pairs. No Qgen points provided.')
            if len(params['qp_curve_p_gen_pts_as']) != len(params['qp_curve_q_gen_pts_as']):
                raise der1547.DER1547Error('P and Q lists are not the same lengths')
        else:
            p_gen_points = self.get_qp().get('qp_curve_p_gen_pts_as')

        if params.get('qp_curve_q_gen_pts_as') is not None:
            q_gen_points = params.get('qp_curve_q_gen_pts_as')
            if params.get('qp_curve_p_gen_pts_as') is None:
                raise der1547.DER1547Error('Watt-Var curves must be writen in pairs. No Pgen points provided')
        else:
            q_gen_points = self.get_qp().get('qp_curve_q_gen_pts_as')

        if params.get('qp_curve_p_load_pts_as') is not None:
            p_load_points = params.get('qp_curve_p_load_pts_as')
            if params.get('qp_curve_q_load_pts_as') is None:
                raise der1547.DER1547Error('Watt-Var curves must be writen in pairs. No Qload points provided.')
            if len(params['qp_curve_p_load_pts_as']) != len(params['qp_curve_q_load_pts_as']):
                raise der1547.DER1547Error('P and Q lists are not the same lengths')
        else:
            p_load_points = self.get_qp().get('qp_curve_p_load_pts_as')
            # self.ts.log_debug('From read')

        if params.get('qp_curve_q_load_pts_as') is not None:
            q_load_points = params.get('qp_curve_q_load_pts_as')
            if params.get('qp_curve_p_load_pts_as') is None:
                raise der1547.DER1547Error('Watt-Var curves must be writen in pairs. No Pload points provided')
        else:
            q_load_points = self.get_qp().get('qp_curve_q_load_pts_as')

        points = len(p_gen_points) + len(p_load_points)
        if points > der_pts.NPt.cvalue:
            raise der1547.DER1547Error('Watt-Var curves require more points than are supported.')

        if params.get('qp_curve_p_gen_pts_as') is None and params.get('qp_curve_q_gen_pts_as') is None and \
            params.get('qp_curve_p_load_pts_as') is None and params.get('qp_curve_q_load_pts_as'):
            # do not write points, because none included in params
            return params
        else:
            if points != der_pts.Crv[group].ActPt.cvalue:
                der_pts.Crv[group].ActPt.cvalue = points
            der_pts.write()

            # reverse the load points so they align to the axis
            p_load_points.reverse()
            q_load_points.reverse()

            p_points = p_load_points + p_gen_points
            q_points = q_load_points + q_gen_points
            # self.ts.log_debug('p_points = %s, q_points: %s' % (p_points, q_points))
            for i in range(points):
                der_pts.Crv[group].Pt[i].W.cvalue = p_points[i]*100.  # convert pu to %
                der_pts.Crv[group].Pt[i].Var.cvalue = q_points[i]*100.

            # if params.get('qp_olrt_as') is not None:
            #     der_pts.Crv[group].RspTms.cvalue = params['qp_olrt_as']

            der_pts.write()

            return params

    def get_pv(self, group=1):
        """
        Get P(V), Voltage-Active Power (Volt-Watt), Parameters
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                         units
        ______________________________________________________________________________________________________________
        Voltage-Active Power Mode Enable                            pv_mode_enable_as                       bool
        P(V) Curve Point V1-2 Setting (list)                        pv_curve_v_pts_as                       V p.u.
        P(V) Curve Point P1-2 Setting (list)                        pv_curve_p_pts_as                       P p.u.
        P(V) Curve Point P1-P'2 Setting (list)                      pv_curve_p_bidrct_pts_as                P p.u.
        P(V) Open Loop Response time Setting (0.5-60)               pv_olrt_as                              s

        :return: dict with keys shown above.

        SunSpec Points
            Model ID [ID]: 706
            Model Length [L]: 29
            Module Enable [Ena]: 0 [Disabled]
            Active Curve State [CrvSt]: 1 [Active Curve Enabled]
            Adopt Curve Request [AdptCrvReq]: 0
            Adopt Curve Result [AdptCrvRslt]: 0 [Update In Progress]
            Number Of Points [NPt]: 2
            Stored Curve Count [NCrv]: 2
            Reversion Timeout [RvrtTms]: None
            Reversion Time Remaining [RvrtRem]: None
            Reversion Curve [RvrtCrv]: None
            Voltage Scale Factor [V_SF]: 0
            Watt  Scale Factor [DeptRef_SF]: 0
                --------------------------------------------------
                Group: Crv (#1)
                    Active Points [ActPt]: 2
                    Dependent Reference [DeptRef]: 1 [None]
                    Open Loop Response Time [RspTms]: 10
                    Curve Access [ReadOnly]: 1 [Read-Only Access]
                    --------------------------------------------------
                    Group: Pt (#1)
                        Voltage Point [V]: 106
                        Dependent Reference [W]: 100
                    --------------------------------------------------
                    Group: Pt (#2)
                        Voltage Point [V]: 110
                        Dependent Reference [W]: 0
        """
        params = {}
        der_pts = self.inv.DERVoltWatt[0]
        der_pts.read()
        group -= 1  # convert to the python index

        if der_pts.Ena.cvalue is not None:
            if der_pts.Ena.cvalue == 1:
                params['pv_mode_enable_as'] = True
            else:
                params['pv_mode_enable_as'] = False

        if der_pts.CrvSt.cvalue is not None:
            params['pv_active_curve'] = der_pts.CrvSt.cvalue
        if der_pts.NPt.cvalue is not None:
            params['pv_n_points'] = der_pts.NPt.cvalue
        if der_pts.NCrv.cvalue is not None:
            params['pv_n_curves'] = der_pts.NCrv.cvalue

        # curve points
        if der_pts.Crv[group].ActPt.cvalue is not None:
            params['pv_curve_n_active_pts'] = der_pts.Crv[group].ActPt.cvalue
        else:
            params['pv_curve_n_active_pts'] = None

        params['pv_curve_v_pts_as'] = []
        params['pv_curve_p_pts_as'] = []
        params['pv_curve_p_bidrct_pts_as'] = []
        for i in range(params['pv_curve_n_active_pts']):
            # self.ts.log_debug('%s, Pt: %s' % (i, der_pts.Crv[group].Pt[i]))
            if der_pts.Crv[group].Pt[i].W.cvalue is not None:
                v_pu = der_pts.Crv[group].Pt[i].V.cvalue / 100.
                p_pu = der_pts.Crv[group].Pt[i].W.cvalue / 100.
                # self.ts.log_debug('P = %s, Q: %s' % (p_pu, q_pu))
                if p_pu >= 0:
                    params['pv_curve_p_pts_as'].append(p_pu)  # pu
                    params['pv_curve_v_pts_as'].append(v_pu)
                else:
                    params['pv_curve_p_bidrct_pts_as'].append(p_pu)  # pu
                    params['pv_curve_v_pts_as'].append(v_pu)

        if der_pts.Crv[group].RspTms.cvalue is not None:
            params['pv_olrt_as'] = der_pts.Crv[group].RspTms.cvalue

        return params

    def set_pv(self, params=None, group=1):
        """
        Set P(V), Voltage-Active Power (Volt-Watt), Parameters
        """
        der_pts = self.inv.DERVoltWatt[0]
        der_pts.read()
        group -= 1  # convert to python index

        if params.get('pv_mode_enable_as') is not None:
            if params.get('pv_mode_enable_as') is True:
                der_pts.Ena.cvalue = 1
            else:
                der_pts.Ena.cvalue = 0

        der_pts.CrvSt.cvalue = group

        v_pts = params.get('pv_curve_v_pts_as')
        p_pts = params.get('pv_curve_p_pts_as')
        p_prime_pts = params.get('pv_curve_p_bidrct_pts_as')
        points = None
        if p_pts is not None:
            if p_prime_pts is not None:
                p_pts += p_prime_pts  # only add p' is p points exist

        if v_pts is not None:
            if p_pts is None:
                raise der1547.DER1547Error('Volt-Watt curves must be writen in pairs. No P points provided.')
            if len(v_pts) != len(p_pts):
                raise der1547.DER1547Error('P and Q lists are not the same lengths')
        if p_pts is not None:
            points = len(p_pts)
            if v_pts is None:
                raise der1547.DER1547Error('Volt-Watt curves must be writen in pairs. No Pgen points provided')

        if points is not None:
            if points > der_pts.NPt.cvalue:
                raise der1547.DER1547Error('Volt-Watt curves require more points than are supported.')

            if points != der_pts.Crv[group].ActPt.cvalue:
                der_pts.Crv[group].ActPt.cvalue = points

            for i in range(points):
                der_pts.Crv[group].Pt[i].V.cvalue = v_pts[i] * 100.  # convert pu to %
                der_pts.Crv[group].Pt[i].W.cvalue = p_pts[i] * 100.  # convert pu to %

        if params.get('pv_olrt_as') is not None:
            der_pts.Crv[group].RspTms.cvalue = params['pv_olrt_as']

        der_pts.write()

        return params

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
            # der_pts.VarSetPri.cvalue = 'Reactive Power Priority'

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

        der_pts.write()

        return params

    def get_pf(self, group=1):
        """
        Get P(f), Frequency-Active Power Mode Parameters - IEEE 1547 Table 38
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          pf_mode_enable_as               bool (True=Enabled)
        P(f) Overfrequency Droop dbOF Setting                       pf_dbof_as                      Hz
        P(f) Underfrequency Droop dbUF Setting                      pf_dbuf_as                      Hz
        P(f) Overfrequency Droop kOF  Setting                       pf_kof_as                       unitless
        P(f) Underfrequency Droop kUF Setting                       pf_kuf_as                       unitless
        P(f) Open Loop Response Time Setting                        pf_olrt_as                      s

        :return: dict with keys shown above.

        SunSpec Points
            DER Frequency Droop ID [ID]: 711
            DER Frequency Droop Length [L]: 19
            DER Frequency-Watt (Frequency-Droop) Module Enable. [Ena]: None
            Active Curve State [CrvSt]: None
            Set Active Control Request [AdptCtlReq]: None
            Set Active Control Result [AdptCtlRslt]: None
            Stored Curve Count [NCtl]: 1
            Reversion Timeout [RvrtTms]: 0
            Reversion Time Left [RvrtRem]: 0
            Reversion Control [RvrtCtl]: None
            Deadband Scale Factor [Db_SF]: -2
            Frequency Change Scale Factor [K_SF]: -2
            Open-Loop Scale Factor [RspTms_SF]: 0
                --------------------------------------------------
                Group: Ctl (#1)
                    Over-Frequency Deadband [DbOf]: 600.3000000000001
                    Under-Frequency Deadband [DbUf]: 599.7
                    Over-Frequency Change Ratio [KOf]: 0.4
                    Under-Frequency Change Ratio [KUf]: 0.4
                    Open-Loop Response Time [RspTms]: 600
                    Control Access [ReadOnly]: None

        """
        params = {}
        der_pts = self.inv.DERFreqDroop[0]
        der_pts.read()
        group -= 1  # convert to the python index

        if der_pts.Ena.cvalue is not None:
            if der_pts.Ena.cvalue == 1:
                params['pf_mode_enable_as'] = True
            else:
                params['pf_mode_enable_as'] = False

        if der_pts.CrvSt.cvalue is not None:
            params['pf_active_curve'] = der_pts.CrvSt.cvalue
        if der_pts.NCtl.cvalue is not None:
            params['pf_n_curves'] = der_pts.NCtl.cvalue

        if der_pts.Ctl[group].DbOf.cvalue is not None:
            params['pf_dbof_as'] = der_pts.Ctl[group].DbOf.cvalue
        if der_pts.Ctl[group].DbUf.cvalue is not None:
            params['pf_dbuf_as'] = der_pts.Ctl[group].DbUf.cvalue
        if der_pts.Ctl[group].KOf.cvalue is not None:
            params['pf_kof_as'] = der_pts.Ctl[group].KOf.cvalue
        if der_pts.Ctl[group].KUf.cvalue is not None:
            params['pf_kuf_as'] = der_pts.Ctl[group].KUf.cvalue
        if der_pts.Ctl[group].RspTms.cvalue is not None:
            params['pf_olrt_as'] = der_pts.Ctl[group].RspTms.cvalue

        return params

    def set_pf(self, params=None, group=1):
        """
        Set P(f), Frequency-Active Power Mode Parameters
        """
        der_pts = self.inv.DERFreqDroop[0]
        der_pts.read()
        group -= 1  # convert to the python index

        if params.get('pf_mode_enable_as') is not None:
            if params.get('pf_mode_enable_as'):
                der_pts.Ena.cvalue = 1
            else:
                der_pts.Ena.cvalue = 0

        der_pts.CrvSt.cvalue = group

        if params.get('pf_dbof_as') is not None:
            der_pts.Ctl[group].DbOf.cvalue = params.get('pf_dbof_as')
        if params.get('pf_dbuf_as') is not None:
            der_pts.Ctl[group].DbUf.cvalue = params.get('pf_dbuf_as')
        if params.get('pf_kof_as') is not None:
            der_pts.Ctl[group].KOf.cvalue = params.get('pf_kof_as')
        if params.get('pf_kuf_as') is not None:
            der_pts.Ctl[group].KUf.cvalue = params.get('pf_kuf_as')
        if params.get('pf_olrt_as') is not None:
            der_pts.Ctl[group].RspTms.cvalue = params.get('pf_olrt_as')

        der_pts.write()

        return params

    def get_es_permit_service(self):
        """
        Get Permit Service Mode Parameters - IEEE 1547 Table 39
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                 units
        ______________________________________________________________________________________________________________
        Permit service                                          es_permit_service_as            bool (True=Enabled)
        ES Voltage Low Setting                                  es_v_low_as                     V p.u.
        ES Voltage High Setting                                 es_v_high_as                    V p.u.
        ES Frequency Low Setting                                es_f_low_as                     Hz
        ES Frequency High Setting                               es_f_high_as                    Hz
        ES Randomized Delay                                     es_randomized_delay_as          bool (True=Enabled)
        ES Delay Setting                                        es_delay_as                     s
        ES Ramp Rate Setting                                    es_ramp_rate_as                 %/s

        :return: dict with keys shown above.

        SunSpec Points
            Enter Service ID [ID]: 703
            Enter Service Length [L]: 12
            Permit Enter Service [ES]: 1 [None]
            Enter Service Voltage High [ESVHi]: 1.05
            Enter Service Voltage Low [ESVLo]: 0.917
            Enter Service Frequency High [ESHzHi]: 60.1
            Enter Service Frequency Low [ESHzLo]: 59.5
            Enter Service Delay Time [ESDlyTms]: 300
            Enter Service Random Delay [ESRndTms]: 100
            Enter Service Ramp Time [ESRmpTms]: 60
            Voltage Scale Factor [V_SF]: -3
            Frequency Scale Factor [Hz_SF]: -2

        """
        params = {}
        der_pts = self.inv.DEREnterService[0]
        der_pts.read()

        if der_pts.ES.cvalue is not None:
            if der_pts.ES.cvalue == 1:
                params['es_permit_service_as'] = True
            else:
                params['es_permit_service_as'] = False

        if der_pts.ESVLo.cvalue is not None:
            params['es_v_low_as'] = der_pts.ESVLo.cvalue
        if der_pts.ESVHi.cvalue is not None:
            params['es_v_high_as'] = der_pts.ESVHi.cvalue

        if der_pts.ESHzLo.cvalue is not None:
            params['es_f_low_as'] = der_pts.ESHzLo.cvalue
        if der_pts.ESHzHi.cvalue is not None:
            params['es_f_high_as'] = der_pts.ESHzHi.cvalue

        if der_pts.ESRndTms.cvalue is not None:
            params['es_randomized_delay_as'] = der_pts.ESRndTms.cvalue
        if der_pts.ESDlyTms.cvalue is not None:
            params['es_delay_as'] = der_pts.ESDlyTms.cvalue
        if der_pts.ESRmpTms.cvalue is not None:
            params['es_ramp_rate_as'] = der_pts.ESRmpTms.cvalue

        return params

    def set_es_permit_service(self, params=None):
        """
        Set Permit Service Mode Parameters
        """
        der_pts = self.inv.DEREnterService[0]
        der_pts.read()

        if params.get('es_permit_service_as') is not None:
            if params.get('es_permit_service_as'):
                der_pts.ES.cvalue = 1
            else:
                der_pts.ES.cvalue = 0

        if params['es_v_low_as'] is not None:
            der_pts.ESVLo.cvalueparams = ['es_v_low_as']
        if params['es_v_high_as'] is not None:
            der_pts.ESVHi.cvalue = params['es_v_high_as']

        if params['es_f_low_as'] is not None:
            der_pts.ESHzLo.cvalue = params['es_f_low_as']
        if params['es_f_high_as'] is not None:
            der_pts.ESHzHi.cvalue = params['es_f_high_as']

        if params['es_randomized_delay_as'] is not None:
            der_pts.ESRndTms.cvalue = params['es_randomized_delay_as']
        if params['es_delay_as'] is not None:
            der_pts.ESDlyTms.cvalue = params['es_delay_as']
        if params['es_ramp_rate_as'] is not None:
            der_pts.ESRmpTms.cvalue = params['es_ramp_rate_as']

        der_pts.write()

        return params

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
        pass

    def get_any_ride_thru_trip_or_mc(self, der_pts=None, group=1, curve_type=None):
        """
        A catch-all function for ride-through curves, trip curves, and momentary cessation

        :param der_pts: the object of the DER that will be written, e.g., self.inv.DERTripLV
        :param group: the top level curve group
        :param curve_type: str 'MustTrip', 'MayTrip', or 'MomCess'
        :return: params dict

        Example SunSpec Points
            DER Trip LV Model ID [ID]: 707
            DER Trip LV Model Length [L]: 18
            DER Trip LV Module Enable [Ena]: 1 [Enabled]
            Active Curve State [CrvSt]: None
            Adopt Curve Request [AdptCrvReq]: None
            Adopt Curve Result [AdptCrvRslt]: None
            Number Of Points [NPt]: 1
            Stored Curve Count [NCrvSet]: 1
            Voltage Scale Factor [V_SF]: -2
            Time Point Scale Factor [Tms_SF]: 0
                --------------------------------------------------
                Group: Crv (#1)
                    Curve Access [ReadOnly]: None
                    --------------------------------------------------
                    Group: MustTrip
                        Number Of Active Points [ActPt]: 1
                        --------------------------------------------------
                        Group: Pt (#1)
                            Voltage Point [V]: 50.0
                            Time Point [Tms]: 5
                    --------------------------------------------------
                    Group: MayTrip
                        Number Of Active Points [ActPt]: 1
                        --------------------------------------------------
                        Group: Pt (#1)
                            Voltage Point [V]: 70.0
                            Time Point [Tms]: 5
                    --------------------------------------------------
                    Group: MomCess
                        Number Of Active Points [ActPt]: 1
                        --------------------------------------------------
                        Group: Pt (#1)
                            Voltage Point [V]: 60.0
                            Time Point [Tms]: 5

        """
        der_pts.read()
        group -= 1  # convert to the python index

        params = {}
        if der_pts.Ena.cvalue is not None:
            if der_pts.Ena.cvalue == 1:
                params['Ena'] = True
            else:
                params['Ena'] = False

        if der_pts.CrvSt.cvalue is not None:
            params['CrvSt'] = der_pts.CrvSt.cvalue
        else:
            params['CrvSt'] = None

        if der_pts.AdptCrvReq.cvalue is not None:
            params['AdptCrvReq'] = der_pts.AdptCrvReq.cvalue
        else:
            params['AdptCrvReq'] = None

        if der_pts.AdptCrvRslt.cvalue is not None:
            params['AdptCrvRslt'] = der_pts.AdptCrvRslt.cvalue
        else:
            params['AdptCrvRslt'] = None

        if der_pts.NPt.cvalue is not None:
            params['NPt'] = der_pts.NPt.cvalue
        else:
            params['NPt'] = None

        if der_pts.NCrvSet.cvalue is not None:
            params['NCrvSet'] = der_pts.NCrvSet.cvalue
        else:
            params['NCrvSet'] = None

        if der_pts.NCrvSet.cvalue is not None:
            params['NCrvSet'] = der_pts.NCrvSet.cvalue
        else:
            params['NCrvSet'] = None

        if curve_type == 'MustTrip':
            if not isinstance(der_pts.Crv[group].MustTrip, list):
                curve = der_pts.Crv[group].MustTrip
            else:
                curve = der_pts.Crv[group].MustTrip[0]  # assume first curve
        elif curve_type == 'MayTrip':
            if not isinstance(der_pts.Crv[group].MayTrip, list):
                curve = der_pts.Crv[group].MayTrip
            else:
                curve = der_pts.Crv[group].MayTrip[0]  # assume first curve
        elif curve_type == 'MomCess':
            if not isinstance(der_pts.Crv[group].MomCess, list):
                curve = der_pts.Crv[group].MomCess
            else:
                curve = der_pts.Crv[group].MomCess[0]  # assume first curve
        else:
            raise der1547.DER1547Error('Incorrect curve_type string in get_any_ride_thru_trip_or_mc')

        if curve.ActPt.cvalue is not None:
            params['ActPt'] = curve.ActPt.cvalue
        else:
            params['ActPt'] = 0

        params['T'] = []
        params['V'] = []
        params['F'] = []

        for i in range(params['ActPt']):
            params['T'].append(curve.Pt[i].Tms.cvalue)
            try:
                params['V'].append(curve.Pt[i].V.cvalue)
            except Exception as e:
                pass  # not a voltage curve
            try:
                params['F'].append(curve.Pt[i].Freq.cvalue)
            except Exception as e:
                pass  # not a freq curve

        return params

    def set_any_ride_thru_trip_or_mc(self, params=None, der_pts=None, group=1, curve_type=None):
        """
        A catch-all function for ride-through curves, trip curves, and momentary cessation

        :param params: dict of points to write to SunSpec device
        :param der_pts: the object of the DER that will be written, e.g., self.inv.DERTripLV
        :param group: the top level curve group
        :param curve_type: str 'MustTrip', 'MayTrip', or 'MomCess'
        :return: params dict

        """
        der_pts.read()
        group -= 1  # convert to the python index

        if params.get('Ena') is not None:
            if params['Ena']:
                der_pts.Ena.cvalue = 1
            else:
                der_pts.Ena.cvalue = 0

        if params.get('CrvSt') is not None:
             der_pts.CrvSt.cvalue = params['CrvSt']
        if params.get('AdptCrvReq') is not None:
             der_pts.AdptCrvReq.cvalue = params['AdptCrvReq']
        if params.get('AdptCrvRslt') is not None:
             der_pts.AdptCrvRslt.cvalue = params['AdptCrvRslt']
        if params.get('NPt') is not None:
             der_pts.NPt.cvalue = params['NPt']
        if params.get('NCrvSet') is not None:
             der_pts.NCrvSet.cvalue = params['NCrvSet']

        if curve_type == 'MustTrip':
            if not isinstance(der_pts.Crv[group].MustTrip, list):
                curve = der_pts.Crv[group].MustTrip
            else:
                curve = der_pts.Crv[group].MustTrip[0]  # assume first curve
        elif curve_type == 'MayTrip':
            if not isinstance(der_pts.Crv[group].MayTrip, list):
                curve = der_pts.Crv[group].MayTrip
            else:
                curve = der_pts.Crv[group].MayTrip[0]  # assume first curve
        elif curve_type == 'MomCess':
            if not isinstance(der_pts.Crv[group].MomCess, list):
                curve = der_pts.Crv[group].MomCess
            else:
                curve = der_pts.Crv[group].MomCess[0]  # assume first curve
        else:
            raise der1547.DER1547Error('Incorrect curve_type string in get_any_ride_thru_trip_or_mc')

        if params.get('T') is not None:
            if len(params.get('T')) > der_pts.NPt.cvalue:
                raise der1547.DER1547Error('Number of points is larger than NPt')
            if curve.ActPt.cvalue > der_pts.NPt.cvalue:
                raise der1547.DER1547Error('ActPt is larger than NPt')
            curve.ActPt.cvalue = len(params['T'])
            # self.ts.log_debug('params[T]: %s' % params['T'])

            for i in range(len(params['T'])):
                # self.ts.log_debug('params[T][i]: %s' % params['T'][i])
                curve.Pt[i].Tms.cvalue = params['T'][i]
                if params.get('V') is not None:
                    # self.ts.log_debug('params[V][i]: %s' % params['V'][i])
                    curve.Pt[i].V.cvalue = params['V'][i]
                if params.get('F') is not None:
                    # self.ts.log_debug('params[F]: %s' % params['F'])
                    curve.Pt[i].Freq.cvalue = params['F'][i]

        der_pts.write()

        return params

    def get_ov(self, params=None):
        """
        Get Overvoltage Trip Parameters - IEEE 1547 Table 35
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        HV Trip Curve Point OV_V1-3 Setting                         ov_trip_v_pts_as                    V p.u.
        HV Trip Curve Point OV_T1-3 Setting                         ov_trip_t_pts_as                    s

        :return: dict with keys shown above.
        """
        suns_dict = self.get_any_ride_thru_trip_or_mc(der_pts=self.inv.DERTripHV[0], group=1, curve_type='MustTrip')
        params = {'ov_trip_v_pts_as': [v / 100. for v in suns_dict['V']], 'ov_trip_t_pts_as': suns_dict['T']}
        return params

    def set_ov(self, params=None):
        """
        Set Overvoltage Trip Parameters - IEEE 1547 Table 35
        """
        suns_dict = {}
        if params.get('ov_trip_v_pts_as') is not None:
            suns_dict['V'] = [v * 100. for v in params.get('ov_trip_v_pts_as')]
            if sorted(suns_dict['V']) != suns_dict['V']:
                raise der1547.DER1547Error('Voltage points are not increasing')
        if params.get('ov_trip_t_pts_as') is not None:
            suns_dict['T'] = params.get('ov_trip_t_pts_as')

        self.set_any_ride_thru_trip_or_mc(params=suns_dict, der_pts=self.inv.DERTripHV[0], group=1, curve_type='MustTrip')

        return params

    def get_uv(self, params=None):
        """
        Get Overvoltage Trip Parameters - IEEE 1547 Table 35
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        LV Trip Curve Point UV_V1-3 Setting                         uv_trip_v_pts_as                    V p.u.
        LV Trip Curve Point UV_T1-3 Setting                         uv_trip_t_pts_as                    s

        :return: dict with keys shown above.
        """
        suns_dict = self.get_any_ride_thru_trip_or_mc(der_pts=self.inv.DERTripLV[0], group=1, curve_type='MustTrip')
        params= {'uv_trip_v_pts_as': [v / 100. for v in suns_dict['V']], 'uv_trip_t_pts_as': suns_dict['T']}
        return params

    def set_uv(self, params=None):
        """
        Set Undervoltage Trip Parameters - IEEE 1547 Table 35
        """
        suns_dict = {}
        if params.get('uv_trip_v_pts_as') is not None:
            suns_dict['V'] = [v * 100. for v in params.get('uv_trip_v_pts_as')]
            if sorted(reversed(suns_dict['V'])) != list(reversed(suns_dict['V'])):
                raise der1547.DER1547Error('Voltage points are not decreasing')
        if params.get('uv_trip_t_pts_as') is not None:
            suns_dict['T'] = params.get('uv_trip_t_pts_as')

        self.set_any_ride_thru_trip_or_mc(params=suns_dict, der_pts=self.inv.DERTripLV[0], group=1, curve_type='MustTrip')

        return params

    def get_of(self, params=None):
        """
        Get Overfrequency Trip Parameters - IEEE 1547 Table 37
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        OF Trip Curve Point OF_F1-3 Setting                         of_trip_f_pts_as                    Hz
        OF Trip Curve Point OF_T1-3 Setting                         of_trip_t_pts_as                    s

        :return: dict with keys shown above.
        """
        suns_dict = self.get_any_ride_thru_trip_or_mc(der_pts=self.inv.DERTripHF[0], group=1, curve_type='MustTrip')
        params= {'of_trip_f_pts_as': suns_dict['F'], 'of_trip_t_pts_as': suns_dict['T']}
        return params

    def set_of(self, params=None):
        """
        Set Overfrequency Trip Parameters - IEEE 1547 Table 37
        """
        suns_dict = {}
        if params.get('of_trip_f_pts_as') is not None:
            suns_dict['F'] = params.get('of_trip_f_pts_as')
            if sorted(suns_dict['F']) != suns_dict['F']:
                raise der1547.DER1547Error('Freq points are not decreasing')
        if params.get('of_trip_t_pts_as') is not None:
            suns_dict['T'] = params.get('of_trip_t_pts_as')

        self.set_any_ride_thru_trip_or_mc(params=suns_dict, der_pts=self.inv.DERTripHF[0], group=1, curve_type='MustTrip')

        return params

    def get_uf(self, params=None):
        """
        Get Underfrequency Trip Parameters - IEEE 1547 Table 37
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        UF Trip Curve Point UF_F1-3 Setting                         uf_trip_f_pts_as                    Hz
        UF Trip Curve Point UF_T1-3 Setting                         uf_trip_t_pts_as                    s

        :return: dict with keys shown above.
        """
        suns_dict = self.get_any_ride_thru_trip_or_mc(der_pts=self.inv.DERTripLF[0], group=1, curve_type='MustTrip')
        params= {'uf_trip_f_pts_as': suns_dict['F'], 'uf_trip_t_pts_as': suns_dict['T']}
        return params

    def set_uf(self, params=None):
        """
        Set Underfrequency Trip Parameters - IEEE 1547 Table 37
        """
        suns_dict = {}
        if params.get('uf_trip_f_pts_as') is not None:
            suns_dict['F'] = params.get('uf_trip_f_pts_as')
            if sorted(reversed(suns_dict['F'])) != list(reversed(suns_dict['F'])):
                raise der1547.DER1547Error('Freq points are not decreasing')
        if params.get('uf_trip_t_pts_as') is not None:
            suns_dict['T'] = params.get('uf_trip_t_pts_as')

        self.set_any_ride_thru_trip_or_mc(params=suns_dict, der_pts=self.inv.DERTripLF[0], group=1,
                                          curve_type='MustTrip')

        return params

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
        suns_dict = self.get_any_ride_thru_trip_or_mc(der_pts=self.inv.DERTripHV[0], group=1, curve_type='MomCess')
        params = {'ov_mc_v_pts_as': [v / 100. for v in suns_dict['V']], 'ov_mc_t_pts_as': suns_dict['T']}
        return params

    def set_ov_mc(self, params=None):
        """
        Set Overvoltage Momentary Cessation (MC) Parameters - IEEE 1547 Table 36
        """
        suns_dict = {}
        if params.get('ov_mc_v_pts_as') is not None:
            suns_dict['V'] = [v * 100. for v in params.get('ov_mc_v_pts_as')]
            if sorted(suns_dict['V']) != suns_dict['V']:
                raise der1547.DER1547Error('Voltage points are not increasing')
        if params.get('ov_mc_t_pts_as') is not None:
            suns_dict['T'] = params.get('ov_mc_t_pts_as')

        self.set_any_ride_thru_trip_or_mc(params=suns_dict, der_pts=self.inv.DERTripHV[0], group=1,
                                          curve_type='MomCess')

        return params

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
        suns_dict = self.get_any_ride_thru_trip_or_mc(der_pts=self.inv.DERTripHV[0], group=1, curve_type='MomCess')
        params = {'uv_mc_v_pts_as': [v / 100. for v in suns_dict['V']], 'uv_mc_t_pts_as': suns_dict['T']}
        return params

    def set_uv_mc(self, params=None):
        """
        Set Undervoltage Momentary Cessation (MC) Parameters - IEEE 1547 Table 36
        """
        suns_dict = {}
        if params.get('uv_mc_v_pts_as') is not None:
            suns_dict['V'] = [v * 100. for v in params.get('uv_mc_v_pts_as')]
            if sorted(reversed(suns_dict['V'])) != list(reversed(suns_dict['V'])):
                raise der1547.DER1547Error('Voltage points are not decreasing')
        if params.get('uv_mc_t_pts_as') is not None:
            suns_dict['T'] = params.get('uv_mc_t_pts_as')

        self.set_any_ride_thru_trip_or_mc(params=suns_dict, der_pts=self.inv.DERTripLV[0], group=1,
                                          curve_type='MomCess')

        return params

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

