"""
Copyright (c) 2020
All rights reserved.

Questions can be directed to support@sunspec.org
"""

import glob, os, time, csv, re, shutil, psutil, sys
from collections import OrderedDict
import scipy.io
try:
    import dataset
except:
    from . import dataset


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

"""
Explanation:

WFM_CHANNELS is a dictionary that defines different sets of measurement channels for waveform capture:
- Each key represents a specific test scenario (e.g. 'Generic', 'VRT', 'FRT', etc.)
- Each value is a list of channel names that will be recorded during that test
- Channel names typically include:
  * TIME: timestamp
  * AC_V_x: AC voltage measurements for phases 1,2,3
  * AC_I_x: AC current measurements for phases 1,2,3
  * Additional channels specific to each test type
"""

WFM_CHANNELS = {'Generic': ['TIME', 'AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'EXT'],
                'PhaseJump': ['TIME', 'AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'Trigger',
                              'Total_RMS_Current', 'Time_Below_80pct_Current', 'Time_Phase_Misalignment',
                              'Ph_Del_A', 'Ph_Del_B', 'Ph_Del_C'],
                'PhaseJumpOld': ['TIME', 'AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'Trigger',
                                 'Total_RMS_Current', 'Time_Below_80pct_Current', 'Time_Phase_Misalignment'],
                'VRT': ['TIME', 'AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3',
                        'AC_V_1_TARGET', 'AC_V_2_TARGET', 'AC_V_3_TARGET'],
                'FRT': ['TIME', 'AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'AC_FREQ1', 'AC_FREQ2',
                        'AC_FREQ3', 'AC_V_1_TARGET', 'AC_V_2_TARGET', 'AC_V_3_TARGET'],
                'VRT_RMS': ['TIME', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'AC_P_1', 'AC_P_2', 'AC_P_3',
                            'AC_Q_1', 'AC_Q_2', 'AC_Q_3', 'Trigger'],
                'Opal_UI_1547': ['TIME', 'TRIGGER', 'AC_I_1', 'AC_I_2', 'AC_I_3',
                                 'AC_V_1', 'AC_V_2', 'AC_V_3'],
                'IEEE1547_PCRT_RMS': ['TIME',
                                 'AC_V_1', 'AC_V_2', 'AC_V_3',
                                 'AC_I_1', 'AC_I_2', 'AC_I_3',
                                 'AC_P_1', 'AC_P_2', 'AC_P_3',
                                 'AC_Q_1', 'AC_Q_2', 'AC_Q_3',
                                 'AC_PH_CMD_1', 'AC_PH_CMD_2', 'AC_PH_CMD_3',
                                 "TRIGGER"],
                'IEEE1547_PCRT_WAV': ['TIME',
                                 'AC_V_1', 'AC_V_2', 'AC_V_3',
                                 'AC_I_1', 'AC_I_2', 'AC_I_3',
                                 'AC_PH_1', 'AC_PH_2', 'AC_PH_3',
                                 'TRIGGER'],
                'IEEE1547_VRT': ['TIME',
                                 'AC_V_1', 'AC_V_2', 'AC_V_3',
                                 'AC_I_1', 'AC_I_2', 'AC_I_3',
                                 'AC_P_1', 'AC_P_2', 'AC_P_3',
                                 'AC_Q_1', 'AC_Q_2', 'AC_Q_3',
                                 'AC_V_CMD_1', 'AC_V_CMD_2', 'AC_V_CMD_3',
                                 "TRIGGER"],
                'IEEE1547_FRT': ['TIME',
                                 'AC_V_1', 'AC_V_2', 'AC_V_3',
                                 'AC_I_1', 'AC_I_2', 'AC_I_3',
                                 'AC_FREQ_1', 'AC_FREQ_2', 'AC_FREQ_3',
                                 'TRIGGER']
                }


def add_RTLAB_API_path_to_environnement_variables():
    """
    Add the API path of currently running RTLAB to the environnment variable, if no RTLAB is running it uses the latest version installed.
    """
    RTLAB_path = get_running_RTLAB_path()
    if not RTLAB_path:
        print("WARNING: RTLAB not running.")
        RTLAB_path = get_latest_RTLAB_path()
    API_path = os.path.join(RTLAB_path,'common','python')
    sys.path.append(API_path)

def get_running_RTLAB_path():
    """
    Return the version of the RTLAB running, None if no RTLAB is not running.
    """
    for process in psutil.process_iter(['name', 'exe']):
        if process.info['name'] == 'RT-LAB.exe' or process.info['name'] == 'MetaController.exe' or process.info['name'] == 'Controller.exe':
            if process.info['exe']:
                return process.info['exe'].split('common')[0]
    return None

def get_latest_RTLAB_path():
    """
    Add path to the latest RTLAB API path on computer to the environment variable.
    """
    root_path = os.path.join("C:\\", "OPAL-RT", "RT-LAB")
    latest_version = max(os.listdir(root_path))
    return os.path.join(root_path, latest_version)

class MatlabException(Exception):
    pass


class Device(object):
    """
    Data Acquisition System (DAS) interface for OPAL-RT hardware
    
    Core interface for OPAL-RT data acquisition, providing real-time data capture,
    signal processing, and hardware integration capabilities. Handles multiple data
    formats (.mat, .csv) and interfaces with HIL systems, grid simulators, and DC
    measurement devices through RtlabApi and DataloggerApi.
    
    Methods:
        __init__(params=None): Initialize DAS device with configuration parameters
        info(): Return system information
        open(): Open communication resources
        close(): Close communication resources
        data_capture(enable=True): Enable/disable data capture
        data_read(): Read current data values
        get_acq_signals(): Get acquisition signals
        waveform_config(params): Configure waveform capture
        waveform_record(filename=None): Start waveform recording
        waveform_stop_record(): Stop waveform recording
        waveform_capture(enable=True, sleep=None): Control waveform capture
        waveform_status(): Get capture status
        waveform_force_trigger(): Force trigger event
        waveform_capture_dataset(counter=None, name_dict=None): Convert waveform to dataset
        get_signals(): Get model signals
        matlab_cmd(cmd): Execute MATLAB command
        set_dc_measurement(obj=None): Set DC measurement device
    """

    def __init__(self, params=None):
        self.params = params
        self.ts = self.params['ts']

        try:
            add_RTLAB_API_path_to_environnement_variables()
            import RtlabApi
            import DataloggerApi
            self.RtlabApi = RtlabApi
            self.DataloggerApi = DataloggerApi
        except ImportError as e:
            self.ts.log('RtlabApi Import Error. Check the version number. %s' % e)
            print('RtlabApi Import Error.')
            print(e)
        self.points = None
        self.point_indexes = []

        # general variables
        self.mat_location = ''
        self.csv_location = ''
        if self.params['wfm_chan_list'] == 'custom':
            self.wfm_channels = self.params['custom_wfm_chan_list']
        else:
            self.wfm_channels = WFM_CHANNELS.get(self.params['wfm_chan_list'])
        self.sample_interval = self.params['sample_interval']
        if not self.sample_interval:
            self.sample_interval = 50

        # optional parameters for interfacing with other SVP devices
        self.hil = self.params['hil']
        if self.hil:
            self.model_name = self.hil.rt_lab_model
            self.target_name = self.hil.target_name
        else:
            _, self.model_name = self.RtlabApi.GetCurrentModel()
        self.gridsim = self.params['gridsim']
        self.dc_measurement_device = self.params['dc_measurement_device']
        self.ts.log_debug('DAS connected to with HIL: %s, DC meas: %s, and gridsim: %s' %
                          (self.hil, self.dc_measurement_device, self.gridsim))

        # build-in recording related variables
        self.use_buildin_recording = self.params['use_buildin_recording']
        if self.use_buildin_recording:
            self.map = self.params['map']
            self.wfm_dir = self.params['wfm_dir']
            self.data_name = self.params['data_name']
            self._get_data_point_mapping()
            self.signal_to_record = self._get_signal_to_record()
            self.dc_measurement_channel = self._get_dc_measurement_channel()

        # datalogger related variables
        self.use_datalogger= self.params['use_datalogger']
        if self.use_datalogger:
            self.data_points = self.wfm_channels
            self.waveform_config()
            self.wfm_dir = os.path.join(os.path.dirname(self.hil.project_dir_path), "data")
            test_name = '_' + self.ts.name if self.ts.name else '' # useful ?
            self.csv_location = os.path.join(self.wfm_dir, self.params['Datalogger_signal_group_name']+ test_name +'.csv') # remove test name ?
            if os.path.exists(self.csv_location): os.remove(self.csv_location)
            self.initial_wfm_channel = self.wfm_channels

        # sc_capture related variables
        self.sc_capture = self.params['sc_capture']
        if self.sc_capture:  # self.sc_capture
           self._get_sc_capture_datapoint()

    def info(self):
        """
        Return system information

        :return: Opal Information
        """
        system_info = self.RtlabApi.GetTargetNodeSystemInfo(self.target_name)
        opal_rt_info = "OPAL-RT - Platform version {0} (IP address : {1})".format(system_info[1], system_info[6])
        return opal_rt_info

    def open(self):
        pass

    def close(self):
        if self.use_datalogger:
            self.signal_group.close()

    def data_capture(self, enable=False):
        if enable:
            self.hil.set_matlab_variable_value("RMS_ENABLE", 1.0)
        else:
            self.hil.set_matlab_variable_value("RMS_ENABLE", 0.0)

    def data_read(self):
        """
        Collect the data for each of the signals representing the data set

        :return: list with data aligned with the data_points order
        """

        dc_meas = None
        if self.dc_measurement_device is not None:
            try:
                dc_meas = self.dc_measurement_device.measurements_get()
            except Exception as e:
                self.ts.log_debug('Could not get data from DC Measurement Object. %s' % e)

        data = []
        try:
            if self.sc_capture :
                self.ts.log_debug('Collecting data from the console\'s acquisition signals.')
                try:
                    data = self.hil.get_acq_signals_raw(verbose=False)
                except Exception as e:
                    self.ts.log_debug('Could not get data using get_acq_signals_raw. Error: %s' % e)
            elif self.use_buildin_recording:
                if self.RtlabApi.GetModelState()[0] == self.RtlabApi.MODEL_RUNNING:
                    data = list(self.RtlabApi.GetSignalsByName(self.signal_to_record))
                else:
                    data = [None]*len(self.signal_to_record)

                if dc_meas:
                    for channel in self.dc_measurement_channel:
                        data.append(dc_meas.get(channel))

            elif self.use_datalogger:
                current_frame = self._wait_to_get_frame()
                if not current_frame: current_frame = self.signal_group.get_sub_frame()
                full_data = current_frame.get_signals_data()
                for set_of_data in full_data:
                    data.append(set_of_data[-1])
                frame_config = self.signal_group.get_frame_config()

        except Exception as e:
            self.ts.log_debug('Could not get data. Simulation likely completed. Error: %s' % e)
            self.ts.log_warning('self.data_points = %s.  Writing all Nones.' % self.data_points)
            if self.use_buildin_recording:
                data = [None]*len(self.wfm_channels)  # Return list of Nones when simulations stops.
            elif self.use_datalogger:
                if self.signal_group:
                    frame_config = self.signal_group.get_frame_config()
                    signals_to_record = frame_config.get_signals()
                    data = [None]*len(signals_to_record)
                else:
                    data = [None]*len(self.initial_wfm_channel)

            # todo: this should be fixed in das.py sometime where a None can be returned and not added to the database

        return data

    def _get_signal_to_record(self):
        """
        Returns the path of the signals to record define in self.data_points_device according the the path saved in self.data_point_map.

        """
        return tuple(self.data_point_map[channel] for channel in self.data_points_device if self.data_point_map[channel])

    def _get_dc_measurement_channel(self):
        """
        Returns the name of the DC measurement signal.
        """
        if self.dc_measurement_device:
            return [channel for channel in self.data_points_device if not self.data_point_map[channel]]

    def _wait_to_get_frame(self):
        """
        Waits until the current OPAL-RT datalogger frame is accessible and returns it.
        """
        current_time = 0
        current_frame = None
        while not current_frame and current_time <= self.sample_interval*10:
            try:
                current_frame = self.signal_group.get_sub_frame()
            except:
                time.sleep(1e-4) # sleep 0.1 ms
                current_time += 1
        return current_frame


    def get_acq_signals(self):
        """
        Get the data acquisition signals from the model

        :return: dict with "label" keys and "value" values

        """
        signals = self.RtlabApi.GetSignalsDescription()
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

    def waveform_config(self, params = None):
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
        if self.use_buildin_recording:
            self.ts.log_debug(params)
            self.mat_location = os.path.join(self.wfm_dir,self.data_name)
            mat_file_name = self.data_name.split(".mat")[0]
            self.csv_location = os.path.join(self.wfm_dir,f'{mat_file_name}_temp.csv')

        if self.use_datalogger:
            status, _ = self.RtlabApi.GetModelState()
            if status != self.RtlabApi.MODEL_RUNNING and status != self.RtlabApi.MODEL_PAUSED:
                self.hil.config() # the model needs to be loaded to connect to the signal group
                self._get_datalogger_signal_group()
                if self.signal_group:
                    sample_interval = self.sample_interval if self.sample_interval else 50
                    frame_size = int(sample_interval*1e6/100) # 1% of sample time, it gives the least deviation from the desired sampling time
                    self._config_datalogger_frame(frame_size)

    def _get_datalogger_signal_group(self):
        """
        Get the datalogger signal group according to the name given by the user. If it is not available the first signal groups of the model will be taken instead.

        Return: None, withe into self.signal_group instead
        """
        try:
            _, _, _, _, _, _, IP = self.RtlabApi.GetTargetNodeSystemInfo(self.target_name)
            self.signal_group = self.DataloggerApi.SignalGroup(str(IP), self.params['Datalogger_signal_group_name'])
        except Exception as e: # if we cannot connect to the signal group with its name, we take the first available if any.
            self.ts.log_warning(e)
            try:
                signal_groups_available = self.DataloggerApi.get_signal_groups_info(self.target_name)
                if signal_groups_available:
                    self.ts.log_warning('Taking available signal group')
                    self.signal_group = signal_groups_available[0]
                else:
                    self.ts.log_warning('No signal group found')
                    self.signal_group = None
            except:
                self.ts.log_warning('No signal group found')
                self.signal_group = None

    def _config_datalogger_frame(self, frame_size):
        """
        Configure the frame of the datalogger signal group with the given frame size and the signals from self.data_points.

        return: None
        """
        frame_config = self.DataloggerApi.FrameConfig()
        frame_config.set_signals(tuple(self._get_datalogger_signal_list()))
        frame_config.set_frame_size(frame_size)
        step_size = int(self.RtlabApi.GetTimeInfo()[0]*1e9) # will not work if is it not the time step
        frame_config.set_step_count_from_duration(frame_size, step_size)
        frame_config.set_step_time_ns(step_size)
        self.signal_group.configure_frame(frame_config)
       
    def _get_datalogger_signal_list(self):
        """
        Get the list of signal paths to record according to the signal names from self.data_points based on the signal manually set to be recorded by the user.

        return: (list of string) list of signal paths
        """
        ordered_selected_signals_list = []
        list_signals_available = self.signal_group.get_signals_info()
        for signal_name in self.data_points:
            for signal_information in list_signals_available:
                if signal_information.get_alias() == signal_name or signal_information.get_label() == signal_name or signal_name in signal_information.get_source() \
                      or (signal_name == 'TIME' and 'Clock' in signal_information.get_source()):
                    ordered_selected_signals_list.append(signal_information.get_source())
                    break
        return ordered_selected_signals_list

    def waveform_record(self, filename=None):
        """
        Starts OPAL-RT datalogger file recording. If filename is given, the recording will be save with this file name.
        """
        if self.use_datalogger:
            if filename:
                self.signal_group.start_recording(filename)
            else:
                self.signal_group.start_recording()

    def waveform_stop_record(self):
        """
        Stops OPAL-RT datalogger file recording.
        """
        if self.use_datalogger:
            self.signal_group.stop_recording()


    def waveform_capture(self, enable=False, sleep=None):
        """
        Enable/disable waveform capture.
        """
        if enable:
            self.hil.set_matlab_variable_value("WAV_ENABLE", 1.0)
        else:
            self.hil.set_matlab_variable_value("WAV_ENABLE", 0.0)

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

    def waveform_capture_dataset(self, counter=None, name_dict=None):
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

        if self.use_buildin_recording:
            for results_file_path in glob.glob(os.path.join(self.wfm_dir, self.data_name.split('.mat')[0]+"*.mat")):
                mat_data = scipy.io.loadmat(results_file_path)
                keys = [key for key in mat_data.keys() if not key.startswith('__')]
                # Check if there is at least one valid key
                if not keys:
                    raise ValueError(f"No valid keys found in the file {results_file_path}.")
                signal_data = mat_data[keys[0]]
                # create the dataset
                size = min(len(self.wfm_channels),len(signal_data))
                ds = dataset.Dataset(points=self.wfm_channels[:size], data=signal_data.tolist()[:size], ts=self.ts)
                datasets.append(ds)

        if self.use_datalogger:
            from opal.convert.file_type import FileType
            status, _ = self.RtlabApi.GetModelState()
            if status == self.RtlabApi.MODEL_RUNNING or status == self.RtlabApi.MODEL_PAUSED:
                self.signal_group.stop_recording()
            recording_file_name = glob.glob(os.path.join(os.path.dirname(self.hil.project_dir_path),'data', '*.oprec'))[-1]
            signal_group_file_streaming = self.DataloggerApi.SignalGroup(recording_file_name)
            signal_group_file_streaming.save_as(FileType.csv, self.csv_location)
            self._clean_csv_from_datalogger(self.csv_location, self.wfm_channels)
            ds = dataset.Dataset(ts=self.ts)
            ds.from_csv(filename=self.csv_location)
            datasets.append(ds)
            if self.test_name != '' and name_dict:
                test_number = int(re.findall(r'\.(.*?)\.' , os.path.basename(self.csv_location))[0])
                new_name = name_dict[test_number] + '.csv'
                shutil.move(self.csv_location, self.ts.result_file_path('') + new_name)

        return datasets


    def get_signals(self):
        """
        Get the signals from the model

        :return: list of parameter tuples with (signalID, path, label, value)
        """
        # (signalType, signalId, path, label, reserved, readonly, value) = self.RtlabApi.GetSignalsDescription()
        signal_parameters = self.RtlabApi.GetSignalsDescription()
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
        """"
        Execute a Matlab command throught the RT-LAB API."""
        try:
            result = self.RtlabApi.ExecuteMatlabCmd(cmd)
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

    def _get_data_point_mapping(self):
        """
        Creates the data point mapping.

        Return: None but creates:
            - self.data_point_map (dict) containing the signal paths
            - self.data_point (list) containing the available signals in data_point_map
        """
        # Mapping from the  channels to be captured and the names that are used in the Opal environment
        if self.map == 'Opal_Phase_Jump':
            self.data_point_map = self._Opal_Phase_Jump_mapping()

        elif self.map == 'Opal_Phase_Jump_Realign':
            self.data_point_map = self._Opal_Phase_jum_Realign_mapping()

        elif self.map == 'Ekhi':
            self.data_point_map = self._Ekhi_mapping()

        elif self.map == 'Opal_Fast_1547':
            self.data_point_map = self._Opal_fast_1547_mapping()

        elif self.map == 'PHIL_testing':
            self.data_point_map = self._PHIL_testing_mapping()

        elif self.map == 'csv':
            self.data_point_map = self._get_data_points_from_csv(self.params['mapping_csv_path'])

        elif self.map == 'Aliases':
            self.data_point_map = self._get_data_points_from_Aliases()

        elif self.map == 'Search IEEE_1547_TESTING subsystem':
            self.data_point_map = self._get_data_points_from_searching_model()

        self.data_points = list(self.data_point_map.keys())
        self.data_points_device = list(self.data_point_map.keys())

    def _get_data_points_from_csv(self, mapping_csv_path):
        """
        Read the given csv and extract the data points.

        Parameter:
            - mapping_csv_path: (string) path to the csv containing the mapping information

        It is assumed the csv follows the format:
        first signal name, first signal path
        second signal name, second signal path

        Return: (ordered dict) signal paths in the format \{signal_name: signal_path\}
        """
        data_point_map = OrderedDict()
        try:
            import csv
            with open(mapping_csv_path) as csvfile:
                content = csv.reader(csvfile)
                for row in content:
                    data_point_map[row[0]] = row[1] if row[1] != 'None' else None
        except Exception as e:
            self.ts.log_error('Could not read mapping csv because of error %s'%e)
        return data_point_map

    def _get_data_points_from_Aliases(self):
        """
        Get the model aliases and add their path to the data points if they refer to a signal.

        Return: (ordered dict) signal paths in the format \{signal_name: signal_path\}
        """
        all_alias_info = self.RtlabApi.GetAliasDescription('*')
        if not all_alias_info:
            all_alias_info = self.RtlabApi.GetAliasDescription2017('*')
        data_point_map = OrderedDict()
        for (aliasName, referencePath,refType, _, _, _) in all_alias_info:
            if refType == self.RtlabApi.OP_TYPE_SIGNAL:
                data_point_map[aliasName] = referencePath
        return data_point_map


    def _get_data_points_from_searching_model(self):
        """
        This fonction will get the sensor mapping by searching the simulink model for composent with the waveform channel names.
        If the channel is 'TIME' the script will look for a block named Clock and use the mapping path_to_clock/port1.
        For all the other channels the script will look for a block with the channel name and use the mapping path_to_block/port1.
        This fonctionnality requires to use Matlab:
            - if Matlab is not opened, the script will open then close it;
            - if Matlab is opened, the working directory will change for the model directory.
        This function was tested with Matlab 2019b other version of matlab might lead to errors.

        Return: (ordered dict) signal paths in the format \{signal_name: signal_path\}
        """
        signal_netlist_path = os.path.join(self.hil.rt_lab_model_dir, 'Opcommon', self.hil.rt_lab_model + '.signal')
        IEEE_1547_TESTING_signal_path_list = []
        with open(signal_netlist_path) as signal_netlist:
            signal_netlist.readline() # skipping the first line
            signal_line = signal_netlist.readline()
            while '=' in signal_line:
                if 'IEEE_1547_TESTING' in signal_line:
                    IEEE_1547_TESTING_signal_path_list.append(signal_line.split('|')[0].split('=')[-1])
                signal_line = signal_netlist.readline()

        data_point_map = OrderedDict()
        for channel_name in self.wfm_channels:
                data_point_map[channel_name] = None
                for signal_path in IEEE_1547_TESTING_signal_path_list:
                    if channel_name in signal_path  or (channel_name == 'TIME' and 'IEEE_1547_TESTING/Clock' in signal_path):
                        data_point_map[channel_name] = signal_path
                        continue

        return data_point_map


    def _Opal_Phase_Jump_mapping(self):
        """
        Create the signal mapping for the phase jump model.

        Return: (ordered dict) signal paths in the format \{signal_name: signal_path\}
        """
        return OrderedDict({  # data point : analog channel name
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

    def _Opal_Phase_jum_Realign_mapping(self):
        """
        Create the signal mapping for the phase jump realigned model.

        Return: (ordered dict) signal paths in the format \{signal_name: signal_path\}
        """
        return OrderedDict({  # data point : analog channel name
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

    def _Ekhi_mapping(self):
        """
        Create the signal mapping for the Ekhi model.

        Return: (ordered dict) signal paths in the format \{signal_name: signal_path\}
        """
        return OrderedDict({  # data point : analog channel name
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

    def _Opal_fast_1547_mapping(self):
        """
        Create the signal mapping for the fast IEEE 1547 model.

        Return: (ordered dict) signal paths in the format \{signal_name: signal_path\}
        """
        return OrderedDict({  # data point : analog channel name
                'TIME': self.model_name + "/SM_Source/IEEE_1547_TESTING/Clock/port1",
                # Voltage
                'AC_VRMS_1': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_VRMS_1/port1',
                'AC_VRMS_2': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_VRMS_2/port1',
                'AC_VRMS_3': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_VRMS_3/port1',
                # Current
                'AC_IRMS_1': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_IRMS_1/port1',
                'AC_IRMS_2': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_IRMS_2/port1',
                'AC_IRMS_3': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_IRMS_3/port1',
                # Frequency
                'AC_FREQ_1': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_FREQ/port1',
                'AC_FREQ_2': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_FREQ/port1',
                'AC_FREQ_3': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_FREQ/port1',
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
                'AC_PF_3': self.model_name + '/SM_Source/IEEE_1547_TESTING/SignalConditionning/AC_PF_3/port1'})

                # TODO : As some point this will be read it from HIL
                # 'DC_V': None,
                # 'DC_I': None,
                # 'DC_P': None})
    def _PHIL_testing_mapping(self):
        """
        Create the signal mapping for the fast PHIL testing model.

        Return: (ordered dict) signal paths in the format \{signal_name: signal_path\}
        """
        return OrderedDict({  # data point : analog channel name
                'TIME': self.model_name + "/SM_Source/Control/Clock/port1",
                # Voltage
                'AC_VRMS_1': self.model_name + '/SM_Source/Control/SignalConditioning/AC_VRMS_1/port1',
                'AC_VRMS_2': self.model_name + '/SM_Source/Control/SignalConditioning/AC_VRMS_2/port1',
                'AC_VRMS_3': self.model_name + '/SM_Source/Control/SignalConditioning/AC_VRMS_3/port1',
                # Current
                'AC_IRMS_1': self.model_name + '/SM_Source/Control/SignalConditioning/AC_IRMS_1/port1',
                'AC_IRMS_2': self.model_name + '/SM_Source/Control/SignalConditioning/AC_IRMS_2/port1',
                'AC_IRMS_3': self.model_name + '/SM_Source/Control/SignalConditioning/AC_IRMS_3/port1',
                # Frequency
                'AC_FREQ_1': self.model_name + '/SM_Source/Control/SignalConditioning/AC_FREQ/port1',
                'AC_FREQ_2': self.model_name + '/SM_Source/Control/SignalConditioning/AC_FREQ/port1',
                'AC_FREQ_3': self.model_name + '/SM_Source/Control/SignalConditioning/AC_FREQ/port1',
                # Active Power
                'AC_P_1': self.model_name + '/SM_Source/Control/SignalConditioning/AC_P_1/port1',
                'AC_P_2': self.model_name + '/SM_Source/Control/SignalConditioning/AC_P_2/port1',
                'AC_P_3': self.model_name + '/SM_Source/Control/SignalConditioning/AC_P_3/port1',
                # Reactive Power
                'AC_Q_1': self.model_name + '/SM_Source/Control/SignalConditioning/AC_Q_1/port1',
                'AC_Q_2': self.model_name + '/SM_Source/Control/SignalConditioning/AC_Q_2/port1',
                'AC_Q_3': self.model_name + '/SM_Source/Control/SignalConditioning/AC_Q_3/port1',
                # Apparent Power
                'AC_S_1': self.model_name + '/SM_Source/Control/SignalConditioning/AC_S_1/port1',
                'AC_S_2': self.model_name + '/SM_Source/Control/SignalConditioning/AC_S_2/port1',
                'AC_S_3': self.model_name + '/SM_Source/Control/SignalConditioning/AC_S_3/port1',
                # Power Factor
                'AC_PF_1': self.model_name + '/SM_Source/Control/SignalConditioning/AC_PF_1/port1',
                'AC_PF_2': self.model_name + '/SM_Source/Control/SignalConditioning/AC_PF_2/port1',
                'AC_PF_3': self.model_name + '/SM_Source/Control/SignalConditioning/AC_PF_3/port1'})

                # TODO : As some point this will be read it from HIL
                # 'DC_V': None,
                # 'DC_I': None,
                # 'DC_P': None})

    def _get_sc_capture_datapoint(self):
        """
        For data capture from data acquisition signals in the SC_console
        """
        self.opal_map_ui = OrderedDict()
        if self.hil is not None:  # Populate dictionary with Opal-RT names and labels
            acq_sigs = self.hil.get_acq_signals(verbose=False)  # get tuple of acq channels (signalId, label, value)
            for i in range(len(list(acq_sigs))):
                label = acq_sigs[i][1].rsplit('.', 1)[-1]
                self.opal_map_ui[label] = acq_sigs[i][1]

        # Replace Opal-RT keys in the dataset with SVP keys
        self.data_points = list(self.opal_map_ui.keys())
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


    def _clean_csv_from_datalogger(self, file_path, signal_name):
        """
        This function cleans a CSV file generated by a datalogger according to the following rules:
        1. It retains only the columns whose header contains a '/' symbol, and the second-to-last part of the
        header (split by '/') is present in the provided 'signal_name' list.
        2. It renames the selected columns using the second-to-last part of the header as the new column name.
        3. It retains the first column as 'TIME' and removes any rows that contain the substring "_F64".
        4. The modified CSV is saved to a temporary file, which is then used to replace the original CSV file.

        Parameters:
        - file_path: The path to the original CSV file.
        - signal_name: A list of valid signal names to retain in the CSV, based on the second-to-last part of the header.

        Returns:
        None. The function modifies the CSV file in place.
        """
        # Temporary file path to store the modified content
        temp_file_path = file_path[:-4]+'_temp.csv'

        # Open the original CSV file and the temporary file
        with open(file_path, mode='r') as infile, open(temp_file_path, mode='w', newline='') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            # select and rename the header
            header = next(reader)
            columns_to_keep = {i: name.split('/')[-2] for i, name in enumerate(header) if '/'in name and name.split('/')[-2] in signal_name}
            new_header = ['TIME'] + [columns_to_keep[i] for i in sorted(columns_to_keep.keys())]
            writer.writerow(new_header)
            # Iterate over the rest of the rows and skip rows that contain "_F64"
            for row in reader:
                if any("_F64" in cell for cell in row):
                    continue
                filtered_row = [row[0]] + [row[i] for i in sorted(columns_to_keep.keys())]
                writer.writerow(filtered_row)

        # Replace the original file with the modified one
        os.replace(temp_file_path, file_path)

if __name__ == "__main__":
    pass