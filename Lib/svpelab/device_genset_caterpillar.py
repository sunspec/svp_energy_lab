"""
Copyright (c) 2021, Sandia National Laboratories
All rights reserved.

V1.2 - Jay Johnson - 7/31/2018
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

GROUP_NAME = 'cat_genset'

class Device(object):

    def __init__(self, params=None, ts=None):
        self.ts = ts
        self.group_name = 'genset'
        self.data_ipaddr = params.get('data_ipaddr')
        self.data_ipport = params.get('data_ipport')
        self.data_slave_id = params.get('data_slave_id')
        self.ctrl_ipaddr = params.get('cntl_ipaddr')
        self.ctrl_ipport = params.get('cntl_ipport')
        self.ctrl_slave_id = params.get('cntl_slave_id')

        self.data_reg_start = 50042
        self.data_modbus_read_length = 79
        self.data_device = client.ModbusClientDeviceTCP(slave_id=self.data_slave_id, ipaddr=self.data_ipaddr,
                                                        ipport=self.data_ipport, timeout=2)

        self.ctrl_reg_start = 50105
        self.ctrl_modbus_read_length = 15
        self.ctrl_device = client.ModbusClientDeviceTCP(slave_id=self.ctrl_slave_id, ipaddr=self.ctrl_ipaddr,
                                                        ipport=self.ctrl_ipport, timeout=2)

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
        data = self.data_device.read(self.data_reg_start, self.data_modbus_read_length)

        reg_start = self.data_reg_start
        for reg in range(self.data_modbus_read_length):
            data_point = suns_util.data_to_u16(data[reg * 2:2 + reg * 2])
            # print('Register: %s = %s' % (reg + reg_start, data_point))
            if (reg + reg_start) == 50061:
                params['Utility_V1'] = data_point
            if reg + reg_start == 50062:
                params['Utility_V2'] = data_point
            if reg + reg_start == 50063:
                params['Utility_V3'] = data_point
            if reg + reg_start == 50064:
                params['Utility_V4'] = data_point
            if reg + reg_start == 50080:
                params['Generator_V5'] = data_point
            if reg + reg_start == 50120:
                params['Generator_V7'] = data_point

            if reg + reg_start == 50073:
                params['Utility_F1'] = data_point
            if reg + reg_start == 50081:
                params['Generator_F2'] = data_point

            if reg + reg_start == 50069:
                params['Utility_I1'] = data_point
            if reg + reg_start == 50070:
                params['Utility_I2'] = data_point
            if reg + reg_start == 50071:
                params['Utility_I3'] = data_point
            if reg + reg_start == 50072:
                params['Utility_I4'] = data_point

            if reg + reg_start == 50059:
                params['Utility_kW'] = data_point

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
            reg_start = self.ctrl_reg_start

            data = self.ctrl_device.read(self.ctrl_reg_start, self.ctrl_modbus_read_length)
            print(data)

            for reg in range(self.ctrl_modbus_read_length):
                # print('Register: %s = %s' % (reg + reg_start, data[reg * 2:2 + reg * 2]))
                try:
                    data_point = suns_util.data_to_u16(data[reg * 2:2 + reg * 2])
                    print('Register: %s = %s' % (reg + reg_start, data_point))
                except Exception as e:
                    print('Warning: %s' % e)
            # data = self.ctrl_device.read(4790, 2)
            # print('Power: %s' % suns_util.data_to_u16(data))
            #
            # data = self.ctrl_device.read(4729, 2)
            # print('Power: %s' % suns_util.data_to_s16(data))

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
                if 0 <= targ_q <= 50:
                    self.ctrl_device.write(4729, suns_util.u16_to_data(int(targ_q)))
                else:
                    print('Genset target reative power out of range.')
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
                if 0 <= targ_power <= 150:
                    self.ctrl_device.write(4790, suns_util.u16_to_data(int(targ_power)))
                else:
                    print('Genset target power out of range.')
        else:
            params = {}
            params['P'] = 25000
        return params


if __name__ == '__main__':
    '''
    192.168.0.1 - MAC Address: 00:12:8C:00:3C:B2 (Woodward Governor) - Control
    192.168.0.33 - MAC Address: 00:12:8C:00:40:C2 (Woodward Governor) - Data
    192.168.0.61 - MAC Address: 00:12:8C:00:40:60 (Woodward Governor)
    192.168.0.100 - MAC Address: 00:01:23:1C:13:F0 (Digital Electronics)
        6000/tcp open  X11
        6001/tcp open  X11:1
    192.168.0.128 - MAC Address: 00:A0:45:35:A3:C0 (Phoenix Contact Electronics Gmbh)
        21/tcp open  ftp
        80/tcp open  http
    '''

    # params = {'data_ipaddr': '192.168.0.33',
    #           'data_ipport': 502,
    #           'data_slave_id': 0,
    #           'cntl_ipaddr': '192.168.0.1',
    #           'cntl_ipport': 502,
    #           'cntl_slave_id': 0,
    #           }

    params = {'data_ipaddr': '10.1.13.32',
              'data_ipport': 502,
              'data_slave_id': 0,
              'cntl_ipaddr': '10.1.13.31',
              'cntl_ipport': 502,
              'cntl_slave_id': 0,
              }

    genset = Device(params=params)

    # print(genset.controls_status())
    # for i in range(10):
    #     print(genset.active_power(params={'P': 25}))
    # print(genset.reactive_power(params={'Q': 35}))
    # time.sleep(1)
    # print(genset.controls_status())
    # print(genset.active_power(params={'P': 45}))
    # print(genset.reactive_power(params={'Q': 15}))
    # time.sleep(1)
    # print(genset.controls_status())

    for i in range(5):
        print(genset.measurements())
        time.sleep(1)

    print(genset.active_power(params={'P': 45}))
    print(genset.reactive_power(params={'Q': 15}))

    # ABB PLC
    # ipaddr = '172.22.61.102'
    # reg_start = 1161
    # modbus_read_length = 1
    # device = client.ModbusClientDeviceTCP(slave_id=0, ipaddr=ipaddr, ipport=502, timeout=2)
    # data = device.read(reg_start, modbus_read_length)
    # print('\nABB PCS Data')
    # for reg in range(modbus_read_length):
    #     data_point = suns_util.data_to_u16(data[reg*2:2+reg*2])
    #     print(('Register: %s = %s' % (reg+reg_start, data_point)))

    # '3.12.25.R'
    # ipaddr = '10.1.13.4'
    # reg_start = 1161
    # modbus_read_length = 1
    # device = client.ModbusClientDeviceTCP(slave_id=3, ipaddr=ipaddr, ipport=502, timeout=2)
    # data = device.read(reg_start, modbus_read_length)
    # print('\nSMA Data')
    # for reg in range(modbus_read_length):
    #     data_point = suns_util.data_to_u16(data[reg*2:2+reg*2])
    #     print(('Register: %s = %s' % (reg+reg_start, data_point)))


    # ipaddr = '10.1.2.28'
    # reg_start = 2
    # modbus_read_length = 30
    # device = client.ModbusClientDeviceTCP(slave_id=1, ipaddr=ipaddr, ipport=5000, timeout=2)
    # data = device.read(reg_start, modbus_read_length)
    # print('\nRTAC Data')
    # for reg in range(modbus_read_length):
    #     data_point = suns_util.data_to_u16(data[reg*2:2+reg*2])
    #     print(('Register: %s = %s' % (reg+reg_start, data_point)))
    # device.write(8, suns_util.s16_to_data(-25))  # Real Power
    # device.write(9, suns_util.s16_to_data(-10))  # Reactive Power

    # opal_sim_pts = {
    #     'CB101 Switch': {'Name': 'CB101', 'Port': 501},
    #     'CB102 Switch': {'Name': 'CB102', 'Port': 502},
    #     'CB103 Switch': {'Name': 'CB106', 'Port': 503},
    #     'CB104 Switch': {'Name': 'CB104', 'Port': 504},
    #     'CB105 Switch': {'Name': 'CB105', 'Port': 505},
    #     'CB106 Switch': {'Name': 'CB106', 'Port': 506},
    #     'CB107 Switch': {'Name': 'CB107', 'Port': 507},
    #     'BUS101-Switch 4': {'Name': 'CB108', 'Port': 508},
    #     'Gen_2': {'Name': 'GEN 2 (BUS103)', 'Port': 500},
    #     'CB110 Switch': {'Name': 'CB110', 'Port': 510},
    #     'CB114 Switch': {'Name': 'CB114', 'Port': 511},
    #     'BUS106-Switch 1': {'Name': 'CB109', 'Port': 509},
    # }
    #
    # name = 'CB106 Switch'
    # ipaddr = '10.1.2.3'
    # reg_start = 2
    # modbus_read_length = 30
    # device = client.ModbusClientDeviceTCP(slave_id=1, ipaddr=ipaddr, ipport=500, timeout=2)
    # data = device.read(reg_start, modbus_read_length)
    # print('\nRTAC Data')
    # for reg in range(modbus_read_length):
    #     data_point = suns_util.data_to_u16(data[reg*2:2+reg*2])
    #     print(('Register: %s = %s' % (reg+reg_start, data_point)))

    # Genset
    # ipaddr = '192.168.0.1'
    # device = client.ModbusClientDeviceTCP(slave_id=0, ipaddr=ipaddr, ipport=502, timeout=2)
    #
    # device.write(4790, suns_util.u16_to_data(75))  # Set power
    # device.write(4729, suns_util.u16_to_data(35))  # set reactive power

    # ipaddr = '192.168.0.33'
    # reg_start = 50042
    # modbus_read_length = 79
    # device = client.ModbusClientDeviceTCP(slave_id=255, ipaddr=ipaddr, ipport=502, timeout=2)
    # data = device.read(reg_start, modbus_read_length)
    # print('Woodward 1 Data')
    # for reg in range(modbus_read_length):
    #     data_point = suns_util.data_to_u16(data[reg*2:2+reg*2])
    #     print(('Register: %s = %s' % (reg+reg_start, data_point)))

    # ipaddr = '192.168.0.1'
    # reg_start = 50105
    # modbus_read_length = 15
    # device = client.ModbusClientDeviceTCP(slave_id=255, ipaddr=ipaddr, ipport=502, timeout=2)
    # data = device.read(reg_start, modbus_read_length)
    # print('\nWoodward 2 Data')
    # for reg in range(modbus_read_length):
    #     data_point = suns_util.data_to_u16(data[reg*2:2+reg*2])
    #     print(('Register: %s = %s' % (reg+reg_start, data_point)))

    # Wireshark captures: modbus.func_code == 6 & & ip.src == 192.168.0.100
    # sniff(count=10)
    # a = sniff(filter='port 502 && src 192.168.0.33 && dst 192.168.0.100', count=1, prn=lambda x: x.sprintf('Packet {} ==> {}'.format(x[0][1].src, x[0][1].dst)))
    # a.nsummary()
    # print(a[0].show())

