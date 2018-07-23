#!/usr/bin/python
# -*- coding: utf-8 -*-

# Szivacs szivattyúvezérlés
# Bemenetek:
# 1 - LOW - Szivattyú müködés
# 2 - LOW - Vésszint jelző
# 3 - LOW - Szint jelző

import automationhat
from flask import Flask, render_template, make_response
app = Flask(__name__)

@app.route("/")
def page():
	resp = make_response(render_template('szivacs.html'))
	resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	resp.headers['Expires'] = '0'
	return resp
