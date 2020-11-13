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

VERSION = '1.4.2'
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
UI = 'UI'  # Unintentional Islanding Tests

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
LFRT = "LFRT"
HFRT = "HFRT"


class p1547Error(Exception):
    pass


"""
This section is for EUT parameters needed such as V, P, Q, etc.
"""


def VersionValidation(script_version):
    if script_version != VERSION:
        raise p1547Error(f'Error in p1547 library version is {VERSION} while script version is {script_version}.'
                         f'Update library and script version accordingly.')


class EutParameters(object):
    def __init__(self, ts):
        self.ts = ts
        try:
            self.v_nom = ts.param_value('eut.v_nom')
            self.s_rated = ts.param_value('eut.s_rated')
            self.v_high = ts.param_value('eut.v_high')
            self.v_low = ts.param_value('eut.v_low')

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
            self.MRA = {
                'V': 0.01 * self.v_nom,
                'Q': 0.05 * ts.param_value('eut.s_rated'),
                'P': 0.05 * ts.param_value('eut.s_rated'),
                'F': 0.01,
                'T': 0.01,
                'PF': 0.01
            }

            self.MRA_V_trans = 0.02 * self.v_nom
            self.MRA_F_trans = 0.1
            self.MRA_T_trans = 2. / 60.

            if ts.param_value('eut.f_nom'):
                self.f_nom = ts.param_value('eut.f_nom')
            else:
                self.f_nom = None

            if ts.param_value('eut.f_max'):
                self.f_max = ts.param_value('eut.f_max')
            else:
                self.f_max = None
            if ts.param_value('eut.f_min'):
                self.f_min = ts.param_value('eut.f_min')
            else:
                self.f_min = None

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
        self.double_letter_label = None
        self.script_complete_name = 'UNDEFINED IN TEST CLASS'

    def reset_curve(self, curve=1):
        self.curve = curve
        self.ts.log_debug(f'P1547 Librairy curve has been set {curve}')

    def reset_pwr(self, pwr=1.0):
        self.pwr = pwr
        self.ts.log_debug(f'P1547 Librairy power level has been set {round(pwr * 100)}%')

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

    def get_params(self, function, curve=None):

        if curve == None:
            return self.param[function]
        else:
            return self.param[function][self.curve]

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

    def get_script_name(self):
        if self.script_complete_name is None:
            self.script_complete_name = 'Script name not initialized'
        return self.script_complete_name


class DataLogging:
    # def __init__(self, meas_values, x_criteria, y_criteria):
    def __init__(self):
        self.type_meas = {'V': 'AC_VRMS', 'I': 'AC_IRMS', 'P': 'AC_P', 'Q': 'AC_Q', 'VA': 'AC_S',
                          'F': 'AC_FREQ', 'PF': 'AC_PF'}
        # Values to be recorded
        # self.meas_values = meas_values
        # Values defined as target/step values which will be controlled as step
        # self.x_criteria = x_criteria
        # Values defined as values which will be controlled as step
        # self.y_criteria = y_criteria
        self.rslt_sum_col_name = ''
        self.sc_points = {}
        # self._config()
        self.set_sc_points()
        self.set_result_summary_name()
        self.tr = None
        self.n_tr = None
        self.initial_value = {}
        self.tr_value = collections.OrderedDict()
        self.current_step_label = None

    # def __config__(self):

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
        self.ts.log_debug(f'summary column={self.rslt_sum_col_name}'.rstrip())

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

        # y_points = '%s_TARGET,%s_MEAS' % (y, y)
        # y2_points = '%s_TARGET,%s_MEAS' % (y2, y2)
        self.ts.log_debug(f'y_variables={y_variables}')
        for y in y_variables:
            self.ts.log_debug('y_temp: %s' % y)
            # y_temp = self.get_measurement_label('%s' % y)
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

    def get_measurement_total(self, type_meas, log=False):
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
                value = self.data.get(self.get_measurement_label(type_meas)[0])
                if log:
                    self.ts.log_debug('        %s are: %s'
                                      % (self.get_measurement_label(type_meas), value))
                nb_phases = 1

            elif self.phases == 'Split phase':
                value1 = self.data.get(self.get_measurement_label(type_meas)[0])
                value2 = self.data.get(self.get_measurement_label(type_meas)[1])
                if log:
                    self.ts.log_debug('        %s are: %s, %s'
                                      % (self.get_measurement_label(type_meas), value1, value2))
                value = value1 + value2
                nb_phases = 2

            elif self.phases == 'Three phase':
                # self.ts.log_debug(f'type_meas={type_meas}')
                value1 = self.data.get(self.get_measurement_label(type_meas)[0])
                value2 = self.data.get(self.get_measurement_label(type_meas)[1])
                value3 = self.data.get(self.get_measurement_label(type_meas)[2])
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
            value = self.data.get(self.get_measurement_label(type_meas)[0])

        return round(value, 3)

    def get_rslt_sum_col_name(self):
        """
        This getters function returns the column name for result_summary.csv
        :return:            self.rslt_sum_col_name
        """
        return self.rslt_sum_col_name

    def write_rslt_sum(self):
        """
        Combines the analysis results, the step label and the filename to return
        a row that will go in result_summary.csv
        :param analysis: Dictionary with all the information for result summary

        :param step:   test procedure step letter or number (e.g "Step G")
        :param filename: the dataset filename use for analysis

        :return: row_data a string with all the information for result_summary.csv
        """

        xs = self.x_criteria
        ys = list(self.y_criteria.keys())
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
        # self.ts.log_debug(f'rowdata={row_data}')
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
        self.data = daq.data_capture_read()
        daq.sc['event'] = self.current_step_label
        if isinstance(self.x_criteria, list):
            for xs in self.x_criteria:
                self.initial_value[xs] = {'x_value': self.get_measurement_total(type_meas=xs, log=False)}
                daq.sc['%s_MEAS' % xs] = self.initial_value[xs]['x_value']
        else:
            self.initial_value[self.x_criteria] = {
                'x_value': self.get_measurement_total(type_meas=self.x_criteria, log=False)}
            daq.sc['%s_MEAS' % self.x_criteria] = self.initial_value[self.x_criteria]['x_value']

        if isinstance(self.y_criteria, dict):
            for ys in list(self.y_criteria.keys()):
                self.initial_value[ys] = {'y_value': self.get_measurement_total(type_meas=ys, log=False)}
                daq.sc['%s_MEAS' % ys] = self.initial_value[ys]["y_value"]
        else:
            self.initial_value[self.y_criteria] = {
                'y_value': self.get_measurement_total(type_meas=self.y_criteria, log=False)}
            daq.sc['%s_MEAS' % self.y_criteria] = self.initial_value[self.y_criteria]['y_value']

        """
        elif isinstance(self.y_criteria, list):
            for ys in self.y_criteria:
                self.initial_value[ys] = {'y_value': self.get_measurement_total(data=data, type_meas=ys, log=False)}
                daq.sc['%s_MEAS' % ys] = self.initial_value[ys]["y_value"]
        """
        daq.data_sample()

    def record_timeresponse(self, daq):
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
        y = list(self.y_criteria.keys())
        # self.tr = tr

        first_tr = self.initial_value['timestamp'] + timedelta(seconds=self.tr)
        tr_list = [first_tr]

        for i in range(self.n_tr):
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

                except Exception as e:
                    self.ts.log_error('Test script exception: %s' % traceback.format_exc())
                    self.ts.log_debug('Measured value (%s) not recorded: %s' % (meas_value, e))

            # self.tr_value[tr_iter]["timestamp"] = tr_
            self.tr_value[f'timestamp_{tr_iter}'] = tr_
            self.tr_value['LAST_ITER'] = tr_iter - 1
            tr_iter = tr_iter + 1

        self.tr_value['FIRST_ITER'] = 1

        return self.tr_value

        # except Exception as e:
        #    raise p1547Error('Error in get_tr_data(): %s' % (str(e)))


