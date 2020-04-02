"""
Copyright (c) 2017, Sandia National Labs, SunSpec Alliance and CanmetENERGY
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
# import sys
# import os
# import glob
# import importlib

VERSION = '1.3.0'
LATEST_MODIFICATION = '4th March 2020'

FW = 'FW'  # Frequency-Watt
CPF = 'CPF'  # Constant Power Factor
VW = 'VW'  # Volt_Watt
VV = 'VV'  # Volt-Var
WV = 'WV'  # Watt-Var
CRP = 'CRP'  # Constant Reactive Power
LAP = 'LAP'  # Limit Active Power
PRI = 'PRI'  # Priority

VOLTAGE = 'V'
FREQUENCY = 'F'
FULL_NAME = {'V': 'Voltage',
             'P': 'Active Power',
             'Q': 'Reactive Power',
             'F': 'Frequency',
             'PF': 'Power Factor'}


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
        self.function_used = []
        self.rslt_sum_col_name = ''
        self.sc_points = {}
        self.pairs = {}
        self.mag = {}
        self.ang = {}
        self.param = {FW: {}, CPF: {}, VW: {}, VV: {}, WV: {}, CRP: {}, PRI: {}}
        self.target_dict = []
        self.x_criteria = None
        self.y_criteria = None
        self.step_label = None
        self.double_letter_label = False
        self.criteria_mode = []
        self.meas_values = []
        self.curve = 1

        """
        According to Table 3-Minimum requirements for manufacturers stated measured and calculated accuracy
        """
        try:
            self.v_nom = ts.param_value('eut.v_nom')
            self.MSA_V = 0.01 * self.v_nom
            self.MSA_Q = 0.05 * ts.param_value('eut.s_rated')
            self.MSA_P = 0.05 * ts.param_value('eut.s_rated')
            self.MSA_F = 0.01
            self.f_nom = ts.param_value('eut.f_nom')
            self.phases = ts.param_value('eut.phases')
            self.p_rated = ts.param_value('eut.p_rated')
            self.p_rated_prime = ts.param_value('eut.p_rated_prime')  # absorption power
            if self.p_rated_prime is None:
                self.p_rated_prime = -self.p_rated
            self.p_min = ts.param_value('eut.p_min')
            self.var_rated = ts.param_value('eut.var_rated')
            self.s_rated = ts.param_value('eut.s_rated')
            self.imbalance_angle_fix = imbalance_angle_fix
            self.absorb = absorb

        except Exception as e:
            self.ts.log_error('Incorrect Parameter value : %s' % e)
            raise

        self._config()

    def _config(self):
        # Set Complete test name
        self.set_complete_test_name()
        # Set measurement variables
        self.set_meas_variable()
        # Set functions to be used with scripts
        self.set_functions()
        # Create the pairs need
        self.set_params()
        # Configure test for imblance operation
        self.set_imbalance_config()
        # Configure the x and y variable for criteria
        self.set_x_y_variable()
        # Set Sc points
        self.set_sc_points()
        # Configuring the criteria that the function need to assess
        self.set_criteria_mode()
        # Set the result summary column names
        self.set_result_summary_col_name()

    """
    Setter functions
    """
    def set_meas_variable(self):
        """
        Sets initial measurement variable taken from DAQ
        :return:
        """
        self.meas_values = ['V', 'P']

        if self.script_name == FW:
            self.meas_values.remove('V')
        if self.script_name == PRI or self.script_name == LAP or self.script_name == FW:
            self.meas_values.insert(1, 'F')
        if self.script_name is not LAP and self.script_name is not FW:
            self.meas_values.append('Q')
        if self.script_name == CPF or self.script_name == CRP:
            self.meas_values.append('PF')

        self.ts.log('measured values variables to be initialized: %s' % self.meas_values)

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
        Write column names for results file depending on which measured variables initialized and targets
        :param nothing:
        :return: nothing
        """

        xs = self.x_criteria
        ys = self.y_criteria
        row_data = []

        # Time response criteria will take last placed value of Y variables
        if self.criteria_mode[0]:
            row_data.append('%s_TR_ACC_REQ' % ys[-1])
            row_data.append('TR_REQ')
            row_data.append('%s_FINAL_ACC_REQ' % ys[-1])

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

        self.rslt_sum_col_name = ','.join(row_data)+'\n'

    def set_sc_points(self):
        """
        Set SC points for DAS depending on which measured variables initialized and targets
        :param nothing:
        :return: nothing
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

    def set_functions(self):
        """
        Configure which functions should be started per test script name as some scripts might need more AIF functions
        :param nothing:
        :return: nothing
        """
        if self.script_name == LAP:
            self.function_used = [VW, FW]

        elif self.script_name == PRI:
            self.function_used = [VW, VV, FW, CPF, CRP, WV, PRI]

        elif self.script_name == VV:
            self.function_used = [VV]

        elif self.script_name == VW:
            self.function_used = [VW]

        elif self.script_name == FW:
            self.function_used = [FW]

        elif self.script_name == CPF:
            self.function_used = [CPF]

        elif self.script_name == CRP:
            self.function_used = [CRP]

        elif self.script_name == WV:
            self.function_used = [WV]

    def set_criteria_mode(self):
        """
        This functions set the criteria mode required for different functions.
        :return: returns a list with the activated mode
        [0] Open Loop Time Response (OLTR) (90% of (y_final-y_intiial) + y_initial),
        [1] Test Results Accuracy on TR 'y' value (TRATR) and
        [2] Test Results Accuracy on final (TRAF) 'y' value.
        """
        if self.script_name == FW or self.script_name == VW or self.script_name == VV \
                or self.script_name == CPF or self.script_name == LAP or self.script_name == WV:
            self.criteria_mode = [True, True, True]

        elif self.script_name == CRP:
            self.criteria_mode = [True, True, True]

        elif self.script_name == PRI:
            self.criteria_mode = [False, False, True]

    def set_params(self, curve=1):
        """
        Configure the parameter specific to the AIF
        :param curve: curve number from 1547.1
        :return: nothing
        """

        if VW in self.function_used:
            if curve == 1:
                self.param[VW][curve] = {
                    'V1': round(1.06 * self.v_nom, 2),
                    'V2': round(1.10 * self.v_nom, 2),
                    'P1': round(self.p_rated, 2)
                }

            elif curve == 2:
                self.param[VW][curve] = {
                    'V1': round(1.05 * self.v_nom, 2),
                    'V2': round(1.10 * self.v_nom, 2),
                    'P1': round(self.p_rated, 2)
                }

            elif curve == 3:
                self.param[VW][curve] = {
                    'V1': round(1.09 * self.v_nom, 2),
                    'V2': round(1.10 * self.v_nom, 2),
                    'P1': round(self.p_rated, 2)
                }

            if self.p_min > (0.2 * self.p_rated):
                self.param[VW][curve]['P2'] = int(0.2 * self.p_rated)
            elif self.absorb == 'Yes':
                if curve == 1:
                    self.param[VW][curve]['P2'] = 0
                elif curve == 2:
                    self.param[VW][curve]['P2'] = self.p_rated_prime
            else:
                self.param[VW][curve]['P2'] = int(self.p_min)

            self.ts.log_debug('VW settings: %s' % self.param[VW])

        # if self.script_name == FW or (self.script_name == LAP and self.x_criteria == 'F' ):
        if FW in self.function_used:
            p_small = self.ts.param_value('eut_fw.p_small')
            if p_small is None:
                p_small = 0.05
            if curve == 1:
                self.param[FW][curve] = {
                    'dbf': 0.036,
                    'kof': 0.05,
                    'tr': self.ts.param_value('fw.test_1_tr'),
                    'f_small': p_small * self.f_nom * 0.05
                }
            elif curve == 2:
                self.param[FW][curve] = {
                    'dbf': 0.017,
                    'kof': 0.03,
                    'tr': self.ts.param_value('fw.test_2_tr'),
                    'f_small': p_small * self.f_nom * 0.02
                }

            self.ts.log_debug('FW settings: %s' % self.param[FW])

        # elif self.script_name == VV:
        if VV in self.function_used:
            if curve == 1:
                self.param[VV][curve] = {
                    'V1': round(0.92 * self.v_nom, 2),
                    'V2': round(0.98 * self.v_nom, 2),
                    'V3': round(1.02 * self.v_nom, 2),
                    'V4': round(1.08 * self.v_nom, 2),
                    'Q1': round(self.s_rated * 0.44, 2),
                    'Q2': round(self.s_rated * 0.0, 2),
                    'Q3': round(self.s_rated * 0.0, 2),
                    'Q4': round(self.s_rated * -0.44, 2)
                }
            elif curve == 2:
                self.param[VV][curve] = {
                    'V1': round(0.88 * self.v_nom, 2),
                    'V2': round(1.04 * self.v_nom, 2),
                    'V3': round(1.07 * self.v_nom, 2),
                    'V4': round(1.10 * self.v_nom, 2),
                    'Q1': round(self.var_rated * 1.0, 2),
                    'Q2': round(self.var_rated * 0.5, 2),
                    'Q3': round(self.var_rated * 0.5, 2),
                    'Q4': round(self.var_rated * -1.0, 2)
                }
            elif curve == 3:
                self.param[VV][curve] = {
                    'V1': round(0.90 * self.v_nom, 2),
                    'V2': round(0.93 * self.v_nom, 2),
                    'V3': round(0.96 * self.v_nom, 2),
                    'V4': round(1.10 * self.v_nom, 2),
                    'Q1': round(self.var_rated * 1.0, 2),
                    'Q2': round(self.var_rated * -0.5, 2),
                    'Q3': round(self.var_rated * -0.5, 2),
                    'Q4': round(self.var_rated * -1.0, 2)
                }

            self.ts.log_debug('VV settings: %s' % self.param[VV])

        if WV in self.function_used:
            if self.p_min > 0.2 * self.p_rated:
                p = self.p_min
                self.ts.log('P1 power is set using p_min')
            else:
                p = 0.2 * self.p_rated
                self.ts.log('P1 power is set using 20% p_rated')

            # Added another Q(P) points since EUT looks to be asking for 4 pts
            if curve == 1:
                self.param[WV][curve] = {
                    'P0': 0,
                    'P1': round(p, 2),
                    'P2': round(0.5 * self.p_rated, 2),
                    'P3': round(1.0 * self.p_rated, 2),
                    'Q0': round(self.s_rated * 0.0, 2),
                    'Q1': round(self.s_rated * 0.0, 2),
                    'Q2': round(self.s_rated * 0.0, 2),
                    'Q3': round(self.s_rated * -0.44, 2)
                }
                if self.absorb is "Yes":
                    self.ts.log('Adding EUT Absorption Points (P1_prime-P3_prime, Q1_prime-Q3_prime)')
                    self.param[WV][curve]['P1_prime'] = round(-p, 2)
                    self.param[WV][curve]['P2_prime'] = round(0.5 * self.p_rated_prime, 2)
                    self.param[WV][curve]['P3_prime'] = round(1.0 * self.p_rated_prime, 2)
                    self.param[WV][curve]['Q1_prime'] = 0
                    self.param[WV][curve]['Q2_prime'] = 0
                    self.param[WV][curve]['Q3_prime'] = round(0.44 * self.s_rated, 2)

            elif curve == 2:
                self.param[WV][curve] = {
                    'P0': 0,
                    'P1': round(p, 2),
                    'P2': round(0.5 * self.p_rated, 2),
                    'P3': round(1.0 * self.p_rated, 2),
                    'Q0': round(self.s_rated * 0.0, 2),
                    'Q1': round(self.s_rated * -0.22, 2),
                    'Q2': round(self.s_rated * -0.22, 2),
                    'Q3': round(self.s_rated * -0.44, 2)
                }
                if self.absorb is "Yes":
                    self.ts.log('Adding EUT Absorption Points (P1_prime-P3_prime, Q1_prime-Q3_prime)')
                    self.param[WV][curve]['P1_prime'] = round(-p, 2)
                    self.param[WV][curve]['P2_prime'] = round(0.5 * self.p_rated_prime, 2)
                    self.param[WV][curve]['P3_prime'] = round(1.0 * self.p_rated_prime, 2)
                    self.param[WV][curve]['Q1_prime'] = round(0.22 * self.s_rated, 2)
                    self.param[WV][curve]['Q2_prime'] = round(0.22 * self.s_rated, 2)
                    self.param[WV][curve]['Q3_prime'] = round(0.44 * self.s_rated, 2)
            elif curve == 3:
                self.param[WV][curve] = {
                    'P0': 0,
                    'P1': round(p, 2),
                    'P2': round(0.5 * self.p_rated, 2),
                    'P3': round(1.0 * self.p_rated, 2),
                    'Q0': round(self.s_rated * 0.0, 2),
                    'Q1': round(self.s_rated * 0.0, 2),
                    'Q2': round(self.s_rated * -0.44, 2),
                    'Q3': round(self.s_rated * -0.44, 2)
                }
                if self.absorb is "Yes":
                    self.ts.log('Adding EUT Absorption Points (P1_prime-P3_prime, Q1_prime-Q3_prime)')
                    self.param[WV][curve]['P1_prime'] = round(-p, 2)
                    self.param[WV][curve]['P2_prime'] = round(0.5 * self.p_rated_prime, 2)
                    self.param[WV][curve]['P3_prime'] = round(1.0 * self.p_rated_prime, 2)
                    self.param[WV][curve]['Q1_prime'] = 0
                    self.param[WV][curve]['Q2_prime'] = round(0.44 * self.s_rated, 2)
                    self.param[WV][curve]['Q3_prime'] = round(0.44 * self.s_rated, 2)
            self.ts.log_debug('WV settings: %s' % self.param[WV])

        if PRI in self.function_used:
            p_rated = self.p_rated
            q_rated = self.var_rated
            self.target_dict = \
                [
                    {'P': 0.5 * p_rated, VV: 0.00 * q_rated, CRP: 0.44 * q_rated, CPF: 0.9 * q_rated, WV: 0},
                    {'P': 0.4 * p_rated, VV: -0.44 * q_rated, CRP: 0.44 * q_rated, CPF: 0.9 * q_rated, WV: 0},
                    {'P': 0.3 * p_rated, VV: -0.44 * q_rated, CRP: 0.44 * q_rated, CPF: 0.9 * q_rated, WV: 0},
                    {'P': 0.4 * p_rated, VV: -0.44 * q_rated, CRP: 0.44 * q_rated, CPF: 0.9 * q_rated, WV: 0},
                    {'P': 0.4 * p_rated, VV: -0.44 * q_rated, CRP: 0.44 * q_rated, CPF: 0.9 * q_rated, WV: 0},
                    {'P': 0.6 * p_rated, VV: 0.00 * q_rated, CRP: 0.44 * q_rated, CPF: 0.9 * q_rated, WV: 0.05 * q_rated},
                    {'P': 0.5 * p_rated, VV: 0.00 * q_rated, CRP: 0.44 * q_rated, CPF: 0.9 * q_rated, WV: 0},
                    {'P': 0.7 * p_rated, VV: 0.00 * q_rated, CRP: 0.44 * q_rated, CPF: 0.9 * q_rated, WV: 0.10 * q_rated}
                ]
            self.param[PRI] = self.target_dict

    def set_grid_asymmetric(self, grid, case):
        """
        Configure the grid simulator to change the magnitude and angles.
        :param grid:   A gridsim object from the svpelab library
        :param case:   string (case_a or case_b)
        :return: nothing
        """
        try:
            self.ts.log('Setting grid to magnitude: %s and angles: %s' % (self.mag[case], self.ang[case]))
            if grid is not None:
                grid.config_asymmetric_phase_angles(mag=self.mag[case], angle=self.ang[case])
        except Exception as e:
            self.ts.log_error('Invalid case option: %s. Please choose correct value' % e)
            raise

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
        :param x:   A list of string that includes all variables that has a target such as V, F, P...
        :param y:   A list of string that includes all variables that has a passfail criteria with min-max
        :param step:   The step of the test since now it change sometimes during the test
        :return: Nothing
        """
        #self.ts.log_debug("Set_x_y_variables: %s" % step)
        if self.script_name == VW or self.script_name == FW or self.script_name == LAP:
            self.y_criteria = ['P']
            if self.script_name == VW:
                self.x_criteria = ['V']
            elif self.script_name == FW:
                self.x_criteria = ['F']
            elif self.script_name == LAP:
                self.x_criteria = ['F', 'V']
            '''
            elif self.script_name == LAP and step is not None:
                if step == "Step C" or "Step D" in step or "Step E" in step:
                    self.x_criteria = ['F']
                elif "Step F" in step:
                    self.x_criteria = ['V']
                else:
                    self.x_criteria = "None"
            '''
        elif self.script_name == CPF or self.script_name == VV or self.script_name == WV or self.script_name == CRP:
            self.y_criteria = ['Q']
            if self.script_name == VV:
                self.x_criteria = ['V']
            elif self.script_name == CRP:
                self.x_criteria = ['V', 'P']
            elif self.script_name == CPF:
                self.x_criteria = ['V', 'P', 'PF']
            elif self.script_name == "WV":
                self.x_criteria = ['P']
        elif self.script_name == PRI:
            self.y_criteria = ['P', 'Q']
            self.x_criteria = ['V', 'F']

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

    def write_rslt_sum(self, analysis, step, filename):
        """
        Combines the analysis results, the step label and the filenamoe to return
        a row that will go in result_summary.csv
        :param analysis: Dictionary with all the information for result summary
        :param step:   test procedure step letter or number (e.g "Step G")
        :param filename: the dataset filename use for analysis
        :return: row_data a string with all the information for result_summary.csv
        """

        try:

            xs = self.x_criteria
            ys = self.y_criteria
            first_iter = analysis['FIRST_ITER']
            last_iter = analysis['LAST_ITER']
            row_data = []

            # Time response criteria will take last placed value of Y variables
            if self.criteria_mode[0]:
                row_data.append(str(analysis['%s_TR_%s_PF' % (ys[-1], first_iter)]))
                row_data.append(str(analysis['TR_90_%_PF']))
                row_data.append(str(analysis['%s_TR_%s_PF' % (ys[-1], last_iter)]))

            # Default measured values are V,P and Q (F can be added) refer to set_meas_variable function
            for meas_value in self.meas_values:
                row_data.append(str(analysis['%s_TR_%d' % (meas_value, last_iter)]))
                # Variables needed for variations
                if meas_value in xs:
                    row_data.append(str(analysis['%s_TR_TARG_%d' % (meas_value, last_iter)]))
                # Variables needed for criteria verifications with min max passfail
                if meas_value in ys:
                    row_data.append(str(analysis['%s_TR_TARG_%s' % (meas_value, last_iter)]))
                    row_data.append(str(analysis['%s_TR_%s_MIN' % (meas_value, last_iter)]))
                    row_data.append(str(analysis['%s_TR_%s_MAX' % (meas_value, last_iter)]))

            row_data.append(step)
            row_data.append(str(filename))
            row_data_str = ','.join(row_data)+'\n'

            return row_data_str

        except Exception as e:
            raise p1547Error('Error in write_rslt_sum() : %s' % (str(e)))

    """
    Getter functions
    """

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
        if type_meas == 'V' or type_meas == 'PF':
            # average value of V or PF
            value = value / nb_phases

        elif type_meas == 'F':
            # No need to do data average for frequency
            value = data.get(self.get_measurement_label(type_meas)[0])

        elif type_meas == 'P':
            # TODO need to handle energy storage systems that will have negative power values
            value = abs(value)
        elif type_meas == 'Q':
            # TODO need to handle energy storage systems that will have negative power values
            value = abs(value)

        return round(value, 3)

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
        daq.data_sample()
        data = daq.data_capture_read()

        daq.sc['event'] = step
        for meas_value in self.meas_values:
            initial['%s_MEAS' % meas_value] = self.get_measurement_total(
                data=data,
                type_meas=meas_value,
                log=False
            )
            daq.sc['%s_MEAS' % meas_value] = initial['%s_MEAS' % meas_value]

        daq.data_sample()

        return initial

    def update_target_value(self, daq, pwr_lvl=1.0, curve=1, x_target=None, y_target=None, data=None, aif=None):
        """
        Function to update target value depending on script name
        :param daq:         (object) data acquisition object from svpelab library
        :param pwr_lvl:     (float) Multiplier value for different power level of test
        :param curve:       (int) By default, curve=1 but can be changed for another curve depending on script
        :param x_target:    (dictionary) This should include the variable that is causing the variation with
                            key as type of value
        :param y_target:    (dictionary) This should be a dictionary of target value for the desired variable
                            (P or/and Q)
        :param data:        (object) This should be included if we need measured value to use with function
                            total_measurement()
        :param aif:
        :return:
        """

        # TODO : This is returning the MIN and Max but not the target value

        if isinstance(x_target, dict):
            for x_meas_variable, x_meas_value in x_target.iteritems():
                daq.sc['%s_TARGET' % x_meas_variable] = x_meas_value

        if isinstance(y_target, dict):
            for y_meas_variable, y_meas_value in y_target.iteritems():
                daq.sc['%s_TARGET' % y_meas_variable] = y_meas_value
                if y_meas_variable == 'P':
                    msa = self.MSA_P
                elif y_meas_variable == 'Q':
                    msa = self.MSA_Q
                else:
                    msa = 0
                if y_meas_value is not None:
                    daq.sc['%s_TARGET_MIN' % y_meas_variable] = y_meas_value - msa * 1.5
                    daq.sc['%s_TARGET_MAX' % y_meas_variable] = y_meas_value + msa * 1.5
        else:
            if self.script_name == VV:
                y = 'Q'
                v_meas = self.get_measurement_total(data=data, type_meas='V', log=False)
                daq.sc['%s_TARGET' % y] = self.get_targ(daq.sc['V_TARGET'])
                daq.sc['%s_TARGET_MIN' % y] = self.get_targ(v_meas + self.MSA_V * 1.5, pwr_lvl, curve)-(self.MSA_Q*1.5)
                daq.sc['%s_TARGET_MAX' % y] = self.get_targ(v_meas - self.MSA_V * 1.5, pwr_lvl, curve)+(self.MSA_Q*1.5)
            elif self.script_name == LAP:
                v_meas = self.get_measurement_total(data=data, type_meas='V', log=False)
                # P target for step F specifically but will be calculated for all of it
                daq.sc['P_TARGET'] = self.get_targ(v_meas)
                # P target min & max for steps D and E
                daq.sc['P_TARGET_MIN'] = self.get_targ(daq.sc['F_MEAS'], variable='F')
                daq.sc['P_TARGET_MAX'] = self.get_targ(daq.sc['F_MEAS'], variable='F')
            elif self.script_name == CPF:
                x = 'Q'
                y = 'P'
                daq.sc['%s_TARGET_MIN' % y] = \
                    self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_P * 1.5, pwr_lvl, pf=x_target['PF']) - 1.5*self.MSA_Q
                daq.sc['%s_TARGET_MAX' % y] = \
                    self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_P * 1.5, pwr_lvl, pf=x_target['PF']) + 1.5*self.MSA_Q
            elif self.script_name == FW:
                x = 'F'
                daq.sc['P_TARGET_MIN'] = \
                    self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_F * 1.5, pwr_lvl, curve) - (self.MSA_P * 1.5)
                daq.sc['P_TARGET_MAX'] = \
                    self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_F * 1.5, pwr_lvl, curve) + (self.MSA_P * 1.5)
            elif self.script_name == VW:
                v_meas = self.get_measurement_total(data=data, type_meas='V', log=False)
                y = 'P'
                daq.sc['%s_TARGET_MIN' % y] = self.get_targ(v_meas + self.MSA_V*1.5, pwr_lvl, curve) - (self.MSA_P*1.5)
                daq.sc['%s_TARGET_MAX' % y] = self.get_targ(v_meas - self.MSA_V*1.5, pwr_lvl, curve) + (self.MSA_P*1.5)
            elif self.script_name == WV:
                y = 'Q'
                x = 'P'
                daq.sc['%s_TARGET_MIN' % y] = \
                    self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_P * 1.5, pwr_lvl, curve) - (self.MSA_Q * 1.5)
                daq.sc['%s_TARGET_MAX' % y] = \
                    self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_P * 1.5, pwr_lvl, curve) + (self.MSA_Q * 1.5)

        daq.data_sample()  # Don't remove

    def get_tr_value(self, daq, initial_value, tr, step, number_of_tr=2, pwr_lvl=1.0, curve=1, x_target=None,
                     y_target=None, aif =None):
        """
        Get the data from a specific time response (tr) corresponding to x and y values returns a dictionary
        but also writes in the soft channels of the DAQ system
        :param daq:             data acquisition object from svpelab library
        :param initial_value:   the dictionary with the initial values (X, Y and timestamp)
        :param pwr_lvl:         The input power level in p.u.
        :param curve:           The characteristic curve number
        :param x_target:        The target value of X value (e.g. FW -> f_step)
        :param y_target:        The target value of Y value (e.g. LAP -> act_pwrs_limits)
        :param number_of_tr:    The number of time responses used to validate the response and steady state values

        :return: returns a dictionary with the timestamp, event and total EUT reactive power
        """

        '''
        For voltage-reactive power, voltage-active power, active power-reactive power, and frequency droop:
        
        Unless otherwise specified in the type tests, the DER performance shall be within 150% of the minimum
        required measurement accuracy (MRA), as specified in Table 3 of IEEE Std 1547-2018 for steady-state
        conditions. For control functions where the DER regulates an output parameter, Y, in response to a 
        measured input parameter, X, the output parameter measured by the test lab, Ymeas, shall meet 2 Equation (1):
        
            Ymin <= Ymeas <= Ymax

        where
            Ymin is Y(Xmeas + 1.5 * MRA(X)) - 1.5 * MRA(Y)
            Ymax is Y(Xmeas - 1.5 * MRA(X)) + 1.5 * MRA(Y)
            Y(X) is a mathematical function defining the target DER output parameter (active or reactive power) in 
            terms of the input (voltage, frequency, or active power)
            Xmeas is the input parameter as measured by the test lab
            MRA(a) is the DER's minimum required steady-state measurement accuracy of a per Table 3 in IEEE Std 
            1547-2018, where a is an input or output parameter under test (voltage, reactive power, active power, 
            or frequency)
        '''

        tr_value = collections.OrderedDict()
        x = self.x_criteria
        y = self.y_criteria

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
            daq.sc['EVENT'] = "{0}_TR_{1}".format(step, tr_iter)

            tr_value[tr_iter] = {}
            for meas_value in self.meas_values:
                try:
                    tr_value[tr_iter]['%s_MEAS' % meas_value] = daq.sc['%s_MEAS' % meas_value]
                    # self.ts.log('Value %s: %s' % (meas_value, daq.sc['%s_MEAS' % meas_value]))
                    if meas_value in x:
                        tr_value[tr_iter]['%s_TARGET' % meas_value] = daq.sc['%s_TARGET' % meas_value]
                        # self.ts.log('X Value (%s) = %s' % (meas_value, daq.sc['%s_MEAS' % meas_value]))
                    elif meas_value in y:
                        tr_value[tr_iter]['%s_TARGET' % meas_value] = daq.sc['%s_TARGET' % meas_value]
                        tr_value[tr_iter]['%s_TARGET_MIN' % meas_value] = daq.sc['%s_TARGET_MIN' % meas_value]
                        tr_value[tr_iter]['%s_TARGET_MAX' % meas_value] = daq.sc['%s_TARGET_MAX' % meas_value]
                        # self.ts.log('Y Value (%s) = %s. Pass/fail bounds = [%s, %s]' %
                        #             (meas_value, daq.sc['%s_MEAS' % meas_value],
                        #              daq.sc['%s_TARGET_MIN' % meas_value], daq.sc['%s_TARGET_MAX' % meas_value]))
                    # self.ts.log_debug('Measured value (%s)' % meas_value)
                except Exception, e:
                    self.ts.log_debug('Measured value (%s) not recorded: %s' % (meas_value, e))

            self.update_target_value(
                daq=daq,
                pwr_lvl=pwr_lvl,
                curve=curve,
                x_target=x_target,
                y_target=y_target,
                data=data#,
                #aif=aif
            )

            tr_value[tr_iter]["timestamp"] = tr_
            tr_iter = tr_iter + 1

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
        xs = self.x_criteria
        ys = self.y_criteria

        if isinstance(ys, list):
            for y in ys:
                analysis['%s_INITIAL' % y] = initial_value['%s_MEAS' % y]
        for tr_iter, tr_value in tr_values.items():
            # self.ts.log_debug('Tr value=%s' % tr_value)
            for meas_value in self.meas_values:
                analysis['%s_TR_%s' % (meas_value, tr_iter)] = tr_value['%s_MEAS' % meas_value]

                if meas_value in xs:
                    analysis['%s_TR_TARG_%s' % (meas_value, tr_iter)] = tr_value['%s_TARGET' % meas_value]

                elif meas_value in ys:
                    if meas_value is not None:
                        analysis['%s_TR_TARG_%s' % (meas_value, tr_iter)] = tr_value['%s_TARGET' % meas_value]
                        analysis['%s_TR_%s_MIN' % (meas_value, tr_iter)] = tr_value['%s_TARGET_MIN' % meas_value]
                        analysis['%s_TR_%s_MAX' % (meas_value, tr_iter)] = tr_value['%s_TARGET_MAX' % meas_value]
                    else:
                        analysis['%s_TR_TARG_%s' % (meas_value, tr_iter)] = None
                        analysis['%s_TR_%s_MIN' % (meas_value, tr_iter)] = None
                        analysis['%s_TR_%s_MAX' % (meas_value, tr_iter)] = None

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
                    # [0] Open Loop Time Response (OLTR) (90% of (y_final-y_intiial) + y_initial),
                    if self.criteria_mode[0]:

                        last_tr_value = tr_values[next(reversed(tr_values.keys()))]
                        # self.ts.log_debug('Last TR value: %s' % last_tr_value)
                        # tr_diff = last_tr_value[ys]['y_value'] - analysis['%s_INITIAL' % ys]
                        tr_diff = last_tr_value['%s_MEAS' % meas_value] - analysis['%s_INITIAL' % meas_value]

                        p_tr_target = ((0.9 * tr_diff) + analysis['%s_INITIAL' % meas_value])

                        if tr_diff < 0:
                            if analysis['%s_TR_1' % meas_value] <= p_tr_target:
                                analysis['TR_90_%_PF'] = 'Pass'
                            else:
                                analysis['TR_90_%_PF'] = 'Fail'
                        elif tr_diff >= 0:
                            if analysis['%s_TR_1' % meas_value] >= p_tr_target:
                                analysis['TR_90_%_PF'] = 'Pass'
                            else:
                                analysis['TR_90_%_PF'] = 'Fail'
                last_tr = tr_iter

        analysis['FIRST_ITER'] = next(iter(tr_values.keys()))
        analysis['LAST_ITER'] = last_tr
        if self.criteria_mode[1] or self.criteria_mode[2]:
            for y in ys:
                for tr_iter, tr_dic in tr_values.items():
                    if (analysis['FIRST_ITER'] == tr_iter and self.criteria_mode[1]) or \
                            (analysis['LAST_ITER'] == tr_iter and self.criteria_mode[2]):
                        if analysis['%s_TR_%s_MIN' % (y, tr_iter)] <= \
                                analysis['%s_TR_%s' % (y, tr_iter)] <= analysis['%s_TR_%s_MAX' % (y, tr_iter)]:
                            analysis['%s_TR_%s_PF' % (y, tr_iter)] = 'Pass'
                        else:
                            analysis['%s_TR_%s_PF' % (y, tr_iter)] = 'Fail'

                        self.ts.log('        %s(Tr_%s) evaluation: %0.1f <= %0.1f <= %0.1f  [%s]' % (
                            y,
                            tr_iter,
                            analysis['%s_TR_%s_MIN' % (y, tr_iter)],
                            analysis['%s_TR_%s' % (y, tr_iter)],
                            analysis['%s_TR_%s_MAX' % (y, tr_iter)],
                            analysis['%s_TR_%s_PF' % (y, tr_iter)]))
        return analysis

    def get_params(self, curve=None, aif=None):
        self.ts.log_debug('Getting params for aif=%s and curve=%s' % (aif, curve))

        # update params if another curve:
        if curve is not None:
            self.set_params(curve=curve)

        # This section is for scripts utilizing multiple AIF, such as prioritization and LAP
        if aif is not None and curve is not None:
            return self.param[aif][curve]
        elif aif is not None:
            return self.param[aif]
        elif curve is not None:
            return self.param[self.script_name][curve]
        else:
            return self.param

    def get_rslt_param_plot(self):

        y_variables = self.y_criteria
        y2_variables = self.x_criteria

        # For VV, VW and FW

        y_points = []
        y2_points = []
        y_title = []
        y2_title = []

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
            'plot.%s_TARGET.min_error' % y2_variables[-1]: '%s_TARGET_MIN' % y2_variables[-1],
            'plot.%s_TARGET.max_error' % y2_variables[-1]: '%s_TARGET_MAX' % y2_variables[-1]
        }

        return result_params

    def get_targ(self, value, pwr_lvl=1.0, curve=1, pf=None, variable=None):
        """
        This functions calculate the target value if there is any special equations to be used with.
        Otherwise, it would be preferred to just enter the target_value while calling process data

        :param value: A dictionary with measurements before a step
        :param pwr_lvl: A dictionary with measurements after one time response cycle
        :return: returns a dictionary with pass fail criteria that will be use in the
        result_summary.csv file.
        """

        # todo: replace all the linear interpolation steps with a numpy or scipy command

        p_targ = None
        if self.script_name == LAP and variable is not 'F':
            p_targ = self.p_rated - (self.p_rated-self.param[VW][curve]['P2'])*((value/self.v_nom)-1.06)/0.04
            return p_targ
        if FW in self.function_used or variable == 'F':
            f_dob = self.f_nom + self.param[FW][curve]['dbf']
            f_dub = self.f_nom - self.param[FW][curve]['dbf']
            p_db = self.p_rated * pwr_lvl
            p_avl = self.p_rated * (1.0 - pwr_lvl)
            if f_dub <= value <= f_dob:
                p_targ = p_db
            elif value > f_dob:
                p_targ = p_db - ((value - f_dob) / (self.f_nom * self.param[FW][curve]['kof'])) * p_db
                if p_targ < self.p_min:
                    p_targ = self.p_min
            elif value < f_dub:
                p_targ = ((f_dub - value) / (self.f_nom * self.param[FW][curve]['kof'])) * p_avl + p_db
                if p_targ > self.p_rated:
                    p_targ = self.p_rated
            p_targ *= pwr_lvl
            return round(p_targ, 2)

        elif VV in self.function_used:
            x = [self.param[VV][curve]['V1'], self.param[VV][curve]['V2'],
                 self.param[VV][curve]['V3'], self.param[VV][curve]['V4']]
            y = [self.param[VV][curve]['Q1'], self.param[VV][curve]['Q2'],
                 self.param[VV][curve]['Q3'], self.param[VV][curve]['Q4']]
            q_value = float(np.interp(value, x, y))
            q_value *= pwr_lvl
            return round(q_value, 1)

        elif CPF in self.function_used:
            q_value = math.sqrt(pow(value, 2) * ((1 / pow(pf, 2)) - 1))
            return round(q_value, 1)

        elif VW in self.function_used or variable == "V":
            x = [self.param[VW][curve]['V1'], self.param[VW][curve]['V2'], self.param[VW][curve]['V3']]
            y = [self.param[VW][curve]['P1'], self.param[VW][curve]['P2'], self.param[VW][curve]['P3']]
            p_targ = float(np.interp(value, x, y))
            p_targ *= pwr_lvl
            return p_targ

        elif WV in self.function_used:
            x = [self.param[WV][curve]['P0'], self.param[WV][curve]['P1'],
                 self.param[WV][curve]['P2'], self.param[WV][curve]['P3']]
            y = [self.param[WV][curve]['Q0'], self.param[WV][curve]['Q1'],
                 self.param[WV][curve]['Q2'], self.param[WV][curve]['Q3']]
            q_value = float(np.interp(value, x, y))
            q_value *= pwr_lvl
            # self.ts.log_debug('Power value: %s --> q_target: %s' % (value, q_value))
            return q_value

    def process_data(self, daq, tr, step, result_summary, filename, pwr_lvl=1.0, curve=1, initial_value=None,
                     x_target=None, y_target=None, aif=None, number_of_tr=2):

        if curve is not self.curve:
            self.curve = curve
            self.set_params(curve=curve)

        tr_values = self.get_tr_value(
            daq=daq,
            initial_value=initial_value,
            tr=tr,
            step=step,
            number_of_tr=number_of_tr,
            curve=curve,
            pwr_lvl=pwr_lvl,
            x_target=x_target,
            y_target=y_target,
            aif=aif
        )
        # self.ts.log_debug('tr_values: %s' % tr_values)

        # get pass-fail criteria for this test step
        analysis = self.get_analysis(initial_value=initial_value, tr_values=tr_values)
        # self.ts.log_debug('analysis: %s' % analysis)

        result_summary.write(self.write_rslt_sum(analysis=analysis, step=step, filename=filename))
        return


if __name__ == "__main__":
    pass
