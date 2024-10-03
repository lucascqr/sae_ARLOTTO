# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 14:45:36 2024

@author: lucas
"""
from ConfigurationReader import ConfigurationReader, Station, Satellite
from skyfield.api import load, wgs84
from TLE_Loader import Tle_Loader, VisibilyWindowComputer
import logging
idle = 0
selected = 1
excluded = 2
overlaps_previous = 3

start_time = 0
end_time = 1


class Plannifier():
    def __init__(self, observations):
        self.observations = observations

    def planning_maker(self):
        self.observations.state = idle
        lastSelected = 0
        i = 0
        while i < len(self.observations):

            if self.observations[i].state == idle or self.observations[i].state == selected:
                if self.observations[i].visibilityWindow[end_time] < self.observations[i+1].visibilityWindow[start_time]:
                    self.observations[i].state = selected
                    lastSelected = i
                else:
                    if self.observations[i].satellite.priority > self.observations[i+1].satellite.priority:
                        self.observations[i].state = selected
                        self.observations[i+1].state = overlaps_previous
                        lastSelected = i
                    else:
                        self.observations[i].state = excluded
                        self.observations[i+1].state = selected
                        lastSelected = i+1
                        if (i > 0) and not (self.observations[i].state == overlaps_previous) and not (self.observations[i].state == selected):
                            if self.observations[i-1].visibilityWindow[end_time] < self.observations[i+1].visibilityWindow[start_time]:
                                self.observations[i-1].state = selected

            elif self.observations[i].state == overlaps_previous:
                if self.observations[lastSelected].visibilityWindow[end_time] < self.observations[i+1].visibilityWindow[start_time]:
                    lastSelected = i+1
                    self.observations[i+1].state = selected
                else:
                    if self.observations[i+1].satellite.priority > self.observations[lastSelected].satellite.priority:
                        self.observations[i+1].state = selected
                        self.observations[lastSelected].state = excluded
                        lastSelected = i+1
                    else:
                        self.observations[i+1].state = overlaps_previous

            i = i+1

        for obs in self.observations:
            print(obs.state)


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
    # computer.print_observation()
    planning = Plannifier(computer.observations)
    planning.planning_maker()
