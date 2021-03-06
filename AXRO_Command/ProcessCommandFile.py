#!/usr/bin/env python2.7
from time import sleep
import pdb
import serial
# import sys
from .VetTheCommand_V3_0 import VetTheCommand
from .. import config
#-------------------------------------------------------------------------------
#
#  ProcessCommandFile - Open the file specified in the argument list, read and
#                vet the commands.  Issue each legal command with a
#                delay of  cmd_delay seconds in between
#-------------------------------------------------------------------------------
def ProcessCommandFile(CheckIt, filespec, cmd_delay):
    ser = config.ser
    cmdfile = open(filespec, "r")

    # Now process each command
    for eachcmd in cmdfile:
        if eachcmd[0] != "#":
            eachcmd = eachcmd[0:-1]

            print("Processing this command from the file:\n\t", eachcmd)
            sleep(float(cmd_delay))

            # make all alpha characters uppercase
            upper_cmd = eachcmd.upper()
            #print "upcased:"+upper_cmd+"***"

            # If the command is a legal command
            if VetTheCommand(CheckIt, upper_cmd):
                #.... then send it to the Arduino
                split_cmd = upper_cmd.split()
                if split_cmd[0] != "QUIT":
                    #
                    ser.write(upper_cmd)
                    print("\t\tWaiting for the command echo...")
                    cmd_echo = ser.readline()
                    print("Command Echo is: ", cmd_echo)
                    if cmd_echo[:3] == '***':
                        pdb.set_trace()
                else:
                    print("ERROR - Cannot issue a QUIT from a command file")
            else:
                print("Unauthorized command")
        #else:
#    print "-------------------Ignoring a comment line: ", eachcmd

    # Finished with the file - close it
    cmdfile.close()
