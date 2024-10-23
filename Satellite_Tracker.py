# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 10:14:21 2024

@author: anoel
"""
from ConfigurationReader import ConfigurationReader
from TLE_Loader import Tle_Loader, VisibilyWindowComputer
from Planifier_remake import Plannifier
from skyfield.api import load, wgs84


class Tracker():
    def __init__(self, station):
        self.station = station
        self.tle = None

    def track_satellite(self, observation):

        start_time = observation.visibility_window[0]
        stop_time = observation.visibility_window[1]
        self.tle = observation.satellite.tle[0]
        ts = load.timescale()
        start_alt, start_az, start_distance = self.calcul_position(start_time)
        stop_alt, stop_az, stop_distance = self.calcul_position(stop_time)

        print(start_az, stop_az)

        # si l'angle d'arret < 90° et que l'angle de départ est supérieur 270
        # alors je change l'angle d'arret pour qu'elle aille jusqu'à 450
        # sinon si l'angle de départ est inférieur à 90 et que l'angle de fin est supérieur à 270
        # alors je change l'angle de départ entre 360 et 450

        # envoi des positions de départ au moteur
        # tant que la position du moteur n'est pas égale à la position de départ du satellite
        # on attends que le moteur se place
        # while (1):
        # si l'écart entre temps actuel est le temps de départ est inférieur a 10s
        # Attends
        # sinon
        # on vérifie si l'écart entre az du moteur et l'az de satellite > 10°
        # si c'est le cas alors on calcul les nouvelles positions et on les envois au moteur
        # sinon
        # Attends

    def calcul_position(self, time):
        bluffton = wgs84.latlon(
            self.station.latitude, self.station.longitude)
        topocentric_position = (self.tle - bluffton).at(time)
        alt, az, distance = topocentric_position.altaz()
        return alt, az, distance


if __name__ == "__main__":
    station_file = 'toml/station.toml'
    satellites_file = 'toml/satellites.toml'

    config = ConfigurationReader(station_file, satellites_file)
    loader = Tle_Loader(config.satellites,
                        config.directories.tle_dir, config.tle.max_days)
    loader.tleLoader()

    ts = load.timescale()
    start_time = ts.now()
    stop_time = ts.now() + 1

    computer = VisibilyWindowComputer(
        config.satellites, config.station, start_time, stop_time)
    computer.compute_Observation()

    planning = Plannifier(computer.observations, config.satellites)
    planning.Planning_Maker()
    # planning.plot_planning()
    # print(planning.observations[0].visibility_window[0])
    # print(planning.planning[0].visibility_window[0])
    tracker = Tracker(config.station)
    for obs in planning.planning:
        tracker.track_satellite(obs)
