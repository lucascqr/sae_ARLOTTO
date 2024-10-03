# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 14:45:36 2024

@author: lucas
"""

import logging
from ConfigurationReader import ConfigurationReader,Station,Satellite
from tleLoader import TleLoader
from skyfield.api import wgs84


class Plannifier():
    def __init__(self,station,satellites,start_time,end_time,level = logging.INFO):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        logging.getLogger().setLevel(level)
        self.station = station
        self.satellites = satellites
        self.start_time = start_time
        self.end_time = end_time
        self.observationsList = []  # listes des observations sans chevauchement
        
        
    