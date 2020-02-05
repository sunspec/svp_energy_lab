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

# import sys
# import os
# import glob
# import importlib


FW = 'FW'
CPF = 'CPF'
VW = 'VW'
VV = 'VV'
WV = 'WV'
CRP = 'CRP'
LAP = 'LAP'
PRI = 'PRI'

VOLTAGE = "V"
FREQUENCY = "F"


class p1547Error(Exception):
    pass


class module_1547(object):
    script_name = ''

    def __init__(self, ts, aif, imbalance_angle_fix='std', absorb='No'):
        """
        param ts: test script object
        param aif: name of the test
        param imbalance_angle_fix: indicates if the phase imbalance tests force the phase angles to be symmetrical
        param absorb: dictionary if the EUT includes storage containing {'ena', 'p_rated_prime'}
        """

        # Library variables
        self.ts = ts
        # self.params = params
        self.script_name = aif
        self.script_complete_name = aif
        self.rslt_sum_col_name = ''
        self.sc_points = {}
        self.pairs = {}
        self.mag = {}
        self.ang = {}
        self.param = {}
        self.x_criteria = None
        self.y_criteria = None
        self.step_label = None
        self.double_letter_label = False

        """
        According to Table 3-Minimum requirements for manufacturers stated measured and calculated accuracy
        """
        if ts.param_value('eut.v_nom') is not None:
            self.v_nom = ts.param_value('eut.v_nom')
        else:
            self.v_nom = None
        self.MSA_V = 0.01 * self.v_nom

        # if ts.param_value('eut.s_rated') is not None:
        self.MSA_Q = 0.05 * ts.param_value('eut.s_rated')
        self.MSA_P = 0.05 * ts.param_value('eut.s_rated')
        # else:
        #   self.MSA_Q = None
        #   self.MSA_P = None
        self.MSA_F = 0.01
        if ts.param_value('eut.f_nom') is not None:
            self.f_nom = ts.param_value('eut.f_nom')
        else:
            self.f_nom = None
        if ts.param_value('eut.phases') is not None:
            self.phases = ts.param_value('eut.phases')
        else:
            self.phases = None
        if ts.param_value('eut.p_rated') is not None:
            self.p_rated = ts.param_value('eut.p_rated')
            self.p_min = ts.param_value('eut.p_min')
        else:
            self.p_rated = None
            self.p_min = None
        if ts.param_value('eut.var_rated') is not None:
            self.var_rated = ts.param_value('eut.var_rated')
        else:
            self.var_rated = None

        if ts.param_value('eut.s_rated') is not None:
            self.s_rated = ts.param_value('eut.s_rated')
        else:
            self.s_rated = None
        self.imbalance_angle_fix = imbalance_angle_fix
        self.absorb = absorb

        self._config()

    def _config(self):
        # Set Complete test name
        self.set_complete_test_name()
        # Set Sc points
        self.set_sc_points()
        # Set the result summary column names
        self.set_result_summary_col_name()
        # Create the pairs need
        self.set_params()
        # Configure test for imblance operation
        self.set_imbalance_config()
        # Configure the x and y variable for criteria
        self.set_x_y_variable()

    """
    Setter functions
    """
    
    def set_complete_test_name(self):
        """
        Write full complete test names
        :param nothing:
        :return: nothing
        """
        if self.script_name == FW:
            self.script_complete_name = 'Frequency-Watt'
        elif self.script_name == CPF:
            self.script_complete_name = 'Constant Power Factor'
        elif self.script_name == VW:
            self.script_complete_name = 'Volt-Watt'
        elif self.script_name == VV:
            self.script_complete_name = 'Volt-Var'
        elif self.script_name == WV:
            self.script_complete_name = 'Watt-Var'
        elif self.script_name == CRP:
            self.script_complete_name = 'Constant Reactive Power'
        else:
            self.script_complete_name = self.script_name

    def set_result_summary_col_name(self):
        """
        Write column names for results file depending on which test is being run
        :param nothing:
        :return: nothing
        """
        if self.script_name == CPF:
            self.rslt_sum_col_name = 'Q_TR_ACC_REQ, TR_REQ, Q_FINAL_ACC_REQ, P_MEAS, Q_MEAS, Q_TARGET, Q_TARGET_MIN,' \
                                     'Q_TARGET_MAX, STEP, FILENAME\n'
        elif self.script_name == VV:
            self.rslt_sum_col_name = 'Q_TR_ACC_REQ, TR_REQ, Q_FINAL_ACC_REQ, P_MEAS, V_MEAS, Q_MEAS, V_TARGET, Q_TARGET_MIN,' \
                                     'Q_TARGET_MAX, STEP, FILENAME\n'
        elif self.script_name == VW:
            self.rslt_sum_col_name = 'P_TR_ACC_REQ, TR_REQ, P_FINAL_ACC_REQ, V_MEAS, P_MEAS, P_TARGET, P_TARGET_MIN,' \
                                     'P_TARGET_MAX, STEP, FILENAME\n'
        elif self.script_name == FW:
            self.rslt_sum_col_name = 'P_TR_ACC_REQ, TR_REQ, P_FINAL_ACC_REQ, F_MEAS, P_MEAS, P_TARGET, P_TARGET_MIN,' \
                                     'P_TARGET_MAX, STEP, FILENAME\n'
        elif self.script_name == WV:
            self.rslt_sum_col_name = 'Q_TR_ACC_REQ, TR_REQ, Q_FINAL_ACC_REQ, P_MEAS, Q_MEAS, Q_TARGET, Q_TARGET_MIN,' \
                                     'Q_TARGET_MAX, STEP, FILENAME\n'
        elif self.script_name == CRP:
            self.rslt_sum_col_name = 'Q_TR_ACC_REQ, TR_REQ, Q_FINAL_ACC_REQ, P_MEAS, Q_MEAS, Q_TARGET, Q_TARGET_MIN,' \
                                     'Q_TARGET_MAX, STEP, FILENAME\n'
        elif self.script_name == LAP:
            self.rslt_sum_col_name = 'Q_TR_ACC_REQ, TR_REQ, Q_FINAL_ACC_REQ, P_MEAS, V_MEAS, F_MEAS, P_TARGET, ' \
                                     'P_TARGET_MIN, P_TARGET_MAX, STEP, FILENAME\n'

    def set_sc_points(self):
        """
        Set SC points for DAS depending on which test is being run
        :param nothing:
        :return: nothing
        """
        if self.script_name == CPF:
            self.sc_points['sc'] = (
            'V_MEAS', 'P_MEAS', 'Q_MEAS', 'Q_TARGET', 'Q_TARGET_MIN', 'Q_TARGET_MAX', 'PF_TARGET', 'event')
        elif self.script_name == VV:
            self.sc_points['sc'] = ('Q_TARGET', 'Q_TARGET_MIN', 'Q_TARGET_MAX', 'Q_MEAS', 'V_TARGET', 'V_MEAS', 'event')
        elif self.script_name == VW:
            self.sc_points['sc'] = ('P_TARGET', 'P_TARGET_MIN', 'P_TARGET_MAX', 'P_MEAS', 'V_TARGET', 'V_MEAS', 'event')
        elif self.script_name == FW:
            self.sc_points['sc'] = ('P_TARGET', 'P_TARGET_MIN', 'P_TARGET_MAX', 'P_MEAS', 'F_TARGET', 'F_MEAS', 'event')
        elif self.script_name == WV:
            self.sc_points['sc'] = ('Q_TARGET', 'Q_TARGET_MIN', 'Q_TARGET_MAX', 'Q_MEAS', 'P_TARGET', 'P_MEAS', 'event')
        elif self.script_name == CRP:
            self.sc_points['sc'] = ('V_MEAS', 'P_MEAS', 'Q_MEAS', 'Q_TARGET_MIN', 'Q_TARGET_MAX', 'PF_TARGET', 'event')
        elif self.script_name == LAP:
            self.sc_points['sc'] = ('V_MEAS', 'F_MEAS', 'P_MEAS', 'P_TARGET_MIN', 'P_TARGET_MAX', \
                                    'V_TARGET', 'F_TARGET', 'P_TARGET', 'event')

    def set_params(self):
        """
        Configure the parameter specific to the AIF
        :param nothing:
        :return: nothing
        """

        if self.script_name == VW or (self.script_name == LAP and self.get_x_y_variable('x') == 'V'):
            self.param[1] = {'V1': round(1.06 * self.v_nom, 2),
                             'V2': round(1.10 * self.v_nom, 2),
                             'P1': round(self.p_rated, 2)}

            self.param[2] = {'V1': round(1.05 * self.v_nom, 2),
                             'V2': round(1.10 * self.v_nom, 2),
                             'P1': round(self.p_rated, 2)}

            self.param[3] = {'V1': round(1.09 * self.v_nom, 2),
                             'V2': round(1.10 * self.v_nom, 2),
                             'P1': round(self.p_rated, 2)}

            if self.p_min > (0.2 * self.p_rated):
                self.param[1]['P2'] = int(0.2 * self.p_rated)
                self.param[2]['P2'] = int(0.2 * self.p_rated)
                self.param[3]['P2'] = int(0.2 * self.p_rated)
            elif self.absorb == 'Yes':
                self.param[1]['P2'] = 0
                self.param[2]['P2'] = self.absorb['p_rated_prime']
                self.param[3]['P2'] = self.absorb['p_rated_prime']
            else:
                self.param[1]['P2'] = int(self.p_min)
                self.param[2]['P2'] = int(self.p_min)
                self.param[3]['P2'] = int(self.p_min)

        if self.script_name == FW or (self.script_name == LAP and self.get_x_y_variable('x') == 'F'):
            p_small = self.ts.param_value('eut_fw.p_small')
            if p_small is None:
                p_small = 0.05
            self.param[1] = {"dbf": 0.036,
                             'kof': 0.05,
                             'tr': self.ts.param_value('fw.test_1_tr'),
                             'f_small': p_small * self.f_nom * 0.05
                             }
            self.param[2] = {'dbf': 0.017,
                             'kof': 0.03,
                             'tr': self.ts.param_value('fw.test_2_tr'),
                             'f_small': p_small * self.f_nom * 0.02
                             }

        elif self.script_name == VV:
            self.param[1] = {'V1': round(0.92 * self.v_nom, 2),
                             'V2': round(0.98 * self.v_nom, 2),
                             'V3': round(1.02 * self.v_nom, 2),
                             'V4': round(1.08 * self.v_nom, 2),
                             # 'V4': round(1.08 * self.v_nom, 2),
                             'Q1': round(self.s_rated * 0.44, 2),
                             'Q2': round(self.s_rated * 0.0, 2),
                             'Q3': round(self.s_rated * 0.0, 2),
                             'Q4': round(self.s_rated * -0.44, 2)}

            self.param[2] = {'V1': round(0.88 * self.v_nom, 2),
                             'V2': round(1.04 * self.v_nom, 2),
                             'V3': round(1.07 * self.v_nom, 2),
                             'V4': round(1.10 * self.v_nom, 2),
                             'Q1': round(self.var_rated * 1.0, 2),
                             'Q2': round(self.var_rated * 0.5, 2),
                             'Q3': round(self.var_rated * 0.5, 2),
                             'Q4': round(self.var_rated * -1.0, 2)}

            self.param[3] = {'V1': round(0.90 * self.v_nom, 2),
                             'V2': round(0.93 * self.v_nom, 2),
                             'V3': round(0.96 * self.v_nom, 2),
                             'V4': round(1.10 * self.v_nom, 2),
                             'Q1': round(self.var_rated * 1.0, 2),
                             'Q2': round(self.var_rated * -0.5, 2),
                             'Q3': round(self.var_rated * -0.5, 2),
                             'Q4': round(self.var_rated * -1.0, 2)}

        # Two sets of value depending if EUT can absorb power or not
        elif self.script_name == "WV":
            if self.absorb is not "Yes":
                self.ts.log('EUT able to absorb: No, P values loaded for characteristic curve')
                self.ts.log('p_min={}'.format(self.p_min))
                self.ts.log('0.2p_rated={}'.format(0.2 * self.p_rated))

                if self.p_min > 0.2 * self.p_rated:
                    p = self.p_min
                    self.ts.log('p_min')
                else:
                    p = 0.2 * self.p_rated
                    self.ts.log('20%p_rated')
                # Added another Q(P) points since EUT looks to be asking for 4 pts
                self.param[1] = {'P0': 0,
                                 'P1': round(p, 2),
                                 'P2': round(0.5 * self.p_rated, 2),
                                 'P3': round(1.0 * self.p_rated, 2),
                                 'Q0': round(self.var_rated * 0.0, 2),
                                 'Q1': round(self.var_rated * 0.0, 2),
                                 'Q2': round(self.var_rated * 0.0, 2),
                                 'Q3': round(self.var_rated * -1.0, 2)}

                self.param[2] = {'P0': 0,
                                 'P1': round(p, 2),
                                 'P2': round(0.5 * self.p_rated, 2),
                                 'P3': round(1.0 * self.p_rated, 2),
                                 'Q0': round(self.var_rated * 0.0, 2),
                                 'Q1': round(self.var_rated * -0.5, 2),
                                 'Q2': round(self.var_rated * -0.5, 2),
                                 'Q3': round(self.var_rated * -1.0, 2)}

                self.param[3] = {'P0': 0,
                                 'P1': round(p, 2),
                                 'P2': round(0.5 * self.p_rated, 2),
                                 'P3': round(1.0 * self.p_rated, 2),
                                 'Q0': round(self.var_rated * 0.0, 2),
                                 'Q1': round(self.var_rated * 0.0, 2),
                                 'Q2': round(self.var_rated * -1.0, 2),
                                 'Q3': round(self.var_rated * -1.0, 2)}

                self.ts.log('P points:{}'.format(self.param))
            else:
                self.ts.log('EUT able to absorb: Yes, P prime values loaded for characteristic curve')
                if self.p_min < 0.2 * self.p_rated:
                    p = self.p_min
                else:
                    p = 0.2 * self.p_rated
                self.param[1] = {'P1': round(p, 2),
                                 'P2': round(0.5 * self.p_rated, 2),
                                 'P3': round(1.0 * self.p_rated, 2),
                                 'Q1': 0,
                                 'Q2': 0,
                                 'Q3': round(-0.44 * self.var_rated, 2)}

                self.param[2] = {'P1': round(p, 2),
                                 'P2': round(0.5 * self.p_rated, 2),
                                 'P3': round(1.0 * self.p_rated, 2),
                                 'Q1': round(-0.22 * self.var_rated, 2),
                                 'Q2': round(-0.22 * self.var_rated, 2),
                                 'Q3': round(-0.44 * self.var_rated, 2)}

                self.param[3] = {'P1': round(p, 2),
                                 'P2': round(0.5 * self.p_rated, 2),
                                 'P3': round(1.0 * self.p_rated, 2),
                                 'Q1': round(0 * self.var_rated, 2),
                                 'Q2': round(-0.44 * self.var_rated, 2),
                                 'Q3': round(-0.44 * self.var_rated, 2)}

    def get_x_y_variable(self, letter):
        """
        A simple getter that return the x or y value of the corresponding AIF

        :param letter:   A string (x or y)
        :return: A string
        """
        if letter == 'x':
            return self.x_criteria
        elif letter == 'y':
            return self.y_criteria
        else:
            raise p1547Error("Error in get_x_y_variable(). Must be either 'x' or 'y' as argument")

    def set_grid_asymmetric(self, grid, case):
        """
        Configure the grid simulator to change the magnitude and angles.
        :param grid:   A gridsim object from the svpelab library
        :param case:   string (case_a or case_b)
        :return: nothing
        """

        if grid is not None:
            grid.config_asymmetric_phase_angles(mag=self.mag[case], angle=self.ang[case])

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

    def set_imbalance_config(self, imbalance_angle_fix=None):
        """
        Initiliaze the case possibility for imbalance test either with fix 120 degrees for the angle or
        with a calculated angles that would result in a null sequence zero
        :param imbalance_angle_fix:   string (Yes or No)
        if Yes, angle are fix at 120 degrees for both cases.
        if No, resulting sequence zero will be null for both cases.

        :return: nothing
        """

        if self.imbalance_angle_fix == 'std':
            # Case A
            self.mag['case_a'] = [1.07 * self.v_nom, 0.91 * self.v_nom, 0.91 * self.v_nom]
            self.ang['case_a'] = [0., 120, -120]
            # Case B
            self.mag['case_b'] = [0.91 * self.v_nom, 1.07 * self.v_nom, 1.07 * self.v_nom]
            self.ang['case_b'] = [0., 120.0, -120.0]
            self.ts.log("Setting test with imbalanced test with FIXED angles/values")
        elif self.imbalance_angle_fix == 'fix_mag':
            # Case A
            self.mag['case_a'] = [1.07 * self.v_nom, 0.91 * self.v_nom, 0.91 * self.v_nom]
            self.ang['case_a'] = [0., 126.59, -126.59]
            # Case B
            self.mag['case_b'] = [0.91 * self.v_nom, 1.07 * self.v_nom, 1.07 * self.v_nom]
            self.ang['case_b'] = [0., 114.5, -114.5]
            self.ts.log("Setting test with imbalanced test with NOT FIXED angles/values")
        elif self.imbalance_angle_fix == 'fix_ang':
            # Case A
            self.mag['case_a'] = [1.08 * self.v_nom, 0.91 * self.v_nom, 0.91 * self.v_nom]
            self.ang['case_a'] = [0., 120, -120]
            # Case B
            self.mag['case_b'] = [0.9 * self.v_nom, 1.08 * self.v_nom, 1.08 * self.v_nom]
            self.ang['case_a'] = [0., 120, -120]
            self.ts.log("Setting test with imbalanced test with NOT FIXED angles/values")
        elif self.imbalance_angle_fix == 'not_fix':
            # Case A
            self.mag['case_a'] = [1.08 * self.v_nom, 0.91 * self.v_nom, 0.91 * self.v_nom]
            self.ang['case_a'] = [0., 126.59, -126.59]
            # Case B
            self.mag['case_b'] = [0.9 * self.v_nom, 1.08 * self.v_nom, 1.08 * self.v_nom]
            self.ang['case_b'] = [0., 114.5, -114.5]
            self.ts.log("Setting test with imbalanced test with NOT FIXED angles/values")

    def set_x_y_variable(self, x=None, y=None, step=None):
        """
        A simple setter that sets the x or y value of the corresponding AIF
        :param x:   A string (x or y)
        :param y:   A string (x or y)
        :param step:   The step of the test since now it change sometimes during the test
        :return: Nothing
        """
        self.ts.log_debug("%s" % step)
        if self.script_name == VW or self.script_name == FW or self.script_name == LAP:
            self.y_criteria = 'P'
            if self.script_name == VW:
                self.x_criteria = 'V'
            elif self.script_name == FW:
                self.x_criteria = 'F'
            elif self.script_name == LAP and step is not None:
                if step == "Step C" or "Step D" in step or "Step E" in step:
                    self.x_criteria = "F"
                elif "Step F" in step:
                    self.x_criteria = "V"
                else:
                    self.x_criteria = "None"

        if self.script_name == CPF or self.script_name == VV or \
                self.script_name == "WV" or self.script_name == CRP:
            self.y_criteria = 'Q'
            if self.script_name == VV:
                self.x_criteria = 'V'
            elif self.script_name == CPF or self.script_name == "WV" or self.script_name == CRP:
                self.x_criteria = 'P'

    def set_step_label(self, starting_label=None):
        """
        Write step labels in alphabetical order as shown in the standard
        :param nothing:
        :return: nothing
        """
        self.double_letter_label = False

        if starting_label is None:
            starting_label = 'a'
        starting_label_value = ord(starting_label)
        self.step_label = starting_label_value

    def write_rslt_sum(self, analysis, step, filename):
        """
        Combines the analysis results, the step label and the filenamoe to return
        a row that will go in result_summary.csv
        :param analysis: Dictionnary with all the information for result summary
        :param step:   test procedure step letter or number (e.g "Step G")
        :param filename: the dataset filname use for analysis
        :return: row_data a string with all the information for result_summary.csv
        """
        row_data = ''
        try:
            if self.get_test_name() == 'LAP':

                x = self.get_x_y_variable('x')
                y = self.get_x_y_variable('y')
                first_iter = analysis['FIRST_ITER']
                last_iter = analysis['LAST_ITER']
                row_data = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (analysis['%s_TR_%s_PF' % (y, first_iter)],
                                                                   analysis['TR_90_%_PF'],
                                                                   analysis['%s_TR_%s_PF' % (y, last_iter)],
                                                                   analysis['P_MEAS_%s' % last_iter],
                                                                   analysis['V_MEAS_%s' % last_iter],
                                                                   analysis['F_MEAS_%s' % last_iter],
                                                                   analysis['%s_TR_TARG_%s' % (y, last_iter)],
                                                                   analysis['%s_TR_%s_MIN' % (y, last_iter)],
                                                                   analysis['%s_TR_%s_MAX' % (y, last_iter)],
                                                                   step,
                                                                   filename)
            elif self.get_test_name() == 'VV':
                x = self.get_x_y_variable('x')
                y = self.get_x_y_variable('y')
                first_iter = analysis['FIRST_ITER']
                last_iter = analysis['LAST_ITER']
                row_data = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (analysis['%s_TR_%s_PF' % (y, first_iter)],
                                                                   analysis['TR_90_%_PF'],
                                                                   analysis['%s_TR_%s_PF' % (y, last_iter)],
                                                                   analysis['P_MEAS_%s' % last_iter],
                                                                   analysis['V_MEAS_%s' % last_iter],
                                                                   analysis['F_MEAS_%s' % last_iter],
                                                                   analysis['%s_TR_TARG_%s' % (y, last_iter)],
                                                                   analysis['%s_TR_%s_MIN' % (y, last_iter)],
                                                                   analysis['%s_TR_%s_MAX' % (y, last_iter)],
                                                                   step,
                                                                   filename)
            else:
                x = self.get_x_y_variable('x')
                y = self.get_x_y_variable('y')
                first_iter = analysis['LAST_ITER']
                last_iter = analysis['LAST_ITER']
                row_data = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (analysis['%s_TR_%s_PF' % (y, first_iter)],
                                                                analysis['TR_90_%_PF'],
                                                                analysis['%s_TR_%s_PF' % (y, last_iter)],
                                                                analysis['%s_TR_%s' % (x, last_iter)],
                                                                analysis['%s_TR_%s' % (y, last_iter)],
                                                                analysis['%s_TR_TARG_%s' % (y, last_iter)],
                                                                analysis['%s_TR_%s_MIN' % (y, last_iter)],
                                                                analysis['%s_TR_%s_MAX' % (y, last_iter)],
                                                                step,
                                                                filename)
            return row_data
        except Exception as e:
            raise p1547Error('Error in write_rslt_sum() : %s' % (str(e)))

    """
    Getter functions
    """
    def get_step_label(self):
        """
        get the step labels and increment in alphabetical order as shown in the standard
        :param nothing:
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

    def get_test_name(self):
        """
        This getters function returns the advanced inverter function complete name
        :return: test_name as a String
        """
        return self.script_complete_name

    def get_rslt_sum_col_name(self):
        """
        This getters function returns the column name for result_summary.csv
        :return:            self.rslt_sum_col_name
        """
        return self.rslt_sum_col_name

    def get_sc_points(self):
        """
        This getters function returns the sc points for DAS
        :return:            self.sc_points
        """
        return self.sc_points

    def get_measurement_label(self, type_meas):
        """
        Sum the EUT reactive power from all phases
        :param type_meas:   Either V, P, PF, I, F, VA, or Q
        :return:            List of labeled measurements
        """
        meas_label = None
        if type_meas == 'V':
            meas_root = 'AC_VRMS'
        elif type_meas == 'P':
            meas_root = 'AC_P'
        elif type_meas == 'PF':
            meas_root = 'AC_PF'
        elif type_meas == 'I':
            meas_root = 'AC_IRMS'
        elif type_meas == 'F':
            meas_root = 'AC_FREQ'
        elif type_meas == 'VA':
            meas_root = 'AC_S'
        else:
            meas_root = 'AC_Q'

        if self.phases == 'Single phase':
            meas_label = [meas_root + '_1']
        elif self.phases == 'Split phase':
            meas_label = [meas_root + '_1', meas_root + '_2']
        elif self.phases == 'Three phase':
            meas_label = [meas_root + '_1', meas_root + '_2', meas_root + '_3']

        return meas_label

    def get_measurement_total(self, data, type_meas, log):
        """
        Sum the EUT reactive power from all phases
        :param data:        dataset from data acquisition object
        :param type_meas:   Either V,P or Q
        :param log:         Boolean variable to disable or enable logging
        :return: Any measurements from the DAQ
        """
        value = None
        nb_phases = None

        self.ts.log_debug('data meas= %s' % data)

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
            self.ts.log_error('type_meas=%s' % type_meas)

            raise p1547Error('Error in get_measurement_total() : %s' % (str(e)))

        # TODO : imbalance_resp should change the way you acquire the data
        if type_meas == 'V':
            # average value of V
            value = value / nb_phases

        elif type_meas == 'F':
            # No need to do data average for frequency
            value = data.get(self.get_measurement_label(type_meas)[0])

        elif type_meas == 'P':
            # TODO need to handle energy storage systems that will have negative power values
            return abs(value)

        return value

    def get_initial_value(self, daq, step):
        """
        Sum the EUT reactive power from all phases
        :param daq:         data acquisition object from svpelab library
        :param step:        test procedure step letter or number (e.g "Step G")
        :return: returns a dictionary with the timestamp, event and total EUT reactive power
        """
        # TODO : In a more sophisticated approach, get_initial['timestamp'] will come from a
        #  reliable secure thread or data acquisition timestamp
        self.set_x_y_variable(step=step)
        initial = {}
        initial['timestamp'] = datetime.now()
        x = self.get_x_y_variable('x')
        y = self.get_x_y_variable('y')
        daq.data_sample()
        data = daq.data_capture_read()
        daq.sc['event'] = step
        if isinstance(x, list):
            for xs in x:
                initial[xs] = {'x_value': self.get_measurement_total(data=data, type_meas=xs, log=False)}
                daq.sc['%s_MEAS' % xs] = initial[xs]['x_value']
        else:
            initial[x] = {'x_value': self.get_measurement_total(data=data, type_meas=x, log=False)}
            daq.sc['%s_MEAS' % x] = initial[x]['x_value']
        if isinstance(y, list):
            for ys in y:
                initial[ys] = {'y_value': self.get_measurement_total(data=data, type_meas=ys, log=False)}
                daq.sc['%s_MEAS' % ys] = initial[ys]["y_value"]
        else:
            initial[y] = {'y_value': self.get_measurement_total(data=data, type_meas=y, log=False)}
            daq.sc['%s_MEAS' % y] = initial[y]['y_value']
        daq.data_sample()

        return initial

    def update_target_value(self, daq, pwr_lvl=None, curve=None, x_target=None, y_target=None, step=None, data=None):
        x = self.get_x_y_variable('x')
        y = self.get_x_y_variable('y')

        # TODO : This is returning the MIN and Max but not the target value

        if self.script_name == CPF:
            daq.sc['%s_TARGET_MIN' % y] = self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_P * 1.5, pwr_lvl, pf=x_target) \
                                          - 1.5 * self.MSA_Q
            daq.sc['%s_TARGET_MAX' % y] = self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_P * 1.5, pwr_lvl, pf=x_target) \
                                          + 1.5 * self.MSA_Q
        elif self.script_name == VV:
            v_meas = self.get_measurement_total(data=data, type_meas='V', log=False)

            daq.sc['%s_TARGET_MIN' % y] = self.get_targ(v_meas + self.MSA_V * 1.5, pwr_lvl, curve) - \
                                          (self.MSA_Q * 1.5)
            daq.sc['%s_TARGET_MAX' % y] = self.get_targ(v_meas - self.MSA_V * 1.5, pwr_lvl, curve) + \
                                          (self.MSA_Q * 1.5)
            '''
            daq.sc['%s_TARGET_MIN' % y] = self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_V * 1.5, pwr_lvl, curve) - \
                                          (self.MSA_Q * 1.5)
            daq.sc['%s_TARGET_MAX' % y] = self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_V * 1.5, pwr_lvl, curve) + \
                                          (self.MSA_Q * 1.5)
            '''
        elif self.script_name == VW:
            daq.sc['%s_TARGET_MIN' % y] = self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_V * 1.5, pwr_lvl, curve) - (
                    self.MSA_P * 1.5)
            daq.sc['%s_TARGET_MAX' % y] = self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_V * 1.5, pwr_lvl, curve) + (
                    self.MSA_P * 1.5)
        elif self.script_name == FW:
            daq.sc['P_TARGET_MIN'] = self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_F * 1.5, pwr_lvl, curve) - (
                    self.MSA_P * 1.5)
            daq.sc['P_TARGET_MAX'] = self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_F * 1.5, pwr_lvl, curve) + (
                    self.MSA_P * 1.5)
        elif self.script_name == "WV":
            daq.sc['%s_TARGET_MIN' % y] = self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_P * 1.5,
                                                        pwr_lvl, curve) - (self.MSA_Q * 1.5)
            daq.sc['%s_TARGET_MAX' % y] = self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_P * 1.5,
                                                        pwr_lvl, curve) + (self.MSA_Q * 1.5)
        elif self.script_name == CRP:
            daq.sc['%s_TARGET_MIN' % y] = y_target * 0.9
            daq.sc['%s_TARGET_MAX' % y] = y_target * 1.1

        elif self.script_name == LAP:
            if x == "V" and x_target is not None:
                daq.sc['%s_TARGET_MIN' % y] = self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_V * 1.5, pwr_lvl,
                                                            curve, variable=x) - (
                                                      self.MSA_P * 1.5)
                daq.sc['%s_TARGET_MAX' % y] = self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_V * 1.5, pwr_lvl,
                                                            curve, variable=x) + (
                                                      self.MSA_P * 1.5)
                daq.sc['%s_TARGET' % x] = x_target
            elif x == "F" and x_target is not None:
                daq.sc['P_TARGET_MIN'] = self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_F * 1.5, pwr_lvl,
                                                       curve, variable=x) - (self.MSA_P * 1.5)
                daq.sc['P_TARGET_MAX'] = self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_F * 1.5, pwr_lvl,
                                                       curve, variable=x) + (self.MSA_P * 1.5)
                daq.sc['%s_TARGET' % x] = x_target

            elif x_target is None and y_target is not None:
                daq.sc['P_TARGET_MIN'] = y_target * self.p_rated - (self.MSA_P * 1.5)
                daq.sc['P_TARGET_MAX'] = y_target * self.p_rated + (self.MSA_P * 1.5)
                daq.sc['%s_TARGET' % y] = y_target * self.p_rated


        elif self.script_name == PRI:
            # TODO : SPECIAL TARGET need to check standard each step is different Mulitple X and Mulitple Y
            self.ts.log("update_target_value() to be done")
        daq.data_sample()

    def get_tr_value(self, daq, initial_value, tr, step, number_of_tr=2, pwr_lvl=None, curve=None, x_target=None,
                     y_target=None):
        """
        Get the data from a specific time response (tr) corresponding to x and y values
        of the aif (e.g. aif='VW' x == voltage and y == active power) returns a dictionary
        but also writes in the soft channels of the DAQ system
        :param daq:             data acquisition object from svpelab library
        :param initial_value:   the dictionnary with the initial values (X, Y and timestamp)
        :param pwr_lvl:     The input power level in p.u.
        :param curve:       The characteristic curve number
        :param x_target:      The target value of X value (e.g. FW -> f_step)
        :param y_target:      The target value of Y value (e.g. LAP -> act_pwrs_limits)
        :param number_of_tr:  1547.1 : Specify two (2) time response in order to validate steady state values

        :return: returns a dictionary with the timestamp, event and total EUT reactive power
        """
        tr_value = collections.OrderedDict()
        x = self.get_x_y_variable('x')
        y = self.get_x_y_variable('y')

        first_tr = initial_value['timestamp'] + timedelta(seconds=tr)
        tr_list = [first_tr]
        for i in range(number_of_tr - 1):
            tr_list.append(tr_list[i] + timedelta(seconds=tr))
        tr_iter = 1
        for tr_ in tr_list:
            now = datetime.now()
            if now <= tr_:
                time_to_sleep = tr_ - datetime.now()
                self.ts.sleep(time_to_sleep.total_seconds())
            data = daq.data_capture_read()
            self.update_target_value(daq=daq,
                                     pwr_lvl=pwr_lvl,
                                     curve=curve,
                                     x_target=x_target,
                                     y_target=y_target,
                                     step=step,
                                     data=data)

            tr_value[tr_iter] = {}
            if x is not None:
                if isinstance(x, list):
                    for xs in x:
                        tr_value[tr_iter][xs] = {
                            'x_value': self.get_measurement_total(data=data, type_meas=xs, log=False)}
                        daq.sc['%s_MEAS' % xs] = tr_value[tr_iter][xs]['x_value']

                else:
                    tr_value[tr_iter][x] = {'x_value': self.get_measurement_total(data=data, type_meas=x, log=False)}
                    daq.sc['%s_MEAS' % x] = tr_value[tr_iter][x]['x_value']
                    if self.get_test_name() == LAP:
                        self.ts.log(tr_value)
                        tr_value[tr_iter]['V_MEAS'] = self.get_measurement_total(data=data, type_meas='V', log=False)
                        daq.sc['V_MEAS'] = tr_value[tr_iter]['V_MEAS']
                        tr_value[tr_iter]['F_MEAS'] = self.get_measurement_total(data=data, type_meas='F', log=False)
                        daq.sc['F_MEAS'] = tr_value[tr_iter]['F_MEAS']
                        tr_value[tr_iter]['P_MEAS'] = self.get_measurement_total(data=data, type_meas='P', log=False)
                        daq.sc['P_MEAS'] = tr_value[tr_iter]['P_MEAS']
            if y is not None:
                if isinstance(y, list):
                    for ys in y:
                        tr_value[tr_iter][ys] = {
                            'y_value': self.get_measurement_total(data=data, type_meas=ys, log=False)}
                        daq.sc['%s_MEAS' % ys] = tr_value[tr_iter][ys]['y_value']
                else:
                    tr_value[tr_iter][y] = {'y_value': self.get_measurement_total(data=data, type_meas=y, log=False)}
                    daq.sc['%s_MEAS' % y] = tr_value[tr_iter][y]['y_value']
            daq.sc['event'] = "{0}_TR_{1}".format(step, tr_iter)
            # TODO : If multiple target this need to be change to a list or handle multiple Xs target

            tr_value[tr_iter]['%s_TARGET' % y] = daq.sc['%s_TARGET' % y]
            tr_value[tr_iter]["timestamp"] = tr_
            tr_value[tr_iter]['%s_TARGET_MIN' % y] = daq.sc['%s_TARGET_MIN' % y]
            tr_value[tr_iter]['%s_TARGET_MAX' % y] = daq.sc['%s_TARGET_MAX' % y]

            tr_iter = tr_iter + 1
            daq.data_sample()

        return tr_value

        # except Exception as e:
        #    raise p1547Error('Error in get_tr_data(): %s' % (str(e)))

    def get_analysis(self, initial_value, tr_values):
        """
        This functions get the analysis results from three pass-fail criteria.

        :param initial_value:   A dictionary with measurements before a step
        :param tr_values:       A dictionary with measurements after one time response cycle
        :return: returns a dictionary with pass fail criteria that will be use in the
        result_summary.csv file.
        """
        analysis = {}
        x = self.get_x_y_variable('x')
        y = self.get_x_y_variable('y')
        analysis['%s_INITIAL' % y] = initial_value[y]['y_value']
        for tr_iter, tr_value in tr_values.items():
            analysis['%s_TR_%s' % (y, tr_iter)] = tr_value[y]['y_value']
            analysis['%s_TR_%s' % (x, tr_iter)] = tr_value[x]['x_value']
            analysis['%s_TR_%s_MIN' % (y, tr_iter)] = tr_value['%s_TARGET_MIN' % y]
            analysis['%s_TR_%s_MAX' % (y, tr_iter)] = tr_value['%s_TARGET_MAX' % y]
            analysis['%s_TR_TARG_%s' % (y, tr_iter)] = tr_value['%s_TARGET' % y]
            if self.get_test_name() == LAP:
                analysis['P_MEAS_%s' % tr_iter] = tr_value['P_MEAS']
                analysis['V_MEAS_%s' % tr_iter] = tr_value['V_MEAS']
                analysis['F_MEAS_%s' % tr_iter] = tr_value['F_MEAS']

        last_tr_value = tr_values[next(reversed(tr_values.keys()))]
        tr_diff = last_tr_value[y]['y_value'] - analysis['%s_INITIAL' % y]
        p_tr_target = ((0.9 * tr_diff) + analysis['%s_INITIAL' % y])

        if tr_diff < 0:
            if analysis['%s_TR_1' % y] <= p_tr_target:
                analysis['TR_90_%_PF'] = 'Pass'
            else:
                analysis['TR_90_%_PF'] = 'Fail'
        elif tr_diff >= 0:
            if analysis['%s_TR_1' % y] >= p_tr_target:
                analysis['TR_90_%_PF'] = 'Pass'
            else:
                analysis['TR'] = 'Fail'

        if tr_1_data['%s_TARGET_MIN' % y] <= analysis['%s_TR_1' % y] <= tr_1_data['%s_TARGET_MAX' % y]:
            analysis['%s_TR' % y] = 'Pass'
        else:
            analysis['%s_TR' % y] = 'Fail'

        self.ts.log('        %s(Tr_1) evaluation: %0.1f <= %0.1f <= %0.1f  [%s]' % (y,
                                                                                    tr_1_data['%s_TARGET_MIN' % y],
                                                                                    analysis['%s_TR_1' % y],
                                                                                    tr_1_data['%s_TARGET_MAX' % y],
                                                                                    analysis['%s_TR' % y]))

        if tr_4_data['%s_TARGET_MIN' % y] <= analysis['%s_FINAL' % y] <= tr_4_data['%s_TARGET_MAX' % y]:
            analysis['%s_FINAL_TR' % y] = 'Pass'
        else:
            analysis['%s_FINAL_TR' % y] = 'Fail'

        self.ts.log('        %s(Tr_4) evaluation: %0.1f <= %0.1f <= %0.1f  [%s]' % (y,
                                                                                    tr_4_data['%s_TARGET_MIN' % y],
                                                                                    analysis['%s_FINAL' % y],
                                                                                    tr_4_data['%s_TARGET_MAX' % y],
                                                                                    analysis['%s_FINAL_TR' % y]))

        analysis['%s_TARGET' % y] = tr_4_data['%s_TARGET' % y]
        analysis['%s_TARGET_MIN' % y] = tr_4_data['%s_TARGET_MIN' % y]
        analysis['%s_TARGET_MAX' % y] = tr_4_data['%s_TARGET_MAX' % y]

        if x is not None:
            analysis['%s_MEAS' % x] = tr_4_data['%s' % x]
        analysis['%s_MEAS' % y] = tr_4_data['%s' % y]
        """
        The variable y_tr is the value use to verify the time response requirement.
        |----------|----------|----------|----------|
                   1st tr     2nd tr     3rd tr     4th tr            
        |          |                                |
        y_initial  y_tr                             y_final_tr    

        (1547.1)After each step, the open loop response time, Tr , is evaluated. 
        The expected output, Y (T r ), at one times the open loop response time,
        is calculated as 90% x (Y_final_tr - Y_initial ) + Y_initial
        """

        self.ts.log('        %s_TR [%s], TR [%s], %s_FINAL [%s]' % (y, analysis['%s_TR' % y],
                                                                    analysis['TR'],
                                                                    y, analysis['%s_FINAL_TR' % y]))
        return analysis

    def get_x_y_variable(self, letter):
                analysis['TR_90_%_PF'] = 'Fail'
        """
              The variable y_tr is the value use to verify the time response requirement.
              |----------|----------|----------|----------|
                         1st tr     2nd tr     3rd tr     4th tr            
              |          |          |
              y_initial  y_tr       y_final_tr    

              (1547.1)After each step, the open loop response time, Tr , is evaluated. 
              The expected output, Y (T r ), at one times the open loop response time,
              is calculated as 90% x (Y_final_tr - Y_initial ) + Y_initial
        """
        for tr_iter, tr_dic in tr_values.items():
            if analysis['%s_TR_%s_MIN' % (y, tr_iter)] <= analysis['%s_TR_%s' % (y, tr_iter)] <= analysis[
                '%s_TR_%s_MAX' % (y, tr_iter)]:
                analysis['%s_TR_%s_PF' % (y, tr_iter)] = 'Pass'
            else:
                analysis['%s_TR_%s_PF' % (y, tr_iter)] = 'Fail'

            self.ts.log('        %s(Tr_%s) evaluation: %0.1f <= %0.1f <= %0.1f  [%s]' % (y,
                                                                                         tr_iter,
                                                                                         analysis['%s_TR_%s_MIN' % (
                                                                                         y, tr_iter)],
                                                                                         analysis[
                                                                                             '%s_TR_%s' % (y, tr_iter)],
                                                                                         analysis['%s_TR_%s_MAX' % (
                                                                                         y, tr_iter)],
                                                                                         analysis['%s_TR_%s_PF' % (
                                                                                         y, tr_iter)]))

        analysis['FIRST_ITER'] = next(iter(tr_values.keys()))
        analysis['LAST_ITER'] = tr_iter
        return analysis

    def get_params(self, curve):
        return self.param[curve]

    def get_rslt_param_plot(self):

        y = self.get_x_y_variable('y')
        y2 = self.get_x_y_variable('x')
        y_title = None
        y2_title = None

        # For VV, VW and FW
        if y == 'Q':
            y_title = 'Reactive Power (Var)'
        elif y == 'P':
            y_title = 'Active Power (W)'

        if y2 == 'V':
            y2_title = 'Voltage (V)'
        elif y2 == 'F':
            y2_title = 'Frequency (Hz)'
        elif y2 == 'P':
            y2_title = 'Active Power (W)'

        y_points = '%s_TARGET,%s_MEAS' % (y, y)
        y2_points = '%s_TARGET,%s_MEAS' % (y2, y2)

        # For CPF
        if self.script_name == 'CPF':
            y_points = '{}, PF_TARGET'.format(','.join(str(x) for x in self.get_measurement_label('PF')))
            y_title = 'Power Factor'
            y2_points = '{}'.format(','.join(str(x) for x in self.get_measurement_label('I')))
            y2_title = 'Current (A)'
        elif self.script_name == 'LAP':
            y_points = '{}'.format(','.join(str(x) for x in self.get_measurement_label('F')))
            y_title = 'Frequency (Hz)'
            y2_points = '{}'.format(','.join(str(x) for x in self.get_measurement_label('P')))
            y2_title = 'Active Power (W)'

        result_params = {
            'plot.title': 'title_name',
            'plot.x.title': 'Time (sec)',
            'plot.x.points': 'TIME',
            'plot.y.points': y_points,
            'plot.y.title': y_title,
            'plot.y2.points': y2_points,
            'plot.y2.title': y2_title,
            'plot.%s_TARGET.min_error' % y: '%s_TARGET_MIN' % y,
            'plot.%s_TARGET.max_error' % y: '%s_TARGET_MAX' % y
        }

        return result_params

    def get_targ(self, value, pwr_lvl, curve=None, pf=None, variable=None):
        if curve is None:
            curve = 1
        p_targ = None
        if self.script_name == FW or variable == "F":
            f_dob = self.f_nom + self.param[curve]['dbf']
            f_dub = self.f_nom - self.param[curve]['dbf']
            p_db = self.p_rated * pwr_lvl
            p_avl = self.p_rated * (1.0 - pwr_lvl)
            if f_dub <= value <= f_dob:
                p_targ = p_db
            elif value > f_dob:
                p_targ = p_db - ((value - f_dob) / (self.f_nom * self.param[curve]['kof'])) * p_db
                if p_targ < self.p_min:
                    p_targ = self.p_min
            elif value < f_dub:
                p_targ = ((f_dub - value) / (self.f_nom * self.param[curve]['kof'])) * p_avl + p_db
                if p_targ > self.p_rated:
                    p_targ = self.p_rated
            p_targ *= pwr_lvl
            return p_targ

        elif self.script_name == VV:
            if value <= self.param[curve]['V1']:
                q_value = self.param[curve]['Q1']
            elif value < self.param[curve]['V2']:
                q_value = self.param[curve]['Q1'] + (
                        (self.param[curve]['Q2'] - self.param[curve]['Q1']) /
                        (self.param[curve]['V2'] - self.param[curve]['V1']) * (value - self.param[curve]['V1']))
            elif value == self.param[curve]['V2']:
                q_value = self.param[curve]['Q2']
            elif value <= self.param[curve]['V3']:
                q_value = self.param[curve]['Q3']
            elif value < self.param[curve]['V4']:
                q_value = self.param[curve]['Q3'] + (
                        (self.param[curve]['Q4'] - self.param[curve]['Q3']) /
                        (self.param[curve]['V4'] - self.param[curve]['V3']) * (value - self.param[curve]['V3']))
            else:
                q_value = self.param[curve]['Q4']
            q_value *= pwr_lvl
            return round(q_value, 1)

        elif self.script_name == CPF:
            q_value = math.sqrt(pow(value, 2) * ((1 / pow(pf, 2)) - 1))
            return round(q_value, 1)

        elif self.script_name == VW or variable == "V":
            self.ts.log(self.param)

            if value <= self.param[curve]['V1']:
                p_targ = self.param[curve]['P1']
            elif value < self.param[curve]['V2']:
                p_targ = self.param[curve]['P1'] + (
                        (self.param[curve]['P2'] - self.param[curve]['P1']) /
                        (self.param[curve]['V2'] - self.param[curve]['V1']) *
                        (value - self.param[curve]['V1']))
            else:
                p_targ = self.param[curve]['P2']

            p_targ *= pwr_lvl
            return p_targ

        elif self.script_name == "WV":
            if value == self.param[curve]['P0']:
                q_value = self.param[curve]['Q0']
                self.ts.log_debug('P0 TARGET')
            elif value < self.param[curve]['P1']:
                q_value = self.param[curve]['Q1']
                self.ts.log_debug('P1 TARGET')
            elif value <= self.param[curve]['P2']:
                self.ts.log_debug('P2 TARGET')
                q_value = self.param[curve]['Q1'] + (
                        (self.param[curve]['Q2'] - self.param[curve]['Q1']) /
                        (self.param[curve]['P2'] - self.param[curve]['P1']) * (value - self.param[curve]['P1']))
            elif value < self.param[curve]['P3']:
                self.ts.log_debug('P3 TARGET')
                q_value = self.param[curve]['Q2'] + (
                        (self.param[curve]['Q3'] - self.param[curve]['Q2']) /
                        (self.param[curve]['P3'] - self.param[curve]['P2']) * (value - self.param[curve]['P2']))
            else:
                self.ts.log_debug('P3 FINAL TARGET')
                q_value = self.param[curve]['Q3']
            q_value *= pwr_lvl
            return q_value


    """
    Passfail functions
    """
    # STD_CHANGE: Analysis of X(Tr) value is not relevant when x_initial is really close to x_final
    def criteria(self, daq, tr, step, initial_value, curve=None, pwr_lvl=1.0, target=None, mode=None):
        """
        Determine the passfail criteria of any test based on the parameter target

        :param target:  float
        The parameter target (PF_TARGET, V_TARGET or F_TARGET)

        :param daq:     DAS object
        data acquisition object in order to manipulated

        :param tr:      float
        The response time (s) of the tested function

        :param step:    string
        The test procedure step letter or number (e.g "Step G" )

        :param initial_value:   dictionary
        This is a dictionary with two important key : 'timestamp' and 'value' before a step

        :param pwr_lvl:   float
        The power level of test to be reflected in interpolation

        :return y_x_analysis:    dictionary
        y_x_analysis that contains passfail of response time requirements ( y_x_analysis[y_tr_passfail_label])
        and test result accuracy requirements ( y_x_analysis[y_final_passfail_label] )
        """
        #try:
        first_tr = initial_value['timestamp'] + timedelta(seconds=tr)
        four_times_tr = initial_value['timestamp'] + timedelta(seconds=4 * tr)
        now = datetime.now()
        if now <= first_tr:
            time_to_sleep = first_tr - datetime.now()
            self.ts.sleep(time_to_sleep.total_seconds())

        tr_1_data = self.get_tr_data(daq, step, tr=1, pwr_lvl=pwr_lvl, curve=curve, target=target)

        if now <= four_times_tr:
            time_to_sleep = four_times_tr - datetime.now()
            self.ts.sleep(time_to_sleep.total_seconds())

        tr_4_data = self.get_tr_data(daq, step, tr=4, pwr_lvl=pwr_lvl, curve=curve, target=target)

        analysis = self.get_analysis(initial_value, tr_1_data, tr_4_data)
        return analysis

        #except Exception as e:

        #   raise p1547Error('Error in criteria(): %s' % (str(e)))

    def process_data(self, daq, tr, step, initial_value, result_summary, filename, \
                     pwr_lvl=None, curve=None, x_target=None, y_target=None):
        self.set_params()
        tr_values = self.get_tr_value(daq=daq,
                                      initial_value=initial_value,
                                      tr=tr,
                                      step=step,
                                      curve=curve,
                                      pwr_lvl=pwr_lvl,
                                      x_target=x_target,
                                      y_target=y_target)
        analysis = self.get_analysis(initial_value=initial_value,
                                     tr_values=tr_values)
        self.ts.log('%s' % (analysis))
        result_summary.write(self.write_rslt_sum(analysis=analysis,
                                                 step=step,
                                                 filename=filename))
        return


if __name__ == "__main__":
    pass
