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
from . import loadsim
from . import device_loadsim_icselect_8064 as icselect
import csv
import time

icselect_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'ICS Electronics 8064 Banks'
}

def loadsim_info():
    return icselect_info

def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = icselect_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)

    info.param(pname('banks'), label='Which Load Banks are Used?', default='RL',
               values=['R', 'L', 'C', 'RL', 'RC', 'RLC'])
    info.param(pname('mode'), label='Load bank operating mode:', default='Read CSV', values=['Read CSV', 'Static'])

    # info.param_group(gname('r_load'), label='Resistive Bank', active=pname('banks'),
    #                  active_value=['R', 'RL', 'RC', 'RLC'])
    info.param(pname('comm_r'), label='Communications Interface (R)', default='VXI11', values=['VXI11'],
               active=pname('banks'), active_value=['R', 'RL', 'RC', 'RLC'])
    info.param(pname('vxi11_device_r'), label='VXI11 IP Address for Resistive Bank', active=pname('comm_r'),
               active_value=['VXI11'], default='10.1.32.63')
    info.param(pname('power'), label='Power Value (W)', default=2000, active=pname('mode'), active_value=['Static'])

    info.param(pname('comm_l'), label='Communications Interface (R)', default='VXI11', values=['VXI11'],
               active=pname('banks'), active_value=['L', 'RL', 'RLC'])
    info.param(pname('vxi11_device_l'), label='VXI11 IP Address for Inductive Bank', active=pname('comm_l'),
               active_value=['VXI11'], default='10.1.32.64')
    info.param(pname('q_l'), label='Reactive Power Value (Var)', default=2000, active=pname('mode'),
               active_value=['Static'])

    info.param(pname('comm_c'), label='Communications Interface (R)', default='VXI11', values=['VXI11'],
               active=pname('banks'), active_value=['C', 'RC', 'RLC'])
    info.param(pname('vxi11_device_c'), label='VXI11 IP Address for Inductive Bank', active=pname('comm_c'),
               active_value=['VXI11'], default='10.1.32.65')
    info.param(pname('q_c'), label='Reactive Power Value (Var)', default=2000, active=pname('mode'),
               active_value=['Static'])

    info.param(pname('csv'), label='CSV string for load profile [time, R, L, C]:',
               default='C:\\Users\detldaq\Downloads\Load_test.csv', active=pname('mode'), active_value=['Read CSV'])


GROUP_NAME = 'icselect'


