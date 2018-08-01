#!/home/tobias/anaconda3/bin/python3

from arduino_python_communication_v3 import *
from datetime import datetime
#import RPi.GPIO as GPIO

#Set the parameters for the PID controller.
#Be carefull when setting a high Kd value and a small sampletime, this will result in the controller outputing either the max. output or the min. output
#when there are changes in the input.

controller = PIDSender('/dev/ttyACM0')

def communicate(counter):

        data=b''

        startTime=time.time()

        temp=controller.sendRandomTemperature()
        tempString="%.2f" % temp

        #Sends and reads the data in an infinite loop.
        while counter:
                if time.time()-startTime>controller.sampleTime/1000:
                        temp=controller.sendRandomTemperature()
                        tempString="%.2f" % temp
                        startTime=time.time()
                        print("The send temperature is:",tempString)

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

                                if type(obj) is int:
                                        counter=counter-1
                                        print(obj, end='', flush=True)
                                        #print("\n",counter)

                                #Floats will be rounded to two numbers after the comma.
                                elif type(obj) is float:
                                        counter=counter-1
                                        print("%.2f" % obj, end='', flush=True)
                                        

                                #All the other datatypes are printed normally.
                                else:   
                                        print(obj, end='', flush=True)

                                #Reinitialize the bytearray for new data.
                                data=b''
                                #print("\n",counter)
                        else:
                                data = data + recievedByte


#Send the main settings to the controller.

#controller.reset()
controller.begin()
#controller.begin()

randomNumber=random()

controller.changeDirection(0)
controller.changeKp(100*randomNumber)
controller.changeKi(2*randomNumber)
controller.changeKd(randomNumber)
controller.changeMode(1)
controller.changeSetpoint(22.00+randomNumber)
controller.changeLowerOutputLimit(1+10*randomNumber)
controller.changeUpperOutputLimit(4095.0+randomNumber)
controller.changeSampleTime(int(1000+100*randomNumber))
#controller.changeOutput(100.0)
controller.sendNewValues()

#print("\n")
#controller.printEverything()
#print("\n")

#fileToWrite=open("/home/pi/lab_temperature_system/Lab_11_temperature_data/temperature_data"+(str(datetime.now())[:19]).replace(" ", "_")+".txt",'w')

#fileToWrite.write("The first coloumn of data is the time, the second is the  temperature and the last is the  output of the controller.\n\n")
#fileToWrite.write("The settings of the controller are:\n"+"kp: "+str(controller.getKp())+", ki: "+str(controller.getKi())+", kd: "+str(controller.getKd())+", setpoint: "+str(controller.getSetpoint())+" ,sample time: "+str(controller.getSampleTime())+" ms"+"\n\n")

if __name__ == "__main__":
        
        print("\n")
        print("Testing direct mode for 5 cycles.")
        print("\n")

        communicate(14)

        print("\n")
        print("Testing reverse mode for 5 cycles.")
        print("\n")

        controller.changeDirection(1)
        controller.sendNewValues()

        communicate(7)

        print("\n")
        print("Testing manual mode for 5 cycles.")
        print("\n")

        controller.changeMode(0)
        controller.changeOutput(100*randomNumber)
        controller.sendNewValues()

        communicate(7)