"""
Copyright (c) 2017, Sandia National Labs and SunSpec Alliance
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

Neither the names of the Sandia National Labs and SunSpec Alliance nor the names of its
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

Questions can be directed to support@sunspec.org
"""

import sys
import os
import glob
import importlib

# switch controller
SWITCH_CLOSED = True
SWITCH_OPEN = False

switch_modules = {}


def params(info, id=None, label='Switch Controller', group_name=None, active=None, active_value=None):
    """
    Defines a function to create parameters for a switch controller implementation.
    
    The `params` function creates a parameter group for a switch controller implementation,
    with a default group name of `SWITCH_DEFAULT_ID`. 
    
    Args:
        info (object): An object that provides methods for defining parameters.
        id (int, optional): An optional identifier for the switch controller.
        label (str, optional): A label for the parameter group.
        group_name (str, optional): An optional group name for the parameters.
        active (str, optional): An optional active condition for the parameter group.
        active_value (any, optional): An optional active value for the parameter group.
    
    Returns:
        None
    """
    if group_name is None:
        group_name = SWITCH_DEFAULT_ID
    else:
        group_name += '.' + SWITCH_DEFAULT_ID
    if id is not None:
        group_name += '_' + str(id)
    print('group_name = %s' % group_name)
    name = lambda name: group_name + '.' + name
    info.param_group(group_name, label='%s Parameters' % label, active=active, active_value=active_value, glob=True)
    print('name = %s' % name('mode'))
    info.param(name('mode'), label='Mode', default='Disabled', values=['Disabled'])
    for mode, m in switch_modules.items():
        m.params(info, group_name=group_name)

SWITCH_DEFAULT_ID = 'switch'


def switch_init(ts, id=None, group_name=None):
    """
    This function initializes a switch controller device based on the specified mode. It creates an 
    instance of the appropriate switch controller implementation class and returns it.
    
    Args:
        ts (object)                 : A test script object that provides access to test script parameters and logging.
        id (int, optional)          : An optional identifier for the switch controller.
        group_name (str, optional)  : An optional group name for the switch controller parameters.
    
    Returns:
        object: An instance of the appropriate switch controller implementation class, or None if the mode is 'Disabled'.
    
    Raises:
        SwitchError: If the specified mode is unknown.
    """
    if group_name is None:
        group_name = SWITCH_DEFAULT_ID
    else:
        group_name += '.' + SWITCH_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    mode = ts.param_value(group_name + '.' + 'mode')
    # ts.log_debug('group_name, %s, mode: %s' % (group_name, mode))
    sim = None
    if mode != 'Disabled':
        # ts.log_debug('mode, %s' % (mode))
        switch_module = switch_modules.get(mode)
        # ts.log_debug('switch_module, %s, switch_modules: %s' % (switch_module, switch_modules))
        if switch_module is not None:
            sim = switch_module.Switch(ts, group_name)
        else:
            raise SwitchError('Unknown switch controller mode: %s' % mode)

    return sim


class SwitchError(Exception):
    """
    Exception to wrap all switch generated exceptions.
    """
    pass


class Switch(object):
    """
    A class representing a switch controller device.

    Methods:
    - info(self): Returns information about the switch.
    - open(self): Opens the switch.
    - close(self): Closes the switch.
    - switch_open(self): Opens the switch (alternative method).
    - switch_close(self): Closes the switch (alternative method).
    - switch_state(self): Returns the current state of the switch.
    """

    def __init__(self, ts, group_name):
        """
        Initialize the Switch object.

        Args:
        - ts: Test script object
        - group_name: Group name for the switch controller parameters
        """
        self.ts = ts
        self.group_name = group_name
        self.device = None
        self.params = {}
        self.switch_state = False

    def info(self):
        """
        Return information string for the switch controller device.

        Raises:
        - SwitchError: If the switch device is not initialized
        """
        if self.device is None:
            raise SwitchError('Switch device not initialized')
        return self.device.info()

    def open(self):
        """
        Open communications resources associated with the switch controller device.

        Raises:
        - SwitchError: If the switch device is not initialized
        """
        if self.device is None:
            raise SwitchError('Switch device not initialized')
        self.device.open()

    def close(self):
        """
        Close any open communications resources associated with the switch controller device.

        Raises:
        - SwitchError: If the switch device is not initialized
        """
        if self.device is None:
            raise SwitchError('Switch device not initialized')
        self.device.close()
        
    def switch_open(self):
        """
        Open the switch associated with this device.

        Raises:
        - SwitchError: If the switch device is not initialized

        Returns:
        - The current switch state
        """
        if self.device is None:
            raise SwitchError('Switch device not initialized')
        self.device.switch_open()
        self.switch_state = SWITCH_OPEN
        return self.switch_state
        
    def switch_close(self):
        """
        Close the switch associated with this device.

        Raises:
        - SwitchError: If the switch device is not initialized
        """
        if self.device is None:
            raise SwitchError('Switch device not initialized')
        self.device.switch_close()
        self.switch_state = SWITCH_CLOSED

    def switch_state(self):
        """
        Get the state of the switch associated with this device.

        Raises:
        - SwitchError: If the switch device is not initialized

        Returns:
        - The current switch state
        """
        if self.device is None:
            raise SwitchError('Switch device not initialized')
        return self.switch_state

def switch_scan():
    """
    Scans for switch modules in the current directory and imports them into the `switch_modules` dictionary, keyed by the 
    'mode' attribute of the module's `switch_info()` function.
    
    This function is responsible for dynamically loading and registering switch modules in the system. It searches for 
    files matching the pattern 'switch_*.py' in the current directory, imports each module, and extracts the 'mode' attribute 
    from the module's `switch_info()` function. The imported modules are then stored in the `switch_modules` dictionary, keyed by their 'mode' value.
    
    This allows the system to dynamically discover and load new switch modules without having to explicitly register them.
    """  
    global switch_modules
    # scan all files in current directory that match switch_*.py
    package_name = '.'.join(__name__.split('.')[:-1])
    files = glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'switch_*.py'))
    for f in files:
        module_name = None
        try:
            module_name = os.path.splitext(os.path.basename(f))[0]
            if package_name:
                module_name = package_name + '.' + module_name
            m = importlib.import_module(module_name)
            if hasattr(m, 'switch_info'):
                info = m.switch_info()
                mode = info.get('mode')
                # place module in module dict
                if mode is not None:
                    switch_modules[mode] = m
            else:
                if module_name is not None and module_name in sys.modules:
                    del sys.modules[module_name]
        except Exception as e:
            if module_name is not None and module_name in sys.modules:
                del sys.modules[module_name]
            raise SwitchError('Error scanning module %s: %s' % (module_name, str(e)))

# scan for switch modules on import
switch_scan()

if __name__ == "__main__":
    pass
