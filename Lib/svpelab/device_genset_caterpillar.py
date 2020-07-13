"""
Copyright (c) 2018, Sandia National Laboratories
All rights reserved.

V1.0 - Jay Johnson - 7/31/2018
"""

try:
    import sunspec.core.modbus.client as client
    import sunspec.core.util as suns_util
    import binascii
except Exception as e:
    print('SunSpec or binascii packages did not import!')
try:
    import numpy as np
except Exception as e:
    print('Error: numpy python package not found!')  # This will appear in the SVP log file.
    # raise  # programmers can raise this error to expose the error to the SVP user
try:
    from scapy.all import *
except Exception as e:
    print('Error: scapy file not found!')  # This will appear in the SVP log file.
    # raise  # programmers can raise this error to expose the error to the SVP user

class Device(object):

    def __init__(self, params=None, ts=None):
        self.ts = ts
        self.device = None
        self.sample_rate = params.get('util_ipaddr')
        self.n_cycles = params.get('util_ipport')
        self.n_cycles = params.get('util_slave_id')

    def param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):
        self.open()

    def open(self):
        ipaddr = self.param_value('ipaddr')
        ipport = self.param_value('ipport')
        slave_id = self.param_value('slave_id')

        self.genset = client.ModbusClientDeviceTCP(slave_id, ipaddr, ipport, timeout=5)

    def info(self):
        """ Get DER device information.

        Params:
            Manufacturer
            Model
            Version
            Options
            SerialNumber

        :return: Dictionary of information elements.
        """
        params = {'Manufacturer': 'Catepillar', 'Model': ''}
        return params

    def nameplate(self):
        """ Get nameplate ratings.

        Params:
            WRtg - Active power maximum rating
            VARtg - Apparent power maximum rating
            VArRtgQ1, VArRtgQ2, VArRtgQ3, VArRtgQ4 - VAr maximum rating for each quadrant
            ARtg - Current maximum rating
            PFRtgQ1, PFRtgQ2, PFRtgQ3, PFRtgQ4 - Power factor rating for each quadrant
            WHRtg - Energy maximum rating
            AhrRtg - Amp-hour maximum rating
            MaxChaRte - Charge rate maximum rating
            MaxDisChaRte - Discharge rate maximum rating

        :return: Dictionary of nameplate ratings.
        """

        params = {}
        params['WRtg'] = 225000.
        params['VARtg'] = 250000.
        params['VArRtgQ1'] = 250000.
        params['VArRtgQ4'] = 250000.
        return params

    def measurements(self):
        """ Get measurement data.

        Params:

        :return: Dictionary of measurement data.
        """

        params = {}
        return params

    def settings(self, params=None):
        """
        Get/set capability settings.

        Params:
            WMax - Active power maximum
            VRef - Reference voltage
            VRefOfs - Reference voltage offset
            VMax - Voltage maximum
            VMin - Voltage minimum
            VAMax - Apparent power maximum
            VArMaxQ1, VArMaxQ2, VArMaxQ3, VArMaxQ4 - VAr maximum for each quadrant
            WGra - Default active power ramp rate
            PFMinQ1, PFMinQ2, PFMinQ3, PFMinQ4
            VArAct

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for connect.
        """
        if params is not None:
            pass
        else:
            params = {}
        return params


    def conn_status(self, params=None):
        """ Get status of controls (binary True if active).
        :return: Dictionary of active controls.
        """
        if params is not None:
            pass
        else:
            params = {}
        return params


    def controls_status(self, params=None):
        """ Get status of controls (binary True if active).
        :return: Dictionary of active controls.
        """
        if params is not None:
            pass
        else:
            params = {}
        return params


    def reactive_power(self, params=None):
        """ Set the reactive power

        Params:
            Ena - Enabled (True/False)
            Q - Reactive power as %Qmax (positive is overexcited, negative is underexcited)
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for Q control.
        """
        if params is not None:
            if params['Q'] is not None:
                targ_q = params['Q']
                if 0 <= targ_q <= 30:
                    self.device.write(4729, suns_util.u16_to_data(int(targ_q)))
                else:
                    print('Genset target power out of range.')
                device.write(4729, suns_util.u16_to_data(0))
        else:
            params = {}
        return params

    def active_power(self, params=None):
        """ Get/set active power of EUT

        Params:
            Ena - Enabled (True/False)
            P - Active power in %Wmax (positive is exporting (discharging), negative is importing (charging) power)
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HFRT control.
        """
        if params is not None:
            if params['P'] is not None:
                targ_power = params['P']
                if 25 <= targ_power <= 150:
                    self.device.write(4790, suns_util.u16_to_data(int(targ_power)))
                else:
                    print('Genset target power out of range.')

        else:
            params = {}
            params['P'] = 25000
        return params


if __name__ == '__main__':
    # Wireshark captures: modbus.func_code == 6 & & ip.src == 192.168.0.100

    ipaddr = '192.168.0.1'
    device = client.ModbusClientDeviceTCP(slave_id=255, ipaddr=ipaddr, ipport=502, timeout=2)
    # Set power
    # device.write(4790, suns_util.u16_to_data(150))
    # set reactive power
    # device.write(4729, suns_util.u16_to_data(0))

    ipaddr = '192.168.0.33'
    reg_start = 50042
    modbus_read_length = 79
    device = client.ModbusClientDeviceTCP(slave_id=255, ipaddr=ipaddr, ipport=502, timeout=2)
    data = device.read(reg_start, modbus_read_length)
    print('Woodward 1 Data')
    for reg in range(modbus_read_length):
        data_point = suns_util.data_to_u16(data[reg*2:2+reg*2])
        print(('Register: %s = %s' % (reg+reg_start, data_point)))

    ipaddr = '192.168.0.1'
    reg_start = 50105
    modbus_read_length = 15
    device = client.ModbusClientDeviceTCP(slave_id=255, ipaddr=ipaddr, ipport=502, timeout=2)
    data = device.read(reg_start, modbus_read_length)
    print('\nWoodward 2 Data')
    for reg in range(modbus_read_length):
        data_point = suns_util.data_to_u16(data[reg*2:2+reg*2])
        print(('Register: %s = %s' % (reg+reg_start, data_point)))

    # sniff(count=10)
    # a = sniff(filter='port 502 && src 192.168.0.33 && dst 192.168.0.100', count=1, prn=lambda x: x.sprintf('Packet {} ==> {}'.format(x[0][1].src, x[0][1].dst)))
    # a.nsummary()
    # print(a[0].show())