class CriteriaValidation:
    def __init__(self, criteria_mode):
        self.criteria_mode = criteria_mode

    def define_target(self, daq, step_dict=None, y_criterias_mod=None):
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
        y_criteria = self.y_criteria

        if isinstance(y_criterias_mod, dict):
            y_criteria.update(y_criterias_mod)

        y = list(y_criteria.keys())
        # self.tr = tr
        self.ts.log_debug(f'daq={daq.sc}')
        for tr_iter in range(self.n_tr + 1):
            self.ts.log_debug(f'tr_iter={tr_iter}')
            # store the daq.sc['Y_TARGET'], daq.sc['Y_TARGET_MIN'], and daq.sc['Y_TARGET_MAX'] in tr_value
            for meas_value in self.meas_values:
                try:
                    if meas_value in x:

                        if (self.step_dict is not None) and (meas_value in list(self.step_dict.keys())):
                            self.ts.log_debug(f'step_dict')
                            daq.sc['%s_TARGET' % meas_value] = self.step_dict[meas_value]
                            self.tr_value['%s_TR_TARG_%s' % (meas_value, tr_iter)] = self.step_dict[meas_value]
                            self.ts.log_debug(f'tr_targ={self.tr_value["%s_TR_TARG_%s" % (meas_value, tr_iter)]}')
                            self.ts.log('X Value (%s) = %s' % (meas_value, daq.sc['%s_MEAS' % meas_value]))

                    elif meas_value in y:
                        if self.step_dict is not None:
                            # self.ts.log_debug(f'meas={meas_value} et step_dict={self.step_dict}')
                            self.ts.log_debug(f'function={y_criteria[meas_value]}')

                            daq.sc['%s_TARGET' % meas_value] = self.update_target_value(function=y_criteria[meas_value])
                            daq.sc['%s_TARGET_MIN' % meas_value], daq.sc['%s_TARGET_MAX' % meas_value] = \
                                self.calculate_min_max_values(function=y_criteria[meas_value])

                        else:
                            daq.sc['%s_TARGET' % meas_value] = self.update_target_value(value=step_value,
                                                                                        function=self.y_criteria[
                                                                                            meas_value])
                            daq.sc['%s_TARGET_MIN' % meas_value], daq.sc['%s_TARGET_MAX' % meas_value] = \
                                self.calculate_min_max_values(function=y_criteria[meas_value], step_dict=step_dict)
                        self.tr_value[f'{meas_value}_TR_TARG_{tr_iter}'] = daq.sc['%s_TARGET' % meas_value]
                        self.tr_value[f'{meas_value}_TR_{tr_iter}_MIN'] = daq.sc['%s_TARGET_MIN' % meas_value]
                        self.tr_value[f'{meas_value}_TR_{tr_iter}_MAX'] = daq.sc['%s_TARGET_MAX' % meas_value]
                        self.ts.log_debug(f"{meas_value}_TR_TARG_{tr_iter}")
                        self.ts.log_debug(f'tr_target={self.tr_value[f"{meas_value}_TR_TARG_{tr_iter}"]}')
                        self.ts.log('Y Value (%s) = %s. Pass/fail bounds = [%s, %s]' %
                                    (meas_value, daq.sc['%s_MEAS' % meas_value],
                                     daq.sc['%s_TARGET_MIN' % meas_value], daq.sc['%s_TARGET_MAX' % meas_value]))
                except Exception as e:
                    self.ts.log_error('Test script exception: %s' % traceback.format_exc())
                    self.ts.log_debug('Measured value (%s) not recorded: %s' % (meas_value, e))

    def update_target_value(self, function, value=None, step_dict=None):

        step_dict = self.step_dict

        if function == VV:
            vv_pairs = self.get_params(function=VV, curve=self.curve)
            x = [vv_pairs['V1'], vv_pairs['V2'],
                 vv_pairs['V3'], vv_pairs['V4']]
            y = [vv_pairs['Q1'], vv_pairs['Q2'],
                 vv_pairs['Q3'], vv_pairs['Q4']]
            if isinstance(step_dict, dict):
                q_value = float(np.interp(step_dict['V'], x, y))
            else:
                q_value = float(np.interp(value, x, y))
            q_value *= self.pwr
            return round(q_value, 1)

        if function == VW:
            # self.ts.log_debug(f'VW target calculation')
            vw_pairs = self.get_params(function=VW, curve=self.curve)
            self.ts.log_debug(f'vw_pairs={vw_pairs}')
            x = [vw_pairs['V1'], vw_pairs['V2']]
            y = [vw_pairs['P1'], vw_pairs['P2']]
            if isinstance(step_dict, dict):
                p_value = float(np.interp(step_dict['V'], x, y))
            else:
                p_value = float(np.interp(value, x, y))
            p_value *= self.pwr
            self.ts.log_debug(f'p_value={p_value}')
            return round(p_value, 1)

        if function == CPF:
            # self.ts.log_debug(f'CPF target calculation')
            q_value = math.sqrt(pow(step_dict['P'], 2) * ((1 / pow(step_dict['PF'], 2)) - 1))
            return q_value

        if function == CRP:
            # self.ts.log_debug(f'CRP target calculation')
            q_value = step_dict['Q']
            return round(q_value, 1)

        if function == WV:
            # self.ts.log_debug(f'WV target calculation')
            x = [self.param[WV][self.curve]['P1'], self.param[WV][self.curve]['P2'], self.param[WV][self.curve]['P3']]
            y = [self.param[WV][self.curve]['Q1'], self.param[WV][self.curve]['Q2'], self.param[WV][self.curve]['Q3']]
            q_value = float(np.interp(step_dict['P'], x, y))
            q_value *= self.pwr
            self.ts.log_debug('Power value: %s --> q_target: %s' % (value, q_value))
            return q_value

        if function == FW:
            # self.ts.log_debug(f'FW target calculation')
            p_targ = None
            fw_pairs = self.get_params(function=FW, curve=self.curve)
            f_dob = self.f_nom + fw_pairs['dbf']
            f_dub = self.f_nom - fw_pairs['dbf']
            p_db = self.p_rated * self.pwr
            p_avl = self.p_rated * (1.0 - self.pwr)
            if isinstance(step_dict, dict):
                value = step_dict['F']
            self.ts.log_debug(f'value={value}')
            if f_dub <= value <= f_dob:
                p_targ = p_db
            elif value > f_dob:
                p_targ = p_db - ((value - f_dob) / (self.f_nom * self.param[FW][self.curve]['kof'])) * p_db
                if p_targ < self.p_min:
                    p_targ = self.p_min
            elif value < f_dub:
                p_targ = ((f_dub - value) / (self.f_nom * self.param[FW][self.curve]['kof'])) * p_avl + p_db
                if p_targ > self.p_rated:
                    p_targ = self.p_rated
            p_targ *= self.pwr
            return round(p_targ, 2)

        if function == LAP:
            self.ts.log_debug(f'LAP target calculation')
            p_targ = (step_dict['P'] * self.p_rated) + self.MRA['P']
            return p_targ

    def calculate_min_max_values(self, function, meas_value=None):

        step_dict = self.step_dict
        if PRI == function:
            v_meas = self.get_measurement_total(type_meas='V', log=False)
            f_meas = self.get_measurement_total(type_meas='F', log=False)

            target_min_vw = self.update_target_value(value=v_meas + self.MRA['V'] * 1.5, function=VW) - (
                    self.MRA['P'] * 1.5)
            target_max_vw = self.update_target_value(value=v_meas - self.MRA['V'] * 1.5, function=VW) + (
                    self.MRA['P'] * 1.5)
            target_min_fw = self.update_target_value(value=f_meas + self.MRA['F'] * 1.5, function=FW) - (
                    self.MRA['P'] * 1.5)
            target_max_fw = self.update_target_value(value=f_meas - self.MRA['F'] * 1.5, function=FW)
            if (target_max_vw - target_min_vw) > (target_max_fw - target_min_fw):
                target_min = target_min_vw
                target_max = target_max_vw
            else:
                target_min = target_min_fw
                target_max = target_max_fw

        if function == VV:
            v_meas = self.get_measurement_total(type_meas='V', log=False)
            target_min = self.update_target_value(value=v_meas + self.MRA['V'] * 1.5, function=VV) - (
                        self.MRA['Q'] * 1.5)
            target_max = self.update_target_value(value=v_meas - self.MRA['V'] * 1.5, function=VV) + (
                        self.MRA['Q'] * 1.5)

        elif function == VW:
            v_meas = self.get_measurement_total(type_meas='V', log=False)
            target_min = self.update_target_value(value=v_meas + self.MRA['V'] * 1.5, function=VW) - (
                        self.MRA['P'] * 1.5)
            target_max = self.update_target_value(value=v_meas - self.MRA['V'] * 1.5, function=VW) + (
                        self.MRA['P'] * 1.5)

        elif function == CPF:
            p_meas = self.get_measurement_total(type_meas='P', log=False)
            target_min = \
                self.update_target_value(value=p_meas + self.MRA['P'] * 1.5, function=CPF, step_dict=step_dict) - 1.5 * \
                self.MRA['Q']
            target_max = \
                self.update_target_value(value=p_meas - self.MRA['P'] * 1.5, function=CPF, step_dict=step_dict) + 1.5 * \
                self.MRA['Q']

        elif function == CRP:
            target_min = step_dict['Q'] - self.MRA['Q']
            target_max = step_dict['Q'] + self.MRA['Q']

        elif function == WV:
            p_meas = self.get_measurement_total(type_meas='P', log=False)
            # q_meas = self.get_measurement_total(data=data, type_meas='Q', log=False)
            step_min = {'P': p_meas + self.MRA['P'] * 1.5}
            step_max = {'P': p_meas - self.MRA['P'] * 1.5}
            target_min = self.update_target_value(step_dict=step_min, function=WV) - (self.MRA['Q'] * 1.5)
            target_max = self.update_target_value(step_dict=step_max, function=WV) + (self.MRA['Q'] * 1.5)

        elif function == FW:
            f_meas = self.get_measurement_total(type_meas='F', log=False)
            target_min = self.update_target_value(value=f_meas + self.MRA['F'] * 1.5, function=FW) - (
                        self.MRA['P'] * 1.5)
            target_max = self.update_target_value(value=f_meas - self.MRA['F'] * 1.5, function=FW) + (
                        self.MRA['P'] * 1.5)

        elif function == LAP:
            target_min = self.update_target_value(function=LAP) - (self.MRA['P'] * 1.5)
            target_max = self.update_target_value(function=LAP) + (self.MRA['P'] * 1.5)

        return target_min, target_max

    def evaluate_criterias(self, daq, step_dict=None, y_criterias_mod=None):

        self.step_dict = step_dict
        self.define_target(daq=daq, y_criterias_mod=y_criterias_mod)

        if self.criteria_mode[0]:
            self.open_loop_resp_criteria()
        if self.criteria_mode[1] or self.criteria_mode[2]:
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
        y = list(self.y_criteria.keys())[0]
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
            y_start = self.initial_value[y]['y_value']
            # y_start = tr_value['%s_INITIAL' % y]
            mra_t = self.MRA['T'] * duration  # MRA(X) = MRA(time) = 0.01*duration
        # self.ts.log_debug(f'tr_value={self.tr_value}')
        y_ss = self.tr_value[f'{y}_TR_TARG_{tr}']
        y_target = self.calculate_open_loop_value(y0=y_start, y_ss=y_ss, duration=duration, tr=tr)  # 90%
        y_meas = self.tr_value[f'{y}_TR_{tr}']
        self.ts.log_debug(
            f'y_target = {y_target:.2f}, y_ss [{y_ss:.2f}], y_start [{y_start:.2f}], duration = {duration}, tr={tr}')

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
        self.ts.log_debug(f'RESULT_ACCURACY')
        for y in self.y_criteria:
            for tr_iter in range(self.tr_value['FIRST_ITER'], self.tr_value['LAST_ITER'] + 1):

                if (self.tr_value['FIRST_ITER'] == tr_iter and self.criteria_mode[1]) or \
                        (self.tr_value['LAST_ITER'] == tr_iter and self.criteria_mode[2]):

                    # pass/fail assessment for the steady-state values
                    # self.ts.log_debug(f'current iter={tr_iter}')
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
                self.ang['case_b'] = [0., 120, -120]
                self.ts.log("Setting test with imbalanced test with NOT FIXED angles/values")
            elif imbalance_angle_fix == 'not_fix':
                # Case A
                self.mag['case_a'] = [1.08 * self.v_nom, 0.91 * self.v_nom, 0.91 * self.v_nom]
                self.ang['case_a'] = [0., 126.59, -126.59]
                # Case B
                self.mag['case_b'] = [0.9 * self.v_nom, 1.08 * self.v_nom, 1.08 * self.v_nom]
                self.ang['case_b'] = [0., 114.5, -114.5]
                self.ts.log("Setting test with imbalanced test with NOT FIXED angles/values")

            # return (self.mag, self.ang)
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
        self.ts.log_debug(f'mag={self.ang}')
        self.ts.log_debug(f'grid={grid}')
        self.ts.log_debug(f'imbalance_resp={imbalance_resp}')

        if grid is not None:
            grid.config_asymmetric_phase_angles(mag=self.mag[case], angle=self.ang[case])
        if imbalance_resp == 'AVG_3PH_RMS':
            self.ts.log_debug(f'mag={self.mag[case]}')
            return round(sum(self.mag[case]) / 3.0, 2)
        elif imbalance_resp is 'INDIVIDUAL_PHASES_VOLTAGES':
            # TODO TO BE COMPLETED
            pass
        elif imbalance_resp is 'POSITIVE_SEQUENCE_VOLTAGES':
            # TODO to be completed
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
        self.set_time_path()
        self.set_nominal_values()
        self.set_input_scale_offset()

    def set_nominal_values(self):
        parameters = []
        parameters.append((f"VNOM", 1.0))
        parameters.append((f"FNOM", self.f_nom))
        self.hil.set_matlab_variables(parameters)

    def set_time_path(self):
        """
        Set the time path signal
        """
        self.hil.set_time_sig("/SM_Source/IEEE_1547_TESTING/Clock/port1")

    def set_input_scale_offset(self):
        """
        Set input scale and offset of voltage and current
        """
        # .replace(" ", "") removes the space 
        # .split(",") split with the comma
        scale_current = self.ts.param_value('eut.scale_current').replace(" ", "").split(",")
        offset_current = self.ts.param_value('eut.offset_current').replace(" ", "").split(",")
        scale_voltage = self.ts.param_value('eut.scale_voltage').replace(" ", "").split(",")
        offset_voltage = self.ts.param_value('eut.offset_voltage').replace(" ", "").split(",")

        if self.phases == "Single Phase":
            phases = ["A"]
        elif self.phases == "Split phase":
            phases = ["A", "B"]
        else:
            phases = ["A", "B", "C"]

        parameters = []
        i = 0
        for ph in phases:
            parameters.append((f"CURRENT_INPUT_SCALE_PH{ph}", float(scale_current[i])))
            parameters.append((f"VOLT_INPUT_SCALE_PH{ph}", float(scale_voltage[i])))
            parameters.append((f"VOLT_INPUT_OFFSET_PH{ph}", float(offset_voltage[i])))
            parameters.append((f"CURRENT_INPUT_OFFSET_PH{ph}", float(offset_current[i])))
            i = i + 1

        self.hil.set_matlab_variables(parameters)

    """
    Getter functions
    """

    def get_model_parameters(self, current_mode):
        self.ts.log(f'Getting HIL parameters for {current_mode}')
        return self.parameters_dic[current_mode], self.start_time, self.stop_time


