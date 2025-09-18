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

vv_voltage_profile = [
    (0, 100, 100),
    (30, 100, 100),
    (30, 106, 100),
    (60, 106, 100),
    (60, 94, 100),
    (90, 94, 100),
    (90, 100, 100),
    (120, 100, 100),
    (135, 106, 100),
    (150, 106, 100),
    (180, 94, 100),
    (195, 94, 100),
    (210, 100, 100),
    (240, 100, 100),
    (245, 106, 100),
    (250, 106, 100),
    (260, 94, 100),
    (265, 94, 100),
    (270, 100, 100),
    (300, 100, 100)
]

'''
Create voltage ride-through profile based on UL 1741 SA ride-through test step function

   v_n - starting voltage(PUT) value
   v_t - test voltage(PUT) value
   t_f - fall time
   t_h - hold time
   t_r - rise time
   t_d - dwell time
   n - number of iterations
'''

def voltage_rt_profile(v_n, v_t, t_f, t_h, t_r, t_d, n):
    profile = []
    t = 0
    for i in range(1, n+1):
        profile.append((t, v_n, 100))  # (time offset, starting voltage (%), freq (100%))
        t += t_d                       # hold for dwell time
        profile.append((t, v_n, 100))  # (time offset, starting voltage (%), freq (100%))
        t += t_f                       # ramp over fall time
        profile.append((t, v_t, 100))  # (time offset, test voltage (%), freq (100%))
        t += t_h                       # hold for hold time
        profile.append((t, v_t, 100))  # (time offset, test voltage (%), freq (100%))
        t += t_r                       # ramp over rise time
        profile.append((t, v_n, 100))  # (time offset, starting voltage (%), freq (100%))
    t += t_d                           # hold for dwell time
    profile.append((t, v_n, 100))      # (time offset, starting voltage (%), freq (100%))

    return profile

def freq_rt_profile(p_n, p_t, t_f, t_h, t_r, t_d, n):
    profile = []
    t = 0
    for i in range(1, n+1):
        profile.append((t, 100, p_n))  # (time offset, voltage (100%), starting freq)
        t += t_d                       # hold for dwell time
        profile.append((t, 100, p_n))  # (time offset, voltage (100%), starting freq)
        t += t_f                       # ramp over fall time
        profile.append((t, 100, p_t))  # (time offset, voltage (100%), test freq)
        t += t_h                       # hold for hold time
        profile.append((t, 100, p_t))  # (time offset, voltage (100%), test freq)
        t += t_r                       # ramp over rise time
        profile.append((t, 100, p_n))  # (time offset, voltage (100%), starting freq)
        t += t_d                       # hold for dwell time
    profile.append((t, 100, p_n))      # (time offset, voltage (100%), starting freq)

    return profile

print(voltage_rt_profile(100, 80, 2, 5, 2, 5, 1))
print(freq_rt_profile(100, 80, 2, 5, 2, 5, 3))

'''
Each region shall have the applicable ride-through magnitudes and durations verified.
In the case of Rule 21 L/HVRT, four ride-through magnitudes will be verified: the upper bound of HV1,
lower bound of LV1, lower bound of LV2, and lower bound of LV3.

HV1 = 110%, 120%, 12s
LV1 = 70, 88, 20s
LV2 = 50, 70, 10s
LV3 = 49, 50, 1s

Inputs:
v_msa
v_max
v_min
duration
dwell_time
freq
iterations
rt = 'HVRT, LVRT'


For high voltage tests (HV1):
v_n = lowest voltage of the region + (v_msa * 1.5)
v_t = highest voltage of the region - (v_msa * 1.5)

The t_r and t_f values shall each be less than or equal to the larger of 1 cycle or 1% of the ride-through region
duration.

t_ex = duration
t_d = dwell_time
count = iterations
t_f = t_r = max(1/freq, duration/100)
t_h = t_ex - t_f - t_r

if rt == 'HVRT':
   v_n = v_min + (v_msa * 1.5)
   v_t = v_max - (v_msa * 1.5)
elif rt == 'LVRT':
   v_n = v_max - (v_msa * 1.5)
   v_t = v_min + (v_msa * 1.5)

profile = voltage_rt_profile(v_n, v_t, t_f, t_h, t_r, t_d, count)

start das
start profile
profile_duration = profile[-1][0]
sleep(profile_duration + 5)
stop das
save das

'''
