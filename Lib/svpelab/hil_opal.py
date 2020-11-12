"""
Copyright (c) 2020, CanmetENERGY, Sandia National Labs and SunSpec Alliance
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
try:
    import hil
except ImportError as e:
    print("Could not import hil")
    from . import hil

import sys
from time import sleep
# import glob
# import numpy as np

try:
    sys.path.insert(0, "C://OPAL-RT//RT-LAB//2020.1//common//python")
    import RtlabApi
    import OpalApiPy
except ImportError as e:
    print(e)


# Dictionary used to create a mapping between a realTimeModeString and a realTimeId
realTimeModeList = {'Hardware Synchronized': 0, 
                    'Simulation': 1,
                    'Software Synchronized': 2, 
                    'Simulation with no data loss': 3,
                    'Simulation with low priority': 4}

opalrt_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Opal-RT'
}


def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = opalrt_info['mode']
    info.param_add_value('hil.mode', opalrt_info['mode'])
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode, active=gname('mode'),
                     active_value=mode, glob=True)

    info.param(pname('target_name'), label='Target name in RT-LAB', default="RTServer")
    info.param(pname('workspace_path'), label='RT-LAB Workspace', default="C:\OPAL-RT\WorkspaceFOREVERYONE")
    info.param(pname('project_name'), label='RT-LAB project name (.llp)', default="IEEE_1547_Fast_Functions.llp")
    info.param(pname('project_dir'), label='Project Directory', default="IEEE_1547_Fast_Functions")
    info.param(pname('rt_lab_model'), label='RT-LAB model name (.mdl or .slx)', default='IEEE_1547_Fast_Functions')

    info.param(pname('hil_config'), label='Configure HIL in init', default='False', values=['True', 'False'])
    info.param(pname('hil_config_open'), label='Open Project?', default="Yes", values=["Yes", "No"])
    info.param(pname('hil_config_compile'), label='Compilation needed?', default="No", values=["Yes", "No"])
    info.param(pname('hil_config_stop_sim'), label='Stop the simulation before loading/execution?',
               default="Yes", values=["Yes", "No"])
    info.param(pname('hil_config_load'), label='Load the model to target?', default="Yes", values=["Yes", "No"])
    info.param(pname('hil_config_execute'), label='Execute the model on target?', default="Yes", values=["Yes", "No"])
    info.param(pname('hil_stop_time'), label='Stop Time', default=3600.)


GROUP_NAME = 'opal'


def hil_info():
    return opalrt_info


class HIL(hil.HIL):
    """
    Opal_RT HIL implementation - The default.
    """
    def __init__(self, ts, group_name):
        hil.HIL.__init__(self, ts, group_name)
        # Add REGEX or parser manipulation to get a good control over user entries.
        self.project_name = self._param_value('project_name')
        self.project_dir = self._param_value('project_dir')
        self.workspace_path = self._param_value('workspace_path')

        self.target_name = self._param_value('target_name')
        # Get without .mdl
        self.rt_lab_model = self._param_value('rt_lab_model').split(".")[0]
        self.rt_lab_model_dir = self._param_value('rt_lab_model_dir')

        self.ts = ts

        self.rt_lab_python_dir = self._param_value('rt_lab_python_dir')
        try:
            sys.path.insert(0, self.rt_lab_python_dir)
            import RtlabApi
        except ImportError as e:
            print(e)

        # self.ts.log_debug(self.info())
        # self.open()

        self.hil_config_open = self._param_value('hil_config_open')
        self.hil_config_compile = self._param_value('hil_config_compile')
        self.hil_config_stop_sim = self._param_value('hil_config_stop_sim')
        self.hil_config_load = self._param_value('hil_config_load')
        self.hil_config_execute = self._param_value('hil_config_execute')
        self.hil_stop_time = self._param_value('hil_stop_time')

        if self._param_value('hil_config') == 'True':
            self.config()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def hil_info(self):
        return opalrt_info

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        self.ts.log("{}".format(self.info()))
        if self._param_value('hil_config_open') == 'Yes':
            self.open()
        if self.hil_config_compile == 'Yes':
            self.ts.sleep(1)
            self.ts.log("    Model ID: {}".format(self.compile_model().get("modelId")))
        if self.hil_config_stop_sim == 'Yes':
            self.ts.sleep(1)
            self.ts.log("    {}".format(self.stop_simulation()))

        self.ts.log('Setting the simulation stop time for %0.1f to run experiment.' % self.hil_stop_time)
        self.set_stop_time(self.hil_stop_time)

        if self.hil_config_load == 'Yes':
            self.ts.sleep(1)
            self.ts.log("    {}".format(self.load_model_on_hil()))
        if self.hil_config_execute == 'Yes':
            self.ts.log("    {}".format(self.start_simulation()))

    def command(self, ownerId=None, command=None, attributes=None, values=None):
        """
        :param ownerId: -   The ID of the object that owns the command. Where there is ambiguity, the owner of the two
                            objects is the expected ID. For example CMD_REMOVE: when the owner is a project, the
                            command removes a model.
        :param command -    The command to be executed (see OP_COMMAND). For each command, the requirements vary
                            depending on the owner ID supplied to OpalCommand.
        :param attributes - The tuple of attributes to send as command arguments (see OP_ATTRIBUTE). The size of the
                            tuple must match the size of the attributeValues tuple.
        :param values -     The tuple of attribute values to send as command arguments. The size of the tuple must match
                            the size of the attributes tuple.

        :return: outputId - The ID corresponding to the object directly affected by the command. If no other object
                            than the parent is affected, the parent ID is returned.

        Examples:

        New Project
            Owner ID class: OP_RTLAB_OBJ
            Command : CMD_NEW
            Description : Create a new project in the current RT-Lab session. If a project is already open it is closed.
            Required control : None
            Required attributes : ATT_FILENAME
            Optional attributes : None
            Output ID class: OP_PROJECT_OBJ

        Open Project
            Owner ID class: OP_RTLAB_OBJ
            Command : CMD_OPEN
            Description : Open an existing project from file or connect to an active project. After this action the
                project opened becomes the current project in the current RT-Lab session. If a project is open
                beforehand it is closed. When connecting to a previously active project, control of this project may
                also be requested.
            Required control : None
            Required attributes : None
            Optional attributes : ATT_FILENAME, ATT_API_INSTANCE_ID, ATT_FUNCTIONAL_BLOCK, ATT_CONTROL_PRIOTRITY,
                ATT_RETURN_ON_AMBIGUUITY
            Output ID class: OP_PROJECT_OBJ


        Add Default Environment Variable
            Owner ID class : OP_RTLAB_OBJ
            Command : CMD_ADD
            Description : Add an environment variable to the default RT-LAB settings. This variable will NOT affect
                the current project directly.
            Required control : OP_FB_CONFIG
            Required attributes : ATT_OBJECT_TYPE, ATT_NAME
            Required attribute values : ATT_OBJECT_TYPE = OP_ENVIRONMENT_VARIABLE_OBJ
            Optional attributes : ATT_VALUE
            Output ID class: OP_ENVIRONMENT_VARIABLE_OBJ


        Load Model Configuration
            Name : CMD_OPEN
            Description : Load an existing model's settings from a file.
            Owner type : OP_TYPE_MODEL
            Required control : OP_FB_SYSTEM
            Required attributes : ATT_FILENAME
            Optional attributes : None
            Output ID class: Same as the value of ATT_REF_ID
        """

        return RtlabApi.Command(ownerId, command, attributes, values)

    def get_active_projects(self):
        """
        Calls GetActiveProjects() to list the current projects

        :return:
        """
        active_projects = RtlabApi.GetActiveProjects()
        for proj in range(len(active_projects)):
            self.ts.log_debug(active_projects[proj])  # *(str(),OP_INSTANCE_ID(),str(),str(),int(),tuple())
        pass

    def open(self):
        """
        Open the communications resources associated with the HIL.
        """
        self.ts.log('Opening Project: %s' % self.project_name)
        if os.path.isfile(self.project_name):
            self.ts.log('Assuming project name is an absolute path to .llp file')
            proj_path = self.project_name
        elif os.path.isdir(self.project_name) and os.path.isfile(self.project_name):
            self.ts.log('Assuming project directory + project name is an absolute path to .llp file')
            self.project_dir.rstrip('\\') + '\\' + self.project_name
            proj_path = self.project_dir.rstrip('\\') + '\\' + self.project_name
        elif os.path.isdir(self.workspace_path):
            self.ts.log('Assuming workspace is used with Project Name and directory')
            proj_path = os.path.join(self.workspace_path, self.project_dir, self.project_name)
        else:
            self.ts.log('Assuming project directory and .llp file are located in svpelab directory')
            svpelab_dir = os.path.abspath(os.path.dirname(__file__))
            proj_path = svpelab_dir + self.project_dir.rstrip('\\') + '\\' + self.project_name

        if proj_path[:-4] != '.llp':
            proj_path += '.llp'
        try:
            # projectId = RtlabApi.OpenProject(project='', functionalBlock=None,
            #                                  controlPriority=OP_CTRL_PRIO_NORMAL, returnOnAmbiguity=False)
            self.ts.log('Opening project: %s' % proj_path)
            RtlabApi.OpenProject(proj_path)
        except Exception as e:
            self.ts.log_warning('Could not open the project %s: %s' % (proj_path, e))
            raise
        self.ts.log('Opened Project: %s' % self.project_name)

        # Set controls to the API
        RtlabApi.GetParameterControl(1)
        RtlabApi.GetSignalControl(1)
        # RtlabApi.GetAcquisitionControl(1, 0)
        RtlabApi.GetMonitoringControl(1)
        self.control_panel_info(state=1)  # GetSystemControl

        pass

    def close(self):
        """
        Close any open communications resources associated with the HIL.
        """
        try:
            self.stop_simulation()
            RtlabApi.CloseProject()
        except Exception as e:
            self.ts.log_error('Unable to close project. %s' % e)

    def info(self):
        """
        Return system information
        :return: Opal Information
        """
        system_info = RtlabApi.GetTargetNodeSystemInfo(self.target_name)
        opal_rt_info = "OPAL-RT - Platform version {0} (IP address : {1})".format(system_info[1], system_info[6])
        return opal_rt_info

    def control_panel_info(self, state=1):
        """
        Requests or releases the system control of the currently connected model. System control enables the client
        API to control the model's execution. Only one client API at a time is granted system control.

        :param state = systemControl: True(1) to request system control of the model, False(0) to release its control.
        :return: None
        """
        try:
            if state == 1 or state == 0:
                RtlabApi.GetSystemControl(state)
            else:
                self.ts.log_warning('Incorrect GetSystemControl state provided: state = %s' % state)
        except Exception as e:
            self.ts.log_warning('Error getting system control: %s' % e)
        pass

    def load_schematic(self):
        """
        Nonfunctional and deprecated!

        Load .mdl file

        :return: None
        """

        # SetCurrentModel is deprecated
        model_info = {"mdlFolder": self.rt_lab_model_dir, "mdlName": self.rt_lab_model}
        if self.rt_lab_model != 'None':
            model_full_loc = self.rt_lab_model_dir + self.rt_lab_model + '\\' + self.rt_lab_model + '.mdl'
            llp_full_loc = self.rt_lab_model_dir + self.rt_lab_model + '\\' + self.rt_lab_model + '.llp'
            os.remove(llp_full_loc)  # remove the .llp associated with the .mdl

            self.ts.log('Setting Current Model to %s.' % model_full_loc)
            (instance_id,) = RtlabApi.SetCurrentModel(model_full_loc)
            self.ts.log('Set Current Model to %s with instance ID: %s.' % (self.rt_lab_model, instance_id))
        else:
            model_info["mdlFolder"], model_info["mdlName"] = RtlabApi.GetCurrentModel()
            self.ts.log('Using default model. %s\\%s' % (model_info["mdlFolder"], model_info["mdlName"]))

        return model_info

    def model_state(self):
        """
        modelState, realTimeMode = RtlabApi.GetModelState()

        modelState - The state of the model. See OP_MODEL_STATE.
        realTimeMode - The real-time mode of the model. See OP_REALTIME_MODE.

        OP_MODEL_STATE:
            MODEL_NOT_CONNECTED (0) - No connected model.
            MODEL_NOT_LOADABLE (1) - Model has not been compiled
            MODEL_COMPILING(2) - Model is compiling
            MODEL_LOADABLE (3) - Model has been compiled and is ready to load
            MODEL_LOADING(4) - Model is loading
            MODEL_RESETTING(5) - Model is resetting
            MODEL_LOADED (6) - Model loaded on target
            MODEL_PAUSED (7) - Model is loaded and paused on target
            MODEL_RUNNING (8) - Model is loaded and executed on target
            MODEL_DISCONNECTED (9) - Model is disconnect

        OP_REALTIME_MODE:
            HARD_SYNC_MODE (0) - Hardware synchronization mode (not available on WIN32 target). An I/O board with
                                 timer is required on target
            SIM_MODE (1) - Simulation as fast as possible mode
            SOFT_SIM_MODE (2) - Software synchronization mode
            SIM_W_NO_DATA_LOSS_MODE (3) - Not used anymore
            SIM_W_LOW_PRIO_MODE (4) - Simulation as fast as possible in low priority mode (available only on WIN32 targ)

        :return: string with model state
        """

        model_status, _ = RtlabApi.GetModelState()
        if model_status == RtlabApi.MODEL_NOT_CONNECTED:
            return 'Model Not Connected'
        elif model_status == RtlabApi.MODEL_NOT_LOADABLE:
            return 'Model Not Loadable'
        elif model_status == RtlabApi.MODEL_COMPILING:
            return 'Model Compiling'
        elif model_status == RtlabApi.MODEL_LOADABLE:
            return 'Model Loadable'
        elif model_status == RtlabApi.MODEL_LOADING:
            return 'Model Loading'
        elif model_status == RtlabApi.MODEL_RESETTING:
            return 'Model Resetting'
        elif model_status == RtlabApi.MODEL_LOADED:
            return 'Model Loaded'
        elif model_status == RtlabApi.MODEL_PAUSED:
            return 'Model Paused'
        elif model_status == RtlabApi.MODEL_RUNNING:
            return 'Model Running'
        elif model_status == RtlabApi.MODEL_DISCONNECTED:
            return 'Model Disconnected'
        else:
            return 'Unknown Model state'

    def compile_model(self):
        """
        Compiles the model

        :return: model_info dict with "mdlFolder", "mdlPath", and "modelId" keys
        """

        # Register Display information to get the target script STD output
        # RtlabApi.RegisterDisplay(RtlabApi.DISPLAY_REGISTER_ALL)

        model_info = {}
        try:
            model_info["mdlFolder"], model_info["mdlName"] = RtlabApi.GetCurrentModel()
            model_info["mdlPath"] = model_info["mdlFolder"] + model_info["mdlName"]
            model_info["modelId"] = RtlabApi.FindObjectId(RtlabApi.OP_TYPE_MODEL, model_info["mdlPath"])
            RtlabApi.SetAttribute(model_info["modelId"], RtlabApi.ATT_FORCE_RECOMPILE, True)
            self.ts.log('Using default model. %s%s' % (model_info["mdlFolder"], model_info["mdlName"]))
        except Exception as e:
            self.ts.log_warning('Error using Current Model: %s' % e)

            try:
                model_info["mdlFolder"] = self.rt_lab_model_dir + self.rt_lab_model + '\\'
                model_info["mdlPath"] = self.rt_lab_model + '.mdl'
                model_info["mdlPath"] = model_info["mdlFolder"] + model_info["mdlPath"]
                model_info["modelId"] = RtlabApi.FindObjectId(RtlabApi.OP_TYPE_MODEL, model_info["mdlPath"])
                RtlabApi.SetAttribute(model_info["modelId"], RtlabApi.ATT_FORCE_RECOMPILE, True)

            except Exception as e:
                self.ts.log_warning('Error compiling model %s: %s' % (model_info["mdlPath"], e))

        if self.model_state() == 'Model Paused':
            self.ts.log('Model is loaded and paused. Restarting Model to re-compile.')
            RtlabApi.Reset()

        # Launch compilation
        compilationSteps = RtlabApi.OP_COMPIL_ALL_NT | RtlabApi.OP_COMPIL_ALL_LINUX
        RtlabApi.StartCompile2((("", compilationSteps),), )
        self.ts.log('Compilation started.  This will take a while...')

        # Wait until the end of the compilation
        status = RtlabApi.MODEL_COMPILING
        while status == RtlabApi.MODEL_COMPILING:
            try:
                # Check status every 0.5 second
                sleep(0.5)

                # Get new status. To be done before DisplayInformation because DisplayInformation may generate an
                # Exception when there is nothing to read
                status, _ = RtlabApi.GetModelState()
                

                # Display compilation log into Python console
                _, _, msg = RtlabApi.DisplayInformation(100)
                while len(msg) > 0:
                    self.ts.log(msg)
                    _, _, msg = RtlabApi.DisplayInformation(100)

            except Exception as exc:
                # Ignore error 11 which is raised when RtlabApi.DisplayInformation is called when there is no
                # pending message
                info = sys.exc_info()
                self.ts.debug(info)
                if info[1][0] != 11:  # 'There is currently no data waiting.'
                    # If a exception occur: stop waiting
                    self.ts.debug("An error occurred during compilation: %s", exc)
                    raise

        # Because we use a comma after print when forward compilation log into python log we have to ensure to
        # write a carriage return when finished.
        print('')

        # Get project status to check is compilation succeeded
        if self.model_state() == 'Model Loadable':
            self.ts.log('Compilation success.')
        else:
            self.ts.log('Compilation failed.')

        return model_info

    def load_model_on_hil(self):
        """
        Load the model on the target

        :return: str indicating load state
        """

        if self.model_state() == 'Model Loadable':
            self.ts.log('Loading Model.  This may take a while...')
            realTimeMode = RtlabApi.HARD_SYNC_MODE
            # Also possible to use SIM_MODE, SOFT_SIM_MODE, SIM_W_NO_DATA_LOSS_MODE or SIM_W_LOW_PRIO_MODE
            timeFactor = 1
            try:
                RtlabApi.Load(realTimeMode, timeFactor)
            except Exception as e:
                self.ts.log_warning('Model failed to load. Recommend opening and rebuilding the model in RT-Lab. '
                                    '%s' % e)
                raise
            return "The model is loaded."
        else:
            self.ts.log_warning('Model was not loaded because the status is:  %s' % self.model_state())
            return "The model is not loaded."

        pass

    def matlab_cmd(self, cmd):
        return RtlabApi.ExecuteMatlabCmd(cmd)

    def init_sim_settings(self):
        pass

    def init_control_panel(self):
        pass

    def voltage(self, voltage=None):
        pass

    def stop_simulation(self):
        """
        Reset simulation

        :return: model status
        """
        self.ts.log('Stopping/Resetting simulation. Current State: %s' % self.model_state())
        if self.model_state() == 'Model Loadable':
            self.ts.log('Model already stopped.')
        else:
            RtlabApi.Reset()
        self.ts.log('Model state is now: %s' % self.model_state())
        return self.model_state()

    def start_simulation(self):
        """
        Begin the simulation

        :return: Status str
        """
        if self.model_state() == 'Model Paused':
            # When in real-time mode, the execution rate is the model's sampling rate times the time factor.
            timeFactor = 1
            RtlabApi.Execute(timeFactor)
        else:
            self.ts.log_warning('Model is not running because the status is:  %s' % self.model_state())
        return 'The model state is now: %s' % self.model_state()

    def run_py_script_on_target(self):
        """
        Untested placeholder to run python code on the Opal target

        This example shows how to use the OpalExecuteTargetScript() API function
        to start a python script on the remote target.

        The OpalExecuteTargetScript API function call requires a valid connection
        to a model.  We use in this example an empty model called empty.mdl only for
        the Rt-Lab connection to be present.

        :return: None
        """

        # Get the current script directory
        currentFolder = os.path.abspath(sys.path[0])
        scriptFullPath = os.path.join(currentFolder, 'myscript.py')

        import glob
        projectName = os.path.abspath(str(glob.glob('.\\..\\*.llp')[0]))
        RtlabApi.OpenProject(projectName)
        print("The connection with '%s' is completed." % projectName)

        modelState, realTimeMode = RtlabApi.GetModelState()
        print(('Model State: %s, Real Time Mode: %s' % (modelState, realTimeMode)))

        TargetPlatform = RtlabApi.GetTargetPlatform()
        nodelist = RtlabApi.GetPhysNodeList()

        if TargetPlatform != RtlabApi.NT_TARGET:
            if len(nodelist) > 0:
                TargetName = nodelist[0]

                print("List of Physicals Nodes available to run the script: ", nodelist)
                print("The script will be executed on the first Physical Node")
                print("Selected Physical Node is: ", TargetName)
                print(" ")
                try:
                    # Register Display information to get the target script STD output
                    RtlabApi.RegisterDisplay(1)

                    print(("Transferring the script :\n%s \nto the physical node %s" % (scriptFullPath, TargetName)))
                    RtlabApi.PutTargetFile(TargetName, scriptFullPath, "/home/ntuser/", RtlabApi.OP_TRANSFER_ASCII, 0)

                    # Executing the script on the target
                    RtlabApi.StartTargetPythonScript(TargetName, "/home/ntuser/myscript.py", "Hello World", "")

                    # Displaying the STD output of the script
                    print("*************Script output on the target************")
                    print((RtlabApi.DisplayInformation(0)[2]))
                    print("****************************************************")
                finally:
                    pass
            else:
                print("At least one Physical Node should be configured in the Rt-Lab configuration")
                print("See RT-LAB User Guide for more details about Physical Node configuration")
                print("This information can be found in the section 2.2.5.9 - Hardware Tab")
        else:
            print("The empty.mdl file is configured to run a Windows Target.  \nThis example does not support the "
                  "Windows target, please select another target platform")

        pass

    def set_parameters(self, parameters):
        """
        Sets the parameters in the RT-Lab Model

        :param parameters: tuple of (parameter, value) pairs
        :return: None
        """

        if parameters is not None:
            for p, v in parameters:
                self.ts.log_debug('Setting parameter %s = %s' % (p, v))
                self.set_params(p, v)

    def get_parameters(self, verbose=False):
        """
        Get the parameters from the model

        :return: list of parameter tuples with (path, name, value)
        """

        model_parameters = RtlabApi.GetParametersDescription()
        # array of tuples: (id, path, name, variableName, value)
        mdl_params = []
        for param in range(len(model_parameters)):
            mdl_params.append((model_parameters[param][1],
                               model_parameters[param][2],
                               model_parameters[param][4]))
            if verbose:
                self.ts.log_debug('Param: %s, %s is %s' % (model_parameters[param][1],
                                                           model_parameters[param][2],
                                                           model_parameters[param][4]))
        return mdl_params

    def get_acq_signals_raw(self, signal_map=None, verbose=False):
        """
        Returns the acquisition signals sent to the console subsystem while the model is running. The acquisition
        signals are the signals sent from the computation nodes to console subsystem in the same order that it was
        specified at the input of the OpComm block for the specified acquisition group. The outputs contains two
        arrays: acquisition signals + monitoring signals.

        The user can activate the synchronization algorithm to synchronize the acquisition time with the simulation
        time by inserting data during missed data intervals. The interpolation can be used in this case to get a
        better result during missed data intervals. Threshold time between acquisition time and simulation time
        exceeds the threshold, the acquisition (console) will be updated to overtake the difference. The acqtimestep
        offers the user a way to change his console step size as in Simulink.

        :param signal_map: list of  acquisition signals names
        :param verbose: bool that indicates if the function prints results
        :return: if a signal map is provided, returns a dict of the acq values mapped to the list'
                 if no signal map, return list of data.
        """

        # SetAcqBlockLastVal -- Set the current settings for the blocking / non-blocking, and associated last value
        # flag, for signal acquisition. This information is used by the API acquisition functions, which have the
        # option not to wait for data, needed by some console's lack of multiple thread support. The ProbeControl
        # panel sets these settings using this call.

        # blockOnGroup: Acquisition group for which the API functions will wait for data (specify n for group n).
        # If 0, API function will wait for data for all groups. If -1, API functions will not wait for any group's data.
        BlockOnGroup = 0
        # lastValues: Boolean, 1 means API functions will output the last values received while a group's data is
        # not available. If 0, the API function will output zeroes. This paramater is ignored when blockOnGroup is
        # not equal to -1.
        lastValues = 1
        RtlabApi.SetAcqBlockLastVal(BlockOnGroup, lastValues)

        # acquisitionGroup: Acquisition group number, starts from 0.
        # synchronization: synchronization 1/0 = Enable/Disable
        # interpolation: interpolation 1/0 = Enable/Disable
        # threshold: Threshold difference time between the simulation and the acquisition (console) time in seconds.
        # acqTimeStep: Sample interval: acquisition (console) timestep must be equal or greater than the model time step
        acquisitionGroup = 0
        synchronization = 0
        interpolation = 0
        threshold = 0
        acqTimeStep = 80e-6
        values, monitoringInfo, simulationTimeStep, endFrame = \
            RtlabApi.GetAcqGroupSyncSignals(acquisitionGroup, synchronization, interpolation, threshold, acqTimeStep)

        # monitoringInfo: Monitoring information tuple. It contains the following values: Missed data, offset,
        # simulationTime and sampleSec. See below for more details.
        missedData, offset, simulationTime, sampleSec = monitoringInfo
        # self.ts.log_debug('SimulationTime of data acquisition = %s' % simulationTime)

        if missedData >= 1.0:
            self.ts.log_warning('Missing data in last acquisition. Number of missing data points: %s' % missedData)

        if verbose:
            # values: Acquired signals from acquisition. It contains a tuple of values with one value for each signal in
            # the acquisition group.
            self.ts.log_debug('Acquired signals from acquisition: %s' % (str(values)))
            # missedData: Number of values between two acquisition frame. If value is 0, there are no missing data
            # between the two frames. Missing data may appear if network communication and display are too slow to
            # refresh value generated by the model.
            self.ts.log_debug('Number of values missing between two acquisition frames (missedData): %s' %
                              (str(missedData)))
            # offset: simulation time when the acquisition started.
            self.ts.log_debug('Simulation time when the acquisition started (offset): %s' % (str(offset)))
            # simulationTime: simulation time of the model when the acquisition has been done.
            self.ts.log_debug('Simulation time at acquisition (simulationTime): %s' %
                              (str(simulationTime)))
            # sampleSec: Number of sample/sec received from target. Calculation is made for one sample. Ex: If model is
            # running at 0.001s, sample/sec value should not exceed 1000 sample/sec.
            self.ts.log_debug('Number of sample/sec received from target (sampleSec): %s' % (str(sampleSec)))
            # simulationTimeStep: Simulation timestep of the acquired data.
            self.ts.log_debug('Simulation timestep of the acquired data (simTimeStep): %s' % (str(simulationTimeStep)))
            # endFrame: True when signals are the last in the acquisition buffer (next values will be in a next frame).
            self.ts.log_debug('Number of values between two acquisition frames: %s' % (str(endFrame)))

        if signal_map is not None:
            idx = 0
            for key, value in signal_map:
                signal_map[key] = values[idx]
                idx += 1
            signal_map['TIME'] = simulationTime
            return signal_map
        else:
            return list(values)

    def get_acq_signals(self, verbose=False):
        """
        Get the data acquisition signals from the model

        :return: list of tuples of data acq signals from SC_ outputs, (signalId, label, value)

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

        acq_signals = []
        for sig in range(len(signals)):
            if str(signals[sig][0]) == 'OP_ACQUISITION_SIGNAL(0)':
                acq_signals.append((signals[sig][1], signals[sig][3], signals[sig][6]))
                if verbose:
                    self.ts.log_debug('Sig #%d: Type: %s, Path: %s, Label: %s, value: %s' %
                                      (signals[sig][1], signals[sig][0], signals[sig][2], signals[sig][3],
                                       signals[sig][6]))

        return acq_signals

    def get_control_signals(self, details=False, verbose=False):
        """
        Get the control signals from the model

        The control signals are the signals sent from the console to the computation nodes in the same order as
        specified in the input of the OpComm of the specified computation nodes.

        :return: list of control signals
            if details == True, return a list of tuples (signalType, signalId, path, label, value)
            if details == False, return list of values for the signals in the control
        """

        if details:
            signals = RtlabApi.GetControlSignalsDescription()
            # (signalType, signalId, path, label, reserved, readonly, value) = signalInfo1
            # 0 signalType: Signal type. See OP_SIGNAL_TYPE.
            # 1 id: Id of the signal.
            # 2 path: Path of the signal.
            # 3 label: Label or name of the signal.
            # 4 reserved:
            # 5 readonly: True when the signal is read-only.
            # 6 value: Current value of the signal

            control_signals = []
            for sig in range(len(signals)):
                control_signals.append((signals[sig][0], signals[sig][1], signals[sig][2], signals[sig][3],
                                       signals[sig][6]))
                if verbose:
                    self.ts.log_debug('Sig #%d: Type: %s, Path: %s, Label: %s, value: %s' %
                                      (signals[sig][1], signals[sig][0], signals[sig][2], signals[sig][3],
                                       signals[sig][6]))

        else:
            control_signals = list(RtlabApi.GetControlSignals())
            if verbose:
                for param in range(len(control_signals)):
                    self.ts.log_debug('Control Signal #%d = %s' % (param, control_signals[param]))

        return control_signals

    def set_control_signals(self, values=None):
        """
        Set the control signals from the model

        The control signals are the signals sent from the console to the computation nodes in the same order as
        specified in the input of the OpComm of the specified computation nodes.

        :return: None
        """

        logical_id = 1  # SC_Subsystem
        # A unique number associated with each subsystem of type SM, SC or SS in a model. This number is assigned during
        # the compilation of the model and is independent of the target where the simulation is performed. The SM
        # subsystem is always assigned Id 1, the SC subsystem is always assigned Id 2 and the SS subsystem is assigned
        # Id 2 if there is no console and a value greater than 2 if there is a console. The logical Id can be obtained
        # by calling the GetSubsystemList function. Note: Some API functions accept an Id of 0. This value means that
        # the function will be applied to all subsystem.

        subsystems = RtlabApi.GetSubsystemList()
        # self.ts.log_debug(subsystems)
        #  ('IEEE_P1547_TEST_V22/SM_SystemDynamics', 1, 'Target_3')
        #  ('IEEE_P1547_TEST_V22/SC_InputsandOutputs', 2, '')
        subsystem = 'None'
        for sub in subsystems:
            # self.ts.log_debug('sub = %s' % str(sub))
            if sub[1] == logical_id:
                subsystem = sub[0]
        if subsystem == 'None':
            self.ts.log_warning('No subsystem was found')

        # self.ts.log_debug('Sending the following control signals: %s to %s' % (values, subsystem))
        if values is not None:
            if isinstance(values, list):
                RtlabApi.SetControlSignals(logical_id, tuple(values))
            elif isinstance(values, tuple):
                RtlabApi.SetControlSignals(logical_id, values)
            else:
                self.ts.log_warning('No values set by RtlabApi.SetControlSignals() because values were not list '
                                    'or tuple')
        else:
            self.ts.log_warning('No values set by RtlabApi.SetControlSignals()')

        return None

    def set_params(self, param, value):
        """
        Set parameters in the model

        :param param: tuple of/or str for the parameter location, e.g., "PF818072_test_model/sm_computation/Rocof/Value"
        :param value: tuple of/or float values of the parameters

        :return: None
        """

        if type(param) is tuple and type(value) is tuple:
            RtlabApi.SetParametersByName(param, value)
        elif type(param) is str and type(float(value)) is float:
            RtlabApi.SetParametersByName(param, value)
        else:
            self.ts.log_debug('Error in the param or value types. type(param) = %s, type(value) = %s ' %
                              (type(param), type(value)))
        pass

    def set_var(self, variable, value):
        """
        Set Matlab variable in the model

        :param variable: variable name 
        :param value: tuple of/or float values of the variable

        :return: None
        """
        pass
        modelName = self.rt_lab_model
        attributeNumber = RtlabApi.FindObjectId(RtlabApi.OP_TYPE_VARIABLE, modelName + '/' + variable)
        RtlabApi.SetAttribute(attributeNumber, RtlabApi.ATT_MATRIX_VALUE, value)

        # attributeNumber = RtlabApi.FindObjectId(RtlabApi.OP_TYPE_VARIABLE, self.rt_lab_model + '/' + variable)

    def set_variables(self, variables):
        """
        Sets the parameters in the RT-Lab Model

        :param parameters: tuple of (parameter, value) pairs
        :return: None
        """

        if variables is not None:
            for variable, value in variables:
                self.ts.log_debug(f'Setting variable {self.rt_lab_model}/{variable} = {value}')
                self.set_var(variable, value)

    def get_signals(self, verbose=False):
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
            if verbose:
                self.ts.log_debug('Signal #%s: %s [%s] = %s' % (signal_parameters[sig][1],
                                                                signal_parameters[sig][2],
                                                                signal_parameters[sig][3],
                                                                signal_parameters[sig][6]))
        return signal_params

    def get_sample_time(self):
        """
        Get the acquisition sample time from the model

        :return: time
        """
        # Get the acquisition sample time for the specified group. The acquisition sample time is the interval between
        # two values inside an acquisition frame.  sampleTime = RtlabApi.GetAcqSample Time(acqGroup)
        # sample_time_step = RtlabApi.GetAcqSampleTime()

        calculationStep, timeFactor = RtlabApi.GetTimeInfo()
        # self.ts.log_debug('Time Info. calculationStep = %s, timeFactor = %s' % (calculationStep, timeFactor))
        return calculationStep

    def set_stop_time(self, stop_time):
        """
        Set the simulation stop time

        :return: None
        """

        if RtlabApi.GetStopTime() != stop_time:
            RtlabApi.SetStopTime(stop_time)
        else:
            self.ts.log_warning('Stop time already set to %s' % stop_time)
        return RtlabApi.GetStopTime()

    def get_time(self):
        """
        Get simulation time from the clock signal
        :return: simulation time in sec
        """

        try:
            if self.model_state() == 'Model Running':
                _, model_name = RtlabApi.GetCurrentModel()
                model_name = model_name.rstrip('.mdl').rstrip('.slx')

                # todo: fix this to be generic
                try:
                    sig = model_name + '/SM_Source/Clock/port1'
                    sim_time = RtlabApi.GetSignalsByName(sig)
                except Exception as e:
                    sig = model_name + '/SM_LOHO13/Dynamic Load Landfill/Clock1/port1'
                    sim_time = RtlabApi.GetSignalsByName(sig)

                return sim_time
            else:
                self.ts.log_debug('Can not read simulation time becauase the simulation is not running. Returning 1e6.')
                sim_time = 1.0e6  # ensures that the simulation loop will stop in the script
                return sim_time
        except Exception as e:
            self.ts.log_debug('Could not get time for simulation. Simulation likely completed. Returning 1e6. %s' % e)
            sim_time = 1.0e6  # ensures that the simulation loop will stop in the script
            return sim_time


