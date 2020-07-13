''' This code sits in the svpdnp3 lib of the SVP Directory.
    The script defines different methods that can be called by the
    SVP scripts to send requests to the DNP3 Agent.
'''

import socket
import json
import logging
import sys
import subprocess
import os
from os import path

''' agent API definitions '''

STXB = b'\x02'
ETXB = b'\x03'
STX = STXB[0]
ETX = ETXB[0]

OP_READ = 'read'
OP_WRITE = 'write'
OP_STATUS = 'status'
OP_ADD = 'add'
OP_SCAN = 'scan'
OP_DEL = 'delete'
OP_STOP = 'stop'

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)

class AgentClient():

    ''' This class creates a TCP Client which sends requests
        to the TCP server in the DNP3 Agent. The request is a
        JSON encoded object of the format:

        request_body = {'oid': oid,
                        'op': op,
                        'rid': rid,
                        'params': params}
    '''

    def __init__(self, ip_addr=None, ip_port=None):
        self.ip_addr = ip_addr
        self.ip_port = ip_port
        self.socket = None

    def connect(self, ip_addr=None, ip_port=None):
        if ip_addr is not None:
            self.ip_addr = ip_addr
        if ip_port is not None:
            self.ip_port = ip_port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip_addr, self.ip_port))

    def status(self, rid=None):
        ''' Request to return the status for agent and each active outstation '''

        resp = self.request(op=OP_STATUS, rid=rid)

        return resp

    def stop_agent(self, rid=None):
        ''' Request to stop the agent from listening further requests '''

        resp = self.request(op=OP_STOP, rid=rid)

        return resp

    def add_outstation(self, ipaddr=None, ipport=None, outstation_addr=None, master_addr=None):
        ''' Request to add an outstation with the given configuration '''

        params = {'ipaddr': ipaddr,
                  'ipport': ipport,
                  'outstation_addr': outstation_addr,
                  'master_addr': master_addr}
        resp = self.request(op=OP_ADD, params=params)

        return resp

    def read_outstation(self, oid, rid=None, points=None):
        ''' Request to read the points from an outstation with the given oid '''

        params = {'points': points}
        resp = self.request(oid=oid, op=OP_READ, rid=rid, params=params)

        return resp

    def write_outstation(self, oid, rid=None, points=None):
        ''' Request to write data points of the outstation with the given oid '''

        params = {'points': points}
        resp = self.request(oid=oid, op=OP_WRITE, rid=rid, params=params)

        return resp

    def scan_outstation(self, oid, rid=None, scan_type=None):
        ''' Request to perform a specific scan on an outstation with the given oid '''

        params = {'scan_type': scan_type}
        resp = self.request(oid=oid, op=OP_SCAN, rid=rid, params=params)

        return resp

    def delete_outstation(self, oid, rid=None):
        ''' Request to delete the outstation with the given oid '''

        params = {}
        resp = self.request(oid=oid, op=OP_DEL, rid=rid, params=params)

        return resp

    def request(self, oid=None, op=OP_READ, rid=None, params=None):
        ''' This method creates the request and sends it to the agent '''

        req = {'oid': oid,
               'op': op,
               'rid': rid,
               'params': params}

        req_msg = b''.join([STXB, json.dumps(req).encode(), ETXB])

        if self.socket:
            self.socket.send(req_msg)

            data = self.socket.recv(32768)
            print(('%s: received "%s"' % (self.socket.getsockname(), data)))

        return data