Ts=40e-6;
dec=1;
Tend=170;
Tstart=10;
Nsig=10;
Nbss=500;
MODE =1;
VNOM = 1.0;
FNOM = 60.0;
Srated = 5e3;       % Inverter nominal 3-phase power (VA) 
Pnom = 5e3;         % Inverter nominal 3-phase active power (W)


%Input scaling and offset for new taraz boards
VOLT_INPUT_SCALE_PHA = 100 ;
VOLT_INPUT_SCALE_PHB = 100 ;
VOLT_INPUT_SCALE_PHC = 100 ;
VOLT_INPUT_OFFSET_PHA = 0 ; %0.3
VOLT_INPUT_OFFSET_PHB = 0 ;
VOLT_INPUT_OFFSET_PHC = 0 ; %0.1

%Input scaling and offset
% VOLT_INPUT_SCALE_PHA = 25 ; 
% VOLT_INPUT_SCALE_PHB = 25 ;
% VOLT_INPUT_SCALE_PHC = 25 ;
% VOLT_INPUT_OFFSET_PHA = 0 ; %0.3
% VOLT_INPUT_OFFSET_PHB = 0 ;
% VOLT_INPUT_OFFSET_PHC = 0 ; %0.1

% Analog inputs are in the range of 16 V on the model though we are using
% 10 V in the HIL box

%Scaling from new CTs
CURRENT_INPUT_SCALE_PHA = 30 ; % (V/A) Canmet Scale and calibration value 
CURRENT_INPUT_SCALE_PHB = 30 ;
CURRENT_INPUT_SCALE_PHC = 30 ;

% % AC port
% % Latest from Mar 2022 considering 60 mV on the HIL box
% CURRENT_INPUT_SCALE_PHA = (60/10)*0.9981 ; % (V/A) Canmet Scale and calibration value 
% CURRENT_INPUT_SCALE_PHB = (60/10)*0.9971 ;
% CURRENT_INPUT_SCALE_PHC = (60/10)*1.0002 ;
% % 50 A --- > 50 mV ---- > 10*50/60 = 8.3333 --- > 50 /8.333 = 6.0002 
% % 27 A --- > 27 mV --- > 10*27/60 = 4.5

% AC port
% Gain_grid_sim_corr = 0.9212;
% CURRENT_INPUT_SCALE_PHA = (1/0.3)*0.9971*Gain_grid_sim_corr ; % (V/A) Canmet Scale and calibration value 
% CURRENT_INPUT_SCALE_PHB = (1/0.3)*1.0002*Gain_grid_sim_corr ;
% CURRENT_INPUT_SCALE_PHC = (1/0.3)*0.9981*Gain_grid_sim_corr ;


% old formula with 30 mV for current 
% CURRENT_INPUT_SCALE_PHA = (1/0.03)*0.9971 ; % (V/A) Canmet Scale and calibration value 
% CURRENT_INPUT_SCALE_PHB = (1/0.03)*1.0002 ;
% CURRENT_INPUT_SCALE_PHC = (1/0.03)*0.9981 ;

% AC Switch
% CURRENT_INPUT_SCALE_PHA = (10/30)*(500/50)*10 ; % (V/A) Canmet Scale and calibration value 
% CURRENT_INPUT_SCALE_PHB = (10/30)*(500/50)*10 ;
% CURRENT_INPUT_SCALE_PHC = (10/30)*(500/50)*10 ;

% CURRENT_INPUT_SCALE_PHA = 29.4474 ; % Considering the Zimmer measurements and for AC switch Use this Dec 2021
% CURRENT_INPUT_SCALE_PHB = 30.2392 ;  % avg = 29.97 % for fronius A & C 29.97 & B 31
% CURRENT_INPUT_SCALE_PHC = 30.2313 ;

%With Fronius@ACswitch on Jan 2022
% iii = 29.97;
% CURRENT_INPUT_SCALE_PHA = iii ; 
% CURRENT_INPUT_SCALE_PHB = 31 ;  
% CURRENT_INPUT_SCALE_PHC = iii ;

CURRENT_INPUT_OFFSET_PHA = 0 ;
CURRENT_INPUT_OFFSET_PHB = 0 ;
CURRENT_INPUT_OFFSET_PHC = 0 ;  %0.3

WAV_ENABLE = 1;
RMS_ENABLE = 0;

% Output scaling considering rms input
VOLT_OUTPUT_SCALE_PHA = 5.6;    
VOLT_OUTPUT_SCALE_PHB = 5.6;
VOLT_OUTPUT_SCALE_PHC = 5.6;
% VOLT_OUTPUT_SCALE_PHA = 120.0*sqrt(2);
% VOLT_OUTPUT_SCALE_PHB = 120.0*sqrt(2);
% VOLT_OUTPUT_SCALE_PHC = 120.0*sqrt(2);

% SVP commands
PHASE = [0.0 -120.0 120.0]
VOLTAGE = [1.0 1.0 1.0]
FREQUENCY = 60.0

% WaveformGenerator parameters
ENABLE_PHA = 1;
ENABLE_PHB = 1;
ENABLE_PHC = 1;

ROCOF_ENABLE = 0;
ROCOF_VALUE = 3;
ROCOF_INIT = 60;

ROCOM_ENABLE = 1;
ROCOM_VALUE = 13.8;
ROCOM_INIT = 1;
ROCOM_START_TIME = 0; 
ROCOM_END_TIME = 100;

FREQUENCY_MAX_LIMIT = 66.0
FREQUENCY_MIN_LIMIT = 56.0
VOLTAGE_MAX_LIMIT = 1.1
VOLTAGE_MIN_LIMIT = 0.0

% VRT parameters
VRT_START = 1;
VRT_PHA_ENABLE = 0;
VRT_PHB_ENABLE = 0;
VRT_PHC_ENABLE = 0;
VRT_CONDITION = [0 1 0 1 0 1 0 1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1]+1;
VRT_START_TIMING = [0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1];
VRT_END_TIMING = [0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 1.1 1.2 1.3 1.4 1.5 1.6 1.7 1.8 1.9 2 2.1];
VRT_VALUES = [1.2 0.94 0 0.5 0.7 0.88 0.94 0.88 0.94 1.1 1.2 0.94 0 0.5 0.7 0.88 0.94 0.88 0.94 1.1];

% FRT parameters
FRT_CONDITION = [1 1 1 0 ];
FRT_START_TIMING = [0.1 0.2 0.3 0.4];
FRT_END_TIMING = [0.2 0.3 0.4 0.5];
FRT_VALUES = [59.0 56.0 55.0 33.0];

% PCRT parameters
PCRT_CONDITION =    [ 0    1     0     2     0     3      0      4      0      4      0   ];
PCRT_START_TIMING = [ 0.0 30.0  30.32 60.32 60.64 90.64  90.96 120.96 175.96 205.96 260.96];
PCRT_END_TIMING   = [30.0 30.32 60.32 60.64 90.64 90.96 120.96 175.96 205.96 260.96 290.96];
PCRT_VALUES       = [ 0.0 60.0   0.0  60.0   0.0  60.0    0.0   20.0    0.0  340.0    0.0 ];
PHNOM             = [0 -120 120];
