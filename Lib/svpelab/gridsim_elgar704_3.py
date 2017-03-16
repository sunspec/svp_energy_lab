
import os
import gridsim

elgar_info = {'name': os.path.splitext(os.path.basename(__file__))[0],
              'mode': 'Elgar704_3'
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
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('phases'), label='Phases', default=1, values=[1, 2, 3])
    info.param(pname('v1_nom'), label='EUT nominal voltage for phase A', default=120.0)
    info.param(pname('v2_nom'), label='EUT nominal voltage for phase B', default=120.0)
    info.param(pname('v3_nom'), label='EUT nominal voltage for phase C', default=120.0)
    info.param(pname('i1_curl'), label='Grid current limiter for phase A', default=120.0)
    info.param(pname('i2_curl'), label='Grid current limiter for phase B', default=120.0)
    info.param(pname('i3_curl'), label='Grid current limiter for phase C', default=120.0)

    info.param(pname('freq'), label='Frequency', default=60.0)
    info.param(pname('comm'), label='Communications Interface', default='VISA',values=['GPIB','VISA'])
    info.param(pname('gpib_device'), label='GPIB address', active=pname('comm'), active_value=['GPIB'], default='GPIB0::17::INSTR')
    info.param(pname('visa_device'), label='VISA address', active=pname('comm'),active_value=['VISA'], default='GPIB0::17::INSTR')
    info.param(pname('comm_wave'), label='Analog Communications Interface', default='VISA', values=['GPIB', 'VISA'])
    info.param(pname('visa_device_wave'), label='VISA address', active=pname('comm_wave'),active_value=['VISA'],default='GPIB0::2::INSTR')

GROUP_NAME = 'elgar_3'

