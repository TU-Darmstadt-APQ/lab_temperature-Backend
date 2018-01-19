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

fixedPoint=16
sampleTime=1000
#kp=9.5#1.30 0.94 
#ki=10.0#0.0091 #0.0075 0.94 
#kd=187.69 #180.0#187.65
#setPoint=30.000

#kp=0.94
kp=383.04 #Value was obtained by parameter estimation.
#ki=0.07
ki=0.50 #Value was obtained by parameter estimation.
#kd=187.69
kd=2.0
setPoint=22.500

controllerIsActive=True
#isFirstTime=True

#Needed for the connection to the temperature bricklet.
HOST="localhost"
PORT=4223
UID="zHg"
#UID="zFZ" #UID for the currently used sensor.
#UID="zih" #UID for the other sensor

#Include a part that can read if the entered dict is accoridng the specifications we want. 

#s = serial.Serial('/dev/ttyACM0', 115200) # Namen ggf. anpassen
#time.sleep(0) # der Arduino resettet nach einer Seriellen Verbindung, daher muss kurz gewartet werden (sleep nimmt als Eingabe Sekunden)


#liefert einen bytearray der in COBS codierten Daten.
#Wird gebrucht als Hilfsfunktion für tobiSender
def encodeWithCobs(data,x):
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
def fixedPointFloatToInt(fixedPoint,floatToConvert):
	return(int(round(floatToConvert*2**(fixedPoint),0)))


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


"""
def sendIntData(dictToEncode,serialPort,fixedPoint):
	global controllerIsActive

	encodedLength=len(encodeWithCobs(cbor2.dumps(dictToEncode),'withCBOR'))

	#Get's tested.
	if not type(dictToEncode) is dict:
		raise TypeError("The data to encode must be of type dict.")

	#Get's tested 
	if not type(fixedPoint) is int:
		raise TypeError("The fixed point value must be of type int.")

	#Get's tested.
	if 0 > fixedPoint or 32 < fixedPoint:
		raise ValueError("The fixed point is "+str(fixedPoint)+", but it must between 0 and 32.")

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
				dictToEncode[key]=fixedPointFloatToInt(fixedPoint,dictToEncode[key])

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
		controllerIsActive=False

	#Not tested yet.
	if 6 in dictToEncode and dictToEncode[6]==1:
		#global controllerIsActive
		controllerIsActive=True

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
	if not 0 in dictToEncode and controllerIsActive:
		raise KeyError("No input (key 0) in dict. Every loop must contain an input when the controller is enabled.")

	#Not tested yet.
	if 10 in dictToEncode and controllerIsActive:
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
	serialPort.write(encodeWithCobs(cbor2.dumps(dictToEncode),'withCBOR'))
	#print(dictToEncode)
	#If the data package is too large the function must be slept to prevent the Arduino from loosing data, because it comes in too fast.
	if encodedLength >= 100:
		time.sleep(encodedLength/1200)
	
	return True