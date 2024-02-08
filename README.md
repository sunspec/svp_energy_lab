# Description
System Validation Platform (SVP) library that enables communication with energy lab equipment.

# Installation and Configuration
To get the SVP operational, download the following repositories:
* [The SVP graphical user interface](https://github.com/jayatsandia/svp)
* [The SVP energy lab code](https://github.com/jayatsandia/svp_energy_lab)
* [IEEE 1547.1 working directory](https://github.com/jayatsandia/svp_1547.1) or another working directory
* Install [pysunspec2](https://github.com/sunspec/pysunspec2) from the latest release (it may also be pip-able now)

Install the SVP dependencies using this [guide](https://github.com/jayatsandia/svp/blob/master/doc/INSTALL.md).  It’s recommended to use Python 3.7.X because there were some issues reported for 3.9+. 

To run an SVP test, you will need to do the following: 
1. Copy the `Lib` directory from the svp_energy_lab into the `Lib` folder in svp_1547.1 (we decided to keep a single, separate copy of the drivers in svp_energy_lab to simplify management). When you do this, leave the `p1547.py` file in the svpelab subdirectory that comes with svp_1547.1.  You will need that. 
2. Run the `ui.py` code in the opensvp to generate the GUI. 
3. Navigate to the Interoperability Test in `tests` in the left pane of the GUI, right click -> edit. 
    * Set the DER1547 Parameters – Mode: SunSpec 
    * Set the Interface to “Mapped SunSpec Device”
    * Set the map file to the path to the `Lib/svpelab/sunspec_device_1547.json` file. (This contains a file representing the PV inverter that is compliant the SunSpec Modbus protocol). 
4. Run the test and verify it works. 
5. Edit the InteroperatiblityTests.py file in the Scripts directory. 
6. When you run the test the code in the `test_run()` function runs.  If you would like something new printed to the screen you can write something like this `ts.log('Hello World')`.  If you would like to see registers of the simulated DER device you can print those too. Change the code to this:
```
# initialize DER configuration
eut = der1547.der1547_init(ts)
eut.config()
ts.log_debug('SunSpec info: %s' % eut.print_modbus_map(w_labels=True))
```
7. Note, this will call the `print_modbus_map()` method in the `Lib` folder in `der1547_modbus.py` that will print out all the registers in the simulated DER device.  Play with changing parameters and rerunning the tests. 

Some noteworthy items: 
* See how the test setup parameters using `info.param()`.  The user can try to make some new parameters.  When you restart the svp these will appear as new options in the test!
* Look at how there are different abstraction layers for the major components (`gridsim.py`, `hil.py`, etc.)  The abstraction layers are in the `Lib` folder and will add options based on the files that have `gridsim_*.py` file names. 
* You may want to create new drivers for the lab equipment that you have.  For instance, if you have an Omicron DC Simulator, you would make a new `pvsim_omicron.py` file if it doesn’t exist already.  You will need to make it uniquely named so the abstraction layer will find it, but then it will appear in the pull down menu in the GUI.  

