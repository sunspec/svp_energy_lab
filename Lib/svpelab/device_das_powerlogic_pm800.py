"""
Communications to a EGX100 Gateway to the Schneider Electric PowerLogic PM800 Series Power Meters
Communications use Modbus TCP/IP

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


# data_points = [
#     'TIME',
#     'DC_V',
#     'DC_I',
#     'AC_VRMS_1',
#     'AC_IRMS_1',
#     'DC_P',
#     'AC_S_1',
#     'AC_P_1',
#     'AC_Q_1',
#     'AC_FREQ_1',
#     'AC_PF_1',
#     'TRIG',
#     'TRIG_GRID'
# ]

data_points = [
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
    'TRIG_GRID'
]

import time
try:
    import sunspec.core.modbus.client as client
    import sunspec.core.util as util
    import binascii
except Exception as e:
    print('SunSpec or binascii packages did not import!')


class DeviceError(Exception):
    pass


class Device(object):

    def __init__(self, params=None, ts=None):
        self.ts = ts
        self.device = None

        self.comm = params.get('comm')
        if self.comm == 'Modbus TCP':
            self.ip_addr = params.get('ip_addr')
            self.ip_port = params.get('ip_port')
            self.ip_timeout = params.get('ip_timeout')
            self.slave_id = params.get('slave_id')

        self.data_points = list(data_points)
        self.points = None
        self.point_indexes = []

        self.rec = {}
        self.recs = []

        self.open()

    def info(self):
        return 'DAS Hardware: Square D PowerLogic PM800 Series Power Meter'

    def open(self):
        """
        Open the communications resources associated with the device.
        """
        try:
            self.device = client.ModbusClientDeviceTCP(slave_id=self.slave_id, ipaddr=self.ip_addr,
                                                       ipport=self.ip_port, timeout=self.ip_timeout)
        except Exception as e:
            raise DeviceError('Cannot connect to PM800: %s' % e)

    def data_capture(self, enable=True):
        pass

    def close(self):
        self.device = None

    def data_read(self):

        # Changed to the bulk read option to speed up acquisition time
        """ Single or Split Phase Option
        datarec = {'time': time.time(),
                   'ac': (self.generic_float_read(11728),   # Voltage, L-N Average
                          self.generic_float_read(11710),   # Current, 3-Phase Average
                          self.generic_float_read(11736),   # Real Power, Total
                          self.generic_float_read(11752),   # Apparent Power, Total
                          self.generic_float_read(11744),   # Reactive Power, Total
                          self.generic_float_read(11760),   # True Power Factor, Total
                          self.generic_float_read(11762)),  # Frequency
                   'dc': (None,
                          None,
                          None)}

        # 3 phase option
        datarec = {'time': time.time(),
                   'ac_1': (self.generic_float_read(11720),  # Voltage, A-N
                            self.generic_float_read(11700),  # Current, Phase A
                            self.generic_float_read(11730),  # Real Power, Phase A
                            self.generic_float_read(11746),  # Apparent Power, Phase A
                            self.generic_float_read(11738),  # Reactive Power, Phase A
                            self.generic_float_read(11754),  # True Power Factor, Phase A,
                            f),
                   'ac_2': (self.generic_float_read(11722),  # Voltage, B-N
                            self.generic_float_read(11702),  # Current, Phase B
                            self.generic_float_read(11732),  # Real Power, Phase B
                            self.generic_float_read(11748),  # Apparent Power, Phase B
                            self.generic_float_read(11740),  # Reactive Power, Phase B
                            self.generic_float_read(11756),  # True Power Factor, Phase B
                            f),
                   'ac_3': (self.generic_float_read(11724),  # Voltage, C-N
                            self.generic_float_read(11704),  # Current, Phase C
                            self.generic_float_read(11734),  # Real Power, Phase C
                            self.generic_float_read(11750),  # Apparent Power, Phase C
                            self.generic_float_read(11742),  # Reactive Power, Phase C
                            self.generic_float_read(11758),  # True Power Factor, Phase C
                            f),
                   'dc': (None,
                          None,
                          None)}
        """
        data_dict = self.bulk_float_read()

        data_points = [
            data_dict['time'], #'TIME',
            data_dict['dc'][0], #'DC_V',
            data_dict['dc'][1], #'DC_I',
            data_dict['ac_1'][0], #'AC_VRMS_1',
            data_dict['ac_2'][0], #'AC_VRMS_2',
            data_dict['ac_3'][0], #'AC_VRMS_3',
            data_dict['ac_1'][1], #'AC_IRMS_1',
            data_dict['ac_2'][1], #'AC_IRMS_2',
            data_dict['ac_3'][1], #'AC_IRMS_3',
            data_dict['dc'][2], #'DC_P',
            data_dict['ac_1'][3], #'AC_S_1',
            data_dict['ac_2'][3], #'AC_S_2',
            data_dict['ac_3'][3], #'AC_S_3',
            data_dict['ac_1'][2], #'AC_P_1',
            data_dict['ac_2'][2], #'AC_P_2',
            data_dict['ac_3'][2], #'AC_P_3',
            data_dict['ac_1'][4], #'AC_Q_1',
            data_dict['ac_2'][4], #'AC_Q_2',
            data_dict['ac_3'][4], #'AC_Q_3',
            data_dict['ac_1'][6], #'AC_FREQ_1',
            data_dict['ac_2'][6], #'AC_FREQ_2',
            data_dict['ac_3'][6], #'AC_FREQ_3',
            data_dict['ac_1'][5], #'AC_PF_1',
            data_dict['ac_2'][5], #'AC_PF_2',
            data_dict['ac_3'][5], #'AC_PF_3',
            None, #'TRIG',
            None, #'TRIG_GRID'
        ]

        return data_points

    def generic_float_read(self, reg_in_lit):
        data = self.device.read(reg_in_lit-1, 2)  # the register is one less than reported in the literature
        data_num = util.data_to_float(data)
        return data_num

    def bulk_float_read(self, start=11700, end=11762):
        actual_start = start - 1  # the register is one less than reported in the literature
        actual_length = (end - start) + 2
        data = self.device.read(actual_start, actual_length)

        datarec = {'time': time.time(),
                   'ac_1': (util.data_to_float(data[reg_shift(11720)[0]:reg_shift(11720)[1]]),  # Voltage, A-N
                            util.data_to_float(data[reg_shift(11700)[0]:reg_shift(11700)[1]]),  # Current, Phase A
                            util.data_to_float(data[reg_shift(11730)[0]:reg_shift(11730)[1]]),  # Real Power, Phase A
                            util.data_to_float(data[reg_shift(11746)[0]:reg_shift(11746)[1]]),  # Apparent Power, Phase A
                            util.data_to_float(data[reg_shift(11738)[0]:reg_shift(11738)[1]]),  # Reactive Power, Phase A
                            util.data_to_float(data[reg_shift(11754)[0]:reg_shift(11754)[1]]),  # True Power Factor, Phase A
                            util.data_to_float(data[reg_shift(11762)[0]:reg_shift(11762)[1]])), # Frequency
                   'ac_2': (util.data_to_float(data[reg_shift(11722)[0]:reg_shift(11722)[1]]),  # Voltage, B-N
                            util.data_to_float(data[reg_shift(11702)[0]:reg_shift(11702)[1]]),  # Current, Phase B
                            util.data_to_float(data[reg_shift(11732)[0]:reg_shift(11732)[1]]),  # Real Power, Phase B
                            util.data_to_float(data[reg_shift(11748)[0]:reg_shift(11748)[1]]),  # Apparent Power, Phase B
                            util.data_to_float(data[reg_shift(11740)[0]:reg_shift(11740)[1]]),  # Reactive Power, Phase B
                            util.data_to_float(data[reg_shift(11756)[0]:reg_shift(11756)[1]]),  # True Power Factor, Phase B
                            util.data_to_float(data[reg_shift(11762)[0]:reg_shift(11762)[1]])), # Frequency
                   'ac_3': (util.data_to_float(data[reg_shift(11724)[0]:reg_shift(11724)[1]]),  # Voltage, C-N
                            util.data_to_float(data[reg_shift(11704)[0]:reg_shift(11704)[1]]),  # Current, Phase C
                            util.data_to_float(data[reg_shift(11734)[0]:reg_shift(11734)[1]]),  # Real Power, Phase C
                            util.data_to_float(data[reg_shift(11750)[0]:reg_shift(11750)[1]]),  # Apparent Power, Phase C
                            util.data_to_float(data[reg_shift(11742)[0]:reg_shift(11742)[1]]),  # Reactive Power, Phase C
                            util.data_to_float(data[reg_shift(11758)[0]:reg_shift(11758)[1]]),  # True Power Factor, Phase C
                            util.data_to_float(data[reg_shift(11762)[0]:reg_shift(11762)[1]])), # Frequency
                   'dc': (None,
                          None,
                          None)}

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
        pass

    def waveform_capture(self, enable=True, sleep=None):
        """
        Enable/disable waveform capture.
        """
        pass

    def waveform_status(self):
        pass

    def waveform_force_trigger(self):
        pass

    def waveform_capture_dataset(self):
        pass


def reg_shift(reg):
    r1 = (reg - 11700)*2
    r2 = r1 + 4
    return r1, r2

''' Float Registers
Currents
Reg     Name                     Size   Type    Access  NV    Scale   Units   Range
11700   Current, Phase A         2      Float   RO      N     -       Amps    RMS
11702   Current, Phase B         2      Float   RO      N     -       Amps    RMS
11704   Current, Phase C         2      Float   RO      N     -       Amps    RMS
11706   Current, Neutral         2      Float   RO      N     -       Amps    RMS
11708   Current, Ground          2      Float   RO      N     -       Amps    RMS
11710   Current, 3-Phase Average 2      Float   RO      N     -       Amps    Calculated mean of Phases A, B & C Y

Voltages
Reg     Name                    Size    Type    Access  NV    Scale Units   Notes
11712   Voltage, A-B            2       Float   RO      N       -   Volts   RMS Voltage measured between A & B Y
11714   Voltage, B-C            2       Float   RO      N       -   Volts   RMS Voltage measured between B & C Y
11716   Voltage, C-A            2       Float   RO      N       -   Volts   RMS Voltage measured between C & A Y
11718   Voltage, L-L Average    2       Float   RO      N       -   Volts   RMS 3 Phase Average L-L Voltage Y
11720   Voltage, A-N            2       Float   RO      N       -   Volts   RMS Voltage measured between A & N
11722   Voltage, B-N            2       Float   RO      N       -   Volts   RMS Voltage measured between B & N
11724   Voltage, C-N            2       Float   RO      N       -   Volts   RMS Voltage measured between C & N
11726   Voltage, N-G            2       Float   RO      N       -   Volts   RMS Voltage measured between N & G
11728   Voltage, L-N Average    2       Float   RO      N       -   Volts   RMS 3-Phase Average L-N Voltage

Powers
Reg     Name                    Size    Type    Access  NV    Scale Units   Notes
11730   Real Power, Phase A     2       Float   RO      N       -   W       Real Power (PA)
11732   Real Power, Phase B     2       Float   RO      N       -   W       Real Power (PB)
11734   Real Power, Phase C     2       Float   RO      N       -   W       Real Power (PC)
11736   Real Power, Total       2       Float   RO      N       -   W       4-wire system = PA+PB+PC
11738   Reactive Power, Phase A 2       Float   RO      N       -   VAr     Reactive Power (QA)
11740   Reactive Power, Phase B 2       Float   RO      N       -   VAr     Reactive Power (QB)
11742   Reactive Power, Phase C 2       Float   RO      N       -   VAr     Reactive Power (QC)
11744   Reactive Power, Total   2       Float   RO      N       -   VAr     4-wire system = QA+QB+QC
11746   Apparent Power, Phase A 2       Float   RO      N       -   VA      Apparent Power (SA)
11748   Apparent Power, Phase B 2       Float   RO      N       -   VA      Apparent Power (SB)
11750   Apparent Power, Phase C 2       Float   RO      N       -   VA      Apparent Power (SC)
11752   Apparent Power, Total   2       Float   RO      N       -   VA      4-wire system = SA+SB+SC

Power Factor
Reg     Name                       Size Type    Access  NV    Notes
11754   True Power Factor, Phase A 2    Float   RO      N     Derived using the complete harmonic content of P&Q
11756   True Power Factor, Phase B 2    Float   RO      N     Derived using the complete harmonic content of P&Q
11758   True Power Factor, Phase C 2    Float   RO      N     Derived using the complete harmonic content of P&Q
11760   True Power Factor, Total   2    Float   RO      N     Derived using the complete harmonic content of P&Q

Frequency
Reg     Name      Size  Type    Access  NV  Units  Notes
11762   Frequency 2     Float   RO      N   Hz     Frequency of circuits being monitored.
'''


"""
These are simple functions for reading individual values.
"""


def trace(msg):
    print(msg)


# Reg   Name            Size    Type    Access  NV  Scale   Units       Range
# 1120  Voltage, A-B    1       Integer RO      N   D       Volts/Scale 0 - 32,767 RMS Voltage measured between A & B
def readVoltageAB():
    data = device.read(1119, 1)
    voltage = util.data_to_s16(data)*(10**scaleD())
    return voltage


# Reg   Name                Size    Type    Access  NV  Scale   Units       Range
# 1140  Real Power, Phase A 1       Integer RO      N   F       kW/Scale    -32,767 to 32,767 (-32,768 if N/A)
def readPowerA():
    data = device.read(1139, 1)
    watt = util.data_to_s16(data)*(10**scaleF())
    return watt


# Reg   Name                Size    Type    Access  NV  Scale   Units       Range
# 1141  Real Power, Phase B 1       Integer RO      N   F       kW/Scale    -32,767 to 32,767 (-32,768 if N/A)
def readPowerB():
    data = device.read(1140, 1)
    watt = util.data_to_s16(data)*(10**scaleF())
    return watt


# Reg   Name                Size    Type    Access  NV  Scale   Units       Range
# 1142  Real Power, Phase C 1       Integer RO      N   F       kW/Scale    -32,767 to 32,767 (-32,768 if N/A)
def readPowerC():
    data = device.read(1141, 1)
    watt = util.data_to_s16(data)*(10**scaleF())
    return watt


# Reg   Name                Size    Type    Access  NV  Scale   Units       Range
# 1143  Real Power, Total   1       Integer RO      N   F       kW/Scale    -32,767 to 32,767 (-32,768 if N/A)
def readPower():
    data = device.read(1142, 1)
    watt = util.data_to_s16(data)*(10**scaleF())
    return watt


# Reg   Name                Size    Type    Access  NV  Scale   Units       Range
# 11736 Real Power, Total   2       Float   RO      N
def readFloatPower():
    data = device.read(11735, 2)
    watt = util.data_to_float(data)
    return watt


# Reg   Name                    Size    Type    Access  NV  Scale   Units       Range
# 1144  Reactive Power, Phase A 1       Integer RO      N   F       kVAr/Scale  -32,767 to 32,767 (-32,768 if N/A)
def readVarsA():
    data = device.read(1143, 1)
    vars = util.data_to_s16(data)
    return vars


# Reg   Name                    Size    Type    Access  NV  Scale   Units       Range
# 1145  Reactive Power, Phase B 1       Integer RO      N   F       kVAr/Scale  -32,767 to 32,767 (-32,768 if N/A)
def readVarsB():
    data = device.read(1144, 1)
    vars = util.data_to_s16(data)*(10**scaleF())
    return vars


# 1146 Reactive Power, Phase C 1 Integer RO N F kVAr/Scale -32,767 to 32,767 (-32,768 if N/A)
def readVarsC():
    data = device.read(1145, 1)
    vars = util.data_to_s16(data)*(10**scaleF())
    return vars


# Reg   Name                    Size    Type    Access  NV  Scale   Units       Range
# 1147  Reactive Power, Total   1       Integer RO      N   F       kVAr/Scale  -32,767 to 32,767 (-32,768 if N/A)
def readVars():
    data = device.read(1146, 1)
    vars = util.data_to_s16(data)*(10**scaleF())
    return vars


# Reg   Name        Size    Type    Access  NV  Scale   Units   Range
# 1180  Frequency   1       Integer RO      N   xx      0.01Hz  2,300 - 6,700 (-32,768 if N/A),
# Frequency of circuits being monitored. If the frequency is out of range, the register will be -32,768.
def readHz():
    data = device.read(1179, 1)
    freq = util.data_to_u16(data)*(10**-2)
    return freq


# Reg   Name        Size    Type    Access  NV  Scale   Units       Range
# 11762 Frequency   2       Float   RO      N   -       Hz          Frequency of circuits being monitored.
def readFloatHz():
    data = device.read(11761, 2)
    freq = util.data_to_float(data)
    return freq


# Reg   Name                     Size   Type    Access  NV  Scale   Units       Range
# 11760 True Power Factor, Total 2      Float   RO      N   -       Derived using the complete harmonic content of real
#                                                                   and apparent power
def readFloatPF():
    data = device.read(11759, 2)
    pf = util.data_to_float(data)
    return pf


# 11699 (Use this as a check for the floating point activation)
def readFloatCurrentA():
    data = device.read(11699, 1)
    currA = util.data_to_s16(data)
    return currA


def enableFloats():
    device.write(7999, util.u16_to_data(9020))  # enable float values
    device.write(3247, util.u16_to_data(1))  # enable float values
    device.write(8000, util.u16_to_data(1))  # enable float values
    device.write(7999, util.u16_to_data(9021))  # enable float values


# Reg   Name                    Size    Type    Access  NV  Scale   Units       Range
# 3209  Scale A - 3 Phase Amps  1       Integer R/CW    Y   xx      1.0         -2 to 1 Power of 10 Default = 0
def scaleA():
    data = device.read(3208, 1)
    return util.data_to_s16(data)


# Reg   Name                    Size    Type    Access  NV  Scale   Units       Range
# 3210  Scale B - Neutral Amps  1       Integer R/CW    Y   xx      1.0         -2 to 1 Power of 10 Default = 0
def scaleB():
    data = device.read(3209, 1)
    return util.data_to_s16(data)


# Reg   Name                    Size    Type    Access  NV  Scale   Units       Range
# 3212  Scale D - 3 Phase Volts 1       Integer R/CW    Y   xx      1.0         -2 to 2 Power of 10 Default = 0
def scaleD():
    data = device.read(3211, 1)
    return util.data_to_s16(data)


# Reg   Name                    Size    Type    Access  NV  Scale   Units       Range
# 3213  Scale E - Neutral Volts 1       Integer R/CW    Y   xx      1.0         -2 to 2 Power of 10 Default = -1
def scaleE():
    data = device.read(3212, 1)
    return util.data_to_s16(data)


# Reg   Name            Size    Type    Access  NV  Scale   Units       Range
# 3214  Scale F - Power 1       Integer R/CW    Y   xx      1.0         -3 to 3 Power of 10 Default = 0
def scaleF():
    data = device.read(3213, 1)
    return util.data_to_s16(data)


# Reg   Name                        Size    Type    Access  NV  Scale   Units       Range
# 3208  Nominal System Frequency    1       Integer R/CW    Y   xx      Hz          50, 60, 400 Default = 60
def readFreqNom():
    data = device.read(3207, 1)
    return util.data_to_u16(data)


# Reg   Name                    Size    Type    Access  NV  Scale   Units       Range
# 624   IP Subnet Mask          2       Octets  R/CW    Y   -       -           IP Address Format Last octet can not
#                                                                               be set to 254. Network part of the mask
#                                                                               must be all '1's and device part must be
#                                                                               all '0's example: 255.255.255.0 is good
#                                                                               255.253.255.0 is invalid
def readIPSubnet():
    data = device.read(623, 2)
    ip_subnet = '%d:%d:%d:%d' % (ord(data[0]), ord(data[1]), ord(data[2]), ord(data[3]))
    #print('%d:%d:%d:%d' % (ord(data[0]), ord(data[1]), ord(data[2]), ord(data[3])))
    return ip_subnet


# Reg   Name                    Size    Type    Access  NV  Scale   Units       Range
# 622   IP Address              2       Octets  R/CW    Y   -       -           IP Address Format First octet must not
#                                                                               be set to 254. Network part of the mask
#                                                                               must be all '1's and device part must be
#                                                                               all '0's example: 255.255.255.0 is good
#                                                                               255.253.255.0 is invalid
def readIP():
    data = device.read(621, 2)
    ip = '%d:%d:%d:%d' % (ord(data[0]), ord(data[1]), ord(data[2]), ord(data[3]))
    #print('%d:%d:%d:%d' % (ord(data[0]), ord(data[1]), ord(data[2]), ord(data[3])))
    return ip


# Reg   Name      Size  Type    Access  NV  Scale   Units       Range
# 629   Baud Rate 1     Integer R/CW    Y   -       -           5-11 Currently Supported 5 = 2400, 6 = 4800, 7 = 9600,
#                                                               8 = 19200 (Default), 9 = 38400
def readBaudRate():
    data = device.read(628, 1)
    return util.data_to_u16(data)

# Testing bulk reads
def bulk_float_read(device, start=11700, end=11762):
    actual_start = start - 1  # the register is one less than reported in the literature
    actual_length = (end - start) + 2
    print(('Start Reg: %s, Read Length: %s' % (actual_start, actual_length)))

    data = device.read(actual_start, actual_length)
    print(('Data length: %s' % len(data)))
    print(('Start Reg: %s, End Reg: %s' % (reg_shift(11762)[0], reg_shift(11762)[1])))
    print(util.data_to_float(data[reg_shift(11762)[0]:reg_shift(11762)[1]]))

    datarec = {'time': time.time(),
               'ac_1': (util.data_to_float(data[reg_shift(11720)[0]:reg_shift(11720)[1]]),  # Voltage, A-N
                        util.data_to_float(data[reg_shift(11700)[0]:reg_shift(11700)[1]]),  # Current, Phase A
                        util.data_to_float(data[reg_shift(11730)[0]:reg_shift(11730)[1]]),  # Real Power, Phase A
                        util.data_to_float(data[reg_shift(11746)[0]:reg_shift(11746)[1]]),  # Apparent Power, Phase A
                        util.data_to_float(data[reg_shift(11738)[0]:reg_shift(11738)[1]]),  # Reactive Power, Phase A
                        util.data_to_float(data[reg_shift(11754)[0]:reg_shift(11754)[1]]),  # True Power Factor, Phase A
                        util.data_to_float(data[reg_shift(11762)[0]:reg_shift(11762)[1]])), # Frequency
               'ac_2': (util.data_to_float(data[reg_shift(11722)[0]:reg_shift(11722)[1]]),  # Voltage, B-N
                        util.data_to_float(data[reg_shift(11702)[0]:reg_shift(11702)[1]]),  # Current, Phase B
                        util.data_to_float(data[reg_shift(11732)[0]:reg_shift(11732)[1]]),  # Real Power, Phase B
                        util.data_to_float(data[reg_shift(11748)[0]:reg_shift(11748)[1]]),  # Apparent Power, Phase B
                        util.data_to_float(data[reg_shift(11740)[0]:reg_shift(11740)[1]]),  # Reactive Power, Phase B
                        util.data_to_float(data[reg_shift(11756)[0]:reg_shift(11756)[1]]),  # True Power Factor, Phase B
                        util.data_to_float(data[reg_shift(11762)[0]:reg_shift(11762)[1]])), # Frequency
               'ac_3': (util.data_to_float(data[reg_shift(11724)[0]:reg_shift(11724)[1]]),  # Voltage, C-N
                        util.data_to_float(data[reg_shift(11704)[0]:reg_shift(11704)[1]]),  # Current, Phase C
                        util.data_to_float(data[reg_shift(11734)[0]:reg_shift(11734)[1]]),  # Real Power, Phase C
                        util.data_to_float(data[reg_shift(11750)[0]:reg_shift(11750)[1]]),  # Apparent Power, Phase C
                        util.data_to_float(data[reg_shift(11742)[0]:reg_shift(11742)[1]]),  # Reactive Power, Phase C
                        util.data_to_float(data[reg_shift(11758)[0]:reg_shift(11758)[1]]),  # True Power Factor, Phase C
                        util.data_to_float(data[reg_shift(11762)[0]:reg_shift(11762)[1]])), # Frequency
               'dc': (None,
                      None,
                      None)}

    return datarec

if __name__ == "__main__":

    ipaddr = '134.253.170.243'
    #ipaddr = str(raw_input('ip address: '))
    device = None

    if ipaddr:
        device = client.ModbusClientDeviceTCP(slave_id=22, ipaddr=ipaddr, ipport=502, timeout=10) #, trace_func=trace)

        print(('%s' % bulk_float_read(device)))

        readVoltageAB()

        print(('Freq is = %s' % readHz()))
        print(('Power is = %s' % readPower()))

        print(('Baud Rate = %s' % readBaudRate()))
        print(('Freq Nom = %s' % readFreqNom()))
        print(('Freq (float) = %s' % readFloatHz()))
        print(('Power (float) = %s' % readFloatPower()))
        print(('Power (float) = %s' % readFloatPF()))

        print(('Scale A = %s' % scaleA()))
        print(('Scale B = %s' % scaleB()))
        print(('Scale D = %s' % scaleD()))
        print(('Scale E = %s' % scaleE()))
        print(('Scale F = %s' % scaleF()))

        # for i in range(100):
        #     print('Power (float) = %s' % readFloatPower())
        #     print('Power is = %s' % readPower())
        #     time.sleep(0.25)


