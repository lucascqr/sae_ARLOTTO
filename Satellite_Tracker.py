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
import matplotlib.pyplot as plt
import numpy as np


class Tracker():
    def __init__(self, station, rotator):
        self.station = station
        self.rotator = rotator
        self.tle = None
        self.socket = None
        self.start_az = None
        self.start_alt = None
        self.stop_az = None
        self.normalize = None

    def connect_rotcltd(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.rotator.ip, self.rotator.port))

    def track_satellite(self):
        az, alt = self.normalize_trajectory(self.start_az, self.start_alt)
        self.send_motor_position(az, alt)

        while (1):
            ts = load.timescale()
            alt, az, distance = self.calcul_position(ts)
            alt, az = self.normalize_trajectory(self.start_az, self.start_alt)

            if ts < start_time:
                time.sleep(10)
            else:
                az_motor, alt_motor = self.get_motor_position()
                if (abs(az.degrees-az_motor) > 10):
                    self.send_motor_position(az, alt)
                else:
                    time.sleep(5)

    def normalize_trajectory(self, azimuth, elevation):

        az_normalized = azimuth.degrees
        elevation_normalized = elevation.degrees
        if self.normalize == 180:
            if azimuth.degrees > 180:
                az_normalized -= 180
            else:
                az_normalized += 180
            elevation_normalized = 180 - elevation
        elif self.normalize == 450:
            if azimuth.degrees < 90:
                az_normalized += 360

        return az_normalized, elevation_normalized

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
        topocentric_position = (self.tle - bluffton).at(t)  # à corriger
        alt, az, distance = topocentric_position.altaz()
        return alt, az, distance

    def calcul_trajectory(self, observation):
        self.tle = observation.satellite.tle[0]

        trajectory = []

        current_time = observation.visibility_window[0]
        stop_time = observation.visibility_window[1]

        self.start_alt, self.start_az, distance = self.calcul_position(
            current_time)
        alt, self.stop_az, distance = self.calcul_position(stop_time)

        while current_time < stop_time:
            alt, az, distance = self.calcul_position(current_time)

            trajectory.append(az.degrees)

            current_time = ts.utc(current_time.utc.year, current_time.utc.month, current_time.utc.day,
                                  current_time.utc.hour, current_time.utc.minute + 1)

        self.normalize = self.select_azimuth_normalization(trajectory)
        self.track_satellite()

    def select_azimuth_normalization(self, trajectory):

        for i, azimuths in enumerate(trajectory[:-1]):
            next_azimuths = trajectory[i + 1]
            if abs(next_azimuths - azimuths) > 180:
                print(next_azimuths, azimuths, "\n")
                if self.start_az.degrees < 90 or self.stop_az.degrees < 90:
                    return 450
                else:
                    return 180
            else:
                normalize = 0

        return normalize


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
    tracker.connect_rotcltd()
    for obs in planning.planning:
        # tracker.track_satellite(obs)
        tracker.calcul_trajectory(obs)
