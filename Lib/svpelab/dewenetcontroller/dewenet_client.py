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










"""DeweNetControllerClient module for remote control purposes of the DeweSoft

This module implements the remote control for the communication with the
DeweSoft measurement software. Therefore the class DeweNetControllerClient is
used. This module also implements the used exceptions.


Command reference (DEWESoft NET protocol version 4) from DeweSoft Net Interface
Manual

Each command has to have New line suffix (0x13 + 0x10). Commands in brackets
can only be sent in control mode.

+-------------------+----------------------------------------------------------+
| Command           | Description                                              |
+===================+==========================================================+
| GETVERSION        | returns DEWESoft version                                 |
+-------------------+----------------------------------------------------------+
| GETINTFVERSION    | returns DEWESoft NET protocol version                    |
+-------------------+----------------------------------------------------------+
| GETDATETIME       | returns current time on measurement unit                 |
+-------------------+----------------------------------------------------------+
| GETMODE           | returns current operation mode (control or view)         |
+-------------------+----------------------------------------------------------+
| SETMODE mode      | sets operation mode;                                     |
|                   +-------------------+--------------------------------------+
|                   | mode parameter:   | 0 - view mode                        |
|                   |                   +--------------------------------------+
|                   |                   | 1 - control mode                     |
+-------------------+-----------------------+----------------------------------+
| SETMASTERMODE mode| sets clock mode of the devices, used for synchronize     |
|                   | several devices at the same time                         |
|                   +-------------------+--------------------------------------+
|                   | mode parameter:   | 0 - standalone (if only one system is|
|                   |                   |     used                             |
|                   |                   | 1 - clock master system (clock is    |
|                   |                   |     output from this system to the   |
|                   |                   |     slaves - only one!)              |
|                   |                   | 2 - clock slave mode (clock will be  |
|                   |                   |     received from a master system)   |
+-------------------+-------------------+--------------------------------------+
| SETSAMPLERATE     | sets sampling rate                                       |
|    samplerate     +---------------------+------------------------------------+
|                   | samplerate parameter|   sample rate in Hz                |
+-------------------+---------------------+------------------------------------+
| GETSAMPLERATE     | reads current sample rate                                |
+-------------------+----------------------------------------------------------+
| LISTUSEDCHS       | lists all used channels                                  |
+-------------------+----------------------------------------------------------+
| PREPARETRANSFER   | sends a list of channels for live capture. Channels can  |
|                   | only be selected from used channel syntax:               |
|                   |                                                          |
|                   | ::                                                       |
|                   |                                                          |
|                   |     /stx preparetransfer                                 |
|                   |     ch 0                                                 |
|                   |     .                                                    |
|                   |     .                                                    |
|                   |     ch x                                                 |
|                   |     /etx                                                 |
|                   |                                                          |
+-------------------+----------------------------------------------------------+
| STARTTRANSFER     | requests DEWESoft to connect to port 'portno' and feed   |
|   portno filename | data to client                                           |
|                   +---------------------+------------------------------------+
|                   | portno parameter:   | TCP port number on client computer |
+-------------------+---------------------+------------------------------------+
| STOPTRANSFER      | stops transfer                                           |
+-------------------+----------------------------------------------------------+
| STARTTRIGTRANSFER | requests DEWESoft to connect to port 'portno' and feed   |
|     portno        | last trigger data to client                              |
|                   +---------------------+------------------------------------+
|                   | portno parameter:   | TCP port number on client computer |
+-------------------+---------------------+------------------------------------+
| STARTACQ          | start acquisition - measure (more suitable name would be |
|                   | STARTMEASURE)                                            |
+-------------------+----------------------------------------------------------+
| STOP              |stop acquisition / leave setup mode and go to start screen|
+-------------------+----------------------------------------------------------+
| STARTSTORE        | starts storing, also starts acquisition if not yet       |
|  filename         | started                                                  |
+-------------------+----------------------------------------------------------+
| SETSTORING status | sets storing on or off on measurement unit               |
|                   +---------------------+------------------------------------+
|                   | status parameter:   | ON - remote storing on             |
|                   +                     +------------------------------------+
|                   |                     | OFF - remote storing off           |
+-------------------+---------------------+------------------------------------+
| ENTERSETUP        | enter setup mode / start acquisiton in setup mode        |
+-------------------+----------------------------------------------------------+
| ISACQUIRING       | returns 'Yes' if acquisition is in progress (measure or  |
|                   | setup), otherwise 'No'                                   |
+-------------------+----------------------------------------------------------+
| ISSETUPMODE       | returns 'Yes' if in setup mode, otherwise 'No'           |
+-------------------+----------------------------------------------------------+
| ISSTORING         |returns 'Yes' if in storing is in progress, otherwise 'No'|
+-------------------+----------------------------------------------------------+
| ISMEASURING       | returns 'Yes' if acquisition is in progress (measure),   |
|                   | otherwise 'No'                                           |
+-------------------+----------------------------------------------------------+
| GETSTATUS         |returns DEWESoft status (measure/analyse mode, clock mode)|
+-------------------+----------------------------------------------------------+
| SETFULLSCREEN     | sets or clears full screen mode of DEWESoft              |
|  status           +---------------------+------------------------------------+
|                   |  status parameter:  | 1 - full screen on                 |
|                   +                     +------------------------------------+
|                   |                     | 0 - full screen off                |
+-------------------+---------------------+------------------------------------+
| SETUP CONNECT     | sets DEWESoft to full screen setup mode.                 |
|                   | Suitable for VNC remote setup of DEWESoft                |
+-------------------+----------------------------------------------------------+
| SETUP DISCONNECT  | cancels setup full screen mode                           |
+-------------------+----------------------------------------------------------+
| DISPLAY START     | sets DEWESoft to full screen display setup mode.         |
|                   | Suitable for VNC remote setup of DEWESoft displays       |
+-------------------+----------------------------------------------------------+
| DISPLAY STOP      | cancels display setup mode                               |
+-------------------+----------------------------------------------------------+
| LOADSETUP filename| loads a setup; filename parameter: setup file stored on  |
|                   | measurement unit                                         |
+-------------------+----------------------------------------------------------+
| SAVESETUP filename| saves a setup; filename parameter: setup file to be      |
|                   | stored on measurement unit                               |
+-------------------+----------------------------------------------------------+
| NEWSETUP          | clears current DEWESoft setup                            |
+-------------------+----------------------------------------------------------+
| SETSCREENSIZE     | sets DEWESoft window size in pixels                      |
|   screensize      +-----------------------+----------------------------------+
|                   | screensize parameter: | XsizexYSize - sets window size to|
|                   |                       | Xsize x Ysize (i.e. 640x480)     |
|                   +-----------------------+----------------------------------+
|                   |                       | max - maximizes window size      |
+-------------------+-----------------------+----------------------------------+

TODO implement automatic start of DeweSoft instance
    If the DeweSoft instance isn't already started and no process is running,
    than automatically start the DeweSoft using an absolute start path.
"""


