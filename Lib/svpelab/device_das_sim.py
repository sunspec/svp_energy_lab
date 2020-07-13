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

import os
import time
from . import dataset


class DeviceError(Exception):
    """
    Exception to wrap all das generated exceptions.
    """
    pass


class Device(object):

    def __init__(self, params=None):
        self.ts = params['ts']
        self.points = params['points']
        self.data_points = []
        self.data_file = params['data_file']
        self.at_end = params['at_end']
        self.file_= None
        self.use_timestamp = params['use_timestamp']
        self.ds = dataset.Dataset()
        self.index = 0

        if self.data_file:
            self.ds.from_csv(self.data_file)
            self.data_points = list(self.ds.points)
        else:
            raise DeviceError('No data file specified')

    def info(self):
        return 'DAS Simulator - 1.0'

    def open(self):
        pass

    def close(self):
        pass

    def data_capture(self, enable=True):
        pass

    def data_read(self):
        data = []
        if len(self.ds.points) > 0:
            count = len(self.ds.data[0])
            if count > 0:
                if self.index >= count:
                    if self.at_end == 'Loop to start':
                        self.index = 0
                    elif self.at_end == 'Repeat last record':
                        self.index = count - 1
                    else:
                        raise DeviceError('End of data reached')

            for i in range(len(self.ds.points)):
                data.append(self.ds.data[i][self.index])

        return data

    def waveform_config(self, params):
        pass

    def waveform_capture(self, enable=True, sleep=None):
        """
        Enable/disable waveform capture.
        """
        pass

    def waveform_status(self):
        # mm-dd-yyyy hh_mm_ss waveform trigger.txt
        # mm-dd-yyyy hh_mm_ss.wfm
        # return INACTIVE, ACTIVE, COMPLETE
        return 'COMPLETE'

    def waveform_force_trigger(self):
        pass

    def waveform_capture_dataset(self):
        return self.ds

if __name__ == "__main__":

    pass


