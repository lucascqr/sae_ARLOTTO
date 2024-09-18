#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul  6 15:50:43 2024

@author: philippe
"""
import toml

# ConfigurationReader class
class ConfigurationReader:
    def __init__(self, station_file, satellites_file):
        self.satellites_file = satellites_file
        self.station_file = station_file
        self.satellites = [] # listes des satellites à recevoir
        self.station = None 
        self.receiver = None
        self.rotator = None
        self.read_configuration()
        
    def read_configuration(self):
        with open(self.station_file, 'r') as f:
            data= toml.load(f)
            s=data['station']
            self.station = Station(s['name'],s['latitude'],s['longitude'],\
                                   s['altitude'],s['locator'])
            rx=data['receiver']
            self.receiver= Receiver(rx['name'], rx['ip'])
            rot = data['rotator']
            self.rotator = Rotator(rot['name'], rot['ip'])
        
        with open(self.satellites_file, 'r') as f:
            data= toml.load(f)
            for sat in data['satellites'] :
                s=Satellite(sat)
                self.satellites.append(s)
            #print(self.satellites)  
            
            
    def print_station_configuration(self):
        print('Ground Station Configuration read from',self.station_file)
        self.station.print()
    
    def print_satellites(self):
        print('Recorded Satellites read from',self.satellites_file)
        for sat in self.satellites :
            print(sat.__dict__)

# Satellite class
class Satellite(object):
    # les attributs sont crées par le dictionnaire issu du fichier toml
    def __init__(self, initial_data):
        for key in initial_data:
            setattr(self, key, initial_data[key])

       
        self.visibility_windows = []
    
    def add_visibility_window(self, start_time, end_time,culminate=None):
        self.visibility_windows.append((start_time, end_time,culminate))
        
    def print_visibility_windows(self) :
        for w in self.visibility_windows :
            print(f"rise {w[0].utc_strftime(format='%Y-%m-%d %H:%M:%S UTC')}",\
                  f"set {w[1].utc_strftime(format='%Y-%m-%d %H:%M:%S UTC')}")
        
# ground station class
class Station:
    def __init__(self, name,latitude,longitude,altitude,locator):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.locator = locator
    def print(self):
        print('name',self.name)
        print('latitude',self.latitude, 'longitude', self.longitude, \
              'altitude',self.altitude)
        print('locator',self.locator)
        
# receiver class
class Receiver:
    def __init__(self,name,ip):
        self.name = name
        self.ip = ip
# rotator class
class Rotator :
    def  __init__(self,name,ip):
        self.name = name
        self.ip = ip