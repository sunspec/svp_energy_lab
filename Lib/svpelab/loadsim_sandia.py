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

sandia_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Sandia'
}


def loadsim_info():
    return sandia_info


def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = sandia_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)

    # RTU parameters
    info.param(pname('ifc_name'), label='Interface Name', default='COM3',  active=pname('ifc_type'),
               active_value=['RTU'],
               desc='Select the communication port from the UMS computer to the EUT.')
    info.param(pname('baudrate'), label='Baud Rate', default=9600, values=[9600, 19200], active=pname('ifc_type'),
               active_value=['RTU'])
    info.param(pname('parity'), label='Parity', default='N', values=['N', 'E'], active=pname('ifc_type'),
               active_value=['RTU'])
    # TCP parameters
    info.param(pname('ipaddr'), label='IP Address', default='192.168.0.170', active=pname('ifc_type'),
               active_value=['TCP'])
    info.param(pname('ipport'), label='IP Port', default=502, active=pname('ifc_type'), active_value=['TCP'])

    info.param(pname('relay_ifc_type'), label='Relay Interface Type', default='VISA', values=['VISA', 'RTU', 'TCP'])
    # VISA parameters
    info.param(pname('relay_ifc_name'), label='VISA String', default='ASRL1::INSTR',  active=pname('relay_ifc_type'),
               active_value=['VISA'], desc='Enter VISA string.')
    # Need to change /Dev1/port0/line17
    # u'ASRL1::INSTR', u'ASRL2::INSTR', u'ASRL3::INSTR', u'ASRL4::INSTR', u'ASRL7::INSTR'

GROUP_NAME = 'sandia'


class LoadSim(loadsim.LoadSim):
    """
    Template for RLC load implementations. This class can be used as a base class or
    independent RLC load classes can be created containing the methods contained in this class.
    """

    def __init__(self, ts, group_name):
        loadsim.LoadSim.__init__(self, ts, group_name)

    def resistance(self, r=None, ph=None):
        if r is not None:
            self.ts.confirm('Adjust the resistive load to R = %0.3f Ohms.' % r)
        else:
            self.ts.log('Enter the resistive load in Ohms.')

    def inductance(self, l=None, ph=None):
        if i is not None:
            self.ts.confirm('Adjust the inductive load to L = %0.6f H.' % l)
        else:
            self.ts.log('Enter the inductive load in H.')

    def capacitance(self, c=None, ph=None):
        if c is not None:
            self.ts.confirm('Adjust the capacitive load to C = %0.6f F.' % c)
        else:
            self.ts.log('Enter the capacitive load in F.')

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
        if c is not None:
            self.ts.confirm('Adjust R, L, and C until the fundamental frequency current through switch S3 is '
                            'less than %0.2f' % i)
        else:
            pass

    def switch_s3(self, switch_state=None):
        if switch_state is not None:
            if switch_state == loadsim.S3_CLOSED:
                self.ts.confirm('Preparing to close S3 switch (switch to the utility). '
                                'Verify that the inverter output current is zero.')
            elif switch_state == loadsim.S3_OPEN:
                self.ts.log('Opening S3 switch (switch to the utility).')
            else:
                self.ts.log_warning('Unknown S3 switch state.')
        else:
            self.ts.log_warning('No switch state given for the RLC Load S3 switch.')
