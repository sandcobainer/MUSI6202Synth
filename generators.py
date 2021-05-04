# Generator functions for sq, sine, saw, tri waves
import numpy as np
import ADSR
from utils import LinearWrap

class Generators:
    def __init__(self, notes, fs):
        self.notenumbers = notes.notenumbers
        self.frequencies = notes.frequencies
        self.durations = notes.durations
        self.fs = fs
        self.amplitude = 0.4
        self.numOfNotes = len(notes.frequencies)


    def additive(self, envelope, partials, coefficients):
        sound = []
        for i in np.arange(self.numOfNotes):
            omega = 2 * np.pi * self.frequencies[i]
            t = np.arange(0, float(self.durations[i]), float(1 / self.fs))
            signal = 0
            for k in range(0, len(partials)):
                partial = (1/partials[k]) * np.sin(k * omega * t)
                signal += coefficients[k] * (4/np.pi)* partial

            env = ADSR.getadsr(signal, envelope)
            # rel_length = 100
            # sig_length = len(signal) - rel_length
            # if(len(signal) < len(env)):
            #     release = np.linspace(signal[-rel_length], 0, num=rel_length) ** 2
            #     print(release)
            #     x_env = signal[:sig_length] * env[:sig_length]
            #     np.hstack((x_env, release))
            #     x_env = list(x_env)
            # else:
            x_env = signal * env

            sound.extend(x_env)

        return np.array(sound)

    def granular(self, s, grainSize, hopSize, timeScale, freqScale, timeVariation, pitchVariation):
        numGrains = int(len(s) / hopSize)
        s = np.pad(s, (0, grainSize), 'constant')

        grainOutputPositions = np.zeros(numGrains, dtype=np.uint64)
        grainOutputPitches = np.zeros(numGrains)
        
        for grainNum in range(numGrains):
            grainPosition = hopSize * grainNum
            grainOutputPosition = grainPosition / timeScale
            grainOutputPositions[grainNum] = grainOutputPosition
            grainOutputPitches[grainNum] = freqScale

        grainOutputPositions[1:] = grainOutputPositions[1:] + ((np.random.randn(numGrains - 1) * 2 - 1) * timeVariation)
        
        grainOutputPositions = grainOutputPositions.astype(np.uint64)
            
        grainOutputPitches = grainOutputPitches + ((np.random.randn(numGrains) * 2 - 1) * pitchVariation)

        minOutputPitch = np.min(grainOutputPitches)
        outputGrainSize = int(grainSize / minOutputPitch) + 1
        lastGrainOutputPosition = grainOutputPositions[-1]
        outputLength = int(lastGrainOutputPosition + outputGrainSize) + grainSize

        print(outputLength, outputGrainSize)
        output = np.zeros(outputLength)
        grainOutput = np.zeros(outputGrainSize)
        
        hanWin = np.hanning(grainSize)
        
        for grainNum in range(numGrains):
            grainOutput.fill(0)

            grainPosition = hopSize * grainNum
            grainOutputPosition = int(grainOutputPositions[grainNum])
            grainPitch = grainOutputPitches[grainNum]
            
            windowedGrain = hanWin * s[grainPosition:grainPosition + grainSize]
            windowedGrain = LinearWrap(windowedGrain)
            for grainOutputIdx in range(outputGrainSize):
                grainInputIdx = grainOutputIdx * grainPitch
                grainOutput[grainOutputIdx] = windowedGrain[grainInputIdx]
            output[grainOutputPosition:grainOutputPosition+outputGrainSize] += grainOutput
        
        return output


