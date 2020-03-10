"""
Copyright (c) 2020
All rights reserved.

Questions can be directed to support@sunspec.org
"""

import time
import traceback
import glob
import waveform
import dataset
import sys
import os
try:
    sys.path.insert(0, "C://OPAL-RT//RT-LAB//2019.1//common//python")
    import RtlabApi
except Exception, e:
    print('Opal RT-Lab API not installed. %s' % e)

data_points = [  # 3 phase
    'TIME',
    'DC_V',
    'DC_I',
    'AC_VRMS_1',
    'AC_VRMS_2',
    'AC_VRMS_3',
    'AC_IRMS_1',
    'AC_IRMS_2',
    'AC_IRMS_3',
    'DC_P',
    'AC_S_1',
    'AC_S_2',
    'AC_S_3',
    'AC_P_1',
    'AC_P_2',
    'AC_P_3',
    'AC_Q_1',
    'AC_Q_2',
    'AC_Q_3',
    'AC_FREQ_1',
    'AC_FREQ_2',
    'AC_FREQ_3',
    'AC_PF_1',
    'AC_PF_2',
    'AC_PF_3',
    'TRIG',
    'TRIG_GRID'
]

# Channels to be captured during the waveform capture
wfm_channels = ['TIME', 'AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'EXT']

event_map = {'Rising_Edge': 'Rising edge',
             'Rising Edge': 'Rising edge',
             'Falling_Edge': 'Falling edge',
             'Falling Edge': 'Falling edge'}


class Device(object):

    def __init__(self, params=None):
        self.params = params
        self.data_points = list(data_points)
        self.points = None
        self.point_indexes = []

        self.ts = self.params['ts']
        self.map = self.params['map']
        self.sample_interval = self.params['sample_interval']
        self.target_name = self.params['target_name']
        self.model_name = self.params['model_name']
        self.wfm_dir = self.params['wfm_dir']
        self.data_name = self.params['data_name']
        self.dc_measurement_device = None
        # _, self.model_name = RtlabApi.GetCurrentModel()

        # Mapping from the  channels to be captured and the names that are used in the Opal environment
        self.opal_map_phase_jump = {  # data point : analog channel name
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
            'TRIG_GRID': self.model_name + '/SM_Source/Switch5/port1'}

        # Mapping from the  channels to be captured and the names that are used in the Opal environment
        opal_points_map = {
            'Opal_Phase_Jump': self.opal_map_phase_jump,  # For use with the IEEE 1547.1 Phase Jump Tests
            # 'Opal_New_Map': self.new_map,  # For use with <>
        }
        self.data_point_map = opal_points_map[self.map]  # dict with the {data_point: opal signal} map

        # After the simulation the data is stored in a .mat file. Matlab is used to convert this to a .csv file.
        # Get the svpelab directory and then add the \OpalRT\...
        import os
        self.driver_path = os.path.dirname(os.path.realpath(__file__))
        # location where opal saves the waveform data (.mat)
        self.mat_location = self.driver_path + self.wfm_dir + self.data_name
        # location where matlab saves the waveform data (.csv)
        self.csv_location = self.driver_path + self.wfm_dir + 'Results.csv'

        # waveform settings
        self.wfm_sample_rate = None
        self.wfm_pre_trigger = None
        self.wfm_post_trigger = None
        self.wfm_trigger_level = None
        self.wfm_trigger_cond = None
        self.wfm_trigger_channel = None
        self.wfm_timeout = None
        self.wfm_channels = None
        self.wfm_capture_name = None
        # self.wfm_capture_name_path = r'C:\captured_signals\capture_test.mat'

        self.numberOfSamples = None
        self.triggerOffset = None
        self.decimation = 1
        self.captureSettings = None
        self.triggerSettings = None
        self.channelSettings = None

        # delete the old data file
        try:
            import os
            os.remove(self.csv_location)
        except Exception, e:
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
            except Exception, e:
                self.ts.log_debug('Could not get data from DC Measurement Object. %s' % e)

        try:
            data = []
            for chan in data_points:
                signal = self.data_point_map[chan]  # get signal name associated with data name
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

                # verify the model is runing before getting the signal data.
                status, _ = RtlabApi.GetModelState()
                if status == RtlabApi.MODEL_RUNNING:
                    signal_value = RtlabApi.GetSignalsByName(signal)
                else:
                    signal_value = None

                # self.ts.log_debug('Signal %s = %s' % (signal, signal_value))
                # self.ts.log_warning('type(sig) %s' % type(signal_value))
                if signal_value is not None and signal_value is not 'None':
                    data.append(signal_value)
                else:
                    data.append(None)
        except Exception, e:
            self.ts.log_debug('Could not get data. Simulation likely completed. %s' % e)
            data = [None]*len(data_points)  # Return list of Nones when simulations stops.
            # todo: this should be fixed in das.py sometime where a None can be returned and not added to the database

        # self.ts.log_debug('Data list %s' % data)
        return data

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
        self.wfm_sample_rate = params.get('sample_rate')
        self.wfm_pre_trigger = params.get('pre_trigger')
        self.wfm_post_trigger = params.get('post_trigger')
        self.wfm_trigger_level = params.get('trigger_level')
        self.wfm_trigger_cond = params.get('trigger_cond')
        self.wfm_trigger_channel = params.get('trigger_channel')
        self.wfm_timeout = params.get('timeout')
        self.wfm_channels = params.get('channels')  # SVP names
        pass

    def waveform_capture(self, enable=True, sleep=None):
        """
        Enable/disable waveform capture.
        """
        if enable:
            self.wfm_data = None  # used as flag in waveform_status()
            # start capture process and if everything ok, continue...
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
        for entry in os.listdir(self.driver_path + self.wfm_dir):
            # self.ts.log_debug('%s, %s, %s' % (entry, entry[-4:], entry[:8]))
            if entry[-4:] == '.mat' and entry[:8] == 'SVP_Data':
                self.mat_location = self.driver_path + self.wfm_dir + entry
                self.ts.log_debug('Processing data in the .mat file at %s' % self.mat_location)
                # Check that the data file is not still being written to
                # attempts = 5
                # while attempts > 0:
                #     import os
                #     try:
                #         os.rename(self.mat_location, self.mat_location + '.temp')
                #         os.rename(self.mat_location + '.temp', self.mat_location)
                #     except OSError:
                #         print('.mat file is still being written...')
                #     self.ts.sleep(1)
                #     attempts -= 1

                # Pull in saved data from the .mat files
                self.ts.log('Loading %s file in matlab...' % self.mat_location)
                m_cmd = "load('" + self.mat_location + "')"
                self.ts.log_debug('Running matlab command: %s' % m_cmd)
                # self.ts.log_debug('Matlab: ' + self.matlab_cmd(m_cmd))
                self.matlab_cmd(m_cmd)

                # Add the header to the data in Matlab
                self.ts.log('Adding Data Header')
                m_cmd = "header = {" + str(wfm_channels)[1:-1] + "};"
                '''
                self.ts.log_debug('Matlab: ' + self.matlab_cmd(m_cmd))
                self.ts.log_debug('Matlab: ' + self.matlab_cmd("[x, y] = size(Data);"))
                self.ts.log_debug('Matlab: ' + self.matlab_cmd("data_w_header = cell(y+1,x);"))
                self.ts.log_debug('Matlab: ' + self.matlab_cmd("data_w_header(1,:) = header;"))
                self.ts.log_debug('Matlab: ' + self.matlab_cmd("data_w_header(2:y+1,:) = num2cell(Data');"))
                '''
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
                m_cmd += "fprintf(fid, '" + "%s,"*(len(wfm_channels)-1) + "%s\\n', data_w_header{1,:});\n"
                m_cmd += "for k=2:size(data_w_header, 1)\n"
                m_cmd += "fprintf(fid, '" + "%f,"*(len(wfm_channels)-1) + "%f\\n', data_w_header{k,:});\n"
                m_cmd += "end\n"
                m_cmd += "fclose(fid);\n"
                m_cmd += "end\n"
                print(m_cmd)
                # self.ts.log_debug('Matlab: ' + self.matlab_cmd(m_cmd))
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
        except Exception, e:
            self.ts.log_warning('Cannot execute Matlab command: %s' % e)
            return ''

    def set_dc_measurement(self, obj=None):
        """
        In the event that DC measurements are taken from another device (e.g., a PV simulator) please add this
        device to the das object
        :param obj: The object (e.g., pvsim) that will gather the dc measurements
        :return: None
        """

        if obj is not None:
            self.ts.log('DAS DC Measurement Device configured to be %s' % (obj.info()))
            self.dc_measurement_device = obj


if __name__ == "__main__":

    system_info = RtlabApi.GetTargetNodeSystemInfo("Target_3")
    for i in range(len(system_info)):
        print(system_info[i])
    print("OPAL-RT - Platform version {0} (IP address : {1})".format(system_info[1], system_info[6]))

    # Pull in saved data from the .mat files
    print('Loading file in matlab...')
    m_cmd = "load('C:\\Users\\DETLDAQ\\OPAL-RT\\RT-LABv2019.1_Workspace\\IEEE_1547.1_Phase_Jump\\models\\" \
            "Phase_Jump_A_B_A\\phase_jump_a_b_a_sm_source\\OpREDHAWKtarget\\SVP_Data.mat')"
    print(RtlabApi.ExecuteMatlabCmd(m_cmd))

    print('Adding Data Header')
    m_cmd = "header = {" + str(wfm_channels)[1:-1] + "};"
    print(m_cmd)
    print(RtlabApi.ExecuteMatlabCmd(m_cmd))
    print(RtlabApi.ExecuteMatlabCmd("[x, y] = size(Data);"))
    print(RtlabApi.ExecuteMatlabCmd("data_w_header = cell(y+1,x);"))
    print(RtlabApi.ExecuteMatlabCmd("data_w_header(1,:) = header;"))
    print(RtlabApi.ExecuteMatlabCmd("data_w_header(2:y+1,:) = num2cell(Data');"))

    csv_location = 'C:\\Users\\DETLDAQ\\OPAL-RT\\RT-LABv2019.1_Workspace\\IEEE_1547.1_Phase_Jump\\models\\' \
            'Phase_Jump_A_B_A\\phase_jump_a_b_a_sm_source\\OpREDHAWKtarget\\Results.csv'
    print('Saving the waveform data as .csv file in %s' % csv_location)
    # m_cmd = "csvwrite(('" + csv_location + "'), data_w_header)"
    # print(m_cmd)
    # RtlabApi.ExecuteMatlabCmd(m_cmd)

    m_cmd = "fid = fopen('" + csv_location + "', 'wt');\n"
    m_cmd += "if fid > 0\n"
    m_cmd += "fprintf(fid, '" + "%s," * (len(wfm_channels) - 1) + "%s\\n', data_w_header{1,:});\n"
    m_cmd += "for k=2:size(data_w_header, 1)\n"
    m_cmd += "fprintf(fid, '" + "%f," * (len(wfm_channels) - 1) + "%f\\n', data_w_header{k,:});\n"
    m_cmd += "end\n"
    m_cmd += "fclose(fid);\n"
    m_cmd += "end\n"
    print(m_cmd)
    print('Matlab: ' + RtlabApi.ExecuteMatlabCmd(m_cmd))

    ds = dataset.Dataset()
    ds.from_csv(filename=csv_location)
    print(ds.data)
    print(ds.points)

    # import csv
    # time_data = []
    # v_data = []
    # with open(csv_location) as csvfile:
    #     reader = csv.DictReader(csvfile)
    #     for row in reader:
    #         time_data.append(float(row['TIME']))
    #         v_data.append(float(row['AC_V_1']))
    #
    # print(time_data)
    # print(v_data)
    #
    # import matplotlib.pyplot as plt
    # plt.figure(1)
    # plt.plot(time_data, v_data)
    # plt.show()




