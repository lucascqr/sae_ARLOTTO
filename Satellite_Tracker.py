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
import subprocess


class Tracker():
    def __init__(self, station, rotator):
        self.station = station
        self.rotator = rotator
        self.tle = None
        self.socket = None
        self.process = None

        self.start_az = None
        self.start_alt = None
        self.stop_az = None
        self.last_az = None
        self.last_alt = None

        self.start_time = None
        self.stop_time = None
        self.normalize = None

        self.simulation = False

    def launch_rotctld(self):
        if self.simulation:
            command = ["wsl", "rotctld", "-t", str(self.rotator.port)]
        else:
            command = ["wsl", "rotctld", "-m", "603", "-r",
                       str(self.rotator.ip), '-t', str(self.rotator.port), "-vvv"]
            # command = ["wsl", "rotctld", "-m", "603", "-r",
            #            "172.20.10.3:9999", '-t', "4545", "-vvv"]

        print(str(self.rotator.ip))

        self.process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        time.sleep(5)
        self.connect_rotcltd()

    def reload_rotctld(self):
        self.process.kill()
        self.launch_rotctld()

    def connect_rotcltd(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.rotator.ip_rotctld, self.rotator.port))

        if self.simulation:
            command = 'C max_el 180\n'
            self.socket.sendall(command.encode())
            command = 'C min_az 0\n'
            self.socket.sendall(command.encode())
            response = self.socket.recv(1024).decode()
            print(f'Simulation mode : {response}')

    def clear_socket_buffer(self):
        self.socket.setblocking(0)  # Passer le socket en mode non-bloquant
        try:
            while True:
                data = self.socket.recv(1024)
                if not data:
                    break
        except BlockingIOError:
            pass  # Rien à lire
        finally:
            self.socket.setblocking(1)  # Revenir au mode bloquant

    def track_satellite(self):
        az, alt = self.normalize_trajectory(self.start_az, self.start_alt)
        self.send_motor_position(int(az), int(alt))

        if self.simulation:
            self.last_az = az
            self.last_alt = alt

        print(self.start_time.utc_strftime(format='%Y-%m-%d %H:%M:%S UTC'))
        print(self.stop_time.utc_strftime(format='%Y-%m-%d %H:%M:%S UTC'))

        time.sleep(20)

        while (1):
            ts = load.timescale()
            t = ts.now()

            if t < self.stop_time:
                alt, az, distance = self.calcul_position(t)
                az, alt = self.normalize_trajectory(
                    az, alt)

                if t < self.start_time:
                    time.sleep(20)
                else:
                    az_motor, alt_motor = self.get_motor_position()
                    if (abs(az-az_motor) > 5 or abs(alt-alt_motor) > 5):
                        self.send_motor_position(int(az), int(alt))
                        self.last_az = az
                        self.last_alt = alt
                        time.sleep(10)
                    else:
                        time.sleep(10)
            else:
                print("fin du suivi du satellite")
                return

    def normalize_trajectory(self, azimuth, elevation):

        az_normalized = azimuth.degrees
        elevation_normalized = elevation.degrees
        if self.normalize == 180:
            if azimuth.degrees > 180:
                az_normalized -= 180
            else:
                az_normalized += 180
            elevation_normalized = 180 - elevation.degrees
        elif self.normalize == 450:
            if azimuth.degrees < 90:
                az_normalized += 360

        return az_normalized, elevation_normalized

    def send_motor_position(self, azimuth, elevation):
        command = f'P {azimuth} {elevation}\n'
        print("command : ", command)

        if self.simulation:
            self.clear_socket_buffer()

        self.socket.sendall(command.encode())
        response = self.socket.recv(1024).decode()
        print(f'Received Command: {response}')

    def get_motor_position(self):
        command = 'p\n'

        if self.simulation:
            self.clear_socket_buffer()

        self.socket.sendall(command.encode())
        response = self.socket.recv(1024).decode()
        index = response.find('\n')
        len_rep = len(response)
        try:
            print(f'Received: {response}')
            azimuth = float(response[0:index])
            elevation = float(response[index+1:len_rep-1])
            return azimuth, elevation
        except ValueError:
            if response.strip() == 'RPRT -6':
                self.reload_rotctld()
            print(f'Réponse invalide : {response}')
            return self.last_az, self.last_alt

    def calcul_position(self, t):
        bluffton = wgs84.latlon(
            self.station.latitude, self.station.longitude)
        topocentric_position = (self.tle - bluffton).at(t)
        alt, az, distance = topocentric_position.altaz()
        return alt, az, distance

    def calcul_trajectory(self, observation):
        self.tle = observation.satellite.tle[0]

        trajectory = []
        times = []

        current_time = observation.visibility_window[0]
        self.start_time = observation.visibility_window[0]
        self.stop_time = observation.visibility_window[1]

        self.start_alt, self.start_az, distance = self.calcul_position(
            current_time)
        alt, self.stop_az, distance = self.calcul_position(stop_time)

        while current_time < self.stop_time:

            alt, az, distance = self.calcul_position(current_time)

            if alt.degrees > 5:
                trajectory.append(az.degrees)
                times.append(current_time.utc_strftime('%Y-%m-%d %H:%M:%S'))

            current_time = ts.utc(current_time.utc.year, current_time.utc.month, current_time.utc.day,
                                  current_time.utc.hour, current_time.utc.minute + 1)

        # print(observation.satellite.name, trajectory)
        self.plot_azimuth(trajectory, times, observation.satellite.name)
        self.normalize = self.select_trajectory_normalization(trajectory)
        print("Normalisation : ", self.normalize,
              "satellite :", observation.satellite.name)
        self.track_satellite()

    def select_trajectory_normalization(self, trajectory):
        # trajectory[0] --> self.start_az.degrees
        # trajectory[-1] --> self.stop_az.degrees

        for i, azimuths in enumerate(trajectory[:-1]):
            next_azimuths = trajectory[i + 1]
            if abs(next_azimuths - azimuths) > 180:
                print(next_azimuths, azimuths, "\n")
                print(self.start_az.degrees, self.stop_az.degrees, "\n")
                if trajectory[0] < 90 or trajectory[-1] < 90:
                    return 450
                else:
                    return 180
            else:
                normalize = 0

        return normalize

    def plot_azimuth(self, azimuths, times, name):
        plt.figure(figsize=(10, 6))
        plt.plot(times, azimuths, marker='x', color='b')
        plt.title(
            f"Évolution des azimutes en fonctions du temps du satellite :{name}")
        plt.xlabel("Temps(UTC)")
        plt.ylabel("Azimut (deg)")
        for x, y in zip(times, azimuths):
            plt.text(x, y + 10, f"{y:.1f}", ha='center',
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
    tracker.launch_rotctld()
    for obs in planning.planning:
        # tracker.track_satellite(obs)
        tracker.calcul_trajectory(obs)
