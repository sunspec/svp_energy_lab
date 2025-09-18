"""
DER1547 methods defined for Opal simulator

Note that this acts as an abstraction for values returned from der_opal.py

It maps the IEEE 1547 names from der1547.py to/from der.py names and uses the methods from
der_opal.py to perform the read/write actions
"""

try:
    import os
    from . import der1547
    from . import der
    from . import der_opal
    import subprocess
    import socket
except Exception as e:
    print(('Import problem in der1547_opal.py: %s' % e))
    raise der1547.DER1547Error('Import problem in der1547_opal.py: %s' % e)

opal_info = der_opal.opal_info



def der1547_info():
    """
    Returns information about the Opal simulator from the clas der_opal.py.

    Returns:
        dict: A dictionary containing information about the Opal simulator.
    """
    return opal_info


GROUP_NAME = der_opal.GROUP_NAME
def params(info, group_name):

    """
    Retrieves the parameters for the DER Opal simulator based on the provided group name.

    Parameters:
    -----------
        info (dict): A dictionary containing information about the DER Opal simulator.
        group_name (str): The name of the group to retrieve the parameters for.
    """
    der_opal.params(info, group_name)





class DER1547(der1547.DER1547):
    """
    OPAL-RT real-time simulator implementation of IEEE 1547 DER interface.
    
    This class extends the base DER1547 class to provide OPAL-RT specific 
    functionality for Hardware-in-the-Loop (HIL) DER simulation and testing.
    
    Key features:
    - Interfaces with OPAL-RT real-time simulator for DER model control
    - Translates between abstract 1547 parameters and OPAL model variables
    - Provides synchronized data acquisition from simulation subsystems
    - Supports dynamic model parameter updates during runtime
    - Enables high-fidelity power system simulation with DER models
    
    The class leverages OPAL-RT's API to interact with real-time DER models
    while maintaining compliance with IEEE 1547 testing requirements.

    Methods:
    --------
    param_value(name)
        Returns parameter value from the OPAL model
    config()
        Returns OPAL model configuration
    info()
        Returns information about the OPAL DER model
    get_const_pf() 
        Get Constant Power Factor Mode control settings
    set_const_pf(params)
        Set Constant Power Factor Mode control settings
    get_qv()
        Get Volt-Var control settings
    set_qv(params)
        Set Volt-Var control settings
    get_const_q()
        Get Constant Reactive Power Mode control settings
    set_const_q(params)
        Set Constant Reactive Power Mode control settings
    get_pf()
        Get the frequency-Active power mode parameters (Droop)
    set_pf(params)
        Set the frequency-Active power mode parameters
    set_p_lim(params)
        Set the active power limits
    get_qp()
        Get the Watt-Var control settings
    set_qp(params)
        Set the Watt-Var control settings
    get_pv()
        Get Volt-Watt control settings
    set_pv(params)
        Set Volt-Watt control settings
    get_ui()
        Get unintenyional islanding control settings
    set_ui(params)
        Set unintenyional islanding control settings
    """

    def __init__(self, ts, group_name, support_interfaces=None):
        der1547.DER1547.__init__(self, ts, group_name, support_interfaces=support_interfaces)  # inherit der1547 functions
        self.opal = der_opal.DER(ts, group_name, support_interfaces=support_interfaces)  # create DER Opal object to send commands
        # self.ts.log_debug('self.opal in der1547_opal is %s' % self.opal)

    def param_value(self, name):
        return self.opal.param_value(name)

    def config(self):
        return self.opal.config()

    def open(self):
        pass

    def close(self):
        pass

    def info(self):
        return self.opal.info()

    def get_nameplate(self):
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

        pass

    def get_settings(self):
        """
        Get settings information

        :return: params dict with keys shown in nameplate.
        """
        pass

    def set_settings(self, params=None):
        """
        Set settings information

        :return: params dict with keys shown in nameplate.
        """

        pass

    def get_configuration(self):
        """
        Get configuration information

        :return: params dict with keys shown in nameplate.
        """
        pass

    def set_configuration(self, params=None):
        """
        Set configuration information. params are those in get_nameplate().
        """

        return {}

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

        Operational State                                           mn_st                              dict of bools
            {'mn_op_local': System in local/maintenance state
             'mn_op_lockout': System locked out
             'mn_op_starting': Start command has been received
             'mn_op_stopping': Emergency Stop command has been received
             'mn_op_started': Started
             'mn_op_stopped': Stopped
             'mn_op_permission_to_start': Start Permission Granted
             'mn_op_permission_to_stop': Stop Permission Granted}

        Connection State                                            mn_conn                            dict of bools
            {'mn_conn_connected_idle': Idle-Connected
             'mn_conn_connected_generating': On-Connected
             'mn_conn_connected_charging': On-Charging-Connected
             'mn_conn_off_available': Off-Available
             'mn_conn_off_not_available': Off-Not-Available
             'mn_conn_switch_closed_status': Switch Closed
             'mn_conn_switch_closed_movement': Switch Moving}

        Alarm Status                                                mn_alrm                            dict of bools
            Reported Alarm Status matches the device
            present alarm condition for alarm and no
            alarm conditions. For test purposes only, the
            DER manufacturer shall specify at least one
            way an alarm condition that is supported in
            the protocol being tested can be set and
            cleared.
            {'mn_alm_system_comm_error': System Communication Error
             'mn_alm_priority_1': System Has Priority 1 Alarms
             'mn_alm_priority_2': System Has Priority 2 Alarms
             'mn_alm_priority_3': System Has Priority 3 Alarms
             'mn_alm_storage_chg_max': Storage State of Charge at Maximum. Maximum Usable State of Charge reached.
             'mn_alm_storage_chg_high': Storage State of Charge is Too High. Maximum Reserve reached.
             'mn_alm_storage_chg_low': Storage State of Charge is Too Low. Minimum Reserve reached.
             'mn_alm_storage_chg_depleted': Storage State of Charge is Depleted. Minimum Usable State of Charge Reached.
             'mn_alm_internal_temp_high': Storage Internal Temperature is Too High
             'mn_alm_internal_temp_low': Storage External (Ambient) Temperature is Too High}

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
        Constant Power Factor Absorbing Setting                 const_pf_abs                     VAr p.u
        Constant Power Factor Injecting Setting                 const_pf_inj                     VAr p.u
        Maximum response time to maintain constant power        const_pf_olrt                    s
            factor. (Not in 1547)

        :return: dict with keys shown above.
        """

        pf = self.opal.fixed_pf()
        ieee_dict = {}
        if pf.get('Ena') is not None:
            ieee_dict['const_pf_mode_enable'] = pf['Ena']
        if pf.get('PF') is not None:
            if pf['PF'] >= 0.:
                ieee_dict['const_pf_abs'] = pf['PF']
                ieee_dict['const_pf_excitation'] = 'abs'
            else:
                ieee_dict['const_pf_inj'] = pf['PF']
                ieee_dict['const_pf_excitation'] = 'inj'
        if pf.get('RvrtTms') is not None:
            ieee_dict['const_pf_olrt'] = pf['RvrtTms']

        return ieee_dict

    def set_const_pf(self, params=None):
        """
        Set Constant Power Factor Mode control settings.
        ________________________________________________________________________________________________________________
        Parameter                                               params dict key                     units
        ________________________________________________________________________________________________________________
        Constant Power Factor Mode Select                       const_pf_mode_enable             bool (True=Enabled)
        Constant Power Factor Excitation                        const_pf_excitation              str ('inj', 'abs')
        Constant Power Factor Absorbing Setting                 const_pf_abs                     VAr p.u
        Constant Power Factor Injecting Setting                 const_pf_inj                     VAr p.u
        Maximum response time to maintain constant power        const_pf_olrt                    s
            factor. (Not in 1547)

        :return: dict with keys shown above.
        """
        new_params = {}

        if 'const_pf_mode_enable' in params:
            new_params['Ena'] = params['const_pf_mode_enable']

        if 'const_pf_excitation' in params and 'const_pf_inj' in params:
            if params['const_pf_excitation'] == 'inj':
                new_params['PF'] = -1*abs(params['const_pf_inj'])
        if 'const_pf_excitation' in params and 'const_pf_abs' in params:
            if params['const_pf_excitation'] == 'abs':
                new_params['PF'] = abs(params['const_pf_abs'])
        if 'const_pf_olrt' in params:
            new_params['RvrtTms'] = params['const_pf_olrt']

        return self.opal.fixed_pf(params=new_params)

    def get_qv(self):
        """
        Get Q(V), Volt-Var, Voltage-Reactive Power Mode
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Voltage-Reactive Power Mode Enable                          qv_mode_enable               bool (True=Enabled)
        Vref (0.95-1.05)                                            qv_vref                      V p.u.
        Autonomous Vref Adjustment Enable                           qv_vref_auto_mode            str
        Vref adjustment time Constant (300-5000)                    qv_vref_olrt                 s
        Q(V) Curve Point V1-4 (list), [0.95, 0.99, 1.01, 1.05]      qv_curve_v_pts                  V p.u.
        Q(V) Curve Point Q1-4 (list), [1., 0., 0., -1.]             qv_curve_q_pts                  VAr p.u.
        Q(V) Open Loop Response Time Setting  (1-90)                qv_olrt                      s
        """

        vv = self.opal.volt_var()

        ieee_dict = {}
        if vv.get('Ena') is not None:
            ieee_dict['qv_mode_enable'] = vv['Ena']
        if vv.get('curve') is not None:
            if vv['curve'].get('v') is not None:
                ieee_dict['qv_curve_v_pts'] = vv['curve'].get('v')
            if vv['curve'].get('var') is not None:
                ieee_dict['qv_curve_q_pts'] = vv['curve'].get('var')
            if vv['curve'].get('vref') is not None:
                ieee_dict['qv_vref'] = vv['curve'].get('vref')
            if vv['curve'].get('RmpPtTms') is not None:
                ieee_dict['qv_olrt'] = vv['curve'].get('RmpPtTms')

        return ieee_dict

    def set_qv(self, params=None):
        """
        Set Q(V), Volt-Var
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Voltage-Reactive Power Mode Enable                          qv_mode_enable               bool (True=Enabled)
        Vref (0.95-1.05)                                            qv_vref                      V p.u.
        Autonomous Vref Adjustment Enable                           qv_vref_auto_mode            str
        Vref adjustment time Constant (300-5000)                    qv_vref_olrt                 s
        Q(V) Curve Point V1-4 (list), [0.95, 0.99, 1.01, 1.05]      qv_curve_v_pts                  V p.u.
        Q(V) Curve Point Q1-4 (list), [1., 0., 0., -1.]             qv_curve_q_pts                  VAr p.u.
        Q(V) Open Loop Response Time Setting  (1-90)                qv_olrt                      s
        ______________________________________________________________________________________________________________
        """

        new_params = {'curve': {}}
        if params.get('qv_mode_enable') is not None:
            new_params['Ena'] = params['qv_mode_enable']
        if params.get('qv_curve_v_pts') is not None:
            new_params['curve']['v'] = params['qv_curve_v_pts']
        if params.get('qv_curve_q_pts') is not None:
            new_params['curve']['var'] = params['qv_curve_q_pts']
        if params.get('qv_vref') is not None:
            new_params['curve']['vref'] = params['qv_vref']
        if params.get('qv_olrt') is not None:
            new_params['curve']['RmpPtTms'] = params['qv_olrt']

        return self.opal.volt_var(params=new_params)

    def get_const_q(self):
        """
        Get Constant Reactive Power Mode
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                     units
        ______________________________________________________________________________________________________________
        Constant Reactive Power Mode Enable                     const_q_mode_enable              bool (True=Enabled)
        Constant Reactive Power Excitation (not specified in    const_q_mode_excitation          str ('inj', 'abs')
            1547)
        Constant Reactive power setting (See Table 7)           const_q                          VAr p.u.
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
        Maximum Response Time to maintain constant reactive     const_q_olrt                     s
            power (not specified in 1547)
        Maximum Response Time to maintain constant reactive     const_q_olrt_er_max                 s
            power(not specified in 1547)

        :return: dict with keys shown above.
        """

        cq = self.opal.reactive_power()
        ieee_dict = {}
        if cq.get('Ena') is not None:
            ieee_dict['const_q_mode_enable'] = cq['Ena']
        if cq.get('Q') is not None:
            if cq['Q'] <= 0.:
                ieee_dict['const_q'] = cq['Q']
                ieee_dict['const_q_mode_excitation'] = 'abs'
            else:
                ieee_dict['const_q'] = cq['Q']
                ieee_dict['const_q_mode_excitation'] = 'inj'
        if cq.get('RvrtTms') is not None:
            ieee_dict['const_q_olrt'] = cq['RvrtTms']

        return ieee_dict

    def set_const_q(self, params=None):
        """
                Set Constant Reactive Power Mode
                ______________________________________________________________________________________________________________
                Parameter                                               params dict key                     units
                ______________________________________________________________________________________________________________
                Constant Reactive Power Mode Enable                     const_q_mode_enable              bool (True=Enabled)
                Constant Reactive Power Excitation (not specified in    const_q_mode_excitation          str ('inj', 'abs')
                    1547)
                Constant Reactive power setting (See Table 7)           const_q                          VAr p.u.
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
                Maximum Response Time to maintain constant reactive     const_q_olrt                     s
                    power (not specified in 1547)
                Maximum Response Time to maintain constant reactive     const_q_olrt_er_max                 s
                    power(not specified in 1547)
        """
        new_params = {}

        if 'const_q_mode_enable' in params:
            new_params['Ena'] = params['const_q_mode_enable']

        if 'const_q_excitation' in params and 'const_q' in params:
            if params['const_q_excitation'] == 'inj':
                new_params['Q'] = -1 * abs(params['const_q'])
        if 'const_q_excitation' in params and 'const_q' in params:
            if params['const_q_excitation'] == 'abs':
                new_params['Q'] = abs(params['const_q'])
        if 'const_q_olrt' in params:
            new_params['RvrtTms'] = params['const_q_olrt']

        return self.opal.reactive_power(params=new_params)

    def get_conn(self):
        """
        Get Connection

        conn = bool for connection
        """

        return {}

    def set_conn(self, params=None):
        """
        This information is used to update functional and mode settings for the
        Constant Reactive Power Mode. This information may be written.

        conn = bool for connection
        """

        return {}

    def get_pf(self):
        """
        Get P(f), Frequency-Active Power Mode Parameters - IEEE 1547 Table 38
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          pf_mode_enable               bool (True=Enabled)
        P(f) Overfrequency Droop dbOF Setting                       pf_dbof                      Hz
        P(f) Underfrequency Droop dbUF Setting                      pf_dbuf                      Hz
        P(f) Overfrequency Droop kOF  Setting                       pf_kof                       unitless
        P(f) Underfrequency Droop kUF Setting                       pf_kuf                       unitless
        P(f) Open Loop Response Time Setting                        pf_olrt                      s

        :return: dict with keys shown above.
        """

        ieee_dict = {}
        fw = self.opal.freq_watt()
        if fw.get('Ena') is not None:
            ieee_dict['pf_mode_enable'] = fw.get('Ena')
        if fw.get('curve') is not None:
            if fw['curve'].get('dbOF') is not None:
                ieee_dict['pf_dbof'] = fw.get('dbOF')
            if fw['curve'].get('dbUF') is not None:
                ieee_dict['pf_dbuf'] = fw.get('dbUF')
            if fw['curve'].get('kOF') is not None:
                ieee_dict['pf_kof'] = fw.get('kOF')
            if fw['curve'].get('kUF') is not None:
                ieee_dict['pf_kuf'] = fw.get('kUF')
            if fw['curve'].get('RmpTms') is not None:
                ieee_dict['pf_olrt'] = fw.get('RmpTms')

        return ieee_dict

    def set_pf(self, params=None):
        """
        Set Frequency-Active Power Mode.
        """

        new_params = {}
        if params.get('pf_mode_enable') is not None:
            new_params['Ena'] = params['pf_mode_enable']
        if params.get('pf_dbof') is not None:
            new_params['dbOF'] = params['pf_dbof']
        if params.get('pf_dbuf') is not None:
            new_params['dbUF'] = params['pf_dbuf']
        if params.get('pf_kof') is not None:
            new_params['kOF'] = params['pf_kof']
        if params.get('pf_kuf') is not None:
            new_params['kUF'] = params['pf_kuf']
        if params.get('pf_olrt') is not None:
            new_params['RmpTms'] = params['pf_olrt']

        return self.opal.freq_watt(params=new_params)

    def get_p_lim(self):
        """
        Get Limit maximum active power - IEEE 1547 Table 40
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          p_lim_mode_enable         bool (True=Enabled)
        Maximum Active Power Min                                    p_lim_w_er_min               P p.u.
        Maximum Active Power                                        p_lim_w                   P p.u.
        Maximum Active Power Max                                    p_lim_w_er_max               P p.u.
        """

        ieee_dict = {}
        p_lim = self.opal.limit_max_power()
        if p_lim.get('Ena') is not None:
            ieee_dict['p_lim_mode_enable'] = p_lim.get('Ena')
        if p_lim.get('WMaxPct') is not None:
            ieee_dict['p_lim_w'] = p_lim.get('WMaxPct')

        return ieee_dict

    def set_p_lim(self, params=None):
        """
        Set Limit maximum active power - IEEE 1547 Table 40
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                 units
        ______________________________________________________________________________________________________________
        Frequency-Active Power Mode Enable                          p_lim_mode_enable         bool (True=Enabled)
        Maximum Active Power Min                                    p_lim_w_er_min               P p.u.
        Maximum Active Power                                        p_lim_w                   P p.u.
        Maximum Active Power Max                                    p_lim_w_er_max               P p.u.
        """
        new_params = {}
        if params.get('p_lim_mode_enable') is not None:
            new_params['Ena'] = params['p_lim_mode_enable']
        if params.get('p_lim_w') is not None:
            new_params['WMaxPct'] = params['p_lim_w']

        return self.opal.limit_max_power(new_params)

    def get_qp(self):
        """
        Get Q(P) parameters. [Watt-Var]
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        Active Power-Reactive Power (Watt-VAr) Enable               qp_mode_enable                   bool
        P-Q curve P1-3 Generation Setting (list)                    qp_curve_p_gen_pts               P p.u.
        P-Q curve Q1-3 Generation Setting (list)                    qp_curve_q_gen_pts               VAr p.u.
        P-Q curve P1-3 Load Setting (list)                          qp_curve_p_load_pts              P p.u.
        P-Q curve Q1-3 Load Setting (list)                          qp_curve_q_load_pts              VAr p.u.
        QP Open Loop Response Time Setting                          qp_olrt                          s
        """

        ieee_dict = {}
        wv = self.opal.watt_var()
        if wv.get('Ena') is not None:
            ieee_dict['qp_mode_enable'] = wv.get('Ena')
        if wv.get('curve') is not None:
            if wv['curve'].get('w') is not None:
                ieee_dict['qp_curve_p_gen_pts'] = wv['curve'].get('w')
            if wv['curve'].get('var') is not None:
                ieee_dict['qp_curve_q_gen_pts'] = wv['curve'].get('var')
            if wv['curve'].get('RmpPtTms') is not None:
                ieee_dict['qp_olrt'] = wv['curve'].get('RmpPtTms')

        return ieee_dict

    def set_qp(self, params=None):
        """
        Set Q(P) parameters. [Watt-Var]
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        Active Power-Reactive Power (Watt-VAr) Enable               qp_mode_enable                   bool
        P-Q curve P1-3 Generation Setting (list)                    qp_curve_p_gen_pts               P p.u.
        P-Q curve Q1-3 Generation Setting (list)                    qp_curve_q_gen_pts               VAr p.u.
        P-Q curve P1-3 Load Setting (list)                          qp_curve_p_load_pts              P p.u.
        P-Q curve Q1-3 Load Setting (list)                          qp_curve_q_load_pts              VAr p.u.
        QP Open Loop Response Time Setting                          qp_olrt                          s
        """

        new_params = {'curve': {}}
        if params.get('qp_mode_enable') is not None:
            new_params['Ena'] = params.get('qp_mode_enable')
        if params.get('qp_curve_p_gen_pts') is not None:
            new_params['curve']['w'] = params.get('qp_curve_p_gen_pts')
        if params.get('qp_curve_p_gen_pts') is not None:
            new_params['curve']['var'] = params.get('qp_curve_q_gen_pts')
        if params.get('qp_olrt') is not None:
            new_params['curve']['RmpPtTms'] = params.get('qp_olrt')

        return self.opal.watt_var(new_params)

    def get_pv(self, params=None):
        """
        Get P(V), Voltage-Active Power (Volt-Watt), Parameters
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                         units
        ______________________________________________________________________________________________________________
        Voltage-Active Power Mode Enable                            pv_mode_enable                       bool
        P(V) Curve Point V1-2 Setting (list)                        pv_curve_v_pts                       V p.u.
        P(V) Curve Point P1-2 Setting (list)                        pv_curve_p_pts                       P p.u.
        P(V) Curve Point P1-P'2 Setting (list)                      pv_curve_p_bidrct_pts                P p.u.
        P(V) Open Loop Response time Setting (0.5-60)               pv_olrt                              s
        """

        ieee_dict = {}
        vw = self.opal.volt_watt()
        if vw.get('Ena') is not None:
            ieee_dict['pv_mode_enable'] = vw.get('Ena')
        if vw.get('curve') is not None:
            if vw['curve'].get('v') is not None:
                ieee_dict['pv_curve_v_pts'] = vw['curve'].get('v')
            if vw['curve'].get('w') is not None:
                ieee_dict['pv_curve_p_pts'] = vw['curve'].get('w')
            if vw['curve'].get('RmpTms') is not None:
                ieee_dict['pv_olrt'] = vw['curve'].get('RmpTms')

        return ieee_dict

    def set_pv(self, params=None):
        """
        Set P(V), Voltage-Active Power (Volt-Watt), Parameters
        ______________________________________________________________________________________________________________
        Parameter                                                   params dict key                         units
        ______________________________________________________________________________________________________________
        Voltage-Active Power Mode Enable                            pv_mode_enable                       bool
        P(V) Curve Point V1-2 Setting (list)                        pv_curve_v_pts                       V p.u.
        P(V) Curve Point P1-2 Setting (list)                        pv_curve_p_pts                       P p.u.
        P(V) Curve Point P1-P'2 Setting (list)                      pv_curve_p_bidrct_pts                P p.u.
        P(V) Open Loop Response time Setting (0.5-60)               pv_olrt                              s

        :return: dict with keys shown above.
        """
        new_params = {'curve': {}}
        if params.get('pv_mode_enable') is not None:
            new_params['Ena'] = params.get('pv_mode_enable')
        if params.get('pv_curve_v_pts') is not None:
            new_params['curve']['v'] = params.get('pv_curve_v_pts')
        if params.get('pv_curve_p_pts') is not None:
            new_params['curve']['w'] = params.get('pv_curve_p_pts')
        if params.get('pv_olrt') is not None:
            new_params['curve']['RmpTms'] = params.get('pv_olrt')

        return self.opal.volt_watt(new_params)

    def get_es_permit_service(self):
        """
        Get Permit Service Mode Parameters - IEEE 1547 Table 39
        ______________________________________________________________________________________________________________
        Parameter                                               params dict key                 units
        ______________________________________________________________________________________________________________
        Permit service                                          es_permit_service            bool (True=Enabled)
        ES Voltage Low (RofA not specified in 1547)             es_v_low_er_min                 V p.u.
        ES Voltage Low Setting                                  es_v_low                     V p.u.
        ES Voltage Low (RofA not specified in 1547)             es_v_low_er_max                 V p.u.
        ES Voltage High (RofA not specified in 1547)            es_v_high_er_min                V p.u.
        ES Voltage High Setting                                 es_v_high                    V p.u.
        ES Voltage High (RofA not specified in 1547)            es_v_high_er_max                V p.u.
        ES Frequency Low (RofA not specified in 1547)           es_f_low_er_min                 Hz
        ES Frequency Low Setting                                es_f_low                     Hz
        ES Frequency Low (RofA not specified in 1547)           es_f_low_er_max                 Hz
        ES Frequency Low (RofA not specified in 1547)           es_f_high_er_min                Hz
        ES Frequency High Setting                               es_f_high                    Hz
        ES Frequency Low (RofA not specified in 1547)           es_f_high_er_max                Hz
        ES Randomized Delay                                     es_randomized_delay          bool (True=Enabled)
        ES Delay (RofA not specified in 1547)                   es_delay_er_min                 s
        ES Delay Setting                                        es_delay                     s
        ES Delay (RofA not specified in 1547)                   es_delay_er_max                 s
        ES Ramp Rate Min (RofA not specified in 1547)           es_ramp_rate_er_min             %/s
        ES Ramp Rate Setting                                    es_ramp_rate                 %/s
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
        Unintentional Islanding Mode (enabled/disabled). This       ui_mode_enable                   bool
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

        ieee_dict = {}
        ui = self.opal.UI()
        if ui.get('Ena') is not None:
            ieee_dict['ui_mode_enable'] = ui.get('Ena')

        ieee_dict['ui_capability_er'] = ui.get('ui_capability_er')
        return ieee_dict



    def set_ui(self, params=None):
        """
        Set Unintentional Islanding Parameters
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        Unintentional Islanding Mode (enabled/disabled). This       ui_mode_enable                   bool
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
        """
        new_params = {}
        if params.get('ui_mode_enable') is not None:
            new_params['Ena'] = params['ui_mode_enable']

        return self.opal.UI(new_params)

    def get_ov(self, params=None):
        """
        Get Overvoltage Trip Parameters - IEEE 1547 Table 35
        _______________________________________________________________________________________________________________
        Parameter                                                   params dict key                     units
        _______________________________________________________________________________________________________________
        HV Trip Curve Point OV_V1-3 (see Tables 11-13)              ov_trip_v_pts_er_min                V p.u.
            (RofA not specified in 1547)
        HV Trip Curve Point OV_V1-3 Setting                         ov_trip_v_pts                    V p.u.
        HV Trip Curve Point OV_V1-3 (RofA not specified in 1547)    ov_trip_v_pts_er_max                V p.u.
        HV Trip Curve Point OV_T1-3 (see Tables 11-13)              ov_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        HV Trip Curve Point OV_T1-3 Setting                         ov_trip_t_pts                    s
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
        LV Trip Curve Point UV_V1-3 Setting                         uv_trip_v_pts                    V p.u.
        LV Trip Curve Point UV_V1-3 (RofA not specified in 1547)    uv_trip_v_pts_er_max                V p.u.
        LV Trip Curve Point UV_T1-3 (see Tables 11-13)              uv_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        LV Trip Curve Point UV_T1-3 Setting                         uv_trip_t_pts                    s
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
        OF Trip Curve Point OF_F1-3 Setting                         of_trip_f_pts                    Hz
        OF Trip Curve Point OF_F1-3 (RofA not specified in 1547)    of_trip_f_pts_er_max                Hz
        OF Trip Curve Point OF_T1-3 (see Tables 11-13)              of_trip_t_pts_er_min                s
            (RofA not specified in 1547)
        OF Trip Curve Point OF_T1-3 Setting                         of_trip_t_pts                    s
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
        pass
