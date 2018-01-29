#!/home/tobias/anaconda3/bin/python3.6

from arduino_python_communication_v3 import *
from datetime import datetime
#import RPi.GPIO as GPIO
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_temperature import BrickletTemperature

#Set the parameters for the PID controller.
#Be carefull when setting a high Kd value and a small sampletime, this will result in the controller outputing either the max. output or the min. output
#when there are changes in the input.


controller = PIDSender('/dev/ttyUSB0')
#Send the main settings to the controller.
controller.sendIntData({0:22.0,1:controller.getKp(),2:controller.getKi(),3:controller.getKd(),6:controller.getControllerActivity(),7:controller.getSampleTime(),8:controller.getDirection(),9:controller.getSetpoint()})

fileToWrite=open("/home/tobias/Dokumente/Tobi/Studium/Bachelor/PID_Beta_temperature_data/temperature_data"+(str(datetime.now())[:19]).replace(" ", "_")+".txt",'w')

fileToWrite.write("The following data is the temperature of the Metallklotz. The first coloumn of data is the time, the second is the  temperature and the last is the  output of the controller.\n\n")
fileToWrite.write("The settings of the controller are:\n"+"kp: "+str(controller.getKp())+", ki: "+str(controller.getKi())+", kd: "+str(controller.getKd())+", setpoint: "+str(controller.getSetpoint())+" ,sample time: "+str(controller.getSampleTime())+" ms"+"\n\n")

if __name__ == "__main__":
        
        #to build the cnnection to the bricklet.
        ipcon = IPConnection()

        t = BrickletTemperature(UID,ipcon)

        ipcon.connect(HOST,PORT)

        #This is needed for the loop in which the incoming data is read.
        data=b''

        objectBefore=0

        #Sends and reads the data in an infinite loop.
        while True:

                #Read the temperature.
                temp = t.get_temperature()/100

                """
                if abs(temp-setPoint) <= 0.5 and isFirstTime:
                        sendIntData({0:temp,1:kp2,2:ki2,3:kd2},s,fixedPoint)
                        isFirstTime=False
                """
                #Send the temperature.
                controller.sendIntData({0:temp})


                #Read the answer of the Arduino with Cbor and Cobs.
                if controller.serialPort.in_waiting:
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
                                                if type(objectBefore) is int:
                                                        fileToWrite.write(str(datetime.now())[:19]+","+str(temp)+","+str(obj)+"\n")
                                                print(obj, end='', flush=True)
                                                objectBefore=obj

                                        #Floats will be rounded to two numbers after the comma.
                                        elif type(obj) is float:
                                                print("%.2f" % obj, end='', flush=True)
                                                objectBefore=obj

                                        #All the other datatypes are printed normally.
                                        else:
                                                print(obj, end='', flush=True)
                                        
                                        
                                        #Reinitialize the bytearray for new data.
                                        data=b''
                                else:
                                        data = data + recievedByte
                
                #The sample is in the unit ms, but the sleep method takes seconds as input so we have to divide by 1000 additionally if we want to wait half the sampletime we get 500.
                time.sleep(sampleTime/1000)

fileToWrite.close()
