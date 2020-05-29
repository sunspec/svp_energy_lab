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
import sys
import os
import glob
import importlib

der1547_modules = {}


def params(info, id=None, label='DER1547', group_name=None, active=None, active_value=None):
    """
    Defining the parameters when der1547 is used in SVP scripts
    """
    if group_name is None:
        group_name = DER1547_DEFAULT_ID
    else:
        group_name += '.' + DER1547_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    name = lambda name: group_name + '.' + name
    info.param_group(group_name, label='%s Parameters' % label, active=active, active_value=active_value, glob=True)
    info.param(name('mode'), label='%s Mode' % label, default='Disabled', values=['Disabled'])
    for mode, m in der1547_modules.items():
        m.params(info, group_name=group_name)


DER1547_DEFAULT_ID = 'der1547'


def der1547_init(ts, id=None, group_name=None):
    """
    Function to create specific der1547 implementation instances.
    """
    if group_name is None:
        group_name = DER1547_DEFAULT_ID
    else:
        group_name += '.' + DER1547_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    print('run group_name = %s' % group_name)
    mode = ts.param_value(group_name + '.' + 'mode')
    sim = None
    if mode != 'Disabled':
        sim_module = der1547_modules.get(mode)
        if sim_module is not None:
            sim = sim_module.DER1547(ts, group_name)
        else:
            raise DER1547Error('Unknown DER1547 system mode: %s' % mode)

    return sim


class DER1547Error(Exception):
    """
    Exception to wrap all der1547 generated exceptions.
    """
    pass


