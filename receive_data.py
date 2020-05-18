#!/usr/bin/env python3

from datetime import datetime
import os

from arduino_python_communication_v3 import *
import constants

sensor_ip = os.getenv("SENSOR_IP", "localhost")
sensor_port = os.getenv("SENSOR_PORT", 4223)
sensor_uid = os.getenv("SENSOR_UID")
assert sensor_uid is not None, "\"SENSOR_UID\" environment variable not found. Cannot create controller."
sensor_type = os.getenv("SENSOR_TYPE", "temperature")

pid_ki = os.getenv("PID_KI")
assert pid_ki is not None, "\"PID_KI\" environment variable not found. Cannot create controller."
pid_kp = os.getenv("PID_KP")
assert pid_kp is not None, "\"PID_KP\" environment variable not found. Cannot create controller."
pid_kd = os.getenv("PID_KD")
assert pid_kd is not None, "\"PID_KD\" environment variable not found. Cannot create controller."
pid_setpoint = os.getenv("PID_SETPOINT")
assert pid_setpoint is not None, "\"PID_SETPOINT\" environment variable  found. Cannot create controller."

try:
  pid_timeout = int(os.getenv("PID_TIMEOUT"))
except ValueError:
  pid_timeout = None
assert pid_setpoint is not None, "\"PID_TIMEOUT\" environment variable  found. Cannot create controller."

dac_enable_gain = os.getenv("OUTPUT_ENABLE_GAIN", True)

# K is Kelvin
# conversion:
# kp: dac_bit_values / K * 165 / 2**16 adc_bit_values / K in Q11.20 notation
# ki: dac_bit_values / (K s) * 165 / 2**16 adc_bit_values / K in Q11.20 notation
# kd: dac_bit_values * s / K * 165 / 2**16 adc_bit_values / K in Q11.20 notation
pid_kp = int(float(pid_kp) * 165 / 2**16 * 2**20)
pid_ki = int(float(pid_ki) * 165 / 2**16 * 2**20)
pid_kd = int(float(pid_kd) * 165 / 2**16 * 2**20)
pid_setpoint = int((float(pid_setpoint) + 40) / 165 * 2**16)    # (temperature + 40) / 165 * 2**16 in adc_bit_values / K

controller = None
controller_ip = os.getenv("CONTROLLER_IP")
controller_port = os.getenv("CONTROLLER_PORT", 4223)
if controller_ip is not None:
  controller = PIDSenderEthernet(controller_ip=controller_ip, controller_port=controller_port, sensor_ip=sensor_ip, sensor_port=sensor_port)

controller_serial = os.getenv("CONTROLLER_SERIAL")
if controller_serial is not None:
  assert controller is None, "Error. More than one controller type specified. Aborting." 
  controller = PIDSenderSerial(serial_port=controller_serial, sensor_ip=sensor_ip, sensor_port=sensor_port)

assert controller is not None, "Neither \"CONTROLLER_IP\" nor \"CONTROLLER_SERIAL\" environment variable found. Cannot create controller."

#Send the main settings to the controller.
controller.begin(sensorUID=sensor_uid, sensor_type=sensor_type)
#controller.begin()
controller.set_pid_direction(False)
#controller.set_pid_direction(True)
controller.set_kp(pid_kp)
controller.set_ki(pid_ki)
controller.set_kd(pid_kd)
controller.set_pid_enable(True)
#controller.set_pid_enable(False)
controller.set_setpoint(pid_setpoint)
controller.set_output_limit_low(0)
controller.set_output_limit_high(4095)
controller.set_timeout(pid_timeout)
#controller.set_output(4095)
controller.set_gain(dac_enable_gain)
controller.sendNewValues()
try:
    fileToWrite=open("logs/temperature_data_"+(str(datetime.now())[:19]).replace(" ", "_")+".txt",'w', buffering=1)
except FileNotFoundError:
    fileToWrite=open("temperature_data_"+(str(datetime.now())[:19]).replace(" ", "_")+".txt",'w', buffering=1)

fileToWrite.write("# The first coloumn of data is the time, the second is the  temperature and the last is the  output of the controller.\n\n")
fileToWrite.write("# The settings of the controller are:\n# kp: {kp}, ki: {ki}, kd: {kd}, setpoint: {setpoint}, sampling interval: {sampling_interval} ms\n\n".format(kp=controller.getKp(), ki=controller.getKi(), kd=controller.getKd(), setpoint=controller.getSetpoint(), sampling_interval=1000))
if __name__ == "__main__":

        data=b''
        startTime=time.time()
        temperature=controller.sendTemperature()

        #Sends and reads the data in an infinite loop.
        while True:
            if time.time() - startTime >= 1:
                temperature = controller.sendTemperature()
                startTime = time.time()

            #Read the answer of the Arduino with Cbor and Cobs.
            recievedByte=controller.socket.recv(1)

            if recievedByte==b'\x00':
                #print(data)
                try:
                    result = cbor2.loads(cobs.decode(data))
                    try:
                        if result.get(constants.MessageType.set_input, constants.MessageCode.error_invalid_command) == constants.MessageCode.messageAck:
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
