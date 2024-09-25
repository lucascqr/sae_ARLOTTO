# -*- coding: utf-8 -*-
"""
Created on Sun Sep 22 16:59:18 2024

@author: anoel
"""

from ConfigurationReader import ConfigurationReader
from skyfield.api import load
import urllib.parse

station_file = 'toml/station.toml'
satellites_file = 'toml/satellites.toml'

config = ConfigurationReader(station_file,satellites_file)

def DownloadTle () : 
    for i in range(len(config.satellites)) : 
        if not load.exists(config.satellites[i].name) or load.days_old(config.satellites[i].name) >= config.tle.max_days:
            download_adress = config.tle.tle_download_adress + '?NAME=' + urllib.parse.quote(config.satellites[i].name) + '&FORMAT=TLE'
            load.download(download_adress, filename = config.directories.tle_dir+"/"+config.satellites[i].name)
  
          
  
if __name__ == "__main__":
    
    DownloadTle()