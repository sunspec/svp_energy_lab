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
import sys

# Wrap driver import statements in try-except clauses to avoid SVP initialization errors
try:
    from PyDAQmx import *
except Exception as e:
    print('Error: PyDAQmx python package not found!')

try:
    import numpy as np
except Exception as e:
    print('Error: numpy python package not found!')

try:
    from . import waveform_analysis
except Exception as e:
    print('Error: waveform_analysis file not found!')

try:
    from ctypes import *
except Exception as e:
    print('Error: ctypes file not found!')


# Data channels for motor control center
dsm_points_mcc = {
    'utility_v_phA': 'Utility_PhA_V',
    'mcc_v_phA': 'MCC_PhA_V',
    'mcc_i_phA': 'MCC_PhA_I',
    'mcc_v_phB': 'MCC_PhB_V',
    'mcc_i_phB': 'MCC_PhB_I',
    'mcc_v_phC': 'MCC_PhC_V',
    'mcc_i_phC': 'MCC_PhC_I',
    'load_v_phA': 'Load_PhA_V',  # Same voltage a MCC
    'load_i_phA': 'Load_PhA_I',
    'load_v_phB': 'Load_PhB_V',   # Same voltage a MCC
    'load_i_phB': 'Load_PhB_I',
    'load_v_phC': 'Load_PhC_V',   # Same voltage a MCC
    'load_i_phC': 'Load_PhC_I',
    'genset_v_phA': 'Diesel_Genset_PhA_V',
    'genset_i_phA': 'Diesel_Genset_PhA_I',
    'genset_v_phB': 'Diesel_Genset_PhB_V',
    'genset_i_phB': 'Diesel_Genset_PhB_I',
    'genset_v_phC': 'Diesel_Genset_PhC_V',
    'genset_i_phC': 'Diesel_Genset_PhC_I',
    'pv_v_phA': 'PV_Inverter_20kW_PhA_V',    # Same voltage a MCC
    'pv_i_phA': 'PV_Inverter_20kW_PhA_I',
    'pv_v_phB': 'PV_Inverter_20kW_PhB_V',    # Same voltage a MCC
    'pv_i_phB': 'PV_Inverter_20kW_PhB_I',
    'pv_v_phC': 'PV_Inverter_20kW_PhC_V',    # Same voltage a MCC
    'pv_i_phC': 'PV_Inverter_20kW_PhC_I',
    'bat_v_phA': 'ESTB_PhA_V',
    'bat_i_phA': 'ESTB_PhA_I',
    'bat_v_phB': 'ESTB_PhB_V',
    'bat_i_phB': 'ESTB_PhB_I',
    'bat_v_phC': 'ESTB_PhC_V',
    'bat_i_phC': 'ESTB_PhC_I'}

dsm_points_mcc_reversed = {
    'Utility_PhA_V': 'utility_v_phA',  # reverse mapping too
    'MCC_PhA_V': 'mcc_v_phA',
    'MCC_PhA_I': 'mcc_i_phA',
    'MCC_PhB_V': 'mcc_v_phB',
    'MCC_PhB_I': 'mcc_i_phB',
    'MCC_PhC_V': 'mcc_v_phC',
    'MCC_PhC_I': 'mcc_i_phC',
    'Load_PhA_V': 'load_v_phA',
    'Load_PhA_I': 'load_i_phA',
    'Load_PhB_V': 'load_v_phB',
    'Load_PhB_I': 'load_i_phB',
    'Load_PhC_V': 'load_v_phC',
    'Load_PhC_I': 'load_i_phC',
    'Diesel_Genset_PhA_V': 'genset_v_phA',
    'Diesel_Genset_PhA_I': 'genset_i_phA',
    'Diesel_Genset_PhB_V': 'genset_v_phB',
    'Diesel_Genset_PhB_I': 'genset_i_phB',
    'Diesel_Genset_PhC_V': 'genset_v_phC',
    'Diesel_Genset_PhC_I': 'genset_i_phC',
    'PV_Inverter_20kW_PhA_V': 'pv_v_phA',
    'PV_Inverter_20kW_PhA_I': 'pv_i_phA',
    'PV_Inverter_20kW_PhB_V': 'pv_v_phB',
    'PV_Inverter_20kW_PhB_I': 'pv_i_phB',
    'PV_Inverter_20kW_PhC_V': 'pv_v_phC',
    'PV_Inverter_20kW_PhC_I': 'pv_i_phC',
    'ESTB_PhA_V': 'bat_v_phA',
    'ESTB_PhA_I': 'bat_i_phA',
    'ESTB_PhB_V': 'bat_v_phB',
    'ESTB_PhB_I': 'bat_i_phB',
    'ESTB_PhC_V': 'bat_v_phC',
    'ESTB_PhC_I': 'bat_i_phC'
}

