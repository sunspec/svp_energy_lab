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

import visa

class DeviceError(Exception):
    """
    Exception to wrap all das generated exceptions.
    """
    pass


class Device(object):

    def __init__(self, params):
        self.params = params
        self.vx = None
        # Resource Manager for VISA
        self.rm = None
        # Connection to instrument for VISA-GPIB
        self.conn = None

    def open(self):

        try:
            self.rm = visa.ResourceManager()
            if self.params['comm'] == 'Network':
                try:
                    self._host = self.params['ip_addr']
                    self._port = 4000
                    self.conn = self.rm.open_resource("TCPIP::{0}::{1}::SOCKET".format(self._host,self._port),read_termination='\n')
                except Exception as e:
                    raise DeviceError('AWG400 communication error: %s' % str(e))
            elif self.params['comm'] == 'GPIB':
                raise NotImplementedError('The driver for plain GPIB is not implemented yet. ' +
                                          'Please use VISA which supports also GPIB devices')
            elif self.params['comm'] == 'VISA':
                try:
                    self.conn = self.rm.open_resource(self.params['visa_address'])

                except Exception as e:
                    raise DeviceError('AWG400 communication error: %s' % str(e))

            else:
                raise ValueError('Unknown communication type %s. Use GPIB or VISA' % self.params['comm'])

        except Exception as e:
            raise DeviceError(str(e))

        self.funcgen_mode()

        pass

    def close(self):
        if self.params['comm'] == 'Network':
            try:
                if self.conn is not None:
                    self.conn.close()
            except Exception as e:
                raise DeviceError('AWG400 communication error: %s' % str(e))
        elif self.params['comm'] == 'GPIB':
            raise NotImplementedError('The driver for plain GPIB is not implemented yet.')
        elif self.params['comm'] == 'VISA':
            try:
                if self.conn is not None:
                    self.conn.close()
            except Exception as e:
                raise DeviceError('AWG400 communication error: %s' % str(e))
        else:
            raise ValueError('Unknown communication type %s. Use Serial, GPIB or VISA' % self.params['comm'])

    def cmd(self, cmd_str):
        if self.params['comm'] == 'VISA' or self.params['comm'] == 'Network':
            self.conn.write(cmd_str)

    def query(self, cmd_str):
        if self.params['comm'] == 'VISA' or self.params['comm'] == 'Network':
            self.cmd(cmd_str)
            resp = self.conn.read()

        return resp

    def info(self):
        try:
            resp = self.conn.query("*IDN?")
        except Exception as e:
            raise DeviceError('AWG400 communication error: %s' % str(e))
        return resp

    def load_config(self,sequence = None):
        """
        Enable channels
        :param params: dict containing following possible elements:
          'sequence_filename': <sequence file name>
        :return:
        """

        # Load configuration settings from sequence file textbox
        self.cmd("AWGControl:SREStore '{}','MAIN'".format(sequence))
        
    def funcgen_mode(self):
        """
        Set the AWG in function generator
        :return: The generator mode
        """

        if self.params['gen_mode'] == 'ON':
            self.cmd("AWGControl:FG ON")
        else:
            self.cmd("AWGControl:FG OFF")



    def start(self):
        """
        Start sequence execution
        :return:
        """
        # self.conn.write("AWGControl:RUN:IMMediate")
        self.conn.write("AWGControl:EVENt:LOGic:IMMediate")
        pass

    def stop(self):
        """
        Stop sequence execution
        :return:
        """

        self.conn.write("AWGControl:STOP:IMMediate")
        # Turn off all channel
        for i in range(1,4):
            self.conn.write("OUTput{}:STATe OFF".format(i))

        pass

    def trigger(self):
        """
        Info : This command is equivalent to pressing the FORCE TRIGGER button front panel
        Send trigger event execution 
        :return:
        """
        self.cmd("*TRG")

    def next_event(self):
        """
        Send event transient execution 
        :return:
        """
        self.conn.write("AWGControl:EVENt:LOGic:IMMediate")

    def chan_state(self, chans):
        """
        Enable channels
        :param chans: list of channels to enable
        :return:
        """
        i = 1
        for chan in chans:
            if chan == True :
                self.cmd("OUTput{}:STATe ON".format(i))
            elif chan == False :
                self.cmd("OUTput{}:STATe OFF".format(i))
            i = i + 1
        pass



    def error(self):
        """
        This only to have a feedback of the last operation
        :return: The error of last operation
        """
        return self.query("SYSTem:ERRor:NEXT?")

    def voltage(self, voltage, channel):
        """
        This command adjusts peak to peak voltage of the function waveform on selected channel.
        :param voltage: The amplitude of the waveform in step of 1mV withing the range of 0.020Vpp to 2.000Vpp
        :param channel: Channel to configure
        """
        if self.params['gen_mode'] == 'ON':
            if channel == 1:
                voltage *=0.005941
            elif channel == 2:
                voltage *= 0.005925
            elif channel == 3:
                voltage *= 0.005891
            print(("AWGControl:FG{}:VOLTage {}".format(channel, voltage)))
            self.cmd("AWGControl:FG{}:VOLTage {}".format(channel, voltage))

    def frequency(self, frequency):
        """
        This command adjusts peak to peak voltage of the function waveform on selected channel.
        :param frequency: The frequency of the waveform on all channels
        """
        self.cmd("AWGControl:FG:FREQuency {}".format(frequency))

    def phase(self, phase, channel):
        """
        This command adjusts peak to peak voltage of the function waveform on selected channel.
        :param phase: The amplitude of the waveform in step of 1mV withing the range of 0.020Vpp to 2.000Vpp
        :param channel: Channel to configure
        """
        self.cmd("AWGControl:FG{}:PHASe {}DEGree".format(channel, phase))



if __name__ == "__main__":
    pass