"""
This section is for Voltage stabilization function such as VV, VW, CPF and CRP
"""


class VoltVar(EutParameters, UtilParameters):
    meas_values = ['V', 'Q', 'P']
    x_criteria = ['V']
    y_criteria = {'Q': VV}
    script_complete_name = 'Volt-Var'

    def __init__(self, ts):
        # self.criteria_mode = [True, True, True]
        EutParameters.__init__(self, ts)
        UtilParameters.__init__(self)
        VoltVar.set_params(self)

    def set_params(self):
        """
        Function to set VV curves points
        :return:
        """
        self.param[VV] = {}
        self.param[VV][1] = {
            'V1': round(0.92 * self.v_nom, 2),
            'V2': round(0.98 * self.v_nom, 2),
            'V3': round(1.02 * self.v_nom, 2),
            'V4': round(1.08 * self.v_nom, 2),
            'Q1': round(self.s_rated * 0.44, 2),
            'Q2': round(self.s_rated * 0.0, 2),
            'Q3': round(self.s_rated * 0.0, 2),
            'Q4': round(self.s_rated * -0.44, 2)
        }

        self.param[VV][2] = {
            'V1': round(0.88 * self.v_nom, 2),
            'V2': round(1.04 * self.v_nom, 2),
            'V3': round(1.07 * self.v_nom, 2),
            'V4': round(1.10 * self.v_nom, 2),
            'Q1': round(self.var_rated * 1.0, 2),
            'Q2': round(self.var_rated * 0.5, 2),
            'Q3': round(self.var_rated * 0.5, 2),
            'Q4': round(self.var_rated * -1.0, 2)
        }
        self.param[VV][3] = {
            'V1': round(0.90 * self.v_nom, 2),
            'V2': round(0.93 * self.v_nom, 2),
            'V3': round(0.96 * self.v_nom, 2),
            'V4': round(1.10 * self.v_nom, 2),
            'Q1': round(self.var_rated * 1.0, 2),
            'Q2': round(self.var_rated * -0.5, 2),
            'Q3': round(self.var_rated * -0.5, 2),
            'Q4': round(self.var_rated * -1.0, 2)
        }

    def create_vv_dict_steps(self, v_ref, mode='Normal'):
        """
        Function to create dictionnary depending on which mode volt-watt is running
        :param mode: string [None, Volt-Var, etc]
        :return: Voltage step dictionnary
        """

        v_steps_dict = collections.OrderedDict()
        a_v = self.MRA['V'] * 1.5
        v_pairs = self.get_params(function=VV, curve=self.curve)
        self.set_step_label(starting_label='G')
        if mode == 'Vref-test':
            pass
        elif mode == 'Imbalanced grid':
            pass
            # TODO to be decided if we can put imbalanced steps in here
        else:
            # Capacitive test
            # Starting from step F
            v_steps_dict[self.get_step_label()] = v_pairs['V3'] - a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V3'] + a_v
            v_steps_dict[self.get_step_label()] = (v_pairs['V3'] + v_pairs['V4']) / 2
            v_steps_dict[self.get_step_label()] = v_pairs['V4'] - a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V4'] + a_v
            v_steps_dict[self.get_step_label()] = self.v_high - a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V4'] + a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V4'] - a_v
            v_steps_dict[self.get_step_label()] = (v_pairs['V3'] + v_pairs['V4']) / 2
            v_steps_dict[self.get_step_label()] = v_pairs['V3'] + a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V3'] - a_v
            v_steps_dict[self.get_step_label()] = v_ref * self.v_nom

            # Inductive test
            # Step S
            v_steps_dict[self.get_step_label()] = v_pairs['V2'] + a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V2'] - a_v
            v_steps_dict[self.get_step_label()] = (v_pairs['V1'] + v_pairs['V2']) / 2
            v_steps_dict[self.get_step_label()] = v_pairs['V1'] + a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V1'] - a_v
            v_steps_dict[self.get_step_label()] = self.v_low + a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V1'] - a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V1'] + a_v
            v_steps_dict[self.get_step_label()] = (v_pairs['V1'] + v_pairs['V2']) / 2
            v_steps_dict[self.get_step_label()] = v_pairs['V2'] - a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V2'] + a_v
            v_steps_dict[self.get_step_label()] = v_ref * self.v_nom

            for step, target in v_steps_dict.items():
                v_steps_dict.update({step: round(target, 2)})
                if target > self.v_high:
                    v_steps_dict.update({step: self.v_high})
                elif target < self.v_low:
                    v_steps_dict.update({step: self.v_low})

                # Skips steps when V4 is higher than Vmax of EUT
            if v_pairs['V4'] > self.v_high:
                self.ts.log_debug('Since V4 is higher than Vmax, Skipping a few steps')
                del v_steps_dict['Step J']
                del v_steps_dict['Step K']
                del v_steps_dict['Step M']
                del v_steps_dict['Step N']

                # Skips steps when V1 is lower than Vmin of EUT
            if v_pairs['V1'] < self.v_low:
                self.ts.log_debug('Since V1 is lower than Vmin, Skipping a few steps')
                del v_steps_dict['Step V']
                del v_steps_dict['Step W']
                del v_steps_dict['Step Y']
                del v_steps_dict['Step Z']

            self.ts.log_debug(v_steps_dict)
            return v_steps_dict


