#!/usr/bin/env python3

from arduino_python_communication_v3 import *
from datetime import datetime

import constants
#import RPi.GPIO as GPIO

#Set the parameters for the PID controller.
#Be carefull when setting a high Kd value and a small sampletime, this will result in the controller outputing either the max. output or the min. output
#when there are changes in the input.


controller = PIDSenderSerial('/dev/ttyACM3')
#controller = PIDSenderEthernet("192.168.1.96")
#Send the main settings to the controller.
#controller.sendIntData({0:22.0,1:controller.getKp(),2:controller.getKi(),3:controller.getKd(),6:controller.getControllerActivity(),7:controller.getSampleTime(),8:controller.getDirection(),9:controller.getSetpoint()})

#controller.reset()
controller.begin(sensorUID="DhJ",type="humidity")
#controller.begin(sensorUID="Dm6",type="humidity")
#controller.begin()
controller.changeDirection(False)
controller.changeKp(1011120) # 383.0 dac_bit_values / K * 165 / 2**16 adc_bit_values / K in Q11.20 notation
controller.changeKi(1320)    # 0.5 dac_bit_values / (K s) * 165 / 2**16 adc_bit_values / K in Q11.20 notation
controller.changeKd(5280)    # 2.0 dac_bit_values * s / K * 165 / 2**16 adc_bit_values / K in Q11.20 notation
controller.changeMode(True)
controller.changeSetpoint(25420)    # ~ 24 °C   (temperature + 40) / 165 * 2**16 in adc_bit_values / K
controller.changeLowerOutputLimit(0)
controller.changeUpperOutputLimit(4095)
controller.changeSampleTime(2000)
#controller.changeOutput(4095.0)
controller.sendNewValues()

#print("\n")
#controller.printEverything()
#print("\n")

try:
    fileToWrite=open("data/temperature_data"+(str(datetime.now())[:19]).replace(" ", "_")+".txt",'w', buffering=1)
except FileNotFoundError:
    fileToWrite=open("temperature_data"+(str(datetime.now())[:19]).replace(" ", "_")+".txt",'w', buffering=1)

fileToWrite.write("# The first coloumn of data is the time, the second is the  temperature and the last is the  output of the controller.\n\n")
fileToWrite.write("# The settings of the controller are:\n"+"# kp: {kp}, ki: {ki}, kd: {kd}, setpoint: {setpoint} ,sampling interval: {sampling_interval} ms\n\n".format(kp=controller.getKp(), ki=controller.getKi(), kd=controller.getKd(), setpoint=controller.getSetpoint(), sampling_interval=controller.getSampleTime()))

if __name__ == "__main__":

        data=b''
        startTime=time.time()
        temperature=controller.sendTemperature()

        #Sends and reads the data in an infinite loop.
        while True:
            if time.time() - startTime > controller.sampleTime / 2000:
                temperature = controller.sendTemperature()
                startTime=time.time()

            #Read the answer of the Arduino with Cbor and Cobs.
            recievedByte=controller.readByte()

            if recievedByte==b'\x00':
                #Rememerber that the code on the Arduino must not contain any Serial.print()-functions.
                #If this is not the case than the communication goes to shit.
                try:
                    result = cbor2.loads(cobs.decode(data))
                    try:
                        if result.get(constants.MessageType.set_input, constants.MessageCode.error_invalid_command) == constants.MessageCode.messageAck:
                            line = "{timestamp},{temp2:f},{temperature:d},{output}".format(timestamp=datetime.utcnow(), temp2=temperature/2**16*165-40, temperature=temperature, output=result[constants.MessageType.callback_update_value])
                            fileToWrite.write(line+"\n")
                            print(line)
                    except KeyError as e:
                        print('error', data)
                except (cobs.DecodeError, cbor2.decoder.CBORDecodeError) as e:
                    print(e, data)

                #Reinitialize the bytearray for new data.
                data=b''
            else:
                data = data + recievedByte
                #print(data)
                #Sleep the script to reduce the cpu load.
                #0.001 is the minimal sample time of the controller.
                time.sleep(0.1)
fileToWrite.close()
