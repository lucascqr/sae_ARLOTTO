# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 14:41:32 2024

@author: anoel
"""

from ConfigurationReader import ConfigurationReader
from skyfield.api import load, wgs84
import matplotlib.pyplot as plt
import numpy as np


class Tle_Loader ():

    def __init__(self, satellites, tle_dir, max_days):
        self.satellites = satellites
        self.tle_dir = tle_dir
        self.max_days = max_days

    def tleLoader(self):
        for sat in self.satellites:
            name = sat.name + '.tle'
            if load.days_old(self.tle_dir + '/' + name) < self.max_days:
                sat.tle = load.tle_file(self.tle_dir + '/' + name)
            else:
                sat.tle = None
                print(
                    "Fichier TLE", sat.name, " trop ancien ou inexistant")

    def printTle(self):
        for sat in self.satellites:
            print(sat.tle)


class Observation ():

    def __init__(self, satellite, visibility_window):
        self.satellite = satellite
        self.visibility_window = visibility_window
        self.state = None

    def print(self):
        print('satellite : ', self.satellite,
              'fenêtre visible : ', self.visibility_window)


class VisibilyWindowComputer ():

    def __init__(self, satellites, station, start_time, end_time):
        self.satellites = satellites
        self.station = station
        self.start_time = start_time
        self.end_time = end_time

        self.observations = []

    def computeVisibilityWindow(self, satellite):
        if satellite.tle:
            bluffton = wgs84.latlon(
                self.station.latitude, self.station.longitude)
            t0, t1 = self.start_time,  self.end_time
            t, events = satellite.tle[0].find_events(
                bluffton, t0, t1, altitude_degrees=satellite.min_elevation)
            event_names = 'rise', 'culminate', 'set'

            visibility_window_open = False
            for ti, event in zip(t, events):
                name = event_names[event]

                if name == 'rise':
                    t_rise = ti
                    visibility_window_open = True

                elif name == 'culminate':
                    t_culminate = ti
                    topocentric_position = (
                        satellite.tle[0] - bluffton).at(t_culminate)
                    alt, az, distance = topocentric_position.altaz()

                else:
                    t_set = ti

                    if visibility_window_open:
                        visibility_window_open = False
                        if alt.degrees > satellite.min_culmination:
                            satellite.add_visibility_window(
                                t_rise, t_set, t_culminate)

    def compute_Observation(self):
        for satellite in self.satellites:
            self.computeVisibilityWindow(satellite)
            for window in satellite.visibility_windows:
                observ = Observation(satellite, window)
                self.observations.append(observ)

        self.observations.sort(key=lambda obs: obs.visibility_window[0])

    def print_observation(self):

        for obs in self.observations:
            start_time = obs.visibility_window[0]
            stop_time = obs.visibility_window[1]
            culmination_time = obs.visibility_window[2]
            satellite_name = obs.satellite.name  # Nom du satellite
            print(f"Satellite: {satellite_name}\n Début du passage: {start_time.utc_strftime('%Y-%m-%d %H:%M:%S')}\n",
                  f"fin de passage : {
                      stop_time.utc_strftime('%Y-%m-%d %H:%M:%S')}\n",
                  f"culmination : {culmination_time.utc_strftime('%Y-%m-%d %H:%M:%S')}")

    def calcul_azimuth(self, observation):
        bluffton = wgs84.latlon(
            self.station.latitude, self.station.longitude)
        ts = load.timescale()

        azimuths = []
        altitudes = []
        times = []
        times_3D = []
        current_time = observation.visibility_window[0]
        while current_time < observation.visibility_window[1]:
            topocentric_position = (
                observation.satellite.tle[0] - bluffton).at(current_time)
            alt, az, distance = topocentric_position.altaz()

            if alt.degrees > 5:
                azimuths.append(az.degrees)
                altitudes.append(alt.degrees)
                times.append(current_time.utc_strftime('%Y-%m-%d %H:%M:%S'))
                times_3D.append(current_time)

            current_time = ts.utc(current_time.utc.year, current_time.utc.month, current_time.utc.day,
                                  current_time.utc.hour, current_time.utc.minute + 1)

        self.plot_azimuth(azimuths, times, observation.satellite.name)
        self.plot_azimuth_3d(azimuths, altitudes, times_3D, observation.visibility_window[0], observation.visibility_window[1],
                             observation.satellite.name)

    def plot_azimuth(self, azimuths, times, name):
        plt.figure(figsize=(10, 6))
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


if __name__ == '__main__':
    station_file = 'toml/station.toml'
    satellites_file = 'toml/satellites.toml'

    config = ConfigurationReader(station_file, satellites_file)
    loader = Tle_Loader(config.satellites,
                        config.directories.tle_dir, config.tle.max_days)
    loader.tleLoader()
    # loader.printTle()

    ts = load.timescale()
    start_time = ts.now()
    stop_time = ts.now() + 1
    computer = VisibilyWindowComputer(
        config.satellites, config.station, start_time, stop_time)
    computer.compute_Observation()
    computer.print_observation()


# calcul des azimuthes des satellites en degrées pendant leur passage
    for obs in computer.observations:
        computer.calcul_azimuth(obs)
