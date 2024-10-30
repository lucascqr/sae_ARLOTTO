# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 10:14:21 2024

@author: anoel
"""
from ConfigurationReader import ConfigurationReader
from TLE_Loader import Tle_Loader, VisibilyWindowComputer
from Planifier_remake import Plannifier
from skyfield.api import load, wgs84
import socket
import time


class Tracker():
    def __init__(self, station, rotator):
        self.station = station
        self.rotator = rotator
        self.tle = None
        self.socket = None

    def connect_rotcltd(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.rotator.ip, self.rotator.port))

    def track_satellite(self, observation):

        start_time = observation.visibility_window[0]
        stop_time = observation.visibility_window[1]
        self.tle = observation.satellite.tle[0]

        start_alt, start_az, start_distance = self.calcul_position(start_time)
        stop_alt, stop_az, stop_distance = self.calcul_position(stop_time)

        start_az.degrees, stop_az.degrees = self.normalize_azimuth(
            start_az.degrees, stop_az.degrees)

        self.send_motor_position(start_az.degrees, start_alt.degrees)

       # envoi des positions de départ au moteur
        # tant que la position du moteur n'est pas égale à la position de départ du satellite
        # on attends que le moteur se place
        while (1):
            ts = load.timescale()
            alt, az, distance = self.calcul_position(ts)

            if ts < start_time:
                time.sleep(10)
            else:
                az_motor, alt_motor = self.get_motor_position()
                az_motor, alt_motor = self.normalize_azimuth(
                    az_motor, alt_motor)
                if (az-az_motor > 10):
                    self.send_motor_position(az, alt)
                else:
                    time.sleep(5)
        # si l'écart entre temps actuel est le temps de départ est inférieur a 10s
        # Attends
        # sinon
        # on vérifie si l'écart entre az du moteur et l'az de satellite > 10°
        # si c'est le cas alors on calcul les nouvelles positions et on les envois au moteur
        # sinon
        # Attends

    def normalize_azimuth(self, azimuth_start, azimuth_stop):
        if azimuth_stop <= 90 and azimuth_start > 270:
            azimuth_stop = 360 + azimuth_stop
            return azimuth_start, azimuth_stop

        elif azimuth_start <= 90 and azimuth_stop > 270:
            azimuth_start = 360 + azimuth_start
            return azimuth_start, azimuth_stop

        else:
            return azimuth_start, azimuth_stop
        # todo trouver une solution pour avoir les bon angles lors des passages voir les screens

    def send_motor_position(self, azimuth, elevation):
        command = f'P {azimuth} {elevation}\n'
        self.socket.sendall(command.encode())
        response = self.socket.recv(1024).decode()
        print(f'Received: {response}')

    def get_motor_position(self):
        command = 'p\n'
        self.socket.sendall(command.encode())
        response = self.socket.recv(1024).decode()
        index = response.find('\n')
        len_rep = len(response)
        print(f'Received: {response}')

        azimuth = float(response[0:index])
        elevation = float(response[index+1:len_rep-1])
        return azimuth, elevation

    def calcul_position(self, t):
        bluffton = wgs84.latlon(
            self.station.latitude, self.station.longitude)
        topocentric_position = (self.tle - bluffton).at(t)
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
    tracker = Tracker(config.station, config.rotator)
    for obs in planning.planning:
        tracker.track_satellite(obs)
    # tracker.connect_rotcltd()
