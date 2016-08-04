from .ATS import AcquisitionController
import math
import numpy as np


# Heterodyne Measurement Controller
# returns unprocessed data averaged by record for 2 channel use
class HD_Controller(AcquisitionController):
    def __init__(self, freq_dif):
        self.freq_dif = freq_dif
        self.samples_per_record = None
        self.bits_per_sample = None
        self.records_per_buffer = None
        self.buffers_per_acquisition = None
        self.number_of_channels = 2
        self.buffer = None

    def pre_start_capture(self, alazar):
        self.bits_per_sample = alazar.get_idn()['bits_per_sample']
        self.samples_per_record = alazar.samples_per_record()
        self.records_per_buffer = alazar.records_per_buffer()
        self.buffers_per_acquisition = alazar.buffers_per_acquisition()
        sample_speed = alazar.get_sample_speed()
        self.buffer = np.zeros(self.samples_per_record *
                              self.records_per_buffer *
                              self.number_of_channels)
        sample_speed = alazar.get_sample_speed()
        integer_list = np.arange(self.samples_per_record)
        angle_list = (2 * np.pi * self.freq_dif / sample_speed *
                      integer_list)
        self.cos_list = np.cos(angle_list)
        self.sin_list = np.sin(angle_list)
                              
    def pre_acquire(self, alazar):
        # gets called after 'AlazarStartCapture'
        pass

    def handle_buffer(self, alazar, data):
        self.buffer += data

    def post_acquire(self, alazar):
        # average over records in buffer:
        # for ATS9360 samples are arranged in the buffer as follows:
        # S0A, S0B, ..., S1A, S1B, ...
        # with SXY the sample number X of channel Y.
        records_per_acquisition = (1. * self.buffers_per_acquisition *
                                   self.records_per_buffer)
        recordA = np.zeros(self.samples_per_record)
        for i in range(self.records_per_buffer):
            i0 = i * self.samples_per_record * self.number_of_channels
            i1 = i0 + self.samples_per_record * self.number_of_channels
            recordA += self.buffer[i0:i1:self.number_of_channels] / records_per_acquisition

        recordB = np.zeros(self.samples_per_record)
        for i in range(self.records_per_buffer):
            i0 = (i * self.samples_per_record * self.number_of_channels) + 1
            i1 = i0 + self.samples_per_record *self.number_of_channels
            recordB += self.buffer[i0:i1:self.number_of_channels] / records_per_acquisition
        
        resA = self.fit(recordA)
        resB = self.fit(recordB)
        
        return resA, resB
      
    def fit(self, rec):
        # Discrete Fourier Transform
        RePart = np.dot(rec, self.cos_list) / self.samples_per_record
        ImPart = np.dot(rec, self.sin_list) / self.samples_per_record

        ampl = np.sqrt(RePart ** 2 + ImPart ** 2)
        phase = math.atan2(ImPart, RePart) * 360 / (2 * math.pi)
        
        return [ampl, phase]


# Test AcquisitionController tested on ATS9360 (nataliejpg)
# returns unprocessed data averaged by record for 2 channel use
class Test_AcquisitionController(AcquisitionController):
    def __init__(self):
        self.samples_per_record = None
        self.records_per_buffer = None
        self.buffers_per_acquisition = None
        self.number_of_channels = 2
        self.buffer = None

    def pre_start_capture(self, alazar):
        self.samples_per_record = alazar.samples_per_record()
        self.records_per_buffer = alazar.records_per_buffer()
        self.buffers_per_acquisition = alazar.buffers_per_acquisition()
        self.buffer = np.zeros(self.samples_per_record *
                              self.records_per_buffer *
                              self.number_of_channels)

    def pre_acquire(self, alazar):
        # gets called after 'AlazarStartCapture'
        pass

    def handle_buffer(self, alazar, data):
        self.buffer += data

    def post_acquire(self, alazar):
        # average over records in buffer:
        # for ATS9360 samples are arranged in the buffer as follows:
        # S0A, S0B, ..., S1A, S1B, ...
        # with SXY the sample number X of channel Y.
        records_per_acquisition = (1. * self.buffers_per_acquisition *
                                   self.records_per_buffer)
        recordA = np.zeros(self.samples_per_record)
        for i in range(self.records_per_buffer):
            i0 = i * self.samples_per_record * self.number_of_channels
            i1 = i0 + self.samples_per_record * self.number_of_channels
            recordA += self.buffer[i0:i1:self.number_of_channels] / records_per_acquisition

        recordB = np.zeros(self.samples_per_record)
        for i in range(self.records_per_buffer):
            i0 = (i * self.samples_per_record * self.number_of_channels) + 1
            i1 = i0 + self.samples_per_record *self.number_of_channels
            recordB += self.buffer[i0:i1:self.number_of_channels] / records_per_acquisition
        return recordA, recordB
    


