'''
EtherCAT parser for SVP 

Initial implementation - jayatsandia - 12/13/2022
'''

import os
import time
import asyncio

try: 
    from . import network
except Exception as e:
    print('Cannot find network.py in svpelab')

try: 
    from scapy.all import *
    from scapy.contrib.ethercat import *
except Exception as e:
    print('Missing scapy. Install with "pip install scapy"')

try: 
    import pandas as pd
except Exception as e:
    print('Missing pyshark. Install with "pip install pandas"')

try: 
    from collections import Counter
except Exception as e:
    print('Missing collections. Install with "pip install collections"')

try: 
    import numpy as np
except Exception as e:
    print('Missing numpy. Install with "pip install numpy"')

# TEXT COLOR    CODE    TEXT STYLE  CODE    BACKGROUND COLOR    CODE
# Black         30      No effect   0               Black       40
# Red           31      Bold        1               Red         41
# Green         32      Underline   2               Green       42
# Yellow        33      Negative1   3               Yellow      43
# Blue          34      Negative2   5               Blue        44
# Purple        35                                  Purple      45
# Cyan          36                                  Cyan        46
# White         37                                  White       47
# e.g., 'green_on_black' = '\033[1;32;40m Text',

RESET = '\033[0m'
UNDERLINE = '\033[2m'
BOLD = '\033[1m'
RED = '\033[31m'
GREEN = '\033[32m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
GREEN_ON_BLACK = '\033[1;32;40m'

INBOUND_SRC = '02:80:2f:17:a7:79'
OUTBOUND_SRC = '00:80:2f:17:a7:79'


'''
Signal Description                                  Direction   ECAT Start      ECAT End Byte   Length  Type    Scale   Units   Bit
Controller has opened Safety Circuit when FALSE     Outbound    26              26              1       Bool                    7
Commanding gear oil cooler to run when TRUE         Outbound    26              26              1       Bool                    6
Commanding hydraulic pump to run when TRUE          Outbound    26              26              1       Bool                    4
HSS brake off when TRUE                             Outbound    26              26              1       Bool                    3
Pitch proportional valve active when TRUE           Outbound    26              26              1       Bool                    2
Commanding yaw counter-clockwise when TRUE          Outbound    26              26              1       Bool                    1
Commanding yaw clockwise when TRUE                  Outbound    26              26              1       Bool                    0
Commanding generator fan to run when TRUE           Outbound    27              27              1       Bool                    1
Commanding fine filter to run when TRUE             Outbound    27              27              1       Bool                    0
Pitch velocity command voltage                      Outbound    30              31              2       INT     10.72   Volts
Heartbeat to VFD                                    Outbound    122             122             1       Bool                    3
Reset controller watchdog                           Outbound    122             122             1       Bool                    2
Heartbeat to controller watchdog                    Outbound    122             122             1       Bool                    1
Remote switching of main contactor                  Outbound    122             122             1       Bool                    0
Command the VFD to change states                    Outbound    154             155             2       UINT    10.72   Volts
Command VFD to produce this amount of torque        Outbound    158             159             2       INT     10.72   lb-ft?
Command VFD to produce this amount of Q             Outbound    162             163             2       INT     10.72   Var?
'''

# Name, ecat_start, ecat_stop, length, type, scaling/bit, offset (INT/UINT)
OUTBOUND = [
['Controller has opened Safety Circuit when FALSE', 26, 26, 1, 'Bool', 7],
['Commanding gear oil cooler to run when TRUE', 26, 26, 1, 'Bool', 6],
['Commanding hydraulic pump to run when TRUE', 26, 26, 1, 'Bool', 4],
['HSS brake off when TRUE', 26, 26, 1, 'Bool', 3],
['Pitch proportional valve active when TRUE', 26, 26, 1, 'Bool', 2],
['Commanding yaw counter-clockwise when TRUE', 26, 26, 1, 'Bool', 1],
['Commanding yaw clockwise when TRUE', 26, 26, 1, 'Bool', 0],
['Commanding generator fan to run when TRUE', 27, 27, 1, 'Bool', 1],
['Commanding fine filter to run when TRUE', 27, 27, 1, 'Bool', 0],
['Pitch velocity command voltage', 30, 31, 2, 'INT', 10.72, 0],
['Heartbeat to VFD', 122, 122, 1, 'Bool', 3],
['Reset controller watchdog', 122, 122, 1, 'Bool', 2],
['Heartbeat to controller watchdog', 122, 122, 1, 'Bool', 1],
['Remote switching of main contactor', 122, 122, 1, 'Bool', 0],
['Command the VFD to change states', 154, 155, 2, 'UINT', 10.72, 0],
['Command VFD to produce this amount of torque', 158, 159, 2, 'INT', 10.72, 0],
['Command VFD to produce this amount of Q', 162, 163, 2, 'INT', 10.72, 0],
]

