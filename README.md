#Description

This repository represents a basic System Validation Platform (SVP) directory with energy lab equipment basic scripts, complete drivers and abstraction layers. 
Its purpose is mainly for driver development. 

# Installation and configuration

To get SVP operational, download and install the **([SVP application] insert link here)**.

Then, if your goal is to develop or run scripts in the context of standard certification, you can take a look at the SVP application README.md 
or directly to **([IEEE1547.1] insert link here)** as a great example.


# Concepts

There are several different user domains for the SVP. At the highest-level, there are operators than can launch the application and use the GUI interface.  The next level down, users would be able to create or modify script logic (See 
Scripts, Tests and Suites section in [OpenSVP](https://github.com/sunspec/svp)).  The next layer are software programmers who are modifying the device drivers and/or abstraction layers.  

![image](https://github.com/user-attachments/assets/6c12e883-5c63-4a8b-8446-3460750ae114)

The software is hierachical.  The GUI reads in the subdirectories of the working directories (i.e., "Scripts", "Tests", "Suites", and/or "Results"): 
	* Scripts - Python (`.py`) files - that include the test logic
	* Tests - xml-encoded `.tst` files - that include the parameters used in a script for a given test. 
	* Suites - xml-encoded `.ste` files - that include the tests in the group plus any parameters used in the suite. 
	* Results - Results manifests and saved files from a test or suite. 
	* Lib - Python (`.py`) files - that define the operations of the SVP. 
	
Importantly, the SVP passes test logic from the script down the low-level equipment device drivers through abstraction layers.  

```
script function -> abstraction layer -> device driver -> (optional) stand-alone driver
```

#### Example
Let's look at an example.  Here we'd like to set the voltage of a Grid simulator to 240 Vac. 

The **script** would include a line: 
```python
grid.voltage(voltage=240.)
```

The **abstration layer** (`gridsim.py`) includes the following method placeholder: 
```python
 def voltage(self, voltage=None):
        """
        Set the value for voltage 1, 2, 3 if provided. If none provided, obtains
        the value for voltage. Voltage is a tuple containing a voltage value for
        each phase.
        """
        if voltage is not None:
            pass
        else:
            voltage = (0.0, 0.0, 0.0)
        return voltage
```
And the Ametek grid simulator **driver** (`gridsim_ametek.py`) includes the code to actually communicate with the lab equipment--in this case using SCPI (IEEE 488.2) commands. 
```python
def voltage(self, voltage=None):
	"""
	Set the value for voltage 1, 2, 3 if provided. If none provided, obtains
	the value for voltage. Voltage is a tuple containing a voltage value for
	each phase.
	"""
	if voltage is not None:
		# set output voltage on all phases
		# self.ts.log_debug('voltage: %s, type: %s' % (voltage, type(voltage)))
		if type(voltage) is not list and type(voltage) is not tuple:
			self.cmd('inst:coup all;:volt:ac %0.1f\n' % voltage)
		else:
			self.cmd('inst:coup all;:volt:ac %0.1f\n' % voltage[0])  # use the first value in the 3 phase list
	v1 = self.query('inst:coup none;:inst:nsel 1;:volt:ac?\n')
	v2 = self.query('inst:nsel 2;:volt:ac?\n')
	v3 = self.query('inst:nsel 3;:volt:ac?\n')
	return float(v1[:-1]), float(v2[:-1]), float(v3[:-1])
```

### Abstraction Layers

The abstraction layers include: 
* `battsim.py` - Battery simulator
* `das.py` - Data Acquisition System
* `dcsim.py` - DC Simulator
* `der.py` - Distributed Energy Resource (DER) 
* `der1547.py` - Distributed Energy Resource (DER) with IEEE1547 communication protocoles
* `hil.py` - Hardware-in-the-loop
* `genset.py` - Engine-Generator (genset)
* `gridsim.py` - Grid (AC) simulator
* `loadsim.py` - Load simulator
* `network.py` - Network capture tools
* `pvsim.py` - PV simulator
* `switch.py` - Switch
* `wavegen.py` - Waveform generator

These include logical placeholder methods that will need to be replicated in each of the device drivers, or the drivers will inherit the method with a "pass" that will take no operation. 

### Device Drivers

Critically, all drivers under an abstraction layer must be labeled in accorance with the abstraction layer, e.g., "der_*.py", "gridsim_*.py", or "pvsim_*.py".  This allows the scanning function that is in the abstraction layer to find each of the drivers so these can be presented as options in the drop-down menu. In many cases, the full logic of the driver is created at this level; however, in other situations, there will be a lower layer Python file that will include the control logic to the device. There are generally named "device_*.py", e.g., `device_<equipment>.py`.  Originally, these files included the low-level communications instructions and could be run independent of the SVP architecture. However, that's often no longer the case because debug statements like `self.ts.log_debug('something')` often appear in these files.  

Scripts can only access device driver methods that exist in the abstraction layer, so please be careful to replicate the methods that exist at the abstraction layer when creating drivers.  If necessary, please add another method to the abstraction layer to add new functionality to these types of devices. 