class VoltWatt(EutParameters, UtilParameters):
    meas_values = ['V', 'Q', 'P']
    x_criteria = ['V']
    y_criteria = {'P': VW}
    script_complete_name = 'Volt-Watt'

    """
    param curve: choose curve characterization [1-3] 1 is default
    """

    def __init__(self, ts):
        self.ts = ts
        # self.criteria_mode = [True, True, True]
        EutParameters.__init__(self, ts)
        UtilParameters.__init__(self)
        VoltWatt.set_params(self)

    def set_params(self):
        """
        Function to set VW curves points
        :return:
        """
        self.param[VW] = {}
        self.param[VW][1] = {
            'V1': round(1.06 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }
        self.param[VW][2] = {
            'V1': round(1.05 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }
        self.param[VW][3] = {
            'V1': round(1.09 * self.v_nom, 2),
            'V2': round(1.10 * self.v_nom, 2),
            'P1': round(self.p_rated, 2)
        }

        if self.p_min > (0.2 * self.p_rated):
            self.param[VW][1]['P2'] = int(0.2 * self.p_rated)
            self.param[VW][2]['P2'] = int(0.2 * self.p_rated)
            self.param[VW][3]['P2'] = int(0.2 * self.p_rated)
        else:
            self.param[VW][1]['P2'] = int(self.p_min)
            self.param[VW][2]['P2'] = int(self.p_min)
            self.param[VW][3]['P2'] = int(self.p_min)
        if self.absorb == 'Yes':
            self.param[VW][1]['P2'] = 0
            self.param[VW][2]['P2'] = self.p_rated_prime
            self.param[VW][3]['P2'] = self.p_rated_prime

        # self.ts.log_debug('VW settings: %s' % self.param[VW])

    def create_vw_dict_steps(self, mode='Normal'):
        """
        This function creates the dictionary steps for Volt-Watt
        :param mode (string): Verifies if VW is operating under normal or imbalanced grid mode
        :return: vw_dict_steps (dictionary)
        """
        if mode == 'Normal':
            # Setting starting letter for label
            self.set_step_label('G')
            v_steps_dict = collections.OrderedDict()
            v_pairs = self.get_params(curve=self.curve, function=VW)
            a_v = self.MRA['V'] * 1.5

            # Step G
            v_steps_dict[self.get_step_label()] = self.v_low + a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V1'] - a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V1'] + a_v
            v_steps_dict[self.get_step_label()] = (v_pairs['V2'] + v_pairs['V1']) / 2
            v_steps_dict[self.get_step_label()] = v_pairs['V2'] - a_v
            # Step K
            v_steps_dict[self.get_step_label()] = v_pairs['V2'] + a_v
            v_steps_dict[self.get_step_label()] = self.v_high - a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V2'] + a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V2'] - a_v
            # Step P
            v_steps_dict[self.get_step_label()] = (v_pairs['V1'] + v_pairs['V2']) / 2
            v_steps_dict[self.get_step_label()] = v_pairs['V1'] + a_v
            v_steps_dict[self.get_step_label()] = v_pairs['V1'] - a_v
            v_steps_dict[self.get_step_label()] = self.v_low + a_v

            if v_pairs['V2'] > self.v_high:
                del v_steps_dict['Step K']
                del v_steps_dict['Step L']
                del v_steps_dict['Step M']
                del v_steps_dict['Step N']
                del v_steps_dict['Step O']

            # Ensure voltage step doesn't exceed the EUT boundaries and round V to 2 decimal places
            for step, voltage in v_steps_dict.items():
                v_steps_dict.update({step: np.around(voltage, 2)})
                if voltage > self.v_high:
                    self.ts.log("{0} voltage step (value : {1}) changed to VH (v_max)".format(step, voltage))
                    v_steps_dict.update({step: self.v_high})
                elif voltage < self.v_low:
                    self.ts.log("{0} voltage step (value : {1}) changed to VL (v_min)".format(step, voltage))
                    v_steps_dict.update({step: self.v_low})

            self.ts.log_debug('curve points:  %s' % v_pairs)

            return v_steps_dict


class ConstantPowerFactor(EutParameters, UtilParameters):
    meas_values = ['V', 'P', 'Q', 'PF']
    x_criteria = ['V', 'P']
    y_criteria = {'Q': CPF}
    script_complete_name = 'Constant Power Factor'

    def __init__(self, ts):
        # self.ts = ts
        # self.criteria_mode = [True, True, True]
        EutParameters.__init__(self, ts)
        UtilParameters.__init__(self)


class ConstantReactivePower(EutParameters, UtilParameters):
    meas_values = ['V', 'Q', 'P']
    x_criteria = ['V']
    y_criteria = {'Q': CRP}
    script_complete_name = 'Constant Reactive Power'

    def __init__(self, ts):
        # self.ts = ts
        # self.criteria_mode = [True, True, True]
        EutParameters.__init__(self, ts)
        UtilParameters.__init__(self)


