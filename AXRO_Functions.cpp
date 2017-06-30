
#include "Arduino.h"

//------------------------------------------------------------------------
//
//   SystemEnable - Sets the /SYSEN line LOW
//                      (ARD Pin 3, TP102)
//
//------------------------------------------------------------------------
//
void SystemEnable()
{
    digitalWrite(SYSENbar, LOW);
} // End SystemEnable
void SysEn()
{
    digitalWrite(SYSENbar, LOW);
} // End SystemEnable


//------------------------------------------------------------------------
//
//   SystemDisable - Sets the /SYSEN line HIGH
//                      (ARD Pin 3, TP102)
//
//------------------------------------------------------------------------
//
void SystemDisable()
{
     digitalWrite(SYSENbar, HIGH);
} // End SystemDisable


//------------------------ General Board Control ----------------------
//
//   Board_Select - Given the input, set the Board Select Pins (BRD_A0
//                  and BRD_A1) to the appropriate values
//                    ( TP-??)
//
//----------------------------------------------------------------------
//
void Board_Select(int board)
{
   switch (board)
    {
      // First disable the system for a clean change
      SystemDisable();
            
      case 0:
            digitalWrite(BRD_A1, LOW);
            digitalWrite(BRD_A0, LOW);
            break;
            
      case 1:
            digitalWrite(BRD_A1, LOW);
            digitalWrite(BRD_A0, HIGH);
            break;
            
      case 2:
            digitalWrite(BRD_A1, HIGH);
            digitalWrite(BRD_A0, LOW);
            break;
            
      case 3:
            digitalWrite(BRD_A1, HIGH);
            digitalWrite(BRD_A0, HIGH);
            break;
      default:
         break;
           
    } // END SWITCH
    
} // End Board_Select

//------------------------------------------------------------------------
//
//   DACCLR_High - Disables the clearing of the DAQ's
//                      (ARD Pin TX-3, TP-101)
//
//------------------------------------------------------------------------
//
void DACCLR_High()
{
    digitalWrite(DACCLRbar, HIGH);
    // /DACCLR is not gated by SYSEN and takes place immediately
} // End DACCLR_High

//------------------------------------------------------------------------
//
//   Clear_DAQ - Causes the clearing of the DAQ's
//                      (ARD Pin TX-3, TP-101)
//
//------------------------------------------------------------------------
//
void Clear_DAQ()
{
    digitalWrite(DACCLRbar, LOW);
} // End DACCLR_High

//------------------------------------------------------------------------
//
//   SelectFunction - Sets SSA3-SSA0 to select the required function:
//                    ADT7310
//                    LTC1859
//                    AD53??
//                              This pulls 74HC154 line /SS9 (Pin 10) LOW
//                                ( Y9, Pin 10, TP-40)
//
//------------------------------------------------------------------------
//
void SelectFunction(int function)
{
    // First disable the system for a clean change
    SystemDisable();
    
    switch (function)
    {
        // ADT7310 Temperature Sensor stuff
            
        // AD5372 DAQ stuff
        case 0:                       // DAQ0, /SS0, Y12, TP-33
            digitalWrite(SSA3, HIGH);
            digitalWrite(SSA2, HIGH);
            digitalWrite(SSA1, LOW);
            digitalWrite(SSA0, LOW);
            break;
        case 1:                       // DAQ1, /SS1, J2-11, Y1,
            digitalWrite(SSA3, LOW);
            digitalWrite(SSA2, LOW);
            digitalWrite(SSA1, LOW);
            digitalWrite(SSA0, HIGH);
            break;
        case 2:                       // DAQ2, /SS2, Y2, TP
            digitalWrite(SSA3, LOW);
            digitalWrite(SSA2, LOW);
            digitalWrite(SSA1, HIGH);
            digitalWrite(SSA0, LOW);
            break;
        case 3:                       // DAQ3, /SS3, Y3, TP-
            digitalWrite(SSA3, LOW);
            digitalWrite(SSA2, LOW);
            digitalWrite(SSA1, HIGH);
            digitalWrite(SSA0, HIGH);
            break;
        case 4:                       // DAQ4, /SS4, Y4, TP-
            digitalWrite(SSA3, LOW);
            digitalWrite(SSA2, HIGH);
            digitalWrite(SSA1, LOW);
            digitalWrite(SSA0, LOW);
            break;
        case 5:                       // DAQ5, /SS5, Y4, TP-
            digitalWrite(SSA3, LOW);
            digitalWrite(SSA2, HIGH);
            digitalWrite(SSA1, LOW);
            digitalWrite(SSA0, HIGH);
            break;
        case 6:                       // DAQ6, /SS6, Y4, TP-
            digitalWrite(SSA3, LOW);
            digitalWrite(SSA2, HIGH);
            digitalWrite(SSA1, HIGH);
            digitalWrite(SSA0, LOW);
            break;
        case 7:                       // DAQ7, /SS7, Y4, TP-
            digitalWrite(SSA3, LOW);
            digitalWrite(SSA2, HIGH);
            digitalWrite(SSA1, HIGH);
            digitalWrite(SSA0, HIGH);
            break;

        case 8:                       //  /RD on LTC1859/SS8, Y9, TP-
            digitalWrite(SSA3, HIGH);
            digitalWrite(SSA2, LOW);
            digitalWrite(SSA1, LOW);
            digitalWrite(SSA0, LOW);
            break;

            
        case Y0:                       // Y0 - NOTHING
            digitalWrite(SSA3, LOW);
            digitalWrite(SSA2, LOW);
            digitalWrite(SSA1, LOW);
            digitalWrite(SSA0, LOW);
            break;
            
        case LDAC:                       // /LDAC, Y10, TP-51
            digitalWrite(SSA3, HIGH);
            digitalWrite(SSA2, LOW);
            digitalWrite(SSA1, HIGH);
            digitalWrite(SSA0, LOW);
            break;
            
        case RESET:                       // RESET, Y15, TP-36
            digitalWrite(SSA3, HIGH);
            digitalWrite(SSA2, HIGH);
            digitalWrite(SSA1, HIGH);
            digitalWrite(SSA0, HIGH);
            break;
            
        // LTC1859 A-to-D stuff
        case LTC1859:                       // LTC1859, /SS8 Y8
            digitalWrite(SSA3, HIGH);
            digitalWrite(SSA2, LOW);
            digitalWrite(SSA1, LOW);
            digitalWrite(SSA0, LOW);
            break;

        case CSTRT:                       // LTC1859, /CSTRT Y11
            digitalWrite(SSA3, HIGH);
            digitalWrite(SSA2, LOW);
            digitalWrite(SSA1, HIGH);
            digitalWrite(SSA0, HIGH);
            break;
        
        case TEMP:                       // ADT7310 Temp Sensor, /SS9, Y9, T
            digitalWrite(SSA3, HIGH);
            digitalWrite(SSA2, LOW);
            digitalWrite(SSA1, LOW);
            digitalWrite(SSA0, HIGH);
            break;
           
        default:
            break;
            

            
    }
    // Now Enable the system to cause the change to take place
    // and delay for 1 ms
    // If selecting Y0 (null output) then don't enable system.
    if(function!=Y0)
    {
        SystemEnable(); 
        delayMicroseconds(50);
    }
    
} // End SelectFunction