'''
Signal Description                                  Direction   ECAT Start  ECAT End Byte   Length  Type    Scale   Units   Bit
Gearbox HSS non-drive-end bearing temperature       Inbound     26          28              3       INT     10.72   Deg C
Gearbox HSS drive-end bearing temperature           Inbound     29          31              3       INT     10.72   Deg C
Generator drive-end bearing temperature             Inbound     32          32              1       INT     10.72   Deg C
Generator non-drive-end bearing temperature         Inbound     35          37              3       INT     10.72   Deg C
Hydraulic fluid temperature                         Inbound     42          44              3       INT     10.72   Deg C
Ambient air temperature                             Inbound     45          47              3       INT     10.72   Deg C
Gearbox oil temperature                             Inbound     48          50              3       INT     10.72   Deg C
Nacelle air temperature                             Inbound     51          53              3       INT     10.72   Deg C
Hydraulic system pressure, voltage positive         Inbound     54          55              2       INT     10.72   Volts
Blade pitch linear position sensor, voltage +       Inbound     56          57              2       INT     10.72   Volts
Hydraulic system pressure, voltage common           Inbound     70          71              2       INT     10.72   Volts
Blade pitch lin. position sensor, voltage comm      Inbound     72          73              2       INT     10.72   Volts
Current overload on yaw motor 2 when FALSE          Inbound     118         118             1       Bool                    7
Current overload on yaw motor 1 when FALSE          Inbound     118         118             1       Bool                    6
Yaw twist pulse                                     Inbound     118         118             1       Bool                    5
Yaw twist nominal range                             Inbound     118         118             1       Bool                    4
Yaw twist counter-clockwise                         Inbound     118         118             1       Bool                    3
Yaw twist clockwise                                 Inbound     118         118             1       Bool                    2
Yawing counter-clockwise when TRUE                  Inbound     118         118             1       Bool                    1
Yawing clockwise when TRUE                          Inbound     118         118             1       Bool                    0
Safety Circuit is open when FALSE                   Inbound     119         119             1       Bool                    7
Radial vibration (knock) sensor trig. if FALSE      Inbound     119         119             1       Bool                    5
Current overload on hydraulic pump motor if FALSE   Inbound     119         119             1       Bool                    4
Brakedisk temp opened Safety Circuit if FALSE       Inbound     119         119             1       Bool                    3
Brake pressure is below safety threshold if FALSE   Inbound     119         119             1       Bool                    2
Hydraulic filter may be clogged if FALSE            Inbound     119         119             1       Bool                    1
Hydraulic pump running when TRUE                    Inbound     119         119             1       Bool                    0
Gearbox oil cooler running when TRUE                Inbound     120         120             1       Bool                    7
Current overload on generator fan motor when FALSE  Inbound     120         120             1       Bool                    6
Generator fan running when TRUE                     Inbound     120         120             1       Bool                    5
Current overload on fine filter pump motor if FALSE Inbound     120         120             1       Bool                    4
Fine filter running when TRUE                       Inbound     120         120             1       Bool                    3
Current overload on gearbox oil cooler when FALSE   Inbound     120         120             1       Bool                    1
Hydraulic fluid level is low when FALSE             Inbound     120         120             1       Bool                    0
"rotor" speed sensor is >~22 rpm when FALSE         Inbound     121         121             1       Bool                    7
"shaft" speed sensor is >~22 rpm when FALSE         Inbound     121         121             1       Bool                    6
Malfunction in rotor overspeed protection if FALSE  Inbound     121         121             1       Bool                    5
Stop Circuit is open when FALSE                     Inbound     121         121             1       Bool                    4
UPS is on battery when FALSE                        Inbound     121         121             1       Bool                    3
Malfunction in shaft overspeed protection if FALSE  Inbound     121         121             1       Bool                    2
Overspeed detected on "shaft" speed sensor if FALSE Inbound     121         121             1       Bool                    1
Three-axis vibration opened Stop Circuit if FALSE   Inbound     121         121             1       Bool                    0
UPS is on battery when FALSE                        Inbound     122         122             1       Bool                    7
UPS is on battery when FALSE                        Inbound     122         122             1       Bool                    6
Grid monitor has opended Safety Circuit when FALSE  Inbound     122         122             1       Bool                    5
Grid monitor has opended Safety Circuit when FALSE  Inbound     122         122             1       Bool                    4
Controller watchdog opened Safety Circuit if FALSE  Inbound     122         122             1       Bool                    3
Main contactor Q8 Is closed when TRUE               Inbound     122         122             1       Bool                    0
Brake chopper is actively consuming power when TRUE Inbound     123         123             1       Bool                    1
Brake chopper controller not ready when FALSE       Inbound     123         123             1       Bool                    0
Indicates the converter's operating state           Inbound     154         155             2       UINT    10.72   state
Estimated generator speed                           Inbound     156         157             2       INT     10.72   rpm
Read-only version of ControlWord actually received  Inbound     158         159             2       UINT    10.72   ControlWord
Generator torque                                    Inbound     160         161             2       INT     10.72   lb-ft
Generator power                                     Inbound     162         163             2       INT     10.72   W
Generator frequency                                 Inbound     164         165             2       INT     10.72   Hz
Power converter dc bus voltage                      Inbound     166         167             2       INT     10.72   Volts
Power converter temperature                         Inbound     168         169             2       INT     10.72   Deg C
Power converter alarm code                          Inbound     170         171             2       UINT    
Power converter fault code                          Inbound     172         173             2       UINT    
Line converter unit actual signal 1                 Inbound     174         175             2       INT     10.72   Deg C
Line converter unit actual signal 2                 Inbound     176         177             2       INT     10.72   Deg C
'''

