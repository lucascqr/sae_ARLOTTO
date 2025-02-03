import os
import subprocess
import logging

# Configuration
WAV_FOLDER = "wav_files"  # Dossier contenant les fichiers .wav
DEMODULATED_FOLDER = "demodulated_files"  # Dossier pour les résultats de démodulation
SATDUMP_COMMAND = "satdump"  # Commande pour satdump (assurez-vous qu'il est dans votre PATH)

# Assurez-vous que le dossier de démodulation existe
if not os.path.exists(DEMODULATED_FOLDER):
    os.makedirs(DEMODULATED_FOLDER)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_wav_file(file_path):
    """
    Démodule un fichier .wav avec satdump.
    """
    try:
        # Extraire le nom du fichier sans extension
        filename = os.path.basename(file_path)
        output_folder_name = os.path.splitext(filename)[0]
        output_folder = os.path.join(DEMODULATED_FOLDER, output_folder_name)

        # Créer le dossier de sortie
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        logger.info(f"Dossier de sortie créé : {output_folder}")

        # Extraire les métadonnées du nom du fichier
        metadata = filename.split("_")
        if len(metadata) != 3:
            logger.error(f"Format de nom de fichier invalide : {filename}. Attendu : <satellite>_<timestamp>_<fréquence>MHz.wav")
            return

        satellite_name = metadata[0]
        frequency = metadata[2].replace("MHz.wav", "")  # Supprimer "MHz" de la fréquence

        frequency_hz = float(frequency) * 1e6  # Convertir MHz en Hz

        # Exécuter satdump pour démoduler le fichier
        command = [
            SATDUMP_COMMAND,
            "process",
            satellite_name,
            str(frequency_hz),
            file_path,
            "--output",
            output_folder
        ]
        
        print(command)
        
        # while 1 :
        #     pass
        
        logger.info(f"Exécution de la commande : {' '.join(command)}")
        subprocess.run(command, check=True)
        logger.info(f"Démodulation terminée. Résultats sauvegardés dans : {output_folder}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de la démodulation : {e}")
    except Exception as e:
        logger.error(f"Une erreur s'est produite : {e}")

def demodulate_all_files():
    """
    Parcourt tous les fichiers .wav dans le dossier wav_files et les démodule.
    """
    # Vérifier si le dossier wav_files existe
    if not os.path.exists(WAV_FOLDER):
        logger.error(f"Le dossier {WAV_FOLDER} n'existe pas.")
        return

    # Parcourir tous les fichiers .wav dans le dossier
    for filename in os.listdir(WAV_FOLDER):
        if filename.endswith(".wav"):
            file_path = os.path.join(WAV_FOLDER, filename)
            logger.info(f"Traitement du fichier : {file_path}")
            process_wav_file(file_path)

if __name__ == "__main__":
    demodulate_all_files()