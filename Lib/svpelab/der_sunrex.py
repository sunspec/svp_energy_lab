
import os
from . import der
import sunspec.core.client as client
import socket

sunrex_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Sunrex'
}

def der_info():
    return sunrex_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = sunrex_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    # TCP parameters
    info.param(pname('ipaddr'), label='IP Address', default='127.0.0.1', active=pname('ifc_type'), active_value=[client.TCP])
    info.param(pname('ipport'), label='IP Port', default=2001, active=pname('ifc_type'), active_value=[client.TCP])

GROUP_NAME = 'sunrex'


def to_uint(integer=None):
    if integer < 0:
        integer += 65536
    return int(integer)


def two_digit_hex(integer=None):
    return format((to_uint(integer)), '02X')


def four_digit_hex(integer=None):
    return format((to_uint(integer)), '04X')


def str(cmd_str=None):
    bcc = 0
    cmd_str_chars = list(cmd_str)
    for cmd_chars in cmd_str_chars:
        v_xor = ord(cmd_chars)
        bcc = bcc ^ v_xor
    return bcc


def der_init(ts, id=None):
    """
    Function to create specific der implementation instances.
    """
    group_name = 'der'
    if id is not None:
        group_name = group_name + '_' + str(id)
    print('run group_name = %s' % group_name)
    mode = ts.param_value(group_name + '.' + 'mode')
    sim_module = der_modules.get(mode)
    if sim_module is not None:
        sim = sim_module.DER(ts, group_name)
    else:
        raise der.DERError('Unknown data acquisition system mode: %s' % mode)

    return sim

