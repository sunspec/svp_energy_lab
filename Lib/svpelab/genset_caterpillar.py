"""
Copyright (c) 2018, Sandia National Laboratories
All rights reserved.

V1.0 - Jay Johnson - 7/31/2018
"""

import os
from . import der

manual_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Catepillar'
}

def genset_info():
    return cat_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = manual_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    # TCP parameters
    info.param(pname('ipaddr'), label='IP Address', default='192.168.0.170')
    info.param(pname('ipport'), label='IP Port', default=502)
    info.param(pname('slave_id'), label='Slave Id', default=1)

GROUP_NAME = 'cat'


class Genset(genset.Genset):

    def __init__(self, ts, group_name):
        das.DAS.__init__(self, ts, group_name)
        self.sample_interval = self._param_value('sample_interval')
        self.params['node'] = self._param_value('node')
        self.params['sample_interval'] = self._param_value('sample_interval')
        self.params['sample_rate'] = self._param_value('sample_rate')
        self.params['n_cycles'] = self._param_value('n_cycles')
        self.params['ts'] = ts

        self.device = device_genset_caterpillar.Device(self.params, ts)
        self.data_points = self.device.data_points

        # initialize soft channel points
        self._init_sc_points()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)


if __name__ == "__main__":

    pass

