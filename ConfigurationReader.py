# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 17:19:39 2024

@author: anoel
"""
import toml


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

# Affichage création des classes

    def print_station_configuration(self):
        print('Ground Station Configuration read from', self.station_file)
        self.station.print()
        self.rotator.print()
        self.receiver.print()
        self.directories.print()
        self.tle.print()

    def print_satellites(self):
        print('Recorded Satellites read from', self.satellites_file)
        for sat in self.satellites:
            print(sat.__dict__)

    def set_priority(self):
        i = 0
        for sat in self.satellites:
            sat.priority = i
            # print(sat.name, sat.priority)
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


# DEBUG

if __name__ == "__main__":
    station_file = "toml/station.toml"
    satellites_file = "toml/satellites.toml"

    configuration_reader = ConfigurationReader(station_file, satellites_file)
    configuration_reader.print_station_configuration()
    # configuration_reader.set_priority()
    configuration_reader.print_satellites()