class DER1547(object):
    """
    Template for grid simulator implementations. This class can be
    used as a base class or independent grid simulator classes can be
    created containing the methods contained in this class.
    """

    def __init__(self, ts, group_name):
        self.ts = ts
        self.group_name = group_name

    def config(self):
        """ Perform any configuration for the simulation
        based on the previously provided parameters. """
        pass

    def open(self):
        """ Open the communications resources associated with the grid simulator. """
        pass

    def close(self):
        """ Close any open communications resources associated with the grid simulator. """
        pass

    def info(self):
        """
        :return: string with information on the IEEE 1547 DER type.
        """
        pass

    def get_nameplate(self):
        """
        Get/Set Nameplate information
        ______________________________________________________________________________________________
        Parameter                                               params dict key
        ______________________________________________________________________________________________
        1. Active power rating at unity power factor            np_active_power_rtg
           (nameplate active power rating)
        2. Active power rating at specified over-excited        np_active_power_rtg_over_excited
           power factor
        3. Specified over-excited power factor                  np_over_excited_pf
        4. Active power rating at specified under-excited       np_active_power_rtg_under_excited
           power factor
        5. Specified under-excited power factor                 np_under_excited_pf
        6. Apparent power maximum rating                        np_apparent_power_max_rtg
        7. Normal operating performance category                np_normal_op_category
        8. Abnormal operating performance category              np_abnormal_op_category
        9. Reactive power injected maximum rating               np_reactive_power_inj_max_rtg
        10. Reactive power absorbed maximum rating              np_reactive_power_abs_max_rtg
        11. Active power charge maximum rating                  np_active_power_chg_max_rtg
        12. Apparent power charge maximum rating                np_apparent_power_chg_max_rtg
        13. AC voltage nominal rating                           np_ac_volt_nom_rtg
        14. AC voltage maximum rating                           np_ac_volt_max_rtg
        15. AC voltage minimum rating                           np_ac_volt_min_rtg
        16. Supported control mode functions                    np_supported_ctrl_mode_func (dict)
        17. Reactive susceptance that remains connected to      np_reactive_susceptance
            the Area EPS in the cease to energize and trip
            state
        18. Manufacturer                                        np_manufacturer
        19. Model                                               np_model
        20. Serial number                                       np_serial_number
        21. Version                                             np_version
        """
        pass

    def set_nameplate(self):
        """ See parameters in get_nameplate()."""
        pass

    def get_monitoring(self):
        '''
            Active Power
            Reactive Power
            Voltage
            Frequency
            Operational State
            Connection State
            Alarm Status
            Operational State of Charge
        '''
        pass

    def get_fixed_pf(self):
        """ Get fixed power factor control settings.

        Constant Power Factor Mode Enable
        Constant Power Factor
        Constant Power Factor Excitation

        :param params: Dictionary of parameters. Following keys are supported:
        enable, pf, pf excitation.
        :return: Dictionary of active settings for fixed factor.
        """
        pass

    def set_fixed_pf(self, params=None):
        """
        Parameters          Name
        PF Enable           pf_enable
        PF                  pf
        PF Excitation       pf_excitation
        """
        pass

    def get_limit_max_power(self):
        '''
        Limit Active Power Enable
        Maximum Active Power
        '''
        pass

    def set_limit_max_power(self, params=None):
        """
        Parameters                      Name
        Limit Active Power Enable       var_enable
        Maximum Active Power            var
        """
        pass

    def get_volt_var(self):
        '''
            Voltage-Reactive Power Mode Enable
            Vref
            Autonomous VRef adjustment Enable
            VRef adjustment time constant
            V/Q Curve Points
            Open Loop Response Time
        '''
        pass

    def set_volt_var(self, params=None):
        """
        Parameters                                  Names
        Voltage-Reactive Power Mode Enable         vv_enable
        VRef Reference voltage                     vv_vref
        Autonomous VRef adjustment enable          vv_vref_enable
        VRef adjustment time constant              vv_vref_time
        V/Q Curve Points                           vv_curve (dict): {'v': [], 'q': []}
        Open Loop Response Time                    vv_open_loop_time
        """
        pass

    def get_freq_watt(self):
        '''
        Over-frequency Droop Deadband DBOF
        Under-frequency Droop Deadband DBUF
        Over-frequency Droop Slope KOF
        Under-frequency Droop Slope KUF
        Open Loop Response Time
        '''
        pass

    def set_freq_watt(self, params=None):
        """
        Parameters                          Names
        Over-frequency Droop DBOF           fw_dbof
        Under-frequency Droop DBUF          fw_dbuf
        Over-frequency Droop KOF            fw_kof
        Under-frequency Droop KUF           fw_kuf
        Open Loop Response Time             fw_open_loop_time
        """
        pass

    def get_enter_service(self):
        '''
        Permit service
        ES Voltage High
        ES Voltage Low
        ES Frequency High
        ES Frequency Low
        ES Delay
        ES Randomized Delay
        ES Ramp Rate
        '''
        pass

    def set_enter_service(self, params=None):
        """
        Parameters              Name
        Permit service          es_permit_service
        ES Voltage High         es_volt_high
        ES Voltage Low          es_volt_low
        ES Frequency High       es_freq_high
        ES Frequency Low        es_freq_low
        ES Delay                es_delay
        ES Randomized Delay     es_randomized_delay
        ES Ramp Rate            es_ramp_rate
        """
        pass

    def get_volt_watt(self):
        """
        Voltage-Active Power (Volt-Watt) Mode Enable
        V/P Curve Points (x,y)
        Open Loop Response Time
        """
        pass

    def set_volt_watt(self, params=None):
        """
        Parameters                      Name
        Voltage-Active Power Enable     vp_enable
        V/P Curve Points                vp_curve: {'v': {}, 'p': {}}
        Open Loop Response Time         vp_open_loop_time
        """
        pass

    def get_reactive_power(self):
        '''
        Constant Reactive Power Mode Enable
        Constant Reactive Power
        '''
        pass

    def set_reactive_power(self, params=None):
        """
        Parameters                      Name
        Constant VAR Enable             var_enable
        Constant Reactive Power         var
        """
        pass

    def get_watt_var(self):
        '''
        Active Power-Reactive Power (Watt-VAr) Enable
        P/Q Curve Points
        '''
        pass

    def set_watt_var(self, params=None):
        """
        Parameters                              Name
        Active Power-Reactive Power Enable      pq_enable
        P/Q Curve Points                        pq_curve: {'p': {}, 'q': {}}
        """
        pass

    def set_volt_trip(self, params=None):
        """
        Set HV Trip curve control settings.

        Parameters                      Name
        HV Trip Curve Points            hv: {'t': [], 'v': []}
        LV Trip Curve Points            lv: {'t': [], 'v': []}
        """
        pass

    def set_freq_trip(self, params=None):
        """
        Set HF Trip curve control settings.

        Parameters                      Name
        HF Trip Curve Points            hf: {'t': [], 'f': []}
        LF Trip Curve Points            lf: {'t': [], 'f': []}
        """
        pass

    def set_volt_cessation(self, params=None):
        """
        Set HV Momentary Cessation control settings.

        Parameters                      Name
        HV Trip Curve Points            hv: {'t': [], 'v': []}
        LV Trip Curve Points            lv: {'t': [], 'v': []}
        """
        pass


def der1547_scan():
    global der1547_modules
    # scan all files in current directory that match der1547_*.py
    package_name = '.'.join(__name__.split('.')[:-1])
    files = glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'der1547_*.py'))
    for f in files:
        module_name = None
        try:
            module_name = os.path.splitext(os.path.basename(f))[0]
            if package_name:
                module_name = package_name + '.' + module_name
            m = importlib.import_module(module_name)
            if hasattr(m, 'der1547_info'):
                info = m.der1547_info()
                mode = info.get('mode')
                # place module in module dict
                if mode is not None:
                    der1547_modules[mode] = m
            else:
                if module_name is not None and module_name in sys.modules:
                    del sys.modules[module_name]
        except Exception as e:
            if module_name is not None and module_name in sys.modules:
                del sys.modules[module_name]
            raise DER1547Error('Error scanning module %s: %s' % (module_name, str(e)))

# scan for der1547 modules on import
der1547_scan()

if __name__ == "__main__":
    pass
