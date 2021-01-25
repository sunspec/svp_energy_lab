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

pvsim_modules = {}

def params(info, id=None, label='PV Simulator', group_name=None, active=None, active_value=None):
    if group_name is None:
        group_name = PVSIM_DEFAULT_ID
    else:
        group_name += '.' + PVSIM_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    name = lambda name: group_name + '.' + name
    info.param_group(group_name, label='%s Parameters' % label, active=active, active_value=active_value, glob=True)
    info.param(name('mode'), label='Mode', default='Disabled', values=['Disabled'])
    for mode, m in pvsim_modules.items():
        m.params(info, group_name=group_name)

PVSIM_DEFAULT_ID = 'pvsim'

def pvsim_init(ts, id=None, group_name=None,support_interfaces=None):
    """
    Function to create specific pv simulator implementation instances.

    Each supported pv simulator type should have an entry in the 'mode' parameter conditional.
    Module import for the simulator is done within the conditional so modules only need to be
    present if used.
    """
    if group_name is None:
        group_name = PVSIM_DEFAULT_ID
    else:
        group_name += '.' + PVSIM_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    mode = ts.param_value(group_name + '.' + 'mode')
    sim = None
    if mode != 'Disabled':
        sim_module = pvsim_modules.get(mode)
        if sim_module is not None:
            sim = sim_module.PVSim(ts, group_name,support_interfaces=support_interfaces)
        else:
            raise PVSimError('Unknown PV simulation mode: %s' % mode)

    return sim


class PVSimError(Exception):
    pass

class PVSim(object):

    def __init__(self, ts, group_name, params=None, support_interfaces=None):
        self.ts = ts
        self.group_name = group_name
        self.params = params
        self.hil = None
        if support_interfaces is not None:
            if support_interfaces.get('hil') is not None:
                self.hil = support_interfaces.get('hil')

    def close(self):
        """
        Close the communication connection to the PVSim

        :return: None
        """
        pass

    def info(self):
        """
        Get the type of PVSim.  Typically this is done with a *IDN? command.

        :return: string of the information from the device
        """
        pass

    def irradiance_set(self, irradiance=1000):
        """
        Set irradiance level for the PVSim channels (individual power supplies that produce the I-V curves)

        :return: None
        """
        pass

    def iv_curve_config(self, pmp, vmp):
        """
        Configure the I-V curves on the channels (individual power supplies that produce the I-V curves)

        Typically this is done using the EN50530 standard.  Pointwise EN50530 curves can be created using
        pv_curve_generation.py if the PV simulator cannot generate the EN50530 curve directly

        :param pmp: Maximum Power Point (MPP) Power in watts
        :param vmp: Maximum Power Point (MPP) Voltage in volts
        :return: None
        """
        pass

    def power_set(self, power):
        """
        Set the maximum power of the I-V curve by adjusting the irradiance on the PVSim channels (or some other means)

        :param power: maximum power in watts
        :return: None
        """
        pass

    def profile_load(self, profile_name):
        """
        Rarely used function to load an irradiance vs time profile

        :param profile_name: a string with the pv_profiles.py profile that is being used for the irradiance vs time
        :return: None
        """
        pass

    def power_on(self):
        """
        Energizes the output of the PVSimulator

        :return: None
        """
        pass

    def profile_start(self):
        """
        Starts the profile that was loaded in profile_load()

        :return: None
        """
        pass


def pvsim_scan():
    global pvsim_modules
    # scan all files in current directory that match gridsim_*.py
    package_name = '.'.join(__name__.split('.')[:-1])
    files = glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pvsim_*.py'))
    for f in files:
        module_name = None
        try:
            module_name = os.path.splitext(os.path.basename(f))[0]
            if package_name:
                module_name = package_name + '.' + module_name
            m = importlib.import_module(module_name)
            if hasattr(m, 'pvsim_info'):
                info = m.pvsim_info()
                mode = info.get('mode')
                # place module in module dict
                if mode is not None:
                    pvsim_modules[mode] = m
            else:
                if module_name is not None and module_name in sys.modules:
                    del sys.modules[module_name]
        except Exception as e:
            if module_name is not None and module_name in sys.modules:
                del sys.modules[module_name]
            print(PVSimError('Error scanning module %s: %s' % (module_name, str(e))))

# scan for gridsim modules on import
pvsim_scan()


if __name__ == "__main__":
    pass