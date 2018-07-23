#!/usr/bin/python
# -*- coding: utf-8 -*-

# Szivacs sump pump control
# inputs:
# 1 - LOW - Pump running
# 2 - LOW - Overflow alert
# 3 - LOW - Level alert

import automationhat as ah
from time import sleep

pin_state = dict()
pin_state["1"] = False
pin_state["2"] = False
pin_state["3"] = False
pin_state["R"] = False

while 1:
	try:
		sleep(1)
		ah.relay.one.toggle()
		print ah.input.one.read(), ah.input.two.read(), ah.input.three.read()
	except KeyboardInterrupt:
		exit()