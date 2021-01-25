"""
Copyright (c) 2020
All rights reserved.

Questions can be directed to support@sunspec.org
"""

import time
import traceback
import glob
from . import waveform
from . import dataset
import sys
import glob, os
from collections import OrderedDict

try:
    sys.path.insert(0, "C://OPAL-RT//RT-LAB//2020.1//common//python")
    import RtlabApi
except Exception as e:
    print(('Opal RT-Lab API not installed. %s' % e))

# data_points = [  # 3 phase
#     'TIME',
#     'DC_V',
#     'DC_I',
#     'AC_VRMS_1',
#     'AC_VRMS_2',
#     'AC_VRMS_3',
#     'AC_IRMS_1',
#     'AC_IRMS_2',
#     'AC_IRMS_3',
#     'DC_P',
#     'AC_S_1',
#     'AC_S_2',
#     'AC_S_3',
#     'AC_P_1',
#     'AC_P_2',
#     'AC_P_3',
#     'AC_Q_1',
#     'AC_Q_2',
#     'AC_Q_3',
#     'AC_FREQ_1',
#     'AC_FREQ_2',
#     'AC_FREQ_3',
#     'AC_PF_1',
#     'AC_PF_2',
#     'AC_PF_3',
#     'TRIG',
#     'TRIG_GRID'
# ]

# Channels to be captured during the waveform capture
# Todo : This should be provided by the IEEE 1547 library