class DER(der.DER):

    def __init__(self, ts, group_name):
        der.DER.__init__(self, ts, group_name)
        self.inv = None
        self.clientsock = None

    def param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):
        self.open()

    def open(self):
        ipaddr = self.param_value('ipaddr')
        ipport = self.param_value('ipport')
        try:
            self.clientsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.clientsock.connect((ipaddr, ipport))
        except Exception as e:
            raise der.DERError('Connect-Failure(Monitor),%s,%s' % (ipaddr, ipport))

    def close(self):
        if self.clientsock is not None:
            self.clientsock.close()

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
            params['Manufacturer'] = 'Sunrex'
            params['Model'] = None
            params['Options'] = None
            params['Version'] = None
            params['SerialNumber'] = None
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def send_command(self, cmd=None):
        if cmd is not None:
            try:
                self.clientsock.send(cmd_str)
            except Exception as e:
                raise der.DERError('Communication Failure with IP: %s, Port: %s, Error: %s' %
                                   (self.ipaddr, self.ipport, e))

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
            if params is not None:  # write the parameters
                cmd_str = ''

                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        pass  # command to enable
                    else:
                        pass  # command to disable

                curve = params.get('curve')
                if curve is not None:
                    # construct the FW command string
                    cmd_str = ':PCS:SABT F2 '
                    for fw in curve:
                        cmd_str += four_digit_hex(fw) + ','
                    bcc = str(cmd_str)
                    cmd_str += two_digit_hex(bcc) + '\n'

                win_tms = params.get('WinTms')
                if win_tms is not None:
                    pass  # add time window to the cmd_str

                rmp_tms = params.get('RmpTms')
                if rmp_tms is not None:
                    pass  # add ramp time to the cmd_str

                rvrt_tms = params.get('RvrtTms')
                if rvrt_tms is not None:
                    pass  # add revert time to the cmd_str

                self.ts.debug(cmd_str)
                self.send_command(cmd_str)

            else:  # read the parameters
                    params = {}
                    params['Ena'] = True
                    params['ActCrv'] = 1
                    params['NCrv'] = 1
                    params['NPt'] = 4
                    params['WinTms'] = None
                    params['RmpTms'] = None
                    params['RvrtTms'] = None
                    params['curve'] = self.freq_watt_curve(id=1)
        except Exception as e:
            raise der.DERError(str(e))

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
        return None

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
        try:
            if params is not None:

                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        pass
                    else:
                        pass

                power_set = params.get('P')

                # construct the power command string
                cmd_str = ':PCS:SABT ES '
                for p in power_set:
                    cmd_str += four_digit_hex(p) + ','
                bcc = str(cmd_str)
                cmd_str += two_digit_hex(bcc) + '\n'
                self.ts.debug(cmd_str)
                self.send_command(cmd_str)

            else:
                params = {}
                params['Ena'] = True
                params['P'] = None
                params['WinTms'] = None
                params['RmpTms'] = None
                params['RvrtTms'] = None

        except Exception as e:
            raise der.DERError(str(e))

        return params

    def reactive_power(self, params=None):
        """ Set the reactive power

        Params:
            Ena - Enabled (True/False)
            VArPct_Mod - Reactive power mode
                    # 'None' : 0,
                    # 'WMax': 1,
                    # 'VArMax': 2,
                    # 'VArAval': 3,
            VArWMaxPct - Reactive power in percent of WMax.
            VArMaxPct - Reactive power in percent of VArMax.
            VArAvalPct - Reactive power in percent of VArAval.

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for Q control.
        """
        try:
            if params is not None:

                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        pass
                    else:
                        pass

                var_pct_mod = params.get('VArPct_Mod')
                var_w_max_pct = params.get('VArWMaxPct')
                var_max_pct = params.get('VArMaxPct')
                var_aval_pct = params.get('VArAvalPct')
                if var_pct_mod is not None:
                    q_set = 0
                elif var_w_max_pct is not None:
                    q_set = var_w_max_pct
                elif var_max_pct is not None:
                    q_set = var_max_pct
                elif var_aval_pct is not None:
                    q_set = var_aval_pct
                else:
                    self.ts.log_warning('No reactive power setting provided.')
                    q_set = []

                # create reactive power command
                cmd_str = ':PCS:SABT V3 '
                for q in q_set:
                    cmd_str += four_digit_hex(q) + ','
                bcc = str(cmd_str)
                cmd_str += two_digit_hex(bcc) + '\n'

                self.ts.debug(cmd_str)
                self.send_command(cmd_str)

            else:
                params = {}
                params['Ena'] = True
                params['VArPct_Mod'] = None
                params['VArWMaxPct'] = None
                params['VArMaxPct'] = None
                params['VArAvalPct'] = None

        except Exception as e:
            raise der.DERError(str(e))

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
        if self.inv is None:
            raise der.DERError('DER not initialized')

        try:
            if params is not None:
                cmd_str = ''
                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        cmd_str = ':PCS:SABT V1 '
                    else:
                        cmd_str = ':PCS:SABT V4 '

                curve = params.get('curve')  # Must write curve first because there is a read() in volt_var_curve
                # construct the power command string
                for vv in curve:
                    cmd_str += four_digit_hex(vv) + ','
                bcc = str(cmd_str)
                cmd_str += two_digit_hex(bcc) + '\n'

                win_tms = params.get('WinTms')
                if win_tms is not None:
                    pass
                rmp_tms = params.get('RmpTms')
                if rmp_tms is not None:
                    pass
                rvrt_tms = params.get('RvrtTms')
                if rvrt_tms is not None:
                    pass

                self.ts.debug(cmd_str)
                self.send_command(cmd_str)

            else:
                params = {}
                params['Ena'] = True
                params['ActCrv'] = None
                params['NCrv'] = None
                params['NPt'] = None
                params['WinTms'] = None
                params['RmpTms'] = None
                params['RvrtTms'] = None
                params['curve'] = self.volt_var_curve(id=1)  # use 1 as default

        except Exception as e:
            raise der.DERError(str(e))

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
        :return: Dictionary of active settings for volt/var curve control.
        """
        return None


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

        try:
            if params is not None:

                ena = params.get('Ena')
                if ena is not None:
                    if ena is True:
                        pass
                    else:
                        pass

                pf = params.get('PF')
                # create reactive power command
                cmd_str = ':PCS:SABT N3 '
                cmd_str += four_digit_hex(pf) + ','
                bcc = str(cmd_str)
                cmd_str += two_digit_hex(bcc) + '\n'

                win_tms = params.get('WinTms')
                if win_tms is not None:
                    pass
                rmp_tms = params.get('RmpTms')
                if rmp_tms is not None:
                    pass
                rvrt_tms = params.get('RvrtTms')
                if rvrt_tms is not None:
                    pass

                self.ts.debug(cmd_str)
                self.send_command(cmd_str)

            else:
                params = {}
                params['Ena'] = True
                params['PF'] = None
                params['WinTms'] = None
                params['RmpTms'] = None
                params['RvrtTms'] = None
        except Exception as e:
            raise der.DERError(str(e))

        return params
