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
@version 2.0.0 03/26/2018
"""

#To save the time in the log file
import time
#For COBSing stuff
from cobs import cobs
#For CBORing the COBSed stuff
import cbor2
#To get the temperature data
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_temperature import BrickletTemperature
from tinkerforge.bricklet_humidity_v2 import BrickletHumidityV2
from tinkerforge.bricklet_humidity import BrickletHumidity

import constants

#Constructor of the PIDSender class. Only takes the device directory of the controller as input (e.g. /dev/ttyACM0).
class PIDSender:
    @property
    def sequence_number(self):
        self.__sequence_number = (self.__sequence_number % 15) + 1
        return self.__sequence_number

    def __init__(self, sensor_ip='localhost', sensor_port=4223):
        #Stuff that is needed to build a connection with the temperature bricklet.
#        self.host="192.168.1.94"
        self.host=sensor_ip
        self.port=sensor_port
        self.uid=0
        self.ipcon=0
        self.bricklet=0
        self.sensor_type="temperature"

        #The data that will be send is saved in this dict.
        self.dataToSend = {}

        #Initale values of the PID controller.
        self.kp = 0.0
        self.ki = 0.0
        self.kd = 0.0
        self.lowerOutputLimit = 0.0
        self.upperOutputLimit = 4095
        self.mode = 1
        self.sampleTime = 1000
        self.direction = True
        self.setpoint = 22.50
        self.output = -1.0
        self.__sequence_number = 0

        #Floating point numbers send as integers using fixed point arithmetic.
        self.fixedPoint=16

    #Before a communciation can be established the begin()-method has to be called.
    #It takes an optional parameter which is the UID of the Tinkerforge temperature sensor (e.g. "zih").
    #Type is the type of the sensor
    def begin(self,*args,**keywordParameters):
        #Start the connection with the Tinkerforge sensor
        if "sensorUID" in keywordParameters and "sensor_type" in keywordParameters:
            self.uid=keywordParameters["sensorUID"]
            self.sensor_type=keywordParameters["sensor_type"]
            self.ipcon = IPConnection()
            if self.sensor_type=="temperature":
                self.bricklet = BrickletTemperature(self.uid,self.ipcon)
            elif self.sensor_type=="humidity":
                self.bricklet = BrickletHumidityV2(self.uid,self.ipcon)
            else:
                print("No specific Bricklet passed, defaulting to Temperature Bricklet.")
                self.bricklet= BrickletTemperature(self.uid,self.ipcon)
            self.ipcon.connect(self.host,self.port)

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

    def set_gain(self, value):
        self.dataToSend[constants.MessageType.set_gain] = value

    def changeKp(self, value):
        if not type(value) is int:
            raise(TypeError("Kp must be of type int."))
        if value < 0 or value > (2**32)-1:
            raise(ValueError("Kp must be greater than 0 and smaller than 32 bit."))
        self.dataToSend[1]=value

    def changeKi(self, value):
        if not type(value) is int:
            raise(TypeError("Ki must be of type int."))
        if value < 0 or value > (2**32)-1:
            raise(ValueError("Ki must be greater than 0 and smaller than 32 bit."))
        self.dataToSend[2]=value

    def changeKd(self, value):
        if not type(value) is int:
            raise(TypeError("Kp must be of type int."))
        if value < 0 or value > (2**32) -1:
            raise ValueError("The output limit must be an unsigned int with a maximum size of 32 Bit.")
        self.dataToSend[3]=value


    def changeLowerOutputLimit(self, value):
        if not type(value) is int:
            raise(TypeError("Lower output limit must be of type int"))
        if value < 0 or value > (2**32) -1:
            raise ValueError("The output limit must be an unsigned int with a maximum size of 32 Bit.")
        self.dataToSend[4] = value

    def changeUpperOutputLimit(self, value):
        if not type(value) is int:
            raise(TypeError("Upper output limit must be of type int"))
        if value < 0 or value > (2**32) -1:
            raise ValueError("The output limit must be an unsigned int with a maximum size of 32 Bit.")
        self.dataToSend[5] = value

    def changeMode(self, newMode):
        self.dataToSend[6]=newMode

    def setTimeout(self, value):
        if not type(value) is int:
            raise TypeError("The timeout must be of type int.")
        if value < 0 or value > (2**32) -1:
            raise ValueError("The timeout must be an unsigned int with a maximum size of 32 Bit.")
        self.dataToSend[constants.MessageType.set_timeout] = value

    def changeDirection(self, newDirection):
        if not (newDirection==1 or newDirection==0):
            raise(ValueError("The direction must be either 0 or 1."))
        self.dataToSend[8]=newDirection

    def changeSetpoint(self, value):
        if not type(value) is int:
            raise(TypeError("Setpoint must be of type int."))
        if value < 0 or value > (2**32)-1:
            raise(ValueError("The setpoint must be an unsigned int with a maximum size of 32 Bit."))
        self.dataToSend[9]=value    

    def changeOutput(self, newOutput):
        if not type(newOutput) is float:
            raise(TypeError("Kp must be of type float."))
        intValue=self.fixedPointFloatToInt(newOutput)
        if newOutput < 0 or intValue > (2**32)-1:
            raise(ValueError("Kp must be greater than 0 and smaller than 32 bit."))
        self.dataToSend[10]=intValue

    #Method to encode given data with cobs.
    #Takes two parameters as input:
    #    -data: The data that should be encoded.
    #    -x: If x equals "withCBOR" the method does not convert the input data to byte array before encding it.
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
        return int((self.bricklet.get_temperature()/100 + 40) / 165 * 2**16)

    def getBuffer(self):
        return self.dataToSend

class PIDSenderEthernet(PIDSender):
    @property
    def socket(self):
        return self.__socket

    def readByte(self):
        return self.socket.recv(1)

    def __init__(self, controller_ip, controller_port=4223, sensor_ip='localhost', sensor_port=4223):
        super().__init__(sensor_ip, sensor_port)

        import socket
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.connect((controller_ip, controller_port)) 

    #Method to send the temperature of the Tinkerforge Bricklet to the controller.
    def sendTemperature(self):
        temperature  = self.getTemperature()
        self.__socket.send(self.encodeWithCobs(cbor2.dumps({
            constants.MessageType.sequence_number: self.sequence_number,
            constants.MessageType.set_input: temperature,
          }),'withCBOR'))
        return temperature

    """
    This method is were the magic happens.
    After the methods to change the parameters are called one has to call this function to send the dict with 
    the new values.
    First a test is performed if new upper and lower output limits are in the dict. If this is the case it is checked
    if the lower output limit is smaller than the upper output limit, if this is the case an error is thrown.

    After that a test is performed to see if an output was written without the controller beginning turned of.

    Next the dict dataToSend is encoded and it is checked if the length is smaller than 255 bytes.
    
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

        # Add sequence number to all requests
        self.dataToSend[constants.MessageType.sequence_number] = self.sequence_number

        encodedData=self.encodeWithCobs(cbor2.dumps(self.dataToSend),'withCBOR')
        encodedLength=len(encodedData)
        if encodedLength > 255:
            raise OverflowError("The length of the encoded data package is "+str(encodedLength)+". It must be smaller than 255 bytes")

        self.__socket.send(encodedData)

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

        self.dataToSend={}
        
        if encodedLength >= 100:
            time.sleep(encodedLength/1200)
        return True

