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

import math
import numpy as np

# T: absolute ambient temperature [K]
# Tmod: module temperature [K]
# G: irradiance [W/m2]
# TPV: computed PV generator temperature;
# Tamb: ambient temperature;
# T0: correction temperature (T0 = -3 deg C);
# k: irradiance gain (k = 0,03 km2/W);
# tau: time constant (? = 5 min);
# alpha: temperature coefficient of the current;
# beta: temperature coefficient of the voltage;
# CR, CV, CG: technology depending correction factor

class PVCurveError(Exception):
    pass


class PVCurve(object):

    def __init__(self, tech='cSi', Pmpp=3000, Vmpp=460, Tpv=25, n_points=1000, v_max=600.):
        """
        Create an I-V curve of n_points number of points based on a simple model from EN 50530
        :param tech: type of module technlogy - crystalline silicon or thin film
        :param Pmpp: power at the maximum power point (W), at STC
        :param Vmpp: voltage at the maximum power point (V), at STC
        :param Tpv: PV temperature (deg C)
        :param n_points: number of (I, V) points in the curve
        :param v_max: maximum voltage of the I-V curve points
        :return: dictionary with i and v lists
        """

        if tech == 'cSi':
            self.FFU = 0.8
            self.FFI = 0.9
            self.CG = 2.514E-03  # W/m2
            self.CV = 8.593E-02
            self.CR = 1.088E-04  # m2/W
            self.vL2H = 0.95  # ratio from VMPP at an irradiance of 200 W/m2 to VMPP at an irradiance of 1000 W/m2
            self.alpha = 0.0004  # 1/K (converted from %/K)
            self.beta = -0.004  # 1/K (converted from %/K)
        elif tech == 'thin film':
            self.FFU = 0.72
            self.FFI = 0.8
            self.CG = 1.252E-03  # W/m2
            self.CV = 8.419E-02
            self.CR = 1.476E-04  # m2/W
            self.vL2H = 0.98  # ratio from VMPP at an irradiance of 200 W/m2 to VMPP at an irradiance of 1000 W/m2
            self.alpha = 0.0002  # 1/K (converted from %/K)
            self.beta = -0.002  # 1/K (converted from %/K)
        else:
            raise PVCurveError('Incorrect PV Module Technology')

        self.G = 1000.  # initial irradiance.
        self.Gstc = 1000.

        # Temperature of the PV (dynamic)
        # Tpv = Tamb + T0 + (k*G)/(1 + tau*s)

        self.Tpv = Tpv
        self.Tstc = 25.

        # STC values
        self.Voc_stc = Vmpp/self.FFU
        self.Impp_stc = Pmpp/Vmpp
        self.Isc_stc = self.Impp_stc/self.FFI

        # Calculate CAQ constant
        self.CAQ = (self.FFU-1)/(math.log(1-self.FFI))

        self.v_points = list(np.linspace(0, v_max, n_points))
        self.i_points = []
        self.p_points = []
        self.Io = 0.
        self.Isc = 0.
        self.Voc = 0.
        self.curve = {}
        self.calc_curve()

    def calc_curve(self):
        """
        calculates new I-V curve based on updates to self.G and self.Tpv
        """
        self.Io = self.Isc_stc*((1 - self.FFI)**(1/(1-self.FFU)))*(self.G/self.Gstc)  # Irradiance dependent current
        self.Isc = self.Isc_stc*(self.G/self.Gstc)*(1 + self.alpha*(self.Tpv-self.Tstc))
        self.Voc = self.Voc_stc*(1 + self.beta*(self.Tpv-self.Tstc)) * \
                   (math.log((self.G/self.CG) + 1.)*self.CV - self.CR*self.G)

        # Generate I-V curve points
        self.i_points = []
        self.p_points = []
        for v in self.v_points:
            current_pt = self.Isc - self.Io*(math.exp(v/(self.Voc*self.CAQ))-1.)
            i_pt = max(current_pt, 0.)  # disallow negative current points
            self.i_points.append(i_pt)
            self.p_points.append(v*i_pt)

        # create curve dict
        self.curve = {'v': self.v_points, 'i': self.i_points, 'p': self.p_points}

    def get_voc(self):
        return self.Voc

    def get_isc(self):
        return self.Isc

    def get_curve(self):
        return self.curve

    def irradiance(self, irradiance):
        if irradiance is not None:
            self.G = irradiance
            self.calc_curve()
        return self.G

    def temperature(self, temp):
        if temp is not None:
            self.Tpv = temp
            self.calc_curve()
        return self.Tpv

if __name__ == "__main__":

    import matplotlib.pyplot as plt

    iv = PVCurve(tech='cSi', Pmpp=3000, Vmpp=450, n_points=1000)

    # plt.plot(iv.curve['v'], iv.curve['p'], label='1000 W/m^2')
    # plt.show()

    fig, ax = plt.subplots()
    line1, = ax.plot(iv.curve['v'], iv.curve['i'], label='1000 W/m^2')
    iv.irradiance(900)
    line2, = ax.plot(iv.curve['v'], iv.curve['i'], label='900 W/m^2')
    iv.irradiance(700)
    line3, = ax.plot(iv.curve['v'], iv.curve['i'], label='700 W/m^2')
    iv.irradiance(900)
    line4, = ax.plot(iv.curve['v'], iv.curve['i'], label='500 W/m^2')
    iv.irradiance(300)
    line5, = ax.plot(iv.curve['v'], iv.curve['i'], label='300 W/m^2')
    iv.irradiance(100)
    line6, = ax.plot(iv.curve['v'], iv.curve['i'], label='100 W/m^2')
    iv.irradiance(1000)
    iv.temperature(50)
    line7, = ax.plot(iv.curve['v'], iv.curve['i'], label='1000 W/m^2, T=50')
    iv.temperature(15)
    line8, = ax.plot(iv.curve['v'], iv.curve['i'], label='1000 W/m^2, T=15')
    ax.legend(loc='lower left')
    plt.show()



