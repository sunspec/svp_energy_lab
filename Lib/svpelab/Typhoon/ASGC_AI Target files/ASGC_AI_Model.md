Model cfe2510f658911e783d8989096b1c7c2 

REM *****************************************: 
REM * Common entries:
REM *****************************************:

REM Setting the simulation time step... 
rtds_write 0x00000000 0x96

REM Machine block inputs... 
rtds_write 0x00000003 0x0

REM LUT solver inputs... 
rtds_write 0x01000000 0x1
rtds_write 0x01000080 0x107
rtds_write 0x010000C0 0.000000e+000
rtds_write 0x01000100 1.000000e+000
rtds_write 0x01000180 498.0

REM *****************************************: 
REM * SPC1 entries:
REM *****************************************:
 
REM SPC1 Topology Selector (TS) initialization... 
rtds_file_write 0x08180000 SPC1_red_table.txt
rtds_write 0x08100004 0x3
rtds_write 0x08100009 0x0
rtds_write 0x08100020 0x1
rtds_write 0x08100021 0x0
rtds_write 0x08100023 0x0
rtds_write 0x08100024 0x0
rtds_write 0x08100025 0x0
rtds_write 0x08100026 0x0
rtds_write 0x08100027 0x0
rtds_file_write 0x08140000 trivial_imem.txt 
rtds_file_write 0x08142000 trivial_lut.txt 
rtds_write 0x08100030 0x1
rtds_write 0x08100031 0x0
rtds_write 0x08100033 0x0
rtds_write 0x08100034 0x0
rtds_write 0x08100035 0x0
rtds_write 0x08100036 0x0
rtds_write 0x08100037 0x0
rtds_file_write 0x08148000 trivial_imem.txt 
rtds_file_write 0x0814A000 trivial_lut.txt 
rtds_write 0x08100040 0x1
rtds_write 0x08100041 0x0
rtds_write 0x08100043 0x0
rtds_write 0x08100044 0x0
rtds_write 0x08100045 0x0
rtds_write 0x08100046 0x0
rtds_write 0x08100047 0x0
rtds_file_write 0x08150000 trivial_imem.txt 
rtds_file_write 0x08152000 trivial_lut.txt 

REM SPC1 Variable Delay initialization... 

REM SPC1 Matrix multiplier initialization... 
rtds_file_write 0x08000000 SPC1_Com_Word.txt
rtds_file_write 0x08020000 SPC1_Com_LUT.txt
rtds_file_write 0x08080000 SPC1_MAC1_Val.txt
rtds_file_write 0x08082000 SPC1_MAC1_Col.txt
rtds_file_write 0x08084000 SPC1_MAC2_Val.txt
rtds_file_write 0x08086000 SPC1_MAC2_Col.txt
rtds_file_write 0x08088000 SPC1_MAC3_Val.txt
rtds_file_write 0x0808A000 SPC1_MAC3_Col.txt
rtds_file_write 0x0808C000 SPC1_MAC4_Val.txt
rtds_file_write 0x0808E000 SPC1_MAC4_Col.txt

REM SPC1 Contactors initialization... 
rtds_write 0x08240000 0x0 
rtds_write 0x08240010 0x0 
rtds_write 0x08240020 0x0 
rtds_write 0x08240030 0x0 
rtds_write 0x08240040 0x0 
rtds_write 0x08240050 0x0 
rtds_write 0x08240060 0x0 
rtds_write 0x08240070 0x0 
rtds_write 0x08240080 0x0 
rtds_write 0x08240001 0x0 
rtds_write 0x08240011 0x0 
rtds_write 0x08240021 0x0 
rtds_write 0x08240031 0x0 
rtds_write 0x08240041 0x0 
rtds_write 0x08240051 0x0 
rtds_write 0x08240061 0x0 
rtds_write 0x08240071 0x0 
rtds_write 0x08240081 0x0 

REM SPC1 GDS compensation settings... 
rtds_write 0x080C0000 0x1
rtds_write 0x080C0001 0x9
rtds_write 0x080C0004 0x3CA3D70A
rtds_write 0x080C0005 0x3D710000
rtds_write 0x08100000 0x32

REM SPC1 FSM digital input pin assignments... 

REM SPC1 Comparators initialization... 

REM SPC1 DTSM initialization... 

REM *****************************************: 
REM * SPC2 entries:
REM *****************************************:
 