class LoadSim(loadsim.LoadSim):
    """
    ICS Electronics loadsim class.
    """
    def __init__(self, ts, group_name):
        loadsim.LoadSim.__init__(self, ts, group_name)
        self.ts = ts

        self.banks = self._param_value('banks')
        self.mode = self._param_value('mode')
        self.r_load = None
        self.l_load = None
        self.c_load = None

        self.time = None  # time steps in csv profile

        self.comm_r = self._param_value('comm_r')
        self.vxi11_device_r = self._param_value('vxi11_device_r')
        self.power = self._param_value('power')

        self.comm_l = self._param_value('comm_l')
        self.vxi11_device_l = self._param_value('vxi11_device_l')
        self.q_l = self._param_value('q_l')

        self.comm_c = self._param_value('comm_c')
        self.vxi11_device_c = self._param_value('vxi11_device_c')
        self.q_c = self._param_value('q_c')

        self.csv = self._param_value('csv')

        if 'R' in self.banks:
            params = {}
            params['loadbank_type'] = 'R'
            params['ip_addr'] = self.vxi11_device_r
            # NOTE: if the CSV file is profiled the time/target levels will be updated in the init
            params['csv'] = self.csv
            params['switch_map'] = {0: None,
                                    263: 1,
                                    526: 2,
                                    1052: 3,
                                    2106: 4,
                                    4210: 5,
                                    1053: 6,
                                    8421: 7,
                                    2105: 8,
                                    9080: 9,
                                    3158: 10}
            self.r_load = icselect.Device(params=params)
            self.r_load.open()

        if 'L' in self.banks:
            params = {}
            params['loadbank_type'] = 'L'
            params['ip_addr'] = self.vxi11_device_l
            # NOTE: if the CSV file is profiled the time/target levels will be updated in the init
            params['csv'] = self.csv
            params['switch_map'] = {0: None,
                                      197: 1,
                                      390: 2,
                                      788: 3,
                                      1582: 4,
                                      3170: 5,
                                      790: 6,
                                      6175: 7,
                                      1562: 8,
                                      9080: 9,
                                      2340: 10}
            self.l_load = icselect.Device(params=params)
            self.l_load.open()
        if 'C' in self.banks:
            params = {}
            params['loadbank_type'] = 'C'
            params['ip_addr'] = self.vxi11_device_c
            # NOTE: if the CSV file is profiled the time/target levels will be updated in the init
            params['csv'] = self.csv
            params['switch_map'] = {0: None,
                                      197: 1,
                                      390: 2,
                                      788: 3,
                                      1582: 4,
                                      3170: 5,
                                      790: 6,
                                      6175: 7,
                                      1562: 8,
                                      9080: 9,
                                      2340: 10}
            self.c_load = icselect.Device(params=params)
            self.c_load.open()

        # if there is a CSV file pull the time and R, L, C data here.
        if self.mode == 'Read CSV':
            self.p_q_profile(csvfile=self.csv)
        elif self.mode == 'Static':
            if self.r_load:
                self.resistance_p(p=self.power)
            if self.l_load:
                self.inductor_q(q=self.q_l)
            if self.c_load:
                self.capacitor_q(q=self.q_c)
        else:
            self.ts.log_warning('Loadbank mode unsupported!')

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def resistance(self, r=None, ph=None):
        pass

    def inductance(self, l=None, ph=None):
        pass

    def capacitance(self, c=None, ph=None):
        pass

    def capacitor_q(self, q=None, ph=None):
        switches, loads, error = self.c_load.set_value(q)
        return switches, loads, error

    def inductor_q(self, q=None, ph=None):
        switches, loads, error = self.l_load.set_value(q)
        return switches, loads, error

    def resistance_p(self, p=None, ph=None):
        switches, loads, error = self.r_load.set_value(p)
        return switches, loads, error

    def tune_current(self, i=None, ph=None):
        pass

    def start_profile(self, debug=False):
        if debug:
            self.ts.log_debug('time = %s, power = %s, q_l = %s, q_c = %s' % (self.time, self.power, self.q_l, self.q_c))
        if type(self.time) is not list:
            self.ts.log_error('Profile not provided in load bank init.')
        start = time.time()
        self.ts.sleep(0.1)
        i = 0
        while i < len(self.time):
            now = time.time()
            elapsed = now - start
            if elapsed >= self.time[i]:
                if self.r_load:
                    switches, loads, error = self.resistance_p(p=self.power[i])
                    if debug:
                        self.ts.log_debug('Target = %s W, Total power = %s, switches: %s, loads: %s, power error = %s W'
                                          % (self.power[i], sum(loads), switches, loads, error))
                if self.l_load:
                    self.inductor_q(q=self.q_l[i])
                if self.c_load:
                    self.capacitor_q(q=self.q_c[i])
                if debug:
                    self.ts.log_debug('Target = %s W, %s inductive var, %s capacitive var at time = %s s.' %
                                      (self.power[i], self.q_l[i], self.q_c[i], round(elapsed, 1)))
                i += 1
            else:
                self.ts.sleep(0.05)

    def p_q_profile(self, csvfile=None):
        if file is not None:
            self.time = []
            self.power = []
            self.q_l = []
            self.q_c = []
            with open(csvfile) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                for row in csv_reader:
                    try:
                        self.time.append(float(row[0]))
                        if self.r_load:
                            self.power.append(float(row[1]))
                        else:
                            self.power.append(0)
                        if self.l_load:
                            self.q_l.append(float(row[2]))
                        else:
                            self.q_l.append(0)
                        if self.c_load:
                            self.q_c.append(float(row[3]))
                        else:
                            self.q_c.append(0)
                    except Exception as e:
                        print(('Not an numerical entry...skipping data for row %s. Error: %s' % (row, e)))

        self.ts.log_debug('time = %s, power = %s, q_l = %s, q_c = %s' % (self.time, self.power, self.q_l, self.q_c))

    def close(self):
        if self.r_load:
            self.r_load.close()
        if self.l_load:
            self.l_load.close()
        if self.c_load:
            self.c_load.close()

    def info(self):
        r_string = None
        l_string = None
        c_string = None
        if self.r_load:
            r_string = self.r_load.info()
        if self.l_load:
            l_string = self.l_load.info()
        if self.c_load:
            c_string = self.c_load.info()
        return 'Resistive Load: %s, Inductive Load: %s, Capacitive Load: %s' % (r_string, l_string, c_string)
