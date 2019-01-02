#!/usr/bin/env python2.7

###############################################################
#
# AXRO_CLI_V2.0.py - This version uses the CommandCheck Class
#                    and VetTheCommand_V3.0,
#                    And has the DACOFF command
###############################################################

from time import sleep
import serial
from AXRO_Command.CommandCheck import *
from AXRO_Command.ProcessCommandFile import *
from AXRO_Command.VetTheCommand_V3_0 import *
import config


# execfile("CommandCheck.py")
# execfile("VetTheCommand_V3.0.py")
# execfile("ProcessCommandFile.py")

def Write_File(outfile, cmd, response):
    outfile.write("\n\n" + cmd + "\n")
    outfile.write(response + "\n")


# Some inits
file_open_flag = False

# Create the class for command checking
CheckIt = CommandCheck()

# Establish the connection on a specific port
ser = config.ser

#  Get the heartbeat
ser.write("HEARTBEAT")
hb_response = ser.readline()
print(hb_response)

# Get a user command
command_line = raw_input("Gimme a full command: ")
split_command = command_line.split()
command = split_command[0].upper().encode()

# Do until the user Control-C's out
while command.upper() != "QUIT":

    # If the command was "FILE" then process the command file
    if command.upper() == "FILE":
        ProcessCommandFile(CheckIt, split_command[1], split_command[2])

    # Check to see if the command is HEARTBEAT. If it is,
    # wait for the response. Eventually we will build in a
    # timeout here.
    elif command.upper() == "HEARTBEAT":
        print("\tSending Heartbeat to the ARDUINO", command_line)
        ser.write(command_line.upper().encode())
        cmd_echo = ser.readline()
        print("Board Response is: ", cmd_echo)

    elif command.upper() == "OPEN":
        filename = raw_input("Give me the name of the output file: ")
        fout = open(filename, "w")
        comment = raw_input("Give me a comment to place at the top: ")
        fout.write(comment+"\n")
        file_open_flag = True

    elif command.upper() == "CLOSE":
        if file_open_flag is True:
            fout.close()
            file_open_flag = False

    elif command.upper() == "DEBUG":
        ser.write(command_line.upper().encode())
        cmd_echo = ser.readline()
        print("Board Response is: ", cmd_echo)

    elif command.upper() == "NODEBUG":
        ser.write(command_line.upper().encode())
        cmd_echo = ser.readline()
        print("Board Response is: ", cmd_echo)

    else:
        # If this is a legal command........
        if VetTheCommand(CheckIt, command_line.upper()) is True:
            #.... then send it to the Arduino
            #print "    Legal Command - Sending to the ARDUINO", command_line
            ser.write(command_line.upper().encode())
            cmd_echo = ser.readline()
            print("Board Response is: ", cmd_echo)
            if file_open_flag == True:
                Write_File(fout, command_line, cmd_echo)

        else:
            print("Unauthorized command IGNORING")
            #ser.write(command_line.upper())
            #cmd_echo = ser.readline()
            #print "Board Response is: ", cmd_echo

    # Get a new command
    command_line = raw_input("Gimme a command: ")
    split_command = command_line.split()
    command = split_command[0]
else:
    # Cleanup try to close the outputing file to remove it from the buffer
    try:
        fout.close()
    except NameError:
        print("File Already Closed or Does not Exist")
# Command was Quit so close down the serial link cleanly
# Send the command to the Arduino so that it drops into it's wait state
ser.write(command_line.upper().encode())

# close down the serial line from this end
ser.close()

print("Ok then bye for now")