class FrequencyWatt(EutParameters, UtilParameters):
    meas_values = ['F', 'P']
    x_criteria = ['F']
    y_criteria = {'P': FW}
    script_complete_name = 'Frequency-Watt'

    def __init__(self, ts):
        EutParameters.__init__(self, ts)
        UtilParameters.__init__(self)
        FrequencyWatt.set_params(self)

    def set_params(self):

        p_small = self.ts.param_value('eut_fw.p_small')
        if p_small is None:
            p_small = 0.05

        self.param[FW] = {}

        self.param[FW][1] = {
            'dbf': 0.036,
            'kof': 0.05,
            'tr': self.ts.param_value('fw.test_1_tr'),
            'f_small': p_small * self.f_nom * 0.05
        }
        self.param[FW][2] = {
            'dbf': 0.017,
            'kof': 0.03,
            'tr': self.ts.param_value('fw.test_2_tr'),
            'f_small': p_small * self.f_nom * 0.02
        }

    def create_fw_dict_steps(self, mode):
        a_f = self.MRA['F'] * 1.5
        f_nom = self.f_nom
        f_steps_dict = collections.OrderedDict()
        fw_param = self.get_params(curve=self.curve, function=FW)

        self.set_step_label(starting_label='G')
        if mode == 'Above':  # 1547.1 (5.15.2.2):
            f_steps_dict[mode] = {}
            f_steps_dict[mode][self.get_step_label()] = (f_nom + fw_param['dbf']) + a_f
            f_steps_dict[mode][self.get_step_label()] = (f_nom + fw_param['dbf']) - a_f
            f_steps_dict[mode][self.get_step_label()] = (f_nom + fw_param['dbf']) + a_f
            f_steps_dict[mode][self.get_step_label()] = fw_param['f_small'] + f_nom + fw_param['dbf']
            # STD_CHANGE : step k) should consider the accuracy
            f_steps_dict[mode][self.get_step_label()] = self.f_max - a_f
            f_steps_dict[mode][self.get_step_label()] = self.f_max - fw_param['f_small']
            f_steps_dict[mode][self.get_step_label()] = (f_nom + fw_param['dbf']) + a_f
            f_steps_dict[mode][self.get_step_label()] = (f_nom + fw_param['dbf']) - a_f
            f_steps_dict[mode][self.get_step_label()] = f_nom

            for step, frequency in f_steps_dict[mode].items():
                f_steps_dict[mode].update({step: np.around(frequency, 3)})
                if frequency > self.f_max:
                    self.ts.log("{0} frequency step (value : {1}) changed to fH (f_max)".format(step, frequency))
                    f_steps_dict[mode].update({step: self.f_max})

        elif mode == 'Below':  # 1547.1 (5.15.3.2):
            f_steps_dict[mode] = {}
            f_steps_dict[mode][self.get_step_label()] = (f_nom + fw_param['dbf']) - a_f
            f_steps_dict[mode][self.get_step_label()] = (f_nom - fw_param['dbf']) - a_f
            f_steps_dict[mode][self.get_step_label()] = f_nom - fw_param['f_small'] - fw_param['dbf']
            # STD_CHANGE : step j) should consider the accuracy
            f_steps_dict[mode][self.get_step_label()] = self.f_min + a_f
            f_steps_dict[mode][self.get_step_label()] = self.f_min + fw_param['f_small']
            f_steps_dict[mode][self.get_step_label()] = (f_nom - fw_param['dbf']) - a_f
            f_steps_dict[mode][self.get_step_label()] = (f_nom - fw_param['dbf']) + a_f
            f_steps_dict[mode][self.get_step_label()] = f_nom

            for step, frequency in f_steps_dict[mode].items():
                f_steps_dict[mode].update({step: np.around(frequency, 3)})
                if frequency < self.f_min:
                    self.ts.log("{0} frequency step (value : {1}) changed to fL (f_min)".format(step, frequency))
                    f_steps_dict[mode].update({step: self.f_min})

        return f_steps_dict[mode]


class Interoperability(EutParameters):
    meas_values = ['V', 'P', 'F']  # Values to be recorded
    x_criteria = ['V']  # Values defined as target/step values which will be controlled as step
    y_criteria = {'P': IOP}  # Values defined as values which will be controlled as step

    def __init__(self, ts):
        self.eut_params = EutParameters.__init__(self, ts)
        # self.datalogging = DataLogging.__init__(self)
        self.pairs = {}
        self.param = {}
        self.target_dict = []
        self.script_name = IOP
        self.script_complete_name = 'Interoperability'
        self.rslt_sum_col_name = 'P_TR_ACC_REQ, TR_REQ, P_FINAL_ACC_REQ, V_MEAS, P_MEAS, P_TARGET, P_TARGET_MIN,' \
                                 'P_TARGET_MAX, STEP, FILENAME\n'
        self.criteria_mode = [True, True, True]

        self._config()

    def _config(self):
        self.set_params()
        # Create the pairs need
        # self.set_imbalance_config()

    def set_params(self):
        self.param['settings_test'] = self.ts.param_value('iop.settings_test')
        self.param['monitoring_test'] = self.ts.param_value('iop.monitoring_test')


class WattVar(EutParameters, UtilParameters):
    meas_values = ['P', 'Q']
    x_criteria = ['P']
    y_criteria = {'Q': WV}
    script_complete_name = 'Watt-Var'

    def __init__(self, ts, curve=1):
        EutParameters.__init__(self, ts)
        UtilParameters.__init__(self)
        WattVar.set_params(self)

    def set_params(self):
        self.param[WV] = {}

        if self.p_min > 0.2 * self.p_rated:
            p = self.p_min
            self.ts.log('P1 power is set using p_min')
        else:
            p = 0.2 * self.p_rated
            self.ts.log('P1 power is set using 20% p_rated')

        if self.absorb is "Yes":
            self.ts.log('Adding EUT Absorption Points (P1_prime-P3_prime, Q1_prime-Q3_prime)')
            self.param[WV][1] = {
                'P1': round(p, 2),
                'P2': round(0.5 * self.p_rated_prime, 2),
                'P3': round(1.0 * self.p_rated_prime, 2),
                'Q1': 0,
                'Q2': 0,
                'Q3': round(self.s_rated * 0.44, 2)
            }
            self.param[WV][2] = {
                'P1': round(-p, 2),
                'P2': round(0.5 * self.p_rated_prime, 2),
                'P3': round(1.0 * self.p_rated_prime, 2),
                'Q1': round(self.s_rated * 0.22, 2),
                'Q2': round(self.s_rated * 0.22, 2),
                'Q3': round(self.s_rated * 0.44, 2)
            }
            self.param[WV][3] = {
                'P1': round(-p, 2),
                'P2': round(0.5 * self.p_rated_prime, 2),
                'P3': round(1.0 * self.p_rated_prime, 2),
                'Q1': round(0, 2),
                'Q2': round(self.s_rated * 0.44, 2),
                'Q3': round(self.s_rated * 0.44, 2)
            }
        else:
            self.param[WV][1] = {
                'P1': round(p, 2),
                'P2': round(0.5 * self.p_rated, 2),
                'P3': round(1.0 * self.p_rated, 2),
                'Q1': round(self.s_rated * 0.0, 2),
                'Q2': round(self.s_rated * 0.0, 2),
                'Q3': round(self.s_rated * -0.44, 2)
            }
            self.param[WV][2] = {
                'P1': round(p, 2),
                'P2': round(0.5 * self.p_rated, 2),
                'P3': round(1.0 * self.p_rated, 2),
                'Q1': round(self.s_rated * -0.22, 2),
                'Q2': round(self.s_rated * -0.22, 2),
                'Q3': round(self.s_rated * -0.44, 2)
            }
            self.param[WV][3] = {
                'P1': round(p, 2),
                'P2': round(0.5 * self.p_rated, 2),
                'P3': round(1.0 * self.p_rated, 2),
                'Q1': round(self.s_rated * 0.0, 2),
                'Q2': round(self.s_rated * -0.44, 2),
                'Q3': round(self.s_rated * -0.44, 2)
            }

        self.ts.log_debug('WV settings: %s' % self.param[WV])

    def create_wv_dict_steps(self):

        p_steps_dict = collections.OrderedDict()
        p_pairs = self.get_params(function=WV, curve=self.curve)
        self.set_step_label(starting_label='G')
        a_p = self.MRA['P'] * 1.5
        p_steps_dict[self.get_step_label()] = self.p_min

        p_steps_dict[self.get_step_label()] = p_pairs['P1'] - a_p
        p_steps_dict[self.get_step_label()] = p_pairs['P1'] + a_p
        p_steps_dict[self.get_step_label()] = (p_pairs['P1'] + p_pairs['P2']) / 2
        p_steps_dict[self.get_step_label()] = p_pairs['P2'] - a_p
        p_steps_dict[self.get_step_label()] = p_pairs['P2'] + a_p
        p_steps_dict[self.get_step_label()] = (p_pairs['P2'] + p_pairs['P3']) / 2
        p_steps_dict[self.get_step_label()] = p_pairs['P3'] - a_p
        p_steps_dict[self.get_step_label()] = p_pairs['P3'] + a_p
        p_steps_dict[self.get_step_label()] = self.p_rated

        # Begin the return to Pmin
        p_steps_dict[self.get_step_label()] = p_pairs['P3'] + a_p
        p_steps_dict[self.get_step_label()] = p_pairs['P3'] - a_p
        p_steps_dict[self.get_step_label()] = (p_pairs['P2'] + p_pairs['P3']) / 2
        p_steps_dict[self.get_step_label()] = p_pairs['P2'] + a_p
        p_steps_dict[self.get_step_label()] = p_pairs['P2'] - a_p
        p_steps_dict[self.get_step_label()] = (p_pairs['P1'] + p_pairs['P2']) / 2
        p_steps_dict[self.get_step_label()] = p_pairs['P1'] + a_p
        p_steps_dict[self.get_step_label()] = p_pairs['P1'] - a_p
        p_steps_dict[self.get_step_label()] = self.p_min

        return p_steps_dict


class LimitActivePower(EutParameters, UtilParameters):
    meas_values = ['F', 'V', 'P', 'Q']
    x_criteria = ['V', 'F']
    y_criteria = {'Q': LAP}
    script_complete_name = 'Limit Active Power'

    def __init__(self, ts):
        EutParameters.__init__(self, ts)
        UtilParameters.__init__(self)
        # LimitActivePower.set_params(self)


