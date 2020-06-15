"""
Communications to NI PCIe Cards

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
import time
import traceback
import glob
from . import waveform
from . import dataset

# Wrap driver import statements in try-except clauses to avoid SVP initialization errors
try:
    from PyDAQmx import *
except Exception as e:
    print('Error: PyDAQmx python package not found!')  # This will appear in the SVP log file.
    # raise  # programmers can raise this error to expose the error to the SVP user
try:
    import numpy as np
except Exception as e:
    print('Error: numpy python package not found!')  # This will appear in the SVP log file.
    # raise  # programmers can raise this error to expose the error to the SVP user
try:
    from . import waveform_analysis
except Exception as e:
    print('Error: waveform_analysis file not found!')  # This will appear in the SVP log file.
    # raise  # programmers can raise this error to expose the error to the SVP user

data_points = [
    'TIME',
    'DC_V',
    'DC_I',
    'AC_VRMS',
    'AC_IRMS',
    'DC_P',
    'AC_S',
    'AC_P',
    'AC_Q',
    'AC_FREQ',
    'AC_PF',
    'TRIG',
    'TRIG_GRID'
]

# data_points = [
#     'time',
#     'dc_voltage',
#     'dc_current',
#     'ac_voltage',
#     'ac_current',
#     'dc_watts',
#     'ac_va',
#     'ac_watts',
#     'ac_vars',
#     'ac_freq',
#     'ac_pf',
#     'trigger',
#     'ametek_trigger'
# ]
#
# data_points_label = {
#     'time': 'Test Time (s)',
#     'dc_voltage': 'DC Voltage (V)',
#     'dc_current': 'DC Current (A)',
#     'ac_voltage': 'AC Voltage (V)',
#     'ac_current': 'AC Current (A)',
#     'dc_watts': 'DC Active Power (W)',
#     'ac_va': 'AC Apparent Power (VA)',
#     'ac_watts': 'AC Active Power (W)',
#     'ac_vars': 'AC Reactive Power (Var)',
#     'ac_freq': 'Frequency (Hz)',
#     'ac_pf': 'AC Power Factor',
#     'trigger': 'Communication Trigger',
#     'ametek_trigger': 'Grid Transient Trigger'
# }

# Data channels for Node 1
dsm_points_1 = {
    'dc_voltage': 'DC_Voltage_1',
    'dc_current': 'DC_Current_1',
    'ac_voltage': 'AC_Voltage_1',
    'ac_current': 'AC_Current_1',
    'ametek_trigger': 'Ametek_Trigger'
}

# Data channels for Node 2
dsm_points_2 = {
    'dc_voltage': 'DC_Voltage_2',
    'dc_current': 'DC_Current_2',
    'ac_voltage': 'AC_Voltage_2',
    'ac_current': 'AC_Current_2',
    'ametek_trigger': 'Ametek_Trigger'
}

# Data channels for Node 3
dsm_points_3 = {
    'dc_voltage': 'DC_Voltage_3',
    'dc_current': 'DC_Current_3',
    'ac_voltage': 'AC_Voltage_3',
    'ac_current': 'AC_Current_3',
    'ametek_trigger': 'Ametek_Trigger'
}

# Data channels for Node 4
dsm_points_4 = {
    'dc_voltage': 'DC_Voltage_4',
    'dc_current': 'DC_Current_4',
    'ac_voltage': 'AC_Voltage_4',
    'ac_current': 'AC_Current_4',
    'ametek_trigger': 'Ametek_Trigger'
}

# Data channels for Node 5
dsm_points_5 = {
    'dc_voltage': 'DC_Voltage_5',
    'dc_current': 'DC_Current_5',
    'ac_voltage': 'AC_Voltage_5',
    'ac_current': 'AC_Current_5',
    'ametek_trigger': 'Ametek_Trigger'
}

# Data channels for Node 6
dsm_points_6 = {
    'dc_voltage': 'DC_Voltage_6',
    'dc_current': 'DC_Current_6',
    'ac_voltage': 'AC_Voltage_6',
    'ac_current': 'AC_Current_6',
    'ametek_trigger': 'Ametek_Trigger'
}

# Data channels for Node 7
dsm_points_7 = {
    'dc_voltage': 'DC_Voltage_7',
    'dc_current': 'DC_Current_7',
    'ac_voltage': 'AC_Voltage_7',
    'ac_current': 'AC_Current_7',
    'ametek_trigger': 'Ametek_Trigger'
}

# Data channels for Node 8
dsm_points_8 = {
    'dc_voltage': 'DC_Voltage_8',
    'dc_current': 'DC_Current_8',
    'ac_voltage': 'AC_Voltage_8',
    'ac_current': 'AC_Current_8',
    'ametek_trigger': 'Ametek_Trigger'
}

# Data channels for Node 9
dsm_points_9 = {
    'dc_voltage': 'DC_Voltage_9',
    'dc_current': 'DC_Current_9',
    'ac_voltage': 'AC_Voltage_9',
    'ac_current': 'AC_Current_9',
    'ametek_trigger': 'Ametek_Trigger'
}

# Data channels for Node 10
dsm_points_10 = {
    'dc_voltage': 'DC_Voltage_10',
    'dc_current': 'DC_Current_10',
    'ac_voltage': 'AC_Voltage_10',
    'ac_current': 'AC_Current_10',
    'ametek_trigger': 'Ametek_Trigger'
}

dsm_points_map = {
    '1': dsm_points_1,
    '2': dsm_points_2,
    '3': dsm_points_3,
    '4': dsm_points_4,
    '5': dsm_points_5,
    '6': dsm_points_6,
    '7': dsm_points_7,
    '8': dsm_points_8,
    '9': dsm_points_9,
    '10': dsm_points_10
}

wfm_points_label = {
    'Time': 'TIME',
    'dc_voltage': 'DC_V',
    'dc_current': 'DC_I',
    'ac_voltage': 'AC_V_1',
    'ac_current': 'AC_I_1',
    'ac_freq': 'FREQ',
    'ametek_trigger': 'EXT'
}

wfm_channels = ['AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'EXT']

wfm_dsm_channels = {'AC_V_1': 'AC_Voltage',
                    'AC_V_2': 'AC_Voltage',
                    'AC_V_3': 'AC_Voltage',
                    'AC_I_1': 'AC_Current',
                    'AC_I_2': 'AC_Current',
                    'AC_I_3': 'AC_Current',
                    'EXT': 'Ametek_Trigger'}

DSM_CHANNELS = {
'DC_Voltage_1': {'physChan': 'Dev1/ai0', 'v_max': 10, 'v_min': -10, 'expression': '(-0.200215) + (502.538477)*x + (-2.620777)*x**2'},
'DC_Current_1': {'physChan': 'Dev1/ai1', 'v_max': 10, 'v_min': -10, 'expression': '(-0.028190) + (3.996167)*x + (0.000333)*x**2'},
'AC_Voltage_1': {'physChan': 'Dev1/ai2', 'v_max': 1, 'v_min': -1, 'expression': '(0.027155) + (495.776006)*x'},
'AC_Current_1': {'physChan': 'Dev1/ai3', 'v_max': 5, 'v_min': -5, 'expression': '(-0.000866) + (9.964413)*x'},
'DC_Voltage_2': {'physChan': 'Dev1/ai4', 'v_max': 10, 'v_min': -10, 'expression': '(-0.406340) + (505.227480)*x + (-2.720517)*x**2'},
'DC_Current_2': {'physChan': 'Dev1/ai5', 'v_max': 10, 'v_min': -10, 'expression': '(-0.024990) + (3.989978)*x + (0.001525)*x**2'},
'AC_Voltage_2': {'physChan': 'Dev1/ai6', 'v_max': 1, 'v_min': -1, 'expression': '(0.047140) + (495.891095)*x'},
'AC_Current_2': {'physChan': 'Dev1/ai7', 'v_max': 5, 'v_min': -5, 'expression': '(0.000813) + (9.957065)*x + (0.003018)*x**2'},
'DC_Voltage_3': {'physChan': 'Dev1/ai16', 'v_max': 10, 'v_min': -10, 'expression': '(-0.028837) + (501.283070)*x + (-1.793270)*x**2'},
'DC_Current_3': {'physChan': 'Dev1/ai17', 'v_max': 10, 'v_min': -10, 'expression': '(-0.040126) + (3.996069)*x'},
'AC_Voltage_3': {'physChan': 'Dev1/ai18', 'v_max': 1, 'v_min': -1, 'expression': '(-0.014691) + (495.979674)*x'},
'AC_Current_3': {'physChan': 'Dev1/ai19', 'v_max': 5, 'v_min': -5, 'expression': '(-0.001307) + (9.937665)*x + (0.005838)*x**2'},
'DC_Voltage_4': {'physChan': 'Dev1/ai20', 'v_max': 10, 'v_min': -10, 'expression': '(-0.171595) + (502.518465)*x + (-2.683304)*x**2'},
'DC_Current_4': {'physChan': 'Dev1/ai21', 'v_max': 10, 'v_min': -10, 'expression': '(-0.027863) + (3.975655)*x + (0.003658)*x**2'},
'AC_Voltage_4': {'physChan': 'Dev1/ai22', 'v_max': 1, 'v_min': -1, 'expression': '(0.253790) + (496.049979)*x'},
'AC_Current_4': {'physChan': 'Dev1/ai23', 'v_max': 5, 'v_min': -5, 'expression': '(0.003498) + (9.971345)*x'},
'DC_Current_5_CC': {'physChan': 'Dev3/ai1', 'v_max': 10, 'v_min': -10, 'expression': '(-0.074444) + (19.616107)*x + (0.012413)*x**2'},
'DC_Voltage_5': {'physChan': 'Dev3/ai2', 'v_max': 10, 'v_min': -10, 'expression': '(0.024648) + (505.471002)*x'},
'DC_Current_5': {'physChan': 'Dev3/ai3', 'v_max': 10, 'v_min': -10, 'expression': 'x*4'},
'AC_Voltage_5': {'physChan': 'Dev3/ai4', 'v_max': 10, 'v_min': -10, 'expression': 'x*500'},
'AC_Current_5': {'physChan': 'Dev3/ai5', 'v_max': 10, 'v_min': -10, 'expression': '(-0.000570) + (9.974244)*x'},
'DC_Current_6_CC': {'physChan': 'Dev3/ai17', 'v_max': 10, 'v_min': -10, 'expression': '(0.135865) + (19.796144)*x + (0.003069)*x**2'},
'DC_Voltage_6': {'physChan': 'Dev3/ai18', 'v_max': 10, 'v_min': -10, 'expression': '(-0.429993) + (502.509411)*x'},
'DC_Current_6': {'physChan': 'Dev3/ai19', 'v_max': 10, 'v_min': -10, 'expression': 'x*4'},
'AC_Voltage_6': {'physChan': 'Dev3/ai20', 'v_max': 1, 'v_min': -1, 'expression': '(0.952273) + (493.108650)*x'},
'AC_Current_6': {'physChan': 'Dev3/ai21', 'v_max': 5, 'v_min': -5, 'expression': '(-0.000103) + (9.969801)*x'},
'DC_Voltage_7': {'physChan': 'Dev2/ai0', 'v_max': 10, 'v_min': -10, 'expression': '(-0.618849) + (502.524386)*x + (-1.739985)*x**2'},
'DC_Current_7': {'physChan': 'Dev2/ai1', 'v_max': 10, 'v_min': -10, 'expression': '(-0.005516) + (3.999591)*x + (0.001029)*x**2'},
'AC_Voltage_7': {'physChan': 'Dev2/ai2', 'v_max': 1, 'v_min': -1, 'expression': '(0.310880) + (494.854118)*x'},
'AC_Current_7': {'physChan': 'Dev2/ai3', 'v_max': 5, 'v_min': -5, 'expression': '(-0.001034) + (9.967874)*x'},
'DC_Voltage_8': {'physChan': 'Dev2/ai4', 'v_max': 10, 'v_min': -10, 'expression': '(-0.120656) + (500.681775)*x + (-2.078309)*x**2'},
'DC_Current_8': {'physChan': 'Dev2/ai5', 'v_max': 10, 'v_min': -10, 'expression': '(-0.019007) + (3.998394)*x + (0.000245)*x**2'},
'AC_Voltage_8': {'physChan': 'Dev2/ai6', 'v_max': 1, 'v_min': -1, 'expression': '(0.278018) + (494.655385)*x'},
'AC_Current_8': {'physChan': 'Dev2/ai7', 'v_max': 5, 'v_min': -5, 'expression': '(0.002679) + (9.956271)*x + (0.003672)*x**2'},
'DC_Voltage_9': {'physChan': 'Dev2/ai16', 'v_max': 10, 'v_min': -10, 'expression': '(-0.370085) + (503.386468)*x + (-2.200746)*x**2'},
'DC_Current_9': {'physChan': 'Dev2/ai17', 'v_max': 10, 'v_min': -10, 'expression': '(-0.042046) + (3.983510)*x + (0.002614)*x**2'},
'AC_Voltage_9': {'physChan': 'Dev2/ai18', 'v_max': 1, 'v_min': -1, 'expression': '(0.341943) + (494.648311)*x'},
'AC_Current_9': {'physChan': 'Dev2/ai19', 'v_max': 5, 'v_min': -5, 'expression': '(-0.002825) + (9.962082)*x'},
'DC_Voltage_10': {'physChan': 'Dev2/ai20', 'v_max': 10, 'v_min': -10, 'expression': '(-0.340525) + (498.672391)*x + (-1.850054)*x**2'},
'DC_Current_10': {'physChan': 'Dev2/ai21', 'v_max': 10, 'v_min': -10, 'expression': '(-0.014178) + (3.991341)*x + (0.001313)*x**2'},
'AC_Voltage_10': {'physChan': 'Dev2/ai22', 'v_max': 1, 'v_min': -1, 'expression': '(0.367553) + (494.801861)*x'},
'AC_Current_10': {'physChan': 'Dev2/ai23', 'v_max': 5, 'v_min': -5, 'expression': '(-0.008982) + (9.955748)*x + (0.001240)*x**2'},
'isoPV_4': {'physChan': 'Dev3/ai0', 'v_max': 10, 'v_min': -10, 'expression': '((3*20*28)/(10*x))-28'},
'node1_10_Current': {'physChan': 'Dev3/ai6', 'v_max': 2, 'v_min': -2, 'expression': '(0.056009) + (93.703259)*x + (0.448038)*x**2'},
'Ametek_Trigger': {'physChan': 'Dev3/ai7', 'v_max': 10, 'v_min': -10, 'expression': 'x'},
'IC1_6_10_ac_current': {'physChan': 'Dev3/ai16', 'v_max': 10, 'v_min': -10, 'expression': '(-0.024781) + (10.008430)*x'},
'irradiance': {'physChan': 'Dev3/ai22', 'v_max': 10, 'v_min': -10, 'expression': 'x*812'},
'trigger_1_5': {'physChan': 'Dev3/ai23', 'v_max': 10, 'v_min': -10, 'expression': 'x'}}


class DeviceError(Exception):
    pass


class Device(object):

    def __init__(self, params=None, ts=None):
        self.ts = ts
        self.device = None
        self.node = params.get('node')
        self.sample_rate = params.get('sample_rate')
        self.n_cycles = params.get('n_cycles')
        self.n_samples = int((self.sample_rate/60.)*self.n_cycles)

        # Get analog channels to acquire
        self.data_points = list(data_points)
        self.points_map = dsm_points_map.get(str(self.node))

        # Create list of analog channels to capture
        self.analog_channels = []
        for key, value in self.points_map.items():
            self.analog_channels.append(value)
        self.analog_channels = sorted(self.analog_channels)  # alphabetize
        # self.ts.log_debug('analog_channels  = %s' % self.analog_channels)

        self.time_vector = np.linspace(0., self.n_samples/self.sample_rate, self.n_samples)

        self.n_channels = len(self.analog_channels)
        self.physical_channels = ''
        self.dev_numbers = []

        for k in range(len(self.analog_channels)):
            chan = DSM_CHANNELS[wfm_dsm_channels[self.analog_channels[k]]]['physChan']
            self.physical_channels += chan
            self.dev_numbers.append(chan[3])
            if k != len(self.analog_channels)-1:
                self.physical_channels += ','
        self.ts.log_debug('The following channels will be captured: %s, on physical channels: %s.' %
                          (self.analog_channels, self.physical_channels))

        # find the unique NI devices
        self.sorted_unique, self.unique_counts = np.unique(self.dev_numbers, return_index=False, return_counts=True)

        self.read = int32()
        self.analog_input = []
        self.physical_channels = []
        self.chan_decoder = []
        for k in range(len(self.unique_counts)):
            self.analog_input.append(Task())
            self.physical_channels.append('')
            self.chan_decoder.append([])

        self.raw_data = []
        self.n_channels = []
        for k in self.unique_counts:
            self.n_channels.append(k)
            self.raw_data.append(np.zeros((self.n_samples*k,), dtype=numpy.float64))

        unique_dev_num = -1  # count for the unique devs
        for dev in self.sorted_unique:
            unique_dev_num += 1
            for k in range(len(self.analog_channels)):  # for each channel
                chan = DSM_CHANNELS[wfm_dsm_channels[self.analog_channels[k]]]['physChan']
                if dev == chan[3]:  # if this device matches, put it in this task
                    self.physical_channels[unique_dev_num] += chan + ','
                    self.chan_decoder[unique_dev_num].append(self.analog_channels[k])
        for dev in range(len(self.sorted_unique)):  # clean up last comma
            self.physical_channels[dev] = self.physical_channels[dev][:-1]  # Remove the last comma.

        # Create empty container for data capture
        self.ac_voltage_vector = None
        self.ac_current_vector = None
        self.ametek_trigger = None

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

    def info(self):
        return 'DAS Hardware: Sandia NI PCIe Cards'

    def open(self):
        pass

    def close(self):
        pass

    def data_read(self):
        # Virtual channels are created. Each one of the virtual channels in question here is used to acquire
        # from an analog voltage signal(s).
        for k in range(len(self.sorted_unique)):
            self.analog_input[k].CreateAIVoltageChan(self.physical_channels[k],  # The physical name of the channel
                                                     "",  # The name to associate with this channel
                                                     DAQmx_Val_Cfg_Default,  # Differential wiring
                                                     -10.0,  # Min voltage
                                                     10.0,  # Max voltage
                                                     DAQmx_Val_Volts,  # Units
                                                     None)  # reserved

        try:
            status = DAQmxConnectTerms('/Dev%s/20MHzTimebase' % self.dev_numbers[0],
                                       '/Dev%s/RTSI7' % self.dev_numbers[len(self.sorted_unique)-1],
                                       DAQmx_Val_DoNotInvertPolarity)
        except Exception as e:
            print(('Error: Task does not support DAQmxConnectTerms: %s' % e))

        for k in range(len(self.sorted_unique)):
            if k == 0:  # Master
                self.analog_input[k].CfgSampClkTiming('',  # const char source[],
                                                 self.sample_rate,   # float64 rate,
                                                 DAQmx_Val_Rising,   #  int32 activeEdge,
                                                 DAQmx_Val_FiniteSamps,   # int32 sampleMode,
                                                 self.n_samples)  # uInt64 sampsPerChanToAcquire

            else:  # Slave
                print(('Configuring Slave %s Sample Clock Timing.' % k))
                # DAQmxCfgSampClkTiming(taskHandle,"",rate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,sampsPerChan)
                self.analog_input[k].CfgSampClkTiming('',   # const char source[], The source terminal of the Sample Clock.
                                                 self.sample_rate,   # float64 rate, The sampling rate in samples per second per channel.
                                                 DAQmx_Val_Rising,   #  int32 activeEdge,
                                                 DAQmx_Val_FiniteSamps,   # int32 sampleMode,
                                                 self.n_samples)  # uInt64 sampsPerChanToAcquire

                try:
                    print(('Configuring Slave %s Clock Time Base.' % k))
                    self.analog_input[k].SetSampClkTimebaseSrc('/Dev3/RTSI7')
                except Exception as e:
                    print(('Task does not support SetSampClkTimebaseSrc: %s' % e))

                try:
                    print(('Configuring Slave %s Clock Time Rate.' % k))
                    self.analog_input[k].SetSampClkTimebaseRate(20e6)
                except Exception as e:
                    print(('Task does not support SetSampClkTimebaseRate: %s' % e))

                print(('Configuring Slave %s Trigger.' % k))
                self.analog_input[k].CfgDigEdgeStartTrig('/Dev%s/ai/StartTrigger' % self.dev_numbers[0],
                                                         DAQmx_Val_Rising)

        for k in range(len(self.sorted_unique)-1, -1, -1):
            # Start Master last so slave(s) will wait for trigger from master over RSTI bus
            print(('Starting Task: %s.' % k))
            self.analog_input[k].StartTask()

        # DAQmx Read Code
        # fillMode options
        # 1. DAQmx_Val_GroupByChannel 		Group by channel (non-interleaved)
        # 2. DAQmx_Val_GroupByScanNumber 	Group by scan number (interleaved)
        for k in range(len(self.sorted_unique)):
            # DAQmxReadAnalogF64(task2,sampsPerChanRead1,timeout,DAQmx_Val_GroupByScanNumber,
            # buffer2,bufferSize,&sampsPerChanRead2,NULL);
            self.analog_input[k].ReadAnalogF64(self.n_samples,  # int32 numSampsPerChan,
                                          5.0,   # float64 timeout,
                                          DAQmx_Val_GroupByChannel,    # bool32 fillMode,
                                          self.raw_data[k],    # float64 readArray[],
                                          self.n_samples*self.n_channels[k],    # uInt32 arraySizeInSamps,
                                          byref(self.read),    # int32 *sampsPerChanRead,
                                          None)   # bool32 *reserved);

            print("Acquired %d points" % self.read.value)
            print(('raw_data length: %s' % len(self.raw_data[k])))

        try:
            for k in range(len(self.sorted_unique)-1, -1, -1):
                self.analog_input[k].StopTask()
                self.analog_input[k].TaskControl(DAQmx_Val_Task_Unreserve)
        except Exception as e:
            self.ts.log_error('Error with DAQmx in StopTask. Returning nones... %s' % e)
            datarec = {'time': time.time(),
                       'ac_1': (None,        # voltage
                                None,        # current
                                None,        # power
                                None,        # VA
                                None,        # vars
                                None,        # PF
                                None),       # freq
                       'ac_2': (None,        # voltage
                                None,        # current
                                None,        # power
                                None,        # VA
                                None,        # vars (Nonactive Power)
                                None,        # PF
                                None),       # freq
                       'dc': (None,
                              None,
                              None)}
            return datarec

        dev_idx = -1
        data = {}
        for k in range(len(self.analog_channels)):
            # print('Getting data for %s' % analog_channels[k])
            for j in range(len(self.chan_decoder)):
                # print('Looking in data set: %s' % chan_decoder[j])
                if any(self.analog_channels[k] in s for s in self.chan_decoder[j]):
                    dev_idx = j
                    chan_idx = self.chan_decoder[j].index(self.analog_channels[k])
                    break
            scaled_data = dsm_expression(channel_name=self.analog_channels[k],
                                         dsm_value=self.raw_data[dev_idx][chan_idx*self.n_samples:(chan_idx+1)*self.n_samples])
            data[self.analog_channels[k]] = scaled_data

        dc_voltage = None
        dc_current = None
        ac_voltage = None
        ac_current = None

        for k in range(len(self.analog_channels)):
            if self.analog_channels[k][0:10] == 'DC_Voltage':
                dc_voltage = np.mean(data[self.analog_channels[k]])
            if self.analog_channels[k][0:10] == 'DC_Current':
                dc_current = np.mean(data[self.analog_channels[k]])
            if self.analog_channels[k][0:10] == 'AC_Voltage':
                self.ac_voltage_vector = data[self.analog_channels[k]]
                ac_voltage = waveform_analysis.calculateRMS(data[self.analog_channels[k]])
            if self.analog_channels[k][0:10] == 'AC_Current':
                self.ac_current_vector = data[self.analog_channels[k]]
                ac_current = waveform_analysis.calculateRMS(data[self.analog_channels[k]])
            if self.analog_channels[k] == 'Ametek_Trigger':
                self.ametek_trigger = data[self.analog_channels[k]]

        if self.ac_voltage_vector is not None:
            freq, _ = waveform_analysis.freq_from_crossings(self.time_vector, self.ac_voltage_vector, self.sample_rate)
        elif self.ac_current_vector is not None:
            freq, _ = waveform_analysis.freq_from_crossings(self.time_vector, self.ac_current_vector, self.sample_rate)
        else:
            freq = None

        avg_P, S, Q1, N, PF1 = waveform_analysis.harmonic_analysis(self.time_vector, self.ac_voltage_vector,
                                                                   self.ac_current_vector,
                                                                   self.sample_rate, self.ts)
        datarec = {'TIME': time.time(),
                   'AC_VRMS_1': ac_voltage,
                   'AC_IRMS_1': ac_current,
                   'AC_P_1': avg_P,
                   'AC_S_1': S,
                   'AC_Q_1': Q1,
                   'AC_PF_1': PF1,
                   'AC_FREQ_1': freq,
                   'AC_VRMS_2': None,
                   'AC_IRMS_2': None,
                   'AC_P_2': None,
                   'AC_S_2': None,
                   'AC_Q_2': None,
                   'AC_PF_2': None,
                   'AC_FREQ_2': None,
                   'AC_VRMS_3': None,
                   'AC_IRMS_3': None,
                   'AC_P_3': None,
                   'AC_S_3': None,
                   'AC_Q_3': None,
                   'AC_PF_3': None,
                   'AC_FREQ_3': None,
                   'DC_V': dc_voltage,
                   'DC_I': dc_current,
                   'DC_P': dc_voltage*dc_current}

        return datarec


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
        self.wfm_channels = params.get('channels')

        for c in self.wfm_channels:
            dsm_chan = wfm_dsm_channels[c]
            if dsm_chan is not None:
                self.wfm_dsm_channels.append('%s_%s' % (dsm_chan, self.dsm_id))
        self.ts.log_debug('Channels to record: %s' % str(self.wfm_channels))

    def waveform_capture(self, enable=True, sleep=None):
        """
        Enable/disable waveform capture.
        """
        if enable:
            for k in range(len(self.sorted_unique)):
                self.analog_input[k].CreateAIVoltageChan(self.physical_channels[k],  # The physical name of the channel
                                                         "",  # The name to associate with this channel
                                                         DAQmx_Val_Cfg_Default,  # Differential wiring
                                                         -10.0,  # Min voltage
                                                         10.0,  # Max voltage
                                                         DAQmx_Val_Volts,  # Units
                                                         None)  # reserved

            try:
                status = DAQmxConnectTerms('/Dev%s/20MHzTimebase' % self.dev_numbers[0],
                                           '/Dev%s/RTSI7' % self.dev_numbers[len(self.sorted_unique)-1],
                                           DAQmx_Val_DoNotInvertPolarity)
            except Exception as e:
                print(('Error: Task does not support DAQmxConnectTerms: %s' % e))

            for k in range(len(self.sorted_unique)):
                if k == 0:  # Master
                    self.analog_input[k].CfgSampClkTiming('',  # const char source[],
                                                     self.sample_rate,   # float64 rate,
                                                     DAQmx_Val_Rising,   #  int32 activeEdge,
                                                     DAQmx_Val_FiniteSamps,   # int32 sampleMode,
                                                     self.n_samples)  # uInt64 sampsPerChanToAcquire

                    trig_chan = DSM_CHANNELS[wfm_dsm_channels[self.wfm_trigger_channel]]['physChan']

                    # approximate scaling/calibration using linear approximation with zero crossing
                    # (Shouldn't matter for analog triggers)
                    linear_slope_approx = dsm_expression(channel_name=trig_chan, dsm_value=100)/100.
                    trig_level = self.wfm_trigger_level/linear_slope_approx

                    if self.wfm_trigger_cond == 'Rising_Edge':
                        self.analog_input[k].CfgAnlgEdgeStartTrig(trig_chan,  # name of analog signal channel
                                                             DAQmx_Val_RisingSlope,  # or DAQmx_Val_FallingSlope
                                                             trig_level)  # threshold at which to start acquiring
                    elif self.wfm_trigger_cond == 'Falling_Edge':
                        self.analog_input[k].CfgAnlgEdgeStartTrig(trig_chan,  # name of analog signal channel
                                                             DAQmx_Val_FallingSlope,  # or DAQmx_Val_RisingSlope
                                                             trig_level)  # threshold at which to start acquiring
                    else:
                        # use this case for the force trigger
                        pass

                else:  # Slave
                    print(('Configuring Slave %s Sample Clock Timing.' % k))
                    # DAQmxCfgSampClkTiming(taskHandle,"",rate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,sampsPerChan)
                    self.analog_input[k].CfgSampClkTiming('',   # const char source[], The source terminal of the Sample Clock.
                                                     self.sample_rate,   # float64 rate, The sampling rate in samples per second per channel.
                                                     DAQmx_Val_Rising,   #  int32 activeEdge,
                                                     DAQmx_Val_FiniteSamps,   # int32 sampleMode,
                                                     self.n_samples)  # uInt64 sampsPerChanToAcquire

                    try:
                        print(('Configuring Slave %s Clock Time Base.' % k))
                        self.analog_input[k].SetSampClkTimebaseSrc('/Dev3/RTSI7')
                    except Exception as e:
                        print(('Task does not support SetSampClkTimebaseSrc: %s' % e))

                    try:
                        print(('Configuring Slave %s Clock Time Rate.' % k))
                        self.analog_input[k].SetSampClkTimebaseRate(20e6)
                    except Exception as e:
                        print(('Task does not support SetSampClkTimebaseRate: %s' % e))

                    print(('Configuring Slave %s Trigger.' % k))
                    self.analog_input[k].CfgDigEdgeStartTrig('/Dev%s/ai/StartTrigger' % self.dev_numbers[0],
                                                             DAQmx_Val_Rising)

            for k in range(len(self.sorted_unique)-1, -1, -1):
                # Start Master last so slave(s) will wait for trigger from master over RSTI bus
                print(('Starting Task: %s.' % k))
                self.analog_input[k].StartTask()

            for k in range(len(self.sorted_unique)):
                self.analog_input[k].ReadAnalogF64(self.n_samples,  # int32 numSampsPerChan,
                                              5.0,   # float64 timeout,
                                              DAQmx_Val_GroupByChannel,    # bool32 fillMode,
                                              self.raw_data[k],    # float64 readArray[],
                                              self.n_samples*self.n_channels[k],    # uInt32 arraySizeInSamps,
                                              byref(self.read),    # int32 *sampsPerChanRead,
                                              None)   # bool32 *reserved);

    def waveform_status(self):
        # return INACTIVE, ACTIVE, COMPLETE

        trig_type = self.analog_input[k].GetStartTrigType()

        if int(trig_type) == 10099 and self.raw_data is None:
            # DAQmx_Val_AnlgEdge 	10099 	Trigger when an analog signal signal crosses a threshold.
            # DAQmx_Val_DigEdge 	10150 	Trigger on the rising or falling edge of a digital signal.
            # DAQmx_Val_DigPattern 	10398 	Trigger when digital physical channels match a digital pattern.
            # DAQmx_Val_AnlgWin 	10103 	Trigger when an analog signal enters or leaves a range of values.
            # DAQmx_Val_None 	10230 	Disable triggering for the task.
            stat = 'ACTIVE'

        elif self.raw_data is not None:
            stat = 'COMPLETE'

            # once complete, close the Task
            try:
                for k in range(len(self.sorted_unique)-1, -1, -1):
                    self.analog_input[k].StopTask()
                    self.analog_input[k].TaskControl(DAQmx_Val_Task_Unreserve)
            except Exception as e:
                self.ts.log_error('Error with DAQmx in StopTask. Returning nones... %s' % e)

        else:
            stat = 'INACTIVE'

        return stat

    def waveform_force_trigger(self):
        """
        Create trigger event with provided value.
        """
        trig_condition = self.wfm_trigger_cond
        self.wfm_trigger_cond = None
        self.waveform_capture()
        self.wfm_trigger_cond = trig_condition

    def waveform_capture_dataset(self):
        ds = dataset.Dataset()
        ds.points.append('TIME')
        ds.data.append(self.time_vector)

        dev_idx = -1
        data = {}
        for k in range(len(self.analog_channels)):
            # print('Getting data for %s' % analog_channels[k])
            for j in range(len(self.chan_decoder)):
                # print('Looking in data set: %s' % chan_decoder[j])
                if any(self.analog_channels[k] in s for s in self.chan_decoder[j]):
                    dev_idx = j
                    chan_idx = self.chan_decoder[j].index(self.analog_channels[k])
                    break
            scaled_data = dsm_expression(channel_name=self.analog_channels[k],
                                         dsm_value=self.raw_data[dev_idx][chan_idx*self.n_samples:(chan_idx+1)*self.n_samples])
            data[self.analog_channels[k]] = scaled_data

            ds.points.append(dsm_points_map.get(self.analog_channels[k]))
            ds.data.append(data[self.analog_channels[k]])  # first row for first signal and so on

        return ds


def dsm_expression(channel_name, dsm_value):
    x = dsm_value
    # print(DSM_CHANNELS[channel_name]['expression'])
    return eval(DSM_CHANNELS[channel_name]['expression'])

def IC2_relay(new_state='close'):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        print('Opening IC2 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        print('Closing IC2 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    task.CreateDOChan("Dev1/port0/line17", "", DAQmx_Val_ChanForAllLines)
    task.StartTask()
    task.WriteDigitalLines(1,  # int32 numSampsPerChan
                           1,  # bool32 autoStart
                           10.0,  # float64 timeout
                           DAQmx_Val_GroupByChannel,  # bool32 dataLayout
                           ditigal_wfm_data,  # uInt8 writeArray[]
                           None,  # int32 *sampsPerChanWritten
                           None)  # bool32 *reserved
    task.StopTask()

def IC1_relay(new_state='close'):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        print('Opening IC1 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        print('Closing IC1 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    task.CreateDOChan("Dev1/port0/line16", "", DAQmx_Val_ChanForAllLines)
    task.StartTask()
    task.WriteDigitalLines(1,  # int32 numSampsPerChan
                           1,  # bool32 autoStart
                           10.0,  # float64 timeout
                           DAQmx_Val_GroupByChannel,  # bool32 dataLayout
                           ditigal_wfm_data,  # uInt8 writeArray[]
                           None,  # int32 *sampsPerChanWritten
                           None)  # bool32 *reserved
    task.StopTask()

def inv1_relay(new_state='close'):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        print('Opening Inverter 1 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        print('Closing Inverter 1 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    task.CreateDOChan("Dev1/port0/line0", "", DAQmx_Val_ChanForAllLines)
    task.StartTask()
    task.WriteDigitalLines(1,  # int32 numSampsPerChan
                           1,  # bool32 autoStart
                           10.0,  # float64 timeout
                           DAQmx_Val_GroupByChannel,  # bool32 dataLayout
                           ditigal_wfm_data,  # uInt8 writeArray[]
                           None,  # int32 *sampsPerChanWritten
                           None)  # bool32 *reserved
    task.StopTask()

def inv2_relay(new_state='close'):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        print('Opening Inverter 2 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        print('Closing Inverter 2 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    task.CreateDOChan("Dev1/port0/line1", "", DAQmx_Val_ChanForAllLines)
    task.StartTask()
    task.WriteDigitalLines(1,  # int32 numSampsPerChan
                           1,  # bool32 autoStart
                           10.0,  # float64 timeout
                           DAQmx_Val_GroupByChannel,  # bool32 dataLayout
                           ditigal_wfm_data,  # uInt8 writeArray[]
                           None,  # int32 *sampsPerChanWritten
                           None)  # bool32 *reserved
    task.StopTask()

def inv3_relay(new_state='close'):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        print('Opening Inverter 3 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        print('Closing Inverter 3 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    task.CreateDOChan("Dev1/port0/line8", "", DAQmx_Val_ChanForAllLines)
    task.StartTask()
    task.WriteDigitalLines(1,  # int32 numSampsPerChan
                           1,  # bool32 autoStart
                           10.0,  # float64 timeout
                           DAQmx_Val_GroupByChannel,  # bool32 dataLayout
                           ditigal_wfm_data,  # uInt8 writeArray[]
                           None,  # int32 *sampsPerChanWritten
                           None)  # bool32 *reserved
    task.StopTask()

def inv4_relay(new_state='close'):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        print('Opening Inverter 4 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        print('Closing Inverter 4 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    task.CreateDOChan("Dev1/port0/line9", "", DAQmx_Val_ChanForAllLines)
    task.StartTask()
    task.WriteDigitalLines(1,  # int32 numSampsPerChan
                           1,  # bool32 autoStart
                           10.0,  # float64 timeout
                           DAQmx_Val_GroupByChannel,  # bool32 dataLayout
                           ditigal_wfm_data,  # uInt8 writeArray[]
                           None,  # int32 *sampsPerChanWritten
                           None)  # bool32 *reserved
    task.StopTask()

def inv5_relay(new_state='close'):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        print('Opening Inverter 5 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        print('Closing Inverter 5 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    task.CreateDOChan("Dev3/port0/line0", "", DAQmx_Val_ChanForAllLines)
    task.StartTask()
    task.WriteDigitalLines(1,  # int32 numSampsPerChan
                           1,  # bool32 autoStart
                           10.0,  # float64 timeout
                           DAQmx_Val_GroupByChannel,  # bool32 dataLayout
                           ditigal_wfm_data,  # uInt8 writeArray[]
                           None,  # int32 *sampsPerChanWritten
                           None)  # bool32 *reserved
    task.StopTask()

def inv6_relay(new_state='close'):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        print('Opening Inverter 6 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        print('Closing Inverter 6 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    task.CreateDOChan("Dev3/port0/line8", "", DAQmx_Val_ChanForAllLines)
    task.StartTask()
    task.WriteDigitalLines(1,  # int32 numSampsPerChan
                           1,  # bool32 autoStart
                           10.0,  # float64 timeout
                           DAQmx_Val_GroupByChannel,  # bool32 dataLayout
                           ditigal_wfm_data,  # uInt8 writeArray[]
                           None,  # int32 *sampsPerChanWritten
                           None)  # bool32 *reserved
    task.StopTask()

def inv7_relay(new_state='close'):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        print('Opening Inverter 7 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        print('Closing Inverter 7 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    task.CreateDOChan("Dev2/port0/line0", "", DAQmx_Val_ChanForAllLines)
    task.StartTask()
    task.WriteDigitalLines(1,  # int32 numSampsPerChan
                           1,  # bool32 autoStart
                           10.0,  # float64 timeout
                           DAQmx_Val_GroupByChannel,  # bool32 dataLayout
                           ditigal_wfm_data,  # uInt8 writeArray[]
                           None,  # int32 *sampsPerChanWritten
                           None)  # bool32 *reserved
    task.StopTask()

def inv8_relay(new_state='close'):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        print('Opening Inverter 8 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        print('Closing Inverter 8 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    task.CreateDOChan("Dev2/port0/line1", "", DAQmx_Val_ChanForAllLines)
    task.StartTask()
    task.WriteDigitalLines(1,  # int32 numSampsPerChan
                           1,  # bool32 autoStart
                           10.0,  # float64 timeout
                           DAQmx_Val_GroupByChannel,  # bool32 dataLayout
                           ditigal_wfm_data,  # uInt8 writeArray[]
                           None,  # int32 *sampsPerChanWritten
                           None)  # bool32 *reserved
    task.StopTask()

def inv9_relay(new_state='close'):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        print('Opening Inverter 9 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        print('Closing Inverter 9 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    task.CreateDOChan("Dev2/port0/line8", "", DAQmx_Val_ChanForAllLines)
    task.StartTask()
    task.WriteDigitalLines(1,  # int32 numSampsPerChan
                           1,  # bool32 autoStart
                           10.0,  # float64 timeout
                           DAQmx_Val_GroupByChannel,  # bool32 dataLayout
                           ditigal_wfm_data,  # uInt8 writeArray[]
                           None,  # int32 *sampsPerChanWritten
                           None)  # bool32 *reserved
    task.StopTask()

def inv10_relay(new_state='close'):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        print('Opening Inverter 10 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        print('Closing Inverter 10 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    task.CreateDOChan("Dev2/port0/line9", "", DAQmx_Val_ChanForAllLines)
    task.StartTask()
    task.WriteDigitalLines(1,  # int32 numSampsPerChan
                           1,  # bool32 autoStart
                           10.0,  # float64 timeout
                           DAQmx_Val_GroupByChannel,  # bool32 dataLayout
                           ditigal_wfm_data,  # uInt8 writeArray[]
                           None,  # int32 *sampsPerChanWritten
                           None)  # bool32 *reserved
    task.StopTask()


def close_1_5():
    inv1_relay('close')
    inv2_relay('close')
    inv3_relay('close')
    inv4_relay('close')
    inv5_relay('close')

def open_1_5():
    inv1_relay('open')
    inv2_relay('open')
    inv3_relay('open')
    inv4_relay('open')
    inv5_relay('open')

def close_6_10():
    inv6_relay('close')
    inv7_relay('close')
    inv8_relay('close')
    inv9_relay('close')
    inv10_relay('close')

def open_6_10():
    inv6_relay('open')
    inv7_relay('open')
    inv8_relay('open')
    inv9_relay('open')
    inv10_relay('open')


if __name__ == "__main__":

    IC2_relay(new_state='close')
    close_1_5()
    close_6_10()

    """
    # consider moving to SuperTask in acq4
    # https://github.com/acq4/acq4/blob/develop/acq4/drivers/nidaq/SuperTask.py

    # analog_channels = ['AC_Voltage_10', 'AC_Current_10', 'AC_Voltage_5', 'Ametek_Trigger']
    analog_channels = ['AC_Voltage_4', 'AC_Current_4', 'DC_Voltage_4', 'DC_Current_4']
    # analog_channels = ['AC_Voltage_10', 'AC_Current_10']
    read = int32()
    n_points = 1000  # number of samples per channel
    sample_rate = 10000.

    dev_numbers = []
    for i in range(len(analog_channels)):
        chan = DSM_CHANNELS[analog_channels[i]]['physChan']
        dev_numbers.append(chan[3])

    sorted_unique, unique_counts = np.unique(dev_numbers, return_index=False, return_counts=True)  # find the unique NI devices
    analog_input = []
    physical_channels = []
    chan_decoder = []
    for i in range(len(unique_counts)):
        analog_input.append(Task())
        physical_channels.append('')
        chan_decoder.append([])

    raw_data = []
    n_channels = []
    for i in unique_counts:
        n_channels.append(i)
        raw_data.append(np.zeros((n_points*i,), dtype=numpy.float64))
    print(n_channels)
    print('raw_data length: %s' % len(raw_data[0]))

    # print('sorted_unique: %s' % sorted_unique)

    unique_dev_num = -1  # count for the unique devs
    for dev in sorted_unique:
        unique_dev_num += 1
        for i in range(len(analog_channels)):  # for each channel
            chan = DSM_CHANNELS[analog_channels[int(i)]]['physChan']
            if dev == chan[3]:  # if this device matches, put it in this task
                physical_channels[unique_dev_num] += chan + ','
                # print(analog_channels[i])
                # print(unique_dev_num)
                chan_decoder[unique_dev_num].append(analog_channels[i])
                # print(chan_decoder)
    for dev in range(len(sorted_unique)):  # clean up last comma
        physical_channels[dev] = physical_channels[dev][:-1]  # Remove the last comma.

    print('Capturing Waveforms on Channels: %s' % physical_channels)
    print('Waveforms Channels are: %s' % chan_decoder)

    # Step 1, virtual channels are created. Each one of the virtual channels in question here is used to acquire
    # from an analog voltage signal(s).
    for i in range(len(sorted_unique)):
        analog_input[i].CreateAIVoltageChan(physical_channels[i],  # The physical name of the channel
                                            "",  # The name to associate with this channel
                                            DAQmx_Val_Cfg_Default,  # Differential wiring
                                            -10.0,  # Min voltage
                                            10.0,  # Max voltage
                                            DAQmx_Val_Volts,  # Units
                                            None)  # reserved

    '''
    PCI Synchronization Using the Reference Clock:
    The RTSI bus offers the ability to share signals between independent devices in the system. Traditionally,
    synchronizing data acquisition devices required sharing a common timebase clock source among the devices.
    M Series devices have an internal timebase of 80 MHz, which is too high a frequency to pass accurately to other
    devices through the RTSI bus. Typically, 10 MHz is a more stable clock frequency to route between devices and is
    used as a standard for synchronization in PXI systems with the 10 MHz PXI clock built into the backplane of the
    chassis. Therefore, M Series devices generate a 10 MHz reference clock to be used for synchronization purposes
    by dividing down their 80 MHz onboard oscillator. To synchronize acquisitions or generations across several
    PCI M Series boards, one board acts as the master and exports its 10 MHz reference clock to all of the other
    slave boards. The NI-STC 2 ASIC on each M Series has PLL circuitry that compares an external reference clock to
    its built in voltage-controlled crystal oscillator clock (VCXO) to output a clock that is synchronized to this
    reference. Thus each device in the system can input a 10 MHz reference clock and synchronize its own 80 MHz
    and 20 MHz timebases to it. With this technology, all devices are synchronized to the same 10 MHz master
    clock, but can use their individual faster 80 and 20 MHz timebases generated onboard. Note that due to the
    way signals are divided down, the 100 kHz timebase will not be in phase with the input to the PLL.
    '''
    try:
        # int32 DAQmxConnectTerms (const char sourceTerminal[], const char destinationTerminal[],
        # int32 signalModifiers)
        print('Connecting Master Timebase to RSTI Channel.')
        # DAQmxDisconnectTerms('/Dev%s/20MHzTimebase' % dev_numbers[1],
        #                            '/Dev%s/RTSI7' % dev_numbers[0])
        status = DAQmxConnectTerms('/Dev%s/20MHzTimebase' % dev_numbers[0],
                                   '/Dev%s/RTSI7' % dev_numbers[len(sorted_unique)-1],
                                   DAQmx_Val_DoNotInvertPolarity)
        print('DAQmxConnectTerms status: %s' % status)

    except Exception, e:
        print('Error: Task does not support DAQmxConnectTerms: %s' % e)

    for i in range(len(sorted_unique)):
        if i == 0:  # Master
            '''
            When routing its 10 MHz reference clock out for other devices to synchronize to, the master device can set
            the source of its reference clock to "OnboardClock". This option will take the 10 MHz reference clock of
            the master device, which has been routed out to RTSI, back to the source of its own PLL. The master device
            then sees the same delays that the slave devices phase locking to the 10 MHz reference clock over RTSI
            will see.
            '''
            print('Configuring Master %s Sample Clock Timing.' % i)
            analog_input[i].CfgSampClkTiming('',  # const char source[],
                                             sample_rate,   # float64 rate,
                                             DAQmx_Val_Rising,   #  int32 activeEdge,
                                             DAQmx_Val_FiniteSamps,   # int32 sampleMode,
                                             n_points)  # uInt64 sampsPerChanToAcquire

            # trigger on analog channel
            # http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcfganlgedgestarttrig/
            # analog_input[i].CfgAnlgEdgeStartTrig('Dev1/ai22',  # name of analog signal channel
            #                                      DAQmx_Val_RisingSlope,  # or DAQmx_Val_FallingSlope
            #                                      0)  # threshold at which to start acquiring

        else:  # Slave
            print('Configuring Slave %s Sample Clock Timing.' % i)
            # DAQmxCfgSampClkTiming(taskHandle,"",rate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,sampsPerChan)
            analog_input[i].CfgSampClkTiming('',   # const char source[], The source terminal of the Sample Clock.
                                             sample_rate,   # float64 rate, The sampling rate in samples per second per channel.
                                             DAQmx_Val_Rising,   #  int32 activeEdge,
                                             DAQmx_Val_FiniteSamps,   # int32 sampleMode,
                                             n_points)  # uInt64 sampsPerChanToAcquire

            try:
                print('Configuring Slave %s Clock Time Base.' % i)
                analog_input[i].SetSampClkTimebaseSrc('/Dev3/RTSI7')
            except Exception, e:
                print('Task does not support SetSampClkTimebaseSrc: %s' % e)

            try:
                print('Configuring Slave %s Clock Time Rate.' % i)
                analog_input[i].SetSampClkTimebaseRate(20e6)
            except Exception, e:
                print('Task does not support SetSampClkTimebaseRate: %s' % e)

            # Used digital trigger to trigger slave when master begins capture.
            # Get Terminal Name with Device Prefix VI is used to programmatically extract the Start Trigger signal
            # of the master device and route it to be used to start the slave device. This step is the second phase
            # of the synchronization - making sure that they start at the same time.
            # analog_input[i].CfgDigEdgeStartTrig('RTSI6', DAQmx_Val_Rising)
            print('Configuring Slave %s Trigger.' % i)
            analog_input[i].CfgDigEdgeStartTrig('/Dev%s/ai/StartTrigger' % dev_numbers[0], DAQmx_Val_Rising)

    for i in range(len(sorted_unique)-1, -1, -1):
        # Start Master last so slave(s) will wait for trigger from master over RSTI bus
        print('Starting Task: %s.' % i)
        analog_input[i].StartTask()

    # DAQmx Read Code
    # fillMode options
    # 1. DAQmx_Val_GroupByChannel 		Group by channel (non-interleaved)
    # 2. DAQmx_Val_GroupByScanNumber 	Group by scan number (interleaved)
    for i in range(len(sorted_unique)):
        # DAQmxReadAnalogF64(task2,sampsPerChanRead1,timeout,DAQmx_Val_GroupByScanNumber,
        # buffer2,bufferSize,&sampsPerChanRead2,NULL);
        analog_input[i].ReadAnalogF64(n_points,  # int32 numSampsPerChan,
                                      5.0,   # float64 timeout,
                                      DAQmx_Val_GroupByChannel,    # bool32 fillMode,
                                      raw_data[i],    # float64 readArray[],
                                      n_points*n_channels[i],    # uInt32 arraySizeInSamps,
                                      byref(read),    # int32 *sampsPerChanRead,
                                      None)   # bool32 *reserved);

        print "Acquired %d points" % read.value
        print('raw_data length: %s' % len(raw_data[i]))

    for i in range(len(sorted_unique)-1, -1, -1):
        analog_input[i].StopTask()
        analog_input[i].TaskControl(DAQmx_Val_Task_Unreserve)

    dev_idx = -1
    data = {}
    for i in range(len(analog_channels)):
        # print('Getting data for %s' % analog_channels[i])
        for j in range(len(chan_decoder)):
            # print('Looking in data set: %s' % chan_decoder[j])
            if any(analog_channels[i] in s for s in chan_decoder[j]):
                device_number = dev_numbers[i]
                dev_idx = j
                chan_idx = chan_decoder[j].index(analog_channels[i])
                break
        # print('Channel: %s, Device number: %s, Device Index: %s, Channel Index: %s'
        #       % (i, device_number, dev_idx, chan_idx))
        # print(raw_data[dev_idx][chan_idx*n_points:(chan_idx+1)*n_points])
        scaled_data = dsm_expression(channel_name=analog_channels[i],
                                     dsm_value=raw_data[dev_idx][chan_idx*n_points:(chan_idx+1)*n_points])
        data[analog_channels[i]] = scaled_data

    time_vector = np.linspace(0., n_points/sample_rate, n_points)
    # print('time length: %s' % (len(time_vector)))
    # for i in range(len(analog_channels)):
    #     print('data length: %s' % (len(data[analog_channels[i]])))

    import matplotlib.pyplot as plt
    # plt.plot(time, ac_voltage_10, 'r', time, ac_current_10, 'b')
    # plt.show()

    fig, ax1 = plt.subplots()
    ax1.plot(time_vector, data[analog_channels[0]], 'b-')
    ax1.plot(time_vector, data[analog_channels[2]], 'k-')
    ax1.set_xlabel('time (s)')
    # Make the y-axis label and tick labels match the line color.
    ax1.set_ylabel('AC Voltage', color='b')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    ax2 = ax1.twinx()
    ax2.plot(time_vector, data[analog_channels[1]], 'r-')
    ax2.plot(time_vector, data[analog_channels[3]], 'g-')
    ax2.set_ylabel('AC Current', color='r')
    for tl in ax2.get_yticklabels():
        tl.set_color('r')

    plt.show()

    avg_P, S, Q1, N, PF1 = waveform_analysis.harmonic_analysis(time_vector, data[analog_channels[0]],
                                                                   data[analog_channels[1]],
                                                                   sample_rate, None)

    print('Power = %s, Q = %s' % (avg_P, Q1))

    f = open('D:\\SVP\\Node_4_waveforms-P=%s, Q=%s.csv' % (avg_P, Q1), 'w')
    f.write('Python Time (s), AC Voltage (V), AC Current (A)\n')
    for t in range(len(time_vector)):
        f.write('%0.6f, %0.6f, %0.6f\n' % (time_vector[t], data[analog_channels[0]][t], data[analog_channels[1]][t]))
    f.close()
    """