REM SPC2 Topology Selector (TS) initialization... 
rtds_file_write 0x08580000 SPC2_red_table.txt
rtds_write 0x08500004 0x0
rtds_write 0x08500009 0x0
rtds_write 0x08500020 0x5
rtds_write 0x08500021 0xF
rtds_write 0x08500023 0x1
rtds_write 0x08500024 0x1
rtds_write 0x08500025 0x0
rtds_write 0x08500026 0xC
rtds_write 0x08500027 0x0
rtds_file_write 0x08540000 igbt_npc2_3l_leg_imem.txt 
rtds_file_write 0x08542000 igbt_npc2_3l_leg_lut.txt 
rtds_write 0x08500030 0x5
rtds_write 0x08500031 0xF
rtds_write 0x08500033 0x1
rtds_write 0x08500034 0x1
rtds_write 0x08500035 0x0
rtds_write 0x08500036 0xC
rtds_write 0x08500037 0x0
rtds_file_write 0x08548000 igbt_npc2_3l_leg_imem.txt 
rtds_file_write 0x0854A000 igbt_npc2_3l_leg_lut.txt 
rtds_write 0x08500040 0x5
rtds_write 0x08500041 0xF
rtds_write 0x08500043 0x1
rtds_write 0x08500044 0x1
rtds_write 0x08500045 0x0
rtds_write 0x08500046 0xC
rtds_write 0x08500047 0x0
rtds_file_write 0x08550000 igbt_npc2_3l_leg_imem.txt 
rtds_file_write 0x08552000 igbt_npc2_3l_leg_lut.txt 

REM SPC2 Variable Delay initialization... 
rtds_write 0x08500001 0x0

REM SPC2 Matrix multiplier initialization... 
rtds_file_write 0x08400000 SPC2_Com_Word.txt
rtds_file_write 0x08420000 SPC2_Com_LUT.txt
rtds_file_write 0x08480000 SPC2_MAC1_Val.txt
rtds_file_write 0x08482000 SPC2_MAC1_Col.txt
rtds_file_write 0x08484000 SPC2_MAC2_Val.txt
rtds_file_write 0x08486000 SPC2_MAC2_Col.txt
rtds_file_write 0x08488000 SPC2_MAC3_Val.txt
rtds_file_write 0x0848A000 SPC2_MAC3_Col.txt
rtds_file_write 0x0848C000 SPC2_MAC4_Val.txt
rtds_file_write 0x0848E000 SPC2_MAC4_Col.txt

REM SPC2 Contactors initialization... 

REM SPC2 GDS compensation settings... 
rtds_write 0x084C0000 0x1
rtds_write 0x084C0001 0x7
rtds_write 0x084C0004 0x3CA3D70A
rtds_write 0x084C0005 0x3D710000
rtds_write 0x08500000 0x32

REM SPC2 FSM digital input pin assignments... 
rtds_write 0x08500028 0x0 
rtds_write 0x08500029 0x0 
rtds_write 0x0850002A 0x0 
rtds_write 0x0850002B 0x1 
rtds_write 0x0850002C 0x6 
rtds_write 0x0850002D 0x7 
rtds_write 0x08500022 0x0 
rtds_write 0x08500038 0x0 
rtds_write 0x08500039 0x0 
rtds_write 0x0850003A 0x2 
rtds_write 0x0850003B 0x3 
rtds_write 0x0850003C 0x8 
rtds_write 0x0850003D 0x9 
rtds_write 0x08500032 0x0 
rtds_write 0x08500048 0x0 
rtds_write 0x08500049 0x0 
rtds_write 0x0850004A 0x4 
rtds_write 0x0850004B 0x5 
rtds_write 0x0850004C 0xa 
rtds_write 0x0850004D 0xb 
rtds_write 0x08500042 0x0 

REM SPC2 Comparators initialization... 

REM SPC2 DTSM initialization... 

REM *****************************************: 
REM * SPC3 entries:
REM *****************************************:
 
REM SPC3 Topology Selector (TS) initialization... 
rtds_file_write 0x08980000 SPC3_red_table.txt
rtds_write 0x08900004 0x0
rtds_write 0x08900009 0x0
rtds_write 0x08900020 0x0
rtds_write 0x08900021 0x0
rtds_write 0x08900023 0x0
rtds_write 0x08900024 0x0
rtds_write 0x08900025 0x0
rtds_write 0x08900026 0xC
rtds_write 0x08900027 0x0
rtds_file_write 0x08940000  
rtds_file_write 0x08942000  
rtds_write 0x08900030 0x0
rtds_write 0x08900031 0x0
rtds_write 0x08900033 0x0
rtds_write 0x08900034 0x0
rtds_write 0x08900035 0x0
rtds_write 0x08900036 0xC
rtds_write 0x08900037 0x0
rtds_file_write 0x08948000  
rtds_file_write 0x0894A000  
rtds_write 0x08900040 0x0
rtds_write 0x08900041 0x0
rtds_write 0x08900043 0x0
rtds_write 0x08900044 0x0
rtds_write 0x08900045 0x0
rtds_write 0x08900046 0xC
rtds_write 0x08900047 0x0
rtds_file_write 0x08950000  
rtds_file_write 0x08952000  

REM SPC3 Variable Delay initialization... 

REM SPC3 Matrix multiplier initialization... 
rtds_file_write 0x08800000 SPC3_Com_Word.txt
rtds_file_write 0x08820000 SPC3_Com_LUT.txt
rtds_file_write 0x08880000 SPC3_MAC1_Val.txt
rtds_file_write 0x08882000 SPC3_MAC1_Col.txt
rtds_file_write 0x08884000 SPC3_MAC2_Val.txt
rtds_file_write 0x08886000 SPC3_MAC2_Col.txt
rtds_file_write 0x08888000 SPC3_MAC3_Val.txt
rtds_file_write 0x0888A000 SPC3_MAC3_Col.txt
rtds_file_write 0x0888C000 SPC3_MAC4_Val.txt
rtds_file_write 0x0888E000 SPC3_MAC4_Col.txt

