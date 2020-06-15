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
from . import dcsim
from . import loadsim
from . import battsim

# This drive creates a battery simulator from a dc electronic load and dc power supply

dc_load_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'DC Load and Power Supply'
}


def battsim_info():
    return dc_load_info


def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = dc_load_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)

    # DC Load
    loadsim.params(info, group_name=group_name, active=gname('mode'), active_value=mode)

    # DC Power Supply
    dcsim.params(info, group_name=group_name, active=gname('mode'), active_value=mode)

GROUP_NAME = 'dc_load'


class BattSim(battsim.BattSim):

    def __init__(self, ts, group_name):
        battsim.BattSim.__init__(self, ts, group_name)

        # init the load simulator
        self.loadsim = loadsim.loadsim_init(ts, group_name=group_name)

        # init the DC power supply
        self.dcsim = loadsim.loadsim_init(ts, group_name=group_name)

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def info(self):
        """
        Return information string for the device.
        """
        load_str = self.loadsim.info()
        dc_str = self.dcsim.info()
        return 'Battery simulator consisting of ' + load_str + ' and ' + dc_str

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        self.loadsim.config()
        self.dcsim.config()

    def open(self):
        """
        Open the communications resources associated with the battery simulator.
        """
        self.loadsim.open()
        self.dcsim.open()

    def close(self):
        """
        Close any open communications resources associated with the battery simulator.
        """
        self.loadsim.close()
        self.dcsim.close()
