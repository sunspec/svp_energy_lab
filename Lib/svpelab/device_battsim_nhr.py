"""
Driver for the SCPI interface for NH Research, Inc. 9200 and 9300 Battery Simulators
"""

import pyvisa
import numpy as np


MODES = {
    'OFF_MODE':'0',
    'STANDBY_MODE':'1',
    'CHARGE_MODE':'2',
    'DISCHARGE_MODE':'3',
    'BATTERY_MODE':'4',
    '0':'OFF_MODE',
    '1':'STANDBY_MODE',
    '2':'CHARGE_MODE',
    '3':'DISCHARGE_MODE',
    '4':'BATTERY_MODE'
}

VOLTAGE_ENABLED = 0  # bit for 1
CURRENT_ENABLED = 1  # bit for 2
POWER_ENABLED = 2  # bit for 4
RESISTANCE_ENABLED = 3  # bit for 8

class NHResearchError(Exception):
    pass


class NHResearch(object):

    def __init__(self, ipaddr='127.0.0.1', ipport=5025, timeout=5):
        self.ipaddr = ipaddr
        self.ipport = ipport
        self.timeout = timeout
        self.buffer_size = 1024
        self.conn = None
        self.rm = pyvisa.ResourceManager()
        resource_loc = 'TCPIP::%s::INSTR' % ipaddr
        self.pmod = self.rm.open_resource(resource_loc)  # power module
        self.clear()
        self.current_sign()

    def cmd(self, cmd_str):
        try:
            self.pmod.write(cmd_str)

            # returns the next error number followed by its corresponding error message string
            resp = self.pmod.query('SYSTem:ERRor?').strip()
            if resp != '0,"No error"':
                print('Error with command %s: %s' % (cmd_str, resp))

        except Exception as e:
            raise NHResearchError(str(e))

        return resp

    def query(self, cmd_str):
        try:
            resp = self.pmod.query(cmd_str).strip()
        except Exception as e:
            raise NHResearchError(str(e))

        return resp

    def info(self):
        return self.query('*IDN?')

    def reset(self):
        return self.cmd('*RST')

    def close(self):
        try:
            if self.pmod is not None:
                self.pmod.close()
        except Exception as e:
            pass
        finally:
            self.conn = None

    def clear(self):
        """
        Clears all event status registers and queues
        """
        return self.cmd('*CLS')

    def status(self):
        """
        Status Byte Register
        0* Busy         Module is busy and NOT able to process any command      0x01
        1* Remote       Module is in remote mode                                0x02
        2* Error Queue  Error in queue, use SYST:ERR?                           0x04
        3  QUES         Questionable status summary.                            0x08
        4  MAV          Message available                                       0x10
        5  ESB          Event status byte summary. See event status register.   0x20
        6  RQS          Request for service.                                    0x40
        7  OPER         Operation event summary. See operation event register.  0x80

        Event Status Register
        0  OPC          Operation Complete                                      0x01
        1  RQC          Request Control                                         0x02
        2  QYE          Query Error                                             0x04
        3  DDE          Device Dependent Error                                  0x08
        4  EXE          Execution Error                                         0x10
        5  CME          Command Error                                           0x20
        6  URQ          User Request                                            0x40
        7  PON          Power On                                                0x80

        Operation Register - instrument specific, (see STATus:OPERation[:EVENt]?
        TODO

        Questionable Status Register (see STATus:QUEStionable[:EVENt]?)
        TODO

        :return: dict with status
        """
        decimal = int(self.query('*STB?'))
        flags = {}
        if (decimal & (1 << 0)) == (1 << 0):
            flags['Busy'] = 'True'
        if (decimal & (1 << 1)) == (1 << 1):
            flags['Remote'] = 'True'
        if (decimal & (1 << 2)) == (1 << 2):
            flags['Error Queue'] = 'True'
        if (decimal & (1 << 3)) == (1 << 3):
            flags['Questionable status'] = 'True'
        if (decimal & (1 << 4)) == (1 << 4):
            flags['Message available'] = 'True'
        if (decimal & (1 << 5)) == (1 << 5):
            flags['Event status byte summary'] = 'True'
        if (decimal & (1 << 6)) == (1 << 6):
            flags['Request for service'] = 'True'
        if (decimal & (1 << 7)) == (1 << 7):
            flags['Operation event summary'] = 'True'

        decimal = int(self.query('*ESR?'))
        if (decimal & (1 << 0)) == (1 << 0):
            flags['Operation Complete'] = 'True'
        if (decimal & (1 << 1)) == (1 << 1):
            flags['Request Control'] = 'True'
        if (decimal & (1 << 2)) == (1 << 2):
            flags['Query Error'] = 'True'
        if (decimal & (1 << 3)) == (1 << 3):
            flags['Device Dependent Error '] = 'True'
        if (decimal & (1 << 4)) == (1 << 4):
            flags['Execution Error'] = 'True'
        if (decimal & (1 << 5)) == (1 << 5):
            flags['Command Error'] = 'True'
        if (decimal & (1 << 6)) == (1 << 6):
            flags['User Request'] = 'True'
        if (decimal & (1 << 7)) == (1 << 7):
            flags['Power On'] = 'True'

        return flags

    def self_test(self):
        if self.query('*TST?') == '0':
            return 'No Errors'

    def wait(self):
        return self.cmd('*WAI')

    def current_sign(self, der_ref=1):
        """
        This command sets or reads the desired current sign. TRUE will return negative current that is charging,
        FALSE will return negative current that is discharging.

        DER reference point will have a negative current when charging, so this value should be set to 1

        :param der_ref: 0 or 1 for False or True
        :return:
        """
        if der_ref not in [0, 1]:
            raise NHResearchError('Setting current direction without correct input')

        return self.cmd('CONFigure:CINegative %s' % der_ref)

    def dsp_version(self):
        return self.query('DIAGnostic:DL:VERSion?')

    def scpi_version(self):
        return self.query('SYSTem:VERSion?')

    def set_local(self):
        """
        This command places the module in local mode during SCPI operation. The front panel keys are functional.
        """
        return self.cmd('SYSTem:LOCal')

    def set_remote(self):
        return self.cmd('SYSTem:REMote')

    def current_ranges(self):
        ivals = {}
        # These queries will retrieve the absolute minimum and maximum aperture setting for the Module.
        ivals['i_min'] = self.query('INSTrument:CAPabilities:APERture:MINimum?')
        ivals['i_max'] = self.query('INSTrument:CAPabilities:APERture:MAXimum?')

        # These queries will retrieve the absolute minimum and maximum current setting for the Module.
        ivals['i_charge_min'] = self.query('INSTrument:CAPabilities:CURRent:CHARge:MINimum?')
        ivals['i_charge_max'] = self.query('INSTrument:CAPabilities:CURRent:CHARge:MAXimum?')

        # These queries will retrieve the range’s maximum current setting for the Module.
        ivals['i_charge_range_max'] = self.query('INSTrument:CAPabilities:CURRent:CHARge:RANGe:MAXimum?')

        # These queries will retrieve the absolute minimum and maximum current setting for the Module.
        ivals['i_discharge_min'] = self.query('INSTrument:CAPabilities:CURRent:DISCharge:MINimum?')
        ivals['i_discharge_max'] = self.query('INSTrument:CAPabilities:CURRent:DISCharge:MAXimum?')

        # These queries will retrieve the range’s maximum current setting for the Module.
        ivals['i_discharge_range_max'] = self.query('INSTrument:CAPabilities:CURRent:DISCharge:RANGe:MAXimum?')

        # These queries will retrieve the absolute minimum and maximum currents for measuring.
        ivals['i_meas_min'] = self.query('INSTrument:CAPabilities:CURRent:MEASurement:MINimum?')
        ivals['i_meas_max'] = self.query('INSTrument:CAPabilities:CURRent:MEASurement:MAXimum?')

        # These queries will retrieve the range’s maximum currents for measuring.
        ivals['i_meas_range_max'] = self.query('INSTrument:CAPabilities:CURRent:MEASurement:RANGe:MAXimum?')

        # These queries will retrieve the absolute minimum and maximum current slew rate for the Module.
        ivals['i_slew_min'] = self.query('INSTrument:CAPabilities:CURRent:SLEW:MINimum?')
        ivals['i_slew_max'] = self.query('INSTrument:CAPabilities:CURRent:SLEW:MAXimum?')

        # These queries will retrieve the range’s minimum and maximum current slew rate for the Module.
        ivals['i_slew_range_min'] = self.query('INSTrument:CAPabilities:CURRent:SLEW:RANGe:MINimum?')
        ivals['i_slew_range_max'] = self.query('INSTrument:CAPabilities:CURRent:SLEW:RANGe:MAXimum?')

        return ivals

    def power_ranges(self):
        pvals = {}
        # These queries will retrieve the absolute minimum and maximum power setting for the Module.
        pvals['p_charge_min'] = self.query('INSTrument:CAPabilities:POWer:CHARge:MINimum?')
        pvals['p_charge_max'] = self.query('INSTrument:CAPabilities:POWer:CHARge:MAXimum?')

        # These queries will retrieve the absolute minimum and maximum power setting for the Module.
        pvals['p_discharge_min'] = self.query('INSTrument:CAPabilities:POWer:DISCharge:MINimum?')
        pvals['p_discharge_max'] = self.query('INSTrument:CAPabilities:POWer:DISCharge:MAXimum?')

        # These queries will retrieve the absolute minimum and maximum power slew rate for the Module.
        pvals['p_slew_min'] = self.query('INSTrument:CAPabilities:POWer:SLEW:MINimum?')
        pvals['p_slew_max'] = self.query('INSTrument:CAPabilities:POWer:SLEW:MAXimum?')

        return pvals

    def voltage_ranges(self):
        vvals = {}
        # These queries will retrieve the absolute minimum and maximum voltage setting for the Module.
        vvals['v_min'] = self.query('INSTrument:CAPabilities:VOLT:MINimum?')
        vvals['v_max'] = self.query('INSTrument:CAPabilities:VOLT:MAXimum?')

        # This query will retrieve the range’s maximum voltage setting for the Module.
        vvals['v_range_max'] = self.query('INSTrument:CAPabilities:VOLT:RANGe:MAXimum?')

        # These queries will retrieve the absolute minimum and maximum voltages for measuring.
        vvals['v_meas_min'] = self.query('INSTrument:CAPabilities:VOLT:MEASurement:MINimum?')
        vvals['v_meas_max'] = self.query('INSTrument:CAPabilities:VOLT:MEASurement:MAXimum?')
        vvals['v_meas_range_max'] = self.query('INSTrument:CAPabilities:VOLT:MEASurement:RANGe:MAXimum?')

        # These queries will retrieve the absolute minimum and maximum voltage slew rate for the Module.
        vvals['v_slew_min'] = self.query('INSTrument:CAPabilities:VOLT:SLEW:MINimum?')
        vvals['v_slew_max'] = self.query('INSTrument:CAPabilities:VOLT:SLEW:MAXimum?')

        # These queries will retrieve the range’s minimum and maximum voltage slew rate for the Module.
        vvals['v_slew_range_min'] = self.query('INSTrument:CAPabilities:VOLT:SLEW:RANGe:MINimum?')
        vvals['v_slew_range_max'] = self.query('INSTrument:CAPabilities:VOLT:SLEW:RANGe:MAXimum?')

        return vvals

    def resistance_ranges(self):
        rvals = {}
        # These queries will retrieve the absolute minimum and maximum resistance setting for the Module.
        rvals['r_min'] = self.query('INSTrument:CAPabilities:RESistance:MINimum?')
        rvals['r_max'] = self.query('INSTrument:CAPabilities:RESistance:MAXimum?')

        # These queries will retrieve the range’s minimum and maximum resistance setting for the Module.
        rvals['r_range_min'] = self.query('INSTrument:CAPabilities:RESistance:RANGe:MINimum?')
        rvals['r_range_max'] = self.query('INSTrument:CAPabilities:RESistance:RANGe:MAXimum?')

        # These queries will retrieve the absolute minimum and maximum resistance slew rate for the Module.
        rvals['r_slew_min'] = self.query('INSTrument:CAPabilities:RESistance:SLEW:RANGe:MINimum?')
        rvals['r_slew_max'] = self.query('INSTrument:CAPabilities:RESistance:SLEW:RANGe:MAXimum?')

        return rvals

    def gain_ranges(self):
        gvals = {}
        # These queries will retrieve the absolute minimum and maximum legal values for regulation gain and the nominal
        # (default) value.
        gvals['reg_gain_min'] = self.query('INSTrument:CAPabilities:RGAin:MINimum?')
        gvals['reg_gain_nom'] = self.query('INSTrument:CAPabilities:RGAin:NOMinal?')
        gvals['reg_gain_max'] = self.query('INSTrument:CAPabilities:RGAin:MAXimum?')
        return gvals


    def abort(self, timeout=2):
        """
        This command resets the list and measurement trigger systems to the Idle state. Any list or measurement that
        is in progress is immediately aborted. ABORt also resets the WTG bit in the Operation Condition Status register.

        :return:
        """
        try:
            return self.cmd('ABORt')
        except NHResearchError:
            print('Abort failure')
            raise

    def measurements_get(self):
        """
        Measure the voltage, current, and power of the Module

        The input voltage and current are digitized whenever a measure command is given or whenever an acquire
        (INIT) trigger occurs. The capture aperture is set by SENSe:SWEep:APERture.

        MEAS:VOLT? // starts acquisition sequence then returns the voltage calculated during the acquisition.
        FETCH:CURR? // returns the current calculated during the SAME acquisition as voltage.
        FETCH:POW? // returns the power calculated during the SAME acquisition as voltage.

        :return: dictionary with power data with keys: 'DC_V', 'DC_I', 'DC_P'
        """
        meas = {'DC_V': float(self.query('MEAS:VOLT?')),
                'DC_I': float(self.query('FETCH:CURR?')),
                'DC_P': float(self.query('FETCH:POW?'))}
        return meas

    def measure_all(self):
        """
        This query returns the most recent measurements that are always being made by the hardware in the background
        (except while a waveform capture is being made).

        :return: dict with data
        """

        str_data = self.query('FETCh:BACKground:ALL?')
        data = [float(i) for i in str_data.split(',')]
        # print(data)
        # print(len(data))
        data_dict = {'Voltage': data[0],
                     'Current': data[1],
                     'Power': data[2],
                     'Ah Total': data[3],
                     'Ah Charge': data[4],
                     'Ah Discharge': data[5],
                     'Ah Time': data[6],
                     'kWA Total': data[7],
                     'kWA Charge': data[8],
                     'kWA Discharge': data[9],
                     'kWA Time': data[10],
                     'Charge Time': data[11],
                     'Discharge Time': data[12],
                     'VoltageNegativePeak': data[13],
                     'VoltagePositivePeak': data[14],
                     'CurrentNegativePeak': data[15],
                     'CurrentPositivePeak': data[16],
                     'PowerNegativePeak': data[17],
                     'PowerPositivePeak': data[18],
                     'Timestamp': data[19],
                     }

        return data_dict

    def measure_peaks(self):
        """
        This query returns the most recent measurements that are always being made by the hardware in the background
        (except while a waveform capture is being made).

        :return: dict with data
        """

        str_data = self.query('FETCh:BACKground:PEAKs?')
        data = [float(i) for i in str_data.split(',')]
        # print(data)
        # print(len(data))
        data_dict = {'VoltageNegativePeak': data[0],
                     'VoltagePositivePeak': data[1],
                     'CurrentNegativePeak': data[2],
                     'CurrentPositivePeak': data[3],
                     'PowerNegativePeak': data[4],
                     'PowerPositivePeak': data[5]
                     }

        return data_dict

    def measure_temp(self):
        """
        Applies to 9300 ONLY.

        This query returns the most recent UUT temperature measurements that are always being made by the hardware in the
        background (except while a waveform capture is being made). Temperature is degrees centigrade.

        :return: float, temp in C
        """

        return float(self.query('FETCh:BACKground:TEMP?'))

    def waverform_capture(self):
        """
        These queries return an array containing the instantaneous input voltage. The array starts at index 0 if
        none is specified, otherwise it starts at the start index.  Waveforms are captured with every initiated
        measurement based on the SENSe:SWEep:APERture, SENSe:SWEep:POINts, and SENSe:SWEep:TINTerval commands.

        :return: dict, with voltage, current, and time lists
        """

        self.cmd('INIT')  # This command starts the measurement aperture.

        sample_rate = self.get_sample_rate()  #SENSe:SWEep:APERture
        sample_duration = self.get_aperture()  # SENSe:SWEep:TINTerval
        n_samples = self.get_max_samples()  # SENSe:SWEep:POINts
        print('sample_rate = %s, sample_duration = %s, n_samples = %s' % (sample_rate, sample_duration, n_samples))

        # v_str += self.query('MEASure:ARRay:VOLTage?')  # This would start a new sample
        v_array = []
        index = 0
        more_data = True
        while more_data:
            data = self.query('FETCh:ARRay:VOLTage? %s' % index)
            # print(data)
            if data.strip() == '<ERROR -222>' or data.strip() == '3.40282347e+38' or index > n_samples:
                # print('Ending loop at index = %d' % index)
                more_data = False
            else:
                v_array += [float(i) for i in data.split(',')]
                index = len(v_array)  # e.g., if returning 3 values, start at index 3 next time
        # print(len(v_array))

        i_array = []
        index = 0
        more_data = True
        while more_data:
            data = self.query('FETCh:ARRay:VOLTage? %s' % index)
            # print(data)
            if data.strip() == '<ERROR -222>' or data.strip() == '3.40282347e+38' or index > n_samples:
                # print('Ending loop at index = %d' % index)
                more_data = False
            else:
                i_array += [float(i) for i in data.split(',')]
                index = len(i_array)  # e.g., if returning 3 values, start at index 3 next time
        # print(len(v_array))

        t_array = list(np.linspace(0, sample_duration, num=len(i_array)))
        # print(len(t_array))

        return {'v_pts': v_array, 'i_pts': i_array, 'time_pts': t_array}

    def reset_accumulators(self):
        """
        Resets all accumulated measurements: AmpereHour, KilowattHour, VoltageNegativePeak, VoltagePositivePeak,
        CurrentNegativePeak, CurrentPositivePeak, PowerNegativePeak, PowerPositivePeak

        :return: SCPI response
        """
        return self.cmd('MEASure:RESet:ALL')

    def set_aperture(self, aperture=0.0010005):
        """

        This command specifies the measurement aperture (capture duration). The Module will pick the sample rate.
        The actual number of samples may be less than that specified in SENS:SWE:POINTS. Applies to both voltage and
        current measurements.

        Command Parameters <NR2>

        :param aperture: sample rate
        :return: SCPI response
        """
        return self.cmd('SENSe:SWEep:APERture "%s"' % aperture)

    def get_aperture(self):
        """

        This command specifies the measurement aperture (capture duration). The Module will pick the sample rate.
        The actual number of samples may be less than that specified in SENS:SWE:POINTS. Applies to both voltage and
        current measurements.

        :return: float, <NR2>, e.g., 0.0010005
        """
        return float(self.query('SENSe:SWEep:APERture?'))

    def set_max_samples(self, samples):
        """
        This command specifies the maximum number of samples. Applies to both voltage and current measurements.

        :return: None
        """
        return self.cmd('SENSe:SWEep:POINts %s' % int(samples))

    def get_max_samples(self):
        """
        This command gets the maximum number of samples. Applies to both voltage and current measurements.

        :return: int, e.g., 1200
        """
        return int(self.query('SENSe:SWEep:POINts?'))

    def get_sample_rate(self):
        """
        This query returns the time interval between samples (1 / sample rate). Applies to both voltage and
        current measurements.

        :return: float, e.g., 1.3e-06
        """
        return float(self.query('SENSe:SWEep:TINTerval?'))

    # Output system
    def get_battery_detect_voltage(self):
        """
        This command (battery detect voltage) sets the minimum voltage that must be present before the module
        is allowed to go into charge mode.

        :return: float
        """
        return float(self.query('BDVoltage?'))

    def set_battery_detect_voltage(self, bd_voltage):
        """
        This command (battery detect voltage) sets the minimum voltage that must be present before the module is
        allowed to go into charge mode.

        :param bd_voltage: 0 through max voltage
        :return: None
        """
        return self.cmd('BDVoltage %s' % bd_voltage)

    def get_operational_mode(self):
        """
        Get the operation mode and settings.

        Command Parameters <mode>,<enable>,<voltage>,<current>,<power>,<resistance> where:
            <mode> NR1: 0 = Off, 1 = standby, 2 = charge, 3 = discharge, 4 = battery
            <enable> NR1: (bit values add for combinations): 1 = voltage enabled, 2 = current enabled,
                                                             4 = power enabled, 8 = resistance enabled.
            <voltage> NR2: the voltage setpoint (if voltage is enabled with <enable>)
            <current >: the current setpoint (if current is enabled with <enable>)
            <power >: the power setpoint (if power is enabled with <enable>)
            <resistance >: the resistance setpoint (if resistance is enabled with <enable>)

        :return: dict, e.g., {'mode': 'BATTERY_MODE',
                              'enable': ['VOLTAGE_ENABLED', 'CURRENT_ENABLED', 'POWER_ENABLED', 'RESISTANCE_ENABLED'],
                              'voltage': 54.0,
                              'current': 150.0,
                              'power': 8000.0,
                              'resistance': 0.0050008}
        """
        str_data = self.query('OPERation?')
        data = [str(i) for i in str_data.split(',')]
        # print(data)

        decimal = int(data[1])
        ena_list = []
        if (decimal & (1 << VOLTAGE_ENABLED)) == (1 << VOLTAGE_ENABLED):
            ena_list.append('VOLTAGE_ENABLED')
        if (decimal & (1 << CURRENT_ENABLED)) == (1 << CURRENT_ENABLED):
            ena_list.append('CURRENT_ENABLED')
        if (decimal & (1 << POWER_ENABLED)) == (1 << POWER_ENABLED):
            ena_list.append('POWER_ENABLED')
        if (decimal & (1 << RESISTANCE_ENABLED)) == (1 << RESISTANCE_ENABLED):
            ena_list.append('RESISTANCE_ENABLED')

        data_dict = {'mode': MODES.get(data[0]),
                     'enable': ena_list,
                     'voltage': float(data[2]),
                     'current': float(data[3]),
                     'power': float(data[4]),
                     'resistance': float(data[5])
                     }

        return data_dict

    def set_operational_mode(self, op_mode=None):
        """
        Get the operation mode and settings.

        Command Parameters <mode>,<enable>,<voltage>,<current>,<power>,<resistance> where:
            <mode> NR1: 0 = Off, 1 = standby, 2 = charge, 3 = discharge, 4 = battery
            <enable> NR1: (bit values add for combinations): 1 = voltage enabled, 2 = current enabled,
                                                             4 = power enabled, 8 = resistance enabled.
            <voltage> NR2: the voltage setpoint (if voltage is enabled with <enable>)
            <current >: the current setpoint (if current is enabled with <enable>)
            <power >: the power setpoint (if power is enabled with <enable>)
            <resistance >: the resistance setpoint (if resistance is enabled with <enable>)

        :param op_mode: dict, e.g., {'mode': 'BATTERY_MODE',
                              'enable': ['VOLTAGE_ENABLED', 'CURRENT_ENABLED', 'POWER_ENABLED', 'RESISTANCE_ENABLED'],
                              'voltage': 54.0,
                              'current': 150.0,
                              'power': 8000.0,
                              'resistance': 0.0050008}
        """
        cmd_str = ''
        current_params = self.get_operational_mode()  # recycle values when not in param dict
        if op_mode is None:
            op_mode = {}

        if 'mode' in op_mode:
            cmd_str += '%s,' % MODES.get(op_mode['mode'])  # convert back to int string
        else:
            cmd_str += '%s,' % MODES.get(current_params['mode'])  # convert back to int string

        bitfield_int = 0
        if 'enable' in op_mode:
            if 'VOLTAGE_ENABLED' in op_mode['enable']:
                bitfield_int += 1
            if 'CURRENT_ENABLED' in op_mode['enable']:
                bitfield_int += 2
            if 'POWER_ENABLED' in op_mode['enable']:
                bitfield_int += 4
            if 'RESISTANCE_ENABLED' in op_mode['enable']:
                bitfield_int += 8
        else:
            if 'VOLTAGE_ENABLED' in current_params['enable']:
                bitfield_int += 1
            if 'CURRENT_ENABLED' in current_params['enable']:
                bitfield_int += 2
            if 'POWER_ENABLED' in current_params['enable']:
                bitfield_int += 4
            if 'RESISTANCE_ENABLED' in current_params['enable']:
                bitfield_int += 8
        cmd_str += '%s,' % bitfield_int

        keys = ['voltage', 'current', 'power', 'resistance']
        for key in keys:
            if key in op_mode:
                cmd_str += '%s,' % op_mode[key]
            else:
                cmd_str += '%s,' % current_params[key]

        command = 'OPERation %s' % cmd_str[:-1]  # remove last comma
        # print('Sending: %s' % command)
        return self.cmd(command)

    def get_watchdog_interval(self):
        return self.query('SYSTem:WATChdog:INTerval')

    def get_regulation_gain(self):
        """
        This command (regulation gain) sets the percent correction applied during each control loop to regulate the
        output. A value of 0 will inhibit the regulation feedback. The larger the value the bigger the adjustment.
        The value is a percent entered as a floating point where 5% is 0.05.

        :return: 0 through 0.30
        """
        return float(self.query('OUTPut:RGAin'))

    def irradiance_set(self, irradiance):
        """ Not implemented """
        pass

    def get_safety(self):
        """
        This command is used to set the maximum allowable time and value, which, if exceeded, will cause the Module
        to shut off. Time values of <0 disable that parameter. Max temperature is optional on setting (it is disabled
        if not set). Max temperature set to -1 to disable.

        SCPI Query Returns <Min V>,<Min V Time>,<Max V>,<Max V Time>,<Max Sink A>,<Max Sink A Time>,<Max Source A>,
        <Max Source A Time>,<Max Sink W>,<Max Sink W Time>,<Max Source W>,<Max Source W Time>,<Max Temperature>

        :return: dict
        """
        str_data = self.query('OUTPut:SAFety?')
        data = [float(i) for i in str_data.split(',')]

        data_dict = {'Min V': data[0],
                     'Min V Time': data[1],
                     'Max V': data[2],
                     'Max V Time': data[3],
                     'Max Sink A': data[4],
                     'Max Sink A Time': data[5],
                     'Max Source A': data[6],
                     'Max Source A Time': data[7],
                     'Max Sink W': data[8],
                     'Max Sink W Time': data[9],
                     'Max Source W': data[10],
                     'Max Source W Time': data[11],
                     'Max Temperature': data[12],
                     }

        return data_dict

    def set_safety(self, safety_dict=None):
        """
        This command is used to set the maximum allowable time and value, which, if exceeded, will cause the Module
        to shut off. Time values of <0 disable that parameter. Max temperature is optional on setting (it is disabled
        if not set). Max temperature set to -1 to disable.

        SCPI Command Params: <Min V>,<Min V Time>,<Max V>,<Max V Time>,<Max Sink A>,<Max Sink A Time>,<Max Source A>,
        <Max Source A Time>,<Max Sink W>,<Max Sink W Time>,<Max Source W>,<Max Source W Time>,<Max Temperature>

        :param safety_dict: dict in the format:
                {'Min V': 0.0,
                'Min V Time': -1.0,
                'Max V': 64.0,
                'Max V Time': -1.0,
                'Max Sink A': 150.0,
                'Max Sink A Time': -1.0,
                'Max Source A': 150.0,
                'Max Source A Time': -1.0,
                'Max Sink W': 8000.0,
                'Max Sink W Time': -1.0,
                'Max Source W': 8000.0,
                'Max Source W Time': -1.0,
                'Max Temperature': -1.0}

            Any missing keys will be replaced with the current value

        :return: None
        """

        cmd_str = ''
        current_params = self.get_safety()  # recycle values when not in param dict

        if safety_dict is None:
            safety_dict = {}

        keys = ['Min V', 'Min V Time', 'Max V', 'Max V Time', 'Max Sink A',
                'Max Sink A Time', 'Max Source A','Max Source A Time', 'Max Sink W',
                'Max Sink W Time', 'Max Source W', 'Max Source W Time', 'Max Temperature']

        for key in keys:
            if key in safety_dict:
                cmd_str += '%s,' % safety_dict[key]
            else:
                cmd_str += '%s,' % current_params[key]

        command = 'OUTPut:SAFety %s' % cmd_str[:-1]  # remove last comma
        # print('Sending: %s' % command)
        return self.cmd(command)

    def get_range(self):
        """
        Set or get the active range using a zero-based index. Use INSTrument:CAPabilities:RANGe[:MAXimum]? to
        determine the maximum number of ranges.

        :return: int
        """
        return int(self.query('OUTPut:RANGe'))

    def get_slew_current(self):
        return float(self.query('SLEW:CURRent?'))

    def get_slew_voltage(self):
        return float(self.query('SLEW:VOLTage?'))

    def get_slew_power(self):
        return float(self.query('SLEW:POWer?'))

    def get_slew_resistance(self):
        return float(self.query('SLEW:RESistance?'))

    def set_slew_current(self, val):
        return self.cmd('SLEW:CURRent %s' % val)

    def set_slew_voltage(self, val):
        return self.cmd('SLEW:VOLTage %s' % val)

    def set_slew_power(self, val):
        return self.cmd('SLEW:POWer %s' % val)

    def set_slew_resistance(self, val):
        return self.cmd('SLEW:RESistance %s' % val)

    def get_output_state(self):
        """
        :return: True if output on, False if output off
        """
        return self.get_operational_mode()['mode'] == 'BATTERY_MODE'

    def set_output_off(self):
        self.set_operational_mode(op_mode={'mode': 'OFF_MODE'})

    def set_output_on(self):
        self.set_operational_mode(op_mode={'mode': 'BATTERY_MODE', 'enable': ['VOLTAGE_ENABLED', 'CURRENT_ENABLED',
                                                                              'POWER_ENABLED', 'RESISTANCE_ENABLED']})

    def get_voltage_protection_level(self):
        return self.get_safety()['MAX V']

    def get_current_protection_level(self):
        protection_levels = self.get_safety()
        return [protection_levels['MAX SINK A'], protection_levels['MAX SOURCE A']]

    def clear_protection_faults(self):
        pass

    def set_overcurrent_protection(self, current=150):
        self.set_safety(safety_dict={'Max Sink A': current, 'Max Source A': current,
                                     'Max Sink A Time': 0.005, 'Max Source A Time': 0.005})

    def set_overvoltage_protection(self, voltage=54):
        self.set_safety(safety_dict={'Max V': voltage, 'Max V Time': 0.005})

    def set_defaults(self):

        self.set_battery_detect_voltage(bd_voltage=0.0)

        safety_vals = {'Min V': 0.0, 'Min V Time': 0.0,
                       'Max V': 64.0, 'Max V Time': 0.005,
                       'Max Sink A': 150.0, 'Max Sink A Time': 0.005,
                       'Max Source A': 150.0, 'Max Source A Time': 0.005,
                       'Max Sink W': 8000.0, 'Max Sink W Time': 0.005,
                       'Max Source W': 8000.0, 'Max Source W Time': 0.005,
                       'Max Temperature': -1.0}
        self.set_safety(safety_dict=safety_vals)

        self.set_output_on()

        op_mode = {'enable': ['VOLTAGE_ENABLED', 'CURRENT_ENABLED', 'POWER_ENABLED', 'RESISTANCE_ENABLED'],
                   'voltage': 54.0,
                   'current': 150.0,
                   'power': 8000.0,
                   'resistance': 0.005}
        self.set_operational_mode(op_mode=op_mode)

    def blink_led(self, on_off='OFF'):
        """
        :param on_off: 0, 1, ON, OFF
        :return: SCPI response
        """
        return self.cmd('SYSTem:LED %s' % on_off)

