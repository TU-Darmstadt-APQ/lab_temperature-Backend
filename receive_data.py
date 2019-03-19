#!/usr/bin/env python3

from arduino_python_communication_v3 import *
from datetime import datetime

import constants

#Set the parameters for the PID controller.
#Be carefull when setting a high Kd value and a small sampletime, this will result in the controller outputing either the max. output or the min. output
#when there are changes in the input.

controller = None
controller_ip = os.getenv("CONTROLLER_IP")
if controller_ip is not None:
  controller = PIDSenderEthernet(controller_ip)

controller_serial = os.getenv("CONTROLLER_SERIAL")
if controller_serial is not None:
  if controller is not None:
    controller = PIDSenderSerial(controller_serial)
  else:
    raise RuntimeError("Error. More than one controller type specified. Aborting.'")

if controller is None:
  raise RuntimeError("Neither \"CONTROLLER_IP\" nor \"CONTROLLER_SERIAL\" environmental variable found. Cannot create controller.")

#Send the main settings to the controller.
#controller.sendIntData({0:22.0,1:controller.getKp(),2:controller.getKi(),3:controller.getKd(),6:controller.getControllerActivity(),7:controller.getSampleTime(),8:controller.getDirection(),9:controller.getSetpoint()})

#controller.reset()
controller.begin(sensorUID="DhJ",type="humidity")
#controller.begin()
controller.changeDirection(False)
#controller.changeDirection(True)
controller.changeKp(1011120) # 383.0 dac_bit_values / K * 165 / 2**16 adc_bit_values / K in Q11.20 notation
controller.changeKi(1320)    # 0.5 dac_bit_values / (K s) * 165 / 2**16 adc_bit_values / K in Q11.20 notation
controller.changeKd(5280)    # 2.0 dac_bit_values * s / K * 165 / 2**16 adc_bit_values / K in Q11.20 notation
controller.changeMode(True)
#controller.changeMode(False)
controller.changeSetpoint(25022)    # ~ 23 °C   (temperature + 40) / 165 * 2**16 in adc_bit_values / K
controller.changeLowerOutputLimit(0)
controller.changeUpperOutputLimit(4095)
controller.changeSampleTime(2000)
#controller.changeOutput(4095)
controller.set_gain(True)
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
            if time.time()-startTime>controller.sampleTime/2000:
                temperature = controller.sendTemperature()
                startTime=time.time()

            #Read the answer of the Arduino with Cbor and Cobs.
            recievedByte=controller.socket.recv(1)

            if recievedByte==b'\x00':
                #print(data)
                #Rememerber that the code on the Arduino must not contain any Serial.print()-functions.
                #If this is not the case than the communication goes to shit.
                try:
                    result = cbor2.loads(cobs.decode(data))
                    try:
                        if result.get(constants.MessageType.set_input, constants.MessageCode.error_invalid_command) == constants.MessageCode.messageAck:
#                            temperature = (temperature / 2**16 * 165 - 40)
                            line = "{timestamp},{temperature:.2f},{raw},{output}".format(timestamp=datetime.utcnow(), temperature=temperature/2**16*165-40, raw=temperature, output=result[constants.MessageType.callback_update_value])
                            fileToWrite.write(line+"\n")
                            print(line)
                        else:
                           print(result)
                    except KeyError:
                        print("Error: Did not receive an update value callback although we send an updated value")
                        print("RAW data: {data}\nDecoded data: {decoded_data}".format(data=data, decoded_data=cobs.decode(data)))
                except cobs.DecodeError:
                    print("Error decoding data: {data}".format(data=data))

                #Reinitialize the bytearray for new data.
                data=b''
            else:
                data = data + recievedByte
                #Sleep the script to reduce the cpu load.
                #0.001 is the minimal sample time of the controller.
                time.sleep(0.1)
fileToWrite.close()
