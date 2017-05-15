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


import time
# import math

# Wrap driver import statements in try-except clauses to avoid SVP initialization errors
try:
    from PyDAQmx import *
except Exception, e:
    print('Error: PyDAQmx python package not found!')  # This will appear in the SVP log file.
    # raise  # programmers can raise this error to expose the error to the SVP user
try:
    import numpy as np
except Exception, e:
    print('Error: numpy python package not found!')  # This will appear in the SVP log file.
    # raise  # programmers can raise this error to expose the error to the SVP user
try:
    import waveform_analysis
except Exception, e:
    print('Error: waveform_analysis file not found!')  # This will appear in the SVP log file.
    # raise  # programmers can raise this error to expose the error to the SVP user


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

        ts.log('sample rate: %s, cycles: %s, n_samples: %s' % (self.sample_rate, self.n_cycles, self.n_samples))

        # Get analog channels to acquire
        self.points_map = dsm_points_map.get(str(self.node))

        # Create list of analog channels to capture
        self.analog_channels = []
        for key, value in self.points_map.iteritems():
            self.analog_channels.append(value)
        self.analog_channels = sorted(self.analog_channels)  # alphabetize
        # self.ts.log_debug('analog_channels  = %s' % self.analog_channels)

        self.time_vector = np.linspace(0., self.n_samples/self.sample_rate, self.n_samples)

        self.n_channels = len(self.analog_channels)
        channels_to_delete = []
        self.physical_channels = ''
        for i in range(len(self.analog_channels)):
            chan = DSM_CHANNELS[self.analog_channels[i]]['physChan']

            # PCIe cards will not support simultaneous capture if all channels are not on the same card
            # Skip all the channels that are not on the same device as ac_current
            # self.ts.log('physical_channels[0:4] = %s, chan[0:4] = %s' % (physical_channels[0:4], chan[0:4]))
            if i > 0 and self.physical_channels[0:4] != chan[0:4]:
                self.ts.log_warning('Removing Channel %s (%s) from capture because it is not on the same device '
                                    'as the other channels being captured.' % (chan, self.analog_channels[i]))
                self.n_channels -= 1
                channels_to_delete.append(i)
            else:
                self.physical_channels += chan
                if i != len(self.analog_channels)-1:
                    self.physical_channels += ','

        for j in range(len(channels_to_delete)):
            del self.analog_channels[channels_to_delete[j]]

        self.ts.log_debug('The following channels will be captured: %s, on physical channels: %s.' %
                          (self.analog_channels, self.physical_channels))

        # Create empty container for data capture
        self.raw_data = np.zeros((self.n_samples*self.n_channels,), dtype=numpy.float64)

    def info(self):
        return 'DAS Hardware: Sandia NI PCIe Cards'

    def open(self):
        pass

    def close(self):
        pass

    def data_capture(self, enable=True):
        pass

    def data_read(self):

        analog_input = Task()
        read = int32()

        # DAQmx Configure Code
        # analog_input.CreateAIVoltageChan("Dev1/ai0", "", DAQmx_Val_Cfg_Default, -10.0, 10.0, DAQmx_Val_Volts, None)
        analog_input.CreateAIVoltageChan(self.physical_channels,  # The physical name of the channel
                                         "",  # The name to associate with this channel
                                         DAQmx_Val_Cfg_Default,  # Differential wiring
                                         -1.0,  # Min voltage
                                         1.0,  # Max voltage
                                         DAQmx_Val_Volts,  # Units
                                         None)  # reserved
        try:
            analog_input.CfgSampClkTiming("",  # const char source[],
                                          self.sample_rate,   # float64 rate,
                                          DAQmx_Val_Rising,   #  int32 activeEdge,
                                          DAQmx_Val_FiniteSamps,   # int32 sampleMode,
                                          self.n_samples)  # uInt64 sampsPerChanToAcquire
        except Exception, e:
            self.ts.log_error('Cannot read multiple cards that do not support this capability. %s' % e)

        # DAQmx Start Code
        try:
            analog_input.StartTask()
        except Exception, e:
            self.ts.log_error('Cannot read DAQ cards when LabVIEW is running. Please stop LabVIEW Acquisition. %s' % e)
            raise

        # DAQmx Read Code
        # fillMode options
        # 1. DAQmx_Val_GroupByChannel 		Group by channel (non-interleaved)
        # 2. DAQmx_Val_GroupByScanNumber 	Group by scan number (interleaved)
        analog_input.ReadAnalogF64(self.n_samples,  # int32 numSampsPerChan,
                                   10.0,   # float64 timeout,
                                   DAQmx_Val_GroupByChannel,    # bool32 fillMode,
                                   self.raw_data,    # float64 readArray[],
                                   self.n_samples*self.n_channels,    # uInt32 arraySizeInSamps,
                                   byref(read),    # int32 *sampsPerChanRead,
                                   None)   # bool32 *reserved);
        try:
            analog_input.StopTask()
        except Exception, e:
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


        # print "Acquired %d points" % read.value
        # print('self.raw_data length: %s' % len(self.raw_data))

        dc_voltage = None
        dc_current = None
        ac_voltage = None
        ac_current = None
        ac_voltage_vector = None
        ac_current_vector = None

        for i in range(self.n_channels):
            # self.ts.log(self.analog_channels[i])
            # self.ts.log(self.raw_data[i*self.n_samples:(i+1)*self.n_samples])
            scaled_data = dsm_expression(channel_name=self.analog_channels[i],
                                         dsm_value=self.raw_data[i*self.n_samples:(i+1)*self.n_samples])

            if self.analog_channels[i][0:10] == 'DC_Voltage':
                dc_voltage = np.mean(scaled_data)
            if self.analog_channels[i][0:10] == 'DC_Current':
                dc_current = np.mean(scaled_data)
            if self.analog_channels[i][0:10] == 'AC_Voltage':
                ac_voltage_vector = scaled_data
                ac_voltage = waveform_analysis.calculateRMS(scaled_data)
            if self.analog_channels[i][0:10] == 'AC_Current':
                ac_current_vector = scaled_data
                ac_current = waveform_analysis.calculateRMS(scaled_data)
            if self.analog_channels[i] == 'Ametek_Trigger':
                ametek_trigger = scaled_data

        if ac_voltage_vector is not None:
            freq, _ = waveform_analysis.freq_from_crossings(self.time_vector, ac_voltage_vector, self.sample_rate)
        elif ac_current_vector is not None:
            freq, _ = waveform_analysis.freq_from_crossings(self.time_vector, ac_current_vector, self.sample_rate)
        else:
            freq = None

        # avg_P, P1, PH, N, Q1, DI, DV, DH, S, S1, SN, SH, PF1, PF, har_poll, THD_V, THD_I = \
        #     waveform_analysis.harmonic_analysis(self.time_vector, ac_voltage_vector, ac_current_vector,
        #                                         self.sample_rate, self.ts)

        avg_P, S, Q1, N, PF1 = waveform_analysis.harmonic_analysis(self.time_vector, ac_voltage_vector,
                                                                   ac_current_vector,
                                                                   self.sample_rate, self.ts)

        datarec = {'time': time.time(),
                   'ac_1': (ac_voltage,  # voltage
                            ac_current,  # current
                            avg_P,       # power
                            S,           # VA
                            Q1,          # vars
                            PF1,         # PF
                            freq),       # freq
                   'ac_2': (None,        # voltage
                            None,        # current
                            None,        # power
                            None,        # VA
                            N,           # vars (Nonactive Power)
                            None,        # PF
                            None),       # freq
                   'dc': (dc_voltage,
                          dc_current,
                          dc_voltage*dc_current)}

        return datarec


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
        print('Unknown new switch state: %s' % new_state)
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

