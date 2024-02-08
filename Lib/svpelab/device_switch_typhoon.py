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
    import typhoon.api.hil as cp  # control panel
    from typhoon.api.schematic_editor import model
    import typhoon.api.pv_generator as pv
except Exception as e:
    print(('Typhoon HIL API not installed. %s' % e))

class Device(object):

    def __init__(self, params=None):
        self.params = params
        self.ts = self.params.get('ts')
        self.name = self.params.get('name')

    def info(self):
        if cp.available_contactors():
            self.ts.log('Contactors in the model: %s' % cp.get_contactors())
        else:
            self.ts.log_warning('No contactors in the model.')
        return 'Switch Controller Typhoon - 1.0'

    def open(self):
        pass

    def close(self):
        pass

    def switch_open(self):
        cp.set_contactor(self.name, swControl=True, swState=False)
        # e.g., self.name = 'Anti-islanding1.Grid'

    def switch_close(self):
        cp.set_contactor(self.name, swControl=True, swState=True)
        # e.g., self.name = 'Anti-islanding1.Grid'

    def switch_state(self):
        pass




