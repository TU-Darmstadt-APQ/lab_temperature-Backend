#!/usr/bin/python3

import os
#import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from wtforms import Form, BooleanField, StringField, DecimalField, IntegerField, PasswordField, validators
from flask_wtf import FlaskForm
from arduino_python_communication_v3 import *


app = Flask(__name__) # create the application instance :)
app.config["SECRET_KEY"]= "secretKey"

class controllerInterfaceForm(FlaskForm):
	kp=DecimalField("kp")
	ki=DecimalField("ki")
	kd=DecimalField("kd")
	lowerOutputLimit=DecimalField("lowerOutputLimit")
	upperOutputLimit=DecimalField("upperOutputLimit")
	mode=IntegerField("mode")
	sampleTime=IntegerField("sampleTime")
	direction=IntegerField("direction")
	setpoint=DecimalField("setpoint")
	output=DecimalField("output")


controller = PIDSender('/dev/ttyACM0')
controller.begin()


@app.route("/formTest",methods=["post","get"])
def formTest():

	form=controllerInterfaceForm()

	if form.kp.data != None:
		controller.changeKp(float(form.kp.data))

	if form.ki.data != None:
		controller.changeKi(float(form.ki.data))

	if form.kd.data != None:
		controller.changeKd(float(form.kd.data))

	if form.lowerOutputLimit.data != None:
		controller.changeLowerOutputLimit(float(form.lowerOutputLimit.data))

	if form.upperOutputLimit.data != None:
		controller.changeUpperOutputLimit(float(form.upperOutputLimit.data))

	if form.mode.data != None:
		controller.changeMode(int(form.mode.data))

	if form.sampleTime.data != None:
		controller.changeSampleTime(int(form.sampleTime.data))

	if form.direction.data != None:
		controller.changeDirection(int(form.direction.data))

	if form.setpoint.data != None:
		controller.changeSetpoint(float(form.setpoint.data))

	if form.output.data != None:
		#print(form.output.data)
		controller.changeOutput(float(form.output.data))

	if bool(controller.getBuffer()):
		controller.sendNewValues()

	return(render_template("form_test.html",form=form))

"""
@app.route("/sendSuccessfull")
def sendSuccessfull():
	return(render_template("sendSuccessfull.html",form=form))


@app.route("/home")
def home():
	return render_template("home.html")

@app.route("/home",methods=["POST"])
def handle_data():
	newKp=request.form["newKp"]
	newKi=request.form["newKi"]
	#print(1+2)
	print(newKi==None)
	return render_template("home.html")


@app.route("/<hurensohn>")
def hurensohn(hurensohn):
	return("huso %s") % hurensohn
"""
if __name__ == "__main__":
	app.run(host="0.0.0.0",debug=True)
