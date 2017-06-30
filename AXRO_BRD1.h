//-------------- General Board Control pins --------------------

// Slave Select Pins ARD-6,7,8,9
#define SSA3 9  // Slave select E-SSA3 J3-7
#define SSA2 8  // Slave Select E-SSA2 J3-6
#define SSA1 7  // Slave Select E-SSA1 J3-5
#define SSA0 6  // Slave Select E-SSA0 J3-4

// Multiplexer Select Pins ARD-10,11,12,13
#define MUXA3 13  // MUX select E-MUXA3 J3-14
#define MUXA2 12  // MUX Select E-MUXA2 J3-13
#define MUXA1 11  // MUX Select E-MUXA1 J3-12
#define MUXA0 10  // MUX Select E-MUXA0 J3-11

// Multiplxer 0/1 Enable/Disable ARD 2
#define MUXA4 2  // MUX select E-MUXA3 J3-15

// Board Select pins ARD-4,5
#define BRD_A0  4   // Board enable 0
#define BRD_A1  5   // Board Enable 1

// System Enable /SYSEN ARD-3
#define SYSENbar 3 // System enable line, active low

// /DACCLR DAQ CLEAR - Bring low to clear an entire daq
#define DACCLRbar 1

// Board select Constants
#define BOARD_0 0
#define BOARD_1 1
#define BOARD_2 2
#define BOARD_3 3

// Function select Constants
#define DAQ0 0  // Y12, TP-33, /SS0
#define DAQ1 1  // Y1 /SS1
#define DAQ2 2  // Y2, /SS2
#define DAQ3 3  // Y3, /SS3
#define DAQ4 4  // Y4, /SS4
#define DAQ5 5  // Y5, /SS5
#define DAQ6 6  // Y6, /SS6
#define DAQ7 7  // Y7, /SS7

#define SS8  8  // Just /SS8, Y9

// AD5372 Base Groups (0-3)
#define BaseGroup0 (0b11001000)
#define BaseGroup1 (0b11010000)
#define BaseGroup2 (0b11011000)
#define BaseGroup3 (0b11100000)

#define DAQ_WRITE_DATA    (0b11000000)
#define DAQ_WRITE_OFFSET  (0b10000000)
#define DAQ_WRITE_GAIN    (0b01000000)
#define DAQ_SPEC_FUNCTION (0b00000000)

#define WRITE_DATA 0
#define WRITE_OFFSET 1
#define WRITE_GAIN 2
#define WRITE_SPEC_FUNCTION 3

#define Vmax 15.25
#define Vmin -15.25

//-------------------------------------
#define Y0   10   // Y0 of the 74HC154 is attached to nothing.

#define LDAC 20    // LDAC Y10, TP-51
#define RESET 30
#define LTC1859 40
#define CSTRT 41    // /CSTRT for LTC1859
#define TEMP 50    // ADT7310, /ss9, Y9, TP-40

//------------ADT7310 Temperature Sensor Function------------------

// Some constants used in the setup for the ADT7310, see datasheet.
#define ADT7310_1FAULT (0b00)
#define ADT7310_2FAULT (0b01)
#define ADT7310_3FAULT (0b10)
#define ADT7310_4FAULT (0b11)

#define ADT7310_CT_POLARITY_LOW (0<<2)
#define ADT7310_CT_POLARITY_HIGH (1<<2)
#define ADT7310_INT_POLARITY_LOW (0<<3)
#define ADT7310_INT_POLARITY_HIGH (1<<3)

#define ADT7310_INTCT_INTERRUPT (0<<4)
#define ADT7310_INTCT_COMPARATOR (1<<4)

#define ADT7310_CONTINUOUS (0b00<<6)
#define ADT7310_ONESHOT (0b01<<6)
#define ADT7310_1SPS (0b10<<6)
#define ADT7310_SHUTDOWN (0b11<<6)

#define ADT7310_13BIT (0 << 7)
#define ADT7310_16BIT (1 << 7)


// Prototypes
void SelectTemperatureSensor();

void DeSelectSlave();


