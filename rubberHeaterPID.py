#This is a prototype script used to heat a rubber heater to a certain temperature.
#It is meant to run on Python 3.

from arduino_python_communication import * #Functions for the communication.
from datetime import datetime #To save the data in a .txt-file.
from tinkerforge.ip_connection import IPConnection #To build a connection with the Tinkerforge Bricklet.
from tinkerforge.bricklet_temperature import BrickletTemperature #To read the temperature from the Tinkerforge Bricklet.

#Set the sample time of the system
sampleTime=100

#Set the conservative parameters to let the controller slowly reach the setpoint. 
kp=8.0
ki=0.05
kd=50000.0

#More aggressive parameters to keep the setpoint.
kp2=30.0
ki2=0.3
kd2=50000.0

#The Temperature in C at which the temperature should be changed
temperatureToChangeParameters=30.0

#Needed for the adaptive parameter tunning to know if temperature to change the parameters is reached for the first time.
isFirstTime=True

#Needed for the Tinkerforge Temperature Bricklet.
HOST="localhost"
PORT=4223
UID="zih"

#The serial port over which the data is send.
s = serial.Serial('/dev/ttyACM0',115200)
#Check if the serial port is open.
if not s.isOpen:
        #If it is not open, open it.
        s.open()
#Sleep the system for a short time so that the serial port can be opened.
time.sleep(1)


fileToWrite=open("/home/tobias/Dokumente/Tobi/Studium/Bachelor/PID_Beta_temperature_data/PID_temperature/temperature_data_"+"kp_"+str(kp)+"ki_"+str(ki)+"kd_"+str(kd)+str(datetime.now())+".txt",'w')

#This script is meant to be run from the Command line.
if __name__ == "__main__":

		#Needed to establish the connection to read temperature data from the Bricklet.
        ipcon = IPConnection()

        t = BrickletTemperature(UID,ipcon)

        ipcon.connect(HOST,PORT)

        #Send the initial data to set up the PID controller.
        sendData({0:0,1:kp,2:ki,3:kd,7:sampleTime,8:0,9:30.0},s)

        #A loop to send and print the temperature data and change the parameters.
        for x in range(6000):

        		#The current temperature  read from the temperature Bricklet.
                temp = t.get_temperature()/100
                
                #Check if the temperature to change the parameters is reached.
                if temp >= temperatureToChangeParameters and isFirstTime:
                     	sendData({0:temp,1:kp2,2:ki2,3:kd2},s) 
                        isFirstTime=False                       
                #Just send the data.
                else:
                        sendData({0:temp},s)
                #Print the Input adn the Output of the Arduino
                print(s.readline()+"\n"+s.readline())
                #Write the temperature which is measured in fileToWrite
                fileToWrite.write(str(temp)+"\n")
                #Sleep the system for the sample time, if i do this the Pi Arduino combo works.
                #If this is removed it doesn't work.
                #Don't ask me why.
                time.sleep(sampleTime/1000)
        #Disconnect the Bricklet
        ipcon.disconnect()
#Close the file.
fileToWrite.close()
#Set this parameter to True again.
isFirstTime=True
