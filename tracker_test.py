# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 15:59:59 2024

@author: anoel
"""

from ConfigurationReader import ConfigurationReader
from TLE_Loader import Tle_Loader, VisibilyWindowComputer
from Planifier_remake import Plannifier
from skyfield.api import load, wgs84
import time
import matplotlib.pyplot as plt
import numpy as np


class Tracker():
    def __init__(self, station, rotator):
        self.station = station
        self.rotator = rotator
        self.tle = None
        self.start_az = None
        self.stop_az = None
        self.middle_az = None
        self.trajectory = []

    def track_satellite(self, observation):
        self.tle = observation.satellite.tle[0]

    def calcul_normalize_azimuth(self, observation):
        bluffton = wgs84.latlon(
            self.station.latitude, self.station.longitude)
        ts = load.timescale()

        azimuths = []
        azimuths_normalize = []
        altitudes = []
        altitudes_normalize = []
        times = []
        times_3D = []
        trajectory = []

        current_time = observation.visibility_window[0]
        stop_time = observation.visibility_window[1]

        current_time_1 = current_time

        topocentric_position = (
            observation.satellite.tle[0] - bluffton).at(current_time)
        alt, self.start_az, distance = topocentric_position.altaz()

        topocentric_position = (
            observation.satellite.tle[0] - bluffton).at(stop_time)
        alt, self.stop_az, distance = topocentric_position.altaz()

        print(observation.satellite.name)
        print(current_time.utc_strftime(format='%Y-%m-%d %H:%M:%S UTC'))
        print(stop_time.utc_strftime(format='%Y-%m-%d %H:%M:%S UTC'))

        while current_time_1 < stop_time:
            topocentric_position = (
                observation.satellite.tle[0] - bluffton).at(current_time_1)
            alt, az, distance = topocentric_position.altaz()

            trajectory.append(az.degrees)

            current_time_1 = ts.utc(current_time_1.utc.year, current_time_1.utc.month, current_time_1.utc.day,
                                    current_time_1.utc.hour, current_time_1.utc.minute + 1)

        # print(observation.satellite.name, self.trajectory)
        normalize = self.normalize_trajectory(trajectory)
        # print(observation.satellite.name, normalize)

        while current_time < stop_time:

            topocentric_position = (
                observation.satellite.tle[0] - bluffton).at(current_time)
            alt, az, distance = topocentric_position.altaz()

            az_normalize, elev_normalize = self.normalize_azimuth(
                az, alt.degrees, normalize)

            if alt.degrees > 5:
                azimuths.append(az.degrees)
                azimuths_normalize.append(az_normalize)
                altitudes.append(alt.degrees)
                altitudes_normalize.append(elev_normalize)
                times.append(current_time.utc_strftime('%Y-%m-%d %H:%M:%S'))
                times_3D.append(current_time)

            current_time = ts.utc(current_time.utc.year, current_time.utc.month, current_time.utc.day,
                                  current_time.utc.hour, current_time.utc.minute + 1)

        self.plot_azimuth_polar(azimuths, azimuths_normalize,
                                times, observation.satellite.name)
        self.plot_azimuth(azimuths, azimuths_normalize,
                          times, observation.satellite.name)
        self.plot_Alt(altitudes, altitudes_normalize,
                      times, observation.satellite.name)

    def normalize_trajectory(self, trajectory):
        for i, azimuths in enumerate(trajectory[:-1]):
            next_azimuths = trajectory[i + 1]
            if abs(next_azimuths - azimuths) > 180:
                # print(next_azimuths, azimuths, "\n")
                if self.start_az.degrees < 90 or self.stop_az.degrees < 90:
                    return 450
                else:
                    return 180
            else:
                normalize = 0

        return normalize

    def normalize_azimuth(self, azimuth, elevation, normalize):
        az_normalized = azimuth.degrees
        elevation_normalized = elevation
        if normalize == 180:
            if azimuth.degrees > 180:
                az_normalized -= 180
            else:
                az_normalized += 180
            elevation_normalized = 180 - elevation
        elif normalize == 450:
            if azimuth.degrees < 90:
                az_normalized += 360

        return az_normalized, elevation_normalized

    def calcul_position(self, t):
        bluffton = wgs84.latlon(
            self.station.latitude, self.station.longitude)
        topocentric_position = (self.tle - bluffton).at(t)  # ┤faute à corriger
        alt, az, distance = topocentric_position.altaz()
        return alt, az, distance

    def plot_azimuth_polar(self, azimuths, azimuths_normalize, times, name):
        azimuths = np.radians(azimuths)
        azimuths_normalize = np.radians(azimuths_normalize)
        plt.figure(figsize=(10, 6))
        ax = plt.subplot(111, projection='polar')
        ax.plot(azimuths_normalize, np.ones_like(azimuths_normalize),
                marker='x', color='r')
        ax.plot(azimuths,  np.full_like(azimuths, 1.5),
                marker='o', linestyle='-', color='b')
        ax.set_theta_zero_location("N")
        plt.title(f"Évolution de l'Azimut du Satellite :{name}")
        ax.set_theta_direction(-1)
        plt.xlabel("Temps (UTC)")
        plt.ylabel("Azimut (degrés)")
        # plt.ylim(0, 450)
        # ax.grid()

        # for x, y in zip(times, azimuths):
        #     plt.text(x, y + 10, f"{y:.1f}", ha='center',
        #              color='black', fontsize=8)
        plt.show()

    def plot_azimuth(self, azimuths, azimuths_normalize, times, name):
        plt.figure(figsize=(10, 6))
        plt.plot(times, azimuths, marker='x', color='b')
        plt.plot(times, azimuths_normalize, marker='o', color='r')
        plt.title(
            f"Évolution des azimutes en fonctions du temps du satellite :{name}")
        plt.xlabel("Temps(UTC)")
        plt.ylabel("Azimut (deg)")
        for x, y in zip(times, azimuths):
            plt.text(x, y + 10, f"{y:.1f}", ha='center',
                     color='black', fontsize=8)

        plt.show()

    def plot_Alt(self, altitudes, altitudes_normalize, times, name):
        plt.figure(figsize=(10, 6))
        plt.plot(times, altitudes, marker='x', color='r')
        plt.plot(times, altitudes_normalize, marker='o', color='b')
        plt.title(
            f"Évolution de l'altitudes en fonction du temps du satellite :{name}")
        plt.xlabel("Temps(UTC)")
        plt.ylabel("Altitudes (degrees)")
        for x, y in zip(times, altitudes):
            plt.text(x, y + 0.2, f"{y:.1f}", ha='center',
                     color='black', fontsize=8)
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
        tracker.calcul_normalize_azimuth(obs)
