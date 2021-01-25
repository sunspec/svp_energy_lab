'''
DER1547 methods defined for the DNP3 devices
'''

import os
from . import der1547
import svpdnp3.device_der_dnp3 as dnp3_agent
import subprocess
import socket

dnp3_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'DNP3'
}

false = False  # Don't remove - required for eval of read_outstation data
true = True  # Don't remove - required for eval of read_outstation data
null = None  # Don't remove - required for eval of read_outstation data

# Independent (X-Value) Units for Curve. Enumeration:  (AO247)
# <0> Curve disabled
# <1> Not applicable / Unknown
# <4> Time
# <29> Voltage
# <33> Frequency
# <38> Watts
# <23> Celsius Temperature
# <100> Price in hundredths of
# local currency
# <129> Percent Voltage
# <133> Percent Frequency
# <138> Percent Watts
# <233> Frequency Deviation
# <234+> Other
X_ENUM = {0: 'Disabled',
          1: 'NA',
          4: 'Time',
          29: 'Voltage',
          33: 'Frequency',
          38: 'Watts',
          23: 'Temperature',
          100: 'Price',
          129: 'Volt_Pct',
          133: 'Freq_Pct',
          138: 'Watts_Pct',
          233: 'Freq_Delta',
          234: 'Other',
          'Disabled': 0,
          'NA': 1,
          'Time': 4,
          'Voltage': 29,
          'Frequency': 33,
          'Watts': 38,
          'Temperature': 23,
          'Price': 100,
          'Volt_Pct': 129,
          'Freq_Pct': 133,
          'Watts_Pct': 138,
          'Freq_Delta': 233,
          'Other': 233}

# Dependent (Y-Value) Units for Curve. Enumeration:  (AO248)
# <0> Curve disabled
# <1> Not applicable / unknown
# <2> VArs as percent of max VArs (VARMax)
# <3> VArs as percent of max available VArs (VArAval)
# <4> Vars as percent of max Watts (Wmax) – not used
# <5> Watts as percent of max Watts (Wmax)
# <6> Watts as percent of frozen active power (DeptSnptRef)
# <7> Power Factor in EEI notation
# <8> Volts as a percent of the nominal voltage (VRef)
# <9> Frequency as a percent of the nominal grid frequency (ECPNomHz)
# <99+> Other
Y_ENUM = {0: 'Disabled',
          1: 'NA',
          2: 'VArMax',
          3: 'VArAval',
          4: 'VArWmax',
          5: 'WMaxPct',
          6: 'WMaxPctFrozen',
          7: 'PF',
          8: 'Volt_Pct',
          9: 'Freq_Pct',
          99: 'Other',
          'Disabled': 0,
          'NA': 1,
          'VArMax': 2,
          'VArAval': 3,
          'VArWmax': 4,
          'WMaxPct': 5,
          'WMaxPctFrozen': 6,
          'PF': 7,
          'Volt_Pct': 8,
          'Freq_Pct': 9,
          'Other': 99}

# Curve Mode Type. Enumeration: (AO245)
# <0> Curve disabled
# <1> Not applicable / Unknown
# <2> Volt-Var modes
# <3> Frequency-Watt mode
# <4> Watt-VAr mode
# <5> Voltage-Watt modes
# <6> Remain Connected
# <7> Temperature mode
# <8> Pricing signal mode
# High Voltage ride-through curves
# <9> HVRT Must Trip
# <10> HVRT Momentary Cessation
# Low Voltage ride-through curves
# <11> LVRT Must Trip
# <12> LVRT Momentary Cessation
# High Frequency ride-through curves
# <13> HFRT Must Trip
# <14> HFRT Momentary Cessation
# Low Frequency ride-through curves
# <15> LFRT Must Trip
# <16> LFRT Mandatory Operation

