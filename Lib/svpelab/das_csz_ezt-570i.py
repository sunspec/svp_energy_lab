"""
Copyright (c) 2021, Sandia National Laboratories
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

# Driver for Cincinnati Sub-Zero (CSZ) EZT-570i Environmental Chamber Controller
# This uses the web server to scrape data.

import os
import urllib3
from bs4 import BeautifulSoup as soup
import re
import pprint
from collections import OrderedDict
import time

try:
    from . import das
except Exception as e:
    print('Could not import das abstraction layer')

csz_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'CSZ EZT-570i'
}

def das_info():
    return csz_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = csz_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('comm'), label='Communications Interface', default='Web',
               values=['Web', 'Modbus (unimplemented)', 'GPIB (unimplemented)'])
    info.param(pname('ip_addr'), label='IP Address',
               active=pname('comm'),  active_value=['Web'], default='10.1.2.52')
    info.param(pname('ip_port'), label='IP Port',
               active=pname('comm'),  active_value=['Web'], default=80)
    info.param(pname('sample_interval'), label='Sample Interval (ms)', default=1000)


GROUP_NAME = 'csz'


class DAS(das.DAS):
    """
    Template for data acquisition (DAS) implementations. This class can be used as a base class or
    independent data acquisition classes can be created containing the methods contained in this class.
    """

    def __init__(self, ts, group_name, points=None, sc_points=None, support_interfaces=None):
        das.DAS.__init__(self, ts, group_name, points=points, sc_points=sc_points, support_interfaces=None)
        self.sample_interval = self._param_value('sample_interval')
        self.params['comm'] = self._param_value('comm')
        self.params['ip_addr'] = self._param_value('ip_addr')
        self.params['ip_port'] = self._param_value('ip_port')
        self.params['sample_interval'] = self._param_value('sample_interval')
        self.params['ts'] = ts
        self.device = Device(self.params)
        self.data_points = self.device.data_points

        if self.params['sample_interval'] < 50 and self.params['sample_interval'] is not 0:
            raise das.DASError('Parameter error: sample interval must be at least 50 ms or 0 for manual sampling')

        # initialize soft channel points
        self._init_sc_points()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)


class DeviceError(Exception):
    """
    Exception to wrap all das generated exceptions.
    """
    pass


class Device(object):

    def __init__(self, params):
        self.params = params
        self.conn = params.get('conn')
        self.ip_addr = params.get('ip_addr')
        self.ip_port = params.get('ip_port')
        self.ts = params.get('ts')
        self.sample_interval = params.get('sample_interval')
        self.data_points = ['TIME', 'TEMP', 'TEMP_SETPOINT', 'HUMIDITY', 'HUMIDITY_SETPOINT',
                            'PRODUCT', 'PRODUCT_SETPOINT', 'PROFILE_STATUS', 'PROFILE_START', 'PROFILE_END_ESTIMATE',
                            'PROFILE_CURRENT_STEP', 'PROFILE_STEP_TIME_LEFT', 'PROFILE_WAIT_FOR_INPUT',
                            'PROFILE_WAIT_SETPOINT', 'PROFILE_TEMP_SETPOINT', 'PROFILE_HUMIDITY_SETPOINT',
                            'PROFILE_PRODUCT_SETPOINT']

    def open(self):
        pass

    def close(self):
        pass

    def info(self):
        return 'Cincinnati Sub-Zero (CSZ) EZT-570i Environmental Chamber Controller'

    def data_capture(self, enable=True):
        pass

    def data_read(self):

        http = urllib3.PoolManager()
        url = 'http://%s:%s/ezt.html' % (self.ip_addr, self.ip_port)
        r = http.request('GET', url, preload_content=False)
        r.release_conn()
        # if self.ts is not None:
        #     self.ts.log(r.data)
        # else:
        #     print(r.data)

        # html parsing
        page_soup = soup(r.data, "html.parser")
        # print(page_soup.prettify())

        page_items = []
        for link in page_soup.find_all("td"):
            # print("Inner Text: {}".format(link.text))
            page_items.append(format(link.text).lstrip('\n\r'))

        # dict with measurement name and value
        datadict = OrderedDict({
            'time': time.time(),
            'temp': float(re.search(r"[+-]?\d+(?:\.\d+)?", page_items[1]).group()),
            'temp_setpoint': float(re.search(r"[+-]?\d+(?:\.\d+)?", page_items[2]).group()),
            'humidity': float(re.search(r"[+-]?\d+(?:\.\d+)?", page_items[4]).group()),
            'humidity_setpoint': float(re.search(r"[+-]?\d+(?:\.\d+)?", page_items[5]).group()),
            'product': float(re.search(r"[+-]?\d+(?:\.\d+)?", page_items[7]).group()),
            'product_setpoint': float(re.search(r"[+-]?\d+(?:\.\d+)?", page_items[8]).group()),
            'profile_status': page_items[10],
            'profile_start': page_items[12],
            'profile_end_estimate': page_items[14],
            'profile_current_step': page_items[16],
            'profile_step_time_left': page_items[18],
            'profile_wait_for_input': page_items[20],
            'profile_wait_setpoint': page_items[22],
            'profile_temp_setpoint': page_items[24],
            'profile_humidity_setpoint': page_items[26],
            'profile_product_setpoint': page_items[28],
        })

        data = []
        for key, value in datadict.items():
            data.append(value)

        # self.ts.log_debug('Data:%s' % data)
        # self.ts.log_debug('Data Points:%s' % self.data_points)
        return data

    def capture(self, enable=None):
        """
        Enable/disable capture.
        """
        pass


if __name__ == "__main__":

    local_url = r'http://localhost:8000/ThermalChamber2.html'

    http = urllib3.PoolManager()
    r = http.request('GET', local_url, preload_content=False)
    r.release_conn()
    print(r.data)

    # html parsing
    page_soup = soup(r.data, "html.parser")
    # data = open(local_url, "r").read()
    # page_soup = soup(data, "html.parser")
    # print(page_soup.prettify())

    page_items = []
    for link in page_soup.find_all("td"):
        # print("Inner Text: {}".format(link.text))
        page_items.append(format(link.text).lstrip('\n\r'))

    for i in range(len(page_items)):
        print('%s: %s' % (i, page_items[i]))

    # dict with measurement name and value
    data = OrderedDict({
        'temp': float(re.search(r"[+-]?\d+(?:\.\d+)?", page_items[1]).group()),
        'temp_setpoint': float(re.search(r"[+-]?\d+(?:\.\d+)?", page_items[2]).group()),
        'humidity': float(re.search(r"[+-]?\d+(?:\.\d+)?", page_items[4]).group()),
        'humidity_setpoint': float(re.search(r"[+-]?\d+(?:\.\d+)?", page_items[5]).group()),
        'product': float(re.search(r"[+-]?\d+(?:\.\d+)?", page_items[7]).group()),
        'product_setpoint': float(re.search(r"[+-]?\d+(?:\.\d+)?", page_items[8]).group()),
        'profile_status': page_items[10],
        'profile_start': page_items[12],
        'profile_end_estimate': page_items[14],
        'profile_current_step': page_items[16],
        'profile_step_time_left': page_items[18],
        'profile_wait_for_input': page_items[20],
        'profile_wait_setpoint': page_items[22],
        'profile_temp_setpoint': page_items[24],
        'profile_humidity_setpoint': page_items[26],
        'profile_product_setpoint': page_items[28],
    })

    pprint.pprint(data)

