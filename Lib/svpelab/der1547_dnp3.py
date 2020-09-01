'''
DER1547 methods defined for the DNP3 devices
'''

import os
from . import der1547
import svpdnp3.device_der_dnp3 as dnp3_agent
import subprocess
import socket
import subprocess

dnp3_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'DNP3'
}

false = False  # Don't remove - required for eval of read_outstation data
true = True  # Don't remove - required for eval of read_outstation data
null = None  # Don't remove - required for eval of read_outstation data


def der1547_info():
    return dnp3_info


def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = dnp3_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'), active_value=mode, glob=True)
    info.param(pname('simulated_outstation'), label='Simulated Outstation?', default='Yes', values=['Yes', 'No'])
    info.param(pname('sim_type'), label='Type of DER Simulation?', default='EPRI DER Simulator',
               values=['EPRI DER Simulator'], active=pname('simulated_outstation'), active_value='Yes')
    info.param(pname('auto_config'), label='Automate Configuration?', default='Yes',
               values=['Yes', 'No'], active=pname('simulated_outstation'), active_value='Yes')
    info.param(pname('dbus_ena'), label='Enable DBus?', default='No', values=['Yes', 'No'],
               active=pname('sim_type'), active_value='EPRI DER Simulator')
    info.param(pname('path_to_dbus'), label='Path to DBUS_CMD.exe',
               default=r'C:\Users\DETLDAQ\Desktop\EPRISimulator\Setup\DBUS_CMD.exe',
               active=pname('dbus_ena'), active_value='Yes')
    info.param(pname('path_to_py'), label='Path to SimController.py',
               default=r'C:\Users\DETLDAQ\Desktop\EPRISimulator\Setup\SimController.py',
               active=pname('sim_type'), active_value='EPRI DER Simulator')
    info.param(pname('path_to_exe'), label='Path to DBUS_CMD.exe',
               default=r'C:\Users\DETLDAQ\Desktop\EPRISimulator\Setup\epri-der-sim-0.1.0.6\epri-der-sim-0.1.0.6\DERSimulator.exe',
               active=pname('sim_type'), active_value='EPRI DER Simulator')
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
        self.simulated_outstation = self.param_value('simulated_outstation')
        if self.simulated_outstation == 'Yes':
            self.sim_type = self.param_value('sim_type')
            self.auto_config = self.param_value('auto_config')
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

        if self.simulated_outstation == 'Yes':
            if self.auto_config == 'Yes':
                if self.sim_type == 'EPRI DER Simulator':
                    from pywinauto.application import Application

                    # Configure EPRI DER Simulator
                    self.ts.log('Running EPRI DER Simulator Setup.  Please wait...')
                    if self.param_value('dbus_ena') == 'Yes':
                        os.system(r'start cmd /k "' + self.param_value('path_to_dbus') + '"')
                        self.ts.sleep(1)
                        # This currently runs in Python 2.7
                        os.system(r'start cmd /k C:\Python27\python.exe "' + self.param_value('path_to_py') + '"')
                        self.ts.sleep(1)

                    try:
                        # connect to DER Simulator app for control
                        app = Application(backend="uia").connect(title_re="DER Simulator")
                    except Exception as e:
                        self.ts.log('Starting DER Simulator')
                        der_sim_start_cmd = r'start cmd /k "' + self.param_value('path_to_exe') + '"'
                        self.ts.log_debug('Using: %s' % der_sim_start_cmd)
                        os.system(der_sim_start_cmd)
                        # sleep 10 seconds to wait for DER Simulator to start
                        self.ts.sleep(10)
                        self.ts.log('Connecting to DER Simulator')
                        app = Application(backend="uia").connect(title_re="DER Simulator")

                    ''' Connect to DNP3 Master'''
                    self.ts.log('Clicking DERMS')
                    app['DER Simulator'].DERMS.click()  # click the DERMS button

                    ''' To create irradiance profile
                    self.ts.log('Clicking ENV')
                    app['DER Simulator'].ENV.click()  # click into ENV button
                    self.ts.log('Browsing to File')
                    app['Environment Settings'].Browse.click()  # click Browse button
                    # add csv file to File name: edit box; assumes this file will be local to Browse button default location
                    self.ts.log('Entering File Name')
                    app['Environment Settings'].Open.child_window(title="File name:", control_type="Edit").set_edit_text(
                        r'EKHIV3_1PVSim1MIN.csv')
                    self.ts.log('Confirming File Name')
                    app['Environment Settings'].Open.OpenButton3.click()
                    # check if Frequency and Voltage buttons are checked; if so, uncheck
                    self.ts.log('Unchecking Freq Toggle')
                    if app['Environment Settings'].Frequency.get_toggle_state():
                        app['Environment Settings'].Frequency.toggle()
                        self.ts.log('Unchecking Voltage Toggle')
                    if app['Environment Settings'].Voltage.get_toggle_state():
                        app['Environment Settings'].Voltage.toggle()
                    self.ts.log('Clicking csv file import and closing')
                    app['Environment Settings'].Import.click()  # import the CSV and close the dialog
                    app['Environment Settings'].Close.click()  # import the CSV and close the dialog
                    '''

                    '''DBus connection for HIL environments
                    self.ts.log('Clicking Co-Sim button')
                    app['DER Simulator']['Co-Sim'].click()
                    # set number of components to 3 and start DBus Client
                    self.ts.log('Setting DBus Components to 3')
                    app['DBus Settings']['Number of ComponentsEdit'].set_edit_text(r'3')
                    self.ts.log('Starting DBus')
                    app['DBus Settings']['Start DBus\r\nClientButton'].click()
                    self.ts.log('Closing DBus')
                    app['DBus Settings'].Close.click()
                    '''

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
        except Exception as e:
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
            self.ts.log('dnp3_agent is not running - attempting to start agent in new cmd window')
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

    def read_dnp3_point_map(self, map_dict):
        """
        Read outstation points

        Translates a DNP3 mapping dict into a point map dict

        points dictionary of format: {'ai': {'PT1': None, 'PT2': None}, 'bi': {'PT3': None}} for the read func.

        :param map_dict: point map in the following format
            monitoring_data = {'mn_active_power': {'ai': {'537': None}},
                               'mn_reactive_power': {'ai': {'541': None}},
                               'mn_voltage': {'ai': {'547': None}},
                               'mn_frequency': {'ai': {'536': None}},
                               'mn_operational_state_of_charge': {'ai': {'48': None}}}

        :return: return_dict = {'mn_active_power': 10000., 'mn_reactive_power': 6542., ...}
        """
        points = {'ai': {}, 'bi': {}}

        # self.ts.log_debug('map_dict.items(): %s' % map_dict.items())
        for key, values in list(map_dict.items()):
            keys1 = list(values.keys())  # ['ai', 'ai', ....]
            val = list(values.values())  # [{'537': None}, {'541': None}, ....]
            for i in val:
                keys2 = list(i.keys())  # ['537', '541']
                for x in keys1:  # ['ai', 'ai', ....]
                    for y in keys2:  # ['537', '541']
                        if x == 'ai':
                            points['ai'][y] = None
                        elif x == 'bi':
                            points['bi'][y] = None

        # Read Outstation Points
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        out_read = agent.read_outstation(self.oid, self.rid, points)
        response = eval(out_read[1:-1])

        # self.ts.log(response)
        # response = {'params': {'ai': {'4': {'value': 10000000.0, 'flags': 1, 'present': True},
        #                               '6': {'value': None, 'flags': 2, 'present': True},
        #                               '8': {'value': None, 'flags': 2, 'present': True},
        #                               '9': {'value': None, 'flags': 2, 'present': True},
        #                               '11': {'value': None, 'flags': 2, 'present': True},
        #                               '14': {'value': 10000000.0, 'flags': 1, 'present': True},
        #                               '22': {'value': 2.0, 'flags': 1, 'present': True},...

        # Populate return dict
        return_dict = {}
        for key, val in map_dict.items():
            return_dict[key] = None

        if 'params' in list(response.keys()):
            for params, ios in list(response.items()):
                io = list(ios.keys())  # ['ai', 'ai', ....]
                num = list(ios.values())  # {'4': {'value': 10000000.0, 'flags': 1, 'present': True}, ...
                for i in num:  # {'4': {'value': 10000000.0, 'flags': 1, 'present': True}, ...
                    keys2 = list(i.keys())  # ['4', '6', ... ]
                    for x in io:  # ['ai', 'ai', ....]
                        for y in keys2:  # ['537', '541']
                            for param_name, decoder in map_dict.items():  # ['mn_active_power', 'mn_reactive_power',...]
                                try:
                                    dummy = decoder[x][y]  # trigger the exception if the param is wrong [x][y]
                                    # self.ts.log_debug('MATCH! param_name=%s' % param_name)
                                    if x == 'ai':
                                        # self.ts.log_debug('x = %s, y = %s, ios[x][y]=%s' % (x, y, ios['ai'][y]))
                                        return_dict[param_name] = ios['ai'][y]['value']
                                    elif x == 'bi':
                                        # self.ts.log_debug('x = %s, y = %s, ios[x][y]=%s' % (x, y, ios['bi'][y]))
                                        return_dict[param_name] = ios['bi'][y]['value']
                                except KeyError as e:
                                    # self.ts.log_debug('No Match! param_name=%s' % param_name)
                                    pass

        # scaling will happen back in main method
        # self.ts.log_debug('return_dict = %s' % return_dict)
        return return_dict

    def write_dnp3_point_map(self, map_dict, write_pts):
        """
        Write points to the outstation.

        The method translates a DNP3 mapping dict into a point map dict for writing to the outstation.
        This method moves the 'enable' parameter to the end of the write list.

        Either exclude_list or include_list should be None.

        :param map_dict: point map in the following format
            map_dict = {'pf_enable': {'bo': {'28': None}},
                        'pf': {'ao': {'210': None}},
                        'pf_excitation': {'bo': {'10': None}}}
        :param write_pts: params dict {'pf_enable': True, 'pf': 0.85}
        :return: dictionary of format: {'pf_enable': 'SUCCESS, 'pf_excitation': 'NOT_WRITTEN'}.
        """

        points = {'ao': {}, 'bo': {}}
        point_name = []
        pt_coords = []

        # self.ts.log_debug('WRITE map_dict: %s' % map_dict)
        ena_point = None  # ensure the enable point is at the end of the list
        ena_val = None  # ensure the enable point is at the end of the list
        for key, value in list(map_dict.items()):
            if 'ena' in key:  # typically "enable" string in the key
                ena_point = key
                ena_val = value
            else:
                point_name.append(key)  # ['pf', ...]
                pt_coords.append(value)  # [{'bo': {'28': None}}, {'ao': {'210': None}}, ...]
        if ena_point is not None and ena_val is not None:
            point_name.append(ena_point)  # ['pf', ..., 'pf_enable']
            pt_coords.append(ena_val)  # [{'ao': {'210': None}}, ..., {'bo': {'28': None}}]

        # self.ts.log_debug('point_name: %s' % point_name)
        # self.ts.log_debug('pt_coords: %s' % pt_coords)
        # self.ts.log_debug('exclude_list: %s' % exclude_list)
        # self.ts.log_debug('include_list: %s' % include_list)

        for x in range(0, len(point_name)):  # ['pf', ..., 'pf_enable']
            key = list(map_dict[point_name[x]].keys())  # ['bo', 'ao', ...]
            val = list(map_dict[point_name[x]].values())  # [{'28': None}, {'210': None}, ...]
            for i in key:  # ['bo', 'ao', ...]
                for j in val:  # [{'28': None}, {'210': None}, ...]
                    key2 = list(j.keys())  # ['28', '210', ...]
                    for y in key2:  # ['28', '210', ...]
                        try:
                            # self.ts.log_debug('write_pts: %s' % write_pts)
                            # self.ts.log_debug('write_pts[point_name[x]]: %s' % write_pts[point_name[x]])
                            points[i][y] = write_pts[point_name[x]]  # {'ai': {'1': None, '2': None}, }
                            # self.ts.log_debug('points: %s' % points)
                        except KeyError as e:
                            # self.ts.log_error('Writing points %s. No key or value for: %s' % (write_pts, e))
                            pass

        # self.ts.log_debug('points: %s' % points)

        # write points
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        write_output = agent.write_outstation(self.oid, self.rid, points)
        response = eval(write_output[1:-1])
        # response: {'params': {'points': {'ao': {'88': {'status': 'SUCCESS'}},
        #                                  'bo': {'17': {'state': 'SUCCESS'}}}}}

        write_status = write_pts.copy()  # initialize with keys from params
        write_status = dict.fromkeys(write_status, 'NOT WRITTEN')  # set all values to 'NOT WRITTEN'
        # self.ts.log_debug('write_status: %s' % write_status)

        if 'params' in list(response.keys()):
            for params, pts in response.items():
                points = list(pts.values())  # {'ao': {'88': {'status': 'SUCCESS'}}, 'bo': {'17': {'state': 'SUCCESS'}}}
                # self.ts.log_debug('points = %s' % points)
                for io_dict in points:  # ios = ['ao', 'bo', ... ], nums = [{'88': {'status': 'SUCCESS'}}]
                    # self.ts.log_debug('io_dict = %s' % (io_dict))
                    for io, num_data in io_dict.items():
                        for num in num_data:
                            # self.ts.log_debug('io = %s, num = %s' % (io, num))
                            for param_name, decoder in map_dict.items():  # ['mn_active_power', 'mn_reactive_power',...]
                                try:
                                    dummy = decoder[io][num]  # trigger the exception if the param is wrong [x][y]
                                    # self.ts.log_debug('MATCH! param_name=%s' % param_name)
                                    # self.ts.log_debug('io = %s, num = %s, num_data[num]=%s' %
                                    #                   (io, num, num_data[num]))
                                    if 'status' in num_data[num]:
                                        write_status[param_name] = num_data[num]['status']
                                    elif 'state' in num_data[num]:
                                        write_status[param_name] = num_data[num]['state']
                                    else:
                                        write_status[param_name] = 'UNKNOWN'
                                except KeyError as e:
                                    # self.ts.log_debug('No Match! param_name=%s' % param_name)
                                    pass

        # self.ts.log_debug('OUTPUT write_status: %s' % write_status)
        return write_status

    def build_sub_dict(self, dictionary=None, new_name=None, keys=None):
        """
        Set dict values into sub dict for easier visualization and analysis, for instance,

            a = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
            a = build_sub_dict(dictionary=a, new_name='sub', keys=['a', 'd'])
            a --> {'sub': {'a': 1, 'd': 4}, 'b': 2, 'c': 3}

        :param dictionary: origional dict
        :param new_name: dictionary key
        :param keys: keys from the original dict to be moved under the new_name

        :return: new dictionary with internal dict
        """

        if dictionary is None or new_name is None or keys is None:
            self.ts.log_warning('build_sub_dict did not have all the necessary parameters. Returning None.')
            return dictionary

        # restructure with dict hierarchy
        dictionary[new_name] = {}
        for key in keys:
            if key in dictionary:
                dictionary[new_name][key] = dictionary[key]
                dictionary.pop(key)  # remove the original key-value pair
            else:
                dictionary[new_name][key] = None
                # self.ts.log_warning('Setting [%s][%s] to None' % (new_name, key))

        return dictionary

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
        Apparent power charge maximum rating                    np_apparent_power_charge_max            KVA
        AC voltage nominal rating                               np_ac_v_nom                             Vac
        AC voltage maximum rating                               np_ac_v_max_er_max                      Vac
        AC voltage minimum rating                               np_ac_v_min_er_min                      Vac
        Supported control mode functions                        np_supported_modes (dict)               str list
            e.g., ['CONST_PF', 'QV', 'QP', 'PV', 'PF']
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

        # Read Outstation Points
        dnp3_pts = {**nameplate_data.copy(), **nameplate_support.copy()}
        nameplate_pts = self.read_dnp3_point_map(dnp3_pts)
        # self.ts.log_debug('nameplate_pts = %s' % nameplate_pts)

        # Scaling
        if nameplate_pts['np_p_max'] is not None:
            nameplate_pts['np_p_max'] /= 1000.  # kW
        if nameplate_pts['np_p_max_over_pf'] is not None:
            nameplate_pts['np_p_max_over_pf'] /= 1000.  # kW
        if nameplate_pts['np_p_max_under_pf'] is not None:
            nameplate_pts['np_p_max_under_pf'] /= 1000.  # kW
        if nameplate_pts['np_va_max'] is not None:
            nameplate_pts['np_va_max'] /= 1000.  # kVA
        if nameplate_pts['np_q_max_inj'] is not None:
            nameplate_pts['np_q_max_inj'] /= 1000.  # kVAr
        if nameplate_pts['np_q_max_abs'] is not None:
            nameplate_pts['np_q_max_abs'] /= 1000.  # kVAr
        if nameplate_pts['np_p_max_charge'] is not None:
            nameplate_pts['np_p_max_charge'] /= 1000.  # kW
        if nameplate_pts['np_apparent_power_charge_max'] is not None:
            nameplate_pts['np_apparent_power_charge_max'] /= 1000.  # kVA

        nameplate_pts = self.build_sub_dict(dictionary=nameplate_pts,
                                            new_name='np_support',
                                            keys=list(nameplate_support.keys()))

        return nameplate_pts

    def get_settings(self):
        """
        Get settings information

        :return: params dict with keys shown in nameplate.
        """
        return self.get_nameplate()

    def set_settings(self, params=None):
        """
        Set settings information

        :return: params dict with keys shown in nameplate.
        """
        return self.set_configuration(params)

    def get_configuration(self):
        """
        Get configuration information

        :return: params dict with keys shown in nameplate.
        """
        return self.get_nameplate()

    def set_configuration(self, params=None):
        """
        Set configuration information. params are those in get_nameplate().
        """

        # nameplate_pts = {**nameplate_data_write.copy(), **nameplate_support_write.copy()}
        # return self.write_dnp3_point_map(map_dict=nameplate_pts, write_pts=params)

        return {}  # no write BO/AO for nameplate points in DNP3

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

        # Read Outstation Points
        dnp3_pts = {**monitoring_data.copy(), **operational_state.copy(),
                    **connection_state.copy(), **alarm_state.copy()}
        monitoring_pts = self.read_dnp3_point_map(dnp3_pts)

        # Scaling
        if monitoring_pts['mn_w'] is not None:
            monitoring_pts['mn_w'] /= 1000.  # kW
        if monitoring_pts['mn_var'] is not None:
            monitoring_pts['mn_var'] /= 1000.  # kVar
        if monitoring_pts['mn_v'] is not None:
            monitoring_pts['mn_v'] /= 10.  # V
        if monitoring_pts['mn_hz'] is not None:
            monitoring_pts['mn_hz'] /= 100.

        # Build hierarchy
        monitoring_pts = self.build_sub_dict(monitoring_pts, new_name='mn_st', keys=list(operational_state.keys()))
        monitoring_pts = self.build_sub_dict(monitoring_pts, new_name='mn_conn', keys=list(connection_state.keys()))
        monitoring_pts = self.build_sub_dict(monitoring_pts, new_name='mn_alrm', keys=list(alarm_state.keys()))

        return monitoring_pts

    def get_const_pf(self):
        """
        Get Constant Power Factor Mode control settings. IEEE 1547-2018 Table 30.
        ________________________________________________________________________________________________________________
        Parameter                                               params dict key                     units
        ________________________________________________________________________________________________________________
        Constant Power Factor Mode Select                       const_pf_mode_enable_as             bool (True=Enabled)
        Constant Power Factor Excitation                        const_pf_excitation_as              str ('inj', 'abs')
        Constant Power Factor Absorbing Setting                 const_pf_abs_as                     VAr p.u
        Constant Power Factor Injecting Setting                 const_pf_inj_as                     VAr p.u
        Maximum response time to maintain constant power        const_pf_olrt_as                    s
            factor. (Not in 1547)

        :return: dict with keys shown above.

        Sign convention
        Generating/Discharging (+)  PFExt = BO10 = <0> Injecting VArs   Q1  PF setpoint = AO210
        Generating/Discharging(+)   PFExt = BO10 = <1> Asorbing VArs    Q4  PF setpoint = AO210
        Charging (-)                PFExt = BO11 = <0> Injecting VArs   Q2  PF setpoint = AO211
        Charging (-)                PFExt = BO11 = <1> Absorbing VArs   Q3  PF setpoint = AO211
        """

        pf_pts = self.read_dnp3_point_map(fixed_pf.copy())
        # self.ts.log_debug('pf_pts = %s' % pf_pts)

        # Scale and put values in 1547 keys
        if 'const_pf_excitation_as' in pf_pts:
            if pf_pts['const_pf_excitation_as']:  # TODO: verify sign
                pf_pts['const_pf_excitation_as'] = 'abs'
                if 'const_pf_as' in pf_pts:
                    # pf_pts['const_pf_abs_as'] = abs(pf_pts['const_pf_as']) / 100.  # pf
                    pf_pts['const_pf_abs_as'] = abs(pf_pts['const_pf_as'])  # pf
                    del pf_pts['const_pf_as']
            else:
                pf_pts['const_pf_excitation_as'] = 'inj'
                if 'const_pf_as' in pf_pts:
                    # pf_pts['const_pf_inj_as'] = abs(pf_pts['const_pf_as']) / 100.  # pf
                    pf_pts['const_pf_inj_as'] = abs(pf_pts['const_pf_as'])  # pf
                    del pf_pts['const_pf_as']

        return pf_pts

    def set_const_pf(self, params=None):
        """
        Set Constant Power Factor Mode control settings.
        ________________________________________________________________________________________________________________
        Parameter                                               params dict key                     units
        ________________________________________________________________________________________________________________
        Constant Power Factor Mode Select                       const_pf_mode_enable_as             bool (True=Enabled)
        Constant Power Factor Excitation                        const_pf_excitation_as              str ('inj', 'abs')
        Constant Power Factor Absorbing Setting                 const_pf_abs_as                     VAr p.u
        Constant Power Factor Injecting Setting                 const_pf_inj_as                     VAr p.u
        Maximum response time to maintain constant power        const_pf_olrt_as                    s
            factor. (Not in 1547)

        :return: dict with keys shown above.

        Sign convention
        Generating/Discharging (+)  PFExt = BO10 = <0> Injecting VArs   Q1  PF setpoint = AO210
        Generating/Discharging(+)   PFExt = BO10 = <1> Asorbing VArs    Q4  PF setpoint = AO210
        Charging (-)                PFExt = BO11 = <0> Injecting VArs   Q2  PF setpoint = AO211
        Charging (-)                PFExt = BO11 = <1> Absorbing VArs   Q3  PF setpoint = AO211
        """
        pf_pts = {**fixed_pf_write.copy()}

        if 'const_pf_excitation_as' in params:
            if params['const_pf_excitation_as'] == 'inj':
                params['const_pf_excitation_as'] = False
            elif params['const_pf_excitation_as'] == 'abs':
                params['const_pf_excitation_as'] = True
            else:
                self.ts.log_warning('const_pf_excitation_as is not "inj" or "abs"')
        else:
            if 'const_pf_mode_enable_as' in params:
                if params['const_pf_mode_enable_as']:
                    self.ts.log_warning('No const_pf_excitation_as provided. Assuming absorption (positive value).')

        # Apply scaling and overload the PF value
        if 'const_pf_abs_as' in params:
            if params['const_pf_abs_as'] < -1. or params['const_pf_abs_as'] > 1.:  # should be 0.0 to 1.0
                self.ts.log_warning('const_pf_abs_as value outside of -1 to 1 pf')
            # overloading this parameter point (both const_pf_inj_as and const_pf_abs_as map here)
            params['const_pf_as'] = int(params['const_pf_abs_as']*100.)  # from pf to pf*100, excit handles sign
            del params['const_pf_abs_as']

        if 'const_pf_inj_as' in params:
            if params['const_pf_inj_as'] < -1. or params['const_pf_inj_as'] > 1.:  # should be 0.0 to 1.0
                self.ts.log_warning('const_pf_inj_as value outside of -1 to 1 pf')
            # overloading this parameter point (both const_pf_inj_as and const_pf_abs_as map here)
            params['const_pf_as'] = int(params['const_pf_inj_as']*100.)  # from pf to pf*100, excit handles sign
            del params['const_pf_inj_as']

        # self.ts.log_debug('pf_pts = %s, params = %s' % (pf_pts, params))
        return self.write_dnp3_point_map(map_dict=pf_pts, write_pts=params)

    def get_qv(self):
        '''
        This information is used to get functional and mode settings for the
        Voltage-Reactive Power Mode. This information may be read.
        '''

        volt_var_pts = volt_var_data.copy()
        volt_var_pts.update(curve_read.copy())

        resp = self.read_dnp3_point_map(volt_var_pts)

        volt_var_read = agent.read_outstation(self.oid, self.rid, points)
        res = eval(volt_var_read[1:-1])
        if 'params' in list(res.keys()):
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
    def set_qv(self, params=None):
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

        for key, value in list(params.items()):
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

        if 'params' in list(res1.keys()):
            resp1 = res1['params']['points']
            v_key = list(points_v['ao'].keys())
            for i in range(0, no_points):
                points['V-Point%s' % str(i + 1)] = resp1['ao'][v_key[i]]

        if 'params' in list(res2.keys()):
            resp2 = res2['params']['points']
            q_key = list(points_q['ao'].keys())
            for i in range(0, no_points):
                points['Q-Point%s' % str(i + 1)] = resp2['ao'][q_key[i]]

        return points

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
        Constant Reactive Power (RofA not specified in 1547)    const_q_abs_er_max                  VAr p.u.
            Absorbing Reactive Power Setting.  Per unit value
            based on NP Qmax Abs. Negative signs should not be
            used but if present indicate absorbing VAr.
        Constant Reactive Power (RofA not specified in 1547)    const_q_inj_er_max                  VAr p.u.
            Injecting Reactive Power (minimum RofA)  Per unit
            value based on NP Qmax Inj. Positive signs should
            not be used but if present indicate Injecting VAr.
        Maximum Response Time to maintain constant reactive     const_q_olrt_er_min                 s
            power (not specified in 1547)
        Maximum Response Time to maintain constant reactive     const_q_olrt_as                     s
            power (not specified in 1547)
        Maximum Response Time to maintain constant reactive     const_q_olrt_er_max                 s
            power(not specified in 1547)

        :return: dict with keys shown above.
        """

        # Read Outstation Points
        dnp3_pts = reactive_power_data.copy()
        reactive_power_pts = self.read_dnp3_point_map(dnp3_pts)

        if reactive_power_pts['const_q_as'] is not None:
            reactive_power_pts['const_q_as'] /= 1000.  # scaling from pct*10 to pu

        return reactive_power_pts

    def set_const_q(self, params=None):
        """
        This information is used to update functional and mode settings for the
        Constant Reactive Power Mode. This information may be written.
        """

        reactive_power_pts = reactive_power_write.copy()
        return reactive_power_pts

    def get_conn(self):
        """
        Get Connection

        conn_as = bool for connection
        """

        # Read Outstation Points
        dnp3_pts = conn_data.copy()
        return self.read_dnp3_point_map(dnp3_pts)

    def set_conn(self, params=None):
        """
        This information is used to update functional and mode settings for the
        Constant Reactive Power Mode. This information may be written.

        conn_as = bool for connection
        """

        dnp3_pts = conn_write.copy()
        return self.write_dnp3_point_map(dnp3_pts, write_pts=params)

    def get_pf(self):
        '''
        Get P(f), Frequency-Active Power Mode Parameters

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

        for key, values in list(freq_watt_pts.items()):
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
        if 'params' in list(res.keys()):
            resp = res['params']
            freq_watt_pts['fw_dbof'] = resp['ai']['121']['value']
            freq_watt_pts['fw_dbuf'] = resp['ai']['125']['value']
            freq_watt_pts['fw_kof'] = resp['ai']['123']['value']
            freq_watt_pts['fw_kuf'] = resp['ai']['127']['value']
            freq_watt_pts['fw_open_loop_time'] = resp['ai']['131']['value']
            res['params'] = freq_watt_pts

        return res

    def set_pf(self, params=None):
        """
        This information is used to update functional and mode settings for the
        Frequency-Active Power Mode. This information may be written.
        """
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        freq_watt_pts = {}
        point_name = []
        pt_value = []

        for key, value in list(params.items()):
            point_name.append(key)
            pt_value.append(value)

        for x in range(0, len(point_name)):
            if point_name[x] == 'fw_dbof':
                dbof_val = pt_value[x]
                dbof_pt = {'ao': {'62': dbof_val, '63': dbof_val}}
                dbof_w = agent.write_outstation(self.oid, self.rid, dbof_pt)
                res1 = eval(dbof_w[1:-1])

            if point_name[x] == 'fw_dbuf':
                dbuf_val = pt_value[x]
                dbuf_pt = {'ao': {'66': dbuf_val, '67': dbuf_val}}
                dbuf_w = agent.write_outstation(self.oid, self.rid, dbuf_pt)
                res2 = eval(dbuf_w[1:-1])

            if point_name[x] == 'fw_kof':
                kof_val = pt_value[x]
                kof_pt = {'ao': {'64': kof_val, '65': kof_val}}
                kof_w = agent.write_outstation(self.oid, self.rid, kof_pt)
                res3 = eval(kof_w[1:-1])

            if point_name[x] == 'fw_kuf':
                kuf_val = pt_value[x]
                kuf_pt = {'ao': {'68': kuf_val, '69': kuf_val}}
                kuf_w = agent.write_outstation(self.oid, self.rid, kuf_pt)
                res4 = eval(kuf_w[1:-1])

            if point_name[x] == 'fw_open_loop_time':
                time_val = pt_value[x]
                time_pt = {'ao': {'72': time_val, '73': time_val}}
                time_w = agent.write_outstation(self.oid, self.rid, time_pt)
                res5 = eval(time_w[1:-1])

            if point_name[x] == 'fw_enable':
                enable_val = pt_value[x]
                enable_pt = {'bo': {'26': enable_val}}
                enable_w = agent.write_outstation(self.oid, self.rid, enable_pt)
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
        if 'params' in list(res.keys()):
            resp = res['params']['points']
            if 'ao' in list(resp.keys()):
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

    def get_p_lim(self):
        """
        Get Limit maximum active power - IEEE 1547 Table 40
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          p_lim_mode_enable_as         bool (True=Enabled)
        Maximum Active Power Min                                    p_lim_w_er_min               P p.u.
        Maximum Active Power                                        p_lim_w_as                   P p.u.
        Maximum Active Power Max                                    p_lim_w_er_max               P p.u.
        """

        # Read Outstation Points
        dnp3_pts = limit_max_power_data.copy()
        limit_max_power_pts = self.read_dnp3_point_map(dnp3_pts)

        if limit_max_power_pts['p_lim_w_as'] is not None:
            limit_max_power_pts['p_lim_w_as'] /= 1000.  # scaling from pct*10 to pu

        return limit_max_power_pts

    def set_p_lim(self, params=None):
        """
        Set Limit maximum active power - IEEE 1547 Table 40
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          p_lim_mode_enable_as         bool (True=Enabled)
        Maximum Active Power Min                                    p_lim_w_er_min               P p.u.
        Maximum Active Power                                        p_lim_w_as                   P p.u.
        Maximum Active Power Max                                    p_lim_w_er_max               P p.u.
        """

        limit_max_power_pts = limit_max_power_write.copy()

        # Apply scaling
        if 'p_lim_w_as' in params:
            if params['p_lim_w_as'] < -1. or params['p_lim_w_as'] > 1.:
                self.ts.log_warning('p_lim_w_as value outside of -1 to 1 pu')
            params['p_lim_w_as'] = int(params['p_lim_w_as']*1000.)  # from pu to pct*10

        return self.write_dnp3_point_map(limit_max_power_pts, write_pts=params)

    def get_enter_service(self):
        """
        This information is used to update functional and mode settings for the
        Enter Service Mode. This information may be read.
        """
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        enter_service_pts = enter_service_data.copy()

        points = {'ai': {}, 'bi': {}}
        false = False  # Don't remove - required for eval of read_outstation data
        true = True  # Don't remove - required for eval of read_outstation data
        null = None   # Don't remove - required for eval of read_outstation data

        for key, values in list(enter_service_pts.items()):
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
        if 'params' in list(res.keys()):
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

        for key, value in list(params.items()):
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

        if 'params' in list(res.keys()):
            resp = res['params']['points']
            if 'bo' in list(resp.keys()):
                if '3' in resp['bo']:
                    enter_service_pts['es_permit_service'] = resp['bo']['3']
                else:
                    enter_service_pts['es_permit_service'] = {'state': 'Not Written'}
            if 'ao' in list(resp.keys()):
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

    def get_qp(self):
        """
        Get Q(P) parameters. [Watt-Var]
        """
        pass

    def set_qp(self, params=None):
        """
        Set Q(P) parameters. [Watt-Var]
        """
        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        point_name = []
        pt_value = []

        for key, value in list(params.items()):
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

        if 'params' in list(res1.keys()):
            resp1 = res1['params']['points']
            p_key = list(points_p['ao'].keys())
            for i in range(0, no_points):
                points['P-Point%s' % str(i + 1)] = resp1['ao'][p_key[i]]

        if 'params' in list(res2.keys()):
            resp2 = res2['params']['points']
            q_key = list(points_q['ao'].keys())
            for i in range(0, no_points):
                points['Q-Point%s' % str(i + 1)] = resp2['ao'][q_key[i]]

        return points

    def set_pv(self, params=None):
        """
        Get P(V), Voltage-Active Power (Volt-Watt), Parameters
        """
        pass

    def set_pv(self, params=None):
        """
        Set P(V), Voltage-Active Power (Volt-Watt), Parameters
        """

        agent = dnp3_agent.AgentClient(self.ipaddr, self.ipport)
        agent.connect(self.ipaddr, self.ipport)
        point_name = []
        pt_value = []

        for key, value in list(params.items()):
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

        if 'params' in list(res1.keys()):
            resp1 = res1['params']['points']
            v_key = list(points_v['ao'].keys())
            for i in range(0, no_points):
                points['V-Point%s' % str(i + 1)] = resp1['ao'][v_key[i]]

        if 'params' in list(res2.keys()):
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

        for key, value in list(params.items()):
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

        if 'params' in list(res1.keys()):
            resp1 = res1['params']['points']
            ht_key = list(points_ht['ao'].keys())
            for i in range(0, no_points_hv):
                points['HT-Point%s' % str(i + 1)] = resp1['ao'][ht_key[i]]

        if 'params' in list(res2.keys()):
            resp2 = res2['params']['points']
            hv_key = list(points_hv['ao'].keys())
            for i in range(0, no_points_hv):
                points['HV-Point%s' % str(i + 1)] = resp2['ao'][hv_key[i]]

        if 'params' in list(res3.keys()):
            resp3 = res3['params']['points']
            lt_key = list(points_lt['ao'].keys())
            for i in range(0, no_points_lv):
                points['LT-Point%s' % str(i + 1)] = resp3['ao'][lt_key[i]]

        if 'params' in list(res4.keys()):
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

        for key, value in list(params.items()):
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

        if 'params' in list(res1.keys()):
            resp1 = res1['params']['points']
            ht_key = list(points_ht['ao'].keys())
            for i in range(0, no_points_hf):
                points['HT-Point%s' % str(i + 1)] = resp1['ao'][ht_key[i]]

        if 'params' in list(res2.keys()):
            resp2 = res2['params']['points']
            hf_key = list(points_hf['ao'].keys())
            for i in range(0, no_points_hf):
                points['HF-Point%s' % str(i + 1)] = resp2['ao'][hf_key[i]]

        if 'params' in list(res3.keys()):
            resp3 = res3['params']['points']
            lt_key = list(points_lt['ao'].keys())
            for i in range(0, no_points_lf):
                points['LT-Point%s' % str(i + 1)] = resp3['ao'][lt_key[i]]

        if 'params' in list(res4.keys()):
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

        for key, value in list(params.items()):
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

        if 'params' in list(res1.keys()):
            resp1 = res1['params']['points']
            ht_key = list(points_ht['ao'].keys())
            for i in range(0, no_points_hv):
                points['HT-Point%s' % str(i + 1)] = resp1['ao'][ht_key[i]]

        if 'params' in list(res2.keys()):
            resp2 = res2['params']['points']
            hv_key = list(points_hv['ao'].keys())
            for i in range(0, no_points_hv):
                points['HV-Point%s' % str(i + 1)] = resp2['ao'][hv_key[i]]

        if 'params' in list(res3.keys()):
            resp3 = res3['params']['points']
            lt_key = list(points_lt['ao'].keys())
            for i in range(0, no_points_lv):
                points['LT-Point%s' % str(i + 1)] = resp3['ao'][lt_key[i]]

        if 'params' in list(res4.keys()):
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

        for key, values in list(curve_read_pts.items()):
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
        if 'params' in list(res.keys()):
            resp = res['params']
            curve_read_pts['curve_edit_selector'] = resp['ai']['328']['value']
            curve_read_pts['curve_mode_type'] = resp['ai']['329']['value']
            curve_read_pts['no_of_points'] = resp['ai']['330']['value']
            curve_read_pts['x_value'] = resp['ai']['331']['value']
            curve_read_pts['y_value'] = resp['ai']['332']['value']
            res['params'] = curve_read_pts

        return res


""" ************** Dictionaries for different der1547_dnp3 methods **************** """

'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Nameplate Information (Energy)
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
Active Power Rating at Unity Power Factor   Watts               n/a                 AI4
Active Power Rating at Specified            Watts               n/a                 AI6 - AI7
Over-excited Power Factor
Specified Over-excited Power Factor         Unitless            n/a                 AI8
Active Power Rating at Specified            Watts               n/a                 AI9 - AI10
Underexcited Power Factor 
Specified Under-excited Power Factor        Unitless            n/a                 AI11
Reactive Power Injected Maximum Rating      VArs                n/a                 AI12
Reactive Power Absorbed Maximum Rating      VArs                n/a                 AI13
Active Power Charge Maximum Rating          Watts               n/a                 AI5
Apparent Power Charge Maximum Rating        VA                  n/a                 AI15
Storage Actual Capacity                     Wh                  n/a                 AI16

Category: Nameplate Information (RMS)
AC Voltage Nominal Rating                   RMS Volts           n/a                 AI29 - AI30
AC Voltage Maximum Rating                   RMS Volts           n/a                 AI3
AC Voltage Minimum Rating                   RMS Volts           n/a                 AI2
AC Current Maximum Rating                   RMS Amperes         n/a                 AI19 - AI20

Category: Namplate Information (other)
Supported Control Mode Functions            List of Yes/No      n/a                 BI31 - BI51
Normal operating performance category       A/B                 n/a                 AI22
Abnormal operating performance category     I/II/III            n/a                 AI23
Reactive Susceptance that remains connected Siemens             n/a                 AI21
Manufacturer                                Text                n/a                 Refer to 2.4.1
Model                                       Text                n/a                 Refer to 2.4.1
Serial Number                               Text                n/a                 Refer to 2.4.1
Version                                     Text                n/a                 Refer to 2.4.1
'''


nameplate_data = {'np_p_max': {'ai': {'4': None}},
                  'np_p_max_over_pf': {'ai': {'6': None}},
                  'np_over_pf': {'ai': {'8': None}},
                  'np_p_max_under_pf': {'ai': {'9': None}},
                  'np_under_pf': {'ai': {'11': None}},
                  'np_va_max': {'ai': {'14': None}},
                  'np_normal_op_cat': {'ai': {'22': None}},
                  'np_abnormal_op_cat': {'ai': {'23': None}},
                  # 'np_intentional_island_cat': {'ai': {'23': None}},
                  'np_q_max_inj': {'ai': {'12': None}},
                  'np_q_max_abs': {'ai': {'13': None}},
                  'np_p_max_charge': {'ai': {'5': None}},
                  'np_apparent_power_charge_max': {'ai': {'15': None}},
                  'np_ac_v_nom': {'ai': {'29': None}},
                  'np_ac_v_min_er_min': {'ai': {'2': None}},
                  'np_ac_v_max_er_max': {'ai': {'3': None}},
                  # 'np_remote_meter_resistance': {'ai': {'3': None}},
                  # 'np_remote_meter_reactance': {'ai': {'3': None}},
                  # 'np_manufacturer': {'ai': {'3': None}},
                  # 'np_model': {'ai': {'3': None}},
                  # 'np_serial_num': {'ai': {'3': None}},
                  # 'np_fw_ver': {'ai': {'3': None}},
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

'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Monitored Information
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
Active Power                                Watts               n/a                 AI537
Reactive Power                              VArs                n/a                 AI541
Voltage                                     Volts               n/a                 AI547 - AI553
Current                                     Amps                n/a                 AI554 - AI556
Frequency                                   Hz                  n/a                 AI536
Operational State / Connection Status       On/Off/others…      n/a                 BI10 - BI24
Alarm Status                                Alarm / No-Alarm    n/a                 BI0 - BI9
Operational State of Charge                 Percent             n/a                 AI48
'''

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

monitoring_data = {'mn_w': {'ai': {'537': None}},
                   'mn_var': {'ai': {'541': None}},
                   'mn_v': {'ai': {'547': None}},
                   'mn_hz': {'ai': {'536': None}},
                   'mn_soc_pct': {'ai': {'48': None}},
                   'mn_conn': {'bi': {'23': None}}}

"""
BI10 System Is In Local State. System has been locked by a local operator which prevents other operators from
executing commands. Note: Local State is also sometimes referred to as Maintenance State. Local State overrides
Lockout State.  1 = System in local state

