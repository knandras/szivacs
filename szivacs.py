#!/usr/bin/python
# -*- coding: utf-8 -*-

# Szivacs sump pump control
# inputs:
# 1 - LOW - Pump running
# 2 - LOW - Overflow alert
# 3 - LOW - Level alert

from flask import Flask, render_template, make_response

app = Flask(__name__)

@app.route("/")
def page():
	resp = make_response(render_template('szivacs.html'))
	resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	resp.headers['Expires'] = '0'
	return resp
