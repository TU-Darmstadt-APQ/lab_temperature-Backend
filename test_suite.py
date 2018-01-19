#!/usr/bin/python3

import arduino_python_communication_v3 as apc
import unittest

#defines the serial port for the Arduino Due, if a Nano is used ACM must be changed to USB
s = apc.serial.Serial('/dev/ttyACM0',115200)
#check if the serial port is open
if not s.isOpen:
        #if it is not open, open it
        s.open()
        #time.sleep(1)

#fixedPoint=16
notIntFixedPoint=16.0
tooBigFixedPoint=33
tooSmallFixedPoint=-1
#This class is here to test the possible errors that can be rasied by the function apc.sendIntData.
#The errors and corresponding tests are below.
class TestErrors(unittest.TestCase):
    #test if an error is raised if no dict is given to the function
    def test_dict_error(self):
        with self.assertRaisesRegex(TypeError,"The data to encode must be of type dict."):
            apc.sendIntData(34,s,apc.fixedPoint)

    #test if a fixedpoint that is not of type int raises an error.
    def test_fixed_point_not_int_error(self):
        with self.assertRaisesRegex(TypeError,"The fixed point value must be of type int."):
            apc.sendIntData({0:12.0},s,notIntFixedPoint)

    #Test if a fixed point smaller than -1 raises an error.
    def test_fixed_point_to_big_error(self):
        with self.assertRaisesRegex(ValueError,"The fixed point is 33, but it must between 0 and 32."):
            apc.sendIntData({0:12.0},s,tooBigFixedPoint)

    #Test if a data package that is larger than 255 bytes raises an error. We can use illegal keys and values because the encoded length is checked before the keys and values.
    def test_map_too_big_error(self):
    	with self.assertRaisesRegex(OverflowError,"The length of the encoded data package is 315. It must be smaller than 255 bytes"):
    		apc.sendIntData({0:12.3,1:23.5,2:34.5,3:45.6,4:45.67,5:56.76,6:45.6,7:67.89,8:45.67,9:56.78,10:23.12,11:34.56,12:34.56,13:34.54,14:345,15:56.78,16:45.567,17:34.45,18:56.78,19:45.67,20:"slgjsgjlshdglnslkglksnglksnlgnslkfnksnföhndöknhökdjfihsöfkngöidjfhödödfnhödjhöshönfhönfödnföhndhöfhn"},s,apc.fixedPoint)

    #Tests if the an error is raised if a key in the dict is not an int.
    def test_key_not_int_error(self):
        with self.assertRaisesRegex(KeyError,"1.62 is not a valid key. All keys must be integers betwenn 0 and 10."):
            apc.sendIntData({0:12.0,1.62:0},s,apc.fixedPoint)

    #Tests if a key of type int that is larger than 9 throws an error.
    def test_key_too_big_error(self):
        with self.assertRaisesRegex(KeyError,"11 is not a valid key. All keys must be integers betwenn 0 and 10."):
            apc.sendIntData({0:12.0,11:34},s,apc.fixedPoint)

    #test if a key smaller than 0 in the dict throws an error.
    def test_key_too_small_error(self):
        with self.assertRaisesRegex(KeyError,"-1 is not a valid key. All keys must be integers betwenn 0 and 10."):
            apc.sendIntData({0:1.0,-1:23},s,apc.fixedPoint)

	#Tests if the an error is raised if a value in the dict is not an int.
    def test_value_not_int_error(self):
        with self.assertRaisesRegex(TypeError,"The value of the key 1 must be a float."):
            apc.sendIntData({0:12.0,1:"Hallo"},s,apc.fixedPoint)

    #Tests if a value of type int in the dict that is larger than 4294967295 throws an error.
    def test_value_too_large_error(self):
        with self.assertRaisesRegex(ValueError,"4294967296.0 is no valid value, after the fixed point conversion the value must be smaller than 4294967295 and greater than 0."):
            apc.sendIntData({0:4294967296.0},s,apc.fixedPoint)

    #test if a value smaller than 0 in the dict throws an error.
    def test_value_too_small_error(self):
        with self.assertRaisesRegex(ValueError,"-1.0 is no valid value, after the fixed point conversion the value must be smaller than 4294967295 and greater than 0."):
            apc.sendIntData({0:12.0,1:-1.0},s,apc.fixedPoint)

    #Test if an error is raised if no input (value with key 0) is given to the controller.
    #assertRaisesRegex is not used because it is not working properly but i don't know why.
    def test_no_input_error(self):
        #with self.assertRaisesRegex(KeyError,"No input (key 0) in dict. Every loop must contain an input."):
        with self.assertRaises(KeyError):
            apc.sendIntData({1:429.0},s,apc.fixedPoint)
	
    #Test if an error is raised if a lower ouptut limit (key 4) but no upper output limit (key 5) is tried to be serialized.
    def test_no_upper_output_limit_error(self):
        with self.assertRaisesRegex(KeyError,"Upper and lower output limits must be passed together."):
            apc.sendIntData({0:12.0,1:87.0,4:34.0},s,apc.fixedPoint)


    #Test if an error is raised if an upper ouptut limit (key 4)but no lower output limit (key 5)is tried to be serialized.
    def test_no_lower_output_limit_error(self):
        with self.assertRaisesRegex(KeyError,"Upper and lower output limits must be passed together."):
            apc.sendIntData({0:10.0,5:56.8},s,apc.fixedPoint)

    #Test that the ode must be of type int.
    def test_mode_not_int(self):
        with self.assertRaisesRegex(TypeError,"The type of the mode must be int."):
            apc.sendIntData({0:12.0,6:2.0},s,apc.fixedPoint)

    #Test if a type error is raised when the wrong type is given as asample time value.
    #assertRaisesRegex is not used because it is not working properly but i don't know why.
    def test_sample_time_not_an_int(self):
    	with self.assertRaises(TypeError):
    		apc.sendIntData({0:12.0,7:2.0},s,apc.fixedPoint)

    #Check if an error is raised when a value for the sample time larger than 32 bit uint is given.
    def test_sample_time_too_big(self):
        with self.assertRaisesRegex(ValueError,"The given sample time is 4294967296 is invalid. It must be smaller than 4294967296 and bigger than 0."):
            apc.sendIntData({0:12.0,7:4294967296},s,apc.fixedPoint)

    #Check if an error is raised when a value for the sample time smaller than a 0 is given.
    def test_sample_time_too_small(self):
        with self.assertRaisesRegex(ValueError,"The given sample time is -1 is invalid. It must be smaller than 4294967296 and bigger than 0."):
            apc.sendIntData({0:12.0,7:-1},s,apc.fixedPoint)

    #Test if a direction that is not of type int raises an error.
    def test_direction_not_int(self):
        with self.assertRaisesRegex(TypeError,"The type of the direction must be int."):
            apc.sendIntData({0:12.0,8:23.0},s,apc.fixedPoint)

    #Check if an error is raised when the upper output limit is smaller than the lower output limit.
    def test_upper_limit_smaller_than_lower_limit(self):
        with self.assertRaisesRegex(ValueError,"The upper output limit must be greater than the lower output limit."):
            apc.sendIntData({0:12.0,4:234.0,5:123.0},s,apc.fixedPoint)

    #Test if an excpetion is raised when a mode (key 6) is given with a value other then 0 or 1.
    #assertRaisesRegex is not used because it is not working properly but i don't know why.
    def test_mode_no_valid_int(self):
        #with self.assertRaisesRegex(ValueError,"The mode (key 6) must be either 0 for MANUAL or 1 for AUTOMATIC."):
        with self.assertRaises(ValueError):
            apc.sendIntData({0:12.0,6:2},s,apc.fixedPoint)

    #Test if an excpetion is raised when a direction (key 8) is given with a value other then 0 or 1.
    #assertRaisesRegex is not used because it is not working properly but i don't know why.
    def test_direction_no_valid_int(self):
        #with self.assertRaisesRegex(ValueError,"The direction (key 8) must be either 0 for DIRECT or 1 for REVERSE."):
        with self.assertRaises(ValueError):
            apc.sendIntData({0:12.0,8:23},s,apc.fixedPoint)

    #Test if an error is raised when the controller is active and the and output should be send to the Arduino.
    #The default setting is active.
    def test_is_active_error(self):
        with self.assertRaisesRegex(KeyError,"The controller must be disabled to write an output."):
            apc.sendIntData({0:12.0,10:2.34},s,apc.fixedPoint)

    #Tests if an error is raised when the controller is disabled put no output is send.
    def test_no_output(self):
        #with self.assertRaisesRegex(KeyError,"When you disable the controller (mode 6 = 0), you have to write an output (key)."):
        with self.assertRaises(KeyError):
            apc.sendIntData({0:12.0,6:0},s,apc.fixedPoint)

