"""
Copyright (c) 2017, Sandia National Labs and SunSpec Alliance
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

try:
    import typhoon
    import typhoon.api.hil as cp  # control panel
    from typhoon.api.schematic_editor import model
    import typhoon.api.pv_generator as pv
except Exception as e:
    print(('Typhoon HIL API not installed. %s' % e))

typhoon_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Typhoon'
}


def hil_info():
    return typhoon_info


def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = typhoon_info['mode']

    info.param_add_value('hil.mode', typhoon_info['mode'])
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode, active=gname('mode'),
                     active_value=mode, glob=True)
    info.param(pname('auto_config'), label='Configure HIL at beginning of test', default='Disabled',
               values=['Enabled', 'Disabled'])
    info.param(pname('eut_nominal_voltage'), label='EUT nameplate voltage (V)', default=230.0)
    info.param(pname('eut_nominal_frequency'), label='EUT nominal frequency (Hz)', default=50.0)

    info.param(pname('model_name'), label='Model file name (.tse)',
               default=r"ASGC_Closed_loop_full_model.tse")
    info.param(pname('setting_name'), label='Settings file name (.runx)',
               default=r"ASGC_full_settings.runx")
    info.param(pname('hil_working_dir'),
               label='Absolute path of working directory where the .tse and the .runx are located',
               default=r"c:/Users/Public/TyphoonHIL/ModelA")

    info.param('hil.typhoon.debug', label='Debug level of HIL API', default=0)


GROUP_NAME = 'typhoon'


class HIL(hil.HIL):
    """
    Typhoon HIL implementation.

    Valid parameters:
      mode - 'Typhoon'
      auto_config - ['Enabled', 'Disabled']
    """

    def __stripExtension__(self, var, extention):
        try:
            fname = var.split('.')
            if fname[-1] == extention:
                fname = fname[:-1]
            var = '.'.join(fname)
            return var
        except Exception as e:
            raise hil.HILGenericException("Failed modelname parsing and formatting: %s" % e)

    def __init__(self, ts):
        hil.HIL.__init__(self, ts)

        self.ts = ts
        self.auto_config = ts.param_value('hil.typhoon.auto_config')
        self.eut_nominal_power = ts.param_value('hil.typhoon.eut_nominal_power')
        self.v = ts.param_value('hil.typhoon.eut_nominal_voltage')
        self.f = ts.param_value('hil.typhoon.eut_nominal_frequency')

        self.model_name = ts.param_value('hil.typhoon.model_name')
        self.pv_name = ts.param_value('hil.typhoon.pv_name')
        self.settings_file_name = ts.param_value('hil.typhoon.setting_name')
        self.hil_model_dir = ts.param_value('hil.typhoon.hil_working_dir')
        self.hil_model_dir = self.hil_model_dir.replace('\\', '/')+'/'
        self.debug = False

        try:
            self.debug_level = int(ts.param_value('hil.typhoon.debug'))
        except:
            self.debug_level = 0

        if self.debug_level > 0:
            self.debug = True

        if self.debug:
            cp.set_debug_level(level=self.debug_level)

        # Check and remove extensions:
        try:
            self.model_name = self.__stripExtension__(self.model_name, 'tse')
            self.settings_file_name = self.__stripExtension__(self.settings_file_name, 'runx')
        except Exception as e:
            raise e

        if self.auto_config == 'Enabled':
            ts.log('Configuring the Typhoon HIL Emulation Environment.')
            self.config()

    def info(self):
        self.ts.log(' ')
        self.ts.log('available ambient temperatures = %s' % cp.available_ambient_temperatures())
        self.ts.log('available analog signals = %s' % cp.available_analog_signals())
        self.ts.log('available contactors = %s' % cp.available_contactors())
        self.ts.log('available digital signals = %s' % cp.available_digital_signals())
        self.ts.log('available machines = %s' % cp.available_machines())
        self.ts.log('available pe switching blocks = %s' % cp.available_pe_switching_blocks())
        self.ts.log('available pvs = %s' % cp.available_pvs())
        self.ts.log('available sources = %s' % cp.available_sources())
        self.ts.log('capture in progress = %s' % cp.capture_in_progress())

    def control_panel_info(self):
        # If using the TI Control Panel API
        self.ts.log('available analog meters = %s' % typhoon.api.ti_control_panel.available_analog_meters())
        self.ts.log('available com ports = %s' % typhoon.api.ti_control_panel.available_com_ports())
        self.ts.log('available commands = %s' % typhoon.api.ti_control_panel.available_commands())
        self.ts.log('available flags = %s' % typhoon.api.ti_control_panel.available_flags())
        self.ts.log('available parameters = %s' % typhoon.api.ti_control_panel.available_parameters())
        self.ts.log('available analog meters = %s' % typhoon.api.ti_control_panel.available_references())
        return typhoon.api.ti_control_panel.available_references()

    def __buildHandler__(self):
        """
        :todo check if model already built
        :return:
        """

        if not os.path.exists(self.hil_model_dir + self.model_name + r" Target files/" + self.model_name + r".cpd"):
            if not self.load_schematic():
                raise hil.HILModelException("Failed to load Schematic!")

            if not self.compile_model():
                raise hil.HILCompileException("Failed to compile model!")
        else:
            self.ts.log("Found cpd! Trying to use precompiled version")

    def __loadHandler__(self):
        self.ts.sleep(1)

        try:
            self.ts.log("Trying to load HIL model {}".format(self.model_name))
            for i in range(0, 4):
                try:
                    self.__buildHandler__()
                except Exception as e:
                    self.ts.log("Failed build with {}".format(e))
                    continue
                if self.load_model_on_hil():
                    self.ts.log("Model loaded after {} tries".format(i))
                    return True
                else:
                    self.ts.log("Retry {}/4: Trying to load HIL Model {}".format(i,self.model_name))
                    # We will delete the Entire compiler output folder
                    import shutil
                    shutil.rmtree(self.hil_model_dir + self.model_name + r" Target files/", ignore_errors=True)
            raise hil.HILModelException("Failed to load the model")
        except Exception as e:
            raise hil.HILRuntimeException("Failed to load model! {}".format(e))

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        self.ts.log('Checking on HIL HW settings...')
        hw = model.get_hw_settings()
        self.ts.log_debug('HIL hardware is %s' % hw)
        # model.set_simulation_time_step(self.sim_time_step)

        try:
            self.__loadHandler__()
        except:
            raise

        self.init_sim_settings()
        self.ts.log("HIL simulation successfully prepared for execution.")

        self.ts.log("Starting Simulation...")
        self.start_simulation()

        """
        This is a rather crude way to wait for EUT to start up! 
        """
        # let the inverter startup
        sleeptime = 15
        try:
            # perturb irradiance
            cp.set_pv_amb_params("PV1", illumination=995.)
            self.ts.sleep(1)
            cp.set_pv_amb_params("PV1", illumination=1000.)
        except Exception as e:
            self.ts.log('Attempted to perturb PV1 irradiance to get inverter to start. This failed. %s' % e)
        for i in range(1, sleeptime):
            print(("Waiting another %d seconds until the inverter starts." % (sleeptime-i)))
            self.ts.sleep(1)

    def load_schematic(self):
        '''
        Load HIL simulation schematic
        '''

        if self.model_name[-4:] == ".tse":
            model_file = self.hil_model_dir + self.model_name
        else:
            model_file = self.hil_model_dir + self.model_name + r".tse"

        self.ts.log("Model File: %s" % model_file)

        if os.path.isfile(model_file):
            self.ts.log_debug("Model file exists! Starting to compile power electronic parts...")
        else:
            self.ts.log_debug("Model file does not exist! {}".format(model_file))
            status = False
            return status

        # load schematic (with default component parameters)
        if not model.load(model_file, debug=self.debug):
            self.ts.log_warning("Model did not load!")
            status = False
            return status
        return True

    def compile_model(self):
        '''
        Compile model
        '''
        if not model.compile():
            self.ts.log_warning("Model did not compile!")
            status = False
            return status
        return True

    def load_model_on_hil(self):
        '''
        Load model
        '''

        hil_model_file = self.hil_model_dir + self.model_name + r" Target files/" + self.model_name + r".cpd"
        self.ts.log("Model File: %s" % hil_model_file)

        if os.path.isfile(hil_model_file):
            self.ts.log_debug("HIL model (.cpd) file exists!")
        else:
            self.ts.log_debug("HIL model (.cpd) file does not exist!")
            status = False
            return status

        if not cp.load_model(file=hil_model_file):
            self.ts.log_warning("HIL model (.cpd) did not load!")
            return False

        return True

    def init_sim_settings(self):
        '''
        Configure simulation settings
        '''
        if self.settings_file_name[-5:] == ".runx":
            settings_file = self.hil_model_dir + self.settings_file_name
        else:
            settings_file = self.hil_model_dir + self.settings_file_name + r".runx"


        self.ts.log("Model File: %s" % settings_file)

        if os.path.isfile(settings_file):
            self.ts.log_debug("Settings file (.runx) file exists!")
        else:
            self.ts.log_debug("Settings file (.runx) file does not exist!")
            status = False
            return status

        # Open existing settings file.
        if not cp.load_settings_file(file=settings_file):
            self.ts.log_warning("Settings file (.runx) did not work did not compile!")
            return False
        return True

    def init_control_panel(self):
        pass

    def stop_simulation(self):
        '''
        Stop simulation
        '''
        cp.stop_simulation()

    def start_simulation(self):
        '''
        Start simulation
        '''
        cp.start_simulation()

if __name__ == "__main__":


    #         self.auto_config = ts.param_value('hil.typhoon.auto_config')
    #         self.eut_nominal_power = ts.param_value('hil.typhoon.eut_nominal_power')
    #         self.v = ts.param_value('hil.typhoon.eut_nominal_voltage')
    #         self.f = ts.param_value('hil.typhoon.eut_nominal_frequency')
    #
    #         self.model_name = ts.param_value('hil.typhoon.model_name')
    #         self.pv_name = ts.param_value('hil.typhoon.pv_name')
    #         self.settings_file_name = ts.param_value('hil.typhoon.setting_name')
    #         self.hil_model_dir = ts.param_value('hil.typhoon.hil_working_dir')
    #         self.hil_model_dir = self.hil_model_dir.replace('\\', '/')+'/'

    class ts(object):
        def param_value(self, v):
            if v == "hil.typhoon.hil_working_dir": return 'C:\\Users\\AblingerR\\Documents\\AITProjects\\EPRI\\Anti-Islanding'
            if v == "hil.typhoon.model_name": return 'ASGC_TestSuite_AI_V6_3_YtoMP_EPRI_60Hz_50p'
            if v == "hil.typhoon.hil.typhoon.setting_name": return 'ASGC_TestSuite_AI_full_settings_HIL402'

            return v

        def log(self, e):
            print(("{}".format(e)))

        def log_debug(self, e):
            self.log("DEBUG: {}".format(e))

        def log_warning(self, e):
            self.log("WARNING: {}".format(e))

        def sleep(self, n):
            import time
            time.sleep(n)

        pass

    e = ts()


    t = HIL(e)
    t.config()








    # import sys
    # import time
    # import numpy as np
    # import math

    # sys.path.insert(0, r'C:/Typhoon HIL Control Center/python_portable/Lib/site-packages')
    # #sys.path.insert(0, r'C:/Typhoon HIL Control Center/python_portable/Scripts')
    # sys.path.insert(0, r'C:/Typhoon HIL Control Center/python_portable')
    # sys.path.insert(0, r'C:/Typhoon HIL Control Center')
    # #sys.path.insert(0, r'C:/Typhoon HIL Control Center/typhoon/conf')
    # #sys.path.insert(0, r'C:/Typhoon HIL Control Center/typhoon/conf/components')
    #
    # import typhoon.api.hil_control_panel as hil
    # from typhoon.api.schematic_editor import model
    # import os
    #
    # hil.set_debug_level(level=1)
    # hil.stop_simulation()
    #
    # model.get_hw_settings()
    # #model_dir = r'D:/SVP/SVP Directories 11-7-16/UL 1741 SA Dev/Lib/TyphoonASGC/'
    # #print model_dir, os.path.isfile(model_dir)
    # if not model.load(r'D:/SVP/SVP Directories 11-7-16/UL 1741 SA Dev/Lib/TyphoonASGC/ASGC_AI.tse'):
    #     print "Model did not load!"
    #
    # if not model.compile():
    #     print "Model did not compile!"
    #
    # # first we need to load model
    # hil.load_model(file=r'D:/SVP/SVP Directories 11-7-16/UL 1741 SA Dev/Lib/TyphoonASGC/ASGC_AI Target files/ASGC_AI.cpd')
    #
    # # we could also open existing settings file...
    # hil.load_settings_file(file=r'D:/SVP/SVP Directories 11-7-16/UL 1741 SA Dev/Lib/TyphoonASGC/settings.runx')
    #
    # # after setting parameter we could start simulation
    # hil.start_simulation()
    #
    # # let the inverter startup
    # sleeptime = 15
    # for i in range(1, sleeptime):
    #     print ("Waiting another %d seconds until the inverter starts. Power = %f." %
    #            ((sleeptime-i), hil.read_analog_signal(name='Pdc')))
    #     time.sleep(1)
    #
    #
    # '''
    # Setup the circuit for anti-islanding
    # '''
    # V_nom = 230.0
    # P_rating = 34500
    # freq_nom = 50
    # resistor = (V_nom**2)/P_rating
    # capacitor = P_rating/(2*np.pi*freq_nom*(V_nom**2))
    # inductor = (V_nom**2)/(2*np.pi*freq_nom*P_rating)
    # resonance_freq = 1/(2*np.pi*math.sqrt(capacitor*inductor))
    # Qf = resistor*(math.sqrt(capacitor/inductor))
    # X_C = 1/(2*np.pi*freq_nom*capacitor)
    # X_L = (2*np.pi*freq_nom*inductor)
    #
    # print('R = %0.3f, L = %0.3f, C = %0.3f' % (resistor, capacitor, inductor))
    # print('F_resonance = %0.3f, Qf = %0.3f, X_C = %0.3f, X_L = %0.3f' % (resonance_freq, Qf, X_C, X_L))
    #
    # R3 = 0
    # R4 = 0
    # R5 = 0
    # L1 = 0
    # L2 = 0
    # L3 = 0
    # C3 = capacitor
    # C4 = capacitor
    # C5 = capacitor
    # L5 = inductor
    # L6 = inductor
    # L4 = inductor
    # R14 = resistor
    # R15 = resistor
    # R16 = resistor
    #
    # '''
    # set_component_property(component, property, value)
    # Sets component property value to provided value.
    #
    # Parameters:
    # component - name of component.
    # property - name of property.
    # value - new property value.
    # Returns:
    # True if successful, False otherwise.
    #
    # set_simulation_time_step(time_step)
    # Set schematic model simulation time time_step
    #
    # Arguments:
    # simulation time step - time step used for simulation
    # Returns:
    # True if successful, False otherwise
    # '''
    #
    # '''
    # Waveform capture
    # '''
    # simulationStep = hil.get_sim_step()
    # print('Simulation time step is %f' % simulationStep)
    # trigsamplingrate = 1./simulationStep
    # pretrig = 1
    # posttrig = 2.5
    # trigval = 0.5
    # trigtimeout = 5
    # trigcondition = 'Falling edge'
    # trigchannel = 'S1_fb'
    # trigacqchannels = [['V( V_DC3 )', 'I( Ipv )', 'V( V_L1 )', 'I( Ia )'], ['S1_fb']]
    # n_analog_channels = 4
    # save_file_name = r'D:\SVP\SVP Directories 11-7-16\UL 1741 SA Dev\Results\capture_test.mat'
    #
    # # signals for capturing
    # channelSettings = trigacqchannels
    #
    # # cpSettings - list[decimation,numberOfChannels,numberOfSamples, enableDigitalCapture]
    # numberOfSamples = int(trigsamplingrate*(pretrig+posttrig))
    # print('Numer of Samples is %d' % numberOfSamples)
    # if numberOfSamples > 32e6/len(channelSettings):
    #     print('Number of samples is not less than 32e6/numberOfChannels!')
    #     numberOfSamples = 32e6/n_analog_channels
    #     print('Number of samples set to 32e6/numberOfChannels!')
    # elif numberOfSamples < 256:
    #     print('Number of samples is not greater than 256!')
    #     numberOfSamples = 256
    #     print('Number of samples set to 256.')
    # elif numberOfSamples % 2 == 1:
    #     print('Number of samples is not even!')
    #     numberOfSamples += 1
    #     print('Number of samples set to %d.' % numberOfSamples)
    #
    # captureSettings = [1, n_analog_channels, numberOfSamples, True]
    #
    # '''
    # triggerSource - channel or the name of signal that will be used for triggering (int value or string value)
    #     Note:
    #     In case triggerType == Analog:
    #         triggerSource (int value) - value can be > 0 and <= "numberOfChannels" if we enter channel number.
    #         triggerSource (string value) - value is Analog signal name that we want to use for trigger source. Analog Signal
    #         name must be one of signal names from list of signals that we want to capture ("chSettings" list, see below).
    #     In case triggerType == Digital:
    #         triggerSource (int value) - value must be > 0 and maximal value depends of number of digital signals in loaded model
    #         triggerSource (string value) - value is Digital signal name that we want to use for trigger source.
    #
    # threshold - trigger threshold (float value)
    #     Note: "threshold" is only used for "Analog" type of trigger. If you use "Digital" type of trigger, you still need to
    #     provided this parameter (for example 0.0 )
    #
    # edge - trigger on "Rising edge" or "Falling edge"
    #
    # triggerOffset - Define the number of samples in percentage to capture before the trigger event (for example 20, if the
    #     numberOfSamples is 100k, 20k samples before and 80k samples after the trigger event will be captured)
    # '''
    # # trSettings - list[triggerType,triggerSource,threshold,edge,triggerOffset]
    # # triggerSettings = ["Analog", 'I( Irms1 )', trigval, trigcondition, (pretrig*100.)/(pretrig+posttrig)]
    # # triggerSettings = ["Digital", 'S1_fb', trigval, trigcondition, (pretrig*100.)/(pretrig+posttrig)]
    # triggerSettings = ["Forced"]
    # # print('digital signals = %s' % hil.available_digital_signals())
    #
    # # python list is used for data buffer
    # capturedDataBuffer = []
    #
    # print captureSettings
    # print triggerSettings
    # print channelSettings
    # print('Power = %0.3f' % hil.read_analog_signal(name='Pdc'))
    # if hil.read_digital_signal(name='S1_fb') == 1:
    #     print('Contactor is closed.')
    # else:
    #     print('Contactor is open.')
    #
    # # start capture process...
    # if hil.start_capture(captureSettings,
    #                      triggerSettings,
    #                      channelSettings,
    #                      dataBuffer=capturedDataBuffer,
    #                      fileName=save_file_name,
    #                      timeout=trigtimeout):
    #
    #     time.sleep(0.5)
    #
    #     #print hil.available_contactors()
    #     print("Actuating S1 Contactor")
    #     hil.set_contactor_control_mode('S1', swControl=True)
    #     hil.set_contactor_state('S1', swState=False, executeAt=None)  # open contactor
    #
    #     if hil.read_digital_signal(name='S1_fb') == 1:
    #         print('Contactor is closed.')
    #     else:
    #         print('Contactor is open.')
    #
    #     # when capturing is finished...
    #     while hil.capture_in_progress():
    #         pass
    #
    #     # unpack data from data buffer
    #     (signalsNames, wfm_data, wfm_time) = capturedDataBuffer[0]
    #
    #     # unpack data for appropriate captured signals
    #     V_dc = wfm_data[0]  # first row for first signal and so on
    #     i_dc = wfm_data[1]
    #     V_ac = wfm_data[2]
    #     i_ac = wfm_data[3]
    #     contactor_trig = wfm_data[4]
    #
    #     import matplotlib.pyplot as plt
    #     plt.plot(wfm_time, V_ac, 'b', wfm_time, i_ac, 'r', wfm_time, contactor_trig*100, 'k')
    #     plt.show()
    #
    # # hil.set_contactor_state('S1', swState=True, executeAt=None)
    #
    # # read the AC Power
    # # for i in range(1, 10):
    # #     print hil.read_analog_signal(name='Pdc')
    # #     time.sleep(2)
    #
    # # stop simulation
    # hil.stop_simulation()
