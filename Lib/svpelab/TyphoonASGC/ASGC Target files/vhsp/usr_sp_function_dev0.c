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
// generated using template: common_consts.template----------------------------------------200};

// arithmetic constants
#define C_SQRT_2                    1.4142135623730950488016887242097f
#define C_SQRT_3                    1.7320508075688772935274463415059f
#define C_PI                        3.1415926535897932384626433832795f
#define C_E                         2.7182818284590452353602874713527f
#define C_2PI                       6.283185307179586476925286766559f

//@cmp.def.start
//component defines
#define SQRT_2OVER3 0.8164965809277260327324280249019f
#define SQRT3_OVER_2 0.8660254037844386467637231707529f
//@cmp.def.end

//-----------------------------------------------------------------------------------------
// generated using template: common_variables.template-------------------------------------
// true global variables

//@cmp.var.start
// variables
float _ig3_ia1__out;
float _ig2_ia1__out;
float _ig1_ia1__out;
float _v_l3_va1__out;
float _v_l1_va1__out;
float _v_l2_va1__out;
float _pq_power_meter1__Pdc;
float _pq_power_meter1__Qdc;
float _pq_power_meter1__Pac;
float _pq_power_meter1__Qac;
float _pq_power_meter1__apparent;
float _pq_power_meter1__k_factor;
float _pq_power_meter1__v_alpha;
float _pq_power_meter1__v_beta;
float _pq_power_meter1__i_alpha;
float _pq_power_meter1__i_beta;
float _pq_power_meter1__P;
float _pq_power_meter1__Q;
float _pq_power_meter1__filter_1_output;
float _pq_power_meter1__filter_1_outputQ;
//@cmp.var.end

