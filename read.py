#!/usr/bin/env python
import serial
from time import sleep

port='/dev/ttyACM0'
baud=9600
sleepTime=0.1
ser=serial.Serial(port,baud,timeout=0)

def sersend(num):
	print "-> %s" % num.replace("\n","\\n")
	ser.write(num)

while True:
	line=ser.read(9999)
	if len(line)>0:
		line=line.strip()
		print line
	sleep(sleepTime)