CURVE_MODE = {0: 'Disabled',
              1: 'NA',
              2: 'VV',
              3: 'FW',
              4: 'WV',
              5: 'VW',
              6: 'RemainConnected',
              7: 'TempMode',
              8: 'HVRT_Price',
              9: 'HVRT_Trip',
              10: 'HVRT_MC',
              11: 'LVRT_Trip',
              12: 'LVRT_MC',
              13: 'HFRT_Trip',
              14: 'HFRT_MC',
              15: 'LFRT_Trip',
              16: 'LFRT_MO',
              'Disabled': 0,
              'NA': 1,
              'VV': 2,
              'FW': 3,
              'WV': 4,
              'VW': 5,
              'RemainConnected': 6,
              'TempMode': 7,
              'HVRT_Price': 8,
              'HVRT_Trip': 9,
              'HVRT_MC': 10,
              'LVRT_Trip': 11,
              'LVRT_MC': 12,
              'HFRT_Trip': 13,
              'HFRT_MC': 14,
              'LFRT_Trip': 15,
              'LFRT_MO': 16}


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
    info.param(pname('path_to_exe'), label='Path to DERSimulator.exe',
               default=r'C:\Users\DETLDAQ\Desktop\EPRISimulator\Setup\epri-der-sim-0.1.0.6\
               epri-der-sim-0.1.0.6\DERSimulator.exe',
               active=pname('sim_type'), active_value='EPRI DER Simulator')
    info.param(pname('irr_csv'), label='Irradiance csv filename. (Use "None" for no load.)',
               default=r'None', active=pname('sim_type'), active_value='EPRI DER Simulator')
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
            self.irr_csv = self.param_value('irr_csv')

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
                        # This currently runs in Python 3.7
                        os.system(r'start cmd /k C:\Python37\python.exe "' + self.param_value('path_to_py') + '"')
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

                    # create irradiance profile
                    if self.irr_csv is not r'None':
                        self.ts.log('Clicking ENV')
                        app['DER Simulator'].ENV.click()  # click into ENV button
                        self.ts.sleep(0.5)  # sleep to permit the stop to operate

                        self.ts.log('Browsing to File')
                        app['Environment Settings'].Browse.click()  # click Browse button
                        self.ts.sleep(0.5)  # sleep to permit the stop to operate

                        # add csv file to File name: edit box; assumes this file will be local to Browse button
                        # default location
                        self.ts.log('Entering File Name')
                        app['Environment Settings'].Open.child_window(title="File name:", control_type="Edit").\
                            set_edit_text(self.irr_csv)
                        self.ts.sleep(0.5)  # sleep to permit the stop to operate
                        self.ts.log('Confirming File Name')
                        app['Environment Settings'].Open.OpenButton3.click()
                        self.ts.sleep(0.5)  # sleep to permit the stop to operate

                        # check if Frequency and Voltage buttons are checked; if so, uncheck
                        self.ts.log('Unchecking Freq Toggle')
                        if app['Environment Settings'].Frequency.get_toggle_state():
                            app['Environment Settings'].Frequency.toggle()
                            self.ts.log('Unchecking Voltage Toggle')
                        if app['Environment Settings'].Voltage.get_toggle_state():
                            app['Environment Settings'].Voltage.toggle()
                        self.ts.sleep(0.5)  # sleep to permit the stop to operate

                        self.ts.log('Clicking csv file import and closing')
                        app['Environment Settings'].Import.click()  # import the CSV and close the dialog
                        app['Environment Settings'].Close.click()  # import the CSV and close the dialog
                        self.ts.sleep(0.5)  # sleep to permit the stop to operate

                    # DBus connection for HIL environments
                    if self.param_value('dbus_ena') == 'Yes':
                        self.ts.log('Clicking Co-Sim button')
                        app['DER Simulator']['Co-Sim'].click()
                        self.ts.sleep(0.5)  # sleep to permit the stop to operate

                        # set number of components to 3 and start DBus Client
                        self.ts.log('Setting DBus Components to 3')
                        app['DBus Settings']['Number of ComponentsEdit'].set_edit_text(r'3')
                        self.ts.sleep(0.5)  # sleep to permit the stop to operate

                        self.ts.log('Starting DBus')
                        app['DBus Settings']['Start DBus\r\nClientButton'].click()
                        self.ts.sleep(0.5)  # sleep to permit the stop to operate

                        self.ts.log('Closing DBus')
                        app['DBus Settings'].Close.click()


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

    def write_dnp3_point_map(self, map_dict, write_pts, debug=False):
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

        if debug:
            self.ts.log_debug('point_name: %s' % point_name)
            self.ts.log_debug('pt_coords: %s' % pt_coords)

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
        if debug:
            self.ts.log_debug('points: %s' % points)

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
                                    if debug:
                                        self.ts.log_debug('MATCH! param_name=%s' % param_name)
                                        self.ts.log_debug('io = %s, num = %s, num_data[num]=%s' %
                                                          (io, num, num_data[num]))
                                    if 'status' in num_data[num]:
                                        write_status[param_name] = num_data[num]['status']
                                    elif 'state' in num_data[num]:
                                        write_status[param_name] = num_data[num]['state']
                                    else:
                                        write_status[param_name] = 'UNKNOWN'
                                except KeyError as e:
                                    if debug:
                                        self.ts.log_debug('No Match! param_name=%s' % param_name)
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
            e.g., {'fixed_pf': True 'volt_var': False} with keys:
            Supports Low Voltage Ride-Through Mode: 'lv_trip'
            Supports High Voltage Ride-Through Mode: 'hv_trip'
            Supports Low Freq Ride-Through Mode: 'lf_trip'
            Supports High Freq Ride-Through Mode: 'hf_trip'
            Supports Active Power Limit Mode: 'max_w'
            Supports Volt-Watt Mode: 'volt_watt'
            Supports Frequency-Watt Curve Mode: 'freq_watt'
            Supports Constant VArs Mode: 'fixed_var'
            Supports Fixed Power Factor Mode: 'fixed_pf'
            Supports Volt-VAr Control Mode: 'volt_var'
            Supports Watt-VAr Mode: 'watt_var'
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

        #<0> unknown, <1> Category A, <2> Category B
        if nameplate_pts['np_normal_op_cat'] == 1:
            nameplate_pts['np_normal_op_cat'] = 'CAT_A'
        elif nameplate_pts['np_normal_op_cat'] == 2:
            nameplate_pts['np_normal_op_cat'] = 'CAT_B'
        else:
            nameplate_pts['np_normal_op_cat'] = 'Unknown'

        nameplate_pts = self.build_sub_dict(dictionary=nameplate_pts,
                                            new_name='np_support_dnp3',
                                            keys=list(nameplate_support.keys()))

        ctrl_modes = {}  # rename points with abstraction layer names
        ctrl_modes['max_w'] = nameplate_pts['np_support_dnp3']['np_support_limit_watt']
        ctrl_modes['fixed_w'] = nameplate_pts['np_support_dnp3']['np_support_chg_dischg']
        ctrl_modes['fixed_var'] = nameplate_pts['np_support_dnp3']['np_support_constant_vars']
        ctrl_modes['fixed_pf'] = nameplate_pts['np_support_dnp3']['np_support_fixed_pf']
        ctrl_modes['volt_var'] = nameplate_pts['np_support_dnp3']['np_support_volt_var_control']
        ctrl_modes['freq_watt'] = nameplate_pts['np_support_dnp3']['np_support_freq_watt']
        ctrl_modes['dyn_react_curr'] = nameplate_pts['np_support_dnp3']['np_support_dynamic_reactive_current']
        ctrl_modes['lv_trip'] = nameplate_pts['np_support_dnp3']['np_support_volt_ride_through']
        ctrl_modes['hv_trip'] = nameplate_pts['np_support_dnp3']['np_support_volt_ride_through']
        ctrl_modes['watt_var'] = nameplate_pts['np_support_dnp3']['np_support_watt_var']
        ctrl_modes['volt_watt'] = nameplate_pts['np_support_dnp3']['np_support_volt_watt']
        ctrl_modes['lf_trip'] = nameplate_pts['np_support_dnp3']['np_support_freq_ride_through']
        ctrl_modes['hf_trip'] = nameplate_pts['np_support_dnp3']['np_support_freq_ride_through']
        nameplate_pts['np_supported_modes'] = ctrl_modes
        del nameplate_pts['np_support_dnp3']  # remove dnp3 keys
        # Unused points
        # np_support_coordinated_chg_dischg
        # np_support_active_pwr_response_1
        # np_support_active_pwr_response_2
        # np_support_active_pwr_response_3
        # np_support_automation_generation_control
        # np_support_active_pwr_smoothing
        # np_support_dynamic_volt_watt
        # np_support_freq_watt_curve
        # np_support_pf_correction
        # np_support_pricing

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
        self.ts.log_warning('NO DNP3 APP NOTE AO/BO CONFIGURATION POINTS EXIST!')
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

        Operational State                                           mn_st                              bool
            'On': True, DER operating (e.g., generating)
            'Off': False, DER not operating

        Connection State                                            mn_conn                            bool
            'Connected': True, DER connected
            'Disconnected': False, DER not connected

        DER OP State (not in IEEE 1547.1)                           mn_der_op_details               dict of bools
             'mn_op_local': System in local/maintenance state
             'mn_op_lockout': System locked out
             'mn_op_starting': Start command has been received
             'mn_op_stopping': Emergency Stop command has been received
             'mn_op_started': Started
             'mn_op_stopped': Stopped
             'mn_op_permission_to_start': Start Permission Granted
             'mn_op_permission_to_stop': Stop Permission Granted}

        DER CONN State (not in IEEE 1547.1)                          mn_der_conn_details               dict of bools
             'mn_conn_connected_idle': Idle-Connected
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
        if monitoring_pts.get('mn_w') is not None:
            monitoring_pts['mn_w'] /= 1000.  # kW
        if monitoring_pts.get('mn_var') is not None:
            monitoring_pts['mn_var'] /= 1000.  # kVar
        if monitoring_pts.get('mn_v') is not None:
            monitoring_pts['mn_v'] = [monitoring_pts['mn_v'] / 10.]  # V
        if monitoring_pts.get('mn_hz') is not None:
            monitoring_pts['mn_hz'] /= 100.

        # Build hierarchy
        monitoring_pts = self.build_sub_dict(monitoring_pts, new_name='mn_der_op_details', keys=list(operational_state.keys()))
        monitoring_pts = self.build_sub_dict(monitoring_pts, new_name='mn_der_conn_details', keys=list(connection_state.keys()))

        if monitoring_pts['mn_der_op_details']['mn_op_started']:
            monitoring_pts['mn_st'] = True
        else:
            monitoring_pts['mn_st'] = False

        if monitoring_pts['mn_der_conn_details']['mn_conn_connected_idle'] or \
                monitoring_pts['mn_der_conn_details']['mn_conn_connected_generating'] or \
                monitoring_pts['mn_der_conn_details']['mn_conn_connected_charging'] or \
                monitoring_pts['mn_der_conn_details']['mn_conn_switch_closed_status']:
            monitoring_pts['mn_conn'] = True
        else:
            monitoring_pts['mn_conn'] = False

        monitoring_pts = self.build_sub_dict(monitoring_pts, new_name='mn_alrm', keys=list(alarm_state.keys()))

        return monitoring_pts

    def get_const_pf(self):
        """
        Get Constant Power Factor Mode control settings. IEEE 1547-2018 Table 30.
        ________________________________________________________________________________________________________________
        Parameter                                               params dict key                     units
        ________________________________________________________________________________________________________________
        Constant Power Factor Mode Select                       const_pf_mode_enable             bool (True=Enabled)
        Constant Power Factor Excitation                        const_pf_excitation              str ('inj', 'abs')
        Constant Power Factor Absorbing Setting                 const_pf_abs                     decimal
        Constant Power Factor Injecting Setting                 const_pf_inj                     decimal
        Maximum response time to maintain constant power        const_pf_olrt                    s
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
        if 'const_pf_excitation' in pf_pts:
            if pf_pts['const_pf_excitation'] is None:
                self.ts.log_warning('No excitation provided by DER. Using PF sign to determine excitation.')
                der_excite = False
            else:
                der_excite = True
                if pf_pts['const_pf_excitation']:
                    pf_pts['const_pf_excitation'] = 'abs'
                else:
                    pf_pts['const_pf_excitation'] = 'inj'

            # get PFs and place in active power injection and absorption keys
            if 'const_pf' in pf_pts:
                # Generating PF
                pf_pts['const_pf_inj'] = abs(pf_pts['const_pf'])  # pf (Q1 pos, Q4 neg)
                if not der_excite:
                    if pf_pts['const_pf'] > 0:
                        pf_pts['const_pf_excitation'] = 'abs'
                    else:
                        pf_pts['const_pf_excitation'] = 'inj'
                # TODO - Charging PF
                # pf_pts['const_pf_abs'] = abs(pf_pts['const_pf'])  # pf (Q2 ?, Q3 ?)
                # if not der_excite:
                #     if pf_pts['const_pf'] > 0:
                #         pf_pts['const_pf_excitation'] = 'abs'
                #     else:
                #         pf_pts['const_pf_excitation'] = 'inj'

                del pf_pts['const_pf']

        return pf_pts

    def set_const_pf(self, params=None):
        """
        Set Constant Power Factor Mode control settings.
        ________________________________________________________________________________________________________________
        Parameter                                               params dict key                     units
        ________________________________________________________________________________________________________________
        Constant Power Factor Mode Select                       const_pf_mode_enable             bool (True=Enabled)
        Constant Power Factor Excitation                        const_pf_excitation              str ('inj', 'abs')
        Constant Power Factor Absorbing W Setting               const_pf_abs                     VAr p.u
        Constant Power Factor Injecting W Setting               const_pf_inj                     VAr p.u
        Maximum response time to maintain constant power        const_pf_olrt                    s
            factor. (Not in 1547)

        :return: dict with keys shown above.

        Sign convention
        Generating/Discharging (+)  PFExt = BO10 = <0> Injecting VArs   Q1  PF setpoint = AO210
        Generating/Discharging(+)   PFExt = BO10 = <1> Asorbing VArs    Q4  PF setpoint = AO210
        Charging (-)                PFExt = BO11 = <0> Injecting VArs   Q2  PF setpoint = AO211
        Charging (-)                PFExt = BO11 = <1> Absorbing VArs   Q3  PF setpoint = AO211
        """
        pf_pts = {**fixed_pf_write.copy()}

        if 'const_pf_excitation' in params:
            if params['const_pf_excitation'] == 'inj':
                params['const_pf_excitation'] = False
            elif params['const_pf_excitation'] == 'abs':
                params['const_pf_excitation'] = True
            else:
                self.ts.log_warning('const_pf_excitation is not "inj" or "abs"')
        else:
            if 'const_pf_mode_enable' in params:
                if params['const_pf_mode_enable']:
                    self.ts.log_warning('No const_pf_excitation provided. Assuming absorption (positive value).')

        # Apply scaling and overload the PF value
        if 'const_pf_abs' in params:
            if params['const_pf_abs'] < -1. or params['const_pf_abs'] > 1.:  # should be 0.0 to 1.0
                self.ts.log_warning('const_pf_abs value outside of -1 to 1 pf')
            # overloading this parameter point (both const_pf_inj and const_pf_abs map here)
            params['const_pf'] = int(params['const_pf_abs']*100.)  # from pf to pf*100, excit handles sign
            del params['const_pf_abs']

        if 'const_pf_inj' in params:
            if params['const_pf_inj'] < -1. or params['const_pf_inj'] > 1.:  # should be 0.0 to 1.0
                self.ts.log_warning('const_pf_inj value outside of -1 to 1 pf')
            # overloading this parameter point (both const_pf_inj and const_pf_abs map here)
            params['const_pf'] = int(params['const_pf_inj']*100.)  # from pf to pf*100, excit handles sign
            del params['const_pf_inj']

        # self.ts.log_debug('pf_pts = %s, params = %s' % (pf_pts, params))
        return self.write_dnp3_point_map(map_dict=pf_pts, write_pts=params)

    def get_qv(self):
        """
        Get Q(V), Volt-Var, Voltage-Reactive Power Mode
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Voltage-Reactive Power Mode Enable                          qv_mode_enable               bool (True=Enabled)
        Vref (0.95-1.05)                                            qv_vref                      V p.u.
        Autonomous Vref Adjustment Enable                           qv_vref_auto_mode            bool (True=Enabled)
        Vref adjustment time Constant (300-5000)                    qv_vref_olrt                 s
        Q(V) Curve Point V1-4 (list), [0.95, 0.99, 1.01, 1.05]      qv_curve_v_pts                  V p.u.
        Q(V) Curve Point Q1-4 (list), [1., 0., 0., -1.]             qv_curve_q_pts                  VAr p.u.
        Q(V) Open Loop Response Time Setting  (1-90)                qv_olrt                      s
        """

        volt_var_pts = volt_var_data.copy()
        volt_var_pts.update(curve_read.copy())

        resp = self.read_dnp3_point_map(volt_var_pts)
        resp = self.build_sub_dict(resp, new_name='qv_curve_dnp3_data', keys=list(curve_read.keys()))

        resp['qv_curve_v_pts'] = []
        resp['qv_curve_q_pts'] = []
        for pt in range(int(resp['qv_curve_dnp3_data']['no_of_points'])):
            resp['qv_curve_v_pts'].append(resp['qv_curve_dnp3_data']['x%d' % (pt + 1)] / 1000.)  # from 10*pct to pu
            resp['qv_curve_q_pts'].append(resp['qv_curve_dnp3_data']['y%d' % (pt + 1)] / 1000.)  # from 10*pct to pu
        resp['qv_curve_dnp3_data']['x_value'] = X_ENUM.get(resp['qv_curve_dnp3_data']['x_value'])
        resp['qv_curve_dnp3_data']['y_value'] = Y_ENUM.get(resp['qv_curve_dnp3_data']['y_value'])
        resp['qv_curve_dnp3_data']['curve_mode_type'] = CURVE_MODE.get(resp['qv_curve_dnp3_data']['curve_mode_type'])

        # self.ts.log_debug('VV read resp: %s' % resp)
        return resp

    def set_qv(self, params=None):
        """
        Set Q(V), Volt-Var
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Voltage-Reactive Power Mode Enable                          qv_mode_enable               bool (True=Enabled)
        Vref (0.95-1.05)                                            qv_vref                      V p.u.
        Autonomous Vref Adjustment Enable                           qv_vref_auto_mode            str
        Vref adjustment time Constant (300-5000)                    qv_vref_olrt                 s
        Q(V) Curve Point V1-4 (list), [0.95, 0.99, 1.01, 1.05]      qv_curve_v_pts                  V p.u.
        Q(V) Curve Point Q1-4 (list), [1., 0., 0., -1.]             qv_curve_q_pts                  VAr p.u.
        Q(V) Open Loop Response Time Setting  (1-90)                qv_olrt                      s
        ______________________________________________________________________________________________________________
        """

        volt_var_pts = volt_var_write.copy()
        volt_var_curve_pts = curve_write.copy()
        volt_var_pts.update(volt_var_curve_pts)

        if 'qv_curve_v_pts' in params or 'qv_curve_q_pts' in params:
            params['curve_index'] = '1'
            params['curve_edit_selector'] = '1'
            params['curve_mode_type'] = CURVE_MODE['VV']  # Curve Mode Type (2 = Volt-var)
            params['no_of_points'] = len(params['qv_curve_v_pts'])
            params['x_value'] = X_ENUM['Volt_Pct']  # Voltage
            params['y_value'] = Y_ENUM['VArMax']  # % DNP3 App Note Table 53 for details
            for pt in range(len(params['qv_curve_v_pts'])):
                params['x%d' % (pt + 1)] = params['qv_curve_v_pts'][pt]*1000.  # from pu to 10*pct
            for pt in range(len(params['qv_curve_q_pts'])):
                params['y%d' % (pt + 1)] = params['qv_curve_q_pts'][pt]*1000.  # from pu to 10*pct

        # Write the VV points
        vv_write = self.write_dnp3_point_map(volt_var_pts, params, debug=False)

        return vv_write

    def get_const_q(self):
        """
        Get Constant Reactive Power Mode
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                     units
        ______________________________________________________________________________________________________________
        Constant Reactive Power Mode Enable                     const_q_mode_enable              bool (True=Enabled)
        Constant Reactive Power Excitation (not specified in    const_q_mode_excitation          str ('inj', 'abs')
            1547)
        Constant Reactive power setting (See Table 7)           const_q                          VAr p.u.
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
        Maximum Response Time to maintain constant reactive     const_q_olrt                     s
            power (not specified in 1547)
        Maximum Response Time to maintain constant reactive     const_q_olrt_er_max                 s
            power(not specified in 1547)

        :return: dict with keys shown above.
        """

        # Read Outstation Points
        dnp3_pts = reactive_power_data.copy()
        reactive_power_pts = self.read_dnp3_point_map(dnp3_pts)

        if reactive_power_pts['const_q'] is not None:
            reactive_power_pts['const_q'] /= 1000.  # scaling from pct*10 to pu

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

        conn = bool for connection
        """

        # Read Outstation Points
        dnp3_pts = conn_data.copy()
        return self.read_dnp3_point_map(dnp3_pts)

    def set_conn(self, params=None):
        """
        This information is used to update functional and mode settings for the
        Constant Reactive Power Mode. This information may be written.

        conn = bool for connection
        """

        dnp3_pts = conn_write.copy()
        return self.write_dnp3_point_map(dnp3_pts, write_pts=params)

    def get_pf(self):
        """
        Get P(f), Frequency-Active Power Mode Parameters - IEEE 1547 Table 38
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          pf_mode_enable               bool (True=Enabled)
        P(f) Overfrequency Droop dbOF Setting                       pf_dbof                      Hz
        P(f) Underfrequency Droop dbUF Setting                      pf_dbuf                      Hz
        P(f) Overfrequency Droop kOF  Setting                       pf_kof                       unitless
        P(f) Underfrequency Droop kUF Setting                       pf_kuf                       unitless
        P(f) Open Loop Response Time Setting                        pf_olrt                      s

        :return: dict with keys shown above.
        """
        freq_watt_pts = freq_watt_data.copy()
        return self.read_dnp3_point_map(freq_watt_pts)

    def set_pf(self, params=None):
        """
        Set Frequency-Active Power Mode.
        """
        freq_watt_pts = freq_watt_write.copy()
        return self.write_dnp3_point_map(freq_watt_pts, params)

    def get_p_lim(self):
        """
        Get Limit maximum active power - IEEE 1547 Table 40
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          p_lim_mode_enable         bool (True=Enabled)
        Maximum Active Power Min                                    p_lim_w_er_min               P p.u.
        Maximum Active Power                                        p_lim_w                   P p.u.
        Maximum Active Power Max                                    p_lim_w_er_max               P p.u.
        """

        # Read Outstation Points
        dnp3_pts = limit_max_power_data.copy()
        limit_max_power_pts = self.read_dnp3_point_map(dnp3_pts)

        if limit_max_power_pts['p_lim_w'] is not None:
            limit_max_power_pts['p_lim_w'] /= 1000.  # scaling from pct*10 to pu

        return limit_max_power_pts

    def set_p_lim(self, params=None):
        """
        Set Limit maximum active power - IEEE 1547 Table 40
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          p_lim_mode_enable         bool (True=Enabled)
        Maximum Active Power Min                                    p_lim_w_er_min               P p.u.
        Maximum Active Power                                        p_lim_w                   P p.u.
        Maximum Active Power Max                                    p_lim_w_er_max               P p.u.
        """

        limit_max_power_pts = limit_max_power_write.copy()

        # Apply scaling
        if 'p_lim_w' in params:
            if params['p_lim_w'] < -1. or params['p_lim_w'] > 1.:
                self.ts.log_warning('p_lim_w value outside of -1 to 1 pu')
            params['p_lim_w'] = int(params['p_lim_w']*1000.)  # from pu to pct*10

        return self.write_dnp3_point_map(limit_max_power_pts, write_pts=params)

    def get_qp(self):
        """
        Get Q(P) parameters. [Watt-Var]
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        Active Power-Reactive Power (Watt-VAr) Enable               qp_mode_enable                   bool
        P-Q curve P1-3 Generation Setting (list)                    qp_curve_p_gen_pts               P p.u.
        P-Q curve Q1-3 Generation Setting (list)                    qp_curve_q_gen_pts               VAr p.u.
        P-Q curve P1-3 Load Setting (list)                          qp_curve_p_load_pts              P p.u.
        P-Q curve Q1-3 Load Setting (list)                          qp_curve_q_load_pts              VAr p.u.

        """
        watt_var_pts = watt_var_data.copy()
        watt_var_pts.update(curve_read.copy())

        resp = self.read_dnp3_point_map(watt_var_pts)
        resp = self.build_sub_dict(resp, new_name='qp_curve_dnp3_data', keys=list(curve_read.keys()))

        resp['qp_curve_p_gen_pts'] = []
        resp['qp_curve_q_gen_pts'] = []
        resp['qp_curve_p_load_pts'] = []
        resp['qp_curve_q_load_pts'] = []
        for pt in range(int(resp['qp_curve_dnp3_data']['no_of_points'])):
            # TODO: manage multiple curves
            resp['qp_curve_p_gen_pts'].append(resp['qp_curve_dnp3_data']['x%d' % (pt + 1)] / 1000.)  # 10*pct to pu
            resp['qp_curve_q_gen_pts'].append(resp['qp_curve_dnp3_data']['y%d' % (pt + 1)] / 1000.)  # 10*pct to pu
            resp['qp_curve_p_load_pts'].append(resp['qp_curve_dnp3_data']['x%d' % (pt + 1)] / 1000.)  # 10*pct to pu
            resp['qp_curve_q_load_pts'].append(resp['qp_curve_dnp3_data']['y%d' % (pt + 1)] / 1000.)  # 10*pct to pu
        resp['qp_curve_dnp3_data']['x_value'] = X_ENUM.get(resp['qp_curve_dnp3_data']['x_value'])
        resp['qp_curve_dnp3_data']['y_value'] = Y_ENUM.get(resp['qp_curve_dnp3_data']['y_value'])
        resp['qp_curve_dnp3_data']['curve_mode_type'] = CURVE_MODE.get(resp['qp_curve_dnp3_data']['curve_mode_type'])

        # self.ts.log_debug('WV read resp: %s' % resp)
        return resp

    def set_qp(self, params=None):
        """
        Set Q(P) parameters. [Watt-Var]
        """
        watt_var_pts = watt_var_write.copy()
        watt_var_curve_pts = curve_write.copy()
        watt_var_pts.update(watt_var_curve_pts)

        if 'pv_curve_p_pts' in params or 'pv_curve_q_pts' in params:
            params['curve_index'] = '1'
            params['curve_edit_selector'] = '1'
            params['curve_mode_type'] = CURVE_MODE['WV']
            params['no_of_points'] = len(params['pv_curve_v_pts'])
            params['x_value'] = X_ENUM['Volt_Pct']  # Voltage
            params['y_value'] = Y_ENUM['WMaxPct']  # DNP3 App Note Table 53 for details
            # TODO: work with multiple curves
            for pt in range(len(params['qp_curve_p_gen_pts'])):
                params['x%d' % (pt + 1)] = params['qp_curve_p_gen_pts'][pt]*1000.  # from pu to 10*pct
            for pt in range(len(params['qp_curve_q_gen_pts'])):
                params['y%d' % (pt + 1)] = params['qp_curve_q_gen_pts'][pt]*1000.  # from pu to 10*pct
            for pt in range(len(params['qp_curve_p_load_pts'])):
                params['x%d' % (pt + 1)] = params['qp_curve_p_load_pts'][pt]*1000.  # from pu to 10*pct
            for pt in range(len(params['qp_curve_q_load_pts'])):
                params['y%d' % (pt + 1)] = params['qp_curve_q_load_pts'][pt]*1000.  # from pu to 10*pct

        # Write the P(V) points
        pv_write = self.write_dnp3_point_map(volt_watt_pts, params, debug=False)

        return pv_write

    def get_pv(self, params=None):
        """
        Get P(V), Voltage-Active Power (Volt-Watt), Parameters
        """

        volt_watt_pts = volt_watt_data.copy()
        volt_watt_pts.update(curve_read.copy())

        resp = self.read_dnp3_point_map(volt_watt_pts)
        resp = self.build_sub_dict(resp, new_name='pv_curve_dnp3_data', keys=list(curve_read.keys()))

        resp['pv_curve_v_pts'] = []
        resp['pv_curve_p_pts'] = []
        for pt in range(int(resp['pv_curve_dnp3_data']['no_of_points'])):
            resp['pv_curve_v_pts'].append(resp['pv_curve_dnp3_data']['x%d' % (pt + 1)] / 1000.)  # from 10*pct to pu
            resp['pv_curve_p_pts'].append(resp['pv_curve_dnp3_data']['y%d' % (pt + 1)] / 1000.)  # from 10*pct to pu
        resp['pv_curve_dnp3_data']['x_value'] = X_ENUM.get(resp['pv_curve_dnp3_data']['x_value'])
        resp['pv_curve_dnp3_data']['y_value'] = Y_ENUM.get(resp['pv_curve_dnp3_data']['y_value'])
        resp['pv_curve_dnp3_data']['curve_mode_type'] = CURVE_MODE.get(resp['pv_curve_dnp3_data']['curve_mode_type'])

        # self.ts.log_debug('VV read resp: %s' % resp)
        return resp

    def set_pv(self, params=None):
        """
        Set P(V), Voltage-Active Power (Volt-Watt), Parameters
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                         units
        ______________________________________________________________________________________________________________
        Voltage-Active Power Mode Enable                            pv_mode_enable                       bool
        P(V) Curve Point V1-2 Setting (list)                        pv_curve_v_pts                       V p.u.
        P(V) Curve Point P1-2 Setting (list)                        pv_curve_p_pts                       P p.u.
        P(V) Curve Point P1-P'2 Setting (list)                      pv_curve_p_bidrct_pts                P p.u.
        P(V) Open Loop Response time Setting (0.5-60)               pv_olrt                              s

        :return: dict with keys shown above.
        """
        volt_watt_pts = volt_watt_write.copy()
        volt_watt_curve_pts = curve_write.copy()
        volt_watt_pts.update(volt_watt_curve_pts)

        if 'pv_curve_v_pts' in params or 'pv_curve_p_pts' in params:
            params['curve_index'] = '1'
            params['curve_edit_selector'] = '1'
            params['curve_mode_type'] = CURVE_MODE['WV']
            params['no_of_points'] = len(params['pv_curve_v_pts'])
            params['x_value'] = X_ENUM['Volt_Pct']  # Voltage
            params['y_value'] = Y_ENUM['WMaxPct']  # DNP3 App Note Table 53 for details
            for pt in range(len(params['pv_curve_v_pts'])):
                params['x%d' % (pt + 1)] = params['pv_curve_v_pts'][pt]*1000.  # from pu to 10*pct
            for pt in range(len(params['pv_curve_p_pts'])):
                params['y%d' % (pt + 1)] = params['pv_curve_p_pts'][pt]*1000.  # from pu to 10*pct

        # Write the P(V) points
        pv_write = self.write_dnp3_point_map(volt_watt_pts, params, debug=False)

        return pv_write

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

    def get_es_permit_service(self):
        """
        Get Permit Service Mode Parameters - IEEE 1547 Table 39
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                 units
        ______________________________________________________________________________________________________________
        Permit service                                          es_permit_service            bool (True=Enabled)
        ES Voltage Low (RofA not specified in 1547)             es_v_low_er_min                 V p.u.
        ES Voltage Low Setting                                  es_v_low                     V p.u.
        ES Voltage Low (RofA not specified in 1547)             es_v_low_er_max                 V p.u.
        ES Voltage High (RofA not specified in 1547)            es_v_high_er_min                V p.u.
        ES Voltage High Setting                                 es_v_high                    V p.u.
        ES Voltage High (RofA not specified in 1547)            es_v_high_er_max                V p.u.
        ES Frequency Low (RofA not specified in 1547)           es_f_low_er_min                 Hz
        ES Frequency Low Setting                                es_f_low                     Hz
        ES Frequency Low (RofA not specified in 1547)           es_f_low_er_max                 Hz
        ES Frequency Low (RofA not specified in 1547)           es_f_high_er_min                Hz
        ES Frequency High Setting                               es_f_high                    Hz
        ES Frequency Low (RofA not specified in 1547)           es_f_high_er_max                Hz
        ES Randomized Delay                                     es_randomized_delay          bool (True=Enabled)
        ES Delay (RofA not specified in 1547)                   es_delay_er_min                 s
        ES Delay Setting                                        es_delay                     s
        ES Delay (RofA not specified in 1547)                   es_delay_er_max                 s
        ES Ramp Rate Min (RofA not specified in 1547)           es_ramp_rate_er_min             %/s
        ES Ramp Rate Setting                                    es_ramp_rate                 %/s
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
        Unintentional Islanding Mode (enabled/disabled). This       ui_mode_enable                   bool
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
        HV Trip Curve Point OV_V1-3 Setting                         ov_trip_v_pts                    V p.u.
        HV Trip Curve Point OV_V1-3 (RofA not specified in 1547)    ov_trip_v_pts_er_max                V p.u.
        HV Trip Curve Point OV_T1-3 (see Tables 11-13)              ov_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        HV Trip Curve Point OV_T1-3 Setting                         ov_trip_t_pts                    s
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
        LV Trip Curve Point UV_V1-3 Setting                         uv_trip_v_pts                    V p.u.
        LV Trip Curve Point UV_V1-3 (RofA not specified in 1547)    uv_trip_v_pts_er_max                V p.u.
        LV Trip Curve Point UV_T1-3 (see Tables 11-13)              uv_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        LV Trip Curve Point UV_T1-3 Setting                         uv_trip_t_pts                    s
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
        OF Trip Curve Point OF_F1-3 Setting                         of_trip_f_pts                    Hz
        OF Trip Curve Point OF_F1-3 (RofA not specified in 1547)    of_trip_f_pts_er_max                Hz
        OF Trip Curve Point OF_T1-3 (see Tables 11-13)              of_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        OF Trip Curve Point OF_T1-3 Setting                         of_trip_t_pts                    s
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
        UF Trip Curve Point UF_F1-3 Setting                         uf_trip_f_pts                    Hz
        UF Trip Curve Point UF_F1-3 (RofA not specified in 1547)    uf_trip_f_pts_er_max                Hz
        UF Trip Curve Point UF_T1-3 (see Tables 11-13)              uf_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        UF Trip Curve Point UF_T1-3 Setting                         uf_trip_t_pts                    s
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
        HV MC Curve Point OV_V1-3 Setting                           ov_mc_v_pts                      V p.u.
        HV MC Curve Point OV_V1-3 (RofA not specified in 1547)      ov_mc_v_pts_er_max                  V p.u.
        HV MC Curve Point OV_T1-3 (see Tables 11-13)                ov_mc_t_pts_er_min                  s
            (RofA not specified in 1547)
        HV MC Curve Point OV_T1-3 Setting                           ov_mc_t_pts                      s
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
        LV MC Curve Point UV_V1-3 Setting                           uv_mc_v_pts                    V p.u.
        LV MC Curve Point UV_V1-3 (RofA not specified in 1547)      uv_mc_v_pts_er_max                V p.u.
        LV MC Curve Point UV_T1-3 (see Tables 11-13)                uv_mc_t_pts_er_min                s
            (RofA not specified in 1547)
        LV MC Curve Point UV_T1-3 Setting                           uv_mc_t_pts                    s
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
        return self.set_es_permit_service(params={'es_permit_service': params['cease_to_energize']})


    def get_curve_settings(self):
        """
        Get DNP3 Curve Points
        :return:
        """
        curve_read_pts = curve_read.copy()
        curve_setting_read = self.read_dnp3_point_map(curve_read_pts)
        return curve_setting_read

    def set_curve_settings(self, params=None):
        """
        Set DNP3 Curve Points
        :return:
        """
        curve_write_pts = curve_write.copy()
        write = self.write_dnp3_point_map(curve_write_pts, params)
        return write


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

Operational State                                           mn_st                              bool

Connection State                                            mn_conn                            bool

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

fixed_pf = {'const_pf_mode_enable': {'bi': {'80': None}},
            # 'const_pf_abs': {'ai': {'288': None}},
            # 'const_pf_inj': {'ai': {'288': None}},
            'const_pf': {'ai': {'288': None}},
            'const_pf_excitation': {'bi': {'29': None}}}

fixed_pf_write = {'const_pf_mode_enable': {'bo': {'28': None}},
                  # 'const_pf_abs': {'ao': {'210': None}},
                  # 'const_pf_inj': {'ao': {'210': None}},
                  'const_pf': {'ao': {'210': None}},
                  'const_pf_excitation': {'bo': {'10': None}}}

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
______________________________________________________________________________________________________________

der1547 Abstraction:
______________________________________________________________________________________________________________
Parameter                                                   params dict key                 units
______________________________________________________________________________________________________________
Voltage-Reactive Power Mode Enable                          qv_mode_enable               bool (True=Enabled)
Vref (0.95-1.05)                                            qv_vref                      V p.u.
Autonomous Vref Adjustment Enable                           qv_vref_auto_mode            str
Vref adjustment time Constant (300-5000)                    qv_vref_olrt                 s
Q(V) Curve Point V1-4 (list, e.g., [95, 99, 101, 105])      qv_curve_v_pts                  V p.u.
Q(V) Curve Point Q1-4 (list)                                qv_curve_q_pts                  VAr p.u.
Q(V) Open Loop Response Time Setting  (1-90)                qv_olrt                      s
______________________________________________________________________________________________________________
'''

volt_var_data = {'qv_mode_enable': {'bi': {'81': None}},
                 'qv_vref': {'ai': {'29': None}},
                 'qv_vref_auto_mode': {'bi': {'93': None}},
                 'qv_vref_olrt': {'ai': {'300': None}},
                 'qv_olrt': {'ai': {'298': None}}}

volt_var_write = {'qv_mode_enable': {'bo': {'29': None}},
                  'qv_vref': {'ao': {'0': None}},
                  'qv_vref_auto_mode': {'bo': {'41': None}},
                  'qv_vref_olrt': {'ao': {'220': None}},
                  'qv_olrt': {'ao': {'218': None}}}

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
Constant Reactive Power Mode Enable                     const_q_mode_enable              bool (True=Enabled)
Constant Reactive Power Excitation (not specified in    const_q_mode_excitation          str ('inj', 'abs')
    1547)
Constant Reactive power setting (See Table 7)           const_q                          VAr p.u.
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
Maximum Response Time to maintain constant reactive     const_q_olrt                     s
    power (not specified in 1547)
Maximum Response Time to maintain constant reactive     const_q_olrt_er_max                 s
    power(not specified in 1547)

:return: dict with keys shown above.
"""

