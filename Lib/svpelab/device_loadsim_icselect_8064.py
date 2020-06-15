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

import time
from . import vxi11
import numpy as np
import itertools
import csv


def p_q_profile(csvfile=None):
        if file is not None:
            time = []
            power = []
            q_l = []
            q_c = []
            with open(csvfile) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                for row in csv_reader:
                    try:
                        time.append(float(row[0]))
                        if r_load:
                            power.append(float(row[1]))
                        else:
                            power.append(0)
                        if l_load:
                            q_l.append(float(row[2]))
                        else:
                            q_l.append(0)
                        if c_load:
                            q_c.append(float(row[3]))
                        else:
                            q_c.append(0)
                    except Exception as e:
                        print(('Not an numerical entry...skipping data for row %s. Error: %s' % (row, e)))
            return time, power, q_l, q_c

class DeviceError(Exception):
    """
    Exception to wrap all loadbank generated exceptions.
    """
    pass


class Device(object):

    def __init__(self, params):
        self.vx = None
        self.params = params
        self.vx = vxi11.Instrument(self.params['ip_addr'])
        self.time = []
        self.target = []
        self.switch_map = self.params['switch_map']

    def open(self):
        pass

    def close(self):
        if self.vx is not None:
            self.vx.close()
            self.vx = None

    def cmd(self, cmd_str):
        try:
            self.vx.write(cmd_str)
            resp = self.query('SYST:ERRor?')

            if len(resp) > 0:
                if resp[0] != '0':
                    raise DeviceError(resp)
        except Exception as e:
            raise DeviceError('ICS Electronics 8064 communication error: %s' % str(e))

    def query(self, cmd_str):
        try:
            resp = self.vx.ask(cmd_str)
        except Exception as e:
            raise DeviceError('ICS Electronics 8064 communication error: %s' % str(e))

        return resp

    def info(self):
        return self.query('*IDN?')

    def version(self):
        return self.query('SYSTem:VERSion?')

    def query_status(self):
        event = self.query('STAT:OPER:EVENt?')
        condition = self.query('STAT:OPER:CONDition?')
        enable = self.query('STAT:OPER:ENABle?')
        print('Event: %s, Condition: %s, Enable: %s' % (event, condition, enable))
        return event, condition, enable

    def query_relay_control_state(self):
        state = self.query('Q?')
        print('Relay Control State: %s' % state)
        return state

    def cmd_open_all(self):
        status = self.cmd('ROUT:OPEN:ALL')
        print('Opened all relays')
        return status

    def cmd_close(self, relays):
        if relays is not [None]:
            if relays == [None]:
                self.cmd('ROUT:OPEN:ALL')
                print('Closing Relays: %s' % relays)
            else:
                cmd_str = 'C (@'
                for r in relays:
                    cmd_str += '%s,' % r
                cmd_str = cmd_str[:-1] + ')'
                print('Closing Relays: %s' % relays)
                self.cmd(cmd_str)
        else:
            print('ERROR: Relays to be closed were not passed as a list.')
        return None

    def set_value(self, value):
        self.target = [value]
        switches, loads, error = self.find_closest_sum(index=0)
        return switches, loads, error

    def find_closest_sum(self, index=None):
        for t in [self.target[index]]:
            if not list(self.switch_map.keys()):
                break
            combs = sum([list(itertools.combinations(list(self.switch_map.keys()), r)) for r in range(1, len(list(self.switch_map.keys()))+1)], [])
            sums = np.asarray(list(map(sum, combs)))
            bestcomb = combs[np.argmin(np.abs(np.asarray(sums) - t))]
            # print("Target: {},  combination: {}".format(t, bestcomb))

            switches = []
            loads = []
            for value in bestcomb:
                loads.append(value)
                switches.append(self.switch_map[value])
            error = abs(sum(loads)-t)
        return switches, loads, error

if __name__ == "__main__":
    r_load = True
    l_load = False
    c_load = False

    filename = 'C:\\Users\detldaq\Downloads\Load_test.csv'
    sec, target_W, target_VA_l, target_VA_c = p_q_profile(filename)

    if r_load:
        params = {}
        params['ip_addr'] = '10.1.32.63'
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

        params['target'] = target_W
        LB_W = Device(params=params)
        print(LB_W.info())
        print(LB_W.version())
        LB_W.query_status()
        LB_W.query_relay_control_state()

    if l_load:
        params = {}
        params['ip_addr'] = '0.0.0.0'
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
        params['target'] = target_VA_l
        LB_VA_l = Device(params=params)
        print(LB_VA_l.info())
        print(LB_VA_l.version())
        LB_VA_l.query_status()
        LB_VA_l.query_relay_control_state()

    if c_load:
        params = {}
        params['ip_addr'] = '0.0.0.0'
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
        params['target'] = target_VA_c
        LB_VA_c = Device(params=params)
        print(LB_VA_c.info())
        print(LB_VA_c.version())
        LB_VA_c.query_status()
        LB_VA_c.query_relay_control_state()



    # for t in range(3):
    #     LB_W.query_relay_control_state()
    #     time.sleep(30)
    #     # d.cmd_close([1, 3, 7, 16])
    #     # d.cmd_close([t + 1])
    #     # d.cmd_close([1])
    #     LB_W.query_relay_control_state()
    #     time.sleep(30)
    #     LB_W.cmd_open_all()
    #     time.sleep(1)
    start = time.time()
    time.sleep(0.1)
    i = 0


    while i < len(sec):
        # switches_VA, loads_VA, error_VA = LB_VA.find_closest_sum([load_VA[i]])
        now = time.time()
        elapsed = now - start
        if elapsed >= sec[i]:
            if r_load:
                switches_W, loads_W, error_W = LB_W.set_value(target_W[i])
                print(('Resistive: Target = %s W, Total power = %s, switches: %s, loads: %s, power error = %s W' %
                    (target_W[i], sum(loads_W), switches_W, loads_W, error_W)))
                LB_W.cmd_close(switches_W)
            else:
                error_W = 0
                loads_W = target_W
                LB_W.cmd_open_all()
            if l_load:
                switches_VA_l, loads_VA_l, error_VA_l = LB_VA_l.set_value(target_VA_l)
                print(('Inductive:  Target = %s VA_l, Total Var = %s, switches: %s, loads: %s, power error = %s W' %
                    (target_VA_l[i], sum(loads_VA_l), switches_VA_l, loads_VA_l, error_VA_l)))
                LB_VA_l.cmd_close(switches_VA_l)
                LB_VA_l.cmd_open_all()
            else:
                error_VA_l = 0
                loads_VA_l = target_VA_l
            if c_load:
                switches_VA_c, loads_VA_c, error_VA_c = LB_VA_c.set_value(target_VA_c)
                LB_VA_c.cmd_close(switches_VA_c)
                LB_VA_c.cmd_open_all()
                print(('Capacitive:  Target = %s W, Total power = %s, switches: %s, loads: %s, power error = %s W' %
                    (target_VA_c[i], sum(loads_W), switches_W, loads_VA_c, error_W)))
            else:
                error_VA_c = 0
                loads_VA_c = target_VA_c

            print(('Target = %s W, %s inductive var, %s capacitive var at time = %s s.' %
                  (target_W[i], target_VA_l[i], target_VA_c[i], round(elapsed, 1))))

            i += 1
        else:
            time.sleep(0.05)

    if r_load:
        LB_W.cmd_open_all()
    if l_load:
        LB_VA_l.cmd_open_all()
    if c_load:
        LB_VA_c.cmd_open_all()







