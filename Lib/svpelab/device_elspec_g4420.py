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

import time
try:
    import sunspec.core.modbus.client as client
    import sunspec.core.util as util
    import binascii
except Exception as e:
    print('SunSpec or binascii packages did not import!')

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

class DeviceError(Exception):
    pass


class Device(object):

    def __init__(self, params=None, ts=None):
        self.ts = ts
        self.device = None
        self.data_points = list(data_points)

        self.comm = params.get('comm')
        if self.comm == 'Modbus TCP':
            self.ip_addr = params.get('ip_addr')
            self.ip_port = params.get('ip_port')
            self.ip_timeout = params.get('ip_timeout')
            self.slave_id = params.get('slave_id')

        self.open()

    def info(self):
        return 'DAS Hardware: Elspec G4420'

    def open(self):
        """
        Open the communications resources associated with the device.
        """
        try:
            self.device = client.ModbusClientDeviceTCP(slave_id=self.slave_id, ipaddr=self.ip_addr,
                                                       ipport=self.ip_port, timeout=self.ip_timeout)
        except Exception as e:
            raise DeviceError('Cannot connect to PM800: %s' % e)

    def close(self):
        self.device = None

    def data_capture(self, enable=True):
        pass

    def data_read(self):

        # Changed to the bulk read option to speed up acquisition time

        # freq = self.generic_float_read(999)

        #p1 = self.generic_float_read(1025)
        #p2 = self.generic_float_read(1027)
        #p3 = self.generic_float_read(1029)

        read_start = 999
        read_end = 1121 #2440
        data = self.bulk_float_read(start=read_start, end=read_end)

        freq_offset = 999 - read_start
        freq = util.data_to_float(data[freq_offset*2+0:freq_offset*2+4])

        p_offset = 1025 - read_start
        p1 = util.data_to_float(data[p_offset*2+0:p_offset*2+4])
        p2 = util.data_to_float(data[p_offset*2+4:p_offset*2+8])
        p3 = util.data_to_float(data[p_offset*2+8:p_offset*2+12])

        var_offset = 1041 - read_start
        var1 = util.data_to_float(data[var_offset*2+0:var_offset*2+4])
        var2 = util.data_to_float(data[var_offset*2+4:var_offset*2+8])
        var3 = util.data_to_float(data[var_offset*2+8:var_offset*2+12])

        v_offset = 1103 - read_start
        v1 = util.data_to_float(data[v_offset*2+0:v_offset*2+4])
        v2 = util.data_to_float(data[v_offset*2+4:v_offset*2+8])
        v3 = util.data_to_float(data[v_offset*2+8:v_offset*2+12])

        va_offset = 1057 - read_start
        va1 = util.data_to_float(data[va_offset*2+0:va_offset*2+4])
        va2 = util.data_to_float(data[va_offset*2+4:va_offset*2+8])
        va3 = util.data_to_float(data[va_offset*2+8:va_offset*2+12])

        i_offset = 1117 - read_start
        i1 = util.data_to_float(data[i_offset*2+0:i_offset*2+4])
        i2 = util.data_to_float(data[i_offset*2+4:i_offset*2+8])
        i3 = util.data_to_float(data[i_offset*2+8:i_offset*2+12])

        read_start = 3973 # Elspec unit rejects any read that includes 2441, so need to do a second read
        read_end = 3977
        data = self.bulk_float_read(start=read_start, end=read_end)

        pf_offset = 3973 - read_start
        pf1 = util.data_to_float(data[pf_offset*2+0:pf_offset*2+4])
        pf1 = -p1 / va1 * var1/abs(var1)
        pf2 = util.data_to_float(data[pf_offset*2+4:pf_offset*2+8])
        pf2 = -p2 / va2 * var2/abs(var2)
        pf3 = util.data_to_float(data[pf_offset*2+8:pf_offset*2+12])
        pf3 = -p3 / va3 * var3/abs(var3)

        '''data = self.bulk_float_read(start=3475, end=3479)
        pf1 = 1
        pf2 = 2
        pf3 = 3'''

        # 3 phase option
        datarec = {'TIME': time.time(),
                   'AC_VRMS_1': v1,
                   'AC_IRMS_1': i1,
                   'AC_P_1': p1,
                   'AC_S_1': va1,
                   'AC_Q_1': var1,
                   'AC_PF_1': pf1,
                   'AC_FREQ_1': freq,
                   'AC_VRMS_2': v2,
                   'AC_IRMS_2': i2,
                   'AC_P_2': p2,
                   'AC_S_2': va2,
                   'AC_Q_2': var2,
                   'AC_PF_2': pf2,
                   'AC_FREQ_2': freq,
                   'AC_VRMS_3': v3,
                   'AC_IRMS_3': i3,
                   'AC_P_3': p3,
                   'AC_S_3': va3,
                   'AC_Q_3': var3,
                   'AC_PF_3': pf3,
                   'AC_FREQ_3': freq,
                   'DC_V': None,
                   'DC_I': None,
                   'DC_P': None,
                   'TRIG': None,
                   'TRIG_GRID': None}

        data = []
        for chan in data_points:
            data.append(datarec[chan])

        return data

    def generic_float_read(self, reg):
        data = self.device.read(reg, 2, op=client.FUNC_READ_INPUT)
        data_num = util.data_to_float(data)
        return data_num

    def bulk_float_read(self, start=11700, end=11762):
        actual_start = start #- 1  # the register is one less than reported in the literature
        actual_length = (end - start) + 2
        data = self.device.read(actual_start, actual_length, op=client.FUNC_READ_INPUT)

        return data

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
    r1 = (reg)*2
    r2 = r1 + 4
    return r1, r2