BI11 System Is In Lockout State. System has been locked by an operator such that other perators may not
execute commands. Lockout State is also sometimes referred to as Blocked State. 1 = System locked out

BI12 System Is Starting Up. Set to 1 when a BO "System Initiate Start-up Sequence" command has been received. 
1 = Start command has been received.

BI13 System Is Stopping. Set to 1 when an BO "System Execute Stop" command has been received.
1 = Emergency Stop command has been received.

BI14 System is Started (Return to Service). If any of the DER Units are started, then true. DER Units in the
maintenance operational state are excluded. 1 = Started

BI15 System is Stopped (Cease to Energize). If all of the DER Units are stopped, then true. DER Units in the
maintenance operational state are excluded. 1 = Stopped

BI16 System Permission to Start Status. 1 = Start Permission Granted

BI17 System Permission to Stop Status. 1 = Stop Permission Granted

BI18 DER is Connected and Idle. 1 = Idle-Connected

BI19 DER is Connected and Generating. 1 = On-Connected

BI20 DER is Connected and Charging. 1 = On-Charging-Connected

BI21 DER is Off but Available to Start. 1 = Off-Available

BI22 DER is Off and Not Available to Start. 1 = Off-Not-Available

BI23 DER Connect/Disconnect Switch Closed Status. 1 = Closed

