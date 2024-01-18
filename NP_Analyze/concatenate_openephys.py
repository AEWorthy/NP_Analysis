import os
import numpy as np

# Provide the path to the overall experiment folder and the path where you would like the merged file to be saved
folder_path = r"D:\Andrew's Data\2024-01-05_ALC4_day3"
output_path = folder_path

folder_path = os.path.join(folder_path,'01-raw').replace('\\', '/')

#Empty list will contain filepaths of recordings that are to be concatenated
files_to_concat = []

#01-raw contains folders for every experiment
experiments = [item for item in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, item))]

#extract files_to_concat list
for experiment in experiments:
    if experiment == '1-mechanical':
        #files_to_concat.append(path)
        recording_path = os.path.join(folder_path, experiment).replace('\\', '/')
        recordings = [item for item in os.listdir(recording_path) if os.path.isdir(os.path.join(recording_path, item))]
        recordings = sorted(recordings, key=lambda x: int(''.join(filter(str.isdigit, x))))

        for recording in recordings:
            path = os.path.join(recording_path, recording,'continuous','Neuropix-PXI-100.ProbeA-AP','continuous.dat').replace('\\', '/')
            files_to_concat.append(path)
    
    elif experiment == 'unused':
        print('"Unused" folder skipped.')
        pass

    elif experiment == '2-acRecField' or '3-physio' or '4-5hz pulsed' or '5-20hz pulsed' or '6-40hz pulsed':
        path = os.path.join(folder_path, experiment, 'continuous', 'Neuropix-PXI-100.ProbeA-AP', 'continuous.dat').replace('\\', '/')
        files_to_concat.append(path)

    else:
        print('Invalid experiment folder detected.')
        pass

# input list of continuous.DAT filepaths to be concatenated. Will save a concatenated version in specified save_path.
def openephys_concat (recording_filepaths, save_path):
    raw_combined = open(os.path.join(save_path, 'combined_trial.DAT').replace('\\', '/'), 'wb')

    for recording in recording_filepaths:
            to_append = np.memmap(recording, mode='r')
            to_append.tofile(raw_combined)
        
            
    raw_combined.close()
    print('Concatenation complete.')

openephys_concat(files_to_concat, output_path)