reactive_power_data = {'const_q_mode_enable': {'bi': {'79': None}},
                       'const_q': {'ai': {'281': None}}}

reactive_power_write = {'const_q_mode_enable': {'bo': {'27': None}},
                        'const_q': {'ao': {'203': None}}}

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

AI122 = Frequency-Watt High Stopping Frequency
AI126 = Frequency-Watt Low Stopping
...

Get P(f), Frequency-Active Power Mode Parameters - IEEE 1547 Table 38
______________________________________________________________________________________________________________
Parameter                                                   params dict key                 units
______________________________________________________________________________________________________________
Frequency-Active Power Mode Enable                          pf_mode_enable               bool (True=Enabled)
P(f) Overfrequency Droop dbOF Setting                       pf_dbof                      Hz
P(f) Underfrequency Droop dbUF Setting                      pf_dbuf                      Hz
P(f) Overfrequency Droop kOF  Setting                       pf_kof                       unitless
P(f) Underfrequency Droop kUF Setting                       pf_kuf                       unitless
P(f) Open Loop Response Time Setting                        pf_olrt                      s
'''

freq_watt_data = {'pf_mode_enable': {'bi': {'78': None}},
                  'pf_dbof': {'ai': {'121': None}},
                  'pf_dbuf': {'ai': {'125': None}},
                  'pf_kof': {'ai': {'123': None}},
                  'pf_kuf': {'ai': {'127': None}},
                  'pf_olrt': {'ai': {'131': None}}}

freq_watt_write = {'pf_mode_enable': {'ao': {'121': None}},
                  'pf_dbof': {'ao': {'62': None}},
                  'pf_dbuf': {'ao': {'66': None}},
                  'pf_kof': {'ao': {'64': None}},
                  'pf_kuf': {'ao': {'68': None}},
                  'pf_olrt': {'ao': {'72': None}}}

'''
DNP3 App Note Table 63 - Mapping of IEC Std 1547 to The DNP3 DER Profile

