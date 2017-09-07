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

import serial #To enable the serial communication.
import time #This is needed to sleep the system after a big data package is send, if not information could get lost.
from cobs import cobs #To decode using COBS.
import cbor2 #To decode using CBOR.
import struct #To store the information of a float in a byte array.
import sys #To distinguish between Big and Little Endian systems. 

#Encodes data using the COBS algorithm.
#The parameter data is the data that should be decoded. x is a String that determines wether the data is already 
#decoded with CBOR or not.
#Returns a bytearray with the decoded data.
def encodeWithCobs(data,x):
	#distinguish between CBOR and without CBOR
	if x=='withCBOR':
		return bytearray(cobs.encode(data)+b'\x00')
	else:
		return bytearray(cobs.encode(bytearray(data))+b'\x00')

#Checks if the given data is a dict with length 255 or less. If it is then all floating point numbers are changed to byte 
#arrays of length four. Furthermore it is distinguished between Little and Big Endian systems. The data is send over the serial
#port serialPort.
#dictToEncode is the dict which should be encoded.
#serialPort is the serial port over which the data should be send.
def sendData(dictToEncode,serialPort):
	#Determine the length of the data package.
	encodedLength=len(encodeWithCobs(cbor2.dumps(dictToEncode),'withCBOR'))
	#checks if the data package is too big.
	if encodedLength < 255:
		#Checks the type of the data package, only dicts are allowed.
		if type(dictToEncode) is dict:
			#Checks the architecture of the System.
			#if Little Endian.
			if sys.byteorder == 'little':
				#Converts floats to bytearrays.
				for x in dictToEncode:
					value = dictToEncode[x]
					if type(value) is float:
						dictToEncode[x]=bytearray(struct.pack('f',value))
			#if Big Endian.
			elif sys.byteorder == 'big':
				for x in dictToEncode:
					value = dictToEncode[x]
					#changes all the floats to byte arrays with a reversed byte order, because 
					#the Arduino uses Little Endian
					if type(value) is float:
						floatBytes=bytearray(struct.pack('f',value))
						floatBytes.reverse()
						dictToEncode[x]=floatBytes
		#Sends the data over the specified serial port.
		serialPort.write(encodeWithCobs(cbor2.dumps(dictToEncode),'withCBOR'))
		#If the data package is bigger than 100 bytes information could get lost, 
		#beause the Arduino only has a 64 Byte Serial Buffer.
		if encodedLength > 100:
			#The number 1200 was obtained via trial and error. By looking which sizes of data packages could still
			#be sent wothout loss of information.
			time.sleep(encodedLength/1200)
	#Let's the user know if the data package is too big.
	else:
		print("Data Package is larger than 255 bytes.","\n")

#Still a bit buggy. Sends the data correctly but doesn't print it correctly. 
#Should print the encoded data and the length of the encoded data to the terminal.
def sendAndPrintData(dataToSend,serialPort):
	#decods the data using CBOR and then COBS
	encodedData=encodeWithCobs(cbor2.dumps(dataToSend),'withCBOR')
	#Prints the encoded form of the data in hexa decimal.
	print("Die mit COBS und CBOR decodierten bytes sind:",encodedData,"\n")
	#Prints the number of bytes in the encoded data package.
	print("Die Größe des codierten Datenpakets ist:",len(encodedData),"\n")
	#Sends the data.
	sendData(dataToSend,serialPort)