# Name, ecat_start, ecat_stop, length, type, scaling/bit offset
INBOUND = [
['Gearbox HSS non-drive-end bearing temperature', 26, 28, 3, 'INT', 1278, 255],
['Gearbox HSS drive-end bearing temperature', 29, 31, 3, 'INT', 1278, 255],
['Generator drive-end bearing temperature', 32, 34, 3, 'INT', 1278, 255],
['Generator non-drive-end bearing temperature', 35, 37, 3, 'INT', 1278, 255],
['Hydraulic fluid temperature', 42, 44, 3, 'INT', 1278, 255],
['Ambient air temperature', 45, 47, 3, 'INT', 1278, 255],
['Gearbox oil temperature', 48, 50, 3, 'INT', 1278, 255],
['Nacelle air temperature', 51, 53, 3, 'INT', 1278, 255],
['Hydraulic system pressure, voltage positive', 54, 55, 2, 'INT', 10.72, 0],
['Blade pitch linear position sensor, voltage pos', 56, 57, 2, 'INT', 10.72, 0],
['Hydraulic system pressure, voltage common', 70, 71, 2, 'INT', 10.72, 0],
['Blade pitch lin. position sensor, voltage comm', 72, 73, 2, 'INT', 10.72, 0],
['Current overload on yaw motor 2 when FALSE', 118, 118, 1, 'Bool', 7],
['Current overload on yaw motor 1 when FALSE', 118, 118, 1, 'Bool', 6],
['Yaw twist pulse', 118, 118, 1, 'Bool', 5],
['Yaw twist nominal range', 118, 118, 1, 'Bool', 4],
['Yaw twist counter-clockwise', 118, 118, 1, 'Bool', 3],
['Yaw twist clockwise ', 118, 118, 1, 'Bool', 2],
['Yawing counter-clockwise when TRUE', 118, 118, 1, 'Bool', 1],
['Yawing clockwise when TRUE', 118, 118, 1, 'Bool', 0],
['Safety Circuit is open when FALSE', 119, 119, 1, 'Bool', 7],
['Radial vibration (knock) sensor trig. if FALSE', 119, 119, 1, 'Bool', 5],
['Current overload on hydraulic pump motor if FALSE', 119, 119, 1, 'Bool', 4],
['Brakedisk temp opened Safety Circuit if FALSE', 119, 119, 1, 'Bool', 3],
['Brake pressure is below safety threshold if FALSE', 119, 119, 1, 'Bool', 2],
['Hydraulic filter may be clogged if FALSE', 119, 119, 1, 'Bool', 1],
['Hydraulic pump running when TRUE', 119, 119, 1, 'Bool', 0],
['Gearbox oil cooler running when TRUE', 120, 120, 1, 'Bool', 7],
['Current overload on generator fan motor when FALSE', 120, 120, 1, 'Bool', 6],
['Generator fan running when TRUE', 120, 120, 1, 'Bool', 5],
['Current overload on fine filter pump motor if FALSE', 120, 120, 1, 'Bool', 4],
['Fine filter running when TRUE', 120, 120, 1, 'Bool', 3],
['Current overload on gearbox oil cooler when FALSE', 120, 120, 1, 'Bool', 1],
['Hydraulic fluid level is low when FALSE', 120, 120, 1, 'Bool', 0],
['"rotor" speed sensor is >~22 rpm when FALSE', 121, 121, 1, 'Bool', 7],
['"shaft" speed sensor is >~22 rpm when FALSE', 121, 121, 1, 'Bool', 6],
['Malfunction in rotor overspeed protection if FALSE', 121, 121, 1, 'Bool', 5],
['Stop Circuit is open when FALSE', 121, 121, 1, 'Bool', 4],
['UPS is on battery when FALSE', 121, 121, 1, 'Bool', 3],
['Malfunction in shaft overspeed protection if FALSE', 121, 121, 1, 'Bool', 2],
['Overspeed detected on "shaft" speed sensor if FALSE', 121, 121, 1, 'Bool', 1],
['Three-axis vibration opened Stop Circuit if FALSE', 121, 121, 1, 'Bool', 0],
['UPS is on battery when FALSE', 122, 122, 1, 'Bool', 7],
['UPS is on battery when FALSE', 122, 122, 1, 'Bool', 6],
['Grid monitor has opended Safety Circuit when FALSE', 122, 122, 1, 'Bool', 5],
['Grid monitor has opended Safety Circuit when FALSE', 122, 122, 1, 'Bool', 4],
['Controller watchdog opened Safety Circuit if FALSE', 122, 122, 1, 'Bool', 3],
['Main contactor Q8 Is closed when TRUE', 122, 122, 1, 'Bool', 0],
['Brake chopper is actively consuming power when TRUE', 123, 123, 1, 'Bool', 1],
['Brake chopper controller not ready when FALSE', 123, 123, 1, 'Bool', 0],
['Indicates the converter\'s operating state', 154, 155, 2, 'UINT', 10.72, 0],
['Estimated generator speed', 156, 157, 2, 'INT', 10.72, 0],
['Read-only version of ControlWord actually received', 158, 159, 2, 'UINT', 10.72, 0],
['Generator torque', 160, 161, 2, 'INT', 10.72, 0],
['Generator power', 162, 163, 2, 'INT', 10.72, 0],
['Generator frequency', 164, 165, 2, 'INT', 10.72, 0],
['Power converter dc bus voltage', 166, 167, 2, 'INT', 10.72, 0],
['Power converter temperature', 168, 169, 2, 'INT', 10.72, 0],
['Power converter alarm code', 170, 171, 2, 'UINT', 10.72, 0],
['Power converter fault code', 172, 173, 2, 'UINT', 10.72, 0],
['Line converter unit actual signal 1', 174, 175, 2, 'INT', 10.72, 0],
['Line converter unit actual signal 2', 176, 177, 2, 'INT', 10.72, 0],
]


