#!/home/tobias/anaconda3/bin/python3.6

from arduino_python_communication_v2 import *
import unittest

#defines the serial port for the Arduino Due, if a Nano is used ACM must be changed to USB
s = serial.Serial('/dev/ttyACM0',115200)
#check if the serial port is open
if not s.isOpen:
        #if it is not open, open it
        s.open()
        #time.sleep(1)


#This class is here to test the possible errors that can be rasied by the function sendIntData.
#The errors and corresponding tests are below.
class TestErrors(unittest.TestCase):

    #test if an error is raised if no dict is given to the function
    @unittest.expectedFailure
    def test_dict_error(self):
        self.assertEqual(sendIntData(34,s),None)

    #Tests if the an error is raised if a key in the dict is not an int.
    @unittest.expectedFailure
    def test_key_not_int_error(self):
        self.assertEqual(sendIntData({1.2:34},s),None)

    #Tests if a key of type int that is larger than 9 throws an error.
    @unittest.expectedFailure
    def test_key_too_large_error(self):
        self.assertEqual(sendIntData({11:23},s),None)

    #test if a key smaller than 0 in the dict throws an error.
    @unittest.expectedFailure
    def test_key_too_small_error(self):
        self.assertEqual(sendIntData({-1:23},s),None)

	#Tests if the an error is raised if a value in the dict is not an int.
    @unittest.expectedFailure
    def test_value_not_int_error(self):
        self.assertEqual(sendIntData({1:3.4},s),None)

    #Tests if a value of type int in the dict that is larger than 4294967295 throws an error.
    @unittest.expectedFailure
    def test_value_too_large_error(self):
        self.assertEqual(sendIntData({1:4294967296},s),None)

    #test if a value smaller than 0 in the dict throws an error.
    @unittest.expectedFailure
    def test_value_too_small_error(self):
        self.assertEqual(sendIntData({1:-23},s),None)

    #Test if an error is raised if now input (value with key 0) is given to the controller.
    @unittest.expectedFailure
    def test_no_input_error(self):
        self.assertEqual(sendIntData({1:34},s),None)
	
    #Test if an error is raised if a lower ouptut limit (key 4) but no upper output limit (key 5) is tried to be serialized.
    @unittest.expectedFailure
    def test_no_upper_output_limit_error(self):
        self.assertEqual(sendIntData({0:10,4:56},s),None)

    #Test if an error is raised if an upper ouptut limit (key 4)but no lower output limit (key 5)is tried to be serialized.
    @unittest.expectedFailure
    def test_no_lower_output_limit_error(self):
        self.assertEqual(sendIntData({0:10,5:56},s),None)

    #Test if an excpetion is raised when a mode (key 6) is given with a value other then 0 or 1. 
    @unittest.expectedFailure
    def test_mode_value_error(self):
        self.assertEqual(sendIntData({0:12,6:2},s),None)

    #Test if an excpetion is raised when a direction (key 8) is given with a value other then 0 or 1. 
    @unittest.expectedFailure
    def test_direction_value_error(self):
        self.assertEqual(sendIntData({0:12,8:20},s),None)

#Tests the function sendIntData. This function returns true when the data was serialized and send successfully.
#Specific errors occurred when uints larger then 65535 were send. So this will be tested excessivly.
class TestSendIntData(unittest.TestCase):

	#Test if the function can handle large values above 65535.
	def test_sendIntData1(self):
		self.assertEqual(sendIntData({0:10,1:99999,2:120,3:2300000,4:450000,5:450001,6:0,7:340,8:0,9:120000},s),True)

	#Tests if the order of the order of the keys does not matter.
	def test_sendIntData1(self):
		self.assertEqual(sendIntData({2:10,0:120,3:2300000,1:2222222,5:450002,4:450001,8:1,9:340,6:0,7:120000},s),True)

	#Tests if the missing keys can cause an error (besides the key 0).
	def test_sendIntData1(self):
		self.assertEqual(sendIntData({0:120,3:2300000,1:2222222,8:1,9:340,7:120000},s),True)

if __name__ == '__main__':
    unittest.main()

