# Post processing scripts: interpolation, dithering, resampling and output

from scipy import signal
import numpy as np
from scipy.interpolate import interp1d
import wavio
from dataclasses import dataclass


@dataclass
class Downsampler:
    output_fs: int = 48000
    output_br: int = 32

    def write_wav(self, wave_file_path, data, fs=output_fs, bitrate=output_br):
        """
        Functions writes result to output wavefile at 
        specified bitrate and sampling rate
        """
        if bitrate == 8:
            sample_width = 1
        elif bitrate == 16:
            sample_width = 2
        elif bitrate == 24:
            sample_width = 3
        else:
            sample_width = 4

        wavio.write(wave_file_path, data, fs, sampwidth=sample_width)

    
    def low_pass(self, data, Fs_new, Fs):
        """
        Functions removes frequencies above the Shannon-Nyquist frequency
        """
        b, a = signal.butter(N=2, Wn=Fs_new / 2, btype='low', analog=False, fs=Fs)
        filtered = signal.filtfilt(b, a, data)
        return filtered.astype(np.int32)

    
    def down_sample(self, data, factor, target_fs, source_fs):
        """
        Function down samples incoming sample to lower sampling rate
        """
        low_filtered = self.low_pass(data, target_fs, source_fs)
        return low_filtered[::factor]

    
    def cubic_interpolate(self, data, t, num_samples):
        """
        Functions implements cubic interpolation
        """
        x = np.linspace(0, t, num=len(data), endpoint=True)
        y = data
        cs = interp1d(x, y, kind='cubic')
        xNew = np.linspace(0, t, num=num_samples, endpoint=True)
        out = cs(xNew).astype(np.int32)
        return out

    
    def up_sample(self, data, source_fs, target_fs, t):
        """
        Function to upsample original data to a higher sampling rate
        """
        new_samples = int(int(len(data) / source_fs) * int(target_fs))
        return self.cubic_interpolate(data, t, new_samples)

    def add_triangular_dither(self, original, original_br, new_br):
        """
        Implements trinagular dithering
        """
        diff = original_br - new_br
        left = (-1) * (2 ** diff)
        mode = 0
        right = (2 ** diff) - 1
        size = original.shape
        noise = np.random.triangular(left, mode, right, size)
        noise = noise.astype(np.int32)

        return original + noise

    def down_quantization(self, data, original_br, new_br):
        """
        Down quantizes input sample with triangular dithering
        """
        dithered = self.add_triangular_dither(data, original_br, new_br)
        dithered = dithered.astype(np.int32)
        down_quantized = np.zeros(len(dithered), dtype=np.int32)

        for i in range(len(dithered)):
            down_quantized[i] = dithered[i] >> (original_br - new_br)
        return down_quantized
