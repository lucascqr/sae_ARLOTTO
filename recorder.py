#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 16:06:01 2024

@author: lucas
"""

from ConfigurationReader import ConfigurationReader
from TLE_Loader import Tle_Loader, VisibilyWindowComputer
from Planifier_remake import Plannifier
from skyfield.api import load, wgs84
import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants
import numpy as np
import time
import matplotlib.pyplot as plt
import wave
import logging

class Recorder():
    def __init__(self,station,receiver,satellites,start_time,end_time,\
                 level = logging.INFO):
       self.station = station
       self.receiver = receiver
       self.satellites = satellites
       self.start_time = start_time
       self.end_time = end_time
       logging.basicConfig(level=logging.INFO)
       self.logger = logging.getLogger(__name__)
       logging.getLogger().setLevel(level)
    
    # to be called a few second before satellite rise
    # will return after satellite set
    def record(self,observation):
        #t=ts.now()
        ts = load.timescale()
        t=ts.utc(2024,7,19,18,30,40)
        fileName =  observation.satellite.name+t.utc_strftime(format="%Y-%m-%d-%H:%M:%S")
        fileName += '-'+str(observation.satellite.frequency)+'MHz'+'.'+'.wav' #+satellite.record_format
        self.logger.debug(f'traking {observation.satellite.name} at {t.utc}')
        ip_address = self.receiver.ip
        sdr = SoapySDR.Device("rtlsdr")
        
        if (observation.satellite.bandwidth <= 3.2 and observation.satellite.bandwidth >= 0.225001) and not (0.225001 <= observation.satellite.bandwidth <= 0.3 or 0.900001 <= observation.satellite.bandwidth <= 3.2):
            sample_frequency = 0.900001 * 1e6
        else :
            sample_frequency = observation.satellite.bandwidth * 1e6
            
        self.logger.debug(f'sample frequency is {sample_frequency}')
        sdr.setSampleRate(SOAPY_SDR_RX, 0, sample_frequency )
        #sdr.setFrequency(SOAPY_SDR_RX, 0, sample_frequency*1e6)
        sdr.setFrequency(SOAPY_SDR_RX, 0, observation.satellite.frequency * 1e6)
        freq = sdr.getSampleRate(SOAPY_SDR_RX, 0)
        self.logger.debug(f'real sample frequency is {freq}')
        rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32,[0]) # todo set from satellite.record_format
        optimal_block_size = sdr.getStreamMTU(rxStream)
        sdr.activateStream(rxStream) #start streaming
       
        with wave.open(fileName, 'wb') as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)  # 16 bits = 2 octets
            wav_file.setframerate( int(sample_frequency) )
            block_size = optimal_block_size  # Taille du bloc d'échantillons
                                  
            while 1 :
                t = t+0.01/(24*3600)
                buffer = np.empty(block_size, np.complex64)
                sr = sdr.readStream(rxStream, [buffer], block_size)
                if sr.ret != block_size:
                    print("Erreur lors de la lecture des échantillons: ", sr.ret)
                else :
                    # Séparer les échantillons en composants réels et imaginaires
                    iq_data = np.column_stack((buffer.real, buffer.imag))
                    # Convertir les données en 16 bits pour l'enregistrement WAV
                    iq_data_int16 = (iq_data * 32767).astype(np.int16)
                    self.logger.debug(f'IQ = {iq_data_int16}')
                    
                    # Écrire les données dans le fichier WAV
                    wav_file.writeframes(iq_data_int16.tobytes())
                
        sdr.deactivateStream(rxStream) #stop streaming
        sdr.closeStream(rxStream)    
                
     # to be called a few second before satellite rise
     # will return after satellite set
         

if __name__ == "__main__":
    from skyfield.api import load
    
    station_file = 'toml/station.toml'
    satellites_file = 'toml/satellites.toml'
    
    config = ConfigurationReader(station_file, satellites_file)
    
    receiver = config.receiver

    loader = Tle_Loader(config.satellites,config.directories.tle_dir, config.tle.max_days)
    loader.tleLoader()

    ts = load.timescale()
    start_time = ts.now()
    stop_time = ts.now() + 1

    computer = VisibilyWindowComputer(config.satellites, config.station, start_time, stop_time)
    computer.compute_Observation()

    planning = Plannifier(computer.observations, config.satellites)
    planning.Planning_Maker()
    planning.plot_planning()
    # print(planning.observations[0].visibility_window[0])
    # print(planning.planning[0].visibility_window[0])
    n=len(planning.observations)
    print(f'{n} Observation du {start_time.utc_strftime(format="%Y-%m-%dT%H:%M:%SZ")} au {stop_time.utc_strftime(format="%Y-%m-%dT%H:%M:%SZ")}')
    # planning.print_planning()
    # planning.print_observation_states()
    
    recorder = Recorder(config.station, receiver, config.satellites, start_time, stop_time,logging.DEBUG)
    for obs in planning.planning:
        recorder.record(obs)