class UnintentionalIslanding(EutParameters, UtilParameters):
    meas_values = ['F', 'V', 'P', 'Q']
    x_criteria = ['V']
    y_criteria = {'P': UI}

    def __init__(self, ts):
        EutParameters.__init__(self, ts)
        UtilParameters.__init__(self)
        self.script_complete_name = 'Unintentional Islanding'


class Prioritization(EutParameters, UtilParameters):
    meas_values = ['F', 'V', 'P', 'Q']
    x_criteria = ['V', 'F']
    y_criteria = {'Q': PRI, 'P': PRI}
    script_complete_name = 'Prioritization'

    def __init__(self, ts):
        EutParameters.__init__(self, ts)
        UtilParameters.__init__(self)

    def create_pri_dict_steps(self, function):
        p_rated = self.p_rated
        q_rated = self.var_rated
        v_nom = self.v_nom
        i = 0

        step_dicts = [{'V': 1.00 * v_nom, 'F': 60.00, 'P': 0.5 * p_rated},
                      {'V': 1.09 * v_nom, 'F': 60.00, 'P': 0.4 * p_rated},
                      {'V': 1.09 * v_nom, 'F': 60.33, 'P': 0.3 * p_rated},
                      {'V': 1.09 * v_nom, 'F': 60.00, 'P': 0.4 * p_rated},
                      {'V': 1.09 * v_nom, 'F': 59.36, 'P': 0.4 * p_rated},
                      {'V': 1.00 * v_nom, 'F': 59.36, 'P': 0.6 * p_rated},
                      {'V': 1.00 * v_nom, 'F': 60.00, 'P': 0.5 * p_rated},
                      {'V': 1.00 * v_nom, 'F': 59.36, 'P': 0.7 * p_rated}]

        if function == VV:
            self.ts.log_debug(f'adding VV in dict step')
            for step_dict in step_dicts:
                self.ts.log_debug(f'step_dict_before={step_dict}')

                if i > 0 or i < 5:
                    step_dict.update({'Q': -0.44 * q_rated})
                    self.ts.log_debug(f'i={i} and step_dict={step_dict}')

                else:
                    step_dict.update({'Q': 0})
                    self.ts.log_debug(f'i={i} and step_dict={step_dict}')

                i += 1
                self.ts.log_debug(f'step_dict={step_dict}')
        elif function == CPF:
            for step_dict in step_dicts:
                step_dict.update({'PF': 0.9})

        elif function == CRP:
            for step_dict in step_dicts:
                step_dict.update({'Q': 0.44 * q_rated})

        elif function == WV:
            for step_dict in step_dicts:
                if i == 5 or i < 7:
                    step_dict.update({'Q': 0.05 * q_rated})
                else:
                    step_dict.update({'Q': 0})
                i += 1

        return step_dicts


"""
This section is for the Active function
"""


class ActiveFunction(DataLogging, CriteriaValidation, ImbalanceComponent, VoltWatt, VoltVar, ConstantReactivePower,
                     ConstantPowerFactor, WattVar, FrequencyWatt, Interoperability, LimitActivePower, Prioritization,
                     UnintentionalIslanding):
    """
    This class acts as the main function
    As multiple functions might be needed for a compliance script, this function will inherit
    of all functions if needed.
    """

    def __init__(self, ts, script_name, functions, criteria_mode):
        self.ts = ts
        # Values defined as target/step values which will be controlled as step
        x_criterias = []
        self.x_criteria = []
        # Values defined as values which will be controlled as step
        y_criterias = []
        self.y_criteria = {}

        # Initiating criteria validation after data acquisition
        CriteriaValidation.__init__(self, criteria_mode=criteria_mode)

        self.param = {}
        # self.criterias = criterias

        self.script_name = script_name

        self.ts.log(f'Functions to be activated in this test script = {functions}')

        if VW in functions:
            VoltWatt.__init__(self, ts)
            x_criterias += VoltWatt.x_criteria
            self.y_criteria.update(VoltWatt.y_criteria)
        if VV in functions:
            VoltVar.__init__(self, ts)
            x_criterias += VoltVar.x_criteria
            self.y_criteria.update(VoltVar.y_criteria)
        if CPF in functions:
            ConstantPowerFactor.__init__(self, ts)
            x_criterias += ConstantPowerFactor.x_criteria
            self.y_criteria.update(ConstantPowerFactor.y_criteria)
        if CRP in functions:
            ConstantReactivePower.__init__(self, ts)
            x_criterias += ConstantReactivePower.x_criteria
            self.y_criteria.update(ConstantReactivePower.y_criteria)
        if WV in functions:
            WattVar.__init__(self, ts)
            x_criterias += WattVar.x_criteria
            self.y_criteria.update(WattVar.y_criteria)
        if FW in functions:
            FrequencyWatt.__init__(self, ts)
            x_criterias += FrequencyWatt.x_criteria
            self.y_criteria.update(FrequencyWatt.y_criteria)
        if LAP in functions:
            LimitActivePower.__init__(self, ts)
            x_criterias += FrequencyWatt.x_criteria
            self.y_criteria.update(FrequencyWatt.y_criteria)
        if PRI in functions:
            Prioritization.__init__(self, ts)
            x_criterias = Prioritization.x_criteria
            self.y_criteria.update(Prioritization.y_criteria)
        if IOP in functions:
            Interoperability.__init__(self, ts)
            x_criterias += Interoperability.x_criteria
            self.y_criteria.update(Interoperability.y_criteria)
        if UI in functions:
            UnintentionalIslanding.__init__(self, ts)
            x_criterias += UnintentionalIslanding.x_criteria
            self.y_criteria.update(UnintentionalIslanding.y_criteria)

        # Remove duplicates
        self.x_criteria = list(OrderedDict.fromkeys(x_criterias))
        # self.y_criteria=list(OrderedDict.fromkeys(y_criterias))
        self.meas_values = list(OrderedDict.fromkeys(x_criterias + list(self.y_criteria.keys())))

        DataLogging.__init__(self)
        ImbalanceComponent.__init__(self)


class NormalOperation(HilModel, EutParameters, DataLogging):
    def __init__(self, ts, support_interfaces):
        EutParameters.__init__(self, ts)
        HilModel.__init__(self, ts, support_interfaces)
        self._config()

    def _config(self):
        self.set_normal_params()
        self.set_vrt_modes()


"""
This section is for Ride-Through test
"""


