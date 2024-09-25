#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 16:06:01 2024

@author: philippe
"""
from ConfigurationReader import ConfigurationReader,Station,Satellite
from tleLoader import TleLoader
from planifier import Planifier
import logging
import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants
import numpy as np #use numpy for buffers
from skyfield.api import wgs84
import time
import wave
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
    def trackAndRecordTest(self,satellite):
         #t=ts.now()
         ts = load.timescale()
         t=ts.utc(2024,7,19,18,30,40)
         fileName =  satellite.name+t.utc_strftime(format="%Y-%m-%d-%H:%M:%S")
         fileName += '-'+str(satellite.frequency)+'MHz'+'.'+'.wav' #+satellite.record_format
         self.logger.debug(f'traking {satellite.name} at {t.utc}')
         ip_address = self.receiver.ip
         args = f"driver=plutosdr,addr={ip_address}"
         sdr = SoapySDR.Device(args)
         sample_frequency = satellite.bandwidth * 1e6
         sdr.setSampleRate(SOAPY_SDR_RX, 0, sample_frequency )
         #sdr.setFrequency(SOAPY_SDR_RX, 0, satellite.frequency*1e6)
         sdr.setFrequency(SOAPY_SDR_RX, 0, 107.1*1e6)
         rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32,[0]) # todo set from satellite.record_format
         optimal_block_size=sdr.getStreamMTU(rxStream)
         sdr.activateStream(rxStream) #start streaming
         
          
         
         skyfiledSatellite = satellite.EarthSatellite[0]
         bluffton = wgs84.latlon(self.station.latitude,self.station.longitude)
         min_elevation= satellite.min_elevation
         pass_started = False
        
         with wave.open(fileName, 'wb') as wav_file:
             wav_file.setnchannels(2)
             wav_file.setsampwidth(2)  # 16 bits = 2 octets
             wav_file.setframerate( int(sample_frequency) )
             block_size = optimal_block_size  # Taille du bloc d'échantillons
                                   
             while 1 :
                 t = t+0.01/(24*3600)
                 geocentric = skyfiledSatellite.at(t)
                 difference = skyfiledSatellite - bluffton
                 topocentric = difference.at(t)
                 alt, az, distance = topocentric.altaz()
                 self.logger.debug(f'{t.utc}: {alt},{az}')
                 if alt.degrees < min_elevation :
                     if not pass_started :
                         time.sleep(10)
                         t+=10/(24*3600)
                         continue
                     else :
                         break # end of pass
                 else :
                     pass_started = True 
                 buffer = np.empty(block_size, np.complex64)
                 sr = sdr.readStream(rxStream, [buffer], block_size)
                 if sr.ret != block_size:
                     print("Erreur lors de la lecture des échantillons: ", sr.ret)
                 # Séparer les échantillons en composants réels et imaginaires
                 iq_data = np.column_stack((buffer.real, buffer.imag))
                 
                 # Convertir les données en 16 bits pour l'enregistrement WAV
                 iq_data_int16 = (iq_data * 32767).astype(np.int16)
                 
                 # Écrire les données dans le fichier WAV
                 wav_file.writeframes(iq_data_int16.tobytes())
         sdr.deactivateStream(rxStream) #stop streaming
         sdr.closeStream(rxStream)    
                 
      # to be called a few second before satellite rise
      # will return after satellite set
    def trackAndRecord(self,observation):
           satellite = observation.satellite
           start_time = observation.observationWindow[0]
           ts = load.timescale()
           t=ts.now()
           fileName =  satellite.name+'-'+start_time.utc_strftime(format="%Y-%m-%d-%H:%M:%S")
           fileName += '-'+str(satellite.frequency)+'MHz'+'.'+'.wav' #+satellite.record_format
           self.logger.debug(f'traking {satellite.name} at {t.utc}')
           ip_address = self.receiver.ip
           args = f"driver=plutosdr,addr={ip_address}"
           sdr = SoapySDR.Device(args)
           sample_frequency = satellite.bandwidth * 1e6
           sdr.setSampleRate(SOAPY_SDR_RX, 0, sample_frequency )
           sdr.setFrequency(SOAPY_SDR_RX, 0, satellite.frequency*1e6)
           rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32,[0]) # todo set from satellite.record_format
           optimal_block_size=sdr.getStreamMTU(rxStream)
           sdr.activateStream(rxStream) #start streaming
           
            
           
           skyfiledSatellite = satellite.EarthSatellite[0]
           bluffton = wgs84.latlon(self.station.latitude,self.station.longitude)
           min_elevation= satellite.min_elevation
           pass_started = False
          
           with wave.open(fileName, 'wb') as wav_file:
               wav_file.setnchannels(2)
               wav_file.setsampwidth(2)  # 16 bits = 2 octets
               wav_file.setframerate( int(sample_frequency) )
               block_size = optimal_block_size  # Taille du bloc d'échantillons
               self.logger.info(f'waiting for {satellite.name} frequency {satellite.frequency} MHz at {start_time.utc_strftime(format="%Y-%m-%d-%H:%M:%S")}')                      
               while 1 :
                   t = ts.now()
                   geocentric = skyfiledSatellite.at(t)
                   difference = skyfiledSatellite - bluffton
                   topocentric = difference.at(t)
                   alt, az, distance = topocentric.altaz()
                   #self.logger.debug(f'{t.utc}: {alt},{az}')
                   if alt.degrees < min_elevation :
                       if not pass_started :
                           time.sleep(10)
                           continue
                       else :
                           self.logger.info(f'end of pass for {satellite.name}')
                           break # end of pass
                   else :
                       if not pass_started :
                           pass_started = True
                           self.logger.info(f'start recoording {satellite.name}')
                   buffer = np.empty(block_size, np.complex64)
                   sr = sdr.readStream(rxStream, [buffer], block_size)
                   if sr.ret != block_size:
                       print("Erreur lors de la lecture des échantillons: ", sr.ret)
                   # Séparer les échantillons en composants réels et imaginaires
                   iq_data = np.column_stack((buffer.real, buffer.imag))
                   
                   # Convertir les données en 16 bits pour l'enregistrement WAV
                   iq_data_int16 = (iq_data * 32767).astype(np.int16)
                   
                   # Écrire les données dans le fichier WAV
                   wav_file.writeframes(iq_data_int16.tobytes())
           sdr.deactivateStream(rxStream) #stop streaming
           sdr.closeStream(rxStream)                  
         

if __name__ == "__main__":
    
    from skyfield.api import load
    config = ConfigurationReader('station.toml','satellites.toml')
    config.print_satellites()
    loader = TleLoader(config.satellites)
    loader.loadTLE() 
    config.print_satellites()
    satellites=config.satellites
    station = config.station
    receiver = config.receiver
    ts = load.timescale()
    start_time = ts.now()
    end_time = ts.now() + 1 #Raw numbers specify days of Terrestrial Time 
    planifier = Planifier(station, satellites, start_time, end_time,logging.INFO)
    planifier.computeObservations()
    n=len(planifier.observationsList)
    print(f'{n} Observation du {start_time.utc_strftime(format="%Y-%m-%dT%H:%M:%SZ")} au {end_time.utc_strftime(format="%Y-%m-%dT%H:%M:%SZ")}')
    for observation in planifier.observationsList :
        observation.printObservation()   
    planifier.writeObservations2Toml()
    
    recorder = Recorder(station, receiver, satellites, start_time, end_time,logging.DEBUG)
    for observation in planifier.observationsList :
        observation.printObservation() 
        recorder.trackAndRecord(observation)