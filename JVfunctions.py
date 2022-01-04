# Import necessary packages
import pymeasure
from pymeasure.instruments.keithley import Keithley2400
import numpy as np
import pandas as pd
from time import sleep
from time import time
from matplotlib import pyplot as plt
import datetime
import os


print('test')


##Basic JV scan function
#############################################################################
#define function with inputs
def JVscan(cell_name, cell_area, v_in, v_fin, averages, data_points, plc, bufdelay, prebias, biasV, biastime, pulse, pulsedelay):
    direc = 'C:/Users/IECs Finest/Desktop/Jupyter/JV/'
    os.chdir(direc)
    now = datetime.datetime.now()                  #Get date and time
    currtime = now.strftime("%m%d%y%H%M")          #get formatted time
    foldtime = now.strftime("%m-%d-%y")
    if os.path.isdir(foldtime) is False:
        os.mkdir(foldtime)
    os.chdir(foldtime)

    if os.path.isdir(cell_name) is False:
        os.mkdir(cell_name)
    os.chdir(cell_name)
    
    # Connect and configure the instrument
    sourcemeter = Keithley2400('GPIB0::24::INSTR')
    sourcemeter.reset()                        #reset meter
    sourcemeter.use_front_terminals()          #sets to use front terminals
    sourcemeter.compliance_voltage = 10        # Sets the compliance voltage to 10 V

    sourcemeter.apply_voltage()                #set meter to apply voltage
    sourcemeter.measure_current(nplc=plc, current=1e-2, auto_range=True) #set meter to measure current

    #sourcemeter.config_voltage_source()

    sleep(bufdelay) # wait here to give the instrument time to react
    sourcemeter.config_buffer(averages,bufdelay) #configure the buffer

    # Allocate arrays to store the measurement results
    voltagedown = np.linspace(v_fin, v_in, num=data_points)
    currentdown = []
    currentdown_stds = []
    powerdown=[]

    voltageup = np.linspace(v_in, v_fin, num=data_points)
    currentup = []
    currentup_stds = []
    powerup=[]
    
    now = datetime.datetime.now()                  #Get date and time
    currtime = now.strftime("%m%d%y%H%M")          #get formatted time
    foldtime = now.strftime("%m-%d-%y")

    
    print('scan1')                                 
    sourcemeter.enable_source()                    # enable the source
    
    #Prebias the cell for steady state or bias pretreatment
    if prebias== True:
        print('Prebiasing at ')
        print(str(biasV)+' volts')
        sourcemeter.source_voltage= biasV                #prebias at "final voltage"
        sourcemeter.measure_current(nplc=plc, current=1e-2, auto_range=True) #set meter to measure current
        sleep(biastime)
    
    #Begin the actual scan
    # Loop through each voltage point, measure and record the current density
    print('Scan Down')
    for i in range(data_points):
        sourcemeter.source_voltage= voltagedown[i]
        sourcemeter.measure_current(nplc=plc, current=1e-2,auto_range=True)
        sourcemeter.reset_buffer()
        #sleep(0.1)
        sourcemeter.start_buffer()
        sleep(bufdelay)
        #sourcemeter.wait_for_buffer(timeout=1, interval=0.05)
        
        # Record the average and standard deviation of the current density
        currentdown.append(sourcemeter.means[1]/cell_area)
        currentdown_stds.append(sourcemeter.standard_devs[1]/cell_area)
        #Calculate the power (which in this case is equal to efficiency)
        powerdown.append(voltagedown[i]*sourcemeter.means[1]/cell_area*-1000)
        if pulse==True:
            sourcemeter.source_voltage = biasV
            sourcemeter.measure_current(nplc=plc, current=1e-2,auto_range=True)
            sleep(pulsedelay)
    
    # Loop through each voltage point, measure and record the current density
    print('Scan Up')
    for i in range(data_points):
        sourcemeter.source_voltage = voltageup[i]
        sourcemeter.reset_buffer()
        #sleep(0.1)
        sourcemeter.start_buffer()
        sleep(bufdelay)
        #sourcemeter.wait_for_buffer(timeout=1, interval=0.05)

        # Record the average and standard deviation of the current density
        currentup.append(sourcemeter.means[1]/cell_area)
        currentup_stds.append(sourcemeter.standard_devs[1]/cell_area)
        #Calculate the power (which in this case is equal to efficiency)
        powerup.append(voltageup[i]*sourcemeter.means[1]*-1000/cell_area)
        if pulse==True:
            sourcemeter.source_voltage = biasV
            sourcemeter.measure_current(nplc=plc, current=1e-2,auto_range=True)
            sleep(pulsedelay)

    data1 = pd.DataFrame({
        'Currentup (A)': currentup,
        'Voltageup (V)': voltageup,
        'Powerup (mW/cm2)': powerup,
        'Currentup Std (V)': currentup_stds,
        'Currentdown (A)': currentdown,
        'Voltagedown (V)': voltagedown,
        'Power down (mW/cm2)': powerdown,
        'Currentdown Std (V)': currentdown_stds,
    })
    filename=cell_name+currtime+str(data_points)+'_pts'+str(averages)+'_avg'+str(plc)+'_plcs'+'_JV.csv'
    data1.to_csv(filename)
    plt.plot(data1['Voltageup (V)'],data1['Currentup (A)'])
    plt.plot(data1['Voltagedown (V)'],data1['Currentdown (A)'])
    plt.xlim(-.6,1.2)
    plt.ylim(-25/1000,25/1000)
    sourcemeter.shutdown()

