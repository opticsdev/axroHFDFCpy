#include "Arduino.h"

// Command Byte Bit Set Possibilities

// Command byte which selects:

//    SGL        1 ------|
//    ODD SIGN   0 ------|--- These 4bits select which of the 8 channels to
//    SELECT     0 ------|    read.
//               0 ------|

//       UNI     1  (unipolar)
//      GAIN     1  (0 to 10 volts)
//       NAP     0  (No Nap)
//     SLEEP     0  (No Sleep)

//------------------------------------------------------------------------------
// RigForLTC1859  - Set the Data Mode and Bit order for the LTC1959
//------------------------------------------------------------------------------

void RigForLTC1859()
{
  // Shut down SPI in case it was running
  SPI.end();
  
  // Set the Data Mode and Bit order for the LTC1959
  // changes to MODE2 12/7/16
  SPI.setDataMode(SPI_MODE2);
  SPI.setBitOrder(MSBFIRST);
  
  // Turn SPI back on again now that you've modified the settings
  SPI.begin();
  
} // END FUNCTION RigForLTC1859



//------------------------------------------------------------------------------
// StartConvert  - Setting SSA3 through SSA0 to 0b1011 causes
//                 the Y11, or /CSTRT, line of the 74HC154 to
//                 go low.  This then causes the CONVST line on the
//                 LTC1859 to go high which starts a Conversion
// 
//------------------------------------------------------------------------------

void StartConvert()
{
 
  // Tell the LTC1859 to execute a conversion /CSTRT
  // Set /CSTRT - Y11 - LOW which is inverted bringing CONVST HIGH
  // on the LTC
  SelectFunction(CSTRT);
  delay(1);
    
  // Now set /CSTRT HIGH which brings CONVST LOW
  SystemDisable();
  SelectFunction(Y0);

  // Delay just a little bit to allow the conversion to finish
  // Since I can't read the BUSY line  
  delay(1);
  
  // Now bring the /SYSENbar HIGH to disable the system
  //digitalWrite(SYSENbar, HIGH);
 
} // End SetCSTRTlow

//---------------------- ADG1206 ---------------------------------------
//
// MUX_Output_Chan_Select - given an integer, set the 4 bits of the
//                          mux (ADG1206) output to connect the
//                          specified DAQ channel to the LTC1859 readback.
//
//----------------------------------------------------------------------
void MUX_Output_Chan_Select( int channel)

{
    byte state0, state1, state2, state3;
    //byte muxval;
    
    // The ADG1206 enable is active HIGH. The lower 16 DAC channels
    // are sent to the 1206 that is tied to /MUXA4.  The high
    // 16 DAC channels are sent to the 1206 toes to MUXA4.
    // therefore if the channel number is 0-15, set MUXA4 LOW
    // else if the channel number is 16-31, set it HIGH.
    if (channel <= 15)
      {
        // Figure out the bit settings for the input channel number
        // for channels 0-15, you can use the bits in the channel
        // number directly.
        digitalWrite(MUXA4, LOW);
        //muxval = LOW;
      }
    else
      {
        // For channels 16-31, you have to shift the channel number
        // to the right 4 bits to get the bits to the least sig 4
        digitalWrite(MUXA4, HIGH);
        //muxval = HIGH;
      }
    
    // Either way, the bits in the channel number are now ready to use
    // Set the channel.You can use the same Least Sig 4 bits for
    // either 0-15 or 16-31
    state0 = bitRead(channel, 0);
    state1 = bitRead(channel, 1);
    state2 = bitRead(channel, 2);
    state3 = bitRead(channel, 3);
    
    // Write those out to the appropriate MUX pins
    digitalWrite(MUXA0, state0);
    digitalWrite(MUXA1, state1);
    digitalWrite(MUXA2, state2);
    digitalWrite(MUXA3, state3);
    
    // Wait a millisec
    delay(1);
    
} // END FUNCTION MUX_Output_Chan_SELECT


//------------------------------------------------------------------------------
// ReadLTC1859Channel  - Read the LTC1959 on the channel you selected with the
//                call to MUX_Output_Chan_Select( int channel)
//------------------------------------------------------------------------------
word ReadLTC1859Channel(byte command, int channel)
  {
    //byte muxval;
      
    //int ii;
      
    // HOME Unipolar 0 to 10 volts, channel 0 fixed
    // byte command=B10001100;
      
    // Enable the system
    SystemEnable();
      
    word conv_result;
    conv_result = 0;
    
    // ....rig for the LTC1859
    RigForLTC1859();
  
    // Selecting Y0 will set RD and CSTRT HIGH by setting an
    // unused line (Y0) LOW.
    SelectFunction(Y0);
   
    
    // Cause the AOUT-0 from the DAC to be selected by the MUX
    // by setting all 4 bits to zero.  This is set and fixed
      //SystemDisable();
      MUX_Output_Chan_Select(channel);
      //SystemEnable();
      
    // We are going to do a read 
    // Trigger a conversion by setting CONVST HIGH then LOW
    // Set /CSTRT HIGH
    StartConvert();

    // FIRST READ IN SETUP
    // Set /SS8  - Y8 - LOW in order to Slave Select the LTC1859 /RD line
    //SystemDisable();
    SelectFunction(LTC1859);
    //SystemEnable();

    
    // Send the command and also get the highbyte of the conversion
    conv_result = SPI.transfer(command)<<8;

    // Send filler and get the low byte of the conversion
    //byte filler = B00000000;
  
    conv_result = conv_result | SPI.transfer(B00000000);

      
    // Bring RD HIGH by selecting Y0 of the 74HC154
    //SystemDisable();
    SelectFunction(Y0);
    //SystemEnable;
      
    return(conv_result);

  } // END FUNCTION ReadLTC1859Channel
