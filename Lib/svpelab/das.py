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

import dataset

points_default = {
    'ac': ('voltage', 'current', 'watts', 'va', 'vars', 'pf', 'freq'),
    'dc': ('voltage', 'current', 'watts'),
    'sc': ('trigger', )
}

MINIMUM_SAMPLE_PERIOD = 50

das_modules = {}

def params(info, id=None, label='Data Acquisition System', group_name=None, active=None, active_value=None):
    if group_name is None:
        group_name = DAS_DEFAULT_ID
    else:
        group_name += '.' + DAS_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    name = lambda name: group_name + '.' + name
    info.param_group(group_name, label='%s Parameters' % label, active=active, active_value=active_value, glob=True)
    info.param(name('mode'), label='Mode', default='Manual', values=['Manual'])
    for mode, m in das_modules.iteritems():
        m.params(info, group_name=group_name)

DAS_DEFAULT_ID = 'das'

def das_init(ts, id=None, points=None, group_name=None):
    """
    Function to create specific das implementation instances.
    """
    if group_name is None:
        group_name = DAS_DEFAULT_ID
    else:
        group_name += '.' + DAS_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    mode = ts.param_value(group_name + '.' + 'mode')
    sim_module = das_modules.get(mode)
    if sim_module is not None:
        sim = sim_module.DAS(ts, group_name, points=points)
    else:
        raise DASError('Unknown data acquisition system mode: %s' % mode)

    return sim


class DASError(Exception):
    """
    Exception to wrap all das generated exceptions.
    """
    pass


class DAS(object):
    """
    Template for grid simulator implementations. This class can be used as a base class or
    independent grid simulator classes can be created containing the methods contained in this class.
    """

    def __init__(self, ts, group_name, points=None):
        self.ts = ts
        self.group_name = group_name
        self.points = points_default
        self.params = {}
        self.device = None
        self.sample_interval = 1000
        self.sc = {}
        self._capture = False
        self._timer = None
        self._ds = dataset.Dataset(self.points)
        self._last_datarec = {}

        if points is not None:
            if 'sc' in points:
                self.points['sc'] = points['sc']

        # init soft channels
        sc_points = self.points.get('sc')
        if sc_points is not None:
            for p in sc_points:
                self.sc[p] = 0

    def _data_expand(self, rec):
        data = {}
        for key, value in rec.iteritems():
            if key == 'time':
                data['time'] = value
            else:
                chan_type = key
                label = ''
                i = key.find('_')
                if i > 0:
                    chan_type = key[:i]
                    if len(key) > i:
                        label = key[i+1:]
                chan_points = self.points.get(chan_type)
                if chan_points is not None:
                    if len(chan_points) != len(value):
                        raise DASError('Point list mismatch for %s: %s %s' % (key, value, chan_points))
                    for x in range(len(chan_points)):
                        chan = '%s_%s' % (chan_type, chan_points[x])
                        if label:
                            chan += '_%s' % (label)
                        data[chan] = value[x]
        return data

    def _timer_timeout(self, arg=None):
        self.data_sample()

    def info(self):
        """
        Return information string for the DAS device.
        """
        if self.device is None:
            raise DASError('DAS device not initialized')
        return self.device.info()

    def open(self):
        """
        Open communications resources associated with the DAS device.
        """
        if self.device is None:
            raise DASError('DAS device not initialized')
        self.device.open()

    def close(self):
        """
        Close any open communications resources associated with the DAS device.
        """
        if self.device is None:
            raise DASError('DAS device not initialized')
        self.device.close()

    def data_capture(self, capture=None):
        """
        Enable/disable data capture.

        If sample_interval == 0, there will be no autonomous data captures and self.data_sample should be used to add
        data points to the capture
        """
        if capture is True:
            if self._capture is False:
                self._ds = dataset.Dataset(self.points)
                self._last_datarec = {}
                if self.sample_interval > 0:
                    if self.sample_interval < MINIMUM_SAMPLE_PERIOD:
                        raise DASError('Sample period too small: %s' % (self.sample_interval))
                    self._timer = self.ts.timer_start(float(self.sample_interval)/1000, self._timer_timeout, repeating=True)
                self._capture = True
        elif capture is False:
            if self._capture is True:
                if self._timer is not None:
                    self.ts.timer_cancel(self._timer)
                self._timer = None
                self._capture = False

    def data_capture_read(self):
        """
        Return the last data sample from the data capture in expanded format.
        """
        return self._data_expand(self._last_datarec)

    def data_capture_dataset(self):
        """
        Return dataset (DataSet) created from last data capture.
        """
        return self._ds

    def device_data_read(self):
        """
        Read the current data values directly from the DAS. It does not create a new data sample in the
        data capture, if active.
        """
        rec = self.device.data_read()
        # add soft channel points
        points = self.points.get('sc')
        if points is not None:
            values = []
            for p in points:
                values.append(self.sc[p])
            rec['sc'] = tuple(values)

        return rec

    def data_read(self):
        """
        Read the current data values directly from the DAS. It does not create a new data sample in the
        data capture, if active.
        """
        return self._data_expand(self.device_data_read())

    def data_sample(self):
        """
        Read the current data values directly from the DAS and place in the current dataset.
        """
        if self._capture is True:
            self._last_datarec = self.device_data_read()
            self._ds.append(self._last_datarec)
        return self._last_datarec

def das_scan():
    global das_modules
    # scan all files in current directory that match das_*.py
    package_name = '.'.join(__name__.split('.')[:-1])
    files = glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'das_*.py'))
    for f in files:
        module_name = None
        try:
            module_name = os.path.splitext(os.path.basename(f))[0]
            if package_name:
                module_name = package_name + '.' + module_name
            m = importlib.import_module(module_name)
            if hasattr(m, 'das_info'):
                info = m.das_info()
                mode = info.get('mode')
                # place module in module dict
                if mode is not None:
                    das_modules[mode] = m
            else:
                if module_name is not None and module_name in sys.modules:
                    del sys.modules[module_name]
        except Exception, e:
            if module_name is not None and module_name in sys.modules:
                del sys.modules[module_name]
            raise DASError('Error scanning module %s: %s' % (module_name, str(e)))

# scan for das modules on import
das_scan()

if __name__ == "__main__":
    pass
