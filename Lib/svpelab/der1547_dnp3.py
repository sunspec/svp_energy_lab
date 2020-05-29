'''
DER1547 methods defined for the DNP3 devices
'''

import os
import der1547
import svpdnp3.device_der_dnp3 as dnp3_agent
import subprocess
import socket

dnp3_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'DNP3'
}


def der1547_info():
    return dnp3_info


def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = dnp3_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'), active_value=mode, glob=True)
    info.param(pname('ipaddr'), label='Agent IP Address', default='127.0.0.1')
    info.param(pname('ipport'), label='Agent IP Port', default=10000)
    info.param(pname('out_ipaddr'), label='Outstation IP Address', default='127.0.0.1')
    info.param(pname('out_ipport'), label='Outstation IP Port', default=20000)
    info.param(pname('outstation_addr'), label='Outstation Local Address', default=100)
    info.param(pname('master_addr'), label='Master Local Address', default=101)
    info.param(pname('oid'), label='OID', default=1)
    info.param(pname('rid'), label='Request ID', default=1234)


GROUP_NAME = 'dnp3'


class DER1547(der1547.DER1547):

    def __init__(self, ts, group_name):
        der1547.DER1547.__init__(self, ts, group_name)
        self.outstation = None
        self.ipaddr = self.param_value('ipaddr')
        self.ipport = self.param_value('ipport')
        self.out_ipaddr = self.param_value('out_ipaddr')
        self.out_ipport = self.param_value('out_ipport')
        self.outstation_addr = self.param_value('outstation_addr')
        self.master_addr = self.param_value('master_addr')
        self.oid = self.param_value('oid')
        self.rid = self.param_value('rid')

    def param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):
        self.start_agent()
        self.ts.sleep(6)
        self.ts.log('Adding outstation: %s' % self.add_out())
        self.ts.log('DNP3 Agent Status: %s' % self.status())

    def add_out(self):
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        outstation = agent.add_outstation(self.out_ipaddr, self.out_ipport, self.outstation_addr, self.master_addr)
        return outstation

    def del_out(self):
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        outstation = agent.delete_outstation(self.oid, self.rid)
        return outstation

    def status(self):
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        try:
            agent.connect(self.ipaddr, self.ipport)
        except Exception, e:
            self.ts.log_warning('Agent Status Error: %s' % e)
            return 'No Agent'
        agent_stat = agent.status(self.rid)
        res = eval(agent_stat[1:-1])
        return res

    def scan(self, scan_type):
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        agent_scan = agent.scan_outstation(self.oid, self.rid, scan_type)
        res = eval(agent_scan[1:-1])
        return res

    def start_agent(self):
        """
        Starts the DNP3 agent in a subprocess.  This agent acts as middleman between SVP and the DNP3 outstation.

        :return: None
        """
        running = True

        try:
            agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
            agent.connect(self.ipaddr, self.ipport)
            status = eval(agent.status(self.rid)[1:-1])

            if status == 'ERROR':
                self.ts.log_warning('Unable to start the agent. Another process may be running at the configured '
                        'IP address and port')

        except socket.error as e:
            running = False

        if not running:
            file_path = os.path.abspath(__file__ + '\\..\\..\\svpdnp3\\dnp3_agent.exe')
            self.ts.log_debug('file_path: %s' % file_path)
            in_new_window = True
            if in_new_window:
                win_command = file_path + ' -ip ' + self.ipaddr + ' -p ' + str(self.ipport)
                # self.ts.log_debug('win_command: %s' % win_command)
                subprocess.Popen(win_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:  # hidden process
                args = [file_path, '-ip', self.ipaddr, '-p', str(self.ipport)]
                subprocess.Popen(args)

        else:
            self.ts.log_error("The system doesn't support this agent")

    def stop_agent(self):
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        agent_end = agent.stop_agent(self.rid)
        os.system('taskkill /F /IM dnp3_agent.exe')
        return agent_end

    def info(self):
        return 'DNP3 der1547 instantiation.'

    def get_nameplate(self):
        '''
        This information is indicative of the as-built characteristics of the DER.
        This information may be read
        '''
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        nameplate_pts = nameplate_data.copy()
        nameplate_sprt_pts = nameplate_support.copy()

        points = {'ai': {}, 'bi': {}}
        false = False  # Don't remove - required for eval of read_outstation data
        true = True  # Don't remove - required for eval of read_outstation data
        null = None   # Don't remove - required for eval of read_outstation data
        for key, values in nameplate_pts.items():
            key1 = list(values.keys())  # (ai and np_support...)
            val1 = list(values.values())  # (points for ai and '{'bi': {'31': None}}' for bi)
            for i in val1:
                key2 = list(i.keys())  # (index for ai points and 'bi' for rest)
                val2 = list(i.values())
                for x in key1:
                    for y in key2:
                        if x == 'ai':
                            points['ai'][y] = None

        for key, values in nameplate_sprt_pts.items():
            keys1 = list(values.keys())  # (ai and np_support...)
            val = list(values.values())  # (points for ai and '{'bi': {'31': None}}' for bi)
            for i in val:
                keys2 = list(i.keys())  # (index for ai points and 'bi' for rest)
                val2 = list(i.values())
                for x in keys1:
                    for y in keys2:
                        if x == 'bi':
                            points['bi'][y] = None

        # self.ts.log_debug('self.status(): %s' % self.status())
        # self.ts.log_debug('self.oid=%s, self.rid=%s, points=%s' % (self.oid, self.rid, points))
        nameplate_read = agent.read_outstation(self.oid, self.rid, points)
        # self.ts.log_debug('nameplate_read %s' % nameplate_read)

        res = eval(nameplate_read[1:-1])
        if 'params' in res.keys():
            resp = res['params']
            nameplate_pts['np_active_power_rtg'] = resp['ai']['4']['value']
            nameplate_pts['np_active_power_rtg_over_excited'] = resp['ai']['6']['value']
            nameplate_pts['np_over_excited_pf'] = resp['ai']['8']['value']
            nameplate_pts['np_active_power_rtg_under_excited'] = resp['ai']['9']['value']
            nameplate_pts['np_under_excited_pf'] = resp['ai']['11']['value']
            nameplate_pts['np_apparent_power_max_rtg'] = resp['ai']['14']['value']
            nameplate_pts['np_normal_op_category'] = resp['ai']['22']['value']
            nameplate_pts['np_abnormal_op_category'] = resp['ai']['23']['value']
            nameplate_pts['np_reactive_power_inj_max_rtg'] = resp['ai']['12']['value']
            nameplate_pts['np_reactive_power_abs_max_rtg'] = resp['ai']['13']['value']
            nameplate_pts['np_active_power_chg_max_rtg'] = resp['ai']['5']['value']
            nameplate_pts['np_apparent_power_chg_max_rtg'] = resp['ai']['15']['value']
            nameplate_pts['np_ac_volt_nom_rtg'] = resp['ai']['29']['value']
            nameplate_pts['np_ac_volt_min_rtg'] = resp['ai']['2']['value']
            nameplate_pts['np_ac_volt_max_rtg'] = resp['ai']['3']['value']
            nameplate_pts['np_reactive_susceptance'] = resp['ai']['21']['value']
            nameplate_pts['np_supported_ctrl_mode_func'] = {}
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_volt_ride_through'] = resp['bi']['31']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_freq_ride_through'] = resp['bi']['32']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_dynamic_reactive_current'] = resp['bi']['33']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_dynamic_volt_watt'] = resp['bi']['34']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_freq_watt'] = resp['bi']['35']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_limit_watt'] = resp['bi']['36']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_chg_dischg'] = resp['bi']['37']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_coordinated_chg_dischg'] = resp['bi']['38']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_active_pwr_response_1'] = resp['bi']['39']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_active_pwr_response_2'] = resp['bi']['40']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_active_pwr_response_3'] = resp['bi']['41']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_automation_generation_control'] = resp['bi']['42']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_active_pwr_smoothing'] = resp['bi']['43']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_volt_watt'] = resp['bi']['44']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_freq_watt_curve'] = resp['bi']['45']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_constant_vars'] = resp['bi']['46']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_fixed_pf'] = resp['bi']['47']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_volt_var_control'] = resp['bi']['48']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_watt_var'] = resp['bi']['49']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_pf_correction'] = resp['bi']['50']['value']
            nameplate_pts['np_supported_ctrl_mode_func']['np_support_pricing'] = resp['bi']['51']['value']
        else:
            self.ts.log_warning('Outstation read of nameplate data failed!')

        return nameplate_pts

    def get_monitoring(self):
        '''
        This information is indicative of the present operating conditions of the
        DER. This information may be read.
        '''
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        # Getting dictionaries containing the points to be read
        monitoring_pts = monitoring_data.copy()
        operational_pts = operational_state.copy()
        connection_pts = connection_state.copy()
        alarm_pts = alarm_state.copy()

        points = {'ai': {}, 'bi': {}}
        false = False  # Don't remove - required for eval of read_outstation data
        true = True  # Don't remove - required for eval of read_outstation data
        null = None   # Don't remove - required for eval of read_outstation data
        # Creating a points dictionary of format:
        # {'ai': {'PT1': None, 'PT2': None}, 'bi': {'PT3': None}} for the read func.
        for key, values in monitoring_pts.items():
            keys1 = list(values.keys())
            val = list(values.values())
            for i in val:
                keys2 = list(i.keys())
                for x in keys1:
                    for y in keys2:
                        if x == 'ai':
                            points['ai'][y] = None

        for key, values in operational_pts.items():
            keys1 = list(values.keys())
            val = list(values.values())
            for i in val:
                keys2 = list(i.keys())
                for x in keys1:
                    for y in keys2:
                        if x == 'bi':
                            points['bi'][y] = None

        for key, values in connection_pts.items():
            keys1 = list(values.keys())
            val = list(values.values())
            for i in val:
                keys2 = list(i.keys())
                for x in keys1:
                    for y in keys2:
                        if x == 'bi':
                            points['bi'][y] = None

        for key, values in alarm_pts.items():
            keys1 = list(values.keys())
            val = list(values.values())
            for i in val:
                keys2 = list(i.keys())
                for x in keys1:
                    for y in keys2:
                        if x == 'bi':
                            points['bi'][y] = None

        monitoring_read = agent.read_outstation(self.oid, self.rid, points)
        res = eval(monitoring_read[1:-1])
        # Reassembling the read response to make it easy to read
        if 'params' in res.keys():
            resp = res['params']
            monitoring_pts['mn_active_power'] = resp['ai']['537']['value']
            monitoring_pts['mn_reactive_power'] = resp['ai']['541']['value']
            monitoring_pts['mn_voltage'] = resp['ai']['547']['value']
            monitoring_pts['mn_frequency'] = resp['ai']['536']['value']
            monitoring_pts['mn_operational_state_of_charge'] = resp['ai']['48']['value']
            monitoring_pts['mn_op'] = {}
            monitoring_pts['mn_conn'] = {}
            monitoring_pts['mn_alm'] = {}
            monitoring_pts['mn_op']['mn_op_local'] = resp['bi']['10']['value']
            monitoring_pts['mn_op']['mn_op_lockout'] = resp['bi']['11']['value']
            monitoring_pts['mn_op']['mn_op_starting'] = resp['bi']['12']['value']
            monitoring_pts['mn_op']['mn_op_stopping'] = resp['bi']['13']['value']
            monitoring_pts['mn_op']['mn_op_started'] = resp['bi']['14']['value']
            monitoring_pts['mn_op']['mn_op_stopped'] = resp['bi']['15']['value']
            monitoring_pts['mn_op']['mn_op_permission_to_start'] = resp['bi']['16']['value']
            monitoring_pts['mn_op']['mn_op_permission_to_stop'] = resp['bi']['17']['value']
            monitoring_pts['mn_conn']['mn_conn_connected_idle'] = resp['bi']['18']['value']
            monitoring_pts['mn_conn']['mn_conn_connected_generating'] = resp['bi']['19']['value']
            monitoring_pts['mn_conn']['mn_conn_connected_charging'] = resp['bi']['20']['value']
            monitoring_pts['mn_conn']['mn_conn_off_available'] = resp['bi']['21']['value']
            monitoring_pts['mn_conn']['mn_conn_off_not_available'] = resp['bi']['22']['value']
            monitoring_pts['mn_conn']['mn_conn_switch_closed_status'] = resp['bi']['23']['value']
            monitoring_pts['mn_conn']['mn_conn_switch_closed_movement'] = resp['bi']['24']['value']
            monitoring_pts['mn_alm']['mn_alm_system_comm_error'] = resp['bi']['0']['value']
            monitoring_pts['mn_alm']['mn_alm_priority_1'] = resp['bi']['1']['value']
            monitoring_pts['mn_alm']['mn_alm_priority_2'] = resp['bi']['2']['value']
            monitoring_pts['mn_alm']['mn_alm_priority_3'] = resp['bi']['3']['value']
            monitoring_pts['mn_alm']['mn_alm_storage_chg_max'] = resp['bi']['4']['value']
            monitoring_pts['mn_alm']['mn_alm_storage_chg_high'] = resp['bi']['5']['value']
            monitoring_pts['mn_alm']['mn_alm_storage_chg_low'] = resp['bi']['6']['value']
            monitoring_pts['mn_alm']['mn_alm_storage_chg_depleted'] = resp['bi']['7']['value']
            monitoring_pts['mn_alm']['mn_alm_internal_temp_high'] = resp['bi']['8']['value']
            monitoring_pts['mn_alm']['mn_alm_internal_temp_low'] = resp['bi']['9']['value']

        return monitoring_pts

    def get_fixed_pf(self):
        '''
        This information is used to update functional and mode settings for the
        Fixed Power Factor Mode. This information may be read.
        '''

        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        fixed_pf_pts = fixed_pf.copy()

        points = {'ai': {}, 'bi': {}}
        false = False  # Don't remove - required for eval of read_outstation data
        true = True  # Don't remove - required for eval of read_outstation data
        null = None   # Don't remove - required for eval of read_outstation data

        for key, values in fixed_pf_pts.items():
            keys1 = list(values.keys())
            val = list(values.values())
            for i in val:
                keys2 = list(i.keys())
                for x in keys1:
                    for y in keys2:
                        if x == 'ai':
                            points['ai'][y] = None
                        elif x == 'bi':
                            points['bi'][y] = None
                        else:
                            points = {}

        fixed_pf_read = agent.read_outstation(self.oid, self.rid, points)
        res = eval(fixed_pf_read[1:-1])
        if 'params' in res.keys():
            resp = res['params']

            # Writing the point values and flags in the fixed_pf dictionary for response
            fixed_pf_pts['pf_enable'] = resp['bi']['80']['value']
            fixed_pf_pts['pf'] = resp['ai']['288']['value']
            fixed_pf_pts['pf_excitation'] = resp['bi']['29']['value']

        return fixed_pf_pts

    def set_fixed_pf(self, params=None):
        '''
        This information is used to update functional and mode settings for the
        Fixed Power Factor Mode. This information may be written.
        '''
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        fixed_pf_pts = fixed_pf_write.copy()
        points = {'ao': {}, 'bo': {}}
        point_name = []
        pt_value = []

        for key, value in params.items():
            point_name.append(key)
            pt_value.append(value)

        for x in range(0, len(point_name)):
            if point_name[x] != 'pf_enable':
                key = list(fixed_pf_pts[point_name[x]].keys())
                val = list(fixed_pf_pts[point_name[x]].values())
                for i in key:
                    for j in val:
                        key2 = list(j.keys())
                        for y in key2:
                            points[i][y] = pt_value[x]

        fixed_pf_w1 = agent.write_outstation(self.oid, self.rid, points)
        res1 = eval(fixed_pf_w1[1:-1])

        points_en = {'bo': {}}

        for x in range(0, len(point_name)):
            if point_name[x] == 'pf_enable':
                key = list(fixed_pf_pts[point_name[x]].keys())
                val = list(fixed_pf_pts[point_name[x]].values())
                for i in key:
                    for j in val:
                        key2 = list(j.keys())
                        for y in key2:
                            points_en[i][y] = pt_value[x]

        fixed_pf_w2 = agent.write_outstation(self.oid, self.rid, points_en)
        res2 = eval(fixed_pf_w2[1:-1])
        res = {'params': {'points': {'ao': {}, 'bo': {}}}}
        res['params']['points']['ao'] = res1['params']['points']['ao']
        res['params']['points']['bo']['10'] = res1['params']['points']['bo']['10']
        res['params']['points']['bo']['28'] = res2['params']['points']['bo']['28']

        if 'params' in res.keys():
            resp = res['params']['points']
            if 'bo' in resp.keys():
                if '28' in resp['bo']:
                    fixed_pf_pts['pf_enable'] = resp['bo']['28']
                else:
                    fixed_pf_pts['pf_enable'] = {'status': 'Not Written'}
                if '10' in resp['bo']:
                    fixed_pf_pts['pf_excitation'] = resp['bo']['10']
                else:
                    fixed_pf_pts['pf_excitation'] = {'status': 'Not Written'}
            if 'ao' in resp.keys():
                if '210' in resp['ao']:
                    fixed_pf_pts['pf'] = resp['ao']['210']
                else:
                    fixed_pf_pts['pf'] = {'status': 'Not Written'}

            res['params']['points'] = fixed_pf_pts

        return res

    def get_volt_var(self):
        '''
        This information is used to get functional and mode settings for the
        Voltage-Reactive Power Mode. This information may be read.
        '''
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        volt_var_pts = volt_var_data.copy()
        volt_var_pts.update(curve_read.copy())

        points = {'ai': {}, 'bi': {}}
        false = False  # Don't remove - required for eval of read_outstation data
        true = True  # Don't remove - required for eval of read_outstation data
        null = None   # Don't remove - required for eval of read_outstation data

        for key, values in volt_var_pts.items():
            keys1 = list(values.keys())
            val = list(values.values())
            for i in val:
                keys2 = list(i.keys())
                for x in keys1:
                    for y in keys2:
                        if x == 'ai':
                            points['ai'][y] = None
                        elif x == 'bi':
                            points['bi'][y] = None
                        else:
                            points = {}

        volt_var_read = agent.read_outstation(self.oid, self.rid, points)
        res = eval(volt_var_read[1:-1])
        if 'params' in res.keys():
            resp = res['params']
            params = {}
            params['vv_enable'] = resp['bi']['81']['value']
            params['vv_vref'] = resp['ai']['29']['value']
            params['vv_vref_enable'] = resp['bi']['93']['value']
            params['vv_vref_time'] = resp['ai']['300']['value']
            params['vv_curve_index'] = resp['ai']['303']['value']
            params['vv_open_loop_time'] = resp['ai']['298']['value']
            no_points = 4

            v = []
            var = []
            for x in range(333, 332 + (no_points * 2), 2):
                v.append(resp['ai'][str(x)]['value'])
                var.append(resp['ai'][str(x+1)]['value'])
            params['vv_curve'] = {'v': v, 'q': var}

        return params

    # Combining volt_var and volt_var_curve
    def set_volt_var(self, params=None):
        """
        Parameters                                  Names
        Voltage-Reactive Power Mode Enable         vv_enable
        VRef Reference voltage                     vv_vref
        Autonomous VRef adjustment enable          vv_vref_enable
        VRef adjustment time constant              vv_vref_time
        V/Q Curve Points                           vv_curve (dict): {'v': [], 'q': []}
        Open Loop Response Time                    vv_open_loop_time

        Step        Description             Optionality     Function Codes              Type    Point   Read-back pt
        1. Set priority of this mode          Optional      Direct Operate / Response   AO      AO212   AI290
        2. Set the enabling time window       Optional      Direct Operate / Response   AO      AO213   AI291
        3. Set the enabling ramp time         Optional      Direct Operate / Response   AO      AO214   AI292
        4. Set the enabling reversion timeout Optional      Direct Operate / Response   AO      AO215   AI293
        5. Identify the meter used to measure
           the voltage. By default this is the
           System Meter (ID = 0)              Optional      Direct Operate / Response   AO      AO216   AI294
        6. If using a fixed Voltage reference:
           Set the reference voltage if
           it has not already been set        Optional      Direct Operate / Response   AO      AO0     AI29
        7. If using a fixed Voltage reference:
           Set the reference voltage offset
           if it has not already been set     Optional      Direct Operate / Response   AO      AO1     AI30
        8. If autonomously adjusting the
           Voltage reference, set the time
           constant for the lowpass filter    Optional      Direct Operate / Response   AO      AO220   AI300
        9. If autonomously adjusting the
           Voltage reference, enable
           autonomous adjustment              Optional      Direct Operate / Response   BO      BO41    BI93
        10. Select which curve to edit        Optional      Direct Operate / Response   AO      AO244   AI328
        11. Specify the Curve Mode Type as
            <2> Volt-VAr mode                 Optional      Direct Operate / Response   AO      AO245   AI329
        12. Specify that the Independent
            (XValue) units are <129> Percent
            Voltage                           Optional      Direct Operate / Response   AO      AO247   AI331
        13. Specify the Dependent (Y-Value)
            units as described in Table 53.   Optional      Direct Operate / Response   AO      AO248   AI332
        14. Set percent voltage (X-Values)
            for each curve point              Optional      Direct Operate / Response   AO      AO249,..AI333,..
        15. Set percent VArs (Y-Values) for
            each curve point                  Optional      Direct Operate / Response   AO      AO250,..AI334,..
        16. Set number of points used for
            the curve.                        Optional      Direct Operate / Response   AO      AO246   AI330
        17. Set the time constant for the
            output of the curve               Optional      Direct Operate / Response   AO      AO218-9 AI298-9
        18. Identify the index of the curve
            being used                        Optional      Direct Operate / Response   AO      AO217   AI297
        19. Enable the Volt-VAr Control
            Mode                              Required      Select/Response, Op/Resp    BO      BO29    BI48
        20. Read the adjusted reference
            voltage, if it is not fixed       Optional      Read                        Class 1/2/3     AI296
        21. Read the measured Voltage         Optional      Read                        Class 1/2/3     AI295
        22. Read the attempted VArs           Optional      Read                        Class 1/2/3     AI301
        23. Read the actual VArs (if using
        system meter)                         Optional      Read                        Class 1/2/3     AI541
        """
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        volt_var_curve_pts = volt_var_curve.copy()
        points = {'ao': {}, 'bo': {}}
        point_name = []
        pt_value = []

        for key, value in params.items():
            point_name.append(key)
            pt_value.append(value)

        for x in range(0, len(point_name)):
            if point_name[x] != 'vv_enable' and point_name[x] != 'vv_curve' and point_name[x] != 'vv_open_loop_time':
                key = list(volt_var_curve_pts[point_name[x]].keys())
                val = list(volt_var_curve_pts[point_name[x]].values())
                for i in key:
                    for j in val:
                        key2 = list(j.keys())
                        for y in key2:
                            points[i][y] = pt_value[x]

        # Write the vv points except Volt-Var Enable
        self.ts.log_debug('Writing the following points: %s' % points)
        volt_var_w1 = agent.write_outstation(self.oid, self.rid, points)

        for x in range(0, len(point_name)):
            if point_name[x] == 'vv_open_loop_time':
                time_pt = {'ao': {'218': pt_value[x], '219': pt_value[x]}}

                # Write Open loop time
                self.ts.log_debug('Writing Open loop time: %s' % time_pt)
                vv_time = agent.write_outstation(self.oid, self.rid, time_pt)

        points_v = {'ao': {}}
        points_q = {'ao': {}}
        i = 0
        j = 0

        v_pts = []
        for x in range(0, len(point_name)):
            if point_name[x] == 'vv_curve':
                v_pts = pt_value[x]['v']
                q_pts = pt_value[x]['q']

        no_points = len(v_pts)
        vv_points = {'ao': {'217': '1',  # Volt-Var Curve Index
                            '244': '1',  # Curve Edit Selector
                            '245': '2',  # Curve Mode Type (2 = Volt-var)
                            '246': no_points,  # Curve number of points
                            '247': '129',  # Voltage
                            '248': '2'}}  #
                            # '248': '2'}}  # % of Available VARs (VArAval)  - DNP3 App Note Table 53 for details
        self.ts.log_debug('Configuring Curve. Writing VV points: %s' % vv_points)
        vv_curve_settings = agent.write_outstation(self.oid, self.rid, vv_points)

        x_curve_point_start = 249
        y_curve_point_start = 250
        for x in range(x_curve_point_start, x_curve_point_start-1 + (no_points * 2), 2):
            points_v['ao'][str(x)] = str(v_pts[i]*10)
            i += 1

        for y in range(y_curve_point_start, y_curve_point_start-1 + (no_points * 2), 2):
            points_q['ao'][str(y)] = str(q_pts[j]*10)
            j += 1

        self.ts.log_debug('Writing Voltage Points: %s' % points_v)
        curve_write_v = agent.write_outstation(self.oid, self.rid, points_v)
        self.ts.log_debug('Writing Var Points: %s' % points_v)
        curve_write_q = agent.write_outstation(self.oid, self.rid, points_q)

        points_en = {'bo': {}}

        for x in range(0, len(point_name)):
            if point_name[x] == 'vv_enable':
                key = list(volt_var_curve_pts[point_name[x]].keys())
                val = list(volt_var_curve_pts[point_name[x]].values())
                for i in key:
                    for j in val:
                        key2 = list(j.keys())
                        for y in key2:
                            points_en[i][y] = pt_value[x]

        # Writing the Volt-Var Enable
        self.ts.log_debug('Enabling VV Function: %s' % points_en)
        volt_var_w2 = agent.write_outstation(self.oid, self.rid, points_en)

        res1 = eval(curve_write_v[1:-1])
        res2 = eval(curve_write_q[1:-1])

        if 'params' in res1.keys():
            resp1 = res1['params']['points']
            v_key = list(points_v['ao'].keys())
            for i in range(0, no_points):
                points['V-Point%s' % str(i + 1)] = resp1['ao'][v_key[i]]

        if 'params' in res2.keys():
            resp2 = res2['params']['points']
            q_key = list(points_q['ao'].keys())
            for i in range(0, no_points):
                points['Q-Point%s' % str(i + 1)] = resp2['ao'][q_key[i]]

        return points

    def get_reactive_power(self):
        '''
        This information is used to update functional and mode settings for the
        Constant Reactive Power Mode. This information may be read.
        '''
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        reactive_power_pts = reactive_power_data.copy()

        points = {'ai': {}, 'bi': {}}
        false = False  # Don't remove - required for eval of read_outstation data
        true = True  # Don't remove - required for eval of read_outstation data
        null = None   # Don't remove - required for eval of read_outstation data

        for key, values in reactive_power_pts.items():
            keys1 = list(values.keys())
            val = list(values.values())
            for i in val:
                keys2 = list(i.keys())
                for x in keys1:
                    for y in keys2:
                        if x == 'ai':
                            points['ai'][y] = None
                        elif x == 'bi':
                            points['bi'][y] = None
                        else:
                            points = {}

        reactive_power_read = agent.read_outstation(self.oid, self.rid, points)
        res = eval(reactive_power_read[1:-1])
        if 'params' in res.keys():
            resp = res['params']
            reactive_power_pts['var_enable'] = resp['bi']['79']['value']
            reactive_power_pts['var'] = resp['ai']['281']['value']
            res['params'] = reactive_power_pts

        return res

    def set_reactive_power(self, params=None):
        '''
        This information is used to update functional and mode settings for the
        Constant Reactive Power Mode. This information may be written.
        '''
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        reactive_power_pts = reactive_power_write.copy()
        points = {'ao': {}, 'bo': {}}
        point_name = []
        pt_value = []

        for key, value in params.items():
            point_name.append(key)
            pt_value.append(value)

        for x in range(0, len(point_name)):
            if point_name[x] != 'var_enable':
                key = list(reactive_power_pts[point_name[x]].keys())
                val = list(reactive_power_pts[point_name[x]].values())
                for i in key:
                    for j in val:
                        key2 = list(j.keys())
                        for y in key2:
                            points[i][y] = pt_value[x]

        reactive_power_w1 = agent.write_outstation(self.oid, self.rid, points)
        res1 = eval(reactive_power_w1[1:-1])

        points_en = {'bo': {}}

        for x in range(0, len(point_name)):
            if point_name[x] == 'var_enable':
                key = list(reactive_power_pts[point_name[x]].keys())
                val = list(reactive_power_pts[point_name[x]].values())
                for i in key:
                    for j in val:
                        key2 = list(j.keys())
                        for y in key2:
                            points_en[i][y] = pt_value[x]

        reactive_power_w2 = agent.write_outstation(self.oid, self.rid, points_en)
        res2 = eval(reactive_power_w2[1:-1])

        res = {'params': {'points': {'ao': {}, 'bo': {}}}}
        res['params']['points']['ao']['203'] = res1['params']['points']['ao']['203']
        res['params']['points']['bo']['27'] = res2['params']['points']['bo']['27']

        if 'params' in res.keys():
            resp = res['params']['points']
            if 'bo' in resp.keys():
                if '27' in resp['bo']:
                    reactive_power_pts['var_enable'] = resp['bo']['27']
                else:
                    reactive_power_pts['var_enable'] = {'status': 'Not Written'}
            if 'ao' in resp.keys():
                if '203' in resp['ao']:
                    reactive_power_pts['var'] = resp['ao']['203']
                else:
                    reactive_power_pts['var'] = {'status': 'Not Written'}

            res['params']['points'] = reactive_power_pts

        return res

    def get_freq_watt(self):
        '''
        This information is used to update functional and mode settings for the
        Frequency-Active Power Mode. This information may be read.
        '''
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        freq_watt_pts = freq_watt_data.copy()

        points = {'ai': {}, 'bi': {}}
        false = False  # Don't remove - required for eval of read_outstation data
        true = True  # Don't remove - required for eval of read_outstation data
        null = None   # Don't remove - required for eval of read_outstation data

        for key, values in freq_watt_pts.items():
            keys1 = list(values.keys())
            val = list(values.values())
            for i in val:
                keys2 = list(i.keys())
                for x in keys1:
                    for y in keys2:
                        if x == 'ai':
                            points['ai'][y] = None
                        elif x == 'bi':
                            points['bi'][y] = None
                        else:
                            points = {}

        freq_watt_read = agent.read_outstation(self.oid, self.rid, points)
        res = eval(freq_watt_read[1:-1])
        if 'params' in res.keys():
            resp = res['params']
            freq_watt_pts['fw_dbof'] = resp['ai']['121']['value']
            freq_watt_pts['fw_dbuf'] = resp['ai']['125']['value']
            freq_watt_pts['fw_kof'] = resp['ai']['123']['value']
            freq_watt_pts['fw_kuf'] = resp['ai']['127']['value']
            freq_watt_pts['fw_open_loop_time'] = resp['ai']['131']['value']
            res['params'] = freq_watt_pts

        return res

    def set_freq_watt(self, params=None):
        """
        This information is used to update functional and mode settings for the
        Frequency-Active Power Mode. This information may be written.
        """
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        freq_watt_pts = {}
        point_name = []
        pt_value = []

        for key, value in params.items():
            point_name.append(key)
            pt_value.append(value)

        for x in range(0, len(point_name)):
            if point_name[x] == 'fw_dbof':
                dbof_val = pt_value[x]
                dbof_pt = {'ao': {'62': dbof_val, '63': dbof_val}}

        for x in range(0, len(point_name)):
            if point_name[x] == 'fw_dbuf':
                dbuf_val = pt_value[x]
                dbuf_pt = {'ao': {'66': dbuf_val, '67': dbuf_val}}

        for x in range(0, len(point_name)):
            if point_name[x] == 'fw_kof':
                kof_val = pt_value[x]
                kof_pt = {'ao': {'64': kof_val, '65': kof_val}}

        for x in range(0, len(point_name)):
            if point_name[x] == 'fw_kuf':
                kuf_val = pt_value[x]
                kuf_pt = {'ao': {'68': kuf_val, '69': kuf_val}}

        for x in range(0, len(point_name)):
            if point_name[x] == 'fw_open_loop_time':
                time_val = pt_value[x]
                time_pt = {'ao': {'72': time_val, '73': time_val}}

        for x in range(0, len(point_name)):
            if point_name[x] == 'fw_enable':
                enable_val = pt_value[x]
                enable_pt = {'bo': {'26': enable_val}}

        dbof_w = agent.write_outstation(self.oid, self.rid, dbof_pt)
        dbuf_w = agent.write_outstation(self.oid, self.rid, dbuf_pt)
        kof_w = agent.write_outstation(self.oid, self.rid, kof_pt)
        kuf_w = agent.write_outstation(self.oid, self.rid, kuf_pt)
        time_w = agent.write_outstation(self.oid, self.rid, time_pt)
        enable_w = agent.write_outstation(self.oid, self.rid, enable_pt)

        res1 = eval(dbof_w[1:-1])
        res2 = eval(dbuf_w[1:-1])
        res3 = eval(kof_w[1:-1])
        res4 = eval(kuf_w[1:-1])
        res5 = eval(time_w[1:-1])
        res6 = eval(enable_w[1:-1])

        res = {'params': {'points': {'ao': {}, 'bo': {}}}}
        res['params']['points']['ao']['62'] = res1['params']['points']['ao']['62']
        res['params']['points']['ao']['62'] = res1['params']['points']['ao']['63']
        res['params']['points']['ao']['66'] = res2['params']['points']['ao']['66']
        res['params']['points']['ao']['67'] = res2['params']['points']['ao']['67']
        res['params']['points']['ao']['64'] = res3['params']['points']['ao']['64']
        res['params']['points']['ao']['65'] = res3['params']['points']['ao']['65']
        res['params']['points']['ao']['68'] = res4['params']['points']['ao']['68']
        res['params']['points']['ao']['69'] = res4['params']['points']['ao']['69']
        res['params']['points']['ao']['72'] = res5['params']['points']['ao']['72']
        res['params']['points']['ao']['73'] = res5['params']['points']['ao']['73']
        res['params']['points']['bo']['26'] = res6['params']['points']['bo']['26']
        if 'params' in res.keys():
            resp = res['params']['points']
            if 'ao' in resp.keys():
                if '62' in resp['ao']:
                    freq_watt_pts['fw_dbof'] = resp['ao']['62']
                else:
                    freq_watt_pts['fw_dbof'] = {'status': 'Not Written'}
                if '66' in resp['ao']:
                    freq_watt_pts['fw_dbuf'] = resp['ao']['66']
                else:
                    freq_watt_pts['fw_dbuf'] = {'status': 'Not Written'}
                if '64' in resp['ao']:
                    freq_watt_pts['fw_kof'] = resp['ao']['64']
                else:
                    freq_watt_pts['fw_kof'] = {'status': 'Not Written'}
                if '68' in resp['ao']:
                    freq_watt_pts['fw_kuf'] = resp['ao']['68']
                else:
                    freq_watt_pts['fw_kuf'] = {'status': 'Not Written'}
                if '72' in resp['ao']:
                    freq_watt_pts['fw_open_loop_time'] = resp['ao']['72']
                else:
                    freq_watt_pts['fw_open_loop_time'] = {'status': 'Not Written'}

            res['params']['points'] = freq_watt_pts

        return res

    def get_limit_max_power(self):
        '''
        This information is used to update functional and mode settings for the
        Limit Maximum Active Power Mode. This information may be read.
        '''
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        limit_max_power_pts = limit_max_power_data.copy()
        points = {'ai': {}, 'bi': {}}
        false = False  # Don't remove - required for eval of read_outstation data
        true = True  # Don't remove - required for eval of read_outstation data
        null = None   # Don't remove - required for eval of read_outstation data

        for key, values in limit_max_power_pts.items():
            keys1 = list(values.keys())
            val = list(values.values())
            for i in val:
                keys2 = list(i.keys())
                for x in keys1:
                    for y in keys2:
                        if x == 'ai':
                            points['ai'][y] = None
                        elif x == 'bi':
                            points['bi'][y] = None
                        else:
                            points = {}

        limit_max_power_read = agent.read_outstation(self.oid, self.rid, points)
        res = eval(limit_max_power_read[1:-1])
        if 'params' in res.keys():
            resp = res['params']
            limit_max_power_pts['watt_enable'] = resp['bi']['69']['value']
            limit_max_power_pts['watt'] = resp['ai']['149']['value']
            res['params'] = limit_max_power_pts

        return res

    def set_limit_max_power(self, params=None):
        '''
        This information is used to update functional and mode settings for the
        Limit Maximum Active Power Mode. This information may be written.
        '''
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        limit_max_power_pts = limit_max_power_write.copy()
        points = {'ao': {}, 'bo': {}}
        point_name = []
        pt_value = []

        for key, value in params.items():
            point_name.append(key)
            pt_value.append(value)

        for x in range(0, len(point_name)):
            if point_name[x] != 'watt_enable':
                key = list(limit_max_power_pts[point_name[x]].keys())
                val = list(limit_max_power_pts[point_name[x]].values())
                for i in key:
                    for j in val:
                        key2 = list(j.keys())
                        for y in key2:
                            points[i][y] = pt_value[x]

        limit_max_power_w1 = agent.write_outstation(self.oid, self.rid, points)
        res1 = eval(limit_max_power_w1[1:-1])

        points_en = {'ao': {}, 'bo': {}}

        for x in range(0, len(point_name)):
            if point_name[x] == 'watt_enable':
                key = list(limit_max_power_pts[point_name[x]].keys())
                val = list(limit_max_power_pts[point_name[x]].values())
                for i in key:
                    for j in val:
                        key2 = list(j.keys())
                        for y in key2:
                            points_en[i][y] = pt_value[x]

        limit_max_power_w2 = agent.write_outstation(self.oid, self.rid, points_en)
        res2 = eval(limit_max_power_w2[1:-1])

        res = {'params': {'points': {'ao': {}, 'bo': {}}}}
        res['params']['points']['ao']['88'] = res1['params']['points']['ao']['88']
        res['params']['points']['bo']['17'] = res2['params']['points']['bo']['17']

        if 'params' in res.keys():
            resp = res['params']['points']
            if 'bo' in resp.keys():
                if '17' in resp['bo']:
                    limit_max_power_pts['watt_enable'] = resp['bo']['17']
                else:
                    limit_max_power_pts['watt_enable'] = {'status': 'Not Written'}
            if 'ao' in resp.keys():
                if '88' in resp['ao']:
                    limit_max_power_pts['watt'] = resp['ao']['88']
                else:
                    limit_max_power_pts['watt'] = {'status': 'Not Written'}

            res['params']['points'] = limit_max_power_pts

        return res

    def get_enter_service(self):
        '''
        This information is used to update functional and mode settings for the
        Enter Service Mode. This information may be read.
        '''
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        enter_service_pts = enter_service_data.copy()

        points = {'ai': {}, 'bi': {}}
        false = False  # Don't remove - required for eval of read_outstation data
        true = True  # Don't remove - required for eval of read_outstation data
        null = None   # Don't remove - required for eval of read_outstation data

        for key, values in enter_service_pts.items():
            keys1 = list(values.keys())
            val = list(values.values())
            for i in val:
                keys2 = list(i.keys())
                for x in keys1:
                    for y in keys2:
                        if x == 'ai':
                            points['ai'][y] = None
                        elif x == 'bi':
                            points['bi'][y] = None
                        else:
                            points = {}

        enter_service_read = agent.read_outstation(self.oid, self.rid, points)
        res = eval(enter_service_read[1:-1])
        if 'params' in res.keys():
            resp = res['params']
            enter_service_pts['es_permit_service'] = resp['bi']['16']['value']
            enter_service_pts['es_volt_high'] = resp['ai']['50']['value']
            enter_service_pts['es_volt_low'] = resp['ai']['51']['value']
            enter_service_pts['es_freq_high'] = resp['ai']['52']['value']
            enter_service_pts['es_freq_low'] = resp['ai']['53']['value']
            enter_service_pts['es_delay'] = resp['ai']['54']['value']
            enter_service_pts['es_randomized_delay'] = resp['ai']['55']['value']
            enter_service_pts['es_ramp_rate'] = resp['ai']['56']['value']
            res['params'] = enter_service_pts

        return res

    def set_enter_service(self, params=None):
        '''
        This information is used to update functional and mode settings for the
        Enter Service Mode. This information may be written.
        '''
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        enter_service_pts = enter_service_write.copy()
        points = {'ao': {}, 'bo': {}}
        point_name = []
        pt_value = []

        for key, value in params.items():
            point_name.append(key)
            pt_value.append(value)

        for x in range(0, len(point_name)):
            key = list(enter_service_pts[point_name[x]].keys())
            val = list(enter_service_pts[point_name[x]].values())
            for i in key:
                for j in val:
                    key2 = list(j.keys())
                    for y in key2:
                        points[i][y] = pt_value[x]

        enter_service_w = agent.write_outstation(self.oid, self.rid, points)
        res = eval(enter_service_w[1:-1])

        if 'params' in res.keys():
            resp = res['params']['points']
            if 'bo' in resp.keys():
                if '3' in resp['bo']:
                    enter_service_pts['es_permit_service'] = resp['bo']['3']
                else:
                    enter_service_pts['es_permit_service'] = {'state': 'Not Written'}
            if 'ao' in resp.keys():
                if '6' in resp['ao']:
                    enter_service_pts['es_volt_high'] = resp['ao']['6']
                else:
                    enter_service_pts['es_volt_high'] = {'state': 'Not Written'}
                if '7' in resp['ao']:
                    enter_service_pts['es_volt_low'] = resp['ao']['7']
                else:
                    enter_service_pts['es_volt_low'] = {'state': 'Not Written'}
                if '8' in resp['ao']:
                    enter_service_pts['es_freq_high'] = resp['ao']['8']
                else:
                    enter_service_pts['es_freq_high'] = {'state': 'Not Written'}
                if '9' in resp['ao']:
                    enter_service_pts['es_freq_low'] = resp['ao']['9']
                else:
                    enter_service_pts['es_freq_low'] = {'state': 'Not Written'}
                if '10' in resp['ao']:
                    enter_service_pts['es_delay'] = resp['ao']['10']
                else:
                    enter_service_pts['es_delay'] = {'state': 'Not Written'}
                if '11' in resp['ao']:
                    enter_service_pts['es_randomized_delay'] = resp['ao']['11']
                else:
                    enter_service_pts['es_randomized_delay'] = {'state': 'Not Written'}
                if '12' in resp['ao']:
                    enter_service_pts['es_ramp_rate'] = resp['ao']['12']
                else:
                    enter_service_pts['es_ramp_rate'] = {'state': 'Not Written'}

            res['params']['points'] = enter_service_pts

        return res

    def get_watt_var(self):
        pass

    def set_watt_var(self, params=None):
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        point_name = []
        pt_value = []

        for key, value in params.items():
            point_name.append(key)
            pt_value.append(value)

        points = {'ao': {}}

        points_p = {'ao': {}}
        points_q = {'ao': {}}
        i = 0
        j = 0

        for x in range(0, len(point_name)):
            if point_name[x] == 'pq_curve':
                p_pts = pt_value[x]['p']
                q_pts = pt_value[x]['q']

        no_points = len(p_pts)
        wq_points = {'ao': {'226': '2', '244': '2', '245': '4', '246': no_points, '247': '38', '248': '3'}}
        wq_curve_settings = agent.write_outstation(self.oid, self.rid, wq_points)

        for x in range(249, 248 + (no_points * 2), 2):
            points_p['ao'][str(x)] = str(p_pts[i])
            i += 1

        for y in range(250, 249 + (no_points * 2), 2):
            points_q['ao'][str(y)] = str(q_pts[j])
            j += 1

        curve_write_p = agent.write_outstation(self.oid, self.rid, points_p)
        curve_write_q = agent.write_outstation(self.oid, self.rid, points_q)

        res1 = eval(curve_write_p[1:-1])
        res2 = eval(curve_write_q[1:-1])

        for x in range(0, len(point_name)):
            if point_name[x] == 'pq_enable':
                enable_pt = {'bo': {'30': pt_value[x]}}

        # Writing the Watt-Var Enable
        watt_var_w = agent.write_outstation(self.oid, self.rid, enable_pt)

        if 'params' in res1.keys():
            resp1 = res1['params']['points']
            p_key = list(points_p['ao'].keys())
            for i in range(0, no_points):
                points['P-Point%s' % str(i + 1)] = resp1['ao'][p_key[i]]

        if 'params' in res2.keys():
            resp2 = res2['params']['points']
            q_key = list(points_q['ao'].keys())
            for i in range(0, no_points):
                points['Q-Point%s' % str(i + 1)] = resp2['ao'][q_key[i]]

        return points

    def set_volt_watt(self, params=None):
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        point_name = []
        pt_value = []

        for key, value in params.items():
            point_name.append(key)
            pt_value.append(value)

        points = {'ao': {}}

        points_v = {'ao': {}}
        points_p = {'ao': {}}
        i = 0
        j = 0

        for x in range(0, len(point_name)):
            if point_name[x] == 'vp_curve':
                v_pts = pt_value[x]['v']
                p_pts = pt_value[x]['p']

        no_points = len(v_pts)
        vp_points = {'ao': {'173': '3', '244': '3', '245': '5', '246': no_points, '247': '29', '248': '5'}}
        vp_curve_settings = agent.write_outstation(self.oid, self.rid, vp_points)

        for x in range(249, 248 + (no_points * 2), 2):
            points_v['ao'][str(x)] = str(v_pts[i])
            i += 1

        for y in range(250, 249 + (no_points * 2), 2):
            points_p['ao'][str(y)] = str(p_pts[j])
            j += 1

        curve_write_v = agent.write_outstation(self.oid, self.rid, points_v)
        curve_write_p = agent.write_outstation(self.oid, self.rid, points_p)

        res1 = eval(curve_write_v[1:-1])
        res2 = eval(curve_write_p[1:-1])

        for x in range(0, len(point_name)):
            if point_name[x] == 'vp_open_loop_time':
                time_val = pt_value[x]
                time_pt = {'ao': {'175': time_val, '176': time_val}}

        # Write Open loop time
        vp_time = agent.write_outstation(self.oid, self.rid, time_pt)

        for x in range(0, len(point_name)):
            if point_name[x] == 'vp_enable':
                enable_pt = {'bo': {'25': pt_value[x]}}

        # Writing the Volt-Watt Enable
        volt_watt_w = agent.write_outstation(self.oid, self.rid, enable_pt)

        if 'params' in res1.keys():
            resp1 = res1['params']['points']
            v_key = list(points_v['ao'].keys())
            for i in range(0, no_points):
                points['V-Point%s' % str(i + 1)] = resp1['ao'][v_key[i]]

        if 'params' in res2.keys():
            resp2 = res2['params']['points']
            p_key = list(points_p['ao'].keys())
            for i in range(0, no_points):
                points['P-Point%s' % str(i + 1)] = resp2['ao'][p_key[i]]

        return points

    def set_volt_trip(self, params=None):
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        point_name = []
        pt_value = []

        for key, value in params.items():
            point_name.append(key)
            pt_value.append(value)

        points = {'ao': {}}

        points_ht = {'ao': {}}
        points_hv = {'ao': {}}
        points_lt = {'ao': {}}
        points_lv = {'ao': {}}
        i = 0
        j = 0
        k = 0
        n = 0

        for x in range(0, len(point_name)):
            if point_name[x] == 'hv':
                ht_pts = pt_value[x]['t']
                hv_pts = pt_value[x]['v']
            if point_name[x] == 'lv':
                lt_pts = pt_value[x]['t']
                lv_pts = pt_value[x]['v']

        no_points_hv = len(ht_pts)
        no_points_lv = len(lt_pts)
        hv_trip_points = {'ao': {'23': '4', '244': '4', '245': '9', '246': no_points_hv, '247': '4', '248': '8'}}
        lv_trip_points = {'ao': {'24': '5', '244': '5', '245': '11', '246': no_points_lv, '247': '4', '248': '8'}}
        hvrt_curve_settings = agent.write_outstation(self.oid, self.rid, hv_trip_points)
        lvrt_curve_settings = agent.write_outstation(self.oid, self.rid, lv_trip_points)

        for x in range(249, 248 + (no_points_hv * 2), 2):
            points_ht['ao'][str(x)] = str(ht_pts[i])
            i += 1

        for y in range(250, 249 + (no_points_hv * 2), 2):
            points_hv['ao'][str(y)] = str(hv_pts[j])
            j += 1

        for x in range(249, 248 + (no_points_lv * 2), 2):
            points_lt['ao'][str(x)] = str(lt_pts[k])
            k += 1

        for y in range(250, 249 + (no_points_lv * 2), 2):
            points_lv['ao'][str(y)] = str(lv_pts[n])
            n += 1

        curve_write_ht = agent.write_outstation(self.oid, self.rid, points_ht)
        curve_write_hv = agent.write_outstation(self.oid, self.rid, points_hv)
        curve_write_lt = agent.write_outstation(self.oid, self.rid, points_lt)
        curve_write_lv = agent.write_outstation(self.oid, self.rid, points_lv)

        res1 = eval(curve_write_ht[1:-1])
        res2 = eval(curve_write_hv[1:-1])
        res3 = eval(curve_write_lt[1:-1])
        res4 = eval(curve_write_lv[1:-1])

        enable_pt = {'bo': {'12': True}}

        # Writing the HV Trip Enable
        vrt_w = agent.write_outstation(self.oid, self.rid, enable_pt)

        if 'params' in res1.keys():
            resp1 = res1['params']['points']
            ht_key = list(points_ht['ao'].keys())
            for i in range(0, no_points_hv):
                points['HT-Point%s' % str(i + 1)] = resp1['ao'][ht_key[i]]

        if 'params' in res2.keys():
            resp2 = res2['params']['points']
            hv_key = list(points_hv['ao'].keys())
            for i in range(0, no_points_hv):
                points['HV-Point%s' % str(i + 1)] = resp2['ao'][hv_key[i]]

        if 'params' in res3.keys():
            resp3 = res3['params']['points']
            lt_key = list(points_lt['ao'].keys())
            for i in range(0, no_points_lv):
                points['LT-Point%s' % str(i + 1)] = resp3['ao'][lt_key[i]]

        if 'params' in res4.keys():
            resp4 = res4['params']['points']
            lv_key = list(points_lv['ao'].keys())
            for i in range(0, no_points_lv):
                points['LV-Point%s' % str(i + 1)] = resp4['ao'][lv_key[i]]

        return points

    def set_freq_trip(self, params=None):
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        point_name = []
        pt_value = []

        for key, value in params.items():
            point_name.append(key)
            pt_value.append(value)

        points = {'ao': {}}

        points_ht = {'ao': {}}
        points_hf = {'ao': {}}
        points_lt = {'ao': {}}
        points_lf = {'ao': {}}
        i = 0
        j = 0
        k = 0
        n = 0

        for x in range(0, len(point_name)):
            if point_name[x] == 'hf':
                ht_pts = pt_value[x]['t']
                hf_pts = pt_value[x]['f']
            if point_name[x] == 'lf':
                lt_pts = pt_value[x]['t']
                lf_pts = pt_value[x]['f']

        no_points_hf = len(ht_pts)
        no_points_lf = len(lt_pts)
        hf_trip_points = {'ao': {'28': '6', '244': '6', '245': '13', '246': no_points_hf, '247': '4', '248': '9'}}
        lf_trip_points = {'ao': {'29': '7', '244': '7', '245': '15', '246': no_points_lf, '247': '4', '248': '9'}}
        hfrt_curve_settings = agent.write_outstation(self.oid, self.rid, hf_trip_points)
        lfrt_curve_settings = agent.write_outstation(self.oid, self.rid, lf_trip_points)

        for x in range(249, 248 + (no_points_hf * 2), 2):
            points_ht['ao'][str(x)] = str(ht_pts[i])
            i += 1

        for y in range(250, 249 + (no_points_hf * 2), 2):
            points_hf['ao'][str(y)] = str(hf_pts[j])
            j += 1

        for x in range(249, 248 + (no_points_lf * 2), 2):
            points_lt['ao'][str(x)] = str(lt_pts[k])
            k += 1

        for y in range(250, 249 + (no_points_lf * 2), 2):
            points_lf['ao'][str(y)] = str(lf_pts[n])
            n += 1

        curve_write_ht = agent.write_outstation(self.oid, self.rid, points_ht)
        curve_write_hf = agent.write_outstation(self.oid, self.rid, points_hf)
        curve_write_lt = agent.write_outstation(self.oid, self.rid, points_lt)
        curve_write_lf = agent.write_outstation(self.oid, self.rid, points_lf)

        res1 = eval(curve_write_ht[1:-1])
        res2 = eval(curve_write_hf[1:-1])
        res3 = eval(curve_write_lt[1:-1])
        res4 = eval(curve_write_lf[1:-1])

        enable_pt = {'bo': {'13': True}}

        # Writing the HV Trip Enable
        frt_w = agent.write_outstation(self.oid, self.rid, enable_pt)

        if 'params' in res1.keys():
            resp1 = res1['params']['points']
            ht_key = list(points_ht['ao'].keys())
            for i in range(0, no_points_hf):
                points['HT-Point%s' % str(i + 1)] = resp1['ao'][ht_key[i]]

        if 'params' in res2.keys():
            resp2 = res2['params']['points']
            hf_key = list(points_hf['ao'].keys())
            for i in range(0, no_points_hf):
                points['HF-Point%s' % str(i + 1)] = resp2['ao'][hf_key[i]]

        if 'params' in res3.keys():
            resp3 = res3['params']['points']
            lt_key = list(points_lt['ao'].keys())
            for i in range(0, no_points_lf):
                points['LT-Point%s' % str(i + 1)] = resp3['ao'][lt_key[i]]

        if 'params' in res4.keys():
            resp4 = res4['params']['points']
            lf_key = list(points_lf['ao'].keys())
            for i in range(0, no_points_lf):
                points['LF-Point%s' % str(i + 1)] = resp4['ao'][lf_key[i]]

        return points

    def set_volt_cessation(self, params=None):
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        point_name = []
        pt_value = []

        for key, value in params.items():
            point_name.append(key)
            pt_value.append(value)

        points = {'ao': {}}

        points_ht = {'ao': {}}
        points_hv = {'ao': {}}
        points_lt = {'ao': {}}
        points_lv = {'ao': {}}
        i = 0
        j = 0
        k = 0
        n = 0

        for x in range(0, len(point_name)):
            if point_name[x] == 'hv':
                ht_pts = pt_value[x]['t']
                hv_pts = pt_value[x]['v']
            if point_name[x] == 'lv':
                lt_pts = pt_value[x]['t']
                lv_pts = pt_value[x]['v']

        no_points_hv = len(ht_pts)
        no_points_lv = len(lt_pts)
        hv_trip_points = {'ao': {'25': '8', '244': '8', '245': '10', '246': no_points_hv, '247': '4', '248': '8'}}
        lv_trip_points = {'ao': {'26': '9', '244': '9', '245': '12', '246': no_points_lv, '247': '4', '248': '8'}}
        hvrt_curve_settings = agent.write_outstation(self.oid, self.rid, hv_trip_points)
        lvrt_curve_settings = agent.write_outstation(self.oid, self.rid, lv_trip_points)

        for x in range(249, 248 + (no_points_hv * 2), 2):
            points_ht['ao'][str(x)] = str(ht_pts[i])
            i += 1

        for y in range(250, 249 + (no_points_hv * 2), 2):
            points_hv['ao'][str(y)] = str(hv_pts[j])
            j += 1

        for x in range(249, 248 + (no_points_lv * 2), 2):
            points_lt['ao'][str(x)] = str(lt_pts[k])
            k += 1

        for y in range(250, 249 + (no_points_lv * 2), 2):
            points_lv['ao'][str(y)] = str(lv_pts[n])
            n += 1

        curve_write_ht = agent.write_outstation(self.oid, self.rid, points_ht)
        curve_write_hv = agent.write_outstation(self.oid, self.rid, points_hv)
        curve_write_lt = agent.write_outstation(self.oid, self.rid, points_lt)
        curve_write_lv = agent.write_outstation(self.oid, self.rid, points_lv)

        res1 = eval(curve_write_ht[1:-1])
        res2 = eval(curve_write_hv[1:-1])
        res3 = eval(curve_write_lt[1:-1])
        res4 = eval(curve_write_lv[1:-1])

        enable_pt = {'bo': {'12': True}}

        # Writing the HV Trip Enable
        vrt_w = agent.write_outstation(self.oid, self.rid, enable_pt)

        if 'params' in res1.keys():
            resp1 = res1['params']['points']
            ht_key = list(points_ht['ao'].keys())
            for i in range(0, no_points_hv):
                points['HT-Point%s' % str(i + 1)] = resp1['ao'][ht_key[i]]

        if 'params' in res2.keys():
            resp2 = res2['params']['points']
            hv_key = list(points_hv['ao'].keys())
            for i in range(0, no_points_hv):
                points['HV-Point%s' % str(i + 1)] = resp2['ao'][hv_key[i]]

        if 'params' in res3.keys():
            resp3 = res3['params']['points']
            lt_key = list(points_lt['ao'].keys())
            for i in range(0, no_points_lv):
                points['LT-Point%s' % str(i + 1)] = resp3['ao'][lt_key[i]]

        if 'params' in res4.keys():
            resp4 = res4['params']['points']
            lv_key = list(points_lv['ao'].keys())
            for i in range(0, no_points_lv):
                points['LV-Point%s' % str(i + 1)] = resp4['ao'][lv_key[i]]

        return points    

    def get_curve_settings(self):
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        curve_read_pts = curve_read.copy()
        points = {'ai': {}}
        false = False  # Don't remove - required for eval of read_outstation data
        true = True  # Don't remove - required for eval of read_outstation data
        null = None   # Don't remove - required for eval of read_outstation data

        for key, values in curve_read_pts.items():
            keys1 = list(values.keys())
            val = list(values.values())
            for i in val:
                keys2 = list(i.keys())
                for x in keys1:
                    for y in keys2:
                        if x == 'ai':
                            points['ai'][y] = None
                        elif x == 'bi':
                            points['bi'][y] = None
                        else:
                            points = {}

        curve_setting_read = agent.read_outstation(self.oid, self.rid, points)
        res = eval(curve_setting_read[1:-1])
        if 'params' in res.keys():
            resp = res['params']
            curve_read_pts['curve_edit_selector'] = resp['ai']['328']['value']
            curve_read_pts['curve_mode_type'] = resp['ai']['329']['value']
            curve_read_pts['no_of_points'] = resp['ai']['330']['value']
            curve_read_pts['x_value'] = resp['ai']['331']['value']
            curve_read_pts['y_value'] = resp['ai']['332']['value']
            res['params'] = curve_read_pts

        return res


