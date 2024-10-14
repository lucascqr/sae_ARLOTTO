# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 14:41:32 2024

@author: anoel
"""

from ConfigurationReader import ConfigurationReader
from skyfield.api import load, wgs84


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
                print("fichier TLE trop ancien")

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
            # print(satellite.name)
            bluffton = wgs84.latlon(
                self.station.latitude, self.station.longitude)
            t0, t1 = self.start_time,  self.end_time
            t, events = satellite.tle[0].find_events(
                bluffton, t0, t1, altitude_degrees=satellite.min_elevation)
            event_names = 'rise', 'culminate', 'set'

            visibility_window_open = False
            for ti, event in zip(t, events):
                name = event_names[event]
                # print(ti.utc_strftime('%Y %b %d %H:%M:%S'), name)

                if name == 'rise':
                    t_rise = ti
                    visibility_window_open = True

                elif name == 'culminate':
                    t_culminate = ti
                    topocentric_position = (
                        satellite.tle[0] - bluffton).at(t_culminate)
                    alt, az, distance = topocentric_position.altaz()
                    # print(f"Angle de culmination : {alt.degrees:.2f}°")
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
                # print ('nom',satellite.name, window  )
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
    # config.satellites[0].print_visibility_windows()
    computer.print_observation()
