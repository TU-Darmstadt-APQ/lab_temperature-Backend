# lab_temperature-Backend
This is the code that should be run on a computer (in our case it is a Raspberry Pi) to communicate with the microcontroller. The basic tool to communicate with the controller is the function sendIntData() in the file arduino_python_communication_v3.py. This function takes a dict as an arguement. This dict should only contain keys from 0 to 10, if this is not the case an error will be thrown. Each key is associated with a specfific value for the PID controller:
	
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
		-10: Output value for the controller. One can only write an output value when the controller mode (key 6) is set to MANUAL.

One should keep in mind that the datatypes for the values in the dict are very important, if you have a wrong datatype an error will be thrown.
The file recieve_data.py is an example of how the communication could look like. In this file the temperature data is taken from a Tinkerforge temperature bricklet that is connected to the Pi via a Masterbrick. The settings of the controller are saved in a log-file together with the temperature, the output and the time. The output is send from the microcontroller to the Pi.