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

# time offset in seconds, Irriadiance (W/m^2)
STPsIrradiance = [
    (0, 200),
    (15, 200),
    (95, 1000),
    (130, 1000),
    (134, 200),
    (154, 200),
    (156, 600),
    (191, 600),
    (193, 200),
    (213, 200),
    (217.5, 1100),
    (253, 1100),
    (353, 200),
    (360, 200),
]

# time offset in seconds, Available Power (% of nameplate)
STPsIrradianceNorm = [
    (0, 20),
    (15, 20),
    (95, 100),
    (130, 100),
    (134, 20),
    (154, 20),
    (156, 60),
    (191, 60),
    (193, 20),
    (213, 20),
    (217.5, 110),
    (253, 110),
    (353, 20),
    (360, 20),
]

profiles = {
    'STPsIrradiance': STPsIrradiance,
    'STPsIrradianceNorm': STPsIrradianceNorm,
}

if __name__ == "__main__":

    pass