class VoltageRideThrough(HilModel, EutParameters, DataLogging):
    def __init__(self, ts, support_interfaces):
        EutParameters.__init__(self, ts)
        HilModel.__init__(self, ts, support_interfaces)
        self.wfm_header = None
        self._config()
        self.phase_combination = None

    def _config(self):
        self.set_vrt_params()
        self.set_vrt_modes()
        self.set_wfm_file_header()

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
            self.params["phase_comb"] = self.ts.param_value('vrt.phase_comb')
            self.params["dataset"] = self.ts.param_value('vrt.dataset_type')
            self.params["consecutive_ena"] = self.ts.param_value('vrt.consecutive_ena')



        except Exception as e:
            self.ts.log_error('Incorrect Parameter value : %s' % e)
            raise

    def extend_list_end(self, _list, extend_value, final_length):
        list_length = len(_list)
        _list.extend([float(extend_value)] * (final_length - list_length))
        return _list

    def set_vrt_model_parameters(self, test_sequence):
        model_name = self.params["model_name"]
        parameters = []
        # Enable VRT mode in the IEEE1547_fast_functions model
        parameters.append(("MODE", 3.0))

        # Add ROCOM only for LVRT CAT II
        self.ts.log_debug(test_sequence)
        # if self.params["lv_mode"] == 'Enabled' and (self.params["categories"] == CAT_2 or self.params["categories"] == 'Both'):
        #     parameters.append(("ROCOF_ENABLE", 1))
        #     parameters.append(("ROCOF_VALUE", 0.115))
        #     parameters.append(("ROCOF_INIT", test_sequence.loc["D"]["Voltage"].item()))
        #     parameters.append(("ROCOM_START_TIME", test_conditionc.loc["E"]["StartTime"].item()))
        #     parameters.append(("ROCOM_END_TIME", test_conditionc.loc["E"]["StopTime"]))

        # We need to do some padding because of RT-compilation allow a fixe size.
        # In our case, with pad with 0 a vector size of 20. This will tell the state machine the final value.

        vrt_condition_list = self.extend_list_end(test_sequence["VRT_CONDITION"].to_list(), 0.0, 20)
        parameters.append(("VRT_CONDITION", vrt_condition_list))

        vrt_start_timing_list = self.extend_list_end(test_sequence["VRT_START_TIMING"].to_list(), 0.0, 20)
        parameters.append(("VRT_START_TIMING", vrt_start_timing_list))

        vrt_end_timing_list = self.extend_list_end(test_sequence["VRT_END_TIMING"].to_list(), 0.0, 20)
        parameters.append(("VRT_END_TIMING", vrt_end_timing_list))

        vrt_values_list = self.extend_list_end(test_sequence["VRT_VALUES"].to_list(), 0.0, 20)
        parameters.append(("VRT_VALUES", vrt_values_list))
        self.hil.set_matlab_variables(parameters)

    def set_phase_combination(self, phase):
        parameters = []

        for ph in phase:
            parameters.append((f"VRT_PH{ph}_ENABLE", 1.0))
        self.hil.set_matlab_variables(parameters)

    def set_wfm_file_header(self):
        self.wfm_header = ['TIME',
                           'AC_V_1', 'AC_V_2', 'AC_V_3',
                           'AC_I_1', 'AC_I_2', 'AC_I_3',
                           'AC_P_1', 'AC_P_2', 'AC_P_3',
                           'AC_Q_1', 'AC_Q_2', 'AC_Q_3',
                           'AC_V_CMD_1', 'AC_V_CMD_2', 'AC_V_CMD_3',
                           "TRIGGER"]

    def set_test_conditions(self, current_mode):
        # Set useful variables
        mra_v_pu = self.MRA["V"] / self.v_nom
        RANGE_STEPS = self.params["range_steps"]
        index = ['VRT_CONDITION', 'MIN_DURATION', 'VRT_VALUES']
        TEST_CONDITION = {}
        # each condition are set with a pandas series as follow:
        # pd.Series([test condition, minimum duration(s), Residual Voltage (p.u.)], index=index)

        # TABLE 4 - CATEGORY II LVRT TEST CONDITION
        if CAT_2 in current_mode and LV in current_mode:
            # The possible test conditions are ABCDD'EF
            if RANGE_STEPS == "Figure":
                # Using value of Figure 2 - CATEGORY II LVRT test signal
                TEST_CONDITION["A"] = pd.Series([1, 10, 0.94], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 0.160, 0.3 - 2 * mra_v_pu], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 0.160, 0.45 - 2 * mra_v_pu], index=index)
                TEST_CONDITION["D"] = pd.Series([4, 2.68, 0.65], index=index)
                TEST_CONDITION["D'"] = pd.Series([4 + 10, 7.68, 0.67 + 2 * mra_v_pu], index=index)
                TEST_CONDITION["E"] = pd.Series([5, 2.0, 0.88], index=index)
                TEST_CONDITION["F"] = pd.Series([6, 120.0, 0.94], index=index)
            elif RANGE_STEPS == "Random":
                TEST_CONDITION["A"] = pd.Series([1, 10, random.uniform(0.88 + 2 * mra_v_pu, 1.0)], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 0.160, random.uniform(0.0, 0.3 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 0.160, random.uniform(0.0, 0.45 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["D"] = pd.Series([4, 2.68, random.uniform(0.45 + 2 * mra_v_pu, 0.65 - 2 * mra_v_pu)],
                                                index=index)
                TEST_CONDITION["D'"] = pd.Series([4 + 10, 7.68, random.uniform(0.67, 0.88 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["E"] = pd.Series([5, 2.0, random.uniform(0.65 + 2 * mra_v_pu, 0.88 - 2 * mra_v_pu)],
                                                index=index)
                TEST_CONDITION["F"] = pd.Series([6, 120.0, random.uniform(0.88 + 2 * mra_v_pu, 1.0)], index=index)

        # TABLE 5 - CATEGORY III LVRT TEST CONDITION
        elif CAT_3 in current_mode and LV in current_mode:
            # The possible test conditions are ABCC'DE
            if RANGE_STEPS == "Figure":
                TEST_CONDITION["A"] = pd.Series([1, 5, 0.94], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 1, 0.05 - 2 * mra_v_pu], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 9, 0.5 - 2 * mra_v_pu], index=index)
                TEST_CONDITION["C'"] = pd.Series([3 + 10, 9, 0.52 + 2 * mra_v_pu], index=index)
                TEST_CONDITION["D"] = pd.Series([4, 10.0, 0.7], index=index)
                TEST_CONDITION["E"] = pd.Series([5, 120.0, 0.94], index=index)
            elif RANGE_STEPS == "Random":
                TEST_CONDITION["A"] = pd.Series([1, 5, random.uniform(0.88 + 2 * mra_v_pu, 1.0)], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 1, random.uniform(0.0, 0.05 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 9, random.uniform(0.0, 0.5 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["C'"] = pd.Series([3 + 10, 9, random.uniform(0.52, 0.7 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["D"] = pd.Series([4, 10.0, random.uniform(0.5 + 2 * mra_v_pu, 0.7 - 2 * mra_v_pu)],
                                                index=index)
                TEST_CONDITION["E"] = pd.Series([5, 120.0, random.uniform(0.88 + 2 * mra_v_pu, 1.0)], index=index)

        # TABLE 7 - CATEGORY II HVRT TEST CONDITION
        elif CAT_2 in current_mode and HV in current_mode:
            # ABCDE
            if RANGE_STEPS == "Figure":
                TEST_CONDITION["A"] = pd.Series([1, 10, 1.0], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 0.2, 1.2 - 2 * mra_v_pu], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 0.3, 1.175], index=index)
                TEST_CONDITION["D"] = pd.Series([4, 0.5, 1.15], index=index)
                TEST_CONDITION["E"] = pd.Series([5, 120.0, 1.0], index=index)
            elif RANGE_STEPS == "Random":
                TEST_CONDITION["A"] = pd.Series([1, 10, random.uniform(1.0, 1.1 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 0.2, random.uniform(1.18, 1.2)], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 0.3, random.uniform(1.155, 1.175)], index=index)
                TEST_CONDITION["D"] = pd.Series([4, 0.5, random.uniform(1.13, 1.15)], index=index)
                TEST_CONDITION["E"] = pd.Series([5, 120.0, random.uniform(1.0, 1.1 - 2 * mra_v_pu)], index=index)

        # TABLE 8 - CATEGORY III HVRT TEST CONDITION
        elif CAT_3 in current_mode and HV in current_mode:
            # ABB'C
            if RANGE_STEPS == "Figure":
                TEST_CONDITION["A"] = pd.Series([1, 5, 1.05], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 12, 1.2 - 2 * mra_v_pu], index=index)
                TEST_CONDITION["B'"] = pd.Series([2 + 10, 12, 1.12], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 120, 1.05], index=index)
            elif RANGE_STEPS == "Random":
                TEST_CONDITION["A"] = pd.Series([1, 5, random.uniform(1.0, 1.1 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 12, random.uniform(1.18, 1.2)], index=index)
                TEST_CONDITION["B'"] = pd.Series([2 + 10, 12, random.uniform(1.12, 1.2)], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 120, random.uniform(1.0, 1.1 - 2 * mra_v_pu)], index=index)
        '''
        Get the full test sequence :
        Example for CAT_2 + LV + Not Consecutive
                ___________________________________________________
        VRT_CONDITION  MIN_DURATION  VRT_VALUES  VRT_START_TIMING  VRT_END_TIMING
        1.0         10.00        0.94              0.00           10.00
        2.0          0.16        0.28             10.00           10.16
        3.0          0.16        0.43             10.16           10.32
        4.0          2.68        0.65             10.32           13.00
        5.0          2.00        0.88             13.00           15.00
        6.0        120.00        0.94             15.00          135.00

                Example for CAT_3 + HV + Consecutive
                ___________________________________________________
        VRT_CONDITION  MIN_DURATION  VRT_VALUES  VRT_START_TIMING  VRT_END_TIMING
        1.0           5.0        1.05               0.0             5.0
        2.0          12.0        1.20               5.0            17.0
        1.0           5.0        1.05              17.0            22.0
        2.0          12.0        1.20              22.0            34.0
        1.0           5.0        1.05              34.0            39.0
        2.0          12.0        1.20              39.0            51.0
        3.0         120.0        1.05              51.0           171.0
        1.0           5.0        1.05             171.0           176.0
        12.0         12.0        1.14             176.0           188.0
        3.0         120.0        1.05             188.0           308.0

        Note: The Test condition value is directly connected to the alphabetical order.
        The value 1.0 is for A, 2.0 is for B and so on. When a prime is present, we 
        just add the value 10.0. The value 12.0 is for B', 13 is for C' and so on.
        The idea is just to show this on the data.
        '''
        test_sequences_df = self.get_test_sequence(current_mode, TEST_CONDITION)

        return test_sequences_df

    def get_vrt_stop_time(self, test_sequences_df):
        return test_sequences_df["VRT_END_TIMING"].iloc[-1]

    def get_test_sequence(self, current_mode, test_condition):
        index = ['VRT_CONDITION', 'MIN_DURATION', 'VRT_VALUES']
        T0 = self.params["eut_startup_time"]
        if self.params["consecutive_ena"] == "Enabled":
            CONSECUTIVE = True
        else:
            CONSECUTIVE = False
        test_sequences_df = pd.DataFrame(columns=index)
        if CAT_2 in current_mode and LV in current_mode:
            if CONSECUTIVE:
                # ABCDE
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
                # ABCDEF
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["F"], ignore_index=True)
                # ABCD'F
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D'"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["F"], ignore_index=True)

            else:
                # ABCDEF 
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["F"], ignore_index=True)
        elif CAT_3 in current_mode and LV in current_mode:
            if CONSECUTIVE:
                # ABCD
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                # ABCD
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                # ABCDE
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
                # ABC'DE
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C'"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
            else:
                # ABCDE
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
        elif CAT_2 in current_mode and HV in current_mode:
            if CONSECUTIVE:
                # ABCD
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)

                # ABCDE
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
            else:
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
                pass
        elif CAT_3 in current_mode and HV in current_mode:
            if CONSECUTIVE:
                # AB
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)

                # AB
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)

                # ABC
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)

                # AB'C
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B'"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
            else:
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                pass

        test_sequences_df.loc[0, 'VRT_START_TIMING'] = T0
        # Calculate the timing sequences
        test_sequences_df.loc[0, 'VRT_END_TIMING'] = T0 + test_sequences_df.loc[0, 'MIN_DURATION']
        for i in range(1, len(test_sequences_df)):
            test_sequences_df.loc[i, 'VRT_START_TIMING'] = test_sequences_df.loc[i - 1, 'VRT_END_TIMING']
            test_sequences_df.loc[i, 'VRT_END_TIMING'] = test_sequences_df.loc[i, 'VRT_START_TIMING'] + \
                                                         test_sequences_df.loc[i, 'MIN_DURATION']
        return test_sequences_df

    def set_vrt_modes(self):
        modes = []
        if self.params["lv_mode"] == 'Enabled' and (
                self.params["categories"] == CAT_2 or self.params["categories"] == 'Both'):
            modes.append(f"{LV}_{CAT_2}")
        if self.params["lv_mode"] == 'Enabled' and (
                self.params["categories"] == CAT_3 or self.params["categories"] == 'Both'):
            modes.append(f"{LV}_{CAT_3}")
        if self.params["hv_mode"] == 'Enabled' and (
                self.params["categories"] == CAT_2 or self.params["categories"] == 'Both'):
            modes.append(f"{HV}_{CAT_2}")
        if self.params["hv_mode"] == 'Enabled' and (
                self.params["categories"] == CAT_3 or self.params["categories"] == 'Both'):
            modes.append(f"{HV}_{CAT_3}")
        self.params["modes"] = modes
        self.ts.log_debug(self.params)

    """
    Getter functions
    """

    def get_wfm_file_header(self):
        return self.wfm_header

    def get_modes(self):
        return self.params["modes"]


