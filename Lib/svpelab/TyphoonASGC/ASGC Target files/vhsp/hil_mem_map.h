/*****************************************************************************************************************************************
**
**  Module Name: hil_mem_map.h
**
**  Description:
**            hil_unit memory map
**
*****************************************************************************************************************************************/

#ifndef HIL_MEM_MAP_H
#define HIL_MEM_MAP_H

// AO (Analog Output) memory space
//#define HIL_OFF_COP_AO_MM                0x2000

/*************** CB address space *****/

// Relative module addresses from hil_unit
// #define HIL_CU_BASEADDR                  0x0
// #define HIL_SG_BASEADDR                  0x400000
// #define HIL_ML_BASEADDR                  0x800000
// #define HIL_IO_BASEADDR                  0xc00000
// #define HIL_LT_BASEADDR                  0x1000000
// #define HIL_SF_BASEADDR                  0x1400000
// #define HIL_CE_BASEADDR                  0x1800000
// #define HIL_HS_BASEADDR                  0x1c00000
// #define HIL_PM_BASEADDR                  0x2000000
// #define HIL_SPC_BASEADDR                 0x8000000

// // CU
// #define HIL_CU_WORKING                   0x1
// #define HIL_CU_REV                       0x10
// #define HIL_CU_PRO_ID                    0x11
// #define HIL_CU_CFG_ID                    0x12
// #define HIL_CU_RELEASE_DATE              0x13
// #define HIL_CU_DEV_ID                    0x16
// #define HIL_CU_SYS_SP_INIT_DONE          0x31
// #define HIL_CU_USER_SP_INIT_DONE         0x32
// #define HIL_CU_SYS_SP_RUNNING            0x35
// #define HIL_CU_USER_SP_RUNNING           0x36
// #define HIL_CU_COMM_SP_RUNNING           0x37
// #define HIL_CU_SYS_SP_CFG                0x50
// #define HIL_CU_USER_SP_CFG               0x51
// #define HIL_CU_COMM_APP_CFG              0x52
// // SG
// #define HIL_OFF_SG_WG                    0x800
// #define HIL_SG_WG                        0x600000
// #define HIL_SG_SAMPLE_STEP               0x400000
// #define HIL_SG_UPDATE                    0x400080
// #define HIL_SG_WAVE_LENGTH               0x400100
// #define HIL_SG_OFFSET                    0x400180
// #define HIL_SG_GAIN                      0x400200
// #define HIL_SG_PERIOD                    0x400280
// #define HIL_SG_WG_UPDATE_EN              0x400300
// #define HIL_SG_SMP_CNT_MODULO            0x400380

// // MS
// #define HIL_OFF_MCH_PAGE_SIZE            0x10000

// // IO
// //#define HIL_IO_COP_MEM                   0xc10000
// //#define HIL_IO_AO_RD_MEM                 0xc80000

// // SF
// #define HIL_SF_BUFF_ADDR                 0x1400000
// #define HIL_SF_BUFF_SIZE_AT              0x1400001
// #define HIL_SF_CH_NUM                    0x1400004
// #define HIL_SF_BUFF_LAST_ADDR            0x1400007
// #define HIL_SF_TRIGGER_ADDR              0x1400008
// #define HIL_SF_BUFF_SIZE_BT              0x1400009
// #define HIL_SF_COP_MEM                   0x1410000

// // SPC
// #define HIL_OFF_SPC_MV                   0x0
// #define HIL_OFF_SPC_TS                   0x100000
// #define HIL_OFF_SPC_CP                   0x200000
// #define HIL_OFF_SPC_CT                   0x240000
// #define HIL_OFF_SPC_DT                   0x280000
// #define HIL_OFF_SPC_SP                   0x2c0000
// #define HIL_OFF_SPC_TV                   0x300000
// #define HIL_OFF_SPC                      0x400000
// #define HIL_OFF_SPC_FSM_SW_CTRL_SRC      0x30
// #define HIL_OFF_SPC_FSM_SW_CTRL_VAL      0x31
// #define HIL_OFF_SPC_CT_SW_CTRL_SRC       0x400
// #define HIL_OFF_SPC_CT_SW_CTRL_VAL       0x480
// #define HIL_OFF_SPC_DT_SW_CTRL_SRC       0x80
// #define HIL_OFF_SPC_DT_SW_CTRL_VAL       0x100

#endif /** HIL_MEM_MAP_H */