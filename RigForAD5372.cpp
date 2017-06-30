//#include "Arduino.h"
#include <SPI.h>


//-----------------------------------------------------------------------
//
//    RigSPIForDAQ - Sets up the SPI for working with the AD5372 DAQ
//
//-----------------------------------------------------------------------
void RigSPIforDAQ()
{
    // Shut off SPI just in case someone left it on
    SPI.end();
    
    // INIT SPI
    SPI.setDataMode(SPI_MODE2);
    SPI.setClockDivider(SPI_CLOCK_DIV4);
    SPI.setBitOrder(MSBFIRST);
    
    // Start SPI
    SPI.begin();
    delay(1);
    
} // END RigSPIforDAQ
    
//-----------------------------------------------------------------------
//-----------------------------------------------------------------------


//-----------------------------------------------------------------------
//
//   WRITE
//
//-----------------------------------------------------------------------
//
void write(byte byte1, unsigned int value)
{
    
    //delay(2);
    
    // Send the command.
    SPI.transfer(byte1);
    SPI.transfer(highByte(value));
    SPI.transfer(lowByte(value));

    SelectFunction(LDAC);
    
    delayMicroseconds(50);
    
    // Select Y0 to put the 74HC154 in a NOP pin
    SelectFunction(Y0);
    SystemDisable();
    
} // END WRITE







