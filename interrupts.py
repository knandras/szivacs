#!/usr/bin/python
# -*- coding: utf-8 -*-

# Szivacs sump pump control
# inputs:
# 1 - LOW - Pump running
# 2 - LOW - Overflow alert
# 3 - LOW - Level alert

# States:
# idle
# level triggered
# pump started
# pump running with level
# pump running
# emergency triggered
# pump runing with emergency
# error


import automationhat as ah
import time as time_module
from collections import deque

class PumpState():
	def __init__(self):
		self.pump = False
		self.emergency = False
		self.level = False
		self.relay = False
		self.last_change = time_module.time()
		self.state = "idle"
		self.past_states = deque([], 10)
		self.cause = "Startup"
		self.prevstate = (self.pump, self.emergency, self.level, self.state, self.cause)
		print "{} Started input polling.".format(time_module.strftime("%Y.%m.%d %H:%M"))

	def update(self):
		self.prevstate = (self.pump, self.emergency, self.level, self.state)
		self.pump = not(ah.input.one.read())
		self.emergency = not(ah.input.two.read())
		self.level = not(ah.input.three.read())

		if (self.pump, self.emergency, self.level, self.relay) == (True, True, True, True): #1
			self.state_change("error", "All inputs and output True #1")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, True, True, True): #2
			self.state_change("error", "Pump not running despite both levels and relay True #2")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, False, True, True) and (self.last_change + 30) > time_module.time(): #3 in-time
			self.state_change("pump start running", "Pump just started, level should clear in 30 sec #3")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, False, True, True) and (self.last_change + 30) < time_module.time(): #3 timeout
			self.state_change("error", "Pump just started, level did not clear in 30 sec #3")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, False, True, True) and (self.last_change + 5) > time_module.time(): #4 in-time
			self.state_change("pump start", "Relay just closed, pump should start in 5 sec #4")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, False, True, True) and (self.last_change + 5) > time_module.time(): #4 timeout
			self.state_change("error", "Relay just closed, pump did not start in 5 sec #4")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, True, False, True): #5
			self.state_change("error", "Pump running and emergency level True, while level False #5")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, True, False, True): #6
			self.state_change("error", "Pump not running despite both emergency and relay True #6")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, False, False, True) and (self.last_change + 120) > time_module.time(): #7 in-time
			self.state_change("pump running", "Pump running, switchoff after 120 sec #7")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, False, False, True) and (self.last_change + 120) < time_module.time(): #7 in-time
			ah.relay.one.write(False)
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, False, False, True): #8
			self.state_change("error", "Only relay True #8")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, True, True, False): #9
			self.state_change("error", "Pump running without relay True #9")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, True, True, False): #10
			self.state_change("error", "Both levels True, but relay and pump False #10")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, False, True, False): #11
			self.state_change("error", "Pump running without relay True #11")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, False, True, False): #12
			self.state_change("level trigger", "Normal level triggered #12")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, True, False, False): #13
			self.state_change("error", "Pump running without relay True #13")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, True, False, False): #14
			self.state_change("error", "emergency level True #14")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, False, False, False): #15
			self.state_change("error", "Pump running without relay True #15")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, False, False, False) and (self.last_change + 604800) > time_module.time(): #16
			self.state_change("idle", "Everything False, idle #16")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, False, False, False) and (self.last_change + 604800) < time_module.time(): #16
			self.state_change("error", "Idle for over a week #16")
			return
		else:
			self.state_change("error", "No conditions matched in update method")
			return

	def state_change(self, state, cause):
		if self.state != state or self.cause != cause:
			print "{} {} -> {} - {}".format(time_module.strftime("%Y.%m.%d %H:%M"), self.state, state, cause)
			if state == "error":
				self.relay = False
				ah.relay.one.off()
			mail_message_body = "\n".join(["{} {} - {}".format(time_module.strftime("%Y.%m.%d %H:%M", time), state, cause) for time, state, cause in self.past_states])
			print mail_message_body
			self.past_states.append((time_module.time(), state, cause))
			self.state = state
			self.cause = cause
			self.last_change = time_module.time()

pump = PumpState()

while 1:
	try:
		time_module.sleep(0.25)
		pump.update()
	except KeyboardInterrupt:
		ah.relay.one.off()
		exit()
