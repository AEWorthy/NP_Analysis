import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import threading
import time


settings = {
    'task_name' : 'pulsedLaser',
    
    'xMirror_output': 'PXI1Slot2/ao0',
    'yMirror_output': 'PXI1Slot2/ao1',
    'laser_output': '/PXI1Slot2/port0/line0',
    'sync': '/PXI1Slot2/port0/line1', #output to trigger NP recording

    'Fs': 30000,  # in samples/s
    'xV' : 7.8, # in Volts. Fixed voltage for mirror's x-axis
    'yV' : 3.2, # in Volts. Fixed voltage for mirror's y-axis

    'laser_duration' : 0.0003,  # seconds
    'laser_frequency' : 40, # Hz (for sustained pulse, equate to settings['Fs']). **Run 5, 20, and 40Hz for full set**
    'train_duration' : 0.5, # seconds
    'rest_duration' : 5, # seconds
    'trial_buffer' : 1, # seconds
    'trial_repeats' : 50 # number of trains to pass (100 takes ~10 minutes; default = 50)
}


# calculate trial_duration
trial_duration = (2 * settings['trial_buffer']) + (settings['trial_repeats'] * (settings['train_duration'] + settings['rest_duration'])) - settings['rest_duration']
minutes = round(trial_duration/60, 2)
print("This experiment will take {} minutes to complete...".format(minutes))


def setupTasks(settings):
    numSamples = int(settings['Fs'] * trial_duration)

    ao_task = nidaqmx.Task()
    ao_task.ao_channels.add_ao_voltage_chan(settings['xMirror_output'], name_to_assign_to_channel='x_out')
    ao_task.ao_channels.add_ao_voltage_chan(settings['yMirror_output'], name_to_assign_to_channel='y_out')
    ao_task.timing.cfg_samp_clk_timing(settings['Fs'], samps_per_chan=numSamples)

    
    do_task = nidaqmx.Task()
    do_task.do_channels.add_do_chan(settings['laser_output'], name_to_assign_to_lines='laser')
    do_task.do_channels.add_do_chan(settings['sync'], name_to_assign_to_lines='sync')
    do_task.timing.cfg_samp_clk_timing(settings['Fs'], samps_per_chan=numSamples)

    return (ao_task, do_task)


def runTasks(ao_task, do_task, settings):

    # initialize zeroed-out arrays
    numSamples = int(settings['Fs'] * trial_duration)
    ao_out = np.zeros((2, numSamples))
    do_out = np.zeros((2, int(settings['Fs'] * trial_duration)), dtype=bool)
    
    # Fill ao_out with mirror coordinates
    ao_out[0] = np.full(1, settings["xV"])
    ao_out[1] = np.full(1, settings["yV"])

    # generate a train of laser pulses for settings['laser_duration']seconds at settings['laser_frequency']Hz    
    train_onsets = np.arange((settings['trial_buffer']), (trial_duration), ((settings['train_duration'] + settings['rest_duration']))) * settings['Fs']
    # Calculate the time points for laser onset within a train
    laser_onsets = np.arange(0, settings['train_duration'], 1 / settings['laser_frequency'])
    # Convert the time points to sample indices
    laser_onsets = (laser_onsets * settings['Fs']).astype(int)

    # # for countdown
    # trials_left = len(train_onsets)

    for train_onset in train_onsets:
        for laser_onset in laser_onsets:
            start_index = int(train_onset + laser_onset)
            end_index = int(start_index + (settings['laser_duration'] * settings['Fs']))
            do_out[0, start_index:end_index] = True
        
        # # Countdown display
        # trials_left -= 1
        # sys.stdout.write(f"\rTrials remaining: {trials_left}")
        # sys.stdout.flush()



    #turn NP sync signal on during trial
    do_out[1, 1:(numSamples-1)] = True

    ## writing daq outputs onto device
    do_task.write(do_out, timeout = trial_duration + 10)
    ao_task.write(ao_out, timeout = trial_duration + 10)

    ## starting tasks (make sure do_task is started last -- it triggers the others)
    ao_task.start()
    do_task.start()
    do_task.wait_until_done(timeout = trial_duration + 10)

    ## adding data to the outputs
    ao_data = ao_out
    do_data = do_out

    ## stopping tasks
    do_task.stop()
    ao_task.stop()

    do_task.close()
    ao_task.close()
    return(ao_data,do_data)
    

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


ao_task, do_task = setupTasks(settings)
ao_data, do_data, = runTasks(ao_task, do_task, settings)
print("\nTrial Complete.")


# save all data to numpy arrays
current_date = datetime.now()
date = current_date.strftime('%Y%m%d_%H%M%S')
np.save("C:/SGL_DATA/{}HzLaser_{}_ao_data.npy".format(settings['laser_frequency'], date), ao_data)
np.save("C:/SGL_DATA/{}HzLaser_{}_do_data.npy".format(settings['laser_frequency'], date), do_data)
np.save("C:/SGL_DATA/{}HzLaser_{}_settings.npy".format(settings['laser_frequency'], date), settings)

# Wait for the timer thread to complete before exiting the program
timer_thread.join()