BI24 DER Connect/Disconnect Switch Movement Status. 1 = Moving

BI25  Islanded Mode. Determines how the DER behaves when in an Islanded configuration.
  <0> Isochronous Mode. DER attempts to control voltage and frequency independent of configured curves and settings
  up to the limits of the machine's capabilities in order to achieve the AO Reference Voltage and AO nominal frequency.
  <1> Droop Mode. DER acts as a follower using Volt/VAR and Freq/Watt curves.

"""

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
"""
BI0 - System Communication Error
BI1 - System Has Priority 1 Alarms
BI2 - System Has Priority 2 Alarms
BI3 - System Has Priority 3 Alarms
BI4 - Storage State of Charge at Maximum. Maximum Usable State of Charge reached.
BI5 - Storage State of Charge is Too High. Maximum Reserve Percentage (of usable capacity) reached.
BI6 - Storage State of Charge is Too Low. Minimum Reserve Percentage (of usable capacity) reached.
BI7 - Storage State of Charge is Depleted. Minimum Usable State of Charge Reached.
BI8 - Storage Internal Temperature is Too High
BI9 - Storage External (Ambient) Temperature is Too High
"""

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

'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Constant Power Factor Mode
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
Constant Power Factor Enable                On/Off              BO28                BI80
Constant Power Factor                       Unitless            AO210 - AO211       AI288 - AI289
Constant Power Factor Excitation            Over/Under          BO10 - BO11         BI29 - BI30
'''

fixed_pf = {'const_pf_mode_enable_as': {'bi': {'80': None}},
            # 'const_pf_abs_as': {'ai': {'288': None}},
            # 'const_pf_inj_as': {'ai': {'288': None}},
            'const_pf_as': {'ai': {'288': None}},
            'const_pf_excitation_as': {'bi': {'29': None}}}

fixed_pf_write = {'const_pf_mode_enable_as': {'bo': {'28': None}},
                  # 'const_pf_abs_as': {'ao': {'210': None}},
                  # 'const_pf_inj_as': {'ao': {'210': None}},
                  'const_pf_as': {'ao': {'210': None}},
                  'const_pf_excitation_as': {'bo': {'10': None}}}

'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Volt-VAr Mode 
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
Voltage-Reactive Power (Volt-VAr) Enable    On/Off              BO29                BI81
VRef (Reference Voltage)                    Volts               AO0 - AO1           AI29 - AI30
Autonomous VRef Adjustment Enable           On/Off              BO41                BI93
VRef Adjustment Time Constant               Seconds             AO220               AI300
V/Q Curve Points (x,y)                      Volts, VArs         AO217, AO244-AO448  AI303
Open Loop Response Time                     Seconds             AO218 - AO219       AI298 - AI299
'''

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

'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Constant VAr Mode
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
Constant Reactive Power Mode Enable         On/Off              BO27                BI79
Constant Reactive Power                     VArs                AO203               AI281
'''

"""
Get Constant Reactive Power Mode
______________________________________________________________________________________________________________
Parameter                                               params dict key                     units
______________________________________________________________________________________________________________
Constant Reactive Power Mode Enable                     const_q_mode_enable_as              bool (True=Enabled)
Constant Reactive Power Excitation (not specified in    const_q_mode_excitation_as          str ('inj', 'abs')
    1547)
