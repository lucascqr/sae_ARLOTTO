import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants
import numpy as np #use numpy for buffers
import wave
args = f"driver=plutosdr,addr={'192.168.0.1'}"
sdr = SoapySDR.Device(args)

sdr.setSampleRate(SOAPY_SDR_RX, 0, 0.5e6 )
sdr.setFrequency(SOAPY_SDR_RX, 0, 107.1*1e6)
rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32,[0]) # todo set from satellite.record_format
optimal_block_size=sdr.getStreamMTU(rxStream)
sdr.activateStream(rxStream) #start streaming


with wave.open(fileName, 'wb') as wav_file:
		wav_file.setnchannels(2)
		wav_file.setsampwidth(2)  # 16 bits = 2 octets
		wav_file.setframerate( int(sample_frequency) )
		block_size = optimal_block_size  # Taille du bloc d'échantillons

		while 1:
			buffer = np.empty(block_size, np.complex64)
			sr = sdr.readStream(rxStream, [buffer], block_size)
			if sr.ret != block_size:
				print("Erreur lors de la lecture des échantillons: ", sr.ret)
                # Séparer les échantillons en composants réels et imaginaires
				iq_data = np.column_stack((buffer.real, buffer.imag))
                 
                 # Convertir les données en 16 bits pour l'enregistrement WAV
				iq_data_int16 = (iq_data * 32767).astype(np.int16)
                 
                 # Écrire les données dans le fichier WAV
				wav_file.writeframes(iq_data_int16.tobytes())
sdr.deactivateStream(rxStream) #stop streaming
sdr.closeStream(rxStream) 
