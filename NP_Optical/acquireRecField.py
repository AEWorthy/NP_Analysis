import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import threading
import time

###Changes to make: don't do multiple recordings (keep sync = 1), but loop within one recording block.

settings = {
    'task_name' : 'acquireRecField',

    'xMirror_output': 'PXI1Slot2/ao0',
    'yMirror_output': 'PXI1Slot2/ao1',
    'laser_output': '/PXI1Slot2/port0/line0',
    'sync': '/PXI1Slot2/port0/line1', #output to trigger NP recording
    
    'Fs': 30000,  # in samples/s
    'xV': 7.8, # in V.
    'yV': 3.2, # in V.

    'stepV' : .05, # in Volts. Increment of voltage to be stepped for mirror
    'time_per_region' : 0.03, # in seconds. Duration to hold mirrors in place for each region
    'trial_repeats' : 10 # number of times each region should be sampled (default = 10)
}


# set mirror x_out and y_out arrays within the specified voltage range and increments
xminV = settings['xV'] - 0.5
xmaxV = settings['xV'] + 0.5
yminV = settings['yV'] - 0.5
ymaxV = settings['yV'] + 0.5
x_out_values = np.arange(xminV, xmaxV, settings['stepV'])
y_out_values = np.arange(yminV, ymaxV, settings['stepV'])

# create matrix for all possible combinations of x_out and y_out
all_combinations = np.array(np.meshgrid(x_out_values, y_out_values)).T.reshape(-1, 2)
trial_duration = len(all_combinations**2) * settings['time_per_region'] * settings['trial_repeats'] # in seconds
minutes = round(trial_duration/60, 2)
print("This experiment will take {} minutes to complete...".format(minutes))


def setupTasks(settings):
    # calculate the trial duration needed to sample every region and numSamples
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
    # shuffle the combinations to randomize the sequence of pulsed regions
    np.random.seed(seed = 89786)
    np.random.shuffle(all_combinations)
    all_combinations_repeated = np.tile(all_combinations, (settings['trial_repeats'], 1))


    # initialize zeroed-out arrays
    numSamples = int(settings['Fs'] * trial_duration)
    ao_out = np.zeros((2, numSamples))
    do_out = np.zeros((2, numSamples), dtype=bool)

    # generate a train of laser pulses for [laser_duration]seconds at [laser_frequency]Hz
    laser_duration = 0.0001  # seconds
    laser_frequency = settings['Fs']  # Hz (for sustained pulse, equate to settings['Fs'])
    laser_samples = int(settings['Fs'] * laser_duration)
    laser_pulse_indices = np.arange(0, laser_samples, int(settings['Fs'] / laser_frequency))

    # Fill ao_out with the shuffled sequence and do_out with laser pulses
    for i, (x_val, y_val) in enumerate(all_combinations_repeated):
        start_index = i * int(settings['Fs'] * settings['time_per_region'])
        end_index = start_index + int(settings['Fs'] * settings['time_per_region'])
        ao_out[0, start_index:end_index] = x_val
        ao_out[1, start_index:end_index] = y_val

        # Add laser pulses at the middle of each position's time_per_region
        do_out[0, laser_pulse_indices + int(end_index-((end_index-start_index)/2)) - laser_samples] = True

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
    return(ao_data, do_data)


def countdown_timer(duration):
    start_time = time.time()
    end_time = start_time + duration

    while time.time() < end_time:
        remaining_time = end_time - time.time()
        print("\rRemaining Time: {:.2f} minutes".format(remaining_time/60), end="", flush=True)
        time.sleep(1)  # Update every 1 second


# run a countdown timer for [trial_duration] seconds
timer_thread = threading.Thread(target=countdown_timer, args=(trial_duration,))
timer_thread.start()


ao_task, do_task = setupTasks(settings)
ao_data, do_data = runTasks(ao_task, do_task, settings)
print("\nTrial Complete.")


# save all data to numpy arrays
current_date = datetime.now()
date = current_date.strftime('%Y%m%d_%H%M%S')
np.save("C:/SGL_DATA/acRecField_{}_ao_data.npy".format(date), ao_data)
np.save("C:/SGL_DATA/acRecField_{}_do_data.npy".format(date), do_data)
np.save("C:/SGL_DATA/acRecField_{}_settings.npy".format(date), settings)

# Wait for the timer thread to complete before exiting the program
timer_thread.join()
