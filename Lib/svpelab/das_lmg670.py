import os
from . import das
from . import device_lmg670

lmg670_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'ZIMMER ZES LMG670'
}


def das_info():
    """
    Returns a dictionary containing information about the LMG670 data acquisition system.
    
    The dictionary includes the name of the module and the mode of operation.
    """
    return lmg670_info


def params(info, group_name=None):
    """
    Define LMG670 DAS parameters.

    Args:
        info (object): Configuration object to add parameters to.
        group_name (str, optional): Name of the parameter group.

    Adds LMG670-specific parameters to the configuration, including
    communication settings, sample intervals, and channel configurations.
    """
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = lmg670_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode, active=gname('mode'), active_value=mode,
                     glob=True)
    info.param(pname('pf_convention'), label='Power Factor Convention', default='Sunspec_EEI', values=['Sunspec_EEI', 'DAQ'])
    info.param(pname('comm'), label='Communications Interface', default='Ethernet', values=['Ethernet'])
    info.param(pname('ip_address'), label='IP address', default='10.0.0.111')
    info.param(pname('sample_interval'), label='Sample Interval (ms)', default=1000)
    info.param(pname('timestamp'), label='Timestamp source', default='Zimmer', values=['Zimmer', 'SVP'])
    info.param(pname('scale_i_inverse'), label='Negative Scale I factor', default='True', values=['True', 'False'])
    # group 1 parameters
    info.param(pname('group_1'), label='Group 1', default='1 channel',
               values=['Unused', '1 channel', '2 channels', '3 channels'])
    info.param(pname('group_1_type'), label='Group 1 type', default='AC', values=['AC', 'DC'], active=pname('group_1'),
               active_value=['1 channel', '2 channels', '3 channels'])
    info.param(pname('wiring_group1_1channel'), label='Wiring configuration group 1', default='Direct', values=['Direct'],
               active=pname('group_1'), active_value='1 channel')
    info.param(pname('wiring_group1_2channel'), label='Wiring configuration group 1', default='Direct',
               values=['Direct', 'Aron'], active=pname('group_1'), active_value='2 channels')
    info.param(pname('wiring_group1_3channel'), label='Wiring configuration group 1', default='Direct',
               values=['Direct', 'Star', 'Delta'], active=pname('group_1'), active_value='3 channels')
    # group 2 parameters
    info.param(pname('group_2'), label='Group 2', default='Unused',
               values=['Unused', '1 channel', '2 channels', '3 channels'])
    info.param(pname('group_2_type'), label='Group 2 type', default='AC', values=['AC', 'DC'], active=pname('group_2'),
               active_value=['1 channel', '2 channels', '3 channels'])
    info.param(pname('wiring_group2_1channel'), label='Wiring configuration group 2', default='Direct', values=['Direct'],
               active=pname('group_2'), active_value='1 channel')
    info.param(pname('wiring_group2_2channel'), label='Wiring configuration group 2', default='Direct',
               values=['Direct', 'Aron'], active=pname('group_2'), active_value='2 channels')
    info.param(pname('wiring_group2_3channel'), label='Wiring configuration group 2', default='Direct',
               values=['Direct', 'Star', 'Delta'], active=pname('group_2'), active_value='3 channels')
    # group 3 parameters
    info.param(pname('group_3'), label='Group 3', default='Unused',
               values=['Unused', '1 channel', '2 channels', '3 channels'])
    info.param(pname('group_3_type'), label='Group 3 type', default='AC', values=['AC', 'DC'], active=pname('group_3'),
               active_value=['1 channel', '2 channels', '3 channels'])
    info.param(pname('wiring_group3_1channel'), label='Wiring configuration group 3', default='Direct',
               values=['Direct'],
               active=pname('group_3'), active_value='1 channel')
    info.param(pname('wiring_group3_2channel'), label='Wiring configuration group 3', default='Direct',
               values=['Direct', 'Aron'], active=pname('group_3'), active_value='2 channels')
    info.param(pname('wiring_group3_3channel'), label='Wiring configuration group 3', default='Direct',
               values=['Direct', 'Star', 'Delta'], active=pname('group_3'), active_value='3 channels')
    # group 4 parameters
    info.param(pname('group_4'), label='Group 4', default='Unused',
               values=['Unused', '1 channel', '2 channels', '3 channels'])
    info.param(pname('group_4_type'), label='Group 4 type', default='AC', values=['AC', 'DC'], active=pname('group_4'),
               active_value=['1 channel', '2 channels', '3 channels'])
    info.param(pname('wiring_group4_1channel'), label='Wiring configuration group 4', default='Direct',
               values=['Direct'],
               active=pname('group_4'), active_value='1 channel')
    info.param(pname('wiring_group4_2channel'), label='Wiring configuration group 4', default='Direct',
               values=['Direct', 'Aron'], active=pname('group_4'), active_value='2 channels')
    info.param(pname('wiring_group4_3channel'), label='Wiring configuration group 4', default='Direct',
               values=['Direct', 'Star', 'Delta'], active=pname('group_4'), active_value='3 channels')
    # group 5 parameters
    info.param(pname('group_5'), label='Group 5', default='Unused',
               values=['Unused', '1 channel', '2 channels', '3 channels'])
    info.param(pname('group_5_type'), label='Group 5 type', default='AC', values=['AC', 'DC'], active=pname('group_5'),
               active_value=['1 channel', '2 channels', '3 channels'])
    info.param(pname('wiring_group5_1channel'), label='Wiring configuration group 5', default='Direct',
               values=['Direct'],
               active=pname('group_5'), active_value='1 channel')
    info.param(pname('wiring_group5_2channel'), label='Wiring configuration group 5', default='Direct',
               values=['Direct', 'Aron'], active=pname('group_5'), active_value='2 channels')
    info.param(pname('wiring_group5_3channel'), label='Wiring configuration group 5', default='Direct',
               values=['Direct', 'Star', 'Delta'], active=pname('group_5'), active_value='3 channels')
    # group 6 parameters
    info.param(pname('group_6'), label='Group 6', default='Unused',
               values=['Unused', '1 channel', '2 channels'])
    info.param(pname('group_6_type'), label='Group 6 type', default='AC', values=['AC', 'DC'], active=pname('group_6'),
               active_value=['1 channel', '2 channels'])
    info.param(pname('wiring_group6_1channel'), label='Wiring configuration group 6', default='Direct',
               values=['Direct'],
               active=pname('group_6'), active_value='1 channel')
    info.param(pname('wiring_group6_2channel'), label='Wiring configuration group 6', default='Direct',
               values=['Direct', 'Aron'], active=pname('group_6'), active_value='2 channels')
    # group 7 parameters
    info.param(pname('group_7'), label='Group 7', default='Unused',
               values=['Unused', '1 channel'])
    info.param(pname('group_7_type'), label='Group 7 type', default='AC', values=['AC', 'DC'], active=pname('group_7'),
               active_value='1 channel')
    info.param(pname('wiring_group7_1channel'), label='Wiring configuration group 7', default='Direct',
               values=['Direct'],
               active=pname('group_7'), active_value='1 channel')
    # channels parameters
    info.param(pname('chan_1'), label='Channel 1', default='Connected', values=['Connected', 'Unused'], active=pname('group_1'),
               active_value=['1 channel', '2 channels', '3 channels'])
    info.param(pname('chan_1_label'), label='Channel 1 Label', default='1', active=pname('chan_1'),
               active_value=['Connected'])
    info.param(pname('chan_1_i_ratio'), label='Scale I(mV/A)', default='0.9923', active=pname('chan_1'),
               active_value=['Connected'])
    info.param(pname('chan_2'), label='Channel 2', default='Unused', values=['Connected', 'Unused'], active=pname('group_1'),
               active_value=['1 channel', '2 channels', '3 channels'])
    info.param(pname('chan_2_label'), label='Channel 2 Label', default='2', active=pname('chan_2'),
               active_value=['Connected'])
    info.param(pname('chan_2_i_ratio'), label='Scale I(mV/A)', default='1.0002', active=pname('chan_2'),
               active_value=['Connected'])
    info.param(pname('chan_3'), label='Channel 3', default='Unused', values=['Connected', 'Unused'], active=pname('group_1'),
               active_value=['1 channel', '2 channels', '3 channels'])
    info.param(pname('chan_3_label'), label='Channel 3 Label', default='3', active=pname('chan_3'),
               active_value=['Connected'])
    info.param(pname('chan_3_i_ratio'), label='Scale I(mV/A)', default='0.9971', active=pname('chan_3'),
               active_value=['Connected'])
    info.param(pname('chan_4'), label='Channel 4', default='Unused', values=['Connected', 'Unused'], active=pname('group_1'),
               active_value=['1 channel', '2 channels', '3 channels'])
    info.param(pname('chan_4_label'), label='Channel 4 Label', default='4', active=pname('chan_4'),
               active_value=['Connected'])
    info.param(pname('chan_4_i_ratio'), label='Scale I(mV/A)', default='1.0000', active=pname('chan_4'),
               active_value=['Connected'])
    info.param(pname('chan_5'), label='Channel 5', default='Unused', values=['Connected', 'Unused'], active=pname('group_1'),
               active_value=['1 channel', '2 channels', '3 channels'])
    info.param(pname('chan_5_label'), label='Channel 5 Label', default='5', active=pname('chan_5'),
               active_value=['Connected'])
    info.param(pname('chan_5_i_ratio'), label='Scale I(mV/A)', default='1.0000', active=pname('chan_5'),
               active_value=['Connected'])
    info.param(pname('chan_6'), label='Channel 6', default='Unused', values=['Connected', 'Unused'], active=pname('group_1'),
               active_value=['1 channel', '2 channels', '3 channels'])
    info.param(pname('chan_6_label'), label='Channel 6 Label', default='6', active=pname('chan_6'),
               active_value=['Connected'])
    info.param(pname('chan_6_i_ratio'), label='Scale I(mV/A)', default='1.0000', active=pname('chan_6'),
               active_value=['Connected'])
    info.param(pname('chan_7'), label='Channel 7', default='Unused', values=['Connected', 'Unused'], active=pname('group_1'),
               active_value=['1 channel', '2 channels', '3 channels'])
    info.param(pname('chan_7_label'), label='Channel 7 Label', default='7', active=pname('chan_7'),
               active_value=['Connected'])
    info.param(pname('chan_7_i_ratio'), label='Scale I(mV/A)', default='1.0000', active=pname('chan_7'),
               active_value=['Connected'])

