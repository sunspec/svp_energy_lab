
import sys
import os
import glob
import importlib


'''
The network module is designed to capture network traffic

Initial design - 8/10/22 - jayatsandia
'''

NET_modules = {}

def params(info, id=None, label='Network Capture System', group_name=None, active=None, active_value=None):
    if group_name is None:
        group_name = NET_DEFAULT_ID
    else:
        group_name += '.' + NET_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    name = lambda name: group_name + '.' + name
    info.param_group(group_name, label='%s Parameters' % label, active=active, active_value=active_value, glob=True)
    info.param(name('mode'), label='Mode', default='Disabled', values=['Disabled'])
    for mode, m in NET_modules.items():
        m.params(info, group_name=group_name)

NET_DEFAULT_ID = 'NET'


def net_init(ts, id=None, group_name=None, support_interfaces=None):
    """
    Function to create specific NET implementation instances.
    """
    if group_name is None:
        group_name = NET_DEFAULT_ID
    else:
        group_name += '.' + NET_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    mode = ts.param_value(group_name + '.' + 'mode')
    sim = None
    if mode != 'Disabled':
        sim_module = NET_modules.get(mode)
        print(sim_module)
        if sim_module is not None:
            sim = sim_module.NET(ts, group_name, support_interfaces=support_interfaces)
        else:
            raise NETError('Unknown network acquisition system mode: %s' % mode)

    return sim


class NETError(Exception):
    """
    Exception to wrap all NET generated exceptions.
    """
    pass


class NET(object):

    def __init__(self, ts, group_name, support_interfaces=None):
        """
        Initialize the NET object with the following parameters

        :param ts: test script with logging capability
        :param group_name: name used when there are multiple instances
        :param support_interfaces: dictionary with keys 'pvsim', 'gridsim', 'hil', etc.
        """
        self.ts = ts
        self.group_name = group_name
        self.capture = None
        
        # Probably will never be used, but you never know if there are is a need
        # to have access to the pvsim, gridsim, or hil in the network capture module
        self.hil = None
        if support_interfaces is not None:
            if support_interfaces.get('hil') is not None:
                self.hil = support_interfaces.get('hil')

        self.gridsim = None
        if support_interfaces is not None:
            if support_interfaces.get('gridsim') is not None:
                self.gridsim = support_interfaces.get('gridsim')

        self.pvsim = None
        if support_interfaces is not None:
            if support_interfaces.get('pvsim') is not None:
                self.pvsim = support_interfaces.get('pvsim')

        # determine SVP Result directory path
        self.net_dir = os.path.join(self.ts._results_dir, self.ts._result_dir)
        # self.ts.log_debug('Network data will be saved to %s' % self.net_dir)

    def info(self):
        """
        Return information string for the NET device.
        """
        if self.device is None:
            raise NETError('NET device not initialized')
        return self.device.info()

    def get_packets(self, iface=None, timeout=None, bpf_filter=None, filename=None, count=None):
        """
        Start data capture and collect packets.

        :param interface: NIC interface, e.g., 'eth0'
        :param timeout: duration of the capture, e.g., 60 seconds
        :param bpf_filter: Berkeley packet filter, e.g., "tcp and port 80"
        :param filename: name of the file to save to the manifest
        :param count: number of packets to capture
        """
        pass
    
    def print_capture(self, n_packets=None):
        pass

    def get_signal_data(self):
        """
        Convert packets into dict of information for the given application.

        :return: dict with singal data
        """
        return {}

    def save_packets(self):
        """
        Save pcap to net_dir directory
        """
        pass

    def filter_packets(self):
        """
        Apply filter on the captured packets
        """
        pass

def net_scan():
    global NET_modules
    # scan all files in current directory that match net_*.py
    package_name = '.'.join(__name__.split('.')[:-1])
    files = glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'net_*.py'))
    for f in files:
        module_name = None
        try:
            module_name = os.path.splitext(os.path.basename(f))[0]
            # print(module_name)
            if package_name:
                module_name = package_name + '.' + module_name
            m = importlib.import_module(module_name)
            if hasattr(m, 'net_info'):
                info = m.net_info()
                mode = info.get('mode')
                # place module in module dict
                if mode is not None:
                    NET_modules[mode] = m
            else:
                if module_name is not None and module_name in sys.modules:
                    del sys.modules[module_name]
        except Exception as e:
            if module_name is not None and module_name in sys.modules:
                del sys.modules[module_name]
            print(NETError('Error scanning module %s: %s' % (module_name, str(e))))

# scan for NET modules on import
net_scan()

if __name__ == "__main__":
    pass
