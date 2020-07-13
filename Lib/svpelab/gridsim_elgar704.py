
import os
from . import grid_profiles
from . import gridsim
from . import wavegen
from . import switch
import collections

elgar_info = {'name': os.path.splitext(os.path.basename(__file__))[0],
              'mode': 'Elgar704'
}

def gridsim_info():
    return elgar_info

"""
This function set the parameter to be viewed in the sunspec SVP
"""
def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = elgar_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode, active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('phases'), label='Phases', default=1, values=[1, 2, 3])
    info.param(pname('v_nom'), label='Nominal voltage for all phases', default=120.0)
    info.param(pname('v_max'), label='Max Voltage', default=200.0)
    info.param(pname('i_max'), label='Max Current', default=10.0)
    info.param(pname('freq'), label='Frequency', default=60.0)
    info.param(pname('comm'), label='Communications Interface', default='VISA',values=['GPIB','VISA','WAVEGEN'])
    info.param(pname('gpib_device'), label='GPIB address', active=pname('comm'), active_value=['GPIB'], default='GPIB0::17::INSTR')
    info.param(pname('visa_device'), label='VISA address', active=pname('comm'),active_value=['VISA'], default='GPIB0::17::INSTR')
    wavegen.params(info, group_name=group_name, active=pname('comm'), active_value=['WAVEGEN'])
    switch.params(info, group_name=group_name, active=gname('mode'), active_value=mode)

GROUP_NAME = 'elgar'