wfm_channels = ['AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'EXT']
wfm_dsm_channels = dsm_points_mcc

DSM_CHANNELS = {
'Utility_PhA_V': {'physChan': 'Dev1/ai0', 'v_max': 1, 'v_min': -1, 'expression': 'x*499.0'},
'MCC_PhA_V': {'physChan': 'Dev1/ai1', 'v_max': 1, 'v_min': -1, 'expression': 'x*496'},
'MCC_PhA_I': {'physChan': 'Dev1/ai2', 'v_max': 1, 'v_min': -1, 'expression': 'x*100'},
'MCC_PhB_V': {'physChan': 'Dev1/ai3', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'MCC_PhB_I': {'physChan': 'Dev1/ai4', 'v_max': 1, 'v_min': -1, 'expression': 'x*100'},
'MCC_PhC_V': {'physChan': 'Dev1/ai5', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'MCC_PhC_I': {'physChan': 'Dev1/ai6', 'v_max': 1, 'v_min': -1, 'expression': 'x*100'},
'Load_PhA_V': {'physChan': 'Dev1/ai1', 'v_max': 1, 'v_min': -1, 'expression': 'x*496'},
'Load_PhA_I': {'physChan': 'Dev1/ai16', 'v_max': 1, 'v_min': -1, 'expression': '49.039198e3 + 93.861867*x'},
'Load_PhB_V': {'physChan': 'Dev1/ai3', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'Load_PhB_I': {'physChan': 'Dev1/ai18', 'v_max': 1, 'v_min': -1, 'expression': '67.837285e3 + 100.687060*x'},
'Load_PhC_V': {'physChan': 'Dev1/ai5', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'Load_PhC_I': {'physChan': 'Dev1/ai20', 'v_max': 1, 'v_min': -1, 'expression': '56.685470e3 + 98.489778*x'},
'Diesel_Genset_PhA_V': {'physChan': 'Dev1/ai21', 'v_max': 1, 'v_min': -1, 'expression': 'x*497.0'},
'Diesel_Genset_PhA_I': {'physChan': 'Dev1/ai22', 'v_max': 1, 'v_min': -1, 'expression': '(22.503877e-3) + (100.403661)*x + (-104.893069e-3)*(x**2)'},
'Diesel_Genset_PhB_V': {'physChan': 'Dev1/ai23', 'v_max': 1, 'v_min': -1, 'expression': 'x*493.5'},
'Diesel_Genset_PhB_I': {'physChan': 'Dev2/ai0', 'v_max': 1, 'v_min': -1, 'expression': '(10.073010e-3) + (99.752587)*x + (284.699652e-3)*(x**2)'},
'Diesel_Genset_PhC_V': {'physChan': 'Dev2/ai1', 'v_max': 1, 'v_min': -1, 'expression': 'x*501.7'},
'Diesel_Genset_PhC_I': {'physChan': 'Dev2/ai2', 'v_max': 1, 'v_min': -1, 'expression': '(-18.106330e-3) + (101.279462)*x + (14.321437e-3)*(x**2)'},
'PV_Inverter_20kW_PhA_V': {'physChan': 'Dev1/ai1', 'v_max': 1, 'v_min': -1, 'expression': 'x*496'},
'PV_Inverter_20kW_PhA_I': {'physChan': 'Dev2/ai4', 'v_max': 1, 'v_min': -1, 'expression': '(-20.988398e-3) + (20.211266)*x'},
'PV_Inverter_20kW_PhB_V': {'physChan': 'Dev1/ai3', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'PV_Inverter_20kW_PhB_I': {'physChan': 'Dev2/ai6', 'v_max': 1, 'v_min': -1, 'expression': '(-29.163501e-3) + (20.230154)*x'},
'PV_Inverter_20kW_PhC_V': {'physChan': 'Dev1/ai5', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'PV_Inverter_20kW_PhC_I': {'physChan': 'Dev2/ai16', 'v_max': 1, 'v_min': -1, 'expression': '(28.511307e-3) + (20.130221)*x'},
'SRP_30kW_Capstone_PhA_V': {'physChan': 'Dev1/ai1', 'v_max': 1, 'v_min': -1, 'expression': 'x*496'},
'SRP_30kW_Capstone_PhA_I': {'physChan': 'Dev2/ai18', 'v_max': 1, 'v_min': -1, 'expression': '(-5.657966e-3) + (102.347456)*x'},
'SRP_30kW_Capstone_PhB_V': {'physChan': 'Dev1/ai3', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'SRP_30kW_Capstone_PhB_I': {'physChan': 'Dev2/ai20', 'v_max': 1, 'v_min': -1, 'expression': '(-17.439877e-3) + (100.015337)*x'},
'SRP_30kW_Capstone_PhC_V': {'physChan': 'Dev2/ai21', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'SRP_30kW_Capstone_PhC_I': {'physChan': 'Dev2/ai22', 'v_max': 1, 'v_min': -1, 'expression': '(2.043021e-3) + (100.963618)*x'},
'Xantrex_30kW_PhA_V': {'physChan': 'Dev1/ai1', 'v_max': 1, 'v_min': -1, 'expression': 'x*496'},
'Xantrex_30kW_PhA_I': {'physChan': 'Dev3/ai2', 'v_max': 1, 'v_min': -1, 'expression': '(-115.865216e-3) + (99.772540)*x'},
'Xantrex_30kW_PhB_V': {'physChan': 'Dev1/ai3', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'Xantrex_30kW_PhB_I': {'physChan': 'Dev3/ai0', 'v_max': 1, 'v_min': -1, 'expression': '(12.373643e-3) + (99.281793)*x'},
'Xantrex_30kW_PhC_V': {'physChan': 'Dev3/ai3', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'Xantrex_30kW_PhC_I': {'physChan': 'Dev3/ai4', 'v_max': 1, 'v_min': -1, 'expression': '(-38.346419e-3) + (99.823882)*x + (-752.629163e-3)*(x**2)'},
'Xantrex_30kW_DC1_V': {'physChan': 'Dev3/ai5', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'Xantrex_30kW_DC1_I': {'physChan': 'Dev3/ai6', 'v_max': 1, 'v_min': -1, 'expression': 'x*93.5'},
'Xantrex_30kW_DC2_V': {'physChan': 'Dev3/ai7', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'Xantrex_30kW_DC2_I': {'physChan': 'Dev3/ai16', 'v_max': 1, 'v_min': -1, 'expression': 'x*93.5'},
'Irradiance': {'physChan': 'Dev3/ai17', 'v_max': 1, 'v_min': -1, 'expression': '812*Irradiance'},
'Xantrex_30kW_Ambient_Temp': {'physChan': 'Dev3/ai18', 'v_max': 1, 'v_min': -1, 'expression': 'x'},
'Xantrex_30kW_HS_Temp': {'physChan': 'Dev3/ai19', 'v_max': 1, 'v_min': -1, 'expression': 'x'},
'Xantrex_30kW_Cap_Temp': {'physChan': 'Dev3/ai20', 'v_max': 1, 'v_min': -1, 'expression': 'x'},
'ESTB_PhA_V': {'physChan': 'Dev3/ai21', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'ESTB_PhA_I': {'physChan': 'Dev3/ai22', 'v_max': 1, 'v_min': -1, 'expression': '(x)*100'},
'ESTB_PhB_V': {'physChan': 'Dev3/ai23', 'v_max': 1, 'v_min': -1, 'expression': '(x)*500'},
'ESTB_PhB_I': {'physChan': 'Dev3/ai18', 'v_max': 1, 'v_min': -1, 'expression': '(x)*100'},
'ESTB_PhC_V': {'physChan': 'Dev3/ai19', 'v_max': 1, 'v_min': -1, 'expression': 'x*500'},
'ESTB_PhC_I': {'physChan': 'Dev3/ai20', 'v_max': 1, 'v_min': -1, 'expression': '(x)*100'}}


class DeviceError(Exception):
    pass


class Device(object):

    def __init__(self, params=None, ts=None):
        self.ts = ts
        self.ts.log_debug(sys.path)
        self.device = None
        self.sample_rate = params.get('sample_rate')
        self.n_cycles = params.get('n_cycles')
        self.n_samples = int((self.sample_rate/60.)*self.n_cycles)
        self.physical_channels = ''  # string of physical channels
        self.dev_numbers = []   # list of device numbers
        self.duplicate_channels = {}  # dict with {recorded channel: [matching channels list]}

        # Get analog channels to acquire
        self.points_map = dsm_points_mcc

        # Create list of analog channels to capture
        self.analog_channels = []
        for key, value in self.points_map.items():
            self.analog_channels.append(value)
        self.analog_channels = sorted(self.analog_channels)  # alphabetize
        # self.ts.log_debug('analog_channels  = %s' % self.analog_channels)

        self.time_vector = np.linspace(0., self.n_samples/self.sample_rate, self.n_samples)
        self.n_channels = len(self.analog_channels)

        for k in range(len(self.analog_channels)):
            chan = DSM_CHANNELS[self.analog_channels[k]]['physChan']
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
        self.physical_channel_str = []  # list of strings of physical channels, sorted by Device
        self.physical_channel_list = []  # list of lists of physical channels, sorted by Device
        self.chan_decoder = []  # list of lists of channel names, aligned to the physical_channel_str
        for k in range(len(self.unique_counts)):
            self.analog_input.append(Task())
            self.physical_channel_str.append('')
            self.physical_channel_list.append([])
            self.chan_decoder.append([])

        self.raw_data = []
        self.n_channels = []
        for k in self.unique_counts:
            self.n_channels.append(k)
            self.raw_data.append(np.zeros((self.n_samples*k,), dtype=np.float64))

        unique_dev_num = -1  # count for the unique devs
        for dev in self.sorted_unique:
            unique_dev_num += 1
            for k in range(len(self.analog_channels)):  # for each channel
                current_chan_name = self.analog_channels[k]
                chan = DSM_CHANNELS[current_chan_name]['physChan']
                if dev == chan[3]:  # if this device matches, put it in this task
                    # self.ts.log_debug('Current Channel: %s' % current_chan_name)
                    if chan not in self.physical_channel_list[unique_dev_num]:  # do not duplicate physical channels
                        self.physical_channel_str[unique_dev_num] += chan + ','
                        self.physical_channel_list[unique_dev_num].append(chan)
                        self.chan_decoder[unique_dev_num].append(current_chan_name)
                    else:  # create dictionary that maps recorded channels to other channels using the same phys channel
                        for prior_chan in self.physical_channel_list[unique_dev_num]:
                            if prior_chan == chan:  # if the channel matches one of the previous, get the index
                                chan_idx = self.physical_channel_list[unique_dev_num].index(prior_chan)
                                prior_channel_name = self.chan_decoder[unique_dev_num][chan_idx]
                                # self.ts.log_debug('Prior Channel: %s, Prior Channel Name: %s, '
                                #                   'Current Channel: %s, Current Channel Name: %s' %
                                #                   (prior_chan, prior_channel_name, chan, current_chan_name))
                                try:
                                    self.duplicate_channels[prior_channel_name].append(current_chan_name)
                                except KeyError:
                                    self.duplicate_channels[prior_channel_name] = [current_chan_name]

        self.ts.log_debug('Duplicate Channel dict: %s' % self.duplicate_channels)

        for dev in range(len(self.sorted_unique)):  # clean up last comma
            self.physical_channel_str[dev] = self.physical_channel_str[dev][:-1]  # Remove the last comma.
        self.ts.log_debug('Sampling the following analog channels: %s' % self.physical_channel_str)

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
        return 'DAS Hardware: Sandia DAQ7 NI PCIe Cards'

    def open(self):
        pass

    def close(self):
        pass

    def data_capture(self, enable=True):  # Enable/disable RMS data capture
        pass

    def data_read(self):
        # Virtual channels are created. Each one of the virtual channels in question here is used to acquire
        # from an analog voltage signal(s).
        for k in range(len(self.sorted_unique)):
            self.analog_input[k].CreateAIVoltageChan(self.physical_channel_str[k],  # The physical name of the channel
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

            self.ts.log_debug('Acquired %d points' % self.read.value)
            self.ts.log_debug('raw_data length: %s' % len(self.raw_data[k]))

        # create null data set with timestamp
        datarec = {'TIME': time.time(),
                   'utility_v_phA': None,
                   'mcc_v_phA': None,
                   'mcc_i_phA': None,
                   'mcc_v_phB': None,
                   'mcc_i_phB': None,
                   'mcc_v_phC': None,
                   'mcc_i_phC': None,
                   'load_v_phA': None,
                   'load_i_phA': None,
                   'load_v_phB': None,
                   'load_i_phB': None,
                   'load_v_phC': None,
                   'load_i_phC': None,
                   'genset_v_phA': None,
                   'genset_i_phA': None,
                   'genset_v_phB': None,
                   'genset_i_phB': None,
                   'genset_v_phC': None,
                   'genset_i_phC': None,
                   'pv_v_phA': None,
                   'pv_i_phA': None,
                   'pv_v_phB': None,
                   'pv_i_phB': None,
                   'pv_v_phC': None,
                   'pv_i_phC': None,
                   'bat_v_phA': None,
                   'bat_i_phA': None,
                   'bat_v_phB': None,
                   'bat_i_phB': None,
                   'bat_v_phC': None,
                   'bat_i_phC': None,
                   'mcc_freq': None,
                   'mcc_p': None,
                   'mcc_s': None,
                   'mcc_q': None,
                   'mcc_pf': None,
                   'load_freq': None,
                   'load_p': None,
                   'load_s': None,
                   'load_q': None,
                   'load_pf': None,
                   'genset_freq': None,
                   'genset_p': None,
                   'genset_s': None,
                   'genset_q': None,
                   'genset_pf': None,
                   'pv_freq': None,
                   'pv_p': None,
                   'pv_s': None,
                   'pv_q': None,
                   'pv_pf': None,
                   'bat_freq': None,
                   'bat_p': None,
                   'bat_s': None,
                   'bat_q': None,
                   'bat_pf': None
                   }

        try:
            for k in range(len(self.sorted_unique)-1, -1, -1):
                self.analog_input[k].StopTask()
                self.analog_input[k].TaskControl(DAQmx_Val_Task_Unreserve)
        except Exception as e:
            self.ts.log_error('Error with DAQmx in StopTask. Returning nones... %s' % e)
            return datarec

        # Scale and save the waveform data
        dev_idx = -1
        data = {}
        rms_data = {}
        chan_idx = None
        for k in range(len(self.analog_channels)):
            # self.ts.log_debug('Getting data for %s' % self.analog_channels[k])
            for j in range(len(self.chan_decoder)):
                # self.ts.log_debug('Looking in data set: %s' % self.chan_decoder[j])
                if any(self.analog_channels[k] in s for s in self.chan_decoder[j]):
                    dev_idx = j
                    chan_idx = self.chan_decoder[j].index(self.analog_channels[k])
                    break
            if chan_idx is not None:
                # self.ts.log_debug('Converting raw data to scaled values for %s' % self.analog_channels[k])
                scaled_data = dsm_expression(channel_name=self.analog_channels[k],
                                             dsm_value=self.raw_data[dev_idx][chan_idx*self.n_samples:(chan_idx+1)*self.n_samples])
                data[self.analog_channels[k]] = scaled_data

                # Calculate all the RMS current and voltage values
                rms_data[self.analog_channels[k]] = waveform_analysis.calculateRMS(scaled_data)  # index RMS value in dict under the channel name
                svp_name = dsm_points_mcc_reversed.get(self.analog_channels[k])  # get the name that will appear in the SVP
                # self.ts.log_debug('Storing data for %s (%s)' % (self.analog_channels[k], svp_name))
                datarec[svp_name] = rms_data[self.analog_channels[k]]  # add RMS data to recorded data under SVP name

            # check to see if this data also belongs to other channels
            for key, value in self.duplicate_channels.items():
                if key == self.analog_channels[k]:
                    for j in value:
                        svp_name = dsm_points_mcc_reversed.get(j)
                        # self.ts.log_debug('Duplicating data for %s (%s) from %s' %
                        #                   (j, svp_name, self.analog_channels[k]))
                        datarec[svp_name] = rms_data[self.analog_channels[k]]

        self.ts.log_debug(datarec)

        # Calculate AC information for each device/metered point
        sets = ['mcc', 'load', 'genset', 'pv', 'bat']
        for s in sets:
            ac_voltage_a = None
            ac_voltage_b = None
            ac_voltage_c = None
            ac_current_a = None
            ac_current_b = None
            ac_current_c = None
            for analog_chan_name, dsm_name in dsm_points_mcc.items():
                # self.ts.log_debug('Checking to see if %s is in %s' % (s, k))
                if analog_chan_name.find(s) != -1:
                    self.ts.log_debug('Found Channel %s' % analog_chan_name)
                    if analog_chan_name[-5:] == 'v_phA':
                        ac_voltage_a = data[dsm_name]
                        svp_name = s + '_freq'
                        datarec[svp_name], _ = waveform_analysis.freq_from_crossings(self.time_vector, ac_voltage_a,
                                                                                     self.sample_rate)
                    elif analog_chan_name[-5:] == 'v_phB':
                        ac_voltage_b = data[dsm_name]
                    elif analog_chan_name[-5:] == 'v_phC':
                        ac_voltage_c = data[dsm_name]
                    elif analog_chan_name[-5:] == 'i_phA':
                        ac_current_a = data[dsm_name]
                    elif analog_chan_name[-5:] == 'i_phB':
                        ac_current_b = data[dsm_name]
                    elif analog_chan_name[-5:] == 'i_phC':
                        ac_current_c = data[dsm_name]
                    else:
                        self.ts.log_warning('Unexpected data set: %s' % analog_chan_name)

            self.ts.log_debug(datarec)

            avg_P_a = None
            avg_P_b = None
            avg_P_c = None
            S_a = None
            S_b = None
            S_c = None
            Q1_a = None
            Q1_b = None
            Q1_c = None
            PF1_a = None

            if ac_voltage_a is not None and ac_current_a is not None:
                avg_P_a, S_a, Q1_a, N_a, PF1_a = waveform_analysis.harmonic_analysis(self.time_vector,
                                                                                     ac_voltage_a, ac_current_a,
                                                                                     self.sample_rate, self.ts)
            else:
                self.ts.log_debug('Missing phase A current or voltage datasets for %s' % s)

            if ac_voltage_b is not None and ac_current_b is not None:
                avg_P_b, S_b, Q1_b, N_b, PF1_b = waveform_analysis.harmonic_analysis(self.time_vector,
                                                                                     ac_voltage_b, ac_current_b,
                                                                                     self.sample_rate, self.ts)
            else:
                self.ts.log_debug('Missing phase B current or voltage datasets for %s' % s)

            if ac_voltage_c is not None and ac_current_c is not None:
                avg_P_c, S_c, Q1_c, N_c, PF1_c = waveform_analysis.harmonic_analysis(self.time_vector,
                                                                                     ac_voltage_c, ac_current_c,
                                                                                     self.sample_rate, self.ts)
            else:
                self.ts.log_debug('Missing phase C current or voltage datasets for %s' % s)

            datarec[s + '_p'] = avg_P_a + avg_P_b + avg_P_c
            datarec[s + '_s'] = S_a + S_b + S_c
            datarec[s + '_q'] = Q1_a + Q1_b + Q1_c
            datarec[s + '_pf'] = PF1_a

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
                self.analog_input[k].CreateAIVoltageChan(self.physical_channel_str[k],  # The physical name of the channel
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
        chan_idx = None
        for k in range(len(self.analog_channels)):
            # print('Getting data for %s' % analog_channels[k])
            for j in range(len(self.chan_decoder)):
                # print('Looking in data set: %s' % chan_decoder[j])
                if any(self.analog_channels[k] in s for s in self.chan_decoder[j]):
                    dev_idx = j
                    chan_idx = self.chan_decoder[j].index(self.analog_channels[k])
                    break
            if chan_idx is not None:
                scaled_data = dsm_expression(channel_name=self.analog_channels[k],
                                             dsm_value=self.raw_data[dev_idx][chan_idx*self.n_samples:(chan_idx+1)*self.n_samples])
                data[self.analog_channels[k]] = scaled_data
            else:
                print('No channel index')
            ds.points.append(dsm_points_mcc.get(self.analog_channels[k]))
            ds.data.append(data[self.analog_channels[k]])  # first row for first signal and so on

        return ds


def dsm_expression(channel_name, dsm_value):
    x = dsm_value  # this is required for the expression calculation
    # print(DSM_CHANNELS[channel_name]['expression'])
    return eval(DSM_CHANNELS[channel_name]['expression'])


def c7_relay(new_state='close', device=(3, 0, 17)):
    if new_state == 'open':
        ditigal_wfm_data = np.array([0], dtype=np.uint8)
        # print('Opening C7 Relay')
    elif new_state == 'close':
        ditigal_wfm_data = np.array([1], dtype=np.uint8)
        # print('Closing C7 Relay')
    else:
        print(('Unknown new switch state: %s' % new_state))
        return

    task = Task()
    dev = "Dev%d/port%d/line%d" % (device[0], device[1], device[2])
    task.CreateDOChan(dev, "", DAQmx_Val_ChanForAllLines)
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

    # for i in [3]:
    #     for j in range(3):
    #         for k in range(24):
    #             print('Switching Dev%s, port%s, line%s' % (i, j, k))
    #             try:
    #                 c7_relay(new_state='close', device=[i, j, k])
    #                 time.sleep(1)
    #                 c7_relay(new_state='open', device=[i, j, k])
    #                 time.sleep(1)
    #             except Exception, e:
    #                 print('Dev%s, port%s, line%s does not exist' % (i, j, k))

    analog_channels = ['MCC_PhA_V', 'MCC_PhA_I', 'Diesel_Genset_PhC_V', 'ESTB_PhA_V']
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
        raw_data.append(np.zeros((n_points*i,), dtype=np.float64))
    print(n_channels)
    print(('raw_data length: %s' % len(raw_data[0])))

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

    print(('Capturing Waveforms on Channels: %s' % physical_channels))
    print(('Waveforms Channels are: %s' % chan_decoder))

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

    for i in range(len(sorted_unique)-1, -1, -1):
        # Start Master last so slave(s) will wait for trigger from master over RSTI bus
        print(('Starting Task: %s.' % i))
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

        print("Acquired %d points" % read.value)
        print(('raw_data length: %s' % len(raw_data[i])))

    for i in range(len(sorted_unique)-1, -1, -1):
        analog_input[i].StopTask()
        analog_input[i].TaskControl(DAQmx_Val_Task_Unreserve)

    dev_idx = -1
    data = {}
    chan_idx = None
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
        if chan_idx is not None:
            scaled_data = dsm_expression(channel_name=analog_channels[i],
                                         dsm_value=raw_data[dev_idx][chan_idx*n_points:(chan_idx+1)*n_points])
            data[analog_channels[i]] = scaled_data
        else:
            print('No Channel Index Found')

    time_vector = np.linspace(0., n_points/sample_rate, n_points)
    # print('time length: %s' % (len(time_vector)))
    # for i in range(len(analog_channels)):
    #     print('data length: %s' % (len(data[analog_channels[i]])))

    import matplotlib.pyplot as plt
    # plt.plot(time, ac_voltage_10, 'r', time, ac_current_10, 'b')
    # plt.show()

    fig, ax1 = plt.subplots()
    ax1.plot(time_vector, data[analog_channels[0]], 'b-')
    ax1.plot(time_vector, data[analog_channels[1]], 'k-')
    ax1.plot(time_vector, data[analog_channels[2]], 'c-')
    ax1.plot(time_vector, data[analog_channels[3]], 'm-')
    ax1.set_xlabel('time (s)')
    # Make the y-axis label and tick labels match the line color.
    ax1.set_ylabel('AC Voltage', color='b')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    plt.show()

    avg_P, S, Q1, N, PF1 = waveform_analysis.harmonic_analysis(time_vector, data[analog_channels[0]],
                                                               data[analog_channels[1]],
                                                               sample_rate, None)

    print(('Power = %s, Q = %s' % (avg_P, Q1)))

    f = open('C:\\SVP\\MCC_waveforms-P=%s, Q=%s.csv' % (avg_P, Q1), 'w')
    f.write('Python Time (s), AC Voltage (V), AC Current (A)\n')
    for t in range(len(time_vector)):
        f.write('%0.6f, %0.6f, %0.6f\n' % (time_vector[t], data[analog_channels[0]][t], data[analog_channels[1]][t]))
    f.close()