//------------------------------------------------------------------------
//
//  Build_Group_Byte - Given the DAQ line number (0 through 31)
//                     build the Group and Line byte which is sent to the 
//                     AD5372  E.G. byte1 = 0b11001000 is for group 1, DAQ 
//                     line zero.
//
//                     There are 4 groups (0->3) per DAQ; 
//                               8 lines per group (0 -> 8)
//
//                     First find the group of 8 in which the line resides
//                     Then OR in the line selector 0 through 7
//
//------------------------------------------------------------------------
//
byte Build_Group_Byte(int line_num)
{
  byte group_byte = 0;

  byte line;

  // First find out which group it belongs in
  if ( (line_num >= 0) && (line_num <= 7))
    { group_byte = BaseGroup0;}
  
  if ( (line_num >= 8) && (line_num <= 15))
    { group_byte = BaseGroup1;}

  if ( (line_num >= 16) && (line_num <= 23))
    { group_byte = BaseGroup2;}
  
  if ( (line_num >= 24) && (line_num <= 31))
    { group_byte = BaseGroup3;}
  
  // Now find out which of the 8 lines in that group
  // the line_num inhabits and set the least significant
  // 3 bits to that number
  line = line_num % 8;

  group_byte |= line;

  return(group_byte);
  

} // END Build_Group_Byte

//------------------------------------------------------------------------
//
//  Build_Command_Byte - Given the DAQ line number (0 through 31) and
//                       one of the 4 functions: 
//                            WRITE_DATA
//                            WRITE_GAIN
//                            WRITE_OFFSET
//                            SPEC_FUNCTION
//
//                       form the command byte you need to send to the 
//                       AD5372 prior to the rest of the data bytes
//
//------------------------------------------------------------------------
//
byte Build_Command_Byte( int function, int line_num)
  {
    byte DAQ_function[4] = { DAQ_WRITE_DATA, DAQ_WRITE_OFFSET, DAQ_WRITE_GAIN, DAQ_SPEC_FUNCTION};

    byte command_byte = DAQ_function[function];

    // First find out which group it belongs in
    if ( (line_num >= 0) && (line_num <= 7))
      { command_byte |= (0b00001000);}
  
    if ( (line_num >= 8) && (line_num <= 15))
      { command_byte |= (0b00010000);}

    if ( (line_num >= 16) && (line_num <= 23))
      { command_byte |= (0b00011000);}
  
    if ( (line_num >= 24) && (line_num <= 31))
      { command_byte |= (0b00100000);}
  
    // Now OR in the line lumber of 0-> 7 for this groupo
    command_byte |= (line_num % 8);

    // Return the completed command byte 
    return(command_byte);

  }  // End Function Build_Command_Byte

//------------------------------------------------------------------------
//
//  
//
//------------------------------------------------------------------------
//
