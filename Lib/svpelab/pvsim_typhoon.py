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
from . import pv_curve_generation
import time
from . import pv_profiles
from . import pvsim

try:
    import typhoon.api.hil as cp  # control panel
    from typhoon.api.schematic_editor import model
    import typhoon.api.pv_generator as pv
except Exception as e:
    print(('Typhoon HIL API not installed. %s' % e))

typhoon_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Typhoon'
}

def pvsim_info():
    return typhoon_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = typhoon_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)
    # info.param(pname('pmp'), label='EN50530 MPP Power (W)', default=34500.0)
    info.param(pname('voc'), label='EN50530 MPP Voc (V)', default=997.)
    info.param(pname('isc'), label='EN50530 MPP Isc (A)', default=50.)
    info.param(pname('pv_name'), label='PV file name (.ipvx)', default=r"init.ipvx")
    info.param(pname('pv_directory'), label='Absolute path to .ipvx file',
               default=r"D:/SVP/1547.1 (5-10-19)/Lib/svpelab/ASGC_Closed_loop_full_model/")
    info.param(pname('irr_start'), label='Irradiance at the start of the test (W/m^2)', default=1000.)
    info.param(pname('profile_name'), label='Irradiance Profile Name', default='STPsIrradiance',
               desc='Typically the Sandia Test Protocols\' (STPs) Irradiance will be used for the profile.')

GROUP_NAME = 'typhoon'