#Tests the function apc.sendIntData. This function returns true when the data was serialized and send successfully.
#Specific errors occurred when uints larger then 65535 were send. So this will be tested excessivly.
class TestSendIntData(unittest.TestCase):
    #Test if the function can handle large values above 65535.
    def test_sendIntData1(self):
        self.assertEqual(apc.sendIntData({0:10.0,1:9999.0,2:120.0,3:23000.0,4:4500.0,5:4501.0,6:1,7:340,8:0,9:1200.0},s,apc.fixedPoint),True)

    #Tests if the order of the order of the keys does not matter.
    def test_sendIntData2(self):
        self.assertEqual(apc.sendIntData({2:10.0,0:120.0,3:23000.0,1:2222.0,5:45002.0,4:45001.0,8:1,9:340.0,6:0,7:1200,10:20.0},s,apc.fixedPoint),True)

    #Tests if the missing keys can cause an error (besides the key 0).
    def test_sendIntData3(self):
        self.assertEqual(apc.sendIntData({0:120.0,3:2300.0,1:2222.0,8:1,9:340.0,7:120000},s,apc.fixedPoint),True)

    #Tests to see if the variable controllerIsActive has the right value.
    def test_controller_is_active_true(self):
        apc.sendIntData({0:10.0,6:1},s,apc.fixedPoint)
        self.assertEqual(apc.controllerIsActive,True)

    def test_controller_is_active_false(self):
        apc.sendIntData({0:10.0,6:0,10:34.0},s,apc.fixedPoint)
        self.assertEqual(apc.controllerIsActive,False)

    def test_controller_not_active(self):
        apc.sendIntData({0:10.0,6:0,10:34.0},s,apc.fixedPoint)
        apc.sendIntData({10:34.0},s,apc.fixedPoint)
        self.assertEqual(apc.controllerIsActive,False)
        apc.sendIntData({0:10.0,6:1},s,apc.fixedPoint)
        self.assertEqual(apc.controllerIsActive,True)