if __name__ == "__main__":

    # rm = pyvisa.ResourceManager()
    # pmod = rm.open_resource('TCPIP::10.1.2.180::INSTR')
    # print(pmod.query('*IDN?'))
    # pmod.close()

    power_module_ips = ['10.1.2.181', '10.1.2.182']
    for ip in power_module_ips:
        pmod = NHResearch(ipaddr=ip)
        print(pmod.info())

        pmod.set_defaults()
        pmod.set_local()
        # pmod.set_output_off()
        pmod.close()

        # print(pmod.waverform_capture())
        # print(pmod.measurements_get())
        # print(pmod.status())
        # print(pmod.current_ranges())
        # print(pmod.power_ranges())
        # print(pmod.resistance_ranges())
        # print(pmod.voltage_ranges())
        # print(pmod.gain_ranges())
        # # print(pmod.waverform_capture())
        # print(pmod.measure_all())
        # print(pmod.get_aperture())
        # print(pmod.get_max_samples())
        # print(pmod.get_sample_rate())
        #
        #
        # print(pmod.get_operational_mode())
        # pmod.set_operational_mode()
        #
        # safety_dict = {'Min V': 0.0, 'Min V Time': -1.0,
        #                'Max V': 64.0, 'Max V Time': -1.0,
        #                'Max Sink A': 150.0, 'Max Sink A Time': -1.0,
        #                'Max Source A': 150.0, 'Max Source A Time': -1.0,
        #                'Max Sink W': 8000.0, 'Max Sink W Time': -1.0,
        #                'Max Source W': 8000.0, 'Max Source W Time': -1.0,
        #                'Max Temperature': -1.0}
        #
        # safety_dict2 = {'Min V': 0.0, 'Min V Time': 0.0,
        #                 'Max V': 64.0, 'Max V Time': 0.0050008,
        #                 'Max Sink A': 150.0, 'Max Sink A Time': 0.0050016,
        #                 'Max Source A': 150.0, 'Max Source A Time': 0.0050008,
        #                 'Max Sink W': 8000.0, 'Max Sink W Time': 0.0050016,
        #                 'Max Source W': 8000.0, 'Max Source W Time': 0.0050008,
        #                 'Max Temperature': -1.0}
        #
        # print(pmod.get_safety())





