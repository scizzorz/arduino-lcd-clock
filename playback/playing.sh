#!/bin/bash
export $(strings /proc/*/environ 2> /dev/null | grep DeUS_SESSION | tail -1) > /dev/null
banshee --query-current-state
