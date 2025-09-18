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
"""
This abstraction layer has been heavily commented to go in details about what we can usually find in an abstraction 
layer. It has the purpose to help the development of new code. Look into der_commented.py for a commented der driver.
"""

"""
Import section: importlib here is necessary to do the scan function located at the bottom of the code
"""
import sys
import os
import glob
import importlib

der_modules = {} # Initialised during the scan function at the bottom. It includes all the driver with der_*.py
DER_DEFAULT_ID = 'der'
"""
Params function: This function initialise the overall parameter sections of der devices. Then, if a mode is selected,
it will fetch that specific driver parameter section. Therefore this params function is responsible for the start of the
der parameters section of the SVP UI where a mode can be selected. Then, when selecting a mode it will show the param 
section of the corresponding driver of the mode selected.
"""
def params(info, id=None, label='DER', group_name=None, active=None, active_value=None):
    """
    Set up parameters for DER (Distributed Energy Resource) configuration.

    Arguments:
    ----------
        info (object)      : The information object to add parameters to.
        id (str)           : An optional identifier for the DER (used if multiple DERs).
        label (str)        : A label for the DER (default is 'DER').
        group_name (str)   : An optional group name for the parameters.
        active (str)       : An optional active parameter name (assign another parameter to activate the current
        parameter or group of parameters).
        active_value (any) : An optional active parameter value. (define the value needed of the other parameter
        assigned in 'active' to activate the current parameters)

    Returns:
        None
    """
    if group_name is None:
        group_name = DER_DEFAULT_ID
    else:
        group_name += '.' + DER_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    name = lambda name: group_name + '.' + name #Used to create the standard name chain sor self.ts (DER.name)
    info.param_group(group_name, label='%s Parameters' % label,  active=active, active_value=active_value, glob=True)
    info.param(name('mode'), label='%s Mode' % label, default='Disabled', values=['Disabled'])
    for mode, m in der_modules.items():
        m.params(info, group_name=group_name)

'''
The init function is used in scripts to initialize the devices. This function will fetch the correct driver and
initialise the device driver by calling the specific device Class (DER in this case).
'''

def der_init(ts, id=None, group_name=None, support_interfaces=None):
    """
    Create specific DER (Distributed Energy Resource) implementation instances and initialize the selected driver in SVP.

    Arguments:
    ----------
        ts (object)               : The test script object.
        id (str)                  : An optional identifier for the DER. (For multiple DERs)
        group_name (str)          : An optional group name for the parameters.
        support_interfaces (list) : A list of supported interfaces. (Depending of the requirement of the device, it
        might need to be linked to other devices. ex.: a simulated Opal DER will need to be linked with an Opal HIL
        simulator)

    Returns:
        object: An instance of the specific DER implementation.
    """
    if group_name is None:
        group_name = DER_DEFAULT_ID
    else:
        group_name += '.' + DER_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    print('run group_name = %s' % group_name)
    mode = ts.param_value(group_name + '.' + 'mode')
    sim = None
    if mode != 'Disabled':
        sim_module = der_modules.get(mode)
        if sim_module is not None:
            try:
                sim = sim_module.DER(ts, group_name, support_interfaces=support_interfaces)
            except TypeError as e:
                sim = sim_module.DER(ts, group_name)
        else:
            raise DERError('Unknown DER system mode: %s' % mode)

    return sim


class DERError(Exception):
    """
    Exception to wrap all der generated exceptions.
    """
    pass

