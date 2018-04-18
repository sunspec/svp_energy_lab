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
// ----------------------------------------------------------------------------------------
// generated using template: VirtualHIL/custom_defines.template----------------------------

typedef unsigned char X_UnInt8;
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
float _ig3__out;
float _ig2__out;
float _ig1__out;
float _v_l3__out;
float _v_l1__out;
float _v_l2__out;
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
    HIL_OutAO(0x2311, 0.0f);

    HIL_OutAO(0x230c, 0.0f);

    HIL_OutAO(0x230f, 0.0f);

    HIL_OutAO(0x2310, 0.0f);

    HIL_OutAO(0x230e, 0.0f);

    HIL_OutAO(0x230d, 0.0f);

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
    // Generated from the component: Ig3
    _ig3__out = HIL_InAO(0x110);

    // Generated from the component: Ig2
    _ig2__out = HIL_InAO(0x10f);

    // Generated from the component: Ig1
    _ig1__out = HIL_InAO(0x10e);

    // Generated from the component: V_L3
    _v_l3__out = HIL_InAO(0xe);

    // Generated from the component: V_L1
    _v_l1__out = HIL_InAO(0xc);

    // Generated from the component: V_L2
    _v_l2__out = HIL_InAO(0xd);

    // Generated from the component: PQ Power Meter1
    _pq_power_meter1__v_alpha = SQRT_2OVER3 * ( _v_l1__out - 0.5f * _v_l2__out - 0.5f * _v_l3__out);
    _pq_power_meter1__v_beta = SQRT_2OVER3 * (SQRT3_OVER_2 * _v_l2__out - SQRT3_OVER_2 * _v_l3__out);
    _pq_power_meter1__i_alpha = SQRT_2OVER3 * ( _ig1__out - 0.5f * _ig2__out - 0.5f * _ig3__out);
    _pq_power_meter1__i_beta = SQRT_2OVER3 * (SQRT3_OVER_2 * _ig2__out - SQRT3_OVER_2 * _ig3__out);

    _pq_power_meter1__P = _pq_power_meter1__v_alpha * _pq_power_meter1__i_alpha + _pq_power_meter1__v_beta * _pq_power_meter1__i_beta;
    _pq_power_meter1__Q = _pq_power_meter1__v_beta * _pq_power_meter1__i_alpha - _pq_power_meter1__v_alpha * _pq_power_meter1__i_beta;

    _pq_power_meter1__filter_1_output = 0.00933678087416 * (_pq_power_meter1__P + _pq_power_meter1__filter_1_input_k_minus_1) - (-0.981326438252) * _pq_power_meter1__filter_1_output_k_minus_1;
    _pq_power_meter1__filter_1_outputQ = 0.00933678087416 * (_pq_power_meter1__Q + _pq_power_meter1__filter_1_input_k_minus_1Q) - (-0.981326438252) * _pq_power_meter1__filter_1_output_k_minus_1Q;

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
    HIL_OutAO(0x2311, _pq_power_meter1__Pdc);
    // Generated from the component: Qdc
    HIL_OutAO(0x230c, _pq_power_meter1__Qdc);
    // Generated from the component: Pac
    HIL_OutAO(0x230f, _pq_power_meter1__Pac);
    // Generated from the component: Qac
    HIL_OutAO(0x2310, _pq_power_meter1__Qac);
    // Generated from the component: S
    HIL_OutAO(0x230e, _pq_power_meter1__apparent);
    // Generated from the component: k
    HIL_OutAO(0x230d, _pq_power_meter1__k_factor);
    //@cmp.out.block.end


    //////////////////////////////////////////////////////////////////////////
    // Update block
    //////////////////////////////////////////////////////////////////////////
    //@cmp.update.block.start
    //@cmp.update.block.end
}
// ----------------------------------------------------------------------------------------  //-----------------------------------------------------------------------------------------