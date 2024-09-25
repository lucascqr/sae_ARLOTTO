#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul  7 12:17:55 2024

@author: philippe
"""
import logging
from skyfield.api import load
from skyfield.iokit import parse_tle_file

class TleLoader():
    def __init__(self, satellites):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        logging.getLogger().setLevel(logging.INFO)
        self.satellites = satellites
    # load (or reload if more than max_days old) tle of every sat
    # then add tle to every sat as a new EarthSatellite attribute
    # set max_days = 0 to force reload from celestrak.org
    def loadTLE(self, max_days = 7.0):
      
       # https://celestrak.org/NORAD/documentation/gp-data-formats.php
       #https://celestrak.org/NORAD/elements/gp.php?{QUERY}=VALUE[&FORMAT=VALUE]
       
       base ='https://celestrak.org/NORAD/elements/gp.php' #'NAME={value}&FORMAT=tle'
       for sat in self.satellites :
           name = sat.name + '.tle'
           name = name.replace(' ', '_')
           if not load.exists(name) or load.days_old(name) >= max_days:
               url = base + '?NAME='+(sat.name).replace(' ','%20')+'&FORMAT=tle'
               load.download(url, filename=name)
           ts = load.timescale()
           with load.open(name) as f:
              sat.EarthSatellite=list(parse_tle_file(f, ts))
              if len(sat.EarthSatellite) > 1 :
                  self.logger.warning(f'more than one satellite found in {name} !')
                  self.logger.warning(f'Only the first one will be used for {sat.name}')
                  
              
if __name__ == "__main__":
    
    from ConfigurationReader import ConfigurationReader
    config = ConfigurationReader('station.toml','satellites.toml')
    config.print_satellites()
    loader = TleLoader(config.satellites)
    loader.loadTLE() 
    config.print_satellites()