class GridSim(gridsim.GridSim):
    """
    Elgar grid simulation implementation.

    Valid parameters:
      mode - 'Elgar'
      auto_config - ['Enabled', 'Disabled']
      v_nom
      v_max
      i_max
      freq
      profile_name
      timeout
      write_timeout
    """
    def __init__(self, ts, group_name):
        ts.log('Grid sim init')
        self.rm = None
        self.conn = None
        gridsim.GridSim.__init__(self, ts, group_name)
        self.v_nom_param = self._param_value('v_nom')
        self.v_max_param = self._param_value('v_max')
        self.i_max_param = self._param_value('i_max')
        self.freq_param = self._param_value('freq')
        self.phases = self._param_value('phases')
        self.profile_name = ts.param_value('profile.profile_name')
        self.comm = self._param_value('comm')
        self.gpib_bus_address = self._param_value('gpib_bus_address')
        self.gpib_board = self._param_value('gpib_board')
        self.visa_device = self._param_value('visa_device')
        self.cmd_str = ''
        self.cmd_str = ''
        self.wg = wavegen.wavegen_init(ts, group_name=group_name)

        #self.sw = switch.switch_init(ts, group_name=group_name)
        self._cmd = None
        self._query = None

        # open communications, not the relay  and stop profile
        self.open()

        if self.auto_config == 'Enabled':
            ts.log('Configuring the Grid Simulator.')
            self.config()

        if self.profile_name is not None and self.profile_name != 'Manual':
            self.profile_load(self.v_nom_param, self.freq_param, self.profile_name)

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def info(self):
        if self.comm == 'VISA':
            info_txt = 'Grid simulator using Elgar 704 interface'
        elif self.comm == 'WAVEGEN':
            info_txt = self.wg.info()
        return info_txt

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        self.ts.log('CanmetEnergy Grid simulator')
        self.ts.log("Grid simulator don't have REGEN mode")

        # TODO : It can be set for HIL wavegen
        # set voltage range
        self.ts.log('Grid sim can`t set voltage range')

        phases = self.phases
        # set the phase angles for the 3 phases
        self.phases_angles(phases)

        # set nominal voltage according to phase

        if phases == 1:
            volt_config = [self.v_nom_param,0.0,0.0]
            self.ts.log('Grid sim nominal voltage settings: v1 = {}'.format(volt_config[0]))
            self.voltage(voltage=volt_config)
        elif phases == 2:
            volt_config = [self.v_nom_param, self.v_nom_param, 0.0]
            self.ts.log('Grid sim nominal voltage settings: v1 = {}, v2 = {}'.format(volt_config[0],volt_config[1]))
            self.voltage(voltage=volt_config)
        elif phases == 3:
            volt_config = [self.v_nom_param, self.v_nom_param, self.v_nom_param]
            self.ts.log('Grid sim nominal voltage settings: v1 = {}, v2 = {}, v3 = {}'.format(volt_config[0],volt_config[1],volt_config[2]))
            self.voltage(voltage=volt_config)
        else:
            raise gridsim.GridSimError('Unsupported phase parameter: %s' % phases)

        # set the frequency
        self.ts.log('Frequency set to {} Hz'.format(self.freq_param))
        self.freq(self.freq_param)

        # set max current if it's not already at gridsim_Imax
        i_max = self.i_max_param
        self.ts.log('Grid sim current limit settings : {} A'.format(self.i_max_param))

        # if i1 != i_max or i2 != i_max or i3 != i_max:
        self.current_max(current=(i_max, i_max, i_max))
        # i1,i2,i3 = self.current()


        self.relay_close()

        self.ts.log('Grid sim configured')





    def open(self):
        """
        Open the communications resources associated with the grid simulator.
        """
        self.ts.log('Gridsim Open')
        try:
            if self.comm == 'GPIB':
                raise NotImplementedError('The driver for plain GPIB is not implemented yet. ' +
                                          'Please use VISA which supports also GPIB devices')
            elif self.comm == 'VISA':
                try:
                    # sys.path.append(os.path.normpath(self.visa_path))
                    import visa
                    self.rm = visa.ResourceManager()
                    self.conn = self.rm.open_resource(self.visa_device)
                    self.ts.log('Gridsim Visa config')

                except Exception as e:
                    raise gridsim.GridSimError('Cannot open VISA connection to %s\n\t%s' % (self.visa_device,str(e)))
            elif self.comm == 'WAVEGEN':
                try:
                    self.wg.open()
                except Exception as e:
                    raise gridsim.GridSimError('Cannot open Wavegen connection : \n\t%s' % (str(e)))
            else:
                raise ValueError('Unknown communication type %s. Use GPIB or VISA' % self.comm)



            self.ts.sleep(2)

        except Exception as e:
            raise gridsim.GridSimError(str(e))

    def cmd(self, cmd_str):
        try:
            self.conn.write(cmd_str)
        except Exception as e:
            raise

    def query(self, cmd_str):
        self.cmd(cmd_str)
        resp = self.conn.read()
        return resp

    def close(self):
        """
        Close any open communications resources associated with the grid
        simulator.
        """
        self.voltage(voltage=(120.0, 120.0, 120.0))
        # self.relay_open()
        #self.voltage ()
        if self.comm == 'Serial':
            self.conn.close()
        elif self.comm == 'GPIB':
            raise NotImplementedError('The driver for plain GPIB is not implemented yet.')
        elif self.comm == 'VISA':
            try:
                if self.rm is not None:
                    if self.conn is not None:
                        self.conn.close()
                    # self.rm.close()

                self.ts.sleep(1)
            except Exception as e:
                raise gridsim.GridSimError(str(e))
        elif self.comm == 'WAVEGEN':
            try:
                self.wg.close()
            except Exception as e:
                raise gridsim.GridSimError('Cannot close Wavegen connection : \n\t%s' % (str(e)))
        else:
            raise ValueError('Unknown communication type %s. Use Serial, GPIB or VISA' % self.comm)

    # ABLE command add it
    def phases_angles(self, pang =None, params=None):
        if self.comm == 'VISA':
            if pang == 1:
                self.ts.log_debug('Configuring system for single phase.')
                # phase 1 always 'preconfigured' at 0 phase angle
                self.cmd('PANGA 0')
                # self.form(1) - UNSUPPORTED
            elif pang== 2:
                # set the phase angles for split phase
                self.ts.log_debug('Configuring system for split phase on Phases A & B.')
                self.cmd('PANGB 180.0')
                # self.form(2) - UNSUPPORTED
            elif pang== 3:
                # set the phase angles for the 3 phases
                self.ts.log_debug('Configuring system for three phase.')
                self.cmd('PANGB 120.0')
                self.cmd('PANGB 240.0')
                # self.form(3)  - UNNECESSARY BECAUSE IT IS THE DEFAULT
        elif self.comm == 'WAVEGEN':
            if pang is not None:
                if pang == 1:
                    self.wg.phase(channel=1, phase=0)
                elif pang == 2:
                    self.wg.phase(channel=1, phase=0)
                    self.wg.phase(channel=2, phase=180)
                elif pang == 3:
                    self.wg.phase(channel=1, phase=0)
                    self.wg.phase(channel=2, phase=120)
                    self.wg.phase(channel=3, phase=240)
        else:
            raise gridsim.GridSimError('Unsupported phase parameter: %s' % (self.pang))


    # ABLE command add it
    def voltage(self, voltage=None):
        """
        Set the value for voltage 1, 2, 3 if provided. If none provided, obtains
        the value for voltage. Voltage is a tuple containing a voltage value for
        each phase.
        """
        if self.comm == 'VISA':
            if voltage is not None:
                if type(voltage) is not list and type(voltage) is not tuple:
                    self.cmd('VOLTS {}' % voltage[0])  # use the first value in the 3 phase list
                else:
                    self.cmd('VOLTA {}'.format(voltage[0]))
                    self.cmd('VOLTB {}'.format(voltage[1]))
                    self.cmd('VOLTC {}'.format(voltage[2]))
        elif self.comm == 'WAVEGEN':
            if voltage is not None and voltage is dict:
                for phase,magnitude in params.items():
                    self.wg.voltage(channel=phase, voltage=magnitude)
            else:
                if type(voltage) is not list and type(voltage) is not tuple:
                    self.wg.voltage(channel =1, voltage=voltage)
                    self.wg.voltage(channel =2, voltage=voltage)
                    self.wg.voltage(channel =3, voltage=voltage)
                else:
                    self.wg.voltage(channel=1, voltage=voltage[0])
                    self.wg.voltage(channel=2, voltage=voltage[1])
                    self.wg.voltage(channel=3, voltage=voltage[2])
        return voltage


    # ABLE command add it
    def voltage_max(self, voltage=None):

        if voltage is not None:
            voltage = max(voltage)  # voltage is a triplet but Elgar only takes one value
            if voltage == 130:
                self.cmd('VOLTS %0.0f' % voltage)
            else:
                raise gridsim.GridSimError('Invalid Max Voltage %s V, must be 132 V.' % str(voltage))

        return

    def current(self, current=None):
        """
        Set the value for current if provided. If none provided, obtains
        the value for current.
        """
        self.ts.log_debug('Unsupported by Elgar 704')

        return

    def current_max(self, current=None):
        """
        Set the value for max current if provided. If none provided, obtains
        the value for max voltage.
        """
        if self.comm == 'VISA':
            if current is not None:
                # set output current limit on all phases
                # self.ts.log_debug('voltage: %s, type: %s' % (voltage, type(voltage)))
                if type(current) is not list and type(current) is not tuple:
                    self.cmd('CURLA {}'.format(current[0]))
                    self.cmd('CURLB {}'.format(current[1]))
                    self.cmd('CURLC {}'.format(current[2]))
                else:
                    self.cmd('CURLS {}'.format(current[0]))  # use the first value in the 3 phase list
            return current
        if self.comm == 'WAVEGEN':
            return current

    def config_asymmetric_phase_angles(self, mag=None, angle=None):
        """
        :param mag: list of voltages for the imbalanced test, e.g., [277.2, 277.2, 277.2]
        :param angle: list of phase angles for the imbalanced test, e.g., [0, 120, -120]
        :returns: voltage list and phase list
        """
        if self.phases == 3:
            if self.comm == 'WAVEGEN':
                self.wg.config_asymmetric_phase_angles(mag=mag, angle=angle)
        else:
            raise gridsim.GridSimError('Invalid phase configuration for config_asymmetric_phase_angles() function. Should be configured as three-phase system (Phase = "%s)"', self.phases)


        return None, None
    # ABLE command add it
    def freq(self, freq=None):
        """
        Set the value for frequency if provided. If none provided, obtains
        the value for frequency.
        """
        if self.comm == 'VISA':
            if freq is not None:
                self.cmd('FREQ {}'.format(freq))
            # freq = self.query('TST FR')
            return freq
        if self.comm == 'WAVEGEN':
            self.wg.frequency(freq)

  

    def profile_load(self, profile_name, v_step=100, f_step=100, t_step=None):
        if self.comm == 'VISA':
            return profile_name
        if self.comm == 'WAVEGEN':
            return profile_name



    def profile_start(self):
        """
        Start the loaded profile.
        """
        if self.comm == 'WAVEGEN':
            self.wg.start()


    # Not implemented yet
    def profile_stop(self):
        """
        Stop the running profile.
        """
        self.cmd('abort')

    def regen(self, state=None):
        """
        Set the state of the regen mode if provided. Valid states are: REGEN_ON,
        REGEN_OFF. If none is provided, obtains the state of the regen mode.
        All this was implemented for the AMETEK not the ELGAR
        """
        self.ts.log_debug('Invalid function the grid simulator does not have regeneration capabilities')
        return state

    def relay_close(self):
        """
        Set the state of the relay if provided. Valid states are: RELAY_OPEN,
        RELAY_CLOSED. If none is provided, obtains the state of the relay.
        """
        # TODO : Add the function of the AC switch driver
        if self.comm == 'VISA':
            self.cmd('CLS')
            self.ts.log('Closed Relay')
        elif self.comm == 'WAVEGEN':
            if self.phases == 1:
                self.wg.chan_state(chans=[True, False, False])
            elif self.phases == 2:
                self.wg.chan_state(chans=[True, True, False])
            elif self.phases == 3:
                self.wg.chan_state(chans=[True, True, True])

    def relay_open(self):
        """
        Set the state of the relay if provided. Valid states are: RELAY_OPEN,
        RELAY_CLOSED. If none is provided, obtains the state of the relay.
        """
        # TODO : Add the function of the AC switch driver
        self.cmd('OPN')
        self.ts.log('Opened Relay')

    def distortion(self, state=None):
        """
        This command listed in paragraphs are used to program an 8% distortion
        """
        if state == True:
            self.cmd('DIST0')
        elif state == False:
            self.cmd('DISTO1')
        else:
            raise gridsim.GridSimError('Invalid relay state. State = "%s" . Try True or False', state)
        return state

    def aberration(self, freq=None, voltage=None, cycles=None):
        """
        This command is only for creating a voltage or frequency ride-through
        """
        if freq is not None and voltage is not None and cycles is not None:
            if freq >= 45 or freq <= 1000 or voltage >= 0 or voltage <= 200 or cycles >= 1 or cycles <= 999 :
                self.cmd('ABBRS {}, V {}, F {}'.format(cycles, voltage, freq))
            else :
                raise gridsim.GridSimError('Invalid parameters for aberration function')
        else:
            raise gridsim.GridSimError('Invalid parameters for aberration function')
        return

    def i_max(self):
        return self.i_max_param

    def v_max(self):
        return self.v_max_param

    def v_nom(self):
        return self.v1_nom_param


if __name__ == "__main__":
    pass
