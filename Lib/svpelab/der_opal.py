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

import os, sys, psutil

def add_RTLAB_API_path_to_environnement_variables():
    """
    Add the API path of currently running RTLAB to the environnment variable, if no RTLAB is running it uses the latest version installed.
    """
    RTLAB_path = get_running_RTLAB_path()
    if not RTLAB_path:
        print("WARNING: RTLAB not running.")
        RTLAB_path = get_latest_RTLAB_path()
    API_path = os.path.join(RTLAB_path,'common','python')
    sys.path.append(API_path)

def get_running_RTLAB_path():
    """
    Return the version of the RTLAB running, None if no RTLAB is not running
    """
    for process in psutil.process_iter(['name', 'exe']):
        if process.info['name'] == 'RT-LAB.exe' or process.info['name'] == 'MetaController.exe' or process.info['name'] == 'Controller.exe':
            if process.info['exe']: 
                return process.info['exe'].split('common')[0]
    return None

def get_latest_RTLAB_path():
    """
    Add path to the latest RTLAB API path on computer to the environment variable.
    """
    root_path = os.path.join("C:\\", "OPAL-RT", "RT-LAB")
    latest_version = max(os.listdir(root_path))
    return os.path.join(root_path, latest_version)

add_RTLAB_API_path_to_environnement_variables()

import RtlabApi as r
from . import der

opal_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Opal'
}

def der_info():
    return opal_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = opal_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('sec_crtl_frz_time'), label='Secondary Control Initialization freeze time', default='10.0')

GROUP_NAME = 'Opal'