manual_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Scapy for EtherCAT'
}

def net_info():
    return manual_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = manual_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'), active_value=mode, glob=True)
    info.param(pname('interface'), label='Communications Interface', default='eth0')
    info.param(pname('timeout'), label='Default Capture Duration', default=60.)
    info.param(pname('bpf_filter'), label='Default BPF filter', default='tcp')

def twos_comp(int_val, bits):
    if (int_val & (1 << (bits-1))) != 0:  # check sign bit
        int_val = int_val - (1 << bits)  # neg value
    return int_val

GROUP_NAME = 'scapy_for_ecat'

class NET(network.NET):

    def __init__(self, ts, group_name, support_interfaces=None):
        network.NET.__init__(self, ts, group_name, support_interfaces)
        self.ts = ts
        self.iface = self._param_value('interface')
        self.timeout = self._param_value('timeout')
        self.bpf_filter = self._param_value('bpf_filter')
        self.mode = "online"

        # save locally if not running with SVP GUI
        if not hasattr(self, 'net_dir'):
            self.net_dir = os.path.realpath(__file__)
        print('net_dir = %s' % self.net_dir)

        # Initialize traffic packets and inbound/outbound objects
        self.packets = []
        # self.get_packets()  # collect online packets
        # self.inbound_packets = [packet for packet in self.packets if packet.src==INBOUND_SRC]
        # self.outbound_packets = [packet for packet in self.packets if packet.src==OUTBOUND_SRC]
        
        # Initialize signal data
        self.signal_data = {}

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def info(self):
        """
        Return information string for the NET device.
        """
        return 'Scapy EtherCAT Network Capture for Vestas V27 Wind Turbines with Sandia NI Controller'

    def print_signals(self):
        """
        Print the key value pairs for self.signal_data
        """

        for k, v in self.signal_data.items():
            if self.ts is not None:
                self.ts.log('%s: %s' % (k, v))
            else:
                print('%s: %s' % (k, v))

    def get_packets(self, count=4):
        """
        Get packets from PCAP file or live from iface interface

        :param iface: interface name for online capture
        :param count: number of packets to collect
        :return packets: scapy packet data
        """

        if self.mode == "offline":
            print('Loading pcap = %s' % self.pcap_file)
            self.packets = rdpcap(self.pcap_file, count=count)
            print('pcap loaded. packets = %s' % len(packets))

        else:  # online
            # Can add prn=self.packet_summary if live debugging is necessary
            self.packets = sniff(iface=self.iface, count=count, filter=self.bpf_filter, timeout=self.timeout)  
            # self.print_capture()

    def print_capture(self):
        """
        Save pcap to net_dir directory with timestamp
        """

        self.ts.log(self.packets)
        for pkt in self.packets:
            try:
                if IP in pkt:
                    ip_src=pkt[IP].src
                    ip_dst=pkt[IP].dst

                    if TCP in pkt:
                        tcp_sport=pkt[TCP].sport
                        tcp_dport=pkt[TCP].dport

                        self.ts.log(str(ip_src) + ":" + str(tcp_sport) + ' -> ' + str(ip_dst) + ":" + str(tcp_dport))
                    else:
                        self.ts.log(str(ip_src) + ' -> ' + str(ip_dst))
                else:
                    # self.ts.log_debug('No IP in packet')
                    if EtherCatLRW in pkt[Ether][EtherCat]:
                        # self.ts.log_debug(pkt[Ether][EtherCat][EtherCatLRW].data)
                        self.ts.log_debug('EtherCatLRW with lenth: %s' % len(pkt[Ether][EtherCat][EtherCatLRW].data))
                    elif EtherCatBWR in pkt[Ether][EtherCat]:
                        self.ts.log_debug('EtherCatBWR with lenth: %s' % len(pkt[Ether][EtherCat][EtherCatBWR].data))
                    elif EtherCatFPRD in pkt[Ether][EtherCat]:
                        self.ts.log_debug('EtherCatFPRD with lenth: %s' % len(pkt[Ether][EtherCat][EtherCatFPRD].data))
                    else:
                        self.ts.log_debug('EtherCat with lenth: %s' % len(pkt[Ether][EtherCat].data))

            except Exception as e: 
                self.ts.log_warning('Error printing packet information: %s' % e)

        #self.ts.log('%s' % self.packets.summary())

    def save_packets(self):
        """
        Save pcap to net_dir directory with timestamp
        """
        
        path = os.path.join(self.net_dir, str(time.time()) + '.pcap')
        if self.ts: 
            self.ts.log('Saving pcap data to %s' % path)
        else:
            print('Saving pcap data to path = %s' % path)
        wrpcap(path, self.packets)

    def filter_packets(self):
        """
        Apply filter on the captured packets
        """
        pass

    def get_signal_data(self):
        """
        Populate dict with values based on pcap data and scaling factors

        :return signal_data: dict, with name:value for each signal
        """

        for p in self.packets:
            # self.ts.log_debug('Raw packet = %s' % raw(p))

            if EtherCat in p[Ether]:
                if EtherCatLRW in p[Ether][EtherCat]:
                    # self.ts.log_debug(p[Ether][EtherCat][EtherCatLRW].data)
                    # self.ts.log_debug('lenth: %s' % len(raw(p[Ether])))
                    # self.ts.log_debug('lenth: %s' % len(raw(p[Ether][EtherCat])))
                    # self.ts.log_debug('lenth: %s' % len(p[Ether][EtherCat][EtherCatLRW].data))

                    hex_str = ''
                    for pkt_data in p[Ether][EtherCat][EtherCatLRW].data:
                        hex_str += "{:02x}".format(pkt_data)

                    # self.ts.log_debug('hex: %s' % hex_str)
                    # self.ts.log_debug('hex len: %s' % len(hex_str))

                    if p.src == OUTBOUND_SRC:
                        params = OUTBOUND
                        # self.ts.log('Packet is Outbound')
                    else:
                        params = INBOUND
                        # self.ts.log('Packet is Inbound')
                        self.ts.log_debug('hex: %s' % hex_str[0:50])

                    self.signal_data = {}
                    for i in range(len(params)):
                        bool_byte = 0
                        header_length = 26  # bytes - this is added to bytes in lists above (subtract to get data index)
                        start = (params[i][1] - header_length) * 2  # in nibbles because this is the hex string
                        end = (params[i][2] - header_length) * 2 + 2  # in nibbles because this is the hex string
                        bit_or_scaling = params[i][5] 

                        hex_slice = hex_str[start:end]

                        # if params[i][0] == 'Blade pitch linear position sensor, voltage pos':
                        #     self.ts.log('hex data: %s' % hex_slice)
                        #     self.ts.log(hex_str[38-26:41-26+1])
                        #     self.ts.log(hex_str[24:32])
                        # if params[i][0] == 'Gearbox HSS non-drive-end bearing temperature':
                        #     self.ts.log('hex data: %s' % hex_slice)
                        #     little_endian = '%s%s%s' % (hex_slice[4:6], hex_slice[2:4], hex_slice[0:2])
                        #     self.ts.log('Reordered: %s' % (little_endian))
                        #     unscaled = int(little_endian, 16)
                        #     self.ts.log('Unscaled: %s' % unscaled)
                        #     scaled = params[i][4] * (twos_comp(unscaled, params[i][3]) / 2**((params[i][3]*8)-1) - params[i][5]
                        #     self.ts.log('Scaled: %s' % scaled)

                        if params[i][4] == 'INT':
                            offset = params[i][6]
                            if params[i][3] == 1:
                                unscaled = twos_comp(int(hex_slice, 16), 8)  # 2's compliment
                            elif params[i][3] == 2:
                                little_endian = '%s%s' % (hex_slice[2:4], hex_slice[0:2])  # little endian conversion
                                unscaled = twos_comp(int(little_endian, 16), 16)  # 2's compliment
                            else: # params[i][3] == 3:
                                little_endian = '%s%s%s' % (hex_slice[4:6], hex_slice[2:4], hex_slice[0:2])
                                unscaled = twos_comp(int(little_endian, 16), 24)  # 2's compliment
                            conversion = 2**((params[i][2] * 8) - 1)  # to put on a [-1, 1] range
                            self.signal_data[params[i][0]] = (bit_or_scaling * (unscaled / conversion)) + offset
                            # self.ts.log_debug('Found %s [INT]: %s' % (params[i][0], self.signal_data[params[i][0]]))

                        if params[i][4] == 'UINT':
                            offset = params[i][6]
                            if params[i][3] == 1:
                                unscaled = int(hex_slice, 16)
                            elif params[i][3] == 2:
                                little_endian = '%s%s' % (hex_slice[2:4], hex_slice[0:2])  # little endian conversion
                                unscaled = int(little_endian, 16)
                            else: # params[i][3] == 3:
                                little_endian = '%s%s%s' % (hex_slice[4:6], hex_slice[2:4], hex_slice[0:2])  # little endian conversion
                                unscaled = int(little_endian, 16)
                            conversion = 2**(params[i][2] * 8)  # to put on a [0, 1] range
                            self.signal_data[params[i][0]] = (bit_or_scaling * (unscaled / conversion)) + offset
                            # self.ts.log_debug('Found %s [UINT]: %s' % (params[i][0], self.signal_data[params[i][0]]))

                        if params[i][4] == 'Bool':
                            val = int(hex_slice, 16)

                            if val & (1 << bit_or_scaling) == (1 << bit_or_scaling):
                                self.signal_data[params[i][0]] = 'True'
                            else:
                                self.signal_data[params[i][0]] = 'False'
                            # self.ts.log_debug('Found %s [Bool]: %s' % (params[i][0], self.signal_data[params[i][0]]))
                else:
                    # self.ts.log_warning('Packet did not contain LWR (Logical WRite)')
                    pass
            else:
                # self.ts.log_warning('Packet did not contain EtherCAT')
                pass

        return self.signal_data

    '''
    Baseline functions were initially used to compare EtherCAT hex packet data to a baseline
    '''
    def get_baselines(self):
        """
        UNUSED - Collect the outbound and inbound baseline hex strings

        :return: outbound hex string, inbound hex string
        """
        outbound = None
        inbound = None
        for p in self.packets:
            if EtherCatLRW in p[Ether][EtherCat]:
                hex_str = ''
                for pkt_data in p[Ether][EtherCat][EtherCatLRW].data:
                    hex_str += hex(pkt_data)[2:]
                
                if outbound is None:
                    if p.src == OUTBOUND_SRC:
                        outbound = hex_str
                
                if inbound is None:
                    if p.src == INBOUND_SRC:
                        inbound = hex_str

            if inbound is not None and outbound is not None: 
                return outbound, inbound

    def compare_to_baseline():
        """
        UNUSED - Color the hex data based on differences from baseline dataset
        """

        for p in self.packets:
            # print('Raw packet = %s' % raw(p))

            if EtherCatLRW in p[Ether][EtherCat]:
                
                color_hex_str = ''
                if p.src == OUTBOUND_SRC:
                    if len(self.outbound) == len(hex_str):
                        for i in range(len(self.outbound)):
                            if self.outbound[i] != hex_str[i]:
                                color_hex_str += self.color_blue(hex_str[i])
                            else:
                                color_hex_str += hex_str[i]
                    else:
                        print('New outbount length. Baseline = %s, packet = %s' % (len(self.outbound),len(hex_str)))
                        print(hex_str)
                        
                elif p.src == INBOUND_SRC:
                    # print(len(self.inbound), len(hex_str))
                    if len(self.inbound) == len(hex_str):
                        for i in range(len(self.inbound)):
                            if self.inbound[i] != hex_str[i]:
                                color_hex_str += self.color_red(hex_str[i])
                            else:
                                color_hex_str += hex_str[i]
                    else:
                        print('New inbound length. Baseline = %s, packet = %s' % (len(self.inbound),len(hex_str)))
                        print(hex_str)
                        
                print(color_hex_str)
                
    def packet_summary(self, pkt):
        """
        scapy print function during the sniff
        """
        if IP in pkt:
            ip_src=pkt[IP].src
            ip_dst=pkt[IP].dst
        if TCP in pkt:
            tcp_sport=pkt[TCP].sport
            tcp_dport=pkt[TCP].dport

            self.ts.log(str(ip_src) + ":" + str(tcp_sport) + ' -> ' + str(ip_dst) + ":" + str(tcp_dport))

    def color_red(self, msg=None):
        return RED + msg + RESET

    def color_blue(self, msg=None):
        return BLUE + msg + RESET

if __name__ == "__main__":
    pass

