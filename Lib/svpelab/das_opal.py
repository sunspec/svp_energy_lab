"""

All rights reserved.

Questions can be directed to support@sunspec.org
"""

import os, glob
try:
    import device_das_opal
    import das
except:
    from . import device_das_opal
    from . import das

opal_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Opal'
}

def das_info():
    return opal_info

def params(info, group_name=None):
    """
    Defines a function to create parameters for a Data Acquisition System (DAS) instance.

    Args:
        info (object): The test script information object used to define the parameters.
        group_name (str, optional): The name of the parameter group. 
            If not provided, it defaults to `DAS_DEFAULT_ID`.

    """
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = opal_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)

    # Recording mode
    info.param(pname('record_mode'), label='Recording mode', default='Build-in', values=['Build-in', 'Datalogger', 'SC_capture'])

    # Parameters to use the build-in waveform recording using getControlSignals API function
    info.param(pname('map'), label='Opal Analog Channel Map (e.g. simulinks blocks, etc,.)',
               values = ['Opal_Phase_Jump', 'Opal_Phase_Jump_Realign', 'Ekhi', 'Opal_Fast_1547', 'PHIL_testing', 'csv', 'Aliases', 'Search IEEE_1547_TESTING subsystem'],
               default='Opal_Phase_Jump', active=pname('record_mode'), active_value=['Build-in'])
    info.param(pname('mapping_csv_path'), label='Path to the csv with mapping information', default='\\models\\Phase_Jump_A_B_A\\Opal_Phase_Jump_mapping.csv',
               active=pname('map'), active_value=['csv'])
    info.param(pname('data_name'), label='Waveform Data File Name (.mat)', default='Data.mat', active=pname('record_mode'), active_value=['Build-in'])

    # Parameters to use the datalogger
    info.param(pname('Datalogger_signal_group_name'), label='Datalogger signal group name', default='SIGNAL_GROUP_1', active=pname('record_mode'), active_value=['Datalogger'])

    # Parameter for all recording type
    info.param(pname('wfm_chan_list'),  label='Waveform Channel List',
                values = list(device_das_opal.WFM_CHANNELS.keys())+['custom'], default='IEEE1547_VRT')
    info.param(pname('wfm_chan_list_custom'),  label='Custom Waveform Channel List', default='', active=pname('wfm_chan_list'), active_value=['custom'])

    info.param(pname('sample_interval'), label='Sample Interval (ms)', default=1000)

GROUP_NAME = 'opal'

