// generated using template: cop_main.template---------------------------------------------
/******************************************************************************************
**
**  Module Name: cop_main.c
**  NOTE: Automatically generated file. DO NOT MODIFY!
**  Description:
**            Main file
**
******************************************************************************************/
// generated using template: arm/custom_include.template-----------------------------------

// x86 libraries:
#include "../include/sp_functions_dev0.h"

// H files from Advanced C Function components
//#include "example_dll.h"

// Header files from additional sources (Advanced C Function)
// ----------------------------------------------------------------------------------------
// generated using template: VirtualHIL/custom_defines.template----------------------------

typedef unsigned char X_UnInt8;
typedef char X_Int8;
typedef signed short X_Int16;
typedef unsigned short X_UnInt16;
typedef int X_Int32;
typedef unsigned int X_UnInt32;
typedef unsigned int uint;
typedef double real;

// ----------------------------------------------------------------------------------------
// generated using template: common_consts.template----------------------------------------200,100000};

// arithmetic constants
#define C_SQRT_2                    1.4142135623730950488016887242097f
#define C_SQRT_3                    1.7320508075688772935274463415059f
#define C_PI                        3.1415926535897932384626433832795f
#define C_E                         2.7182818284590452353602874713527f
#define C_2PI                       6.283185307179586476925286766559f

//@cmp.def.start
//component defines
//@cmp.def.end

//-----------------------------------------------------------------------------------------
// generated using template: common_variables.template-------------------------------------
// true global variables

//@cmp.var.start
// variables
float _vrms3_vinst_va1__out;
float _vrms2_vinst_va1__out;
float _irms3_iinst_ia1__out;
float _irms2_iinst_ia1__out;
float _vrms1_vinst_va1__out;
float _irms1_iinst_ia1__out;
float _irms1_rms_calc_fast__var_eff_s;
unsigned int _irms1_rms_calc_fast__period;
X_UnInt8 _irms1_rms_calc_fast__var_zc;
float _irms1_rms_calc_fast__var_filt_old;
float _vrms1_rms_calc_fast__var_eff_s;
unsigned int _vrms1_rms_calc_fast__period;
X_UnInt8 _vrms1_rms_calc_fast__var_zc;
float _vrms1_rms_calc_fast__var_filt_old;
float _irms2_rms_calc_fast__var_eff_s;
unsigned int _irms2_rms_calc_fast__period;
X_UnInt8 _irms2_rms_calc_fast__var_zc;
float _irms2_rms_calc_fast__var_filt_old;
float _irms3_rms_calc_fast__var_eff_s;
unsigned int _irms3_rms_calc_fast__period;
X_UnInt8 _irms3_rms_calc_fast__var_zc;
float _irms3_rms_calc_fast__var_filt_old;
float _vrms2_rms_calc_fast__var_eff_s;
unsigned int _vrms2_rms_calc_fast__period;
X_UnInt8 _vrms2_rms_calc_fast__var_zc;
float _vrms2_rms_calc_fast__var_filt_old;
float _vrms3_rms_calc_fast__var_eff_s;
unsigned int _vrms3_rms_calc_fast__period;
X_UnInt8 _vrms3_rms_calc_fast__var_zc;
float _vrms3_rms_calc_fast__var_filt_old;
float _irms1_rms_calc_slow__var_rms;
float _vrms1_rms_calc_slow__var_rms;
float _irms2_rms_calc_slow__var_rms;
float _irms3_rms_calc_slow__var_rms;
float _vrms2_rms_calc_slow__var_rms;
float _vrms3_rms_calc_slow__var_rms;
//@cmp.var.end

//@cmp.svar.start
// state variables
float _irms1_rms_calc_fast__v_sq_sum_state;
unsigned int _irms1_rms_calc_fast__pc_cnt_1_state;
float _irms1_rms_calc_fast__var_filt;
float _vrms1_rms_calc_fast__v_sq_sum_state;
unsigned int _vrms1_rms_calc_fast__pc_cnt_1_state;
float _vrms1_rms_calc_fast__var_filt;
float _irms2_rms_calc_fast__v_sq_sum_state;
unsigned int _irms2_rms_calc_fast__pc_cnt_1_state;
float _irms2_rms_calc_fast__var_filt;
float _irms3_rms_calc_fast__v_sq_sum_state;
unsigned int _irms3_rms_calc_fast__pc_cnt_1_state;
float _irms3_rms_calc_fast__var_filt;
float _vrms2_rms_calc_fast__v_sq_sum_state;
unsigned int _vrms2_rms_calc_fast__pc_cnt_1_state;
float _vrms2_rms_calc_fast__var_filt;
float _vrms3_rms_calc_fast__v_sq_sum_state;
unsigned int _vrms3_rms_calc_fast__pc_cnt_1_state;
float _vrms3_rms_calc_fast__var_filt;
float _vrms3_rt1_output__out =  0.0;