"""
DER Class: It represents the mother Class of a DER or the Abstraction layer for DERs. It is meant to represent a template
of how a driver need to be coded. It is important to follow this specific layout and redefine the function in the device
driver since the scripts are coded to be usable by any driver. This is why most functions are empty and skipped. However,
They often include a description of what they should include
"""
class DER(object):
    """
    Template for DER/EUT implementations. This class can be used as a base class or
    independent DER classes can be created containing the methods contained in this class.

    Attributes:
    -----------
    None

    Methods:
    --------
    config()                        : Configure the DER settings.
    open()                          : Open communication with the DER.
    close()                         : Close communication with the DER.
    nameplate()                     : Retrieve nameplate information of the DER.
    measurements()                  : Get measurements from the DER.
    setting(params=None)            : Set or get DER settings.
    conn_status(params=None)        : Get the connection status of the DER.
    controls_status(params=None)    : Get the control status of the DER.
    connect(params=None)            : Connect, disconnect or get the DER function settings.
    fixed_pf(params=None)           : Set or get fixed power factor settings.
    limit_max_power(params=None)    : Set or get maximum power limit.
    volt_var(params=None)           : Set or get volt-var control settings.
    volt_var_curve(id, params=None) : Set or get volt-var curve settings.
    freq_watt(self, params=None)    : Set or get frequency-watt control settings.
    freq_watt_curve(id, params=None): Set or get frequency-watt curve settings.
    freq_watt_param(params=None)    : Set or get frequency-watt parameters.
    soft_start_ramp_rate(params=None): Set or get soft start ramp rate.
    ramp_rate(params=None)          : Set or get general ramp rate.
    volt_watt(params=None)          : Set or get volt-watt mode settings.
    reactive_power(params=None)     : Set or get reactive power settings.
    active_power(params=None)       : Set or get active power settings.
    storage(params=None)            : Set or get energy storage settings.
    frt_stay_connected_high(params=None): Set or get high frequency ride-through stay connected settings.
    frt_stay_connected_low(params=None): Set or get low frequency ride-through stay connected settings.
    frt_trip_high(params=None)      : Set or get high frequency ride-through trip settings.
    frt_trip_low(params=None)       : Set or get low frequency ride-through trip settings.
    vrt_stay_connected_high(params=None): Set or get high voltage ride-through stay connected settings.
    vrt_stay_connected_low(params=None): Set or get low voltage ride-through stay connected settings.
    vrt_trip_high(params=None)      : Set or get high voltage ride-through trip settings.
    vrt_trip_low(params=None)       : Set or get low voltage ride-through trip settings.
    watt_var(params=None)           : Set or get watt-var control settings.
    deactivate_all_fct()            : Deactivate all functions.
    phase()                         : Get the phase configuration of the DER.
    v_nom()                         : Get the nominal voltage of the DER.
    v_in_nom()                      : Get the nominal input voltage of the DER.
    v_low()                         : Get the low voltage limit of the DER.
    v_high()                        : Get the high voltage limit of the DER.
    s_rated()                       : Get the rated apparent power of the DER.
    p_rated()                       : Get the rated active power of the DER.
    p_min()                         : Get the minimum active power of the DER.
    var_rated()                     : Get the rated reactive power of the DER.
    f_nom()                         : Get the nominal frequency of the DER.
    f_min()                         : Get the minimum frequency of the DER.
    f_max()                         : Get the maximum frequency of the DER.
    absorb()                        : Get the energy absorption capability of the DER.
    startup_time()                  : Get the startup time of the DER.
    imbalance_resp()                : Get the imbalance response of the DER.    
    """

    def __init__(self, ts, group_name, support_interfaces=None):
        self.ts = ts
        self.group_name = group_name
        self.hil = None
        if support_interfaces is not None:
            if support_interfaces.get('hil') is not None:
                self.hil = support_interfaces.get('hil')
        else:
            self.hil = None

    def config(self):
        """ Perform any configuration for the simulation based on the previously provided parameters. """
        pass

    def open(self):
        """ Open the communications resources associated with the grid simulator. """
        pass

    def close(self):
        """ Close any open communications resources associated with the grid simulator. """
        pass

    def nameplate(self):
        """
        returns a dict with the following keys:
            WRtg
            VARtg
            VArRtgQ1
            VArRtgQ2
            VArRtgQ3
            VArRtgQ4
            ARtg
            PFRtgQ1
            PFRtgQ2
            PFRtgQ3
            PFRtgQ4
            WHRtg
            AhrRtg
            MaxChaRte
            MaxDisChaRte
        """
        pass

    def measurements(self):
        """ Get measurement data.

        Params:
            A - Current
            AphA - Current on Phase A
            AphB - Current on Phase B
            AphC - Current on Phase C
            PPVphAB - Phase-phase voltage between A and B phases
            PPVphBC - Phase-phase voltage between B and C phases
            PPVphCA - Phase-phase voltage between C and A phases
            PhVphA - Phase A voltage
            PhVphB - Phase B voltage
            PhVphC - Phase C voltage
            W - Power
            Hz - Frequency
            VA - Apparent Power
            VAr - Reactive Power
            PF - Power factor (displacement power factor)
            WH - Energy (watt-hours)
            DCA - DC current
            DCV - DC voltage
            DCW - DC power
            TmpCab - Cabinet temperature
            TmpSnk - Heatsink temperature
            TmpTrns -
            TmpOt -
            St -
            StVnd -
            Evt1 -
            Evt2 -
            EvtVnd1 -
            EvtVnd2 -
            EvtVnd3 -
            EvtVnd4 -

        :return: Dictionary of measurement data
        """
        pass

    def settings(self, params=None):
        """
        Get/set DER settings.

        :param params: Dictionary of parameters to be updated.
            Params keys:
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

        :return: Dictionary of active settings.
        """

        pass

    def conn_status(self, params=None):
        """ Get status of controls (binary True if active).

        :return: binary of connection status
        """
        pass

    def controls_status(self, params=None):
        """ Get status of controls (binary True if active).

        :return: Dictionary of active controls.
        """
        pass

    def connect(self, params=None):
        """ Get/set connect/disconnect function settings.

        Params:
            Conn - Connected (True/False)
            WinTms - Randomized start time delay in seconds
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for connect.
        """
        pass

    def fixed_pf(self, params=None):
        """ Get/set fixed power factor control settings.

        :param params: Dictionary of parameters. Following keys are supported:
            'Ena': True/False
            'PF': 1.0
            'WinTms': 0
            'RmpTms': 0
            'RvrtTms': 0
        :return: Dictionary of active settings for fixed factor.
        """
        pass

    def limit_max_power(self, params=None):
        """ Get/set max active power control settings.

        Params:
            Ena - Enabled (True/False)
            WMaxPct - Active power maximum as percentage of WMax
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for limit max power.
        """
        pass

    def volt_var(self, params=None):
        """ Get/set volt/var control

        Params:
            Ena - Enabled (True/False)
            ActCrv - Active curve number (0 - no active curve)
            NCrv - Number of curves supported
            NPt - Number of points supported per curve
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for volt/var control.
        """
        pass

    def volt_var_curve(self, id, params=None):
        """ Get/set volt/var curve
            v [] - List of voltage curve points
            var [] - List of var curve points based on DeptRef
            DeptRef - Dependent reference type: 'VAR_MAX_PCT', 'VAR_AVAL_PCT', 'VA_MAX_PCT', 'W_MAX_PCT'
            RmpTms - Ramp timer
            RmpDecTmm - Ramp decrement timer
            RmpIncTmm - Ramp increment timer

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for volt/var curve control.
        """
        pass

    def freq_watt(self, params=None):
        """ Get/set freq/watt control

        Params:
            Ena - Enabled (True/False)
            ActCrv - Active curve number (0 - no active curve)
            NCrv - Number of curves supported
            NPt - Number of points supported per curve
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for freq/watt control.
        """
        pass

    def freq_watt_curve(self, id, params=None):
        """ Get/set freq/watt curve
            hz [] - List of frequency curve points
            w [] - List of power curve points
            CrvNam - Optional description for curve. (Max 16 chars)
            RmpPT1Tms - The time of the PT1 in seconds (time to accomplish a change of 95%).
            RmpDecTmm - Ramp decrement timer
            RmpIncTmm - Ramp increment timer
            RmpRsUp - The maximum rate at which the power may be increased after releasing the frozen value of
                      snap shot function.
            SnptW - 1=enable snapshot/capture mode
            WRef - Reference active power (default = WMax).
            WRefStrHz - Frequency deviation from nominal frequency at the time of the snapshot to start constraining
                        power output.
            WRefStopHz - Frequency deviation from nominal frequency at which to release the power output.
            ReadOnly - 0 = READWRITE, 1 = READONLY

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for freq/watt curve.
        """
        pass

    def freq_watt_param(self, params=None):
        """ Get/set frequency-watt with parameters

        Params:
            Ena - Enabled (True/False)
            HysEna - Enable hysteresis (True/False)
            WGra - The slope of the reduction in the maximum allowed watts output as a function of frequency.
            HzStr - The frequency deviation from nominal frequency (ECPNomHz) at which a snapshot of the instantaneous
                    power output is taken to act as the CAPPED power level (PM) and above which reduction in power
                    output occurs.
            HzStop - The frequency deviation from nominal frequency (ECPNomHz) at which curtailed power output may
                    return to normal and the cap on the power level value is removed.
            HzStopWGra - The maximum time-based rate of change at which power output returns to normal after having
                         been capped by an over frequency event.

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for frequency-watt with parameters control.
        """
        pass

    def soft_start_ramp_rate(self, params=None):
        pass

    def ramp_rate(self, params=None):
        pass

    def volt_watt(self, params=None):
        """ Get/set volt/watt control

        Params:
            Ena - Enabled (True/False)
            ActCrv - Active curve number (0 - no active curve)
            NCrv - Number of curves supported
            NPt - Number of points supported per curve
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds
            curve - curve parameters in the repeating block in another dictionary with parameters:
                    v [] - List of voltage curve points (e.g., [95, 101, 105])
                    w [] - List of watt curve points based on DeptRef (e.g., [100, 100, 0])
                    DeptRef - Dependent reference type:  'W_MAX_PCT', 'W_AVAL_PCT'
                    RmpTms - Ramp timer
                    RmpDecTmm - Ramp decrement timer
                    RmpIncTmm - Ramp increment timer

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for volt/watt control.
        """
        pass

    def reactive_power(self, params=None):
        """ Set the reactive power

        Params:
            Ena - Enabled (True/False)
            VArPct_Mod - Reactive power mode
                    'None' : 0,
                    'WMax': 1,
                    'VArMax': 2,
                    'VArAval': 3,
            VArWMaxPct - Reactive power in percent of WMax. (positive is overexcited, negative is underexcited)
            VArMaxPct - Reactive power in percent of VArMax. (positive is overexcited, negative is underexcited)
            VArAvalPct - Reactive power in percent of VArAval. (positive is overexcited, negative is underexcited)

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for Q control.
        """

        pass

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
        pass

    def storage(self, params=None):
        """ Get/set storage parameters

        Params:
            WChaMax - Setpoint for maximum charge.
            WChaGra - Setpoint for maximum charging rate. Default is MaxChaRte.
            WDisChaGra - Setpoint for maximum discharge rate. Default is MaxDisChaRte.
            StorCtl_Mod - Activate hold/discharge/charge storage control mode. Bitfield value.
            VAChaMax - Setpoint for maximum charging VA.
            MinRsvPct - Setpoint for minimum reserve for storage as a percentage of the nominal maximum storage.
            ChaState (Read only) - Currently available energy as a percent of the capacity rating.
            StorAval (Read only) - State of charge (ChaState) - (storage reserve (MinRsvPct) * capacity rating (AhrRtg))
            InBatV (Read only) - Internal battery voltage.
            ChaSt (Read only) - Charge status of storage device. Enumerated value.
            OutWRte - Percent of max discharge rate.
            InWRte - Percent of max charging rate.
            InOutWRte_WinTms - Time window for charge/discharge rate change.
            InOutWRte_RvrtTms - Timeout period for charge/discharge rate.
            InOutWRte_RmpTms - Ramp time for moving from current setpoint to new setpoint.

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings.
        """
        pass

    def frt_stay_connected_high(self, params=None):
        """ Get/set high frequency ride through (must stay connected curve)

        Params:
            curve:
                t - Time point in the curve
                Hz - Frequency point in the curve

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HFRT control.
        """
        pass

    def frt_stay_connected_low(self, params=None):
        """ Get/set high frequency ride through (must stay connected curve)

        Params:
            curve:
                t - Time point in the curve
                Hz - Frequency point in the curve

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for LFRT control.
        """
        pass

    def frt_trip_high(self, params=None):
        """ Get/set high frequency ride through (trip curve)

        Params:  params = {'curve': 't': [299., 10.], 'Hz': [61.0, 61.8]}
            curve:
                t - Time point in the curve
                Hz - Frequency point in the curve

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HFT control.
        """
        pass

    def frt_trip_low(self, params=None):
        """ Get/set lower frequency ride through (trip curve)

        Params: params = {'curve': 't': [299., 10.], 'Hz': [59.0, 58.2]}
            curve:
                t - Time point in the curve
                Hz - Frequency point in the curve

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for LFT control.
        """
        pass

    def vrt_stay_connected_high(self, params=None):
        """ Get/set high voltage ride through (must stay connected curve)

        Params:
            curve:
                t - Time point in the curve
                v - voltage point in the curve

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HVRT control.
        """
        pass

    def vrt_stay_connected_low(self, params=None):
        """ Get/set low voltage ride through (must stay connected curve)

        Params:
            curve:
                t - Time point in the curve
                v - voltage point in the curve

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for LVRT control.
        """

    def vrt_trip_high(self, params=None):
        """ Get/set high voltage ride through (trip curve)

        Params:  params = {'curve': 't': [60., 10.], 'V': [110.0, 120.0]}
            curve:
                t - Time point in the curve
                Hz - Voltage point in the curve % of Vnom

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HVT control.
        """
        pass

    def vrt_trip_low(self, params=None):
        """ Get/set lower voltage ride through (trip curve)

        Params:  params = {'curve': 't': [60., 10.], 'V': [110.0, 120.0]}
            curve:
                t - Time point in the curve
                Hz - Voltage point in the curve % of Vnom

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for LVT control.
        """
        pass

    def watt_var(self, params=None):
        """watt/var control

        :param params: Dictionary of parameters to be updated.
            'ModEna': True/False
            'ActCrv': 0
            'NCrv': 1
            'NPt': 4
            'WinTms': 0
            'RvrtTms': 0
            'RmpTms': 0
            'curve': {
                 'ActPt': 3
                 'w': [50, 75, 100]
                 'var': [0, 0, -100]
                 'DeptRef': 1
                 'RmpPt1Tms': 0
                 'RmpDecTmm': 0
                 'RmpIncTmm': 0
                 }
        :return: Dictionary of active settings for volt_watt
        """
        pass

    def deactivate_all_fct(self):
        """
        Deactivate all functions.
        """
        pass

    def phase(self):
        """
        Get the phase information of the DER.

        :return: Phase information or a message if not initiated.
        """
        if self._phase is None:
            return "DER Phases hasn't been initiated"
        else:
            return self._phase

    def v_nom(self):
        """
        Get the nominal voltage of the DER.

        :return: Nominal voltage or a message if not initiated.
        """
        if self._v_nom is None:
            return "DER V nominal hasn't been initiated"
        else:
            return self._v_nom
    
    def v_in_nom(self):
        """
        Get the nominal input voltage of the DER.

        :return: Nominal input voltage or a message if not initiated.
        """
        if self._v_in_nom is None:
            return "DER V_in_nominal hasn't been initiated"
        else:
            return self._v_in_nom

    def v_low(self):
        """
        Get the low voltage threshold of the DER.

        :return: Low voltage threshold or a message if not initiated.
        """
        if self._v_nom is None:
            return "DER V low hasn't been initiated"
        else:
            return self._v_low

    def v_high(self):
        """
        Get the high voltage threshold of the DER.

        :return: High voltage threshold or a message if not initiated.
        """
        if self._v_high is None:
            return "DER V high hasn't been initiated"
        else:
            return self._v_high

    def s_rated(self):
        """
        Get the rated apparent power of the DER.

        :return: Rated apparent power or a message if not initiated.
        """
        if self._s_rated is None:
            return "DER S rated hasn't been initiated"
        else:
            return self._s_rated
    
    def p_rated(self):
        """
        Get the rated active power of the DER.

        :return: Rated active power or a message if not initiated.
        """
        if self._p_rated is None:
            return "DER P rated hasn't been initiated"
        else:
            return self._p_rated

    def p_min(self):
        """
        Get the minimum active power of the DER.

        :return: Minimum active power or a message if not initiated.
        """
        if self._p_min is None:
            return "DER P minimum hasn't been initiated"
        else:
            return self._p_min

    def var_rated(self):
        """
        Get the rated reactive power of the DER.

        :return: Rated reactive power or a message if not initiated.
        """
        if self._var_rated is None:
            return "DER VAR rated hasn't been initiated"
        else:
            return self._var_rated

    def f_nom(self):
        """
        Get the nominal frequency of the DER.

        :return: Nominal frequency or a message if not initiated.
        """
        if self._var_rated is None:
            return "DER f nominal hasn't been initiated"
        else:
            return self._f_nom

    def f_min(self):
        """
        Get the minimum frequency of the DER.

        :return: Minimum frequency or a message if not initiated.
        """
        if self._f_min is None:
            return "DER f min hasn't been initiated"
        else:
            return self._f_min

    def f_max(self):
        """
        Get the maximum frequency of the DER.

        :return: Maximum frequency or a message if not initiated.
        """
        if self._f_max is None:
            return "DER f max hasn't been initiated"
        else:
            return self._f_max

    def absorb(self):
        """
        Get the absorption capabilities of the DER.

        :return: Absorption capabilities or a message if not initiated.
        """
        if self._abs_ena is None:
            return "DER absorb capabilities hasn't been initiated"
        else:
            return self._abs_ena
    
    def startup_time(self):
        """
        Get the startup time of the DER.

        :return: Startup time or a message if not initiated.
        """
        if self._startup_time is None:
                return "DER startup time hasn't been initiated"
        else:
            return self._startup_time
    
    def imbalance_resp(self):
        """
        Get the imbalance response of the DER.

        :return: Imbalance response or None if not set.
        """
        if self._imbalance_resp:
            return self._imbalance_resp
        else:
            return None    

