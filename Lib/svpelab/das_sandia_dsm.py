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

import script
from . import device_sandia_dsm
from . import das

sandia_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Sandia DSM'
}

def das_info():
    return sandia_info

def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = sandia_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('dsm_method'), label='Data Acquisition Method', default='Sandia LabView DSM',
               values=['Sandia LabView DSM', 'Sandia LabView DSM UDP'],
               desc='Each lab will have different data acquisition methods. Sandia passes the data from the DAQ '
                    'to python by writing the values locally or collecting them over the local network.')
    info.param(pname('das_comp'), label='Data Acquisition Computer', default='10 Node',
               values=['10 Node', 'DAS 3', 'DAS 5', 'DAS 8'],
               active=pname('dsm_method'), active_value=['Sandia LabView DSM UDP'],
               desc='Selection of the data acquisition system')
    info.param(pname('node'), label='Node at Sandia - Used to ID DAQ channel', default=10,
               desc='Selection of the EUT which will be used for the test (Sandia specific).')
    info.param(pname('sample_interval'), label='Sample Interval (ms)', default=1000)
    info.param(pname('file_path'), label='File Path', default='C:\\python_dsm', ptype=script.PTYPE_DIR)

GROUP_NAME = 'sandia'


class DAS(das.DAS):

    def __init__(self, ts, group_name, points=None, sc_points=None):
        das.DAS.__init__(self, ts, group_name, points=points, sc_points=sc_points)

        self.params['sample_interval'] = self._param_value('sample_interval')
        self.params['dsm_method'] = self._param_value('dsm_method')
        self.params['dsm_id'] = self._param_value('node')
        self.params['comp'] = self._param_value('comp')
        self.params['ts'] = ts

        # if not absolute path, use SVP 'Files' directory
        file_path = self._param_value('file_path')
        if not os.path.isabs(file_path):
            os.path.join(self.files_dir, file_path)
        self.params['file_path'] = file_path

        self.device = device_sandia_dsm.Device(self.params)
        self.data_points = self.device.data_points

        # initialize soft channel points
        self._init_sc_points()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

if __name__ == "__main__":

    pass