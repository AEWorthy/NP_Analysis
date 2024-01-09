import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import threading
import time

settings = {
    'task_name' : 'motorControl',

    'lengthChannel_input':'PXI1Slot2/ai0',
    'forceChannel_input':'PXI1Slot2/ai1',
    'lengthChannel_output':'PXI1Slot2/ao0',
    'forceChannel_output':'PXI1Slot2/ao1',
    'sync':'/PXI1Slot2/port0/line1',


    'Fs':30000, ## in samples/s

    'camera_output':'/PXI1Slot2/port0/line3',
    'cycle_duration': 5,  ## in seconds. Time it takes for full wait-press/hold-release cycle takes (default = 5 seconds).
    'num_cycles' : 200, # number of trials to be completed (default = 200)
    'force_voltage': [1,2,4] ## in V (1V ~= 50mN; default = [1,2,4]).
}


# calculate trial_duration and load example trace_array
trial_duration = (settings['num_cycles'] * settings['cycle_duration'])
minutes = round(trial_duration/60, 2)
print("This experiment will take ~{} minutes to complete...".format(minutes))


def setupTasks(settings):
    numSamples = int(settings['Fs'] * settings['cycle_duration'])

    ai_task = nidaqmx.Task()
    ai_task.ai_channels.add_ai_voltage_chan(settings['lengthChannel_input'],name_to_assign_to_channel='length_in', terminal_config=nidaqmx.constants.TerminalConfiguration(10083))
    ai_task.ai_channels.add_ai_voltage_chan(settings['forceChannel_input'],name_to_assign_to_channel='force_in',terminal_config=nidaqmx.constants.TerminalConfiguration(10083))
    ai_task.timing.cfg_samp_clk_timing(settings['Fs'], samps_per_chan=numSamples)

    ao_task = nidaqmx.Task()
    ao_task.ao_channels.add_ao_voltage_chan(settings['lengthChannel_output'],name_to_assign_to_channel='length_out')
    ao_task.ao_channels.add_ao_voltage_chan(settings['forceChannel_output'],name_to_assign_to_channel='force_out')
    ao_task.timing.cfg_samp_clk_timing(settings['Fs'], samps_per_chan=numSamples)
        
    do_task = nidaqmx.Task()
    do_task.do_channels.add_do_chan(settings['sync'], name_to_assign_to_lines='sync')
    do_task.timing.cfg_samp_clk_timing(settings['Fs'], samps_per_chan=numSamples)

    return (ai_task, ao_task, do_task)


def runTasks(ai_task, ao_task, do_task, settings):
    numSamples = int(settings['Fs'] * settings['cycle_duration'])
    trial_voltage = settings['force_voltage'][np.random.randint(0,3)]
    
    ## make the length command
    ao_out = np.zeros((2,numSamples))
    do_out = np.zeros((numSamples),dtype=bool)
    ao_out[0,:settings['Fs']] = np.arange(0,1,1/settings['Fs'])*5. ## gradually ramp up length command over first second
    ao_out[0,settings['Fs']:] = 5 ## hold length command high
    ao_out[0,-settings['Fs']:] = np.arange(1,0,-1/settings['Fs'])*5 ## gradually ramp down length command over final second

    ### make the force command
    ao_out[1,int(2*settings['Fs']):int(2.03*settings['Fs'])] = np.linspace(0,trial_voltage,int(0.03*settings['Fs'])-1)
    ao_out[1,int(2.03*settings['Fs']):int(3*settings['Fs'])] = trial_voltage ## increase force between seconds 2 and 3; add filter in future
    ao_out[1,int(3*settings['Fs']):int(3.03*settings['Fs'])] = np.linspace(trial_voltage,0,int(0.03*settings['Fs']))

    
    do_out[1:-1] = True

    ## writing daq outputs onto device
    do_task.write(do_out)
    ao_task.write(ao_out)

    ## starting tasks (make sure do_task is started last -- it triggers the others)
    ai_task.start()
    # di_task.start()
    ao_task.start()
    do_task.start()
    do_task.wait_until_done(timeout = settings['cycle_duration'] + 1)

    ## adding data to the outputs
    ai_data = np.array(ai_task.read(numSamples))
    ao_data = ao_out
    do_data = do_out

    ## stopping tasks
    do_task.stop()
    ao_task.stop()
    ai_task.stop()

    do_task.close()
    ao_task.close()
    ai_task.close()

    return(ai_data,ao_data,do_data,trial_voltage)

def countdown_timer(duration):
    start_time = time.time()
    end_time = start_time + duration

    while time.time() < end_time:
        remaining_time = end_time - time.time()
        print("\rRemaining Time: {:.2f} minutes".format(remaining_time/60), end="", flush=True)
        time.sleep(5)  # Update every 5 seconds


# run a countdown timer for [trial_duration] seconds
timer_thread = threading.Thread(target=countdown_timer, args=(trial_duration,))
timer_thread.start()


current_date = datetime.now()
date = current_date.strftime('%Y%m%d_%H%M%S')
np.save("C:/SGL_DATA/motorControl_{}_settings.npy".format(date), settings)


for j in range(settings['num_cycles']):
    ai_task, ao_task, do_task = setupTasks(settings)
    ai_data, _, _, trial_voltage = runTasks(ai_task, ao_task, do_task, settings)
    force = trial_voltage * 50 # 1V ~= 50mN
    np.save("C:/SGL_DATA/mC_ai_data_{}mN_{}_{}.npy".format(force, date, (j+1)), ai_data)
print("\nTrial Complete.")

# Wait for the timer thread to complete before exiting the program
timer_thread.join()