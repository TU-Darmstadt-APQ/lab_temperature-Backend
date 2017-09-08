# lab_temperature-Backend
Lab Temperature Controller (Python Code)

- arduino_python_communication.ino:
	 
	This part contains the software for the Arduino consisting of an PID controller and a part for serial communication implemented with COBS and CBOR as en- and decoding method. The decoding is achived with the cobs.4-library by
	Patrick  Baus and Arduino-Cbor-master library. The PID controller is realized with the PID library by Brett Beauregard.  

- arduino_python_communication.py:
	
	This part consists of a an encoder for dicts and other data called sendData(...), this function encodes data using COBS and CBOR. To dispatch data to the PID controller the following format is used. The keys consist of the ints
	0 to 9. Each int represents different parameters and variables for the PID controller:
		
		-0: The temperature given to controller as Input, datatype double.
		-1: The Parameter Kp representing the proportional part of the controller, datatype double.
        -2: The Parameter Ki representing the integral part of the controller, datatype double.
        -3: The Parameter Kd representing the differential part of the controller, datatype double.
		-4: The lower output limit for the Output (should only be send with an upper limit), datatype int (default is 0). 
		-5: The upper output limit for the Output (should only be send with a lower limit), datatype int (default is 255).
		-6: The mode of the controller AUTOMATIC or MANUAL, the values which can be send are 0 (MANUAL) or 1 (AUTOMATIC), data type int, default is AUTOMATIC.
		-7: Set the sample time of the controller, default is 200 ms (value: 200), data type is int.
		-8: Controller direction is either DIRECT or REVERSE, the value send is eihter 0 (DIRECT) or 1 (REVERSE), the default is DIRECT, datatype is int.
		-9: The setpoint which should be achieved by the controller, datatype is double.

The hardware part of which the controller consits are a Raspberry Pi, Arduino Due, Tinkerforge Temperature Brick and a Peltier module (at the moment).
