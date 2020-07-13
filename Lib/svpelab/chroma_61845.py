'''
    Chroma 61845 45 kW Grid Sim Driver File
    Nathaniel Black
    (c) 2-feb-2017 Nathaniel Black at Outback Power Inc
'''

from . import gridsim
from . import gridsim_chroma
import time
TEST = None
TERMINATOR = '\n'

class ChromaGridSimError(Exception):
    pass

class ChromaGridSim(object):

    def __init__(self, visa_device, visa_path = None):

        self.conn = None

        self.visa_device = visa_device
        self.visa_path = visa_path

    def _query(self, cmd_str):
        """
        Performs an SCPI Querry
        :param cmd_str:
        :return:
        """
        if TEST is not None:
            print((cmd_str.strip()))
            return '0.0'
        try:
            if self.conn is None:
                raise ChromaGridSimError('GPIB connection not open')
            return self.conn.query(cmd_str.strip('\n'))

        except Exception as e:
            raise ChromaGridSimError(str(e))

    def _cmd(self, cmd_str):
        """
        Performs an SCPI Querry
        :param cmd_str:
        :return:
        """
        if TEST is not None:
            print(cmd_str.strip())
            return
        try:
            if self.conn is None:
                raise ChromaGridSimError('GPIB connection not open')
            return self.conn.write(cmd_str.strip('\n'))
        except Exception as e:
            raise ChromaGridSimError(str(e))

    def cmd(self, cmd_str):
        try:
            self._cmd(cmd_str)
            resp = self._query('SYSTem:ERRor?\n') #\r
            print('resp\n')
            print(resp)
            if len(resp) > 0:
                if resp[0] != '0':
                    raise ChromaGridSimError(resp + ' ' + cmd_str)
        except Exception as e:
            raise ChromaGridSimError(str(e))

    def query(self, cmd_str):
        try:
            resp = self._query(cmd_str).strip()
        except Exception as e:
            raise ChromaGridSimError(str(e))
        return resp

    def config_phase_angles(self, phases):
        if phases == 1:
            self.cmd('inst:phase single\n')
            self.cmd('sour:func:shap:a sine\n')
            self.cmd('sour:func:shape a\n')
        elif phases == 2:
            self.cmd('inst:phase three\n')
            self.cmd('sour:phase:p12 180.0\n')
            self.cmd('sour:phase:p13 240.0\n')
            self.cmd('sour:phase:three independ\n')
            self.cmd('inst:edit all')
            self.cmd('sour:func:shap:a sine\n')
            self.cmd('sour:func:shap a\n')
        elif phases == 3:
            # set the phase angles for the 3 phases
            self.cmd('inst:phase three')
            self.cmd('sour:phase:p12 120.0\n')
            self.cmd('sour:phase:p13 240.0\n')
            self.cmd('sour:phase:three independ\n')
            self.cmd('isnt:edit all')
            self.cmd('sour:func:shap:a sine\n')
            self.cmd('sour:func:shape a\n')

        else:
            raise ChromaGridSimError('Unsupported phase count: %s' % (phases))

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        # Perform Device Specific Setup Here
        #self.query('INSTrument:EDIT ALL')

    def open(self):
        """
        Open the communications resources associated with the device.
        """
        try:
            # sys.path.append(os.path.normpath(self.visa_path))
            import visa
            self.rm = visa.ResourceManager(self.visa_path)
            self.conn = self.rm.open_resource(self.visa_device)
            # set terminator in pyvisa
            self.conn.write_termination = TERMINATOR

        except Exception as e:
            raise ChromaGridSimError('Cannot open VISA connection to %s' % (self.visa_device))

    def close(self):
        """
        Close any open communications resources associated with the grid
        simulator.
        """
        if self.conn:
            self.conn.close()

    def current(self, current=None):
        """
        Set the value for current if provided. If none provided, obtains
        the value for current.
        """
        if current is not None:
            self.cmd('inst:coup all')
            self.cmd('source:curr:lim %0.2f\n' % current)
        curr_str = self.query('source:curr:lim?\n')
        return float(curr_str[:-1])

    def freq(self, freq=None):
        """
        Set the value for frequency if provided. If none provided, obtains
        the value for frequency.
        Chroma has CW or IMMediate options for the frequency.  Need to figure out what these are.
        """
        if freq is not None:
            self.cmd('inst:edit all')
            self.cmd('source:freq %0.2f\n' % freq)
        freq = self.query('source:freq?\n')
        return freq

    def profile_load(self, dwell_list, freq_start_list, freq_end_list, v_start_list, v_end_list, shape_list):

        cmd_list = []
        #cmd_list.append('trig:tran:sour imm\n')voltage

        #cmd_list.append('list:step auto\n')
        cmd_list.append('trig off\n')
        cmd_list.append('output:mode fixed\n')
        cmd_list.append('list:coup ALL')
        cmd_list.append('list:count 1')
        cmd_list.append('list:base TIME')
        cmd_list.append('list:trig auto')
        cmd_list.append('list:dwel %s' % dwell_list)
        cmd_list.append('list:shape %s' % shape_list)
        cmd_list.append('list:volt:ac:star %s' % v_start_list)
        cmd_list.append('list:volt:ac:end %s' % v_end_list)
        cmd_list.append('list:freq:star %s' % freq_start_list)
        cmd_list.append('list:freq:end %s' %freq_end_list)
        #cmd_list.append('*esr?\n')
        cmd_list.append('output:mode list\n')

        return cmd_list

    def profile_stop(self):
        """
        Stop the running profile.
        """
        self.cmd('trig off\n')
        self.relay(gridsim.RELAY_OPEN)

    def output(self, state=None):
        """
        Set the state of the output if provided. Valid states are: ON,
        OFF. If none is provided, obtains the state of the Output.
        """
        if state is not None:
            if state == gridsim.OUTPUT_OFF:
                # Some clean up here.  Is this the correct place?
                self.cmd('trig off\n')
                self.cmd('output:state off\n')
                self.cmd('output:mode fixed\n')
            elif state == gridsim.OUTPUT_ON:
                self.cmd('output:state on\n')
            else:
                raise ChromaGridSimError('Invalid Output state. State = "%s"', state)
        else:
            output = self.query('output:state?\n').strip()
            if output == '0':
                state = gridsim.OUTPUT_OFF
            elif output == '1':
                state = gridsim.OUTPUT_ON
            else:
                state = gridsim.RELAY_UNKNOWN
        return state



    def relay(self, state=None):
        """
        Set the state of the relay if provided. Valid states are: RELAY_OPEN,
        RELAY_CLOSED. If none is provided, obtains the state of the relay.
        """
        if state is not None:
            if state == gridsim.RELAY_OPEN:
                # Some clean up here.  Is this the correct place?
                self.cmd('trig off\n')
                self.cmd('output:state off\n')
                self.cmd('output:relay off\n')
                self.cmd('output:mode fixed\n')
            elif state == gridsim.RELAY_CLOSED:
                self.cmd('output:relay on\n')
                time.sleep(.100)
                self.cmd('output:state on\n')
            else:
                raise ChromaGridSimError('Invalid relay state. State = "%s"', state)
        else:
            relay = self.query('output:relay?\n').strip()
            # self.ts.log(relay)
            if relay == '0':
                state = gridsim.RELAY_OPEN
            elif relay == '1':
                state = gridsim.RELAY_CLOSED
            else:
                state = gridsim.RELAY_UNKNOWN
        return state

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
                self.cmd('inst:edit all')
                self.cmd('source:volt:lev:imm:ampl:ac %0.1f\n' % voltage)
            else:
                self.cmd('inst:edit all')
                self.cmd('source:volt:lev:imm:ampl:ac %0.1f\n' % voltage[0])  # use the first value in the 3 phase list
        v1 = self.query('source:volt:lev:imm:ampl:ac?\n')
        return float(v1), float(v1), float(v1)

    def voltage_max(self, voltage=None):
        """
        Set the value for max voltage if provided. If none provided, obtains
        the value for max voltage.
        """
        v1 = 0
        if voltage is not None:
            voltage = max(voltage)  # voltage is a triplet but chroma only takes one value
            if voltage is not None:
                if (voltage > 0 and voltage < 300):
                    self.cmd('source:volt:limit:ac %0.0f\n' % voltage)
                else: raise ChromaGridSimError
            v1 = self.query('source:volt:limit:ac?\n')
        return float(v1), float(v1), float(v1)

    def voltage_range(self, range):
        if range == 300:
            self.cmd('voltage:range hi')
        elif range == 150:
            self.cmd('voltage:range low')
        else:
            raise ChromaGridSimError

    def voltage_slew(self,slew):
        if slew is not None:
            self.cmd('output:slew:voltage:ac %s' % slew)
        else: raise ChromaGridSimError

    def freq_slew(self,slew):
        if slew is not None:
            self.cmd('output:slew:freq %s' % slew)
        else:
            raise ChromaGridSimError

