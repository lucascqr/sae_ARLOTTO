#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul  6 15:48:23 2024

@author: philippe
"""

import json
import time
from datetime import datetime, timedelta
from skyfield.api import load, Topos, EarthSatellite

# ConfigurationReader class
class ConfigurationReader:
    def __init__(self, config_file):
        self.config_file = config_file
        self.satellites = []
        self.observer_location = None

    def read_config(self):
        with open(self.config_file, 'r') as file:
            data = json.load(file)
            self.observer_location = (
                data['observer_location']['latitude'],
                data['observer_location']['longitude']
            )
            for sat_data in data['satellites']:
                satellite = Satellite(
                    name=sat_data['name'],
                    priority=sat_data['priority'],
                    tle=sat_data['tle']
                )
                self.satellites.append(satellite)

# Satellite class
class Satellite:
    def __init__(self, name, priority, tle):
        self.name = name
        self.priority = priority
        self.tle = tle
        self.visibility_windows = []
    
    def add_visibility_window(self, start_time, end_time):
        self.visibility_windows.append((start_time, end_time))

# VisibilityCalculator class
class VisibilityCalculator:
    def __init__(self, satellites):
        self.satellites = satellites

    def calculate_visibility(self):
        for satellite in self.satellites:
            visibility_windows = self.get_visibility_windows(satellite)
            for window in visibility_windows:
                satellite.add_visibility_window(window[0], window[1])

    def get_visibility_windows(self, satellite):
        return [(datetime.now(), datetime.now() + timedelta(minutes=10))]

# SatelliteTracker class
class SatelliteTracker:
    def __init__(self, satellite, tle_data, observer_location, antenna_controller, receiver):
        self.satellite = satellite
        self.tle_data = tle_data
        self.observer_location = observer_location
        self.antenna_controller = antenna_controller
        self.receiver = receiver

    def track_and_record(self):
        for window in self.satellite.visibility_windows:
            start_time, end_time = window
            self.wait_until(start_time)
            self.receiver.start_recording()
            self.track_satellite_until(end_time)
            self.receiver.stop_recording()

    def wait_until(self, target_time):
        while datetime.now() < target_time:
            time.sleep(1)

    def track_satellite_until(self, end_time):
        while datetime.now() < end_time:
            position = self.calculate_position()
            self.antenna_controller.point_to(position)
            time.sleep(1)

    def calculate_position(self):
        ts = load.timescale()
        t = ts.now()
        satellite = EarthSatellite(self.tle_data[0], self.tle_data[1], self.satellite.name, ts)
        observer = Topos(latitude_degrees=self.observer_location[0], longitude_degrees=self.observer_location[1])
        difference = satellite - observer
        topocentric = difference.at(t)
        alt, az, distance = topocentric.altaz()
        return az.degrees, alt.degrees

# AntennaController class
class AntennaController:
    def point_to(self, position):
        azimuth, elevation = position
        print(f"Pointing antenna to azimuth: {azimuth}, elevation: {elevation}")

# Receiver class
class Receiver:
    def start_recording(self):
        print("Starting recording")

    def stop_recording(self):
        print("Stopping recording")

# Scheduler class
class Scheduler:
    def __init__(self, satellites, observer_location, antenna_controller, receiver):
        self.satellites = satellites
        self.observer_location = observer_location
        self.antenna_controller = antenna_controller
        self.receiver = receiver

    def schedule(self):
        sorted_satellites = sorted(self.satellites, key=lambda x: x.priority, reverse=True)
        for satellite in sorted_satellites:
            tracker = SatelliteTracker(satellite, satellite.tle, self.observer_location, self.antenna_controller, self.receiver)
            tracker.track_and_record()

# Main function
def main():
    config_reader = ConfigurationReader('config.json')
    config_reader.read_config()

    visibility_calculator = VisibilityCalculator(config_reader.satellites)
    visibility_calculator.calculate_visibility()

    observer_location = config_reader.observer_location
    antenna_controller = AntennaController()
    receiver = Receiver()
    scheduler = Scheduler(config_reader.satellites, observer_location, antenna_controller, receiver)
    
    scheduler.schedule()

if __name__ == "__main__":
    main()


from datetime import datetime, timedelta

class VisibilityCalculator:
    def __init__(self, satellites):
        self.satellites = satellites

    def calculate_visibility(self):
        for satellite in self.satellites:
            visibility_windows = self.get_visibility_windows(satellite)
            for window in visibility_windows:
                satellite.add_visibility_window(window[0], window[1])

        self.resolve_overlaps()

    def get_visibility_windows(self, satellite):
        # This should be replaced by actual visibility calculation logic
        now = datetime.now()
        return [(now + timedelta(minutes=15*i), now + timedelta(minutes=15*i + 10)) for i in range(5)]

    def resolve_overlaps(self):
        # Create a list of all visibility windows with priorities
        windows = []
        for satellite in self.satellites:
            for window in satellite.visibility_windows:
                windows.append((window[0], window[1], satellite.priority, satellite))

        # Sort by start time, and then by priority (higher first)
        windows.sort(key=lambda x: (x[0], -x[2]))

        # Resolve overlaps
        resolved_windows = []
        for i, (start, end, priority, satellite) in enumerate(windows):
            overlap = False
            for res_start, res_end, res_priority, res_satellite in resolved_windows:
                if start < res_end and end > res_start:  # There is an overlap
                    overlap = True
                    if priority > res_priority:
                        resolved_windows.remove((res_start, res_end, res_priority, res_satellite))
                        resolved_windows.append((start, end, priority, satellite))
                    break
            if not overlap:
                resolved_windows.append((start, end, priority, satellite))

        # Clear the visibility windows for all satellites
        for satellite in self.satellites:
            satellite.visibility_windows = []

        # Assign the resolved windows back to the satellites
        for start, end, priority, satellite in resolved_windows:
            satellite.add_visibility_window(start, end)

class Scheduler:
    def __init__(self, satellites, observer_location, antenna_controller, receiver):
        self.satellites = satellites
        self.observer_location = observer_location
        self.antenna_controller = antenna_controller
        self.receiver = receiver

    def schedule(self):
        sorted_satellites = sorted(self.satellites, key=lambda x: x.priority, reverse=True)
        for satellite in sorted_satellites:
            tracker = SatelliteTracker(satellite, satellite.tle, self.observer_location, self.antenna_controller, self.receiver)
            tracker.track_and_record()
