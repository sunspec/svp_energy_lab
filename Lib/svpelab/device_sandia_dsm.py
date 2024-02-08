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
from . import waveform
from . import dataset

data_points = [
    'TIME',
    'DC_V',
    'DC_I',
    'AC_VRMS_1',
    'AC_IRMS_1',
    'DC_P',
    'AC_S_1',
    'AC_P_1',
    'AC_Q_1',
    'AC_FREQ_1',
    'AC_PF_1',
    'TRIG',
    'TRIG_GRID'
]

# Data channels for Node 1
dsm_points_1 = [
    'time',
    'dc_voltage_1',
    'dc_current_1',
    'ac_voltage_1',
    'ac_current_1',
    'dc1_watts',
    'ac1_va',
    'ac1_watts',
    'ac1_vars',
    'ac1_freq',
    'ac_1_pf',
    'pythontrigger',
    'ametek_trigger'
]

# Data channels for Node 2
dsm_points_2 = [
    'time',
    'dc_voltage_2',
    'dc_current_2',
    'ac_voltage_2',
    'ac_current_2',
    'dc2_watts',
    'ac2_va',
    'ac2_watts',
    'ac2_vars',
    'ac1_freq',
    'ac_2_pf',
    'pythontrigger',
    'ametek_trigger'
]

# Data channels for Node 3
dsm_points_3 = [
    'time',
    'dc_voltage_3',
    'dc_current_3',
    'ac_voltage_3',
    'ac_current_3',
    'dc3_watts',
    'ac3_va',
    'ac3_watts',
    'ac3_vars',
    'ac1_freq',
    'ac_3_pf',
    'pythontrigger',
    'ametek_trigger'
]

# Data channels for Node 4
dsm_points_4 = [
    'time',
    'dc_voltage_4',
    'dc_current_4',
    'ac_voltage_4',
    'ac_current_4',
    'dc4_watts',
    'ac4_va',
    'ac4_watts',
    'ac4_vars',
    'ac1_freq',
    'ac_4_pf',
    'pythontrigger',
    'ametek_trigger'
]

# Data channels for Node 5
dsm_points_5 = [
    'time',
    'dc_voltage_5',
    'dc_current_5',
    'ac_voltage_5',
    'ac_current_5',
    'dc5_watts',
    'ac5_va',
    'ac5_watts',
    'ac5_vars',
    'ac1_freq',
    'ac_5_pf',
    'pythontrigger',
    'ametek_trigger'
]

# Data channels for Node 6
dsm_points_6 = [
    'time',
    'dc_voltage_6',
    'dc_current_6',
    'ac_voltage_6',
    'ac_current_6',
    'dc6_watts',
    'ac6_va',
    'ac6_watts',
    'ac6_vars',
    'ac1_freq',
    'ac_6_pf',
    'pythontrigger',
    'ametek_trigger'
]

# Data channels for Node 7
dsm_points_7 = [
    'time',
    'dc_voltage_7',
    'dc_current_7',
    'ac_voltage_7',
    'ac_current_7',
    'dc7_watts',
    'ac7_va',
    'ac7_watts',
    'ac7_vars',
    'ac1_freq',
    'ac_7_pf',
    'pythontrigger',
    'ametek_trigger'
]

# Data channels for Node 8
dsm_points_8 = [
    'time',
    'dc_voltage_8',
    'dc_current_8',
    'ac_voltage_8',
    'ac_current_8',
    'dc8_watts',
    'ac8_va',
    'ac8_watts',
    'ac8_vars',
    'ac1_freq',
    'ac_8_pf',
    'pythontrigger',
    'ametek_trigger'
]

# Data channels for Node 9
dsm_points_9 = [
    'time',
    'dc_voltage_9',
    'dc_current_9',
    'ac_voltage_9',
    'ac_current_9',
    'dc9_watts',
    'ac9_va',
    'ac9_watts',
    'ac9_vars',
    'ac1_freq',
    'ac_9_pf',
    'pythontrigger',
    'ametek_trigger'
]

# Data channels for Node 10
dsm_points_10 = [
    'time',
    'dc_voltage_10',
    'dc_current_10',
    'ac_voltage_10',
    'ac_current_10',
    'dc10_watts',
    'ac10_va',
    'ac10_watts',
    'ac10_vars',
    'ac6_freq',
    'ac_10_pf',
    'pythontrigger',
    'ametek_trigger'
]

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

PATH = 'C:\\python_dsm\\'
POINTS_FILE = 'channels.txt'
DATA_FILE = 'data.txt'
TRIGGER_FILE = 'trigger.txt'
WFM_TRIGGER_FILE = 'waveform trigger.txt'

event_map = {'Rising_Edge': 'Rising Edge', 'Falling_Edge': 'Falling Edge'}

class DeviceError(Exception):
    pass


