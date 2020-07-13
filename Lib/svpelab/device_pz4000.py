
import time

# map data points to query points
query_points = {
    'AC_VRMS': 'URMS',
    'AC_IRMS': 'IRMS',
    'AC_P': 'P',
    'AC_S': 'S',
    'AC_Q': 'Q',
    'AC_PF': 'LAMBDA',
    'AC_FREQ': 'FU',
    'DC_V': 'UDC',
    'DC_I': 'IDC',
    'DC_P': 'P'
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
        self.data_points = ['TIME']
        # Resource Manager for VISA
        self.rm = None
        # Connection to instrument for VISA-GPIB
        self.conn = None

        # create query string for configured channels
        query_chan_str = ''
        item = 0
        for i in range(1,5):
            chan = self.channels[i]
            if chan is not None:
                chan_type = chan.get('type')
                points = chan.get('points')
                chan_label = chan.get('label')
                if chan_type is None:
                    raise DeviceError('No channel type specified')
                if points is None:
                    raise DeviceError('No points specified')
                for p in points:
                    item += 1
                    point_str = '%s_%s' % (chan_type, p)
                    chan_str = query_points.get(point_str)
                    query_chan_str += ':NUMERIC:NORMAL:ITEM%d %s,%d;' % (item, chan_str, i)
                    if chan_label:
                        point_str = '%s_%s' % (point_str, chan_label)
                    self.data_points.append(point_str)
        query_chan_str += '\n:NUMERIC:NORMAL:VALUE?'

        self.query_str = ':NUMERIC:FORMAT ASCII\nNUMERIC:NORMAL:NUMBER %d\n' % (item) + query_chan_str

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

                except Exception as e:
                    raise DeviceError('PZ4000 communication error: %s' % str(e))

            else:
                raise ValueError('Unknown communication type %s. Use GPIB or VISA' % self.params['comm'])

        except Exception as e:
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


            except Exception as e:
                raise DeviceError('PZ4000 communication error: %s' % str(e))
        else:
            raise ValueError('Unknown communication type %s. Use Serial, GPIB or VISA' % self.params['comm'])

    def cmd(self, cmd_str):
        try:
            self.conn.write(cmd_str)

        except Exception as e:
            raise DeviceError('PZ4000 communication error: %s' % str(e))

    def query(self, cmd_str):
        self.cmd(cmd_str)
        resp = self.conn.read()
        return resp

    def info(self):
        return self.query('*IDN?')

    def data_capture(self, enable=True):
        pass

    def data_read(self):
        data = [float(i) for i in self.query(self.query_str).split(',')]
        data.insert(0, time.time())
        return data

if __name__ == "__main__":

    pass