""" Dictionaries for different der1547_dnp3 methods """

nameplate_data = {'np_active_power_rtg': {'ai': {'4': None}},
                  'np_active_power_rtg_over_excited': {'ai': {'6': None}},
                  'np_over_excited_pf': {'ai': {'8': None}},
                  'np_active_power_rtg_under_excited': {'ai': {'9': None}},
                  'np_under_excited_pf': {'ai': {'11': None}},
                  'np_apparent_power_max_rtg': {'ai': {'14': None}},
                  'np_normal_op_category': {'ai': {'22': None}},
                  'np_abnormal_op_category': {'ai': {'23': None}},
                  'np_reactive_power_inj_max_rtg': {'ai': {'12': None}},
                  'np_reactive_power_abs_max_rtg': {'ai': {'13': None}},
                  'np_active_power_chg_max_rtg': {'ai': {'5': None}},
                  'np_apparent_power_chg_max_rtg': {'ai': {'15': None}},
                  'np_ac_volt_nom_rtg': {'ai': {'29': None}},
                  'np_ac_volt_min_rtg': {'ai': {'2': None}},
                  'np_ac_volt_max_rtg': {'ai': {'3': None}},
                  'np_reactive_susceptance': {'ai': {'21': None}}}

nameplate_support = {'np_support_volt_ride_through': {'bi': {'31': None}},
                     'np_support_freq_ride_through': {'bi': {'32': None}},
                     'np_support_dynamic_reactive_current': {'bi': {'33': None}},
                     'np_support_dynamic_volt_watt': {'bi': {'34': None}},
                     'np_support_freq_watt': {'bi': {'35': None}},
                     'np_support_limit_watt': {'bi': {'36': None}},
                     'np_support_chg_dischg': {'bi': {'37': None}},
                     'np_support_coordinated_chg_dischg': {'bi': {'38': None}},
                     'np_support_active_pwr_response_1': {'bi': {'39': None}},
                     'np_support_active_pwr_response_2': {'bi': {'40': None}},
                     'np_support_active_pwr_response_3': {'bi': {'41': None}},
                     'np_support_automation_generation_control': {'bi': {'42': None}},
                     'np_support_active_pwr_smoothing': {'bi': {'43': None}},
                     'np_support_volt_watt': {'bi': {'44': None}},
                     'np_support_freq_watt_curve': {'bi': {'45': None}},
                     'np_support_constant_vars': {'bi': {'46': None}},
                     'np_support_fixed_pf': {'bi': {'47': None}},
                     'np_support_volt_var_control': {'bi': {'48': None}},
                     'np_support_watt_var': {'bi': {'49': None}},
                     'np_support_pf_correction': {'bi': {'50': None}},
                     'np_support_pricing': {'bi': {'51': None}}}