class Device(object):

    def extract_points(self, points_str, op):
        x = list(map(op, points_str[points_str.rfind('[')+1:points_str.rfind(']')].strip().split(',')))
        return x

    def __init__(self, params):
        self.params = params
        self.dsm_method = self.params.get('dsm_method')
        self.dsm_id = self.params.get('dsm_id')
        self.comp = self.params.get('comp')
        self.file_path = self.params.get('file_path')
        self.sample_interval = self.params.get('sample_interval')
        self.data_file = os.path.join(self.file_path, DATA_FILE)
        self.points_file = os.path.join(self.file_path, POINTS_FILE)
        self.wfm_trigger_file = os.path.join(self.file_path, WFM_TRIGGER_FILE)

        self.data_points = list(data_points)
        self.points_map = dsm_points_map.get(str(self.dsm_id))
        self.points = None
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

        self.ts = self.params.get('ts')

        try:
            if self.points_file is None:
                raise Exception('Point file not specified')
            if self.dsm_method == 'Sandia LabView DSM UDP':
                import socket
                UDP_IP = "0.0.0.0"
                UDP_PORT = 6495
                sock = socket.socket(socket.AF_INET,  # Internet
                                     socket.SOCK_DGRAM)  # UDP
                sock.bind((UDP_IP, UDP_PORT))
                while True:
                    data, addr = sock.recvfrom(4096)
                    if self.ts is not None:
                        self.ts.log("received message: %s" % data)
                    else:
                        print(("received message: %s" % data))
            else:
                f = open(self.points_file)
                channels = f.read()
                f.close()

                self.points = self.extract_points(channels, str)
                # if self.ts is not None:
                #     self.ts.log("self.points: %s" % self.points)
                # else:
                #     print(self.points)

                for p in self.points_map:
                    try:
                        index = self.points.index(p)
                    except ValueError:
                        index = -1
                    self.point_indexes.append(index)
        except Exception as e:
            raise DeviceError(traceback.format_exc())
    '''
        try:
            self.x = map(op, points_str[points_str.rfind('[')+1:points_str.rfind(']')].strip().split(','))
        except Exception, e:
            self.x = None

    def extract_points(self, points_str, op):
        try:
            x = map(op, points_str[points_str.rfind('[')+1:points_str.rfind(']')].strip().split(','))
            self.x = x  # repeat last data point.
        except Exception, e:
            x = self.x
        return x
    '''

    def info(self):
        return 'Sandia DSM - 1.2'

    def open(self):
        pass

    def close(self):
        pass

    def data_capture(self, enable=True):
        pass

    def data_read(self):
        retries = 10
        rec = []
        data = None
        try:
            while data is None and retries > 0:
                try:
                    f = open(self.data_file)
                    data = f.read()
                    f.close()
                except Exception as e:
                    retries -= 1

            if data is not None:
                points = self.extract_points(data, float)
                print(list(zip(self.points, points)))
                if points is not None:
                    if len(points) == len(self.points):
                        for index in self.point_indexes:
                            if index >= 0:
                                p = points[index]
                            else:
                                p = float('NaN')
                            rec.append(p)
                    else:
                        raise Exception('Error reading points: point count mismatch %d %d' % (len(points),
                                                                                              len(self.points)))
        except Exception as e:
            raise Exception(traceback.format_exc())

        return rec

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
        self.wfm_dsm_trigger_channel = '%s_%s' % (wfm_dsm_channels.get(self.wfm_trigger_channel), self.dsm_id)
        self.wfm_dsm_channels = []

        for c in self.wfm_channels:
            dsm_chan = wfm_dsm_channels[c]
            if dsm_chan is not None:
                self.wfm_dsm_channels.append('%s_%s' % (dsm_chan, self.dsm_id))
        print(('Channels to record: %s' % str(self.wfm_channels)))


    def waveform_capture(self, enable=True, sleep=None):
        """
        Enable/disable waveform capture.
        """
        if enable:
            if sleep is None:
                raise DeviceError('Must supply a sleep function on waveform capture enable')
            self.wfm_capture_name = None
            # remove old trigger file results
            files = glob.glob(os.path.join(self.file_path, '* %s' % WFM_TRIGGER_FILE))
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
                self.wfm_timeout, event_map[self.wfm_trigger_cond], self.wfm_dsm_trigger_channel)
            for c in self.wfm_dsm_channels:
                config_str += '%s\n' % c

            # create capture file
            f = open(self.wfm_trigger_file, 'w')
            f.write(config_str)
            f.close()

            wait_time = self.wfm_timeout
            for i in range(int(wait_time) + 1):
                print(('looking for %s' % self.wfm_trigger_file))
                if not os.path.exists(self.wfm_trigger_file):
                    break
                if i >= wait_time:
                    raise DeviceError('Waveform start capture timeout')
                sleep(1)

            filename = os.path.join(self.file_path, '* %s' % WFM_TRIGGER_FILE)
            print(('looking for %s' % filename))
            files = glob.glob(filename)
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

    def waveform_capture_dataset(self):
        ds = dataset.Dataset()
        f = open(self.wfm_capture_name_path, 'r')
        ids = f.readline().strip().split('\t')
        print((str(ids)))
        if ids[0] != 'Time':
            raise DeviceError('Unexpected time point name in waveform capture: %s' % ids[0])
        ds.points.append('TIME')
        count = len(ids)
        points = []
        point_count = 1
        points.append([])  # for time
        for i in range(1, count):
            if ids[i]:
                id = ids[i].strip().lower()
                i = id.rfind('_')
                if id[i+1:] == str(self.dsm_id):
                    id = id[:i]
                label = wfm_points_label.get(id)
                if label is None:
                    raise DeviceError('Unknown DSM point name in waveform capture: %s', id)
                ds.points.append(label)
                points.append([])
                point_count += 1

        line = 0
        for data in f:
            line += 1
            values = data.strip().split('\t')
            if len(values) != point_count:
                raise DeviceError('Point data error in waveform capture line %s' % (line))
            for i in range(point_count):
                points[i].append(float(values[i]))

        for i in range(point_count):
            ds.data.append(points[i])

        return ds

