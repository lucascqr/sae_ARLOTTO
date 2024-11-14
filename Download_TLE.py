# -*- coding: utf-8 -*-
"""
Created on Sun Sep 22 16:59:18 2024

@author: anoel
"""

from ConfigurationReader import ConfigurationReader
from skyfield.api import load
import urllib.parse


class Tle_Downloader ():
    def __init__(self, satellites, tle_dir, max_days):
        self.satellites = satellites
        self.tle_dir = tle_dir
        self.max_days = max_days

    def DownloadTle(self):
        for sat in self.satellites:
            name = sat.name + '.tle'
            if not load.exists(self.tle_dir+"/"+name) or load.days_old(self.tle_dir+"/"+name) >= self.max_days:
                if hasattr(sat, 'norad'):
                    download_adress = config.tle.tle_download_adress + '?CATNR=' + \
                        urllib.parse.quote(str(sat.norad)) + '&FORMAT=TLE'
                else:
                    download_adress = config.tle.tle_download_adress + '?NAME=' + \
                        urllib.parse.quote(str(sat.name)) + '&FORMAT=TLE'

                load.download(download_adress,
                              filename=self.tle_dir + "/" + name)


if __name__ == "__main__":

    station_file = 'toml/station.toml'
    satellites_file = 'toml/satellites.toml'

    config = ConfigurationReader(station_file, satellites_file)
    downloader = Tle_Downloader(
        config.satellites, config.directories.tle_dir, config.tle.max_days)
    downloader.DownloadTle()
