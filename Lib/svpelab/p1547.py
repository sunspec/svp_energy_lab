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
IOP = 'IOP'  # Interoperability Tests

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
        self.param = {FW: {}, CPF: {}, VW: {}, VV: {}, WV: {}, CRP: {}, PRI: {}, IOP: {}}
        self.target_dict = []
        self.x_criteria = None
        self.y_criteria = None
        self.step_label = None
        self.double_letter_label = False
        self.criteria_mode = []
        self.meas_values = []
        self.curve = 1

        try:
            self.v_nom = ts.param_value('eut.v_nom')
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
            self.MRA_V = 0.01 * self.v_nom
            self.MRA_Q = 0.05 * ts.param_value('eut.s_rated')
            self.MRA_P = 0.05 * ts.param_value('eut.s_rated')
            self.MRA_F = 0.01
            self.MRA_T = 0.01
            self.MRA_V_trans = 0.02 * self.v_nom
            self.MRA_F_trans = 0.1
            self.MRA_T_trans = 2./60.

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
        if self.script_name == CPF:
            self.meas_values.append('PF')
        if self.script_name == CRP:
            self.meas_values.append('PF')
            # self.meas_values.remove('V')
            # self.meas_values.remove('P')
        if self.script_name == WV:
            self.meas_values.remove('V')
        if self.script_name == IOP:
            self.meas_values.append(['PF', 'F', 'Q'])

        self.ts.log('Measured values variables to be initialized: %s' % self.meas_values)

    def set_complete_test_name(self):
        """
        Write full complete test names

        :return: None
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
        elif self.script_name == IOP:
            self.script_complete_name = 'Interoperability Tests'
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

        self.rslt_sum_col_name = ','.join(row_data)+'\n'

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

        elif self.script_name == IOP:
            self.function_used = [VW, VV, FW, CPF, CRP, WV]

    def set_criteria_mode(self):
        """
        This functions set the criteria mode required for different functions.
        [0] Open Loop Time Response (OLTR) (90% of (y_final-y_intiial) + y_initial),
        [1] Test Results Accuracy on Tr 'y' value (TRATR) and
        [2] Test Results Accuracy on final (TRAF) 'y' value.

        :return: returns a binary list with the activated mode, e.g., [True, True, True]

        """
        if self.script_name == FW or self.script_name == VW or self.script_name == VV \
                or self.script_name == CPF or self.script_name == LAP:
            self.criteria_mode = [True, True, True]
        elif self.script_name == WV:
            self.criteria_mode = [True, False, True]
        elif self.script_name == CRP:  # EUT shall reach 90% of Qfinal before 10 s after a voltage or power step
            self.criteria_mode = [True, False, False]
        elif self.script_name == PRI:
            self.criteria_mode = [False, False, True]
        elif self.script_name == IOP:
            self.criteria_mode = [False, False, False]

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
                    'P1': round(p, 2),
                    'P2': round(0.5 * self.p_rated, 2),
                    'P3': round(1.0 * self.p_rated, 2),
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
                    'P1': round(p, 2),
                    'P2': round(0.5 * self.p_rated, 2),
                    'P3': round(1.0 * self.p_rated, 2),
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
                    'P1': round(p, 2),
                    'P2': round(0.5 * self.p_rated, 2),
                    'P3': round(1.0 * self.p_rated, 2),
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

        if IOP in self.function_used:
            self.target_dict = []
            self.param[IOP] = self.target_dict

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
            elif self.script_name == WV:
                self.x_criteria = ['P']

        elif self.script_name == PRI:
            self.y_criteria = ['P', 'Q']
            self.x_criteria = ['V', 'F']

        elif self.script_name == IOP:
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

        xs = self.x_criteria
        ys = self.y_criteria
        first_iter = analysis['FIRST_ITER']
        last_iter = analysis['LAST_ITER']
        row_data = []

        # Time response criteria will take last placed value of Y variables
        if self.criteria_mode[0]:
            row_data.append(str(analysis['TR_90_%_PF']))
        if self.criteria_mode[1]:
            row_data.append(str(analysis['%s_TR_%s_PF' % (ys[-1], first_iter)]))
        if self.criteria_mode[2]:
            row_data.append(str(analysis['%s_TR_%s_PF' % (ys[-1], last_iter)]))

        # Default measured values are V, P and Q (F can be added) refer to set_meas_variable function
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

        # except Exception as e:
        #     raise p1547Error('Error in write_rslt_sum() : %s' % (str(e)))

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
        Returns the measurement label for a measurement type

        :param type_meas:   (str) Either V, P, PF, I, F, VA, or Q
        :return:            (list of str) List of labeled measurements, e.g., ['AC_VRMS_1', 'AC_VRMS_2', 'AC_VRMS_3']
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
            self.ts.log_error('type_meas=%s' % type_meas)

            raise p1547Error('Error in get_measurement_total() : %s' % (str(e)))

        # TODO : imbalance_resp should change the way you acquire the data
        if type_meas == 'V' or type_meas == 'PF':
            # average value of V or PF
            value = value / nb_phases
        elif type_meas == 'F':
            # No need to do data average for frequency
            value = data.get(self.get_measurement_label(type_meas)[0])

        return round(value, 3)

    def get_initial_value(self, daq, step):
        """
        Sum the EUT phases for given parameter (power, reactive power, etc.) from all phases
        :param daq:         data acquisition object from svpelab library
        :param step:        test procedure step letter or number (e.g "Step G")
        :return: returns a dictionary with the timestamp, event, and total EUT phase, e.g.,
            {'timestamp': datetime.datetime(2020, 4, 3, 10, 23, 21, 786000),
            'Y_MEAS': 60.998,
            'X_MEAS': 2088.702}
        """
        # TODO : In a more sophisticated approach, get_initial['timestamp'] will come from a
        # reliable secure thread or data acquisition timestamp
        self.set_x_y_variable(step=step)
        initial = {}
        initial['timestamp'] = datetime.now()
        daq.data_sample()
        data = daq.data_capture_read()

        daq.sc['event'] = step
        for meas_value in self.meas_values:
            initial['%s_MEAS' % meas_value] = self.get_measurement_total(data=data, type_meas=meas_value, log=False)
            daq.sc['%s_MEAS' % meas_value] = initial['%s_MEAS' % meas_value]

        daq.data_sample()

        return initial

    def update_target_value(self, daq, pwr_lvl=1.0, curve=1, x_target=None, y_target=None, data=None, aif=None):
        """
        Function to update target values depending on script name

        ----------------------------------------------------------------
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
        ----------------------------------------------------------------

        :param daq:         (object) data acquisition object from svpelab library
        :param pwr_lvl:     (float) Multiplier value for different power level of test
        :param curve:       (int) By default, curve=1 but can be changed for another curve depending on script
        :param x_target:    (dictionary) This should include the variable that is causing the variation with
                            key as type of value
        :param y_target:    (dictionary) This should be a dictionary of target value for the desired variable
                            (P or/and Q)
        :param data:        (object) This should be included if we need measured value to use with function
                            total_measurement()
        :param aif:         (str) advanced inverter function, e.g., 'PF'
        :return:
        """

        if isinstance(x_target, dict):
            for x_meas_variable, x_meas_value in x_target.items():
                daq.sc['%s_MEAS' % x_meas_variable] = self.get_measurement_total(data=data, type_meas=x_meas_variable)
                daq.sc['%s_TARGET' % x_meas_variable] = x_meas_value

        if isinstance(y_target, dict):
            for y_meas_variable, y_meas_value in y_target.items():
                daq.sc['%s_MEAS' % y_meas_variable] = self.get_measurement_total(data=data, type_meas=y_meas_variable)
                daq.sc['%s_TARGET' % y_meas_variable] = y_meas_value

                # get MRA for the y parameter
                if y_meas_variable == 'P':
                    mra = self.MRA_P
                elif y_meas_variable == 'Q':
                    mra = self.MRA_Q
                else:
                    mra = 0
                # apply MRA to the y parameter for the min and max
                if y_meas_value is not None:
                    daq.sc['%s_TARGET_MIN' % y_meas_variable] = y_meas_value - (mra * 1.5)
                    daq.sc['%s_TARGET_MAX' % y_meas_variable] = y_meas_value + (mra * 1.5)

                self.ts.log('Y Value (%s) = %s. Pass/fail bounds = [%s, %s]' %
                            (y_meas_value, daq.sc['%s_MEAS' % y_meas_variable],
                             daq.sc['%s_TARGET_MIN' % y_meas_variable], daq.sc['%s_TARGET_MAX' % y_meas_variable]))

        else:
            if self.script_name == VV:
                daq.sc['V_MEAS'] = self.get_measurement_total(data=data, type_meas='V', log=False)
                daq.sc['Q_MEAS'] = self.get_measurement_total(data=data, type_meas='Q', log=False)
                v_meas = daq.sc['V_MEAS']
                daq.sc['Q_TARGET'] = self.get_targ(v_meas, pwr_lvl, curve)
                daq.sc['Q_TARGET'] = self.get_targ(v_meas, pwr_lvl, curve)
                daq.sc['Q_TARGET_MIN'] = self.get_targ(v_meas + self.MRA_V * 1.5, pwr_lvl, curve)-(self.MRA_Q*1.5)
                daq.sc['Q_TARGET_MAX'] = self.get_targ(v_meas - self.MRA_V * 1.5, pwr_lvl, curve)+(self.MRA_Q*1.5)
            elif self.script_name == LAP:
                p_meas = self.get_measurement_total(data=data, type_meas='P', log=False)
                daq.sc['P_MEAS'] = p_meas
                # P target for step F specifically but will be calculated for all of it
                daq.sc['P_TARGET'] = self.get_targ(p_meas)
                # P target min & max for steps D and E
                daq.sc['P_TARGET_MIN'] = self.get_targ(daq.sc['F_MEAS'], variable='F')
                daq.sc['P_TARGET_MAX'] = self.get_targ(daq.sc['F_MEAS'], variable='F')
            elif self.script_name == CPF:
                pf_meas = self.get_measurement_total(data=data, type_meas='PF', log=False)
                daq.sc['PF_MEAS'] = pf_meas
                daq.sc['Q_MEAS'] = self.get_measurement_total(data=data, type_meas='Q', log=False)
                daq.sc['Q_TARGET'] = self.get_targ(daq.sc['Q_MEAS'], pwr_lvl, pf=x_target['PF'])
                daq.sc['Q_TARGET_MIN'] = \
                    self.get_targ(daq.sc['Q_MEAS'] + self.MRA_P * 1.5, pwr_lvl, pf=x_target['PF']) - 1.5*self.MRA_Q
                daq.sc['Q_TARGET_MAX'] = \
                    self.get_targ(daq.sc['Q_MEAS'] - self.MRA_P * 1.5, pwr_lvl, pf=x_target['PF']) + 1.5*self.MRA_Q
            elif self.script_name == CRP:
                q_meas = self.get_measurement_total(data=data, type_meas='Q', log=False)
                daq.sc['Q_MEAS'] = q_meas
                # regardless of the power level, the EUT should produce target reactive power
                daq.sc['Q_TARGET'] = y_target
                daq.sc['Q_TARGET_MIN'] = daq.sc['Q_TARGET'] - 1.5*self.MRA_Q
                daq.sc['Q_TARGET_MAX'] = daq.sc['Q_TARGET'] + 1.5*self.MRA_Q
            elif self.script_name == FW:
                p_meas = self.get_measurement_total(data=data, type_meas='P', log=False)
                daq.sc['P_MEAS'] = p_meas
                daq.sc['F_MEAS'] = self.get_measurement_total(data=data, type_meas='F', log=False)
                daq.sc['P_TARGET'] = self.get_targ(p_meas, pwr_lvl, curve)
                daq.sc['P_TARGET_MIN'] = \
                    self.get_targ(daq.sc['F_MEAS'] + self.MRA_F * 1.5, pwr_lvl, curve) - (self.MRA_P * 1.5)
                daq.sc['P_TARGET_MAX'] = \
                    self.get_targ(daq.sc['F_MEAS'] - self.MRA_F * 1.5, pwr_lvl, curve) + (self.MRA_P * 1.5)
            elif self.script_name == VW:
                v_meas = self.get_measurement_total(data=data, type_meas='V', log=False)
                daq.sc['V_MEAS'] = v_meas
                p_meas = self.get_measurement_total(data=data, type_meas='P', log=False)
                daq.sc['P_MEAS'] = p_meas
                daq.sc['P_TARGET'] = self.get_targ(v_meas, pwr_lvl, curve)
                daq.sc['P_TARGET_MIN'] = self.get_targ(v_meas + self.MRA_V*1.5, pwr_lvl, curve) - (self.MRA_P*1.5)
                daq.sc['P_TARGET_MAX'] = self.get_targ(v_meas - self.MRA_V*1.5, pwr_lvl, curve) + (self.MRA_P*1.5)
            elif self.script_name == WV:
                p_meas = self.get_measurement_total(data=data, type_meas='P', log=False)
                daq.sc['P_MEAS'] = p_meas
                q_meas = self.get_measurement_total(data=data, type_meas='Q', log=False)
                daq.sc['Q_MEAS'] = q_meas
                daq.sc['Q_TARGET'] = self.get_targ(daq.sc['P_MEAS'], pwr_lvl, curve)
                daq.sc['Q_TARGET_MIN'] = \
                    self.get_targ(daq.sc['P_MEAS'] + self.MRA_P * 1.5, pwr_lvl, curve) - (self.MRA_Q * 1.5)
                daq.sc['Q_TARGET_MAX'] = \
                    self.get_targ(daq.sc['P_MEAS'] - self.MRA_P * 1.5, pwr_lvl, curve) + (self.MRA_Q * 1.5)

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
                self.ts.log('Waiting %s seconds to get the next Tr data for analysis...' %
                            time_to_sleep.total_seconds())
                self.ts.sleep(time_to_sleep.total_seconds())
            daq.data_sample()  # sample new data
            data = daq.data_capture_read()  # Return dataset created from last data capture
            daq.sc['EVENT'] = "{0}_TR_{1}".format(step, tr_iter)

            # update daq.sc values for Y_TARGET, Y_TARGET_MIN, and Y_TARGET_MAX
            self.update_target_value(daq=daq, pwr_lvl=pwr_lvl, curve=curve, x_target=x_target, y_target=y_target,
                                     data=data)

            # store the daq.sc['Y_TARGET'], daq.sc['Y_TARGET_MIN'], and daq.sc['Y_TARGET_MAX'] in tr_value
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
                except Exception as e:
                    self.ts.log_debug('Measured value (%s) not recorded: %s' % (meas_value, e))

            tr_value[tr_iter]["timestamp"] = tr_
            tr_iter = tr_iter + 1

        return tr_value

        # except Exception as e:
        #    raise p1547Error('Error in get_tr_data(): %s' % (str(e)))

    def get_open_loop_value(self, y0, y_ss, duration, tr):
        """
        Calculated the anticipated Y(Tr +/- MRA_T) values based on duration and Tr

        Note: for a unit step response Y(t) = 1 - exp(-t/tau) where tau is the time constant

        :param y0: initial Y(0) value
        :param y_ss: steady-state solution, e.g., Y(infinity)
        :param duration: time since the change in the input parameter that the output should be calculated
        :param tr: open loop response time (90% change or 2.3 * time constant)

        :return: output Y(duration) anticipated based on the open loop response function
        """

        time_const = tr/(-(math.log(0.1)))  # ~2.3 * time constants to reach the open loop response time in seconds
        number_of_taus = duration / time_const  # number of time constants into the response
        resp_fraction = 1-math.exp(-number_of_taus)  # fractional response after the duration, e.g. 90%

        # Y must be 90% * (Y_final - Y_initial) + Y_initial
        resp = (y_ss - y0) * resp_fraction + y0  # expand to y units

        return resp

    def get_analysis(self, initial_value, tr_values, tr):
        """
        Get the analysis results of the pass-fail criteria.

        Two pass/fail results based on the data from the Tr's collected with get_tr_value(). The first is a TRANSIENT
        requirement using the temporal response of the system and the other is a STEADY-STATE evaluation based on the
        AIF

        TRANSIENT:
            After 1*Tr, the Y must be 90% * (Y_final - Y_initial) + Y_initial.
            Accuracy requirements are from 1547.1 4.2 (Ymin <= Ymeas <= Ymax) with X = Tr, Y = Y(Tr)

            ^                                      Y(Tr+MRA_t)            _________________
            |                           Y(Tr)     ____+_________________/
            |                             ______/
            |          Y(Tr-MRA_t)  ____/ |
            |                  +__/       |
        Y(t)|                _/           |
            |              /              |
            |            /                |
            |          /                  |
            |        /                    |
            |------/                      |
            _______|______________________|________________________|___________________________>
                  t_initial              Tr     time (sec)        2*Tr

            Ymin <= Ymeas <= Ymax
            Ymin is Y(Tr_meas + 1.5 * MRA(time)) - 1.5 * MRA(Y)
            Ymax is Y(Tr_meas - 1.5 * MRA(time)) + 1.5 * MRA(Y)

        STEADY-STATE:
            At steady state (i.e., after 2*Tr), the Y must be within the MRA of the X-Y curve
            Accuracy requirements are from 1547.1 4.2 (Ymin <= Ymeas <= Ymax) with X = X_final, Y = Y_final

            Assuming the curve has a negative slope the following is used to determine Ymin and Ymax
            Ymin is Y(Xmeas + 1.5 * MRA(X)) - 1.5 * MRA(Y)
            Ymax is Y(Xmeas - 1.5 * MRA(X)) + 1.5 * MRA(Y)

            Ymax -------------->   \ * (x_value - 1.5*x_mra, y1 + 1.5*y_mra)
                                      \
                                       . (x_value - 1.5*x_msa, y1)
                                        \
                                         x (x_value, y_target)
                                          \
                                           . (x_value + 1.5*x_msa, y2)
                                            \
            Ymin ---------------------->   * \  (x_value + 1.5*x_msa, y2 - 1.5*y_mra)

        :param initial_value: A dictionary with measurements before a step, e.g.,
                {'timestamp': datetime.datetime(2020, 4, 3, 10, 23, 21, 786000),
                'Y_MEAS': 60.998,
                'X_MEAS': 2088.702}

        :param tr_values: An ordered dictionary with measurements after each time response cycle, e.g.,
                OrderedDict([
                    (1,{  # Results from the first Tr
                        'Y_MEAS': 2532.715,
                        'Y_TARGET': 100,
                        'Y_TARGET_MAX': 1800.0,
                        'Y_TARGET_MIN': -3841.43,
                        'X_TARGET': 18000.0,
                        'X_MEAS': 16520.606,
                        'timestamp': datetime.datetime(2020, 4, 3, 9, 40, 55, 793000)
                        }),
                    (2,{  # Results after 2*Tr
                        'Y_MEAS': 2532.715,
                        'Y_TARGET': 100,
                        'Y_TARGET_MAX': 1800.0,
                        'Y_TARGET_MIN': -3841.43,
                        'X_TARGET': 18000.0,
                        'X_MEAS': 16520.606,
                        'timestamp': datetime.datetime(2020, 4, 3, 9, 40, 55, 793000)
                        })
                ])

        :param tr: (float) time response in sec

        :return: returns a dictionary with pass fail criteria that will be use in the result_summary.csv file, e.g.,
                 {'FIRST_ITER': 1,      # The first time response used for pass/fail evaluation
                 'Y_INITIAL': 60.998,   # value of the y-value at the start of the step
                 'Y_TR_TARG_1': 100,    # the target y-value at Tr=1
                 'Y_TR_1': 60.998,      # the y-value at Tr=1
                 'Y_TR_1_MAX': -6659.,  # the maximum passing y-value at Tr=1
                 'Y_TR_1_MIN': -12360,  # the minimum passing y-value at Tr=1
                 'X_TR_TARG_1': 2400.0, # the x-value target at Tr=1
                 'X_TR_1': 2088.702,    # the x-value at Tr=1
                 'TR_90_%_PF': 'Pass',  # the 90% pass/fail score
                 'Y_TR_1_PF': 'Fail',   # the 1 Tr pass/fail score (optional)

                 'LAST_ITER': 2,        # the final Tr where the steady-state results are evaluated
                 'Y_TR_2': 60.998       # the y-value at Tr=2(last)
                 'Y_TR_TARG_2': 100,    # the y-value at Tr=2(last)
                 'Y_TR_2_MAX': 1800.0,  # the maximum passing y-value at Tr=2(last)
                 'Y_TR_2_MIN': -1800.0, # the minimum passing y-value at Tr=2(last)
                 'X_TR_TARG_2': 3000.0, # the x-value target at Tr=2(last)
                 'X_TR_2': 2088.702,    # the x-value at Tr=2(last)
                 'Y_TR_2_PF': 'Pass',   # the final Tr pass/fail score
                 }
        """

        analysis = {}
        xs = self.x_criteria
        ys = self.y_criteria

        analysis['FIRST_ITER'] = next(iter(list(tr_values.keys())))
        analysis['LAST_ITER'] = len(tr_values)

        if isinstance(ys, list):
            for y in ys:
                analysis['%s_INITIAL' % y] = initial_value['%s_MEAS' % y]

        for tr_iter, tr_value in list(tr_values.items()):
            self.ts.log_debug('tr_iter=%s, Tr value=%s' % (tr_iter, tr_value))

            for meas_value in self.meas_values:
                # Determine how close to the target input variable the test was:
                if meas_value in xs:
                    analysis['%s_TR_TARG_%s' % (meas_value, tr_iter)] = tr_value['%s_TARGET' % meas_value]

                # Get all the measured values after the Tr period
                if meas_value is not None:
                    analysis['%s_TR_%s' % (meas_value, tr_iter)] = tr_value['%s_MEAS' % meas_value]
                    analysis['%s_TR_TARG_%s' % (meas_value, tr_iter)] = None
                    analysis['%s_TR_%s_MIN' % (meas_value, tr_iter)] = None
                    analysis['%s_TR_%s_MAX' % (meas_value, tr_iter)] = None

                    # For each of the measured values of interest, determine how close they are to the EUT target
                    if meas_value in ys:
                        analysis['%s_TR_TARG_%s' % (meas_value, tr_iter)] = tr_value['%s_TARGET' % meas_value]
                        analysis['%s_TR_%s_MIN' % (meas_value, tr_iter)] = tr_value['%s_TARGET_MIN' % meas_value]
                        analysis['%s_TR_%s_MAX' % (meas_value, tr_iter)] = tr_value['%s_TARGET_MAX' % meas_value]

                        if tr_iter == 1 and self.criteria_mode[0]: # Only evaluate the 90% criterion after the first Tr
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
                            if self.script_name == VV or self.script_name == CPF or self.script_name == WV \
                                    or self.script_name == CRP:
                                mra_y = self.MRA_Q
                            else:  # self.script_name == LAP or self.script_name == FW or self.script_name == VW:
                                mra_y = self.MRA_P

                            duration = tr_value['timestamp'] - initial_value['timestamp']
                            duration = duration.total_seconds()
                            self.ts.log('Calculating pass/fail for Tr = %s sec, with a target of %s sec' %
                                        (duration, tr))

                            # Given that Y(time) is defined by an open loop response characteristic, use that curve to
                            # calculated the target, minimum, and max, based on the open loop response expectation
                            if self.script_name == CRP:  # for those tests with a flat 90% evaluation
                                y_start = 0.0  # only look at 90% of target
                                mra_t = 0  # direct 90% evaluation without consideration of MRA(time)
                            else:
                                y_start = analysis['%s_INITIAL' % meas_value]
                                mra_t = self.MRA_T * duration  # MRA(X) = MRA(time) = 0.01*duration

                            y_ss = tr_value['%s_TARGET' % meas_value]
                            y_target = self.get_open_loop_value(y0=y_start, y_ss=y_ss, duration=duration, tr=tr)  # 90%
                            y_meas = analysis['%s_TR_%s' % (meas_value, tr_iter)]
                            # self.ts.log_debug('y_target = %s, y_ss [%s], y_start [%s], duration = %s, tr=%s' %
                            #                   (y_target, y_ss, y_start, duration, tr))

                            if y_start <= y_target:  # increasing values of y
                                increasing = True
                                # Y(time) = open loop curve, so locate the Y(time) value on the curve
                                y_min = self.get_open_loop_value(y0=y_start, y_ss=y_ss,
                                                                 duration=duration-1.5*mra_t, tr=tr) - 1.5 * mra_y
                                # Determine maximum value based on the open loop response expectation
                                y_max = self.get_open_loop_value(y0=y_start, y_ss=y_ss,
                                                                 duration=duration+1.5*mra_t, tr=tr) + 1.5 * mra_y
                            else:  # decreasing values of y
                                increasing = False
                                # Y(time) = open loop curve, so locate the Y(time) value on the curve
                                y_min = self.get_open_loop_value(y0=y_start, y_ss=y_ss,
                                                                 duration=duration+1.5*mra_t, tr=tr) - 1.5 * mra_y
                                # Determine maximum value based on the open loop response expectation
                                y_max = self.get_open_loop_value(y0=y_start, y_ss=y_ss,
                                                                 duration=duration-1.5*mra_t, tr=tr) + 1.5 * mra_y

                            # pass/fail applied to the open loop time response
                            if self.script_name == CRP:  # 1-sided analysis
                                # Pass: Ymin <= Ymeas when increasing y output
                                # Pass: Ymeas <= Ymax when decreasing y output
                                if increasing:
                                    if y_min <= y_meas:
                                        analysis['TR_90_%_PF'] = 'Pass'
                                    else:
                                        analysis['TR_90_%_PF'] = 'Fail'
                                    self.ts.log_debug('Transient y_targ = %s, y_min [%s] <= y_meas [%s] = %s' %
                                                      (y_target, y_min, y_meas, analysis['TR_90_%_PF']))
                                else:  # decreasing
                                    if y_meas <= y_max:
                                        analysis['TR_90_%_PF'] = 'Pass'
                                    else:
                                        analysis['TR_90_%_PF'] = 'Fail'
                                    self.ts.log_debug('Transient y_targ = %s, y_meas [%s] <= y_max [%s] = %s'
                                                      % (y_target, y_meas, y_max, analysis['TR_90_%_PF']))

                            else:  # 2-sided analysis
                                # Pass/Fail: Ymin <= Ymeas <= Ymax
                                if y_min <= y_meas <= y_max:
                                    analysis['TR_90_%_PF'] = 'Pass'
                                else:
                                    analysis['TR_90_%_PF'] = 'Fail'
                                self.ts.log_debug('Transient y_targ = %s, y_min [%s] <= y_meas [%s] <= y_max [%s] = %s'
                                                  % (y_target, y_min, y_meas, y_max, analysis['TR_90_%_PF']))

        # Note: Note sure where criteria_mode[1] (SS accuracy after 1 Tr) is used in IEEE 1547.1
        if self.criteria_mode[1] or self.criteria_mode[2]:  # STEADY-STATE pass/fail evaluation
            for y in ys:
                for tr_iter, tr_dic in list(tr_values.items()):
                    if (analysis['FIRST_ITER'] == tr_iter and self.criteria_mode[1]) or \
                            (analysis['LAST_ITER'] == tr_iter and self.criteria_mode[2]):

                        # pass/fail assessment for the steady-state values
                        if analysis['%s_TR_%s_MIN' % (y, tr_iter)] <= \
                                analysis['%s_TR_%s' % (y, tr_iter)] <= analysis['%s_TR_%s_MAX' % (y, tr_iter)]:
                            analysis['%s_TR_%s_PF' % (y, tr_iter)] = 'Pass'
                        else:
                            analysis['%s_TR_%s_PF' % (y, tr_iter)] = 'Fail'

                        self.ts.log('  Steady state %s(Tr_%s) evaluation: %0.1f <= %0.1f <= %0.1f  [%s]' % (
                            y,
                            tr_iter,
                            analysis['%s_TR_%s_MIN' % (y, tr_iter)],
                            analysis['%s_TR_%s' % (y, tr_iter)],
                            analysis['%s_TR_%s_MAX' % (y, tr_iter)],
                            analysis['%s_TR_%s_PF' % (y, tr_iter)]))
        return analysis

    def get_params(self, curve=None, aif=None):
        """
        Gets the parameters for the test for a given AIF and curve number

        If curve provided, this will update the curve using set_params()

        :param curve: int, Curve number
        :param aif: str, Advanced inverter function, e.g., 'VV', 'WV'
        :return: (X, Y) pairs of the curves in a list, e.g., [P1, P2, P3, V1, V2, V3]
        """
        self.ts.log_debug('Getting params for aif=%s and curve=%s' % (aif, curve))

        # update params if curve number is provided
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

        In the case of the curve-based functions, this interpolates the value

        :param value: (float) input value, as measured during the test
        :param pwr_lvl: (float) DC power level the test was conducted, this is used to scale expected results
        :param curve: (int) curve number
        :param pf: (float) power factor, used in the CPF tests
        :param variable: (str) the name of input 'value', e.g., V for the VV test

        :return: (float) EUT target
        """

        # limit active power evaluation
        if self.script_name == LAP and variable is not 'F':
            p_targ = self.p_rated - (self.p_rated-self.param[VW][curve]['P2'])*((value/self.v_nom)-1.06)/0.04
            return p_targ

        if FW in self.function_used or variable == 'F':  # frequency-based evaluations, e.g., FW
            p_targ = None
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

        elif CRP in self.function_used:
            q_value = math.sqrt(pow(value, 2) * ((1 / pow(pf, 2)) - 1))
            return round(q_value, 1)

        elif VW in self.function_used or variable == "V":
            x = [self.param[VW][curve]['V1'], self.param[VW][curve]['V2'], self.param[VW][curve]['V3']]
            y = [self.param[VW][curve]['P1'], self.param[VW][curve]['P2'], self.param[VW][curve]['P3']]
            p_targ = float(np.interp(value, x, y))
            p_targ *= pwr_lvl
            return p_targ

        elif WV in self.function_used:
            x = [self.param[WV][curve]['P1'], self.param[WV][curve]['P2'], self.param[WV][curve]['P3']]
            y = [self.param[WV][curve]['Q1'], self.param[WV][curve]['Q2'], self.param[WV][curve]['Q3']]
            q_value = float(np.interp(value, x, y))
            q_value *= pwr_lvl
            # self.ts.log_debug('Power value: %s --> q_target: %s' % (value, q_value))
            return q_value

    def process_data(self, daq, tr, step, result_summary, filename, pwr_lvl=1.0, curve=1, initial_value=None,
                     x_target=None, y_target=None, aif=None, number_of_tr=2):
        """
        Processing the data is done in two steps

        1. get_tr_value()
            Collects the values from each of the Tr's of interest

            returns tr_values dict of the form:
                OrderedDict([
                    (1,{  # Results from the first Tr
                        'Y_MEAS': 2532.715,
                        'Y_TARGET': 100,
                        'Y_TARGET_MAX': 1800.0,
                        'Y_TARGET_MIN': -3841.4389599999995,
                        'X_TARGET': 18000.0,
                        'X_MEAS': 16520.606,
                        'timestamp': datetime.datetime(2020, 4, 3, 9, 40, 55, 793000)
                        }),
                    (2,{  # Results after 2*Tr
                        'Y_MEAS': 2532.715,
                        'Y_TARGET': 100,
                        'Y_TARGET_MAX': 1800.0,
                        'Y_TARGET_MIN': -3841.4389599999995,
                        'X_TARGET': 18000.0,
                        'X_MEAS': 16520.606,
                        'timestamp': datetime.datetime(2020, 4, 3, 9, 40, 55, 793000)
                        })
                ])

        2. get_analysis()
            Determines the pass/fail results based on the data from the Tr's collected with get_tr_value()

            After 1*Tr, the Y must be 90% * (Y_final - Y_initial) + Y_initial.
            Accuracy requirements are from 1547.1 4.2 (Ymin <= Ymeas <= Ymax) with X = Tr, Y = Y(Tr)

            After 2*Tr, the Y must be within the MRA of the X-Y curve
            Accuracy requirements are from 1547.1 4.2 (Ymin <= Ymeas <= Ymax) with X = X_final, Y = Y_final

            returns analysis dict of the form:
                {'Q_INITIAL': 356.574,
                'P_TR_1': 5930.334,
                'Q_TR_1_PF': 'Pass',
                'TR_90_%_PF': 'Pass',
                'P_TR_TARG_1': 6600.0,
                'LAST_ITER': 1,
                'Q_TR_1_MIN': -1800.0,
                'Q_TR_1_MAX': 1800.0,
                'FIRST_ITER': 1,
                'Q_TR_TARG_1': 100,
                'Q_TR_1': 356.574,
                'V_TR_1': 279.733}

        :param daq: Data acquisition system object
        :param tr: programmed time response (sec)
        :param step: Step label, e.g., STEP H
        :param result_summary: SVP result summary (.csv) handle
        :param filename: result filename, e.g., VV_1
        :param pwr_lvl: DC power level used for the test (used as curve multiplier for expected results)
        :param curve: dict with curve used for the test
        :param initial_value: the starting value for the step from lib_1547.get_initial_value()
        :param x_target: input parameter target
        :param y_target: EUT output target based on the function (e.g. LAP -> act_pwrs_limits)
        :param aif: advanced inverter function name
        :param number_of_tr: number of time responses used to validate the response and steady state values
        :return: None
        """

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
        analysis = self.get_analysis(initial_value=initial_value, tr_values=tr_values, tr=tr)
        # self.ts.log_debug('analysis: %s' % analysis)

        result_summary.write(self.write_rslt_sum(analysis=analysis, step=step, filename=filename))
        return


if __name__ == "__main__":
    pass