REM SPC3 Contactors initialization... 
rtds_write 0x08A40003 0x0 
rtds_write 0x08A40013 0x0 
rtds_write 0x08A40023 0x0 
rtds_write 0x08A40033 0x0 
rtds_write 0x08A40043 0x0 
rtds_write 0x08A40053 0x0 
rtds_write 0x08A40063 0x0 
rtds_write 0x08A40073 0x0 

REM SPC3 GDS compensation settings... 
rtds_write 0x088C0000 0x0
rtds_write 0x088C0001 0x0
rtds_write 0x088C0004 0x0
rtds_write 0x088C0005 0x0

REM SPC3 FSM digital input pin assignments... 

REM SPC3 Comparators initialization... 

REM SPC3 DTSM initialization... 

REM *****************************************: 
REM * SPC4 entries:
REM *****************************************:
 
REM SPC4 Topology Selector (TS) initialization... 
rtds_file_write 0x08D80000 SPC4_red_table.txt
rtds_write 0x08D00004 0x0
rtds_write 0x08D00009 0x0
rtds_write 0x08D00020 0x0
rtds_write 0x08D00021 0x0
rtds_write 0x08D00023 0x0
rtds_write 0x08D00024 0x0
rtds_write 0x08D00025 0x0
rtds_write 0x08D00026 0xC
rtds_write 0x08D00027 0x0
rtds_file_write 0x08D40000  
rtds_file_write 0x08D42000  
rtds_write 0x08D00030 0x0
rtds_write 0x08D00031 0x0
rtds_write 0x08D00033 0x0
rtds_write 0x08D00034 0x0
rtds_write 0x08D00035 0x0
rtds_write 0x08D00036 0xC
rtds_write 0x08D00037 0x0
rtds_file_write 0x08D48000  
rtds_file_write 0x08D4A000  
rtds_write 0x08D00040 0x0
rtds_write 0x08D00041 0x0
rtds_write 0x08D00043 0x0
rtds_write 0x08D00044 0x0
rtds_write 0x08D00045 0x0
rtds_write 0x08D00046 0xC
rtds_write 0x08D00047 0x0
rtds_file_write 0x08D50000  
rtds_file_write 0x08D52000  

REM SPC4 Variable Delay initialization... 

REM SPC4 Matrix multiplier initialization... 
rtds_file_write 0x08C00000 SPC4_Com_Word.txt
rtds_file_write 0x08C20000 SPC4_Com_LUT.txt
rtds_file_write 0x08C80000 SPC4_MAC1_Val.txt
rtds_file_write 0x08C82000 SPC4_MAC1_Col.txt
rtds_file_write 0x08C84000 SPC4_MAC2_Val.txt
rtds_file_write 0x08C86000 SPC4_MAC2_Col.txt
rtds_file_write 0x08C88000 SPC4_MAC3_Val.txt
rtds_file_write 0x08C8A000 SPC4_MAC3_Col.txt
rtds_file_write 0x08C8C000 SPC4_MAC4_Val.txt
rtds_file_write 0x08C8E000 SPC4_MAC4_Col.txt

REM SPC4 Contactors initialization... 
rtds_write 0x08E40003 0x0 
rtds_write 0x08E40013 0x0 
rtds_write 0x08E40023 0x0 
rtds_write 0x08E40033 0x0 
rtds_write 0x08E40043 0x0 
rtds_write 0x08E40053 0x0 
rtds_write 0x08E40063 0x0 
rtds_write 0x08E40073 0x0 

REM SPC4 GDS compensation settings... 
rtds_write 0x08CC0000 0x0
rtds_write 0x08CC0001 0x0
rtds_write 0x08CC0004 0x0
rtds_write 0x08CC0005 0x0

REM SPC4 FSM digital input pin assignments... 

REM SPC4 Comparators initialization... 

REM SPC4 DTSM initialization... 

REM DI active level settings... 
rtds_write 0x00F00000 0x0 

REM HSSL configuration files... 
rtds_file_write 0x01C80000 hssl_tx_config.txt
rtds_file_write 0x01D00000 hssl_rx_config.txt
*****************************************:


REM SP data configuration...
*****************************************:


REM CoProcessors uBlaze_1, uBlaze_2 and uBlaze_3 configuration
glbl_write 0x40800000 0x7
glbl_file_write 0x50000000 cop_1_app_imem.bin
glbl_file_write 0x50100000 cop_2_app_imem.bin
glbl_write 0x40800000 0x4


REM Setting the capture sample step...
rtds_write 0x00000027 0x00000096


REM post SP Init calculation...
rtds_write 0x00000040 0x002FFFFF
rtds_write 0x00000041 0x000001C1
rtds_write 0x00000005 0x00000003
glbl_write 0x41200048 0x00000001
glbl_write 0x42200048 0x00000001
glbl_write 0x43200048 0x00000000
rtds_write 0x00000042 0x047868BF
rtds_write 0x0000000A 0x00000001