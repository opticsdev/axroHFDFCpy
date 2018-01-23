import numpy as np
import serial
import time
import os

#Load Gregg's functions
arddir = u'C:\\Users\\rallured\\Dropbox\\AXRO\\Arduino\\AXROMirrorControlSoftware\\'
execfile(arddir+"CommandCheck.py")
execfile(arddir+"VetTheCommand_V3.0.py")
execfile(arddir+"ProcessCommandFile.py")

board_num = 1
verbose = True
abs_volt_max = 15.0

#Establish the serial connection
ser = serial.Serial('COM5', 9600)

cellmap = range(256)

def convChan(chan):
    """
    Convert channel from 0 - 255 to proper DAC and channel number on board.
    """
    dac = int(chan) / 32
    channel = int(chan) % 32
    return dac,channel

def echo():
    """
    Retrieve the response from the board after a command is issued.
    Print the response, also return the response as a string.
    """
    cmd_echo = ser.readline()
    if verbose:
        print "Board Response is: ", cmd_echo
    return cmd_echo

def encoded_init():
    """
    Change to software directory and run initialization script.
    """
    ProcessCommandFile(CommandCheck(),arddir+'SetUp_DACOFF_FullBoard3.txt',0)
    return None

def setChan(chan,volt):
    """
    Convert the channel number into board format and then issue
    command to set voltage.
    Limit of <= abs(15 V) is encoded into this function.
    """
    if abs(volt) <= abs_volt_max:
        dac,channel = convChan(chan)
        cstr = 'VSET %i %i %i %f' % (board_num,dac,channel,volt)
        ser.write(cstr.encode())
        echo()
    else:
        print 'Voltage out of bounds!'
    return None

def readChan(chan):
    """
    Convert channel into proper DAC and channel number
    Then issue read command and parse voltage from echo.
    """
    dac,channel = convChan(chan)
    cstr = 'VREAD %i %i %i' % (board_num,dac,channel)
    ser.write(cstr.encode())
    s = echo()
    return float(s.split()[-1])
    
def close():
    """
    Close the serial connection to the Arduino
    """
    ser.write('QUIT'.encode())
    ser.close()
    return None

#Define higher level functions for interacting with piezo mirror
def ground():
    """
    Set all channels to zero volts
    """
    for c in range(256):
        setChan(c,0.0)
    return None

def setVoltArr(voltage):
    """
    Set all 112 channels using a 112 element voltage vector.
    The indices correspond to piezo cell number.
    """
    for c in range(256):
        setChan(cellmap[c],voltage[c])
    return None

def setVoltChan(chan,volt):
    """
    Set individual piezo cell, channel corresponds to piezo cell number
    """
    setChan(cellmap[chan],volt)
    return None

def readVoltArr():
    """
    Loop through and read the voltages on all piezo cells. Return
    vector of voltages where index matches cell number (minus one).
    """
    v = []
    for c in range(256):
        v.append(readChan(cellmap[c]))
    return np.asarray(v)

def readVoltChan(chan):
    """
    Read individual piezo cell voltage. Chan refers to piezo cell number.
    """
    return readChan(cellmap[chan])

def init(board_num = board_num):
    """
    Change to software directory and run initialization script.
    """
    cstr = 'RESET %i' % (board_num)
    ser.write(cstr.encode())
    echo()
    
    for dac in range(8):
        cstr = 'DACOFF %i %i 0 8192' % (board_num,dac)
        ser.write(cstr.encode())
        echo()
        
        cstr = 'DACOFF %i %i 1 8192' % (board_num,dac)
        ser.write(cstr.encode())
        echo()

    ground()
    return None

def test_board(tvolts = [0,-10,-1,1,10],header = arddir + '180110_Board2_Retest_'):
    ground()
    
    for volt in tvolts:
        ground()
        setVoltArr(np.ones(256)*volt)
        rvolts = readVoltArr()
        np.savetxt(header + str(volt) + 'V_ReadResponse.txt',rvolts)
        print 'Tested ' + str(volt) + 'V, Sleeping Briefly....'
        time.sleep(10)