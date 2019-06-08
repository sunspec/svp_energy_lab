import os
import xml.etree.ElementTree as ET
import csv
import math
import xlsxwriter
import traceback
from datetime import datetime, timedelta

import time
import collections
#import sys
#import os
#import glob
#import importlib


class p1547Error(Exception):

    pass

class module_1547(object):
    script_name = ''
    def __init__(self, ts, aif, imbalance_angle_fix='No', absorb=None):
        # Library variables
        self.ts = ts
        #self.params = params
        self.script_name = aif
        self.rslt_sum_col_name = ''
        self.pairs = {}
        self.mag = {}
        self.ang = {}
        self.param = {}
        """
        According to Table 3-Minimum requirements for manufacturers stated measured and calculated accuracy
        """
        # TODO: Add verification?
        self.v_nom = ts.param_value('eut.v_nom')
        self.MSA_V = 0.01 * self.v_nom
        self.MSA_Q = 0.05 * ts.param_value('eut.s_rated')
        self.MSA_P = 0.05 * ts.param_value('eut.s_rated')
        self.MSA_F = 0.01
        self.f_nom = ts.param_value('eut.f_nom')
        self.phases = ts.param_value('eut.phases')
        self.p_rated = ts.param_value('eut.p_rated')
        self.p_min = ts.param_value('eut.p_rated')
        self.var_rated = ts.param_value('eut.var_rated')
        self.imbalance_angle_fix = imbalance_angle_fix
        self.absorb = absorb


        self._config()

    def _config(self):
        # Set the result summary column names
        self.set_result_summary_col_name()
        # Create the pairs need
        self.set_params()
        # Configure test for imblance operation
        self.set_imbalance_config()

    """
    Setter functions
    """



    def set_result_summary_col_name(self):
        """
        Write column names for results file depending on which test is being run
        :param nothing:
        :return: nothing
        """
        if self.script_name == "CPF":
            self.rslt_sum_col_name = 'Q_TR_ACC_REQ,TR_REQ,Q_FINAL_ACC_REQ,P_MEAS,Q_MEAS,Q_TARGET,Q_TARGET_MIN,' \
                       'Q_TARGET_MAX,STEP,FILENAME\n'
        elif self.script_name == "VV":
            self.rslt_sum_col_name = 'Q_TR_ACC_REQ,TR_REQ,Q_FINAL_ACC_REQ,V_MEAS,Q_MEAS,Q_TARGET,Q_TARGET_MIN,' \
                       'Q_TARGET_MAX,STEP,FILENAME\n'
        elif self.script_name == "VW":
            self.rslt_sum_col_name = 'P_TR_ACC_REQ,TR_REQ,P_FINAL_ACC_REQ,V_MEAS,P_MEAS,P_TARGET,P_TARGET_MIN,' \
                       'P_TARGET_MAX,STEP,FILENAME\n'
        elif self.script_name == "FW":
            self.rslt_sum_col_name = 'P_TR_ACC_REQ,TR_REQ,P_FINAL_ACC_REQ,F_MEAS,P_MEAS,P_TARGET,P_TARGET_MIN,' \
                          'P_TARGET_MAX,STEP,FILENAME\n'

    def set_params(self):
        """
        Configure the parameter specific to the AIF
        :param nothing:
        :return: nothing
        """

        if self.script_name == "VW":
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
            elif self.absorb['ena'] == 'Yes':
                self.param[1]['P2'] = 0
                self.param[2]['P2'] = self.absorb['p_rated_prime']
                self.param[3]['P2'] = self.absorb['p_rated_prime']
            else:
                self.param[1]['P2'] = int(self.p_min)
                self.param[2]['P2'] = int(self.p_min)
                self.param[3]['P2'] = int(self.p_min)

        elif self.script_name == "FW":
            p_small = self.ts.param_value('eut_fw.p_small')
            self.param[1] = {"dbf": 0.036,
                             'kof': 0.05,
                             'tr': self.ts.param_value('fw.test_1_tr'),
                             'f_small': p_small * self.f_nom * 0.05
                             }
            self.param[2] = {'dbf': 0.017,
                             'kof': 0.02,
                             'tr': self.ts.param_value('fw.test_2_tr'),
                             'f_small': p_small * self.f_nom  * 0.02
                             }

        elif self.script_name == "VV":
            self.param[1] = {'V1': round(0.92 * self.v_nom, 2),
                             'V2': round(0.98 * self.v_nom, 2),
                             'V3': round(1.02 * self.v_nom, 2),
                             'V4': round(1.08 * self.v_nom, 2),
                             'Q1': round(self.var_rated * 1.0, 2),
                             'Q2': round(self.var_rated * 0.0, 2),
                             'Q3': round(self.var_rated * 0.0, 2),
                             'Q4': round(self.var_rated * -1.0, 2)}

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

    def set_imbalance_config(self,imbalance_angle_fix=None):
        """
        Initiliaze the case possibility for imbalance test either with fix 120 degrees for the angle or
        with a calculated angles that would result in a null sequence zero
        :param imbalance_angle_fix:   string (Yes or No)
        if Yes, angle are fix at 120 degrees for both cases.
        if No, resulting sequence zero will be null for both cases.

        :return: nothing
        """

        if self.imbalance_angle_fix == 'Yes':
            # Case A
            self.mag['case_a'] = [1.07 * self.v_nom, 0.91 * self.v_nom, 0.91 * self.v_nom]
            self.ang['case_a'] = [0., 120, -120]
            # Case B
            self.mag['case_b'] = [0.91 * self.v_nom, 1.07 * self.v_nom, 1.07 * self.v_nom]
            self.ang['case_b'] = [0., 120.0, -120.0]
            self.ts.log("Setting test with imbalanced test with FIXED angles/values")
        elif self.imbalance_angle_fix == 'No':
            # Case A
            self.mag['case_a'] = [1.08 * self.v_nom, 0.91 * self.v_nom, 0.91 * self.v_nom]
            self.ang['case_a'] = [0., 126.59, -126.59]
            # Case B
            self.mag['case_b'] = [0.9 * self.v_nom, 1.08 * self.v_nom, 1.08 * self.v_nom]
            self.ang['case_b'] = [0., 114.5, -114.5]
            self.ts.log("Setting test with imbalanced test with NOT FIXED angles/values")

    def write_rslt_sum(self, analysis, step, filename):
        """
        Combines the analysis results, the step label and the filenamoe to return
        a row that will go in result_summary.csv
        :param analysis: Dictionnary with all the information for result summary
        :param step:   test procedure step letter or number (e.g "Step G")
        :param filename: the dataset filname use for analysis
        :return: row_data a string with all the information for result_summary.csv
        """
        try:
            row_data = ''
            x = self.get_letter('x')
            y = self.get_letter('y')

            row_data = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (analysis['%s_TR' % y],
                                                            analysis['TR'],
                                                            analysis['%s_FINAL_TR' % y],
                                                            analysis['%s_MEAS' % x],
                                                            analysis['%s_MEAS' % y],
                                                            analysis['%s_TARGET' % y],
                                                            analysis['%s_TARGET_MIN' % y],
                                                            analysis['%s_TARGET_MAX' % y],
                                                            step, filename)

            return row_data
        except Exception as e:
            raise p1547Error('Error in write_rslt_sum() : %s' % (str(e)))

    """
    Getter functions
    """

    def get_test_name(self):
        """
        This getters function returns the advanced inverter function complete name
        :return: test_name as a String
        """
        try:
            test_name = ''
            if self.script_name == 'FW':
                test_name = 'Frequency-Watt'
            if self.script_name == 'CPF':
                test_name = 'Constant Power Factor'
            if self.script_name == 'VW':
                test_name = 'Volt-Watt'
            if self.script_name == 'VV':
                test_name = 'Volt-Var'

            return test_name
        except Exception as e:
            raise p1547Error('Error in get_test_name(): %s' % ( str(e)))

    def get_rslt_sum_col_name(self):
        """
        This getters function returns the column name for result_summary.csv
        :return:            self.rslt_sum_col_name
        """
        return self.rslt_sum_col_name

    def get_measurement_label(self, type_meas):
        """
        Sum the EUT reactive power from all phases
        :param type_meas:   Either V,P or Q
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
        else:
            meas_root = 'AC_Q'
        if self.phases == 'Single phase':
            meas_label = [meas_root+'_1']
        elif self.phases == 'Split phase':
            meas_label = [meas_root+'_1', meas_root+'_2']
        elif self.phases == 'Three phase':
            meas_label = [meas_root+'_1', meas_root+'_2', meas_root+'_3']

        return meas_label

    def get_measurement_total(self, data, type_meas, log):
        """
        Sum the EUT reactive power from all phases
        :param data:        dataset from data acquistion object
        :param type_meas:   Either V,P or Q
        :param log:         Boolean variable to disable or enable logging
        :return: Any measurements from the DAQ
        """
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
            # average value of V and F
            value = value / nb_phases

        elif type_meas == 'F':
            # No need to do data average for frequency
            value = data.get(self.get_measurement_label(type_meas)[0])

        elif type_meas == 'P':
            return abs(value)

        return value

    def get_initial(self, daq, step):
        """
        Sum the EUT reactive power from all phases
        :param daq:         data acquisition object from svpelab library
        :param step:        test procedure step letter or number (e.g "Step G")
        :return: returns a dictionnary with the timestamp, event and total EUT reactive power
        """
        # TODO : In a more sophisticated approach, get_initial['timestamp'] will come from a
        #  reliable secure thread or data acquisition timestamp
        try:
            initial = {}
            initial['timestamp'] = datetime.now()
            x = self.get_letter('x')
            y = self.get_letter('y')
            daq.data_sample()
            data = daq.data_capture_read()
            daq.sc['event'] = step
            initial['x_value'] = self.get_measurement_total(data=data, type_meas=x, log=False)
            initial['y_value'] = self.get_measurement_total(data=data, type_meas=y, log=False)
            daq.sc['%s_MEAS' % x] = initial['x_value']
            daq.sc['%s_MEAS' % y] = initial['y_value']
            daq.data_sample()

            return initial

        except Exception as e:
            raise p1547Error('Error in get_initial(): %s' % (str(e)))

    def get_tr_data(self, daq, step, tr, pwr_lvl=None, curve=None, target = None):
        """
        Get the data from a specific time response (tr) corresponding to x and y values
        of the aif (e.g. aif='VW' x == voltage and y == active power) returns a dictionnary
        but also writes in the soft channels of the DAQ system
        :param daq:         data acquisition object from svpelab library
        :param step:        test procedure step letter or number (e.g "Step G")
        :param pwr_lvl:     The input power level in p.u.
        :param curve:       The characteristic curve number
        :param target:      The target value of AIF, only use for CPF
        :return: returns a dictionnary with the timestamp, event and total EUT reactive power
        """
        tr_data = {}
        x=None
        y=None
        daq.data_sample()
        data = daq.data_capture_read()
        try :
            x = self.get_letter('x')
            y = self.get_letter('y')
            daq.sc['%s_MEAS' % x] = self.get_measurement_total(data=data, type_meas='%s' % x, log=False)
    
            if self.script_name == "CPF":
                daq.sc['%s_TARGET_MIN' % y] = self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_P * 1.5, pwr_lvl,pf=target)\
                                              -1.5*self.MSA_Q
                daq.sc['%s_TARGET_MAX' % y] = self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_P * 1.5, pwr_lvl,pf=target)\
                                              +1.5*self.MSA_Q
            elif self.script_name == "VV":
                daq.sc['%s_TARGET_MIN' % y] = self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_V * 1.5, pwr_lvl,curve) - \
                                              (self.MSA_Q * 1.5)
                daq.sc['%s_TARGET_MAX' % y] = self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_V * 1.5, pwr_lvl,curve) + (self.MSA_Q * 1.5)
            elif self.script_name == "VW":
                daq.sc['%s_TARGET_MIN'% y] = self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_V * 1.5, pwr_lvl, curve) - (
                        self.MSA_P * 1.5)
                daq.sc['%s_TARGET_MAX' % y] = self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_V * 1.5, pwr_lvl, curve) + (
                        self.MSA_P * 1.5)
            elif self.script_name == "FW":
                daq.sc['P_TARGET_MIN'] = self.get_targ(daq.sc['%s_MEAS' % x] + self.MSA_F * 1.5, pwr_lvl, curve) - (
                        self.MSA_P * 1.5)
                daq.sc['P_TARGET_MAX'] = self.get_targ(daq.sc['%s_MEAS' % x] - self.MSA_F * 1.5, pwr_lvl, curve) + (
                        self.MSA_P * 1.5)
            tr_data['%s_TARGET' % y] = target
            tr_data['%s' % x] = daq.sc['%s_MEAS' % x]
            tr_data['%s' % y] = daq.sc['%s_MEAS' % y]
            tr_data['%s_TARGET_MIN'% y] = daq.sc['%s_TARGET_MIN'% y]
            tr_data['%s_TARGET_MAX'% y] = daq.sc['%s_TARGET_MAX'% y]
            daq.sc['event'] = "{0}_TR_{1}".format(step,tr)
            daq.data_sample()
    
            return tr_data

        except Exception as e:
            raise p1547Error('Error in get_tr_data(): %s' % (str(e)))

    def get_analysis(self, initial_value, tr_1_data, tr_4_data):
        """
        This functions get the analysis results from three pass-fail criteria.

        :param initial_value:   A dictionary with measurements before a step
        :param tr_1_data:       A dictionary with measurements after one time response cycle
        :param tr_4_data:       A dictionary with measurements after four time response cycle
        :return: returns a dictionnary with pass fail criteria that will be use in the
        result_summary.csv file.
        """
        analysis = {}
        x = self.get_letter('x')
        y = self.get_letter('y')

        analysis['%s_INITIAL' % y] = initial_value['y_value']
        analysis['%s_FINAL'% y] = tr_4_data['%s'% y]
        analysis['%s_TR_1' % y] = tr_1_data['%s'% y]
        tr_diff = analysis['%s_FINAL' % y] - analysis['%s_INITIAL'% y]
        p_tr_target = ((0.9 * tr_diff) + analysis['%s_INITIAL'% y])

        if tr_diff < 0:
            if analysis['%s_TR_1' % y] <= p_tr_target:
                analysis['TR'] = 'Pass'
            else:
                analysis['TR'] = 'Fail'
        elif tr_diff >= 0:
            if analysis['%s_TR_1' % y] >= p_tr_target:
                analysis['TR'] = 'Pass'
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

        if tr_4_data['%s_TARGET_MIN' % y] <= analysis['%s_FINAL' % y] <= tr_1_data['%s_TARGET_MAX' % y]:
            analysis['%s_FINAL_TR' % y] = 'Pass'
        else:
            analysis['%s_FINAL_TR' % y] = 'Fail'

        self.ts.log('        %s(Tr_4) evaluation: %0.1f <= %0.1f <= %0.1f  [%s]' % (y,
                                                                                    tr_4_data['%s_TARGET_MIN' % y],
                                                                                    analysis['%s_FINAL' % y],
                                                                                    tr_4_data['%s_TARGET_MAX' % y],
                                                                                    analysis['%s_FINAL_TR' % y]))

        analysis['%s_TARGET'% y] = tr_4_data['%s_TARGET'% y]
        analysis['%s_TARGET_MIN'% y] = tr_4_data['%s_TARGET_MIN'% y]
        analysis['%s_TARGET_MAX'% y] = tr_4_data['%s_TARGET_MAX'% y]
        analysis['%s_MEAS' % x] =  tr_4_data['%s' % x]
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

        self.ts.log('        %s_TR [%s], TR [%s], %s_FINAL [%s]' %(y, analysis['%s_TR' % y],
                                                                   analysis['TR'],
                                                                   y, analysis['%s_FINAL_TR' % y]))
        return analysis

    def get_letter(self,letter):
        """
        A simple getter that return the x or y value of the corresponding AIF

        :param letter:   A string (x or y)
        :return: A string
        """
        if self.script_name == "VW" or self.script_name == "FW":
            y = 'P'
            if self.script_name == "VW":
                x = 'V'
            elif self.script_name == "FW":
                x = 'F'
        if self.script_name == "CPF" or self.script_name == "VV":
            y = 'Q'
            if self.script_name == "VV":
                x= 'V'
            elif self.script_name == "CPF":
                x = 'P'

        if letter == 'x':
            return x
        elif letter == 'y':
            return y
        else:
            raise p1547Error("Error in get_letter(). Try 'x' or 'y' as argument")

    def get_params(self, curve):
        return self.param[curve]

    def get_rslt_param_plot(self):

        y = self.get_letter('y')
        y2 = self.get_letter('x')
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

        y_points = '%s_TARGET,%s_MEAS' % (y,y)
        y2_points = '%s_TARGET,%s_MEAS' % (y2,y2)

        # For CPF
        if self.script_name =='CPF' :
            y_points = '{}, PF_TARGET'.format(','.join(str(x) for x in self.get_measurement_label('PF')))
            y_title = 'Power Factor'
            y2_points = '{}'.format(','.join(str(x) for x in self.get_measurement_label('I')))
            y2_title = 'Current (A)'

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

    def get_targ(self, value, pwr_lvl, curve=None, pf=None):
        p_targ = None
        if self.script_name == "FW":
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

        elif self.script_name == "VV":

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

        elif self.script_name == "CPF":
            q_value = math.sqrt(pow(value, 2) * ((1 / pow(pf, 2)) - 1))
            return round(q_value, 1)

        elif self.script_name == "VW":
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
        try:
            analysis = {}
            tr_4_data = None
            tr_4_data = None
            analysis_loop = 'start'
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

        except Exception as e:
            raise p1547Error('Error in criteria(): %s' % (str(e)))



























if __name__ == "__main__":
    pass
