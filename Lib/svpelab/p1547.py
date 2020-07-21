"""
Copyright (c) 2018, Sandia National Labs, SunSpec Alliance and CanmetENERGY(Natural Resources Canada)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

Neither the names of the Sandia National Labs, SunSpec Alliance and CanmetENERGY(Natural Resources Canada)
nor the names of its contributors may be used to endorse or promote products derived from
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
import xml.etree.ElementTree as ET
import csv
import math
import xlsxwriter
import traceback
from datetime import datetime, timedelta
from collections import OrderedDict
import time
import collections
import numpy as np
import pandas as pd
import random
# import sys
# import os
# import glob
# import importlib

VERSION = '1.4.1'
LATEST_MODIFICATION = '17th July 2020'

FW = 'FW'  # Frequency-Watt
CPF = 'CPF'  # Constant Power Factor
VW = 'VW'  # Volt_Watt
VV = 'VV'  # Volt-Var
WV = 'WV'  # Watt-Var
CRP = 'CRP'  # Constant Reactive Power
LAP = 'LAP'  # Limit Active Power
PRI = 'PRI'  # Priority
IOP = 'IOP'  # Interoperability Tests
LV = 'LV'
HV = 'HV'
CAT_2 = 'CAT_2'
CAT_3 = 'CAT_3'
VOLTAGE = 'V'
FREQUENCY = 'F'
FULL_NAME = {'V': 'Voltage',
             'P': 'Active Power',
             'Q': 'Reactive Power',
             'F': 'Frequency',
             'PF': 'Power Factor'}


class p1547Error(Exception):
    pass
"""
This section is for EUT parameters needed such as V, P, Q, etc.
"""

class EutParameters(object):
    def __init__(self, ts):
        self.ts = ts
        try:
            self.v_nom = ts.param_value('eut.v_nom')
            self.s_rated = ts.param_value('eut.s_rated')

            '''
            Minimum required accuracy (MRA) (per Table 3 of IEEE Std 1547-2018)

            Table 3 - Minimum measurement and calculation accuracy requirements for manufacturers
            ______________________________________________________________________________________________
            Time frame                  Steady-state measurements      
            Parameter       Minimum measurement accuracy    Measurement window      Range
            ______________________________________________________________________________________________        
            Voltage, RMS    (+/- 1% Vnom)                   10 cycles               0.5 p.u. to 1.2 p.u.
            Frequency       10 mHz                          60 cycles               50 Hz to 66 Hz
            Active Power    (+/- 5% Srated)                 10 cycles               0.2 p.u. < P < 1.0
            Reactive Power  (+/- 5% Srated)                 10 cycles               0.2 p.u. < Q < 1.0
            Time            1% of measured duration         N/A                     5 s to 600 s 
            ______________________________________________________________________________________________
                                        Transient measurements
            Parameter       Minimum measurement accuracy    Measurement window      Range
            Voltage, RMS    (+/- 2% Vnom)                   5 cycles                0.5 p.u. to 1.2 p.u.
            Frequency       100 mHz                         5 cycles                50 Hz to 66 Hz
            Time            2 cycles                        N/A                     100 ms < 5 s
            ______________________________________________________________________________________________
            '''
            self.MRA={
                'V': 0.01*self.v_nom,
                'Q': 0.05*ts.param_value('eut.s_rated'),
                'P': 0.05*ts.param_value('eut.s_rated'),
                'F': 0.01,
                'T': 0.01
            }

            self.MRA_V_trans = 0.02 * self.v_nom
            self.MRA_F_trans = 0.1
            self.MRA_T_trans = 2. / 60.

            if ts.param_value('eut.f_nom'):
                self.f_nom = ts.param_value('eut.f_nom')
            else:
                self.f_nom = None
            if ts.param_value('eut.phases') is not None:
                self.phases = ts.param_value('eut.phases')
            else:
                self.phases = None
            if ts.param_value('eut.p_rated') is not None:
                self.p_rated = ts.param_value('eut.p_rated')
                self.p_rated_prime = ts.param_value('eut.p_rated_prime')  # absorption power
                if self.p_rated_prime is None:
                    self.p_rated_prime = -self.p_rated
                self.p_min = ts.param_value('eut.p_min')
                self.var_rated = ts.param_value('eut.var_rated')
            else:
                self.var_rated = None
            # self.imbalance_angle_fix = imbalance_angle_fix
            self.absorb = ts.param_value('eut.abs_enabled')

        except Exception as e:
            self.ts.log_error('Incorrect Parameter value : %s' % e)
            raise

"""
This section is utility function needed to run the scripts such as data acquisition.
"""

class UtilParameters:

    def __init__(self):
        self.step_label = None
        self.pwr = 1.0
        self.curve = 1
        self.filename = None

    def reset_curve(self, curve=1):
        self.curve = curve
        self.ts.log_debug(f'P1547 Librairy curve has been set {curve}')

    def reset_pwr(self, pwr=1.0):
        self.pwr = pwr
        self.ts.log_debug(f'P1547 Librairy power level has been set {round(pwr*100)}%')

    def reset_filename(self, filename):
        self.filename = filename

    def set_step_label(self, starting_label=None):
        """
        Write step labels in alphabetical order as shown in the standard
        :param starting_label:
        :return: nothing
        """
        self.double_letter_label = False

        if starting_label is None:
            starting_label = 'a'
        starting_label_value = ord(starting_label)
        self.step_label = starting_label_value

    """
    Getter functions
    """
    def get_params(self, curve=None):

        if curve == None:
            return self.param
        else:
            return self.param[self.curve]

    def get_step_label(self):
        """
        get the step labels and increment in alphabetical order as shown in the standard
        :param: None
        :return: nothing
        """
        if self.step_label > 90:
            self.step_label = ord('A')
            self.double_letter_label = True

        if self.double_letter_label:
            step_label = 'Step {}{}'.format(chr(self.step_label), chr(self.step_label))
        else:
            step_label = 'Step {}'.format(chr(self.step_label))

        self.step_label += 1
        return step_label

    def get_measurement_label(self, type_meas):
        """
        Returns the measurement label for a measurement type

        :param type_meas:   (str) Either V, P, PF, I, F, VA, or Q
        :return:            (list of str) List of labeled measurements, e.g., ['AC_VRMS_1', 'AC_VRMS_2', 'AC_VRMS_3']
        """

        meas_root = self.type_meas[type_meas]

        if self.phases == 'Single phase':
            meas_label = [meas_root + '_1']
        elif self.phases == 'Split phase':
            meas_label = [meas_root + '_1', meas_root + '_2']
        elif self.phases == 'Three phase':
            meas_label = [meas_root + '_1', meas_root + '_2', meas_root + '_3']

        return meas_label

    def get_measurement_total(self, data, type_meas, log=False):
        """
        Sum or average the EUT values from all phases

        :param data:        dataset from data acquisition object
        :param type_meas:   Either V,P or Q
        :param log:         Boolean variable to disable or enable logging
        :return: Any measurements from the DAQ
        """
        value = None
        nb_phases = None

        try:
            if self.phases == 'Single phase':
                value = data.get(self.get_measurement_label(type_meas)[0])
                if log:
                    self.ts.log_debug('        %s are: %s'
                                      % (self.get_measurement_label(type_meas), value))
                nb_phases = 1

            elif self.phases == 'Split phase':
                value1 = data.get(self.get_measurement_label(type_meas)[0])
                value2 = data.get(self.get_measurement_label(type_meas)[1])
                if log:
                    self.ts.log_debug('        %s are: %s, %s'
                                      % (self.get_measurement_label(type_meas), value1, value2))
                value = value1 + value2
                nb_phases = 2

            elif self.phases == 'Three phase':
                value1 = data.get(self.get_measurement_label(type_meas)[0])
                value2 = data.get(self.get_measurement_label(type_meas)[1])
                value3 = data.get(self.get_measurement_label(type_meas)[2])
                if log:
                    self.ts.log_debug('        %s are: %s, %s, %s'
                                      % (self.get_measurement_label(type_meas), value1, value2, value3))
                value = value1 + value2 + value3
                nb_phases = 3

        except Exception as e:
            self.ts.log_error('Inverter phase parameter not set correctly.')
            self.ts.log_error('phases=%s' % self.phases)
            raise p1547Error('Error in get_measurement_total() : %s' % (str(e)))

        # TODO : imbalance_resp should change the way you acquire the data
        if type_meas == 'V':
            # average value of V
            value = value / nb_phases
        elif type_meas == 'F':
            # No need to do data average for frequency
            value = data.get(self.get_measurement_label(type_meas)[0])

        return round(value, 3)

    def get_script_name(self):
        if self.script_complete_name is None:
            self.script_complete_name = 'Script name not initialized'
        return self.script_complete_name


class DataLogging:
    def __init__(self, meas_values, x_criteria, y_criteria):
        self.type_meas = {'V': 'AC_VRMS', 'I': 'AC_IRMS', 'P': 'AC_P', 'Q': 'AC_Q', 'VA': 'AC_S',
                          'F': 'AC_FREQ', 'PF': 'AC_PF'}
        # Values to be recorded
        self.meas_values = meas_values
        # Values defined as target/step values which will be controlled as step
        self.x_criteria = x_criteria
        # Values defined as values which will be controlled as step
        self.y_criteria = y_criteria
        self.rslt_sum_col_name = ''
        self.sc_points = {}
        #self._config()
        self.set_sc_points()
        self.set_result_summary_name()
        self.tr = None
        self.n_tr = None
        self.initial_value = {}
        self.tr_value = collections.OrderedDict()
        self.current_step_label = None
    #def __config__(self):

    def reset_time_settings(self, tr, number_tr=2):
        self.tr = tr
        self.ts.log_debug(f'P1547 Time response has been set to {self.tr} seconds')
        self.n_tr = number_tr
        self.ts.log_debug(f'P1547 Number of Time response has been set to {self.n_tr} cycles')

    def set_sc_points(self):
        """
        Set SC points for DAS depending on which measured variables initialized and targets

        :return: None
        """
        # TODO : The target value are in percentage (0-100) and something in P.U. (0-1.0)
        #       The measure value are in absolute value

        xs = self.x_criteria
        ys = self.y_criteria
        row_data = []

        for meas_value in self.meas_values:
            row_data.append('%s_MEAS' % meas_value)

            if meas_value in xs:
                row_data.append('%s_TARGET' % meas_value)

            elif meas_value in ys:
                row_data.append('%s_TARGET' % meas_value)
                row_data.append('%s_TARGET_MIN' % meas_value)
                row_data.append('%s_TARGET_MAX' % meas_value)

        row_data.append('EVENT')
        self.ts.log_debug('Sc points: %s' % row_data)
        self.sc_points['sc'] = row_data

    def set_result_summary_name(self):
        """
        Write column names for results file depending on which test is being run
        :param nothing:
        :return: nothing
        """
        xs = self.x_criteria
        ys = self.y_criteria
        row_data = []


        # Time response criteria will take last placed value of Y variables
        if self.criteria_mode[0]:  # transient response pass/fail
            row_data.append('90%_BY_TR=1')
        if self.criteria_mode[1]:
            row_data.append('WITHIN_BOUNDS_BY_TR=1')
        if self.criteria_mode[2]:  # steady-state accuracy
            row_data.append('WITHIN_BOUNDS_BY_LAST_TR')


        for meas_value in self.meas_values:
            row_data.append('%s_MEAS' % meas_value)

            if meas_value in xs:
                row_data.append('%s_TARGET' % meas_value)

            elif meas_value in ys:
                row_data.append('%s_TARGET' % meas_value)
                row_data.append('%s_TARGET_MIN' % meas_value)
                row_data.append('%s_TARGET_MAX' % meas_value)

        row_data.append('STEP')
        row_data.append('FILENAME')

        self.rslt_sum_col_name = ','.join(row_data) + '\n'

    def get_rslt_param_plot(self):
        """
        This getters function creates and returns all the predefined columns for the plotting process
        :return: result_params
        """
        y_variables = self.y_criteria
        y2_variables = self.x_criteria

        # For VV, VW and FW
        y_points = []
        y2_points = []
        y_title = []
        y2_title = []

        #y_points = '%s_TARGET,%s_MEAS' % (y, y)
        #y2_points = '%s_TARGET,%s_MEAS' % (y2, y2)

        for y in y_variables:
            self.ts.log_debug('y_temp: %s' % y)
            #y_temp = self.get_measurement_label('%s' % y)
            y_temp = '{}'.format(','.join(str(x) for x in self.get_measurement_label('%s' % y)))
            y_title.append(FULL_NAME[y])
            y_points.append(y_temp)
        self.ts.log_debug('y_points: %s' % y_points)
        y_points = ','.join(y_points)
        y_title = ','.join(y_title)

        for y2 in y2_variables:
            self.ts.log_debug('y2_variable for result: %s' % y2)
            y2_temp = '{}'.format(','.join(str(x) for x in self.get_measurement_label('%s' % y2)))
            y2_title.append(FULL_NAME[y2])
            y2_points.append(y2_temp)
        y2_points = ','.join(y2_points)
        y2_title = ','.join(y2_title)

        result_params = {
            'plot.title': 'title_name',
            'plot.x.title': 'Time (sec)',
            'plot.x.points': 'TIME',
            'plot.y.points': y_points,
            'plot.y.title': y_title,
            'plot.y2.points': y2_points,
            'plot.y2.title': y2_title,
            'plot.%s_TARGET.min_error' % y: '%s_TARGET_MIN' % y,
            'plot.%s_TARGET.max_error' % y: '%s_TARGET_MAX' % y,
        }

        return result_params

    def get_sc_points(self):
        """
        This getters function returns the sc points for DAS
        :return:            self.sc_points
        """
        return self.sc_points

    def get_rslt_sum_col_name(self):
        """
        This getters function returns the column name for result_summary.csv
        :return:            self.rslt_sum_col_name
        """
        return self.rslt_sum_col_name

    def write_rslt_sum(self):
        """
        Combines the analysis results, the step label and the filenamoe to return
        a row that will go in result_summary.csv
        :param analysis: Dictionary with all the information for result summary

        :param step:   test procedure step letter or number (e.g "Step G")
        :param filename: the dataset filename use for analysis

        :return: row_data a string with all the information for result_summary.csv
        """

        xs = self.x_criteria
        ys = self.y_criteria
        first_iter = self.tr_value['FIRST_ITER']
        last_iter = self.tr_value['LAST_ITER']
        row_data = []


        # Time response criteria will take last placed value of Y variables
        if self.criteria_mode[0]:
            row_data.append(str(self.tr_value['TR_90_%_PF']))
        if self.criteria_mode[1]:
            row_data.append(str(self.tr_value['%s_TR_%s_PF' % (ys[-1], first_iter)]))
        if self.criteria_mode[2]:
            row_data.append(str(self.tr_value['%s_TR_%s_PF' % (ys[-1], last_iter)]))

        # Default measured values are V, P and Q (F can be added) refer to set_meas_variable function
        for meas_value in self.meas_values:
            row_data.append(str(self.tr_value['%s_TR_%d' % (meas_value, last_iter)]))
            # Variables needed for variations
            if meas_value in xs:
                row_data.append(str(self.tr_value['%s_TR_TARG_%d' % (meas_value, last_iter)]))
            # Variables needed for criteria verifications with min max passfail
            if meas_value in ys:
                row_data.append(str(self.tr_value['%s_TR_TARG_%s' % (meas_value, last_iter)]))
                row_data.append(str(self.tr_value['%s_TR_%s_MIN' % (meas_value, last_iter)]))
                row_data.append(str(self.tr_value['%s_TR_%s_MAX' % (meas_value, last_iter)]))

        row_data.append(self.current_step_label)
        row_data.append(str(self.filename))
        #self.ts.log_debug(f'rowdata={row_data}')
        row_data_str = ','.join(row_data) + '\n'

        return row_data_str

        # except Exception as e:
        #     raise p1547Error('Error in write_rslt_sum() : %s' % (str(e)))

    def start(self, daq, step_label):
        """
        Sum the EUT reactive power from all phases
        :param daq:         data acquisition object from svpelab library
        :param step:        test procedure step letter or number (e.g "Step G")
        :return: returns a dictionary with the timestamp, event and total EUT reactive power
        """
        # TODO : In a more sophisticated approach, get_initial['timestamp'] will come from a
        #  reliable secure thread or data acquisition timestamp

        self.initial_value['timestamp'] = datetime.now()
        self.current_step_label = step_label
        daq.data_sample()
        data = daq.data_capture_read()
        daq.sc['event'] = self.current_step_label
        if isinstance(self.x_criteria, list):
            for xs in self.x_criteria:
                self.initial_value[xs] = {'x_value': self.get_measurement_total(data=data, type_meas=xs, log=False)}
                daq.sc['%s_MEAS' % xs] = self.initial_value[xs]['x_value']
        else:
            self.initial_value[self.x_criteria] = {'x_value': self.get_measurement_total(data=data, type_meas=self.x_criteria, log=False)}
            daq.sc['%s_MEAS' % self.x_criteria] = self.initial_value[self.x_criteria]['x_value']
        if isinstance(self.y_criteria, list):
            for ys in self.y_criteria:
                self.initial_value[ys] = {'y_value': self.get_measurement_total(data=data, type_meas=ys, log=False)}
                daq.sc['%s_MEAS' % ys] = self.initial_value[ys]["y_value"]
        else:
            self.initial_value[self.y_criteria] = {'y_value': self.get_measurement_total(data=data, type_meas=self.y_criteria, log=False)}
            daq.sc['%s_MEAS' % self.y_criteria] = self.initial_value[self.y_criteria]['y_value']
        daq.data_sample()

        #return self.initial_value

    def record_timeresponse(self, daq, step_value, pwr_lvl=1.0, curve=1, x_target=None, y_target=None):
        """
        Get the data from a specific time response (tr) corresponding to x and y values returns a dictionary
        but also writes in the soft channels of the DAQ system
        :param daq:             data acquisition object from svpelab library
        :param initial_value:   the dictionary with the initial values (X, Y and timestamp)
        :param pwr_lvl:         The input power level in p.u.
        :param curve:           The characteristic curve number
        :param x_target:        The target value of X value (e.g. FW -> f_step)
        :param y_target:        The target value of Y value (e.g. LAP -> act_pwrs_limits)
        :param n_tr:            The number of time responses used to validate the response and steady state values

        :return: returns a dictionary with the timestamp, event and total EUT reactive power
        """

        x = self.x_criteria
        y = self.y_criteria
        #self.tr = tr

        first_tr = self.initial_value['timestamp'] + timedelta(seconds=self.tr)
        tr_list = [first_tr]

        for i in range(self.n_tr - 1):
            tr_list.append(tr_list[i] + timedelta(seconds=self.tr))
            for meas_value in self.meas_values:
                self.tr_value['%s_TR_%s' % (meas_value, i)] = None
                if meas_value in x:
                    self.tr_value['%s_TR_TARG_%s' % (meas_value, i)] = None
                elif meas_value in y:
                    self.tr_value['%s_TR_TARG_%s' % (meas_value, i)] = None
                    self.tr_value['%s_TR_%s_MIN' % (meas_value, i)] = None
                    self.tr_value['%s_TR_%s_MAX' % (meas_value, i)] = None
        tr_iter = 1
        for tr_ in tr_list:
            #self.ts.log_debug(f'tr_={tr_list}')
            now = datetime.now()
            if now <= tr_:
                time_to_sleep = tr_ - datetime.now()
                self.ts.log('Waiting %s seconds to get the next Tr data for analysis...' %
                            time_to_sleep.total_seconds())
                self.ts.sleep(time_to_sleep.total_seconds())
            daq.data_sample()  # sample new data
            data = daq.data_capture_read()  # Return dataset created from last data capture
            daq.sc['EVENT'] = "{0}_TR_{1}".format(self.current_step_label, tr_iter)

            # update daq.sc values for Y_TARGET, Y_TARGET_MIN, and Y_TARGET_MAX

            # store the daq.sc['Y_TARGET'], daq.sc['Y_TARGET_MIN'], and daq.sc['Y_TARGET_MAX'] in tr_value

            for meas_value in self.meas_values:
                try:
                    self.tr_value['%s_TR_%s' % (meas_value, tr_iter)] = daq.sc['%s_MEAS' % meas_value]

                    self.ts.log('Value %s: %s' % (meas_value, daq.sc['%s_MEAS' % meas_value]))
                    if meas_value in x:
                        daq.sc['%s_TARGET' % meas_value] = step_value
                        self.tr_value['%s_TR_TARG_%s' % (meas_value, tr_iter)] = step_value
                        self.ts.log('X Value (%s) = %s' % (meas_value, daq.sc['%s_MEAS' % meas_value]))
                    elif meas_value in y:
                        daq.sc['%s_TARGET' % meas_value] = self.update_target_value(step_value)
                        daq.sc['%s_TARGET_MIN' % meas_value], daq.sc[
                            '%s_TARGET_MAX' % meas_value] = self.calculate_min_max_values(daq=daq, data=data)
                        self.tr_value[f'{meas_value}_TR_TARG_{tr_iter}'] = daq.sc['%s_TARGET' % meas_value]
                        self.tr_value[f'{meas_value}_TR_{tr_iter}_MIN'] = daq.sc['%s_TARGET_MIN' % meas_value]
                        self.tr_value[f'{meas_value}_TR_{tr_iter}_MAX'] = daq.sc['%s_TARGET_MAX' % meas_value]
                        self.ts.log('Y Value (%s) = %s. Pass/fail bounds = [%s, %s]' %
                                     (meas_value, daq.sc['%s_MEAS' % meas_value],
                                      daq.sc['%s_TARGET_MIN' % meas_value], daq.sc['%s_TARGET_MAX' % meas_value]))
                except Exception as e:
                    self.ts.log_debug('Measured value (%s) not recorded: %s' % (meas_value, e))

            #self.tr_value[tr_iter]["timestamp"] = tr_
            self.tr_value[f'timestamp_{tr_iter}'] = tr_
            self.tr_value['LAST_ITER'] = tr_iter
            tr_iter = tr_iter + 1

        self.tr_value['FIRST_ITER'] = 1

        return self.tr_value

        # except Exception as e:
        #    raise p1547Error('Error in get_tr_data(): %s' % (str(e)))


class CriteriaValidation:
    def __init__(self, criteria):
        self.criteria_mode = criteria

    def evaluate_criterias(self):
        if self.criteria_mode[0] is True:
            self.open_loop_resp_criteria()
        if self.criteria_mode[1] is True or self.criteria_mode[2] is True:
            self.result_accuracy_criteria()

    def calculate_open_loop_value(self, y0, y_ss, duration, tr):
        """
        Calculated the anticipated Y(Tr +/- MRA_T) values based on duration and Tr

        Note: for a unit step response Y(t) = 1 - exp(-t/tau) where tau is the time constant

        :param y0: initial Y(0) value
        :param y_ss: steady-state solution, e.g., Y(infinity)
        :param duration: time since the change in the input parameter that the output should be calculated
        :param tr: open loop response time (90% change or 2.3 * time constant)

        :return: output Y(duration) anticipated based on the open loop response function
        """

        time_const = tr / (-(math.log(0.1)))  # ~2.3 * time constants to reach the open loop response time in seconds
        number_of_taus = duration / time_const  # number of time constants into the response
        resp_fraction = 1 - math.exp(-number_of_taus)  # fractional response after the duration, e.g. 90%

        # Y must be 90% * (Y_final - Y_initial) + Y_initial
        resp = (y_ss - y0) * resp_fraction + y0  # expand to y units

        return resp

    def open_loop_resp_criteria(self, tr=1):
        """
        TRANSIENT: Open Loop Time Response (OLTR) = 90% of (y_final-y_initial) + y_initial

            The variable y_tr is the value used to verify the time response requirement.
            |----------|----------|----------|----------|
                     1st tr     2nd tr     3rd tr     4th tr
            |          |          |
            y_initial  y_tr       y_final_tr

            (1547.1)After each step, the open loop response time, Tr, is evaluated.
            The expected output, Y(Tr), at one times the open loop response time,
            is calculated as 90%*(Y_final_tr - Y_initial ) + Y_initial
        """

        y = self.y_criteria[0]
        mra_y = self.MRA[y]

        duration = self.tr_value[f"timestamp_{tr}"] - self.initial_value['timestamp']
        duration = duration.total_seconds()
        self.ts.log('Calculating pass/fail for Tr = %s sec, with a target of %s sec' %
                    (duration, tr))

        # Given that Y(time) is defined by an open loop response characteristic, use that curve to
        # calculated the target, minimum, and max, based on the open loop response expectation
        if self.script_name == CRP:  # for those tests with a flat 90% evaluation
            y_start = 0.0  # only look at 90% of target
            mra_t = 0  # direct 90% evaluation without consideration of MRA(time)
        else:
            #self.ts.log_debug(f'{self.initial_value[y]}')
            y_start = self.initial_value[y]['y_value']
            #y_start = tr_value['%s_INITIAL' % y]
            mra_t = self.MRA['T'] * duration  # MRA(X) = MRA(time) = 0.01*duration

        y_ss = self.tr_value[f'{y}_TR_TARG_{tr}']
        y_target = self.calculate_open_loop_value(y0=y_start, y_ss=y_ss, duration=duration, tr=tr)  # 90%
        y_meas = self.tr_value[f'{y}_TR_{tr}']
        self.ts.log_debug(f'y_target = {y_target:.2f}, y_ss [{y_ss:.2f}], y_start [{y_start:.2f}], duration = {duration}, tr={tr}')

        if y_start <= y_target:  # increasing values of y
            increasing = True
            # Y(time) = open loop curve, so locate the Y(time) value on the curve
            y_min = self.calculate_open_loop_value(y0=y_start, y_ss=y_ss,
                                             duration=duration - 1.5 * mra_t, tr=tr) - 1.5 * mra_y
            # Determine maximum value based on the open loop response expectation
            y_max = self.calculate_open_loop_value(y0=y_start, y_ss=y_ss,
                                             duration=duration + 1.5 * mra_t, tr=tr) + 1.5 * mra_y
        else:  # decreasing values of y
            increasing = False
            # Y(time) = open loop curve, so locate the Y(time) value on the curve
            y_min = self.calculate_open_loop_value(y0=y_start, y_ss=y_ss,
                                             duration=duration + 1.5 * mra_t, tr=tr) - 1.5 * mra_y
            # Determine maximum value based on the open loop response expectation
            y_max = self.calculate_open_loop_value(y0=y_start, y_ss=y_ss,
                                             duration=duration - 1.5 * mra_t, tr=tr) + 1.5 * mra_y

        # pass/fail applied to the open loop time response
        if self.script_name == CRP:  # 1-sided analysis
            # Pass: Ymin <= Ymeas when increasing y output
            # Pass: Ymeas <= Ymax when decreasing y output
            if increasing:
                if y_min <= y_meas:
                    self.tr_value['TR_90_%_PF'] = 'Pass'
                else:
                    self.tr_value['TR_90_%_PF'] = 'Fail'
                self.ts.log_debug('Transient y_targ = %s, y_min [%s] <= y_meas [%s] = %s' %
                                  (y_target, y_min, y_meas, self.tr_value['TR_90_%_PF']))
            else:  # decreasing
                if y_meas <= y_max:
                    self.tr_value['TR_90_%_PF'] = 'Pass'
                else:
                    self.tr_value['TR_90_%_PF'] = 'Fail'
                self.ts.log_debug('Transient y_targ = %s, y_meas [%s] <= y_max [%s] = %s'
                                  % (y_target, y_meas, y_max, self.tr_value['TR_90_%_PF']))

        else:  # 2-sided analysis
            # Pass/Fail: Ymin <= Ymeas <= Ymax
            if y_min <= y_meas <= y_max:
                self.tr_value['TR_90_%_PF'] = 'Pass'
            else:
                self.tr_value['TR_90_%_PF'] = 'Fail'
            display_value_p1 = f'Transient y_targ ={y_target:.2f}, y_min [{y_min:.2f}] <= y_meas'
            display_value_p2 = f'[{y_meas:.2f}] <= y_max [{y_max:.2f}] = {self.tr_value["TR_90_%_PF"]}'

            self.ts.log_debug(f'{display_value_p1} {display_value_p2}')

    def result_accuracy_criteria(self):

        # Note: Note sure where criteria_mode[1] (SS accuracy after 1 Tr) is used in IEEE 1547.1
        for y in self.y_criteria:
            for tr_iter in range(self.tr_value['FIRST_ITER'], self.tr_value['LAST_ITER']+1):

                if (self.tr_value['FIRST_ITER'] == tr_iter and self.criteria_mode[1]) or \
                        (self.tr_value['LAST_ITER'] == tr_iter and self.criteria_mode[2]):


                    # pass/fail assessment for the steady-state values
                    #self.ts.log_debug(f'current iter={tr_iter}')
                    if self.tr_value['%s_TR_%s_MIN' % (y, tr_iter)] <= \
                            self.tr_value['%s_TR_%s' % (y, tr_iter)] <= self.tr_value['%s_TR_%s_MAX' % (y, tr_iter)]:
                        self.tr_value['%s_TR_%s_PF' % (y, tr_iter)] = 'Pass'
                    else:
                        self.tr_value['%s_TR_%s_PF' % (y, tr_iter)] = 'Fail'

                    self.ts.log('  Steady state %s(Tr_%s) evaluation: %0.1f <= %0.1f <= %0.1f  [%s]' % (
                        y,
                        tr_iter,
                        self.tr_value['%s_TR_%s_MIN' % (y, tr_iter)],
                        self.tr_value['%s_TR_%s' % (y, tr_iter)],
                        self.tr_value['%s_TR_%s_MAX' % (y, tr_iter)],
                        self.tr_value['%s_TR_%s_PF' % (y, tr_iter)]))


class ImbalanceComponent:

    def __init__(self):
        self.mag = {}
        self.ang = {}

    def set_imbalance_config(self, imbalance_angle_fix=None):
        """
        Initialize the case possibility for imbalance test either with fix 120 degrees for the angle or
        with a calculated angles that would result in a null sequence zero

        :param imbalance_angle_fix:   string (Yes or No)
        if Yes, angle are fix at 120 degrees for both cases.
        if No, resulting sequence zero will be null for both cases.

        :return: None
        """

        '''
                                            Table 24 - Imbalanced Voltage Test Cases
                +-----------------------------------------------------+-----------------------------------------------+
                | Phase A (p.u.)  | Phase B (p.u.)  | Phase C (p.u.)  | In order to keep V0 magnitude                 |
                |                 |                 |                 | and angle at 0. These parameter can be used.  |
                +-----------------+-----------------+-----------------+-----------------------------------------------+
                |       Mag       |       Mag       |       Mag       | Mag   | Ang  | Mag   | Ang   | Mag   | Ang    |
        +-------+-----------------+-----------------+-----------------+-------+------+-------+-------+-------+--------+
        |Case A |     >= 1.07     |     <= 0.91     |     <= 0.91     | 1.08  | 0.0  | 0.91  |-126.59| 0.91  | 126.59 |
        +-------+-----------------+-----------------+-----------------+-------+------+-------+-------+-------+--------+
        |Case B |     <= 0.91     |     >= 1.07     |     >= 1.07     | 0.9   | 0.0  | 1.08  |-114.5 | 1.08  | 114.5  |
        +-------+-----------------+-----------------+-----------------+-------+------+-------+-------+-------+--------+

        For tests with imbalanced, three-phase voltages, the manufacturer shall state whether the EUT responds
        to individual phase voltages, or the average of the three-phase effective (RMS) values or the positive
        sequence of voltages. For EUTs that respond to individual phase voltages, the response of each
        individual phase shall be evaluated. For EUTs that response to the average of the three-phase effective
        (RMS) values mor the positive sequence of voltages, the total three-phase reactive and active power
        shall be evaluated.
        '''
        try:
            if imbalance_angle_fix == 'std':
                # Case A
                self.mag['case_a'] = [1.07 * self.v_nom, 0.91 * self.v_nom, 0.91 * self.v_nom]
                self.ang['case_a'] = [0., 120, -120]
                # Case B
                self.mag['case_b'] = [0.91 * self.v_nom, 1.07 * self.v_nom, 1.07 * self.v_nom]
                self.ang['case_b'] = [0., 120.0, -120.0]
                self.ts.log("Setting test with imbalanced test with FIXED angles/values")
            elif imbalance_angle_fix == 'fix_mag':
                # Case A
                self.mag['case_a'] = [1.07 * self.v_nom, 0.91 * self.v_nom, 0.91 * self.v_nom]
                self.ang['case_a'] = [0., 126.59, -126.59]
                # Case B
                self.mag['case_b'] = [0.91 * self.v_nom, 1.07 * self.v_nom, 1.07 * self.v_nom]
                self.ang['case_b'] = [0., 114.5, -114.5]
                self.ts.log("Setting test with imbalanced test with NOT FIXED angles/values")
            elif imbalance_angle_fix == 'fix_ang':
                # Case A
                self.mag['case_a'] = [1.08 * self.v_nom, 0.91 * self.v_nom, 0.91 * self.v_nom]
                self.ang['case_a'] = [0., 120, -120]
                # Case B
                self.mag['case_b'] = [0.9 * self.v_nom, 1.08 * self.v_nom, 1.08 * self.v_nom]
                self.ang['case_a'] = [0., 120, -120]
                self.ts.log("Setting test with imbalanced test with NOT FIXED angles/values")
            elif imbalance_angle_fix == 'not_fix':
                # Case A
                self.mag['case_a'] = [1.08 * self.v_nom, 0.91 * self.v_nom, 0.91 * self.v_nom]
                self.ang['case_a'] = [0., 126.59, -126.59]
                # Case B
                self.mag['case_b'] = [0.9 * self.v_nom, 1.08 * self.v_nom, 1.08 * self.v_nom]
                self.ang['case_b'] = [0., 114.5, -114.5]
                self.ts.log("Setting test with imbalanced test with NOT FIXED angles/values")

            #return (self.mag, self.ang)
        except Exception as e:
            self.ts.log_error('Incorrect Parameter value : %s' % e)
            raise

    def set_grid_asymmetric(self, grid, case, imbalance_resp='AVG_3PH_RMS'):
        """
        Configure the grid simulator to change the magnitude and angles.
        :param grid:   A gridsim object from the svpelab library
        :param case:   string (case_a or case_b)
        :return: nothing
        """
        self.ts.log_debug(f'mag={self.mag}')
        self.ts.log_debug(f'grid={grid}')
        self.ts.log_debug(f'imbalance_resp={imbalance_resp}')

        if grid is not None:
            grid.config_asymmetric_phase_angles(mag=self.mag[case], angle=self.ang[case])
        if imbalance_resp == 'AVG_3PH_RMS':
            self.ts.log_debug(f'mag={self.mag[case]}')
            return round(sum(self.mag[case])/3.0,2)
        elif imbalance_resp is 'INDIVIDUAL_PHASES_VOLTAGES':
            #TODO TO BE COMPLETED
            pass
        elif imbalance_resp is 'POSITIVE_SEQUENCE_VOLTAGES':
            #TODO to be completed
            pass
"""
Section for criteria validation
"""
"""
class PassFail:
    def __init__(self):
