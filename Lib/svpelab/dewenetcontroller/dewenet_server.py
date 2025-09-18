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


"""






""" Server for the DeweNetController

This module contains the server, which is necessary for real time communication
with the DeweSoft Net interface.

The DeweSoft will send its measured values to this server.
"""

import socket
import struct
import codecs

import threading
import logging


class DeweNetControllerServer(threading.Thread):
    """TCP Server for communication with the DeweSoft Net interface.

    The server will receive actual measurement values from the DeweSoft unit.
    Therefore a real time communication with actual data transport can be built
    up.

    Usage: The server must be initialized by the controller. Therefore it needs
    a list of channels (order is related), which is transmitted to the DeweSoft
    system by the DeweNetControllerClient before.

    The DeweSoft sends packets with actual measurement data to the opened
    server: The list_of_channel and its order is required to translate the
    received packet to the actual data.

    Attributes:
        START_OF_MESSAGE (bytes): Start bytes of packet
        END_OF_MESSAGE (bytes): End bytes of packet

        _logger (logging.logger): Logger of the class
        _server_ip (str): IP address of the server
        _tcp_port (int): TCP port of the server
        _socket: server socket of the server
        _list_of_channels (list): List of DeweChannel
        _keep_running (bool): running flag for the server thread
        read_only_single_values: read only the last value of the incoming
            packet.
        samplerate (int): Samplerate of the current measurement
        _last_chunk (bytes): last received chunk. This state variable will be
            used to temporarily store the last half received message.
    """

    START_OF_MESSAGE = codecs.decode('0001020304050607', 'hex_codec')
    END_OF_MESSAGE = codecs.decode('0706050403020100', 'hex_codec')

    def __init__(self, list_of_channels, server_ip="",
                 tcp_port=9000, read_only_single_values=True,
                 server_socket=None, logger=None):
        """ Constructor

        Args:
            list_of_channels (list): list of strings containing the list of
                channels that will be received from DeweSoft. This list is set
                during the client's prepareTransfer.
            server_ip (str): IP address of the TCP server Default: ""
            tcp_port (int): TCP port of the server Default: 9000
            read_only_single_values (bool): read only last value for
                each channel of the incoming data packet.
            server_socket (socket.socket): Socket for the TCP server
            logger (logging.logger): Logger of the class

        """
        threading.Thread.__init__(self)
        self.daemon = True
        self._logger = logger or logging.getLogger(__name__)

        self._tcp_port = tcp_port
        self._server_ip = server_ip
        self._socket = server_socket or socket.socket(socket.AF_INET,
                                                      socket.SOCK_STREAM)

        self._list_of_channels = list(list_of_channels)
        self._keep_running = True

        self.read_only_single_values = read_only_single_values
        self.samplerate = 1

        self._last_chunk = b''

    def run(self):
        """ Run method of the server thread

        It will opened the server socket at the given port and it will
        wait for incoming packet.
        """
        threading.Thread.run(self)
        self._logger.debug("Start run IP: {}, Port {}".format(self._server_ip,
                                                              self._tcp_port))
        self._socket.bind((self._server_ip, self._tcp_port))
        self._socket.listen(1)

        connection, client = self._socket.accept()
        self._socket.settimeout(5.0)
        self._logger.info("Client connected: " + str(client))

        while self._keep_running:
            try:
                self._handle_message(connection)
            except (KeyboardInterrupt, RuntimeError) as ex:
                self._logger.warn("Stopping server.", ex)
                self._keep_running = False

    def close_server(self):
        """ Close the server thread
        """
        self._logger.info("Close DeweNetControllerServer")
        self._keep_running = False

    def _handle_message(self, connection):
        """ Message parser for incoming packets

        This helper function will parse the incoming message block and convert
        the measurement data to the dedicated channel storage.

        See DeweSoft-NET manual (or DeweChannel module description) for further
        description of the incoming packet

        Args:
            connection: connection that is used to receive data from the socket.
        """
        messages = self._read_messages(connection)

        if self.read_only_single_values:
            messages = messages[-1:]

        for message in messages:
            self._parse_message(message)

    def _read_messages(self, connection):
        """Read messages from the socket.

        Args:
            connection: connection that is used to receive data from the socket.

        Returns:
            list: List of messages that are received. The messages are stored
                as bytes.
        """
        self._logger.debug("Wait for data")

        chunk = [self._last_chunk]

        while True:
            data = connection.recv(4096)
            chunk.append(data)
            if data.find(DeweNetControllerServer.END_OF_MESSAGE) != -1:
                break

        chunk = b''.join(chunk)

        messages, self._last_chunk = _split_messages(
            chunk,
            DeweNetControllerServer.START_OF_MESSAGE,
            DeweNetControllerServer.END_OF_MESSAGE)

        return messages

    def _parse_message(self, chunk):
        """Parse a received message.

        Args:
            chunk (bytes): received data that represents the message in bytes.
        """

        try:
            chunk, header = Header.from_bytes(chunk)
            chunk = self._read_channels(header, chunk)
            # log message
            if self._logger.isEnabledFor(logging.DEBUG):
                outstr = "Received Packet: "
                outstr += header.log_format()
                self._logger.debug(outstr)

        except struct.error as ex:
            self._logger.warn("Error during parsing message", ex)
            return

    def _read_channels(self, header, chunk):
        """Read channel informations from packet

        Args:
            header (Header): Parsed header of the received message.
            chunk (bytes): the packet bytes
        Returns:
            bytes: reduced chunk with removed channel bytes
        """
        # parse and handle channels in the received packet
        for channel in self._list_of_channels:
            chinfo = channel.channel_info
            # get data format and data size from the channel info
            value_size_byte = chinfo.get_value_size()
            value_formatter = chinfo.get_value_format()

            # read samples counter for the next channel
            chunk, samples_nr = _read_number_of_samples(chunk)

            # Read only the last values of the received packet
            # or read all values of the packet
            if samples_nr > 0 and self.read_only_single_values:
                range_begin = samples_nr - 1
            else:
                range_begin = 0

            # Read list of values
            for i in range(range_begin, samples_nr):

                begin_chunk_index = i * value_size_byte
                end_chunk_index = begin_chunk_index + value_size_byte
                sample_value = struct.unpack_from(
                    "<" + value_formatter,
                    memoryview(chunk[begin_chunk_index:end_chunk_index]))[0]

                # read timestamp
                if chinfo.type == "sync":
                    timestamp_sample_index = header.samples_acquired_so_far + \
                        (i * chinfo.samplerate_divider)

                    timestamp_sample = \
                        float(timestamp_sample_index) / float(self.samplerate)

                elif chinfo.type == "async":
                    delta_index_time_value = samples_nr * value_size_byte
                    begin_time_index = i * 8 + delta_index_time_value
                    end_time_index = begin_time_index + 8

                    timestamp_sample = struct.unpack_from(
                        "<d",
                        memoryview(chunk[begin_time_index:end_time_index]))[0]

                else:  # also if chinfo.type == "single":
                    timestamp_sample = header.time_of_packet_in_sec

                # Set the value
                channel.set_value(sample_value, timestamp_sample)

            # Remove from chunk
            begin_next = samples_nr * value_size_byte
            if chinfo.type == "async":
                begin_next += samples_nr * 8
            chunk = chunk[begin_next:]

        return chunk


def _split_messages(chunk, som, eom):
    """Split messages from the chunk.

    Args:
        chunk (bytes): Received data containing multiple messages.
        som (bytes): Start bytes of message
        eom (bytes): End bytes of message

    Returns:
        list: containing two elements
            list: list of splitted messages in bytes.
            bytes: end part containing half received message. This part can
                be used during the next receiving of data.
    """
    end_part = b''
    first_som = chunk.find(som)
    if first_som == -1:
        return [], end_part
    elif first_som > 0:
        chunk = chunk[first_som:]

    last_eom = chunk.rfind(eom)
    if last_eom == -1:
        return [], [chunk]
    elif last_eom <= len(chunk) - len(eom):
        end_part = chunk[last_eom+len(eom):]
        chunk = chunk[:last_eom+len(eom)]
    else:
        raise Exception("Split Messages: Len of chunk is too low")

    messages = chunk.split(som)
    messages = [msg[:msg.rfind(eom)] for msg in messages if msg]

    return messages, end_part

def _read_number_of_samples(chunk):
    """Read the number from samples of a channel
    Args:
        chunk (bytes): the packet bytes
    Returns:
        bytes: reduced chunk with removed channel bytes
    """
    # pylint: disable=R0201
    samples_nr = (struct.unpack_from("<i", memoryview(chunk)))[0]
    return chunk[4:], samples_nr

class Header:
    """Read header elements from DeweSoft

    See: dewenet_data.py for more information

    Attributes:
        packet_size (int): Size in bytes of the whole packet
        packet_type (int): Always 0 = data packet
        samples_sync_in_packet (int): number of samples in packet
        samples_acquired_so_far (long): number of acquired samples
        time_of_packet_in_sec (float): timestamp of the packet
    """

    def __init__(self):
        """Constructor
        """
        self.packet_size = None
        self.packet_type = None
        self.samples_sync_in_packet = None
        self.samples_acquired_so_far = None
        self.time_of_packet_in_sec = None

    def log_format(self):
        """Return a log formated string of attributes.

        Returns:
            str: formatted string of header elements
        """
        outstr = ("\tPacket Size: {}"
                  "\tSync. Samples in Packet: {}"
                  "\tTime of Packet: {}"
                  "\tAbs. No of Packets: {}"
                  "\tPacket Type: {}".format(
                      self.packet_size, self.samples_sync_in_packet,
                      self.time_of_packet_in_sec,
                      self.samples_acquired_so_far, self.packet_type))
        return outstr

    @staticmethod
    def from_bytes(chunk):
        """Generate a header element from a byte string

        Args:
            chunk (bytes): Read bytes from DeweSoft
        Returns:
            bytes: reduced chunk with removed header bytes
            Header: generated header containing read elements
        """
        packet_header = struct.unpack_from("<iiiqd",
                                           memoryview(chunk))
        header = Header()
        header.packet_size = packet_header[0]
        header.packet_type = packet_header[1]  # Always 0
        header.samples_sync_in_packet = packet_header[2]
        header.samples_acquired_so_far = packet_header[3]
        header.time_of_packet_in_sec = packet_header[4] * 86400

        return chunk[28:], header
