#include "Arduino.h"
#include <SPI.h>

//-----------------------------------------------------------------------------
//
//   Read_ADT7310
//
// Read from a generic register of the ADT7310.  numbits indicates 
// either an 8 or 16 bit read. 
// 
// The ADT7310 works by sending a command byte, which indicates which 
// register you want to  read from, followed by a second read (8/16 bit) 
// which is the data from that register.  
//
// Note that the command has a flag to put the ADT7310 into continuous 
// read, which I don't do anything with. 
// 
// Data is clocked out of the ADT7310 on the negative edge of SCLK, and
// clocked into the device on the positive edge of SCLK.   Hardware SPI 
// looks after this for us, as long as the modes are  set right.  
// 
//----------------------------------------------------------------------------
//
unsigned int Read_ADT7310(int reg, int numbits) 
{
  unsigned int readval = 0;
  unsigned int readval2 = 0; 
  //unsigned int bitval = 0; 
  
  // Command bits - 0, READ, 3 bits address, continuous read, 0, 0
  byte commandbits = 0b01000000;
  
  // OR in the specified register
  commandbits = commandbits | (reg << 3);
  
  //  Select ADT7310 --------------------------------------------------------SELECT
  SelectFunction(TEMP);
  // Send command byte via SPI
  SPI.transfer(commandbits); 
  delay(300);
  
  //read bits from ADT7310, 16-bit read
  
  readval=0;
  
  // Doing an SPI.transfer(0x00) essentially does a 'read' 
  readval = SPI.transfer(0x00); 
  
  // See if we have to read more bits yet. 
  numbits -= 8; 
  if (numbits > 0) 
  {
     // Shift the LSbyte
     readval=readval << 8; 
	 // Do a second read of the next 8 bits 
     readval2 = SPI.transfer(0x00); 

    // Combine ther two results if this was a 16 bit read
     readval = readval | readval2;
 
  } // ENDIF numbits > 0)
  
  // DeSelect ADT7310  ------------------------------------------------ DE-SELECT
  SelectFunction(Y0);

  return readval;
  
  } // END READ_ADT7310
  


//-----------------------------------------------------------------------------
//
//   Write_ADT7310
//
//-----------------------------------------------------------------------------
//
void Write_ADT7310(int reg, unsigned int value, int numbits)
{
  //unsigned int bitval = 0; 
  byte byteval = 0; 
  byte commandbits = 0b00000000; //command bits - 0, R/W, 3 bits address, continuous read, 0, 0
  commandbits = commandbits | (reg << 3);
  
   // Select the slave
  SelectFunction(TEMP);     
  // Send the command.
  SPI.transfer(commandbits); 

  // write value to SPI bus
  if (numbits == 8)
    { 
       // If 8-bit data, send that as one transfer 
       byteval = value & 0xFF; 

       // setup command to be written
    
       SPI.transfer(byteval); 
     } // END NUMBITS == 8
   else 
     if (numbits == 16) 
       {
	  // if 16-bit data, send as two chunks - MSB first 
          byteval = (value >>8); 
    
	  // Send high 8-bits
          SPI.transfer(byteval);

         // send low 8-bits
        byteval = (value & 0xFF);  
        SPI.transfer(byteval); 	
      } // END NUMBITS == 16
  
  // Deselect the ADT7310 slave
  SelectFunction(Y0);
  
} // END WRITE_ADT7310

//--------------------------------------------------------------------------
//
//   SETMODE
//
// Writes to register 0x01, the configuation register.  You can use the define's 
//  in ADT7310.h to make this easier
// e.g.       adt7310.setmode(ADT7310_1FAULT | ADT7310_CT_POLARITY_LOW | ADT7310_INT_POLARITY_LOW | 
//            ADT7310_INTCT_INTERRUPT | ADT7310_CONTINUOUS | ADT7310_16BIT); 
//
//----------------------------------------------------------------------
//
void setmode(int value) 
  {
	Write_ADT7310(0x01,value,8);
  }


//-------------------------------------------------------------------------------
//
//   Temperature
//
//------------------------------------------------------------------------------
//
float temperature(unsigned int value, int numbits)
{
	float temperature;
	boolean isNegative = false;  

	value = (value >> (16-numbits));   // Bits are left-aligned in two-byte response
	
	// Check for two's complement (negative) temperature value
	if (bitRead(value,numbits-1)==1)  {
		value |= (0xFFFF << numbits);   // Extend sign bit to the end of the 16-bit space
		value = (~value +1);   // calculate two's complement 
		
		isNegative=true;
	}
	
        // Dummy value to get us started.   If the routine returns the -9999.99 you 
	// know something fell through incorrectly. 
    //warning: statement has no effect [-Wunused-value]
	temperature == -9999.99;  
	// Taken directly from the datasheet 
	if (numbits == 16) {
			temperature = value/128.0;
	} else if (numbits == 13) {
			temperature = value/16.0;
	} else if (numbits == 10) {
			temperature = value/2.0; 
	} else if (numbits == 9) {
			temperature = value*1.0; 
	}
	
	
	if (isNegative)
		temperature=-temperature; 
		
	
	return temperature;
}

//-----------------------------------------------------------------------
//   RESET the ADT7310
//     Selects TEMP function
//     Sends 100 1's
//     DeSelects Temp sensor
//     Executes a throw away READ 16
//     Waits 240
// This also does a Setmode for the ADT7310
//-----------------------------------------------------------------------

void Reset_ADT7310()
  {
      
    // Reset the ADT7310 write at least 32 1's
    SelectFunction(TEMP);
 
    for(int i=0; i<100; i++) 
      {
        SPI.transfer(0x01);
      }
    
    delay(500);
    
    //Done with the reset. Disable the ADT7310
    SelectFunction(Y0);

    // Execute a setmode
    // Setting the mode
    setmode(ADT7310_1FAULT | ADT7310_CT_POLARITY_LOW | ADT7310_INT_POLARITY_LOW |
		ADT7310_INTCT_INTERRUPT | ADT7310_CONTINUOUS | ADT7310_16BIT);

   // Execute a READ
   Read_ADT7310(0x04, 16);
     
   //delay(240);   // First conversion takes ~ 240 ms 
  }  // END RESET_ADT7310
  
//-----------------------------------------------------------------------------------------
//---------------------------------------------------------------------------------------

void RigSPIforTREAD()
{
  // Shut off SPI just in case someone left it on
  SPI.end();
  
  // INIT SPI for this particular device
  SPI.setDataMode(SPI_MODE2); // CHANGED TO SPI_MODE2 
  SPI.setClockDivider(SPI_CLOCK_DIV4);
  SPI.setBitOrder(MSBFIRST);

 // Start SPI
  SPI.begin();
 
 
 // Setting the mode
 //setmode(ADT7310_1FAULT | ADT7310_CT_POLARITY_LOW | ADT7310_INT_POLARITY_LOW | 
  //		ADT7310_INTCT_INTERRUPT | ADT7310_CONTINUOUS | ADT7310_16BIT); 



} // END RIGSPIFORTREAD