if __name__ == "__main__":

    import time

    #TEST = True

    visa_path = 'C:/Program Files (x86)/IVI Foundation/VISA/WinNT/agvisa/agbin/visa32.dll'
    visa_device = 'USB0::0x0A69::0x0870::618450000066::0::INSTR'
    cgs = ChromaGridSim(visa_device, visa_path)
    cgs.open()

    print('Testing Query String')
    print(cgs.query('*IDN?'))
    '''
    print '\nconfig_phase_angles for Single Phase'
    cgs.config_phase_angles(1)
    '''
    print('\nconfig_phase_angles for 3 phase')
    cgs.config_phase_angles (2)
    '''

    print '\nClosing'
    cgs.close()
    print '\nRe-Opening'
    cgs.open()
    '''
    print('\nRunning Config()')
    cgs.config()

    cgs.voltage(40)
    cgs.freq (50)

    print('\nRunning Current()')
    cgs.current(15)

    print('\nRunning freq()')
    cgs.freq (62)

    cgs.relay('closed')

    print('\nRunning Profile_load()')
    dwell_list = '2000,2000,2000,2000,2000,0.0'
    freq_start_list = '40,50,60,50,40'
    freq_end_list = '50,60,60,40,40'
    v_start_list = '60,60,120,120,60'
    v_end_list = '60,120,120,60,60'
    shape_list = 'a,a,a,a,a'

    cmd_list = cgs.profile_load(dwell_list=dwell_list,
                                freq_start_list=freq_start_list,
                                freq_end_list=freq_end_list,
                                v_start_list=v_start_list,
                                v_end_list=v_end_list,
                                shape_list=shape_list)

    '''
    print('\nRunning Profile')
    for entry in cmd_list:
        cgs.cmd(entry)
    cgs.cmd('trig ON')
    cgs.relay('closed')
    '''
    '''
    time.sleep (10)

    print'\nRunning profile_stop()'
    cgs.profile_stop()

    print '\nRunning relay()'
    cgs.relay ('open')
    cgs.relay('closed')

    print '\nRunning Voltage()'
    cgs.voltage(122.5)
    '''
    print('\nRunning Voltage_max()')
    cgs.voltage_max({125,124,124})

    print('\nDone, closing connection')

    cgs.close()