def send(data, port=50003, addr='127.0.0.1'):
        """send(data[, port[, addr]]) - multicasts a UDP datagram."""
        # Create the socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Make the socket multicast-aware, and set TTL.
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 20) # Change TTL (=20) to suit
        # Send the data
        s.sendto(data, (addr, port))

def recv(port=50003, addr="127.0.0.1", buf_size=1024):
        """recv([port[, addr[,buf_size]]]) - waits for a datagram and returns the data."""

        # Create the socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set some options to make it multicast-friendly
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
                pass # Some systems don't support SO_REUSEPORT
        s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, 20)
        s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)

        # Bind to the port
        s.bind(('', port))

        # Set some more multicast options
        intf = socket.gethostbyname(socket.gethostname())
        s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(intf))
        s.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(addr) + socket.inet_aton(intf))

        # Receive the data, then unregister multicast receive membership, then close the port
        data, sender_addr = s.recvfrom(buf_size)
        s.setsockopt(socket.SOL_IP, socket.IP_DROP_MEMBERSHIP, socket.inet_aton(addr) + socket.inet_aton('0.0.0.0'))
        s.close()
        return data

if __name__ == "__main__":

    from netifaces import interfaces, ifaddresses, AF_INET
    import struct
    import socket
    import time
    import sys

    print((socket.gethostbyname(socket.gethostname())))

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the port
    server_address = ('239.100.100.100', 51051)
    print('starting up on %s port %s' % server_address)
    # sock.bind(server_address)
    while True:
        print('\nwaiting to receive message', file=sys.stderr)
        data, address = sock.recvfrom(4096)

        print('received %s bytes from %s' % (len(data), address))
        print(data)

    '''
    ip_addr = '10.1.2.78'
    for interface in interfaces():
        for link in ifaddresses(interface)[AF_INET]:
            local_addr = link['addr'].split('.', 3)
            targ_addr = ip_addr.split('.', 3)
            if '%s.%s.%s' % (local_addr[0], local_addr[1], local_addr[2]) == \
                            '%s.%s.%s' % (targ_addr[0], targ_addr[1], targ_addr[2]):
                iface_for_comms = interface
            print('interface: %s, IP: %s' % (interface, link['addr']))
    print('Interface for comms: %s' % iface_for_comms)
    '''

    UDP_IP = '10.1.2.78'
    IP = '10.1.2.218'
    UDP_PORT = 51051
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((UDP_IP, UDP_PORT))
    # mreq = struct.pack("=4sl", socket.inet_aton(UDP_IP), socket.INADDR_ANY)
    # sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    for i in range(10):
        data, addr = sock.recvfrom(4096)
        print("received message:", data)
        time.sleep(0.1)

    '''
    import pyshark
    capture = pyshark.LiveCapture()
    capture.sniff(timeout=50)
    for packet in capture.sniff_continuously(packet_count=5):
        print('Just arrived:', packet)
        capture = pyshark.LiveCapture(capture_filter='udp')
        capture.apply_on_packets(packet_captured)
        packet['ip'].dst
        packet.ip.src

    params = {}
    params['dsm_method'] = 'Sandia LabView DSM'
    params['file_path'] = 'c:\\users\\bob\\pycharmprojects\\loadsim\\files\\python_dsm'
    params['dsm_id'] = 10
    params['sample_interval'] = 1000

    d = Device(params)
    print d.data_points
    print d.data_read()

    wfm = {}
    wfm['sample_rate'] = 6000
    wfm['pre_trigger'] = 5
    wfm['post_trigger'] = 10
    wfm['trigger_level'] = 1
    wfm['trigger_cond'] = 'Rising Edge'
    wfm['trigger_channel'] = 'AC_V_1'
    wfm['timeout'] = 10
    wfm['channels'] = ['AC_V_1', 'AC_I_1']

    d.waveform_config(params=wfm)
    d.waveform_capture(sleep=time.sleep)
    ds = d.waveform_capture_dataset()
    print ds.points
    ds.to_csv('c:\\users\\bob\\pycharmprojects\\loadsim\\files\\python_dsm\\wave.csv')
    '''






