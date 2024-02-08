"""
Copyright (c) 2018, Sandia National Laboratories
All rights reserved.

This Modbus interface controls a ProSoft MVI46-MNET connected to a AB 5/05 SLC PLC

The ladder logic is built in a way so the control of these Modbus registers triggers different switching operations
for microgrid testing and other experiments.

V1.0 - Jay Johnson - 7/31/2018
"""

try:
    import sunspec.core.modbus.client as client
    import sunspec.core.util as suns_util
    import binascii
except Exception as e:
    print('SunSpec or binascii packages did not import!')
import time


class Device(object):

    def __init__(self, params=None, ts=None):
        self.ts = ts
        self.device = None
        self.ipaddr = params.get('ipaddr')
        self.ipport = params.get('ipport')
        self.slave_id = params.get('slave_id')
        self.reg = params.get('register')
        self.group_name = None

    def param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):
        self.open()

    def open(self):
        self.device = client.ModbusClientDeviceTCP(self.slave_id, self.ipaddr, self.ipport, timeout=5)

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
        params = {'Manufacturer': 'ProSoft', 'Model': 'MVI46-MNET'}

        # Registers:
        # 0: Reset
        # 1: Stop
        # 2: Islanding Request
        # 3: Utility Switch (button)
        # 4: Diesel Switch (button)
        # 5: Simulator Switch (button)

        return params

    def switch_open(self):
        """
        Open the switch associated with this device
        """
        self.device.write(self.reg, suns_util.u16_to_data(1))

    def switch_close(self):
        """
        Close the switch associated with this device
        """
        self.device.write(self.reg, suns_util.u16_to_data(0))

    def switch_state(self):
        """
        Get the state of the switch associated with this device
        """
        pass

    def reset_button(self, state=False):
        if state:
            self.device.write(0, suns_util.u16_to_data(1))
        else:
            self.device.write(0, suns_util.u16_to_data(0))

    def stop_button(self, state=True):
        """
        Note that upon power loss, all registers reset to 0, so B3:2/6 must reset to 1 for proper operation

        :param state: bool for "press the stop button"
        :return: None
        """
        # Stop button is nominally high (1) and goes low (0) when pressed
        if state:
            self.device.write(1, suns_util.u16_to_data(1))
        else:
            self.device.write(1, suns_util.u16_to_data(0))

    def islanding_button(self, state=False):
        if state:
            self.device.write(2, suns_util.u16_to_data(1))
        else:
            self.device.write(2, suns_util.u16_to_data(0))

    def utility_button(self, state=False):
        if state:
            self.device.write(3, suns_util.u16_to_data(1))
        else:
            self.device.write(3, suns_util.u16_to_data(0))

    def diesel_button(self, state=False):
        if state:
            self.device.write(4, suns_util.u16_to_data(1))
        else:
            self.device.write(4, suns_util.u16_to_data(0))

    def simulator_button(self, state=False):
        if state:
            self.device.write(5, suns_util.u16_to_data(1))
        else:
            self.device.write(5, suns_util.u16_to_data(0))

    def press_reset(self):
        self.reset_button(True)
        time.sleep(0.5)
        self.reset_button(False)

    def press_stop(self):
        self.stop_button(False)
        time.sleep(0.5)
        self.stop_button(True)

    def set_default_switch_mode(self):
        self.reset_button()
        self.stop_button()
        self.islanding_button()
        self.utility_button()
        self.diesel_button()
        self.simulator_button()


if __name__ == '__main__':

    ipaddr = '10.1.2.100'

    PLC = Device(params={'ipaddr': ipaddr, 'ipport': 502, 'slave_id': 1, 'register': 0})
    PLC.config()
    PLC.set_default_switch_mode()

    # PLC.stop_button(state=False)
    # PLC.utility_button(False)
    # PLC.diesel_button(False)

    # device = client.ModbusClientDeviceTCP(slave_id=1, ipaddr=ipaddr, ipport=502, timeout=2)
    # Read Modbus registers
    # reg_start = 100
    # modbus_read_length = 10
    # data = device.read(reg_start, modbus_read_length)
    # for reg in range(modbus_read_length):
    #     data_point = suns_util.data_to_u16(data[reg*2:2+reg*2])
    #     print('Register: %s = %s' % (reg+reg_start, data_point))
    #
    # for i in range(4):
    #     # Write Modbus Register
    #     device.write(0, suns_util.u16_to_data(1))
    #     time.sleep(2)
    #     device.write(0, suns_util.u16_to_data(0))
    #
    #     device.write(1, suns_util.u16_to_data(1))
    #     time.sleep(2)
    #     device.write(1, suns_util.u16_to_data(0))
    #
    #     device.write(2, suns_util.u16_to_data(1))
    #     time.sleep(2)
    #     device.write(2, suns_util.u16_to_data(0))
    #
    #     device.write(3, suns_util.u16_to_data(1))
    #     time.sleep(2)
    #     device.write(3, suns_util.u16_to_data(0))
    #
    #     device.write(4, suns_util.u16_to_data(1))
    #     time.sleep(2)
    #     device.write(4, suns_util.u16_to_data(0))