monitoring_data = {'mn_active_power': {'ai': {'537': None}},
                   'mn_reactive_power': {'ai': {'541': None}},
                   'mn_voltage': {'ai': {'547': None}},
                   'mn_frequency': {'ai': {'536': None}},
                   'mn_operational_state_of_charge': {'ai': {'48': None}}}

operational_state = {'mn_op_local': {'bi': {'10': None}},
                     'mn_op_lockout': {'bi': {'11': None}},
                     'mn_op_starting': {'bi': {'12': None}},
                     'mn_op_stopping': {'bi': {'13': None}},
                     'mn_op_started': {'bi': {'14': None}},
                     'mn_op_stopped': {'bi': {'15': None}},
                     'mn_op_permission_to_start': {'bi': {'16': None}},
                     'mn_op_permission_to_stop': {'bi': {'17': None}}}

connection_state = {'mn_conn_connected_idle': {'bi': {'18': None}},
                    'mn_conn_connected_generating': {'bi': {'19': None}},
                    'mn_conn_connected_charging': {'bi': {'20': None}},
                    'mn_conn_off_available': {'bi': {'21': None}},
                    'mn_conn_off_not_available': {'bi': {'22': None}},
                    'mn_conn_switch_closed_status': {'bi': {'23': None}},
                    'mn_conn_switch_closed_movement': {'bi': {'24': None}}}

