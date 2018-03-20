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
@version 2.1.0 10/4/2017
"""

import serial
import time
from cobs import cobs
import cbor2
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_temperature import BrickletTemperature
from random import random

#fixedPoint=16
#sampleTime=1000
#kp=9.5#1.30 0.94 
#ki=10.0#0.0091 #0.0075 0.94 
#kd=187.69 #180.0#187.65
#setPoint=30.000

#kp=0.94
#kp=103.04 #Value was obtained by parameter estimation.
#ki=0.07
#ki=0.50 #Value was obtained by parameter estimation.
#kd=187.69
#kd=2.0
#setPoint=18.500

#Needed for the connection to the temperature bricklet.
#HOST="localhost"
#PORT=4223
#UID="zHg"
#UID="zFZ" #UID for the currently used sensor.
#UID="zih" #UID for the other sensor

#to build the cnnection to the bricklet.
#ipcon = IPConnection()

#t = BrickletTemperature(UID,ipcon)

#ipcon.connect(HOST,PORT)

#Include a part that can read if the entered dict is accoridng the specifications we want. 

class PIDSender:
	def __init__(self, initSerialPort):
		self.host="localhost"
		self.port=4223
		self.uid=0
		self.ipcon=0
		self.tempBricklet=0
		
		self.dataToSend = {}
		
		self.baudRate = 115200
		self.kp = 383.04
		self.ki = 0.50
		self.kd = 2.0
		self.lowerOutputLimit = 0.0
		self.upperOutputLimit = 4095.0
		self.mode = 1
		self.sampleTime = 1000
		self.direction = 0
		self.setpoint = 22.50
		self.output = self.lowerOutputLimit -1 
		#self.controllerIsActive = 1
		
		self.fixedPoint=16
		
		self.serialPort = serial.Serial(initSerialPort,self.baudRate)
		

	def begin(self,*SensorUID,**keyword_parameters):
		if "SensorUID" in keyword_parameters:
			self.uid=SensorUID
			self.ipcon = IPConnection()
			self.tempBricklet = BrickletTemperature(self.uid,self.ipcon)
			self.ipcon.connect(self.host,self.port)
		
		self.serialPort.close()
		if not self.serialPort.isOpen():
			self.serialPort.open()
			print("Serial port opened.")
		else:
			print("Serial port was already open.")
		time.sleep(2) # sleep two seconds to make sure the communication is established.

	#All the setter methods.

	def changeKp(self, newKp):
		if not type(newKp) is float:
			raise(TypeError("Kp must be of type float."))
		intValue=self.fixedPointFloatToInt(newKp)
		if newKp < 0 or intValue > (2**32)-1:
			raise(ValueError("Kp must be greater than 0 and smaller than 32 bit."))
		if not newKp == self.kp:
				self.dataToSend[1]=intValue	

	def changeKi(self, newKi):
		if not type(newKi) is float:
			raise(TypeError("Ki must be of type float."))
		intValue=self.fixedPointFloatToInt(newKi)
		if newKi < 0 or intValue > (2**32)-1:
			raise(ValueError("Ki must be greater than 0 and smaller than 32 bit."))
		if not newKi == self.ki:
				self.dataToSend[2]=intValue

	def changeKd(self, newKd):
		if not type(newKd) is float:
			raise(TypeError("Kp must be of type float."))
		intValue=self.fixedPointFloatToInt(newKd)
		if newKd < 0 or intValue > (2**32)-1:
			raise(ValueError("Kp must be greater than 0 and smaller than 32 bit after fixed point conversion."))
		if not newKd == self.kd:
				self.dataToSend[3]=intValue


	def changeLowerOutputLimit(self, newLowerOutputLimit):
		if not type(newLowerOutputLimit) is float:
			raise(TypeError("Lower output limit must be of type float"))
		if not self.lowerOutputLimit == newLowerOutputLimit:
				self.dataToSend[4]=self.fixedPointFloatToInt(newLowerOutputLimit)

	def changeUpperOutputLimit(self, newUpperOutputLimit):
		if not type(newUpperOutputLimit) is float:
			raise(TypeError("Upper output limit must be of type float"))
		if not self.upperOutputLimit == newUpperOutputLimit:
				self.dataToSend[5]=self.fixedPointFloatToInt(newUpperOutputLimit)

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
		if not newSetpoint == self.kp:
				self.dataToSend[9]=intValue	

	def changeOutput(self, newOutput):
		if not type(newOutput) is float:
			raise(TypeError("Kp must be of type float."))
		intValue=self.fixedPointFloatToInt(newOutput)
		if newOutput < 0 or intValue > (2**32)-1:
			raise(ValueError("Kp must be greater than 0 and smaller than 32 bit."))
		if not newSetpoint == self.kp:
				self.dataToSend[10]=intValue

	def sendTemperature(self):
		temp=self.tempBricklet.get_temperature()/100
		self.serialPort.write(self.encodeWithCobs(cbor2.dumps({0:temp}),'withCBOR'))

	def sendRandomTemperature(self):
		#if the direction is 1 (direct)
		temp=random()
		print(self.direction)
		#print(temp)
		if self.direction==0:
			temp=self.setpoint-10*temp
		#if the direction is 0 (reverse)
		else:
			temp=self.setpoint+10*temp
		print("The random temperature is:",temp)
		#print("Writing data to serial port.")
		self.serialPort.write(self.encodeWithCobs(cbor2.dumps({0:temp}),'withCBOR'))
		#print("Random Temperature was send.")

	#liefert einen bytearray der in COBS codierten Daten.
	#Wird gebrucht als Hilfsfunktion für tobiSender
	def encodeWithCobs(self,data,x):
	#distinguish between CBOR and withour CBOR
		if x=='withCBOR':
			return bytearray(cobs.encode(data)+b'\x00')
		else:
			return bytearray(cobs.encode(bytearray(data))+b'\x00')

	"""
	Converts a given positive floating point number to a uint via fixed point arithmetic.
	The value of the fixed point represents the comma in binary. A fixed point of 16 means 
	that the numbers after the comma has precession of 16 bit. This function raises errors if incorrect values are handed to it.

	@param fixedPoint
		The given fixed point for the conversion, it must be an integer value between 0 and 33.

	@param  floatToConvert
		The floating number that sis converted. It must be choosen according to fixedPoint because we only have 32 bit memory so too large values are prohibited.

	@return
		The uint which belongs to the converted float with respect to the fixed point.
	"""
	def fixedPointFloatToInt(self,floatToConvert):
		return(int(round(floatToConvert*2**(self.fixedPoint),0)))

	def fixedPointIntToFloat(self,intToConvert):
		return(intToConvert/2**(self.fixedPoint))

	#All the getter methods.
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

	#def getControllerActivity(self):
	#	return self.controllerIsActive

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
		print("The mode is: %d" % (self.mode))
		print("The sample time is: %d" % (self.sampleTime))
		print("The direction is: %d" % (self.direction))
		print("The setpoint is: %.2f" % (self.setpoint))
		#print("Controller is active") if self.controllerIsActive else print("Controller is not active")
	
	#Check if upper and lower output limit are send together. If they are not send together than the last value is taken.
	def sendNewValues(self):
		if 4 in self.dataToSend and 5 in self.dataToSend and self.dataToSend[4] >= self.dataToSend[5]:
			raise(ValueError("The upper output limit must be greater than the lower output limit."))
		if 4 in self.dataToSend and not 5 in self.dataToSend and self.dataToSend[4] >= self.upperOutputLimit:
			raise(ValueError("The upper output limit must be greater than the lower output limit."))
		if not 4 in self.dataToSend and 5 in self.dataToSend and self.dataToSend[5] <= self.lowerOutputLimit:
			raise(ValueError("The upper output limit must be greater than the lower output limit."))

		if 10 in self.dataToSend and 6 in self.dataToSend and self.dataToSend[6]==1:
			raise(ValueError("You can only write an output when the controller mode is 0."))
		if 10 in self.dataToSend and not 6 in self.dataToSend and self.mode==1:
			raise(ValueError("You can only write an output when the controller mode is 0."))

		if 6 in self.dataToSend and self.dataToSend[6]==1 and self.mode==0:
			self.dataToSend[10]=0

		encodedData=self.encodeWithCobs(cbor2.dumps(self.dataToSend),'withCBOR')
		encodedLength=len(encodedData)
		if encodedLength > 255:
			raise OverflowError("The length of the encoded data package is "+str(encodedLength)+". It must be smaller than 255 bytes")

		print("Trying to write data on serial port.")
		self.serialPort.write(encodedData)
		print("Data written to port.")

		for key in self.dataToSend:
			if key==1:
				self.kp=self.fixedPointIntToFloat(self.dataToSend[1])
			elif key==2:
				self.ki=self.fixedPointIntToFloat(self.dataToSend[2])
			elif key==3:
				self.kd=self.fixedPointIntToFloat(self.dataToSend[3])
			elif key==4:
				self.lowerOutputLimit=self.fixedPointIntToFloat(self.dataToSend[4])
			elif key==5:
				self.upperOutputLimit=self.fixedPointIntToFloat(self.dataToSend[5])
			elif key==6:
				self.mode=self.dataToSend[6]
			elif key==7:
				self.sampleTime=self.dataToSend[7]
			elif key==8:
				self.direction=self.dataToSend[8]
			elif key==9:
				self.setpoint=self.fixedPointIntToFloat(self.dataToSend[9])
			elif key==10:
				self.output=self.fixedPointIntToFloat(self.dataToSend[10])

		if encodedLength >= 100:
			time.sleep(encodedLength/1200)
		return True


	"""
	Sends a dict via serial communication to the Arduino. For more information which keys are connected to which parameters take a look in the file readMe.txt.
	The serialization of the data is ensured by COBS and CBOR. Before the data is send it is checked that the dict fullfills the properties to be read by the Arduino.
	If a part of the dict is not proper the function will raise an error.

	@param dictToEncode
		The dict that will be send, it should be smaller than 100 bytes in the encoded form, because the serial buffer of the Arduino only has 64 bytes.
		If it is larger and two large dict are send quickly after each other data will be lost. Furhtermore the number of encoded bytes mustn't be larger
		than 255 bytes due to the COBS algorithm.

	@param serialPort
		The serial port over which the data is send, must be initialzed before this function is called and one must wait about 2 seconds before the dat can be send because the
		Arduino needs some time to respond. For this pyserial is recommended. 

	@param fixedPoint
		Double which are written in dictToEncode are converted to uints using fixed point arithmetic. The recommend value is 16.


	
	def sendIntData(self,dictToEncode):

		encodedLength=len(self.encodeWithCobs(cbor2.dumps(dictToEncode),'withCBOR'))

		#Get's tested.
		if not type(dictToEncode) is dict:
			raise TypeError("The data to encode must be of type dict.")

		#Get's tested 
		if not type(self.fixedPoint) is int:
			raise TypeError("The fixed point value must be of type int.")

		#Get's tested.
		if 0 > self.fixedPoint or 32 < self.fixedPoint:
			raise ValueError("The fixed point is "+str(self.fixedPoint)+", but it must between 0 and 32.")

		#Get's tested.
		if encodedLength > 255:
			raise OverflowError("The length of the encoded data package is "+str(encodedLength)+". It must be smaller than 255 bytes")

		#keyFlag=True
		#valueFlag=True

		for key in dictToEncode:
			
			#Both get's tested.
			if (not type(key) is int) or key > 10 or key < 0:
				raise KeyError(str(key)+" is not a valid key. All keys must be integers betwenn 0 and 10.")

			if (key==0 or key==1 or key==2 or key==3 or key==4 or key==5 or key==9 or key==10):
				if type(dictToEncode[key]) is float:
					value=dictToEncode[key]
					dictToEncode[key]=self.fixedPointFloatToInt(dictToEncode[key])

					#get's tested
					if dictToEncode[key] >  4294967295 or dictToEncode[key] < 0:
						raise ValueError(str(value)+" is no valid value, after the fixed point conversion the value must be smaller than 4294967295 and greater than 0.")

				#get's tested
				else:
					print(type(dictToEncode[key]))
					raise TypeError("The value of the key "+str(key)+" must be a float.")
		#Get's tested.
		if 6 in dictToEncode and (not type(dictToEncode[6]) is int):
			raise TypeError("The type of the mode must be int.")

		#Get's tested.
		if 6 in dictToEncode and not(dictToEncode[6]==0 or dictToEncode[6]==1):
			raise ValueError("The mode (key 6) must be either 0 for MANUAL or 1 for AUTOMATIC.")

		#not tested yet.
		if 6 in dictToEncode and dictToEncode[6]==0:
			#global controllerIsActive
			self.controllerIsActive=False

		#Not tested yet.
		if 6 in dictToEncode and dictToEncode[6]==1:
			#global controllerIsActive
			self.controllerIsActive=True

		#Get's tested.
		if 7 in dictToEncode: 
			#Get's tested.
			if not type(dictToEncode[7]) is int:
				raise TypeError("The sample time (key 7) must be of type int.")
			#Get's tested.
			if dictToEncode[7]>=4294967295 or dictToEncode[7]<0:
				raise ValueError("The given sample time is "+str(dictToEncode[7])+" is invalid. It must be smaller than 4294967296 and bigger than 0.")

		#Get's tested.
		if 8 in dictToEncode and (not type(dictToEncode[8]) is int): #and (not type(dictToEncode[8]) is int):
			raise TypeError("The type of the direction must be int.")

		#Get's tested.
		if 8 in dictToEncode and not (dictToEncode[8]==0 or dictToEncode[8]==1):
			raise ValueError("The direction (key 8) must be either 0 for DIRECT or 1 for REVERSE.")


		#Get's tested.
		if not 0 in dictToEncode and self.controllerIsActive:
			raise KeyError("No input (key 0) in dict. Every loop must contain an input when the controller is enabled.")

		#Not tested yet.
		if 10 in dictToEncode and self.controllerIsActive:
			raise KeyError("The controller must be disabled to write an output.")

		#Not tested yet.
		if not 10 in dictToEncode and 6 in dictToEncode and dictToEncode[6]==0:
			raise KeyError("When you disable the controller (mode 6 = 0), you have to write an output (key).")

		#if 0 in dictToEncode and 10 in dictToEncode:
		#	raise KeyError("An input and an output can't be send together.")

		#Get's tested.
		if (4 in dictToEncode and not 5 in dictToEncode) or (5 in dictToEncode and not 4 in dictToEncode):
			raise KeyError("Upper and lower output limits must be passed together.")

		#Get's tested.
		elif 4 in dictToEncode and 5 in dictToEncode and dictToEncode[4] >= dictToEncode[5]:
			raise ValueError("The upper output limit must be greater than the lower output limit.")

		#Serialize the data.
		self.serialPort.write(self.encodeWithCobs(cbor2.dumps(dictToEncode),'withCBOR'))
		#print(dictToEncode)
		#If the data package is too large the function must be slept to prevent the Arduino from loosing data, because it comes in too fast.
		
				
		for key in dictToEncode:
			if key==1:
				self.kp=dictToEncode[1]
			elif key==2:
				self.ki=dictToEncode[2]
			elif key==3:
				self.ki=dictToEncode[3]
			elif key==4:
				self.lowerOutputLimit=dictToEncode[4]
			elif key==5:
				self.lowerOutputLimit=dictToEncode[5]
			#elif key==6:
			#	self.mode=dictToEncode[6]
			elif key==7:
				self.sampleTime=dictToEncode[7]
			elif key==8:
				self.direction=dictToEncode[8]
			elif key==9:
				self.setpoint=dictToEncode[9]

		if encodedLength >= 100:
			time.sleep(encodedLength/1200)
		return True
		"""