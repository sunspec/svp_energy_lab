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
import time
import traceback
import glob
import waveform

data_points = [
    'time',
    'dc_voltage',
    'dc_current',
    'ac_voltage',
    'ac_current',
    'dc_watts',
    'ac_va',
    'ac_watts',
    'ac_vars',
    'ac_freq',
    'ac_pf',
    'trigger',
    'ametek_trigger'
]

data_points_label = {
    'time': 'Test Time (s)',
    'dc_voltage': 'DC Voltage (V)',
    'dc_current': 'DC Current (A)',
    'ac_voltage': 'AC Voltage (V)',
    'ac_current': 'AC Current (A)',
    'dc_watts': 'DC Active Power (W)',
    'ac_va': 'AC Apparent Power (VA)',
    'ac_watts': 'AC Active Power (W)',
    'ac_vars': 'AC Reactive Power (Var)',
    'ac_freq': 'Frequency (Hz)',
    'ac_pf': 'AC Power Factor',
    'trigger': 'Communication Trigger',
    'ametek_trigger': 'Grid Transient Trigger'
}

# Data channels for Node 1
dsm_points_1 = {
    'time': 'time',
    'dc_voltage': 'dc_voltage_1',
    'dc_current': 'dc_current_1',
    'ac_voltage': 'ac_voltage_1',
    'ac_current': 'ac_current_1',
    'dc_watts': 'dc1_watts',
    'ac_va': 'ac1_va',
    'ac_watts': 'ac1_watts',
    'ac_vars': 'ac1_vars',
    'ac_freq': 'ac1_freq',
    'ac_pf': 'ac_1_pf',
    'trigger': 'pythontrigger',
    'ametek_trigger': 'ametek_trigger'
}

# Data channels for Node 2
dsm_points_2 = {
    'time': 'time',
    'dc_voltage': 'dc_voltage_2',
    'dc_current': 'dc_current_2',
    'ac_voltage': 'ac_voltage_2',
    'ac_current': 'ac_current_2',
    'dc_watts': 'dc2_watts',
    'ac_va': 'ac2_va',
    'ac_watts': 'ac2_watts',
    'ac_vars': 'ac2_vars',
    'ac_freq': 'ac1_freq',
    'ac_pf': 'ac_2_pf',
    'trigger': 'pythontrigger',
    'ametek_trigger': 'ametek_trigger'
}

# Data channels for Node 3
dsm_points_3 = {
    'time': 'time',
    'dc_voltage': 'dc_voltage_3',
    'dc_current': 'dc_current_3',
    'ac_voltage': 'ac_voltage_3',
    'ac_current': 'ac_current_3',
    'dc_watts': 'dc3_watts',
    'ac_va': 'ac3_va',
    'ac_watts': 'ac3_watts',
    'ac_vars': 'ac3_vars',
    'ac_freq': 'ac1_freq',
    'ac_pf': 'ac_3_pf',
    'trigger': 'pythontrigger',
    'ametek_trigger': 'ametek_trigger'
}

# Data channels for Node 4
dsm_points_4 = {
    'time': 'time',
    'dc_voltage': 'dc_voltage_4',
    'dc_current': 'dc_current_4',
    'ac_voltage': 'ac_voltage_4',
    'ac_current': 'ac_current_4',
    'dc_watts': 'dc4_watts',
    'ac_va': 'ac4_va',
    'ac_watts': 'ac4_watts',
    'ac_vars': 'ac4_vars',
    'ac_freq': 'ac1_freq',
    'ac_pf': 'ac_4_pf',
    'trigger': 'pythontrigger',
    'ametek_trigger': 'ametek_trigger'
}

# Data channels for Node 5
dsm_points_5 = {
    'time': 'time',
    'dc_voltage': 'dc_voltage_5',
    'dc_current': 'dc_current_5',
    'ac_voltage': 'ac_voltage_5',
    'ac_current': 'ac_current_5',
    'dc_watts': 'dc5_watts',
    'ac_va': 'ac5_va',
    'ac_watts': 'ac5_watts',
    'ac_vars': 'ac5_vars',
    'ac_freq': 'ac5_freq',
    'ac_pf': 'ac_5_pf',
    'trigger': 'pythontrigger',
    'ametek_trigger': 'ametek_trigger'
}

