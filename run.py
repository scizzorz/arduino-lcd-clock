#!/usr/bin/env python
import serial, os
import time
from datetime import datetime

env='/usr/bin/env'
path=os.path.dirname(os.path.realpath(__file__))
port='/dev/ttyACM0'
baud=9600

ser=serial.Serial(port, baud, timeout=0)
print 'living in %s' % path

brightness = 255

# send a value
def send(val):
	# print it so we know what up
	if type(val)==str:
		print '-> %s' % val.replace('\n',r'\n').replace('\t',r'\t').replace('\b',r'\b')
	else:
		print '-> %s' % val

	# write it
	ser.write(val)

class Clock:
	def __init__(self, max_ticks=10):
		self.top = Line(' ')
		self.bottom = Line(' ')
		self.ticks = max_ticks - 1
		self.max_ticks = max_ticks

	def send(self):
		self.top.send()
		send('\n')
		self.bottom.send()
		send('\t')

	def tick(self):
		self.ticks += 1
		if self.ticks >= self.max_ticks:
			self.ticks = 0
			self.update()

	def update(self):
		# grab the date and make some formats
		d=datetime.now()

		# make the time and convert '[ap]m' -> '[ap]'
		time_string = d.strftime('%l:%M%P').strip()
		time_string = time_string.replace('m','')

		# make each piece of the date individually
		# to get rid of leading whitespace / zeros
		day_string = d.strftime('%a')
		month_string = int(d.strftime('%m'))
		date_string = int(d.strftime('%e'))
		date_string = '%s %d/%d' % (day_string, month_string, date_string)

		# pad the inside of the final string
		full_string = time_string + (' '*(16 - len(time_string+date_string))) + date_string

		self.top = Line(full_string)
		self.send()

	def read(self, line):
		line = line.strip()
		if not line: return

		print line
		# volume down
		if line == '8':
			os.system(env + ' amixer -q sset Master 4%- unmute')

		# volume up
		elif line == '4':
			os.system(env + ' amixer -q sset Master 4%+ unmute')

		# toggle screens
		elif line == '1':
			os.system('screens.sh')

class Line:
	def __init__(self, source):
		self.source = source
		self.disp = ' | '.join((source, source)) if len(source) > 16 else source
		self.scroll = 0
		self.scrollEnabled = (len(source) > 16)

	def send(self):
		if self.scrollEnabled:
			send(self.disp[self.scroll:self.scroll+16])

			self.scroll += 1
			if self.scroll == len(disp)+3:
				self.scroll = 0

		else:
			send(self.disp)

def send_brightness(newval):
	global brightness
	print r'-> \b = %d' % newval
	brightness = newval
	ser.write('\b' + chr(newval))

CLOCK = Clock(50)

send_brightness(brightness)
while True:
	CLOCK.read(ser.read(9999))
	CLOCK.tick()
	time.sleep(0.1)
