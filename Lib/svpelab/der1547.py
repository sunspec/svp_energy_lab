"""
Copyright (c) 2017, Sandia National Laboratories and SunSpec Alliance
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

Acronyms in this document:
 - RofA: Range of Adjustability
 - OLRT: Open Loop Response Time
 - ER: Evaluated Range
 - AS: Applied Setting

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
    for mode, m in list(der1547_modules.items()):
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
    print(('run group_name = %s' % group_name))
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
        """ Open the communications resources associated with the DER. """
        pass

    def close(self):
        """ Close any open communications resources associated with the DER. """
        pass

    def info(self):
        """
        :return: string with information on the IEEE 1547 DER type.
        """
        pass

    def get_nameplate(self):
        """
        Get Nameplate information - See IEEE 1547-2018 Table 28
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                         Units
        ______________________________________________________________________________________________________________
        Active power rating at unity power factor               np_p_max                                kW
            (nameplate active power rating)
        Active power rating at specified over-excited           np_p_max_over_pf                        kW
            power factor
        Specified over-excited power factor                     np_over_pf                              Decimal
        Active power rating at specified under-excited          np_p_max_under_pf                       kW
            power factor
        Specified under-excited power factor                    np_under_pf                             Decimal
        Apparent power maximum rating                           np_va_max                               kVA
        Normal operating performance category                   np_normal_op_cat                        str
            e.g., CAT_A-CAT_B
        Abnormal operating performance category                 np_abnormal_op_cat                      str
            e.g., CAT_II-CAT_III
        Intentional Island  Category (optional)                 np_intentional_island_cat               str
            e.g., UNCAT-INT_ISLAND_CAP-BLACK_START-ISOCH
        Reactive power injected maximum rating                  np_q_max_inj                            kVAr
        Reactive power absorbed maximum rating                  np_q_max_abs                            kVAr
        Active power charge maximum rating                      np_p_max_charge                         kW
        Apparent power charge maximum rating                    np_apparent_power_charge_max            kVA
        AC voltage nominal rating                               np_ac_v_nom                             Vac
        AC voltage maximum rating                               np_ac_v_max_er_max                      Vac
        AC voltage minimum rating                               np_ac_v_min_er_min                      Vac
        Supported control mode functions                        np_supported_modes                      dict
            e.g., {'fixed_pf': True 'volt_var': False} with keys:
            Supports Low Voltage Ride-Through Mode: 'lv_trip'
            Supports High Voltage Ride-Through Mode: 'hv_trip'
            Supports Low Freq Ride-Through Mode: 'lf_trip'
            Supports High Freq Ride-Through Mode: 'hf_trip'
            Supports Active Power Limit Mode: 'max_w'
            Supports Volt-Watt Mode: 'volt_watt'
            Supports Frequency-Watt Curve Mode: 'freq_watt'
            Supports Constant VArs Mode: 'fixed_var'
            Supports Fixed Power Factor Mode: 'fixed_pf'
            Supports Volt-VAr Control Mode: 'volt_var'
            Supports Watt-VAr Mode: 'watt_var'
        Reactive susceptance that remains connected to          np_reactive_susceptance                 Siemens
            the Area EPS in the cease to energize and trip
            state
        Maximum resistance (R) between RPA and POC.             np_remote_meter_resistance              Ohms
            (unsupported in 1547)
        Maximum reactance (X) between RPA and POC.              np_remote_meter_reactance               Ohms
            (unsupported in 1547)
        Manufacturer                                            np_manufacturer                         str
        Model                                                   np_model                                str
        Serial number                                           np_serial_num                           str
        Version                                                 np_fw_ver                               str

        :return: dict with keys shown above.
        """

        '''
        Table 28 - Nameplate information
        ________________________________________________________________________________________________________________
        Parameter                                               Description
        ________________________________________________________________________________________________________________
        1. Active power rating at unity power factor            Active power rating in watts at unity power factor
           (nameplate active power rating)
        2. Active power rating at specified over-excited        Active power rating in watts at specified over-excited
           power factor                                         power factor
        3. Specified over-excited power factor                  Over-excited power factor as described in 5.2
        4. Active power rating at specified under-excited       Active power rating in watts at specified under-excited
           power factor                                         power factor
        5. Specified under-excited power factor                 Under-excited power factor as described in 5.2
        6. Apparent power maximum rating                        Maximum apparent power rating in voltamperes
        7. Normal operating performance category                Indication of reactive power and voltage/power control
                                                                capability. (Category A/B as described in 1.4)
        8. Abnormal operating performance category              Indication of voltage and frequency ride-through
                                                                capability Category I, II, or III, as described in 1.4
        9. Reactive power injected maximum rating               Maximum injected reactive power rating in vars
        10. Reactive power absorbed maximum rating              Maximum absorbed reactive power rating in vars
        11. Active power charge maximum rating                  Maximum active power charge rating in watts
        12. Apparent power charge maximum rating                Maximum apparent power charge rating in voltamperes. May
                                                                differ from the apparent power maximum rating
        13. AC voltage nominal rating                           Nominal AC voltage rating in RMS volts
        14. AC voltage maximum rating                           Maximum AC voltage rating in RMS volts
        15. AC voltage minimum rating                           Minimum AC voltage rating in RMS volts
        16. Supported control mode functions                    Indication of support for each control mode function
        17. Reactive susceptance that remains connected to      Reactive susceptance that remains connected to the Area
            the Area EPS in the cease to energize and trip      EPS in the cease to energize and trip state
            state
        18. Manufacturer                                        Manufacturer
        19. Model                                               Model
        20. Serial number                                       Serial number
        21. Version                                             Version
        '''
        pass

    def get_configuration(self):
        """
        Get configuration information in the 1547 DER. Each rating in Table 28 may have an associated configuration
        setting that represents the as-configured value. If a configuration setting value is different from the
        corresponding nameplate value, the configuration setting value shall be used as the rating within the DER.

        :return: params dict with keys shown in nameplate.
        """
        return None

    def set_configuration(self, params=None):
        """
        Set configuration information. params are those in get_nameplate().
        """
        pass

    def configuration(self, params=None):
        if params is None:
            return self.get_configuration()
        else:
            return self.set_configuration(params=params)

    def get_settings(self):
        """
        Get configuration information in the 1547 DER. Each rating in Table 28 may have an associated configuration
        setting that represents the as-configured value. If a configuration setting value is different from the
        corresponding nameplate value, the configuration setting value shall be used as the rating within the DER.

        :return: params dict with keys shown in nameplate.
        """
        return None

    def set_settings(self, params=None):
        """
        Set configuration information. params are those in get_nameplate().
        """
        return self.set_configuration(params)

    def settings(self, params=None):
        if params is None:
            return self.get_settings()
        else:
            return self.set_settings(params=params)

    def get_monitoring(self):
        """
        This information is indicative of the present operating conditions of the
        DER. This information may be read.

        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                    units
        ______________________________________________________________________________________________________________
        Active Power                                                mn_w                               kW
        Reactive Power                                              mn_var                             kVAr
        Voltage (list)                                              mn_v                               V-N list
            Single phase devices: [V]
            3-phase devices: [V1, V2, V3]
        Frequency                                                   mn_hz                              Hz

        Operational State                                           mn_st                              bool
            'On': True, DER is operating (e.g., generating)
            'Off': False, DER is not operating

        Connection State                                            mn_conn                            bool
            'Connected': DER connected
            'Disconnected': DER not connected

        DER State (not in IEEE 1547.1)                              mn_der_st                         dict of bools
            {'mn_der_st_local': System in local/maintenance state  # DNP3 points
             'mn_der_st_lockout': System locked out
             'mn_der_st_starting': Start command has been received
             'mn_der_st_stopping': Emergency Stop command has been received
             'mn_der_st_started': Started
             'mn_der_st_stopped': Stopped
             'mn_der_st_permission_to_start': Start Permission Granted
             'mn_der_st_permission_to_stop': Stop Permission Granted
             'mn_der_st_connected_idle': Idle-Connected
             'mn_der_st_connected_generating': On-Connected
             'mn_der_st_connected_charging': On-Charging-Connected
             'mn_der_st_off_available': Off-Available
             'mn_der_st_off_not_available': Off-Not-Available
             'mn_der_st_switch_closed_status': Switch Closed
             'mn_der_st_switch_closed_movement': Switch Moving}
             'mn_der_st_off': OFF   # SunSpec Points
             'mn_der_st_sleeping': SLEEPING
             'mn_der_st_mppt': MPPT
             'mn_der_st_throttled': THROTTLED  (curtailed)
             'mn_der_st_shutting_down': SHUTTING_DOWN
             'mn_der_st_fault': FAULT
             'mn_der_st_standby': STANDBY

        Alarm Status                                                mn_alrm                            dict of bools
            Reported Alarm Status matches the device
            present alarm condition for alarm and no
            alarm conditions. For test purposes only, the
            DER manufacturer shall specify at least one
            way an alarm condition that is supported in
            the protocol being tested can be set and
            cleared.
            {'mn_alm_system_comm_error': System Communication Error  # Start of DNP3 alarms (BI0-9)
             'mn_alm_priority_1': System Has Priority 1 Alarms
             'mn_alm_priority_2': System Has Priority 2 Alarms
             'mn_alm_priority_3': System Has Priority 3 Alarms
             'mn_alm_storage_chg_max': Storage State of Charge at Maximum. Maximum Usable State of Charge reached.
             'mn_alm_storage_chg_high': Storage State of Charge is Too High. Maximum Reserve reached.
             'mn_alm_storage_chg_low': Storage State of Charge is Too Low. Minimum Reserve reached.
             'mn_alm_storage_chg_depleted': Storage State of Charge is Depleted. Minimum Usable State of Charge Reached.
             'mn_alm_internal_temp_high': Storage Internal Temperature is Too High
             'mn_alm_internal_temp_low': Storage External (Ambient) Temperature is Too High
             'mn_alm_ground_fault': Ground Fault  # Start of SunSpec Errors
             'mn_alm_over_dc_volt': DC Over Voltage
             'mn_alm_disconn_open': Disconnect Open
             'mn_alm_dc_disconn_open': DC Disconnect Open
             'mn_alm_grid_disconn': Grid Disconnect
             'mn_alm_cabinet_open': Cabinet Open
             'mn_alm_manual_shutdown': Manual Shutdown
             'mn_alm_over_temp': Over Temperature
             'mn_alm_over_freq': Frequency Above Limit
             'mn_alm_under_freq': Frequency Under Limit
             'mn_alm_over_volt': AC Voltage Above Limit
             'mn_alm_under_volt': AC Voltage Under Limit
             'mn_alm_fuse': Blown String Fuse On Input
             'mn_alm_under_temp': Under Temperature
             'mn_alm_mem_or_comm': Generic Memory Or Communication Error (Internal)
             'mn_alm_hdwr_fail': Hardware Test Failure
             'mn_alm_mfr_alrm': Manufacturer Alarm
             'mn_alm_over_cur': Over Current  # IEEE 2030.5/CSIP Alarms (not covered in the above)
             'mn_alm_imbalance_volt': Voltage Imbalance
             'mn_alm_imbalance_cur': Current Imbalance
             'mn_alm_local_emgcy': Local Emergency
             'mn_alm_remote_emgcy': Remote Emergency
             'mn_alm_input_power': Low Input Power
             'mn_alm_phase_rotation': Phase Rotation}

        Operational State of Charge (not required in 1547)          mn_soc_pct                         pct

        :return: dict with keys shown above.
        """
        pass

    def get_const_pf(self):
        """
        Get Constant Power Factor Mode control settings. IEEE 1547-2018 Table 30.
        ________________________________________________________________________________________________________________
        Parameter                                               params dict key                     units
        ________________________________________________________________________________________________________________
        Constant Power Factor Mode Select                       const_pf_mode_enable             bool (True=Enabled)
        Constant Power Factor Excitation                        const_pf_excitation              str ('inj', 'abs')
        Constant Power Factor Setting (RofA not specified in    const_pf_abs_er_min                 decimal
            1547)
        Constant Power Factor Absorbing Setting                 const_pf_abs                        decimal
        Constant Power Factor Setting (RofA not specified in    const_pf_abs_er_max                 decimal
            1547)
        Constant Power Factor Setting (RofA not specified in    const_pf_inj_er_min                 decimal
            1547)
        Constant Power Factor Injecting Setting                 const_pf_inj                        decimal
        Constant Power Factor Setting (RofA not specified in    const_pf_inj_er_max                 decimal
            1547)
        Maximum response time to maintain constant power        const_pf_olrt_er_min                s
            factor. (Not in 1547)
        Maximum response time to maintain constant power        const_pf_olrt                       s
            factor. (Not in 1547)
        Maximum Response time to maintain constant power        const_pf_olrt_er_max                s
            factor. (Not in 1547)

        :return: dict with keys shown above.
        """
        return None

    def set_const_pf(self, params=None):
        """
        Set Constant Power Factor Mode control settings.
        """
        pass

    # volt_var redirects
    def get_volt_var(self):
        return get_qv()

    def set_volt_var(self, params=None):
        return set_qv(params=params)

    def volt_var(self, params=None):
        if params is None:
            return get_volt_var()
        else:
            return set_volt_var(params=params)

    def get_qv(self):
        """
        Get Q(V) parameters. [Volt-Var]
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Voltage-Reactive Power Mode Enable                          qv_mode_enable                  bool (True=Enabled)
        Vref Min (RofA not specified in 1547)                       qv_vref_er_min                  V p.u.
        Vref (0.95-1.05)                                            qv_vref                         V p.u.
        Vref Max (RofA not specified in 1547)                       qv_vref_er_max                  V p.u.

        Autonomous Vref Adjustment Enable                           qv_vref_auto_mode               bool (True=Enabled)
        Vref adjustment time Constant (RofA not specified           qv_vref_olrt_er_min             s
            in 1547)
        Vref adjustment time Constant (300-5000)                    qv_vref_olrt                    s
        Vref adjustment time Constant (RofA not specified           qv_vref_olrt_er_max             s
            in 1547)

        Q(V) Curve Point V1-4 Range of Adjustability (Min)          qv_curve_v_er_min               V p.u.
            (RofA not specified in 1547) (list)
        Q(V) Curve Point V1-4 (list, e.g., [95, 99, 101, 105])      qv_curve_v_pts                  V p.u.
        Q(V) Curve Point V1-4 Range of Adjustability (Max)          qv_curve_v_er_max               V p.u.
            (RofA not specified in 1547) (list)

        Q(V) Curve Point Q1-4 Range of Adjustability (Min)          qv_curve_q_er_min               VAr p.u.
            (RofA not specified in 1547) (list)
        Q(V) Curve Point Q1-4 (list)                                qv_curve_q_pts                  VAr p.u.
        Q(V) Curve Point Q1-4 Range of Adjustability (Max)          qv_curve_q_er_max               VAr p.u.
            (RofA not specified in 1547) (list)

        Q(V) Open Loop Response Time (RofA not specified in 1547)   qv_olrt_er_min                  s
        Q(V) Open Loop Response Time Setting  (1-90)                qv_olrt                         s
        Q(V) Open Loop Response Time (RofA not specified in 1547)   qv_olrt_er_max                  s

        :return: dict with keys shown above.
        """
        return None

    def set_qv(self, params=None):
        """
        Set Q(V) parameters. [Volt-Var]
        """
        pass

    # watt_var redirects
    def get_watt_var(self):
        return get_qp()

    def set_watt_var(self, params=None):
        return set_qp(params=params)

    def watt_var(self, params=None):
        if params is None:
            return get_watt_var()
        else:
            return set_watt_var(params=params)

    def get_qp(self):
        """
        Get Q(P) parameters. [Watt-Var] - IEEE 1547 Table 32
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        Active Power-Reactive Power (Watt-VAr) Enable               qp_mode_enable                      bool
        P-Q curve P1-3 Generation (RofA not Specified in 1547)      qp_curve_p_gen_pts_er_min           P p.u.
        P-Q curve P1-3 Generation Setting (list)                    qp_curve_p_gen_pts                  P p.u.
        P-Q curve P1-3 Generation (RofA not Specified in 1547)      qp_curve_p_gen_pts_er_max           P p.u.

        P-Q curve Q1-3 Generation (RofA not Specified in 1547)      qp_curve_q_gen_pts_er_min           VAr p.u.
        P-Q curve Q1-3 Generation Setting (list)                    qp_curve_q_gen_pts                  VAr p.u.
        P-Q curve Q1-3 Generation (RofA not Specified in 1547)      qp_curve_q_gen_pts_er_max           VAr p.u.

        P-Q curve P1-3 Load (RofA not Specified in 1547)            qp_curve_p_load_pts_er_min          P p.u.
        P-Q curve P1-3 Load Setting (list)                          qp_curve_p_load_pts                 P p.u.
        P-Q curve P1-3 Load (RofA not Specified in 1547)            qp_curve_p_load_pts_er_max          P p.u.

        P-Q curve Q1-3 Load (RofA not Specified in 1547)            qp_curve_q_load_pts_er_min          VAr p.u.
        P-Q curve Q1-3 Load Setting (list)                          qp_curve_q_load_pts                 VAr p.u.
        P-Q curve Q1-3 Load (RofA not Specified in 1547)            qp_curve_q_load_pts_er_max          VAr p.u.

        :return: dict with keys shown above.
        """
        return None

    def set_qp(self, params=None):
        """
        Set Q(P) parameters. [Watt-Var]
        """
        pass

    # volt_watt redirects
    def get_volt_watt(self):
        return get_pv()

    def set_volt_watt(self, params=None):
        return set_pv(params=params)

    def volt_watt(self, params=None):
        if params is None:
            return get_volt_watt()
        else:
            return set_volt_watt(params=params)

    def get_pv(self):
        """
        Get P(V), Voltage-Active Power (Volt-Watt), Parameters
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                         units
        ______________________________________________________________________________________________________________
        Voltage-Active Power Mode Enable                            pv_mode_enable                          bool
        P(V) Curve Point V1-2 Min (RofA not specified in 1547)      pv_curve_v_pts_er_min                   V p.u.
        P(V) Curve Point V1-2 Setting (list)                        pv_curve_v_pts                          V p.u.
        P(V) Curve Point V1-2 Max (RofA not specified in 1547)      pv_curve_v_pts_er_max                   V p.u.

        P(V) Curve Point P1-2 Min (RofA not specified in 1547)      pv_curve_p_pts_er_min                   P p.u.
        P(V) Curve Point P1-2 Setting (list)                        pv_curve_p_pts                          P p.u.
        P(V) Curve Point P1-2 Max (RofA not specified in 1547)      pv_curve_p_pts_er_max                   P p.u.

        P(V) Curve Point P1-P'2 Min (RofA not specified in 1547)    pv_curve_p_bidrct_pts_er_min            P p.u.
        P(V) Curve Point P1-P'2 Setting (list)                      pv_curve_p_bidrct_pts                   P p.u.
        P(V) Curve Point P1-P'2 Max (RofA not specified in 1547)    pv_curve_p_bidrct_pts_er_max            P p.u.

        P(V) Open Loop Response time min (RofA not specified        pv_olrt_er_min                          s
            in 1547)
        P(V) Open Loop Response time Setting (0.5-60)               pv_olrt                                 s
        P(V) Open Loop Response time max (RofA not specified        pv_olrt_er_max                          s
            in 1547)

        :return: dict with keys shown above.
        """
        return None

    def set_pv(self, params=None):
        """
        Set P(V), Voltage-Active Power (Volt-Watt), Parameters
        """
        pass

    def get_const_q(self):
        """
        Get Constant Reactive Power Mode
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                     units
        ______________________________________________________________________________________________________________
        Constant Reactive Power Mode Enable                     const_q_mode_enable              bool (True=Enabled)
        Constant Reactive Power Excitation (not specified in    const_q_mode_excitation          str ('inj', 'abs')
            1547)
        Constant Reactive power setting (See Table 7)           const_q                             VAr p.u.
        Constant Reactive Power (RofA not specified in 1547)    const_q_abs_er_max                  VAr p.u.
            Absorbing Reactive Power Setting.  Per unit value
            based on NP Qmax Abs. Negative signs should not be
            used but if present indicate absorbing VAr.
        Constant Reactive Power (RofA not specified in 1547)    const_q_inj_er_max                  VAr p.u.
            Injecting Reactive Power (minimum RofA)  Per unit
            value based on NP Qmax Inj. Positive signs should
            not be used but if present indicate Injecting VAr.
        Maximum Response Time to maintain constant reactive     const_q_olrt_er_min                 s
            power (not specified in 1547)
        Maximum Response Time to maintain constant reactive     const_q_olrt                        s
            power (not specified in 1547)
        Maximum Response Time to maintain constant reactive     const_q_olrt_er_max                 s
            power(not specified in 1547)

        :return: dict with keys shown above.
        """
        pass

    def set_const_q(self, params=None):
        """
        Set Constant Reactive Power Mode
        """
        pass

    def get_p_lim(self):
        """
        Get Limit maximum active power - IEEE 1547 Table 40
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          p_lim_mode_enable            bool (True=Enabled)
        Maximum Active Power Min                                    p_lim_w_er_min               P p.u.
        Maximum Active Power                                        p_lim_w                      P p.u.
        Maximum Active Power Max                                    p_lim_w_er_max               P p.u.
        """
        pass

    def set_p_lim(self, params=None):
        """
        Get Limit maximum active power.
        """
        pass

    # freq_watt redirects
    def get_freq_watt(self):
        return get_pf()

    def set_freq_watt(self, params=None):
        return set_pf(params=params)

    def freq_watt(self, params=None):
        if params is None:
            return get_freq_watt()
        else:
            return set_freq_watt(params=params)

    def get_pf(self):
        """
        Get P(f), Frequency-Active Power Mode Parameters - IEEE 1547 Table 38
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          pf_mode_enable               bool (True=Enabled)
        P(f) Overfrequency Droop dbOF RofA min                      pf_dbof_er_min                  Hz
        P(f) Overfrequency Droop dbOF Setting                       pf_dbof                         Hz
        P(f) Overfrequency Droop dbOF RofA max                      pf_dbof_er_max                  Hz

        P(f) Underfrequency Droop dbUF RofA min                     pf_dbuf_er_min                  Hz
        P(f) Underfrequency Droop dbUF Setting                      pf_dbuf                         Hz
        P(f) Underfrequency Droop dbUF RofA max                     pf_dbuf_er_max                  Hz

        P(f) Overfrequency Droop kOF RofA min                       pf_kof_er_min                   unitless
        P(f) Overfrequency Droop kOF  Setting                       pf_kof                          unitless
        P(f) Overfrequency Droop kOF RofA max                       pf_kof_er_max                   unitless

        P(f) Underfrequency Droop kUF RofA min                      pf_kuf_er_min                   unitless
        P(f) Underfrequency Droop kUF Setting                       pf_kuf                          unitless
        P(f) Underfrequency Droop kUF RofA Max                      pf_kuf_er_max                   unitless

        P(f) Open Loop Response Time RofA min                       pf_olrt_er_min                  s
        P(f) Open Loop Response Time Setting                        pf_olrt                         s
        P(f) Open Loop Response Time RofA max                       pf_olrt_er_max                  s

        :return: dict with keys shown above.
        """
        pass

    def set_pf(self, params=None):
        """
        Set P(f), Frequency-Active Power Mode Parameters
        """
        pass

    def get_es_permit_service(self):
        """
        Get Permit Service Mode Parameters - IEEE 1547 Table 39
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                 units
        ______________________________________________________________________________________________________________
        Permit service                                          es_permit_service               bool (True=Enabled)
        ES Voltage Low (RofA not specified in 1547)             es_v_low_er_min                 V p.u.
        ES Voltage Low Setting                                  es_v_low                        V p.u.
        ES Voltage Low (RofA not specified in 1547)             es_v_low_er_max                 V p.u.
        ES Voltage High (RofA not specified in 1547)            es_v_high_er_min                V p.u.
        ES Voltage High Setting                                 es_v_high                       V p.u.
        ES Voltage High (RofA not specified in 1547)            es_v_high_er_max                V p.u.
        ES Frequency Low (RofA not specified in 1547)           es_f_low_er_min                 Hz
        ES Frequency Low Setting                                es_f_low                        Hz
        ES Frequency Low (RofA not specified in 1547)           es_f_low_er_max                 Hz
        ES Frequency Low (RofA not specified in 1547)           es_f_high_er_min                Hz
        ES Frequency High Setting                               es_f_high                       Hz
        ES Frequency Low (RofA not specified in 1547)           es_f_high_er_max                Hz
        ES Randomized Delay                                     es_randomized_delay             bool (True=Enabled)
        ES Delay (RofA not specified in 1547)                   es_delay_er_min                 s
        ES Delay Setting                                        es_delay                        s
        ES Delay (RofA not specified in 1547)                   es_delay_er_max                 s
        ES Ramp Rate Min (RofA not specified in 1547)           es_ramp_rate_er_min             %/s
        ES Ramp Rate Setting                                    es_ramp_rate                    %/s
        ES Ramp Rate Min (RofA not specified in 1547)           es_ramp_rate_er_max             %/s

        :return: dict with keys shown above.
        """
        pass

    def set_es_permit_service(self, params=None):
        """
        Set Permit Service Mode Parameters
        """
        pass

    def get_ui(self):
        """
        Get Unintentional Islanding Parameters
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        Unintentional Islanding Mode (enabled/disabled). This       ui_mode_enable                      bool
            function is enabled by default, and disabled only by
            request from the Area EPS Operator.
            UI is always on in 1547 BUT 1547.1 says turn it off
            for some testing
        Unintential Islanding methods supported. Where multiple     ui_capability_er                    list str
            modes are supported place in a list.
            UI BLRC = Balanced RLC,
            UI PCPST = Powerline conducted,
            UI PHIT = Permissive Hardware-input,
            UI RMIP = Reverse/min relay. Methods other than UI
            BRLC may require supplemental comissioning tests.
            e.g., ['UI_BLRC', 'UI_PCPST', 'UI_PHIT', 'UI_RMIP']

        :return: dict with keys shown above.
        """
        pass

    def set_ui(self):
        """
        Get Unintentional Islanding Parameters
        """

    def get_ov(self, params=None):
        """
        Get Overvoltage Trip Parameters - IEEE 1547 Table 35
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        HV Trip Curve Point OV_V1-3 (see Tables 11-13)              ov_trip_v_pts_er_min                V p.u.
            (RofA not specified in 1547)
        HV Trip Curve Point OV_V1-3 Setting (list)                  ov_trip_v_pts                       V p.u.
        HV Trip Curve Point OV_V1-3 (RofA not specified in 1547)    ov_trip_v_pts_er_max                V p.u.
        HV Trip Curve Point OV_T1-3 (see Tables 11-13)              ov_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        HV Trip Curve Point OV_T1-3 Setting (list)                  ov_trip_t_pts                       s
        HV Trip Curve Point OV_T1-3 (RofA not specified in 1547)    ov_trip_t_pts_er_max                s

        :return: dict with keys shown above.
        """
        pass

    def set_ov(self, params=None):
        """
        Set Overvoltage Trip Parameters - IEEE 1547 Table 35
        """
        pass

    def get_uv(self, params=None):
        """
        Get Overvoltage Trip Parameters - IEEE 1547 Table 35
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        LV Trip Curve Point UV_V1-3 (see Tables 11-13)              uv_trip_v_pts_er_min                V p.u.
            (RofA not specified in 1547)
        LV Trip Curve Point UV_V1-3 Setting (list)                  uv_trip_v_pts                       V p.u.
        LV Trip Curve Point UV_V1-3 (RofA not specified in 1547)    uv_trip_v_pts_er_max                V p.u.
        LV Trip Curve Point UV_T1-3 (see Tables 11-13)              uv_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        LV Trip Curve Point UV_T1-3 Setting (list)                  uv_trip_t_pts                       s
        LV Trip Curve Point UV_T1-3 (RofA not specified in 1547)    uv_trip_t_pts_er_max                s

        :return: dict with keys shown above.
        """
        pass

    def set_uv(self, params=None):
        """
        Set Undervoltage Trip Parameters - IEEE 1547 Table 35
        """
        pass

    def get_of(self, params=None):
        """
        Get Overfrequency Trip Parameters - IEEE 1547 Table 37
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        OF Trip Curve Point OF_F1-3 (see Tables 11-13)              of_trip_f_pts_er_min                Hz
            (RofA not specified in 1547)
        OF Trip Curve Point OF_F1-3 Setting                         of_trip_f_pts                       Hz
        OF Trip Curve Point OF_F1-3 (RofA not specified in 1547)    of_trip_f_pts_er_max                Hz
        OF Trip Curve Point OF_T1-3 (see Tables 11-13)              of_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        OF Trip Curve Point OF_T1-3 Setting                         of_trip_t_pts                       s
        OF Trip Curve Point OF_T1-3 (RofA not specified in 1547)    of_trip_t_pts_er_max                s

        :return: dict with keys shown above.
        """
        pass

    def set_of(self, params=None):
        """
        Set Overfrequency Trip Parameters - IEEE 1547 Table 37
        """
        pass

    def get_uf(self, params=None):
        """
        Get Underfrequency Trip Parameters - IEEE 1547 Table 37
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        UF Trip Curve Point UF_F1-3 (see Tables 11-13)              uf_trip_f_pts_er_min                Hz
            (RofA not specified in 1547)
        UF Trip Curve Point UF_F1-3 Setting                         uf_trip_f_pts                       Hz
        UF Trip Curve Point UF_F1-3 (RofA not specified in 1547)    uf_trip_f_pts_er_max                Hz
        UF Trip Curve Point UF_T1-3 (see Tables 11-13)              uf_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        UF Trip Curve Point UF_T1-3 Setting                         uf_trip_t_pts                       s
        UF Trip Curve Point UF_T1-3 (RofA not specified in 1547)    uf_trip_t_pts_er_max                s

        :return: dict with keys shown above.
        """
        pass

    def set_uf(self, params=None):
        """
        Set Underfrequency Trip Parameters - IEEE 1547 Table 37
        """
        pass

    def get_ov_mc(self, params=None):
        """
        Get Overvoltage Momentary Cessation (MC) Parameters - IEEE 1547 Table 36
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        HV MC Curve Point OV_V1-3 (see Tables 11-13)                ov_mc_v_pts_er_min                  V p.u.
            (RofA not specified in 1547)
        HV MC Curve Point OV_V1-3 Setting                           ov_mc_v_pts                         V p.u.
        HV MC Curve Point OV_V1-3 (RofA not specified in 1547)      ov_mc_v_pts_er_max                  V p.u.
        HV MC Curve Point OV_T1-3 (see Tables 11-13)                ov_mc_t_pts_er_min                  s
            (RofA not specified in 1547)
        HV MC Curve Point OV_T1-3 Setting                           ov_mc_t_pts                         s
        HV MC Curve Point OV_T1-3 (RofA not specified in 1547)      ov_mc_t_pts_er_max                  s

        :return: dict with keys shown above.
        """
        pass

    def set_ov_mc(self, params=None):
        """
        Set Overvoltage Momentary Cessation (MC) Parameters - IEEE 1547 Table 36
        """
        pass

    def get_uv_mc(self, params=None):
        """
        Get Overvoltage Momentary Cessation (MC) Parameters - IEEE 1547 Table 36
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                   units
        _______________________________________________________________________________________________________________
        LV MC Curve Point UV_V1-3 (see Tables 11-13)                uv_mc_v_pts_er_min                V p.u.
            (RofA not specified in 1547)
        LV MC Curve Point UV_V1-3 Setting                           uv_mc_v_pts                       V p.u.
        LV MC Curve Point UV_V1-3 (RofA not specified in 1547)      uv_mc_v_pts_er_max                V p.u.
        LV MC Curve Point UV_T1-3 (see Tables 11-13)                uv_mc_t_pts_er_min                s
            (RofA not specified in 1547)
        LV MC Curve Point UV_T1-3 Setting                           uv_mc_t_pts                       s
        LV MC Curve Point UV_T1-3 (RofA not specified in 1547)      uv_mc_t_pts_er_max                s

        :return: dict with keys shown above.
        """
        pass

    def set_uv_mc(self, params=None):
        """
        Set Undervoltage Momentary Cessation (MC) Parameters - IEEE 1547 Table 36
        """
        pass

    def set_cease_to_energize(self, params=None):
        """

        A DER can be directed to cease to energize and trip by changing the Permit service setting to “disabled” as
        described in IEEE 1574 Section 4.10.3.
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                 units
        ______________________________________________________________________________________________________________
        Cease to energize and trip                              cease_to_energize               bool (True=Enabled)

        """
        return self.set_es_permit_service(params={'es_permit_service': params['cease_to_energize']})

    # Additional functions outside of IEEE 1547-2018
    def get_conn(self):
        """
        Get Connection - DER Connect/Disconnect Switch
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Connect/Disconnect Enable                                   conn                     bool (True=Enabled)
        """
        pass

    def set_conn(self, params=None):
        """
        Set Connection
        """
        pass

    def set_error(self, params=None):
        """
        Set Error, for testing Monitoring Data in DER

        error = set error
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
                print('DER 1547 Info %s' % info)
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
