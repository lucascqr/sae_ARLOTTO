#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul  7 17:06:10 2024

@author: philippe
"""
import logging
from ConfigurationReader import ConfigurationReader,Station,Satellite
from tleLoader import TleLoader
from skyfield.api import wgs84

class Planifier() :
    def __init__(self,station,satellites,start_time,end_time,level = logging.INFO):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        logging.getLogger().setLevel(level)
        self.station = station
        self.satellites = satellites
        self.start_time = start_time
        self.end_time = end_time
        self.observationsList = []  # listes des observations sans chevauchement
        
    def computeVisibilityWindows(self,satellite):
        bluffton = wgs84.latlon(self.station.latitude,self.station.longitude)
        t0 = self.start_time
        t1 = self.end_time 
        min_elevation= satellite.min_elevation
        skyfiledSatellite = satellite.EarthSatellite[0] # should have only one sat
        t, events = skyfiledSatellite.find_events(bluffton, t0, t1\
                                          ,altitude_degrees=min_elevation)
        event_names = ('rise', 'culminate', 'set')
        done = False
        begin = False
        for ti, event in zip(t, events):
                name = event_names[event]
               # print(name,begin,done)
                if name =='rise':
                    begin=True
                    t_rise = ti
                elif name=='culminate' : # !! ne prend pas en compte les culminations multiples
                    t_culminate = ti
                    if not begin :
                        t_rise = ti
                        begin=True
                else :
                    t_set = ti
                    if begin :
                      done = True
                      begin = False
                    else :
                        continue
                 
                self.logger.debug(f"{ti.utc_strftime('%Y %b %d %H:%M:%S')}, {name}")
                # on vérifier si la culmination est assez élevée pour 
                # considérer le passage
                if done :                   
                    geocentric = skyfiledSatellite.at(t_culminate)
                    difference = skyfiledSatellite - bluffton
                    topocentric = difference.at(t_culminate)
                    alt, az, distance = topocentric.altaz()
                    self.logger.debug(f'{alt},{az}')
                    if alt.degrees > satellite.min_culmination :
                          self.logger.debug(f'conservé car > {satellite.min_culmination}')
                          satellite.add_visibility_window(t_rise,t_set,alt)
                    else :
                        self.logger.debug(f' non conservé car < {satellite.min_culmination}')
                    done = False
   
    
    def computeObservations(self):
        # on calcule les fenêtres de visibilités de chaque satellite pour
        # la période
        for satellite in self.satellites :
            self.computeVisibilityWindows(satellite)
        
        observations = [] # listes des observations avec chevauchement possibles
        
        for satellite in self.satellites :
            for window in satellite.visibility_windows :
                obs = Observation(satellite,window)
                observations.append(obs)
        # trie des observations en fonction de la date de départ (rise)
        observations = sorted(observations,key=lambda observation: observation.observationWindow[0]) 
        # suppression des observations qui se chevauchent en fonction
        # de la priorité du satellite
        
        i=0
        j=1
        last = False
        while i < len(observations):
            #print(i,j,last)        
            t_end = observations[i].observationWindow[1]
            if not last :
                t_begin_next = observations[j].observationWindow[0]
            
            if (t_end > t_begin_next) and not last : # conflit 
                #print(f"conflit entre {observations[i].satellite.name} et {observations[j].satellite.name}")
                if observations[i].satellite.priority <  observations[j].satellite.priority :
                    j+=1 # on va tester la passage suivant en gardant le i
                    #print(f"{observations[i].satellite.name} conservé")
                    if j>=len(observations) :
                        last = True
                else :
                   # print(f"{observations[j].satellite.name} conservé")
                    i=j # on élimine le i 
                    j+=2 # on examine si conflit avec la suivante
                    if j>=len(observations) :
                        last = True
            else : # pas de conflit ou dernier
                self.observationsList.append(observations[i]) 
                i=j # attention pas forcément i+=1 !!
                j+=1
                if j>=len(observations) :
                        last = True
                        
    def writeObservations2Toml(self,baseName = 'planification',dateInFileName=False):
        fileName = baseName
        if dateInFileName :
            fileName = '-' + self.start_time.utc_strftime(format="%Y-%m-%dT%H:%M:%SZ")
            fileName += '-to-' + self.end_time.utc_strftime(format="%dT%H:%M:%SZ")
        fileName +='.toml'
        with open(fileName,'w') as f :
            f.write(f'title="{baseName}"\n')
            f.write('#dates are in RFC3339 UTC timestamp format\n\n')
            f.write(f'#computed from {self.start_time.utc_strftime(format="%Y-%m-%dT%H:%M:%SZ")} to {self.end_time.utc_strftime(format="%Y-%m-%dT%H:%M:%SZ")}\n\n')
            for observation in self.observationsList :
              f.write('[[observations]]\n')
              f.write(f'satellite="{observation.satellite.name}"\n')
              # RFC3339 UTC timestamp
              f.write(f'start_time={observation.observationWindow[0].utc_strftime( format="%Y-%m-%dT%H:%M:%SZ") }\n')
              f.write(f'end_time={observation.observationWindow[1].utc_strftime( format="%Y-%m-%dT%H:%M:%SZ") }\n')
              f.write(f'culmination={round(observation.observationWindow[2].degrees)}\n\n')
        
class Observation():
    def __init__(self,satellite,observationWindow):
        self.satellite = satellite
        self.observationWindow = observationWindow
    def printObservation(self):
        print(f"{self.satellite.name:12s}:\t{self.observationWindow[0].utc_strftime('%b %d %H:%M:%S')} : {self.observationWindow[1].utc_strftime('%H:%M:%S')}\
              {round(self.observationWindow[2].degrees,0)} ")
        
    
    
                             
                
        
if __name__ == "__main__":
    
    from skyfield.api import load
    config = ConfigurationReader('station.toml','satellites.toml')
    config.print_satellites()
    loader = TleLoader(config.satellites)
    loader.loadTLE() 
    config.print_satellites()
    satellites=config.satellites
    station = config.station
    ts = load.timescale()
    start_time = ts.now()
    end_time = ts.now() + 1 #Raw numbers specify days of Terrestrial Time 
    planifier = Planifier(station, satellites, start_time, end_time,logging.DEBUG)
    planifier.computeObservations()
    n=len(planifier.observationsList)
    print(f'{n} Observation du {start_time.utc_strftime(format="%Y-%m-%dT%H:%M:%SZ")} au {end_time.utc_strftime(format="%Y-%m-%dT%H:%M:%SZ")}')
    for observation in planifier.observationsList :
        observation.printObservation()   
    planifier.writeObservations2Toml()
    # fileName = 'planification.toml'
    # with open(fileName,'w') as f :
    #     f.write('title="palnification"\n')
    #     f.write('#dates are in RFC3339 UTC timestamp format\n\n')
    #     f.write(f'#computed from {start_time.utc_strftime(format="%Y-%m-%dT%H:%M:%SZ")} to {end_time.utc_strftime(format="%Y-%m-%dT%H:%M:%SZ")}\n\n')
    #     for observation in planifier.observationsList :
    #       f.write('[[observations]]\n')
    #       f.write(f'satellite="{observation.satellite.name}"\n')
    #       # RFC3339 UTC timestamp
    #       f.write(f'start_time={observation.observationWindow[0].utc_strftime( format="%Y-%m-%dT%H:%M:%SZ") }\n')
    #       f.write(f'end_time={observation.observationWindow[1].utc_strftime( format="%Y-%m-%dT%H:%M:%SZ") }\n')
    #       f.write(f'culmination={round(observation.observationWindow[2].degrees)}\n\n')
    # for satellite in satellites :
    #     print(f'satellite {satellite.name}')
    #     planifier.computeVisibilityWindows(satellite)
    #     satellite.print_visibility_windows()
    # observations = []
    # for satellite in satellites :
    #     for window in satellite.visibility_windows :
    #         obs = Observation(satellite,window)
    #         observations.append(obs)
    # observations = sorted(observations,key=lambda observation: observation.observationWindow[0])
    # print(f'{len(observations)} observations avec risque de cheuvauchement :')
    # for observation in observations :
    #     #print(observation.satellite.name,observation.observationWindow[0].utc)
    #     observation.printObservation()
    # # suppression des observations qui se chevauchent en fonction
    # # de la priorité du satellite
    # observationsList = []
    
    
    # i=0
    # j=1
    # last = False
    # while i < len(observations):
    #     #print(i,j,last)        
    #     t_end = observations[i].observationWindow[1]
    #     if not last :
    #         t_begin_next = observations[j].observationWindow[0]
        
    #     if (t_end > t_begin_next) and not last :
    #         # conflit 
    #         print(f"conflit entre {observations[i].satellite.name} et {observations[j].satellite.name}")
    #         if observations[i].satellite.priority <  observations[j].satellite.priority :
    #             j+=1 # on va tester la passage suivant en gardant le i
    #             print(f"{observations[i].satellite.name} conservé")
    #             if j>=len(observations) :
    #                 last = True
    #         else :
    #             print(f"{observations[j].satellite.name} conservé")
    #             i=j # on élimine le i 
    #             j+=2 
    #             if j>=len(observations) :
    #                 last = True
    #     else :
    #         # pas de conflit ou dernier
    #         observationsList.append(observations[i])
    #         i=j # attention pas forcément i+=1 !!
    #         j+=1
    #         if j>=len(observations) :
    #                 last = True
    # print(f'{len(observationsList)} observations sans cheuvauchement :')               
    # for observation in observationsList :
    #     #print(observation.satellite.name,observation.observationWindow[0].utc)
    #     observation.printObservation()      
   
        