Category: Active Power 
____________________________________________________________________________________________________________
Information                                 Units               Output(s)           Input(s)
____________________________________________________________________________________________________________
Limit Active Power Enable                   On/Off              BO17                BI69
Limit Mode Maximum Active Power             Watts (pct)         AO87 - AO88         AI148 - AI149
'''

limit_max_power_data = {'p_lim_mode_enable': {'bi': {'69': None}},
                        'p_lim_w': {'ai': {'149': None}}}

limit_max_power_write = {'p_lim_mode_enable': {'bo': {'17': None}},
                         'p_lim_w': {'ao': {'88': None}}}


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

curve_read = {'curve_index': {'ai': {'297': None}},
              'curve_edit_selector': {'ai': {'328': None}},
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

curve_write = {'curve_index': {'ao': {'217': None}},
               'curve_edit_selector': {'ao': {'244': None}},
               'curve_mode_type': {'ai': {'245': None}},
               'no_of_points': {'ao': {'246': None}},
               'x_value': {'ao': {'247': None}},
               'y_value': {'ao': {'248': None}},
               'x1': {'ao': {'249': None}},
               'y1': {'ao': {'250': None}},
               'x2': {'ao': {'251': None}},
               'y2': {'ao': {'252': None}},
               'x3': {'ao': {'253': None}},
               'y3': {'ao': {'254': None}},
               'x4': {'ao': {'255': None}},
               'y4': {'ao': {'256': None}}}

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

______________________________________________________________________________________________________________
Parameter                                                   params dict key                         units
______________________________________________________________________________________________________________
Voltage-Active Power Mode Enable                            pv_mode_enable                       bool
P(V) Curve Point V1-2 Setting (list)                        pv_curve_v_pts                       V p.u.
P(V) Curve Point P1-2 Setting (list)                        pv_curve_p_pts                       P p.u.
P(V) Curve Point P1-P'2 Setting (list)                      pv_curve_p_bidrct_pts                P p.u.
P(V) Open Loop Response time Setting (0.5-60)               pv_olrt                              s


'''
volt_watt_data = {'pv_mode_enable': {'bi': {'77': None}},
                  'pv_olrt': {'ai': {'251': None}}}

volt_watt_write = {'pv_mode_enable': {'bo': {'25': None}},
                   'pv_olrt': {'ao': {'175': None}}}

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

conn_data = {'conn': {'bi': {'21': None}}}
conn_write = {'conn': {'bo': {'5': None}}}