class DER(der.DER):
    """
    An implementation of the  der.DER that implements DER functionality for OPAL-RT simulations.

    This class provides methods to interface with OPAL-RT hardware-in-the-loop (HIL) simulations
    for distributed energy resource (DER) testing and control.

    Methods:
        __init__(ts, group_name, support_interfaces=None): Initialize the DER OPAL instance
       param_value(name): Get parameter value from the test script
       info(): Get DER device information
       config(): Configure the DER OPAL model parameters
       nameplate(): Get nameplate ratings for the DER
       measurements(): Retrieve measurement data
       deactivate_all_fct(): Deactivate all functions
       settings(): Get/set capability settings
       conn_status(): Get connection status of controls
       controls_status(): Get status of controls
       connect(): Manage connection/disconnection settings
       fixed_pf(): Manage fixed power factor control
       limit_max_power(): Control maximum active power
       volt_var(): Manage volt/var control
       volt_var_curve(): Configure volt/var curve parameters
       watt_var(): Manage watt/var control
       watt_var_curve(): Configure watt/var curve parameters
       volt_watt(): Manage volt/watt control
       volt_watt_curve(): Configure volt/watt curve parameters
       freq_watt(): Manage frequency/watt control
       freq_watt_curve(): Configure frequency/watt curve parameters
       freq_watt_param(): Manage frequency-watt specific parameters
       frt_stay_connected_high(): Configure high frequency ride through
       frt_stay_connected_low(): Configure low frequency ride through
       reactive_power(): Control reactive power output
       active_power(): Manage active power output
       storage(): Configure storage parameters
       UI(): Configure UI-related capabilities
    """
    
    def __init__(self, ts, group_name, support_interfaces=None):
        der.DER.__init__(self, ts, group_name, support_interfaces=support_interfaces)
        # optional parameters for interfacing with other SVP devices
        if self.hil is None:
            ts.log_warning('No HIL support interface was provided to der_opal.py')

    def param_value(self, name):
        """
        Set the parameter name in the correct format 
        """
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)
    
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
        try:
            params = {}
            params['Manufacturer'] = self.ts.prompt('Enter Manufacturer: ')
            params['Model'] = self.ts.prompt('Enter Model: ')
            params['Options'] = self.ts.prompt('Enter Options: ')
            params['Version'] = self.ts.prompt('Enter Version: ')
            params['SerialNumber'] = self.ts.prompt('Enter Serial Number: ')
        except Exception as e:
            raise der.DERError(str(e))

        return params
    
    def config(self):
        """
        Set model parameters for the DER OPAL simulation.

        This method configures specific model parameters, primarily setting the secondary control 
        freeze time using a MATLAB variable.

        Returns:
            list: A list of configuration parameters (currently minimal)
        """

        #Set model parameters
        parameters = []
        if self.hil is not None:
            #parameters.append((self.hil.rt_lab_model + "/SM_Source/SVP Commands/mode/Value", 1))
            sec_crtl_frz_time = float(self.param_value('sec_crtl_frz_time'))
            self.hil.set_matlab_variable_value("SEC_CTRL_FRZ_TIME",sec_crtl_frz_time)
            self.ts.sleep(0.5)
            #self.ts.log_debug(f"Model ({self.hil.rt_lab_model} set to mode 1 and disable to 0)")
            #self.ts.log('DER OPAL model simulation started')
            #self.hil.start_simulation()
        return parameters

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
        pass

    def measurements(self):
        """ Get measurement data.

        Params:

        :return: Dictionary of measurement data.
        """
        self.ts.log_debug("No measurements() functions from der_opal.py")
        return None
    
    def deactivate_all_fct(self):
        """
        Deactivate all DER control functions.

        This method sets various MATLAB variables to their default or deactivated states, 
        effectively turning off multiple control functions such as grid support functions 
        for power, frequency, and reactive power.

        Returns:
            dict: A dictionary of the deactivated function parameters and their values
        """

        self.hil.set_matlab_variable_value("GSF_P",1.0)
        self.hil.set_matlab_variable_value("GSF_F",1.0)
        self.hil.set_matlab_variable_value("GSF_Q",1.0)
        self.hil.set_matlab_variable_value("CPF_Ext",1.0)
        self.hil.set_matlab_variable_value("CPF_AbsSet",1.0)
        self.hil.set_matlab_variable_value("CPF_InjSet",1.0)

        self.hil.set_matlab_variable_value("CPF_RspTms",0.5)
        self.hil.set_matlab_variable_value("Plim",1.0)
        params = {}
        params["GSF_P"] = self.hil.get_matlab_variable_value(variableName="GSF_P")
        params["GSF_F"] = self.hil.get_matlab_variable_value(variableName="GSF_F")
        params["GSF_Q"] = self.hil.get_matlab_variable_value(variableName="GSF_Q")
        params["CPF_Ext"] = self.hil.get_matlab_variable_value(variableName="CPF_Ext")
        params["CPF_AbsSet"] = self.hil.get_matlab_variable_value(variableName="CPF_AbsSet")
        params["CPF_RspTms"] = self.hil.get_matlab_variable_value(variableName="CPF_RspTms")
        params["PLIM"] = self.hil.get_matlab_variable_value(variableName="Plim")

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
        try:
            params = {}
            params['WMax'] = self.inv.settings['WMax']
            params['VRef'] = self.inv.settings.VRef
            params['VRefOfs'] = self.inv.settings.VRefOfs
            params['VMax'] = self.inv.settings.VMax
            params['VMin'] = self.inv.settings.VMin
            params['VAMax'] = self.inv.settings.VAMax
            params['VArMaxQ1'] = self.inv.settings.VArMaxQ1
            params['VArMaxQ2'] = self.inv.settings.VArMaxQ2
            params['VArMaxQ3'] = self.inv.settings.VArMaxQ3
            params['VArMaxQ4'] = self.inv.settings.VArMaxQ4
            params['WGra'] = self.inv.settings.WGra
            params['PFMinQ1'] = self.inv.settings.PFMinQ1
            params['PFMinQ2'] = self.inv.settings.PFMinQ2
            params['PFMinQ3'] = self.inv.settings.PFMinQ3
            params['PFMinQ4'] = self.inv.settings.PFMinQ4
            params['VArAct'] = self.inv.settings.VArAct
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def conn_status(self, params=None):
        """ Get status of controls (binary True if active).
        :return: Dictionary of active controls.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            self.inv.status.read()
            pv_conn_bitfield = self.inv.status.PVConn
            stor_conn_bitfield = self.inv.status.StorConn
            ecp_conn_bitfield = self.inv.status.ECPConn

            params = {}
            if pv_conn_bitfield is not None:
                params['PV_Connected'] = (pv_conn_bitfield & PVCONN_CONNECTED) == PVCONN_CONNECTED
                params['PV_Available'] = (pv_conn_bitfield & PVCONN_AVAILABLE) == PVCONN_AVAILABLE
                params['PV_Operating'] = (pv_conn_bitfield & PVCONN_OPERATING) == PVCONN_OPERATING
                params['PV_Test'] = (pv_conn_bitfield & PVCONN_TEST) == PVCONN_TEST
            elif stor_conn_bitfield is not None:
                params['Storage_Connected'] = (stor_conn_bitfield & STORCONN_CONNECTED) == STORCONN_CONNECTED
                params['Storage_Available'] = (stor_conn_bitfield & STORCONN_AVAILABLE) == STORCONN_AVAILABLE
                params['Storage_Operating'] = (stor_conn_bitfield & STORCONN_OPERATING) == STORCONN_OPERATING
                params['Storage_Test'] = (stor_conn_bitfield & STORCONN_TEST) == STORCONN_TEST
            elif ecp_conn_bitfield is not None:
                params['EPC_Connected'] = (ecp_conn_bitfield & ECPCONN_CONNECTED) == ECPCONN_CONNECTED
            else:
                params = {}
        except Exception as e:
            raise der.DERError(str(e))

        return params

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
        try:
            if params is not None:
                #self.ts.confirm('Set the following parameters %s' % params)
                pass
            else:
                params = {}
                params['Conn'] = self.ts.prompt('What is the connect status: True/False')
                params['WinTms'] = self.ts.prompt('What is the Time Window?')
                params['RvrtTms'] = self.ts.prompt('What is the Revert Time?')
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def fixed_pf(self, params=None):
        """ Get/set fixed power factor control settings.

        Params:
            Ena - Enabled (True/False)
            PF - Power Factor set point
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for fixed factor.
        """
        # Apply the configuration
        if params is not None:
            ena = params.get('Ena')
            pf = params.get('PF')
            RvrtTms = params.get('RvrtTms')

            if ena :
                self.hil.set_matlab_variable_value("Pow_Prio",1.0)
                self.hil.set_matlab_variable_value("GSF_Q",1.0)
                self.hil.set_matlab_variable_value("CPF_RspTms",RvrtTms)

                if pf > 0.0:
                    self.hil.set_matlab_variable_value("CPF_Ext",2.0)
                    self.hil.set_matlab_variable_value("CPF_AbsSet",abs(pf))
                else:
                    self.hil.set_matlab_variable_value("CPF_Ext",1.0)
                    self.hil.set_matlab_variable_value("CPF_InjSet",abs(pf))

        params = {}
        params["Ena"] = self.hil.get_matlab_variable_value("GSF_Q")
        sign = float(self.hil.get_matlab_variable_value("CPF_Ext"))
        if sign == 1.0:
            params["PF"]  = self.hil.get_matlab_variable_value("CPF_AbsSet")
        elif sign == 2.0:
            params["PF"]  = self.hil.get_matlab_variable_value("CPF_InjSet")*-1
        params["RvrtTms"]  = self.hil.get_matlab_variable_value("CPF_RspTms")
        return params

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
        if params is not None:
            ena = params.get('Ena')
            Plim = params.get('WMaxPct')
            RvrtTms = params.get('RvrtTms')
            Plim /= 100.0
            if ena :
                self.hil.set_matlab_variable_value("Plim",Plim)

        params = {}
        if float(self.hil.get_matlab_variable_value("Plim")) != 1.00:
            params["Ena"] = True
        else:
            params["Ena"] = False
        params["WMaxPct"] = self.hil.get_matlab_variable_value("Plim")

        return params

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

        # Apply the configuration
        if params is not None:
            ena = params.get('Ena')
            if ena :
                self.hil.set_matlab_variable_value("Pow_Prio",1.0)
                self.hil.set_matlab_variable_value("GSF_Q",2.0)
                self.volt_var_curve(params=params)
        params = {}
        params["Ena"] = self.hil.get_matlab_variable_value("GSF_Q")
        params["curve"] = self.volt_var_curve()

        return params

    def volt_var_curve(self, params=None):
        """ Get/set volt/var curve
            v [] - List of voltage curve points
            var [] - List of var curve points based on DeptRef
            DeptRef - Dependent reference type: 'VAR_MAX_PCT', 'VAR_AVAL_PCT', 'VA_MAX_PCT', 'W_MAX_PCT'
            RmpTms - Ramp timer
            RmpDecTmm - Ramp decrement timer
            RmpIncTmm - Ramp increment timer

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for volt/var control.
        """
        self.ts.log(params)
        try:
            if params is not None:
                v = params['curve'].get('v')
                v2 = v[len(v)//2-1:len(v)//2][0]
                v3 = v[len(v)//2:len(v)//2+1][0]
                v_mean  = round((v2+v3) /2 ,2 )
                v = v[:len(v)//2] + [v_mean] + v[len(v)//2:]
                self.hil.set_matlab_variable_value("VV_V",v)
                var = params['curve'].get('var')
                q2 = var[len(var)//2-1:len(var)//2][0]
                q3 = var[len(var)//2:len(var)//2+1][0]
                var_mean = round((q2+q3) /2 ,2 )
                var = var[:len(var)//2] + [var_mean] + var[len(var)//2:]
                self.hil.set_matlab_variable_value("VV_Q",var)
                vref = params['curve'].get('vref')
                self.hil.set_matlab_variable_value("VV_Vref",vref)
                vv_tr = params['curve'].get('RmpPtTms')
                self.hil.set_matlab_variable_value("VV_RspTms",vv_tr)
            params= {}
            params["v"] = self.hil.get_matlab_variable_value(variableName="VV_V")
            params["var"] = self.hil.get_matlab_variable_value(variableName="VV_Q")
            params["vref"] = self.hil.get_matlab_variable_value(variableName="VV_Vref")
            params["RmpPtTms"] = self.hil.get_matlab_variable_value(variableName="VV_RspTms")

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def watt_var(self, params=None):
        """ Get/set watt/var control

        Params:
            Ena - Enabled (True/False)
            ActCrv - Active curve number (0 - no active curve)
            NCrv - Number of curves supported
            NPt - Number of points supported per curve
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for watt/var control.
        """

        # Apply the configuration
        if params is not None:
            ena = params.get('Ena')
            if ena :
                self.hil.set_matlab_variable_value("Pow_Prio",1.0)
                self.hil.set_matlab_variable_value("GSF_Q",3.0)
                self.watt_var_curve(params=params)
        params = {}
        params["Ena"] = self.hil.get_matlab_variable_value("GSF_Q")
        params["curve"] = self.watt_var_curve()

        return params

    def watt_var_curve(self, params=None):
        """ Get/set watt/var curve
            v [] - List of voltage curve points
            var [] - List of var curve points based on DeptRef
            DeptRef - Dependent reference type: 'VAR_MAX_PCT', 'VAR_AVAL_PCT', 'VA_MAX_PCT', 'W_MAX_PCT'
            RmpTms - Ramp timer
            RmpDecTmm - Ramp decrement timer
            RmpIncTmm - Ramp increment timer

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for watt/var control.
        """
        self.ts.log(params)

        try:
            if params is not None:
                w = params['curve'].get('w')
                self.hil.set_matlab_variable_value("WV_P",w)
                var = params['curve'].get('var')
                self.hil.set_matlab_variable_value("WV_Q",var)
                wv_tr = params['curve'].get('RmpPtTms')
                self.hil.set_matlab_variable_value("WV_RspTms",wv_tr)
            params= {}
            params["w"] = self.hil.get_matlab_variable_value(variableName="WV_P")
            params["var"] = self.hil.get_matlab_variable_value(variableName="WV_Q")
            params["RmpPtTms"] = self.hil.get_matlab_variable_value(variableName="WV_RspTms")

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def volt_watt(self, params=None):
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
        # Apply the configuration
        if params is not None:
            ena = params.get('Ena')
            if ena :
                self.hil.set_matlab_variable_value("GSF_P",2.0)
                self.volt_watt_curve(params=params)
            else:
                self.hil.set_matlab_variable_value("GSF_P", 1.0)
        params = {}
        params["Ena"] = self.hil.get_matlab_variable_value(variableName="GSF_P")
        params["curve"] = self.volt_watt_curve()

        return params

    def volt_watt_curve(self,params=None):
        """ Get/set volt/var curve
            v [] - List of voltage curve points
            var [] - List of var curve points based on DeptRef
            DeptRef - Dependent reference type: 'VAR_MAX_PCT', 'VAR_AVAL_PCT', 'VA_MAX_PCT', 'W_MAX_PCT'
            RmpTms - Ramp timer
            RmpDecTmm - Ramp decrement timer
            RmpIncTmm - Ramp increment timer

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for volt/var control.
        """
        try:
            if params is not None:
                v = params['curve'].get('v')
                self.hil.set_matlab_variable_value("VW_V",v)
                p = params['curve'].get('w')
                self.hil.set_matlab_variable_value("VW_P",p)
                time = params['curve'].get('RmpTms')
                self.hil.set_matlab_variable_value("VW_RspTms",time)
            params = {}
            params["v"] = self.hil.get_matlab_variable_value(variableName="VW_V")
            params["w"] = self.hil.get_matlab_variable_value(variableName="VW_P")
            params["RmpTms"] = self.hil.get_matlab_variable_value(variableName="VW_RspTms")

        except Exception as e:
            raise der.DERError(str(e))

        return params

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
        if params is not None:
            ena = params.get('Ena')
            if ena :
                self.hil.set_matlab_variable_value("GSF_F",2.0)
                self.freq_watt_curve(params=params)
        params["Ena"] = self.hil.get_matlab_variable_value(variableName="GSF_F")
        params["curve"] = self.freq_watt_curve()

        return params

    def freq_watt_curve(self, params=None):
        """ Get/set volt/var curve
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

        if params is not None:
            dbf = params.get('dbf')
            self.hil.set_matlab_variable_value("FW_dbUF",dbf)
            self.hil.set_matlab_variable_value("FW_dbOF",dbf)

            kof = params.get('kof')
            self.hil.set_matlab_variable_value("FW_kUF",kof)
            self.hil.set_matlab_variable_value("FW_kOF",kof)

            time = params.get('RspTms')
            self.hil.set_matlab_variable_value("FW_RspTms",time)
        params = {}
        params["dbUF"] = self.hil.get_matlab_variable_value(variableName="FW_dbUF")
        params["dbOF"] = self.hil.get_matlab_variable_value(variableName="FW_dbOF")

        params["kUF"] = self.hil.get_matlab_variable_value(variableName="FW_kUF")
        params["kOF"] = self.hil.get_matlab_variable_value(variableName="FW_kOF")

        params["RmpTms"] = self.hil.get_matlab_variable_value(variableName="FW_RspTms")

        return params

    def freq_watt_param(self, params=None):
        """ Get/set frequency-watt with parameters

        Params:
            Ena - Enabled (True/False)
            HysEna - Enable hysterisis (True/False)
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

        try:
            if params is not None:
                #self.ts.confirm('Set the following parameters %s' % params)
                pass
            else:
                params = {}
                self.inv.hfrtc.read()
                if self.inv.freq_watt_param.ModEna == 0:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                if self.inv.freq_watt_param.HysEna == 0:
                    params['HysEna'] = False
                else:
                    params['HysEna'] = True
                params['WGra'] = self.inv.freq_watt_param.WGra
                params['HzStr'] = self.inv.freq_watt_param.HzStr
                params['HzStop'] = self.inv.freq_watt_param.HzStop
                params['HzStopWGra'] = self.inv.freq_watt_param.HzStopWGra

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def frt_stay_connected_high(self, params=None):
        """ Get/set high frequency ride through (must stay connected curve)

        Params:
            Ena - Enabled (True/False)
            ActCrv - Active curve number (0 - no active curve)
            NCrv - Number of curves supported
            NPt - Number of points supported per curve
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds
            Tms# - Time point in the curve
            Hz# - Frequency point in the curve

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HFRT control.
        """

        try:
            pass

        except Exception as e:
            raise der.DERError(str(e))

        return "frt_stay_connected_high() not configure in der_opal.py"

    def frt_stay_connected_low(self, params=None):
        """ Get/set high frequency ride through (must stay connected curve)

        Params:
            Ena - Enabled (True/False)
            ActCrv - Active curve number (0 - no active curve)
            NCrv - Number of curves supported
            NPt - Number of points supported per curve
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds
            Tms# - Time point in the curve
            Hz# - Frequency point in the curve

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HFRT control.
        """
        try:
            pass

        except Exception as e:
            raise der.DERError(str(e))

        return "frt_stay_connected_low() not configure in der_opal.py"

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

         # Apply the configuration
        if params is not None:
            ena = params.get('Ena')
            q = params.get('Q')
            RvrtTms = params.get('RvrtTms')
            if ena :
                self.hil.set_matlab_variable_value("Pow_Prio",1.0)
                self.hil.set_matlab_variable_value("GSF_Q",4.0)
                self.hil.set_matlab_variable_value("CQ_RspTms",RvrtTms)

                if q>0 :
                    self.hil.set_matlab_variable_value("CQ_Ext",1.0)
                    self.hil.set_matlab_variable_value("CQ_InjSet",abs(q))
                else:
                    self.hil.set_matlab_variable_value("CQ_Ext",2.0)
                    self.hil.set_matlab_variable_value("CQ_AbsSet",abs(q))

        params = {}
        params["Ena"] = self.hil.get_matlab_variable_value("GSF_Q")
        sign = self.hil.get_matlab_variable_value("CQ_Ext")
        if sign == 1.0:
            params["Q"]  = self.hil.get_matlab_variable_value("CQ_InjSet")
        elif sign == 2.0:
            params["Q"]  = self.hil.get_matlab_variable_value("CQ_AbsSet")*-1
        params["RvrtTms"]  = self.hil.get_matlab_variable_value("CQ_RspTms")
        return params

    def active_power(self, params=None):
        """ Get/set active power of EUT

        Parameter:
        --------
        params: Dictionary of parameters to be updated.
            Ena - Enabled (True/False)
            P - Active power in %Wmax (positive is exporting (discharging), negative is importing (charging) power)
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        
        :return: Dictionary of active settings for HFRT control.
        """
        try:
            if params is not None:
                #self.ts.confirm('Set the following parameters %s' % params)
                pass
            else:
                params = {}
                params['P'] = 2000
                '''
                params['Ena'] = self.ts.prompt('Active power is enabled (True/False)? ')
                params['P'] = self.ts.prompt('Active power is: ')
                params['WinTms'] = self.ts.prompt('Time Window is: ')
                params['RmpTms'] = self.ts.prompt('Ramp Time is: ')
                params['RvrtTms'] = self.ts.prompt('Revert Time is: ')
                params['curve'] = self.ts.prompt('Curve parameters are: ')
                '''

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def storage(self, params=None):
        """ Get/set storage parameters

        Parameter:
        --------
        params: Dictionary of parameters to be updated.
            WChaMax - Setpoint for maximum charge.
            WChaGra - Setpoint for maximum charging rate. Default is MaxChaRte.
            WDisChaGra - Setpoint for maximum discharge rate. Default is MaxDisChaRte.
            StorCtl_Mod - Activate hold/discharge/charge storage control mode. Bitfield value.
            VAChaMax - Setpoint for maximum charging VA.
            MinRsvPct - Setpoint for minimum reserve for storage as a percentage of the nominal maximum storage.
            ChaState (R) - Currently available energy as a percent of the capacity rating.
            StorAval (R) - State of charge (ChaState) minus storage reserve (MinRsvPct) times capacity rating (AhrRtg).
            InBatV (R) - Internal battery voltage.
            ChaSt (R) - Charge status of storage device. Enumerated value.
            OutWRte - Percent of max discharge rate.
            InWRte - Percent of max charging rate.
            InOutWRte_WinTms - Time window for charge/discharge rate change.
            InOutWRte_RvrtTms - Timeout period for charge/discharge rate.
            InOutWRte_RmpTms - Ramp time for moving from current setpoint to new setpoint.

        :return: Dictionary of active settings for HFRT control.
        """
        try:
            if params is not None:
                #self.ts.confirm('Set the following parameters %s' % params)
                pass

            else:
                params = {}
                params['ChaState'] = 50
                '''
                params['WChaMax'] = self.ts.prompt('WChaMax? ')
                params['WChaGra'] = self.ts.prompt('WChaGra? ')
                params['WDisChaGra'] = self.ts.prompt('WDisChaGra? ')
                params['StorCtl_Mod'] = self.ts.prompt('StorCtl_Mod? ')
                params['VAChaMax'] = self.ts.prompt('VAChaMax? ')
                params['MinRsvPct'] = self.ts.prompt('MinRsvPct? ')
                params['ChaState'] = self.ts.prompt('ChaState? ')
                params['StorAval'] = self.ts.prompt('StorAval? ')
                params['InBatV'] = self.ts.prompt('InBatV? ')
                params['ChaSt'] = self.ts.prompt('ChaSt? ')
                params['OutWRte'] = self.ts.prompt('OutWRte? ')
                params['InWRte'] = self.ts.prompt('InWRte? ')
                params['InOutWRte_WinTms'] = sself.ts.prompt('InOutWRte_WinTms? ')
                params['InOutWRte_RvrtTms'] = self.ts.prompt('InOutWRte_RvrtTms? ')
                params['InOutWRte_RmpTms'] = self.ts.prompt('InOutWRte_RmpTms? ')
                '''
        except Exception as e:
            raise der.DERError(str(e))

        return params
    
    def UI(self, params=None):
        """
        Configure Uinintentionnal Islanding related capabilities

        This method allows enabling or disabling specific UI capabilities in the OPAL-RT simulation.

        Args:
            params (dict, optional): A dictionary of parameters to configure UI settings.
                - 'Ena': Enable/disable UI capability (boolean)

        Returns:
            dict: A dictionary containing:
                - 'Ena': Current UI enable status
                - 'ui_capability_er': Specific UI capability (set to 'Sandia Frequency Shift')
        """
        # Apply the configuration
        if params is not None:
            ena = params.get('Ena')
            self.hil.set_matlab_variable_value("ID_enable", ena)

        params = {}
        params["Ena"] = self.hil.get_matlab_variable_value("ID_enable")
        params['ui_capability_er'] = 'Sandia Frequency Shift'

        return params