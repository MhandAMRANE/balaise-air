from machine import Pin, ADC
from neopixel import NeoPixel
import dht
import time

capteur = dht.DHT11(Pin(3))
air = ADC(Pin(2))
air.atten(ADC.ATTN_11DB)
led = NeoPixel(Pin(8), 1)


def etat_air(v):
    if v < 500:
        return "Good"
    elif v < 1000:
        return "Moderate"
    else:
        return "Poor"


def etat_temperature(t):
    if 19 <= t <= 26:
        return "Good"
    elif 17 <= t <= 28:
        return "Moderate"
    else:
        return "Poor"


def etat_humidite(h):
    if 30 <= h <= 60:
        return "Good"
    elif 20 <= h <= 70:
        return "Moderate"
    else:
        return "Poor"


while True:
    # 1. Mesurer
    valeur_air = air.read()
    try:
        capteur.measure()
        t = capteur.temperature()
        h = capteur.humidity()
    except OSError:
        print("ERREUR : le capteur de température ne répond pas. Vérifiez les fils.")
        led[0] = (0, 0, 0)
        led.write()
        break

    # 2. Noter chaque mesure
    e_air = etat_air(valeur_air)
    e_temp = etat_temperature(t)
    e_hum = etat_humidite(h)

    # 3. État de la balise = la plus mauvaise note
    notes = [e_air, e_temp, e_hum]
    if "Poor" in notes:
        etat = "Poor"
        led[0] = (20, 0, 0)
    elif "Moderate" in notes:
        etat = "Moderate"
        led[0] = (20, 15, 0)
    else:
        etat = "Good"
        led[0] = (0, 20, 0)
    led.write()

    # 4. La cause : quelles mesures ne sont pas Good ?
    causes = []
    if e_air != "Good":
        causes.append("air")
    if e_temp != "Good":
        causes.append("température")
    if e_hum != "Good":
        causes.append("humidité")

    if len(causes) == 0:
        texte_cause = "aucune"
    else:
        texte_cause = ", ".join(causes)

    # 5. Afficher
    print("Air :", valeur_air, e_air, "| T :", t, "°C", e_temp,
          "| H :", h, "%", e_hum, "| BALISE :", etat, "| Cause :", texte_cause)
    time.sleep(5)