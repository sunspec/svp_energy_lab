"""
Copyright (c) 2020, Sandia National Laboratories
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
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
from . import vxi11
import numpy as np
from pylab import *
import math
from . import dataset

DATA_POINTS = [  # 3 phase
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
    'TRIG_GRID',
    'SWITCH_LOSS_1',
    'BLOCK_LOSS_1',
    'CONDUCT_LOSS_1',
    'SWITCH_LOSS_2',
    'BLOCK_LOSS_2',
    'CONDUCT_LOSS_2',
    'DCBUS_RIPPLE_V',
    'DCBUS_V',
    'DCBUS_RIPPLE_I',
    'DCBUS_I',
    'V_OFF_1',
    'I_OFF_1',
    'V_OFF_2',
    'I_OFF_2',
    'WAVENAME'
]


def pf_scan(points, pf_points):
    for i in range(len(points)):
        if points[i].startswith('AC_PF'):
            label = points[i][5:]
            try:
                p_index = points.index('AC_P%s' % label)
                q_index = points.index('AC_Q%s' % label)
                pf_points.append((i, p_index, q_index))
            except ValueError:
                pass


class DeviceError(Exception):
    """
    Exception to wrap all das generated exceptions.
    """
    pass


class Device(object):

    def __init__(self, params):
        self.vx = None  # tcp implementation
        self.conn = None  # visa implementation
        self.params = params
        self.comm = params.get('comm')  # the communication connection type, e.g., "VISA", "TCPIP", "GPIB"
        self.visa_id = params.get('visa_id')
        self.ts = params.get('ts')
        self.sample_interval = params.get('sample_interval')
        self.save_wave = params.get('save_wave')

        self.data_points = []
        for x in range(len(DATA_POINTS)):
            self.data_points.append(DATA_POINTS[x])  # don't link DATA_POINTS to self.data_points
        self.channel_types = params.get('channel_types')  # List
        # Options: 'Switch_Current', 'Switch_Voltage', 'Bus_Voltage', 'None'
        self.chan_types = {1: self.channel_types[0],
                           2: self.channel_types[1],
                           3: self.channel_types[2],
                           4: self.channel_types[3]}

        self.vertical_scale = params.get('vertical_scale')
        if self.vertical_scale is None:
            self.vertical_scale = [5., 5., 5., 5.]  # V/div

        self.trig_chan = params.get('trig_chan')
        if self.trig_chan is None:
            self.ts.log_debug('Trigger Channel is None!!')
            self.trig_chan = 'Chan 4'

        self.trig_level = params.get('trig_level')
        if self.trig_level is None:
            self.trig_level = 20

        self.trig_slope = params.get('trig_slope')
        if self.trig_slope is None:
            self.trig_slope = 'Fall'

        self.horiz_scale = params.get('horiz_scale')
        if self.horiz_scale is None:
            self.horiz_scale = 20e-6  # time scale s/div...full scale = 10 * scale

        self.sample_rate = params.get('sample_rate')
        if self.sample_rate is None:
            self.sample_rate = 2.5e9  # sets rate of sampling...total time = length / rate

        self.length = params.get('length')
        if self.length is None:
            self.length = '1k'  # sets record length...valid values are 1k, 10k, 100k, 1M, 5M

        if self.params.get('comm') == 'VISA':
            try:
                # sys.path.append(os.path.normpath(self.visa_path))
                import visa
                self.rm = visa.ResourceManager()
                self.conn = self.rm.open_resource(params.get('visa_id'))
                self.conn.encoding = 'latin_1'
                self.conn.write_termination = '\n'

                try:
                    if self.ts is not None:
                        self.ts.sleep(1)
                    else:
                        time.sleep(1)
                except Exception as e:
                    time.sleep(1)

            except Exception as e:
                raise Exception('Cannot open VISA connection to %s\n\t%s' % (params.get('visa_id'), str(e)))

        # clear any error conditions
        self.cmd('*CLS')
        self.config()
        self.dType, self.bigEndian = self.get_waveform_info()

    def config(self):
        self.cmd('AUTOSet EXECute')
        if self.ts is not None:
            self.ts.sleep(5)
        else:
            time.sleep(5)
        opc = self.query('*OPC?')  # waiting for command execution?
        while opc != '1\n':
            # self.ts.log(opc)
            time.sleep(1)
            # self.ts.log('waiting for previous command to finish...')
        self.ts.log_debug('Setting vertical and horizontal scale...')
        self.set_vertical_scale()
        self.set_horizontal_scale()
        self.set_trigger()

        # turn on all channels
        for i in range(0, 4):
            self.ts.log('turning on channel ' + str(i + 1) + '...')
            self.cmd('SELect:CH' + str(i + 1) + ' ON')
        self.cmd('ACQ:STOPA SEQ')
        self.cmd('ACQUIRE:STATE RUN')  # go to RUN state
        # ACQuire:MODe {SAMple|PEAKdetect|HIRes|AVErage|ENVelope}
        # self.cmd('ACQuire:MODe AVErage')
        # self.cmd('ACQuire:MODe HIRes')
        self.cmd('ACQuire:MODe SAMple')
        # self.cmd('ACQuire:NUMEnv 16')  # get 16 samples on average
        # self.cmd('ACQuire:NUMAVg 32')

    def set_vertical_scale(self):
        for i in range(0, 4):
            self.ts.log('setting vertical scale for CH' + str(i + 1) + ' at ' + str(self.vertical_scale[i]) + '...')
            self.cmd('CH' + str(i + 1) + ':SCAle ' + str(self.vertical_scale[i]))
            if self.chan_types.get(i + 1) == 'Bus_Voltage':
                self.cmd('CH' + str(i + 1) + ':POSition ' + str(-5))
                self.cmd('CH' + str(i + 1) + ':OFFset ' + str(430))
            else:
                self.cmd('CH' + str(i + 1) + ':POSition ' + str(0))
                self.cmd('CH' + str(i + 1) + ':OFFSet ' + str(0))
        return self.query('CH' + str(i + 1) + ':SCAle?')

    def set_horizontal_scale(self):
        self.cmd('HORizontal:RECOrdlength ' + str(self.length))
        self.cmd('HORizontal:SCAle ' + str(self.horiz_scale))
        # self.ts.log('setting number of acquired points to ', self.query(':HORIZONTAL:ACQLENGTH?') + '...')
        self.cmd('HORizontal:DELay:MODe OFF')
        # self.ts.log('setting sampling rate to maximum...')

        max_sample = float(self.query('ACQUIRE:MAXSAMPLERATE?'))
        if max_sample < self.sample_rate:
            raise DeviceError('Sample rate is greater than supported rate of %s' % max_sample)
        self.cmd('HORIZONTAL:MAIN:SAMPLERATE ' + str(self.sample_rate))
        horizontal = self.query('HORizontal?')
        # print(horizontal)
        # self.ts.log(self.query('HORizontal:ACQLENGTH?'))
        # self.ts.log(self.query('HORizontal:MAIn?'))
        # self.ts.log(horizontal)
        return horizontal

    def cmd(self, cmd_str):
        if self.params['comm'] == 'VISA':
            try:
                self.conn.write(cmd_str)
            except Exception as e:
                raise DeviceError('DPO3000 communication error: %s' % str(e))

    def query(self, cmd_str, binary=None):
        try:
            resp = ''
            if self.params.get('comm') == 'VISA':
                if binary:
                    # returns list
                    resp = self.conn.query_binary_values(cmd_str, datatype=self.dType, is_big_endian=self.bigEndian)
                else:
                    # returns str
                    resp = self.conn.query(cmd_str)

        except Exception as e:
            raise DeviceError('DPO3000 communication error: %s' % str(e))

        return resp

    def open(self):
        pass

    def close(self):
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception as e:
            self.ts.log_error('Could not close DPO3000: %s' % e)
        finally:
            self.conn = None

    def info(self):
        return self.query('*IDN?').rstrip('\n\r')

    def data_capture(self, enable=True):
        """
        Enable/disable data capture.

        If sample_interval == 0, there will be no autonomous data captures and self.data_sample should be used to add
        data points to the capture
        """

        # self.cmd("SAVE:WAVEFORM:FILEFORMAT SPREADSHEET")
        # self.cmd("SAVE:WAVEFORM:SPREADSHEET:RESOLUTION FULL")
        #
        # # Create directory where files will be saved
        # self.cmd("FILESYSTEM:MAKEDIR \"E:/Saves\"")
        pass

    def data_read(self):
        """
        Return the last data sample from the data capture in expanded format.
        """
        self.start_acquisition()

        wfm_sw_i = None
        wfm_sw_v = None
        wfm_sw_i_2 = None
        wfm_sw_v_2 = None
        wfm_bus_v = None
        wfm_bus_i = None
        times = None
        for i in range(1, 5):  # pull data from each channel
            self.ts.log_debug('Pulling data from Channel %i' % i)
            if self.chan_types.get(i) != 'None':
                # self.ts.log_debug('Bus Type = %s' % self.chan_types.get(i))
                if self.chan_types.get(i) == 'Switch_Current':
                    times, wfm_sw_i = self.bitstream_to_analog(channel=i)
                if self.chan_types.get(i) == 'Switch_Voltage':
                    times, wfm_sw_v = self.bitstream_to_analog(channel=i)
                if self.chan_types.get(i) == 'Bus_Voltage':
                    times, wfm_bus_v = self.bitstream_to_analog(channel=i)
                    # self.ts.log(wfm_bus_v)
                if self.chan_types.get(i) == 'Bus_Current':
                    times, wfm_bus_i = self.bitstream_to_analog(channel=i)

        # save the waveform data to a csv in the test manifest
        wave_filename = None
        if self.save_wave == 'Yes':
            self.ts.log('Saving a .csv file of the waveform. This will take a while...')
            ds = dataset.Dataset()
            wave_filename = '%s_wave.csv' % time.time()
            self.ts.log('Saving file: %s' % wave_filename)
            ds.points.append('TIME')
            if times is not None:
                ds.data.append(times)
            else:
                ds.data.append([0, 0])
            for chan in range(0, 4):
                self.ts.log_debug(chan + 1)
                self.ts.log_debug(self.chan_types.get(chan + 1))
                if self.channel_types[chan] != 'None':
                    ds.points.append(self.channel_types[chan])
                    if self.chan_types.get(chan + 1) == 'Switch_Current':
                        # self.ts.log_debug(wfm_sw_i)
                        ds.data.append(wfm_sw_i)
                    if self.chan_types.get(chan + 1) == 'Switch_Voltage':
                        # self.ts.log_debug(wfm_sw_v)
                        ds.data.append(wfm_sw_v)
                    if self.chan_types.get(chan + 1) == 'Bus_Voltage':
                        # self.ts.log_debug(wfm_bus_v)
                        ds.data.append(wfm_bus_v)
                    if self.chan_types.get(chan + 1) == 'Bus_Current':
                        # self.ts.log_debug(wfm_bus_i)
                        ds.data.append(wfm_bus_i)
            self.ts.log_debug(wave_filename)
            self.ts.log_debug(self.ts.result_file_path(wave_filename))
            ds.to_csv(self.ts.result_file_path(wave_filename))
            self.ts.result_file(wave_filename)

        v_off_1 = None
        i_off_1 = None
        v_off_2 = None
        i_off_2 = None
        if wfm_sw_i is not None and wfm_sw_v is not None:
            switch_loss_energy, block_loss_energy, conduct_loss_energy, v_off_1, i_off_1 = \
                self.calc_switch_loss(time_vect=times, current=wfm_sw_i, voltage=wfm_sw_v)
        else:
            switch_loss_energy = None
            block_loss_energy = None
            conduct_loss_energy = None

        # TODO add 2nd switch loss
        if wfm_sw_i_2 is not None and wfm_sw_v_2 is not None:
            switch_loss_energy_2, block_loss_energy_2, conduct_loss_energy_2, v_off_2, i_off_2 = \
                self.calc_switch_loss(time_vect=times, current=wfm_sw_i, voltage=wfm_sw_v)
        else:
            switch_loss_energy_2 = None
            block_loss_energy_2 = None
            conduct_loss_energy_2 = None

        if wfm_bus_v is not None:
            bus_ripple_v, bus_v = self.calc_bus_ripple(time_vect=times, data=wfm_bus_v)
            self.ts.log_debug('Bus_V = %s' % bus_v)
            self.ts.log_debug('Bus_Ripple_V = %s' % bus_ripple_v)
        else:
            bus_ripple_v = None
            bus_v = None

        if wfm_bus_i is not None:
            bus_ripple_i, bus_i = self.calc_bus_ripple(time_vect=times, data=wfm_bus_i)
            self.ts.log_debug('Bus_I = %s' % bus_i)
            self.ts.log_debug('Bus_Ripple_I = %s' % bus_ripple_i)
        else:
            bus_ripple_i = None
            bus_i = None

        datarec = {'TIME': time.time(),
                   'AC_VRMS_1': None,
                   'AC_IRMS_1': None,
                   'AC_P_1': None,
                   'AC_S_1': None,
                   'AC_Q_1': None,
                   'AC_PF_1': None,
                   'AC_FREQ_1': None,
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
                   'DC_V': None,
                   'DC_I': None,
                   'DC_P': None,
                   'TRIG': 0,
                   'TRIG_GRID': 0,
                   'SWITCH_LOSS_1': switch_loss_energy,
                   'SWITCH_LOSS_2': switch_loss_energy_2,
                   'BLOCK_LOSS_1': block_loss_energy,
                   'BLOCK_LOSS_2': block_loss_energy_2,
                   'CONDUCT_LOSS_1': conduct_loss_energy,
                   'CONDUCT_LOSS_2': conduct_loss_energy_2,
                   'DCBUS_RIPPLE_V': bus_ripple_v,
                   'DCBUS_V': bus_v,
                   'DCBUS_RIPPLE_I': bus_ripple_i,
                   'DCBUS_I': bus_i,
                   'V_OFF_1': v_off_1,
                   'I_OFF_1': i_off_1,
                   'V_OFF_2': v_off_2,
                   'I_OFF_2': i_off_2,
                   'WAVENAME': wave_filename}

        data = []
        # self.ts.log_debug('DATA_POINTS=%s, self.data_points=%s' % (DATA_POINTS,  self.data_points))
        for chan in DATA_POINTS:
            # self.ts.log_debug('chan = %s' % chan)
            if chan[0:3] != 'SC_':
                if datarec.get(chan) is not None:
                    data.append(datarec[chan])
                    # self.ts.log_debug('data = %s' % datarec[chan])
                else:
                    data.append(None)
                    # self.ts.log_debug('data = NO DATA/NONE')

        return data

    def set_trigger(self):
        if self.trig_chan == 'Chan 1':
            chan = 'CH1'
        elif self.trig_chan == 'Chan 2':
            chan = 'CH2'
        elif self.trig_chan == 'Chan 3':
            chan = 'CH3'
        elif self.trig_chan == 'Chan 4':
            chan = 'CH4'
        elif self.trig_chan == 'Line':
            chan = 'Line'
        else:
            print('unknown trigger channel, assuming channel 1 for the trigger')
            chan = 'Chan 1'

        self.ts.log_debug('Trigger Channel = %s' % self.trig_chan)
        self.ts.log_debug('Trigger Level = %s' % self.trig_level)
        self.ts.log_debug('Trigger Slope = %s' % self.trig_slope)

        self.cmd('TRIGger:A:EDGE:SOUrce ' + chan)
        self.cmd('TRIGger:A:LEVel ' + str(self.trig_level))
        self.cmd('TRIGger:A:EDGE:SLOpe ' + self.trig_slope)
        # TRIGger:A:EDGE:COUPling {AC|DC|HFRej|LFRej|NOISErej}
        self.cmd('TRIGger:A:EDGE:COUPling HFRej')
        pass

    def calc_bus_ripple(self, time_vect=None, data=None):
        # number of slices in data to calculate ripple
        # num_slice = 1000
        # slice_length = int(self.length) / num_slice
        # rip = []
        # for n in range(0, num_slice - 1):
        #     start = n * slice_length
        #     stop = (n + 1) * slice_length
        #     temp = [n, num_slice, slice_length, start, stop, len(data)]
        #     # self.ts.log_debug(temp)
        #     rip.append(max(data[start:stop])-min(data[start:stop]))
        # # self.ts.log_debug('Measured Ripple = %s' % rip)
        # bus_rip = mean(rip)
        # bus_rip = min(rip)
        # bus_rip = max(data) - min(data)
        bus_mag = mean(data)

        f_s = 1 / (time_vect[1] - time_vect[0])  # Hz  sampling frequency
        f = 1.0  # Hz
        N = len(time_vect)
        T = 1 / f_s

        FFT = np.fft.fft(data)
        n = len(FFT)
        yf = np.linspace(0.0, 1.0 / (2.0 * T), N // 2)
        # print('f_s = ', f_s, f_s/N, yf[round(120/(f_s/N))], 2.0/N * np.abs(FFT[round(120/(f_s/N))]),
        #       sum(2.0/N * np.abs(FFT)))
        subset = FFT[0:N // 2]

        # self.ts.log_debug(yf[round(110/(f_s/N)):round(130/(f_s/N))])
        # self.ts.log_debug(2.0/N * np.abs(FFT[round(110/(f_s/N)):round(130/(f_s/N))]))
        # self.ts.log_debug(sum(2.0/N * np.abs(FFT[round(110/(f_s/N)):round(130/(f_s/N))])))

        amplitude_120 = sum(2.0 / N * np.abs(FFT[round(110 / (f_s / N)):round(130 / (f_s / N))]))
        pk_pk_120 = 2 * amplitude_120
        # amplitude_mppt = sum(2/N * np.abs(FFT[round(1/(f_s/N)):round(10/(f_s/N))]))
        # pk_pk_mppt = 2 * sum(2/N * np.abs(FFT[round(1/(f_s/N)):round(10/(f_s/N))]))
        bus_rip = pk_pk_120
        # self.ts.log_debug(pk_pk_120)
        # self.ts.log_debug(bus_rip)

        self.ts.log_debug('Measured 120Hz Ripple = %s' % pk_pk_120)
        self.ts.log_debug('Bus Mag = %s' % bus_mag)
        # self.ts.log_debug('Max Ripple = %s' % max(rip))

        return bus_rip, bus_mag

    def calc_switch_loss(self, time_vect=None, current=None, voltage=None):
        """
        Calculate total dissipated energy (J/s)

         param: time_vect - time vector list
         param: current - current list
         param: voltage - voltage list

        """

        # determine time step
        dt = round(time_vect[-1] - time_vect[-2], 11)
        # self.ts.log('dT = ', dT)
        for i in range(1, len(time_vect)):
            temp = round(time_vect[i] - time_vect[i - 1], 11)
            if temp != dt:
                self.ts.log_warning('Uneven time step!')
                self.ts.log_warning(temp, dt)

        # need to determine I_offset and V_offset automatically
        print('voltage offset')
        volt_offset, volt_max = self.get_probe_offset(voltage)
        print(volt_offset)
        print('current offset')
        curr_offset, curr_max = self.get_probe_offset(current)
        print(curr_offset)
        self.ts.log_debug('Voltage Offset = %s' % volt_offset)
        self.ts.log_debug('Current Offset = %s' % curr_offset)
        self.ts.log_debug('Voltage Max = %s' % volt_max)

        # self.ts.log('Voltage offset = %s' % volt_offset)
        # self.ts.log('Current offset = %s' % curr_offset)

        # re-bias time so it always starts at 0
        start = time_vect[0]
        for i in range(0, len(time_vect)):
            time_vect[i] = time_vect[i] - start

            if curr_offset <= 0:
                current[i] = current[i] - curr_offset
            else:
                current[i] = current[i] + curr_offset
            if volt_offset <= 0:
                voltage[i] = voltage[i] + volt_offset
            else:
                voltage[i] = voltage[i] - volt_offset

        # Calculate the instantaneous power
        # Calculate the cumulative energy

        power = []
        block_power = []
        conduct_power = []

        energy = []
        block_energy = []
        conduct_energy = []

        cum_energy = [0]
        cum_block_energy = [0]
        cum_conduct_energy = [0]

        unknown = []

        high = 0.90
        low = 0.10
        current_status = []
        for i in range(0, len(current)):
            if voltage[i] < (low * volt_max):
                power.append(0)
                block_power.append(0)
                conduct_power.append(current[i] * voltage[i])
                unknown.append(0)
                current_status.append('conducting')
            elif (high * volt_max) >= voltage[i] >= (low * volt_max):
                power.append(current[i] * voltage[i])
                conduct_power.append(0)
                block_power.append(0)
                unknown.append(0)
                current_status.append('switching')
            elif voltage[i] > (high * volt_max):
                power.append(0)
                conduct_power.append(0)
                block_power.append(current[i] * voltage[i])
                unknown.append(0)
                current_status.append('blocking')
            else:
                power.append(0)
                conduct_power.append(0)
                block_power.append(0)
                unknown.append(current[i] * voltage[i])
                current_status.append('unknown')
        pre = 20
        for i in range(pre, len(current_status)):
            if current_status[i] == 'switching' and current_status[i - 1] == 'blocking':
                # print(block_power[i - pre:i - 1], power[i - pre:i - 1])
                current_status[i - pre:i - 1] = ['switching'] * len(current_status[i - pre:i - 1])
                power[i - pre:i - 1] = block_power[i - pre:i - 1]
                block_power[i - pre:i - 1] = [0] * len(block_power[i - pre:i - 1])
                # print(block_power[i-pre:i-1], power[i-pre:i-1])
            else:
                pass

        for i in range(len(current_status), pre, -1):
            # self.ts.log_debug('i is %s' % i)
            if current_status[i - 1] == 'switching' and current_status[i] == 'blocking':
                # print(block_power[i:i + pre], power[i:i + pre])
                current_status[i:i + pre] = ['switching'] * len(current_status[i:i + pre])
                power[i:i + pre] = block_power[i:i + pre]
                block_power[i:i + pre] = [0] * len(block_power[i:i + pre])
                # print(block_power[i:i+pre], power[i:i+pre])
            else:
                pass
        for i in range(0, len(current)):
            energy.append(power[i] * dt)
            cum_energy.append(energy[i] + cum_energy[-1])

            block_energy.append(block_power[i] * dt)
            cum_block_energy.append(block_energy[i] + cum_block_energy[-1])

            conduct_energy.append(conduct_power[i] * dt)
            cum_conduct_energy.append(conduct_energy[i] + cum_conduct_energy[-1])
        self.ts.log_debug('Average Switch Power (W) = %s' % str(mean(power)))
        self.ts.log_debug('Average Conducting Power (W) = %s' % str(mean(conduct_power)))
        self.ts.log_debug('Average Blocking Power (W) = %s' % str(mean(block_power)))
        self.ts.log_debug('')
        self.ts.log_debug('Cumulative Switch Energy (J) = %s' % str(cum_energy[-1]))
        self.ts.log_debug('Switch Energy (J) per cycle (J/cycle)= %s' % str(cum_energy[-1] / time_vect[-1] * 16.66e-3))
        self.ts.log_debug('Cumulative Conducting Energy (J) = %s' % str(cum_conduct_energy[-1]))
        self.ts.log_debug('Conducting Energy (J) per cycle (J/cycle)= %s' %
                          str(cum_conduct_energy[-1] / time_vect[-1] * 16.66e-3))
        self.ts.log_debug('Cumulative Blocking Energy (J) = %s' % str(cum_block_energy[-1]))
        self.ts.log_debug('Blocking Energy (J) per cycle (J/cycle)= %s' %
                          str(cum_block_energy[-1] / time_vect[-1] * 16.66e-3))
        self.ts.log_debug('')
        self.ts.log_debug('Switch Power (J/s) = %s' % str(cum_energy[-1] / time_vect[-1]))
        self.ts.log_debug('Conducting Power (J/s) = %s' % str(cum_conduct_energy[-1] / time_vect[-1]))
        self.ts.log_debug('Blocking Power (J/s) = %s' % str(cum_block_energy[-1] / time_vect[-1]))
        self.ts.log_debug('')
        return cum_energy[-1] / time_vect[-1], cum_block_energy[-1] / time_vect[-1], \
               cum_conduct_energy[-1] / time_vect[-1], volt_offset, curr_offset  # Total dissipated energy (J/s)

    def get_probe_offset(self, data):
        """
        Determine probe offset using histogram
        """
        sor = sort(data)
        sor_min = sor[sor <= (0.5 * sor[-1])]
        sor_max = sor[sor > (0.5 * sor[-1])]

        # find min
        data_gram = histogram(data, bins=np.arange(sor_min[0], sor_min[-1], (sor_min[-1] - sor_min[0]) / 500))
        loc = np.where(data_gram[0] == max(data_gram[0]))
        data_offset = data_gram[1][loc][0]
        # find max
        data_gram = histogram(data, bins=np.arange(sor_max[0], sor_max[-1], (sor_max[-1] - sor_max[0]) / 500))
        loc2 = np.where(data_gram[0] == max(data_gram[0]))
        data_max = data_gram[1][loc2][0]
        # sor = sort(data)
        # hgram = histogram(data, bins=np.arange(sor[0], sor[-1], float(sor[-1]-sor[0]) / 100.))
        # loc = np.where(hgram[0] == max(hgram[0][0:int(round(len(hgram[0])/2))]))
        # loc2 = np.where(hgram[0] == max(hgram[0][round(len(hgram[0])/2):]))
        # data_max = hgram[1][loc2][0]
        # data_offset = hgram[1][loc][0]
        return data_offset, data_max

    def start_acquisition(self):
        # trigger a measurement
        permitted_failures = 10
        while permitted_failures >= 0:
            permitted_failures -= 1
            trig_state = self.query('TRIGger:STATE?').split('\n')[0]
            if self.ts is not None:
                self.ts.log('Scope is in ' + trig_state + ' mode...')
            else:
                print(('Scope is in ' + trig_state + ' mode...'))

            time.sleep(5)

            time.sleep(1)
            if trig_state == 'ARMED':
                if self.ts is not None:
                    self.ts.log('Scope is acquiring pretrigger information...')
                    self.ts.log('triggering...')
                else:
                    print('Scope is acquiring pretrigger information...')
                    print('triggering...')
                self.cmd('TRIGger')
                break
            elif trig_state == 'AUTO':
                if self.ts is not None:
                    self.ts.log('Scope is in the automatic mode and acquires data even in the absence of a trigger...')
                    self.cmd('TRIGger:A:MODe NORMal')
                else:
                    print('Scope is in the automatic mode and acquires data even in the absence of a trigger...')
                    self.cmd('TRIGger:A:MODe NORMal')
                break
            elif trig_state == 'READY':
                if self.ts is not None:
                    self.ts.log('all pretrigger information has been acquired and scope is ready to accept a trigger..')
                    self.ts.log('triggering...')
                else:
                    print('all pretrigger information has been acquired and scope is ready to accept a trigger..')
                    print('triggering...')
                self.cmd('TRIGger')
                break
            elif trig_state == 'SAVE' or trig_state == 'SAV':
                if self.ts is not None:
                    self.ts.log('Scope is in save mode and is not acquiring data...')
                else:
                    print('Scope is in save mode and is not acquiring data...')
                self.cmd('FPANEL:PRESS RUnstop')
            elif trig_state == 'TRIGGER' or trig_state == 'TRIG':
                if self.ts is not None:
                    self.ts.log('Scope triggered and is acquiring the post trigger information...')
                else:
                    print('Scope triggered and is acquiring the post trigger information...')
                break
            else:
                if self.ts is not None:
                    self.ts.log('unknown trigger state...')
                    self.ts.log('Trigger State is: %s' % trig_state)
                else:
                    print('unknown trigger state...')
                    self.ts.log('Trigger State is: %s' % trig_state)

        # Start single sequence acquisition
        self.cmd("ACQ:STOPA SEQ")

    def waveform(self):
        """
        Return waveform (Waveform) created from last waveform capture.
        """
        pass

    def bitstream_to_analog(self, channel=1):
        """
        Collect data and convert channels to current/voltage values
        """

        self.cmd('DATa:SOUrce CH' + str(channel))  # setup the channel to read

        """
        Get the conversion parameters to move bit stream into voltage/current values
        """

        x_incr = float(self.query('WFMOutpre:XINcr?').split('\n')[0])
        y_mu = float(self.query('WFMOutpre:YMUlt?').split('\n')[0])
        y_offset = float(self.query('WFMOutpre:YOFf?').split('\n')[0])
        y_zero = float(self.query('WFMOutpre:YZEro?').split('\n')[0])

        total_length = float(self.query('HORizontal:RECOrdlength?').split('\n')[0])
        """
        Get the conversion parameters to move bit stream into voltage/current values
        """
        # self.ts.log(y_offset)
        # self.ts.log(y_mu)
        # self.ts.log(y_zero)
        waveform = []  # single channel data set as list
        x = []  # time vector as list

        """
        Can only transfer 1M points at a time, so if the number of points is greater than 1M, then have to break it up
        """
        data = []

        if total_length > 1e6:
            num = int(math.ceil(total_length / 1e6))
            max_size = 1e6
        else:
            num = 1
            max_size = total_length

        for i in range(0, num):
            # self.ts.log('data start = ', str(1 + i * 1e6))
            # self.ts.log('data stop = ', str((i + 1) * 1e6))
            self.cmd('DATa:STARt ' + str(1 + i * max_size))
            self.cmd('DATa:STOP ' + str((i + 1) * max_size))
            opc = self.query('*OPC?')
            while opc != '1\n':
                # self.ts.log(opc)
                if self.ts is not None:
                    self.ts.sleep(1)
                else:
                    time.sleep(1)
                # self.ts.log('waiting for previous command to finish...')
            record = self.query('CURVe?', binary=True)
            opc = self.query('*OPC?')
            while opc != '1\n':
                # self.ts.log(opc)
                if self.ts is not None:
                    self.ts.sleep(1)
                else:
                    time.sleep(1)
                # self.ts.log('waiting for previous command to finish...')
            # self.ts.log(data)
            # data = data + record.split(',')
            data += record
            if self.ts is not None:
                self.ts.sleep(2)
            else:
                time.sleep(2)

            lst = [int(i) for i in data]
            # self.ts.log_debug(lst)
            rst = [tmp == int(127) for tmp in lst]
            rst_2 = [tmp == int(-127) for tmp in lst]
            # self.ts.log_debug(rst)
            if True in rst:
                # self.ts.log(rst)
                self.ts.log_warning('Positive Clipping at ' + str(len([i for i in lst if i == int(127)])) + ' of ' +
                                    str(len(rst)) + ' elements!!! Increase Channel Scale')
            if True in rst_2:
                # self.ts.log(rst_2)
                self.ts.log_warning('Negative Clipping at ' + str(len([i for i in lst if i == int(-127)])) + ' of ' +
                                    str(len(rst_2)) + ' elements!!! Reduce Channel Scale')

            # self.ts.log('data length = ', len(data))
            # Formula for computing horizontal (time) point value:
            # Xi= XZEro + XINcr * (i - 1)
            #
            # Formula for computing vertical (amplitude) point value:
            # Yi= YZEro + (YMUlt * DataPoint_i)
            # where:
            # i is the index of a curve data point 1 based: first data point is point number 1
            # Xi is the ith horizontal value in XUNits
            # Yi is the ith vertical value in YUNits

            """
            Convert data from bitstream into voltage/current values
            """

        for n in range(0, len(data)):
            # data[n] = (float(data[n]) * y_mu) + y_zero
            data[n] = ((float(data[n]) - y_offset) * y_mu) + y_zero
            waveform.append(data[n])
            # x.append(x_zero + len(x) * x_incr)
            x.append(len(x) * x_incr)
        # self.ts.log('number of datapoints = ', len(waveform), i)

        return x, waveform

    def status(self):
        """
        Returns dict with following entries:
            'trigger_wait' - waiting for trigger - True/False
            'capturing' - waveform capture is active - True/False
        """
        pass

    def get_waveform_info(self):
        self.conn.write('acquire:stopafter sequence')
        self.conn.write('acquire:state on')
        # dpo.query('*OPC?')
        binaryFormat = self.conn.query('wfmoutpre:bn_fmt?').rstrip()
        print('Binary format: ', binaryFormat)
        numBytes = self.conn.query('wfmoutpre:byt_nr?').rstrip()
        print('Number of Bytes: ', numBytes)
        byteOrder = self.conn.query('wfmoutpre:byt_or?').rstrip()
        print('Byte order: ', byteOrder)
        encoding = self.conn.query('data:encdg?').rstrip()
        print('Encoding: ', encoding)
        if 'RIB' in encoding or 'FAS' in encoding:
            dType = 'b'
            bigEndian = True
        elif encoding.startswith('RPB'):
            dType = 'B'
            bigEndian = True
        elif encoding.startswith('SRI'):
            dType = 'b'
            bigEndian = False
        elif encoding.startswith('SRP'):
            dType = 'B'
            bigEndian = False
        elif encoding.startswith('FP'):
            dType = 'f'
            bigEndian = True
        elif encoding.startswith('SFP'):
            dType = 'f'
            bigEndian = False
        elif encoding.startswith('ASCI'):
            raise visa.InvalidBinaryFormat('ASCII Formatting.')
        else:
            raise visa.InvalidBinaryFormat
        return dType, bigEndian


if __name__ == "__main__":
    import time
    import ftplib
    import visa

    params = {'comm': 'VISA'}
    ip_addr = '10.1.2.87'
    params['channels'] = [None, None, None, None, None]
    params['visa_id'] = "TCPIP::%s::INSTR" % ip_addr
    params['vertical_scale'] = [250., 250., 10., 5.]  # V/div
    params['horiz_scale'] = 2e-3  # time scale s/div...full scale = 10 * scale
    params['sample_rate'] = 2.5e9  # sets rate of sampling...total time = length / rate
    params['length'] = 1000  # sets record length...valid values are 1k, 10k, 100k, 1M, 5M
    # params['channel_types'] = ['Switch_Current', 'Switch_Voltage', 'None', 'None']
    params['channel_types'] = ['Switch_Voltage', 'Bus_Voltage', 'Bus_Current', 'Switch_Current', 'None']
    params['trig_level'] = -20.4
    params['trig_chan'] = 'Chan 3'
    params['trig_slope'] = 'Fall'

    das = Device(params=params)

    # Setup Acquisition
    das.config()
    das.set_horizontal_scale()
    das.set_vertical_scale()
    das.set_trigger()

    # trigger measurement
    print((das.data_read()))
