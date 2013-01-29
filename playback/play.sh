#!/bin/bash
if pgrep banshee > /dev/null 2>&1; then
	export $(strings /proc/*/environ 2> /dev/null | grep DeUS_SESSION | tail -1) > /dev/null
	banshee --toggle-playing
else
	echo "Banshee dead"
fi
