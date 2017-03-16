
import time

# map data points to query points
query_points = {
    'ac_voltage': 'URMS',
    'ac_current': 'IRMS',
    'ac_watts': 'P',
    'ac_va': 'S',
    'ac_vars': 'Q',
    'ac_pf': 'LAMBDA',
    'ac_freq': 'FU',
    'dc_voltage': 'UDC',
    'dc_current': 'IDC',
    'dc_watts': 'P'
}

class DeviceError(Exception):
    """
    Exception to wrap all das generated exceptions.
    """
    pass

class Device(object):

    def __init__(self, params):

        self.params = params
        self.channels = params.get('channels')
        self.query_info = []
        # Resource Manager for VISA
        self.rm = None
        # Connection to instrument for VISA-GPIB
        self.conn = None

        # create query string for configured channels
        query_chan_str = ''
        item = 0
        for i in range(1,5):
            query_info = None
            chan = self.channels[i]
            if chan is not None:
                chan_type = chan.get('type')
                points = chan.get('points')
                chan_label = chan.get('label')
                if chan_type is None:
                    raise DeviceError('No channel type specified')
                if points is None:
                    raise DeviceError('No points specified')
                chan_str = chan_type
                if chan_label:
                    chan_str += '_%s' % (chan_label)
                query_info = (chan_str, item, item + len(points))
                for p in points:
                    item += 1
                    chan_str = query_points.get('%s_%s' % (chan_type, p))
                    query_chan_str += ':NUMERIC:NORMAL:ITEM%d %s,%d;' % (item, chan_str, i)
                self.query_info.append(query_info)
        query_chan_str += '\n:NUMERIC:NORMAL:VALUE?'

        self.query_str = ':NUMERIC:FORMAT ASCII\nNUMERIC:NORMAL:NUMBER %d\n' % (item) + query_chan_str
        # print self.query_str
        # print self.query_info

        self.open()

    def open(self):
        try:
            if self.params['comm'] == 'GPIB':
                raise NotImplementedError('The driver for plain GPIB is not implemented yet. ' +
                                          'Please use VISA which supports also GPIB devices')
            elif self.params['comm'] == 'VISA':
                try:
                    # sys.path.append(os.path.normpath(self.visa_path))
                    import visa
                    self.rm = visa.ResourceManager()
                    self.conn = self.rm.open_resource(self.params['visa_address'])

                except Exception, e:
                    raise DeviceError('PZ4000 communication error: %s' % str(e))

            else:
                raise ValueError('Unknown communication type %s. Use GPIB or VISA' % self.params['comm'])

        except Exception, e:
            raise DeviceError(str(e))


    def close(self):
        """
                Close any open communications resources associated with the grid
                simulator.
                """
        if self.params['comm'] == 'GPIB':
            raise NotImplementedError('The driver for plain GPIB is not implemented yet.')
        elif self.params['comm'] == 'VISA':
            try:
                if self.rm is not None:
                    if self.conn is not None:
                        self.conn.close()
                    self.rm.close()


            except Exception, e:
                raise DeviceError('PZ4000 communication error: %s' % str(e))
        else:
            raise ValueError('Unknown communication type %s. Use Serial, GPIB or VISA' % self.params['comm'])

    def cmd(self, cmd_str):
        try:
            self.conn.write(cmd_str)

        except Exception, e:
            raise DeviceError('PZ4000 communication error: %s' % str(e))

    def query(self, cmd_str):
        self.cmd(cmd_str)
        resp = self.conn.read()
        return resp

    def info(self):
        return self.query('*IDN?')

    def data_read(self):
        rec = {'time': time.time()}
        data = self.query(self.query_str).split(',')
        # extract points for each channel
        for info in self.query_info:
            rec[info[0]] = tuple(data[info[1]:info[2]])

        return rec

if __name__ == "__main__":

    pass
