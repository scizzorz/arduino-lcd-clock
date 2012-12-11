#!/usr/bin/env python
import serial

port='/dev/ttyACM0'
baud=9600
ser=serial.Serial(port,baud)

def sersend(num):
	print "-> %s" % num.replace("\n","\\n")
	ser.write(num)

while True:
	line = ser.readline().strip();
	print line
