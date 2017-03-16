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

import time
import traceback

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
        self.data_file = self.params.get('data_file')
        self.points_file = self.params.get('points_file')

        self.points_map = dsm_points_map.get(str(self.dsm_id))
        self.points = []
        self.point_indexes = []

        self.rec = {}
        self.recs = []

        self.read_error_count = 0
        self.read_last_error = ''

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

if __name__ == "__main__":

    pass


