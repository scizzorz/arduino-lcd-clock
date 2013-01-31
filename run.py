#!/usr/bin/env python
import serial,os,subprocess,re,dbus,json,urllib2
from time import sleep
from datetime import datetime,date,time

env='/usr/bin/env'
path=os.path.dirname(os.path.realpath(__file__))
port='/dev/ttyACM0'
baud=9600

bus = dbus.SessionBus()
banshee = bus.get_object('org.bansheeproject.Banshee','/org/bansheeproject/Banshee/PlayerEngine')

sleepDelay = 0.1
sleepTimer = 0.0
tickDelay = 0.6
longDisplay = 3.0

ser=serial.Serial(port,baud,timeout=0)
print 'living in %s' % path

brightness = 255
auxMode = 'song'
auxDisp = '...'
auxScroll = 0
auxTime = 0.0

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
	global sleepTimer

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
	sleepTimer = tickDelay

def updateAux():
	global auxMode, auxTime

	if auxTime > 0:
		auxTime -= tickDelay
		if auxTime <= 0.0:
			auxMode = 'song'
			auxTime = 0.0

	if auxMode=='song':
		if banshee.GetCurrentState() == 'paused':
			changeAux("paused")
		else:
			changeAux('%s - %s' % (banshee.GetCurrentTrack()['name'], banshee.GetCurrentTrack()['artist']))

	elif auxMode=='volume':
		vol=subprocess.check_output(["amixer","-c","0","get","Master"])
		volMatch=re.search(r'Mono: Playback (\d+)',vol,re.MULTILINE)

		# if the regex didn't match, error!
		if volMatch==None:
			changeAux("(volume error)")
		else: # send it off!
			changeAux("Volume: %d/64" % int(volMatch.group(1)))


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

def getWeather():
	# GUYS DON't STEAL MY WUNDERGROUND API KEY SRSLY
	# nah I don't care.
	data = urllib2.urlopen('http://api.wunderground.com/api/4871050179d0b3bc/conditions/q/NY/Vestal.json')

	j = json.load(data)

	temp = int(j['current_observation']['temp_f'])
	feelslike = int(j['current_observation']['feelslike_f'])
	weather = j['current_observation']['weather']

	#changeAux('%s: %d / %d' % (weather, temp, feelslike))
	changeAux('%s: %d' % (weather, temp))



# toggle the screens on and off
def toggleScreens():
	global sleepTimer

	state=subprocess.check_output(["%s/playback/screens.sh" % path]).strip()

	send(state)
	if state=='Locking':
		sendBrightness(5)
	elif state=='Unlocking':
		sendBrightness(255)
	sendEnd()

	# reset the sleep counter
	sleepTimer=longSleepReset


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
			auxMode = 'volume'
			auxTime = longDisplay

		elif line=='4': # volume up
			os.system('%s amixer -q sset Master 2dB+' % env)
			auxMode = 'volume'
			auxTime = longDisplay

		elif line=='2': # previous track
			os.system('%s/playback/prev.sh' % path)

		elif line=='1': # next track
			os.system('%s/playback/next.sh' % path)

		elif line=='3': # play/pause track
			#banshee.TogglePlaying()
			os.system('%s/playback/play.sh' % path)

		elif line=='6': # weather!
			getWeather()
			auxMode = 'weather'
			auxTime = 3*longDisplay

		elif line=='12':
			toggleScreens()

		sendClock()

	# increment sleep counter
	sleepTimer-=sleepDelay

	# if we're sleeped out, send the default display
	if sleepTimer<=0.0:
		state=subprocess.check_output(["%s/playback/screen-status.sh" % path]).strip()
		if state=='locked' and brightness==255:
			sendBrightness(5)
		elif state=='unlocked' and brightness==5:
			sendBrightness(255)
		sendClock()


	# sleeeeeep
	sleep(sleepDelay)