//@cmp.svar.start
// state variables
float _pq_power_meter1__filter_1_output_k_minus_1;
float _pq_power_meter1__filter_1_input_k_minus_1;
float _pq_power_meter1__filter_1_output_k_minus_1Q;
float _pq_power_meter1__filter_1_input_k_minus_1Q;         //@cmp.svar.end
// generated using template: virtual_hil/custom_functions.template---------------------------------
void ReInit_user_sp_cpu_dev0() {

#if DEBUG_MODE
    printf("\n\rReInitTimer");
#endif

    //@cmp.init.block.start






    _pq_power_meter1__filter_1_output_k_minus_1 = 0.0;
    _pq_power_meter1__filter_1_input_k_minus_1 = 0.0;
    _pq_power_meter1__filter_1_output_k_minus_1Q = 0.0;
    _pq_power_meter1__filter_1_input_k_minus_1Q = 0.0;
    HIL_OutAO(0x200b, 0.0f);

    HIL_OutAO(0x2007, 0.0f);

    HIL_OutAO(0x2009, 0.0f);

    HIL_OutAO(0x200a, 0.0f);

    HIL_OutAO(0x2008, 0.0f);

    HIL_OutAO(0x2006, 0.0f);

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

void TimerCounterHandler_0_user_sp_cpu_dev0() {

#if DEBUG_MODE
    printf("\n\rTimerCounterHandler_0");
#endif

    //////////////////////////////////////////////////////////////////////////
    // Output block
    //////////////////////////////////////////////////////////////////////////
    //@cmp.out.block.start
    // Generated from the component: Ig3.Ia1
    _ig3_ia1__out = HIL_InAO(0x110);

    // Generated from the component: Ig2.Ia1
    _ig2_ia1__out = HIL_InAO(0x10f);

    // Generated from the component: Ig1.Ia1
    _ig1_ia1__out = HIL_InAO(0x10e);

    // Generated from the component: V_L3.Va1
    _v_l3_va1__out = HIL_InAO(0x4);

    // Generated from the component: V_L1.Va1
    _v_l1_va1__out = HIL_InAO(0x2);

    // Generated from the component: V_L2.Va1
    _v_l2_va1__out = HIL_InAO(0x3);

    // Generated from the component: PQ Power Meter1
    _pq_power_meter1__v_alpha = SQRT_2OVER3 * ( _v_l1_va1__out - 0.5f * _v_l2_va1__out - 0.5f * _v_l3_va1__out);
    _pq_power_meter1__v_beta = SQRT_2OVER3 * (SQRT3_OVER_2 * _v_l2_va1__out - SQRT3_OVER_2 * _v_l3_va1__out);
    _pq_power_meter1__i_alpha = SQRT_2OVER3 * ( _ig1_ia1__out - 0.5f * _ig2_ia1__out - 0.5f * _ig3_ia1__out);
    _pq_power_meter1__i_beta = SQRT_2OVER3 * (SQRT3_OVER_2 * _ig2_ia1__out - SQRT3_OVER_2 * _ig3_ia1__out);

    _pq_power_meter1__P = _pq_power_meter1__v_alpha * _pq_power_meter1__i_alpha + _pq_power_meter1__v_beta * _pq_power_meter1__i_beta;
    _pq_power_meter1__Q = _pq_power_meter1__v_beta * _pq_power_meter1__i_alpha - _pq_power_meter1__v_alpha * _pq_power_meter1__i_beta;

    _pq_power_meter1__filter_1_output = 0.009336780874162044 * (_pq_power_meter1__P + _pq_power_meter1__filter_1_input_k_minus_1) - (-0.9813264382516759) * _pq_power_meter1__filter_1_output_k_minus_1;
    _pq_power_meter1__filter_1_outputQ = 0.009336780874162044 * (_pq_power_meter1__Q + _pq_power_meter1__filter_1_input_k_minus_1Q) - (-0.9813264382516759) * _pq_power_meter1__filter_1_output_k_minus_1Q;

    _pq_power_meter1__filter_1_input_k_minus_1 = _pq_power_meter1__P;
    _pq_power_meter1__filter_1_output_k_minus_1 = _pq_power_meter1__filter_1_output;
    _pq_power_meter1__filter_1_input_k_minus_1Q = _pq_power_meter1__Q;;
    _pq_power_meter1__filter_1_output_k_minus_1Q = _pq_power_meter1__filter_1_outputQ;

    _pq_power_meter1__Pdc = _pq_power_meter1__filter_1_output;
    _pq_power_meter1__Qdc = _pq_power_meter1__filter_1_outputQ;

    _pq_power_meter1__apparent = sqrtf(powf(_pq_power_meter1__Pdc, 2) + powf(_pq_power_meter1__Qdc, 2));

    if (_pq_power_meter1__apparent > 0)
        _pq_power_meter1__k_factor = _pq_power_meter1__Pdc / _pq_power_meter1__apparent;
    else
        _pq_power_meter1__k_factor = 0;

    _pq_power_meter1__Pac = _pq_power_meter1__P - _pq_power_meter1__Pdc;
    _pq_power_meter1__Qac = _pq_power_meter1__Q - _pq_power_meter1__Qdc;

    // Generated from the component: Pdc
    HIL_OutAO(0x200b, _pq_power_meter1__Pdc);
    // Generated from the component: Qdc
    HIL_OutAO(0x2007, _pq_power_meter1__Qdc);
    // Generated from the component: Pac
    HIL_OutAO(0x2009, _pq_power_meter1__Pac);
    // Generated from the component: Qac
    HIL_OutAO(0x200a, _pq_power_meter1__Qac);
    // Generated from the component: S
    HIL_OutAO(0x2008, _pq_power_meter1__apparent);
    // Generated from the component: k
    HIL_OutAO(0x2006, _pq_power_meter1__k_factor);
    //@cmp.out.block.end


    //////////////////////////////////////////////////////////////////////////
    // Update block
    //////////////////////////////////////////////////////////////////////////
    //@cmp.update.block.start
    //@cmp.update.block.end
}
// ----------------------------------------------------------------------------------------  //-----------------------------------------------------------------------------------------