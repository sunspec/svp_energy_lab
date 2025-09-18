'''
pyshark network capture

Initial design - 8/10/22 - jayatsandia
'''

import os
import time
import asyncio

try: 
    from . import network
except Exception as e:
    print('Cannot find network.py in svpelab')
try: 
    import pyshark
except Exception as e:
    print('Missing pyshark. Install with "pip install pyshark"')
try: 
    import pandas as pd
except Exception as e:
    print('Missing pyshark. Install with "pip install pandas"')


manual_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'PyShark'
}

def net_info():
    return manual_info

def params(info, group_name):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = manual_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'), active_value=mode, glob=True)
    info.param(pname('interface'), label='Communications Interface', default='eth0')
    info.param(pname('timeout'), label='Default Capture Duration', default=60.)
    info.param(pname('bpf_filter'), label='Default BPF filter', default='tcp')


GROUP_NAME = 'pyshark'

class NET(network.NET):

    def __init__(self, ts, group_name, support_interfaces=None):
        network.NET.__init__(self, ts, group_name, support_interfaces)
        self.interface = self._param_value('interface')
        self.timeout = self._param_value('timeout')
        self.bpf_filter = self._param_value('bpf_filter')
        self.capture = None
        self.packet_list = []
        
        # save locally if not running with SVP GUI
        if not hasattr(self, 'net_dir'):
            self.net_dir = os.path.realpath(__file__)
        print('net_dir = %s' % self.net_dir)

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def info(self):
        """
        Return information string for the NET device.
        """
        return 'PyShark Network Capture'

    def pkt_callback(self, pkt):
        self.packet_list.append(pkt)
        try:
            if 'ipv6' in [l.layer_name for l in pkt.layers]:
                src_addr = pkt.ipv6.src
                dst_addr = pkt.ipv6.dst
                src_port = pkt.tcp.srcport
                dst_port = pkt.tcp.dstport
                size = int(pkt.ipv6.plen)
            else:
                src_addr = pkt.ip.src
                dst_addr = pkt.ip.dst
                src_port = pkt.tcp.srcport
                dst_port = pkt.tcp.dstport
                size = int(pkt.ip.get_field('Len'))

            timestamp = float(pkt.sniff_timestamp) - self.start_time
            protocol = pkt.transport_layer    # protocol type

            # self.ts.log("%0.4f   %s:%s <-> %s:%s (%s)" % (timestamp, src_addr, src_port, dst_addr, dst_port, protocol))
        except AttributeError as e:
            pass  # ignore some packets


    def net_capture(self, interface=None, timeout=None, bpf_filter=None, filename=None):
        """
        Get data capture.

        :param interface: NIC interface, e.g., 'eth0'
        :param timeout: duration of the capture, e.g., 60 seconds
        :param filter: Berkeley packet filter, e.g., "tcp and port 80"
        """
        if interface is None:
            interface = self.interface
        if timeout is None: 
            timeout = self.timeout
        if bpf_filter is None:
            bpf_filter = self.bpf_filter
            if bpf_filter is None or bpf_filter == 'None':
                bpf_filter = ''  # None is an invalid filter
        if bpf_filter is None:
            bpf_filter = self.bpf_filter
        if filename is None:
            filename = time.asctime(time.localtime()).replace(':', '-').replace(' ', '_')
        if filename[-5:] != '.pcap':
            filename += '.pcap'

        output_file = os.path.join(self.net_dir, filename)
        self.ts.log_debug('Interface = %s, Timeout = %s, Filter = %s, output_file = %s' % (interface, timeout, bpf_filter, output_file))

        # Configure Capture
        self.capture = pyshark.LiveCapture(interface=interface, bpf_filter=bpf_filter, output_file=output_file, custom_parameters='')
        self.capture.set_debug()  # printed to %USERPROFILE%\.sunspec\sunssvp_script.log
        if self.ts is not None: 
            self.ts.log('Capturing network traffic for %0.2f seconds' % timeout)
        else:
            print('Capturing network traffic for %0.2f seconds' % timeout)

        print('Capture = %s' % self.capture)
        # Begin Capture
        self.start_time = time.time()
        try:
            print('Starting capture')
            self.capture.apply_on_packets(self.pkt_callback, timeout=5)
            # capture.sniff(timeout=5)  # this wasn't working...
        except asyncio.TimeoutError:
            pass

        self.ts.log('Capture Complete with %s packets' % len(self.packet_list))

    def print_capture(self, n_packets=None):
        """
        Print n_packets from capture.
        """
        if n_packets is None or len(self.packet_list) < n_packets:
            n_packets = len(self.packet_list)
            self.ts.log('Printing all %s packets from network capture.' % n_packets)
        else:
            self.ts.log('Printing first %s packets from network capture.' % n_packets)

        # attribute_list = []
        # for packet in self.packet_list[:n_packets]:
        #     try:
        #         packet_version = packet.layers[1].version
        #         layer_name = packet.layers[2].layer_name
        #         attribute_list.append([packet_version, layer_name, packet.length, str(packet.sniff_time)])
        #     except AttributeError:
        #         pass

        # df = pd.DataFrame(attribute_list, columns=['packet version', 'layer type', 'length', 'capture time'])
        # self.ts.log(df)

        count = 0
        for pkt in self.packet_list[:n_packets]:
            count += 1
            try:
                if 'ipv6' in [l.layer_name for l in pkt.layers]:
                    src_addr = pkt.ipv6.src
                    dst_addr = pkt.ipv6.dst
                    src_port = pkt.tcp.srcport
                    dst_port = pkt.tcp.dstport
                    size = int(pkt.ipv6.plen)
                else:
                    src_addr = pkt.ip.src
                    dst_addr = pkt.ip.dst
                    src_port = pkt.tcp.srcport
                    dst_port = pkt.tcp.dstport
                    size = int(pkt.ip.get_field('Len'))

                timestamp = float(pkt.sniff_timestamp) - self.start_time
                protocol = pkt.transport_layer    # protocol type

                self.ts.log("%4d   t=%0.4f   %s:%s <-> %s:%s (%s)" % (count, timestamp, src_addr, src_port, 
                                                                     dst_addr, dst_port, protocol))
            except AttributeError as e:
                pass  # ignore some packets
            except Exception as e:
                self.ts.log_warning('Unable to print packet. %s' % e)

if __name__ == "__main__":

    capture = pyshark.LiveCapture(interface='Local Area Connection', bpf_filter='', output_file='test.pcap')
    capture.sniff(timeout=5)

    for packet in capture.sniff_continuously(packet_count=10):
        try:
            # get timestamp
            localtime = time.asctime(time.localtime(time.time()))
         
            # get packet content
            protocol = packet.transport_layer    # protocol type
            src_addr = packet.ip.src             # source address
            src_port = packet[protocol].srcport  # source port
            dst_addr = packet.ip.dst             # destination address
            dst_port = packet[protocol].dstport  # destination port

            # output packet info
            print ("%s IP %s:%s <-> %s:%s (%s)" % (localtime, src_addr, src_port, dst_addr, dst_port, protocol))
        except AttributeError as e:
            # ignore packets other than TCP, UDP and IPv4
            pass