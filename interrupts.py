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
		self.cause = "Startup"
		self.prevstate = (self.pump, self.emergency, self.level, self.state, self.cause)
		print "{} Started input polling.".format(strftime("%Y.%m.%d %H:%M"))

	def update(self):
		self.prevstate = (self.pump, self.emergency, self.level, self.state)
		self.pump = not(ah.input.one.read())
		self.emergency = not(ah.input.two.read())
		self.level = not(ah.input.three.read())

		# normal states
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
