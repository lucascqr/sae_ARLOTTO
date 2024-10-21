# -*- coding: utf-8 -*-
"""
Created on Sun Oct 13 18:34:12 2024

@author: anoel
"""
from ConfigurationReader import ConfigurationReader
from skyfield.api import load, wgs84
from TLE_Loader import Tle_Loader, VisibilyWindowComputer
import matplotlib.pyplot as plt
import os
from datetime import datetime

IDLE = 0
SELECTED = 1
EXCLUDED = 2
OVERLAPS_PREVIOUS = 3
ADDABLE = 4
SUPPRESSED = 5

START_TIME = 0
END_TIME = 1


class Plannifier ():
    def __init__(self, observations, satellites):
        self.observations = observations
        self.satellites = satellites
        self.planning = []

    def Planning_Maker(self):
        for observation in self.observations:
            observation.state = IDLE

        lastSelected = None
        modifications = 0
        nbr_passage = 0
        # addable_list = []
        while True:
            modifications = 0
            for i, observation in enumerate(self.observations[:-1]):
                if observation.state in ({IDLE} if nbr_passage else {IDLE, SELECTED, EXCLUDED, OVERLAPS_PREVIOUS}):
                    if nbr_passage == 0:
                        j = i+1
                        next_observation = self.observations[j]
                        previous_observation = self.observations[i-1]
                    else:
                        for j in range(i+1, len(self.observations)-1):
                            if self.observations[j].state == IDLE:
                                print("i = " + str(i) + " j = " + str(j))
                                next_observation = self.observations[j]
                                break

                    if observation.state in ({IDLE} if nbr_passage else {SELECTED, IDLE}):
                        if observation.visibility_window[END_TIME] < next_observation.visibility_window[START_TIME]:
                            if observation.state != SELECTED:
                                modifications += 1
                                observation.state = SELECTED
                            lastSelected = i
                        else:
                            if observation.satellite.priority < next_observation.satellite.priority:
                                if observation.state != SELECTED:
                                    modifications += 1
                                    observation.state = SELECTED
                                next_observation.state = OVERLAPS_PREVIOUS
                                lastSelected = i
                            else:
                                observation.state = EXCLUDED
                                if next_observation.state != SELECTED:
                                    modifications += 1
                                    next_observation.state = SELECTED
                                lastSelected = j
                                if i > 0 and previous_observation.state not in {OVERLAPS_PREVIOUS, SELECTED}:
                                    if previous_observation.visibility_window[END_TIME] < next_observation.visibility_window[START_TIME]:
                                        if previous_observation.state != SELECTED:
                                            modifications += 1
                                            previous_observation.state = SELECTED
                    elif observation.state == OVERLAPS_PREVIOUS:
                        if self.observations[lastSelected].visibility_window[END_TIME] < next_observation.visibility_window[START_TIME]:
                            lastSelected = j
                            if next_observation.state != SELECTED:
                                modifications += 1
                                next_observation.state = SELECTED
                        else:
                            if next_observation.satellite.priority < self.observations[lastSelected].satellite.priority:
                                if next_observation.state != SELECTED:
                                    modifications += 1
                                    next_observation.state = SELECTED
                                self.observations[lastSelected].state = EXCLUDED
                                lastSelected = j
                            else:
                                next_observation.state = OVERLAPS_PREVIOUS
                    previous_observation = self.observations[i]

            nbr_passage = 1
            if modifications == 0:
                break

            addable_window = 0
            for i, observation in enumerate(self.observations[:-1]):
                if observation.state == SELECTED:
                    minimun_start_time = observation.visibility_window[END_TIME]
                    for j, observation in enumerate(self.observations[:-1], i+1):
                        if j >= len(self.observations)-1:
                            break
                        elif j < len(self.observations)-1:
                            element_associe = self.observations[j]
                            if element_associe.state == SELECTED:
                                maximun_end_time = element_associe.visibility_window[START_TIME]
                                break
                    if i+1 < j:
                        for k in range(i+1, j):
                            tested_observation = self.observations[k]
                            if (tested_observation.visibility_window[START_TIME] > minimun_start_time and tested_observation.visibility_window[END_TIME] < maximun_end_time):
                                tested_observation.state = IDLE
                                addable_window += 1

            for i, observation in enumerate(self.observations[:]):
                if observation.state not in {SELECTED, IDLE}:
                    observation.state = SUPPRESSED

            if addable_window == 0:
                break

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
        ymax = len(self.satellites)
        plt.figure(figsize=(150, 6))
        plt.plot([], [], color='r', marker='|', linestyle='-',
                 label='Fenêtres sélectionnées')
        plt.plot([], [], color='b', marker='|',
                 linestyle='-', label='Fenêtres exclues')
        plt.legend()
        count = 0
        for sat in self.observations:
            start_time = sat.visibility_window[START_TIME]
            end_time = sat.visibility_window[END_TIME]
            priority = sat.satellite.priority
            if sat.state == SELECTED:
                plt.plot([start_time.utc_datetime(), end_time.utc_datetime()],
                         [priority, priority],
                         marker='|', linestyle='-', color='r')
                # # Calcul du milieu entre start_time et end_time pour centrer le texte
                # mid_time = start_time.utc_datetime() + (end_time.utc_datetime() -
                #                                         start_time.utc_datetime()) / 2

                # # Ajout du texte centré au-dessus de la ligne
                # plt.text(x=mid_time,
                #           y=priority + 0.2,  # Ajustez l'offset pour positionner le texte au-dessus
                #           s=sat.satellite.name,
                #           ha='center',  # Centre le texte horizontalement
                #           fontsize=8,
                #           color='black')
                plt.vlines(start_time.utc_datetime(), 0, ymax, 'k', 'dashed')
                plt.vlines(end_time.utc_datetime(), 0, ymax, 'k', 'dashed')
            elif sat.state == ADDABLE:
                plt.plot([start_time.utc_datetime(), end_time.utc_datetime()],
                         [priority, priority],
                         marker='|', linestyle='-', color='g')
            else:
                plt.plot([start_time.utc_datetime(), end_time.utc_datetime()],
                         [priority, priority],
                         marker='|', linestyle='-', color='b')
            # Calcul du milieu entre start_time et end_time pour centrer le texte
            mid_time = start_time.utc_datetime() + (end_time.utc_datetime() -
                                                    start_time.utc_datetime()) / 2

            # Ajout du texte centré au-dessus de la ligne
            plt.text(x=mid_time,
                     y=priority + 0.2,  # Ajustez l'offset pour positionner le texte au-dessus
                     s=count,
                     ha='center',  # Centre le texte horizontalement
                     fontsize=8,
                     color='black')
            count += 1

        plt.xlabel('Temps')
        plt.ylabel('Priorité du Satellite')
        plt.title('Fenêtres de Visibilité des Satellites')

        # Obtenir l'heure et la date actuelles
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Obtenir le répertoire courant
        current_directory = os.getcwd()
        # Définir un sous-dossier dans le répertoire courant
        directory = os.path.join(current_directory, "planning")
        filename = f"planning_{current_time}.png"
        # Vérifier si le sous-dossier existe, sinon le créer
        if not os.path.exists(directory):
            os.makedirs(directory)
        # Combiner le sous-dossier et le nom du fichier
        full_path = os.path.join(directory, filename)
        # Sauvegarde du graphique dans le sous-dossier
        plt.savefig(full_path)

        # Affichage
        plt.show()


if __name__ == '__main__':
    station_file = 'toml/station.toml'
    satellites_file = 'toml/satellites.toml'

    config = ConfigurationReader(station_file, satellites_file)
    # config.set_priority()
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
    planning = Plannifier(computer.observations, config.satellites)
    planning.Planning_Maker()
    # planning.print_observation_states()
    # planning.print_planning()
    planning.plot_planning()
