#!/usr/bin/env python2.7

import numpy as np
import config
# import os
# from AXRO_Command.CommandCheck import CommandCheck
# from AXRO_Command.ProcessCommandFile import ProcessCommandFile
#from AXRO_Command.VetTheCommand_V3_0.py import *

########
# Top level settings for axroElectronics.
########
# Establish HFDFC3 mirror channel to board channel map
cellmap = np.array([0, 1, 2, 3, 4, 5, 6, 7, 32, 33, 34, 35, 36, 37,\
           16, 17, 18, 19, 20, 21, 22, 23, 48, 49, 50, 51, 52, 53, 54, 55,\
           8, 9, 10, 11, 12, 40, 41, 42, 43, 44, 45, 46, 47, 24, 25, 26, 27, 28, 29, 30, 31,\
           56, 57, 58, 59, 60, 64, 65, 66, 67, 68, 69, 70, 71, 96, 97, 98, 99, 100, 101,\
           80, 81, 82, 83, 84, 85, 86, 87, 112, 113, 114, 115, 116, 117, 118, 119,\
           72, 73, 74, 75, 76, 104, 105, 106, 107, 108, 109, 110, 111,\
           88, 89, 90, 91, 92, 93, 94, 95, 120, 121, 122, 123, 124])

# Import Globals from config.py
volt_max = config.volt_max
board_num = config.board_num
ser = config.ser

def convChan(chan):
    """
    Convert channel from piezo cell num (minus 1)
    to proper DAC and channel number on board.
    0 corresponds to cell 1
    """
    dac = int(chan) / 32
    channel = int(chan) % 32
    return dac, channel

def echo():
    """
    Retrieve the response from the board after a command is issued.
    Print the response, also return the response as a string.
    """
    cmd_echo = ser.readline()
    print("Board Response is: ", cmd_echo)
    return cmd_echo

def setChan(chan, volt=0):
    """
    Convert the channel number into board format and then issue
    command to set voltage.
    Limit of <= 5 V is encoded into this function.
    """
    if 0.0 <= volt <= volt_max:
        dac, channel = convChan(chan)
        cstr = 'VSET %i %i %i %f' % (board_num, dac, channel, volt)
        ser.write(cstr.encode())
        echo()
    else:
        print('Voltage out of bounds!')


def readChan(chan):
    """
    Convert channel from 0-112 into proper DAC and channel number
    Then issue read command and parse voltage from echo.
    """
    dac, channel = convChan(chan)
    cstr = 'VREAD %i %i %i' % (board_num, dac, channel)
    ser.write(cstr.encode())
    s = echo()
    return float(s.split()[-1])

def close():
    """
    Close the serial connection to the Arduino
    """
    ser.write('QUIT'.encode())
    ser.close()

#Define higher level functions for interacting with piezo mirror
def ground():
    """
    Set all channels to zero volts
    """
    for c in range(len(cellmap)):
        setChan(c, 0.0)

def setVoltArr(voltage):
    """
    Set all 112 channels using a 112 element voltage vector.
    The indices correspond to piezo cell number.
    """
    for c in range(len(cellmap)):
        setChan(cellmap[c], voltage[c])

def setVoltChan(chan, volt=0):
    """
    Set individual piezo cell, channel corresponds to piezo cell number
    """
    setChan(cellmap[chan-1], volt)

def readVoltArr():
    """
    Conviencence Fuction to Loop through and read the voltages on all piezo
    cells. Return vector of voltages where index matches cell number (minus one)
    """
    v = np.array([])
    for c in range(len(cellmap)):
        v = np.append(v, readChan(cellmap[c]))
    return v

def readVoltChan(chan):
    """
    Read individual piezo cell voltage. Chan refers to piezo cell number.
    """
    return readChan(cellmap[chan-1])

def init(board=config.board_num):
    """
    Change to software directory and run initialization script.
    """
    cstr = 'RESET %i' % (board_num)
    ser.write(cstr.encode())
    echo()

    for dac in range(8):
        cstr = 'DACOFF %i %i 0 8192' % (board, dac)
        ser.write(cstr.encode())
        echo()

        cstr = 'DACOFF %i %i 1 8192' % (board, dac)
        ser.write(cstr.encode())
        echo()

    ground()