class GridSim(gridsim.GridSim):

    def __init__(self, ts, group_name):
        ts.log('Grid sim init')
        # Resource Manager for VISA
        self.rm = None
        # Connection to instrument for VISA-GPIB
        self.conn = None
        gridsim.GridSim.__init__(self, ts, group_name)
        self.phases_param = ts._param_value('phases')
        self.v1_nom_param = ts._param_value('v1_nom')
        self.v2_nom_param = ts._param_value('v2_nom')
        self.v3_nom_param = ts._param_value('v3_nom')
        self.i1_curl = ts._param_value('i1_curl')
        self.i2_curl = ts._param_value('i2_curl')
        self.i3_curl = ts._param_value('i3_curl')
        self.freq_param = ts._param_value('freq')
        self.profile_name = ts.param_value('profile.profile_name')
        self.comm = ts._param_value('comm')
        self.gpib_bus_address = ts._param_value('gpib_bus_address')
        self.gpib_board = ts._param_value('gpib_board')
        self.visa_device = ts._param_value('visa_device')
        self.cmd_str = ''

        # open communications, not the relay  and stop profile
        self.open()

        self.profile_stop()

        # Configure grid simulator at beginning of test = auto_config
        # Follow the Power ON/OFF sequence (p.3-4 Manual Addendum)
        # Config implemented with ABLE command
        # if self.auto_config == 'Enabled':
        #     ts.log('Configuring the Grid Simulator.')
        #     self.config()
        #
        # state = self.relay()
        # if ts.confirm('Please turn ON the output by pressing on (Output ON/OFF) push button on the Grid simulator') is False:
        #     raise gridsim.GridSimError('Aborted grid simulation')
        # else:
        # TODO : Here is where we can add the AC switch control
        #     self.ts.log('Grid is energize.')
        # if state != gridsim.RELAY_CLOSED:
        #     if self.ts.confirm('Would you like to close the grid simulator relay and ENERGIZE the system?') is False:
        #         raise gridsim.GridSimError('Aborted grid simulation')
        #     else:
        #         self.ts.log('Turning on grid simulator.')
        #         self.relay(state=gridsim.RELAY_CLOSED)

        if self.profile_name is not None and self.profile_name != 'Manual':
            self.profile_load(self.v1_nom_param, self.freq_param, self.profile_name)




    # Search for ABLE equivalent - <ATN> Not tested -
    def info(self):
        # self.ts.log('CanmetEnergy Grid simulator' )
        return

    # Missing the method regen() to be implemented
    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """

        # self.ts.log('Grid simulator model: %s' % self.info().strip())
        self.ts.log('CanmetEnergy Grid simulator')

        # put simulator in regenerative mode

        # state = self.regen()
        # if state != gridsim.REGEN_ON:
        #     state = self.regen(gridsim.REGEN_ON)
        # # self.ts.log('Grid sim regenerative mode is: %s' % state)
        self.ts.log('Grid sim regenerative mode is not yet implemented for ELGAR704')

        # set the phase angles for the 3 phases
        self.config_phase_angles()

        # set voltage range
        self.ts.log('Grid sim can`t set voltage range')
        #         v_max = self.v_max_param
        # self.ts.log('Grid sim max voltage settings: v1 = %s, v2 = %s, v3 = %s' % (v_max, v_max, v_max))
        #
        # v1, v2, v3 = self.voltage_max()
        # if v1 != v_max or v2 != v_max or v3 != v_max:
        #     self.voltage_max(voltage=(v_max, v_max, v_max))
        #     v1, v2, v3 = self.voltage_max()
        # self.ts.log('Grid sim max voltage settings: v1 = %s, v2 = %s, v3 = %s' % (v1, v2, v3))


        # set nominal voltage

        self.ts.log('Grid sim nominal voltage settings: v1 = {}, v2 = {}, v3 = {}'.format(self.v1_nom_param, self.v2_nom_param, self.v3_nom_param))
        # v_nom = self.v1_nom_param
        # v1, v2, v3 = self.voltage()
        # if v1 != v_nom or v2 != v_nom or v3 != v_nom:
        self.voltage(voltage=(self.v1_nom_param, self.v2_nom_param, self.v3_nom_param))
            # v1, v2, v3 = self.voltage()

        # set the frequency
        self.ts.log('Frequency set to {} Hz'.format(self.freq_param))
        self.freq(self.freq_param)


        # set max current if it's not already at gridsim_Imax
        self.ts.log('Grid sim current limit settings : curl_1 : ')
        # i_max = self.i_max_param
        # i1, i2, i3 = self.current()
        ''' ###
        if i1 != i_max or i2 != i_max or i3 != i_max:
            self.current(current=(i_max, i_max, i_max))
            i1,i2,i3 = self.current()
        '''

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
                    # TODO : Add the connection for AWG430
                    # the default pyvisa write termination is '\r\n' work with the ELGAR704 (p.3-2 Manual Addendum)
                    #self.conn.write_termination = '\r\n'

                    self.ts.sleep(1)

                except Exception, e:
                    raise gridsim.GridSimError('Cannot open VISA connection to %s\n\t%s' % (self.visa_device,str(e)))

            else:
                raise ValueError('Unknown communication type %s. Use GPIB or VISA' % self.comm)

            self.ts.sleep(2)

        except Exception, e:
            raise gridsim.GridSimError(str(e))

    def cmd(self, cmd_str):
        try:
            self.conn.write(cmd_str)
        except Exception, e:
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
        if self.comm == 'Serial':
            self.conn.close()
        elif self.comm == 'GPIB':
            raise NotImplementedError('The driver for plain GPIB is not implemented yet.')
        elif self.comm == 'VISA':
            try:
                if self.rm is not None:
                    if self.conn is not None:
                        self.conn.close()
                    self.rm.close()

                self.ts.sleep(1)
            except Exception, e:
                raise gridsim.GridSimError(str(e))
        else:
            raise ValueError('Unknown communication type %s. Use Serial, GPIB or VISA' % self.comm)

    # ABLE command add it
    def config_phase_angles(self,pang =None):
        if self.phases_param == 1:
            self.ts.log_debug('Configuring system for single phase.')
            # phase 1 always 'preconfigured' at 0 phase angle
            self.cmd('PANGA 0')
            # self.form(1) - UNSUPPORTED
        elif self.phases_param == 2:
            # set the phase angles for split phase
            self.ts.log_debug('Configuring system for split phase on Phases A & B.')
            self.cmd('PANGB 180.0')
            # self.form(2) - UNSUPPORTED
        elif self.phases_param == 3:
            # set the phase angles for the 3 phases
            self.ts.log_debug('Configuring system for three phase.')
            self.cmd('PANGB 120.0')
            self.cmd('PANGB 240.0')
            # self.form(3)  - UNNECESSARY BECAUSE IT IS THE DEFAULT
        else:
            raise gridsim.GridSimError('Unsupported phase parameter: %s' % (self.phases_param))


    # ABLE command add it
    def voltage(self, voltage=None):
        """
        Set the value for voltage 1, 2, 3 if provided. If none provided, obtains
        the value for voltage. Voltage is a tuple containing a voltage value for
        each phase.
        """
        if voltage is not None:
            # set output voltage on all phases
            # self.ts.log_debug('voltage: %s, type: %s' % (voltage, type(voltage)))
            if type(voltage) is not list and type(voltage) is not tuple:
                self.cmd('VOLTA {}'.format(voltage[0]))
                self.cmd('VOLTB {}'.format(voltage[1]))
                self.cmd('VOLTC {}'.format(voltage[2]))
            else:
                self.cmd('VOLTS %0.1f' % voltage[0])  # use the first value in the 3 phase list

        # TODO : See why TST VA,VB,VC don't work
        # v1 = self.query('TST VA')
        # v2 = self.query('TST VB')
        # v3 = self.query('TST VC')
        # return float(v1[:-1]), float(v2[:-1]), float(v3[:-1])
        return

    # ABLE command add it
    def voltage_max(self, voltage=None):
        """
        Set the value for max voltage if provided. If none provided, obtains
        the value for max voltage.
        """
        if voltage is not None:
            voltage = max(voltage)  # voltage is a triplet but Elgar only takes one value
            # TODO : Check if it matches with ELGAR 704
            if voltage == 132 :
                self.cmd('VOLTS %0.0f' % voltage)
            else:
                raise gridsim.GridSimError('Invalid Max Voltage %s V, must be 132 V.' % str(voltage))
        v1 = 120.0
        v2 = 120.0
        v3 = 120.0
        # TODO : See why TST VA,VB,VC don't work
        # v1 = self.query('TST VA')
        # v2 = self.query('TST VB')
        # v3 = self.query('TST VC')
        return

    # ABLE command add it
    def current(self, current=None):
        """
        Set the value for current if provided. If none provided, obtains
        the value for current.
        """
        if current is not None:
            # set output current limit on all phases
            # self.ts.log_debug('voltage: %s, type: %s' % (voltage, type(voltage)))
            if type(current) is not list and type(current) is not tuple:
                self.cmd('CURLA {}'.format(current[0]))
                self.cmd('CURLB {}'.format(current[1]))
                self.cmd('CURLC {}'.format(current[2]))
            else:
                self.cmd('CURLS {}'.format(current[0]))  # use the first value in the 3 phase list
        # i1 = self.query('TST IA')
        # i2 = self.query('TST IB')
        # i3 = self.query('TST IC')
        return

    # ABLE command add it
    def current_max(self, current=None):
        """
        Set the value for max current if provided. If none provided, obtains
        the value for max voltage.
        """
        if current is not None:
            current = max(current) # current is a triplet but Elgar only takes one value
            # TODO : Check if it matches with ELGAR 704
            if current == 10 :
                self.cmd('CURLS %0.0f' % current)

            else:
                raise gridsim.GridSimError('Invalid Max Voltage %s V, must be 132 V.' % str(current))
        i1 = self.query('TST IA')
        i2 = self.query('TST IB')
        i3 = self.query('TST IC')
        return float(i1[:-1]), float(i2[:-1]), float(i3[:-1])

    # ABLE command add it
    def freq(self, freq=None):
        """
        Set the value for frequency if provided. If none provided, obtains
        the value for frequency.
        """
        if freq is not None:
            self.cmd('FREQ {}'.format(freq))
        # freq = self.query('TST FR')
        return freq

    # Not implemented yet
    def profile_load(self, profile_name, v_step=100, f_step=100, t_step=None):

        return

    # Not implemented yet
    def profile_start(self):
        """
        Start the loaded profile.
        """
        if self.profile is not None:
            for entry in self.profile:
                self.cmd(entry)

    # Not implemented yet
    def profile_stop(self):
        """
        Stop the running profile.
        """
        self.cmd('abort')

    # Not implemented yet
    def regen(self, state=None):
        """
        Set the state of the regen mode if provided. Valid states are: REGEN_ON,
        REGEN_OFF. If none is provided, obtains the state of the regen mode.
        All this was implemented for the AMETEK not the ELGAR
        """
        # TODO : Check if we can implement a REGEN function for the elgar 704

        return state

    # ABLE command add it but need to test TST CLS
    # TODO : Add a function to test the state of the relay
    def relay_close(self):
        """
        Set the state of the relay if provided. Valid states are: RELAY_OPEN,
        RELAY_CLOSED. If none is provided, obtains the state of the relay.
        """
        # This command doesn't affect the output, need to implement remote control AC switch
        self.cmd('CLS')
        self.ts.log('Closed Relay')

    def relay_open(self):
        """
        Set the state of the relay if provided. Valid states are: RELAY_OPEN,
        RELAY_CLOSED. If none is provided, obtains the state of the relay.
        """
        # This command doesn't affect the output, need to implement remote control AC switch
        self.cmd('OPN')
        self.ts.log('Opened Relay')

    def distorsion(self):
        pass

    def i_max(self):
        return self.i_max_param

    def v_max(self):
        return self.v_max_param

    def v_nom(self):
        return self.v1_nom_param


if __name__ == "__main__":
    pass