#JVscan(v_in, v_fin, averages, data_points, plc, bufdelay, prebias)


################################################################################################################
#MPPT function
def MPPT(plc,averages, data_points, i_volt, timedelay):
    
    #define some variables and get current date and time
    bufdelay=0.1 # delay time to ensure there is enough time to communicate with SMU
    #i_volt=0.001 #initial guess voltage, can be changed to start mppt scan at fwd bias or near mppt instead of near 0
    now = datetime.datetime.now()                  #Get date and time
    currtime = now.strftime("%m%d%y%H%M")          #get formatted time
    foldtime = now.strftime("%m-%d-%y")

    
    # Connect and configure the instrument
    sourcemeter = Keithley2400('GPIB0::24::INSTR') #Connect 
    sourcemeter.reset()
    sourcemeter.use_front_terminals()
    sourcemeter.compliance_voltage = 2        # Sets the compliance voltage to 2V

    sourcemeter.apply_voltage()
    sourcemeter.measure_current(nplc=plc, current=1e-2, auto_range=True)

    sleep(bufdelay) # wait here to give the instrument time to react
    sourcemeter.config_buffer(averages,bufdelay)



    #set voltage to initial voltage setpoint
    volt=i_volt
    sourcemeter.source_voltage = volt

    pval=0.1 #initial value for power
    pscale=0.01 #scaling factor
    scale=0.01 #scaling factor

    sourcemeter.enable_source()  
    voltnew=volt
    start_time = time() # get start time of measurement for time tracking

    try: #inside a try loop so you can interrupt the kernel and still save the current measurement
        while True: #This makes the mppt scan go until you press abort, you could set it to do a number of scans instead
            sourcemeter.enable_source() # enable source
            
            # Allocate arrays to store the measurement results
            voltages = []
            currents =  []
            current_stds = [] 
            powers= []
            meas_num=[]

            sourcemeter.source_voltage = volt

            pval=0.1
            pscale=0.01
            scale=0.01 #this value scales the random number the voltage is scaled by: smaller number will result in more stable mppt but slower time to reach mppt
            sourcemeter.enable_source()  
            voltnew=volt
            now = datetime.datetime.now()
            currtime = now.strftime("%m%d%y%H%M")


            for i in range(data_points):
                direc = 'C:/Users/IECs Finest/Desktop/Jupyter/MPPT/'
                os.chdir(direc)
                now = datetime.datetime.now()                  #Get date and time
                currtime = now.strftime("%m%d%y%H%M")          #get formatted time
                foldtime = now.strftime("%m-%d-%y")
                if os.path.isdir(foldtime) is False:
                    os.mkdir(foldtime)
                os.chdir(foldtime)

                if os.path.isdir(cell_name) is False:
                    os.mkdir(cell_name)
                os.chdir(cell_name)
                
                
                random_val=scale*np.random.rand(1).tolist()[0] #a random value to increase the voltage set point between 0 and 10mV
                 #increase new voltage based on random number
                sourcemeter.source_voltage=voltnew #set voltage
                sourcemeter.reset_buffer() #reset buffer
                sleep(bufdelay)                  #wait
                sourcemeter.start_buffer()  
                sleep(bufdelay)

                # Record the average and standard deviation
                voltages.append(voltnew) #record the voltage the cell is at
                currents.append(sourcemeter.means[1]*1000/cell_area) #record the average current measurement of the number of averages
                current_stds.append(sourcemeter.standard_devs[1]) #record the standard deviation
                powers.append(currents[i]*voltnew*-1) #calculate and record the power
                pvalnew=powers[i] #update pval to calculate the scaling factor
                pscale=pvalnew-pval #the difference in power from the last to new measurement, tells wether the voltage iteration made power higher or lower
                vscale=voltnew-volt #the difference in voltage from last to new measurement, telling whether you increased or decreased the voltga
                sleep(timedelay) #allows you to slow down measurements by adding a wait time (you will get fewer points)
                meas_num.append(time()-start_time) #record the time since the measurement started
                volt=voltnew #update the old voltage with the new voltage since the measurement cycle is over
                
                #control algorithm using the perturb and observe method
                if pscale>0:
                    if vscale>0:
                        voltnew=volt+random_val
                    else:
                        voltnew=volt-random_val
                elif pscale<0:
                    if vscale>0:
                        voltnew=volt-random_val
                    else:
                        voltnew=volt+random_val
                else:
                    voltnew=volt
                pval=pvalnew
                print('Pmax = '+str(round(pval,3))+'%'+'                        ',end='\r') #prints the power



            sourcemeter.shutdown() #shuts down source at end of measurement 
            tempdict = {
                        'Measurement_Number' : meas_num,
                        'Voltage' : voltages,
                        'Currents' : currents,
                        'current_stds' : current_stds,
                        'powers' : powers
                    } #put arrays of values in a temporary dictionary to save data
            data=pd.DataFrame(tempdict) #put into a pandas dataframe to save data

            filename= currtime+'_'+str(cell_name)+'MPPT'+'.csv' #define file name
            data.to_csv(filename) #save file
            sleep(1)
            
    except:
        KeyboardInterrupt #this is so the data will save for the current scan you're doing when you interrupt the kernel
        print('Interrupted                      ')
        if len(meas_num)<len(voltages):
            meas_num.append(time()-start_time)
        if len(currents)<len(voltages):
            currents.append(np.nan)
        if len(current_stds)<len(currents):
            current_stds.append(np.nan)
        if len(powers)<len(current_stds):
            powers.append(np.nan)

        sourcemeter.shutdown()  
        tempdict = {
                    'Measurement_Number' : meas_num,
                    'Voltage' : voltages,
                    'Currents' : currents,
                    'current_stds' : current_stds,
                    'powers' : powers
                }
        data=pd.DataFrame(tempdict)

        filename= currtime+'_'+str(cell_name)+'MPPT'+'.csv'
        data.to_csv(filename)
    plt.scatter(tempdict['Measurement_Number'],tempdict['powers'])



    print('Measurement complete')
    print('Files saved: ')
    print(filename)

