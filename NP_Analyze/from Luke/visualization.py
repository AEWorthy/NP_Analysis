import math
import numpy as np
import pandas as pd

def importKS(folderpath,tipDepth,sampleRate=30000):
    
    # import kilosort/phy2 outputs

    ### Inputs:
    #1. `folderpath` - str with path to kilosort output
    #2. `tipDepth` - int/float, depth of the shank tip in microns (Reading of D axis given by sensapex micromanipulator)
    #3. `sampleRate` - int sample rate in Hz (find in params.py if unknown)
        
    ### Output: Dict with keys
    #1. `sampleRate` - int sample rate in Hz (same as input)
    #2. `goodSpikes` - ndarray of clusters (unit identities of spikes)
    #3. `goodSamples` - ndarray of spike samples (time of spike)
    #4. `goodTimes` - ndarray of spike times (in s)
    #5. `clusterIDs` - ndarray of unit index as listed in the Kilosort/Phy output
    #6. `goodIDs` - ndarray of all units included in goodSpikes
    #7. `depths` - ndarray of recording site depth, order match with `clusterID` (counting the depth of shank)
    #8. `nSpikes` - ndarray of number of spikes 

    ### Not yet implemented
    #1. `unitPosXY` - tuple of two ndarrays, (X center of mass, Y center of mass)
    #2. `depthIndices` - index of good units in the order of their depth
    #3. `layers` - the cortical layer to which the depth corresponds
    #4. 'waveforms of unit at its best site'
     
    # parameters
    tipLength = 175 # the tip length of neuropixel 1.0 [unit: µm]

    # import the Kilosort Output
    clusterInfo = pd.read_csv(folderpath+'/cluster_info.tsv',sep='\t')
    spikeClusters = np.load(folderpath+'/spike_clusters.npy')
    spikeTimes = np.load(folderpath+'/spike_times.npy')

    # apply label from manual curation 
    clusterInfo.loc[clusterInfo['group'] == 'good', 'KSLabel'] = 'good'

    # store units with good qualities
    try:
        goodIDs = np.array(clusterInfo['id'][clusterInfo['KSLabel'] == 'good'])
    except KeyError:
        goodIDs = np.array(clusterInfo['cluster_id'][clusterInfo['KSLabel'] == 'good'])
    
    # compute the depth
        siteDepth = tipDepth - tipLength - np.array(clusterInfo['depth'])
        if any(depth < 0 for depth in siteDepth):
            print("Warning: Negative depth value found, changing to 0.")
            siteDepth = [0 if depth < 0 else depth for depth in siteDepth]

    # write the output
    outDict = {}
    outDict['sampleRate'] = sampleRate
    outDict['goodSpikes'] = spikeClusters[np.array([n in goodIDs for n in spikeClusters])]
    outDict['goodSamples'] = np.int64(spikeTimes[np.array([n in goodIDs for n in spikeClusters])].reshape(-1))
    outDict['goodTimes'] = outDict['goodSamples']/sampleRate
    outDict['clusterIDs'] = np.array(clusterInfo['cluster_id']) ## to get a list of cluster ids
    outDict['goodIDs'] = goodIDs
    outDict['depths'] =  siteDepth
    outDict['nSpikes'] = np.array(clusterInfo['n_spikes']) ## to get number of spikes 
    #outDict['depthIndices'] = np.argsort(clusterInfo['depth']) ## to get an index to use for sorting by depth

    # print the number of good neurons
    print("Number of neurons pass the quality check: {}".format(len(goodIDs)))

    # report the sampling frequency
    print("Sampling frequency: {} Hz.".format(outDict['sampleRate']))
    
    return outDict
 
def getNormRoster(outDict, dt = 1):

    # 
    maxTime = int(np.ceil(np.max(outDict['goodTimes'])/dt))
    numGoodID = len(outDict['goodIDs'])
    roster = np.zeros([numGoodID,maxTime]) 

    for i in range(len(outDict['goodSpikes'])):
        xIdx = np.where(outDict['goodIDs'] == outDict['goodSpikes'][i])
        yIdx =  np.floor(outDict['goodTimes'][i]/dt).astype(int)
        roster[xIdx, yIdx] += 1

    # compute delta firing rate
    baseline = np.mean(roster, axis = 1)[:, np.newaxis]
    normRoster = roster - baseline

    return normRoster
    
