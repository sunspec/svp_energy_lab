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
from . import hil
import sys
from time import sleep
# import glob
# import numpy as np

try:
    sys.path.insert(0, "C://OPAL-RT//RT-LAB//2019.1//common//python")
    import RtlabApi
except ImportError as e:
    print(e)


# Dictionary used to create a mapping between a realTimeModeString and a realTimeId
realTimeModeList = {'Hardware Synchronized': 0, 'Simulation': 1,
                    'Software Synchronized': 2, 'Simulation with no data loss': 3,
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

    info.param(pname('target_name'), label='Target name in RT-LAB', default="Target_3")
    info.param(pname('project_name'), label='RT-LAB project name (.llp)', default="IEEE 1547.1 Phase Jump.llp")
    info.param(pname('project_dir'), label='Project Directory', default="\\OpalRT\\IEEE_1547.1_Phase_Jump\\")
    info.param(pname('rt_lab_model'), label='RT-LAB model name', default='3PhaseGeneric')
    info.param(pname('rt_lab_model_dir'), label='RT-LAB Model Directory',
               default="\\OpalRT\\IEEE_1547.1_Phase_Jump\\models")

    info.param(pname('hil_config'), label='Configure HIL in init', default='False', values=['True', 'False'])
    info.param(pname('hil_config_open'), label='Open Project?', default="Yes", values=["Yes", "No"])
    info.param(pname('hil_config_compile'), label='Compilation needed?', default="No", values=["Yes", "No"])
    info.param(pname('hil_config_stop_sim'), label='Stop the simulation before loading/execution?',
               default="Yes", values=["Yes", "No"])
    info.param(pname('hil_config_load'), label='Load the model to target?', default="Yes", values=["Yes", "No"])
    info.param(pname('hil_config_execute'), label='Execute the model on target?', default="Yes", values=["Yes", "No"])


GROUP_NAME = 'opal'


def hil_info():
    return opalrt_info


class HIL(hil.HIL):
    """
    Opal_RT HIL implementation - The default.
    """
    def __init__(self, ts, group_name):
        hil.HIL.__init__(self, ts, group_name)
        self.project_name = self._param_value('project_name')
        self.project_dir = self._param_value('project_dir')

        self.target_name = self._param_value('target_name')

        self.rt_lab_model = self._param_value('rt_lab_model')
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
        self.ts.log('Setting the simulation stop time for 2 hours to run experiment.')
        self.set_stop_time(3600 * 2)
        if self.hil_config_compile == 'Yes':
            self.ts.sleep(1)
            self.ts.log("    Model ID: {}".format(self.compile_model().get("modelId")))
        if self.hil_config_stop_sim == 'Yes':
            self.ts.sleep(1)
            self.ts.log("    {}".format(self.stop_simulation()))
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
        if self.project_name[1] == ':':
            self.ts.log('Assuming project name is an absolute path to .llp file')
            proj_path = self.project_name
        elif self.project_dir[1] == ':':
            self.ts.log('Assuming project directory + project name is an absolute path to .llp file')
            self.project_dir.rstrip('\\') + '\\' + self.project_name
            proj_path = self.project_dir.rstrip('\\') + '\\' + self.project_name
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

        # Set parameter control for later
        parameterControl = 1
        RtlabApi.GetParameterControl(parameterControl)

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
                    sig = model_name + '/SM_Source/Clock1/port1'
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

    system_info = RtlabApi.GetTargetNodeSystemInfo("Target_3")
    for i in range(len(system_info)):
        print((system_info[i]))
    print(("OPAL-RT - Platform version {0} (IP address : {1})".format(system_info[1], system_info[6])))

    '''
    projectName = "C:\\Users\\DETLDAQ\\OPAL-RT\\RT-LABv2019.1_Workspace\\" \
                  "IEEE_1547.1_Phase_Jump\\IEEE_1547.1_Phase_Jump.llp"
    RtlabApi.OpenProject(projectName)
    parameterControl = 1
    RtlabApi.GetParameterControl(parameterControl)

    status, _ = RtlabApi.GetModelState()
    if status == RtlabApi.MODEL_LOADABLE:
        realTimeMode = RtlabApi.HARD_SYNC_MODE
        timeFactor = 1
        RtlabApi.Load(realTimeMode, timeFactor)
        print("The model is loaded.")
    else:
        print("The model is not loadable.")

    for loop in range(2):
        print("Run times: %s" % loop)

        status, _ = RtlabApi.GetModelState()
        print('Status is: %s' % status)
        if status == RtlabApi.MODEL_PAUSED:
            RtlabApi.Execute(1)
            modelState, realTimeMode = RtlabApi.GetModelState()
            "The model state is now %s." % RtlabApi.OP_MODEL_STATE(modelState)
        sleep(2)

        model_parameters = RtlabApi.GetParametersDescription()
        for param in range(len(model_parameters)):
            print('Param: %s, %s is %s' % (model_parameters[param][1],
                                           model_parameters[param][2],
                                           model_parameters[param][4]))

        # print('Simulation time is: %s' % [RtlabApi.GetTimeInfo()])
        # print('Simulation time is: %s' % (RtlabApi.GetPauseTime()))
        # print('Simulation time is: %s' % (RtlabApi.GetStopTime()))
        # print('Simulation time is: %s' % (RtlabApi.GetAcqSampleTime()))

        RtlabApi.Pause()
        sleep(2)

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
                print msg,
                _, _, msg = RtlabApi.DisplayInformation(100)

        except Exception, exc:
            # Ignore error 11 which is raised when RtlabApi.DisplayInformation is called whereas there is no
            # pending message
            info = sys.exc_info()
            if info[1][0] != 11:  # 'There is currently no data waiting.'
                # If a exception occur: stop waiting
                print("An error occurred during compilation.")
                raise

    # Because we use a comma after print when forward compilation log into python log we have to ensure to
    # write a carriage return when finished.
    print ''

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