if __name__ == "__main__":

    analog_channels = ['AC_Voltage_4', 'AC_Current_4']
    n_channels = len(analog_channels)
    analog_input = Task()
    read = int32()
    n_points = 2000  # number of samples per channel
    sample_rate = 60000.

    raw_data = np.zeros((n_points*n_channels,), dtype=numpy.float64)

    physical_channels = ''
    for i in range(len(analog_channels)):
        chan = DSM_CHANNELS[analog_channels[i]]['physChan']
        physical_channels += chan
        if i != len(analog_channels)-1:
            physical_channels += ','
    print('Capturing Waveforms on Channels: %s' % physical_channels)

    # DAQmx Configure Code
    # analog_input.CreateAIVoltageChan("Dev1/ai0", "", DAQmx_Val_Cfg_Default, -10.0, 10.0, DAQmx_Val_Volts, None)
    analog_input.CreateAIVoltageChan(physical_channels,  # The physical name of the channel
                                     "",  # The name to associate with this channel
                                     DAQmx_Val_Cfg_Default,  # Differential wiring
                                     -1.0,  # Min voltage
                                     1.0,  # Max voltage
                                     DAQmx_Val_Volts,  # Units
                                     None)  # reserved

    analog_input.CfgSampClkTiming("",  # const char source[],
                                  sample_rate,   # float64 rate,
                                  DAQmx_Val_Rising,   #  int32 activeEdge,
                                  DAQmx_Val_FiniteSamps,   # int32 sampleMode,
                                  n_points)  # uInt64 sampsPerChanToAcquire

    # DAQmx Start Code
    analog_input.StartTask()

    # DAQmx Read Code
    # fillMode options
    # 1. DAQmx_Val_GroupByChannel 		Group by channel (non-interleaved)
    # 2. DAQmx_Val_GroupByScanNumber 	Group by scan number (interleaved)
    analog_input.ReadAnalogF64(n_points,  # int32 numSampsPerChan,
                               10.0,   # float64 timeout,
                               DAQmx_Val_GroupByChannel,    # bool32 fillMode,
                               raw_data,    # float64 readArray[],
                               n_points*n_channels,    # uInt32 arraySizeInSamps,
                               byref(read),    # int32 *sampsPerChanRead,
                               None)   # bool32 *reserved);

    analog_input.StopTask()



    # print "Acquired %d points" % read.value
    # print('raw_data length: %s' % len(raw_data))

    data = {}
    for i in range(len(analog_channels)):
        print analog_channels[i]
        print(raw_data[i*n_points:(i+1)*n_points])
        scaled_data = dsm_expression(channel_name=analog_channels[i], dsm_value=raw_data[i*n_points:(i+1)*n_points])
        data[analog_channels[i]] = scaled_data

    time_vector = np.linspace(0., n_points/sample_rate, n_points)
    # print('time: %s, volt: %s, curr: %s' % (len(time), len(ac_voltage_10), len(ac_current_10)))
    import matplotlib.pyplot as plt
    # plt.plot(time, ac_voltage_10, 'r', time, ac_current_10, 'b')
    # plt.show()

    fig, ax1 = plt.subplots()
    ax1.plot(time_vector, data[analog_channels[0]], 'b-')
    ax1.set_xlabel('time (s)')
    # Make the y-axis label and tick labels match the line color.
    ax1.set_ylabel('AC Voltage', color='b')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    ax2 = ax1.twinx()
    ax2.plot(time_vector, data[analog_channels[1]], 'r-')
    ax2.set_ylabel('AC Current', color='r')
    for tl in ax2.get_yticklabels():
        tl.set_color('r')
    plt.show()

    f = open('D:\\SVP\\Node_10_waveforms-%s.csv' % (time.time()), 'w')
    f.write('Python Time (s), AC Voltage (V), AC Current (A)\n')
    for t in range(len(time_vector)):
        f.write('%0.6f, %0.6f, %0.6f\n' % (time_vector[t], data[analog_channels[0]][t], data[analog_channels[1]][t]))
    f.close()
