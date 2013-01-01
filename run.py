#!/usr/bin/env python
import serial,os,subprocess,re
from time import sleep
from datetime import datetime,date,time

env='/usr/bin/env'
path=os.path.dirname(os.path.realpath(__file__))
port='/dev/ttyACM0'
baud=9600
sleepTime=0.1
sleepTimeout=3.0

sleepCounter=0.0
ser=serial.Serial(port,baud,timeout=0)
print 'living in %s' % path

# send a value
def send(val):
	global sleepCounter

	# print it so we know what up
	if type(val)==str:
		print "-> %s" % val.replace("\n","\\n").replace("\t","\\t").replace("\b","\\b")
	else:
		print "-> %s" % val
	
	# write it
	ser.write(val)

	# reset the sleep counter
	sleepCounter=0.0

def sendNewline():
	print r'-> \n'
	ser.write('\n')

def sendEnd():
	print r'-> \eof'
	ser.write('\t')

def sendBrightness(brightness):
	print r'-> \b = %d' % brightness
	ser.write('\b' + chr(brightness))

# default display
def sendClock():
	# grab the date and make some formats
	d=datetime.now()
	dstring=d.strftime("%B %e")
	tstring=d.strftime("%l:%M%P %A")

	# shrink 'am' and 'pm' because of limited display size
	tstring=tstring.replace("pm","p").replace("am","a")

	# send them off!
	send(tstring.strip()[0:16])
	sendNewline()
	send(dstring.strip()[0:16])
	sendEnd()

# volume display
def sendVolume():
	# request volume from amixer and regex the value out
	vol=subprocess.check_output(["amixer","-c","0","get","Master"])
	volMatch=re.search(r'Mono: Playback (\d+)',vol,re.MULTILINE)

	# if the regex didn't match, error!
	if volMatch==None:
		send("(volume error)\n1")
	else: # send it off!
		send("Volume: %d/64" % int(volMatch.group(1)))
		sendEnd()

# song display
def sendSong():
	# request title and artist from banshee
	title=subprocess.check_output(["%s/playback/title.sh" % path])
	artist=subprocess.check_output(["%s/playback/artist.sh" % path])

	# regex the values out
	titleMatch=re.search(r'title: (.+)',title)
	artistMatch=re.search(r'artist: (.+)',artist)

	# if the regex didn't match, error!
	if artistMatch==None or titleMatch==None:
		send("(music error)\n2")
	else: # send them off!
		send(titleMatch.group(1)[0:16])
		sendNewline()
		send(artistMatch.group(1)[0:16])
		sendEnd()

# banshee state display (playing / paused)
def sendState():
	# request state from banshee and regex the value out
	state=subprocess.check_output(["%s/playback/playing.sh" % path])
	stateMatch=re.search(r'current.state: (.+)',state)

	# if the regex didn't match, error!
	if stateMatch==None:
		send("(music error)\n3")
	else: # send it off!
		send("Music: %s" % stateMatch.group(1)[0:16])
		sendEnd()

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
			sendSong()
		elif line=='1': # next track
			os.system('%s/playback/next.sh' % path)
			sendSong()
		elif line=='3': # play/pause track
			os.system('%s/playback/play.sh' % path)
			sendState()
	
	# increment sleep counter
	sleepCounter+=sleepTime

	# if we're sleeped out, send the default display
	if sleepCounter>=sleepTimeout:
		sendClock()

	# sleeeeeep
	sleep(sleepTime)
