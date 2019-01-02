#!/usr/bin/env python2.7

import serial
import time
#import os
import numpy as np
from AXRO_Command.CommandCheck import CommandCheck
from AXRO_Command.ProcessCommandFile import ProcessCommandFile
#from AXRO_Command.VetTheCommand_V3_0.py import *

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
    return dac, channel

def echo():
    """
    Retrieve the response from the board after a command is issued.
    Print the response, also return the response as a string.
    """
    cmd_echo = ser.readline()
    if verbose:
        print("Board Response is: ", cmd_echo)
    return cmd_echo

def encoded_init():
    """
    Change to software directory and run initialization script.
    """
    ProcessCommandFile(CommandCheck(), 'SetUp_DACOFF.txt', 0)

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
        print('Voltage out of bounds!')

def readChan(chan):
    """
    Convert channel into proper DAC and channel number
    Then issue read command and parse voltage from echo.
    """
    dac,channel = convChan(chan)
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
    for c in range(256):
        setChan(c, 0.0)

def setVoltArr(voltage):
    """
    Set all 112 channels using a 112 element voltage vector.
    The indices correspond to piezo cell number.
    """
    for c in range(256):
        setChan(cellmap[c], voltage[c])


def setVoltChan(chan, volt):
    """
    Set individual piezo cell, channel corresponds to piezo cell number
    """
    setChan(cellmap[chan], volt)

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

def init(board=board_num):
    """
    Change to software directory and run initialization script.
    """
    cstr = 'RESET %i' % (board)
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

def test_board(tvolts=None, header='180110_Board2_Retest_'):
    if tvolts is None:
        tvolts = [0, -10, -1, 1, 10]
    ground()

    for volt in tvolts:
        ground()
        setVoltArr(np.ones(256) * volt)
        rvolts = readVoltArr()
        np.savetxt(header + str(volt) + 'V_ReadResponse.txt', rvolts)
        print('Tested ' + str(volt) + 'V, Sleeping Briefly....')
        time.sleep(10)
