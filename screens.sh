#!/bin/bash
dpms=$(xset q | grep "Monitor is" | grep -o "On\|Off")

if [ "$dpms" == "On" ]; then
	xset dpms force off
else
	xset dpms force on
fi