# DFT AcquisitionController
class DFT_AcquisitionController(AcquisitionController):
    def __init__(self, demodulation_frequency):
        self.demodulation_frequency = demodulation_frequency
        self.samples_per_record = None
        self.bits_per_sample = None
        self.records_per_buffer = None
        self.buffers_per_acquisition = None
        self.allocated_buffers = None
        # TODO (S) this is not very general:
        self.number_of_channels = 2
        self.cos_list = None
        self.sin_list = None
        self.buffer = None

    def pre_start_capture(self, alazar):
        self.samples_per_record = alazar.samples_per_record.get()
        self.records_per_buffer = alazar.records_per_buffer.get()
        self.buffers_per_acquisition = alazar.buffers_per_acquisition.get()
        sample_speed = alazar.get_sample_speed()
        integer_list = np.arange(self.samples_per_record)
        angle_list = (2 * np.pi * self.demodulation_frequency / sample_speed *
                      integer_list)

        self.cos_list = np.cos(angle_list)
        self.sin_list = np.sin(angle_list)
        self.buffer = np.zeros(self.samples_per_record *
                               self.records_per_buffer *
                               self.number_of_channels)

    def pre_acquire(self, alazar):
        # this could be used to start an Arbitrary Waveform Generator, etc...
        # using this method ensures that the contents are executed AFTER the
        # Alazar card starts listening for a trigger pulse
        pass

    def handle_buffer(self, alazar, data):
        self.buffer += data

    def post_acquire(self, alazar):
        # average all records in a buffer
        records_per_acquisition = (1. * self.buffers_per_acquisition *
                                   self.records_per_buffer)
        recordA = np.zeros(self.samples_per_record)
        for i in range(self.records_per_buffer):
            i0 = i * self.samples_per_record
            i1 = i0 + self.samples_per_record
            recordA += self.buffer[i0:i1] / records_per_acquisition

        recordB = np.zeros(self.samples_per_record)
        for i in range(self.records_per_buffer):
            i0 = i * self.samples_per_record + len(self.buffer) / 2
            i1 = i0 + self.samples_per_record
            recordB += self.buffer[i0:i1] / records_per_acquisition

        if self.number_of_channels == 2:
            # fit channel A and channel B
            res1 = self.fit(recordA)
            res2 = self.fit(recordB)
            return [alazar.signal_to_volt(1, res1[0] + 127.5),
                    alazar.signal_to_volt(2, res2[0] + 127.5),
                    res1[1], res2[1],
                    (res1[1] - res2[1]) % 360]
        else:
            raise Exception("Could not find CHANNEL_B during data extraction")
        return None

    def fit(self, buf):
        # Discrete Fourier Transform
        RePart = np.dot(buf - 127.5, self.cos_list) / self.samples_per_record
        ImPart = np.dot(buf - 127.5, self.sin_list) / self.samples_per_record

        # the factor of 2 in the amplitude is due to the fact that there is
        # a negative frequency as well
        ampl = 2 * np.sqrt(RePart ** 2 + ImPart ** 2)

        # see manual page 52!!! (using unsigned data)
        return [ampl, math.atan2(ImPart, RePart) * 360 / (2 * math.pi)]
