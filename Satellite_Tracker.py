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
        self.stop_az = None

    def connect_rotcltd(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.rotator.ip, self.rotator.port))

    def track_satellite(self, observation):
        start_time = observation.visibility_window[0]
        stop_time = observation.visibility_window[1]
        self.tle = observation.satellite.tle[0]

    def normalize_azimuth(self, azimuth):

        # az_normalize = azimuth
        # if self.start_az.degrees < 90 and self.stop_az.degrees > 190:
        #     # print("1er : ", self.stop_az.degrees)
        #     if az_normalize.degrees < 90:
        #         az_normalize.degrees += 360
        # elif self.start_az.degrees > 200 and self.stop_az.degrees < 90:
        #     # print("2e : ", self.stop_az.degrees)
        #     if az_normalize.degrees < 90:
        #         az_normalize.degrees += 360

        # return az_normalize.degrees
        az_normalized = azimuth.degrees
        if self.start_az.degrees < 90 and self.stop_az.degrees > 190:
            if azimuth.degrees < 90:
                az_normalized += 360
        elif self.start_az.degrees > 200 and self.stop_az.degrees < 90:
            if azimuth.degrees < 90:
                az_normalized += 360
        return az_normalized

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
        topocentric_position = (self.tle - bluffton).at(t)  # à corriger
        alt, az, distance = topocentric_position.altaz()
        return alt, az, distance

    def calcul_normalize_azimuth(self, observation):
        bluffton = wgs84.latlon(
            self.station.latitude, self.station.longitude)
        ts = load.timescale()

        azimuths = []
        azimuths_normalize = []
        altitudes = []
        times = []
        times_3D = []

        current_time = observation.visibility_window[0]
        stop_time = observation.visibility_window[1]
        topocentric_position = (
            observation.satellite.tle[0] - bluffton).at(current_time)
        alt, self.start_az, distance = topocentric_position.altaz()

        topocentric_position = (
            observation.satellite.tle[0] - bluffton).at(stop_time)
        alt, self.stop_az, distance = topocentric_position.altaz()

        while current_time < observation.visibility_window[1]:
            topocentric_position = (
                observation.satellite.tle[0] - bluffton).at(current_time)
            alt, az, distance = topocentric_position.altaz()

            az_normalize = self.normalize_azimuth(az)
            # az_normalize = 0

            if alt.degrees > 5:
                azimuths.append(az.degrees)
                azimuths_normalize.append(az_normalize)
                altitudes.append(alt.degrees)
                times.append(current_time.utc_strftime('%Y-%m-%d %H:%M:%S'))
                times_3D.append(current_time)

            current_time = ts.utc(current_time.utc.year, current_time.utc.month, current_time.utc.day,
                                  current_time.utc.hour, current_time.utc.minute + 1)

        self.plot_azimuth(azimuths, azimuths_normalize,
                          times, observation.satellite.name)
        # self.plot_azimuth_3d(azimuths, altitudes, times_3D, observation.visibility_window[0], observation.visibility_window[1],
        #                      observation.satellite.name)

    def plot_azimuth(self, azimuths, azimuths_normalize, times, name):
        plt.figure(figsize=(10, 6))
        plt.plot(times, azimuths_normalize,
                 marker='x', color='r')
        plt.plot(times, azimuths, marker='o', linestyle='-', color='b')
        plt.title(f"Évolution de l'Azimut du Satellite :{name}")
        plt.xlabel("Temps (UTC)")
        plt.ylabel("Azimut (degrés)")
        plt.ylim(0, 450)
        plt.grid()

        for x, y in zip(times, azimuths):
            plt.text(x, y + 10, f"{y:.1f}", ha='center',
                     color='black', fontsize=8)
        plt.show()

    def plot_azimuth_3d(self, azimuths, altitudes, times, start_time, stop_time, name):
        start_time = start_time.utc[0] * 86400 + start_time.utc[1]
        stop_time = stop_time.utc[0] * 86400 + stop_time.utc[1]
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111, projection='3d')
        times = np.array([t.utc[0] * 86400 + t.utc[1] for t in times])/60

        ax.plot(azimuths, times, altitudes,
                marker='o', linestyle='-', color='b')
        ax.set_title(
            f"Évolution de l'Azimut et Altitude du Satellite : {name}")

        ax.set_ylabel("Temps (UTC)")
        ax.set_xlabel("Azimut (degrés)")
        ax.set_zlabel("Altitude (degrés)")

        ax.set_ylim(start_time/60, stop_time/60)

        plt.show()


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
        # tracker.track_satellite(obs)
        tracker.calcul_normalize_azimuth(obs)
    # tracker.connect_rotcltd()
