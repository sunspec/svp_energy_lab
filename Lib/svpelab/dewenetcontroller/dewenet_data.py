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













""" Storage Classes for a DeweSoft Channel

This module contains the classes which are used for storage and organisation of
Dewe Soft channel, which are read by the Net interface.


Channel information (From DeweSoft Net Interface Manual)
==============================================================

Binary data delivered to client are always raw binary data. To get information
about sample data type, scaling and other important info of every channel client
should send 'LISTUSEDCHS' command. Response contains following info for each
channel separated by tab character

+-------------+-----------------------------------------+---------------------+
| Data        |     Description                         |     Data type       |
+=============+=========================================+=====================+
| CH          | Fixed string                            |                     |
+-------------+-----------------------------------------+---------------------+
| Number      | Consequent channel number               | Integer number      |
+-------------+-----------------------------------------+---------------------+
| Name        | Channel name                            | Text                |
+-------------+-----------------------------------------+---------------------+
| Unit        | Measure unit                            | Text                |
+-------------+-----------------------------------------+---------------------+
| Samplerate  | Divider for sync channel                | Integer number or   |
| divider     +-----------------------------------------+ text                |
|             | 'Async' for async channels,             |                     |
|             +-----------------------------------------+                     |
|             | 'SingleValue' for single value channels |                     |
+-------------+-----------------------------------------+---------------------+
| Measurement | Defines channel meaning                 | Integer number      |
| type        |                                         |                     |
+-------------+-----------------------------------------+---------------------+
| Sample data | 0 - 8 bit unsigned integer              |                     |
| type        +-----------------------------------------+                     |
|             | 1 - 8 bit signed integer                |                     |
|             +-----------------------------------------+                     |
|             | 2 - 16 bit signed integer               |                     |
|             +-----------------------------------------+                     |
|             | 3 - 16 bit unsigned integer             |                     |
|             +-----------------------------------------+                     |
|             | 4 - 32 bit signed integer               |                     |
|             +-----------------------------------------+                     |
|             | 5 - Single floating point (32bit)       |                     |
|             +-----------------------------------------+                     |
|             | 6 - 64 bit signed integer               |                     |
|             +-----------------------------------------+                     |
|             | 7 - Double floating point (64 bit)      |                     |
+-------------+-----------------------------------------+---------------------+
| Buffer size | Buffer size for data                    | Integer number      |
+-------------+-----------------------------------------+---------------------+
| Custom scale| Custom scale after amplifier            | Float number        |
+-------------+-----------------------------------------+---------------------+
|Custom offset| Custom offset after amplifier           | Float number        |
+-------------+-----------------------------------------+---------------------+
| Scale raw   | Scale for raw data                      | Float number        |
| data        |                                         |                     |
+-------------+-----------------------------------------+---------------------+
| Offset raw  | Offset for raw data                     | Float number        |
| data        |                                         |                     |
+-------------+-----------------------------------------+---------------------+
| Description | Channel description                     | Text                |
+-------------+-----------------------------------------+---------------------+
| Settings    | Channel settings                        | Text                |
+-------------+-----------------------------------------+---------------------+
| Range min   | Range min in scaled units               | Float number        |
+-------------+-----------------------------------------+---------------------+
| Range max   | Range max in scaled units               | Float number        |
+-------------+-----------------------------------------+---------------------+
| Actual Value| Actual value in scaled unit             | Float number        |
+-------------+-----------------------------------------+---------------------+


To get real scaled value, client has to apply the following formula:
ScaledValue = ScaleRawData * RawValue + OffsetRawData


.. warning:: The received values from `list_used_chs` can be differ in the
   length of the given protocol.

Channels in data packet are delivered in the same order they are included in
'PREPARE TRANSFER' command.

Binary data format, which will be receied by the server

Header
----------------------------------------------------

+-------+-------+---------------+---------------------------------------------+
|Offset |Length |Data type      |   Description                               |
|(bytes)|(bytes)|               |   Comment                                   |
+=======+=======+===============+=============================================+
|  0    |  8    |               |Start packet string                          |
|       |       |               | 0x00 0x01 0x02 0x03 0x04 0x05 0x06 0x07     |
+-------+-------+---------------+---------------------------------------------+
|  8    |  4    |Integer 32 bit |Packet size                                  |
|       |       |               |Size in bytes without stop and start string  |
+-------+-------+---------------+---------------------------------------------+
| 12    |  4    |Integer 32 bit |Packet type                                  |
|       |       |               |Always 0 for data packets                    |
+-------+-------+---------------+---------------------------------------------+
| 16    |  4    |Integer 32 bit |Samples in packet                            |
|       |       |               |Number of synchronous samples per ch.        |
+-------+-------+---------------+---------------------------------------------+
| 20    |  8    |Integer 64 bit |Samples acquired so far                      |
+-------+-------+---------------+---------------------------------------------+
| 28    |  8    |Double floating|Absolute/relative time                       |
|       |       |point          |Number of days since 12/30/1899              |
|       |       |               |Number of days since start of acq.           |
+-------+-------+---------------+---------------------------------------------+

Off = 36 bytes,


Repeat for each channel
------------------------------------------------------

* If Channel is asynchronous
+--------------+--------------+----------------+------------------------------+
| Offset       | Length       | Data type      |    Description               |
| (bytes)      | (bytes)      |                |    Comment                   |
+==============+==============+================+==============================+
| Off          | 4            | 4              | Number of samples            |
|              |              |                | = X                          |
+--------------+--------------+----------------+------------------------------+
| Off + 4      |X * SampleSize|Sample data type| Data samples                 |
+--------------+--------------+----------------+------------------------------+
| Off + 4 +    | X * 8        | Integer 64 bit | Timestamp samples            |
|X * SampleSize|              |                | Timestamps for samples       |
|              |              |                | since start of acquisition   |
+--------------+--------------+----------------+------------------------------+
Off = Off + 4 + X * (SampleSize + 8)


* If Channel is synchronous
+--------------+---------------+----------------+-----------------------------+
| Offset       | Length        | Data type      |    Description              |
| (bytes)      | (bytes)       |                |    Comment                  |
+==============+===============+================+=============================+
| Off          | 4             | 4              | Number of samples           |
|              |               |                | = X = SamplesInPacket div   |
|              |               |                | Channel SR divider          |
+--------------+---------------+----------------+-----------------------------+
| Off + 4      |X * SampleSize |Sample data type| Data samples                |
+--------------+---------------+----------------+-----------------------------+
Off = Off + 4 + X * SampleSize


* If Channel is single value
+--------------+--------------+-----------------+-----------------------------+
| Offset       | Length       | Data type       |    Description              |
| (bytes)      | (bytes)      |                 |    Comment                  |
+==============+==============+=================+=============================+
| Off          | 4            | 4               | Number of samples           |
|              |              |                 | Always 1                    |
+--------------+--------------+-----------------+-----------------------------+
| Off + 4      | 8            | Double floating | Data sample                 |
|              |              | point           |                             |
+--------------+--------------+-----------------+-----------------------------+
Off = Off + 12


End repeat
--------------------------------------------------------
+--------------+--------------+-----------------+-----------------------------+
| Offset       | Length       | Data type       |    Description              |
| (bytes)      | (bytes)      |                 |    Comment                  |
+==============+==============+=================+=============================+
| Off          | 8            |                 | Stop packet string          |
|              |              |                 | 0x07 0x06 0x05 0x04 0x03    |
|              |              |                 | 0x02 0x01 0x00              |
+--------------+--------------+-----------------+-----------------------------+

"""

