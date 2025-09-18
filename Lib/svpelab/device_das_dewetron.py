"""
Copyright (c) 2018, Austrian Institute of Technology
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

Neither the names of the Austrian Institute of Technology nor the names of its
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

import time
from collections import OrderedDict
import datetime

import numpy as np

try:
    from .dewenetcontroller import dewenetcontroller as dewe
except Exception as e:
    print(('Missing dewecontroller. %s' % e))

"""
todo: thread needs to be joined and stopped!

"""

"""
This is a really bad hack! 
"""
data_points = [  # 3 phase
                'TIME',
                'DC_V',
                'DC_I',
                'AC_VRMS_1',
                'AC_VRMS_2',
                'AC_VRMS_3',
                'AC_IRMS_1',
                'AC_IRMS_2',
                'AC_IRMS_3',
                'DC_P',
                'AC_S_1',
                'AC_S_2',
                'AC_S_3',
                'AC_P_1',
                'AC_P_2',
                'AC_P_3',
                'AC_Q_1',
                'AC_Q_2',
                'AC_Q_3',
                'AC_FREQ_1',
                'AC_FREQ_2',
                'AC_FREQ_3',
                'AC_PF_1',
                'AC_PF_2',
                'AC_PF_3',
                'TRIG',
                'TRIG_GRID'
            ]



dewe_channelmap = OrderedDict([
    ('TIME', None),
    ('AC_VRMS_1', 'Va'),
    ('AC_IRMS_1', 'Ia'),
    ('AC_P_1', 'Pa'),
    ('AC_S_1', 'Sa'),
    ('AC_Q_1', 'Qa'),
    ('AC_PF_1', 'PFa'),
    ('AC_FREQ_1', 'F'),
    ('AC_VRMS_2', 'Vb'),
    ('AC_IRMS_2', 'Ib'),
    ('AC_P_2', 'Pb'),
    ('AC_S_2', 'Sb'),
    ('AC_Q_2', 'Qb'),
    ('AC_PF_2', 'PFb'),
    ('AC_FREQ_2', 'F'),
    ('AC_VRMS_3', 'Vc'),
    ('AC_IRMS_3', 'Ic'),
    ('AC_P_3', 'Pc'),
    ('AC_S_3', 'Sc'),
    ('AC_Q_3', 'Qc'),
    ('AC_PF_3', 'PFc'),
    ('AC_FREQ_3', 'F'),
    ('DC_V', 'Vdc'),
    ('DC_I', 'Idc'),
    ('DC_P', 'Pdc'),
    ('TRIG', None),
    ('TRIG_GRID', None)
])


deweResults = OrderedDict()


def update_value(channel_name, timestamp, value):
    ts_m = (np.float64(timestamp.strftime('%M.0'))*60)*1000
    ts_us = np.longlong(ts_m+np.float64(timestamp.strftime('%S.%f'))*1000)

    for k in list(dewe_channelmap.keys()):
        if dewe_channelmap[k]:
            if dewe_channelmap[k] in channel_name:
                try:
                    deweResults[k]
                except:
                    deweResults[k] = []
                deweResults[k].append( (ts_us, value) )

class Device(object):

    def __logevent__(self, msg):
        if self.ts:
            self.ts.log(msg)
        else:
            print('%s' % msg)


    def __init__(self, params=None):
        if not params:
            raise ValueError('Params can not be None for this module!')


        self.deweDevice = None

        self.params = params


        try:
            self.dewehost = self.params['ip_addr']
            self.deweport = self.params['ipport']
            self.sample_interval = self.params['sample_interval']
        except:
            raise ValueError('Minimum required paramters were not supplied!')


        try:
            global dewe_channelmap
            dewe_channelmap['AC_VRMS_1'] = self.params['AC_VRMS_1']
            dewe_channelmap['AC_VRMS_2'] = self.params['AC_VRMS_2']
            dewe_channelmap['AC_VRMS_3'] = self.params['AC_VRMS_3']
            dewe_channelmap['AC_IRMS_1'] = self.params['AC_IRMS_1']
            dewe_channelmap['AC_IRMS_2'] = self.params['AC_IRMS_2']
            dewe_channelmap['AC_IRMS_3'] = self.params['AC_IRMS_3']
            dewe_channelmap['AC_FREQ_1'] = self.params['AC_FREQ_1']
            dewe_channelmap['AC_FREQ_2'] = self.params['AC_FREQ_2']
            dewe_channelmap['AC_FREQ_3'] = self.params['AC_FREQ_3']
            dewe_channelmap['AC_P_1'] = self.params['AC_P_1']
            dewe_channelmap['AC_P_2'] = self.params['AC_P_2']
            dewe_channelmap['AC_P_3'] = self.params['AC_P_3']
            dewe_channelmap['AC_S_1'] = self.params['AC_S_1']
            dewe_channelmap['AC_S_2'] = self.params['AC_S_2']
            dewe_channelmap['AC_S_3'] = self.params['AC_S_3']
            dewe_channelmap['AC_Q_1'] = self.params['AC_Q_1']
            dewe_channelmap['AC_Q_2'] = self.params['AC_Q_2']
            dewe_channelmap['AC_Q_3'] = self.params['AC_Q_3']
            dewe_channelmap['DC_V'] = self.params['DC_V']
            dewe_channelmap['DC_I'] = self.params['DC_I']
            dewe_channelmap['DC_P'] = self.params['DC_P']
            dewe_channelmap['AC_PF_1'] = self.params['AC_PF_1']
            dewe_channelmap['AC_PF_2'] = self.params['AC_PF_2']
            dewe_channelmap['AC_PF_3'] = self.params['AC_PF_3']
            dewe_channelmap['TIME'] = None
            dewe_channelmap['TRIG'] = None
            dewe_channelmap['TRIG_GRID'] = None

            self.deweproxyhost = self.params['deweproxy_ip_addr']
            self.deweproxyport = self.params['deweproxy_ip_port']

        except Exception as e:
            self.deweproxyhost = '127.0.0.1'
            self.deweproxyport = 9000
            print('Using default map')


        try:
            self.sampling_interval_dewe = self.params['sample_interval_dewe']
        except:
            self.sampling_interval_dewe = None


        try:
            self.ts = self.params['ts']
        except:
            self.ts = None

        self.__logevent__('DEWESoft NET Plugin Initialized!.')

        try:
            self.__logger__ = self.params['logger']
        except:
            self.__logger__ = None

        self.channellist = []

        for k in list(dewe_channelmap.keys()):
            if dewe_channelmap[k] is not None:
                if dewe_channelmap[k] not in self.channellist:
                    self.channellist.append(dewe_channelmap[k])


        self.data_points = list(data_points)

        self.points = None
        self.point_indexes = []

             # waveform settings
        self.wfm_sample_rate = None
        self.wfm_pre_trigger = None
        self.wfm_post_trigger = None
        self.wfm_trigger_level = None
        self.wfm_trigger_cond = None
        self.wfm_trigger_channel = None
        self.wfm_timeout = None
        self.wfm_channels = None
        self.wfm_capture_name = None

        self.numberOfSamples = None
        self.triggerOffset = None
        self.decimation = 1
        self.captureSettings = None
        self.triggerSettings = None
        self.channelSettings = None

        # regular python list is used for data buffer
        self.capturedDataBuffer = []
        self.time_vector = None
        self.wfm_data = None
        self.signalsNames = None
        self.analog_channels = []
        self.digital_channels = []
        self.subsampling_rate = None



        """
        Why is .open() not handled at toplevel?
        """
        self.open()

    def info(self):
        if self.deweDevice:
            return self.deweDevice.get_dewe_information()
        else:
            raise ValueError("Not connected to DAS - open() was not called prior")

    def open(self):
        if not self.deweDevice:
            self.__logevent__('Starting connection to local DEWESoft NET Instance.')
            try:
                self.deweDevice = dewe.DeweNetController(logger=self.__logger__)
                self.deweDevice.connect_to_dewe(dewe_ip=self.dewehost, dewe_port=int(self.deweport),
                                           client_server_ip=self.deweproxyhost, client_server_port=int(self.deweproxyport),
                                           list_of_channels=self.channellist, samplerate=self.sampling_interval_dewe)

                self.deweDevice.add_update_value_handler(update_value, channels=self.channellist)

                self.deweDevice.start_dewe_measurement()

            except Exception as e:
                self.__logevent__('Error on establishing connection to dewe! [%s]' % e)
                raise

        return self.deweDevice


    def close(self):
        if self.deweDevice:
            self.deweDevice.stop_dewe_measurement()
            self.deweDevice.disconnect_from_dewe()
            self.deweDevice = None

        return self.deweDevice


    def data_capture(self, enable=True):
        """todo: """
        pass

    def data_read(self):
        if self.deweDevice:
            """For Later dict support:
            retry = 0
            e = datetime.datetime.now()
            while True:
                data = {}
                try:
                    data['TIME'] = time.time()
                    data['TRIG'] = 0
                    data['TRIG_GRID'] = 0
                    for i in deweResults.keys():
                        data[i] = deweResults[i][-1][1]

                    self.__logevent__(data)
                    return data
                except Exception, e:
                    self.__logevent__(e)
            """
            while True:
                data = []
                try:
                    data.append(time.time())        #Channle TIME
                    for i in data_points:

                        if dewe_channelmap[i]:
                            data.append(deweResults[i][-1][1])
                    data.append(0)                  #channel TRIG
                    data.append(0)                  #channel TRIG_GRID
                    return data
                except Exception as e:
                    pass
        else:
            raise ValueError("Not connected to DAS - open() was not called prior")







    def waveform_config(self, params):
        pass

    def waveform_capture(self, enable=True, sleep=None):
        pass

    def waveform_status(self):
        pass

    def waveform_force_trigger(self):
        """
        Create trigger event with provided value.
        """
        pass

    def waveform_capture_dataset(self):
        pass


if __name__ == "__main__":


    params = {}
    params['ip_addr'] = '127.0.0.1'
    params['ipport'] = 8999
    params['sample_interval'] = 1000
    params['sample_interval_dewe'] = 10000

    params['AC_VRMS_1'] = "EUT/U_rms_L1"
    params['AC_VRMS_2'] = "EUT/U_rms_L2"
    params['AC_VRMS_3'] = "EUT/U_rms_L3"
    params['AC_IRMS_1'] = "EUT/I_rms_L1"
    params['AC_IRMS_2'] = "EUT/I_rms_L2"
    params['AC_IRMS_3'] = "EUT/I_rms_L3"
    params['AC_FREQ_1'] = "EUT/Frequency"
    params['AC_FREQ_2'] = "EUT/Frequency"
    params['AC_FREQ_3'] = "EUT/Frequency"
    params['AC_P_1'] = "EUT/P_L1"
    params['AC_P_2'] = "EUT/P_L2"
    params['AC_P_3'] = "EUT/P_L1"
    params['AC_S_1'] = "EUT/S_L1"
    params['AC_S_2'] = "EUT/S_L2"
    params['AC_S_3'] = "EUT/S_L3"
    params['AC_Q_1'] = "EUT/Q_L1"
    params['AC_Q_2'] = "EUT/Q_L2"
    params['AC_Q_3'] = "EUT/Q_L3"
    params['AC_PF_1'] = "EUT/PF_L1"
    params['AC_PF_2'] = "EUT/PF_L2"
    params['AC_PF_3'] = "EUT/PF_L3"
    params['DC_V'] = "PV/U_rms_L1"
    params['DC_I'] = "PV/I_rms_L1"
    params['DC_P'] = "PV/P_L1"

    params['deweproxy_ip_addr'] = "0.0.0.0"
    params['deweproxy_ip_port'] = 9999

    d = Device(params=params)

    d.open()
    count = 0
    while True:
        count +=1
        time.sleep(0.25)
        print("[%s] -> %s" % (count, d.data_read()))
        if count > 200: break
    d.close()

