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

SEPARATOR = ','
TERMINATOR = '\n'

# map data points to query points
query_points = {
    'AC_VRMS': 'V',
    'AC_IRMS': 'I',
    'AC_P': 'W',
    'AC_S': 'VA',
    'AC_Q': 'VAR',
    'AC_PF': 'PF',
    'AC_FREQ': 'FREQ',
    'DC_V': 'VDC',
    'DC_I': 'IDC',
    'DC_P': 'WDC'
}


class DeviceError(Exception):
    pass


class Device(object):
    """
    """
    def __init__(self, params=None):
        self.params = params
        self.rm = None      # Resource Manager for VISA
        self.conn = None    # Connection to instrument for VISA-GPIB
        self.visa_device = params.get('visa_device')
        self.visa_path = params.get('visa_path', '')
        self.channels = params.get('channels')
        self.query_str = []
        self.data_points = ['TIME']
        self.ts = params.get('ts')

        # create query strings for configured channels
        for i in range(1,5):
            chan = self.channels[i]
            if chan is not None:
                chan_type = chan.get('type')
                points = chan.get('points')
                chan_label = chan.get('label')
                if chan_type is None:
                    raise DeviceError('No channel type specified')
                if points is None:
                    raise DeviceError('No points specified')
                query_str = 'CHAN %d; MEAS?' % (i)
                first = True
                for p in points:
                    point_str = '%s_%s' % (chan_type, p)
                    p_str = query_points.get(point_str)
                    if p_str is None:
                        raise DeviceError('Unknown point type: %s' % (p))
                    if not first:
                        query_str += ','
                    else:
                        first = False
                    query_str += ' %s' % (p_str)
                    if chan_label:
                        point_str = '%s_%s' % (point_str, chan_label)
                    self.data_points.append(point_str)

                self.query_str.append(query_str)

        self.open()  # open communications, not the relay

        # turn off header in response
        self._write('SYST:HEAD OFF')

    def info(self):
        """
        Returns the SCPI identification of the device
        :return: a string like ''
        """
        return self._query('*IDN?')

    def data_capture(self, enable=True):
        pass

    def data_read(self):
        """
        Read current measurement values.
        :return: a dictionary with the current measurement values.
        """
        data = [time.time()]
        for qs in self.query_str:
            data.extend([float(i) for i in self._query(qs).split(',')])
        return data

    def waveform_config(self, params):
        raise DeviceError('Device does not support waveform operations')

    def waveform_capture(self, enable=True):
        raise DeviceError('Device does not support waveform operations')

    def waveform_status(self):
        raise DeviceError('Device does not support waveform operations')

    def waveform_force_trigger(self):
        raise DeviceError('Device does not support waveform operations')

    def waveform_capture_dataset(self):
        raise DeviceError('Device does not support waveform operations')

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
            raise DeviceError('Cannot open VISA connection to %s' % (self.visa_device))

    def close(self):
        """
        Close any open communications resources associated with the device.
        """

        try:
            if self.rm is not None:
                if self.conn is not None:
                    self.conn.close()
                self.rm.close()

        except Exception as e:
            raise DeviceError(str(e))

    def _query(self, cmd_str):
        """
        Performs a SCPI query with the given cmd_str and returns the reply of the device
        :param cmd_str: the SCPI command which must be a valid command
        :return: the answer from the SPS
        """

        try:
            if self.conn is None:
                raise DeviceError('Device connection not open')

            return self.conn.query(cmd_str).strip()
        except Exception as e:
            raise DeviceError(str(e))

    def _write(self, cmd_str):
        """
        Performs a SCPI write command with the given cmd_str
        :param cmd_str: the SCPI command which must be a valid command
        """
        try:
            if self.conn is None:
                raise DeviceError('Device connection not open')

            return self.conn.write(cmd_str)
        except Exception as e:
            raise DeviceError(str(e))


if __name__ == "__main__":

    dpm = Device(params={'visa_device': 'GPIB0::12::INSTR',
                         'visa_path': 'C:/Program Files (x86)/IVI Foundation/VISA/WinNT/agvisa/agbin/visa32.dll',
                         'channels': [None,
                                      {'type': 'AC',
                                       'points': ('VRMS', 'IRMS', 'P', 'S', 'Q', 'PF', 'FREQ'),
                                       'label': '1'},
                                      {'type': 'AC',
                                       'points': ('VRMS', 'IRMS', 'P', 'S', 'Q', 'PF', 'FREQ'),
                                       'label': '2'},
                                      {'type': 'AC',
                                       'points': ('VRMS', 'IRMS', 'P', 'S', 'Q', 'PF', 'FREQ'),
                                       'label': '3'},
                                      {'type': 'DC',
                                       'points': ('V', 'I', 'P'),
                                       'label': ''}]
    })
    print(dpm.data_points)

