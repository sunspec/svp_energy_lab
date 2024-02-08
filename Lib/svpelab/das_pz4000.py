
import os
from . import das
from . import device_pz4000



pz4000_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Yokogawa PZ4000'
}

def das_info():
    return pz4000_info 

def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = pz4000_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,active=gname('mode'),  active_value=mode, glob=True)
    info.param(pname('comm'), label='Communications Interface', default='VISA', values=['VISA', 'GPIB'])
    info.param(pname('visa_address'), label='VISA address', default='GPIB0::6::INSTR')
    info.param(pname('sample_interval'), label='Sample Interval (ms)', default=1000)

    info.param(pname('chan_1'), label='Channel 1', default='AC', values=['AC', 'DC', 'Unused'])
    info.param(pname('chan_2'), label='Channel 2', default='AC', values=['AC', 'DC', 'Unused'])
    info.param(pname('chan_3'), label='Channel 3', default='AC', values=['AC', 'DC', 'Unused'])
    info.param(pname('chan_4'), label='Channel 4', default='DC', values=['AC', 'DC', 'Unused'])
    
    info.param(pname('chan_1_label'), label='Channel 1 Label', default='1', active=pname('chan_1'),active_value=['AC', 'DC'])
    info.param(pname('chan_2_label'), label='Channel 2 Label', default='2', active=pname('chan_2'),active_value=['AC', 'DC'])
    info.param(pname('chan_3_label'), label='Channel 3 Label', default='3', active=pname('chan_3'),active_value=['AC', 'DC'])
    info.param(pname('chan_4_label'), label='Channel 4 Label', default='', active=pname('chan_4'),active_value=['AC', 'DC'])

    '''
    info.param(pname('wiring_system'), label='Wiring System', default='1P2W', values=['1P2W', '1P3W', '3P3W','3P4W', '3P3W(3V3A)'])
    '''
    # info.param(pname('ip_port'), label='IP Port',
    #            active=pname('comm'),  active_value=['Network'], default=4944)
    # info.param(pname('ip_timeout'), label='IP Timeout',
    #            active=pname('comm'),  active_value=['Network'], default=5)

GROUP_NAME = 'pz4000'


class DAS(das.DAS):
    """
    Template for data acquisition (DAS) implementations. This class can be used as a base class or
    independent data acquisition classes can be created containing the methods contained in this class.
    """

    def __init__(self, ts, group_name, points=None, sc_points=None):

        das.DAS.__init__(self, ts, group_name, points=points, sc_points=sc_points)
        self.params['visa_address'] = self._param_value('visa_address')
        self.params['comm'] = self._param_value('comm')
        self.params['timeout'] = self._param_value('ip_timeout')
        # self.params['wiring_system'] = self._param_value('wiring_system')
        self.params['sample_interval'] = self._param_value('sample_interval')

        # create channel info for each channel from parameters
        channels = [None]
        for i in range(1,5):
            chan = None
            chan_type = self._param_value('chan_%d' % (i))
            chan_label = self._param_value('chan_%d_label' % (i))
            if chan_label == 'None':
                chan_label = ''
            if chan_type == 'AC':
                chan = {'type': 'ac', 'points': self.points['ac'], 'label':  chan_label}
            elif chan_type == 'DC':
                chan = {'type': 'dc', 'points': self.points['dc'], 'label':  chan_label}
            channels.append(chan)

        self.params['channels'] = channels

        self.device = device_pz4000.Device(self.params)

        #config here

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)


if __name__ == "__main__":

    pass


