"""
Copyright (c) 2018, Sandia National Laboratories
All rights reserved.

V1.0 - Jay Johnson - 7/31/2018
"""

import sys
import os
import glob
import importlib

genset_modules = {}

def params(info, id=None, label='Genset', group_name=None, active=None, active_value=None):
    if group_name is None:
        group_name = GENSET_DEFAULT_ID
    else:
        group_name += '.' + GENSET_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    name = lambda name: group_name + '.' + name
    info.param_group(group_name, label='%s Parameters' % label,  active=active, active_value=active_value, glob=True)
    info.param(name('mode'), label='%s Mode' % label, default='Disabled', values=['Disabled'])
    for mode, m in genset_modules.items():
        m.params(info, group_name=group_name)

GENSET_DEFAULT_ID = 'genset'


def genset_init(ts, id=None, group_name=None):
    """
    Function to create specific genset implementation instances.
    """
    if group_name is None:
        group_name = GENSET_DEFAULT_ID
    else:
        group_name += '.' + GENSET_DEFAULT_ID
    if id is not None:
        group_name = group_name + '_' + str(id)
    print('run group_name = %s' % group_name)
    mode = ts.param_value(group_name + '.' + 'mode')
    sim = None
    if mode != 'Disabled':
        sim_module = genset_modules.get(mode)
        if sim_module is not None:
            sim = sim_module.Genset(ts, group_name)
        else:
            raise GensetError('Unknown Genset system mode: %s' % mode)

    return sim


class GensetError(Exception):
    """
    Exception to wrap all genset generated exceptions.
    """
    pass


class Genset(object):
    """
    Template for genset implementations. This class can be used as a base class or
    independent genset classes can be created containing the methods contained in this class.
    """

    def __init__(self, ts, group_name):
        self.ts = ts
        self.group_name = group_name

    def config(self):
        """ Perform any configuration for the simulation based on the previously provided parameters. """
        pass

    def open(self):
        """ Open the communications resources associated with the genset. """
        pass

    def close(self):
        """ Close any open communications resources associated with the genset. """
        pass

    def info(self):
        pass

    def measurements(self):
        """ Get measurement data.
        :params: None
        :return: Dictionary of measurement data.
        """
        pass

    def settings(self, params=None):
        """ Get genset settings.
        :params:
        :return: Dictionary of settings.
        """
        pass

    def conn_status(self, params=None):
        """ Get status of controls (binary True if active).
        :params:
        :return: Dictionary of active controls.
        """
        pass

    def controls_status(self, params=None):
        """ Get status of controls (binary True if active).
        :params: None
        :return: Dictionary of active controls.
        """
        pass

    def connect(self, params=None):
        """ Get/set connect/disconnect function settings.

        :param params: Dictionary of parameters. Following keys are supported: enable, conn, win_tms, rvrt_tms.
        :return: Dictionary of active settings for fixed factor.
        """

        if params is None:
            # get current settings
            params = {}
        else:
            # apply params
            pass

        return params


def genset_scan():
    global genset_modules
    # scan all files in current directory that match genset_*.py
    package_name = '.'.join(__name__.split('.')[:-1])
    files = glob.glob(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'genset_*.py'))
    for f in files:
        module_name = None
        try:
            module_name = os.path.splitext(os.path.basename(f))[0]
            if package_name:
                module_name = package_name + '.' + module_name
            m = importlib.import_module(module_name)
            if hasattr(m, 'genset_info'):
                info = m.genset_info()
                mode = info.get('mode')
                # place module in module dict
                if mode is not None:
                    genset_modules[mode] = m
            else:
                if module_name is not None and module_name in sys.modules:
                    del sys.modules[module_name]
        except Exception as e:
            if module_name is not None and module_name in sys.modules:
                del sys.modules[module_name]
            raise GensetError('Error scanning module %s: %s' % (module_name, str(e)))

# scan for genset modules on import
genset_scan()

if __name__ == "__main__":
    pass
