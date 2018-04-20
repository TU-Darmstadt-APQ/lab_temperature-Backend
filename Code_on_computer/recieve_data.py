#!/home/tobias/anaconda3/bin/python3

from arduino_python_communication_v3 import *
from datetime import datetime
#import RPi.GPIO as GPIO

#Set the parameters for the PID controller.
#Be carefull when setting a high Kd value and a small sampletime, this will result in the controller outputing either the max. output or the min. output
#when there are changes in the input.


controller = PIDSender('/dev/ttyACM0')
#Send the main settings to the controller.
#controller.sendIntData({0:22.0,1:controller.getKp(),2:controller.getKi(),3:controller.getKd(),6:controller.getControllerActivity(),7:controller.getSampleTime(),8:controller.getDirection(),9:controller.getSetpoint()})

#controller.reset()
controller.begin()
#controller.begin()
controller.changeDirection(1)
controller.changeKp(100.0)
controller.changeKi(0.1)
controller.changeKd(2.0)
controller.changeMode(1)
controller.changeSetpoint(30.00)
controller.changeLowerOutputLimit(0.0)
controller.changeUpperOutputLimit(4095.0)
controller.changeSampleTime(1000)
#controller.changeOutput(100.0)
controller.sendNewValues()

controller.reset()

#print("\n")
#controller.printEverything()
#print("\n")

fileToWrite=open("/home/tobias/throw_away_data/temperature_data"+(str(datetime.now())[:19]).replace(" ", "_")+".txt",'w')

fileToWrite.write("The first coloumn of data is the time, the second is the  temperature and the last is the  output of the controller.\n\n")
fileToWrite.write("The settings of the controller are:\n"+"kp: "+str(controller.kp)+", ki: "+str(controller.ki)+", kd: "+str(controller.kd)+", setpoint: "+str(controller.setpoint)+" ,sample time: "+str(controller.sampleTime)+" ms"+"\n\n")

if __name__ == "__main__":

        data=b''

        startTime=time.time()

        tempString="0"

        #Sends and reads the data in an infinite loop.
        while True:

                #settingsFile=open("settings.txt","r")

                #settings=settingsFile.readlines()

                settingsSampleTime=controller.sampleTime

                if time.time()-startTime>settingsSampleTime/1000:
                        temp=controller.sendRandomTemperature()
                        tempString="%.2f" % temp
                        startTime=time.time()


                #Read the answer of the Arduino with Cbor and Cobs.
                while controller.serialPort.in_waiting:
                        
                        recievedByte=controller.serialPort.read()
                        
                        if recievedByte==b'\x00':
                                #print(data)
                                #Rememerber that the code on the Arduino must not contain any Serial.print()-functions.
                                #If this is not the case than the communication goes to shit.
                                obj=cbor2.loads(cobs.decode(data))
                                
                                if obj==cbor2.CBORSimpleValue(0):
                                        obj=0

                                #This part is needed if the number 0.0 is send.
                                #0.0 will not be recognized as a 32 bit floating point number but as a SimpleValue.
                                #This is the case because simple values and floating point numbers have the same major type in CBOR.
                                """
                                if obj==cbor2.CBORSimpleValue(0):
                                        if type(objectBefore) is int:
                                                fileToWrite.write(str(datetime.now())[:19]+"   "+str(temp)+"   "+str(obj)+"\n")
                                        print(0, end='', flush=True)
                                        objectBefore=0
                                """
                                if type(obj) is int:
                                        fileToWrite.write(str(datetime.now())[:19]+","+tempString+","+str(obj)+"\n")
                                        print(obj, end='', flush=True)

                                #Floats will be rounded to two numbers after the comma.
                                elif type(obj) is float:
                                        fileToWrite.write(str(obj)+"\n")
                                        print("%.2f" % obj, end='', flush=True)

                                #All the other datatypes are printed normally.
                                else:   
                                        if obj != "\n":
                                                fileToWrite.write(str(datetime.now())[:19]+","+tempString+","+str(obj))
                                        print(obj, end='', flush=True)

                                #Reinitialize the bytearray for new data.
                                data=b''
                        else:
                                data = data + recievedByte
                #The sample is in the unit ms, but the sleep method takes seconds as input so we have to divide by 1000 additionally if we want to wait half the sampletime we get 500.
fileToWrite.close()
