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
from datetime import datetime
import matplotlib.pyplot as plt
import wave
import logging
import os

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
       
    def findSDR(self):
        i = True
        # Trouver :
            # diver name
            # sample rate
            
    
    # to be called a few second before satellite rise
    # will return after satellite set
    def record(self,observation):
        ts = load.timescale()
        t=ts.now()

        filename = f"{observation.satellite.name}_{t.utc_strftime(format='%Y-%m-%d-%H:%M:%S')}_{observation.satellite.frequency}MHz.wav"
        print(filename)
        
        # Create directory for WAV files
        current_directory = os.getcwd()
        directory = os.path.join(current_directory, "wav_files")
        if not os.path.exists(directory):
            os.makedirs(directory)
        filepath = os.path.join(directory, filename)
        
        # Configure SDR
        sdr = SoapySDR.Device("rtlsdr")   
        # if (observation.satellite.bandwidth <= 3.2 and observation.satellite.bandwidth >= 0.225001) and not (0.225001 <= observation.satellite.bandwidth <= 0.3 or 0.900001 <= observation.satellite.bandwidth <= 3.2):
        #     sample_frequency = 0.900001 * 1e6
        # else :
        #     sample_frequency = observation.satellite.bandwidth * 1e6
            
        sample_frequency = 0.900001 * 1e6
            
        sdr.setSampleRate(SOAPY_SDR_RX, 0, sample_frequency )
        sdr.setFrequency(SOAPY_SDR_RX, 0, observation.satellite.frequency * 1e6)
        
        # Set gain to 48 dB and disable AGC
        sdr.setGainMode(SOAPY_SDR_RX, 0, False)
        sdr.setGain(SOAPY_SDR_RX, 0, 48.0)
        
        # Set up RX stream
        rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32,[0]) # todo set from satellite.record_format
        sdr.activateStream(rxStream) #start streaming
        
        # Wait for satellite to rise
        i=0
        print(f'waiting {observation.satellite.name}')
        while t < observation.visibility_window[0] :
            t=ts.now()
            i+=1
            # if i>=100000 :
            #     print(f'waiting {observation.satellite.name}')
            #     i=0
        
               
        # Open WAV file for writing
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)  # 16 bits = 2 octets
            wav_file.setframerate(int(sample_frequency))
            
            block_size = 4096  # Taille du bloc d'échantillons
                                  
            try :
                while t < observation.visibility_window[1] :
                    t=ts.now()
                    buffer = np.empty(block_size, np.complex64)
                    sr = sdr.readStream(rxStream, [buffer], block_size)
                    
                    if sr.ret != block_size:
                        print("Erreur lors de la lecture des échantillons: ", sr.ret)
                    else :
                        # Séparer les échantillons en composants réels et imaginaires
                        iq_data = np.column_stack((buffer.real, buffer.imag))
                        # Convertir les données en 16 bits pour l'enregistrement WAV
                        iq_data_int16 = (iq_data * 32767).astype(np.int16)
                        self.logger.debug(f'IQ = {iq_data_int16}')#stop streaming
                        
                        # Écrire les données dans le fichier WAV
                        wav_file.writeframes(iq_data_int16.tobytes())
            
            except KeyboardInterrupt :
                print('Recording stopped by user')
                
        print(f"Enregistrement terminé. Fichier sauvegardé : {filepath}")
                
        # Clean up SDR ressources
        sdr.deactivateStream(rxStream) #stop streaming
        sdr.closeStream(rxStream)
        
    
    def recordStation(self, frequency):
        ts = load.timescale()
        t=ts.now()
        
        filename = f"test_{t.utc_strftime(format='%Y-%m-%d-%H:%M:%S')}_{frequency}MHz.wav"
        print(filename)
            
        current_directory = os.getcwd()
        # Définir un sous-dossier dans le répertoire courant
        directory = os.path.join(current_directory, "wav_files")
        # Vérifier si le sous-dossier existe, sinon le créer
        if not os.path.exists(directory):
            os.makedirs(directory)
        filepath = os.path.join(directory, filename)
        
        sdr = SoapySDR.Device("rtlsdr")
        
        # Configure SDR
        sample_frequency = 0.900001 * 1e6
        sdr.setSampleRate(SOAPY_SDR_RX, 0, sample_frequency)
        sdr.setFrequency(SOAPY_SDR_RX, 0, frequency * 1e6)
        
        # Set gain to 48 dB and disable AGC
        sdr.setGainMode(SOAPY_SDR_RX, 0, False)
        sdr.setGain(SOAPY_SDR_RX, 0, 48.0)
        
        rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32,[0]) # todo set from satellite.record_format
        sdr.activateStream(rxStream) #start streaming
        
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)  # 16 bits = 2 octets
            wav_file.setframerate(int(sample_frequency))
            
            # block_size = optimal_block_size  # Taille du bloc d'échantillons
            block_size = 4096  # Taille du bloc d'échantillons
                                  
            try :
                while 1 :
                    buffer = np.empty(block_size, np.complex64)
                    sr = sdr.readStream(rxStream, [buffer], block_size)
                    
                    if sr.ret != block_size:
                        print("Erreur lors de la lecture des échantillons: ", sr.ret)
                    else :
                        # Séparer les échantillons en composants réels et imaginaires
                        iq_data = np.column_stack((buffer.real, buffer.imag))
                        # Convertir les données en 16 bits pour l'enregistrement WAV
                        iq_data_int16 = (iq_data * 32767).astype(np.int16)
                        self.logger.debug(f'IQ = {iq_data_int16}')#stop streaming
                        
                        # Écrire les données dans le fichier WAV
                        wav_file.writeframes(iq_data_int16.tobytes())
            
            except KeyboardInterrupt :
                print('Recording stopped by user')
                
        sdr.deactivateStream(rxStream) #stop streaming
        sdr.closeStream(rxStream)   
        
        print(f"Enregistrement terminé. Fichier sauvegardé : {filepath}")
                
      # to be called a few second before satellite rise
      # will return after satellite set
         

if __name__ == "__main__":
    test = False
    
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
    
    if test :    
        Station = Recorder(config.station, receiver, config.satellites, start_time, stop_time,logging.DEBUG)
        Station.recordStation(137.1)
    else :
        recorder = Recorder(config.station, receiver, config.satellites, start_time, stop_time,logging.DEBUG)
        for obs in planning.planning:
            recorder.record(obs)