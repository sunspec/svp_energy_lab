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

import sys
import os
import glob
import importlib
import chroma_17040

# Import all battsim extensions in current directory.
# A battsim extension has a file name of battsim_*.py and contains a function battsim_params(info) that contains
# a dict with the following entries: name, init_func.

# dict of modules found, entries are: name : module_name
chroma_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Chroma'
}

battsim_modules = {}

def battsim_info():
    return chroma_info

GROUP_NAME = 'Chroma'



#def params(info, id=None, label='Battery Simulator', group_name=None, active=None, active_value=None):
def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = chroma_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
                     
    info.param(pname('comm'), label='Communications Interface', default='VISA',
               values=['Serial', 'GPIB', 'VISA'])
    info.param(pname('visa_device'), label='VISA Device String', active=pname('comm'),
               active_value=['VISA'], default='TCPIP::192.168.1.100::60000::SOCKET', width='40')   #wanbin
    #info.param_group('INIT', label='Initial Condition', glob=True)
    info.param(pname('CAP'), label='Battery Capacity (Ah)', default=100)
    info.param(pname('INIT_SOC'), label='Initial SOC (%)', default=50)
    info.param(pname('SOC'), label='SOC Step(%)', default='100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0')
    info.param(pname('OCV'), label='OCV at SOC (V)', default='41.1,40,39.1,38.3,37.6,36.9,36.6,36.3,35.9,35,33.8')
    info.param(pname('DCR_D'), label='Discharge DC internal resistance at SOC (Ohm)', default='0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.1')
    info.param(pname('DCR_C'), label='Charge DC internal resistance at SOC (Ohm)', default='0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.1')
    info.param(pname('ESR'), label='DC internal resistance', default=0.001)
    info.param(pname('BVL'), label='Low Voltage Alarm (V)', default=10)
    info.param(pname('VOLP'), label='Low Voltage Protection (V)', default=5)
    info.param(pname('BVH'), label='High Voltage Alarm (V)', default=35)
    info.param(pname('VOH'), label='High Voltage Protection (V)', default=40.1)
    
    
    #DC internal resistance
    
    

RELAY_OPEN = 'open'
RELAY_CLOSED = 'closed'
RELAY_UNKNOWN = 'unknown'


class BattSimError(Exception):
    """
    Exception to wrap all battery simulator generated exceptions.
    """
    pass


class BattSim(object):
    """
    Template for battery simulator implementations. This class can be used as a base class or
    independent battery simulator classes can be created containing the methods contained in this class.
    """

    def _param_value(self, name):	#wanbin # from pvsim_terrasas.py
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)


    def __init__(self, ts, group_name, params=None):
        self.ts = ts
        self.group_name = group_name
        self.params = params
        if self.params is None:
            self.params = {}
        self.auto_config = self._group_param_value('auto_config')

        self.visa_device = self._param_value('visa_device')
        self.cap=self._param_value('CAP')
        self.init_soc=self._param_value('INIT_SOC')
        self.soc=self._param_value('SOC')
        self.ocv=self._param_value('OCV')
        self.dcr_d=self._param_value('DCR_D')
        self.dcr_c=self._param_value('DCR_C')
        self.esr=self._param_value('ESR')
        self.bvl=self._param_value('BVL')
        self.volp=self._param_value('VOLP')
        self.bvh=self._param_value('BVH')
        self.voh=self._param_value('VOH')
        
        self.dev=chroma_17040.ChromaBattSim(self.ts,self.visa_device)
        

    def _group_param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + name)

    def info(self):
        """
        Return information string for the device.
        """
        pass

    def config(self):
        """
        Perform any configuration for the simulation based on the previously
        provided parameters.
        """
        pass

    def open(self):       
        """
        Open the communications resources associated with the battery simulator.
        """
        self.dev.open()
        self.dev.protection_clear()
        self.dev.set_capacity(self.cap)
        soc=self.soc.split(",")
        soc=[float(item) for item in soc]
        ocv=self.ocv.split(",")
        ocv=[float(item) for item in ocv]
        dcr_d=self.dcr_d.split(",")
        dcr_d=[float(item) for item in dcr_d]
        dcr_c=self.dcr_c.split(",")
        dcr_c=[float(item) for item in dcr_c]
        self.dev.set_curve(soc,ocv,dcr_d,dcr_c)
        self.dev.set_init_soc(self.init_soc)
        self.dev.set_volt_alarm(self.bvl, self.bvh)
        self.dev.set_volt_protection(self.volp, self.voh)
        self.dev.set_esr(self.esr)
        self.dev.set_efficiency(99,99)
        self.dev.set_current_protection(100)
        

    def power_on(self):
        self.dev.power_on()
        
    def power_off(self):
        self.dev.power_off()


    def close(self):
        """
        Close any open communications resources associated with the battery simulator.
        """
        pass

    def get_volt(self):
        return self.dev.get_volt()

    def is_error(self):
        return self.dev.is_error()

if __name__ == "__main__":
    pass