def der_scan():
    """
    Scans for DER (Distributed Energy Resource) modules in the current directory and imports them.
    
    This function searches for all Python files in the current directory that match the pattern 'der_*.py', imports them, and 
    extracts the 'der_info' function from each module. The 'der_info' function is expected to return a dictionary containing 
    information about the DER module, including the 'mode' key which is used to store the module in the 'der_modules' global dictionary.
    
    If a module does not have a 'der_info' function, or if an exception occurs during the import, 
    the module is removed from the 'sys.modules' dictionary to prevent further attempts to import it.
    """
    global der_modules
    # scan all files in current directory that match der_*.py
    package_name = '.'.join(__name__.split('.')[:-1])
    files = glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'der_*.py'))
    for f in files:
        module_name = None
        try:
            module_name = os.path.splitext(os.path.basename(f))[0]
            if package_name:
                module_name = package_name + '.' + module_name
            m = importlib.import_module(module_name)
            if hasattr(m, 'der_info'):
                info = m.der_info()
                print('DER Info %s' % info)
                mode = info.get('mode')
                # place module in module dict
                if mode is not None:
                    der_modules[mode] = m
            else:
                if module_name is not None and module_name in sys.modules:
                    del sys.modules[module_name]
        except Exception as e:
            if module_name is not None and module_name in sys.modules:
                del sys.modules[module_name]
            print(DERError('Error scanning module %s: %s' % (module_name, str(e))))

# scan for der modules on import
der_scan()

if __name__ == "__main__":
    pass
