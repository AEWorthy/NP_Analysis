import nidaqmx
import numpy as np


settings = {
    'lengthChannel_input':'PXI1Slot2/ai0',
    'forceChannel_input':'PXI1Slot2/ai1',
    'lengthChannel_output':'PXI1Slot2/ao0',
    'forceChannel_output':'PXI1Slot2/ao1',
    'sync':'/PXI1Slot2/port0/line0',
    'Fs':30000, ## in samples/s
    'trigger_input':'/PXI1Slot2/port0/line1',
    'trigger_output':'/PXI1Slot2/port0/line2',
    'camera_output':'/PXI1Slot2/port0/line3',
    'trial_duration':5  ## in seconds
}



def setupTasks(settings):
    numSamples = int(settings['Fs']*settings['trial_duration'])


    ai_task = nidaqmx.Task()
    ai_task.ai_channels.add_ai_voltage_chan(settings['lengthChannel_input'],name_to_assign_to_channel='length_in')
    ai_task.ai_channels.add_ai_voltage_chan(settings['forceChannel_input'],name_to_assign_to_channel='force_in')
    ai_task.timing.cfg_samp_clk_timing(settings['Fs'], samps_per_chan=numSamples)


    ao_task = nidaqmx.Task()
    ao_task.ao_channels.add_ao_voltage_chan(settings['lengthChannel_output'],name_to_assign_to_channel='length_out')
    ao_task.ao_channels.add_ao_voltage_chan(settings['forceChannel_output'],name_to_assign_to_channel='force_out')
    ao_task.timing.cfg_samp_clk_timing(settings['Fs'],samps_per_chan=numSamples)
    return (ai_task, ao_task)


def runTasks(ai_task, ao_task, settings):
    numSamples = int(settings['Fs']*settings['trial_duration'])

    ## starting tasks (make sure do_task is started last -- it triggers the others)
    ai_task.start()
    # di_task.start()
    ai_task.wait_until_done()

    ## adding data to the outputs
    ai_data = np.array(ai_task.read(numSamples))
    # # di_data = np.array(di_task.read(numSamples))
    # ao_data = ao_out
    # do_data = do_out

    ## stopping tasks
    # do_task.stop()
    # ao_task.stop()
    ai_task.stop()
    # di_task.stop()

    # do_task.close()
    # ao_task.close()
    ai_task.close()
    # di_task.close()
    print(ai_data)

    
ai_task = setupTasks(settings)
runTasks(ai_task, settings)
print('finished')

# with nidaqmx.Task() as task:
#     task.ai_channels.add_ai_voltage_chan("PXI1Slot2/ai0")
#     task.ai_channels.add_ai_voltage_chan("PXI1Slot2/ai1")
#     a, b  = task.read()
#     print(a)
#     print(b)


# with nidaqmx.Task() as task:
#     task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
#     task.read(number_of_samples_per_channel=2)

# [0.26001373311970705, 0.37796597238117036]
# from nidaqmx.constants import LineGrouping
# with nidaqmx.Task() as task:
#     task.di_channels.add_di_chan(
#         "cDAQ2Mod4/port0/line0:1", line_grouping=LineGrouping.CHAN_PER_LINE)
#     task.read(number_of_samples_per_channel=2)

# [[False, True], [True, True]]