class PVSim(pvsim.PVSim):

    def __init__(self, ts, group_name):
        pvsim.PVSim.__init__(self, ts, group_name)

        self.ts = ts

        try:
            # self.pmp = ts.param_value('pvsim.typhoon.pmp')
            self.voc = self._param_value('voc')
            self.isc = self._param_value('isc')
            self.irr_start = self._param_value('irr_start')
            self.profile_name = self._param_value('profile_name')
            self.profile = None
            self.settings_file = None

            self.pv_name = self._param_value('pv_name')
            self.pv_directory = self._param_value('pv_directory')
            self.pv_file = self.pv_directory.replace("\\", "/") + self.pv_name

            # PV is configured with the .runx file in hil.typhoon
            # self.ts.log('Configuring PV simulation in Typhoon environment...')
            # self.config()

            # update the pmp after setting up I-V curve
            self.pmp = self.pv_pmp_get()

        except Exception:
            raise

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def config(self):

            lib_dir = os.path.dirname(__file__) + os.path.sep
            if self.pv_name[-5:] == ".ipvx":
                model_file = r"Typhoon/" + self.pv_name
            else:
                model_file = r"Typhoon/" + self.pv_name + r".ipvx"
            self.pv_file = lib_dir.replace("\\", "/") + model_file
            self.ts.log("PV model (.ipvx) file: %s" % self.pv_file)

            if os.path.isfile(self.pv_file):
                self.ts.log_debug("PV model (.ipvx) file exists!")
            else:
                self.ts.log_debug("PV model (.ipvx) file does not exist! Creating new EN50530 curve.")

                # generating PV file
                self.ts.log("Setting PV parameters...")
                pv_params = {"Voc_ref": self.voc,                  # Open-circuit voltage (Voc [V])
                             "Isc_ref": self.isc,                  # Short-circuit current (Isc [A])
                             "pv_type": pv.EN50530_PV_TYPES[0],    # "cSi" pv type ("cSi" or "Thin film")
                             "neg_current": False}                 # allow negative current

                (status, msg) = pv.generate_pv_settings_file(pv.PV_MT_EN50530, self.pv_file, pv_params)
                if not status:
                    self.ts.log("Error during generating PV curve. Error: %s" % msg)
                    return status

            # initialize PV using .ipvx PV file from config, set initial irradiance and temperature values
            if not cp.set_pv_input_file('PV1', file=self.pv_file, illumination=self.irr_start, temperature=25.0):
                self.ts.log("Error during setting PV curve (init.ipvx).")
                status = False
                return status

            return True  # PV configured correctly

    def set_pv_curve(self, pv_curve_path):

        # generating PV file
        self.ts.log("Generating new PV curve...")
        pv_params = {"Voc_ref": self.voc,                  # Open-circuit voltage (Voc [V])
                     "Isc_ref": self.isc,                  # Short-circuit current (Isc [A])
                     "pv_type": pv.EN50530_PV_TYPES[0],    # "cSi" pv type ("cSi" or "Thin film")
                     "neg_current": False}                 # allow negative current
        (status, msg) = pv.generate_pv_settings_file(pv.PV_MT_EN50530, pv_curve_path, pv_params)
        if not status:
            self.ts.log_error("Error during generating PV curve. Error: %s" % msg)
            return status

        if os.path.isfile(pv_curve_path):
            self.ts.log_debug("PV model (.ipvx) file exists!  Setting curve in Typhoon environment...")

            if not cp.set_pv_input_file('PV1', file=pv_curve_path, illumination=self.irr_start, temperature=25.0):
                self.ts.log_error("Error during setting PV curve (%s)." % pv_curve_path)
                status = False
                return status
        else:
            self.ts.log_debug("PV model (.ipvx) file does not exist! Did not set new PV curve. ")
            return False

        return True

    def close(self):
        pass

    def pv_pmp_get(self):
        (status, (imp, vmp)) = cp.get_pv_mpp("PV1")
        return imp*vmp

    def pv_imp_get(self):
        (status, (imp, vmp)) = cp.get_pv_mpp("PV1")
        return imp

    def pv_vmp_get(self):
        (status, (imp, vmp)) = cp.get_pv_mpp("PV1")
        return vmp

    def power_set(self, power):
        # Assume that the PV has been configured to provide rated power of the DER
        irr = (power/self.pmp)*1000.
        self.irradiance_set(irradiance=irr)

    def irradiance_set(self, irradiance=1000.):
        self.ts.log('PV Models in the Simulation: %s. Changing the settings for "PV1"' % cp.get_pvs())
        cp.set_pv_amb_params("PV1", illumination=irradiance)
        # cp.wait_msec(50.0)

    '''
    def iv_curve_config(self, pmp=None, vmp=None):
        """
        Hack method to generate I-V curves in typhoon that the ASGC plays nicely with. File names
        are, e.g., 20Prated.ipvx, 60Prated.ipvx, and 100Prated.ipvx.
        """
        tol = 0.02
        asgc_power = 34500.
        for p_rated_ratio in [0.2, 0.6, 1.0]:
            if asgc_power*(p_rated_ratio - tol) <= pmp <= asgc_power*(p_rated_ratio + tol):
                new_pv_file = '%s%sPrated.ipvx' % (self.pv_file[:-5], int(p_rated_ratio*100.))
                self.ts.log_debug('New PV file name: %s' % new_pv_file)

                # set pv curve in Typhoon
                self.set_pv_curve(new_pv_file)
                self.ts.sleep(2)
                return True

        self.ts.log_error('Did not update I-V Curve in the Typhoon environment!')
        return False
    '''

    def iv_curve_config(self, pmp=None, vmp=None):
        """
        Configure EN50530 curve based on Pmp and Vmp inputs
        """
        if pmp is None:
            pmp = self.pv_pmp_get()
        if vmp is None:
            vmp = self.pv_vmp_get()

        self.ts.log_debug("Creating new EN50530 curve based on Pmp and Vmp...")
        pv_curve = pv_curve_generation.PVCurve(tech='cSi', Pmpp=pmp, Vmpp=vmp, Tpv=25, n_points=1000, v_max=self.voc)
        self.voc = pv_curve.Voc
        self.isc = pv_curve.Isc

        # Create new pv_file
        self.ts.log_debug('Current PV file name: %s' % self.pv_file)
        # new_pv_file = '%s%s.ipvx' % (self.pv_file[:-5], time.time())
        new_pv_file = '%s_new.ipvx' % (self.pv_file[:-5])
        self.ts.log_debug('New PV file name: %s' % new_pv_file)

        # set pv curve in Typhoon
        self.set_pv_curve(new_pv_file)
        self.ts.sleep(2)

        return True

    def profile_load(self, profile_name):
        if profile_name != 'None' and profile_name is not None:
            self.ts.log('Loading irradiance profile %s' % profile_name)
            self.profile_name = profile_name

            # get profile from pv_profiles.py
            self.profile = pv_profiles.profiles.get(self.profile_name)
            executeAt1 = self.profile[0][1]  # execute after x number of seconds

            # change illumination at specified simulation time
            (status, (Imp, Vmp)) = cp.set_pv_amb_params("PV1", illumination=1000.0, executeAt=executeAt1)

            # NOTE: You need to wait 10000 simulation cycles until first time command is finished
            #       and then execute next timed command

            # need to spawn a new process here to handle the PV profiles

    def power_on(self):
        pass

    def profile_start(self):
        cp.start_simulation()

if __name__ == "__main__":
    pass