WFM_CHANNELS = {'Generic': ['TIME', 'AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'EXT'],
                'PhaseJump': ['TIME', 'AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'Trigger',
                              'Total_RMS_Current', 'Time_Below_80pct_Current', 'Time_Phase_Misalignment',
                              'Ph_Del_A', 'Ph_Del_B', 'Ph_Del_C'],
                'PhaseJumpOld': ['TIME', 'AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'Trigger',
                                 'Total_RMS_Current', 'Time_Below_80pct_Current', 'Time_Phase_Misalignment'],
                'VRT': ['TIME', 'AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3',
                        'AC_V_1_TARGET', 'AC_V_2_TARGET', 'AC_V_3_TARGET'],
                'FRT': ['TIME', 'AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3',
                        'AC_V_1_TARGET', 'AC_V_2_TARGET', 'AC_V_3_TARGET'],
                'VRT_RMS': ['TIME', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'AC_P_1', 'AC_P_2', 'AC_P_3',
                            'AC_Q_1', 'AC_Q_2', 'AC_Q_3', 'Trigger'],
                'Opal_UI_1547': ['TIME', 'TRIGGER', 'AC_I_1', 'AC_I_2', 'AC_I_3',
                                 'AC_V_1', 'AC_V_2', 'AC_V_3'],
                'IEEE1547_VRT': ['TIME',
                                 'AC_V_1', 'AC_V_2', 'AC_V_3',
                                 'AC_I_1', 'AC_I_2', 'AC_I_3',
                                 'AC_P_1', 'AC_P_2', 'AC_P_3',
                                 'AC_Q_1', 'AC_Q_2', 'AC_Q_3',
                                 'AC_V_CMD_1', 'AC_V_CMD_2', 'AC_V_CMD_3',
                                 "TRIGGER"]
                }


class MatlabException(Exception):
    pass


class Device(object):

    def __init__(self, params=None):
        self.params = params
        self.points = None
        self.point_indexes = []

        self.ts = self.params['ts']
        self.map = self.params['map']
        self.sc_capture = self.params['sc_capture']
        self.sample_interval = self.params['sample_interval']
        self.wfm_dir = self.params['wfm_dir']
        self.data_name = self.params['data_name']
        self.dc_measurement_device = None
        # _, self.model_name = RtlabApi.GetCurrentModel()

        self.mat_location = ''
        self.csv_location = ''


        # optional parameters for interfacing with other SVP devices
        self.hil = self.params['hil']
        self.model_name = self.hil.rt_lab_model
        self.target_name = self.hil.target_name

        self.gridsim = self.params['gridsim']
        self.dc_measurement_device = self.params['dc_measurement_device']

        self.ts.log_debug('DAS connected to with HIL: %s, DC meas: %s, and gridsim: %s' %
                          (self.hil, self.dc_measurement_device, self.gridsim))

        # TODO: All this could be replaced with Alias manipulations.
        if self.sc_capture == 'No':
            # Mapping from the  channels to be captured and the names that are used in the Opal environment
            self.opal_map_phase_jump = OrderedDict({  # data point : analog channel name
                'TIME': self.model_name + '/SM_Source/Clock1/port1',
                'AC_VRMS_1': self.model_name + '/SM_Source/AC_VRMS_1/Switch/port1',
                'AC_VRMS_2': self.model_name + '/SM_Source/AC_VRMS_2/Switch/port1',
                'AC_VRMS_3': self.model_name + '/SM_Source/AC_VRMS_3/Switch/port1',
                'AC_IRMS_1': self.model_name + '/SM_Source/AC_IRMS_1/Switch/port1',
                'AC_IRMS_2': self.model_name + '/SM_Source/AC_IRMS_2/Switch/port1',
                'AC_IRMS_3': self.model_name + '/SM_Source/AC_IRMS_3/Switch/port1',
                'AC_P_1': self.model_name + '/SM_Source/AC_P_1/port1(2)',
                'AC_P_2': self.model_name + '/SM_Source/AC_P_2/port1(2)',
                'AC_P_3': self.model_name + '/SM_Source/AC_P_3/port1(2)',
                'AC_Q_1': self.model_name + '/SM_Source/AC_Q_1/port1(2)',
                'AC_Q_2': self.model_name + '/SM_Source/AC_Q_2/port1(2)',
                'AC_Q_3': self.model_name + '/SM_Source/AC_Q_3/port1(2)',
                'AC_S_1': self.model_name + '/SM_Source/AC_S_1/port1(2)',
                'AC_S_2': self.model_name + '/SM_Source/AC_S_2/port1(2)',
                'AC_S_3': self.model_name + '/SM_Source/AC_S_3/port1(2)',
                'AC_PF_1': self.model_name + '/SM_Source/AC_PF_3/port1(2)',
                'AC_PF_2': self.model_name + '/SM_Source/AC_PF_2/port1(2)',
                'AC_PF_3': self.model_name + '/SM_Source/AC_PF_3/port1(2)',
                'AC_FREQ_1': self.model_name + '/SM_Source/AC_FREQ_1/port1',
                'AC_FREQ_2': self.model_name + '/SM_Source/AC_FREQ_2/port1',
                'AC_FREQ_3': self.model_name + '/SM_Source/AC_FREQ_3/port1',
                'DC_V': None,
                'DC_I': None,
                'DC_P': None,
                'TRIG': self.model_name + '/SM_Source/Switch5/port1',
                'TRIG_GRID': self.model_name + '/SM_Source/Switch5/port1'})

            self.opal_map_phase_jump_w_phase_realign = OrderedDict({  # data point : analog channel name
                'TIME': self.model_name + '/SM_Source/Clock1/port1',
                'AC_VRMS_1': self.model_name + '/SM_Source/AC_VRMS_1/Switch/port1',
                'AC_VRMS_2': self.model_name + '/SM_Source/AC_VRMS_2/Switch/port1',
                'AC_VRMS_3': self.model_name + '/SM_Source/AC_VRMS_3/Switch/port1',
                'AC_IRMS_1': self.model_name + '/SM_Source/AC_IRMS_1/Switch/port1',
                'AC_IRMS_2': self.model_name + '/SM_Source/AC_IRMS_2/Switch/port1',
                'AC_IRMS_3': self.model_name + '/SM_Source/AC_IRMS_3/Switch/port1',
                'AC_P_1': self.model_name + '/SM_Source/AC_P_1/port1(2)',
                'AC_P_2': self.model_name + '/SM_Source/AC_P_2/port1(2)',
                'AC_P_3': self.model_name + '/SM_Source/AC_P_3/port1(2)',
                'AC_Q_1': self.model_name + '/SM_Source/AC_Q_1/port1(2)',
                'AC_Q_2': self.model_name + '/SM_Source/AC_Q_2/port1(2)',
                'AC_Q_3': self.model_name + '/SM_Source/AC_Q_3/port1(2)',
                'AC_S_1': self.model_name + '/SM_Source/AC_S_1/port1(2)',
                'AC_S_2': self.model_name + '/SM_Source/AC_S_2/port1(2)',
                'AC_S_3': self.model_name + '/SM_Source/AC_S_3/port1(2)',
                'AC_PF_1': self.model_name + '/SM_Source/AC_PF_3/port1(2)',
                'AC_PF_2': self.model_name + '/SM_Source/AC_PF_2/port1(2)',
                'AC_PF_3': self.model_name + '/SM_Source/AC_PF_3/port1(2)',
                'AC_FREQ_1': self.model_name + '/SM_Source/AC_FREQ_1/port1',
                'AC_FREQ_2': self.model_name + '/SM_Source/AC_FREQ_2/port1',
                'AC_FREQ_3': self.model_name + '/SM_Source/AC_FREQ_3/port1',
                'DC_V': None,
                'DC_I': None,
                'DC_P': None,
                'TRIG': self.model_name + '/SM_Source/Switch5/port1',
                'TRIG_GRID': self.model_name + '/SM_Source/Switch5/port1',
                'T_Phase_Realign': self.model_name + '/SM_Source/T_Phase_Realign/port1',
                'T_Curr_80': self.model_name + '/SM_Source/T_Curr_80/port1'})

            self.opal_map_ekhi = OrderedDict({  # data point : analog channel name
                'TIME': self.model_name + '/SM_LOHO13/Dynamic Load Landfill/Clock1/port1',
                'IED2_V_1': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(1)',
                'IED2_V_2': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(3)',
                'IED2_V_3': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(5)',
                'IED2_I_1': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(7)',
                'IED2_I_2': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(9)',
                'IED2_I_3': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(11)',
                'IED2_Frequency': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(13)',
                'IED5_V_1': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(15)',
                'IED5_V_2': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(17)',
                'IED5_V_3': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(19)',
                'IED5_I_1': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(21)',
                'IED5_I_2': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(23)',
                'IED5_I_3': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(25)',
                'IED5_Frequency': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(27)',
                'IED9_V_1': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(29)',
                'IED9_V_2': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(31)',
                'IED9_V_3': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(33)',
                'IED9_I_1': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(35)',
                'IED9_I_2': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(37)',
                'IED9_I_3': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(39)',
                'IED9_Frequency': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(41)',
                'IED13_V_1': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(43)',
                'IED13_V_2': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(45)',
                'IED13_V_3': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(47)',
                'IED13_I_1': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(49)',
                'IED13_I_2': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(51)',
                'IED13_I_3': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(53)',
                'IED13_Frequency': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(55)',
                'IED17_V_1': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(57)',
                'IED17_V_2': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(59)',
                'IED17_V_3': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(61)',
                'IED17_I_1': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(63)',
                'IED17_I_2': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(65)',
                'IED17_I_3': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(67)',
                'IED17_Frequency': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(69)',
                'GPS_YEAR': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(71)',
                'GPS_DAY': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(72)',
                'GPS_HOUR': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(73)',
                'GPS_MIN': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(74)',
                'GPS_SEC': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(75)',
                # 'GPS_NANOSEC': self.model_name + '/SM_LOHO13/SS_PMU/SVPOUT/port1(76)',
                'DC_V': None,
                'DC_I': None,
                'DC_P': None})

            self.opal_fast_1547 = OrderedDict({  # data point : analog channel name
                'TIME': self.model_name + "/SM_Source/IEEE_1547_TESTING/Clock/port1",
                # Voltage
                'AC_VRMS_1': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_VRMS_1/Switch/port1',
                'AC_VRMS_2': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_VRMS_2/Switch/port1',
                'AC_VRMS_3': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_VRMS_3/Switch/port1',
                # Current
                'AC_IRMS_1': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_IRMS_1/Switch/port1',
                'AC_IRMS_2': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_IRMS_2/Switch/port1',
                'AC_IRMS_3': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_IRMS_3/Switch/port1',
                # Frequency
                'AC_FREQ_1': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_FREQ_1/port1',
                'AC_FREQ_2': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_FREQ_2/port1',
                'AC_FREQ_3': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_FREQ_3/port1',
                # Active Power
                'AC_P_1': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_P_1/port1',
                'AC_P_2': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_P_2/port1',
                'AC_P_3': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_P_3/port1',
                # Reactive Power
                'AC_Q_1': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_Q_1/port1',
                'AC_Q_2': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_Q_2/port1',
                'AC_Q_3': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_Q_3/port1',
                # Apparent Power
                'AC_S_1': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_S_1/port1',
                'AC_S_2': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_S_2/port1',
                'AC_S_3': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_S_3/port1',
                # Power Factor
                'AC_PF_1': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_PF_1/port1',
                'AC_PF_2': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_PF_2/port1',
                'AC_PF_3': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_PF_3/port1',

                # TODO : As some point this will be read it from HIL
                'DC_V': None,
                'DC_I': None,
                'DC_P': None})

            # Mapping from the  channels to be captured and the names that are used in the Opal environment
            opal_points_map = {
                'Opal_Phase_Jump': self.opal_map_phase_jump,  # For use with the IEEE 1547.1 Phase Jump Tests
                'Opal_Phase_Jump_Realign': self.opal_map_phase_jump_w_phase_realign,  # Phase Jump Tests with Realignment
                'Ekhi': self.opal_map_ekhi,  # For use with Ekhi
                'Opal_Fast_1547': self.opal_fast_1547,   # PCRT, VRT and FRT
                }
            self.data_point_map = opal_points_map[self.map]  # dict with the {data_point: opal signal} map

            # self.data_points will be appended with the soft channels, so keep a local version for getting device data
            self.data_points = list(opal_points_map[self.map].keys())
            self.data_points_device = list(opal_points_map[self.map].keys())

        else:  # self.sc_capture == 'Yes'
            """
            For data capture from data acquisition signals in the SC_ console
            """
            self.opal_map_ui = OrderedDict()
            if self.hil is not None:  # Populate dictionary with Opal-RT names and labels
                acq_sigs = self.hil.get_acq_signals(verbose=False)  # get tuple of acq channels (signalId, label, value)
                # self.ts.log_debug('acq_sigs: %s' % str(acq_sigs))
                for i in range(len(list(acq_sigs))):
                    label = acq_sigs[i][1].rsplit('.', 1)[-1]
                    self.opal_map_ui[label] = acq_sigs[i][1]

            # Replace Opal-RT keys in the dataset with SVP keys
            self.data_points = list(self.opal_map_ui.keys())
            # self.ts.log_debug('List: %s' % self.data_points)
            self.data_points[self.data_points.index('Utility Vph(1)')] = 'AC_VRMS_SOURCE_1'  # Utility measurements
            self.data_points[self.data_points.index('Utility Vph(2)')] = 'AC_VRMS_SOURCE_2'
            self.data_points[self.data_points.index('Utility Vph(3)')] = 'AC_VRMS_SOURCE_3'
            self.data_points[self.data_points.index('Utility Vph pu(1)')] = 'AC_VRMS_SOURCE_1_PU'  # Utility measurements
            self.data_points[self.data_points.index('Utility Vph pu(2)')] = 'AC_VRMS_SOURCE_2_PU'
            self.data_points[self.data_points.index('Utility Vph pu(3)')] = 'AC_VRMS_SOURCE_3_PU'
            self.data_points[self.data_points.index('Utility I(1)')] = 'AC_IRMS_SOURCE_1'
            self.data_points[self.data_points.index('Utility I(2)')] = 'AC_IRMS_SOURCE_2'
            self.data_points[self.data_points.index('Utility I(3)')] = 'AC_IRMS_SOURCE_3'
            self.data_points[self.data_points.index('Puti_Watts')] = 'AC_SOURCE_P'
            self.data_points[self.data_points.index('Quti_Vars')] = 'AC_SOURCE_Q'
            self.data_points[self.data_points.index('Utility Ppu')] = 'AC_SOURCE_P_PU'
            self.data_points[self.data_points.index('Utility Qpu')] = 'AC_SOURCE_Q_PU'
            self.data_points[self.data_points.index('Inv Vph(1)')] = 'AC_VRMS_1'  # Inverter measurements
            self.data_points[self.data_points.index('Inv Vph(2)')] = 'AC_VRMS_2'
            self.data_points[self.data_points.index('Inv Vph(3)')] = 'AC_VRMS_3'
            self.data_points[self.data_points.index('Inv I(1)')] = 'AC_IRMS_1'
            self.data_points[self.data_points.index('Inv I(2)')] = 'AC_IRMS_2'
            self.data_points[self.data_points.index('Inv I(3)')] = 'AC_IRMS_3'
            self.data_points[self.data_points.index('Inv Ptot')] = 'AC_P'
            self.data_points[self.data_points.index('Inv Qtot')] = 'AC_Q'
            self.data_points[self.data_points.index('Inv Freq')] = 'AC_FREQ_1'
            self.data_points[self.data_points.index('Load Vph(1)')] = 'AC_VRMS_LOAD_1'  # Load measurements
            self.data_points[self.data_points.index('Load Vph(2)')] = 'AC_VRMS_LOAD_2'
            self.data_points[self.data_points.index('Load Vph(3)')] = 'AC_VRMS_LOAD_3'
            self.data_points[self.data_points.index('Load I(1)')] = 'AC_IRMS_LOAD_1'
            self.data_points[self.data_points.index('Load I(2)')] = 'AC_IRMS_LOAD_2'
            self.data_points[self.data_points.index('Load I(3)')] = 'AC_IRMS_LOAD_3'
            self.data_points[self.data_points.index('PLoad Watts')] = 'AC_P_LOAD'
            self.data_points[self.data_points.index('QLoad Vars')] = 'AC_Q_LOAD'
            self.data_points[self.data_points.index('Load Ppu')] = 'AC_P_LOAD_PU'
            self.data_points[self.data_points.index('Load Qpu')] = 'AC_Q_LOAD_PU'

            self.data_points[self.data_points.index('Inv QFactor')] = 'QUALITY_FACTOR'

            # R
            self.data_points[self.data_points.index('IR(1)')] = 'AC_IRMS_LOAD_R_1'
            self.data_points[self.data_points.index('IR(2)')] = 'AC_IRMS_LOAD_R_2'
            self.data_points[self.data_points.index('IR(3)')] = 'AC_IRMS_LOAD_R_3'
            self.data_points[self.data_points.index('R1_P')] = 'AC_P_LOAD_R_1'  # pu
            self.data_points[self.data_points.index('R2_P')] = 'AC_P_LOAD_R_2'
            self.data_points[self.data_points.index('R3_P')] = 'AC_P_LOAD_R_3'
            self.data_points[self.data_points.index('R1_Q')] = 'AC_Q_LOAD_R_1'
            self.data_points[self.data_points.index('R2_Q')] = 'AC_Q_LOAD_R_2'
            self.data_points[self.data_points.index('R3_Q')] = 'AC_Q_LOAD_R_3'

            # L
            self.data_points[self.data_points.index('IL(1)')] = 'AC_IRMS_LOAD_L_1'
            self.data_points[self.data_points.index('IL(2)')] = 'AC_IRMS_LOAD_L_2'
            self.data_points[self.data_points.index('IL(3)')] = 'AC_IRMS_LOAD_L_3'
            self.data_points[self.data_points.index('L1_P')] = 'AC_P_LOAD_L_1'  # pu
            self.data_points[self.data_points.index('L2_P')] = 'AC_P_LOAD_L_2'
            self.data_points[self.data_points.index('L3_P')] = 'AC_P_LOAD_L_3'
            self.data_points[self.data_points.index('L1_Q')] = 'AC_Q_LOAD_L_1'
            self.data_points[self.data_points.index('L2_Q')] = 'AC_Q_LOAD_L_2'
            self.data_points[self.data_points.index('L3_Q')] = 'AC_Q_LOAD_L_3'
            self.data_points[self.data_points.index('QL pu')] = 'QL'

            # C
            self.data_points[self.data_points.index('IC(1)')] = 'AC_IRMS_LOAD_C_1'
            self.data_points[self.data_points.index('IC(2)')] = 'AC_IRMS_LOAD_C_2'
            self.data_points[self.data_points.index('IC(3)')] = 'AC_IRMS_LOAD_C_3'
            self.data_points[self.data_points.index('C1_P')] = 'AC_P_LOAD_C_1'  # pu
            self.data_points[self.data_points.index('C2_P')] = 'AC_P_LOAD_C_2'
            self.data_points[self.data_points.index('C3_P')] = 'AC_P_LOAD_C_3'
            self.data_points[self.data_points.index('C1_Q')] = 'AC_Q_LOAD_C_1'
            self.data_points[self.data_points.index('C2_Q')] = 'AC_Q_LOAD_C_2'
            self.data_points[self.data_points.index('C3_Q')] = 'AC_Q_LOAD_C_3'
            self.data_points[self.data_points.index('QC pu')] = 'QC'

            # Switch P/Q in pu
            self.data_points[self.data_points.index('S1_P_Pu')] = 'AC_P_S1_PU'
            self.data_points[self.data_points.index('S2_P_Pu')] = 'AC_P_S2_PU'
            self.data_points[self.data_points.index('S3_P_Pu')] = 'AC_P_S3_PU'
            self.data_points[self.data_points.index('S1_Q_Pu')] = 'AC_Q_S1_PU'
            self.data_points[self.data_points.index('S2_Q_Pu')] = 'AC_Q_S2_PU'
            self.data_points[self.data_points.index('S3_Q_Pu')] = 'AC_Q_S3_PU'

            # Switch P/Q in watts/vars
            self.data_points[self.data_points.index('S1_P_Watts')] = 'AC_P_S1'
            self.data_points[self.data_points.index('S2_P_Watts')] = 'AC_P_S2'
            self.data_points[self.data_points.index('S3_P_Watts')] = 'AC_P_S3'
            self.data_points[self.data_points.index('S1_Q_Vars')] = 'AC_Q_S1'
            self.data_points[self.data_points.index('S2_Q_Vars')] = 'AC_Q_S2'
            self.data_points[self.data_points.index('S3_Q_Vars')] = 'AC_Q_S3'

            self.data_points[self.data_points.index('Resistor (ohms)')] = 'R'  # RLC measurements
            self.data_points[self.data_points.index('Rint (ohms)')] = 'R_INT'
            self.data_points[self.data_points.index('Inductor (mH)')] = 'L'
            self.data_points[self.data_points.index('Capacitor (uF)')] = 'C'
            self.data_points[self.data_points.index('Freq PCC')] = 'AC_FREQ_PCC'
            self.data_points[self.data_points.index('pf_inv')] = 'AC_PF_1'

            self.data_points[self.data_points.index('Trip Time(1)')] = 'TRIP_TIME'
            self.data_points[self.data_points.index('Island Freq(1)')] = 'ISLAND_FREQ'
            self.data_points[self.data_points.index('Island Vrms(1)')] = 'ISLAND_VRMS'

            # self.ts.log_debug('data_points %s' % self.data_points)


        # After the simulation the data is stored in a .mat file. Matlab is used to convert this to a .csv file.
        # Get the svpelab directory and then add the \OpalRT\...
        self.driver_path = os.path.dirname(os.path.realpath(__file__))

        # location where opal saves the waveform data (.mat)
        # self.mat_location = self.wfm_dir + self.data_name
        # location where matlab saves the waveform data (.csv)
        # self.csv_location = self.wfm_dir + f'\{self.data_name.split(".mat")[0]}_temp.csv'
        self.wfm_channels = WFM_CHANNELS.get(self.params['wfm_chan_list'])
        self.waveform_config({"mat_file_name": self.data_name})

        # delete the old data file
        try:
            os.remove(self.csv_location)
        except Exception as e:
            # self.ts.log_warning('Could not delete old data file at %s: %s' % (self.csv_location, e))
            pass

    def info(self):
        """
        Return system information

        :return: Opal Information
        """
        system_info = RtlabApi.GetTargetNodeSystemInfo(self.target_name)
        opal_rt_info = "OPAL-RT - Platform version {0} (IP address : {1})".format(system_info[1], system_info[6])
        return opal_rt_info

    def open(self):
        pass

    def close(self):
        pass

    def data_capture(self, enable=True):
        pass

    def data_read(self):
        """
        Collect the data for each of the signals representing the data set

        :return: list with data aligned with the data_points order
        """

        dc_meas = None
        if self.dc_measurement_device is not None:
            try:
                dc_meas = self.dc_measurement_device.measurements_get()
                # if self.ts is not None:
                #     self.ts.log_debug('The DC measurements are %s' % dc_meas)
                # else:
                #     print('The DC measurements are %s' % dc_meas)
            except Exception as e:
                self.ts.log_debug('Could not get data from DC Measurement Object. %s' % e)

        data = []
        try:
            if self.sc_capture == 'Yes':
                # self.ts.log_debug('Collecting data from the console\'s aqcuisition signals.')
                try:
                    data = self.hil.get_acq_signals_raw(verbose=False)
                except Exception as e:
                    self.ts.log_debug('Could not get data using get_acq_signals_raw. Error: %s' % e)
            else:
                for chan in self.data_points_device:
                    # self.ts.log_debug('self.data_points = %s' % self.data_points)
                    signal = self.data_point_map[chan]  # get signal name associated with data name
                    # self.ts.log_debug('Chan = %s, signal = %s' % (chan, signal))
                    if signal is None:  # skip the signals that have no mapping to the simulink model

                        # search the dc measurement object for the data that isn't in the opal_points_map
                        if self.dc_measurement_device is not None:
                            dc_value = dc_meas.get(chan)  # signal = 'DC_V', 'DC_I', or 'DC_P'
                            # if self.ts is not None:
                            #     self.ts.log_debug('Setting Chan = %s to dc_value = %s' % (chan, dc_value))
                            # else:
                            #     print('Setting Chan = %s to dc_value = %s' % (chan, dc_value))
                            if dc_value is not None:
                                data.append(dc_value)
                            else:  # Channel data missing
                                # self.ts.log_debug('Appending None for data point: %s' % chan)
                                data.append(None)
                        else:  # DC Measurement Object missing

                            # self.ts.log_debug('Appending None for data point: %s' % chan)
                            data.append(None)
                        continue

                    # verify the model is running before getting the signal data.
                    status, _ = RtlabApi.GetModelState()
                    if status == RtlabApi.MODEL_RUNNING:
                        signal_value = RtlabApi.GetSignalsByName(signal)
                        # self.ts.log_warning('signal_value is %s from Opal' % signal_value)
                    else:
                        signal_value = None
                        # self.ts.log_warning('Signal_value set to None because Opal isn\'t running')

                    # self.ts.log_debug('Signal %s = %s' % (signal, signal_value))
                    # self.ts.log_warning('type(sig) %s' % type(signal_value))
                    if signal_value is not None and signal_value is not 'None':
                        data.append(signal_value)
                    else:
                        data.append(None)

        except Exception as e:
            self.ts.log_debug('Could not get data. Simulation likely completed. Error: %s' % e)
            # self.ts.log_warning('self.data_points = %s.  Writing all Nones.' % self.data_points)
            # self.ts.log_warning('self.data_points = %s.  Writing all Nones.' % self.data_points_device)
            data = [None]*len(self.data_points_device)  # Return list of Nones when simulations stops.
            # todo: this should be fixed in das.py sometime where a None can be returned and not added to the database

        return data

    def get_acq_signals(self):
        """
        Get the data acquisition signals from the model

        :return: dict with "label" keys and "value" values

        """
        signals = RtlabApi.GetSignalsDescription()
        # array of tuples: (signalType, signalId, path, label, reserved, readonly, value)
        # 0 signalType: Signal type. See OP_SIGNAL_TYPE.
        # 1 signalId: Id of the signal.
        # 2 path: Path of the signal.
        # 3 label: Label or name of the signal.
        # 4 reserved: unused?
        # 5 readonly: True when the signal is read-only.
        # 6 value: Current value of the signal.

        # ts.log_debug('Signals: %s' % signals)
        acq_signals = {}
        for sig in range(len(signals)):
            if str(signals[sig][0]) == 'OP_ACQUISITION_SIGNAL(0)':
                acq_signals[signals[sig][1]] = signals[sig][6]

        return acq_signals

    def waveform_config(self, params):
        """
        Configure waveform capture.

        params: Dictionary with following entries:
            'sample_rate' - Sample rate (samples/sec)
            'pre_trigger' - Pre-trigger time (sec)
            'post_trigger' - Post-trigger time (sec)
            'trigger_level' - Trigger level
            'trigger_cond' - Trigger condition - ['Rising_Edge', 'Falling_Edge']
            'trigger_channel' - Trigger channel - ['AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'EXT']
            'timeout' - Timeout (sec)
            'channels' - Channels to capture - ['AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'EXT']
        """

        # start_time_value = params["start_time_value"]
        # end_time_value = params["end_time_value"]
        # start_time_variable = params["start_time_variable"]
        # end_time_variable = params["end_time_variable"]
        # variables = []
        # variables.append((start_time_variable, start_time_value))
        # variables.append((end_time_variable, end_time_value))
        # self.hil.set_variables(variables)

        # self.ts.log_debug(params)
        mat_file_name = params.get("mat_file_name")
        self.data_name = mat_file_name
        self.mat_location = self.wfm_dir + mat_file_name
        self.csv_location = self.wfm_dir + f'\{mat_file_name.split(".mat")[0]}_temp.csv'

    def waveform_capture(self, enable=True, sleep=None):
        """
        Enable/disable waveform capture.
        """
        if enable:
            pass

    def waveform_status(self):
        """

        :return: str 'INACTIVE', 'ACTIVE', or 'COMPLETE'
        """
        pass

    def waveform_force_trigger(self):
        """
        Create trigger event with provided value.
        """
        pass

    def waveform_capture_dataset(self):
        """
        Convert saved waveform data into a list of datasets

        Steps:
            1. Use matlab to read in the .mat file that is saved with an OpWriteFile block in RT-Lab
            2. Use matlab to write a .csv file in the same directory with the data header and the simulation data
            3. Use python to read the .csv file and save the data as a database object

        :return: dataset
        """

        # in case multiple waveform captures are required for the test, create list of datasets
        datasets = []
        os.chdir(self.wfm_dir)
        self.ts.log_debug(f'.mat in  {self.wfm_dir,self.data_name }')

        for entry in glob.glob("*.mat"):
            if self.data_name in entry:
                self.mat_location = f'{self.wfm_dir}\{entry}'
                self.ts.log_debug(f'The model state is {self.hil.model_state()}')

                while self.hil.model_state() == "Model Resetting":
                    self.ts.log_debug('The model is still resetting. Waiting 10 sec')
                    self.ts.sleep(10)

                # Pull in saved data from the .mat files
                self.ts.log('Loading %s file in matlab...' % self.mat_location)
                m_cmd = "load('" + self.mat_location + "')"
                # self.ts.log_debug('Running matlab command: %s' % m_cmd)
                if isinstance(self.matlab_cmd(m_cmd), MatlabException):
                    self.ts.log_warning('Matlab command failed. Waiting 10 sec and retrying...')
                    self.ts.sleep(10)
                    self.matlab_cmd(m_cmd)

                # Add the header to the data in Matlab
                self.ts.log('Adding Data Header from self.wfm_channels = %s' % self.wfm_channels)
                m_cmd = "header = {" + str(self.wfm_channels)[1:-1] + "};"
                if isinstance(self.matlab_cmd(m_cmd), MatlabException):
                    self.ts.log_warning('Matlab command failed. Waiting 10 sec and retrying...')
                    self.ts.sleep(10)
                    self.matlab_cmd(m_cmd)
                self.matlab_cmd("[x, y] = size(Data);")
                self.matlab_cmd("data_w_header = cell(y+1,x);")
                self.matlab_cmd("data_w_header(1,:) = header;")
                self.matlab_cmd("data_w_header(2:y+1,:) = num2cell(Data');")

                # save as xlsx
                # m_cmd = "xlswrite(('" + self.csv_location + "'), data_w_header)"
                # self.ts.log_debug('Running matlab command: %s' % m_cmd)
                # self.ts.log_debug('Matlab: ' + self.matlab_cmd(m_cmd))

                # save the data as a csv file so it is easier to read in python
                self.ts.log('Saving the waveform data as .csv file in %s' % self.csv_location)
                m_cmd = "fid = fopen('" + self.csv_location + "', 'wt');"
                m_cmd += "if fid > 0\n"
                m_cmd += "fprintf(fid, '" + "%s,"*(len(self.wfm_channels)-1) + "%s\\n', data_w_header{1,:});\n"
                m_cmd += "for k=2:size(data_w_header, 1)\n"
                m_cmd += "fprintf(fid, '" + "%f,"*(len(self.wfm_channels)-1) + "%f\\n', data_w_header{k,:});\n"
                m_cmd += "end\n"
                m_cmd += "fclose(fid);\n"
                m_cmd += "end\n"

                # self.ts.log_debug('Matlab: ' + m_cmd)
                if self.matlab_cmd(m_cmd) == '':
                    self.ts.log_warning('Matlab command failed. Waiting 10 sec and retrying...')
                    self.ts.sleep(10)
                    self.matlab_cmd(m_cmd)

                # read csv file and convert to ds
                ds = dataset.Dataset()
                ds.from_csv(filename=self.csv_location)

                datasets.append(ds)

        return datasets

    def get_signals(self):
        """
        Get the signals from the model

        :return: list of parameter tuples with (signalID, path, label, value)
        """
        # (signalType, signalId, path, label, reserved, readonly, value) = signalInfo = RtlabApi.GetSignalsDescription()
        signal_parameters = RtlabApi.GetSignalsDescription()
        signal_params = []
        for sig in range(len(signal_parameters)):
            signal_params.append((signal_parameters[sig][1],
                                  signal_parameters[sig][2],
                                  signal_parameters[sig][3],
                                  signal_parameters[sig][6]))
            self.ts.log_debug('Signal #%s: %s [%s] = %s' % (signal_parameters[sig][1],
                                                            signal_parameters[sig][2],
                                                            signal_parameters[sig][3],
                                                            signal_parameters[sig][6]))
        return signal_params

    def matlab_cmd(self, cmd):
        try:
            result = RtlabApi.ExecuteMatlabCmd(cmd)
            return result
        except Exception as e:
            self.ts.log_warning('Cannot execute Matlab command: %s' % e)
            return MatlabException(e)

    def set_dc_measurement(self, obj=None):
        """
        DEPRECATED

        In the event that DC measurements are taken from another device (e.g., a PV simulator) please add this
        device to the das object
        :param obj: The object (e.g., pvsim) that will gather the dc measurements
        :return: None
        """

        if obj is not None:
            self.ts.log('DAS DC Measurement Device configured to be %s' % (obj.info()))
            self.dc_measurement_device = obj


if __name__ == "__main__":

    system_info = RtlabApi.GetTargetNodeSystemInfo("RTServer")
    
    projectName = os.path.abspath(r"C:\OPAL-RT\WorkspaceFOREVERYONE\1547_fast_functions\1547_fast_functions.llp")
    RtlabApi.OpenProject(projectName)
    print("The connection with '%s' is completed." % projectName)

    modelState, realTimeMode = RtlabApi.GetModelState()
    print(modelState,realTimeMode)
 