"""
"""
Section reserved for HIL model object
"""

class HilModel(object):
    def __init__(self, ts, support_interfaces):
        self.params = {}
        self.parameters_dic = {}
        self.mode = []
        self.ts = ts
        self.start_time = None
        self.stop_time = None
        if support_interfaces.get('hil') is not None:
            self.hil = support_interfaces.get('hil')
        else:
            self.hil = None

    def set_model_on(self):
        """
        Set the HIL model on
        """
        model_name = self.params["model_name"]
        self.hil.set_params(model_name + "/SM_Source/SVP Commands/mode/Value", 3)

    """
    Getter functions
    """

    def get_model_parameters(self, current_mode):
        self.ts.log(f'Getting HIL parameters for {current_mode}')
        return self.parameters_dic[current_mode], self.start_time, self.stop_time

    def get_waveform_config(self, current_mode, offset):
        params = {}
        params["start_time_value"] = float(self.start_time - offset)
        params["end_time_value"] = float(self.stop_time + offset)
        params["start_time_variable"] = "Tstart"
        params["end_time_variable"] = "Tend"
        return params

"""
This section is for Voltage stabilization function such as VV, VW, CPF and CRP
"""

class VoltVar(EutParameters, UtilParameters, DataLogging, CriteriaValidation, ImbalanceComponent):
    """
    param curve: choose curve characterization [1-3] 1 is default
    """

    # Default curve initialization will be 1
    def __init__(self, ts, imbalance=False):
        self.ts = ts
        self.criteria_mode = [True, True, True]
        EutParameters.__init__(self, ts)
        UtilParameters.__init__(self)
        DataLogging.__init__(self, meas_values=['V', 'Q'], x_criteria=['V'], y_criteria=['Q'])
        CriteriaValidation.__init__(self, self.criteria_mode)
        if imbalance:
            ImbalanceComponent.__init__(self)
        self.pairs = {}
        self.param = [0, 0, 0, 0]
        self.target_dict = []
        self.script_name = VV
        self.script_complete_name = 'Volt-Var'
        self._config()

    def _config(self):
        self.set_params()
        # Create the pairs need
        # self.set_imbalance_config()

    def set_params(self):
        self.param[1] = {
            'V1': round(0.92 * self.v_nom, 2),
            'V2': round(0.98 * self.v_nom, 2),
            'V3': round(1.02 * self.v_nom, 2),
            'V4': round(1.08 * self.v_nom, 2),
            'Q1': round(self.s_rated * 0.44, 2),
            'Q2': round(self.s_rated * 0.0, 2),
            'Q3': round(self.s_rated * 0.0, 2),
            'Q4': round(self.s_rated * -0.44, 2)
        }

        self.param[2] = {
            'V1': round(0.88 * self.v_nom, 2),
            'V2': round(1.04 * self.v_nom, 2),
            'V3': round(1.07 * self.v_nom, 2),
            'V4': round(1.10 * self.v_nom, 2),
            'Q1': round(self.var_rated * 1.0, 2),
            'Q2': round(self.var_rated * 0.5, 2),
            'Q3': round(self.var_rated * 0.5, 2),
            'Q4': round(self.var_rated * -1.0, 2)
        }
        self.param[3] = {
            'V1': round(0.90 * self.v_nom, 2),
            'V2': round(0.93 * self.v_nom, 2),
            'V3': round(0.96 * self.v_nom, 2),
            'V4': round(1.10 * self.v_nom, 2),
            'Q1': round(self.var_rated * 1.0, 2),
            'Q2': round(self.var_rated * -0.5, 2),
            'Q3': round(self.var_rated * -0.5, 2),
            'Q4': round(self.var_rated * -1.0, 2)
        }

    def update_target_value(self, value):

        x = [self.param[self.curve]['V1'], self.param[self.curve]['V2'],
             self.param[self.curve]['V3'], self.param[self.curve]['V4']]
        y = [self.param[self.curve]['Q1'], self.param[self.curve]['Q2'],
             self.param[self.curve]['Q3'], self.param[self.curve]['Q4']]
        q_value = float(np.interp(value, x, y))
        q_value *= self.pwr
        return round(q_value, 1)

    def calculate_min_max_values(self, daq, data):
        y = 'Q'
        v_meas = self.get_measurement_total(data=data, type_meas='V', log=False)
        target_min = self.update_target_value(v_meas + self.MRA['V'] * 1.5) - (self.MRA['Q'] * 1.5)
        target_max = self.update_target_value(v_meas - self.MRA['V'] * 1.5) + (self.MRA['Q'] * 1.5)

        return target_min, target_max

class VoltWatt(EutParameters, UtilParameters, DataLogging, ImbalanceComponent):
    """
    param curve: choose curve characterization [1-3] 1 is default
    """
    # Default curve initialization will be 1
    def __init__(self, ts, curve=1):
        EutParameters.__init__(self, ts)
        self.curve = curve
        self.pairs = {}
        self.param = [0, 0, 0, 0]
        self.target_dict = []
        self.script_name = VW
        self.script_complete_name = 'Volt-Watt'
        self.rslt_sum_col_name = 'P_TR_ACC_REQ, TR_REQ, P_FINAL_ACC_REQ, V_MEAS, P_MEAS, P_TARGET, P_TARGET_MIN,' \
                                 'P_TARGET_MAX, STEP, FILENAME\n'
        self.criteria_mode = [True, True, True]
        # Values to be recorded
        self.meas_values = ['V', 'P']
        # Values defined as target/step values which will be controlled as step
        self.x_criteria = ['V']
        # Values defined as values which will be controlled as step
        self.y_criteria = ['P']
        self._config()

    def _config(self):
        self.set_params()
        # Create the pairs need
        # self.set_imbalance_config()

    def set_params(self):
        self.param[1] = {
            'V1': round(1.06 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }
        self.param[2] = {
            'V1': round(1.05 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }
        self.param[3] = {
            'V1': round(1.09 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }

class ConstantPowerFactor(EutParameters, UtilParameters, ImbalanceComponent):
    def __init__(self, ts, curve=1):
        EutParameters.__init__(self, ts)
        self.curve = curve
        self.pairs = {}
        self.param = [0, 0, 0, 0]
        self.target_dict = []
        self.script_name = VW
        self.script_complete_name = 'Volt-Watt'
        self.rslt_sum_col_name = 'P_TR_ACC_REQ, TR_REQ, P_FINAL_ACC_REQ, V_MEAS, P_MEAS, P_TARGET, P_TARGET_MIN,' \
                                 'P_TARGET_MAX, STEP, FILENAME\n'
        self.criteria_mode = [True, True, True]
        # Values to be recorded
        self.meas_values = ['V', 'P']
        # Values defined as target/step values which will be controlled as step
        self.x_criteria = ['V']
        # Values defined as values which will be controlled as step
        self.y_criteria = ['P']
        self._config()

    def _config(self):
        self.set_params()
        # Create the pairs need
        # self.set_imbalance_config()

    def set_params(self):
        self.param[1] = {
            'V1': round(1.06 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }
        self.param[2] = {
            'V1': round(1.05 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }
        self.param[3] = {
            'V1': round(1.09 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }

class ConstantReactivePower(EutParameters, UtilParameters, ImbalanceComponent):
    def __init__(self, ts, curve=1):
        EutParameters.__init__(self, ts)
        self.curve = curve
        self.pairs = {}
        self.param = [0, 0, 0, 0]
        self.target_dict = []
        self.script_name = VW
        self.script_complete_name = 'Volt-Watt'
        self.rslt_sum_col_name = 'P_TR_ACC_REQ, TR_REQ, P_FINAL_ACC_REQ, V_MEAS, P_MEAS, P_TARGET, P_TARGET_MIN,' \
                                 'P_TARGET_MAX, STEP, FILENAME\n'
        self.criteria_mode = [True, True, True]
        # Values to be recorded
        self.meas_values = ['V', 'P']
        # Values defined as target/step values which will be controlled as step
        self.x_criteria = ['V']
        # Values defined as values which will be controlled as step
        self.y_criteria = ['P']
        self._config()

    def _config(self):
        self.set_params()
        # Create the pairs need
        # self.set_imbalance_config()

    def set_params(self):
        self.param[1] = {
            'V1': round(1.06 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }
        self.param[2] = {
            'V1': round(1.05 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }
        self.param[3] = {
            'V1': round(1.09 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }

"""
This section is for 
"""

class FrequencyWatt(EutParameters, UtilParameters):
    def __init__(self, ts, curve=1):
        EutParameters.__init__(self, ts)
        self.curve = curve
        self.pairs = {}
        self.param = [0, 0, 0, 0]
        self.target_dict = []
        self.script_name = VW
        self.script_complete_name = 'Volt-Watt'
        self.rslt_sum_col_name = 'P_TR_ACC_REQ, TR_REQ, P_FINAL_ACC_REQ, F_MEAS, P_MEAS, P_TARGET, P_TARGET_MIN,' \
                                 'P_TARGET_MAX, STEP, FILENAME\n'
        self.criteria_mode = [True, True, True]
        # Values to be recorded
        self.meas_values = ['F', 'P']
        # Values defined as target/step values which will be controlled as step
        self.x_criteria = ['F']
        # Values defined as values which will be controlled as step
        self.y_criteria = ['P']
        self._config()

    def _config(self):
        self.set_params()
        # Create the pairs need
        # self.set_imbalance_config()

    def set_params(self):
        p_small = self.ts.param_value('eut_fw.p_small')
        if p_small is None:
            p_small = 0.05

        self.param[1] = {
            'dbf': 0.036,
            'kof': 0.05,
            'tr': self.ts.param_value('fw.test_1_tr'),
            'f_small': p_small * self.f_nom * 0.05
        }
        self.param[2] = {
            'dbf': 0.017,
            'kof': 0.03,
            'tr': self.ts.param_value('fw.test_2_tr'),
            'f_small': p_small * self.f_nom * 0.02
        }

class Interoperability(EutParameters, UtilParameters):
    def __init__(self, ts, curve=1):
        EutParameters.__init__(self, ts)
        self.curve = curve
        self.pairs = {}
        self.param = [0, 0, 0, 0]
        self.target_dict = []
        self.script_name = VW
        self.script_complete_name = 'Volt-Watt'
        self.rslt_sum_col_name = 'P_TR_ACC_REQ, TR_REQ, P_FINAL_ACC_REQ, V_MEAS, P_MEAS, P_TARGET, P_TARGET_MIN,' \
                                 'P_TARGET_MAX, STEP, FILENAME\n'
        self.criteria_mode = [True, True, True]
        # Values to be recorded
        self.meas_values = ['V', 'P']
        # Values defined as target/step values which will be controlled as step
        self.x_criteria = ['V']
        # Values defined as values which will be controlled as step
        self.y_criteria = ['P']
        self._config()

    def _config(self):
        self.set_params()
        # Create the pairs need
        # self.set_imbalance_config()

    def set_params(self):
        self.param[1] = {
            'V1': round(1.06 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }
        self.param[2] = {
            'V1': round(1.05 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }
        self.param[3] = {
            'V1': round(1.09 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }

class WattVar(EutParameters, UtilParameters):
    def __init__(self, ts, curve=1):
        EutParameters.__init__(self, ts)
        self.curve = curve
        self.pairs = {}
        self.param = [0, 0, 0, 0]
        self.target_dict = []
        self.script_name = VW
        self.script_complete_name = 'Volt-Watt'
        self.rslt_sum_col_name = 'P_TR_ACC_REQ, TR_REQ, P_FINAL_ACC_REQ, V_MEAS, P_MEAS, P_TARGET, P_TARGET_MIN,' \
                                 'P_TARGET_MAX, STEP, FILENAME\n'
        self.criteria_mode = [True, True, True]
        # Values to be recorded
        self.meas_values = ['V', 'P']
        # Values defined as target/step values which will be controlled as step
        self.x_criteria = ['V']
        # Values defined as values which will be controlled as step
        self.y_criteria = ['P']
        self._config()

    def _config(self):
        self.set_params()
        # Create the pairs need
        # self.set_imbalance_config()

    def set_params(self):
        self.param[1] = {
            'V1': round(1.06 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }
        self.param[2] = {
            'V1': round(1.05 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }
        self.param[3] = {
            'V1': round(1.09 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }


"""
This section is for Ride-Through test
"""


class VoltageRideThrough(HilModel, EutParameters,DataLogging):
    def __init__(self,ts,support_interfaces):
        EutParameters.__init__(self, ts)
        HilModel.__init__(self,ts, support_interfaces)
        self._config()

    def _config(self):
        self.set_vrt_params()
        self.set_vrt_modes()

    """
    Setter functions
    """

    def set_vrt_params(self):
        try:
            # RT test parameters
            self.params["lv_mode"] = self.ts.param_value('vrt.lv_ena')
            self.params["hv_mode"] = self.ts.param_value('vrt.hv_ena')
            self.params["categories"] = self.ts.param_value('vrt.cat')
            self.params["range_steps"] = self.ts.param_value('vrt.range_steps')
            self.params["eut_startup_time"] = self.ts.param_value('eut.startup_time')
            self.params["model_name"] = self.hil.rt_lab_model
            self.params["range_steps"] = self.ts.param_value('vrt.range_steps')
        except Exception as e:
            self.ts.log_error('Incorrect Parameter value : %s' % e)
            raise

    def set_vrt_model_parameters(self):
        tc = self.params["test_condition"]
        mn = self.params["model_name"]
        parameters = []
        # Enable VRT mode in the IEEE1547_fast_functions model
        parameters.append((mn + '/SM_Source/SVP Commands/mode/Value',3))
        self.ts.log_debug(tc)
        self.params["vrt_start_time"] = tc.head(1)["StartTime"].item()
        self.params["vrt_stop_time"] = tc.tail(1)["StopTime"].item()
        # Add ROCOM only for LVRT CAT II
        if self.params["lv_mode"] == 'Enabled' and (self.params["categories"] == CAT_2 or self.params["categories"] == 'Both'):
            parameters.append((mn + '/SM_Source/Waveform_Generator/ROCOM_ENABLE/Value',1))
            # 0.115 p.u. Volt per second
            parameters.append((mn + '/SM_Source/Waveform_Generator/ROCOM_VALUE/Value',0.115*self.v_nom))
            parameters.append((mn + '/SM_Source/Waveform_Generator/ROCOM_INIT/Value',tc.loc["D"]["Voltage"].item()))
            parameters.append((mn + '/SM_Source/Waveform_Generator/ROCOM_START_TIME/Value', tc.loc["E"]["StartTime"].item()))
            parameters.append((mn + '/SM_Source/Waveform_Generator/ROCOM_END_TIME/Value', tc.loc["E"]["StopTime"].item()))
        for index, row in tc.iterrows():
            # Enable needed conditions
            parameters.append((mn + f'/SM_Source/VRT/VRT_State_Machine/Condition_{index}_Enable/Value', 1))
            # Start time of condition
            parameters.append((mn + f'/SM_Source/VRT/VRT_State_Machine/Condition_{index}_Time/Threshold', row["StartTime"].item()))
            # Voltage value of condition
            parameters.append((mn + f'/SM_Source/VRT/VRT_State_Machine/Condition_{index}_Voltage/Value', row["Voltage"].item()))
        self.params["parameters"] = parameters
    
    def set_test_conditions(self,current_mode):
        t0 = self.params["eut_startup_time"]
        # Table 4 - Category II LVRT
        mra_v_pu = self.MRA["V"]/self.v_nom
        if CAT_2 in current_mode  and LV in current_mode :
            t1 = t0 + 10
            t2 = t1 + 0.16
            t3 = t1 + 0.32
            t4 = t1 + 3
            t5 = t1 + 5
            t6 = t5 + 120.0
            if self.params["range_steps"] == "Figure":
                voltage = [0.94,0.3-2*mra_v_pu,0.45-2*mra_v_pu,0.65,0.88,0.94]     
            elif self.params["range_steps"] == "Random": 
                voltage = [random.uniform(0.88,1.0),
                random.uniform(0.0,0.3),
                random.uniform(0.0,0.45),
                random.uniform(0.45,0.65),
                random.uniform(0.65,0.88),
                random.uniform(0.88,1.0)]     
            test_condition = pd.DataFrame({'Voltage' :   np.array(voltage)*self.v_nom,
                                            'StartTime' : [t0,t1,t2,t3,t4,t5],
                                            'StopTime' : [t1,t2,t3,t4,t5,t6]},
                                            index = ["A","B","C","D","E","F"])
        # Table 5 - Category III LVRT
        elif CAT_3 in current_mode  and LV in current_mode :
            t1 = t0 + 5
            t2 = t1 + 1
            t3 = t1 + 10
            t4 = t1 + 20
            t5 = t4 + 120
            if self.params["range_steps"] == "Figure":
                voltage = [0.94,0.05-2*mra_v_pu,0.5,0.7,0.94]     
            elif self.params["range_steps"] == "Random": 
                voltage = [random.uniform(0.88,1.0),
                random.uniform(0.0,0.05),
                random.uniform(0.0,0.5),
                random.uniform(0.5,0.7),
                random.uniform(0.88,1.0)]     
            test_condition = pd.DataFrame({'Voltage' :   np.array(voltage)*self.v_nom,
                                            'StartTime' : [t0,t1,t2,t3,t4],
                                            'StopTime' : [t1,t2,t3,t4,t5]},
                                            index = ["A","B","C","D","E"])
        # Table 7 - Category II HVRT
        elif CAT_2 in current_mode  and HV in current_mode :
            t1 = t0 + 10
            t2 = t1 + 0.2
            t3 = t1 + 0.5
            t4 = t1 + 1.0
            t5 = t4 + 120
            if self.params["range_steps"] == "Figure":
                voltage = [1.0,1.2,1.175,1.15,1.0]     
            elif self.params["range_steps"] == "Random": 
                voltage = [random.uniform(1.0,1.1),
                random.uniform(1.18,1.2),
                random.uniform(1.155,1.175),
                random.uniform(1.13,1.15),
                random.uniform(1.0,1.1)] 
            test_condition = pd.DataFrame({'Voltage' :   np.array(voltage)*self.v_nom,
                                        'StartTime' : [t0,t1,t2,t3,t4],
                                        'StopTime' : [t1,t2,t3,t4,t5]},
                                        index = ["A","B","C","D","E"])
        # Table 7 - Category III HVRT
        elif CAT_3 in current_mode  and HV in current_mode :
            t1 = t0 + 5
            t2 = t1 + 12
            t3 = t2 + 120
            if self.params["range_steps"] == "Figure":
                voltage = [1.05,1.2,1.05]     
            elif self.params["range_steps"] == "Random": 
                voltage = [random.uniform(1.0,1.1),
                random.uniform(1.18,1.2),
                random.uniform(1.0,1.1)] 
            test_condition = pd.DataFrame({'Voltage' :   np.array(voltage)*self.v_nom,
                                        'StartTime' : [t0,t1,t2],
                                        'StopTime' : [t1,t2,t3]},
                                        index = ["A","B","C"])
        else :
             self.ts.log_error('No test_condition value')
             self.ts.log_debug(self.params)
        self.params["test_condition"] = test_condition
        
        self.set_vrt_model_parameters()

        return test_condition

    def set_vrt_modes(self):
        modes= []
        if self.params["lv_mode"] == 'Enabled' and (self.params["categories"] == CAT_2 or self.params["categories"] == 'Both'):
            modes.append(f"{LV}_{CAT_2}")
        if self.params["lv_mode"] == 'Enabled' and (self.params["categories"] == CAT_3 or self.params["categories"] == 'Both'):
            modes.append(f"{LV}_{CAT_3}")
        if self.params["hv_mode"] == 'Enabled' and (self.params["categories"] == CAT_2 or self.params["categories"] == 'Both'):
            modes.append(f"{HV}_{CAT_2}")
        if self.params["hv_mode"] == 'Enabled' and (self.params["categories"] == CAT_3 or self.params["categories"] == 'Both'):
            modes.append(f"{HV}_{CAT_3}")
        self.params["modes"] = modes
        self.ts.log_debug(self.params)
    
    def waveform_config(self, param):  
        parameters = []
        mn = self.params["model_name"]
        pre_trigger = param["pre_trigger"]
        post_trigger = param["post_trigger"]
        parameters.append((mn + '/SM_Source/VRT/VRT_Trigger_Start/Threshold',pre_trigger))
        parameters.append((mn + '/SM_Source/VRT/VRT_Trigger_End/Threshold',post_trigger))
        self.hil.set_parameters(parameters)
        

    """
    Getter functions
    """
    


    def get_model_parameters(self,current_mode):
        self.ts.log(f"Getting HIL parameters for mode '{current_mode}''")
        self.set_test_conditions(current_mode)
        return self.params["parameters"],self.params["vrt_start_time"], self.params["vrt_stop_time"] 

    def get_modes(self):
        return self.params["modes"]

    

class FrequencyRideThrough(HilModel):
    def __init__(self):
        HilModel.__init__()
        self._config()

    def _config(self):
        self.set_frt_params()
        self.set_model_on()
        self.set_frt_model_parameters_dic()

    """
    Setter functions
    """

    def set_params(self):
        try:
            # RT test parameters
            self.params["lf_mode"] = self.ts.param_value('frt.lv_ena')
            self.params["hf_mode"] = self.ts.param_value('frt.hv_ena')

            # consecutive_ena = ts.param_value('vrt.consecutive_ena')
            self.params["categories"] = self.ts.param_value('frt.cat')
            self.params["range_steps"] = self.ts.param_value('frt.range_steps')
            self.eut_startup_time = self.ts.param_value('eut.startup_time')
            self.params["model_name"] = self.hil.rt_lab_model
        except Exception as e:
            self.ts.log_error('Incorrect Parameter value : %s' % e)
            raise

    # TODO to be completed with FRT
    def set_model_parameters_dic(self):
        categories = self.params["categories"]
        lf_mode = self.params["lf_mode"]
        hf_mode = self.params["hf_mode"]
        model_name = self.params["model_name"]
        range_steps = self.params["range_steps"]

        if lf_mode == 'Enabled':
            # Timestep is cumulative
            if categories == CAT_2 or categories == 'Both':
                self.mode.append(f'{LV}_{CAT_2}')
                self.vrt_start_time = self.eut_startup_time
                self.vrt_stop_time = 12 + self.vrt_start_time
                # TODO change sequence parameter for parameter to be chosen by users or average of both max & min values?
                self.parameters_dic.update({f'{LV}_{CAT_2}': [
                    # Add ROCOM only for condition E
                    (model_name + '/SM_Source/Waveform_Generator/ROCOM_START_TIME/Value', 10 + self.vrt_start_time),
                    (model_name + '/SM_Source/Waveform_Generator/ROCOM_END_TIME/Value', 12 + self.vrt_start_time),
                    # Enable needed conditions
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/cond_a_ena/Value', 1),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/cond_b_ena/Value', 1),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/cond_c_ena/Value', 1),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/cond_d_ena/Value', 1),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/cond_e_ena/Value', 1),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/cond_f_ena/Value', 1),
                    # Timesteps
                    # (model_name + '/SM_Source/VRT/VRT_State_Machine/condition A/Threshold', 20 + self.vrt_start_time),
                    # (model_name + '/SM_Source/VRT/VRT_State_Machine/condition B/Threshold', 20.16 + self.vrt_start_time),
                    # (model_name + '/SM_Source/VRT/VRT_State_Machine/condition C/Threshold', 20.32 + self.vrt_start_time),
                    # (model_name + '/SM_Source/VRT/VRT_State_Machine/condition D/Threshold', 23 + self.vrt_start_time),
                    # (model_name + '/SM_Source/VRT/VRT_State_Machine/condition E/Threshold', 25 + self.vrt_start_time),
                    # (model_name + '/SM_Source/VRT/VRT_State_Machine/condition F/Threshold', 125 + self.vrt_start_time),

                    (model_name + '/SM_Source/VRT/VRT_State_Machine/condition A/Threshold', 2 + self.vrt_start_time),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/condition B/Threshold', 4 + self.vrt_start_time),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/condition C/Threshold', 6 + self.vrt_start_time),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/condition D/Threshold', 8 + self.vrt_start_time),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/condition E/Threshold', 10 + self.vrt_start_time),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/condition F/Threshold', self.vrt_stop_time),
                    # Values
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/voltage_ph_seqA/Value', 0.94 * 120),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/condition B/Threshold', 0.28 * 120),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/condition C/Threshold', 0.43 * 120),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/condition D/Threshold', 0.65 * 120),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/condition E/Threshold', 0.88 * 120),
                    (model_name + '/SM_Source/VRT/VRT_State_Machine/condition F/Threshold', 0.94 * 120)]})


if __name__ == "__main__":
    pass

