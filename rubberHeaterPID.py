#!/home/tobias/anaconda3/bin/python3.6

from arduino_python_communication import *
from datetime import datetime
#import RPi.GPIO as GPIO
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_temperature import BrickletTemperature

sampleTime=100
kp=8.0
ki=0.05
kd=50000.0

kp2=30.0
ki2=0.3
kd2=50000.0

temperatureToChangeParameters=30.0

isFirstTime=True

HOST="localhost"
PORT=4223
UID="zih"   #Keine Ahnung, was hier rein muss

dict1={0:22.23,1:2.22,2:3.33,3:4.44,6:1,7:0,8:0,9:31}

s = serial.Serial('/dev/ttyACM0',115200)
#check if the serial port is open
if not s.isOpen:
        #if it is not open, open it
        s.open()
        #time.sleep(1)
time.sleep(1)
#sendData({7:5},s)

#sendData({0:19.99,1:2.0,2:2.0,3:2.0,7:100,8:0,9:30.0},s)
"""
for x in range(2):
        print(s.readline())
time.sleep(0.1)
sendData({0:33.0},s)
for x in range(2):
        print(s.readline())

#anderer Code-Schnipsel
for x in range(20):
        sendData({0:34.0+0.01*x},s)
        for y in range(4):
                print(s.readline())
        time.sleep(0.1)
"""

fileToWrite=open("/home/tobias/Dokumente/Tobi/Studium/Bachelor/PID_Beta_temperature_data/PID_temperature/temperature_data_"+"kp_"+str(kp)+"ki_"+str(ki)+"kd_"+str(kd)+str(datetime.now())+".txt",'w')

if __name__ == "__main__":

        ipcon = IPConnection()

        t = BrickletTemperature(UID,ipcon)

        ipcon.connect(HOST,PORT)

        sendData({0:0,1:kp,2:ki,3:kd,7:sampleTime,8:0,9:30.0},s)

        for x in range(6000):

                temp = t.get_temperature()/100
                
                if temp >= temperatureToChangeParameters and isFirstTime:
                        sendData({0:temp,1:kp2,2:ki2,3:kd2},s) 
                        isFirstTime=False                       
                else:
                        sendData({0:temp},s)

                print(s.readline())
                print(s.readline())

                fileToWrite.write(str(temp)+"\n")
                time.sleep(sampleTime/1000)

        ipcon.disconnect()

fileToWrite.close()
isFirstTime=True