float _vrms3_rt2_output__out =  0.0;

float _vrms2_rt1_output__out =  0.0;

float _vrms2_rt2_output__out =  0.0;

float _irms3_rt2_output__out =  0.0;

float _irms3_rt1_output__out =  0.0;

float _irms2_rt2_output__out =  0.0;

float _irms2_rt1_output__out =  0.0;

float _vrms1_rt1_output__out =  0.0;

float _vrms1_rt2_output__out =  0.0;

float _irms1_rt2_output__out =  0.0;

float _irms1_rt1_output__out =  0.0;

//@cmp.svar.end
// generated using template: virtual_hil/custom_functions.template---------------------------------
void ReInit_sys_sp_cpu_dev0() {

#if DEBUG_MODE
    printf("\n\rReInitTimer");
#endif

    //@cmp.init.block.start






    _irms1_rms_calc_fast__var_filt = 0.0f;
    _irms1_rms_calc_fast__v_sq_sum_state = 0.0f;
    _irms1_rms_calc_fast__pc_cnt_1_state = 0;






    _vrms1_rms_calc_fast__var_filt = 0.0f;
    _vrms1_rms_calc_fast__v_sq_sum_state = 0.0f;
    _vrms1_rms_calc_fast__pc_cnt_1_state = 0;




    _irms2_rms_calc_fast__var_filt = 0.0f;
    _irms2_rms_calc_fast__v_sq_sum_state = 0.0f;
    _irms2_rms_calc_fast__pc_cnt_1_state = 0;





    _irms3_rms_calc_fast__var_filt = 0.0f;
    _irms3_rms_calc_fast__v_sq_sum_state = 0.0f;
    _irms3_rms_calc_fast__pc_cnt_1_state = 0;






    _vrms2_rms_calc_fast__var_filt = 0.0f;
    _vrms2_rms_calc_fast__v_sq_sum_state = 0.0f;
    _vrms2_rms_calc_fast__pc_cnt_1_state = 0;





    _vrms3_rms_calc_fast__var_filt = 0.0f;
    _vrms3_rms_calc_fast__v_sq_sum_state = 0.0f;
    _vrms3_rms_calc_fast__pc_cnt_1_state = 0;




    _vrms3_rt1_output__out =  0.0;


    _vrms3_rt2_output__out =  0.0;


    _vrms2_rt1_output__out =  0.0;


    _vrms2_rt2_output__out =  0.0;


    _irms3_rt2_output__out =  0.0;


    _irms3_rt1_output__out =  0.0;


    _irms2_rt2_output__out =  0.0;


    _irms2_rt1_output__out =  0.0;


    _vrms1_rt1_output__out =  0.0;


    _vrms1_rt2_output__out =  0.0;


    _irms1_rt2_output__out =  0.0;


    _irms1_rt1_output__out =  0.0;




    HIL_OutAO(0x2001, 0.0f);


    HIL_OutAO(0x2004, 0.0f);




    HIL_OutAO(0x2003, 0.0f);



    HIL_OutAO(0x2000, 0.0f);


    HIL_OutAO(0x2005, 0.0f);



    HIL_OutAO(0x2002, 0.0f);


    //@cmp.init.block.end
}
// generated using template: common_timer_counter_handler.template-------------------------

/*****************************************************************************************/
/**
* This function is the handler which performs processing for the timer counter.
* It is called from an interrupt context such that the amount of processing
* performed should be minimized.  It is called when the timer counter expires
* if interrupts are enabled.
*
*
* @param    None
*
* @return   None
*
* @note     None
*
*****************************************************************************************/

