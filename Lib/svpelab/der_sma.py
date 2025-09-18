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
SMA Inverter DER (Distributed Energy Resource) Module

This module implements the DER interface for SMA inverters, providing
a standardized way to interact with these devices within the SVP framework.
It extends the abstract DER class to offer SMA-specific functionality,
including power factor control, reactive power control, and other inverter-
specific operations.

The DER class in this module acts as an intermediary between high-level
test scripts and low-level SMA inverter communication, abstracting
device-specific details and offering a consistent interface for
various distributed energy resource operations.

Key features:
- Modbus TCP communication with SMA inverters
- Implementation of standard DER interface methods
- SMA-specific parameter handling and command execution

This module is an integral part of the DER abstraction layer, facilitating
seamless integration of SMA inverters into the broader SVP testing ecosystem.
"""

# revision for merging SMA drivers with different register # EugeneRNCan


try:
    import os
    from . import der
    import script
    import sunspec.core.modbus.client as client
    import sunspec.core.util as util
except Exception as e:
    print(('Import problem in der_sma.py: %s' % e))
    raise der.DERError('Import problem in der_sma.py: %s' % e)

sma_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'SMA'
}

def der_info():
    return sma_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = sma_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    # TCP parameters
    info.param(pname('ipaddr'), label='IP Address', default='192.168.0.170')
    info.param(pname('ipport'), label='IP Port', default=502)
    info.param(pname('slave_id'), label='Slave Id', default=1)
    info.param(pname('firmware'), label='Firmware Number', default='02.02.30.R', values=['02.02.30.R', '02.83.03.R'])
    info.param(pname('confgridguard'), label='Configure Grid Guard', default='False', values=['True', 'False'])
    info.param(pname('gridguard'), label='Grid Guard Number', default=12345678,
               active=pname('confgridguard'),  active_value='True')

GROUP_NAME = 'sma'
SB_FIRMWARE_NUMBER = '02.02.30.R'
STP_FIRMWARE_NUMBER = '02.83.03.R'

class DER(der.DER):
    """
    SMA DER (Distributed Energy Resource) Implementation

    This class extends the abstract der.DER class to provide specific
    functionality for SMA inverters. It implements methods for
    configuration, connection, and various power control functions.

    The class serves as an abstraction layer between the test scripts
    and the physical SMA device, allowing standardized interaction
    with the inverter across different test scenarios.
    """

    def __init__(self, ts, group_name, support_interfaces=None):
        der.DER.__init__(self, ts, group_name, support_interfaces=support_interfaces)
        self.inv = None
        self.ts = ts
        self.firmware = {}
        # Adding a registry dictionary corresponding to different SMA  der firmware
        firmware = self.param_value('firmware')
        if firmware == STP_FIRMWARE_NUMBER:
            vw_register = {'VW_X1_V1': 41029, 'VW_X1_V2': 41033, 'VW_Y1_P1': 41031, 'VW_Y1_P2': 41035}
            vv_register = {'Q(U)': 2269, 'VAR_%_PMAX': 41075, 'NB_OF_POINT_1': 41071}
            self.firmware.update({'firmware': firmware})
            self.firmware.update(vw_register)
            self.firmware.update(vv_register)
        elif firmware == SB_FIRMWARE_NUMBER:
            vw_register = {'VW_X1_V1': 40282, 'VW_X1_V2': 40284, 'VW_Y1_P1': 40306, 'VW_Y1_P2': 40308}
            vv_register = {'Q(U)': 1069, 'VAR_%_PMAX': 40977, 'NB_OF_POINT_1': 40262}
            self.firmware.update({'firmware': firmware})
            self.firmware.update(vw_register)
            self.firmware.update(vv_register)
        else:
            ts.log_error('The SMA firmware is invalid')

    def param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):
        self.open()

    def open(self):
        ipaddr = self.param_value('ipaddr')
        ipport = self.param_value('ipport')
        slave_id = self.param_value('slave_id')

        self.inv = client.ModbusClientDeviceTCP(slave_id, ipaddr, ipport, timeout=5)

        config_grid_guard = self.param_value('confgridguard')
        if config_grid_guard == 'True':
            gg = int(self.param_value('gridguard'))
            gg_success = self.gridguard(gg)
            if gg_success:
                self.ts.log('Grid Guard Code Accepted.')
            else:
                self.ts.log_warning('Grid Guard Code Not Accepted!')


    def gridguard(self, new_gg=None):
        """ Read/Write SMA Grid Guard.

        Params:
            new_gg : Grid Guard

        return: 
            0 or 1 for GG (off or on).
        """
        data = self.inv.read(43090, 2)
        gg = util.data_to_u32(data)
        if int(gg)==1:
            self.ts.log("Grid Guard is already set")
            return True

        if new_gg is not None:
            self.ts.log('Writing new Grid Guard: %d' % new_gg)
            self.inv.write(43090, util.u32_to_data(int(new_gg)))

        self.ts.sleep(1)

        data = self.inv.read(43090, 2)
        gg = util.data_to_u32(data)
        #self.ts.log("gg %s" % gg)
        if gg == 0:
            print('Grid guard was not enabled')
            return False
        else:
            print('Grid guard was enabled')
            return True

    def close(self):
        if self.inv is not None:
            self.inv.close()
            self.inv = None

    def info(self): #wanbin
        self.ts.log("info")
        try:
            params = {}

            params['Manufacturer']='SMA'
            '''
            params['Model']=util.data_to_s32(self.inv.read(40631, 2))
            params['Version']=util.data_to_u32(self.inv.read(40789, 2))
            params['Options']=''
            params['SerialNumber']=util.data_to_u32(self.inv.read(30057, 2))
            '''
            """ Get DER device information.

            Params:
                Manufacturer
                Model
                Version
                Options
                SerialNumber

            :return: Dictionary of information elements.
            """
        except Exception as e:
            raise der.DERError('Unimplemented function: info')

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

        der.DERError('Unimplemented function: nameplate')

    def measurements(self):
        """ Get measurement data.

        return: 
            Dictionary of measurement data.
        """
        try:
            params = {}
            params['A'] = util.data_to_u32(self.inv.read(30795, 2))/1000.
            params['AphA'] = None
            params['AphB'] = None
            params['AphC'] = None
            params['PPVphAB'] = None
            params['PPVphBC'] = None
            params['PPVphCA'] = None
            params['PhVphA'] = None
            params['PhVphB'] = None
            params['PhVphC'] = None
            params['W'] = util.data_to_s32(self.inv.read(30775, 2))
            params['Hz'] = util.data_to_u32(self.inv.read(30803, 2))/100.
            params['VA'] = util.data_to_s32(self.inv.read(30813, 2))
            params['VAr'] = util.data_to_s32(self.inv.read(30805, 2))
            pf = util.data_to_u32(self.inv.read(30821, 2))
            if util.data_to_u32(self.inv.read(30823, 2)) == 1041:
                params['PF'] = -pf  # 1041 = Leading
            else:
                params['PF'] = pf
            params['WH'] = None
            params['DCA'] = None
            params['DCV'] = None
            params['DCW'] = None
            params['TmpCab'] = None
            params['TmpSnk'] = None
            params['TmpTrns'] = None
            params['TmpOt'] = None
            params['St'] = None
            params['StVnd'] = None
            params['Evt1'] = None
            params['Evt2'] = None
            params['EvtVnd1'] = None
            params['EvtVnd2'] = None
            params['EvtVnd3'] = None
            params['EvtVnd4'] = None
        except Exception as e:
            raise der.DERError(str(e))

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

        der.DERError('Unimplemented function: settings')

    def conn_status(self, params=None):
        """ Get status of controls (binary True if active).
        :return: Dictionary of active controls.
        """
        der.DERError('Unimplemented function: cons_status')

    def controls_status(self, params=None):
        """ Get status of controls (binary True if active).
        :return: Dictionary of active controls.
        """
        der.DERError('Unimplemented function: controls_status')

    def connect(self, params=None):
        """ Get/set connect/disconnect function settings.

        Params:
            Conn - Connected (True/False)
            WinTms - Randomized start time delay in seconds
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for connect.
        """

        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                conn = params.get('Conn')
                if conn is not None:
                    if conn is True:
                        reg = 1467  # start
                    else:
                        reg = 1749  # Full stop (AC and DC side)
                        # reg = 381  # Stop (AC side)
                    self.inv.write(40018, util.u32_to_data(int(reg)))
            else:
                params = {}
                reg = self.inv.read(40018, 2)
                if util.data_to_u32(reg) == 1467:
                    params['Conn'] = True
                else:
                    params['Conn'] = False
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
        if self.inv is None:
            der.DERError('DER not initialized')

        try:
            if params is not None:
                pf = params.get('PF')

                # Configuring Grid Management Services Control with Sunny Explorer
                # Cos phi (if supported by the device): Read Modbus register 30825. If the value 1075 can be read
                # from this register, the power factor is specified via system control.

                if pf is not None:
                    if pf > 0:
                        reg = 1042  # lagging #wanbin Underexcited
                    else:
                        reg = 1041   # leading #wanbin Overexcited

                    self.inv.write(40200, util.u32_to_data(1074))
                    self.inv.write(40208, util.u32_to_data(int(reg))) # 40025 -> 40208

                    #reg = int(abs(round(pf, 4) * 10000))
                    #self.inv.write(40024, util.u16_to_data(int(reg)))
                    #self.ts.log("write pf")
                    self.inv.write(40206, util.u32_to_data(int(abs(pf)*100)))
                    #self.inv.write(40206, util.u32_to_data(4294967216))


                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        reg = 1074  # 1075 = cos phi, specified by PV system control
                        # reg = 1074  # 1075 = cos phi, direct specific.
                    else:
                        reg = 303
                    if reg != util.data_to_u32(self.inv.read(40200, 2)):
                        self.inv.write(40200, util.u32_to_data(int(reg)))

            else:
                params = {}
                reg = self.inv.read(40200, 2)
                if util.data_to_u32(reg) == 1074:   #wanbin
                    params['Ena'] = True
                else:
                    params['Ena'] = False
                #self.ts.log("here?")
                pf = (self.inv.read(40206, 2))                          #wanbin
                params['PF'] = float(util.data_to_u32(pf))/100.0        #wanbin
        except Exception as e:
            der.DERError(str(e))

        return params

    def limit_max_power(self, params=None):
        if params is not None:
            ena = params.get('Ena')
            if ena is not None:
                if ena is True:
                    self.inv.write(40210, util.u32_to_data(1077))
                    limW=params.get('WMaxPct') * self.p_rated()
                    self.inv.write(40212, util.u32_to_data(limW))
                else:
                    self.inv.write(40210, util.u32_to_data(303))

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
        '''
        if self.inv is None:
            raise der.DERError('DER not initialized')

        #####  UNTESTED ####

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        self.inv.write(40151, util.u32_to_data(802))
                    else:
                        self.inv.write(40151, util.u32_to_data(803))

                power = int(params.get('WMaxPct'))
                self.inv.write(40016, util.s16_to_data(int(power)))  # Active power setpoint P, in % of the maximum active power (PMAX) of the inverter
                # self.inv.write(40023, util.s16_to_data(int(power)))  # Normalized active power limitation by PV system ctrl, in %
                # self.inv.write(40143, util.s32_to_data(int(power)))  # Active power setpoint for the operating mode "Active power limitation P via PV system control" (A)
                # self.inv.write(40147, util.u32_to_data(int(power)))  # Generator active power limitation for the operating mode "Active power limitation P via system control" (A)
                # self.inv.write(40149, util.s32_to_data(int(power)))  # Active power setpoint for the operating mode "Active power limitation P via system control" (W)

            else:
                params = {}
                if util.data_to_u32(self.inv.read(40151, 2)) == 803:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['WMaxPct'] = util.data_to_s16(self.inv.read(40016, 1))
                # params['WMaxPct'] = util.data_to_s16(self.inv.read(40023, 1))
                # params['WMaxPct'] = util.data_to_s32(self.inv.read(40143, 2))
                # params['WMaxPct'] = util.data_to_u32(self.inv.read(40147, 2))
                # params['WMaxPct'] = util.data_to_s32(self.inv.read(40149, 2))

        except Exception, e:
            raise der.DERError(str(e))
        '''
        return params


    def volt_watt(self,params=None):
        """Get/set volt/watt control
        
                This method configures the volt/watt curve for the inverter. It can either retrieve the current settings
                or update them based on the provided parameters.
        
                Args:
                    params (dict, optional): A dictionary containing the volt/watt curve parameters.
                        If provided, it should contain:
                            'Ena' (bool): Enable/disable the volt/watt function
                            'curve' (dict): A dictionary with 'v' and 'w' lists, each containing two values
                                representing the voltage and power points of the curve.
        
                Returns:
                    str: A string representation of the current volt/watt settings if params is None.
                    None: If params is provided and the settings are successfully updated.
        
                Raises:
                    Potential exceptions during read/write operations to the inverter.
                """
        
        v_adrs=[self.firmware['VW_X1_V1'], self.firmware['VW_X1_V2']]
        w_adrs=[self.firmware['VW_Y1_P1'], self.firmware['VW_Y1_P2']]

        v0=util.data_to_u32(self.inv.read(v_adrs[0], 2))/1000
        v1=util.data_to_u32(self.inv.read(v_adrs[1], 2))/1000
        w0=util.data_to_u32(self.inv.read(w_adrs[0], 2))/1000
        w1=util.data_to_u32(self.inv.read(w_adrs[1], 2))/1000

        if params is None:
            return "v: (%d, %d), w: (%d, %d)" % (v0,v1,w0,w1)

        else:
            if params['Ena']:
                self.inv.write(40917, util.u32_to_data(int(1)))
                self.inv.write(40937, util.u32_to_data(int(308)))

                v=[params['curve']['v'][0],params['curve']['v'][1]]
                w=[params['curve']['w'][0],params['curve']['w'][1]]
                #self.ts.log_debug("=====test : %d,%d" % (v[0],v[1]))

                if v[0]!=v0:
                    self.inv.write(v_adrs[0], util.u32_to_data(int(v[0]*1000)))
                if v[1]!=v1:
                    self.inv.write(v_adrs[1], util.u32_to_data(int(v[1]*1000)))
                if w[0]!=w0:
                    self.inv.write(w_adrs[0], util.u32_to_data(int(w[0]*1000)))
                if w[1]!=w1:
                    self.inv.write(w_adrs[1], util.u32_to_data(int(w[1]*1000)))


                #if reg != util.data_to_u32(self.inv.read(40200, 2)):
                #    self.inv.write(40200, util.u32_to_data(int(reg)))




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
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                curve = params.get('curve')  ## Must write curve first because there is a read() in volt_var_curve
                act_crv = params.get('ActCrv')

                if curve is not None:
                    self.volt_var_curve(id=act_crv, params=curve)

                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        reg = self.firmware['Q(U)']  # React. power/volt. char. Q(U) #wanbin
                    else:
                        reg = 303
                    if reg != util.data_to_u32(self.inv.read(40200, 2)):
                        self.inv.write(40200, util.u32_to_data(int(reg)))

                    # Activation of the characteristic curve, configuration of characteristic curve mode
                    if ena is True:
                        reg = 308  # on
                    else:
                        reg = 303  # off
                    if self.firmware['firmware'] == STP_FIRMWARE_NUMBER:

                        if reg != util.data_to_u32(self.inv.read(41063, 2)):
                            self.inv.write(41063, util.u32_to_data(reg))  # Curve 1, 303 = off, 308 = on
                        if int(util.data_to_u32(self.inv.read(41061, 2)))!=2:
                            self.inv.write(41061, util.u32_to_data(2))  # Curve 1, 303 = off, 308 = on
                    elif self.firmware['firmware'] == SB_FIRMWARE_NUMBER:
                        if act_crv == 1:
                            if reg != util.data_to_u32(self.inv.read(40937, 2)):
                                self.inv.write(40937, util.u32_to_data(reg))  # Curve 1, 303 = off, 308 = on
                        if act_crv == 2:
                            if reg != util.data_to_u32(self.inv.read(40939, 2)):
                                self.inv.write(40939, util.u32_to_data(reg))  # Curve 2, 303 = off, 308 = on
                        if act_crv == 3:
                            if reg != util.data_to_u32(self.inv.read(40941, 2)):
                                self.inv.write(40941, util.u32_to_data(reg))  # Curve 3, 303 = off, 308 = on

                if self.firmware['firmware'] == SB_FIRMWARE_NUMBER:
                    if act_crv is not None:
                        # Characteristic curve number, configuration of the active power/voltage
                        # characteristic curve P(V). 0 = function is switched off.
                        if act_crv in [1, 2, 3]:
                            if act_crv != util.data_to_u32(self.inv.read(40260, 2)):
                                self.inv.write(40260, util.u32_to_data(act_crv))
                        else:
                            raise der.DERError('Unsupported characteristic curve number.')
                    else:
                        # Q(U) programmed into curve 2 by default
                        act_crv = 2
                        if act_crv != util.data_to_u32(self.inv.read(40260, 2)):
                            self.inv.write(40260, util.u32_to_data(act_crv))

            else:
                params = {}
                self.ts.sleep(1)
                reg = self.inv.read(40200, 2)
                if int(util.data_to_u32(reg)) == self.firmware['Q(U)']:
                    params['Ena'] = True
                else:
                    params['Ena'] = False
                    self.ts.log(util.data_to_u32(reg))

                if self.firmware['firmware'] == STP_FIRMWARE_NUMBER:
                    params['ActCrv'] = 2
                elif self.firmware['firmware'] == SB_FIRMWARE_NUMBER:

                    if util.data_to_u32(self.inv.read(40937, 2)) == 303:
                        if util.data_to_u32(self.inv.read(40977, 2)) == 1977 and \
                           util.data_to_u32(self.inv.read(40957, 2)) == 1976:   # Voltage in %Vnom and Var in %Pmax
                                params['ActCrv'] = 1
                    elif util.data_to_u32(self.inv.read(40937, 2)) == 303:
                        if util.data_to_u32(self.inv.read(40979, 2)) == 1977 and \
                           util.data_to_u32(self.inv.read(40959, 2)) == 1976:   # Voltage in %Vnom and Var in %Pmax
                                params['ActCrv'] = 2
                    elif util.data_to_u32(self.inv.read(40937, 2)) == 303:
                        if util.data_to_u32(self.inv.read(40981, 2)) == 1977 and \
                           util.data_to_u32(self.inv.read(40961, 2)) == 1976:   # Voltage in %Vnom and Var in %Pmax
                                params['ActCrv'] = 3
                    else:
                        params['ActCrv'] = None
                    params['NCrv'] = 3  # SMA supports 3 curves
                    if params['ActCrv'] is not None:
                        params['curve'] = self.volt_var_curve(id=params['ActCrv'])

        except Exception as e:
            der.DERError(str(e))

        return params

    def volt_var_curve(self, id=1, params=None):
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
        if self.inv is None:
            raise der.DERError('DER not initialized')

        if self.firmware['firmware'] == STP_FIRMWARE_NUMBER:
            x1 = [41077,41081,41085,41089]    #wanbin
            y1 = [41079,41083,41087,41091]    #wanbin
        elif self.firmware['firmware'] == SB_FIRMWARE_NUMBER:
            x1 = list(range(40282, 40306, 2))  # X values 1 to 12 of the characteristic curve 1
            y1 = list(range(40306, 40330, 2))  # Y values 1 to 12 of the characteristic curve 1
            x2 = list(range(40330, 40354, 2))  # X values 1 to 12 of the characteristic curve 2
            y2 = list(range(40354, 40378, 2))  # Y values 1 to 12 of the characteristic curve 2
            x3 = list(range(40378, 40402, 2))  # X values 1 to 12 of the characteristic curve 3
            y3 = list(range(40402, 40426, 2))  # Y values 1 to 12 of the characteristic curve 3

            volt_var_dept_ref = {
            'W_MAX_PCT': 1,
            'VAR_MAX_PCT': 2,
            'VAR_AVAL_PCT': 3,
            1: 'W_MAX_PCT',
            2: 'VAR_MAX_PCT',
            3: 'VAR_AVAL_PCT'
        }

        try:
            if int(id) > 3:
                raise der.DERError('Curve id out of range: %s' % id)

            if params is not None:
                # self.ts.log_debug('Writing VV Curve to SMA....')


                # set voltage points
                v = params.get('v')
                if v is not None:
                    v_len = len(v)
                    # if v_len > n_pt:
                    #     raise der.DERError('Voltage point count out of range: %d' % (v_len))

                    for i in range(v_len):  # SunSpec point index starts at 1
                        if id == 1:
                            v_val = int(util.data_to_s32(self.inv.read(x1[i], 2)))  # read
                            self.ts.log_debug('Voltage point %s is %s' % (i, v_val))
                            if int(v_val)==int(round(v[i], 3)*1000):
                                self.ts.log_debug('V points : Skip Writing: Same setting')
                            else:
                                self.ts.log_debug('Writing v point %s to reg %s with value %s' % (i, x1[i], v[i]))
                                self.inv.write(x1[i], util.s32_to_data(int(round(v[i], 3)*1000)))
                                self.ts.log_debug('Wrote V points')

                        elif self.firmware['firmware'] == SB_FIRMWARE_NUMBER:
                            if id == 2:
                                self.inv.write(x2[i], util.s32_to_data(int(round(v[i], 3)*1000)))
                            else:
                                self.inv.write(x3[i], util.s32_to_data(int(round(v[i], 3)*1000)))

                # set var points
                var = params.get('var')
                if var is not None:
                    var_len = len(var)
                    # if var_len > n_pt:
                    #     raise der.DERError('VAr point count out of range: %d' % (var_len))

                    self.inv.write(self.firmware['VAR_%_PMAX'], util.u32_to_data(1977))  # Var in percentages of Pmax #wanbin

                    for i in range(var_len):  # SunSpec point index starts at 1
                        if id == 1:
                            var_val = int(util.data_to_s32(self.inv.read(y1[i], 2)))  # read
                            if int(var_val)==int(round(var[i], 3)*1000):
                                self.ts.log_debug('VAR : Skip Writing: Same Setting')
                            else:
                                self.inv.write(y1[i], util.s32_to_data(int(round(var[i], 3)*1000)))
                                self.ts.log_debug('Wrote Var points')

                        elif self.firmware['firmware'] == SB_FIRMWARE_NUMBER:
                            if id == 2:
                                self.inv.write(y2[i], util.s32_to_data(int(round(var[i], 3)*1000)))
                                self.inv.write(40979, util.u32_to_data(1977))  # Var in percentages of Pmax
                            else:
                                self.inv.write(y3[i], util.s32_to_data(int(round(var[i], 3)*1000)))
                                self.inv.write(40981, util.u32_to_data(1977))  # Var in percentages of Pmax

            else:
                self.ts.log_debug('Reading VV curve in SMA')
                params = {}
                v = []
                var = []
                if id == 1:
                    n_pt = int(util.data_to_u32(self.inv.read(self.firmware['NB_OF_POINT_1'], 2)))   #wanbin
                    for i in range(int(4)):
                        self.ts.log('Getting V%s' % i)
                        v.append(util.data_to_s32(self.inv.read(x1[i], 2))/1000.)
                        self.ts.log('Getting Q%s' % i)
                        var.append(util.data_to_s32(self.inv.read(y1[i], 2))/1000.)

                elif self.firmware['firmware'] == SB_FIRMWARE_NUMBER:
                    if id == 2:
                        n_pt = int(util.data_to_u32(self.inv.read(40264, 2)))
                        self.ts.log_debug('n_pt %s' % n_pt)
                        if n_pt < 1 or n_pt > 12:
                            raise der.DERError('Unsupported number of VV points. n_pt: %s' % n_pt)
                        for i in range(int(n_pt)):
                            v.append(util.data_to_s32(self.inv.read(x2[i], 2))/1000)
                            var.append(util.data_to_s32(self.inv.read(y2[i], 2))/1000)
                    else:
                        n_pt = int(util.data_to_u32(self.inv.read(40266, 2)))
                        if n_pt < 1 or n_pt > 12:
                            raise der.DERError('Unsupported number of VV points. n_pt: %s' % n_pt)
                        for i in range(int(n_pt)):
                            v.append(util.data_to_s32(self.inv.read(x3[i], 2))/1000)
                            var.append(util.data_to_s32(self.inv.read(y3[i], 2))/1000)

                dept_ref = volt_var_dept_ref.get(1)  # 'W_MAX_PCT'
                params['DeptRef'] = dept_ref
                params['id'] = id  # also store the curve number
                params['v'] = v
                params['var'] = var

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

        dbf_adrs=[40218,40220]
        kof_adrs=40234

        dbf=float(util.data_to_u32(self.inv.read(dbf_adrs[0], 2)))/100.0
        kof=util.data_to_u32(self.inv.read(kof_adrs, 2))


        return "dfb: %f, kof: %d" % (dbf, kof)

        #der.DERError('Unimplemented function: freq_watt')


    '''
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

        der.DERError('Unimplemented function: freq_watt_curve')
    '''

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
        if params is not None:
            Ena=params['Ena']
            if Ena:
                # Ena==true
                self.inv.write(40216, util.u32_to_data(int(1132)))      # linear gradient
                dbf_adrs = [40218, 40220]
                kof_adrs = 40234

                dbf_set = int(round(params['dbf'],2)*100)
                kof_set = int(1/params['kf'])
                self.ts.log_debug("set dbf to %d and kof to %d" % (dbf_set,kof_set))
                self.inv.write(dbf_adrs[0], util.u32_to_data(dbf_set))      # dbf
                self.inv.write(dbf_adrs[1], util.u32_to_data(dbf_set))      # dbf
                self.inv.write(kof_adrs, util.u32_to_data(kof_set))      # kof


            else:
                # Ena==false
                self.inv.write(40216, util.u32_to_data(int(303)))       # off



        der.DERError('Unimplemented function: freq_watt_param')

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

        der.DERError('Unimplemented function: frt_stay_connected_high')

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

        der.DERError('Unimplemented function: frt_stay_connected_low')

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

        # reactive_power_dept_ref = {
        #     'None': 0,
        #     'WMax': 1,
        #     'VArMax': 2,
        #     'VArAval': 3,
        #     0: 'None',
        #     1: 'WMax',
        #     2: 'VArMax',
        #     3: 'VArAval'
        # }

        if self.inv is None:
            raise der.DERError('DER not initialized')

        #####  UNTESTED ####

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        # self.inv.write(40151, util.u32_to_data(802))
                        self.inv.write(40200, util.u32_to_data(1070))
                    else:
                        # self.inv.write(40151, util.u32_to_data(803))
                        self.inv.write(40200, util.u32_to_data(303))    #wanbin

                var_pct_mod = params.get('VArPct_Mod')
                if var_pct_mod is not None:
                    if var_pct_mod == 'WMax':
                        var_w_max_pct = int(params.get('VArWMaxPct'))
                        self.inv.write(40015, util.s16_to_data(int(var_w_max_pct)))
                        # self.inv.write(40153, util.s32_to_data(int(var_w_max_pct)))
                    else:
                        raise der.DERError('DER reactive power mode not supported')

            else:
                params = {}
                # enabled = util.data_to_u32(self.inv.read(40151, 1)) == 803
                enabled = util.data_to_u32(self.inv.read(40200, 2)) == 1070  # Reactive power Q, direct spec.
                # enabled = util.data_to_u32(self.inv.read(40200, 2)) == 1071  # React. power const. Q in kvar
                if enabled:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                params['VArPct_Mod'] = 'WMax'
                params['VArWMaxPct'] = util.data_to_s16(self.inv.read(40015, 1))
                # params['VArWMaxPct'] = util.data_to_s32(self.inv.read(40153, 2))
                # params['VArWMaxPct'] = util.data_to_s32(self.inv.read(40202, 2))  # Reactive power setpoint (VAr)
                params['VArWMaxPct'] = util.data_to_s32(self.inv.read(40204, 2))  # Reactive power setpoint (%)


        except Exception as e:
            raise der.DERError(str(e))

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
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        # self.inv.write(40151, util.u32_to_data(802))
                        self.inv.write(40210, util.u32_to_data(1078))
                    else:
                        # self.inv.write(40151, util.u32_to_data(803))
                        self.inv.write(40210, util.u32_to_data(303))
                        # Operating mode of active power limitation
                        # 303 = Off
                        # 1077 = Active power limitation P in W
                        # 1078 = Act. power lim. as % of Pmax
                        # 1079 = Act. power lim. via PV system ctrl
                        # 1390 = Active power limitation P via analogue input
                        # 1391 = Active power limitation P via digital inputs

                power = int(params.get('P'))
                # self.inv.write(40016, util.s16_to_data(int(power)))  # Active power setpoint P, in % of the maximum active power (PMAX) of the inverter
                # self.inv.write(40023, util.s16_to_data(int(power)))  # Normalized active power limitation by PV system ctrl, in %
                # self.inv.write(40143, util.s32_to_data(int(power)))  # Active power setpoint for the operating mode "Active power limitation P via PV system control" (A)
                # self.inv.write(40147, util.u32_to_data(int(power)))  # Generator active power limitation for the operating mode "Active power limitation P via system control" (A)
                # self.inv.write(40149, util.s32_to_data(int(power)))  # Active power setpoint for the operating mode "Active power limitation P via system control" (W)

                # self.inv.write(40212, util.u32_to_data(int(power)))  # Active power setpoint (W)
                self.inv.write(40214, util.u32_to_data(int(power)))  # Active power setpoint (%)

            else:
                params = {}
                # enabled = util.data_to_u32(self.inv.read(40151, 1)) == 803
                enabled = util.data_to_u32(self.inv.read(40210, 1)) == 1078
                if enabled:
                    params['Ena'] = False
                else:
                    params['Ena'] = True
                # params['P'] = util.data_to_s16(self.inv.read(40016, 1))
                # params['P'] = util.data_to_s16(self.inv.read(40023, 1))
                # params['P'] = util.data_to_s32(self.inv.read(40143, 2))
                # params['P'] = util.data_to_u32(self.inv.read(40147, 2))
                # params['P'] = util.data_to_s32(self.inv.read(40149, 2))
                params['P'] = util.data_to_u32(self.inv.read(40214, 2))

        except Exception as e:
            raise der.DERError(str(e))

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

        der.DERError('Unimplemented function: storage')

if __name__ == "__main__":
    pass
