# wanbin son 

import time

TERMINATOR = "\n"
TEST = None

class ChromaBattSimError(Exception):
    pass

class ChromaBattSim(object):
    def __init__(self,ts, visa_device, visa_path = None):	#wanbin
        self.conn = None
        self.visa_device = visa_device
        self.visa_path = visa_path
        self.ts=ts
        
    def _query(self, cmd_str):
        """
        Performs an SCPI Querry
        :param cmd_str:
        :return:
        """
        if TEST is not None:
            print(cmd_str.strip())
            return '0.0'
        try:
            if self.conn is None:
                raise ChromaBattSimError('GPIB connection not open')
            return self.conn.query(cmd_str.strip('\n'))

        except Exception, e:
            raise ChromaBattSimError(str(e))
        
    def query(self, cmd_str):
        try:
            resp = self._query(cmd_str).strip()
        except Exception, e:
            raise ChromaBattSimError(str(e))
        return resp

        
    def _cmd(self, cmd_str):
        """
        Performs an SCPI Querry
        :param cmd_str:
        :return:
        """
        if TEST is not None:
            print cmd_str.strip()
            return
        try:
            if self.conn is None:
                raise ChromaBattSimError('connection not open')
            return self.conn.write(cmd_str.strip('\n'))
        except Exception, e:
            raise ChromaBattSimError(str(e))

    def cmd(self, cmd_str):
        try:
            self._cmd(cmd_str)
            resp = self._query('SYST:ERR?\n') #\r
            print 'resp\n'
            print resp
            if len(resp) > 0:
                if resp[0] != '0':
                    raise ChromaBattSimError(resp + ' ' + cmd_str)

        except Exception, e:
            raise ChromaBattSimError(str(e))
            
            
    def open(self):
        import visa
        """
        Open the communications resources associated with the device.
        """
        try:
            self.rm = visa.ResourceManager() 
            self.conn = self.rm.open_resource(self.visa_device)
            # set terminator in pyvisa
            self.conn.write_termination = TERMINATOR
            self.conn.read_termination = TERMINATOR
            self.conn.timeout=10000
            self.cmd('OUTPut:MODe 1')
        except Exception, e:
            raise ChromaGridSimError('Cannot open VISA connection to %s' % (self.visa_device))

    def protection_clear(self):
        self.cmd('PROTection:CLEar')
        
    def set_capacity(self, cap):
		self.cmd("BATTery:CAP %f" % cap)	

    def set_curve(self,soc,vol,dcr_d,dcr_c):
        cmd_str="BATTery:CURVe 0, %d " % len(vol)
        for item in vol:
            cmd_str+=", %.2f" % item 
        self.cmd(cmd_str)
        cmd_str="BATTery:CURVe 1, %d " % len(soc)
        for item in soc:
            cmd_str+=", %.1f" % item 
        self.cmd(cmd_str)
		
        cmd_str="BATTery:CURVe 2, %d " % len(dcr_d)
        for item in dcr_d:
            cmd_str+=", %f" % item 
        self.cmd(cmd_str)

        cmd_str="BATTery:CURVe 3, %d " % len(dcr_c)
        for item in dcr_c:
            cmd_str+=", %f" % item 
        self.cmd(cmd_str)
        
        self.ts.log_debug("BATTery:VH %f" % max(vol))
        self.cmd("BATTery:VH %f" % max(vol))
        self.cmd("BATTery:VL %f" % min(vol))


    def set_init_soc(self, soc):
        self.cmd("BATTery:INITial 0")     
        self.cmd("BATTery:INITial:CAP %f" % soc)
        #self.query("BATTery:INITial:CAP?")

    def set_volt_alarm(self, low, high):
        self.cmd("BATTery:BVL %.2f" % low)     
        self.cmd("BATTery:BVH %.2f" % high)     


    def set_volt_protection(self, low, high):
        self.cmd("BATTery:VOLP %.2f" % low) # Low Voltage Protection
        self.cmd("BATTery:VOH %.2f" % high) # High Voltage Protection        
        
        self.cmd("BATTery:BOH 110")         # high soc protection
        self.cmd("BATTery:BOL -20")         # low soc protection
        

    def set_current_protection(self, high):
        self.cmd("BATTery:OCP %.2f" % high)     

    def set_esr(self, esr):
        self.cmd("BATTery:ESR %.3f" % esr)

    def set_efficiency(self, charge, discharge):
        self.cmd("BATTery:EFFCHG %.1f" % charge)
        self.cmd("BATTery:EFFDSG %.1f" % discharge)

    def power_on(self):
        #self.cmd("CHANnel:SOURce 1")
        self.cmd("BATTery:OUTPut 1")	# mode A.  consider mode B

    def power_off(self):
        self.cmd("BATTery:OUTPut OFF")	# off

    def get_volt(self):
		return self.query("MEASure:VOLT?")
		
    def is_error(self):
        resp=self._query("MEAS:STATe?\n")        
        if int(resp.split(",")[0])!=0:
            return True
        else:
            return False


if __name__ == "__main__":
    TEST=True
    a=ChromaBattSim("TCPIP::192.168.1.100::60000::SOCKET")
    a.protection_clear()
    a.set_capacity(100)
    a.set_curve(range(10),range(10),range(10),range(10))
    a.set_init_soc(50)
    pass
