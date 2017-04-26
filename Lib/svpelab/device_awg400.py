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

import time

import vxi11


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
        self.open()


    def open(self):

        try:
            if self.params['comm'] == 'Network':
                try:
                    self.vx = vxi11.Instrument(self.params['ip_addr'])
                except Exception, e:
                    raise DeviceError('AWG400 communication error: %s' % str(e))
            elif self.params['comm'] == 'GPIB':
                raise NotImplementedError('The driver for plain GPIB is not implemented yet. ' +
                                          'Please use VISA which supports also GPIB devices')
            elif self.params['comm'] == 'VISA':
                try:
                    # sys.path.append(os.path.normpath(self.visa_path))
                    import visa
                    self.rm = visa.ResourceManager()
                    self.conn = self.rm.open_resource(self.params['visa_address'])

                except Exception, e:
                    raise DeviceError('AWG400 communication error: %s' % str(e))

            else:
                raise ValueError('Unknown communication type %s. Use GPIB or VISA' % self.params['comm'])

        except Exception, e:
            raise DeviceError(str(e))
        pass

    def close(self):
        if self.params['comm'] == 'Network':
            if self.vx is not None:
                self.vx.close()
                self.vx = None
        elif self.params['comm'] == 'GPIB':
            raise NotImplementedError('The driver for plain GPIB is not implemented yet.')
        elif self.params['comm'] == 'VISA':
            try:
                if self.rm is not None:
                    if self.conn is not None:
                        self.conn.close()
                    self.rm.close()
            except Exception, e:
                raise DeviceError('AWG400 communication error: %s' % str(e))
        else:
            raise ValueError('Unknown communication type %s. Use Serial, GPIB or VISA' % self.params['comm'])

    def cmd(self, cmd_str):
        if self.params['comm'] == 'Network':
            try:
                self.vx.write(cmd_str)
            except Exception, e:
                raise DeviceError('AWG400 communication error: %s' % str(e))

        elif self.params['comm'] == 'VISA':
            try:
                self.conn.write(cmd_str)
            except Exception, e:
                raise DeviceError('AWG400 communication error: %s' % str(e))

    def query(self, cmd_str):
        resp = ''
        if self.params['comm'] == 'Network':
            try:
                resp = self.vx.ask(cmd_str)
            except Exception, e:
                raise DeviceError('AWG400 communication error: %s' % str(e))
        elif self.params['comm'] == 'VISA':
            self.cmd(cmd_str)
            resp = self.conn.read()

        return resp

    def info(self):
        return self.query('*IDN?')

    def load_config(self, params):
        """
        Enable channels
        :param params: dict containing following possible elements:
          'sequence_filename': <sequence file name>
        :return:
        """
        pass

    def start(self):
        """
        Start sequence execution
        :return:
        """
        pass

    def stop(self):
        """
        Start sequence execution
        :return:
        """
        pass

    def chan_enable(self, chans):
        """
        Enable channels
        :param chans: list of channels to enable
        :return:
        """
        pass

    def chan_disable(self, chans):
        """
        Disable channels
        :param chans: list of channels to disable
        :return:
        """
        pass


if __name__ == "__main__":

    pass
