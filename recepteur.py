import json
import os
from datetime import datetime
import paho.mqtt.client as mqtt
import psycopg
from dotenv import load_dotenv

# --- Connexion à PostgreSQL ---
load_dotenv()        
base = psycopg.connect(
    host="127.0.0.1",     
    port=5432,
    dbname="balise",
    user="balise",
    password=os.environ["POSTGRES_PASSWORD"],
    autocommit=True,        # chaque INSERT est enregistré tout de suite
)
print("Connecté à PostgreSQL")


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

    # 2. Prendre la date et l'heure du PC, avec son fuseau horaire (colonne TIMESTAMPTZ)
    maintenant = datetime.now().astimezone()

    # 3. Ajouter une ligne dans la table PostgreSQL
    base.execute(
        "INSERT INTO mesures (date_heure, temperature, humidite, air, etat, cause) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (maintenant, mesure.get("temperature"), mesure.get("humidite"),
         mesure.get("air"), mesure.get("etat"), mesure.get("cause")),
    )
    print("Enregistré dans PostgreSQL :", mesure)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883)
print("En attente des mesures... (Ctrl+C pour arrêter)")
client.loop_forever()