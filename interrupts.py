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
from time import sleep, time, strftime
from collections import deque

pin_state = dict()
pin_state["1"] = False
pin_state["2"] = False
pin_state["3"] = False
pin_state["R"] = False

class PumpState():
	def __init__(self):
		self.pump = False
		self.emergency = False
		self.level = False
		self.relay = False
		self.last_change = time()
		self.state = "idle"
		self.past_states = deque(10)
		self.cause = "Startup"
		self.prevstate = (self.pump, self.emergency, self.level, self.state, self.cause)
		print "{} Started input polling.".format(strftime("%Y.%m.%d %H:%M"))

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
		elif (self.pump, self.emergency, self.level, self.relay) == (True, False, True, True) and (self.last_change + 30) > time(): #3 in-time
			self.state_change("pump start running", "Pump just started, level should clear in 30 sec #3")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, False, True, True) and (self.last_change + 30) < time(): #3 timeout
			self.state_change("error", "Pump just started, level did not clear in 30 sec #3")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, False, True, True) and (self.last_change + 5) > time(): #4 in-time
			self.state_change("pump start", "Relay just closed, pump should start in 5 sec #4")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, False, True, True) and (self.last_change + 5) > time(): #4 timeout
			self.state_change("error", "Relay just closed, pump did not start in 5 sec #4")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, True, False, True): #5
			self.state_change("error", "Pump running and emergency level True, while level False #5")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, True, False, True): #6
			self.state_change("error", "Pump not running despite both emergency and relay True #6")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, False, False, True) and (self.last_change + 120) > time(): #7 in-time
			self.state_change("pump running", "Pump running, switchoff after 120 sec #7")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (True, False, False, True) and (self.last_change + 120) < time(): #7 in-time
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
		elif (self.pump, self.emergency, self.level, self.relay) == (False, False, False, False) and (self.last_change + 604800) > time(): #16
			self.state_change("idle", "Everything False, idle #16")
			return
		elif (self.pump, self.emergency, self.level, self.relay) == (False, False, False, False) and (self.last_change + 604800) < time(): #16
			self.state_change("error", "Idle for over a week #16")
			return
		else:
			self.state_change("error", "No conditions matched in update method")
			return


"""		# normal states
		if not(self.pump) and not(self.emergency) and not(self.level) and not(self.relay):
			self.state_change("idle", "idle")

		if self.level and self.state == "idle":
			self.state_change("level triggered", "Alert from level sensor.")
			self.relay = True

		if self.level and self.state == "level triggered" and self.relay:
			self.state_change("pump started", "Relay swithed on because of level alert.")

		# error states
		if self.pump and not(self.relay):
			self.state_change("error", "Pump running without signal.")

		# timed states
		if self.state == "pump started" and float(self.last_change + 5) < time():
			self.state_change("error", "Pump failed to start.")
		elif self.state == "pump running with level" and float(self.last_change + 15) < time():
			self.state_change("error", "Pump started, but level does not decrease.")

"""
		ah.relay.one.write(self.relay)

	def state_change(self, state, cause):
		if self.state != state or self.cause != cause:
			print "{} {} -> {} - {}".format(strftime("%Y.%m.%d %H:%M"), self.state, state, cause)
			if state == "error":
				self.relay = False
				ah.relay.one.off()
			self.state = state
			self.cause = cause
			self.last_change = time()

pump = PumpState()

while 1:
	try:
		sleep(0.25)
		pump.update()
	except KeyboardInterrupt:
		ah.relay.one.off()
		exit()