import threading


def _local_handler(name, value, timestamp):
    """A local handler implementation as backup solution.

    This method will be used if no update handler will be set.

    Args:
        name (str): Name of the channel
        value (float): Value of hte measured sample
        timestamp (float): Relative timestamp of the value in seconds since
            start of acquisition
    """
    pass


class DeweChannel:
    """ Representation of a DeweSoft channel.

    This class is used for storage and representation of a DeweSoft channel.

    Attributes:
        channel_info (DeweChannelInfo): Channel information read from DeweSoft
        last_value (float): Last received raw value of the channel
        last_timestamp (float): Last received relative timestamp of the channel
        update_handler (function): Reference to the handler function

        _values_lock (RLock):

    """

    def __init__(self, channel_info, update_handler=None):
        """ Constructor.

        Args:
            channel_info (DeweChannelInfo): Static information about the
                DeweSoft channel_info

            update_handler (function): Reference to update handler function.

                The function must have three arguments:
                    name (str): Name of the channel
                    index (int): last index from DeweSoft of the received value.
                        Can be used to calculate the timestamp of the value
                        using the timestamp of the measurement start.
                    value (float): scaled value of the last received point

                    Example of the handler function:
                        def update_value(name, index, value):
                            print("Update Handler called:",name, index, value)
        """
        self.channel_info = channel_info
        self.last_value = None
        self.last_timestamp = None

        self._values_lock = threading.RLock()
        self.update_handler = update_handler or _local_handler

    def __str__(self, *args, **kwargs):

        ret_str = "Channel {}: ".format(self.channel_info.name)

        if self.last_value:
            ret_str += "{} {} at index {}".format(self.last_value,
                                                  self.channel_info.unit,
                                                  self.last_timestamp)
        else:
            ret_str += "No value available"
        return ret_str

    def __repr__(self, *args, **kwargs):
        return "{} (Channel)".format(self.channel_info.name)

    def get_info_as_dict(self):
        """Get all references as dict

        Get all stored information variables of the channel as an dictionary

        Returns:
            dict: Dict of all stored attributes for easier handling

        """
        last_timestamp, last_value = self.get_last_value()
        info = {
            'last_value': last_value,
            'last_timestamp': last_timestamp
        }
        info.update(self.channel_info.get_info_as_dict())
        return info

    def set_value(self, raw_value, timestamp):
        """Set a new value

        Sets a new value (threadsafe) of the channel with its index. After that
        it will call all stored update handler by the new value

        Args:
            raw_value (float): value of the data point (type is listed in
                channel info)
            timestamp (float): index of the data point
        """

        with self._values_lock:
            self.last_timestamp = timestamp
            self.last_value = raw_value

        if self.update_handler:
            last_value = self._calc_value_raw(raw_value)
            self.update_handler(self.channel_info.name, last_value, timestamp)

    def get_last_value(self):
        """ Read the last value of the channel

        This function reads (threadsafe) the last stored value of the channel

        Returns:
            list: output list containing two elements
                 float: calculated value of the last receive measurement value
                 float: timestamp in seconds since start of acquisition
        """
        with self._values_lock:
            if self.last_value is None:
                raise ValueError('No value available for {0}'.format(self.channel_info.name))
        
            return self._calc_value_raw(self.last_value), self.last_timestamp

    def _calc_value_raw(self, raw_value):
        """ Calculate the scaled value of the channel

        Returns calculates (scaled) value of the Channel given by its position

        Args:
            raw_value (number): raw value that should be converted.

        Returns:
            Float: calculated scaled value of the channel's raw value

        """
        
        calcvalue = raw_value * self.channel_info.scale_raw_data * \
            self.channel_info.custom_scale + \
            self.channel_info.offset_raw_data + self.channel_info.custom_offset
        return calcvalue