# Data channels for Node 6
dsm_points_6 = {
    'time': 'time',
    'dc_voltage': 'dc_voltage_6',
    'dc_current': 'dc_current_6',
    'ac_voltage': 'ac_voltage_6',
    'ac_current': 'ac_current_6',
    'dc_watts': 'dc6_watts',
    'ac_va': 'ac6_va',
    'ac_watts': 'ac6_watts',
    'ac_vars': 'ac6_vars',
    'ac_freq': 'ac6_freq',
    'ac_pf': 'ac_6_pf',
    'trigger': 'pythontrigger',
    'ametek_trigger': 'ametek_trigger'
}

# Data channels for Node 7
dsm_points_7 = {
    'time': 'time',
    'dc_voltage': 'dc_voltage_7',
    'dc_current': 'dc_current_7',
    'ac_voltage': 'ac_voltage_7',
    'ac_current': 'ac_current_7',
    'dc_watts': 'dc7_watts',
    'ac_va': 'ac7_va',
    'ac_watts': 'ac7_watts',
    'ac_vars': 'ac7_vars',
    'ac_freq': 'ac_6_freq',
    'ac_pf': 'ac_7_pf',
    'trigger': 'pythontrigger',
    'ametek_trigger': 'ametek_trigger'
}

# Data channels for Node 8
dsm_points_8 = {
    'time': 'time',
    'dc_voltage': 'dc_voltage_8',
    'dc_current': 'dc_current_8',
    'ac_voltage': 'ac_voltage_8',
    'ac_current': 'ac_current_8',
    'dc_watts': 'dc8_watts',
    'ac_va': 'ac8_va',
    'ac_watts': 'ac8_watts',
    'ac_vars': 'ac8_vars',
    'ac_freq': 'ac6_freq',
    'ac_pf': 'ac_8_pf',
    'trigger': 'pythontrigger',
    'ametek_trigger': 'ametek_trigger'
}

# Data channels for Node 9
dsm_points_9 = {
    'time': 'time',
    'dc_voltage': 'dc_voltage_9',
    'dc_current': 'dc_current_9',
    'ac_voltage': 'ac_voltage_9',
    'ac_current': 'ac_current_9',
    'dc_watts': 'dc9_watts',
    'ac_va': 'ac9_va',
    'ac_watts': 'ac9_watts',
    'ac_vars': 'ac9_vars',
    'ac_freq': 'ac6_freq',
    'ac_pf': 'ac_9_pf',
    'trigger': 'pythontrigger',
    'ametek_trigger': 'ametek_trigger'
}

# Data channels for Node 10
dsm_points_10 = {
    'time': 'time',
    'dc_voltage': 'dc_voltage_10',
    'dc_current': 'dc_current_10',
    'ac_voltage': 'ac_voltage_10',
    'ac_current': 'ac_current_10',
    'dc_watts': 'dc10_watts',
    'ac_va': 'ac10_va',
    'ac_watts': 'ac10_watts',
    'ac_vars': 'ac10_vars',
    'ac_freq': 'ac6_freq',
    'ac_pf': 'ac_10_pf',
    'trigger': 'pythontrigger',
    'ametek_trigger': 'ametek_trigger'
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
    'Time': 'Test',
    'dc_voltage': 'DC_V',
    'dc_current': 'DC_I',
    'ac_voltage': 'AC_V_1',
    'ac_current': 'AC_I_1',
    'ac_freq': 'Freq',
    'ametek_trigger': 'Ext'
}

