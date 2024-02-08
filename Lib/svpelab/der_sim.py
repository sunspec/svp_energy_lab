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

from . import der

sim_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'DER Simulation'
}

def der_info():
    return sim_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = sim_info['mode']
    info.param_add_value(gname('mode'), mode)
    '''
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    '''

GROUP_NAME = 'manual'

class DER(der.DER):

    def __init__(self, ts, group_name):
        der.DER.__init__(self, ts, group_name)

    def info(self):
        """ Get DER device information.

        Params:
            Manufacturer
            Model
            Version
            Options
            SerialNumber

        :return: Dictionary of information elements.
        """
        try:
            params = {}
            params['Manufacturer'] = 'RANDOM SIMULATED'
            params['Model'] = 'RANDOM SIMULATED'
            params['Options'] = 'RANDOM SIMULATED'
            params['Version'] = 'RANDOM SIMULATED'
            params['SerialNumber'] = 'RANDOM SIMULATED'
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def measurements(self):
        """ Get measurement data.

        Params:

        :return: Dictionary of measurement data.
        """

        try:
            a = 123
            params = {}

            params['A'] = a
            params['AphA'] = a
            params['AphB'] = a
            params['AphC'] = a
            params['PPVphAB'] = a
            params['PPVphBC'] = a
            params['PPVphCA'] = a
            params['PhVphA'] = a
            params['PhVphB'] = a
            params['PhVphC'] = a
            params['W'] = a
            params['Hz'] = a
            params['VA'] = a
            params['VAr'] = a
            params['PF'] = a
            params['WH'] = a
            params['DCA'] = a
            params['DCV'] = a
            params['DCW'] = a
            params['TmpCab'] = a
            params['TmpSnk'] = a
            params['TmpTrns'] = a
            params['TmpOt'] = a
            params['St'] = a
            params['StVnd'] = a
            params['Evt1'] = a
            params['Evt2'] = a
            params['EvtVnd1'] = a
            params['EvtVnd2'] = a
            params['EvtVnd3'] = a
            params['EvtVnd4'] = a

        except Exception as e:
            raise der.DERError(str(e))

        return params

