#!/usr/bin/env python2.7

import numpy as np
import serial
import os
from AXRO_Command.CommandCheck import *
from AXRO_Command.ProcessCommandFile import *
from AXRO_Command.VetTheCommand_V3_0.py import *

########
# Top level settings for axroElectronics.
########
# Establish HFDFC3 mirror channel to board channel map
cellmap = np.array([0,1,2,3,4,5,6,7,32,33,34,35,36,37,\
           16,17,18,19,20,21,22,23,48,49,50,51,52,53,54,55,\
           8,9,10,11,12,40,41,42,43,44,45,46,47,24,25,26,27,28,29,30,31,\
           56,57,58,59,60,64,65,66,67,68,69,70,71,96,97,98,99,100,101,\
           80,81,82,83,84,85,86,87,112,113,114,115,116,117,118,119,\
           72,73,74,75,76,104,105,106,107,108,109,110,111,\
           88,89,90,91,92,93,94,95,120,121,122,123,124])
board_num = 1
volt_max = 10.0

#Establish the serial connection
ser = serial.Serial('COM5', 9600)

def convChan(chan):
    """
    Convert channel from piezo cell num (minus 1)
    to proper DAC and channel number on board.
    0 corresponds to cell 1
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
    print "Board Response is: ", cmd_echo
    return cmd_echo

def setChan(chan,volt):
    """
    Convert the channel number into board format and then issue
    command to set voltage.
    Limit of <= 5 V is encoded into this function.
    """
    if volt <= volt_max and volt >= 0.:
        dac,channel = convChan(chan)
        cstr = 'VSET %i %i %i %f' % (board_num,dac,channel,volt)
        ser.write(cstr.encode())
        echo()
    else:
        print 'Voltage out of bounds!'
    return None

def readChan(chan):
    """
    Convert channel from 0-112 into proper DAC and channel number
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
    for c in range(32*4):
        setChan(c,0.)
    return None

def setVoltArr(voltage):
    """
    Set all 112 channels using a 112 element voltage vector.
    The indices correspond to piezo cell number.
    """
    for c in range(len(cellmap)):
        setChan(cellmap[c],voltage[c])
    return None

def setVoltChan(chan,volt):
    """
    Set individual piezo cell, channel corresponds to piezo cell number
    """
    setChan(cellmap[chan-1],volt)
    return None

def readVoltArr():
    """
    Loop through and read the voltages on all piezo cells. Return
    vector of voltages where index matches cell number (minus one).
    """
    v = np.array([])
    for c in range(len(cellmap)):
        v = np.append(v,readChan(cellmap[c]))
    return v

def readVoltChan(chan):
    """
    Read individual piezo cell voltage. Chan refers to piezo cell number.
    """
    return readChan(cellmap[chan-1])

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
    return

#def init():
#    """
#    Change to software directory and run initialization script.
#    """
#    ProcessCommandFile(CommandCheck(),arddir+'SetUp_DACOFF.txt',0)
#    return None
