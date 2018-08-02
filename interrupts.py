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
		self.state = ""
		self.past_states = deque([], 10)
		self.cause = ""
		self.state_change("idle", "Startup")

	def update(self):
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
		elif (self.pump, self.emergency, self.level, self.relay) == (False, False, True, True) and (self.last_change + 5) < time_module.time(): #4 timeout
			self.state_change("error", "Relay just closed, pump did not start in 5 sec #4")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, True, False, True): #5
			self.state_change("error", "Pump running and emergency level True, while level False #5")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, True, False, True): #6
			self.state_change("error", "Pump not running despite both emergency and relay True #6")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, False, False, True) and (self.last_change + 20) > time_module.time(): #7 in-time
			self.state_change("pump running", "Pump running, switchoff after 120 sec #7")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, False, False, True) and (self.last_change + 20) < time_module.time(): #7 in-time
			self.state_change("pump stopping", "Pump has exceeded switchoff time limit. #7")
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
		if (self.state != "error") or (self.state == "error" and state == "idle") or ((self.state == "error" and state == "error") and self.cause != cause):
			if state in ["error", "pump stopping"]:
				self.relay = False
			elif state in ["level trigger"]:
				self.relay = True
			ah.relay.one.write(self.relay)
			if self.state != state or self.cause != cause:
				print "{} {} -> {} - {}".format(time_module.strftime("%Y.%m.%d %H:%M"), self.state, state, cause)
				self.state = state
				self.cause = cause
				self.last_change = time_module.time()
				self.past_states.append((time_module.localtime(), state, cause))

				# mail_message_body = "\n".join(["\t{} {} - {}".format(time_module.strftime("%Y.%m.%d %H:%M", m_time), m_state, m_cause) for m_time, m_state, m_cause in self.past_states])
				# print mail_message_body

pump = PumpState()

try:
	while 1:
		time_module.sleep(1)
		pump.update()
except KeyboardInterrupt:
	ah.relay.one.off()
	print ""
	exit()
