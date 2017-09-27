#Import all the necessary packages
#This programm is meant to run on Python3.

from arduino_python_communication_v2 import *
from datetime import datetime
#import RPi.GPIO as GPIO
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_temperature import BrickletTemperature

#Set the parameters for the PID controller.
fixedPoint=16
sampleTime=10
kp=0.94
ki=0.07
kd=187.69
setPoint=30.000

#Needed for the connection to the temperature bricklet.
HOST="localhost"
PORT=4223
UID="zFZ" #UID for the currently used sensor.
#UID="zih" #UID for the other sensor

s = serial.Serial('/dev/ttyUSB1',115200,timeout=0.5)
#check if the serial port is open
if not s.isOpen:
        #if it is not open, open it
        s.open()
        #time.sleep(1)
time.sleep(2) #for Arduino Nano/Uno wait 2 s for Due 1 s is okay.

#Send the main settings to the controller.
sendIntData({0:22.000,1:kp,2:ki,3:kd,6:1,7:sampleTime,8:0,9:setPoint},s,fixedPoint)

if __name__ == "__main__":

        #to build the cnnection to the bricklet.
        ipcon = IPConnection()

        t = BrickletTemperature(UID,ipcon)

        ipcon.connect(HOST,PORT)

        #This is needed for the loop in which the incoming data is read.
        data=b''

        #Sends and reads the data in an infinite loop.
        while True:

                #Read the temperature.
                temp = t.get_temperature()/100

                #Send the temperature.
                sendIntData({0:temp},s,fixedPoint)

                #Read the answer of the Arduino with Cbor and Cobs.
                if s.in_waiting:
                        while s.in_waiting:
                                #print(s.in_waiting)
                                recievedByte=s.read()
                                #print(recievedByte)
                                if recievedByte==b'\x00':
                                        #print(data)
                                        print(cbor2.loads(cobs.decode(data)))
                                        data=b''
                                else:
                                        data = data + recievedByte

                fileToWrite.write(str(temp)+"\n")
                #The sample is in the unit ms, but the sleep method takes seconds as input so we have to divide by 1000 additionally if we want to wait half the sampletime we get 500.
                time.sleep(sampleTime/1000) 

        ipcon.disconnect()
