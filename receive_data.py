#!/usr/bin/env python3

from arduino_python_communication_v3 import *
from datetime import datetime

import constants
#import RPi.GPIO as GPIO

#Set the parameters for the PID controller.
#Be carefull when setting a high Kd value and a small sampletime, this will result in the controller outputing either the max. output or the min. output
#when there are changes in the input.


controller = PIDSender('/dev/ttyACM0')
#Send the main settings to the controller.
#controller.sendIntData({0:22.0,1:controller.getKp(),2:controller.getKi(),3:controller.getKd(),6:controller.getControllerActivity(),7:controller.getSampleTime(),8:controller.getDirection(),9:controller.getSetpoint()})

#controller.reset()
controller.begin(sensorUID="DhJ",type="humidity")
#controller.begin()
controller.changeDirection(False)
controller.changeKp(383.0)
controller.changeKi(0.5)
controller.changeKd(2.0)
controller.changeSetpoint(24.00)
controller.changeLowerOutputLimit(0.0)
controller.changeUpperOutputLimit(4095.0)
controller.changeSampleTime(2000)
controller.changeOutput(2400.0)
controller.sendNewValues()

controller.changeMode(True)
controller.sendNewValues()

#print("\n")
#controller.printEverything()
#print("\n")

try:
    fileToWrite=open("/home/pi/lab_temperature_system/Lab_11_temperature_data/temperature_data"+(str(datetime.now())[:19]).replace(" ", "_")+".txt",'w', buffering=1)
except FileNotFoundError:
    fileToWrite=open("temperature_data"+(str(datetime.now())[:19]).replace(" ", "_")+".txt",'w', buffering=1)

fileToWrite.write("The first coloumn of data is the time, the second is the  temperature and the last is the  output of the controller.\n\n")
fileToWrite.write("The settings of the controller are:\n"+"kp: "+str(controller.getKp())+", ki: "+str(controller.getKi())+", kd: "+str(controller.getKd())+", setpoint: "+str(controller.getSetpoint())+" ,sample time: "+str(controller.getSampleTime())+" ms"+"\n\n")

if __name__ == "__main__":

        data=b''
        startTime=time.time()
        temperature=controller.sendTemperature()

        #Sends and reads the data in an infinite loop.
        while True:
                if time.time()-startTime>controller.sampleTime/2000:
                        temperature = controller.sendTemperature()
                        startTime=time.time()

                #Read the answer of the Arduino with Cbor and Cobs.
                while controller.serialPort.in_waiting:
                        
                        recievedByte=controller.serialPort.read()
                        
                        if recievedByte==b'\x00':
                                #print(data)
                                #Rememerber that the code on the Arduino must not contain any Serial.print()-functions.
                                #If this is not the case than the communication goes to shit.
                                try:
                                    result = cbor2.loads(cobs.decode(data))
                                    try:
                                        if result.get(constants.MessageCodes.set_input, constants.MessageCodes.error_invalid_command) == constants.MessageCodes.messageAck:
                                            line = "{timestamp},{temperature:.2f},{output}".format(timestamp=datetime.utcnow(), temperature=temperature, 
output=result[constants.MessageCodes.callback_update_value])
                                            fileToWrite.write(line+"\n")
                                            print(line)
                                    except KeyError:
                                        print(data)
                                except cobs.DecodeError:
                                    print(data)

                                #Reinitialize the bytearray for new data.
                                data=b''
                        else:
                                data = data + recievedByte
                #Sleep the script to reduce the cpu load.
                #0.001 is the minimal sample time of the controller.
                time.sleep(0.1)
fileToWrite.close()
