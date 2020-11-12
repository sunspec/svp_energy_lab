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
    info.param(pname('slave_id'), label='Slave Id', default=3)
    info.param(pname('firmware'), label='Firmware Number', default='02.02.30.R',
               values=['02.02.30.R', '02.83.03.R', '02.84.01.R', '02.63.33.S'])
    info.param(pname('confgridguard'), label='Configure Grid Guard', default='False', values=['True', 'False'])
    info.param(pname('gridguard'), label='Grid Guard Number', default=12345678,
               active=pname('confgridguard'),  active_value='True')


GROUP_NAME = 'sma'


class DER(der.DER):

    def __init__(self, ts, group_name):
        der.DER.__init__(self, ts, group_name)
        self.inv = None
        self.ts = ts
        self.firmware = self.param_value('firmware')

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
            Grid Guard

        :return: 0 or 1 for GG off or on.
        """

        gg_reg = {'02.02.30.R': 43090, '02.84.01.R': 43090,
                  '02.83.03.R': 43090, '02.63.33.S': 43090}

        data = self.inv.read(gg_reg[self.firmware], 2)
        gg = util.data_to_u32(data)
        if int(gg) == 1:
            self.ts.log("Grid Guard is already set")
            return True

        if new_gg is not None:
            if self.ts is not None:
                self.ts.log('Writing new Grid Guard: %d' % new_gg)
            else:
                print(('Writing new Grid Guard: %d' % new_gg))
            self.inv.write(gg_reg[self.firmware], util.u32_to_data(int(new_gg)))
        self.ts.sleep(1)

        data = self.inv.read(gg_reg[self.firmware], 2)
        gg = util.data_to_u32(data)

        if gg == 0:
            if self.ts is not None:
                self.ts.log('Grid guard was not enabled')
            else:
                print('Grid guard was not enabled')
            return False
        else:
            if self.ts is not None:
                self.ts.log('Grid guard was enabled')
            else:
                print('Grid guard was enabled')
            return True

    def close(self):
        if self.inv is not None:
            self.inv.close()
            self.inv = None

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

        model_reg = {'02.02.30.R': 30053, '02.84.01.R': 30053, '02.83.03.R': 30053, '02.63.33.S': 30053}
        serial_reg = {'02.02.30.R': 30057, '02.84.01.R': 30057, '02.83.03.R': 30057, '02.63.33.S': 30057}
        # Software Package
        version_reg = {'02.02.30.R': 30059, '02.84.01.R': 30059, '02.83.03.R': 30059, '02.63.33.S': 30059}

        try:
            params = {}
            params['Manufacturer'] = 'SMA'
            model_code = util.data_to_u32(self.inv.read(model_reg[self.firmware], 2))
            if model_code == 9194:
                params['Model'] = 'STP 12000TL-US-10'
            if model_code == 9195:
                params['Model'] = 'STP 15000TL-US-10'
            if model_code == 9196:
                params['Model'] = 'STP 20000TL-US-10'
            if model_code == 9197:
                params['Model'] = 'STP 24000TL-US-10'
            if model_code == 9310:
                params['Model'] = 'STP 30000TL-US-10'

            params['Version'] = util.data_to_u32(self.inv.read(version_reg[self.firmware], 2))
            params['Options'] = ''
            params['SerialNumber'] = util.data_to_u32(self.inv.read(serial_reg[self.firmware], 2))

        except Exception as e:
            raise der.DERError('Info Error: %s' % e)

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

        # raise der.DERError('Unimplemented function: nameplate')
        return {}

    def measurements(self):
        """ Get measurement data.

        Params: None

        :return: Dictionary of measurement data.
        """

        a_reg = {'02.02.30.R': 30795, '02.84.01.R': 30795, '02.83.03.R': 30795, '02.63.33.S': 30795}
        v1_reg = {'02.02.30.R': 30783, '02.84.01.R': 30783, '02.83.03.R': 30783, '02.63.33.S': 30783}
        v2_reg = {'02.02.30.R': 30785, '02.84.01.R': 30785, '02.83.03.R': 30785, '02.63.33.S': 30785}
        v3_reg = {'02.02.30.R': 30787, '02.84.01.R': 30787, '02.83.03.R': 30787, '02.63.33.S': 30787}

        w_reg = {'02.02.30.R': 30775, '02.84.01.R': 30775, '02.83.03.R': 30775, '02.63.33.S': 30775}
        f_reg = {'02.02.30.R': 30803, '02.84.01.R': 30803, '02.83.03.R': 30803, '02.63.33.S': 30803}
        va_reg = {'02.02.30.R': 30813, '02.84.01.R': 30813, '02.83.03.R': 30813, '02.63.33.S': 30813}
        var_reg = {'02.02.30.R': 30805, '02.84.01.R': 30805, '02.83.03.R': 30805, '02.63.33.S': 30805}

        dc_i_reg = {'02.02.30.R': 30769, '02.84.01.R': 30769, '02.83.03.R': 30769, '02.63.33.S': 30769}
        dc_i2_reg = {'02.02.30.R': None, '02.84.01.R': 30957, '02.83.03.R': 30957, '02.63.33.S': None}
        dc_v_reg = {'02.02.30.R': 30771, '02.84.01.R': 30771, '02.83.03.R': 30771, '02.63.33.S': 30771}
        dc_v2_reg = {'02.02.30.R': None, '02.84.01.R': 30959, '02.83.03.R': 30959, '02.63.33.S': None}
        dc_p_reg = {'02.02.30.R': 30773, '02.84.01.R': 30773, '02.83.03.R': 30773, '02.63.33.S': 30773}
        dc_p2_reg = {'02.02.30.R': None, '02.84.01.R': 30961, '02.83.03.R': 30961, '02.63.33.S': None}

        pf_reg = {'02.02.30.R': 30821, '02.84.01.R': 30949, '02.83.03.R': 30949, '02.63.33.S': 30821}
        eei_pf_reg = {'02.02.30.R': 31221, '02.84.01.R': 31221, '02.83.03.R': 31221, '02.63.33.S': 31221}  # EEI

        try:
            params = {}
            params['A'] = util.data_to_u32(self.inv.read(a_reg[self.firmware], 2))/1000.
            params['AphA'] = params['A']/3.
            params['AphB'] = params['A']/3.
            params['AphC'] = params['A']/3.
            params['PPVphAB'] = None
            params['PPVphBC'] = None
            params['PPVphCA'] = None
            params['PhVphA'] = util.data_to_u32(self.inv.read(v1_reg[self.firmware], 2))/100.
            params['PhVphB'] = util.data_to_u32(self.inv.read(v2_reg[self.firmware], 2))/100.
            params['PhVphC'] = util.data_to_u32(self.inv.read(v3_reg[self.firmware], 2))/100.
            params['W'] = float(util.data_to_s32(self.inv.read(w_reg[self.firmware], 2)))
            params['Hz'] = util.data_to_u32(self.inv.read(f_reg[self.firmware], 2))/100.
            params['VA'] = float(util.data_to_s32(self.inv.read(va_reg[self.firmware], 2)))
            params['VAr'] = float(util.data_to_s32(self.inv.read(var_reg[self.firmware], 2)))
            # pf = util.data_to_u32(self.inv.read(pf_reg[self.firmware], 2)) / 1000.
            params['PF'] = util.data_to_s32(self.inv.read(eei_pf_reg[self.firmware], 2)) / 1000.
            params['WH'] = None
            params['DCA'] = util.data_to_s32(self.inv.read(dc_i_reg[self.firmware], 2))/1000.
            if dc_i2_reg[self.firmware] is not None:
                params['DCA'] += util.data_to_s32(self.inv.read(dc_i2_reg[self.firmware], 2)) / 1000.
            params['DCV'] = util.data_to_s32(self.inv.read(dc_v_reg[self.firmware], 2)) / 100.
            params['DCW'] = float(util.data_to_s32(self.inv.read(dc_p_reg[self.firmware], 2)))
            if dc_p2_reg[self.firmware] is not None:
                params['DCW'] += float(util.data_to_s32(self.inv.read(dc_p2_reg[self.firmware], 2)))
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

        wlim_reg = {'02.02.30.R': 31405, '02.84.01.R': 31405, '02.83.03.R': 31405, '02.63.33.S': 31405}
        v_ref_reg = {'02.02.30.R': 40472, '02.84.01.R': 40472, '02.83.03.R': 40472, '02.63.33.S': 40472}  # PV sys cntrl
        v_ref_ofs_reg = {'02.02.30.R': 40474, '02.84.01.R': 40474, '02.83.03.R': 40474, '02.63.33.S': 40474}  # PV sys cntrl
        v_max_reg = {'02.02.30.R': 41125, '02.84.01.R': 41125, '02.83.03.R': 41125, '02.63.33.S': 41125}
        v_min_reg = {'02.02.30.R': 41123, '02.84.01.R': 41123, '02.83.03.R': 41123, '02.63.33.S': 41123}
        va_max_reg = {'02.02.30.R': None, '02.84.01.R': 40185, '02.83.03.R': 40185, '02.63.33.S': None}
        var_max_reg = {'02.02.30.R': None, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': None}
        wgra_reg = {'02.02.30.R': 40234, '02.84.01.R': 40234, '02.83.03.R': 40234, '02.63.33.S': 40234}
        pfmin_reg = {'02.02.30.R': None, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': None}
        varact_reg = {'02.02.30.R': None, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': None}

        try:
            params = {}
            params['WMax'] = util.data_to_u32(self.inv.read(wlim_reg[self.firmware], 2)) / 1000.
            params['VRef'] = util.data_to_u32(self.inv.read(v_ref_reg[self.firmware], 2))  # V
            params['VRefOfs'] = util.data_to_s32(self.inv.read(v_ref_ofs_reg[self.firmware], 2))  # V
            params['VMax'] = util.data_to_u32(self.inv.read(v_max_reg[self.firmware], 2)) / 100.  # V, for reconnect
            params['VMin'] = util.data_to_u32(self.inv.read(v_min_reg[self.firmware], 2)) / 100.  # V, for reconnect
            params['VAMax'] = util.data_to_u32(self.inv.read(va_max_reg[self.firmware], 2))
            params['VArMaxQ1'] = None
            params['VArMaxQ2'] = None
            params['VArMaxQ3'] = None
            params['VArMaxQ4'] = None
            params['WGra'] = util.data_to_s32(self.inv.read(wgra_reg[self.firmware], 2))  # V
            params['PFMinQ1'] = None
            params['PFMinQ2'] = None
            params['PFMinQ3'] = None
            params['PFMinQ4'] = None
            params['VArAct'] = None
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def conn_status(self, params=None):
        """ Get status of controls (binary True if active).
        :return: Dictionary of active controls.
        """

        # SMA Operating status:
        # 295 = MPP
        # 1467 = Start
        # 381 = Stop
        # 2119 = Derating
        # 1469 = Shut down
        # 1392 = Fault
        # 1480 = Waiting for utilities company
        # 1393 = Waiting for PV voltage
        # 443 = Constant voltage
        # 1855 = Stand-alone operation

        op_reg = {'02.02.30.R': 40029, '02.84.01.R': 40029, '02.83.03.R': 40029, '02.63.33.S': 40029}

        try:
            params = {}
            status_enum = util.data_to_u32(self.inv.read(op_reg[self.firmware], 2))
            if status_enum == 295:
                params['Status'] = 'Connected'
            else:
                params['Status'] = 'Not Connected'
        except Exception as e:
            raise der.DERError(str(e))

        return params

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

        # SMA Fast shut-down:
        # 381 = Stop
        # 1467 = Start
        # 1749 = Full stop

        conn_reg = {'02.02.30.R': 40018, '02.84.01.R': 40018, '02.83.03.R': 40018, '02.63.33.S': 40018}

        try:
            if params is not None:
                conn = params.get('Conn')
                if conn is not None:
                    if conn is True:
                        reg = 1467  # start
                    else:
                        reg = 1749  # Full stop (AC and DC side)
                        # reg = 381  # Stop (AC side)
                    self.inv.write(conn_reg[self.firmware], util.u32_to_data(int(reg)))
            else:
                params = {}
                reg = self.inv.read(conn_reg[self.firmware], 2)
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

        excitation_reg = {'02.02.30.R': 40208, '02.84.01.R': 40208, '02.83.03.R': 40025, '02.63.33.S': 40025}
        pf_s32_reg = {'02.02.30.R': None, '02.84.01.R': 40206, '02.83.03.R': 40025, '02.63.33.S': 40025}
        pf_u16_reg = {'02.02.30.R': 40206, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': None}
        pf_eei_reg = {'02.02.30.R': None, '02.84.01.R': 40999, '02.83.03.R': 40999, '02.63.33.S': None}
        # 1075 = cos phi, specified by PV system control
        # 1074 = cos phi, direct specific.
        q_mode_val = {'02.02.30.R': 1074, '02.84.01.R': 1074, '02.83.03.R': 1074, '02.63.33.S': 1074}
        q_mode_reg = {'02.02.30.R': 40200, '02.84.01.R': 40200, '02.83.03.R': 40200, '02.63.33.S': 40200}

        try:
            if params is not None:
                pf = params.get('PF')

                if pf is not None:
                    # write excitation register
                    if pf > 0:
                        reg = 1042  # Lagging, Underexcited
                    else:
                        reg = 1041  # Leading, Overexcited
                    self.inv.write(excitation_reg[self.firmware], util.u32_to_data(int(reg)))

                    # write pf value register
                    if isinstance(pf_s32_reg[self.firmware], int):
                        self.inv.write(pf_s32_reg[self.firmware], util.s32_to_data(int(abs(pf)*100)))
                    else:
                        reg = int(abs(round(pf, 4) * 10000))
                        self.inv.write(pf_u16_reg[self.firmware], util.u16_to_data(int(reg)))

                ena = params.get('Ena')
                if ena is not None:
                    # configure the reactive power mode to PF
                    if ena is True:
                        reg = q_mode_val[self.firmware]  # cos phi
                    else:
                        reg = 303  # off
                    self.inv.write(q_mode_reg[self.firmware], util.u32_to_data(int(reg)))

            else:
                params = {}
                reg = self.inv.read(q_mode_reg[self.firmware], 2)
                if util.data_to_u32(reg) == q_mode_val[self.firmware]:
                    params['Ena'] = True
                else:
                    params['Ena'] = False

                # Read back option: Operating mode of stat.V stab., stat.V stab. config.:
                # q_mode_meas = util.data_to_u32(self.inv.read(30825, 2))
                # if q_mode_meas == q_mode_val[self.firmware]:
                #     self.ts.log_debug('PF mode is enabled')

                if isinstance(pf_s32_reg[self.firmware], int):  # s32
                    params['PF'] = float(util.data_to_s32(self.inv.read(pf_s32_reg[self.firmware], 2)))/100.0
                    # params['PF'] = float(util.data_to_s32(self.inv.read(pf_eei_reg[self.firmware], 2)))/10000.0
                else:
                    pf = self.inv.read(pf_u16_reg[self.firmware], 2)
                    params['PF'] = float(util.data_to_u16(pf))/100.0

        except Exception as e:
            raise der.DERError(str(e))

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
        if self.inv is None:
            raise der.DERError('DER not initialized')

        control_mode = {'02.02.30.R': 'PMAX', '02.84.01.R': 'PMAX', '02.83.03.R': 'PMAX', '02.63.33.S': 'PMAX'}
        # Active power setpoint P, in % of the maximum active power (PMAX) of the inverter
        wlim_pmaxpct_reg = {'02.02.30.R': 40016, '02.84.01.R': 40214, '02.83.03.R': 40016, '02.63.33.S': 40016}
        # Normalized active power limitation by PV system ctrl, in %
        wlim_pvpct_reg = {'02.02.30.R': 40023, '02.84.01.R': None, '02.83.03.R': 40023, '02.63.33.S': 40023}
        # Active power setpoint for the operating mode "Active power limitation P via PV system control" (A)
        wlim_pvcurrent_reg = {'02.02.30.R': 40143, '02.84.01.R': None, '02.83.03.R': 40143, '02.63.33.S': 40143}
        # Generator active power limitation for the operating mode "Active power limitation P via system control" (A)
        wlim_current_reg = {'02.02.30.R': 40147, '02.84.01.R': None, '02.83.03.R': 40147, '02.63.33.S': 40147}
        # Active power setpoint for the operating mode "Active power limitation P via system control" (W)
        wlim_power_reg = {'02.02.30.R': 40149, '02.84.01.R': 40212, '02.83.03.R': 40149, '02.63.33.S': 40149}

        # Operating mode of feed-in management:
        # 303 = Off
        # 1077 = Active power limitation P in W
        # 1078 = Act. power lim. as % of Pmax
        # 1079 = Act. power lim. via PV system ctrl
        wlim_ena_reg = {'02.02.30.R': 40151, '02.84.01.R': 40210, '02.83.03.R': 40210, '02.63.33.S': 40151}
        wlim_type_val = {'02.02.30.R': 1078, '02.84.01.R': 1078, '02.83.03.R': 1078, '02.63.33.S': 1078}

        try:
            if params is not None:
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        self.inv.write(wlim_ena_reg[self.firmware], util.u32_to_data(wlim_type_val[self.firmware]))
                    else:
                        self.inv.write(wlim_ena_reg[self.firmware], util.u32_to_data(303))

                if params.get('WMaxPct') is not None:
                    power = int(params.get('WMaxPct'))
                if control_mode[self.firmware] == 'PMAX':
                    self.inv.write(wlim_pmaxpct_reg[self.firmware], util.u32_to_data(int(power)))
                elif control_mode[self.firmware] == 'PVPCT':
                    self.inv.write(wlim_pvpct_reg[self.firmware], util.s16_to_data(int(power)))
                elif control_mode[self.firmware] == 'PVCURRENT':
                    self.inv.write(wlim_pvcurrent_reg[self.firmware], util.s32_to_data(int(power)))
                elif control_mode[self.firmware] == 'CURRENT':
                    self.inv.write(wlim_current_reg[self.firmware], util.u32_to_data(int(power)))
                elif control_mode[self.firmware] == 'POWER':
                    self.inv.write(wlim_power_reg[self.firmware], util.u32_to_data(int(power)))
                else:
                    raise der.DERError('Unknowned Limit Power operating mode')

            else:
                params = {}
                if util.data_to_u32(self.inv.read(wlim_ena_reg[self.firmware], 2)) == 303:
                    params['Ena'] = False
                else:
                    params['Ena'] = True

                if control_mode[self.firmware] == 'PMAX':
                    params['WMaxPct'] = util.data_to_u32(self.inv.read(wlim_pmaxpct_reg[self.firmware], 2))
                elif control_mode[self.firmware] == 'PVPCT':
                    params['WMaxPct'] = util.data_to_s16(self.inv.read(wlim_pvpct_reg[self.firmware], 1))
                elif control_mode[self.firmware] == 'PVCURRENT':
                    params['WMaxPct'] = util.data_to_s32(self.inv.read(wlim_pvcurrent_reg[self.firmware], 2))
                elif control_mode[self.firmware] == 'CURRENT':
                    params['WMaxPct'] = util.data_to_u32(self.inv.read(wlim_current_reg[self.firmware], 2))
                elif control_mode[self.firmware] == 'POWER':
                    params['WMaxPct'] = util.data_to_u32(self.inv.read(wlim_power_reg[self.firmware], 2))
                else:
                    der.DERError('Unknowned Limit Power operating mode')

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def get_curve_registers(self, id):
        """
        Returns dictionary of dictionaries with curve parameters

        :param id: SMA Curve Number
        :return: dict with registers or the number of points, x and y units, and 4 x and y points

        NPTS = Number of supported curve points to be used
        TIME_CHAR = Adjustment time of characteristic operating point, conf. of grid integr. char. 1
        RAMP_DOWN = Decrease ramp, conf. of grid integr. char. 1
        RAMP_UP = Increase ramp, conf. of grid integr. char. 1

        Units for characteristic curve - X units
            1975 = Voltage in V
            1976 = Voltage in percentages of Un
            3158 = Active power as a percentage of Pmax
            3420 = Hertz
            3421 = Hertz as the difference from the nominal frequency

        Units for characteristic curve - Y units
            1977 = Var in percentages of Pmax
            1978 = Power in percentages of Pmax
            1979 = Power in percentages of frozen active power
            2272 = cos Phi (EEI convention)
        """

        if id == 1:  # curve 1
            NPTS = {'02.02.30.R': 40262, '02.84.01.R': 41023, '02.83.03.R': 41023, '02.63.33.S': 40262}
            TIME_CHAR = {'02.02.30.R': 41017, '02.84.01.R': 41017, '02.83.03.R': 41017, '02.63.33.S': 41017}
            RAMP_UP = {'02.02.30.R': 41021, '02.84.01.R': 41021, '02.83.03.R': 41021, '02.63.33.S': 41021}
            RAMP_DOWN = {'02.02.30.R': 41019, '02.84.01.R': 41019, '02.83.03.R': 41019, '02.63.33.S': 41019}
            X_UNITS = {'02.02.30.R': 40977, '02.84.01.R': 41025, '02.83.03.R': 40977, '02.63.33.S': 40977}
            X1 = {'02.02.30.R': 41077, '02.84.01.R': 41029, '02.83.03.R': 41029, '02.63.33.S': 40282}
            X2 = {'02.02.30.R': 41081, '02.84.01.R': 41033, '02.83.03.R': 41033, '02.63.33.S': 40284}
            X3 = {'02.02.30.R': 41085, '02.84.01.R': 41037, '02.83.03.R': 41037, '02.63.33.S': 40286}
            X4 = {'02.02.30.R': 41089, '02.84.01.R': 41041, '02.83.03.R': 41041, '02.63.33.S': 40288}
            Y_UNITS = {'02.02.30.R': 40957, '02.84.01.R': 41027, '02.83.03.R': 40957, '02.63.33.S': 40957}
            Y1 = {'02.02.30.R': 41079, '02.84.01.R': 41031, '02.83.03.R': 41031, '02.63.33.S': 40306}
            Y2 = {'02.02.30.R': 41083, '02.84.01.R': 41035, '02.83.03.R': 41035, '02.63.33.S': 40308}
            Y3 = {'02.02.30.R': 41087, '02.84.01.R': 41039, '02.83.03.R': 41039, '02.63.33.S': 40310}
            Y4 = {'02.02.30.R': 41091, '02.84.01.R': 41043, '02.83.03.R': 41043, '02.63.33.S': 40312}
        elif id == 2:
            NPTS = {'02.02.30.R': 40262, '02.84.01.R': 41071, '02.83.03.R': 41071, '02.63.33.S': 40262}
            TIME_CHAR = {'02.02.30.R': 41065, '02.84.01.R': 41065, '02.83.03.R': 41065, '02.63.33.S': 41065}
            RAMP_UP = {'02.02.30.R': 41067, '02.84.01.R': 41067, '02.83.03.R': 41067, '02.63.33.S': 41067}
            RAMP_DOWN = {'02.02.30.R': 41069, '02.84.01.R': 41069, '02.83.03.R': 41069, '02.63.33.S': 41069}
            X_UNITS = {'02.02.30.R': 40979, '02.84.01.R': 41073, '02.83.03.R': 40979, '02.63.33.S': 40979}
            X1 = {'02.02.30.R': None, '02.84.01.R': 41077, '02.83.03.R': 41077, '02.63.33.S': 40330}
            X2 = {'02.02.30.R': None, '02.84.01.R': 41081, '02.83.03.R': 41081, '02.63.33.S': 40332}
            X3 = {'02.02.30.R': None, '02.84.01.R': 41085, '02.83.03.R': 41085, '02.63.33.S': 40334}
            X4 = {'02.02.30.R': None, '02.84.01.R': 41089, '02.83.03.R': 41089, '02.63.33.S': 40336}
            Y_UNITS = {'02.02.30.R': 40959, '02.84.01.R': 41075, '02.83.03.R': 40959, '02.63.33.S': 40959}
            Y1 = {'02.02.30.R': None, '02.84.01.R': 41079, '02.83.03.R': 41079, '02.63.33.S': 40354}
            Y2 = {'02.02.30.R': None, '02.84.01.R': 41083, '02.83.03.R': 41083, '02.63.33.S': 40356}
            Y3 = {'02.02.30.R': None, '02.84.01.R': 41087, '02.83.03.R': 41087, '02.63.33.S': 40358}
            Y4 = {'02.02.30.R': None, '02.84.01.R': 41091, '02.83.03.R': 41091, '02.63.33.S': 40360}
        else:  # id == 3
            NPTS = {'02.02.30.R': None, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': None}
            TIME_CHAR = {'02.02.30.R': 41065, '02.84.01.R': 41065, '02.83.03.R': 41065, '02.63.33.S': 41065}
            RAMP_UP = {'02.02.30.R': 41067, '02.84.01.R': 41067, '02.83.03.R': 41067, '02.63.33.S': 41067}
            RAMP_DOWN = {'02.02.30.R': 41069, '02.84.01.R': 41069, '02.83.03.R': 41069, '02.63.33.S': 41069}
            X_UNITS = {'02.02.30.R': 40981, '02.84.01.R': None, '02.83.03.R': 40981, '02.63.33.S': 40981}
            X1 = {'02.02.30.R': None, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': 40378}
            X2 = {'02.02.30.R': None, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': 40380}
            X3 = {'02.02.30.R': None, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': 40382}
            X4 = {'02.02.30.R': None, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': 40384}
            Y_UNITS = {'02.02.30.R': 40961, '02.84.01.R': None, '02.83.03.R': 40961, '02.63.33.S': 40961}
            Y1 = {'02.02.30.R': None, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': 40402}
            Y2 = {'02.02.30.R': None, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': 40404}
            Y3 = {'02.02.30.R': None, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': 40406}
            Y4 = {'02.02.30.R': None, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': 40408}

        return {'NPts': NPTS, 'x_units': X_UNITS, 'y_units': Y_UNITS, 'x1': X1, 'x2': X2, 'x3': X3, 'x4': X4, 'y1': Y1,
                'y2': Y2, 'y3': Y3, 'y4': Y4, 'TIME_CHAR': TIME_CHAR, 'RAMP_UP': RAMP_UP, 'RAMP_DOWN': RAMP_DOWN}

    def volt_watt(self, params=None):
        """volt/watt control

        :param params: Dictionary of parameters to be updated.
            'Ena': True/False
            'ActCrv': 0
            'NCrv': 1
            'NPt': 4
            'WinTms': 0
            'RvrtTms': 0
            'RmpTms': 0
            'curve': {
                 'ActPt': 3
                 'v': [95, 101, 105]
                 'w': [100, 100, 0]
                 'DeptRef': 1
                 'RmpPt1Tms': 0
                 'RmpDecTmm': 0
                 'RmpIncTmm': 0
                 }
        :return: Dictionary of active settings for volt_watt
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        # 2269 = Reactive power charact. curve
        q_mode_ena = {'02.02.30.R': 40200, '02.84.01.R': 40200, '02.83.03.R': 40200, '02.63.33.S': 40200}
        q_mode_ena_val = {'02.02.30.R': 1069, '02.84.01.R': 2269, '02.83.03.R': 2269, '02.63.33.S': 1069}

        # Curve 1 = Characteristic curve number, configuration of characteristic curve mode [1]
        nonactive_crv_activation = {'02.02.30.R': 40937, '02.84.01.R': 40937, '02.83.03.R': 40937, '02.63.33.S': 40937}
        active_crv_activation = {'02.02.30.R': 40937, '02.84.01.R': 41063, '02.83.03.R': 40937, '02.63.33.S': 40937}
        vw_ena_curve_val = {'02.02.30.R': 308, '02.84.01.R': 308, '02.83.03.R': 308, '02.63.33.S': 308}
        # 2nd characteristic curve number, configuration of characteristic curve mode
        # This maps the characteristic curve points to the characteristic behavior
        vw_curve_num = {'02.02.30.R': 40937, '02.84.01.R': 41061, '02.83.03.R': 40917, '02.63.33.S': 40937}

        # Use curve 2
        reg = self.get_curve_registers(2)
        n_pts = reg['NPts']
        v_units_val = {'02.02.30.R': 1976, '02.84.01.R': 1976, '02.83.03.R': 1976, '02.63.33.S': 1976}
        p_units_val = {'02.02.30.R': 1978, '02.84.01.R': 1978, '02.83.03.R': 1978, '02.63.33.S': 1978}
        v_adrs = [reg['x1'][self.firmware], reg['x2'][self.firmware]]
        w_adrs = [reg['y1'][self.firmware], reg['y2'][self.firmware]]

        if params is not None:
            if params['Ena']:
                # put in characteristic curve mode
                self.inv.write(q_mode_ena[self.firmware], util.u32_to_data(q_mode_ena_val[self.firmware]))

                # enable/disable curves
                self.inv.write(nonactive_crv_activation[self.firmware], util.u32_to_data(303))
                self.inv.write(active_crv_activation[self.firmware],
                               util.u32_to_data(vw_ena_curve_val[self.firmware]))

                # set configuration characteristic to the active curve
                self.ts.log('Using Curve 2 in SMA for the VW Write')
                params['ActCrv'] = 2
                self.inv.write(vw_curve_num[self.firmware], util.u32_to_data(params['ActCrv']))

                # set curve units to %Vnom and %PMax
                self.inv.write(reg['x_units'][self.firmware], util.u32_to_data(int(v_units_val[self.firmware])))
                self.inv.write(reg['y_units'][self.firmware], util.u32_to_data(int(p_units_val[self.firmware])))
            else:
                self.inv.write(active_crv_activation[self.firmware], util.u32_to_data(303))
                self.inv.write(q_mode_ena[self.firmware], util.u32_to_data(303))
            if params.get('NPt') is not None:
                self.inv.write(n_pts[self.firmware], util.u32_to_data(params['NPt']))
            if params.get('curve') is not None:
                if params['curve'].get('v') is not None:
                    v = [params['curve']['v'][0], params['curve']['v'][1]]
                    if len(v) != 2:
                        self.ts.log_warning('Only two VW voltage points used!')
                    if params['curve']['v'][0] is not None:
                        self.inv.write(v_adrs[0], util.s32_to_data(int(v[0]*1000)))
                    if params['curve']['v'][1] is not None:
                        self.inv.write(v_adrs[1], util.s32_to_data(int(v[1]*1000)))
                if params['curve'].get('w') is not None:
                    w = [params['curve']['w'][0], params['curve']['w'][1]]
                    if len(w) != 2:
                        self.ts.log_warning('Only two VW power points used!')
                    if params['curve']['w'][0] is not None:
                        self.inv.write(w_adrs[0], util.s32_to_data(int(w[0]*1000)))
                    if params['curve']['w'][1] is not None:
                        self.inv.write(w_adrs[1], util.s32_to_data(int(w[1]*1000)))

            # self.debug_read_curves()

        else:
            params = {}
            q_mode = util.data_to_u32(self.inv.read(q_mode_ena[self.firmware], 2)) == q_mode_ena_val[self.firmware]
            curve_ena = util.data_to_u32(self.inv.read(active_crv_activation[self.firmware], 2)) == \
                        vw_ena_curve_val[self.firmware]
            if q_mode and curve_ena:
                params['Ena'] = True
            else:
                params['Ena'] = False

            params['NPt'] = util.data_to_u32(self.inv.read(n_pts[self.firmware], 2))

            v0 = util.data_to_s32(self.inv.read(v_adrs[0], 2))/1000.
            v1 = util.data_to_s32(self.inv.read(v_adrs[1], 2))/1000.
            w0 = util.data_to_s32(self.inv.read(w_adrs[0], 2))/1000.
            w1 = util.data_to_s32(self.inv.read(w_adrs[1], 2))/1000.

            params['curve'] = {'id': 1, 'v': [v0, v1], 'w': [w0, w1]}

        return params

    def watt_var(self, params=None):
        """watt/var control

        :param params: Dictionary of parameters to be updated.
            'Ena': True/False
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
        if self.inv is None:
            raise der.DERError('DER not initialized')

        # 2269 = Reactive power charact. curve
        q_mode_ena = {'02.02.30.R': 40200, '02.84.01.R': 40200, '02.83.03.R': 40200, '02.63.33.S': 40200}
        q_mode_ena_val = {'02.02.30.R': 1069, '02.84.01.R': 2269, '02.83.03.R': 2269, '02.63.33.S': 1069}

        # Curve 1 = Characteristic curve number, configuration of characteristic curve mode [1]
        nonactive_crv_activation = {'02.02.30.R': 40937, '02.84.01.R': 40937, '02.83.03.R': 40937, '02.63.33.S': 40937}
        active_crv_activation = {'02.02.30.R': 40937, '02.84.01.R': 41063, '02.83.03.R': 40937, '02.63.33.S': 40937}
        wv_ena_curve_val = {'02.02.30.R': 308, '02.84.01.R': 308, '02.83.03.R': 308, '02.63.33.S': 308}
        # 2nd characteristic curve number, configuration of characteristic curve mode
        # This maps the characteristic curve points to the characteristic behavior
        wv_curve_num = {'02.02.30.R': 40937, '02.84.01.R': 41061, '02.83.03.R': 40917, '02.63.33.S': 40937}

        # Use curve 2
        reg = self.get_curve_registers(2)
        n_pts = reg['NPts']
        w_units_val = {'02.02.30.R': 3158, '02.84.01.R': 3158, '02.83.03.R': 3158, '02.63.33.S': 3158}
        var_units_val = {'02.02.30.R': 1977, '02.84.01.R': 1977, '02.83.03.R': 1977, '02.63.33.S': 1977}
        w_adrs = [reg['x1'][self.firmware], reg['x2'][self.firmware],
                  reg['x3'][self.firmware],  reg['x4'][self.firmware]]
        var_adrs = [reg['y1'][self.firmware], reg['y2'][self.firmware],
                    reg['y3'][self.firmware], reg['y4'][self.firmware]]

        if params is not None:
            if params['Ena']:
                # put in characteristic curve mode
                self.inv.write(q_mode_ena[self.firmware], util.u32_to_data(q_mode_ena_val[self.firmware]))

                # enable/disable curves
                self.inv.write(nonactive_crv_activation[self.firmware], util.u32_to_data(303))
                self.inv.write(active_crv_activation[self.firmware],
                               util.u32_to_data(wv_ena_curve_val[self.firmware]))

                # set configuration characteristic to the active curve
                self.ts.log('Using Curve 2 in SMA for the Watt/Var Write')
                params['ActCrv'] = 2
                self.inv.write(wv_curve_num[self.firmware], util.u32_to_data(params['ActCrv']))

                # set curve units to p = %PMax and var = %PMax
                self.inv.write(reg['x_units'][self.firmware], util.u32_to_data(int(w_units_val[self.firmware])))
                self.inv.write(reg['y_units'][self.firmware], util.u32_to_data(int(var_units_val[self.firmware])))
            else:
                self.inv.write(active_crv_activation[self.firmware], util.u32_to_data(303))
                self.inv.write(q_mode_ena[self.firmware], util.u32_to_data(303))
            if params.get('NPt') is not None:
                self.inv.write(n_pts[self.firmware], util.u32_to_data(params['NPt']))
            if params.get('RmpTms') is not None:
                time_const = params['RmpTms']
                self.inv.write(reg['TIME_CHAR'][self.firmware], util.u32_to_data(int(round(time_const*10))))

            if params.get('curve') is not None:
                w = params['curve'].get('w')
                if w is not None:
                    w_len = len(w)
                    for i in range(w_len):  # SunSpec point index starts at 1
                        self.inv.write(w_adrs[i], util.s32_to_data(int(round(w[i], 3) * 1000)))
                        self.ts.log_debug('Writing w point %s to reg %s with value %s' % (i, w_adrs[i], w[i]))

                # set var points
                var = params['curve'].get('var')
                if var is not None:
                    var_len = len(var)
                    for i in range(var_len):  # SunSpec point index starts at 1
                        self.inv.write(var_adrs[i], util.s32_to_data(int(round(var[i], 3) * 1000)))
                        self.ts.log_debug('Writing v point %s to reg %s with value %s' % (i, var_adrs[i], var[i]))

        else:
            params = {}
            q_mode = util.data_to_u32(self.inv.read(q_mode_ena[self.firmware], 2)) == q_mode_ena_val[self.firmware]
            curve_ena = util.data_to_u32(self.inv.read(active_crv_activation[self.firmware], 2)) == \
                        wv_ena_curve_val[self.firmware]
            if q_mode and curve_ena:
                params['Ena'] = True
            else:
                params['Ena'] = False

            params['NPt'] = util.data_to_u32(self.inv.read(n_pts[self.firmware], 2))
            params['RmpTms'] = util.data_to_u32(self.inv.read(reg['TIME_CHAR'][self.firmware], 2))/10.
            params['ActCrv'] = 2
            params['NCrv'] = 3

            w = []
            var = []
            if reg['NPts'][self.firmware] is not None:
                n_pt = int(util.data_to_u32(self.inv.read(reg['NPts'][self.firmware], 2)))
            else:
                n_pt = 3
            for i in range(int(n_pt)):
                w.append(util.data_to_s32(self.inv.read(w_adrs[i], 2))/1000.)
                var.append(util.data_to_s32(self.inv.read(var_adrs[i], 2))/1000.)

            params['curve'] = {'id': 1, 'w': w, 'var': var}

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
            'curve': {
                 'v': [50, 75, 100]
                 'var': [0, 0, -100]
                 'DeptRef': 1
                 'RmpDecTmm': 0
                 'RmpIncTmm': 0
                 }
        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for volt/var control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        # 2269 = Reactive power charact. curve
        q_mode_ena = {'02.02.30.R': 40200, '02.84.01.R': 40200, '02.83.03.R': 40200, '02.63.33.S': 40200}
        q_mode_ena_val = {'02.02.30.R': 1069, '02.84.01.R': 2269, '02.83.03.R': 2269, '02.63.33.S': 1069}

        # Curve 1 = Characteristic curve number, configuration of characteristic curve mode [1]
        nonactive_crv_activation = {'02.02.30.R': 40937, '02.84.01.R': 40937, '02.83.03.R': 40937, '02.63.33.S': 40937}
        active_crv_activation = {'02.02.30.R': 40937, '02.84.01.R': 41063, '02.83.03.R': 40937, '02.63.33.S': 40937}
        vw_ena_curve_val = {'02.02.30.R': 308, '02.84.01.R': 308, '02.83.03.R': 308, '02.63.33.S': 308}
        # 2nd characteristic curve number, configuration of characteristic curve mode
        # This maps the characteristic curve points to the characteristic behavior
        vw_curve_num = {'02.02.30.R': 40937, '02.84.01.R': 41061, '02.83.03.R': 40917, '02.63.33.S': 40937}

        # Use curve 2
        reg = self.get_curve_registers(2)
        n_pts = reg['NPts']
        # Units for characteristic curve 1. Voltage in %Vnom and Var in %Pmax
        v_units_val = {'02.02.30.R': 1976, '02.84.01.R': 1976, '02.83.03.R': 1976, '02.63.33.S': 1976}
        q_units_val = {'02.02.30.R': 1977, '02.84.01.R': 1977, '02.83.03.R': 1977, '02.63.33.S': 1977}

        if params is not None:
            curve = params.get('curve')  # Must write curve first because there is a read() in volt_var_curve
            if curve is not None:
                self.volt_var_curve(id=2, params=curve)

            ena = params.get('Ena')
            if ena is not None:
                # put in Reactive power charact. curve, not Q(V) mode
                self.inv.write(q_mode_ena[self.firmware], util.u32_to_data(q_mode_ena_val[self.firmware]))

                # enable/disable curves
                self.inv.write(nonactive_crv_activation[self.firmware], util.u32_to_data(303))
                self.inv.write(active_crv_activation[self.firmware],
                               util.u32_to_data(vw_ena_curve_val[self.firmware]))

                # set configuration characteristic to the active curve
                self.ts.log('Using Curve 2 in SMA for the VV Write')
                params['ActCrv'] = 2
                self.inv.write(vw_curve_num[self.firmware], util.u32_to_data(params['ActCrv']))

                # set curve units to %Vnom and %PMax
                self.inv.write(reg['x_units'][self.firmware], util.u32_to_data(int(v_units_val[self.firmware])))
                self.inv.write(reg['y_units'][self.firmware], util.u32_to_data(int(q_units_val[self.firmware])))
            else:
                self.inv.write(active_crv_activation[self.firmware], util.u32_to_data(303))
                self.inv.write(q_mode_ena[self.firmware], util.u32_to_data(303))

            if params.get('NPt') is not None:
                self.inv.write(n_pts[self.firmware], util.u32_to_data(params['NPt']))

        else:
            params = {}
            reg = self.inv.read(q_mode_ena_val[self.firmware], 2)
            if util.data_to_u32(reg) == q_mode_ena[self.firmware]:
                params['Ena'] = True
            else:
                params['Ena'] = False

            params['ActCrv'] = 2

            params['NCrv'] = 3  # SMA supports 3 curves (...or sometimes 2)
            if params.get('ActCrv') is not None:
                params['curve'] = self.volt_var_curve(id=params['ActCrv'])

        return params

    def volt_var_curve(self, id=2, params=None):
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

        reg = self.get_curve_registers(2)
        v_adrs = [reg['x1'][self.firmware], reg['x2'][self.firmware],
                  reg['x3'][self.firmware], reg['x4'][self.firmware]]
        var_adrs = [reg['y1'][self.firmware], reg['y2'][self.firmware],
                    reg['y3'][self.firmware], reg['y4'][self.firmware]]

        volt_var_dept_ref = {
            'W_MAX_PCT': 1,
            'VAR_MAX_PCT': 2,
            'VAR_AVAL_PCT': 3,
            1: 'W_MAX_PCT',
            2: 'VAR_MAX_PCT',
            3: 'VAR_AVAL_PCT'
        }


        if int(id) > 3:
            raise der.DERError('Curve id out of range: %s' % id)

        if params is not None:
            n_pt = int(util.data_to_s32(self.inv.read(reg['NPts'][self.firmware], 2)))
            self.ts.log_debug('Number of points in the curve is %s' % n_pt)
            if n_pt != len(params['v']):
                self.inv.write(reg['NPts'][self.firmware], util.u32_to_data(int(len(params['v']))))
                self.ts.log_debug('Wrote number of points (%d) to Reg %s.' %
                                  (int(len(params['v'])), reg['NPts'][self.firmware]))

            # set voltage points
            v = params.get('v')
            if v is not None:
                v_len = len(v)
                for i in range(v_len):  # SunSpec point index starts at 1
                    self.inv.write(v_adrs[i], util.s32_to_data(int(round(v[i], 3) * 1000)))
                    # v_val = int(util.data_to_s32(self.inv.read(v_adrs[i], 2)))
                    # self.ts.log_debug('Voltage point %s is %s' % (i, v_val))
                    # self.ts.log_debug('Writing v point %s to reg %s with value %s' % (i, v_adrs[i], v[i]))

            # set var points
            var = params.get('var')
            if var is not None:
                var_len = len(var)
                for i in range(var_len):  # SunSpec point index starts at 1
                    self.inv.write(var_adrs[i], util.s32_to_data(int(round(var[i], 3)*1000)))

        else:
            self.ts.log_debug('Reading VV curve in SMA')
            params = {}
            v = []
            var = []
            if reg['NPts'][self.firmware] is not None:
                n_pt = int(util.data_to_u32(self.inv.read(reg['NPts'][self.firmware], 2)))
            else:
                n_pt = 4
            for i in range(int(n_pt)):
                self.ts.log('Getting V%s' % i)
                v.append(util.data_to_s32(self.inv.read(v_adrs[i], 2))/1000.)
                self.ts.log('Getting Q%s' % i)
                var.append(util.data_to_s32(self.inv.read(var_adrs[i], 2))/1000.)

            params['DeptRef'] = volt_var_dept_ref.get(1)  # 'W_MAX_PCT'
            params['id'] = id  # also store the curve number
            params['v'] = v
            params['var'] = var

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
            curve - dict of curve parameters:
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
        :return: Dictionary of active settings for freq/watt control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        # 2269 = Reactive power charact. curve  --- Use the curve to create FW curve
        q_mode_ena = {'02.02.30.R': 40200, '02.84.01.R': 40200, '02.83.03.R': 40200, '02.63.33.S': 40200}
        q_mode_ena_val = {'02.02.30.R': 1069, '02.84.01.R': 2269, '02.83.03.R': 2269, '02.63.33.S': 1069}

        # Curve 1 = Characteristic curve number, configuration of characteristic curve mode [1]
        nonactive_crv_activation = {'02.02.30.R': 40937, '02.84.01.R': 40937, '02.83.03.R': 40937, '02.63.33.S': 40937}
        active_crv_activation = {'02.02.30.R': 40937, '02.84.01.R': 41063, '02.83.03.R': 40937, '02.63.33.S': 40937}
        fw_ena_curve_val = {'02.02.30.R': 308, '02.84.01.R': 308, '02.83.03.R': 308, '02.63.33.S': 308}
        # 2nd characteristic curve number, configuration of characteristic curve mode
        # This maps the characteristic curve points to the characteristic behavior
        fw_curve_num = {'02.02.30.R': 40937, '02.84.01.R': 41061, '02.83.03.R': 40917, '02.63.33.S': 40937}

        self.ts.log_warning('Using Curve 2 for the FW function.')
        reg = self.get_curve_registers(2)

        n_pts = reg['NPts']
        f_units_val = {'02.02.30.R': 3420, '02.84.01.R': 3420, '02.83.03.R': 3420, '02.63.33.S': 3420}
        p_units_val = {'02.02.30.R': 1978, '02.84.01.R': 1978, '02.83.03.R': 1978, '02.63.33.S': 1978}

        f_adrs = []
        p_adrs = []
        for i in range(4):  # Prepolulate 4 register values
            f_adrs.append(reg['x%d' % (i+1)][self.firmware])
            p_adrs.append(reg['y%d' % (i+1)][self.firmware])

        if params is not None:
            if params['Ena']:
                # put in characteristic curve mode
                self.inv.write(q_mode_ena[self.firmware], util.u32_to_data(q_mode_ena_val[self.firmware]))

                # enable/disable curves
                self.inv.write(nonactive_crv_activation[self.firmware], util.u32_to_data(303))
                self.inv.write(active_crv_activation[self.firmware],
                               util.u32_to_data(fw_ena_curve_val[self.firmware]))

                # set configuration characteristic to the active curve
                self.ts.log('Using Curve 2 in SMA for the FW Write')
                params['ActCrv'] = 2
                self.inv.write(fw_curve_num[self.firmware], util.u32_to_data(params['ActCrv']))

                # set curve units to %Vnom and %PMax
                self.inv.write(reg['x_units'][self.firmware], util.u32_to_data(int(f_units_val[self.firmware])))
                self.inv.write(reg['y_units'][self.firmware], util.u32_to_data(int(p_units_val[self.firmware])))
            else:
                self.inv.write(active_crv_activation[self.firmware], util.u32_to_data(303))
                self.inv.write(q_mode_ena[self.firmware], util.u32_to_data(303))
            if params.get('NPt') is not None:
                self.inv.write(n_pts[self.firmware], util.u32_to_data(params['NPt']))

            if params.get('curve') is not None:
                curve = params['curve']

                # set freq points
                f = curve.get('hz')
                if f is not None:
                    f_len = len(f)
                    for i in range(f_len):  # point name starts at 1 but index starts at 0
                        self.inv.write(f_adrs[i], util.s32_to_data(int(round(f[i], 3) * 1000)))

                # set power points
                p = curve.get('w')
                if p is not None:
                    p_len = len(p)
                    for i in range(p_len):  # point name starts at 1 but index starts at 0
                        self.inv.write(p_adrs[i], util.s32_to_data(int(round(p[i], 3) * 1000)))
                        # self.ts.log_debug('Writing Power point %s @ %s' % (int(round(p[i], 3) * 1000), p_adrs[i]))
                        # self.ts.log_debug('Writing P point %s to reg %s with value %s' % (i, p_adrs[i], p[i]))
        else:
            params = {}
            q_mode = util.data_to_u32(self.inv.read(q_mode_ena[self.firmware], 2)) == q_mode_ena_val[self.firmware]
            curve_ena = util.data_to_u32(self.inv.read(active_crv_activation[self.firmware], 2)) == \
                        fw_ena_curve_val[self.firmware]
            if q_mode and curve_ena:
                params['Ena'] = True
            else:
                params['Ena'] = False

            params['NPt'] = util.data_to_u32(self.inv.read(n_pts[self.firmware], 2))  # number of points
            params['ActCrv'] = 2  # active curve
            params['NCrv'] = 3  # number of supported curves

            f = []
            w = []
            for i in range(params['NPt']):
                f.append(util.data_to_s32(self.inv.read(f_adrs[i], 2))/1000.)
                w.append(util.data_to_s32(self.inv.read(p_adrs[i], 2))/1000.)

            params['curve'] = {'id': 2, 'hz': f, 'w': w, 'WRef': 'WMax'}

        return params

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

        if self.inv is None:
            raise der.DERError('DER not initialized')

        self.ts.log_warning('freq_watt_param() is not programmed. Use freq_droop()')

        if params is not None:
            return params
        else:
            return self.freq_droop(params)

    def freq_droop(self, params=None):
        """ Get/set freq droop control

        Params:
            Ena - Enabled (True/False)
            dbOF - single-sided deadband value for high-frequency and low-frequency, respectively, in Hz
            dbUF - single-sided deadband value for high-frequency and low-frequency, respectively, in Hz
            kOF - per-unit frequency change corresponding to 1 per-unit power output change (frequency droop), unitless
            kUF - per-unit frequency change corresponding to 1 per-unit power output change (frequency droop), unitless
                  Note: a 5% droop per 0.1 Hz is created with a kOF,kUF = (0.1/60)/0.05 (this will change the EUT power
                  from 100% to 0% output as frequency increases to 2 Hz above nominal)

            'RspTms'

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for freq droop control.
        """
        if self.inv is None:
            raise der.DERError('DER not initialized')

        # Operating mode of active power reduction in case of overfrequency P(f):
        fdroop_ena = {'02.02.30.R': 40216, '02.84.01.R': 40216, '02.83.03.R': 40216, '02.63.33.S': 40216}
        # 303 = Off
        # 1132 = Linear gradient
        # 3175 = Linear gradient of the maximum active power
        fdroop_val = {'02.02.30.R': 1132, '02.84.01.R': 1132, '02.83.03.R': 1132, '02.63.33.S': 1132}

        # Difference between starting frequency and grid frequency, linear instantaneous power gradient configuration
        dbf1 = {'02.02.30.R': 40218, '02.84.01.R': 40218, '02.83.03.R': 40218, '02.63.33.S': 40218}
        dbf2 = {'02.02.30.R': 40220, '02.84.01.R': None, '02.83.03.R': None, '02.63.33.S': 40220}
        # Difference between reset frequency and grid frequency, linear instantaneous power gradient configuration
        dbf_return = {'02.02.30.R': 40220, '02.84.01.R': 40220, '02.83.03.R': 40220, '02.63.33.S': 40220}
        kof = {'02.02.30.R': 40234, '02.84.01.R': 40234, '02.83.03.R': 40234, '02.63.33.S': 40234}
        # Active power gradient after reset frequency, linear instantaneous power gradient configuration
        kof_return = {'02.02.30.R': 40242, '02.84.01.R': 40242, '02.83.03.R': 40242, '02.63.33.S': 40242}

        if params is not None:
            ena = params['Ena']
            if ena:
                self.inv.write(fdroop_ena[self.firmware], util.u32_to_data(int(fdroop_val[self.firmware])))  # lin grad
            else:
                self.inv.write(fdroop_ena[self.firmware], util.u32_to_data(int(303)))       # off

            if params.get('dbOF') is not None:
                dbf_set = int(round(params['dbOF'], 2)*100)
                self.inv.write(dbf1[self.firmware], util.u32_to_data(dbf_set))      # dbf
                if dbf2[self.firmware] is not None:
                    self.inv.write(dbf2[self.firmware], util.u32_to_data(dbf_set))      # dbf
                # set the return curve to be the same
                self.inv.write(dbf_return[self.firmware], util.u32_to_data(dbf_return))         # dbf

            if params.get('kOF') is not None:
                kof_set = int(1/(params['kOF']))
                self.inv.write(kof[self.firmware], util.u32_to_data(kof_set))  # dbf
                # set the return curve to be the same
                if kof_return[self.firmware] is not None:
                    self.inv.write(kof_return[self.firmware], util.u32_to_data(kof_set))      # dbf

        else:
            dbf = float(util.data_to_u32(self.inv.read(dbf1[self.firmware], 2)))/100.0
            kof = util.data_to_u32(self.inv.read(kof[self.firmware], 2))
            params = {'dbOF': dbf, 'dbUF': dbf, 'kOF': kof, 'kUF': kof}

        return params

    def frt_trip_high(self, params=None):
        """ Get/set high frequency ride through (trip curve)

        Params:  params = {'curve': 't': [299., 10.], 'Hz': [61.0, 61.8]}
            curve:
                t - Time point in the curve
                Hz - Frequency point in the curve

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HFT control.

            ^
            |           T0   Median Max
        F   |-----------+ F0
            |           |              T1  Lower Max
            |           +--------------+ F1
            |                          |
        Fnom-------------------------------> Time
            |                          |
            |                          |
            |           +--------------+ F1 Upper Min
            |           |              T1
            |-----------+ F0
            |           T0 Median Min

        """

        # Frequency monitoring median maximum threshold                                 Hz   U32       FIX2      RW
        f0 = {'02.02.30.R': 40428, '02.84.01.R': 40428, '02.83.03.R': 40428, '02.63.33.S': 40428}
        # Frq. monitoring median max. threshold trip. time                              ms   U32       FIX0      RW
        t0 = {'02.02.30.R': 40430, '02.84.01.R': 40430, '02.83.03.R': 40430, '02.63.33.S': 40430}
        # Frequency monitoring lower maximum threshold                                  Hz   U32       FIX2      RW
        f1 = {'02.02.30.R': 40432, '02.84.01.R': 40432, '02.83.03.R': 40432, '02.63.33.S': 40432}
        # Frq. monitoring lower max. threshold trip. time                               ms   U32       FIX0      RW
        t1 = {'02.02.30.R': 40434, '02.84.01.R': 40434, '02.83.03.R': 40434, '02.63.33.S': 40434}

        if params is not None:
            if params.get('curve') is not None:
                if params.get('curve').get('Hz') is not None:
                    hz = params.get('curve').get('Hz')
                    t = params.get('curve').get('t')
                    if len(hz) != 2:
                        f0_set = int(round(hz[0], 2) * 100)
                        self.inv.write(f0[self.firmware], util.u32_to_data(f0_set))  # Hz
                        f1_set = int(round(hz[0], 2) * 100)
                        self.inv.write(f1[self.firmware], util.u32_to_data(f1_set))  # Hz
                        t0_set = int(t[0]*1000.)
                        self.inv.write(t0[self.firmware], util.u32_to_data(t0_set))  # ms
                        t1_set = int(t[1]*1000.)
                        self.inv.write(t1[self.firmware], util.u32_to_data(t1_set))  # ms
                    else:
                        self.ts.log_warning('Use 2 points for FRT curves')

        else:
            f0 = float(util.data_to_u32(self.inv.read(f0[self.firmware], 2))) / 100.0
            t0 = util.data_to_u32(self.inv.read(t0[self.firmware], 2)) / 1000.
            f1 = float(util.data_to_u32(self.inv.read(f1[self.firmware], 2))) / 100.0
            t1 = util.data_to_u32(self.inv.read(t1[self.firmware], 2)) / 1000.

            params = {'curve': {'Hz': [f0, f1], 't': [t0, t1]}}

        return params

    def frt_trip_low(self, params=None):
        """ Get/set lower frequency ride through (trip curve)

        Params: params = {'curve': 't': [299., 10.], 'Hz': [59.0, 58.2]}
            curve:
                t - Time point in the curve
                Hz - Frequency point in the curve

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for LFT control.
        """

        # Frequency monitoring median minimum threshold                                 Hz   U32       FIX2      RW
        f0 = {'02.02.30.R': 40440, '02.84.01.R': 40440, '02.83.03.R': 40440, '02.63.33.S': 40440}
        # Frq. monitoring median min. threshold trip. time                              ms   U32       FIX0      RW
        t0 = {'02.02.30.R': 40442, '02.84.01.R': 40442, '02.83.03.R': 40442, '02.63.33.S': 40442}
        # Frequency monitoring upper minimum threshold                                  Hz   U32       FIX2      RW
        f1 = {'02.02.30.R': 40436, '02.84.01.R': 40436, '02.83.03.R': 40436, '02.63.33.S': 40436}
        # Frq. monitoring upper min. threshold trip. time                               ms   U32       FIX0      RW
        t1 = {'02.02.30.R': 40438, '02.84.01.R': 40438, '02.83.03.R': 40438, '02.63.33.S': 40438}

        if params is not None:
            if params.get('curve') is not None:
                if params.get('curve').get('Hz') is not None:
                    hz = params.get('curve').get('Hz')
                    t = params.get('curve').get('t')
                    if len(hz) != 2:
                        f0_set = int(round(hz[0], 2) * 100)
                        self.inv.write(f0[self.firmware], util.u32_to_data(f0_set))  # Hz
                        f1_set = int(round(hz[0], 2) * 100)
                        self.inv.write(f1[self.firmware], util.u32_to_data(f1_set))  # Hz
                        t0_set = int(t[0] * 1000.)
                        self.inv.write(t0[self.firmware], util.u32_to_data(t0_set))  # ms
                        t1_set = int(t[1] * 1000.)
                        self.inv.write(t1[self.firmware], util.u32_to_data(t1_set))  # ms
                    else:
                        self.ts.log_warning('Use 2 points for FRT curves')

        else:
            f0 = float(util.data_to_u32(self.inv.read(f0[self.firmware], 2))) / 100.0
            t0 = util.data_to_u32(self.inv.read(t0[self.firmware], 2)) / 1000.
            f1 = float(util.data_to_u32(self.inv.read(f1[self.firmware], 2))) / 100.0
            t1 = util.data_to_u32(self.inv.read(t1[self.firmware], 2)) / 1000.

            params = {'curve': {'Hz': [f0, f1], 't': [t0, t1]}}

        return params

    def vrt_trip_high(self, params=None):
        """ Get/set high voltage ride through (trip curve)

        Params:  params = {'curve': 't': [60., 10.], 'V': [110.0, 120.0]}
            curve:
                t - Time point in the curve
                V - Voltage point in the curve % of Vnom

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for HVT control.

            ^       T0  Upper Max
            |-------+ V0
            |       |          T1   Median Max
        V   |       +----------+ V1
            |                  |              T2  Lower Max
            |                  +--------------+ V2
            |                                 |
        Vnom-------------------------------> Time
            |                                 |
            |                                 |
            |                  +--------------+ V2 Upper Min
            |                  |              T2
            |      +-----------+ V1
            |      |           T1 Median Min
            |------+ V0
            |      T0 Lower Min
        """

        # Voltage monitoring of upper maximum threshold as RMS value                     V   U32       FIX2      RW
        v0 = {'02.02.30.R': 41115, '02.84.01.R': 41115, '02.83.03.R': 41115, '02.63.33.S': 41115}
        # Voltage monitoring of upper max. thresh. as RMS value for tripping time       ms   U32       FIX0      RW
        t0 = {'02.02.30.R': 41117, '02.84.01.R': 41117, '02.83.03.R': 41117, '02.63.33.S': 41117}
        # Voltage monitoring upper max. threshold trip. time                            ms   U32       FIX3      RW
        # t0 = {'02.02.30.R': 40446, '02.84.01.R': 40446, '02.83.03.R': 40446, '02.63.33.S': 40446}

        # Voltage monitoring median maximum threshold                                    V   U32       FIX2      RW
        v1 = {'02.02.30.R': 40448, '02.84.01.R': 40448, '02.83.03.R': 40448, '02.63.33.S': 40448}
        # Voltage monitoring median max. threshold trip.time                            ms   U32       FIX0      RW
        t1 = {'02.02.30.R': 40450, '02.84.01.R': 40450, '02.83.03.R': 40450, '02.63.33.S': 40450}

        # Voltage monitoring lower maximum threshold                                     V   U32       FIX2      RW
        v2 = {'02.02.30.R': 40452, '02.84.01.R': 40452, '02.83.03.R': 40452, '02.63.33.S': 40452}
        # Voltage monitoring lower max. threshold trip. time                            ms   U32       FIX0      RW
        t2 = {'02.02.30.R': 40456, '02.84.01.R': 40456, '02.83.03.R': 40456, '02.63.33.S': 40456}

        if params is not None:
            if params.get('curve') is not None:
                if params.get('curve').get('V') is not None:
                    v = params.get('curve').get('V')
                    t = params.get('curve').get('t')
                    if len(v) != 3:
                        v0_set = int(round(v[0], 2) * 100)
                        self.inv.write(v0[self.firmware], util.u32_to_data(v0_set))  # V
                        v1_set = int(round(v[1], 2) * 100)
                        self.inv.write(v1[self.firmware], util.u32_to_data(v1_set))  # V
                        v2_set = int(round(v[2], 2) * 100)
                        self.inv.write(v1[self.firmware], util.u32_to_data(v2_set))  # V
                        t0_set = int(t[0] * 1000.)
                        self.inv.write(t0[self.firmware], util.u32_to_data(t0_set))  # ms
                        t1_set = int(t[1] * 1000.)
                        self.inv.write(t1[self.firmware], util.u32_to_data(t1_set))  # ms
                        t2_set = int(t[2] * 1000.)
                        self.inv.write(t2[self.firmware], util.u32_to_data(t2_set))  # ms
                    else:
                        self.ts.log_warning('Use 3 points for FRT curves')

        else:
            v0 = float(util.data_to_u32(self.inv.read(v0[self.firmware], 2))) / 100.0
            t0 = util.data_to_u32(self.inv.read(t0[self.firmware], 2)) / 1000.
            v1 = float(util.data_to_u32(self.inv.read(v1[self.firmware], 2))) / 100.0
            t1 = util.data_to_u32(self.inv.read(t1[self.firmware], 2)) / 1000.
            v2 = float(util.data_to_u32(self.inv.read(v2[self.firmware], 2))) / 100.0
            t2 = util.data_to_u32(self.inv.read(t2[self.firmware], 2)) / 1000.
            params = {'curve': {'V': [v0, v1, v2], 't': [t0, t1, t2]}}

        return params

    def vrt_trip_low(self, params=None):
        """ Get/set lower voltage ride through (trip curve)

        Params:  params = {'curve': 't': [60., 10.], 'V': [110.0, 120.0]}
            curve:
                t - Time point in the curve
                V - Voltage point in the curve % of Vnom

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for LVT control.
        """

        # Voltage monitoring of lower minimum threshold as RMS value                     V   U32       FIX2      RW
        v0 = {'02.02.30.R': 41111, '02.84.01.R': 41111, '02.83.03.R': 41111, '02.63.33.S': 41111}
        # Voltage monitoring of lower min.threshold as RMS value for tripping time      ms   U32       FIX0      RW
        t0 = {'02.02.30.R': 41113, '02.84.01.R': 41113, '02.83.03.R': 41113, '02.63.33.S': 41113}

        # Voltage monitoring of median minimum threshold                                 V   U32       FIX2      RW
        v1 = {'02.02.30.R': 40464, '02.84.01.R': 40464, '02.83.03.R': 40464, '02.63.33.S': 40464}
        # Voltage monitoring median min. threshold trip.time                            ms   U32       FIX0      RW
        t1 = {'02.02.30.R': 40466, '02.84.01.R': 40466, '02.83.03.R': 40466, '02.63.33.S': 40466}

        # Voltage monitoring upper minimum threshold                                     V   U32       FIX2      RW
        v2 = {'02.02.30.R': 40458, '02.84.01.R': 40458, '02.83.03.R': 40458, '02.63.33.S': 40458}
        # Voltage monitoring upper min. threshold trip. time                            ms   U32       FIX0      RW
        t2 = {'02.02.30.R': 40462, '02.84.01.R': 40462, '02.83.03.R': 40462, '02.63.33.S': 40462}

        if params is not None:
            if params.get('curve') is not None:
                if params.get('curve').get('V') is not None:
                    v = params.get('curve').get('V')
                    t = params.get('curve').get('t')
                    if len(v) != 3:
                        v0_set = int(round(v[0], 2) * 100)
                        self.inv.write(v0[self.firmware], util.u32_to_data(v0_set))  # V
                        v1_set = int(round(v[1], 2) * 100)
                        self.inv.write(v1[self.firmware], util.u32_to_data(v1_set))  # V
                        v2_set = int(round(v[2], 2) * 100)
                        self.inv.write(v1[self.firmware], util.u32_to_data(v2_set))  # V
                        t0_set = int(t[0] * 1000.)
                        self.inv.write(t0[self.firmware], util.u32_to_data(t0_set))  # ms
                        t1_set = int(t[1] * 1000.)
                        self.inv.write(t1[self.firmware], util.u32_to_data(t1_set))  # ms
                        t2_set = int(t[2] * 1000.)
                        self.inv.write(t2[self.firmware], util.u32_to_data(t2_set))  # ms
                    else:
                        self.ts.log_warning('Use 3 points for FRT curves')

        else:
            v0 = float(util.data_to_u32(self.inv.read(v0[self.firmware], 2))) / 100.0
            t0 = util.data_to_u32(self.inv.read(t0[self.firmware], 2)) / 1000.
            v1 = float(util.data_to_u32(self.inv.read(v1[self.firmware], 2))) / 100.0
            t1 = util.data_to_u32(self.inv.read(t1[self.firmware], 2)) / 1000.
            v2 = float(util.data_to_u32(self.inv.read(v2[self.firmware], 2))) / 100.0
            t2 = util.data_to_u32(self.inv.read(t2[self.firmware], 2)) / 1000.
            params = {'curve': {'V': [v0, v1, v2], 't': [t0, t1, t2]}}

        return params

    def reactive_power(self, params=None):
        """ Set the reactive power

        Params:
            Ena - Enabled (True/False)
            VArPct_Mod - Reactive power mode
                    'None' : 0,
                    'WMax': 1,
                    'VArMax': 2,
                    'VArAval': 3,
            VArWMaxPct - Reactive power in percent of WMax.
            VArMaxPct - Reactive power in percent of VArMax.
            VArAvalPct - Reactive power in percent of VArAval.

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for Q control.
        """

        reactive_power_dept_ref = {
            'None': 0,
            'WMax': 1,
            'VArMax': 2,
            'VArAval': 3,
            0: 'None',
            1: 'WMax',
            2: 'VArMax',
            3: 'VArAval'
        }

        if self.inv is None:
            raise der.DERError('DER not initialized')

        # 1070 - Reactive power Q, direct spec.
        q_mode_ena = {'02.02.30.R': 40200, '02.84.01.R': 40200, '02.83.03.R': 40200, '02.63.33.S': 40200}
        q_mode_ena_val = {'02.02.30.R': 1070, '02.84.01.R': 1070, '02.83.03.R': 1070, '02.63.33.S': 1070}

        # 40204 - Reactive power set value as a %	      %	  S32     FIX1    RW
        var_wmax_pct_reg = {'02.02.30.R': 40204, '02.84.01.R': 40204, '02.83.03.R': 40204, '02.63.33.S': 40204}
        # var_wmax_pct_reg = {'02.02.30.R': 40015, '02.84.01.R': 40015, '02.83.03.R': 40015, '02.63.33.S': 40015}
        # var_varmax_pct_reg = {'02.02.30.R': 40204, '02.84.01.R': 40204, '02.83.03.R': 40204, '02.63.33.S': 40204}
        # var_varaval_pct_reg = {'02.02.30.R': 40204, '02.84.01.R': 40204, '02.83.03.R': 40204, '02.63.33.S': 40204}

        if params is not None:
            ena = params.get('Ena')
            if ena is not None:
                if ena is True:
                    self.inv.write(q_mode_ena[self.firmware], util.u32_to_data(q_mode_ena_val[self.firmware]))
                else:
                    self.inv.write(q_mode_ena[self.firmware], util.u32_to_data(303))

            var_pct_mod = params.get('VArPct_Mod')
            if isinstance(reactive_power_dept_ref, int):
                var_pct_mod = reactive_power_dept_ref.get(reactive_power_dept_ref)  # use the string format
            if var_pct_mod != 'WMax':
                var_pct_mod = 'WMAX'
                self.ts.log_warning('Using WMAX for reactive_power VArPct_Mod because '
                                    'this is the only supported mode for SMA EUTs.')

            if var_pct_mod == 'WMAX':
                q_target = params.get('VArWMaxPct')
                if q_target is not None:
                    self.inv.write(var_wmax_pct_reg[self.firmware], util.s32_to_data(int(q_target*10.)))
            else:
                self.ts.log_warning('Unsupported reactive power mode. VArPct_Mod = %s' % var_pct_mod)

        else:
            params = {}
            if util.data_to_u32(self.inv.read(q_mode_ena[self.firmware], 2)) == q_mode_ena_val[self.firmware]:
                params['Ena'] = False
            else:
                params['Ena'] = True

            params['VArPct_Mod'] = reactive_power_dept_ref.get('WMax')  # return the integer
            params['VArWMaxPct'] = util.data_to_s32(self.inv.read(var_wmax_pct_reg[self.firmware], 2)) / 10.
            params['VArMaxPct'] = None
            params['VArAvalPct'] = None

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

        p_mode_ena = {'02.02.30.R': 40210, '02.84.01.R': 40210, '02.83.03.R': 40210, '02.63.33.S': 40210}
        # 303 = Off
        # 1077 = Active power limitation P in W
        # 1078 = Act. power lim. as % of Pmax
        # 1079 = Act. power lim. via PV system ctrl
        p_mode_val = {'02.02.30.R': 1078, '02.84.01.R': 1078, '02.83.03.R': 1078, '02.63.33.S': 1078}

        p_in_watts = {'02.02.30.R': 40212, '02.84.01.R': 40212, '02.83.03.R': 40212, '02.63.33.S': 40212}
        p_in_pct = {'02.02.30.R': 40214, '02.84.01.R': 40214, '02.83.03.R': 40214, '02.63.33.S': 40214}

        # map to limit_max_power() parameters
        lim_p_params = {'Ena': params['Ena'], 'WMaxPct': params['P'], 'WinTms': params['WinTms'],
                        'RmpTms': params['RmpTms'], 'RvrtTms': params['RvrtTms']}
        returned_params = self.limit_max_power(lim_p_params)
        params = {'Ena': returned_params['Ena'], 'P': returned_params['WMaxPct'],
                  'WinTms': returned_params['WinTms'], 'RmpTms': returned_params['RmpTms'],
                  'RvrtTms': returned_params['RvrtTms']}

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

    def debug_read_curves(self):
        """
        Curves for SMA PKG 2.84

        :return: None
        """
        self.ts.log('----------------')
        self.ts.log('Characteristic curve number, configuration of characteristic curve mode [1]: %s' %
                    util.data_to_u32(self.inv.read(40917, 2)))
        self.ts.log('Activation of the characteristic curve, configuration of characteristic curve mode: [1]: %s' %
                    util.data_to_u32(self.inv.read(40937, 2)))
        self.ts.log('Adjustment time of characteristic operating point, conf. of grid integr. char. 1: %s' %
                    util.data_to_u32(self.inv.read(41017, 2)))
        self.ts.log('Decrease ramp, conf. of grid integr. char. 1: %s' % util.data_to_u32(self.inv.read(41019, 2)))
        self.ts.log('Increase ramp, conf. of grid integr. char. 1: %s' % util.data_to_u32(self.inv.read(41021, 2)))
        self.ts.log('Number of points to be used, conf. of grid integr. char. 1: %s' %
                    util.data_to_u32(self.inv.read(41023, 2)))
        self.ts.log('X-axes reference, conf. of grid integration char. 1: %s' %
                    util.data_to_u32(self.inv.read(41025, 2)))
        self.ts.log('Y-axes reference, conf. of grid integration char. 1: %s' %
                    util.data_to_u32(self.inv.read(41027, 2)))
        self.ts.log('X value 1, conf. of grid integr. char. 1: %s' % util.data_to_s32(self.inv.read(41029, 2)))
        self.ts.log('Y value 1, conf. of grid integr. char. 1: %s' % util.data_to_s32(self.inv.read(41031, 2)))
        self.ts.log('X value 2, conf. of grid integr. char. 1: %s' % util.data_to_s32(self.inv.read(41033, 2)))
        self.ts.log('Y value 2, conf. of grid integr. char. 1: %s' % util.data_to_s32(self.inv.read(41035, 2)))
        self.ts.log('X value 3, conf. of grid integr. char. 1: %s' % util.data_to_s32(self.inv.read(41037, 2)))
        self.ts.log('Y value 3, conf. of grid integr. char. 1: %s' % util.data_to_s32(self.inv.read(41039, 2)))
        self.ts.log('X value 4, conf. of grid integr. char. 1: %s' % util.data_to_s32(self.inv.read(41041, 2)))
        self.ts.log('Y value 4, conf. of grid integr. char. 1: %s' % util.data_to_s32(self.inv.read(41043, 2)))
        self.ts.log('----------------')
        self.ts.log('2nd characteristic curve number, configuration of characteristic curve mode: %s' %
                    util.data_to_u32(self.inv.read(41061, 2)))
        self.ts.log('2nd activation of the characteristic curve, configuration of characteristic curve mode: %s' %
                    util.data_to_u32(self.inv.read(41063, 2)))
        self.ts.log('Adjustment time of char. operating point, conf. of grid integration char. 2: %s' %
                    util.data_to_u32(self.inv.read(41065, 2)))
        self.ts.log('Decrease ramp, conf. of grid integr. char. 2: %s' % util.data_to_u32(self.inv.read(41067, 2)))
        self.ts.log('Increase ramp, conf. of grid integr. char. 2: %s' % util.data_to_u32(self.inv.read(41069, 2)))
        self.ts.log('Number of points to be used, conf. of grid integr. char. 2: %s' %
                    util.data_to_u32(self.inv.read(41071, 2)))
        self.ts.log('X-axes reference, conf. of grid integration char. 2: %s' %
                    util.data_to_u32(self.inv.read(41073, 2)))
        self.ts.log('Y-axes reference, conf. of grid integration char. 2: %s' %
                    util.data_to_u32(self.inv.read(41075, 2)))
        self.ts.log('X value 1, conf. of grid integr. char. 2: %s' % util.data_to_s32(self.inv.read(41077, 2)))
        self.ts.log('Y value 1, conf. of grid integr. char. 2: %s' % util.data_to_s32(self.inv.read(41079, 2)))
        self.ts.log('X value 2, conf. of grid integr. char. 2: %s' % util.data_to_s32(self.inv.read(41081, 2)))
        self.ts.log('Y value 2, conf. of grid integr. char. 2: %s' % util.data_to_s32(self.inv.read(41083, 2)))
        self.ts.log('X value 3, conf. of grid integr. char. 2: %s' % util.data_to_s32(self.inv.read(41085, 2)))
        self.ts.log('Y value 3, conf. of grid integr. char. 2: %s' % util.data_to_s32(self.inv.read(41087, 2)))
        self.ts.log('X value 4, conf. of grid integr. char. 2: %s' % util.data_to_s32(self.inv.read(41089, 2)))
        self.ts.log('Y value 4, conf. of grid integr. char. 2: %s' % util.data_to_s32(self.inv.read(41091, 2)))
        self.ts.log('----------------')

    def ui(self, params=None):
        """
        Unintentional islanding configuration

        :param params:
        :return:
        """
        return None

    def country_code(self, params=None):
        """

        :param params:
            ui_set - bool to turn on/off anti-islanding

        :return: params dictionary
        """
        set_country_code = {'02.02.30.R': 41121, '02.84.01.R': 41121, '02.83.03.R': 41121, '02.63.33.S': 41121}
        # Set country standard:  U32	FUNKTION_SEC	RW
        # 306 = Island mode 60 Hz
        # 1013 = Other standard
        # 7519 = UL1741/2010/277

        country_code = {'02.02.30.R': 40109, '02.84.01.R': 40109, '02.83.03.R': 40109, '02.63.33.S': 40109}
        # Country standard set:  U32	ENUM	RO
        # 27 = Special setting
        # 306 = Island mode 60 Hz
        # 1013 = Other standard
        # 7519 = UL1741/2010/277
        # 16777213 = Information not available

        plant_conn = {'02.02.30.R': 30881, '02.84.01.R': 30881, '02.83.03.R': 30881, '02.63.33.S': 30881}
        # "Plant mains connection:  U32	ENUM	RO
        # 1779 = Separated
        # 1780 = Public electricity mains
        # 1781 = Island mains"

        if params is not None:
            ena = params.get('Ena')
            if ena is not None:
                if ena is True:
                    self.inv.write(set_country_code[self.firmware], util.u32_to_data(27))
                else:
                    self.inv.write(set_country_code[self.firmware], util.u32_to_data(306))

        else:
            params = {}

            set_cc = util.data_to_u32(self.inv.read(set_country_code[self.firmware], 2))
            if set_cc == 306:
                params['Country Code'] = 'Island mode 60 Hz'
            elif set_cc == 1013:
                params['Country Code'] = 'Other standard'
            elif set_cc == 7519:
                params['Country Code'] = 'UL1741/2010/277'
            else:
                params['Country Code'] = str(set_cc)

            cc = util.data_to_u32(self.inv.read(country_code[self.firmware], 2))
            if cc == 27:
                params['Country Code Read'] = 'Special setting'
            elif cc == 306:
                params['Country Code Read'] = 'Island mode 60 Hz'
            elif cc == 1013:
                params['Country Code Read'] = 'Other standard'
            elif cc == 7519:
                params['Country Code Read'] = 'UL1741/2010/277'
            elif cc == 16777213:
                params['Country Code Read'] = 'Information not available'
            else:
                params['Country Code Read'] = str(cc)

            plant_conn = util.data_to_u32(self.inv.read(plant_conn[self.firmware], 2))
            if plant_conn == 1779:
                params['Plant Conn'] = 'Separated'
            elif plant_conn == 1780:
                params['Plant Conn'] = 'Public electricity mains'
            elif plant_conn == 1781:
                params['Plant Conn'] = 'Island mains'
            else:
                params['Plant Conn'] = str(plant_conn)

            if params['Country Code'] == 'Island mode 60 Hz':  # Island mode
                params['ui_mode_enable_as'] = False
            else:
                params['ui_mode_enable_as'] = True

        return params


if __name__ == "__main__":
    pass


'''
SMA Data Formats
-----------------------------------------------------------------------------------------------------------------------
Format       Explanation
Duration     Time in seconds, in minutes or in hours, depending on the Modbus register.
DT           Date/time, in accordance with country setting. Transmission in seconds since 1970-01-01.
ENUM         Coded numerical values. The breakdown of the possible codes can be found directly under the designation of
             the Modbus register in the SMA Modbus profile - assignment tables.
FIX0         Decimal number, commercially rounded, no decimal place.
FIX1         Decimal number, commercially rounded, one decimal place.
FIX2         Decimal number, commercially rounded, two decimal places.
FIX3         Decimal number, commercially rounded, three decimal places.
FIX4         Decimal number, commercially rounded, four decimal places.
FW           Firmware version (see Section 3.8, "SMA Firmware Data Format (FW)", 15)
HW           Hardware version e.g. 24.
IP4          4-byte IP address (IPv4) of the form XXX.XXX.XXX.XXX.
RAW          Text or number. A RAW number has no decimal places and no thousand or other separation indicators.
TEMP         Temperature values are stored in special Modbus registers in degrees Celsius (deg C), in degrees Fahrenheit
             (dge F), or in Kelvin K. The values are commercially rounded, with one decimal place.

-----------------------------------------------------------------------------------------------------------------------
Sunny Tripower US version with "Speedwire data module"
"Sunny Tripower: STP 12000TL-US-10, STP 15000TL-US-10, STP 20000TL-US-10, STP 24000TL-US-10 and STP 30000TL-US-10"
Speedwire data module: SWDM-10
Starting with software package: 02.84.01.R
-----------------------------------------------------------------------------------------------------------------------

30051 Device class:
    8001 = Solar Inverters                                                               U32       ENUM      RO
30053 Device type:
    9194 = STP 12000TL-US-10
    9195 = STP 15000TL-US-10
    9196 = STP 20000TL-                                                                  U32       ENUM      RO
30057 Serial number                                                                      U32       RAW       RO
30059 Software package                                                                   U32       FW        RO
30197 Current event number                                                               U32       FIX0      RO
30199 Waiting time until feed-in                                                     s   U32     Duration    RO
30201 Condition:
    35 = Fault
    303 = Off
    307 = Ok
    455 = Warning                                                                        U32       ENUM      RO
30203 Nominal power in Ok Mode                                                       W   U32       FIX0      RO
30205 Nominal power in Warning Mode                                                  W   U32       FIX0      RO
30207 Nominal power in Fault Mode                                                    W   U32       FIX0      RO
30211 Recommended action:
    336 = Contact manufacturer
    337 = Contact installer
    338 = inval                                                                          U32       ENUM      RO
30213 Message:
    886 = none                                                                           U32       ENUM      RO
30215 Fault correction measure:
    885 = none                                                                           U32       ENUM      RO
30217 Grid relay/contactor:
    51 = Closed
    311 = Open
    16777213 = Information not available                                                 U32       ENUM      RO
30219 Derating:
    557 = Temperature derating
    884 = not active
    16777213 = Information not a                                                         U32       ENUM      RO
30225 Insulation resistance                                                        Ohms  U32       FIX0      RO
30231 Maximum active power device                                                    W   U32       FIX0      RO
30233 Set active power limit                                                         W   U32       FIX0      RO
30235 Backup mode status:
    1440 = Grid mode
    1441 = Separate network mode
    16777213 = Infor                                                                     U32       ENUM      RO
30247 Current event number for manufacturer                                              U32       FIX0      RO
30513 Total yield                                                                   Wh   U64       FIX0      RO
30517 Daily yield                                                                   Wh   U64       FIX0      RO
30521 Operating time                                                                 s   U64     Duration    RO
30525 Feed-in time                                                                   s   U64     Duration    RO
30529 Total yield                                                                   Wh   U32       FIX0      RO
30531 Total yield                                                                   kWh  U32       FIX0      RO
30533 Total yield                                                                   MWh  U32       FIX0      RO
30535 Daily yield                                                                   Wh   U32       FIX0      RO
30537 Daily yield                                                                   kWh  U32       FIX0      RO
30539 Daily yield                                                                   MWh  U32       FIX0      RO
30541 Operating time                                                                 s   U32     Duration    RO
30543 Feed-in time                                                                   s   U32     Duration    RO
30559 Number of events for user                                                          U32       FIX0      RO
30561 Number of events for installer                                                     U32       FIX0      RO
30563 Number of events for service                                                       U32       FIX0      RO
30583 Grid feed-in counter reading                                                  Wh   U32       FIX0      RO
30599 Number of grid connections                                                         U32       FIX0      RO
30769 DC current input [1]                                                           A   S32       FIX3      RO
30771 DC voltage input [1]                                                           V   S32       FIX2      RO
30773 DC power input [1]                                                             W   S32       FIX0      RO
30775 Power                                                                          W   S32       FIX0      RO
30777 Power L1                                                                       W   S32       FIX0      RO
30779 Power L2                                                                       W   S32       FIX0      RO
30781 Power L3                                                                       W   S32       FIX0      RO
30783 Grid voltage phase L1                                                          V   U32       FIX2      RO
30785 Grid voltage phase L2                                                          V   U32       FIX2      RO
30787 Grid voltage phase L3                                                          V   U32       FIX2      RO
30795 Grid current                                                                   A   U32       FIX3      RO
30803 Grid frequency                                                                Hz   U32       FIX2      RO
30805 Reactive power                                                                VAr  S32       FIX0      RO
30807 Reactive power L1                                                             VAr  S32       FIX0      RO
30809 Reactive power L2                                                             VAr  S32       FIX0      RO
30811 Reactive power L3                                                             VAr  S32       FIX0      RO
30813 Apparent power                                                                VA   S32       FIX0      RO
30815 Apparent power L1                                                             VA   S32       FIX0      RO
30817 Apparent power L2                                                             VA   S32       FIX0      RO
30819 Apparent power L3                                                             VA   S32       FIX0      RO
30825 Operating mode of stat.V stab., stat.V stab. config.:
    303 = Off
    1069 = React. power/volt. char. Q(U)
    1070 = Reactive power Q, direct spec.
    1072 = Q specified by PV system control
    1074 = cosPhi, direct specific.
    1075 = cosPhi, specified by PV system control
    1076 = cosPhi(P) characteristic
    2269 = Reactive power charact. curve
    2270 = cos Phi or Q specification through optimum PV system control"                 U32       ENUM      RO
30829 Reactive power set value as a %	                                             %	 S32       FIX1      RO
30831 cosPhi setpoint, cosPhi config., direct specif.                                    S32       FIX2      RO
30833 cosPhi excit.type, cosPhi config., direct spec.:
    1041 = Overexcited
    1042 = Underexcited                                                                  U32       ENUM      RO
30835 Operating mode of feed-in management:
    303 = Off
    1077 = Active power limitation P in W
    1078 = Act. power lim. as % of Pmax
    1079 = Act. power lim. via PV system ctrl"                                           U32       ENUM      RO
30837 Active power limitation P, active power configuration                          W   U32       FIX0      RO
30839 Active power limitation P, active power configuration                          %   U32       FIX0      RO
30881 Plant mains connection:
    1779 = Separated
    1780 = Public electricity mains
    1781 = Is                                                                            U32       ENUM      RO
30919 Oper.mode vol.maint.at Q on Dem., st.vol.maint.conf.:
    303 = Off
    2476 = As static v                                                                   U32       ENUM      RO
30925 Connection speed of SMACOM A:
    302 = -------
    1720 = 10 Mbit/s
    1721 = 100 Mbit/s                                                                    U32       ENUM      RO
30927 Duplex mode of SMACOM A:
    302 = -------
    1726 = Half duplex
    1727 = Full duplex                                                                   U32       ENUM      RO
30929 Speedwire connection status of SMACOM A:
    35 = Fault
    307 = Ok
    455 = Warning
    1725 =                                                                               U32       ENUM      RO
30931 Connection speed of SMACOM B:
    302 = -------
    1720 = 10 Mbit/s
    1721 = 100 Mbit/s                                                                    U32       ENUM      RO
30933 Duplex mode of SMACOM B:
    302 = -------
    1726 = Half duplex
    1727 = Full duplex                                                                   U32       ENUM      RO
30935 Speedwire connection status of SMACOM B:
    35 = Fault
    307 = Ok
    455 = Warning
    1725 =                                                                               U32       ENUM      RO
30949 Displacement power factor                                                          U32       FIX3      RO
30953 Internal temperature                                                           C   S32       TEMP      RO
30957 DC current input [2]                                                           A   S32       FIX3      RO
30959 DC voltage input [2]                                                           V   S32       FIX2      RO
30961 DC power input [2]                                                             W   S32       FIX0      RO
30975 Intermediate circuit voltage                                                   V   S32       FIX2      RO
30977 Grid current phase L1                                                          A   S32       FIX3      RO
30979 Grid current phase L2                                                          A   S32       FIX3      RO
30981 Grid current phase L3                                                          A   S32       FIX3      RO
31017 Current speedwire IP address                                                      STR32      UTF8      RO
31025 Current speedwire subnet mask                                                     STR32      UTF8      RO
31033 Current speedwire gateway address                                                 STR32      UTF8      RO
31041 Current speedwire DNS server address                                              STR32      UTF8      RO
31085 Nominal power in Ok Mode                                                       W   U32       FIX0      RO
31159 Current spec. reactive power Q                                                VAr  S32       FIX0      RO
31221 EEI displacement power factor                                                      S32       FIX3      RO
31247 Residual current                                                               A   S32       FIX3      RO
31405 Current spec. active power limitation P                                        W   U32       FIX0      RO
31407 Current spec. cos Phi                                                              U32       FIX4      RO
31409 Current spec. stimulation type cos Phi:
1041 = Overexcited
1042 = Underexcited
167                                                                                      U32       ENUM      RO
31411 Current spec. reactive power Q                                                VAr  S32       FIX0      RO
31793 DC current input [1]                                                           A   S32       FIX3      RO
31795 DC current input [2]                                                           A   S32       FIX3      RO
34113 Internal temperature                                                           C   S32       TEMP      RO
35377 Number of events for user                                                          U64       FIX0      RO
35381 Number of events for installer                                                     U64       FIX0      RO
35385 Number of events for service                                                       U64       FIX0      RO
40009 Operating condition:
    295 = MPP
    381 = Stop
    443 = Constant voltage                                                               U32       ENUM      RW
40013 Language of the user interface:
    777 = Deutsch
    778 = English
    779 = Italiano
    780 = E                                                                              U32       ENUM      RW
40015 Normalized reactive power limitation by PV system ctrl                         %   S16       FIX1       W
40016 Normalized active power limitation by PV system ctrl                           %   S16       FIX0       W
40018 Fast shut-down:
    381 = Stop
    1467 = Start
    1749 = Full stop                                                                     U32       ENUM       W
40022 Normalized reactive power limitation by PV system ctrl                         %   S16       FIX2       W
40023 Normalized active power limitation by PV system ctrl                           %   S16       FIX2       W
40024 Dis.pow.factor that can be changed via PV system ctrl                              U16       FIX4       W
40025 Excitation type that can be changed by PV system ctrl:
    1041 = Overexcited
    1042 = U                                                                             U32       ENUM       W
40029 Operating status:
    295 = MPP
    1467 = Start
    381 = Stop
    2119 = Derating
    1469 = Shut do                                                                       U32       ENUM      RO
40063 Firmware version of the main processor                                             U32        FW       RO
40065 Firmware version of the logic component                                            U32        FW       RO
40067 Serial number                                                                      U32        RAW      RO
40095 Voltage monitoring upper maximum threshold                                     V   U32       FIX2      RW
40109 Country standard set:
    27 = Special setting
    306 = Island mode 60 Hz
    1013 = Other st                                                                      U32       ENUM      RO
40133 Grid nominal voltage                                                           V   U32       FIX0      RW
40135 Nominal frequency                                                             Hz   U32       FIX2      RW
40157 Automatic speedwire configureation switched on:
    1129 = Yes
    1130 = No                                                                            U32       ENUM      RW
40159 Speedwire IP address                                                              STR32       IP4      RW
40167 Speedwire subnet mask                                                             STR32       IP4      RW
40175 Speedwire gateway address                                                         STR32       IP4      RW
40185 Maximum apparent power device                                                 VA   U32       FIX0      RO
40195 Currently set apparent power limit                                            VA   U32       FIX0      RW
40200 Operating mode of stat.V stab., stat.V stab. config.:
    303 = Off
    1069 = React. powe                                                                   U32       ENUM      RW
40204 Reactive power set value as a %                                                %   S32       FIX1      RW
40206 cosPhi setpoint, cosPhi config., direct specif.                                    S32       FIX2      RW
40208 cosPhi excit.type, cosPhi config., direct spec.:
    1041 = Overexcited
    1042 = Underex                                                                       U32       ENUM      RW
40210 Operating mode of feed-in management:
    303 = Off
    1077 = Active power limitation P i                                                   U32       ENUM      RW
40212 Active power limitation P, active power configuration                          W   U32       FIX0      RW
40214 Active power limitation P, active power configuration                          %   U32       FIX0      RW
40216 Operating mode of active power reduction in case of overfrequency P(f):
303 = Off
                                                                                         U32       ENUM      RW
40218 Difference between starting frequency and grid frequency, linear instantaneou Hz   U32       FIX2      RW
40220 Difference between reset frequency and grid frequency, linear instantaneous p Hz   U32       FIX2      RW
40222 cosPhi at start point, cosPhi(P) char. config.                                     U32       FIX2      RW
40224 Excit. type at start point, cosPhi(P) char. conf.:
    1041 = Overexcited
    1042 = Under                                                                         U32       ENUM      RW
40226 cosPhi at end point, cosPhi(P) char. config.                                       U32       FIX2      RW
40228 Excit. type at end point, cosPhi(P) char. config.:
    1041 = Overexcited
    1042 = Under                                                                         U32       ENUM      RW
40230 Act. power at start point, cosPhi(P) char. config.                             %   U32       FIX0      RW
40232 Act. power at end point, cosPhi(P) char. config.                               %   U32       FIX0      RW
40234 Active power gradient                                                          %   U32       FIX0      RW
40238 Active power gradient, linear instantaneous power gradient configuration       %   U32       FIX0      RW
40240 Activation of stay-set indicator function, linear instantaneous power gradient con U32       ENUM      RW
40242 Active power gradient after reset frequency, linear instantaneous power gradi  %   U32       FIX0      RW
40244 Reactive current droop, full dynamic grid support configuration:
    1233 = SDLWindV
    1                                                                                    U32       ENUM      RW
40246 Grad.K react.curr.stat.for UV for dyn.grid support                             %   U32       FIX2      RW
40248 Grad.K reac.curr.stat.for dyn.grid support OV                                  %   U32       FIX2      RW
40250 Operating mode of dynamic grid support, dynamic grid support configuration:
    1265 =                                                                               U32       ENUM      RW
40252 Lower limit, voltage dead band, full dynamic grid support configuration        %   S32       FIX0      RW
40254 Upper limit, voltage dead band, full dynamic support configuration             %   U32       FIX0      RW
40256 PWM inverse voltage, dynamic grid support configuration                        %   U32       FIX0      RW
40258 PWM inversion delay, dynamic grid support configuration                        s   U32       FIX2      RW
40428 Frequency monitoring median maximum threshold                                 Hz   U32       FIX2      RW
40430 Frq. monitoring median max. threshold trip. time                              ms   U32       FIX0      RW
40432 Frequency monitoring lower maximum threshold                                  Hz   U32       FIX2      RW
40434 Frq. monitoring lower max. threshold trip. time                               ms   U32       FIX0      RW
40436 Frequency monitoring upper minimum threshold                                  Hz   U32       FIX2      RW
40438 Frq. monitoring upper min. threshold trip. time                               ms   U32       FIX0      RW
40440 Frequency monitoring median minimum threshold                                 Hz   U32       FIX2      RW
40442 Frq. monitoring median min. threshold trip. time                              ms   U32       FIX0      RW
40446 Voltage monitoring upper max. threshold trip. time                            ms   U32       FIX3      RW
40448 Voltage monitoring median maximum threshold                                    V   U32       FIX2      RW
40450 Voltage monitoring median max. threshold trip.time                            ms   U32       FIX0      RW
40452 Voltage monitoring lower maximum threshold                                     V   U32       FIX2      RW
40456 Voltage monitoring lower max. threshold trip. time                            ms   U32       FIX0      RW
40458 Voltage monitoring upper minimum threshold                                     V   U32       FIX2      RW
40462 Voltage monitoring upper min. threshold trip. time                            ms   U32       FIX0      RW
40464 Voltage monitoring of median minimum threshold                                 V   U32       FIX2      RW
40466 Voltage monitoring median min. threshold trip.time                            ms   U32       FIX0      RW
40472 Reference voltage, PV system control                                           V   U32       FIX0      RW
40474 Reference correction voltage, PV system control                                V   S32       FIX0      RW
40482 Reactive power gradient                                                        %   U32       FIX0      RW
40484 Activation of active power gradient:
    303 = Off
    308 = On                                                                             U32       ENUM      RW
40490 Reactive power gradient, reactive power/voltage characteristic curve configur  %   U32       FIX1      RW
40497 MAC address                                                                       STR32      UTF8      RO
40513 Speedwire DNS server address                                                      STR32       IP4      RW
40575 Operating mode of multifunction relay: [1]
    258 = Switching status grid relay
    1341                                                                                 U32       ENUM      RW
40631 Device name                                                                       STR32      UTF8      RW
40789 Communication version                                                              U32        REV      RO
40791 Timeout for communication fault indication                                     s   U32       FIX0      RW
40809 Revision status of the logic component                                             U32       FIX0      RW
40915 Set active power limit                                                         W   U32       FIX0      RW
40917 Characteristic curve number, configuration of characteristic curve mode [1]        U32       FIX0      RW
40937 Activation of the characteristic curve, configuration of characteristic curve mode U32       ENUM      RW
40997 Hysteresis voltage, dynamic grid support configuration                         %   U32       FIX0      RW
40999 Setpoint cos(phi) as per EEI convention                                            S32       FIX4       W
41001 Maximum achievable reactive power quadrant 1                                  VAr  S32       FIX0      RO
41007 Maximum achievable reactive power quadrant 4                                  VAr  S32       FIX0      RO
41009 Minimum achievable cos(phi) quadrant 1                                             S32       FIX3      RO
41015 Minimum achievable cos(phi) quadrant 4                                             S32       FIX3      RO
41017 Adjustment time of characteristic operating point, conf. of grid integr. char  s   U32       FIX1      RW
41019 Decrease ramp, conf. of grid integr. char. 1                                   %   U32       FIX1      RW
41021 Increase ramp, conf. of grid integr. char. 1                                   %   U32       FIX1      RW
41023 Number of points to be used, conf. of grid integr. char. 1                         U32       FIX0      RW
41025 X-axes reference, conf. of grid integration char. 1:
    1975 = Voltage in V
    1976 = Vo                                                                            U32       ENUM      RW
41027 Y-axes reference, conf. of grid integration char. 1:
    1977 = Var in percentages of                                                         U32       ENUM      RW
41029 X value 1, conf. of grid integr. char. 1                                           S32       FIX3      RW
41031 Y value 1, conf. of grid integr. char. 1                                           S32       FIX3      RW
41033 X value 2, conf. of grid integr. char. 1                                           S32       FIX3      RW
41035 Y value 2, conf. of grid integr. char. 1                                           S32       FIX3      RW
41037 X value 3, conf. of grid integr. char. 1                                           S32       FIX3      RW
41039 Y value 3, conf. of grid integr. char. 1                                           S32       FIX3      RW
41041 X value 4, conf. of grid integr. char. 1                                           S32       FIX3      RW
41043 Y value 4, conf. of grid integr. char. 1                                           S32       FIX3      RW
41045 X value 5, conf. of grid integr. char. 1                                           S32       FIX3      RW
41047 Y value 5, conf. of grid integr. char. 1                                           S32       FIX3      RW
41049 X value 6, conf. of grid integr. char. 1                                           S32       FIX3      RW
41051 Y value 6, conf. of grid integr. char. 1                                           S32       FIX3      RW
41053 X value 7, conf. of grid integr. char. 1                                           S32       FIX3      RW
41055 Y value 7, conf. of grid integr. char. 1                                           S32       FIX3      RW
41057 X value 8, conf. of grid integr. char. 1                                           S32       FIX3      RW
41059 Y value 8, conf. of grid integr. char. 1                                           S32       FIX3      RW
41061 2nd characteristic curve number, configuration of characteristic curve mode        U32       FIX0      RW
41063 2nd activation of the characteristic curve, configuration of characteristic curve  U32       ENUM      RW
41065 Adjustment time of char. operating point, conf. of grid integration char. 2    s   U32       FIX1      RW
41067 Decrease ramp, conf. of grid integration char. 2                               %   U32       FIX1      RW
41069 Increase ramp, conf. of grid integration char. 2                               %   U32       FIX1      RW
41071 Number of points to be used, conf. of grid integr. char. 2                         U32       FIX0      RW
41073 Input unit, conf. of grid integration char. 2:
    1975 = Voltage in V
    1976 = Voltage                                                                       U32       ENUM      RW
41075 Output frequency, conf. of grid integration char. 2:
    1977 = Var in percentages of                                                         U32       ENUM      RW
41077 X value 1, conf. of grid integr. char. 2                                           S32       FIX3      RW
41079 Y value 1, conf. of grid integr. char. 2                                           S32       FIX3      RW
41081 X value 2, conf. of grid integr. char. 2                                           S32       FIX3      RW
41083 Y value 2, conf. of grid integr. char. 2                                           S32       FIX3      RW
41085 X value 3, conf. of grid integr. char. 2                                           S32       FIX3      RW
41087 Y value 3, conf. of grid integr. char. 2                                           S32       FIX3      RW
41089 X value 4, conf. of grid integr. char. 2                                           S32       FIX3      RW
41091 Y value 4, conf. of grid integr. char. 2                                           S32       FIX3      RW
41093 X value 5, conf. of grid integr. char. 2                                           S32       FIX3      RW
41095 Y value 5, conf. of grid integr. char. 2                                           S32       FIX3      RW
41097 X value 6, conf. of grid integr. char. 2                                           S32       FIX3      RW
41099 Y value 6, conf. of grid integr. char. 2                                           S32       FIX3      RW
41101 X value 7, conf. of grid integr. char. 2                                           S32       FIX3      RW
41103 Y value 7, conf. of grid integr. char. 2                                           S32       FIX3      RW
41105 X value 8, conf. of grid integr. char. 2                                           S32       FIX3      RW
41107 Y value 8, conf. of grid integr. char. 2                                           S32       FIX3      RW
41111 Voltage monitoring of lower minimum threshold as RMS value                     V   U32       FIX2      RW
41113 Voltage monitoring of lower min.threshold as RMS value for tripping time      ms   U32       FIX0      RW
41115 Voltage monitoring of upper maximum threshold as RMS value                     V   U32       FIX2      RW
41117 Voltage monitoring of upper max. thresh. as RMS value for tripping time       ms   U32       FIX0      RW
41121 Set country standard:                                                     
    306 = Island mode 60 Hz
    1013 = Other standard
    7519 = UL1741/2010/277                                                               U32   FUNKTION_SEC  RW
41123 Min. voltage for reconnection                                                  V   U32       FIX2      RW
41125 Max. voltage for reconnection                                                  V   U32       FIX2      RW
41127 Lower frequency for reconnection                                              Hz   U32       FIX2      RW
41129 Upper frequency for reconnection                                              Hz   U32       FIX2      RW
41131 Minimum voltage input [1]                                                      V   U32       FIX2      RW
41133 Minimum voltage input [2]                                                      V   U32       FIX2      RW
41155 Start delay input [1]                                                          s   U32       FIX0      RW
41157 Start delay input [2]                                                          s   U32       FIX0      RW
41169 Minimum insulation resistance                                                Ohms  U32       FIX0      RW
41171 Set total yield                                                               kWh  U32       FIX0      RW
41173 Set total operating time at grid connection point                              h   U32     Duration    RW
41193 Operating mode for absent active power limitation:
    2506 = Values maintained
    2507 =                                                                               U32       ENUM      RW
41195 Timeout for absent active power limitation                                     s   U32     Duration    RW
41197 Fallback act power lmt P in % of WMax for absent act power lmt                 %   U32       FIX2      RW
41201 Active power gradient in feeding operation                                     %   U32       FIX0      RW
41219 Operating mode for absent reactive power control:
    2506 = Values maintained
    2507 =  U32       ENUM      RW
41221 Timeout for absent reactive power control                                      s   U32     Duration    RW
41223 Fallback react power Q in % of WMax for absent react power ctr                 %   S32       FIX2      RW
41225 Operating mode for absent cos Phi spec:
    2506 = Values maintained
    2507 = Use fallba                                                                    U32       ENUM      RW
41227 Timeout for absent cos Phi spec                                                s   U32     Duration    RW
41229 Fallback cos Phi for absent cos Phi spec                                           S32       FIX4      RW
41253 Fast shut-down:
    381 = Stop
    1467 = Start
    1749 = Full stop                                                                     U32       ENUM      RW
41255 Normalized active power limitation by PV system ctrl                           %   S16       FIX2      RW
41256 Normalized reactive power limitation by PV system ctrl                         %   S16       FIX2      RW
41257 Setpoint cos(phi) as per EEI convention                                            S32       FIX4      RW
41265 AFCI switched on:
    1129 = Yes
    1130 = No                                                                            U32       ENUM      RW
43090 Login with Grid Guard-Code                                                         U32       FIX0      RW

-----------------------------------------------------------------------------------------------------------------------

'''