class PIDSenderSerial(PIDSender):
    @property
    def serial_port(self):
        return self.__serial_port

    def __init__(self, serial_port, sensor_ip='localhost', sensor_port=4223):
        super().__init__(sensor_ip, sensor_port)
        self.__baudRate = 115200

        import serial
        self.__serial_port = serial.Serial(serial_port, self.__baudRate)

        if not self.serial_port.isOpen():
            self.serial_port.open()
            print("Serial port opened.")
        else:
            print("Serial port was already open.")
        time.sleep(1) # sleep two seconds to make sure the communication is established.

    def readByte(self):
        return self.serial_port.read(1)

    #Method to send the temperature of the Tinkerforge Bricklet to the controller.
    def sendTemperature(self):
        temperature = self.getTemperature()
        self.serial_port.write(self.encodeWithCobs(cbor2.dumps({
            constants.MessageType.sequence_number: self.sequence_number,
            constants.MessageType.set_input: temperature,
          }),'withCBOR'))
        return temperature

    #Sends a specific temperature to controller that the user acn choose.
    def sendManualTemperature(self,inputTemperature):
        self.serial_port.write(self.encodeWithCobs(cbor2.dumps({0:self.fixedPointFloatToInt(inputTemperature)}),'withCBOR'))

    """
    This method is were the magic happens.
    After the methods to change the parameters are called one has to call this function to send the dict with 
    the new values.
    First a test is performed if new upper and lower output limits are in the dict. If this is the case it is checked
    if the lower output limit is smaller than the upper output limit, if this is the case an error is thrown.

    After that a test is performed to see if an output was written without the controller beginning turned of.

    Next the dict dataToSend is encoded and it is checked if the length is smaller than 255 bytes.
    
    In the last step the values of the controller are updated, the dict is reset and the method returns true if no errors
    have occured.   
    """
    def sendNewValues(self):
        # Add sequence number to all requests
        self.dataToSend[constants.MessageType.sequence_number] = self.sequence_number

        encodedData=self.encodeWithCobs(cbor2.dumps(self.dataToSend),'withCBOR')
        encodedLength=len(encodedData)
        if encodedLength > 255:
            raise OverflowError("The length of the encoded data package is "+str(encodedLength)+". It must be smaller than 255 bytes")

        self.serial_port.write(encodedData)

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

        self.dataToSend={}

        if encodedLength >= 100:
            time.sleep(encodedLength/1200)
        return True

