'''
Copyright (c) 2016, Sandia National Labs and SunSpec Alliance
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

Written by Sandia National Laboratories, Loggerware, and SunSpec Alliance
Questions can be directed to Jay Johnson (jjohns2@sandia.gov)
'''

#!C:\Python27\python.exe

import sys
import os
import traceback
# from svpelab import das
from svpelab import der
import script

def test_run():

    # initialize DER configuration
    eut = der.der_init(ts)
    eut.config()

    ts.log('---')
    info = eut.info()
    if info is not None:
        ts.log('DER info:')
        ts.log('  Manufacturer: %s' % (info.get('Manufacturer')))
        ts.log('  Model: %s' % (info.get('Model')))
        ts.log('  Options: %s' % (info.get('Options')))
        ts.log('  Version: %s' % (info.get('Version')))
        ts.log('  Serial Number: %s' % (info.get('SerialNumber')))
    else:
        ts.log_warning('DER info not supported')
    ts.log('---')
    m = eut.measurements()
    if m is not None:
        ts.log('DER measurements:')
        ts.log('  A: %s' % (m.get('A')))
        ts.log('  AphA: %s' % (m.get('AphA')))
        ts.log('  AphB: %s' % (m.get('AphB')))
        ts.log('  AphC: %s' % (m.get('AphC')))
        ts.log('  PPVphAB: %s' % (m.get('PPVphAB')))
        ts.log('  PPVphBC: %s' % (m.get('PPVphBC')))
        ts.log('  PPVphCA: %s' % (m.get('PPVphCA')))
        ts.log('  PhVphA: %s' % (m.get('PhVphA')))
        ts.log('  PhVphB: %s' % (m.get('PhVphB')))
        ts.log('  PhVphC: %s' % (m.get('PhVphC')))
        ts.log('  W: %s' % (m.get('W')))
        ts.log('  Hz: %s' % (m.get('Hz')))
        ts.log('  VA: %s' % (m.get('VA')))
        ts.log('  VAr: %s' % (m.get('VAr')))
        ts.log('  PF: %s' % (m.get('PF')))
        ts.log('  WH: %s' % (m.get('WH')))
        ts.log('  DCA: %s' % (m.get('DCA')))
        ts.log('  DCV: %s' % (m.get('DCV')))
        ts.log('  DCW: %s' % (m.get('DCW')))
        ts.log('  TmpCab: %s' % (m.get('TmpCab')))
        ts.log('  TmpSnk: %s' % (m.get('TmpSnk')))
        ts.log('  TmpTrns: %s' % (m.get('TmpTrns')))
        ts.log('  TmpOt: %s' % (m.get('TmpCt')))
        ts.log('  St: %s' % (m.get('St')))
        ts.log('  StVnd: %s' % (m.get('StVnd')))
        ts.log('  Evt1: %s' % (m.get('Evt1')))
        ts.log('  Evt2: %s' % (m.get('Evt2')))
        ts.log('  EvtVnd1: %s' % (m.get('EvtVnd1')))
        ts.log('  EvtVnd2: %s' % (m.get('EvtVnd2')))
        ts.log('  EvtVnd3: %s' % (m.get('EvtVnd3')))
        ts.log('  EvtVnd4: %s' % (m.get('EvtVnd4')))
    else:
        ts.log_warning('DER measurements not supported')
    ts.log('---')
    nameplate = eut.nameplate()
    if nameplate is not None:
        ts.log('DER nameplate:')
        ts.log('  WRtg: %s' % (nameplate.get('WRtg')))
        ts.log('  VARtg: %s' % (nameplate.get('VARtg')))
        ts.log('  VArRtgQ1: %s' % (nameplate.get('VArRtgQ1')))
        ts.log('  VArRtgQ2: %s' % (nameplate.get('VArRtgQ2')))
        ts.log('  VArRtgQ3: %s' % (nameplate.get('VArRtgQ3')))
        ts.log('  VArRtgQ4: %s' % (nameplate.get('VArRtgQ4')))
        ts.log('  ARtg: %s' % (nameplate.get('ARtg')))
        ts.log('  PFRtgQ1: %s' % (nameplate.get('PFRtgQ1')))
        ts.log('  PFRtgQ2: %s' % (nameplate.get('PFRtgQ2')))
        ts.log('  PFRtgQ3: %s' % (nameplate.get('PFRtgQ3')))
        ts.log('  PFRtgQ4: %s' % (nameplate.get('PFRtgQ4')))
        ts.log('  WHRtg: %s' % (nameplate.get('WHRtg')))
        ts.log('  AhrRtg: %s' % (nameplate.get('AhrRtg')))
        ts.log('  MaxChaRte: %s' % (nameplate.get('MaxChrRte')))
        ts.log('  MaxDisChaRte: %s' % (nameplate.get('MaxDisChaRte')))
    else:
        ts.log_warning('DER nameplate not supported')
    ts.log('---')
    settings = eut.settings()
    if settings is not None:
        ts.log('DER settings:')
        ts.log('  WMax: %s' % (settings.get('WMax')))
        ts.log('  VRef: %s' % (settings.get('VRef')))
        ts.log('  VRefOfs: %s' % (settings.get('VRefOfs')))
        ts.log('  VMax: %s' % (settings.get('VMax')))
        ts.log('  VMin: %s' % (settings.get('VMin')))
        ts.log('  VAMax: %s' % (settings.get('VAMax')))
        ts.log('  VArMaxQ1: %s' % (settings.get('VArMaxQ1')))
        ts.log('  VArMaxQ2: %s' % (settings.get('VArMaxQ2')))
        ts.log('  VArMaxQ3: %s' % (settings.get('VArMaxQ3')))
        ts.log('  VArMaxQ4: %s' % (settings.get('VArMaxQ4')))
        ts.log('  WGra: %s' % (settings.get('WGra')))
        ts.log('  PFMaxQ1: %s' % (settings.get('PFMaxQ1')))
        ts.log('  PFMaxQ2: %s' % (settings.get('PFMaxQ2')))
        ts.log('  PFMaxQ3: %s' % (settings.get('PFMaxQ3')))
        ts.log('  PFMaxQ4: %s' % (settings.get('PFMaxQ4')))
        ts.log('  VArAct: %s' % (settings.get('VArAct')))
    else:
        ts.log_warning('DER settings not supported')
    ts.log('---')
    connect = eut.connect()
    if connect is not None:
        ts.log('DER connect:')
        ts.log('  Conn: %s' % (connect.get('Conn')))
        ts.log('  WinTms: %s' % (connect.get('WinTms')))
        ts.log('  RvrtTms: %s' % (connect.get('RvrtTms')))
    else:
        ts.log_warning('DER connect not supported')
    ts.log('---')
    fixed_pf = eut.fixed_pf()
    if fixed_pf is not None:
        ts.log('DER fixed_pf:')
        ts.log('  Ena: %s' % (fixed_pf.get('Ena')))
        ts.log('  PF: %s' % (fixed_pf.get('PF')))
        ts.log('  WinTms: %s' % (fixed_pf.get('WinTms')))
        ts.log('  RmpTms: %s' % (fixed_pf.get('RmpTms')))
        ts.log('  RvrtTms: %s' % (fixed_pf.get('RvrtTms')))
    else:
        ts.log_warning('DER fixed_pf not supported')
    ts.log('---')
    wmax = eut.limit_max_power()
    if wmax is not None:
        ts.log('DER limit_max_power:')
        ts.log('  Ena: %s' % (wmax.get('Ena')))
        ts.log('  WMaxPct: %s' % (wmax.get('WMaxPct')))
        ts.log('  WinTms: %s' % (wmax.get('WinTms')))
        ts.log('  RmpTms: %s' % (wmax.get('RmpTms')))
        ts.log('  RvrtTms: %s' % (wmax.get('RvrtTms')))
    else:
        ts.log_warning('DER limit_max_power not supported')
    ts.log('---')

    volt_var = eut.volt_var()
    if volt_var is not None:
        ts.log('DER volt/var:')
        ts.log('  Ena: %s' % (volt_var.get('Ena')))
        ts.log('  ActCrv: %s' % (volt_var.get('ActCrv')))
        ts.log('  NCrv: %s' % (volt_var.get('NCrv')))
        ts.log('  NPt: %s' % (volt_var.get('NPt')))
        ts.log('  WinTms: %s' % (volt_var.get('WinTms')))
        ts.log('  RmpTms: %s' % (volt_var.get('RmpTms')))
        ts.log('  RvrtTms: %s' % (volt_var.get('RvrtTms')))
        curve = volt_var.get('curve')
        if curve is not None:
            ts.log('  curve #%d:' % (curve.get('id')))
            ts.log('    v: %s' % (curve.get('v')))
            ts.log('    var: %s' % (curve.get('var')))
            ts.log('    DeptRef: %s' % (curve.get('DeptRef')))
            ts.log('    RmpTms: %s' % (curve.get('RmpTms')))
            ts.log('    RmpDecTmm: %s' % (curve.get('RmpDecTmm')))
            ts.log('    RmpIncTmm: %s' % (curve.get('RmpIncTmm')))
    else:
        ts.log_warning('DER volt_var not supported')

    '''
    eut.volt_var(params={'curve': {'v': [89, 97, 103, 105], 'var': [100, 50, 50, 0]}})
    volt_var = eut.volt_var()
    if volt_var is not None:
        ts.log('DER volt/var:')
        ts.log('  Ena: %s' % (volt_var.get('Ena')))
        ts.log('  ActCrv: %s' % (volt_var.get('ActCrv')))
        ts.log('  NCrv: %s' % (volt_var.get('NCrv')))
        ts.log('  NPt: %s' % (volt_var.get('NPt')))
        ts.log('  WinTms: %s' % (volt_var.get('WinTms')))
        ts.log('  RmpTms: %s' % (volt_var.get('RmpTms')))
        ts.log('  RvrtTms: %s' % (volt_var.get('RvrtTms')))
        curve = volt_var.get('curve')
        if curve is not None:
            ts.log('  curve #%d:' % (curve.get('id')))
            ts.log('    v: %s' % (curve.get('v')))
            ts.log('    var: %s' % (curve.get('var')))
            ts.log('    DeptRef: %s' % (curve.get('DeptRef')))
            ts.log('    RmpTms: %s' % (curve.get('RmpTms')))
            ts.log('    RmpDecTmm: %s' % (curve.get('RmpDecTmm')))
            ts.log('    RmpIncTmm: %s' % (curve.get('RmpIncTmm')))
    else:
        ts.log_warning('DER volt_var not supported')
    ts.log('---')
    curve_num = 1
    eut.volt_var_curve(id=curve_num, params={'v': [80, 97, 103, 105], 'var': [100, 50, 50, 0]})
    curve = eut.volt_var_curve(id=curve_num)
    if curve is not None:
        ts.log('  curve #%d:' % (curve.get('id')))
        ts.log('    v: %s' % (curve.get('v')))
        ts.log('    var: %s' % (curve.get('var')))
        ts.log('    DeptRef: %s' % (curve.get('DeptRef')))
        ts.log('    RmpTms: %s' % (curve.get('RmpTms')))
        ts.log('    RmpDecTmm: %s' % (curve.get('RmpDecTmm')))
        ts.log('    RmpIncTmm: %s' % (curve.get('RmpIncTmm')))
    else:
        ts.log_warning('DER volt_var not supported')
    ts.log('---')
    '''

    volt_var = eut.volt_watt()
    if volt_var is not None:
        ts.log('DER volt/watt:')
        ts.log('  Ena: %s' % (volt_var.get('Ena')))
        ts.log('  ActCrv: %s' % (volt_var.get('ActCrv')))
        ts.log('  NCrv: %s' % (volt_var.get('NCrv')))
        ts.log('  NPt: %s' % (volt_var.get('NPt')))
        ts.log('  WinTms: %s' % (volt_var.get('WinTms')))
        ts.log('  RmpTms: %s' % (volt_var.get('RmpTms')))
        ts.log('  RvrtTms: %s' % (volt_var.get('RvrtTms')))
        curve = volt_var.get('curve')
        if curve is not None:
            ts.log('  curve #%d:' % (curve.get('id')))
            ts.log('    v: %s' % (curve.get('v')))
            ts.log('    w: %s' % (curve.get('w')))
            ts.log('    DeptRef: %s' % (curve.get('DeptRef')))
            ts.log('    RmpTms: %s' % (curve.get('RmpTms')))
            ts.log('    RmpDecTmm: %s' % (curve.get('RmpDecTmm')))
            ts.log('    RmpIncTmm: %s' % (curve.get('RmpIncTmm')))
    else:
        ts.log_warning('DER volt_var not supported')

    status = eut.controls_status()
    if status is not None:
        ts.log('    Is Fixed_W enabled?: %s' % (status.get('Fixed_W')))
        ts.log('    Is Fixed_Var enabled?: %s' % (status.get('Fixed_Var')))
        ts.log('    Is Fixed_PF enabled?: %s' % (status.get('Fixed_PF')))
        ts.log('    Is Volt_Var enabled?: %s' % (status.get('Volt_Var')))
        ts.log('    Is Freq_Watt_Param enabled?: %s' % (status.get('Freq_Watt_Param')))
        ts.log('    Is Freq_Watt_Curve enabled?: %s' % (status.get('Freq_Watt_Curve')))
        ts.log('    Is Dyn_Reactive_Power enabled?: %s' % (status.get('Dyn_Reactive_Power')))
        ts.log('    Is LVRT enabled?: %s' % (status.get('LVRT')))
        ts.log('    Is HVRT enabled?: %s' % (status.get('HVRT')))
        ts.log('    Is Watt_PF enabled?: %s' % (status.get('Watt_PF')))
        ts.log('    Is Volt_Watt enabled?: %s' % (status.get('Volt_Watt')))
        ts.log('    Is Scheduled enabled?: %s' % (status.get('Scheduled')))
        ts.log('    Is LFRT enabled?: %s' % (status.get('LFRT')))
        ts.log('    Is HFRT enabled?: %s' % (status.get('HFRT')))

        ts.log('---')
        status = eut.conn_status()
        ts.log('    Is PV_Connected?: %s' % (status.get('PV_Connected')))
        ts.log('    Is PV_Available?: %s' % (status.get('PV_Available')))
        ts.log('    Is PV_Operating?: %s' % (status.get('PV_Operating')))
        ts.log('    Is PV_Test?: %s' % (status.get('PV_Test')))
        ts.log('    Is Storage_Connected?: %s' % (status.get('Storage_Connected')))
        ts.log('    Is Storage_Available?: %s' % (status.get('Storage_Available')))
        ts.log('    Is Storage_Operating?: %s' % (status.get('Storage_Operating')))
        ts.log('    Is Storage_Test?: %s' % (status.get('Storage_Test')))
        ts.log('    Is EPC_Connected?: %s' % (status.get('EPC_Connected')))
        ts.log('---')

    return script.RESULT_COMPLETE

def run(test_script):

    try:
        global ts
        ts = test_script
        rc = 0
        result = script.RESULT_COMPLETE

        ts.log_debug('')
        ts.log_debug('**************  Starting %s  **************' % (ts.config_name()))
        ts.log_debug('Script: %s %s' % (ts.name, ts.info.version))
        ts.log_active_params()

        result = test_run()

        ts.result(result)
        if result == script.RESULT_FAIL:
            rc = 1

    except Exception, e:
        ts.log_error('Test script exception: %s' % traceback.format_exc())
        rc = 1

    sys.exit(rc)

info = script.ScriptInfo(name=os.path.basename(__file__), run=run, version='1.0.0')


# DER
der.params(info)


info.logo('sunspec.gif')

def script_info():
    
    return info


if __name__ == "__main__":

    # stand alone invocation
    config_file = None
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    params = None

    test_script = script.Script(info=script_info(), config_file=config_file, params=params)

    run(test_script)


