import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import square

settings = {
    'xMirror_output': 'PXI1Slot2/ao0',
    'yMirror_output': 'PXI1Slot2/ao1',
    'laser_output': '/PXI1Slot2/port0/line0',

    'Fs': 30000,  # in samples/s
    'V_X': 7.8, # in V
    'V_Y': 3.2, # in V
    'duration': 5, # in s
    'minV' : -10, # in Volts. Minimum voltage for mirror
    'maxV' : 10, # in Volts. Maximum voltage for mirror

#9,3 is 0,0 for test on  12/14/23
#12.5mm/2V

}

def setupTasks(settings):
    # calculate the trial duration needed to sample every region and numSamples

    numSamples = settings['duration'] * settings['Fs']
  
    ao_task = nidaqmx.Task()
    ao_task.ao_channels.add_ao_voltage_chan(settings['xMirror_output'], name_to_assign_to_channel='x_out')
    ao_task.ao_channels.add_ao_voltage_chan(settings['yMirror_output'], name_to_assign_to_channel='y_out')
    ao_task.timing.cfg_samp_clk_timing(settings['Fs'], samps_per_chan=numSamples)

    
    do_task = nidaqmx.Task()
    do_task.do_channels.add_do_chan(settings['laser_output'], name_to_assign_to_lines='laser')
    do_task.timing.cfg_samp_clk_timing(settings['Fs'], samps_per_chan=numSamples)

    return ao_task, do_task

def align(ao_task, do_task, settings):
    ### Generate alignment pulse based on duration and voltages in settings ###

    
    ## Construct stimulus
    
    t = np.arange(0,settings['duration'],1/settings['Fs'])

    lz1 = 0.5 * (square(2*np.pi*30*t,.001)+1)

    x1 = np.zeros(len(lz1))
    y1 = np.zeros(len(lz1))
    x1[:] = settings['V_X']
    y1[:] = settings['V_Y']
  
    lz1[-1] = 0

    ao_out = np.zeros((2,len(lz1)))
    ao_out[0,:] = x1
    ao_out[1,:] = y1
    do_out = np.array(lz1 == True,dtype=bool)
  
    ## writing daq outputs onto device
    do_task.write(do_out,timeout=10+settings['duration'])
    ao_task.write(ao_out,timeout=10+settings['duration'])
    do_task.start()
    ao_task.start()

    do_task.wait_until_done(timeout=10+settings['duration'])
    

    ## stopping tasks
    do_task.stop()
    ao_task.stop()
  
    do_task.close()
    ao_task.close()
  
    ao_data = ao_out
    do_data = do_out

    return ao_data, do_data

ao_task, do_task = setupTasks(settings)
ao_data, do_data = align(ao_task, do_task, settings)
print("Task complete.")


# plt.plot(do_data)
# plt.show()
# plt.close()