class FrequencyRideThrough(HilModel, EutParameters, DataLogging):
    def __init__(self, ts, support_interfaces):
        EutParameters.__init__(self, ts)
        self.params = {}
        # HilModel.__init__(self, ts, support_interfaces)
        self.wfm_header = None
        self._config()

    def _config(self):
        self.set_frt_params()
        self.set_modes()
        self.set_wfm_file_header()

    """
    Setter functions
    """

    def set_frt_params(self):
        try:
            # RT test parameters
            self.params["lf_mode"] = self.ts.param_value('frt.lf_ena')
            self.params["hf_mode"] = self.ts.param_value('frt.hf_ena')
            self.params["lf_parameter"] = self.ts.param_value('frt.lf_parameter')
            self.params["lf_period"] = self.ts.param_value('frt.lf_period')
            self.params["hf_parameter"] = self.ts.param_value('frt.hf_parameter')
            self.params["hf_period"] = self.ts.param_value('frt.hf_period')
            self.params["eut_startup_time"] = self.ts.param_value('eut.startup_time')
            # self.params["model_name"] = self.hil.rt_lab_model

        except Exception as e:
            self.ts.log_error('Incorrect Parameter value : %s' % e)
            raise

    def set_modes(self):

        modes = []
        if self.params["lf_mode"] == "Enabled":
            modes.append(LFRT)
        if self.params["hf_mode"] == "Enabled":
            modes.append(HFRT)
        self.params["modes"] = modes

    def set_wfm_file_header(self):
        self.wfm_header = ['TIME',
                           'AC_V_1', 'AC_V_2', 'AC_V_3',
                           'AC_I_1', 'AC_I_2', 'AC_I_3',
                           'AC_FREQ_CMD', "TRIGGER"]

    def set_test_conditions(self, current_mode):
        # Set useful variables
        mra_f = self.MRA["F"]
        index = ['FRT_CONDITION', 'MIN_DURATION', 'FRT_VALUES']
        TEST_CONDITION = {}
        # Test Procedure 5.5.3.4
        if LFRT in current_mode:
            TEST_CONDITION["Step E"] = pd.Series([1, 1, self.f_nom], index=index)
            TEST_CONDITION["Step G"] = pd.Series([2, self.params["lf_period"], self.params["lf_parameter"]],
                                                 index=index)
            TEST_CONDITION["Step H"] = pd.Series([1, 1, self.f_nom], index=index)

        # TABLE 5 - CATEGORY III LVRT TEST CONDITION
        elif HFRT in current_mode:
            TEST_CONDITION["Step E"] = pd.Series([1, 1, self.f_nom], index=index)
            TEST_CONDITION["Step G"] = pd.Series([2, self.params["hf_period"], self.params["hf_parameter"]],
                                                 index=index)
            TEST_CONDITION["Step H"] = pd.Series([1, 1, self.f_nom], index=index)
        test_sequences_df = self.get_test_sequence(current_mode, TEST_CONDITION)

        return test_sequences_df

    def set_frt_model_parameters(self, test_sequence):
        model_name = self.params["model_name"]
        parameters = []
        # Enable FRT mode in the IEEE1547_fast_functions model
        parameters.append(("MODE", 4.0))

        condition_list = self.extend_list_end(test_sequence["FRT_CONDITION"].to_list(), 0.0, 4)
        parameters.append(("FRT_CONDITION", condition_list))

        start_timing_list = self.extend_list_end(test_sequence["FRT_START_TIMING"].to_list(), 0.0, 4)
        parameters.append(("FRT_START_TIMING", start_timing_list))

        end_timing_list = self.extend_list_end(test_sequence["FRT_END_TIMING"].to_list(), 0.0, 4)
        parameters.append(("FRT_END_TIMING", end_timing_list))

        values_list = self.extend_list_end(test_sequence["FRT_VALUES"].to_list(), 0.0, 4)
        parameters.append(("FRT_VALUES", values_list))
        self.hil.set_matlab_variables(parameters)

    """
    Getter functions
    """

    def get_rocof_dic(self, ):
        params = {"ROCOF_ENABLE": 1.0,
                  "ROCOF_VALUE": 3.0,
                  "ROCOF_INIT": 60.0}
        return params

    def get_test_sequence(self, current_mode, test_condition):
        index = ['FRT_CONDITION', 'MIN_DURATION', 'FRT_VALUES']
        T0 = self.params["eut_startup_time"]
        test_sequences_df = pd.DataFrame(columns=index)
        test_sequences_df = test_sequences_df.append(test_condition["Step E"], ignore_index=True)
        test_sequences_df = test_sequences_df.append(test_condition["Step G"], ignore_index=True)
        test_sequences_df = test_sequences_df.append(test_condition["Step H"], ignore_index=True)

        test_sequences_df.loc[0, 'FRT_START_TIMING'] = T0
        # Calculate the timing sequences
        test_sequences_df.loc[0, 'FRT_END_TIMING'] = T0 + test_sequences_df.loc[0, 'MIN_DURATION']
        for i in range(1, len(test_sequences_df)):
            test_sequences_df.loc[i, 'FRT_START_TIMING'] = test_sequences_df.loc[i - 1, 'FRT_END_TIMING']
            test_sequences_df.loc[i, 'FRT_END_TIMING'] = test_sequences_df.loc[i, 'FRT_START_TIMING'] + \
                                                         test_sequences_df.loc[i, 'MIN_DURATION']
        return test_sequences_df

    def get_frt_stop_time(self, test_sequences_df):
        return test_sequences_df["FRT_END_TIMING"].iloc[-1]

    def get_modes(self):
        return self.params["modes"]

    def get_wfm_file_header(self):
        return self.wfm_header

    def extend_list_end(self, _list, extend_value, final_length):
        list_length = len(_list)
        _list.extend([float(extend_value)] * (final_length - list_length))
        return _list


if __name__ == "__main__":
    pass