from io import StringIO
import logging
import socket

from datetime import datetime

from .dewenet_data import DeweChannelInfo


def dt_now():
    """Helper method for getting the timestamp

    Will be necessary for testing

    Returns:
        datetime: current time
    """
    return datetime.now()


class DeweNetClientException(Exception):
    """Base exception raised for errors in the DeweNetClient module"""

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class DeweNetControllerClient(object):
    """Client for Communication with DeweSoft.

    The DeweNetControllerClient class implements the necessary functionality
    for controlling the DeweSoft. Thereby the NET-Plugin for DeweSoft must be
    registered and the Slave Mode of the DeweSoft program must be activated
    (Settings-Hardware Setup-NET-Computer role in NETwork -> Slave measurement
    unit)

    The class uses a TCP-client that connects to an open port of the DeweSoft
    (usually 8999)

    Example:

    ::

        deweController = DeweNetControllerClient()
        deweController.connect_to_Dewe('127.0.0.1',8999)

        print "GetSampleRate",deweController.dewe_get_samplerate()
        print "ISAquiring",deweController.dewe_is_acquiring()
        print "GetMode",deweController.dewe_get_mode()
        deweController.dewe_load_setupfile(
            "C:\\DATA\\Cotevos\\EVTestStand\\EvTestStand.d7s")
        deweController.dewe_list_used_channels()
        deweController.dewe_start_acquisition()
        time.sleep(10)
        deweController.dewe_stop()
        deweController.close_Dewe_Connection()


    Attributes:
        EXP_INTF_VERSION (int): Definition of implemented protocol
            version. If other revisions are used, please check the
            communication flow for changes.

        _socket (socket): The TCP client socket for communication with the TCP
            Server of the DeweSoft Slave device

        available_channels (dict): After loading a setup file of the DeweSoft
            (function dewe_load_setupfile() ) the channels can be read from
            DeweSoft by using dewe_list_used_channels().
            This dictionary contains a list of 'DeweChannel' classes with the
            name of the channel as key. Therefore different settings of the
            channel are stored (see DeweChannel documentation)
    """

    EXP_INTF_VERSION = 31
    """Interface version that is used during development.

    The client is tested against this protocol version.
    """

    def __init__(self, client_socket=None, logger=None):
        """Default constructor

        Args:
            client_socket (socket.socket, optional): Socket for connecting to
                DeweSoft (usually a TCP socket)
            logger (logging.logger, optional): Sets the logger
        """
        self._logger = logger or logging.getLogger(__name__)
        self._socket = client_socket or socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self.available_channels = dict()
        self._logger.debug("Initialize DeweNetController Client")

    def connect_to_dewe(self, dewe_ip='127.0.0.1', dewe_port=8999):
        """Connect to the DeweSoft Net interface

        The function must be called after creation of the
        DeweNetControllerClient. It will connect to a running instance off
        DeweSoft on the Host computer and reads the interface version and the
        version of the DeweSoft.

        Args:
            dewe_ip (str, optional): IP address of the computer with running
                DeweSoft
            dewe_port (int, optional): Open port of the DeweSoft client,
                usually 8999

        Returns:
            list: dewe_interface_version, dewe_version
                dewe_interface_version (int): version of the Dewe-Net interface
                dewe_version (str): version of the connected DeweSoft instance

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """

        self._logger.info("Connect to DeweSoft at {}: {}".format(dewe_ip,
                                                                 dewe_port))
        dewe_ip = dewe_ip.encode("ascii")
        self._socket.connect((dewe_ip, dewe_port))

        # get first response after successful connection
        con_respmsg = self._dewe_read_response()[0]
        self._logger.debug("Response: '{}'".format(con_respmsg))

        if con_respmsg.startswith("+CONNECTED"):
            self._logger.info("Connection successfully opened.")
        else:
            raise DeweNetClientException(
                "connect_to_Dewe",
                "Unkown response received from DeweSoft : " + con_respmsg)

        dewe_interface_version = self._dewe_read_interface_version()
        dewe_version = self._dewe_read_version()
        self._logger.info("Interface Version: {}   Version: {}".format(
            dewe_interface_version, dewe_version))
        return dewe_interface_version, dewe_version

    def _dewe_read_interface_version(self):
        """Read the interface version of the connected DeweSoft.

        This helper function reads the interface version of the connected
        DeweSoft and stores the value in the attribute
        '_dewe_interface_version'.

        Returns:
            int: interface version read from DeweSoft

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """

        response = self._dewe_request_control_message("GETINTFVERSION")[0]

        if response.startswith("+OK"):
            intf_version = int(response.replace("+OK ", ""))

            if intf_version != DeweNetControllerClient.EXP_INTF_VERSION:
                self._logger.warn(
                    "Used Interface with Version '{0}'"
                    " doesn't match expected one '{1}'.".format(
                        intf_version,
                        DeweNetControllerClient.EXP_INTF_VERSION))
            else:
                self._logger.debug(
                    "Used Interface with Version '{0}' matches expected one "
                    "'{1}'.".format(
                        intf_version,
                        DeweNetControllerClient.EXP_INTF_VERSION))

            return intf_version

        else:
            raise DeweNetClientException(
                "dewe_read_interface_version",
                "Error reading interface version: '{}'".format(response))

    def _dewe_read_version(self):
        """Read the version of the connected DeweSoft

        This helper function reads the version of the connected DeweSoft and
        stores the value in the attribute '_dewe_version'.

        Returns:
            str: Version string read from DeweSoft

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """

        response = self._dewe_request_control_message("GETVERSION")[0]

        if not response.startswith("+OK"):
            raise DeweNetClientException(
                "dewe_read_version",
                "Error reading version: '{}'".format(response))

        return response.replace("+OK ", "")

    def disconnect_from_dewe(self):
        """Closes the connection to the DeweSoft

        """
        self._logger.info("Close DeweNetControllerClient")
        self._socket.close()

    def dewe_get_datetime(self):
        """Read the current time on the measurement device

        Returns:
            datetime: Current datetime read from DeweSoft

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """

        response = self._dewe_request_control_message("GETDATETIME")[0]
        if not response.startswith("+OK"):
            raise DeweNetClientException(
                "_dewe_get_dateTime: Can't "
                "convert received message to datetime", response)

        response = response.replace("+OK", "").strip()
        return datetime.strptime(response, "%d.%m.%Y %H:%M:%S")

    def dewe_set_mode(self, mode=False):
        """Sets the operation mode of the DeweSoft

        Args:
            mode (bool,optional): Mode of the DeweSoft
                False - Set to View Mode
                True  - Set to Control Mode

        Returns:
            bool: True - DeweSoft is in control mode
            False - DeweSoft is in view mode

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """

        comm_mode = 1 if mode else 0  # generate argument for request

        response = self._dewe_request_control_message(
            "SETMODE " + str(comm_mode))[0]

        if not response.startswith("+OK"):
            raise DeweNetClientException(
                "dewe_set_mode",
                "Error setting mode of DeweSoft: '{}'".format(response))
        return mode

    def dewe_get_mode(self):
        """Read the current mode of the DeweSoft.

        Returns:
            bool: True - DeweSoft is in control mode
            False - DeweSoft is in view mode

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """
        response = self._dewe_request_control_message("GETMODE")[0]

        if response.startswith("+OK"):
            response = response.split(" ")
            return int(response[2]) == 1

        else:
            raise DeweNetClientException(
                "dewe_set_mode",
                "Error setting mode of DeweSoft: '{}'".format(response))

    def dewe_start_acquisition(self):
        """Start the acquisition (measurement) on the DeweSoft

        Returns:
            time: current time of measurement start

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """

        if not self.dewe_get_mode():
            self.dewe_set_mode(True)    # Set to control mode

        response = self._dewe_request_control_message("STARTACQ")[0]
        if response.startswith("+OK"):
            return dt_now()
        else:
            raise DeweNetClientException(
                "dewe_set_mode",
                "Error setting mode of DeweSoft: '{}'".format(response))

    def dewe_start_store(self, filename):
        """Start the storing function and the acquisition (if not already
        running) on the DeweSoft

        Args:
            filename (str): Filename and path of the storage file on local
                DeweSoft

        Returns:
            time: current time of measurement start

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """

        if not self.dewe_get_mode():
            self.dewe_set_mode(True)    # Set to control mode

        response = self._dewe_request_control_message(
            "STARTSTORE " + filename)[0]
        if response.startswith("+OK"):
            return dt_now()
        else:
            raise DeweNetClientException(
                "dewe_set_mode",
                "Error starting storage on DeweSoft: '{}'".format(response))

    def dewe_set_storing(self, storing=True):
        """Start storing mode of the DeweSoft

        Sets the Mode for the control option of the DEWE connection

        Args:
            storing (bool): False - Not storing
                True - Store

        Returns:
            bool: mode of storing

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """
        if not self.dewe_get_mode():
            self.dewe_set_mode(True)    # Set to control mode

        comm_storing = "ON" if storing else "OFF"

        response = self._dewe_request_control_message(
            "SETSTORING " + comm_storing)[0]

        if response.startswith("+OK"):
            return storing
        else:
            raise DeweNetClientException(
                "dewe_set_mode",
                "Error setting mode of DeweSoft: '{}'".format(response))

    def dewe_stop(self):
        """Stop the acquisition (measurement) and/or storing on the DeweSoft

        Returns:
            time: current time of measurement start
        Raises:
            DeweNetClientException: If an error is occured during communication.
        """
        if not self.dewe_get_mode():
            self.dewe_set_mode(True)    # Set to control mode

        response = self._dewe_request_control_message("STOP")[0]
        if response.startswith("+OK"):
            return dt_now()
        else:
            raise DeweNetClientException(
                "dewe_set_mode",
                "Error setting mode of DeweSoft: '{}'".format(response))

    def dewe_is_acquiring(self):
        """Get actual state of acquisition

        Returns:
            bool: True, if DeweSoft is in acquisition mode, otherwise False

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """
        return self._dewe_get_bool_message("ISACQUIRING")

    def dewe_is_setup_mode(self):
        """Get actual state of setup mode

        Returns:
            bool: True, if DeweSoft is in setup mode, otherwise False

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """
        return self._dewe_get_bool_message("ISSETUPMODE")

    def dewe_is_storing(self):
        """Get actual state of storing

        Returns:
            bool: True, if DeweSoft is in storing mode, otherwise False

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """
        return self._dewe_get_bool_message("ISSTORING")

    def dewe_is_measuring(self):
        """Get actual state of acquisition

        Returns:
            bool: True, if DeweSoft is in acquisition mode, otherwise False

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """
        return self._dewe_get_bool_message("ISMEASURING")

    def dewe_get_status(self):
        """Get actual status of DeweSOft

        Returns:
            str: State information of DeweSoft (e.g. Response Mode: Measure,
                Acquiring; Clock mode: Standalone)

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """
        response = self._dewe_request_control_message("GETSTATUS")[0]
        if response.startswith("+OK"):
            return response.replace("+OK", "").strip()
        else:
            raise DeweNetClientException(
                "dewe_set_mode",
                "Error setting mode of DeweSoft: '{}'".format(response))

    def dewe_load_setupfile(self, filename):
        """Loads a setup file stored on the DeweSoft computer

        Args:
            filename (str): Full Filename with path of the setup file to be
                loaded
        Returns:
            str: Response from DeweSoft

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """
        if not self.dewe_get_mode():
            self.dewe_set_mode(True)    # Set to control mode

        response = self._dewe_request_control_message(
            "LOADSETUP " + filename)[0]
        if response.startswith("+OK"):
            return response.replace("+OK", "").strip()
        else:
            raise DeweNetClientException(
                "dewe_set_mode",
                "Error setting mode of DeweSoft: '{}'".format(response))
    def dewe_set_samplerate(self, samplefrequency = None):
        """Writes the sample rate of the DeweS
        oft

        Returns:
            int: Sample Rate of DeweSoft in Hz

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """
        if samplefrequency:
            response = self._dewe_request_control_message(
                "SETSAMPLERATE " + str(samplefrequency))[0]
            #response = self._dewe_request_control_message("GETSAMPLERATE")[0]
            if response.startswith("+OK"):
                self._logger.info(response)
                response = response.replace("+OK", "").strip()
                self._logger.info(response)
                response = response[response.find('<') + 1:response.find('>')]
                self._logger.info(response)
                return int(response)

            else:
                self._logger.info(response)
                raise DeweNetClientException(
                    "dewe_set_samplerate",
                    "Can't set samplerate from DeweSoft: '{}'".format(response))
        else:
            return None



    def dewe_get_samplerate(self):
        """Read the actual sample rate of the DeweSoft

        Returns:
            int: Sample Rate of DeweSoft in Hz

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """
        response = self._dewe_request_control_message("GETSAMPLERATE")[0]
        if response.startswith("+OK"):
            return int(response.replace("+OK", "").strip())
        else:
            raise DeweNetClientException(
                "dewe_get_samplerate",
                "Can't read samplerate from DeweSoft: '{}'".format(response))

    def dewe_list_used_channels(self):
        """Read all available channels from DeweSoft with its parameters

        This function reads all available channels from the DeweSoft and stores
        it in the available_channels list. Then it is possible to get these
        values for further work. (using client.available_channels.keys())
        """
        response = self._dewe_request_control_message("LISTUSEDCHS")

        for line in response:
            element = line.split("\t")

            if len(element) > 22:
               channel = DeweChannelInfo(channel_number=element[2],
                                          name=element[3],
                                          unit=element[5],
                                          samplerate_divider=element[6],
                                          measurement_type=element[8],
                                          sample_data_type=element[9],
                                          buffer_size=element[10],
                                          custom_scale=element[11],
                                          custom_offset=element[12],
                                          scale_raw_data=element[13],
                                          offset_raw_data=element[14],
                                          description=element[15],
                                          settings=element[16] + " " + element[19],
                                          range_min=element[17],
                                          range_max=element[18],
                                          value_min=element[21],
                                          value_max=element[22],
                                          value_act=(element[23]
                                                     if len(element) > 23 else 0.0))
               self.available_channels[channel.name] = channel
            elif len(element) > 18:

                channel = DeweChannelInfo(channel_number=element[2],
                                      name=element[3],
                                      unit=element[5],
                                      samplerate_divider=element[6],
                                      measurement_type=element[8],
                                      sample_data_type=element[9],
                                      buffer_size=element[10],
                                      custom_scale=element[11],
                                      custom_offset=element[12],
                                      scale_raw_data=element[13],
                                      offset_raw_data=element[14],
                                      description=element[15],
                                      settings=element[16] + " " + element[19],
                                      range_min=element[17],
                                      range_max=element[18],
                                      value_min=0.0,
                                      value_max=0.0,
                                      value_act=0.0)
                self.available_channels[channel.name] = channel
            else:
                raise DeweNetClientException(
                    "Error reading channel",
                    "Channel {} hasn't enough elements".format(
                        element[3] if len(element) > 3 else "unknown"))

    def dewe_read_last_values(self):
        """Read last values from DeweSoft

        This method uses the client interface to read current values from
        DeweSoft.
        This method can be used as a fallback solution to read values cyclic.

        Returns:
            list: List of tuples containing all DeweSoft channels
                tuple: (ch_number,ch_name,value)
                    ch_number (int): number of DeweSoft channel
                    ch_name (str): Name of the channel
                    value (float): Last value of the channel
        """
        response = self._dewe_request_control_message("LISTUSEDCHS")
        channels = list()
        for line in response:
            element = line.split("\t")
            if len(element) > 23:
                channel = (int(element[2]), element[3], float(element[23]))
                channels.append(channel)
                del channel
        return channels

    def dewe_prepare_transfer(self, channel_list):
        """Transmit a list of channels, which you want to be automatically
        transmitted by DeweSoft.

        This function must be called before the `dewe_start_transfer()` is
        called to rightly configure the DeweSoft communication.

        Args:
            channel_list (list): List of channels names (order will be taken
                into account by transfering data values)This argument must be
                a list of string containing the names of the channels

                Example:
                    [r'Power_AC_Netz/U_rms_L1',r'Power_AC_Netz/U_rms_L2',
                        r'Power_AC_Netz/U_rms_L3']
        Raises:
            DeweNetClientException: If the channels can't be prepared
        """
        request = "/stx PREPARETRANSFER\r\n"
        for channel in channel_list:
            request += "ch {}\r\n".format(self.available_channels[
                channel].channel_number)
        request += "/etx\r\n"

        response = self._dewe_request_control_message(request)[0]

        if not response.startswith("+OK"):
            self._logger.debug(response)
            raise DeweNetClientException(
                "dewe_prepare_transfer",
                "Can't prepare channels for transfer: '{}'".format(response))

    def dewe_start_transfer(self, port_number):
        """Start the transfer of values from DeweSoft to the
        DeweNetControllerServer

        Args:
            port_number (int): Port number of the client, which will be used
                from the `DeweNetControllerServer`
        Raises:
            DeweNetClientException: If the transfer can't be started
        """
        response = self._dewe_request_control_message(
            "STARTTRANSFER {}".format(port_number))[0]

        if not response.startswith("+OK"):
            raise DeweNetClientException(
                "dewe_start_transfer",
                "Error setting mode of DeweSoft: '{}'".format(response))

    def dewe_init_start_transfer(self, port_number, channel_list):
        """Combination of the prepare_transfer and the start transfer command

        Args:
            port_number (int): Port number of the client, which will be used
                from the `DeweNetControllerServer`
            channel_list (list): List of channels names (order will be taken
                into account by transfering data values)This argument must be
                a list of string containing the names of the channels
        Raises:
            DeweNetClientException: If the transfer can't be started
        """
        self.dewe_prepare_transfer(channel_list)
        self.dewe_start_transfer(port_number)

    def dewe_start_trigger_transfer(self, port_number):
        """Start the data transfer and get the already last stored values from
        DeweSoft

        Args:
            port_number (int): Port number of the client, which will be used
                from the `DeweNetControllerServer`

        Raises:
            DeweNetClientException: If the transfer can't be started
        """
        response = self._dewe_request_control_message(
            "STARTTRIGTRANSFER " + str(port_number))[0]

        if not response.startswith("+OK"):
            raise DeweNetClientException(
                "dewe_start_trigger_transfer",
                "Can't start trigger transfer: '{}'".format(response))

    def dewe_stop_transfer(self):
        """Stops an actual running transmission from DeweSoft

        Raises:
            DeweNetClientException: If the transfer can't be stopped
        """
        response = self._dewe_request_control_message("STOPTRANSFER")[0]

        if not response.startswith("+OK"):
            raise DeweNetClientException(
                "dewe_stop_transfer",
                "Error stopping transfer of DeweSoft: '{}'".format(response))

    def _dewe_request_control_message(self, request):
        """Sends a request to the Dewesoft and waits for a response.

        Args:
            request (str): Request string of the command for DeweSoft
                communication.
        Returns:
            str: Response message

        Raises:
            DeweNetClientException: If an error is occured during communication.
        """
        if not request.endswith("\r\n"):
            request = request + "\r\n"

        self._socket.sendall(request.encode())
        self._logger.debug("Request: '" + request.replace("\r\n", "") + "'")

        response = self._dewe_read_response()

        if not response:
            raise DeweNetClientException("dewe_request_control_message",
                                         "No response received from DeweSoft.")

        self._logger.debug("Response: '{}'".format(response))
        return response

    def _dewe_read_response(self):
        """Read the Response of the DeweSoft message

        This function receives a single line response or a multiline response
        from DeweSoft

        Returns:
            str: Response message striped by end delimiter
        """
        response = self._readlines()

        if response[0].startswith("+STX"):
            while True:
                if response[-1].startswith("+ETX"):
                    return response[1:-1]
                response.extend(self._readlines())
        else:  # single line response
            return response

    def _readlines(self, delimiter="\r\n"):
        """Read lines from socket.

        Args:
            delimiter (str): Delimiter of a line

        Returns:
            list: A list of lines with removed line delimiter
        """
        eol = delimiter[-1:].encode()  # last character

        buff = StringIO()
        while True:
            data = self._socket.recv(1024)
            buff.write(data.decode())
            if data.endswith(eol):
                break

        return_lines = buff.getvalue().splitlines()
        return [string.strip() for string in return_lines]

    def _dewe_get_bool_message(self, request):
        """Read a bool value from DeweSoft.

        Args:
            request (str): Request that is sent.

        Returns:
            bool: Response as bool value

        Raises:
            DeweNetClientException: if an error during request occurs.
        """
        response = self._dewe_request_control_message(request)[0]
        response = str(response)

        if isinstance(response, str) and response.startswith("+OK"):
            response = response.split(" ")
            return response[1].upper() == "YES"
        else:
            raise DeweNetClientException(
                'get_bool_message',
                "Error reading bool value from DeweSoft: '{}'".format(response))
