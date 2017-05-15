
import os
import wxmplot
import numpy

def menu(result, result_dir, result_name):
    if result is not None and result.filename is not None:
        ext = os.path.splitext(result.filename)[1]
        if ext == '.csv':
            rm = ResultMenu(result, result_dir, result_name)
            return rm.menu_items


class ResultMenu(object):

    def __init__(self, result, result_dir, result_name):
        self.result = result
        self.result_dir = result_dir
        self.result_name = result_name

        self.menu_open_items = [('WXMPlot', '', None, self.plot_wxmplot, None),
                                ('Pyplot', '', None, self.plot_pyplot, None)]

        self.menu_items = [('Open with', '', self.menu_open_items, None, None),
                           ('', '', None, None, None),
                           ('Other', '', None, None, None)]


    def result_other(self, arg=None):
        pass

    def plot_wxmplot(self, arg=None):
        frame = wxmplot.PlotFrame()
        filename = os.path.join(self.result_dir, self.result_name, self.result.filename)
        f = open(filename, 'r')
        names = f.readline().split(',')
        columns = len(names)
        value_arrays = []
        for i in range(columns):
            value_arrays.append([])

        base_time = None
        for line in f:
            values = line.split(',')
            if base_time is None:
                base_time = float(values[0])
            t = round(float(values[0]) - base_time, 2)
            value_arrays[0].append(t)
            for i in range(1, columns):
                try:
                    v = float(values[i])
                    value_arrays[i].append(v)
                except Exception, e:
                    value_arrays[i].append('nan')
                    pass

        time_array = numpy.array(value_arrays[0])
        for i in range(1, columns):
            value_array = numpy.array(value_arrays[i])
            frame.oplot(time_array, value_array, label=names[i])

        '''
        r = numpy.recfromcsv(filename, case_sensitive=True)
        print(repr(r))
        print r.dtype
        names = r.dtype.names
        x = names[0]
        print r[x]
        for name in names[1:]:
            # print name, r[x], r[name]
            frame.oplot(r[x], r[name])
        '''
        # pframe.plot(x, y1, title='Test 2 Axes with different y scales',
        #            xlabel='x (mm)', ylabel='y1', ymin=-0.75, ymax=0.75)
        # pframe.oplot(x, y2, y2label='y2', side='right', ymin=0)

        frame.SetTitle(self.result.name)
        frame.Show()

    def plot_pyplot(self, arg=None):
        print 'plot_pyplot'


