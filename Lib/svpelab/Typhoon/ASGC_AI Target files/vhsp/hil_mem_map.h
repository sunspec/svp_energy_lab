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
#define HIL_OFF_SPC_AO_MM                0x0
#define HIL_OFF_MS_AO_MM                 0x2000
#define HIL_OFF_SG_AO_MM                 0x2100
#define HIL_OFF_DS_AO_MM                 0x2200
#define HIL_OFF_COP_AO_MM                0x2300
#define HIL_OFF_AI_AO_MM                 0x2400

// DS (Digital Signal) memory space
#define HIL_OFF_IO_DS_RD_MS              0x100
#define HIL_OFF_IO_DS_RD_DI              0x200
#define HIL_OFF_IO_DS_RD_SW              0x300
#define HIL_OFF_IO_DS_RD_SPC_CB          0x400
#define HIL_OFF_IO_DS_RD_SPC_SPC_CMPL    0x406
#define HIL_OFF_IO_DS_RD_SPC_FSM_STF     0x40c
#define HIL_OFF_IO_DS_RD_PWM             0x600

/*************** CB address space *****/

// Relative module addresses from hil_unit
#define HIL_CU_BASEADDR                  0x0
#define HIL_SG_BASEADDR                  0x400000
#define HIL_ML_BASEADDR                  0x800000
#define HIL_IO_BASEADDR                  0xc00000
#define HIL_LT_BASEADDR                  0x1000000
#define HIL_SF_BASEADDR                  0x1400000
#define HIL_CE_BASEADDR                  0x1800000
#define HIL_HS_BASEADDR                  0x1c00000
#define HIL_PM_BASEADDR                  0x2000000
#define HIL_SPC_BASEADDR                 0x8000000

// CU
#define HIL_CU_WORKING                   0x1
#define HIL_CU_REV                       0x10
#define HIL_CU_PRO_ID                    0x11
#define HIL_CU_CFG_ID                    0x12
#define HIL_CU_RELEASE_DATE              0x13
#define HIL_CU_DEV_ID                    0x16
#define HIL_CU_SYS_SP_INIT_DONE          0x31
#define HIL_CU_USER_SP_INIT_DONE         0x32

// SG
#define HIL_OFF_SG_WG                    0x800
#define HIL_SG_WG                        0x600000
#define HIL_SG_SAMPLE_STEP               0x400000
#define HIL_SG_UPDATE                    0x400010
#define HIL_SG_WAVE_LENGTH               0x400020
#define HIL_SG_OFFSET                    0x400030
#define HIL_SG_GAIN                      0x400040
#define HIL_SG_PERIOD                    0x400050
#define HIL_SG_WG_UPDATE_EN              0x400060
#define HIL_SG_SMP_CNT_MODULO            0x400070

// MS
#define HIL_OFF_MCH_PAGE_SIZE            0x80000

// IO
#define HIL_IO_COP_MEM                   0xc04600
#define HIL_IO_DS_RD                     0xf80000
#define HIL_IO_SW_DS                     0xf00200
#define HIL_IO_AO_RD_MEM                 0xc80000

// SF
#define HIL_SF_BUFF_ADDR                 0x1400000
#define HIL_SF_BUFF_SIZE_AT              0x1400001
#define HIL_SF_CH_NUM                    0x1400004
#define HIL_SF_BUFF_LAST_ADDR            0x1400007
#define HIL_SF_TRIGGER_ADDR              0x1400008
#define HIL_SF_BUFF_SIZE_BT              0x1400009
#define HIL_SF_COP_MEM                   0x1400100

// PWM
#define HIL_PM_EN                        0x2000000
#define HIL_PM_REF_SIG                   0x2000010
#define HIL_PM_MAX_CNT                   0x2000020
#define HIL_PM_D_TIME                    0x2000030
#define HIL_PM_EN_UPDATE                 0x2000040
#define HIL_PM_MASK                      0x2000050
#define HIL_PM_RESET                     0x2000060
#define HIL_PM_CARR_PHASE_OFF            0x2000070
#define HIL_PM_CARR_SIG_DIR              0x2000080
#define HIL_PM_USE_DI                    0x2000090
#define HIL_PM_DI_ADDR                   0x20000a0

// SPC
#define HIL_OFF_SPC_MV                   0x0
#define HIL_OFF_SPC_TS                   0x100000
#define HIL_OFF_SPC_CP                   0x200000
#define HIL_OFF_SPC_CT                   0x240000
#define HIL_OFF_SPC_DT                   0x280000
#define HIL_OFF_SPC_SP                   0x2c0000
#define HIL_OFF_SPC_TV                   0x300000
#define HIL_OFF_SPC                      0x400000
#define HIL_OFF_SPC_CT_SW_CTRL_SRC       0x80
#define HIL_OFF_SPC_CT_SW_CTRL_VAL       0x90
#define HIL_OFF_SPC_DT_SW_CTRL_SRC       0x80
#define HIL_OFF_SPC_DT_SW_CTRL_VAL       0x100

#endif /** HIL_MEM_MAP_H */