Constant Reactive power setting (See Table 7)           const_q_as                          VAr p.u.
Constant Reactive Power (RofA not specified in 1547)    const_q_abs_er_max                  VAr p.u.
    Absorbing Reactive Power Setting.  Per unit value
    based on NP Qmax Abs. Negative signs should not be
    used but if present indicate absorbing VAr.
Constant Reactive Power (RofA not specified in 1547)    const_q_inj_er_max                  VAr p.u.
    Injecting Reactive Power (minimum RofA)  Per unit
    value based on NP Qmax Inj. Positive signs should
    not be used but if present indicate Injecting VAr.
Maximum Response Time to maintain constant reactive     const_q_olrt_er_min                 s
    power (not specified in 1547)
Maximum Response Time to maintain constant reactive     const_q_olrt_as                     s
    power (not specified in 1547)
Maximum Response Time to maintain constant reactive     const_q_olrt_er_max                 s
    power(not specified in 1547)

:return: dict with keys shown above.
"""

reactive_power_data = {'const_q_mode_enable_as': {'bi': {'79': None}},
                       'const_q_as': {'ai': {'281': None}}}

reactive_power_write = {'const_q_mode_enable_as': {'bo': {'27': None}},
                        'const_q_as': {'ao': {'203': None}}}

'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Frequency Droop (Frequency-Watt)
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
Over-frequency Droop Deadband DBOF          Hz                  AO62 - AO63         AI121 - AI122
Under-frequency Droop Deadband DBUF         Hz                  AO66 - AO67         AI125 - AI126
Over-frequency Droop Slope KOF Watts per    Hz                  AO64 - AO65         AI123 - AI124
Under-frequency Droop Slope KUF Watts per   Hz                  AO68 - AO69         AI127 - AI128
Open Loop Response Time                     Seconds             AO72 - AO73         AI131 - AI132

'''

freq_watt_data = {'fw_dbof': {'ai': {'121': None}},
                  'fw_dbuf': {'ai': {'125': None}},
                  'fw_kof': {'ai': {'123': None}},
                  'fw_kuf': {'ai': {'127': None}},
                  'fw_open_loop_time': {'ai': {'131': None}}}

'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Active Power 
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
Limit Active Power Enable                   On/Off              BO17                BI69
Limit Mode Maximum Active Power             Watts (pct)         AO87 - AO88         AI148 - AI149
'''

limit_max_power_data = {'p_lim_mode_enable_as': {'bi': {'69': None}},
                        'p_lim_w_as': {'ai': {'149': None}}}

limit_max_power_write = {'p_lim_mode_enable_as': {'bo': {'17': None}},
                         'p_lim_w_as': {'ao': {'88': None}}}


'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Enter Service 
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
Permit service                              Enabled/Disabled    BO3                 BI16
ES Voltage High                             Percent Nominal     AO6                 AI50
ES Voltage Low                              Percent Nominal     AO7                 AI51
ES Frequency High                           Hz                  AO8                 AI52
ES Frequency Low                            Hz                  AO9                 AI53
ES Delay                                    Seconds             AO10                AI54
ES Randomized Delay                         Seconds             AO11                AI55
ES Ramp Rate                                Seconds             AO12                AI56
'''

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


'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Watt-VAr Mode 
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
Active Power-Reactive Power (Watt-VAr)      On/Off              BO30                BI82
Enable
P/Q Curve Points (x,y)                      Watts, VArs         AO226, AO244-AO448  AI308, AI328-AI532
'''
watt_var_data = {'watt_var_enable': {'bi': {'82': None}}}

watt_var_write = {'watt_var_enable': {'bo': {'30': None}}}

'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Volt-Watt Mode 
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
Voltage-Active Power Mode Enable            On/Off              BO25                BI77
V/P Curve Points (x,y)                      Volts, Watts        AO173, AO244-AO44   AI248, AI328 - AI532
Open Loop Response Time                     Seconds             AO175 - AO176       AI251 - AI252
'''
volt_watt_data = {'vw_enable': {'bi': {'177': None}},
                  'vw_open_loop_time': {'ai': {'251': None}}}

volt_watt_write = {'vw_enable': {'bo': {'25': None}},
                   'vw_open_loop_time': {'ao': {'175': None}}}

'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Voltage Trip
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
HV Trip Curve Points (x,y)                  Seconds, Volts      AO23, AO244-AO448   AI73, AI328 - AI532
LV Trip Curve Points (x,y)                  Seconds, Volts      AO24, AO244-AO448   AI74, AI328 - AI532
'''

'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Momentary Cessation
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
HV Momentary Cessation Curve Points (x,y)   Seconds, Volts      AO25, AO244-AO448   AI75, AI328 - AI532
LV Momentary Cessation Curve Points (x,y)   Seconds, Volts      AO26, AO244-AO448   AI76, AI328 - AI532
Frequency Trip HF Trip Curve Points (x,y)   Seconds, Hz         AO28, AO244-AO448   AI79, AI328 - AI532
LF Trip Curve Points (x,y)                  Seconds, Hz         AO29, AO244-AO448   AI80, AI328 - AI532
'''

'''
Table 29 – Steps to perform a Connect/Disconnect DER
Step    Description         Optionality     Function Codes              Data Type   Point Number    Read-back Point
1. Set time window          Optional        Direct Operate / Response   AO          AO16            AI60
2. Set reversion timeout    Optional        Direct Operate / Response   AO          AO17            AI61
3. Retrieve status of       Optional        Read / Response or          BI          BI23            n/a
switch                                      Unsolicited Response
4. Issue switch control     Required        Select / Response,          BO          BO5             BI23
command and receive                         Operate / Response
response
5. Detect if switch is  Optional            Read / Response or          BI          BI24            n/a
moving                                      Unsolicited Response
'''

conn_data = {'conn_as': {'bi': {'21': None}}}
conn_write = {'conn_as': {'bo': {'5': None}}}

