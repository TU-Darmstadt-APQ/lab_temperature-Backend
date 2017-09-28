#!/home/tobias/anaconda3/bin/python3.6

from arduino_python_communication_v2 import *
from datetime import datetime
#import RPi.GPIO as GPIO
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_temperature import BrickletTemperature

#Set the parameters for the PID controller.
#Be carefull when setting a high Kd value and a small sampletime, this will result in the controller outputing either the max. output or the min. output
#when there are changes in the input.
fixedPoint=16
sampleTime=1000
kp=0.94
ki=0.07
kd=180.00
setPoint=30.000

#Needed for the connection to the temperature bricklet.
HOST="localhost"
PORT=4223
UID="zFZ" #UID for the currently used sensor.
#UID="zih" #UID for the other sensor

s = serial.Serial('/dev/ttyUSB0',115200,timeout=sampleTime)
#check if the serial port is open
if not s.isOpen:
        #if it is not open, open it
        s.open()
        #time.sleep(1)
time.sleep(2) #for Arduino Nano/Uno wait 2 s for Due 1 s is okay.

#Send the main settings to the controller.
sendIntData({0:22.000,1:kp,2:ki,3:kd,4:0.0,5:255.0,6:1,7:sampleTime,8:0,9:setPoint},s,fixedPoint)

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
                                
                                recievedByte=s.read()
                                
                                if recievedByte==b'\x00':
                                        
                                        obj=cbor2.loads(cobs.decode(data))

                                        #This part is needed if the number 0.0 is send.
                                        #0.0 will not be recognized as a 32 bit floating point number but as a SimpleValue.
                                        #This is the case because simple values and floating point numbers have the same major type in CBOR.
                                        if obj==cbor2.CBORSimpleValue(0):
                                                print(0.00, end='', flush=True)
                                        
                                        #Floats will be rounded to two numbers after the comma.
                                        elif type(obj) is float:
                                                print("%.2f" % obj, end='', flush=True)
                                        
                                        #All the other datatypes are printed normally.
                                        else:
                                                print(obj, end='', flush=True)
                                        
                                        #Reinitialize the bytearray for new data.
                                        data=b''
                                else:
                                        data = data + recievedByte

                #The sample is in the unit ms, but the sleep method takes seconds as input so we have to divide by 1000 additionally if we want to wait half the sampletime we get 500.
                time.sleep(sampleTime/1000) 

        ipcon.disconnect()

fileToWrite.close()