################################################################################################################
#MPPTJV function
def MPPTJV(plc,averages, data_points, i_volt, timedelay, cell_name, cell_area, v_in, v_fin, bufdelay, prebias, pulse, pulsedelay):
    
    #define some variables and get current date and time
    bufdelay=0.1 # delay time to ensure there is enough time to communicate with SMU
    #i_volt=0.001 #initial guess voltage, can be changed to start mppt scan at fwd bias or near mppt instead of near 0
    now = datetime.datetime.now()                  #Get date and time
    currtime = now.strftime("%m%d%y%H%M")          #get formatted time
    foldtime = now.strftime("%m-%d-%y")

    
    # Connect and configure the instrument
    sourcemeter = Keithley2400('GPIB0::24::INSTR') #Connect 
    sourcemeter.reset()
    sourcemeter.use_front_terminals()
    sourcemeter.compliance_voltage = 2        # Sets the compliance voltage to 2V

    sourcemeter.apply_voltage()
    sourcemeter.measure_current(nplc=plc, current=1e-2, auto_range=True)

    sleep(bufdelay) # wait here to give the instrument time to react
    sourcemeter.config_buffer(averages,bufdelay)



    #set voltage to initial voltage setpoint
    volt=i_volt
    sourcemeter.source_voltage = volt

    pval=0.1 #initial value for power
    pscale=0.01 #scaling factor
    scale=0.01 #scaling factor

    sourcemeter.enable_source()  
    voltnew=volt
    start_time = time() # get start time of measurement for time tracking

    try: #inside a try loop so you can interrupt the kernel and still save the current measurement
        while True: #This makes the mppt scan go until you press abort, you could set it to do a number of scans instead
            sourcemeter.enable_source() # enable source
            
            # Allocate arrays to store the measurement results
            voltages = []
            currents =  []
            current_stds = [] 
            powers= []
            meas_num=[]

            sourcemeter.source_voltage = volt

            pval=0.1
            pscale=0.01
            scale=0.01 #this value scales the random number the voltage is scaled by: smaller number will result in more stable mppt but slower time to reach mppt
            sourcemeter.enable_source()  
            voltnew=volt
            now = datetime.datetime.now()
            currtime = now.strftime("%m%d%y%H%M")


            for i in range(data_points):
                direc = 'C:/Users/IECs Finest/Desktop/Jupyter/MPPT/'
                os.chdir(direc)
                now = datetime.datetime.now()                  #Get date and time
                currtime = now.strftime("%m%d%y%H%M")          #get formatted time
                foldtime = now.strftime("%m-%d-%y")
                if os.path.isdir(foldtime) is False:
                    os.mkdir(foldtime)
                os.chdir(foldtime)

                if os.path.isdir(cell_name) is False:
                    os.mkdir(cell_name)
                os.chdir(cell_name)
                
                
                random_val=scale*np.random.rand(1).tolist()[0] #a random value to increase the voltage set point between 0 and 10mV
                 #increase new voltage based on random number
                sourcemeter.source_voltage=voltnew #set voltage
                sourcemeter.reset_buffer() #reset buffer
                sleep(bufdelay)                  #wait
                sourcemeter.start_buffer()  
                sleep(bufdelay)

                # Record the average and standard deviation
                voltages.append(voltnew) #record the voltage the cell is at
                currents.append(sourcemeter.means[1]*1000/cell_area) #record the average current measurement of the number of averages
                current_stds.append(sourcemeter.standard_devs[1]) #record the standard deviation
                powers.append(currents[i]*voltnew*-1) #calculate and record the power
                pvalnew=powers[i] #update pval to calculate the scaling factor
                pscale=pvalnew-pval #the difference in power from the last to new measurement, tells wether the voltage iteration made power higher or lower
                vscale=voltnew-volt #the difference in voltage from last to new measurement, telling whether you increased or decreased the voltga
                sleep(timedelay) #allows you to slow down measurements by adding a wait time (you will get fewer points)
                meas_num.append(time()-start_time) #record the time since the measurement started
                volt=voltnew #update the old voltage with the new voltage since the measurement cycle is over
                
                #control algorithm using the perturb and observe method
                if pscale>0:
                    if vscale>0:
                        voltnew=volt+random_val
                    else:
                        voltnew=volt-random_val
                elif pscale<0:
                    if vscale>0:
                        voltnew=volt-random_val
                    else:
                        voltnew=volt+random_val
                else:
                    voltnew=volt
                pval=pvalnew
                print('Pmax = '+str(round(pval,3))+'%'+'                        ',end='\r') #prints the power
                JVscan(cell_name, cell_area, v_in, v_fin, averages, data_points, plc, bufdelay, prebias, pulse, pulsedelay)


            sourcemeter.shutdown() #shuts down source at end of measurement 
            tempdict = {
                        'Measurement_Number' : meas_num,
                        'Voltage' : voltages,
                        'Currents' : currents,
                        'current_stds' : current_stds,
                        'powers' : powers
                    } #put arrays of values in a temporary dictionary to save data
            data=pd.DataFrame(tempdict) #put into a pandas dataframe to save data

            filename= currtime+'_'+str(cell_name)+'MPPT'+'.csv' #define file name
            data.to_csv(filename) #save file
            sleep(1)
            
    except:
        KeyboardInterrupt #this is so the data will save for the current scan you're doing when you interrupt the kernel
        print('Interrupted                      ')
        if len(meas_num)<len(voltages):
            meas_num.append(time()-start_time)
        if len(currents)<len(voltages):
            currents.append(np.nan)
        if len(current_stds)<len(currents):
            current_stds.append(np.nan)
        if len(powers)<len(current_stds):
            powers.append(np.nan)

        sourcemeter.shutdown()  
        tempdict = {
                    'Measurement_Number' : meas_num,
                    'Voltage' : voltages,
                    'Currents' : currents,
                    'current_stds' : current_stds,
                    'powers' : powers
                }
        data=pd.DataFrame(tempdict)

        filename= currtime+'_'+str(cell_name)+'MPPT'+'.csv'
        data.to_csv(filename)
    plt.scatter(tempdict['Measurement_Number'],tempdict['powers'])



    print('Measurement complete')
    print('Files saved: ')
    print(filename)