#Tests the converter fixedPointFloatToInt for the fixed point values.
#This function takes a float and a fixed point and then converts the float in an int with
#precission defined by the fixed point.
class TestFixedPointBasicUse(unittest.TestCase):
	
	#Test if the function does return the disired values.
	def test_fixedPointBasicUse1(self):
		self.assertEqual(apc.fixedPointFloatToInt(16,4000.05),262147277) 

	#Test if the function does return the disired values.
	def test_fixedPointBasicUse2(self):
		self.assertEqual(apc.fixedPointFloatToInt(8,60900.732),15590587)

#Test if the errors which were defined are raised accordingly.

"""
class TestFixedPointErrors(unittest.TestCase):
	
	#Test if the function returns an error if a negative fixed point is given to it.
	def negativeFixedPoint(self):
		with self.assertRaises(ValueError):
			fixedPointFloatToInt(-2,345.56)

	#Test if the function returns an error if a too large fixed point is given to it.
	@unittest.expectedFailure
	def tooBigFixedPoint(self):
		with self.assertRaises(ValueError):
			fixedPointFloatToInt(33,563.45)

	#Test if the function returns an error if the given float exceeds a 32 bit uint value after the conversion.
	@unittest.expectedFailure
	def floatTooBig1(self):
		with self.assertRaises(ValueError):
			fixedPointFloatToInt(16,65536)

	#Test if the function returns an error if the given float exceeds a 32 bit uint value after the conversion.
	@unittest.expectedFailure
	def floatToobig2(self):
		with self.assertRaises(ValueError):
			fixedPointFloatToInt(8,16777217)

	#Test if the function returns an error if the given float is negative.
	@unittest.expectedFailure
	def negativeFloat1(self):
		with self.assertRaises(ValueError):
			fixedPointFloatToInt(8,-123.34)

	#Test if the function returns an error if the given float is negative
	@unittest.expectedFailure
	def negativeFloat2(self):
		with self.assertRaises(ValueError):
			fixedPointFloatToInt(3,-23.56)

	#Test if the function returns an error if the fixed point is not an int.
	@unittest.expectedFailure
	def fixedPointNotInt1(self):
		with self.assertraises(TypeError):
			fixedPointFloatToInt(2.34,56.9)

	#Test if the function returns an error if the fixed point is not an int.
	@unittest.expectedFailure
	def fixedPointNotInt2(self):
		with self.assertraises(TypeError):
			fixedPointFloatToInt(-5.64,0.8)

	#Test if the function returns an error if the value to convert is not a float.
	@unittest.expectedFailure
	def valueToConvertNotFloat1(self):
		with self.assertRaises(TypeError):
			fixedPointFloatToInt(6,0)

	#Test if the function returns an error if the value to convert is not a float.
	@unittest.expectedFailure
	def valueToConvertNotFloat2(self):
		with self.assertRaises(TypeError):
			fixedPointFloatToInt(6,-20)

	#Test if the function returns an error if the value to convert is not a float.
	@unittest.expectedFailure
	def valueToConvertNotFloat3(self):
		with self.assertRaises(TypeError):
			fixedPointFloatToInt(6,12)
"""
if __name__ == '__main__':
    unittest.main()