def data_read():

        # Changed to the bulk read option to speed up acquisition time

        # freq = self.generic_float_read(999)

        #p1 = self.generic_float_read(1025)
        #p2 = self.generic_float_read(1027)
        #p3 = self.generic_float_read(1029)

        read_start = 999
        read_end = 1121 #2440
        data = bulk_float_read(start=read_start, end=read_end)

        freq_offset = 999 - read_start
        freq = util.data_to_float(data[freq_offset*2+0:freq_offset*2+4])

        p_offset = 1025 - read_start
        p1 = util.data_to_float(data[p_offset*2+0:p_offset*2+4])
        p2 = util.data_to_float(data[p_offset*2+4:p_offset*2+8])
        p3 = util.data_to_float(data[p_offset*2+8:p_offset*2+12])

        var_offset = 1041 - read_start
        var1 = util.data_to_float(data[var_offset*2+0:var_offset*2+4])
        var2 = util.data_to_float(data[var_offset*2+4:var_offset*2+8])
        var3 = util.data_to_float(data[var_offset*2+8:var_offset*2+12])

        v_offset = 1103 - read_start
        v1 = util.data_to_float(data[v_offset*2+0:v_offset*2+4])
        v2 = util.data_to_float(data[v_offset*2+4:v_offset*2+8])
        v3 = util.data_to_float(data[v_offset*2+8:v_offset*2+12])

        va_offset = 1057 - read_start
        va1 = util.data_to_float(data[va_offset*2+0:va_offset*2+4])
        va2 = util.data_to_float(data[va_offset*2+4:va_offset*2+8])
        va3 = util.data_to_float(data[va_offset*2+8:va_offset*2+12])

        i_offset = 1117 - read_start
        i1 = util.data_to_float(data[i_offset*2+0:i_offset*2+4])
        i2 = util.data_to_float(data[i_offset*2+4:i_offset*2+8])
        i3 = util.data_to_float(data[i_offset*2+8:i_offset*2+12])

        read_start = 3483 # Elspec unit rejects any read that includes 2441, so need to do a second read
        read_end = 3487
        data = bulk_float_read(start=read_start, end=read_end)

        pf_offset = 3483 - read_start
        pf1 = util.data_to_float(data[pf_offset*2+0:pf_offset*2+4])
        pf1 = -p1 / va1 * var1/abs(var1)
        pf2 = util.data_to_float(data[pf_offset*2+4:pf_offset*2+8])
        pf2 = -p2 / va2 * var2/abs(var2)
        pf3 = util.data_to_float(data[pf_offset*2+8:pf_offset*2+12])
        pf3 = -p3 / va3 * var3/abs(var3)

        '''data = self.bulk_float_read(start=3475, end=3479)
        pf1 = 1
        pf2 = 2
        pf3 = 3'''

        # 3 phase option
        datarec = {'TIME': time.time(),
                   'AC_VRMS_1': v1,
                   'AC_IRMS_1': i1,
                   'AC_P_1': p1,
                   'AC_S_1': va1,
                   'AC_Q_1': var1,
                   'AC_PF_1': pf1,
                   'AC_FREQ_1': freq,
                   'AC_VRMS_2': v2,
                   'AC_IRMS_2': i2,
                   'AC_P_2': p2,
                   'AC_S_2': va2,
                   'AC_Q_2': var2,
                   'AC_PF_2': pf2,
                   'AC_FREQ_2': freq,
                   'AC_VRMS_3': v3,
                   'AC_IRMS_3': i3,
                   'AC_P_3': p3,
                   'AC_S_3': va3,
                   'AC_Q_3': var3,
                   'AC_PF_3': pf3,
                   'AC_FREQ_3': freq,
                   'DC_V': None,
                   'DC_I': None,
                   'DC_P': None}

        return datarec

def generic_float_read(reg):
    data = device.read(reg, 2, op=client.FUNC_READ_INPUT)
    data_num = util.data_to_float(data)
    return data_num

def bulk_float_read(start=11700, end=11762):
    actual_start = start #- 1  # the register is one less than reported in the literature
    actual_length = (end - start) + 2
    data = device.read(actual_start, actual_length, op=client.FUNC_READ_INPUT)
    '''actual_start = start - 1  # the register is one less than reported in the literature
    actual_length = (end - start) + 2
    data = device.read(actual_start, actual_length, op=client.FUNC_READ_INPUT)'''
    return data

'''
Registers
999: Frequency
1025: Power 1
1027: Power 2
1029: Power 3
1041: Var 1
1043: Var 2
1045: Var 3
1057: VA 1
1059: VA 2
1061: VA 3
1103: V1
1105: V2
1107: V3
1117: I1
1119: I2
1121: I3
3475: PF1
3477: PF2
3479: PF3
'''

if __name__ == "__main__":

    ipaddr = '1.1.1.39'
    #ipaddr = str(raw_input('ip address: '))
    device = None

    if ipaddr:
        device = client.ModbusClientDeviceTCP(slave_id=159, ipaddr=ipaddr, ipport=502, timeout=10)#, trace_func=trace)

        data = device.read(1025, 2, op=client.FUNC_READ_INPUT)
        print((util.data_to_float(data)))
        data = device.read(1027, 2, op=client.FUNC_READ_INPUT)
        print((util.data_to_float(data)))
        data = device.read(1029, 2, op=client.FUNC_READ_INPUT)
        print((util.data_to_float(data)))

        print(('%s' % data_read()))
        print((data_read()['AC_P_1']))
        print((data_read()['AC_P_2']))
        print((data_read()['AC_P_3']))


