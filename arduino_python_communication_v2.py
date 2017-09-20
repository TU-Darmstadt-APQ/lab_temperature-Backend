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
@version 2.0.0 09/17/2017
"""

import serial
import time
from cobs import cobs
import cbor2
import struct
import sys

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
	
	#The fixed point must be an int.
	if not type(fixedPoint) is int:
		raise TypeError("The type of the fixed point must be int.")

	if fixedPoint < 0 or fixedPoint > 32:
		raise ValueError("The fixed point must be between 0 and 32.")

	if not type(floatToConvert) is float:
		raise TypeError("The type of the value to be converted must be float.")

	#In this section it is determined wether or not the given float would be larger than 32 bit when converted.
	if floatToConvert >= 2**(32-fixedPoint):
		raise ValueError("The given flaoting point number must be small enough so that it can be converted using 32 bit uints.")
	
	if floatToConvert < 0:
		raise ValueError("The floating point number must be greater than zero.") 

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
	encodedLength=len(encodeWithCobs(cbor2.dumps(dictToEncode),'withCBOR'))
	if encodedLength > 256:
		raise OverflowError("The length of the encoded data package is larger than 255 bytes.")

	if not type(dictToEncode) is dict:
		raise TypeError("The data to encode must be of type dict.")

	keyFlag=True
	valueFlag=True

	for key in dictToEncode:
		
		#Changes all floats in the dict to uints using the fixed point.
		if type(dictToEncode[key]) is float:
			dictToEncode[key]=fixedPointFloatToInt(fixedPoint,dictToEncode[key])

		value=dictToEncode[key]

		#Checks if the basic properties for the keys and values are fullfilled.
		keyFlag=keyFlag and (type(key) is int) and (key >= 0) and (key < 10)
		valueFlag=valueFlag and (type(value) is int) and (value >= 0) and (value <= 4294967295)

	if not keyFlag:
		raise ValueError("All keys must be greater or equal to zero, smaller than 10 and of type int.")

	if not valueFlag:
		raise ValueError("All values in the dict must be of type int, larger than 0 and smaller than 4294967295.")

	if not 0 in dictToEncode:
		raise KeyError("An input must be passed each cycle with the key 0.")

	if (4 in dictToEncode and not 5 in dictToEncode) or (5 in dictToEncode and not 4 in dictToEncode):
		raise KeyError("Upper and lower output limits must be passed together.")

	elif 4 in dictToEncode and 5 in dictToEncode:
		if dictToEncode[4] >= dictToEncode[5]:
			raise ValueError("The upper output limit must be greater than the lower output limit.")

	if 6 in dictToEncode and not(dictToEncode[6]==0 or dictToEncode[6]==1):
		raise ValueError("The mode (key 6) must be either 0 for MANUAL or 1 for AUTOMATIC.")

	if 8 in dictToEncode and not(dictToEncode[8]==0 or dictToEncode[8]==1):
		raise ValueError("The direction must be either 0 for DIRECT or 1 for REVERSE.")

	#Serialize the data.
	serialPort.write(encodeWithCobs(cbor2.dumps(dictToEncode),'withCBOR'))

	#If the data package is too large the function must be slept to prevent the Arduino from loosing data, because it comes in too fast.
	if encodedLength >= 100:
		time.sleep(encodedLength/1200)
	
	return True





				

#sendet jegliche Art von Daten mit CBOR und COBS. Die Parameter sind die Daten die gesendet werden sollen.
#Weiterer Parameter ist der serielle Port über den die Daten gesendet werden sollen. 
def sendData(dictToEncode,serialPort):
	"""
	s = serial.Serial(serialPort,baudrate)
	#check if the serial port is open
	if not s.isOpen:
		#if it is not open, open it
		s.open()
		time.sleep(1)
	"""
	encodedLength=len(encodeWithCobs(cbor2.dumps(dictToEncode),'withCBOR'))
	#Ueberpruefe, ob das Datenpaket nicht zu groß ist.
	if encodedLength < 256:
		#Diese Teil wird nur ausgeführt, falls es sich um ein dict mit floats handelt.
		if type(dictToEncode) is dict:
			#Wandelt alle floats in die zugehörigen bytearrays um, amkes a distinction between big ednian and little endian machines
			#little endian
			if sys.byteorder == 'little':
				for x in dictToEncode:
					value = dictToEncode[x]
					#changes all the floats to byte arrays
					if type(value) is float:
						dictToEncode[x]=bytearray(struct.pack('f',value))
			#big endian
			elif sys.byteorder == 'big':
				for x in dictToEncode:
					value = dictToEncode[x]
					#changes all the floats to byte arrays with a reversed byte order
					if type(value) is float:
						floatBytes=bytearray(struct.pack('f',value))
						floatBytes.reverse()
						dictToEncode[x]=floatBytes
		#sendet die Daten.
		serialPort.write(encodeWithCobs(cbor2.dumps(dictToEncode),'withCBOR'))
		#Ueberpruefe, ob nach dem Senden der Daten eine Pause gemacht werden muss, damit der serielle Buffer vom Arduino nicht voll wird.
		if encodedLength > 100:
			time.sleep(encodedLength/1200) #1200 für eine Baudraute von 115200
	else:
		print("Data Package is larger than 256 bytes.")
		print()

#Ist irgendwie noch verbugged. Printet die Daten nicht korrekt. Aber sendet sie korrekt.
#Sends the given data with the help of tobiSender to the specified serial port.
#Prints the encoded data and the length of the encoded data to the terminal.
def sendAndPrintData(dataToSend,serialPort):
	#decods the data using CBOR and then COBS
	encodedData=encodeWithCobs(cbor2.dumps(dataToSend),'withCBOR')
	print()
	#Prints the encoded form of the data in hexa decimal.
	print("Die mit COBS und CBOR decodierten bytes sind:",encodedData)
	print()
	#Prints the number of bytes in the encoded data package.
	print("Die Größe des codierten Datenpakets ist:",len(encodedData))
	print()
	#Sends the data.
	sendData(dataToSend,serialPort)


