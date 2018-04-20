#!/home/tobias/anaconda3/bin/python3

from arduino_python_communication_v3 import *
from datetime import datetime
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_temperature import BrickletTemperature

#Open the ports.
controller2 = PIDSender('/dev/ttyACM0')
controller1 = PIDSender('/dev/ttyACM1')
#Send the main settings to the controller.
#controller.sendIntData({0:22.0,1:controller.getKp(),2:controller.getKi(),3:controller.getKd(),6:controller.getControllerActivity(),7:controller.getSampleTime(),8:controller.getDirection(),9:controller.getSetpoint()})

#Print nice stuff to the console.
print("\nController 2:")
controller2.reset()
controller2.begin()

#I don't know why but at the moment we need a work around for the start.
#If I don't set the output manually to zero. The two controllers will start with different values.
controller1.changeMode(0)
controller1.changeOutput(0.0)
controller2.changeMode(0)
controller2.changeOutput(0.0)

controller2.changeDirection(1)
controller2.changeKp(100.0)
controller2.changeKi(0.1)
controller2.changeKd(2.0)
controller2.changeSetpoint(30.00)
controller2.changeLowerOutputLimit(0.0)
controller2.changeUpperOutputLimit(4095.0)
controller2.changeSampleTime(1000)
controller2.sendNewValues()

print()

print("Controller 1:")
controller1.reset()
controller1.begin()

controller1.changeDirection(1)
controller1.changeKp(100.0)
controller1.changeKi(0.1)
controller1.changeKd(2.0)
controller1.changeSetpoint(30.00)
controller1.changeLowerOutputLimit(0.0)
controller1.changeUpperOutputLimit(4095.0)
controller1.changeSampleTime(1000)
controller1.sendNewValues()

print()


#Print the settings in the log file.
fileToWrite=open("/home/tobias/throw_away_data/twocontrollerData_"+(str(datetime.now())[:19]).replace(" ", "_")+".txt",'w')

fileToWrite.write("The first coloumn of data is the time, the second is the  temperature and the last is the  output of the controller.\n\n")
fileToWrite.write("The settings of the first controller are:\n"+"kp: "+str(controller1.getKp())+", ki: "+str(controller1.getKi())+", kd: "+str(controller1.getKd())+", setpoint: "+str(controller1.getSetpoint())+" ,sample time: "+str(controller1.getSampleTime())+" ms"+"\n\n")
fileToWrite.write("The settings of the second controller are:\n"+"kp: "+str(controller2.getKp())+", ki: "+str(controller2.getKi())+", kd: "+str(controller2.getKd())+", setpoint: "+str(controller2.getSetpoint())+" ,sample time: "+str(controller2.getSampleTime())+" ms"+"\n\n")

if __name__ == "__main__":

		data=b''

		startTime=time.time()

		firstTime=True

		#change the mode to automatic, so that both controllers start at zero.
		controller1.changeMode(1)
		controller2.changeMode(1)
		controller1.sendNewValues()
		controller2.sendNewValues()

		temp=10*random()+controller1.setpoint
		tempString="%.2f" % temp

		#Sends and reads the data in an infinite loop.
		while True:
				if time.time()-startTime>controller1.sampleTime/1000:
					temp=10*random()+controller1.setpoint
					tempString="%.2f" % temp
					buffer1=controller1.getBuffer()
					buffer2=controller2.getBuffer()
					fileToWrite.write("\nPi buffer for controller1: "+str(datetime.now())[:19]+","+str(buffer1)+"\n")
					fileToWrite.write("Pi buffer for controller2: "+str(datetime.now())[:19]+","+str(buffer2)+"\n\n")
					#print(temp)
					controller1.sendManualTemperature(temp)
					#print("first temperature send.")
					controller2.sendManualTemperature(temp)
					#print("second temperature send.")
					startTime=time.time()

				#Read the answer of the Arduino with Cbor and Cobs.
				while controller1.serialPort.in_waiting:
						
						recievedByte=controller1.serialPort.read()
						
						if recievedByte==b'\x00':
								#print(data)
								#Rememerber that the code on the Arduino must not contain any Serial.print()-functions.
								#If this is not the case than the communication goes to shit.
								obj=cbor2.loads(cobs.decode(data))
								
								if obj==cbor2.CBORSimpleValue(0):
										obj=0

								if type(obj) is int:
										fileToWrite.write("Controller 1:"+str(datetime.now())[:19]+","+tempString+","+str(obj)+"\n")
										print("Controller 1:",obj, end='', flush=True)

								#Floats will be rounded to two numbers after the comma.
								elif type(obj) is float:
										fileToWrite.write(str(obj)+"\n")
										print("%.2f" % obj, end='', flush=True)

								#All the other datatypes are printed normally.
								else:   
										if obj != "\n":
												fileToWrite.write("Controller 1:"+str(datetime.now())[:19]+","+tempString+","+str(obj))
												print("Controller 1:",obj, end='', flush=True)
										else:
											print(obj, end='', flush=True)

								#Reinitialize the bytearray for new data.
								data=b''
						else:
								data = data + recievedByte

				#Read the answer of the Arduino with Cbor and Cobs.
				while controller2.serialPort.in_waiting:
				
						recievedByte=controller2.serialPort.read()
						
						if recievedByte==b'\x00':
								#print(data)
								#Rememerber that the code on the Arduino must not contain any Serial.print()-functions.
								#If this is not the case than the communication goes to shit.
								obj=cbor2.loads(cobs.decode(data))
								
								if obj==cbor2.CBORSimpleValue(0):
										obj=0

								if type(obj) is int:
										fileToWrite.write("Controller 2:"+str(datetime.now())[:19]+","+tempString+","+str(obj)+"\n")
										print("Controller 2:",obj, end='', flush=True)

								#Floats will be rounded to two numbers after the comma.
								elif type(obj) is float:
										fileToWrite.write(str(obj)+"\n")
										print("%.2f" % obj, end='', flush=True)

								#All the other datatypes are printed normally.
								else:   
										if obj != "\n":
												fileToWrite.write("Controller 2:"+str(datetime.now())[:19]+","+tempString+","+str(obj))
												print("Controller 2:",obj, end='', flush=True)
										else:
											print(obj, end='', flush=True)
								#Reinitialize the bytearray for new data.
								data=b''
						else:
								data = data + recievedByte
fileToWrite.close()
