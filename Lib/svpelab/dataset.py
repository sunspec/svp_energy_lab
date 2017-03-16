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


class DatasetError(Exception):
    """
    Exception to wrap all das generated exceptions.
    """
    pass


class Dataset():
    def __init__(self, points, recs=None):
        self.points = points
        if recs is not None:
            self.recs = recs
        else:
            self.recs = []

    def append(self, data):
        self.recs.append(data)

    def clear(self, data):
        self.recs = []

    def to_csv(self, filename):
        time = None
        cols = []
        chans = []
        if len(self.recs) > 0:
            rec = self.recs[0]
            if type(rec) is not dict:
                raise DatasetError('Invalid dataset record format')
            # if time present, add time columns
            time = rec.get('time')
            if time is not None:
                time = float(time)
                rtime = 0
                cols.extend(['time', 'rtime'])
            # sort keys alphabetically
            types=sorted(rec.keys(), key=lambda x:x.lower())
            for t in types:
                if type(t) is str and len(t) >= 2:
                    ctype = t
                    id = ''
                    index = t.find('_')
                    if index != -1:
                        ctype = t[:index]
                        id = t[index:]
                    if ctype in self.points:
                        points = self.points[ctype]
                        # save key and value length
                        count = len(rec.get(t))
                        chans.append((t, count))
                        for i in range(count):
                            cols.append('%s_%s%s' % (ctype, points[i], id))

        f = open(filename, 'w')
        f.write('%s\n' % ', '.join(map(str, cols)))
        for rec in self.recs:
            p = []
            if time is not None:
                t = rec.get('time')
                if t is not None:
                    rtime = float(t) - time
                    p.extend([t, rtime])
                else:
                    p.extend(['', ''])
            for chan in chans:
                values = rec.get(chan[0])
                for i in range(chan[1]):
                    value = ''
                    if values is not None and len(values) > i:
                        value = values[i]
                    p.append(value)
            f.write('%s\n' % ', '.join(map(str, p)))
        f.close()

    def from_csv(self, filename):
        pass


if __name__ == "__main__":

    points = {
        'ac': ('voltage', 'current', 'watts', 'va', 'vars', 'pf', 'freq'),
        'dc': ('voltage', 'current', 'watts')
    }

    recs =   [{'ac_1': (220.1, 10.1, 2100.1, 2200, 0.011, 0.991, 60.1),
               'ac_3': (220.3, 10.3, 2100.3, 2200, 0.013, 0.993, 60.3),
               'ac_2': (220.2, 10.2, 2100.2, 2200, 0.012, 0.992, 60.2),
               'dc': (440, 5, 2200), 'time': 1482505585.423},
              {'ac_1': (220.1, 10.1, 2100.1, 2200, 0.011, 0.991, 60.1),
               'ac_3': (220.3, 10.3, 2100.3, 2200, 0.013, 0.993, 60.3),
               'ac_2': (220.2, 10.2, 2100.2, 2200, 0.012, 0.992, 60.2),
               'dc': (440, 5, 2200), 'time': 1482505585.923},
              {'ac_1': (220.1, 10.1, 2100.1, 2200, 0.011, 0.991, 60.1),
               'ac_3': (220.3, 10.3, 2100.3, 2200, 0.013, 0.993, 60.3),
               'ac_2': (220.2, 10.2, 2100.2, 2200, 0.012, 0.992, 60.2),
               'dc': (440, 5, 2200), 'time': 1482505586.423},
              {'ac_1': (220.1, 10.1, 2100.1, 2200, 0.011, 0.991, 60.1),
               'ac_3': (220.3, 10.3, 2100.3, 2200, 0.013, 0.993, 60.3),
               'ac_2': (220.2, 10.2, 2100.2, 2200, 0.012, 0.992, 60.2),
               'dc': (440, 5, 2200), 'time': 1482505586.923},
              {'ac_1': (220.1, 10.1, 2100.1, 2200, 0.011, 0.991, 60.1),
               'ac_3': (220.3, 10.3, 2100.3, 2200, 0.013, 0.993, 60.3),
               'ac_2': (220.2, 10.2, 2100.2, 2200, 0.012, 0.992, 60.2),
               'dc': (440, 5, 2200), 'time': 1482505587.423},
              {'ac_1': (220.1, 10.1, 2100.1, 2200, 0.011, 0.991, 60.1),
               'ac_3': (220.3, 10.3, 2100.3, 2200, 0.013, 0.993, 60.3),
               'ac_2': (220.2, 10.2, 2100.2, 2200, 0.012, 0.992, 60.2),
               'dc': (440, 5, 2200), 'time': 1482505587.923},
              {'ac_1': (220.1, 10.1, 2100.1, 2200, 0.011, 0.991, 60.1),
               'ac_3': (220.3, 10.3, 2100.3, 2200, 0.013, 0.993, 60.3),
               'ac_2': (220.2, 10.2, 2100.2, 2200, 0.012, 0.992, 60.2),
               'dc': (440, 5, 2200), 'time': 1482505588.423},
              {'ac_1': (220.1, 10.1, 2100.1, 2200, 0.011, 0.991, 60.1),
               'ac_3': (220.3, 10.3, 2100.3, 2200, 0.013, 0.993, 60.3),
               'ac_2': (220.2, 10.2, 2100.2, 2200, 0.012, 0.992, 60.2),
               'dc': (440, 5, 2200), 'time': 1482505588.923}]


    ds = Dataset(points, recs=recs)
    ds.to_csv('xyz')
