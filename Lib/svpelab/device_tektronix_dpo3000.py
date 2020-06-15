"""
Copyright (c) 2020, Sandia National Laboratories
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
    'SWITCH_LOSS_2',
    'DCBUS_RIPPLE',
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
                p_index = points.index('AC_P%s' % (label))
                q_index = points.index('AC_Q%s' % (label))
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
            # self.ts.log('turning on channel ' + str(i + 1) + '...')
            self.cmd('SELect:CH' + str(i + 1) + ' ON')
        self.cmd('ACQ:STOPA SEQ')
        self.cmd('ACQUIRE:STATE RUN')  # go to RUN state
        self.cmd('ACQuire:NUMEnv 16')  # get 16 samples on average

    def set_vertical_scale(self):
        for i in range(0, 4):
            # self.ts.log('setting vertical scale for CH' + str(i + 1) + ' at ' + str(self.vertical_scale[i]) + '...')
            self.cmd('CH' + str(i + 1) + ':SCAle ' + str(self.vertical_scale[i]))
            self.cmd('CH' + str(i + 1) + ':POSition ' + str(0))
            self.cmd('CH' + str(i + 1) + ':OFFSet ' + str(0))
        return self.query('CH' + str(i + 1) + ':SCAle?')

    def set_horizontal_scale(self):
        self.cmd('HORizontal:RECOrdlength ' + str(self.length))
        self.cmd('HORizontal:SCAle ' + str(self.horiz_scale))
        # self.ts.log('setting number of acquired points to ', self.query(':HORIZONTAL:ACQLENGTH?') + '...')
        self.cmd('HORizontal:DELay:MODe OFF')
        # self.ts.log('setting sampling rate to maximum...')

        max_sample = self.query('ACQUIRE:MAXSAMPLERATE?')
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

    def query(self, cmd_str):
        try:
            resp = ''
            if self.params.get('comm') == 'VISA':
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
        times = None
        for i in range(1, 4):  # pull data from each channel
            if self.chan_types.get(i) != 'None':
                if self.chan_types.get(i) == 'Switch_Current':
                    times, wfm_sw_i = self.bitstream_to_analog(channel=i)
                if self.chan_types.get(i) == 'Switch_Voltage':
                    times, wfm_sw_v = self.bitstream_to_analog(channel=i)
                if self.chan_types.get(i) == 'Bus_Voltage':
                    times, wfm_bus_v = self.bitstream_to_analog(channel=i)

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
            for chan in range(0, 3):
                if self.channel_types[chan] != 'None':
                    ds.points.append(self.channel_types[chan])
                    if self.chan_types.get(chan+1) == 'Switch_Current':
                        ds.data.append(wfm_sw_i)
                    if self.chan_types.get(chan+1) == 'Switch_Voltage':
                        ds.data.append(wfm_sw_v)
                    if self.chan_types.get(chan+1) == 'Bus_Voltage':
                        ds.data.append(wfm_bus_v)
            ds.to_csv(self.ts.result_file_path(wave_filename))
            self.ts.result_file(wave_filename)

        v_off_1 = None
        i_off_1 = None
        v_off_2 = None
        i_off_2 = None
        if wfm_sw_i is not None and wfm_sw_v is not None:
            switch_loss_energy, v_off_1, i_off_1 = self.calc_switch_loss(time_vect=times, current=wfm_sw_i,
                                                                         voltage=wfm_sw_v)
        else:
            switch_loss_energy = None

        # TODO add 2nd switch loss
        if wfm_sw_i_2 is not None and wfm_sw_v_2 is not None:
            switch_loss_energy_2, v_off_2, i_off_2 = self.calc_switch_loss(time_vect=times, current=wfm_sw_i,
                                                                           voltage=wfm_sw_v)
        else:
            switch_loss_energy_2 = None

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
                   'DCBUS_RIPPLE': None,
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
        else:
            print('unknown channel')
        self.ts.log_debug('Trigger Channel = %s' % self.trig_chan)
        self.ts.log_debug('Trigger Level = %s' % self.trig_level)
        self.ts.log_debug('Trigger Slope = %s' % self.trig_slope)

        self.cmd('TRIGger:A:EDGE:SOUrce ' + chan)
        self.cmd('TRIGger:A:LEVel ' + str(self.trig_level))
        self.cmd('TRIGger:A:EDGE:SLOpe ' + self.trig_slope)
        pass

    def calc_switch_loss(self, time_vect=None, current=None, voltage=None):
        """
        Calculate total dissipated energy (J/s)

         param: time_vect - time vector list
         param: current - current list
         param: voltage - voltage list

        """

        # determine time step
        dT = round(time_vect[-1] - time_vect[-2], 11)
        # self.ts.log('dT = ', dT)
        for i in range(1, len(time_vect)):
            temp = round(time_vect[i] - time_vect[i-1], 11)
            if temp != dT:
                self.ts.log_warning('Uneven time step!')
                self.ts.log_warning(temp, dT)

        # need to determine I_offset and V_offset automatically
        print('voltage offset')
        volt_offset = self.get_probe_offset(voltage)
        print(volt_offset)
        print('current offset')
        curr_offset = self.get_probe_offset(current)
        print(curr_offset)
        self.ts.log_debug('Voltage Offset = %s' % volt_offset)
        self.ts.log_debug('Current Offset = %s' % curr_offset)

        # self.ts.log('Voltage offset = %s' % volt_offset)
        # self.ts.log('Current offset = %s' % curr_offset)
        cumEnergy = [0]
        power = []
        energy = []

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
        for i in range(0, len(current)):
            power.append(abs(current[i] * voltage[i]))
            energy.append(power[i] * dT)
            cumEnergy.append(energy[i] + cumEnergy[-1])

        # (fig, ax) = plt.subplots(1, 1)
        # # ax.plot(time, cumEnergy[1:], 'k')
        # ax.plot(time, voltage, 'k')
        # # self.ts.log(curr_gram[0], volt_gram[0])
        # # ax.plot(curr_gram[1][1:], curr_gram[0], 'k')
        # # ax.plot(volt_gram[1][1:], volt_gram[0], 'r')
        #
        # # plt.hist(voltage, bins=np.arange(0, max(voltage), max(voltage)/1000))
        # # plt.hist(current, bins=np.arange(0, max(current), max(current)/1000))
        # # self.ts.log(gram[0], np.where(gram[0] == max(gram[0])), gram[1][16])
        # ax.plot()
        # axes = plt.gca()
        # fig.show()

        # plt.title('Cumulative Energy Loss at Different Power Factors')
        # plt.xlabel('time (s)')
        # plt.ylabel('Energy Loss (J)')

        # plt.show()

        return cumEnergy[-1]/time_vect[-1], volt_offset, curr_offset  # Total dissipated energy (J/s)

    def get_probe_offset(self, data):
        """
        Determine probe offset using histogram
        """

        sor = sort(data)
        hgram = histogram(data, bins=np.arange(sor[0], sor[-1], float(sor[-1]-sor[0]) / 100.))
        loc = np.where(hgram[0] == max(hgram[0][0:int(round(len(hgram[0])/2))]))
        print((hgram[0], int(round(len(hgram[0])/2)), len(hgram[0])))
        print(('max bin =', hgram[1][int(round(len(hgram[0])/2))]))
        data_offset = hgram[1][loc][0]
        return data_offset

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
            elif trig_state == 'SAVE':
                if self.ts is not None:
                    self.ts.log('Scope is in save mode and is not acquiring data...')
                else:
                    print('Scope is in save mode and is not acquiring data...')
                self.cmd('FPANEL:PRESS RUnstop')
            elif trig_state == 'TRIGGER':
                if self.ts is not None:
                    self.ts.log('Scope triggered and is acquiring the post trigger information...')
                else:
                    print('Scope triggered and is acquiring the post trigger information...')
                break
            else:
                if self.ts is not None:
                    self.ts.log('unknown trigger state...')
                else:
                    print('unknown trigger state...')

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

        # preamble = self.query('WFMOutpre?')
        # self.ts.log('Preamble')
        # preamble = preamble.split(';')

        # self.ts.log(preamble)
        # preamble = self.query('WFMInpre?')
        # preamble = preamble.split(';')
        # self.ts.log(preamble)
        # for i in range(0, len(preamble)):
        #     self.ts.log(i, preamble[i])

        # data_width = float(preamble[0])
        # bits_per_waveform = float(preamble[1])
        # encoding = preamble[2]
        # binary_format = preamble[3]
        # first_byte = preamble[4]
        # wfid = preamble[5]
        # source = preamble[5].split(',')[0].split('\"')[1]
        # coupling = preamble[5].split(',')[1]
        # vert_scale = preamble[5].split(',')[2]
        # horiz_scale = preamble[5].split(',')[3]
        # record_length = float(preamble[5].split(',')[4].split(' ')[1])
        # acq_mode = preamble[5].split(',')[5]

        # self.ts.log ('')
        # self.ts.log('Getting data for ' + source + '...')

        # number_datapoints = float(preamble[6])
        # point_format = preamble[7]
        # point_order = preamble[8]
        # x_unit = preamble[9]

        x_incr = float(self.query('WFMOutpre:XINcr?').split('\n')[0])
        # self.ts.log('x_incr = ', self.query('WFMOutpre:XINcr?'))
        # x_zero = float(self.query('WFMOutpre:XZEro?').split('\n')[0])
        # self.ts.log('x_zero = ', self.query('WFMOutpre:XZEro?'))
        # pt_off = float(preamble[12])
        # y_unit = preamble[13]
        y_mu = float(self.query('WFMOutpre:YMUlt?').split('\n')[0])
        # self.ts.log('y_mult = ', self.query('WFMOutpre:YMUlt?'))
        y_offset = float(self.query('WFMOutpre:YOFf?').split('\n')[0])
        # self.ts.log('y_offset = ', self.query('WFMOutpre:YOFf?'))
        y_zero = float(self.query('WFMOutpre:YZEro?').split('\n')[0])
        # domain_type = preamble[17]
        # wafmtype = preamble[18]
        # center_freq = float(preamble[19])
        # span = float(preamble[20])
        # ref_level = float(preamble[21])

        total_length = float(self.query('HORizontal:RECOrdlength?').split('\n')[0])
        """
        Get the conversion parameters to move bit stream into voltage/current values
        """
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
            record = self.query('CURVe?')
            opc = self.query('*OPC?')
            while opc != '1\n':
                # self.ts.log(opc)
                if self.ts is not None:
                    self.ts.sleep(1)
                else:
                    time.sleep(1)
                # self.ts.log('waiting for previous command to finish...')
            # self.ts.log(data)
            data = data + record.split(',')
            if self.ts is not None:
                self.ts.sleep(2)
            else:
                time.sleep(2)

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


if __name__ == "__main__":

    import time
    import ftplib
    import visa

    params = {'comm': 'VISA'}
    ip_addr = '10.1.2.87'
    params['channels'] = [None, None, None, None, None]
    params['visa_id'] = "TCPIP::%s::INSTR" % ip_addr
    params['vertical_scale'] = [250, 250, 10, 5]  # V/div
    params['horiz_scale'] = 2e-3  # time scale s/div...full scale = 10 * scale
    params['sample_rate'] = 2.5e9  # sets rate of sampling...total time = length / rate
    params['length'] = 1000  # sets record length...valid values are 1k, 10k, 100k, 1M, 5M
    # params['channel_types'] = ['Switch_Current', 'Switch_Voltage', 'None', 'None']
    params['channel_types'] = ['Switch_Voltage', 'Bus_Voltage', 'Switch_Current', 'None']
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





