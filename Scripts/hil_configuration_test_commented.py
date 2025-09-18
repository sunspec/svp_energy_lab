'''
This kind of script is used for testing a specific device's driver. It is
usually for commissioning purposes or during the coding of drivers.
'''

'''
Import section: 
If you are testing specific equipment, you need to import its abstraction layer from svpelab like the hil
 abstraction layer below
'''
import sys
import os
import traceback
from svpelab import hil # HIL abstraction layer

import script


def test_run():
    '''
    Test_run() is the function where the test logic is located The test usually follows these stages :
    1. Initialisation : This stage is where the device parameters are defined and the devices are initialised
    2. Test execution : After initialisation, the different test step are executed. Then, for some device it might be
    interesting to add some post-processing
    3. Closing : the devices are properly shutdown
    '''

    ''' 1. Initialisation--------------------------------------------------------------------------------------------'''
    result = script.RESULT_PASS
    phil = None


    try:
        # Below we are fetching parameters that the user entered in the SVP edit window of this specific test (Look at
        # the info section at the bottom of this code)
        compilation = ts.param_value('hil_config.compile')
        load = ts.param_value('hil_config.load')
        execute = ts.param_value('hil_config.execute')
        # initialize the hardware in the loop
        phil = hil.hil_init(ts) # Every devices is initialized through it's abstraction layer as shown here

        ''' 2. Execution---------------------------------------------------------------------------------------------'''
        if phil is not None: # Always verify that the device exist
            ts.log("{}".format(phil.info()))
            #Verify if the driver can start the Opal-RT model compilation
            if compilation == 'Yes':
                ts.log("    Model ID : {}".format(phil.compile_model().get("modelId")))
            # Verify if the driver can load the Opal-RT model in the Opal-RT target
            if load == 'Yes':
                ts.log("    {}".format(phil.load_model_on_hil()))
            # Verify if the driver can execute the Opal-rt real-time simulation
            if execute == 'Yes':
                ts.log("    {}".format(phil.start_simulation()))

        ''' 3. Closing-----------------------------------------------------------------------------------------------'''
    except script.ScriptFail as e: # If there is any exception occurring in the code, it should be caught here and shown
        # in the SVP UI
        reason = str(e)
        if reason:
            ts.log_error(reason)
    finally:
        # For all the device in use, you need to close them properly with their own close function.
        if phil is not None:
            phil.close()

    return result # Test_run() always return some results, but in this context it is replaced by the script.RESULT_PASS



def run(test_script):
    '''
    The run function is the first one called by SVP which initialise the environnement around the test.
    '''
    try:
        global ts # ts is the most valuable variable of your test since it contains the configuration of the test and
        # can be used for logging through SVP UI or fetching data, it also pass through most parts of SVP.
        ts = test_script
        rc = 0
        result = script.RESULT_COMPLETE

        ts.log_debug('')
        ts.log_debug('**************  Starting %s  **************' % (ts.config_name()))
        ts.log_debug('Script: %s %s' % (ts.name, ts.info.version))
        ts.log_active_params()

        ts.svp_version(required='1.5.9')

        result = test_run() # Here it calls test_run above

        ts.result(result)
        if result == script.RESULT_FAIL:
            rc = 1

    except Exception as e:
        ts.log_error('Test script exception: %s' % traceback.format_exc())
        rc = 1

    sys.exit(rc)
'''
Info section :

Here we establish the parameters section of the SVP UI when you click on the script or related test.
However, most of the device info are coded in their respective drivers and then called below like hil.params(info)
Then, for the specific test parameters/info, you need to define them as shown directly below. 
'''
# Test parameters/info
info = script.ScriptInfo(name=os.path.basename(__file__), run=run, version='1.0.0')
# Data acquisition
info.param_group('hil_config', label='HIL Configuration')
info.param('hil_config.compile', label='Compilation need it?', default="Yes", values=["Yes", "No"])
info.param('hil_config.load', label='Load the model to target?', default="Yes", values=["Yes", "No"])
info.param('hil_config.execute', label='Execute the model to target?', default="Yes", values=["Yes", "No"])

# Specific device parameters/info
hil.params(info)

def script_info():
    
    return info


if __name__ == "__main__":

    config_file = None
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    params = None

    test_script = script.Script(info=script_info(), config_file=config_file, params=params)
    test_script.log('log it')

    run(test_script)