class DAS(das.DAS):
    """
    DAS implementation for OPAL-RT systems. This class inherits from the DAS base class and provides
    specific implementation for data acquisition using OPAL-RT hardware.

    Attributes:
    -----------
        ts (object): Test script object.

    Methods das.DAS:
    ----------------
        open(): Open the DAS connection.
        info(): Return information about the DAS device.
        data_capture(enable): Enable/disable data capture.
        data_read(): Read captured data from the DAS device.
        data_sample(): Read a single data sample from the DAS device.
        config(): Configure the DAS device.
        status(): Get the status of the DAS device.

    Methods DAS (das_opal):
    ----------------------- 
        data_sample(): Read a single data sample from the DAS device.
        waveform_config(params): Configures the waveform capture settings
        waveform_record(filename=None): Starts recording waveform data on the OPAL device.
        waveform_stop(): Stops the waveform recording on the OPAL device.
        close(): Unimplemented
        waveform_capture_dataset(counter=None, name_dict=None): Captures a waveform dataset from the OPAL device
        waveform_capture(enable, sleep)
    
    """

    def __init__(self, ts, group_name, points=None, sc_points=None, support_interfaces=None):
        das.DAS.__init__(self, ts, group_name, points=points, sc_points=sc_points,
                         support_interfaces=support_interfaces)
        self.params['ts'] = ts

        self.params['sample_interval'] = self._param_value('sample_interval')
        if self.params['sample_interval'] is not None:
            if self.params['sample_interval'] < 50 and self.params['sample_interval'] is not 0:
                raise das.DASError('Parameter error: sample interval must be at least 50 ms or 0 for manual sampling')

        self.params['wfm_chan_list'] = self._param_value('wfm_chan_list')
        if self._param_value('wfm_chan_list') == 'custom':
            self.params['custom_wfm_chan_list'] = self._get_custom_chan_list()

        # initialize build-in recording
        if self._param_value('record_mode') == 'Build-in':
            self.params['use_buildin_recording'] = True
            self.params['map'] = self._param_value('map')
            if self._param_value('map') == 'csv':
                self.params['mapping_csv_path'] = self._get_mapping_csv_path()
            # self.params['wfm_dir'] = self._param_value('wfm_dir')
            self.params['wfm_dir'] = self._get_opWriteFile_results_directory()
            self.params['data_name'] = self._param_value('data_name')
        else:
            self.params['use_buildin_recording'] = False

        # initialize sc_capture
        if self._param_value('record_mode') == 'SC_capture':
            self.params['sc_capture'] = True
        else:
            self.params['sc_capture'] = False

        # initialize datalogger
        if self._param_value('record_mode') == 'Datalogger':
            self.params['use_datalogger'] = True
            self.params['Datalogger_signal_group_name'] = self._param_value('Datalogger_signal_group_name')
        else:
            self.params['use_datalogger'] = False

        if self.hil is None:
            ts.log_warning('No HIL support interface was provided to das_opal.py. It is recommended to provide the '
                           'hil, at minimum, using "daq = das.das_init(ts, support_interfaces='
                           '{"hil": phil, "pvsim": pv})"')
        self.params['hil'] = self.hil
        self.params['gridsim'] = self.gridsim
        self.params['dc_measurement_device'] = self.dc_measurement_device

        self.device = device_das_opal.Device(self.params)
        self.data_points = self.device.data_points

         # initialize soft channel points
        self._init_sc_points()



    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def _get_mapping_csv_path(self):
        """
        Get the absolute path of the csv with the sensor mapping according the the path given by the user.
        In order of priority, the function will look if :
        - the path given by the user is absolute or is a relative path from the SVP directory
        - it is a relative path from the RT-LAB model directory
        - it is a relative path from the RT-LAB project directory
        - it is a relative path from the SVP workspace directory
        - it is a relative pas from the OPAL Workspace directory.
        If at anypoint the corresponding absolute path points to an existing file, the function will return that path.

        Return: (string) absolute path of sensor mapping csv
        """
        csv_path = self._param_value('mapping_csv_path')
        if os.path.exists(os.path.abspath(csv_path)):
            # actual path
            return os.path.abspath(csv_path)
        elif os.path.exists(os.path.join(self.hil.rt_lab_model_dir, csv_path)):
            # relative path from model directory
            return os.path.join(self.hil.rt_lab_model_dir, csv_path)
        elif os.path.exists(os.path.join(os.path.dirname(self.hil.project_dir_path), csv_path)):
            # relative path from project directory
            return os.path.join(os.path.dirname(self.hil.project_dir_path), csv_path)
        SVP_working_directory = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if os.path.exists(SVP_working_directory, csv_path):
            # relative path from SVP workspace directory
            return os.path.join(SVP_working_directory, csv_path)
        OPAL_Workspaces_directory = os.path.join(os.path.expanduser('~').split("AppData")[0],'OPAL-RT')
        if os.path.exists(OPAL_Workspaces_directory, csv_path):
            # relative path from OPAL workspace
            return os.path.join(OPAL_Workspaces_directory, csv_path)
        self.ts.log_error('Mapping csv not found')
        return None

    def _get_custom_chan_list(self):
        """
        Transform the custom channel list from a string to a python list.
        The function will split the text entered by the user by the separator ',', ';' or ' ' and strip any remaining space.

        Return: (list of string) list of channel names
        """
        custom_chan_list = self._param_value('wfm_chan_list_custom').split(',')
        if len(custom_chan_list) == 1:
            custom_chan_list = custom_chan_list[0].split(';')
        if len(custom_chan_list) == 1:
            custom_chan_list = custom_chan_list[0].split(' ')
        custom_chan_list = [element.replace(' ','') for element in custom_chan_list]
        return custom_chan_list

    def _get_opWriteFile_results_directory(self):
        """
        Get the directory where .mat from opWriteFile are stored.

        Return: (string) absolute path of the results directory
        """
        OS_platform = self.hil.RtlabApi.GetTargetPlatform()
        OS_directory = 'OpREDHAWK64target' if OS_platform == self.hil.RtlabApi.REDHAWK64_TARGET else 'OpREDHAWKtarget'
        model_directory = self.hil.rt_lab_model_dir
        possible_directories = glob.glob(os.path.join(model_directory,'*',OS_directory))
        return possible_directories[0]

    def set_dc_measurement(self, obj=None):
        """
        DEPRECATED

        In the event that DC measurements are taken from another device (e.g., a PV simulator) please add this
        device to the das object
        :param obj: The object (e.g., pvsim) that will gather the dc measurements
        :return: None
        """
        # self.ts.log_debug('device: %s, obj: %s' % (self.device, obj))
        self.device.set_dc_measurement(obj)


    def data_sample(self):
        """
        Read the current data values directly from the DAS and place in the current dataset.
        """
        if self._capture is True:
            self._last_datarec = self.device_data_read()
            self._ds.append(self._last_datarec)
        return self._last_datarec

    def waveform_config(self, params):
        """
        Configures the waveform capture settings for the OPAL device.
        
        Args:
            params (dict): A dictionary containing the waveform capture
            configuration parameters.
        """
        self.device.waveform_config(params=params)

    def waveform_record(self, filename=None):
        """
        Starts recording waveform data on the OPAL device.
        
        Args:
            filename (str, optional): If provided, the waveform data will 
            be saved to the specified file. If not provided, the waveform 
            data will be recorded but not saved to a file.
        """
        if filename is None:
            self.device.waveform_record()
        else:
            self.device.waveform_record(filename)

    def waveform_stop_record(self):
        """
        Stops the waveform recording on the OPAL device.
        """
        self.device.waveform_stop_record()

    def close(self):
        pass

    def waveform_capture_dataset(self, counter=None, name_dict=None):
        """
        Captures a waveform dataset from the OPAL device.
        
        Args:
            counter (int, optional): An optional counter value to include in the dataset name.
            name_dict (dict, optional): An optional dictionary of names to associate with the dataset.

        """
        return self.device.waveform_capture_dataset(counter, name_dict)

    def waveform_capture(self, enable=True):
        """
        Enable/disable waveform capture.
        """
        if enable:
            self.device.waveform_capture(enable, sleep)

if __name__ == "__main__":

    pass