wfm_channels = ['AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'Ext']

wfm_dsm_channels = {'AC_V_1': 'AC_Voltage_10',
                    'AC_V_2': None,
                    'AC_V_3': None,
                    'AC_I_1': 'AC_Current_10',
                    'AC_I_2': None,
                    'AC_I_3': None,
                    'Ext': 'Ametek_Trigger'}


class DeviceError(Exception):
    pass


class Device(object):

    def extract_points(self, points_str):
        x = points_str.replace(' ', '_').replace('][', ' ').strip('[]').split()
        for p in x:
            if p.find(',') != -1:
                return p.split(',')

    def __init__(self, params):
        self.params = params
        self.dsm_method = self.params.get('dsm_method')
        self.dsm_id = self.params.get('dsm_id')
        self.comp = self.params.get('comp')
        self.file_path = self.params.get('file_path')
        self.data_file = self.params.get('data_file')
        self.points_file = self.params.get('points_file')
        self.wfm_trigger_file = 'waveform trigger.txt'

        self.points_map = dsm_points_map.get(str(self.dsm_id))
        self.points = []
        self.point_indexes = []

        self.rec = {}
        self.recs = []

        self.read_error_count = 0
        self.read_last_error = ''

        # waveform settings
        self.wfm_sample_rate = None
        self.wfm_pre_trigger = None
        self.wfm_post_trigger = None
        self.wfm_trigger_level = None
        self.wfm_trigger_cond = None
        self.wfm_trigger_channel = None
        self.wfm_timeout = None
        self.wfm_channels = None
        self.wfm_dsm_trigger_channel = None
        self.wfm_dsm_channels = None
        self.wfm_capture_name = None
        self.wfm_capture_name_path = None

        try:
            if self.points_file is None:
                raise Exception('Point file not specified')
            if self.dsm_method != 'Sandia LabView DSM':
                raise Exception('Method not supported: %s' % (self.dsm_method))

            f = open(self.points_file)
            channels = f.read()
            f.close()

            self.points = self.extract_points(channels)

            for p in data_points:
                point_name = self.points_map.get(p)
                try:
                    index = self.points.index(point_name)
                except ValueError:
                    index = -1
                self.point_indexes.append(index)
        except Exception, e:
            raise (traceback.format_exc())

    def info(self):
        return 'Sandia DSM - 1.0'

    def open(self):
        pass

    def close(self):
        pass

    def data_read(self):
        '''
        datarec = {'time': time.time(),
                   'ac_1': (220.1, 10.1, 2100.1, 2200, .011, .991, 60.1),
                   'ac_2': (220.2, 10.2, 2100.2, 2200, .012, .992, 60.2),
                   'ac_3': (220.3, 10.3, 2100.3, 2200, .013, .993, 60.3),
                   'dc': (440, 5, 2200)}
        return datarec
        '''
        rec = {}
        try:
            try:
                f = open(self.data_file)
                data = f.read()
                f.close()
            except Exception, e:
                data = None

            if data is not None:
                points = self.extract_points(data)
                if points is not None:
                    if len(points) == len(self.points):
                        for i in xrange(len(data_points)):
                            index = self.point_indexes[i]
                            if index >= 0:
                                rec[data_points[i]] = points[index]
                            else:
                                rec[data_points[i]] = None
                    else:
                        raise Exception('Error reading points: point count mismatch %d %d' % (len(points),
                                                                                              len(self.points)))

        except Exception, e:
            raise Exception(traceback.format_exc())

        datarec = {'time': time.time(),
                   'ac_1': (rec['ac_voltage'], rec['ac_current'], rec['ac_watts'], rec['ac_va'],
                            rec['ac_vars'], rec['ac_pf'], rec['ac_freq']),
                   'dc': (rec['dc_voltage'], rec['dc_current'], rec['dc_watts'])}

        return datarec

    def waveform_config(self, params):
        self.wfm_sample_rate = params.get('sample_rate')
        self.wfm_pre_trigger = params.get('pre_trigger')
        self.wfm_post_trigger = params.get('post_trigger')
        self.wfm_trigger_level = params.get('trigger_level')
        self.wfm_trigger_cond = params.get('trigger_cond')
        self.wfm_trigger_channel = params.get('trigger_channel')
        self.wfm_timeout = params.get('timeout')
        self.wfm_channels = params.get('channels')
        self.wfm_dsm_trigger_channel = wfm_dsm_channels.get(self.wfm_trigger_channel)
        self.wfm_dsm_channels = []

        for c in self.wfm_channels:
            dsm_chan = wfm_dsm_channels[c]
            if dsm_chan is not None:
                self.wfm_dsm_channels.append(dsm_chan)
        self.params['ts'].log('Channels to record: %s' % str(self.wfm_channels))


    def waveform_capture(self, enable=True):
        """
        Enable/disable waveform capture.
        """
        if enable:
            self.wfm_capture_name = None
            # remove old trigger file results
            files = glob.glob(os.path.join(self.file_path, '* %s' % self.wfm_trigger_file))
            # self.params['ts'].log(str(self.params))
            # self.params['ts'].log(files)
            for f in files:
                os.remove(f)

            # if self.waveform_status() is True:
             #    raise DeviceError('Waveform capture already in progress')
            '''
            File format:
                sample rate
                pre-trigger time in seconds
                post-trigger time in seconds
                level
                window
                timeout in seconds
                condition ['Rising Edge', 'Falling Edge']
                trigger channel
                channel
                channel
                ...
            '''
            config_str = '%0.1fe3\n%f\n%f\n%f\n10e-3\n%d\n%s\n%s\n' % (
                self.wfm_sample_rate/1000, self.wfm_pre_trigger, self.wfm_post_trigger, self.wfm_trigger_level,
                self.wfm_timeout, self.wfm_trigger_cond, self.wfm_dsm_trigger_channel)
            for c in self.wfm_dsm_channels:
                config_str += '%s\n' % c

            # create capture file
            f = open(os.path.join(self.file_path, self.wfm_trigger_file), 'w')
            f.write(config_str)
            f.close()

            wait_time = 15
            for i in range(wait_time + 1):
                if not os.path.exists(os.path.join(self.file_path, self.wfm_trigger_file)):
                    break
                if i >= wait_time:
                    raise DeviceError('Waveform start capture timeout')
                time.sleep(1)

            files = glob.glob(os.path.join(self.file_path, '* %s' % self.wfm_trigger_file))
            if len(files) == 0:
                raise DeviceError('No waveform trigger result file')
            elif len(files) > 1:
                raise DeviceError('Unexpected multiple waveform trigger result files')
            self.wfm_capture_name = '%s.wfm' % (os.path.basename(files[0])[:19])
            self.wfm_capture_name_path = os.path.join(self.file_path, self.wfm_capture_name)
            # self.params['ts'].log(self.wfm_capture_name)

    def waveform_status(self):
        # mm-dd-yyyy hh_mm_ss waveform trigger.txt
        # mm-dd-yyyy hh_mm_ss.wfm
        # return INACTIVE, ACTIVE, COMPLETE
        stat = 'ACTIVE'
        if self.wfm_capture_name is not None:
            # self.params['ts'].log('Searching for %s' % self.wfm_capture_name_path)
            if os.path.exists(self.wfm_capture_name_path):
                size = os.path.getsize(self.wfm_capture_name_path)
                time.sleep(.1)
                if size == os.path.getsize(self.wfm_capture_name_path):
                    stat = 'COMPLETE'
        else:
            stat = 'INACTIVE'
        return stat

    def waveform_force_trigger(self):
        pass

    def waveform_load(self):
        wf = waveform.Waveform()
        f = open(self.wfm_capture_name_path, 'r')
        ids = f.readline().split('\t')
        if ids[0] != 'Time':
            raise DeviceError('Unexpected time channel name in waveform capture: %s' % ids[0])
        wf.channels.append('Time')
        chan_count = len(ids)
        chans = []
        chans.append([])  # for time
        for i in range(1, chan_count):
            wfm_chan_id = ids[i].strip().lower()
            chan_id = [chan_id for chan_id, dsm_chan_id in self.points_map.iteritems() if dsm_chan_id == wfm_chan_id]
            if chan_id is None:
                raise DeviceError('Unknown DSM channel name in waveform capture: %s', wfm_chan_id)
            chan_label = wfm_points_label[chan_id[0]]
            wf.channels.append(chan_label)
            chans.append([])

        line = 0
        for data in f:
            line += 1
            values = data.split('\t')
            if len(values) != chan_count:
                raise DeviceError('Channel data error in waveform capture line %s' % (line))
            for i in range(chan_count):
                chans[i].append(float(values[i]))

        for i in range(chan_count):
            wf.channel_data.append(chans[i])

        return wf


if __name__ == "__main__":

    pass


