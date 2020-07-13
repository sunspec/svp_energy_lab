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
from . import loadsim
try:
    import typhoon.api.hil as cp  # control panel
    from typhoon.api.schematic_editor import model
    import typhoon.api.pv_generator as pv
except Exception as e:
    print(('Typhoon HIL API not installed. %s' % e))

typhoon_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Typhoon'
}


def loadsim_info():
    return typhoon_info


def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = typhoon_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('component_name'), label='Component Name', default='Anti-islanding1')
    # info.param(pname('property_name'), label='Property Name', default='resistance')

GROUP_NAME = 'typhoon'


class LoadSim(loadsim.LoadSim):
    """
    Template for RLC load implementations. This class can be used as a base class or
    independent RLC load classes can be created containing the methods contained in this class.
    """

    def __init__(self, ts, group_name):
        loadsim.LoadSim.__init__(self, ts, group_name)
        self.component_name = self._param_value('component_name')
        self.ts = ts

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):
        pass

    def info(self):
        return 'Typhoon Anti-islanding RLC Load - 1.0'

    def resistance(self, r=None, ph=None):
        if r is not None:
            # For setting particular property of the Anti-islanding component (resistor, capacitor and inductor values):
            model.set_component_property(self.component_name, property="resistance", value=r)
            # self.ts.log_debug('Resistor set to %s Ohms' % r)
        else:
            self.ts.log('No resistance provided.')

    def inductance(self, l=None, ph=None):
        if l is not None:
            # For setting particular property of the Anti-islanding component (resistor, capacitor and inductor values):
            model.set_component_property(self.component_name, property="inductance", value=l)
        else:
            self.ts.log('No inductance provided.')

    def capacitance(self, c=None, ph=None):
        if c is not None:
            # For setting particular property of the Anti-islanding component (resistor, capacitor and inductor values):
            model.set_component_property(self.component_name, property="capacitance", value=c)
        else:
            self.ts.log('No capacitance provided.')

    def capacitor_q(self, q=None, ph=None):
        if q is not None:
            self.ts.confirm('Adjust the capacitive load of the fundamental freq to %0.3f VAr.' % q)
        else:
            self.ts.log('Enter the capacitor reactive power in VAr.')

    def inductor_q(self, q=None, ph=None):
        if q is not None:
            self.ts.confirm('Adjust the inductive load of the fundamental freq to %0.3f VAr.' % q)
        else:
            self.ts.log('Enter the inductor reactive power in VAr.')

    def resistance_p(self, p=None, ph=None):
        if p is not None:
            self.ts.confirm('Adjust the resistive load of the fundamental freq to %0.3f W.' % p)
        else:
            self.ts.log('Enter the resistor power in W.')

    def tune_current(self, i=None, ph=None):
        if i is not None:
            self.ts.confirm('Adjust R, L, and C until the fundamental frequency current through switch S3 is '
                            'less than %0.2f' % i)
        else:
            pass
