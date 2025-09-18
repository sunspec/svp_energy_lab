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






""" Main module for the communication with the DeweSoft over the NET interface

The dewenetcontroller is used to watch the channels of a DeweSoft
measurement unit.

TODO: implement fallback solution if DeweSoft can't connect to the python
server.

TODO: start dewesoft if it isn't running and the dewenetcontroller connects to
    localhost
"""

import logging
import time
import datetime

import numpy as np

from .dewenet_client import DeweNetControllerClient
from .dewenet_server import DeweNetControllerServer
from .dewenet_data import DeweChannel

logging.basicConfig(level=logging.INFO)


class DeweNetController(object):
    """ Main class for communication with DeweSoft measurement system

    Attributes:
        _logger: Logger of the Class
        _client (DeweNetControllerClient): Client for remote control the
            DeweSoft system
        _server (DeweNetControllerServer): Server for receiving measurement
            values from the DeweSoft system.
        _setup_filename (str): Path and name of the setup file that is stored
            on the measurement system
        _storage_filename (str): Path and name of the storage file in the
            DeweSoft measurement system

        samplerate (int): Used sample rate read from DeweSoft (in Hertz)
        starttime (datetime): Start time of the measurement. All measurement
            timestamps are indexes using the samplerate and the starttime to
            get a real timestamp
        stoptime (datetime): Time of the stopped measurement
        is_running (bool): State variable for a running instance/connection
            with the DeweSoft

        _channels (dict): Dictionary of channels to be watched with the name of
            the channel as key.
    """

    def __init__(self, setup_filename=None, storage_filename=None, logger=None, debug = False):
        """Constructor

        Args:
            setup_filename (str): File name and path of the DeweSoft setup file
                stored on the DeweSoft host
            storage_filename (str): File name and path of the DeweSoft
                measurement file stored on the DeweSoft host
            logger (logging.logger): optional logger of the class.
        """

        self._timecount_ = 0.0




        self._logger = logger or logging.getLogger(__name__)

        if debug:
            self._logger.setLevel(logging.DEBUG)

        self._logger.debug("Init DeweNetController")

        self._client = DeweNetControllerClient(logger=self._logger)
        self._server = None

        if setup_filename and setup_filename.endswith(".d7s"):
            self._setup_filename = setup_filename
        else:
            self._logger.warn("No setup file defined")
            self._setup_filename = None

        if storage_filename and storage_filename.endswith(".d7d"):
            self._storage_filename = storage_filename
        else:
            self._logger.warn("No storage file defined")
            self._storage_filename = None

        self.samplerate = None
        self.starttime = None
        self.stoptime = None
        self.is_running = False

        self._channels = dict()

        self.dewe_interface_version = None
        self.dewe_version = None

    def get_dewe_information(self):
        return 'DEWESoft %s (Interface Version: %s)' % (self.dewe_version, self.dewe_interface_version)


    def connect_to_dewe(self, dewe_ip='127.0.0.1', dewe_port=8999,
                        client_server_ip="", client_server_port=9000,
                        list_of_channels=None, samplerate = None,
                        read_only_single_values = False, controlMode = False):
        """Connect to the DeweSoft instances.

        The instance must already be running on the host.

        Args:
            dewe_ip (str): IP address of the running DeweSoft to be controlled.
            dewe_port (int): Port of the running DeweSoft to be controlled.
            client_server_ip (str): Network interface of the server that will be
                opened. If an empty string is set, than from any computer the
                server is reachable.
            client_server_port (int): Port of the server that will be opened to
                receive measurement data.
            list_of_channels (list): List of str. A list of channel names, that
                the client should listen. If None is given than all available
                channels of the DeweSoft measurement will be used.

        Note:
            TODO - start DeweSoft program, if it isn't running exec()
        """

        self._logger.info("Start DeweNetClient ({}: {})".format(dewe_ip,
                                                                dewe_port))
        self.dewe_interface_version, self.dewe_version = self._client.connect_to_dewe(dewe_ip, dewe_port)
        time.sleep(0.2)

        if self._client.dewe_is_measuring():
            self._client.dewe_stop()

        #self._client.dewe_stop()

        if self._setup_filename:
            self._logger.info(
                "Load Setup file: {}".format(self._setup_filename))
            self._client.dewe_load_setupfile(self._setup_filename)
        else:
            self._logger.info(
                "Load no Setup file. Use already running DeweSoft Setup ")

        self._client.dewe_list_used_channels()

        self._logger.info(
            "Available Channels {}".format(
                [ch_info.name for ch_info in
                 list(self._client.available_channels.values())]))

        if not list_of_channels:
            # use all available channels if no definition is given in the args
            list_of_channels = [ch_info.name for ch_info in
                                list(self._client.available_channels.values())]

        for element in list_of_channels:
            if element in self._client.available_channels:
                channel = DeweChannel(self._client.available_channels[element])
                channel.update_handler = self._handling_value_updates
                self._channels[element] = {'ch': channel,
                                           'handlers': list()}

        self._logger.info("Watch Channels: {}".format(list(self._channels.keys())))

        list_server_channels = [ch['ch'] for ch in list(self._channels.values())]
        self._logger.info(
            "Start DeweNetControllerServer ({})".format(client_server_port))
        self._server = DeweNetControllerServer(list_server_channels,
                                               read_only_single_values = read_only_single_values,
                                               server_ip=client_server_ip,
                                               tcp_port=client_server_port,
                                               logger=self._logger)
        self._server.start()

        self._logger.info("Start Transfer")
        if not samplerate:
            self.samplerate = self._client.dewe_get_samplerate()
        else:
            try:
                try:
                    self._client.dewe_set_mode(1)
                except:
                    pass
                self.samplerate = self._client.dewe_set_samplerate(samplerate)
            except:
                self._logger.error("Failed to set custom samplerate")
                raise

        self._server.samplerate = self.samplerate
        channel_list = [ch for ch in list(self._channels.keys())]
        time.sleep(0.2)
        self._client.dewe_init_start_transfer(client_server_port, channel_list)


    def stop_dewe_measurement(self):
        if self._client:
            self._client.dewe_stop()
            self._client.dewe_stop_transfer()
            self.is_running = False


    def start_dewe_measurement(self):
        """Start the measurement of the DeweSoft system.

        This will start an acquisition with or without storage of the DeweSoft
        measuremnt unit.
        """

        if self._storage_filename:
            self._logger.info(
                "Start Acquisition and Storage at {}.".format(
                    self._storage_filename))
            self._client.dewe_set_storing(True)

            self.starttime = self._client.dewe_start_store(
                self._storage_filename)
        else:
            self._logger.info("Start Acquisition only")
            self.starttime = self._client.dewe_start_acquisition()

        self._logger.info(
            "Startup at {} with sample rate {}  Hz".format(self.starttime,
                                                           self.samplerate))
        self.is_running = True

    def disconnect_from_dewe(self):
        """Disconnect from the running DeweSoft measurement system.
        """
        if self.is_running:
            self._logger.info("Disconnect from DeweSoft")
            self._client.dewe_stop_transfer()
            self.stoptime = self._client.dewe_stop()
            self._logger.info(
                "Stopped at {} Measurement Duration: {}".format(
                    self.stoptime, self.stoptime - self.starttime))
        self.close_connections()

    def close_connections(self):
        """Close all opened connections of the DewenetController"""
        self._logger.warn("Close opened Servers and Connections")
        if self._client:
            self._client.disconnect_from_dewe()
        if self._server:
            self._server.close_server()
        self.is_running = False

    def _handling_value_updates(self, name, value, timestamp):
        """Handling callback for channel updates

        This handler will be called if a value of a channel is received. This
        is a single instance handler for all managed channels. This method
        will be called from the internal channel object.

        It will used the registered handler in this class to inform components
        that are using the dewenetcontroller.

        Args:
            name (str): Name of the channel
            value (float): Value of hte measured sample
            timestamp (float): Relative timestamp of the value in seconds since
                start of acquisition
        """
        try:
            delta = datetime.timedelta(seconds=timestamp)

            timestamp = self.starttime + delta
            for handler in self._channels[name]['handlers']:
                handler(name, timestamp, value)

        except OverflowError as ex:
            self._logger.warn(
                "Timestamp ({timestamp}) conversation OverflowError "
                "for {name} {value}:".format(name=name,
                                             value=value,
                                             timestamp=timestamp),
                ex)

    def add_update_value_handler(self, function, channels=None):
        """Add an update handler to the Dewenet Controller.

        The update handler will be called if a channel received an update

        Args:
            function (function): Update handler to be registered
                The update handler must have following ordered arguments:
                    name (str): Name of the channel
                    timestamp (datetime): Time of the measured sample
                    value (float, int): Value of the sample
            channels (list): A list of channel names. The handler will be
                registered to the given channels. If None is set to the list,
                than the handler method will be registered to all available
                channels.
        """

        if not channels:
            channels = list(self._channels.keys())
        for channel in channels:
            if channel in self._channels:
                self._channels[channel]['handlers'].append(function)

    def get_watched_channel(self, channel_name):
        """Get a watched channel by name:

        Args:
            channel_name (str): Name of the DeweSoft channel.

        Returns:
            DeweChannel: The requested channel.
        """
        return self._channels[channel_name]['ch']

    @property
    def watched_channels(self):
        """List of watched channels

        Returns
            list: list of str containing the names of all watched channels.
        """
        return list(self._channels.keys())
