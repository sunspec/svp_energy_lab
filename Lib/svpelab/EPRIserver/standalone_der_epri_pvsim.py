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
import http.client
import json
import requests
import http.server
import socketserver


def client_tests():

    # Client tests
    headers = {'Content-type': 'application/json'}

    comm_start_cmd = {
        "namespace": "comms",
        "function": "startCommunication",
        "requestId": "requestId",
        "parameters": {
            "deviceIds": ['03ac0d62-2d29-49ad-915e-15b9fbd46d86',]
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


if __name__ == "__main__":

    from http.server import BaseHTTPRequestHandler, HTTPServer
    PORT_NUMBER = 8081

    comm_start_cmd = {
        "namespace": "comms",
        "function": "startCommunication",
        "requestId": "requestId",
        "parameters": {
            "deviceIds": ['03ac0d62-2d29-49ad-915e-15b9fbd46d86', '22261658-4c34-41ec-ab51-6a794bb47d37',
                          'a3bbf028-ff09-4185-95ea-4c6dfea23d8c']
        }
    }

    response = requests.post('http://10.1.2.2:8000', json=comm_start_cmd)
    print(('Data Posted! statusMessage: %s' % response.json()['statusMessage']))

    server_values = {'03ac0d62-2d29-49ad-915e-15b9fbd46d86': {'Watts': None, 'Vars': None, 'SOC': None, 'W_set': None,
                                                              'W_discharge': None, 'VV_V': None, 'VV_Q': None,
                                                              'F': None, 'VphAN': None, 'PF': None, 'W_DC': None},
                     '22261658-4c34-41ec-ab51-6a794bb47d37': {'Watts': None, 'Vars': None, 'SOC': None, 'W_set': None,
                                                              'W_discharge': None, 'VV_V': None, 'VV_Q': None,
                                                              'F': None, 'VphAN': None, 'PF': None, 'W_DC': None},
                     'a3bbf028-ff09-4185-95ea-4c6dfea23d8c': {'Watts': None, 'Vars': None, 'SOC': None, 'W_set': None,
                                                              'W_discharge': None, 'VV_V': None, 'VV_Q': None,
                                                              'F': None, 'VphAN': None, 'PF': None, 'W_DC': None}}

    class myHandler(BaseHTTPRequestHandler):

        # Handler for the GET requests
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(server_values))
            # print 'Get complete'
            return

        def log_message(self, format, *args):
            return

        # Handler for the POST requests
        def do_POST(self):
            request_headers = self.headers
            content_length = request_headers.getheaders('content-length')
            length = int(content_length[0]) if content_length else 0

            data = self.rfile.read(length)
            data_dict = json.loads(data)
            # print(data_dict)

            try:
                inverter_id = data_dict['parameters']['deviceId']

                # Get power
                try:
                    if data_dict['parameters']['dataPointId'] == '5f2c5fa3-de91-4a61-9856-efbc5067ab29':
                        server_values[inverter_id]['Watts'] = data_dict['parameters']['value']
                except Exception as e:
                    print(('Error: %s' % e))

                # Get reactive power
                try:
                    if data_dict['parameters']['dataPointId'] == 'c11f25be-8f4c-460d-9e9e-e862eea0e7c4':
                        server_values[inverter_id]['Vars'] = data_dict['parameters']['value']
                        # if inverter_id == '03ac0d62-2d29-49ad-915e-15b9fbd46d86':
                        #     print('Inverter %s has %s VAr' % (inverter_id, server_values[inverter_id]['Vars']))
                except Exception as e:
                    print(('Error: %s' % e))

                # Get charge level
                try:
                    if data_dict['parameters']['dataPointId'] == '038ddc37-6e3d-4ab3-9ae8-23e88f196841':
                        server_values[inverter_id]['SOC'] = data_dict['parameters']['value']
                except Exception as e:
                    print(('Error: %s' % e))

                # Get active power setpoint
                try:
                    if data_dict['parameters']['dataPointId'] == '6d990f64-a07d-4d5d-990f-c0a416fd574a':
                        server_values[inverter_id]['W_set'] = data_dict['parameters']['value']
                except Exception as e:
                    print(('Error: %s' % e))

                # Get discharge setpoint
                try:
                    if data_dict['parameters']['dataPointId'] == '9da0712c-a979-4d2a-8412-99057d275c39':
                        server_values[inverter_id]['W_discharge'] = data_dict['parameters']['value']
                except Exception as e:
                    print(('Error: %s' % e))

                # Get VV V points
                try:
                    if data_dict['parameters']['dataPointId'] == '26258083-ae18-479c-8461-51f8cf218b94':
                        server_values[inverter_id]['VV_V'] = data_dict['parameters']['value']
                except Exception as e:
                    print(('Error: %s' % e))

                # Get VV Q points
                try:
                    if data_dict['parameters']['dataPointId'] == '09b4c134-a96c-4177-88a8-3baa634a86ec':
                        server_values[inverter_id]['VV_Q'] = data_dict['parameters']['value']
                except Exception as e:
                    print(('Error: %s' % e))

                # Get frequency
                try:
                    if data_dict['parameters']['dataPointId'] == 'f5cc27dd-df4a-4c8f-960c-9c8a1c73dbe6':
                        server_values[inverter_id]['F'] = data_dict['parameters']['value']
                except Exception as e:
                    print(('Error: %s' % e))

                # Get Voltage A-N
                try:
                    if data_dict['parameters']['dataPointId'] == '508efa72-c054-4995-a411-5b9d306f727b':
                        server_values[inverter_id]['VphAN'] = data_dict['parameters']['value']
                except Exception as e:
                    print(('Error: %s' % e))

                # Get PF
                try:
                    if data_dict['parameters']['dataPointId'] == '4096bbda-23d3-4f8e-8625-d800266ceba0':
                        server_values[inverter_id]['PF'] = data_dict['parameters']['value']
                except Exception as e:
                    print(('Error: %s' % e))

                # Get DC Power
                try:
                    if data_dict['parameters']['dataPointId'] == 'c23b52fd-8dce-4a46-9480-61705534496a':
                        server_values[inverter_id]['W_DC'] = data_dict['parameters']['value']
                except Exception as e:
                    print(('Error: %s' % e))

            except Exception as e:
                print(('No inverter ID: %s....Data Dictionary: %s' % (e, data_dict)))

            self.send_response(200)
            self.end_headers()
            return

    try:
        # Create a web server and define the handler to manage the incoming request
        server = HTTPServer(('', PORT_NUMBER), myHandler)
        print('Started httpserver on port ', PORT_NUMBER)

        # Wait forever for incoming http requests
        server.serve_forever()

        print('THE SERVER DIED')

    except KeyboardInterrupt:
        print('^C received, shutting down the web server')
        server.socket.close()

