"""
# ##### BEGIN GPL LICENSE BLOCK #####
#
# Copyright (C) 2017  Tobias Liebmann
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

@author Tobias Liebmann
@version 2.0.0 03/26/2017
"""

#Build a serial communication
import serial
#To save the time in the log file
import time
#For COBSing stuff
from cobs import cobs
#For CBORing the COBSed stuff
import cbor2
#To get the temperature data
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_temperature import BrickletTemperature
#To send temperature without a Tinkerforge sensor
from random import random
#To check if a settings.txt file exists
import os.path
import os
 

#Constructor of the PIDSender class. Only takes the device directory of the controller as input (e.g. /dev/ttyACM0).
class PIDSender:
	def __init__(self, initSerialPort):
		#Stuff that is needed to build a connection with the temperature bricklet.
		self.host="localhost"
		self.port=4223
		self.uid=0
		self.ipcon=0
		self.tempBricklet=0
		
		#The data that will be send is saved in this dict.
		self.dataToSend = {}
		
		#Baudrate of the communication.
		self.baudRate = 115200
		
		#Initale values of the PID controller.
		self.kp = 0.0
		self.ki = 0.0
		self.kd = 0.0
		self.lowerOutputLimit = 0.0
		self.upperOutputLimit = 4095.0
		self.mode = 1
		self.sampleTime = 1000
		self.direction = 0
		self.setpoint = 22.50
		self.output = -1.0

		#List of the settings that are saved in the settings.txt file.
		self.settingsList=[str(self.kp)+"\n",str(self.ki)+"\n",str(self.ki)+"\n",str(self.lowerOutputLimit)+"\n",str(self.upperOutputLimit)+"\n",str(self.mode)+"\n",str(self.sampleTime)+"\n",str(self.direction)+"\n",str(self.setpoint)+"\n",str(self.output)]
		
		#Floating point numbers send as integers using fixed point arithmetic.
		self.fixedPoint=16
		
		#Serial port used for the communication.
		self.serialPort = serial.Serial(initSerialPort,self.baudRate)
	
	#Before a communciation can be established the begin()-method has to be called.
	#It takes an optional parameter which is the UID of the Tinkerforge temperature sensor (e.g. "zih").
	def begin(self,*SensorUID,**keyword_parameters):
		#The settings are saved in a settings.txt file.
		#If the settings file does not exist, we have to create one.
		if not os.path.exists("settings.txt"):
			print("Have to create a file.")
			#Open and closing the file with the parameter "w" will create a new file.
			settings=open("settings.txt","w")
			#Write the initiale values in the file.
			settings.writelines(self.settingsList)
			settings.close()

		#If no file has to be created. We read the already existing file to get the same
		#settings as in the last session where the controller was used.
		settings=open("settings.txt","r")
		self.settingsList=settings.readlines()
		self.kp=float(self.settingsList[0][:-1])
		self.ki=float(self.settingsList[1][:-1])
		self.kd=float(self.settingsList[2][:-1])
		self.lowerOutputLimit=float(self.settingsList[3][:-1])
		self.upperOutputLimit=float(self.settingsList[4][:-1])
		self.mode=int(self.settingsList[5][:-1])
		self.sampleTime=int(self.settingsList[6][:-1])
		self.direction=int(self.settingsList[7][:-1])
		self.setpoint=float(self.settingsList[8][:-1])
		self.output=float(self.settingsList[9][:-1])
		settings.close()

		#Start the connection with the Tinkerforge sensor
		if "SensorUID" in keyword_parameters:
			self.uid=keyword_parameters["SensorUID"]
			self.ipcon = IPConnection()
			self.tempBricklet = BrickletTemperature(self.uid,self.ipcon)
			self.ipcon.connect(self.host,self.port)
		
		#self.serialPort.close()
		#Open the serial port if it was not open already.
		if not self.serialPort.isOpen():
			self.serialPort.open()
			print("Serial port opened.")
		else:
			print("Serial port was already open.")
		time.sleep(2) # sleep two seconds to make sure the communication is established.

	#All the setter methods.

	"""
	The following methods are all needed to change the parameters of the controller.
	They are mostly the same the only difference is if they take floating point numbers or integers as input.
	These methods work as follows.
	-floating point numbers:
		1.The type of the input is checked if it is not of type float an error is thrown.
		2.The given float is converted to a fixedpoint unit.
		3.It is checked if the resulting integer is too big (larger than 32 bit) or smaller than zero, if thi is the
		  case an error is thrown.
		4.It is checked if the entered value is the same as the current value, if this is not the case the integer
		  is added to the dataToSend dictonary with the according key.
	-integer values:
		Works the same as the floating point values without the conversion at the beginning.
	"""
	def reset(self):
		if os.path.exists("settings.txt"):
			os.remove("settings.txt")
			print("The existing settings file was removed.")
		else:
			print("Couldn't reset the controller. No settings file has been created.")

	def changeKp(self, newKp):
		if not type(newKp) is float:
			raise(TypeError("Kp must be of type float."))
		intValue=self.fixedPointFloatToInt(newKp)
		if newKp < 0 or intValue > (2**32)-1:
			raise(ValueError("Kp must be greater than 0 and smaller than 32 bit."))
		if not intValue == self.fixedPointFloatToInt(self.kp):
			self.dataToSend[1]=intValue

	def changeKi(self, newKi):
		if not type(newKi) is float:
			raise(TypeError("Ki must be of type float."))
		intValue=self.fixedPointFloatToInt(newKi)
		if newKi < 0 or intValue > (2**32)-1:
			raise(ValueError("Ki must be greater than 0 and smaller than 32 bit."))
		if not intValue == self.fixedPointFloatToInt(self.ki):
			self.dataToSend[2]=intValue

	def changeKd(self, newKd):
		if not type(newKd) is float:
			raise(TypeError("Kp must be of type float."))
		intValue=self.fixedPointFloatToInt(newKd)
		if newKd < 0 or intValue > (2**32)-1:
			raise(ValueError("Kp must be greater than 0 and smaller than 32 bit after fixed point conversion."))
		if not intValue == self.fixedPointFloatToInt(self.kd):
			self.dataToSend[3]=intValue


	def changeLowerOutputLimit(self, newLowerOutputLimit):
		if not type(newLowerOutputLimit) is float:
			raise(TypeError("Lower output limit must be of type float"))
		intValue=self.fixedPointFloatToInt(newLowerOutputLimit)
		if not self.fixedPointFloatToInt(self.lowerOutputLimit) == intValue:
			self.dataToSend[4]=intValue

	def changeUpperOutputLimit(self, newUpperOutputLimit):
		if not type(newUpperOutputLimit) is float:
			raise(TypeError("Upper output limit must be of type float"))
		intValue=self.fixedPointFloatToInt(newUpperOutputLimit)
		if not self.fixedPointFloatToInt(self.upperOutputLimit) == intValue:
			self.dataToSend[5]=intValue

	def changeMode(self, newMode):
		if not (newMode==1 or newMode==0):
			raise(ValueError("The mode must be either 0 or 1."))
		if not self.mode==newMode:
			self.dataToSend[6]=newMode

	def changeSampleTime(self, newSampleTime):
		if not type(newSampleTime) is int:
			raise TypeError("The sample time must be of type int.")
		if newSampleTime < 0 or newSampleTime > (2**32) -1:
			raise ValueError("the sample time must be an unsigned int with a maximal length of 32 Bit.")
		if not self.sampleTime==newSampleTime:
			self.dataToSend[7]=newSampleTime

	def changeDirection(self, newDirection):
		if not (newDirection==1 or newDirection==0):
			raise(ValueError("The direction must be either 0 or 1."))
		if not self.direction==newDirection:
			self.dataToSend[8]=newDirection

	def changeSetpoint(self, newSetpoint):
		if not type(newSetpoint) is float:
			raise(TypeError("Kp must be of type float."))
		intValue=self.fixedPointFloatToInt(newSetpoint)
		if newSetpoint < 0 or intValue > (2**32)-1:
			raise(ValueError("Kp must be greater than 0 and smaller than 32 bit."))
		if not intValue == self.fixedPointFloatToInt(self.setpoint):
			self.dataToSend[9]=intValue	

	def changeOutput(self, newOutput):
		if not type(newOutput) is float:
			raise(TypeError("Kp must be of type float."))
		intValue=self.fixedPointFloatToInt(newOutput)
		if newOutput < 0 or intValue > (2**32)-1:
			raise(ValueError("Kp must be greater than 0 and smaller than 32 bit."))
		if not intValue == self.fixedPointFloatToInt(self.output):
			self.dataToSend[10]=intValue

	#Method to send the temperature of the Tinkerforge Bricklet to the controller.
	def sendTemperature(self):
		temp=self.tempBricklet.get_temperature()/100
		self.serialPort.write(self.encodeWithCobs(cbor2.dumps({0:self.fixedPointFloatToInt(temp)}),'withCBOR'))
		return(temp)

	#Sends a random temperature to the controller.
	#No connection with a Tinkerforge bricklet is needed for this method to work.
	#This method is mostly used for testing the communication between the controller and the Computer.
	def sendRandomTemperature(self):
		temp=random()
		#if the direction is 1 (direct)
		if self.direction==0:
			temp=self.setpoint-10*temp
		#if the direction is 0 (reverse)
		else:
			temp=self.setpoint+10*temp
		self.serialPort.write(self.encodeWithCobs(cbor2.dumps({0:self.fixedPointFloatToInt(temp)}),'withCBOR'))
		return(temp)

	#Sends a specific temperature to controller that the user acn choose.
	def sendManualTemperature(self,inputTemperature):
		self.serialPort.write(self.encodeWithCobs(cbor2.dumps({0:self.fixedPointFloatToInt(inputTemperature)}),'withCBOR'))		

	#Method to encode given data with cobs.
	#Takes two parameters as input:
	#	-data: The data that should be encoded.
	#	-x: If x equals "withCBOR" the method does not convert the input data to byte array before encding it.
	def encodeWithCobs(self,data,x):
	#distinguish between CBOR and withour CBOR
		if x=='withCBOR':
			return bytearray(cobs.encode(data)+b'\x00')
		else:
			return bytearray(cobs.encode(bytearray(data))+b'\x00')

	#Takes a number as input and returns the according value in fixed point arithmetic.
	def fixedPointFloatToInt(self,floatToConvert):
		return(int(round(floatToConvert*2**(self.fixedPoint),0)))

	#Takes a number that was converted with fixed point arithmetic as input and returns the original number.
	def fixedPointIntToFloat(self,intToConvert):
		return(intToConvert/2**(self.fixedPoint))

	"""
	All the getter methods.
	"""
	def getKp(self):
		return self.kp

	def getKd(self):
		return self.kd

	def getKi(self):
		return self.ki

	def getLowerOutputLimit(self):
		return self.lowerOutputLimit

	def getUpperOutputLimit(self):
		return self.upperOutputLimit

	def getMode(self):
		return self.mode

	def getSampleTime(self):
		return self.sampleTime

	def getDirection(self):
		return self.direction

	def getSetpoint(self):
		return self.setpoint

	def getOutput(self):
		return self.output

	def getFixedPoint(self):
		return self.fixedPoint

	def getBaudRate(self):
		return self.baudRate

	def getTemperature(self):
		return self.tempBricklet.get_temperature()/100

	def getBuffer(self):
		return self.dataToSend

	#This method is here to print all the current settings of the controller to the console.
	def printEverything(self):
		print("The value of Kp is: %.2f" % (self.kp))
		print("The value of Ki is: %.2f" % (self.ki))
		print("The value of Kd is: %.2f" % (self.kd))
		print("The lower output limit is: %.2f" % (self.lowerOutputLimit))
		print("The upper output limit is: %.2f" % (self.upperOutputLimit))
		print("The mode is: ",self.mode)
		print("The sample time is: ",self.sampleTime)
		print("The direction is: ",self.direction)
		print("The setpoint is: %.2f" % (self.setpoint))

	"""
	This method is were the magic happens.
	After the methods to change the parameters are called one has to call this function to send the dict with 
	the new values.
	First a test is performed if new upper and lower output limits are in the dict. If this is the case it is checked
	if the lower output limit is smaller than the upper output limit, if this is the case an error is thrown.

	After that a test is performed to see if an output was written without the controller beginning turned of.

	Next the dict dataToSend is encoded and it is checked if the length is smaller than 255 bytes.
	
	After that the changed data is written in to the settings.txt file and the data is send to the controller.
	
	In the last step the values of the controller are updated, the dict is reset and the method returns true if no errors
	have occured.   
	"""
	def sendNewValues(self):
		if 4 in self.dataToSend and 5 in self.dataToSend and self.dataToSend[4] >= self.dataToSend[5]:
			raise(ValueError("The upper output limit must be greater than the lower output limit."))
		
		if 4 in self.dataToSend and not 5 in self.dataToSend:
			if self.dataToSend[4] >= self.fixedPointFloatToInt(self.upperOutputLimit):
				raise(ValueError("The upper output limit must be greater than the lower output limit."))
			else:
				intValue=self.fixedPointFloatToInt(self.upperOutputLimit)
				self.dataToSend[5]=intValue	

		if not 4 in self.dataToSend and 5 in self.dataToSend:
			if self.dataToSend[5] <= self.fixedPointFloatToInt(self.lowerOutputLimit):
				raise(ValueError("The upper output limit must be greater than the lower output limit."))
			else:
				intValue=self.fixedPointFloatToInt(self.lowerOutputLimit)
				self.dataToSend[4]=intValue	

		if 10 in self.dataToSend and 6 in self.dataToSend and self.dataToSend[6]==1:
			raise(ValueError("You can only write an output when the controller mode is 0."))
		if 10 in self.dataToSend and not 6 in self.dataToSend and self.mode==1:
			raise(ValueError("You can only write an output when the controller mode is 0."))


		encodedData=self.encodeWithCobs(cbor2.dumps(self.dataToSend),'withCBOR')
		encodedLength=len(encodedData)
		if encodedLength > 255:
			raise OverflowError("The length of the encoded data package is "+str(encodedLength)+". It must be smaller than 255 bytes")

		self.serialPort.write(encodedData)

		settings=open("settings.txt","r+")
		self.settingsList=settings.readlines()
		for key in self.dataToSend:
			if key==1:
				self.kp=self.fixedPointIntToFloat(self.dataToSend[1])
				self.settingsList[0]=str(self.kp)+"\n"
			elif key==2:
				self.ki=self.fixedPointIntToFloat(self.dataToSend[2])
				self.settingsList[1]=str(self.ki)+"\n"
			elif key==3:
				self.kd=self.fixedPointIntToFloat(self.dataToSend[3])
				self.settingsList[2]=str(self.kd)+"\n"
			elif key==4:
				self.lowerOutputLimit=self.fixedPointIntToFloat(self.dataToSend[4])
				self.settingsList[3]=str(self.lowerOutputLimit)+"\n"
			elif key==5:
				self.upperOutputLimit=self.fixedPointIntToFloat(self.dataToSend[5])
				self.settingsList[4]=str(self.upperOutputLimit)+"\n"
			elif key==6:
				self.mode=self.dataToSend[6]
				self.settingsList[5]=str(self.mode)+"\n"
			elif key==7:
				self.sampleTime=self.dataToSend[7]
				self.settingsList[6]=str(self.sampleTime)+"\n"
			elif key==8:
				self.direction=self.dataToSend[8]
				self.settingsList[7]=str(self.direction)+"\n"
			elif key==9:
				self.setpoint=self.fixedPointIntToFloat(self.dataToSend[9])
				self.settingsList[8]=str(self.setpoint)+"\n"
			elif key==10:
				self.output=self.fixedPointIntToFloat(self.dataToSend[10])
				self.settingsList[9]=str(self.output)
		settings.close()

		self.dataToSend={}
		
		with open("settings.txt","w") as settings:
			#print(self.settingsList)
			settings.writelines(self.settingsList)

		if encodedLength >= 100:
			time.sleep(encodedLength/1200)
		return True