class DeweChannelInfo:
    ''' Information header of a channel of DeweSoft

    This class contains the header information of a DeweSoft channel.
    These values are transmitted by the DeweSoft using the 'listusedchs'
    command. Fur detailed information see DeweSoft Net interface manual

    Attributes:
        see module description

        channel_number (int):
        name (str):
        unit (str):
        samplerate_divider (int,str)
        measurement_type (int):
        sample_data_type (int):
        buffer_size (int):
        custom_scale (float):
        custom_offset (flaot):
        scale_raw_data (float):
        offset_raw_data (float):
        settings (str):
        range_min (float):
        range_max (float):
        value_min (float):
        value_max (float):
        value_act (float):
    '''

    def __init__(self, channel_number, name, unit, samplerate_divider,
                 measurement_type, sample_data_type, buffer_size,
                 custom_scale, custom_offset, scale_raw_data, offset_raw_data,
                 description, settings, range_min, range_max, value_min,
                 value_max, value_act):
        ''' Constructor

        Args:
            Information, which are transmitted by the DeweSoft 'listusedchs'
            command
        '''
        self.channel_number = int(channel_number)   # int
        self.name = str(name)  # string
        self.unit = str(unit) if unit != "-" else ""  # string
        if samplerate_divider.isdigit():
            self.samplerate_divider = int(samplerate_divider)    # int,string
        else:
            self.samplerate_divider = str(samplerate_divider).upper()

        self.measurement_type = int(measurement_type)  # int
        self.sample_data_type = int(sample_data_type)  # int
        self.buffer_size = int(buffer_size)   # int
        self.custom_scale = DeweChannelInfo.convert_str_to_float(custom_scale)
        self.custom_offset = DeweChannelInfo.convert_str_to_float(
            custom_offset)
        self.scale_raw_data = DeweChannelInfo.convert_str_to_float(
            scale_raw_data)
        self.offset_raw_data = DeweChannelInfo.convert_str_to_float(
            offset_raw_data)
        self.description = str(description)
        self.settings = str(settings)
        self.range_min = DeweChannelInfo.convert_str_to_float(range_min)
        self.range_max = DeweChannelInfo.convert_str_to_float(range_max)
        self.value_min = DeweChannelInfo.convert_str_to_float(value_min)
        self.value_max = DeweChannelInfo.convert_str_to_float(value_max)
        self.value_act = DeweChannelInfo.convert_str_to_float(value_act)

    @property
    def type(self):
        """Get the type of the channel as str.

        Returns:
            str: "sync" for a synchronous channel,
                 "async" for an asynchronous channel,
                 "single" for a single ValueError
        """
        if isinstance(self.samplerate_divider, int):
            return "sync"
        elif (isinstance(self.samplerate_divider, str) and
              self.samplerate_divider == "ASYNC"):
            return "async"
        elif (isinstance(self.samplerate_divider, str) and
              self.samplerate_divider == "SINGLEVALUE"):
            return "single"

    @staticmethod
    def convert_str_to_float(string_value):
        """Convert a string value into a float.

        The method will also accept float values that are divided by a colon.

        Args:
            string_value (str): String containing float value to be converted.

        Returns:
            float: converted value from string
        """

        if isinstance(string_value, str):
            string_value = string_value.replace(",", ".")
        if isinstance(string_value, str):
            string_value = string_value.replace(",", ".")
        return float(string_value)  # float

    def __str__(self, *args, **kwargs):
        string = "DeweCh {} ({}): \r\n".format(self.channel_number, self.name)
        string += "\tUnit: {}\r\n".format(self.unit)
        string += "\tSamplerate Divider: {}\r\n".format(
            self.samplerate_divider)
        string += "\tMeasurement Type: {}\r\n".format(self.measurement_type)
        string += "\tSample Data Type: {}\r\n".format(self.sample_data_type)
        string += "\tBuffer Size: {}\r\n".format(self.buffer_size)
        string += "\tCustom Scale: {}\r\n".format(self.custom_scale)
        string += "\tCustom Offset: {}\r\n".format(self.custom_offset)
        string += "\tScale Raw Data: {}\r\n".format(self.scale_raw_data)
        string += "\tOffset Raw Data: {}\r\n".format(self.offset_raw_data)
        string += "\tDescription: {}\r\n".format(self.description)
        string += "\tSettings: {}\r\n".format(self.settings)
        string += "\tRange min: {}\r\n".format(self.range_min)
        string += "\tRange max: {}\r\n".format(self.range_max)
        string += "\tValue min: {}\r\n".format(self.value_min)
        string += "\tValue max: {}\r\n".format(self.value_max)
        string += "\tActual Value: {}\r\n".format(self.value_act)
        return string

    def __repr__(self, *args, **kwargs):
        return self.name + " (ChannelInfo)"

    def get_info_as_dict(self):
        """ Get all references as dict.

        Get all stored information variables of the channel as an dictionary.

        Returns:
            dict: Dict of all stored attributes
        """
        info = {
            'name': self.name,
            'unit': self.unit,
            'samplerate_divider': self.samplerate_divider,
            'measurement_type': self.measurement_type,
            'sample_data_type': self.sample_data_type,
            'buffer_size': self.buffer_size,
            'custom_scale': self.custom_scale,
            'custom_offset': self.custom_offset,
            'scale_raw_data': self.scale_raw_data,
            'offset_raw_data': self.offset_raw_data,
            'value_act': self.value_act,
            'settings': self.settings,
            'channel_number': self.channel_number,
            'range_min': self.range_min,
            'range_max': self.range_max,
            'value_min': self.value_min,
            'value_max': self.value_max
        }

        return info

    _value_converter = {
        'size': {0: 1, 1: 1, 2: 2, 3: 3, 4: 4, 5: 4, 6: 8, 7: 8},
        'decoder': {0: 'B', 1: 'b', 2: 'h', 3: 'H',
                    4: 'i', 5: 'f', 6: 'q', 7: 'd'}
    }

    # Converter dictionary for DeweSoft's data types.

    # The converter dictionary will contains following entries:

    # size: The number of bytes that are used to store the specific DeweSoft's
    #       data value. It will be used by the TCP server to receive the
    #       specific number of byter
    # decoder: The formatter string for the struct.unpack function to interpret
    #          the received bytes during the encoding of the raw values.

    def get_value_size(self):
        """ Read size of value.

        This function calculates the used size of the channel's value in bytes.

        Returns:
            int: Size of the value calculated in number of bytes
        """
        return DeweChannelInfo._value_converter['size'][self.sample_data_type]

    def get_value_format(self):
        """ Get the value formatter.

        Get the formatter for the struct command of the stored channel

        Returns:
            str: formatter string for using in the struct conversion

        """
        decoder = DeweChannelInfo._value_converter['decoder']
        return decoder[self.sample_data_type]
