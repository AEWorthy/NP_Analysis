#Run this code under "Extract Spike Trains from drgDict" in "DRG LP Electrophysiology Analysis - for S1 paper.ipynb" to re-save the "saltmr_trace{X}.npy" files
# This code will pull empirical SA-LTMR (TrkC+) AP traces during ~0.5 seconds of 40mN pressure applied to the paw (this occurs from 5 to 5.5 seconds into the recordings).
 
cells = 0
ymin = 0
ymax = 1

# create a figure and axis
fig, ax = plt.subplots()

for i, cell in enumerate(drgDict)
    if drgDict[cell]['label'] == 'TrkC'
        spikeTimes = np.array(drgDict[cell]['bestTimes'])
        spikeTimes = spikeTimes - 2
        spikesOI = spikeTimes[(spikeTimes = 5)&(spikeTimes = 5.5)]
        spikesOI -= 5 #set to a new relative 0
        print(spikesOI)
        print(len(spikesOI))
        
        cells += 1
        np.save('saltmr_trace{}.npy'.format(cells), spikesOI)

        # Plot spikes as vertical lines for each onset array
        ax.vlines(spikesOI, ymin, ymax, colors='b', linewidth=2, label='Neuron {}'.format(cells))
        ymin += 1
        ymax += 1

print("# Cells "{}.format(cells))

# adjust the raster plot
ax.set_xlim(0, 0.6)  # x-axis limits
ax.set_ylim(0, cells)   # y-axis limits based on the number of neurons
ax.set_xlabel('Time (seconds)')
ax.set_ylabel('Neuron')
ax.set_title('Raster Plot')

# Show the plot
plt.show()