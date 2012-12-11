#!/usr/bin/env python
import serial,os,subprocess,re
from datetime import datetime,date,time

env='/usr/bin/env'
path=os.path.dirname(os.path.realpath(__file__))
port='/dev/ttyACM0'
baud=9600

ser=serial.Serial(port,baud)
print 'living in %s' % path

# send a value
def sersend(val):
	# print it so we know what up
	if type(val)==str:
		print "-> %s" % val.replace("\n","\\n").replace("\t","\\t")
	else:
		print "-> %s" % val
	
	# write it
	ser.write(val)

# default display
def sendClock():
	# grab the date and make some formats
	d=datetime.now()
	dstring=d.strftime("%B %e")
	tstring=d.strftime("%l:%M%P %A")

	# shrink 'am' and 'pm' because of limited display size
	tstring=tstring.replace("pm","p").replace("am","a")

	# send them off!
	sersend(tstring.strip()[0:16])
	sersend('\n')
	sersend(dstring.strip()[0:16])
	sersend('\t')

# volume display
def sendVolume():
	# request volume from amixer and regex the value out
	vol=subprocess.check_output(["amixer","-c","0","get","Master"])
	volMatch=re.search(r'Mono: Playback (\d+)',vol,re.MULTILINE)

	# if the regex didn't match, error!
	if volMatch==None:
		sersend("(volume error)\n1")
	else: # send it off!
		sersend("Volume: %d/64" % int(volMatch.group(1)))
		sersend('\t')

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
		sersend("(music error)\n2")
	else: # send them off!
		sersend(titleMatch.group(1)[0:16])
		sersend("\n")
		sersend(artistMatch.group(1)[0:16])
		sersend('\t')

# banshee state display (playing / paused)
def sendState():
	# request state from banshee and regex the value out
	state=subprocess.check_output(["%s/playback/playing.sh" % path])
	stateMatch=re.search(r'current.state: (.+)',state)

	# if the regex didn't match, error!
	if stateMatch==None:
		sersend("(music error)\n3")
	else: # send it off!
		sersend("Music: %s" % stateMatch.group(1)[0:16])
		sersend('\t')

# endless loop
while True:
	# read a line, strip it of excess whitespace, and print it
	line=ser.readline().strip()
	print line

	# request for default display
	if line=='r' or line=='-1':
		sendClock()
	elif line=='1': # volume down
		os.system('%s amixer -q sset Master 2dB-' % env)
		sendVolume()
	elif line=='2': # volume up
		os.system('%s amixer -q sset Master 2dB+' % env)
		sendVolume()
	elif line=='4': # previous track
		os.system('%s/playback/prev.sh' % path)
		sendSong()
	elif line=='8': # next track
		os.system('%s/playback/next.sh' % path)
		sendSong()
	elif line=='12': # play/pause track
		os.system('%s/playback/play.sh' % path)
		sendState()