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
@version 1.0.0 07/24/2017
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
	#distinguish between CBOR and without CBOR
	if x=='withCBOR':
		return bytearray(cobs.encode(data)+b'\x00')
	else:
		return bytearray(cobs.encode(bytearray(data))+b'\x00')


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
	if encodedLength < 255:
		#Diese Teil wird nur ausgeführt, falls es sich um ein dict mit floats handelt.
		if type(dictToEncode) is dict:
			#Wandelt alle floats in die zugehörigen bytearrays um, amkes a distinction between big endian and little endian machines
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


