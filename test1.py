# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 10:45:55 2024

@author: lucas
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 08:18:18 2024

@author: anoel
"""

import toml
from skyfield.api import load, wgs84
from ConfigurationReader import ConfigurationReader
from skyfield.api import load, wgs84
from TLE_Loader import Tle_Loader, VisibilyWindowComputer
import matplotlib.pyplot as plt
IDLE = 0
SELECTED = 1
EXCLUDED = 2
OVERLAPS_PREVIOUS = 3

START_TIME = 0
END_TIME = 1


class ConfigurationReader:

    def __init__(self, station_file, satellites_file):
        self.station_file = station_file
        self.satellites_file = satellites_file
        self.satellites = []
        self.station = None
        self.receiver = None
        self.rotator = None
        self.directories = None
        self.tle = None
        self.Read_Configuration()

    def Read_Configuration(self):

        with open(self.station_file, 'r') as f:
            data = toml.load(f)
            s = data['station']
            self.station = Station(s['name'], s['latitude'], s['longitude'],
                                   s['altitude'], s['locator'])
            rx = data['receiver']
            self.receiver = Receiver(rx['name'], rx['ip'], rx['api'])

            rot = data['rotator']
            self.rotator = Rotator(rot['name'], rot['ip'], rot['port'])

            fch = data['directories']
            self.directories = Directories(
                fch['base_dir'], fch['recording_output_dir'], fch['tle_dir'], fch['planification_dir'])

            tle = data['tle']
            self.tle = Tle(tle['max_days'], tle['tle_download_address'])

        with open(self.satellites_file, 'r') as f:
            data = toml.load(f)
            for sat in data['satellites']:
                s = Satellites(sat)
                self.satellites.append(s)
            self.set_priority()

    def set_priority(self):
        i = 0
        for sat in self.satellites:
            sat.priority = i
            print(sat.name, sat.priority)
            i = i+1


class Station:
    def __init__(self, name, latitude, longitude, altitude, locator):
        self.name = name
        self.longitude = longitude
        self.latitude = latitude
        self.altitude = altitude
        self.locator = locator

    def print(self):
        print('name', self.name)
        print('latitude', self.latitude, 'longitude', self.longitude,
              'altitude', self.altitude)
        print('locator', self.locator)


class Satellites:
    def __init__(self, initial_data={}):
        for key in initial_data:
            setattr(self, key, initial_data[key])

        self.visibility_windows = []
        self.priority = None

    def add_visibility_window(self, start_time, end_time, culminate=None):
        self.visibility_windows.append((start_time, end_time, culminate))

    def print_visibility_windows(self):
        for w in self.visibility_windows:
            print(f"rise {w[0].utc_strftime(format='%Y-%m-%d %H:%M:%S UTC')}",
                  f"set {w[1].utc_strftime(format='%Y-%m-%d %H:%M:%S UTC')}")


class Receiver:
    def __init__(self, name, ip, api):
        self.name = name
        self.ip = ip
        self.api = api

    def print(self):
        print('name', self.name, ' ip', self.ip, ' api', self.api)


class Rotator:
    def __init__(self, name, ip, port):
        self.name = name
        self.ip = ip
        self.port = port

    def print(self):
        print('name', self.name, ' ip', self.ip, ' port', self.port)


class Directories:
    def __init__(self, base_dir, recording_output_dir, tle_dir, planification_dir):
        self.base_dir = base_dir
        self.recording_output_dir = recording_output_dir
        self.tle_dir = tle_dir
        self.planification_dir = planification_dir

    def print(self):
        print('base_dir ', self.base_dir, ' recording_output', self.recording_output_dir,
              ' tle_dir', self.tle_dir, ' planification_dir', self.planification_dir)


class Tle:
    def __init__(self, max_days, tle_download_adress):
        self.max_days = max_days
        self.tle_download_adress = tle_download_adress

    def print(self):
        print('max_days', self.max_days, ' tle_adress', self.tle_download_adress)


class Observation ():

    def __init__(self, satellite, visibility_window):
        self.satellite = satellite
        self.visibility_window = visibility_window
        self.state = None


class Test_planning ():

    def __init__(self, satellites):
        self.satellites = satellites
        self.observations = []

    def test_plan(self):
        ts = load.timescale()
        self.satellites[0].add_visibility_window(
            ts.utc(2024, 10, 15, 12, 30, 45), ts.utc(2024, 10, 15, 12, 40, 45))
        self.satellites[1].add_visibility_window(
            ts.utc(2024, 10, 15, 12, 35, 45), ts.utc(2024, 10, 15, 12, 45, 45))
        self.satellites[2].add_visibility_window(
            ts.utc(2024, 10, 15, 12, 42, 45), ts.utc(2024, 10, 15, 12, 50, 45))

        self.satellites[3].add_visibility_window(
            ts.utc(2024, 10, 15, 13, 40, 45), ts.utc(2024, 10, 15, 13, 50, 45))
        self.satellites[2].add_visibility_window(
            ts.utc(2024, 10, 15, 13, 42, 45), ts.utc(2024, 10, 15, 13, 52, 45))
        self.satellites[4].add_visibility_window(
            ts.utc(2024, 10, 15, 13, 45, 45), ts.utc(2024, 10, 15, 13, 55, 45))

        self.satellites[0].add_visibility_window(
            ts.utc(2024, 10, 15, 14, 42, 45), ts.utc(2024, 10, 15, 14, 50, 45))
        self.satellites[1].add_visibility_window(
            ts.utc(2024, 10, 15, 14, 35, 45), ts.utc(2024, 10, 15, 14, 45, 45))
        self.satellites[2].add_visibility_window(
            ts.utc(2024, 10, 15, 14, 30, 45), ts.utc(2024, 10, 15, 14, 40, 45))

    def compute_observation(self):
        self.test_plan()
        # print(self.satellites[0].visibility_windows[0])
        for satellite in self.satellites:
            for window in satellite.visibility_windows:
                observ = Observation(satellite, window)
                self.observations.append(observ)
        self.observations.sort(key=lambda obs: obs.visibility_window[0])

    def print_observation(self):

        for obs in self.observations:
            start_time = obs.visibility_window[0]
            stop_time = obs.visibility_window[1]
            # culmination_time = obs.visibility_window[2]
            satellite_name = obs.satellite.name  # Nom du satellite
            print(f"Satellite: {satellite_name}\n Début du passage: {start_time.utc_strftime('%Y-%m-%d %H:%M:%S')}\n",
                  f"fin de passage : {stop_time.utc_strftime('%Y-%m-%d %H:%M:%S')}\n")


class Plannifier ():
    def __init__(self, observations):
        self.observations = observations
        self.planning = []

    def Planning_Maker(self):
        for observation in self.observations:
            observation.state = IDLE

        LAST_SELECTED = None

        for i, observation in enumerate(self.observations[:-1]):
            next_observation = self.observations[i + 1]
            previous_observation = self.observations[i-1]
            if observation.state == IDLE:
                if observation.visibility_window[END_TIME] < next_observation.visibility_window[START_TIME]:
                    observation.state = SELECTED
                    LAST_SELECTED = i
                else:
                    if observation.satellite.priority < next_observation.satellite.priority:
                        observation.state = SELECTED
                        next_observation.state = OVERLAPS_PREVIOUS
                        LAST_SELECTED = i
                    else:
                        observation.state = EXCLUDED
                        next_observation.state = SELECTED
                        LAST_SELECTED = i+1
            elif observation.state == SELECTED:
                if observation.visibility_window[END_TIME] > next_observation.visibility_window[START_TIME]:
                    if observation.satellite.priority < next_observation.satellite.priority:
                        next_observation.state = OVERLAPS_PREVIOUS
                    else:
                        observation.state = EXCLUDED
                        next_observation.state = SELECTED
                        LAST_SELECTED = i+1
                        if i > 0 and previous_observation.state not in {OVERLAPS_PREVIOUS, SELECTED}:
                            if previous_observation.visibility_window[END_TIME] < next_observation.visibility_window[START_TIME]:
                                previous_observation.state = SELECTED
            elif observation.state == OVERLAPS_PREVIOUS:
                if self.observations[LAST_SELECTED].visibility_window[END_TIME] < next_observation.visibility_window[START_TIME]:
                    LAST_SELECTED = i+1
                    next_observation.state = SELECTED
                else:
                    if next_observation.satellite.priority < self.observations[LAST_SELECTED].satellite.priority:
                        next_observation.state = SELECTED
                        self.observations[LAST_SELECTED].state = EXCLUDED
                        LAST_SELECTED = i+1
                    else:
                        next_observation.state = OVERLAPS_PREVIOUS
        self.Planning_append()

    def print_observation_states(self):
        for obs in self.observations:
            print(obs.satellite.name, "etat : ", obs.state)

    def Planning_append(self):
        for observation in self.observations:
            if observation.state == SELECTED:
                self.planning.append(observation)

    def print_planning(self):
        for sat in self.planning:
            print(sat.satellite.name)

    def plot_planning(self):
        plt.figure(figsize=(60, 2))
        for sat in self.observations:
            start_time = sat.visibility_window[START_TIME]
            end_time = sat.visibility_window[END_TIME]
            priority = sat.satellite.priority
            if sat.state == 1:
                plt.plot([start_time.utc_datetime(), end_time.utc_datetime()],
                         [priority, priority],
                         marker='|', linestyle='-', color='r')
            else:
                plt.plot([start_time.utc_datetime(), end_time.utc_datetime()],
                         [priority, priority],
                         marker='|', linestyle='-', color='b')

        plt.xlabel('Temps')
        plt.ylabel('Priorité du Satellite')
        plt.title('Fenêtres de Visibilité des Satellites')
        plt.legend()
        plt.show()


if __name__ == '__main__':

    station_file = "toml/station.toml"
    satellites_file = "toml/satellites.toml"

    configuration_reader = ConfigurationReader(station_file, satellites_file)
    test = Test_planning(configuration_reader.satellites)
    test.compute_observation()
    test.print_observation()

planning = Plannifier(test.observations)
planning.Planning_Maker()
planning.print_observation_states()
planning.print_planning()
planning.plot_planning()
