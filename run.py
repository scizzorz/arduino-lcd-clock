#!/usr/bin/env python
import serial,os,subprocess,re,dbus
from time import sleep
from datetime import datetime,date,time

env='/usr/bin/env'
path=os.path.dirname(os.path.realpath(__file__))
port='/dev/ttyACM0'
baud=9600

bus = dbus.SessionBus()
banshee = bus.get_object('org.bansheeproject.Banshee','/org/bansheeproject/Banshee/PlayerEngine')

sleepTime=0.1

sleepReset=0.6
longSleepReset=3.0

sleepCounter=0.0
ser=serial.Serial(port,baud,timeout=0)
print 'living in %s' % path

brightness = 255
auxMode = 'song'
auxDisp = '...'
auxScroll = 0

# send a value
def send(val):
	# print it so we know what up
	if type(val)==str:
		print "-> %s" % val.replace("\n","\\n").replace("\t","\\t").replace("\b","\\b")
	else:
		print "-> %s" % val

	# write it
	ser.write(val)

def sendNewline():
	print r'-> \n'
	ser.write('\n')

def sendEnd():
	print r'-> \eof'
	ser.write('\t')

def sendBrightness(newval):
	global brightness
	print r'-> \b = %d' % newval
	brightness = newval
	ser.write('\b' + chr(newval))

# default display
def sendClock():
	global sleepCounter

	# grab the date and make some formats
	d=datetime.now()
	timeString=d.strftime("%l:%M%P").strip()

	dayString=d.strftime('%a')
	monthString=d.strftime('%m').strip()
	if monthString[0]=='0': monthString=monthString[1]
	dateString=d.strftime('%e').strip()

	dateString='%s %s/%s' % (dayString, monthString, dateString)

	# shrink 'am' and 'pm' because of limited display size
	timeString=timeString.replace("pm","p").replace("am","a")

	topString = timeString + (' '*(16 - len(timeString+dateString))) + dateString

	# update the aux display
	updateAux()

	# send them off!
	send(topString[0:16])
	sendNewline()
	sendAux()
	sendEnd()

	# reset the sleep counter
	sleepCounter=sleepReset

def updateAux():
	global auxMode

	if auxMode=='song':
		changeAux('%s - %s' % (banshee.GetCurrentTrack()['name'], banshee.GetCurrentTrack()['artist']))

def changeAux(newAux):
	global auxDisp, auxScroll

	if auxDisp != newAux:
		print r':: "%s"' % newAux
		auxDisp = newAux
		auxScroll = 0

def sendAux():
	global auxDisp, auxScroll

	tempDisp = '%s | %s' % (auxDisp, auxDisp)

	if len(auxDisp)>16:
		send(tempDisp[auxScroll:auxScroll+16])
		auxScroll += 1
		if auxScroll == len(auxDisp)+3:
			auxScroll = 0
	else:
		send(auxDisp)

# volume display
def sendVolume():
	global sleepCounter

	# request volume from amixer and regex the value out
	vol=subprocess.check_output(["amixer","-c","0","get","Master"])
	volMatch=re.search(r'Mono: Playback (\d+)',vol,re.MULTILINE)

	# if the regex didn't match, error!
	if volMatch==None:
		send("(volume error)\n1")
	else: # send it off!
		send("Volume: %d/64" % int(volMatch.group(1)))
		sendEnd()

	# reset the sleep counter
	sleepCounter=longSleepReset

# song display
def sendSong():
	global sleepCounter

	send(banshee.GetCurrentTrack()['name'][0:16])
	sendNewline()
	send(banshee.GetCurrentTrack()['artist'][0:16])
	sendEnd()

	# reset the sleep counter
	sleepCounter=longSleepReset

# banshee state display (playing / paused)
def sendState():
	global sleepCounter

	send(("Music: %s" % banshee.GetCurrentState())[0:16])
	sendEnd()

	# reset the sleep counter
	sleepCounter=longSleepReset

# toggle the screens on and off
def toggleScreens():
	global sleepCounter

	state=subprocess.check_output(["%s/playback/screens.sh" % path]).strip()

	send(state)
	if state=='Locking':
		sendBrightness(5)
	elif state=='Unlocking':
		sendBrightness(255)
	sendEnd()

	# reset the sleep counter
	sleepCounter=longSleepReset


sendBrightness(brightness)
# endless loop
while True:
	# read 9999 bytes from serial
	line=ser.read(9999)

	# if it's more than zero bytes of real data...
	if len(line) > 0:

		# strip it, print it
		line=line.strip()
		print line

		# do actions
		if line=='8': # volume down
			os.system('%s amixer -q sset Master 2dB-' % env)
			sendVolume()
		elif line=='4': # volume up
			os.system('%s amixer -q sset Master 2dB+' % env)
			sendVolume()
		elif line=='2': # previous track
			os.system('%s/playback/prev.sh' % path)
			#banshee.Previous()
			#sendSong()
		elif line=='1': # next track
			os.system('%s/playback/next.sh' % path)
			#banshee.Next()
			#sendSong()
		elif line=='3': # play/pause track
			os.system('%s/playback/play.sh' % path)
			#banshee.TogglePlaying()
			sendState()
		elif line=='12':
			toggleScreens()
		elif line=='6':
			sendState()
		elif line=='5':
			sendSong()
		elif line=='15':
			send('Self-destruct...')
			sendEnd()
			sleep(1)

			send('5')
			sendEnd()
			sleep(1)

			send('4')
			sendEnd()
			sleep(1)

			send('3')
			sendEnd()
			sleep(1)

			send('2')
			sendEnd()
			sleep(1)

			send('1')
			sendEnd()
			sleep(1)

	# increment sleep counter
	sleepCounter-=sleepTime

	# if we're sleeped out, send the default display
	if sleepCounter<=0.0:
		state=subprocess.check_output(["%s/playback/screen-status.sh" % path]).strip()
		if state=='locked' and brightness==255:
			sendBrightness(5)
		elif state=='unlocked' and brightness==5:
			sendBrightness(255)
		sendClock()


	# sleeeeeep
	sleep(sleepTime)
