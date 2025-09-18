"""
Driver for the SCPI interface for NH Research, Inc. 9200 and 9300 Battery Simulators
"""

import os
from svpelab import device_battsim_nhr as batt
from . import battsim

nhr_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'NHR'
}

def battsim_info():
    return nhr_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = nhr_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)

    info.param(pname('ipaddr'), label='IP Address', default='10.1.2.181')
    info.param(pname('overvoltage'), label='Overvoltage Protection Level (V)', default=64.0)
    info.param(pname('overcurrent'), label='Overcurrent Protection Level (A)', default=150.0)
    info.param(pname('max_power'), label='Maximum Power (W)', default=8000.0)

    info.param(pname('voltage'), label='Voltage (V)', default=54.0)
    info.param(pname('current'), label='Current (A)', default=150.0)
    info.param(pname('power'), label='Power (W)', default=8000.0)
    info.param(pname('resistance'), label='Resistance (Ohm)', default=0.005)

GROUP_NAME = 'nhr'


class BattSim(battsim.BattSim):

    def __init__(self, ts, group_name, support_interfaces=None):
        # todo: add support_interfaces like PVSim
        battsim.BattSim.__init__(self, ts, group_name)

        self.ts = ts
        self.pmod = None
        self.support_interfaces = support_interfaces

        try:
            self.ipaddr = self._param_value('ipaddr')
            self.overvoltage = self._param_value('overvoltage')
            self.overcurrent = self._param_value('overcurrent')
            self.max_power = self._param_value('max_power')
            self.voltage = self._param_value('voltage')
            self.current = self._param_value('current')
            self.power = self._param_value('power')
            self.resistance = self._param_value('resistance')

            self.pmod = batt.NHResearch(ipaddr=self.ipaddr)

            self.pmod.set_battery_detect_voltage(bd_voltage=0.0)

            safety_vals = {'Min V': 0.0, 'Min V Time': 0.0,
                           'Max V': self.overvoltage, 'Max V Time': 0.005,
                           'Max Sink A': self.overcurrent, 'Max Sink A Time': 0.005,
                           'Max Source A': self.overcurrent, 'Max Source A Time': 0.005,
                           'Max Sink W': self.max_power, 'Max Sink W Time': 0.005,
                           'Max Source W': self.max_power, 'Max Source W Time': 0.005,
                           'Max Temperature': -1.0}
            self.pmod.set_safety(safety_dict=safety_vals)

            self.pmod.set_output_on()

            op_mode = {'enable': ['VOLTAGE_ENABLED', 'CURRENT_ENABLED', 'POWER_ENABLED', 'RESISTANCE_ENABLED'],
                       'voltage': self.voltage,
                       'current': self.current,
                       'power': self.power,
                       'resistance': self.resistance}
            self.pmod.set_operational_mode(op_mode=op_mode)

        except Exception:
            if self.pmod is not None:
                self.pmod.close()
            raise

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def close(self):
        if self.pmod is not None:
            self.pmod.close()
            self.pmod = None

    def info(self):
        return self.pmod.info()

    def measurements_get(self):
        """
        Measure the voltage, current, and power

        :return: dictionary with dc power data with keys: 'DC_V', 'DC_I', 'DC_P'
        """

        if self.pmod is not None:
            # spread across active channels
            meas = self.pmod.measure_all()
            total_meas = {'DC_V': meas['Voltage'], 'DC_I': meas['Current'], 'DC_P': meas['Power']}
            return total_meas
        else:
            raise battsim.BattSimError('Not initialized')

    def measure_power(self):
        """
        Get the current, voltage, and power from the NHR
        returns: dictionary with power data with keys: 'DC_V', 'DC_I', and 'DC_P'
        """
        if self.pmod is not None:
            return self.measurements_get()
        else:
            raise battsim.BattSimError('Not initialized')

    def power_set(self, power):
        if self.pmod is not None:
            if self.pmod.get_safety()['Max Source W'] > power:
                self.pmod.set_operational_mode(op_mode={'power': float(power)})
            else:
                self.ts.log_error('Cannot change power because Max Source W is too low.')
        else:
            raise battsim.BattSimError('Not initialized')

    def power_on(self):
        if self.pmod is not None:
            self.pmod.set_output_on()
        else:
            raise battsim.BattSimError('Not initialized')

    def power_off(self):
        if self.pmod is not None:
            self.pmod.set_output_on()
        else:
            raise battsim.BattSimError('Not initialized')

    # profiles
    def profile_load(self, profile_name):
        pass

    def profile_start(self):
        pass

    def profile_stop(self):
        pass


    def clear_faults(self):
        """
        Clear overvoltage and overcurrent faults on the channels
        """
        if self.pmod is not None:
            self.pmod.clear()

    # Solar functions
    def iv_curve_config(self, pmp, vmp):
        pass

    def irradiance_set(self, irradiance=1000):
        pass

if __name__ == "__main__":
    pass