GROUP_NAME = 'lmg670'


class DAS(das.DAS):
    """
    LMG670 Data Acquisition System Implementation

    This class provides specific functionality for the LMG670 DAS device,
    including initialization, channel configuration, and data handling.

    Parameters:
    -----------
    - ts (object): Test script object
    - group_name (str): Name of the DAS group
    - points (int): Data points to capture
    - sc_points (int): Soft channel points
    - support_interfaces (dict): Dictionary of supported interfaces

    Inherits methods from das.DAS for data capture, reading, and waveform operations.
    """
    
    def __init__(self, ts, group_name, points=None, sc_points=None, support_interfaces=None):
        das.DAS.__init__(self, ts, group_name, points=points, sc_points=sc_points)
        self.params['ip_address'] = self._param_value('ip_address')
        self.params['comm'] = self._param_value('comm')
        self.params['sample_interval'] = self._param_value('sample_interval')
        self.params['timestamp'] = self._param_value('timestamp')
        self.params['scale_i_inverse'] = self._param_value('scale_i_inverse')
        self.params['pf_convention'] = self._param_value('pf_convention')

        # create channel info for each channel from parameters
        channels = [None]
        groups = []
        counter = 0
        grouping = ''
        for i in range(1, 8):
            if self._param_value('group_%d' % i) != 'Unused':
                channel_in_group = int(self._param_value('group_%d' % (i))[0])
                group_wiring = self._param_value('wiring_group%d_%dchannel' % (i, channel_in_group))
                group = {'wiring': group_wiring}
                grouping += (',%d' % channel_in_group)
                groups.append(group)
                for j in range(1, channel_in_group + 1):
                    counter += 1
                    chan_type = self._param_value('group_%d_type' % i)
                    chan_label = self._param_value('chan_%d_label' % counter)
                    chan_ratio = self._param_value('chan_%d_i_ratio' % i)
                    if chan_label == 'None':
                        chan_label = ''
                    chan = {'type': chan_type, 'points': self.points.get(chan_type), 'label': chan_label, 'ratio': chan_ratio}
                    channels.append(chan)
            elif counter < 7:
                for j in range(counter + 1, 8):
                    grouping += (',%d' % 1)
                    counter += 1
                    chan_type = self._param_value('chan_%d' % j)
                    chan_label = self._param_value('chan_%d_label' % j)
                    chan_ratio = self._param_value('chan_%d_i_ratio' % (i - 1))
                    if chan_label == 'None':
                        chan_label = ''
                    chan = {'type': chan_type, 'points': self.points.get(chan_type), 'label': chan_label,
                            'ratio': chan_ratio}
                    channels.append(chan)
            else:
                groups.insert(0, grouping[1:])
                break

        self.params['channels'] = channels
        self.params['groups'] = groups

        self.device = device_lmg670.Device(self.params)
        self.data_points = self.device.data_points

        # initialize soft channel points
        self._init_sc_points()

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)


if __name__ == "__main__":
    pass


