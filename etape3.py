import network
import time
from umqtt.simple import MQTTClient

from config import NOM_WIFI, MOT_DE_PASSE, BROKER

# 1. Wi-Fi
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(NOM_WIFI, MOT_DE_PASSE)
while not wifi.isconnected():
    time.sleep(1)
print("Wi-Fi OK :", wifi.ifconfig()[0])

# 2. Connexion au broker
client = MQTTClient("balise", BROKER)
client.connect()
print("Connecté au broker")

# 3. Envoyer 5 messages de test
for i in range(5):
    message = "test " + str(i)
    client.publish(b"balise/mesures", message.encode())
    print("Envoyé :", message)
    time.sleep(2)

client.disconnect()