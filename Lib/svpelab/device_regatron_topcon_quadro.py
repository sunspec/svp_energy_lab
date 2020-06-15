"""
Regatron driver developed by ZHAW and SNL
"""

import sys
import time
import socket

class RegatronError(Exception):
    pass

class Regatron(object):

    def __init__(self, ipaddr='10.0.0.4', ipport=771, timeout=5):
        self.ipaddr = ipaddr
        self.ipport = ipport
        self.timeout = timeout
        self.buffer_size = 1024
        self.conn = None

    def _cmd(self, cmd_str):
        try:
            print('Trying to send command in _cmd')
            if self.conn is None:
                self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.conn.settimeout(self.timeout)
                self.conn.connect((self.ipaddr, self.ipport))

            # print('cmd> %s' % (cmd_str))
            self.conn.send(cmd_str)
        except Exception as e:
            raise

    def _query(self, cmd_str):
        print('Getting response to query in _query')
        resp = ''
        more_data = True

        self._cmd(cmd_str)

        while more_data:
            try:
                data = self.conn.recv(self.buffer_size)
                if len(data) > 0:
                    for d in data:
                        resp += d
                        if d == '\r':
                            more_data = False
                            break
            except Exception as e:
                raise RegatronError('Timeout waiting for response')

        return resp

    def cmd(self, cmd_str):
        try:
            self._cmd(cmd_str)
            resp = self._query('SYSTem:ERRor?\r')
            if len(resp) > 0:
                if resp[0] != '0':
                    raise RegatronError(resp)
        except Exception as e:
            raise RegatronError(str(e))

    def query(self, cmd_str):
        try:
            resp = self._query(cmd_str).strip()
        except Exception as e:
            raise RegatronError(str(e))
        finally:
            self.close()

        return resp

    def info(self):
        return self.query('*IDN?\r')

    def reset(self):
        self.cmd('*RST\r')

    def irradiance_set(self, irradiance=1000):
        pass

    def output_set_off(self):
        pass

    def output_set_on(self):
        pass

    def profile_load(self, profile_name):
        # use pv_profiles.py to generate time vs irradiance/power profiles
        pass

    def profile_start(self):
        pass

    def close(self):
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception as e:
            pass
        finally:
            self.conn = None


if __name__ == "__main__":

    # Instantiate regatron object
    reg = Regatron(ipaddr='10.0.0.4', ipport=771, timeout=5)

    # test the information method
    print((reg.info()))

    # close the connection to the regatron
    reg.close()