void TimerCounterHandler_0_sys_sp_cpu_dev0() {

#if DEBUG_MODE
    printf("\n\rTimerCounterHandler_0");
#endif

    //////////////////////////////////////////////////////////////////////////
    // Output block
    //////////////////////////////////////////////////////////////////////////
    //@cmp.out.block.start
    // Generated from the component: Vrms3.Vinst.Va1
    _vrms3_vinst_va1__out = HIL_InAO(0xa);

    // Generated from the component: Vrms2.Vinst.Va1
    _vrms2_vinst_va1__out = HIL_InAO(0x9);

    // Generated from the component: Irms3.Iinst.Ia1
    _irms3_iinst_ia1__out = HIL_InAO(0x114);

    // Generated from the component: Irms2.Iinst.Ia1
    _irms2_iinst_ia1__out = HIL_InAO(0x113);

    // Generated from the component: Vrms1.Vinst.Va1
    _vrms1_vinst_va1__out = HIL_InAO(0x8);

    // Generated from the component: Irms1.Iinst.Ia1
    _irms1_iinst_ia1__out = HIL_InAO(0x112);

    // Generated from the component: Irms1.rms_calc_fast
    _irms1_rms_calc_fast__v_sq_sum_state = _irms1_rms_calc_fast__v_sq_sum_state + _irms1_iinst_ia1__out * _irms1_iinst_ia1__out;
    _irms1_rms_calc_fast__var_filt_old = _irms1_rms_calc_fast__var_filt;
    _irms1_rms_calc_fast__var_filt = (_irms1_rms_calc_fast__var_filt_old * 0.909 + _irms1_iinst_ia1__out * 0.0909);
    if((_irms1_rms_calc_fast__var_filt >= 0.0f) && (_irms1_rms_calc_fast__var_filt_old < 0.0f)) {
        _irms1_rms_calc_fast__var_zc = 1;
    }
    else {
        _irms1_rms_calc_fast__var_zc = 0;
    }
    //square sum and period update on signal zero cross
    if ((_irms1_rms_calc_fast__var_zc == 1) || (5000 == _irms1_rms_calc_fast__pc_cnt_1_state)) {
        _irms1_rms_calc_fast__var_eff_s = _irms1_rms_calc_fast__v_sq_sum_state;
        _irms1_rms_calc_fast__period = (float)_irms1_rms_calc_fast__pc_cnt_1_state;
        _irms1_rms_calc_fast__v_sq_sum_state = 0.0f;
    }

    // Generated from the component: Irms1.t1


    // Generated from the component: Irms1.sys1

    // Generated from the component: Irms1.rt1.Input
    _irms1_rt1_output__out = _irms1_rms_calc_fast__var_eff_s;
    // Generated from the component: Irms1.rt2.Input
    _irms1_rt2_output__out = _irms1_rms_calc_fast__period;
    // Generated from the component: Vrms1.sys1

    // Generated from the component: Vrms1.rms_calc_fast
    _vrms1_rms_calc_fast__v_sq_sum_state = _vrms1_rms_calc_fast__v_sq_sum_state + _vrms1_vinst_va1__out * _vrms1_vinst_va1__out;
    _vrms1_rms_calc_fast__var_filt_old = _vrms1_rms_calc_fast__var_filt;
    _vrms1_rms_calc_fast__var_filt = (_vrms1_rms_calc_fast__var_filt_old * 0.909 + _vrms1_vinst_va1__out * 0.0909);
    if((_vrms1_rms_calc_fast__var_filt >= 0.0f) && (_vrms1_rms_calc_fast__var_filt_old < 0.0f)) {
        _vrms1_rms_calc_fast__var_zc = 1;
    }
    else {
        _vrms1_rms_calc_fast__var_zc = 0;
    }
    //square sum and period update on signal zero cross
    if ((_vrms1_rms_calc_fast__var_zc == 1) || (5000 == _vrms1_rms_calc_fast__pc_cnt_1_state)) {
        _vrms1_rms_calc_fast__var_eff_s = _vrms1_rms_calc_fast__v_sq_sum_state;
        _vrms1_rms_calc_fast__period = (float)_vrms1_rms_calc_fast__pc_cnt_1_state;
        _vrms1_rms_calc_fast__v_sq_sum_state = 0.0f;
    }

    // Generated from the component: Vrms1.t1


    // Generated from the component: Vrms1.rt2.Input
    _vrms1_rt2_output__out = _vrms1_rms_calc_fast__period;
    // Generated from the component: Vrms1.rt1.Input
    _vrms1_rt1_output__out = _vrms1_rms_calc_fast__var_eff_s;
    // Generated from the component: Irms2.rms_calc_fast
    _irms2_rms_calc_fast__v_sq_sum_state = _irms2_rms_calc_fast__v_sq_sum_state + _irms2_iinst_ia1__out * _irms2_iinst_ia1__out;
    _irms2_rms_calc_fast__var_filt_old = _irms2_rms_calc_fast__var_filt;
    _irms2_rms_calc_fast__var_filt = (_irms2_rms_calc_fast__var_filt_old * 0.909 + _irms2_iinst_ia1__out * 0.0909);
    if((_irms2_rms_calc_fast__var_filt >= 0.0f) && (_irms2_rms_calc_fast__var_filt_old < 0.0f)) {
        _irms2_rms_calc_fast__var_zc = 1;
    }
    else {
        _irms2_rms_calc_fast__var_zc = 0;
    }
    //square sum and period update on signal zero cross
    if ((_irms2_rms_calc_fast__var_zc == 1) || (5000 == _irms2_rms_calc_fast__pc_cnt_1_state)) {
        _irms2_rms_calc_fast__var_eff_s = _irms2_rms_calc_fast__v_sq_sum_state;
        _irms2_rms_calc_fast__period = (float)_irms2_rms_calc_fast__pc_cnt_1_state;
        _irms2_rms_calc_fast__v_sq_sum_state = 0.0f;
    }

    // Generated from the component: Irms2.t1


    // Generated from the component: Irms2.sys1

    // Generated from the component: Irms2.rt1.Input
    _irms2_rt1_output__out = _irms2_rms_calc_fast__var_eff_s;
    // Generated from the component: Irms2.rt2.Input
    _irms2_rt2_output__out = _irms2_rms_calc_fast__period;
    // Generated from the component: Irms3.rms_calc_fast
    _irms3_rms_calc_fast__v_sq_sum_state = _irms3_rms_calc_fast__v_sq_sum_state + _irms3_iinst_ia1__out * _irms3_iinst_ia1__out;
    _irms3_rms_calc_fast__var_filt_old = _irms3_rms_calc_fast__var_filt;
    _irms3_rms_calc_fast__var_filt = (_irms3_rms_calc_fast__var_filt_old * 0.909 + _irms3_iinst_ia1__out * 0.0909);
    if((_irms3_rms_calc_fast__var_filt >= 0.0f) && (_irms3_rms_calc_fast__var_filt_old < 0.0f)) {
        _irms3_rms_calc_fast__var_zc = 1;
    }
    else {
        _irms3_rms_calc_fast__var_zc = 0;
    }
    //square sum and period update on signal zero cross
    if ((_irms3_rms_calc_fast__var_zc == 1) || (5000 == _irms3_rms_calc_fast__pc_cnt_1_state)) {
        _irms3_rms_calc_fast__var_eff_s = _irms3_rms_calc_fast__v_sq_sum_state;
        _irms3_rms_calc_fast__period = (float)_irms3_rms_calc_fast__pc_cnt_1_state;
        _irms3_rms_calc_fast__v_sq_sum_state = 0.0f;
    }

    // Generated from the component: Irms3.t1


    // Generated from the component: Irms3.sys1

    // Generated from the component: Irms3.rt1.Input
    _irms3_rt1_output__out = _irms3_rms_calc_fast__var_eff_s;
    // Generated from the component: Irms3.rt2.Input
    _irms3_rt2_output__out = _irms3_rms_calc_fast__period;
    // Generated from the component: Vrms2.sys1

    // Generated from the component: Vrms2.rms_calc_fast
    _vrms2_rms_calc_fast__v_sq_sum_state = _vrms2_rms_calc_fast__v_sq_sum_state + _vrms2_vinst_va1__out * _vrms2_vinst_va1__out;
    _vrms2_rms_calc_fast__var_filt_old = _vrms2_rms_calc_fast__var_filt;
    _vrms2_rms_calc_fast__var_filt = (_vrms2_rms_calc_fast__var_filt_old * 0.909 + _vrms2_vinst_va1__out * 0.0909);
    if((_vrms2_rms_calc_fast__var_filt >= 0.0f) && (_vrms2_rms_calc_fast__var_filt_old < 0.0f)) {
        _vrms2_rms_calc_fast__var_zc = 1;
    }
    else {
        _vrms2_rms_calc_fast__var_zc = 0;
    }
    //square sum and period update on signal zero cross
    if ((_vrms2_rms_calc_fast__var_zc == 1) || (5000 == _vrms2_rms_calc_fast__pc_cnt_1_state)) {
        _vrms2_rms_calc_fast__var_eff_s = _vrms2_rms_calc_fast__v_sq_sum_state;
        _vrms2_rms_calc_fast__period = (float)_vrms2_rms_calc_fast__pc_cnt_1_state;
        _vrms2_rms_calc_fast__v_sq_sum_state = 0.0f;
    }

    // Generated from the component: Vrms2.t1


    // Generated from the component: Vrms2.rt2.Input
    _vrms2_rt2_output__out = _vrms2_rms_calc_fast__period;
    // Generated from the component: Vrms2.rt1.Input
    _vrms2_rt1_output__out = _vrms2_rms_calc_fast__var_eff_s;
    // Generated from the component: Vrms3.sys1

    // Generated from the component: Vrms3.rms_calc_fast
    _vrms3_rms_calc_fast__v_sq_sum_state = _vrms3_rms_calc_fast__v_sq_sum_state + _vrms3_vinst_va1__out * _vrms3_vinst_va1__out;
    _vrms3_rms_calc_fast__var_filt_old = _vrms3_rms_calc_fast__var_filt;
    _vrms3_rms_calc_fast__var_filt = (_vrms3_rms_calc_fast__var_filt_old * 0.909 + _vrms3_vinst_va1__out * 0.0909);
    if((_vrms3_rms_calc_fast__var_filt >= 0.0f) && (_vrms3_rms_calc_fast__var_filt_old < 0.0f)) {
        _vrms3_rms_calc_fast__var_zc = 1;
    }
    else {
        _vrms3_rms_calc_fast__var_zc = 0;
    }
    //square sum and period update on signal zero cross
    if ((_vrms3_rms_calc_fast__var_zc == 1) || (5000 == _vrms3_rms_calc_fast__pc_cnt_1_state)) {
        _vrms3_rms_calc_fast__var_eff_s = _vrms3_rms_calc_fast__v_sq_sum_state;
        _vrms3_rms_calc_fast__period = (float)_vrms3_rms_calc_fast__pc_cnt_1_state;
        _vrms3_rms_calc_fast__v_sq_sum_state = 0.0f;
    }

    // Generated from the component: Vrms3.t1


    // Generated from the component: Vrms3.rt2.Input
    _vrms3_rt2_output__out = _vrms3_rms_calc_fast__period;
    // Generated from the component: Vrms3.rt1.Input
    _vrms3_rt1_output__out = _vrms3_rms_calc_fast__var_eff_s;
    //@cmp.out.block.end


    //////////////////////////////////////////////////////////////////////////
    // Update block
    //////////////////////////////////////////////////////////////////////////
    //@cmp.update.block.start
    // Generated from the component: Irms1.rms_calc_fast
    if ((_irms1_rms_calc_fast__var_zc == 1) || (5000 == _irms1_rms_calc_fast__pc_cnt_1_state)) {
        _irms1_rms_calc_fast__pc_cnt_1_state = 0;
    }
    _irms1_rms_calc_fast__pc_cnt_1_state ++;

    // Generated from the component: Vrms1.rms_calc_fast
    if ((_vrms1_rms_calc_fast__var_zc == 1) || (5000 == _vrms1_rms_calc_fast__pc_cnt_1_state)) {
        _vrms1_rms_calc_fast__pc_cnt_1_state = 0;
    }
    _vrms1_rms_calc_fast__pc_cnt_1_state ++;

    // Generated from the component: Irms2.rms_calc_fast
    if ((_irms2_rms_calc_fast__var_zc == 1) || (5000 == _irms2_rms_calc_fast__pc_cnt_1_state)) {
        _irms2_rms_calc_fast__pc_cnt_1_state = 0;
    }
    _irms2_rms_calc_fast__pc_cnt_1_state ++;

    // Generated from the component: Irms3.rms_calc_fast
    if ((_irms3_rms_calc_fast__var_zc == 1) || (5000 == _irms3_rms_calc_fast__pc_cnt_1_state)) {
        _irms3_rms_calc_fast__pc_cnt_1_state = 0;
    }
    _irms3_rms_calc_fast__pc_cnt_1_state ++;

    // Generated from the component: Vrms2.rms_calc_fast
    if ((_vrms2_rms_calc_fast__var_zc == 1) || (5000 == _vrms2_rms_calc_fast__pc_cnt_1_state)) {
        _vrms2_rms_calc_fast__pc_cnt_1_state = 0;
    }
    _vrms2_rms_calc_fast__pc_cnt_1_state ++;

    // Generated from the component: Vrms3.rms_calc_fast
    if ((_vrms3_rms_calc_fast__var_zc == 1) || (5000 == _vrms3_rms_calc_fast__pc_cnt_1_state)) {
        _vrms3_rms_calc_fast__pc_cnt_1_state = 0;
    }
    _vrms3_rms_calc_fast__pc_cnt_1_state ++;

    //@cmp.update.block.end
}
void TimerCounterHandler_1_sys_sp_cpu_dev0() {

#if DEBUG_MODE
    printf("\n\rTimerCounterHandler_1");
#endif

    //////////////////////////////////////////////////////////////////////////
    // Output block
    //////////////////////////////////////////////////////////////////////////
    //@cmp.out.block.start
    // Generated from the component: Vrms3.rt1.Output

    // Generated from the component: Vrms3.rt2.Output

    // Generated from the component: Vrms2.rt1.Output

    // Generated from the component: Vrms2.rt2.Output

    // Generated from the component: Irms3.rt2.Output

    // Generated from the component: Irms3.rt1.Output

    // Generated from the component: Irms2.rt2.Output

    // Generated from the component: Irms2.rt1.Output

    // Generated from the component: Vrms1.rt1.Output

    // Generated from the component: Vrms1.rt2.Output

    // Generated from the component: Irms1.rt2.Output

    // Generated from the component: Irms1.rt1.Output

    // Generated from the component: Irms1.rms_calc_slow
    if(_irms1_rt2_output__out > 0.0f) {
        _irms1_rms_calc_slow__var_rms = sqrtf(_irms1_rt1_output__out / _irms1_rt2_output__out);
    }
    else {
        _irms1_rms_calc_slow__var_rms = 0.0f;
    }

    // Generated from the component: Irms1.sys2

    // Generated from the component: Irms1.rms
    HIL_OutAO(0x2001, _irms1_rms_calc_slow__var_rms);
    // Generated from the component: Vrms1.rms_calc_slow
    if(_vrms1_rt2_output__out > 0.0f) {
        _vrms1_rms_calc_slow__var_rms = sqrtf(_vrms1_rt1_output__out / _vrms1_rt2_output__out);
    }
    else {
        _vrms1_rms_calc_slow__var_rms = 0.0f;
    }

    // Generated from the component: Vrms1.rms
    HIL_OutAO(0x2004, _vrms1_rms_calc_slow__var_rms);
    // Generated from the component: Vrms1.sys2

    // Generated from the component: Irms2.rms_calc_slow
    if(_irms2_rt2_output__out > 0.0f) {
        _irms2_rms_calc_slow__var_rms = sqrtf(_irms2_rt1_output__out / _irms2_rt2_output__out);
    }
    else {
        _irms2_rms_calc_slow__var_rms = 0.0f;
    }

    // Generated from the component: Irms2.sys2

    // Generated from the component: Irms2.rms
    HIL_OutAO(0x2003, _irms2_rms_calc_slow__var_rms);
    // Generated from the component: Irms3.rms_calc_slow
    if(_irms3_rt2_output__out > 0.0f) {
        _irms3_rms_calc_slow__var_rms = sqrtf(_irms3_rt1_output__out / _irms3_rt2_output__out);
    }
    else {
        _irms3_rms_calc_slow__var_rms = 0.0f;
    }

    // Generated from the component: Irms3.sys2

    // Generated from the component: Irms3.rms
    HIL_OutAO(0x2000, _irms3_rms_calc_slow__var_rms);
    // Generated from the component: Vrms2.rms_calc_slow
    if(_vrms2_rt2_output__out > 0.0f) {
        _vrms2_rms_calc_slow__var_rms = sqrtf(_vrms2_rt1_output__out / _vrms2_rt2_output__out);
    }
    else {
        _vrms2_rms_calc_slow__var_rms = 0.0f;
    }

    // Generated from the component: Vrms2.rms
    HIL_OutAO(0x2005, _vrms2_rms_calc_slow__var_rms);
    // Generated from the component: Vrms2.sys2

    // Generated from the component: Vrms3.rms_calc_slow
    if(_vrms3_rt2_output__out > 0.0f) {
        _vrms3_rms_calc_slow__var_rms = sqrtf(_vrms3_rt1_output__out / _vrms3_rt2_output__out);
    }
    else {
        _vrms3_rms_calc_slow__var_rms = 0.0f;
    }

    // Generated from the component: Vrms3.rms
    HIL_OutAO(0x2002, _vrms3_rms_calc_slow__var_rms);
    // Generated from the component: Vrms3.sys2

    //@cmp.out.block.end


    //////////////////////////////////////////////////////////////////////////
    // Update block
    //////////////////////////////////////////////////////////////////////////
    //@cmp.update.block.start
    //@cmp.update.block.end
}
// ----------------------------------------------------------------------------------------  //-----------------------------------------------------------------------------------------