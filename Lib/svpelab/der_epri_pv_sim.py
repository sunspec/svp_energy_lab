"""
Copyright (c) 2018, Sandia National Labs and SunSpec Alliance
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
import math

try:
    import requests
except Exception as e:
    print('Missing requests package')
try:
    import json
except Exception as e:
    print('Missing json package')
try:
    import urllib.request, urllib.error, urllib.parse
except Exception as e:
    print('Missing urllib2 package')
epri_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'EPRI'
}

def der_info():
    return epri_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = epri_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    # TCP parameters
    info.param(pname('ipaddr'), label='IP Address', default='http://10.1.2.2')
    info.param(pname('ipport'), label='IP Port', default=8000)
    info.param(pname('ipaddr_reads'), label='IP Address Data Stream', default='http://localhost')
    info.param(pname('ipport_reads'), label='IP Port Data Stream', default=8081)
    info.param(pname('mRID'), label='Inverter ID', default='03ac0d62-2d29-49ad-915e-15b9fbd46d86')
    # a3bbf028-ff09-4185-95ea-4c6dfea23d8c
    # 22261658-4c34-41ec-ab51-6a794bb47d37

GROUP_NAME = 'epri'


class DER(der.DER):

    def __init__(self, ts, group_name):
        der.DER.__init__(self, ts, group_name)
        self.headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        self.connection = None
        self.mrid = self.param_value('mRID')

        # Setup client for writing to EPRI inverter
        ipaddr = self.param_value('ipaddr')
        ipport = self.param_value('ipport')
        self.address = '%s:%s' % (ipaddr, ipport)

        # Configure client connection to server for monitoring points
        server_ipaddr = self.param_value('ipaddr_reads')
        server_ipport = self.param_value('ipport_reads')
        self.server_address = '%s:%s' % (server_ipaddr, server_ipport)

    def param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):
        self.open()

    def open(self):
        # Start communications between DERMS and EPRI PV Sim
        comm_start_cmd = {
            "namespace": "comms",
            "function": "startCommunication",
            "requestId": "requestId",
            "parameters": {
                "deviceIds": [self.mrid]
            }
        }

        r = requests.post(self.address, json=comm_start_cmd)
        self.ts.log_debug('Communication established to PDA. Data Posted! '
                          'statusMessage: %s' % r.json()['statusMessage'])

    def close(self):
        if self.connection is not None:
            self.connection.close()

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
            params['Manufacturer'] = 'EPRI'
            params['Model'] = "PV Simulator"
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def measurements(self):
        """ Get measurement data.

        Params:

        :return: Dictionary of measurement data.
        """

        try:
            params = {}
            req = urllib.request.Request(self.server_address)
            resp = urllib.request.urlopen(req, timeout=0.5)
            r = resp.read()
            if len(r) > 0:
                data = json.loads(r)
                # self.ts.log_debug(data)
                params['W'] = data.get(self.mrid).get('Watts')
                params['Hz'] = data.get(self.mrid).get('F')
                params['VAr'] = data.get(self.mrid).get('Vars')
                params['PF'] = data.get(self.mrid).get('PF')
                params['PhVphA'] = data.get(self.mrid).get('VphAN')
                try:
                    params['VA'] = math.sqrt(params['W']**2 + params['VAr']**2)
                    # self.ts.log_debug('%s Watts, %s Vars, %s VA' % (params['W'], params['VAr'], params['VA']))
                except Exception as e:
                    params['VA'] = None
        except Exception as e:
            raise der.DERError(str(e))

        return params

    def fixed_pf(self, params=None):
        """ Get/set fixed power factor control settings.

        Params:
            Ena - Enabled (True/False)
            PF - Power Factor set point
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for fixed factor.
        """
        if params is not None:
            pf = params.get('PF')
            if pf is None:
                pf = 1.0
                var_action = "reverseProducingVars"
            else:
                if pf < 0:  # negative pf indicates the the inverter is injecting vars (EEI/SunSpec Sign Convention)
                    var_action = "doNotreverseProducingVars"
                else:
                    var_action = "reverseProducingVars"

            win_tms = params.get('WinTms')
            if win_tms is None:
                win_tms = 0.0
            rmp_tms = params.get('RmpTms')
            if rmp_tms is None:
                rmp_tms = 0.0
            rvrt_tms = params.get('RvrtTms')
            if rvrt_tms is None:
                rvrt_tms = 0.0

            # Field	           Data Type	    Description
            # namespace	       String	        Namespace will be "der" for all device level messages to the PDA
            # function	       String	        Function name will be "configurePowerFactor" to enable the power
            #                                   factorfunction in the inverter
            # requestId	       String	        RequestId will be a unique identifier for each request. Request IDs
            #                                   can be used by RT-OPF to track the status of the request. Response
            #                                   from PDA will contain the request ID of the corresponding request.
            # deviceIds	       Array of strings	Array containing the mRIDs of the devices
            # timeWindow	   Integer	        Time in seconds, over which a new setting is to take effect
            # reversionTimeout Integer	        Time in seconds, after which the function is disabled
            # rampTime	       Integer	        Time in seconds, over which the DER linearly places the new limit into
            #                                   effect
            # powerFactor	   number	        Sets the power factor of the inverter. Value must be between -1.0 and
            #                                   +1.0
            # varAction        String           Specifies whether the PF setting is leading or lagging. The value
            #                                   must be "reverseProducingVars" to absorb VARs and
            #                                   "doNotreverseProducingVars" to produce VARs
            pf_cmd = {"namespace": "der",
                      "function": "configurePowerFactor",
                      "requestId": "requestId",
                      "parameters": {
                            "deviceIds": [self.mrid],
                            "timeWindow": win_tms,
                            "reversionTimeout": rvrt_tms,
                            "rampTime": rmp_tms,
                            "powerFactor": pf,
                            "varAction": var_action
                            }
                      }

            # self.ts.log_debug('Setting new PF...')
            r = requests.post(self.address, json=pf_cmd)
            # self.ts.log_debug('Data Posted! statusMessage: %s' % r.json()['statusMessage'])

            ena = params.get('Ena')
            if ena is None:
                ena = False
            # Field	           Data Type	    Description
            # enable           Boolean          Enable key will be set to true in order to enable the function
            #                                   and false to disable the power factor function
            pf_enable_cmd = {"namespace": "der",
                             "function": "powerFactor",
                             "requestId": "requestId",
                             "parameters": {
                                   "deviceIds": [self.mrid],
                                   "enable": ena
                                   }
                             }

            # self.ts.log_debug('Enabling new PF...')
            r = requests.post(self.address, json=pf_enable_cmd)
            # self.ts.log_debug('Data Posted! statusMessage: %s' % r.json()['statusMessage'])

        else:  # read PF data
            params = {'Ena': None, 'PF': None, 'WinTms': None, 'RmpTms': None, 'RvrtTms': None}

        return params

    def limit_max_power(self, params=None):
        """ Get/set max active power control settings.

        Params:
            Ena - Enabled (True/False)
            WMaxPct - Active power maximum as percentage of WMax
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for limit max power.
        """
        pass

    def volt_var(self, params=None):
        """ Get/set volt/var control

        Params:
            Ena - Enabled (True/False)
            ActCrv - Active curve number (0 - no active curve)
            NCrv - Number of curves supported
            NPt - Number of points supported per curve
            WinTms - Randomized start time delay in seconds
            RmpTms - Ramp time in seconds to updated output level
            RvrtTms - Reversion time in seconds

        :param params: Dictionary of parameters to be updated.
        :return: Dictionary of active settings for volt/var control.
        """
        pass

if __name__ == "__main__":

    import os
    import http.client
    import json
    import requests

    headers = {'Content-type': 'application/json'}

    comm_start_cmd = {
        "namespace": "comms",
        "function": "startCommunication",
        "requestId": "requestId",
        "parameters": {
            "deviceIds": ['03ac0d62-2d29-49ad-915e-15b9fbd46d86', ]
        }
    }

    response = requests.post('http://localhost:8000', json=comm_start_cmd)
    print(('Data Posted! statusMessage: %s' % response.json()['statusMessage']))

    pf_cmd = {"namespace": "der",
              "function": "configurePowerFactor",
              "requestId": "requestId",
              "parameters": {
                  "deviceIds": ["03ac0d62-2d29-49ad-915e-15b9fbd46d86"],
                  "timeWindow": 0,
                  "reversionTimeout": 0,
                  "rampTime": 0,
                  "powerFactor": 0.85,
                  "varAction": "reverseProducingVars"
              }
              }

    print('Setting new PF...')
    response = requests.post('http://localhost:8000', json=pf_cmd)
    print(('Data Posted! statusMessage: %s' % response.json()['statusMessage']))

    pf_enable_cmd = {"namespace": "der",
                     "function": "powerFactor",
                     "requestId": "requestId",
                     "parameters": {
                         "deviceIds": ["03ac0d62-2d29-49ad-915e-15b9fbd46d86"],
                         "enable": True
                     }
                     }

    print('Enabling new PF...')
    response = requests.post('http://localhost:8000', json=pf_enable_cmd)
    print(('Data Posted! statusMessage: %s' % response.json()['statusMessage']))

