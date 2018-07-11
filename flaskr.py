#!//home/tobias/anaconda3/bin/python3

import os
#import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from wtforms import Form, BooleanField, StringField, DecimalField, IntegerField, PasswordField, validators
from flask_wtf import FlaskForm
from arduino_python_communication_v3 import *
from recieve_data import controller

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


#controller = PIDSender('/dev/ttyACM0')
controller.begin()


@app.route("/",methods=["post","get"])
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

	if form.sampleTime.data != None:
		controller.changeSampleTime(int(form.sampleTime.data))

	if form.setpoint.data != None:
		controller.changeSetpoint(float(form.setpoint.data))

	if form.output.data != None:
		#print(form.output.data)
		if controller.getMode()==0:
			controller.changeOutput(float(form.output.data))
		else:
			pass

	if request.form.get("mode") == "AUTOMATIC":
		controller.changeMode(int(1))
	elif request.form.get("mode") == "MANUAL":
		controller.changeMode(int(0))
	else:
		pass

	if request.form.get("direction") == "REVERSE":
		controller.changeDirection(int(1))
	elif request.form.get("direction") == "DIRECT":
		controller.changeDirection(int(0))
	else:
		pass

	if bool(controller.getBuffer()):
		controller.sendNewValues()

	kpValue="%.2f" % (controller.getKp())
	kiValue="%.2f" % (controller.getKi())
	kdValue="%.2f" % (controller.getKd())
	lowerOutputLim="%.2f" % (controller.getLowerOutputLimit())
	upperOutputLim="%.2f" % (controller.getUpperOutputLimit())
	sampleTimeValue=controller.getSampleTime()
	setpointValue="%.2f" % (controller.getSetpoint())
	outputValue="%.2f" % (controller.getOutput())
	
	checkModeDisabled=0
	checkModeEnabled=0
	checkDirectionDirect=0
	checkDirectionReversed=0

	if controller.getMode()==0:
		modeValue="manual"
		checkModeDisabled="true"
		checkModeEnabled="false"
	else:
		modeValue="automatic"
		checkModeDisabled="false"
		checkModeEnabled="true"

	if controller.getDirection()==0:
		directionValue="direct"
		checkDirectionDirect="true"
		checkDirectionReversed="false"
	else:
		directionValue="reverse"
		checkDirectionDirect="false"
		checkDirectionReversed="true"

	return(render_template("form_test.html",form=form,checkModeDisabled=checkModeDisabled,checkModeEnabled=checkModeEnabled,checkDirectionReversed=checkDirectionReversed,checkDirectionDirect=checkDirectionDirect,kpValue=kpValue,kiValue=kiValue,kdValue=kdValue,lol=lowerOutputLim,uol=upperOutputLim,setpointValue=setpointValue,sampleTimeValue=sampleTimeValue,outputValue=outputValue,modeValue=modeValue,directionValue=directionValue))

if __name__ == "__main__":
	app.run(debug=True)
