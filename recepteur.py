import json
import csv
import os
from datetime import datetime
import paho.mqtt.client as mqtt

FICHIER = "mesures.csv"
COLONNES = ["date_heure", "temperature", "humidite", "air", "etat", "cause"]


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connecté au broker")
    client.subscribe("balise/mesures")


def on_message(client, userdata, msg):
    # 1. Lire le message JSON
    try:
        mesure = json.loads(msg.payload.decode())
    except ValueError:
        print("Message ignoré (pas du JSON) :", msg.payload)
        return

    # 2. Ajouter la date et l'heure du PC
    mesure["date_heure"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Ajouter une ligne dans le fichier CSV
    nouveau = not os.path.exists(FICHIER)
    with open(FICHIER, "a", newline="", encoding="utf-8") as f:
        ecrivain = csv.DictWriter(f, fieldnames=COLONNES)
        if nouveau:
            ecrivain.writeheader()
        ecrivain.writerow(mesure)
    print("Enregistré :", mesure)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883)
print("En attente des mesures... (Ctrl+C pour arrêter)")
client.loop_forever()