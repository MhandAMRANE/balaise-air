import network
import time

from config import NOM_WIFI, MOT_DE_PASSE

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(NOM_WIFI, MOT_DE_PASSE)

for i in range(20):
    if wifi.isconnected():
        break
    print("Connexion en cours...")
    time.sleep(1)

if wifi.isconnected():
    print("Connecté ! Adresse IP de la carte :", wifi.ifconfig()[0])
else:
    print("Échec : vérifiez le nom, le mot de passe et le 2,4 GHz")