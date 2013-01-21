#!/usr/bin/env python
import serial

port='/dev/ttyACM0'
baud=1200
ser=serial.Serial(port,baud,timeout=0)
ser.close();