alarm_state = {'mn_alm_system_comm_error': {'bi': {'0': None}},
               'mn_alm_priority_1': {'bi': {'1': None}},
               'mn_alm_priority_2': {'bi': {'2': None}},
               'mn_alm_priority_3': {'bi': {'3': None}},
               'mn_alm_storage_chg_max': {'bi': {'4': None}},
               'mn_alm_storage_chg_high': {'bi': {'5': None}},
               'mn_alm_storage_chg_low': {'bi': {'6': None}},
               'mn_alm_storage_chg_depleted': {'bi': {'7': None}},
               'mn_alm_internal_temp_high': {'bi': {'8': None}},
               'mn_alm_internal_temp_low': {'bi': {'9': None}}}

fixed_pf = {'pf_enable': {'bi': {'80': None}},
            'pf': {'ai': {'288': None}},
            'pf_excitation': {'bi': {'29': None}}}

fixed_pf_write = {'pf_enable': {'bo': {'28': None}},
                  'pf': {'ao': {'210': None}},
                  'pf_excitation': {'bo': {'10': None}}}

volt_var_data = {'vv_enable': {'bi': {'81': None}},
                 'vv_vref': {'ai': {'29': None}},
                 'vv_vref_enable': {'bi': {'93': None}},
                 'vv_vref_time': {'ai': {'300': None}},
                 'vv_curve_index': {'ai': {'303': None}},
                 'vv_open_loop_time': {'ai': {'298': None}}}