if __name__ == "__main__":

    import time
    system_info = RtlabApi.GetTargetNodeSystemInfo("Target_3")
    for i in range(len(system_info)):
        print((system_info[i]))
    print(("OPAL-RT - Platform version {0} (IP address : {1})".format(system_info[1], system_info[6])))

    projectName = r"C:/Users/DETLDAQ/OPAL-RT/RT-LABv2020.1_Workspace_new/1547.1_UI_CatB_22/1547.1_UI_CatB_22.llp"

    RtlabApi.OpenProject(projectName)
    RtlabApi.GetParameterControl(1)
    RtlabApi.GetSystemControl(1)
    RtlabApi.GetAcquisitionControl(1)

    RtlabApi.SetAcqBlockLastVal(0, 1)
    print(RtlabApi.GetAcqBlockLastVal())

    acquisitionGroup = 0
    synchronization = 0
    interpolation = 0
    threshold = 0
    acqTimeStep = 0.001

    for i in range(10):

        values, (missedData, offset, simulationTime, sampleSec), simulationTimeStep, endFrame = \
            RtlabApi.GetAcqGroupSyncSignals(acquisitionGroup, synchronization, interpolation,
                                            threshold, acqTimeStep)
        print('Simulation Time = %s, Acquired signals from acquisition: %s' %
              (simulationTime, str(values)[0:80]))

        time.sleep(1)

    for i in range(10):
        frames = 0  # the number of frames is configured in the probe control for the model in RT-Lab
        while 1:
            values, (missedData, offset, simulationTime, sampleSec), simulationTimeStep, endFrame = \
                RtlabApi.GetAcqGroupSyncSignals(acquisitionGroup, synchronization, interpolation,
                                                threshold, acqTimeStep)

            frames += 1
            if endFrame:  # if the frame is over
                print('Simulation Time = %s, Acquired signals from acquisition: %s' %
                      (simulationTime, str(values)[0:300]))
                break  # stop loop

        # print('Total frames: %s' % frames)
        time.sleep(1)

    # io_interface = RtlabApi.GetIOInterfaces()
    # print('GetIOInterfaces: %s' % io_interface)
    # print(type(io_interface[0]))
    # io_name = io_interface[0]['name']
    # print('io_name: %s' % io_name)
    # io_points = RtlabApi.GetConnectionPointsForIO()
    # for point in range(len(io_points)):
    #     print(io_points[point])
    #
    # control_signals = RtlabApi.GetControlSignals()
    # for sig in range(len(control_signals)):
    #     print('GetControlSignals[%d]: %s' % (sig, control_signals[sig]))



    # status, _ = RtlabApi.GetModelState()
    # if status == RtlabApi.MODEL_LOADABLE:
    #     realTimeMode = RtlabApi.HARD_SYNC_MODE
    #     timeFactor = 1
    #     RtlabApi.Load(realTimeMode, timeFactor)
    #     print("The model is loaded.")
    # else:
    #     print("The model is not loadable.")
    #
    # status, _ = RtlabApi.GetModelState()
    # print('Status is: %s' % status)
    # if status == RtlabApi.MODEL_PAUSED:
    #     RtlabApi.Execute(1)
    #     modelState, realTimeMode = RtlabApi.GetModelState()
    #     "The model state is now %s." % RtlabApi.OP_MODEL_STATE(modelState)
    # sleep(2)
    #
    # model_parameters = RtlabApi.GetParametersDescription()
    # for param in range(len(model_parameters)):
    #     print('Param: %s, %s is %s' % (model_parameters[param][1],
    #                                    model_parameters[param][2],
    #                                    model_parameters[param][4]))

    # print('Simulation time is: %s' % [RtlabApi.GetTimeInfo()])
    # print('Simulation time is: %s' % (RtlabApi.GetPauseTime()))
    # print('Simulation time is: %s' % (RtlabApi.GetStopTime()))
    # print('Simulation time is: %s' % (RtlabApi.GetAcqSampleTime()))

    # RtlabApi.Pause()
    # sleep(2)

    '''
    RtlabApi.CloseProject()

    RtlabApi.SetParametersByName("PF818072_test_model/sm_computation/Rocof/Value", 10.)
    RtlabApi.SetParametersByName("PF818072_test_model/sm_computation/Rocom/Value", 10.)
    sleep(2)
    '''

    ''' Change phase and amplitude of sine wave
    # ampl = [2, 2, 2]
    # phases = [0, 60, 120]
    for loop in range(1, 10):
        ampl = [1.*loop, 1.*loop, 1.*loop]
        phases = [0.+5.*loop, 120.-5.*loop, 240.+2.*loop]
        print('Amplitudes are: %s, Phase angles are: %s' % (ampl, phases))
        RtlabApi.SetParametersByName((mag[1], mag[2], mag[3], ang[1], ang[2], ang[3]),
                                     (ampl[0], ampl[1], ampl[2], phases[0], phases[1], phases[2]))
        sleep(1)
    '''

    '''
    # Compile Model
    model_info = {}
    model_info["mdlFolder"], model_info["mdlName"] = RtlabApi.GetCurrentModel()  # Get path to model
    model_info["mdlPath"] = os.path.join(model_info["mdlFolder"], model_info["mdlName"])
    RtlabApi.RegisterDisplay(RtlabApi.DISPLAY_REGISTER_ALL)

    # Set attribute on project to force to recompile (optional)
    model_info["modelId"] = RtlabApi.FindObjectId(RtlabApi.OP_TYPE_MODEL, model_info["mdlPath"])
    RtlabApi.SetAttribute(model_info["modelId"], RtlabApi.ATT_FORCE_RECOMPILE, True)

    # Launch compilation
    compilationSteps = RtlabApi.OP_COMPIL_ALL_NT | RtlabApi.OP_COMPIL_ALL_LINUX
    RtlabApi.StartCompile2((("", compilationSteps),), )
    print('Compilation started.')

    # Wait until the end of the compilation
    status = RtlabApi.MODEL_COMPILING
    while status == RtlabApi.MODEL_COMPILING:
        try:
            # Check status every 0.5 second
            sleep(0.5)

            # Get new status. To be done before DisplayInformation because DisplayInformation may generate an Exception
            # when there is nothing to read
            status, _ = RtlabApi.GetModelState()

            # Display compilation log into Python console
            _, _, msg = RtlabApi.DisplayInformation(100)
            while len(msg) > 0:
                print(msg)
                _, _, msg = RtlabApi.DisplayInformation(100)

        except Exception as exc:
            # Ignore error 11 which is raised when RtlabApi.DisplayInformation is called whereas there is no
            # pending message
            info = sys.exc_info()
            if info[1][0] != 11:  # 'There is currently no data waiting.'
                # If a exception occur: stop waiting
                print("An error occurred during compilation.")
                raise

    # Because we use a comma after print when forward compilation log into python log we have to ensure to
    # write a carriage return when finished.
    print('')

    # Get project status to check is compilation succeeded
    status, _ = RtlabApi.GetModelState()
    if status == RtlabApi.MODEL_LOADABLE:
        print('Compilation success.')
    else:
        print('Compilation failed.')

    status, _ = RtlabApi.GetModelState()
    if status == RtlabApi.MODEL_LOADABLE:
        realTimeMode = RtlabApi.HARD_SYNC_MODE
        # Other options: SIM_MODE, SOFT_SIM_MODE, SIM_W_NO_DATA_LOSS_MODE or SIM_W_LOW_PRIO_MODE
        timeFactor = 1
        RtlabApi.Load(realTimeMode, timeFactor)
        print("The model is loaded.")
    else:
        print("The model is not loadable.")

    # Run simulation
    status, _ = RtlabApi.GetModelState()
    if status == RtlabApi.MODEL_PAUSED:
        RtlabApi.Execute(1)
        modelState, realTimeMode = RtlabApi.GetModelState()
    print("The model state is now %s." % RtlabApi.OP_MODEL_STATE(modelState))

    RtlabApi.CloseProject()
    '''


