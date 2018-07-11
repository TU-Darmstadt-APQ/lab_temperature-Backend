#!/home/tobias/anaconda3/bin/python3

from arduino_python_communication_v3 import *
from datetime import datetime
#import RPi.GPIO as GPIO

#Set the parameters for the PID controller.
#Be carefull when setting a high Kd value and a small sampletime, this will result in the controller outputing either the max. output or the min. output
#when there are changes in the input.


controller = PIDSender('/dev/ttyACM0')
#Send the main settings to the controller.
#controller.sendIntData({0:22.0,1:controller.getKp(),2:controller.getKi(),3:controller.getKd(),6:controller.getControllerActivity(),7:controller.getSampleTime(),8:controller.getDirection(),9:controller.getSetpoint()})

#controller.reset()
controller.begin()
#controller.begin()
controller.changeDirection(1)
controller.changeKp(100.0)
controller.changeKi(0.1)
controller.changeKd(2.0)
controller.changeMode(1)
controller.changeSetpoint(30.00)
controller.changeLowerOutputLimit(0.0)
controller.changeUpperOutputLimit(4095.0)
controller.changeSampleTime(1000)
#controller.changeOutput(100.0)
controller.sendNewValues()

controller.reset()

#print("\n")
#controller.printEverything()
#print("\n")

fileToWrite=open("/home/tobias/throw_away_data/temperature_data"+(str(datetime.now())[:19]).replace(" ", "_")+".txt",'w')

fileToWrite.write("The first coloumn of data is the time, the second is the  temperature and the last is the  output of the controller.\n\n")
fileToWrite.write("The settings of the controller are:\n"+"kp: "+str(controller.kp)+", ki: "+str(controller.ki)+", kd: "+str(controller.kd)+", setpoint: "+str(controller.setpoint)+" ,sample time: "+str(controller.sampleTime)+" ms"+"\n\n")

def communication():
        data=b''

        startTime=time.time()

        temp=controller.sendTemperature()
        tempString="%.2f" % temp

        #Sends and reads the data in an infinite loop.
        while True:

                settingsFile=open("settings.txt","r")

                settings=settingsFile.readlines()

                settingsSampleTime=float(settings[6][:-1])

                settingsFile.close()
                
                if time.time()-startTime>controller.sampleTime/1000:
                        temp=controller.sendTemperature()
                        tempString="%.2f" % temp
                        startTime=time.time()

                #Read the answer of the Arduino with Cbor and Cobs.
                while controller.serialPort.in_waiting:
                        
                        recievedByte=controller.serialPort.read()
                        
                        if recievedByte==b'\x00':
                                #print(data)
                                #Rememerber that the code on the Arduino must not contain any Serial.print()-functions.
                                #If this is not the case than the communication goes to shit.
                                obj=cbor2.loads(cobs.decode(data))
                                
                                if obj==cbor2.CBORSimpleValue(0):
                                        obj=0

                                if type(obj) is int:
                                        fileToWrite.write(str(datetime.now())[:19]+","+tempString+","+str(obj)+"\n")
                                        print(obj, end='', flush=True)

                                #Floats will be rounded to two numbers after the comma.
                                elif type(obj) is float:
                                        fileToWrite.write(str(obj)+"\n")
                                        print("%.2f" % obj, end='', flush=True)

                                #All the other datatypes are printed normally.
                                else:   
                                        if obj != "\n":
                                                fileToWrite.write(str(datetime.now())[:19]+","+tempString+","+str(obj))
                                        print(obj, end='', flush=True)

                                #Reinitialize the bytearray for new data.
                                data=b''
                        else:
                                data = data + recievedByte

def hostServer():
        app.config["SECRET_KEY"]= "secretKey"

        class controllerInterfaceForm(FlaskForm):
                kp=DecimalField("kp")
                ki=DecimalField("ki")
                kd=DecimalField("kd")
                lowerOutputLimit=DecimalField("lowerOutputLimit")
                upperOutputLimit=DecimalField("upperOutputLimit")
                mode=IntegerField("mode")
                sampleTime=IntegerField("sampleTime")
                direction=IntegerField("direction")
                setpoint=DecimalField("setpoint")
                output=DecimalField("output")

        @app.route("/formTest",methods=["post","get"])
        def formTest():

                form=controllerInterfaceForm()

                if form.kp.data != None:
                        controller.changeKp(float(form.kp.data))

                if form.ki.data != None:
                        controller.changeKi(float(form.ki.data))

                if form.kd.data != None:
                        controller.changeKd(float(form.kd.data))

                if form.lowerOutputLimit.data != None:
                        controller.changeLowerOutputLimit(float(form.lowerOutputLimit.data))

                if form.upperOutputLimit.data != None:
                        controller.changeUpperOutputLimit(float(form.upperOutputLimit.data))

                if form.sampleTime.data != None:
                        controller.changeSampleTime(int(form.sampleTime.data))

                if form.setpoint.data != None:
                        controller.changeSetpoint(float(form.setpoint.data))

                if form.output.data != None:
                        #print(form.output.data)
                        if controller.mode==0:
                                controller.changeOutput(float(form.output.data))
                        else:
                                pass

                if request.form.get("mode") == "AUTOMATIC":
                        controller.changeMode(int(1))
                elif request.form.get("mode") == "MANUAL":
                        controller.changeMode(int(0))
                else:
                        pass

                if request.form.get("direction") == "REVERSE":
                        controller.changeDirection(int(1))
                elif request.form.get("direction") == "DIRECT":
                        controller.changeDirection(int(0))
                else:
                        pass

                if bool(controller.getBuffer()):
                        controller.sendNewValues()

                kpValue="%.2f" % (controller.kp)
                kiValue="%.2f" % (controller.ki)
                kdValue="%.2f" % (controller.kd)
                lowerOutputLim="%.2f" % (controller.getLowerOutputLimit())
                upperOutputLim="%.2f" % (controller.getUpperOutputLimit())
                sampleTimeValue="%.2f" % (controller.getSampleTime())
                setpointValue="%.2f" % (controller.getSetpoint())
                outputValue="%.2f" % (controller.getOutput())
                
                if controller.getMode()==0:
                        modeValue="disabled"
                else:
                        modeValue="enabled"

                if controller.getDirection()==0:
                        directionValue="direct"
                else:
                        directionValue="reverse"

                return(render_template("form_test.html",form=form,kpValue=kpValue,kiValue=kiValue,kdValue=kdValue,lol=lowerOutputLim,uol=upperOutputLim,setpointValue=setpointValue,sampleTimeValue=sampleTimeValue,outputValue=outputValue,modeValue=modeValue,directionValue=directionValue))

        app.run(debug=True)

if __name__ == "__main__":
        Thread(target = func1).start()
        Thread(target = func2).start()
        fileToWrite.close()
