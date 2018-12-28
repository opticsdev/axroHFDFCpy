"""
File for constants used by AXRO board and electronics
"""
import serial
# import os

board_num = 1
volt_max = 15.0

#Establish the serial connection
#ser = serial.Serial('/dev/ttyACM0', 9600)
ser = serial.Serial('COM5', 9600)
