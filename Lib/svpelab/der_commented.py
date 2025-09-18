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

'''
This driver has been heavily commented to assist coder to start coding and understand main principles found in drivers.
This driver is not meant to be used with any device.
'''

'''
Import section: the driver always import it's related abstraction layer to be able to inherit its attributes and functions
'''
import os

from . import der

commented_info = { # This global variable is defining the name used in the 'ts'/params of a test (der_'commented'.py)
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Commented'
}

def der_info(): # This function is used at the end of script to fetch the parameter sections defined in params function
    return commented_info

"""
Params function: This function initialise the parameter section of the commented der driver. If the commented mode is 
selected, it will show the parameters defined below under the der parameter section.
"""
def params(info, group_name):
    gname = lambda name: group_name + '.' + name # define the driver name in param naming format
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name # define the specific driver parameter in param naming format
    mode = commented_info['mode']
    info.param_add_value(gname('mode'), mode)# add the driver section in the overall info directory
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode, # Define the group or driver parameter section
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('list'), label='This is a list', default='None', values=['None', 'textfield', 'list2']) # Add a list
    # parameter under the commented driver paramenter section.
    info.param(pname('textfield'), label='This is a textfield', default='HelloWorld', active=pname('list'),
               active_value='textfield') # add a testfield parameter under the above list parameter. It shows the
    # functionnality of active and active_value and it shows only if the 'textfield' value is selected in the list parameter
    info.param(pname('list2'), label='This is another list', default='None', values=['None', 'textfield2'],
               active=pname('list'), active_value='list2')  # add a list parameter under the above list parameter. It shows the
    # functionnality of active and active_value and it shows only if the 'list2' value is selected in the list parameter
    info.param(pname('textfield2'), label='This is another textfield', default='HelloWorld2', active=pname('list2'),
               active_value='textfield2') # add a testfield parameter under the above list2 parameter. It shows that the
    # active functionnality can be at multiple level.


GROUP_NAME = 'commented'

class DER(der.DER):

    def __init__(self, ts, group_name, support_interfaces=None):
        der.DER.__init__(self, ts, group_name, support_interfaces=support_interfaces)
        # Fetching the parameters that the user input for the parameters in the parameters section of
        # the driver
        self.list1 = self._param_value('list')
        self.textfield = self._param_value('textfield')
        # sometimes driver or abstraction layers have a params attribute that is used to pass to a device object (look
        # into most das drivers like das_opal.py) Therefore, the following way could also be used.
        self.params = {}
        self.params['list2'] = self._param_value('list2')
        self.params['textfield2'] = self._param_value('textfield2')
        # It's then a good idea to add ts as a function attribute since you can use it to fetch any other parameters or
        # use the logging functions in the class methods
        self.ts = ts
        # example
        self.ts.log_debug(f"Here are the values of the first list:\n{self.list1},\nthe textfield: {self.textfield},"
                          f"\nthe second list: {self.params['list2']}\nand the second texfield: {self.params['textfield2']}" )
        self.ts.log_warning(f"Here is the driver used: {self.ts.param('der.commented')}")

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)
    '''
    For the rest of the driver's Class, it would usually include the redefined methodology from the abstraction layer 
    (der.py) that the device can reproduce and that are needed to run scripts. In the case of this driver, most of the 
    needed functions have been copied from the der_pass.py driver.
    '''

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
        params = {}
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
        params['WRtg'] = 5500.
        params['VArRtgQ1'] = 1600.
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
            params['Fixed_PF'] = True
        return params

    def connect(self, params=None):
        """ Get/set connect/disconnect function settings.

        Params:
            Conn - Connected (True/False)
            WinTms - Randomized start time delay in seconds
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for connect.
        """
        if params is not None:
            pass
        else:
            params = {}
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
        if params is not None:
            pass
        else:
            params = {}
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
            pass
        else:
            params = {}
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
        if params is not None:
            pass
        else:
            params = {}
        return params

    def volt_var_curve(self, id, params=None):
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
        if params is not None:
            pass
        else:
            params = {}
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

        try:
            if params is not None:
                pass
            else:
                params = {}
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def freq_watt_curve(self, id, params=None):
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

        try:
            if params is not None:
                pass
            else:
                params = {}

        except Exception as e:
            raise der.DERError(str(e))

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
                pass
            else:
                params = {}

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
        if params is not None:
            pass
        else:
            params = {}
        return params


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
            pass
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
            pass
        else:
            params = {}
            params['P'] = 2000
        return params


    def storage(self, params=None):
        """ Get/set storage parameters

        Params:
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

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HFRT control.
        """
        try:
            if params is not None:
                pass
            else:
                params = {}
                params['ChaState'] = 50
        except Exception as e:
            raise der.DERError(str(e))

        return params