volt_var_curve = {'vv_enable': {'bo': {'29': None}},
                  'vv_vref': {'ao': {'0': None}},
                  'vv_vref_enable': {'bo': {'41': None}},
                  'vv_vref_time': {'ao': {'220': None}},
                  'vv_open_loop_time': {'ao': {'218': None}}}

reactive_power_data = {'var_enable': {'bi': {'79': None}},
                       'var': {'ai': {'281': None}}}

reactive_power_write = {'var_enable': {'bo': {'27': None}},
                        'var': {'ao': {'203': None}}}

freq_watt_data = {'fw_dbof': {'ai': {'121': None}},
                  'fw_dbuf': {'ai': {'125': None}},
                  'fw_kof': {'ai': {'123': None}},
                  'fw_kuf': {'ai': {'127': None}},
                  'fw_open_loop_time': {'ai': {'131': None}}}

limit_max_power_data = {'watt_enable': {'bi': {'69': None}},
                        'watt': {'ai': {'149': None}}}

limit_max_power_write = {'watt_enable': {'bo': {'17': None}},
                         'watt': {'ao': {'88': None}}}

enter_service_data = {'es_permit_service': {'bi': {'16': None}},
                      'es_volt_high': {'ai': {'50': None}},
                      'es_volt_low': {'ai': {'51': None}},
                      'es_freq_high': {'ai': {'52': None}},
                      'es_freq_low': {'ai': {'53': None}},
                      'es_delay': {'ai': {'54': None}},
                      'es_randomized_delay': {'ai': {'55': None}},
                      'es_ramp_rate': {'ai': {'56': None}}}

enter_service_write = {'es_permit_service': {'bo': {'3': None}},
                       'es_volt_high': {'ao': {'6': None}},
                       'es_volt_low': {'ao': {'7': None}},
                       'es_freq_high': {'ao': {'8': None}},
                       'es_freq_low': {'ao': {'9': None}},
                       'es_delay': {'ao': {'10': None}},
                       'es_randomized_delay': {'ao': {'11': None}},
                       'es_ramp_rate': {'ao': {'12': None}}}

curve_read = {'curve_edit_selector': {'ai': {'328': None}},
              'curve_mode_type': {'ai': {'329': None}},
              'no_of_points': {'ai': {'330': None}},
              'x_value': {'ai': {'331': None}},
              'y_value': {'ai': {'332': None}},
              'x1': {'ai': {'333': None}},
              'y1': {'ai': {'334': None}},
              'x2': {'ai': {'335': None}},
              'y2': {'ai': {'336': None}},
              'x3': {'ai': {'337': None}},
              'y3': {'ai': {'338': None}},
              'x4': {'ai': {'339': None}},
              'y4': {'ai': {'340': None}}}
