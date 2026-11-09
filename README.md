# Balise de qualité de l'air intérieur

Projet IoT — Master Data Engineering.

La balise mesure la **température**, l'**humidité** et un **indicateur de qualité de l'air**.
Elle affiche l'état de la pièce sur sa LED (🟢 Good / 🟡 Moderate / 🔴 Poor) et envoie ses
mesures en **MQTT** vers un PC, qui les **enregistre** et les affiche sur un **dashboard**.

```
Capteurs → ESP32-C6 → Wi-Fi / MQTT → Mosquitto (PC) → recepteur.py → mesures.csv → dashboard.py
```

**Niveau minimum atteint** : capteurs + ESP32 + LED + Wi-Fi + MQTT + dashboard.
**Déjà fait du niveau normal** : stockage des données et historique (`mesures.csv` + courbes).

---

## 1. Les fichiers

### Sur la carte (Thonny + MicroPython)

| Fichier | Rôle |
|---|---|
| `etape1.py` | Apprentissage : mesures + LED, sans réseau |
| `etape2.py` | Apprentissage : test de connexion Wi-Fi |
| `etape3.py` | Apprentissage : envoi de 5 messages MQTT de test |
| **`balise.py`** | **Programme final** : mesure, décide l'état, allume la LED, envoie au PC |

### Sur le PC (VS Code + Python)

| Fichier | Rôle |
|---|---|
| `mosquitto.conf` | Réglages du broker MQTT Mosquitto |
| **`recepteur.py`** | Reçoit les messages MQTT et les enregistre dans `mesures.csv` |
| **`dashboard.py`** | Affiche l'état, les valeurs, les courbes et les dernières mesures |
| `mesures.csv` | L'historique — **créé automatiquement** par `recepteur.py` |

---

## 2. Le matériel

- Carte **ESP32-C6-DevKitM-1** (LED RGB intégrée sur la broche 8)
- Capteur **Grove Temperature & Humidity v1.0** (DHT11)
- Capteur **Grove Air Quality Sensor v1.3** (indicateur de pollution : COV, fumée, alcool…)
- Breadboard, fils, câble **USB-C de données** (un câble « charge seule » ne marche pas)

### Câblage

Les deux capteurs ont le même connecteur Grove. Le 3V3 et le GND de la carte sont partagés
grâce aux colonnes des bords de la breadboard (une colonne pour le 3V3, une pour le GND).

| Fil Grove | Capteur température (DHT11) | Capteur d'air |
|---|---|---|
| Noir (GND) | GND | GND |
| Rouge (VCC) | 3V3 | 3V3 |
| Jaune (SIG) | **broche 3** | **broche 2** |
| Blanc (NC) | rien | rien |

⚠️ Ne jamais mettre le 3V3 et le GND dans la même colonne ou la même rangée : court-circuit.
⚠️ Toujours débrancher l'USB avant de modifier le câblage.

---

## 3. Comment la balise décide

Chaque mesure reçoit une note, puis la balise prend **la plus mauvaise des trois**.

| Mesure | Good | Moderate | Poor |
|---|---|---|---|
| Air (valeur brute 0–4095) | moins de 500 | 500 à 1000 | 1000 ou plus |
| Température | 19 à 26 °C | 17–19 ou 26–28 °C | moins de 17 ou plus de 28 °C |
| Humidité | 30 à 60 % | 20–30 ou 60–70 % | moins de 20 ou plus de 70 % |

- **État de la balise** : s'il y a au moins un Poor → Poor ; sinon s'il y a au moins un Moderate → Moderate ; sinon → Good.
- **Cause** : la liste des mesures qui ne sont pas Good (ou « aucune »).
- **Seuils de l'air** : choisis à partir de nos mesures. Air normal ≈ 200 à 330, avec du parfum > 2000.
  Le capteur d'air n'est **pas** un capteur de CO₂ : c'est un **indicateur** de pollution, sans unité.
- Si le capteur de température ne répond pas, la balise affiche une erreur, éteint la LED et s'arrête.

Le dashboard **ne recalcule pas** l'état : il affiche celui envoyé par la balise.
La LED et le dashboard affichent donc toujours la même chose.

### Message envoyé par la balise (topic `balise/mesures`, toutes les 5 s)

```json
{"temperature": 23, "humidite": 37, "air": 272, "etat": "Good", "cause": "aucune"}
```

La date et l'heure sont ajoutées par le PC (`recepteur.py`), car la carte ne connaît pas l'heure.

---

## 4. Installation (une seule fois)

### Carte

1. Installer **Thonny**. *Outils → Options → Interpréteur* : **MicroPython (ESP32)** + port COM de la carte.
2. *Installer ou mettre à jour MicroPython (esptool)* : famille **ESP32-C6**, variante **Espressif • ESP32-C6**.
3. Vérifier la bibliothèque MQTT dans la console de Thonny : `from umqtt.simple import MQTTClient`.

### PC

1. Installer **Mosquitto** (mosquitto.org → Download → Windows 64 bits).
2. Installer les bibliothèques Python :
   ```powershell
   pip install paho-mqtt streamlit pandas
   ```
3. Autoriser le port MQTT dans le pare-feu (PowerShell **administrateur**) :
   ```powershell
   New-NetFirewallRule -DisplayName "Mosquitto MQTT" -Direction Inbound -Protocol TCP -LocalPort 1883 -Action Allow
   ```

### `mosquitto.conf`

```
listener 1883
allow_anonymous true
```

- `listener 1883` : écouter sur le port 1883, sur toutes les connexions du PC (y compris le Wi-Fi).
- `allow_anonymous true` : accepter les connexions sans identifiant.
  Pratique pour le projet, mais pas sécurisé (amélioration possible : mots de passe + TLS).

### Réseau

- Utiliser le **partage de connexion du téléphone** en **2,4 GHz**
  (iPhone : activer « Maximiser la compatibilité »). L'ESP32 ne voit pas le 5 GHz.
- Le **PC et la carte doivent être sur le même réseau**.
- Dans `balise.py`, remplir `NOM_WIFI`, `MOT_DE_PASSE` et `BROKER` (adresse IP du PC).

---

## 5. Trouver l'adresse du broker (IP du PC)

```powershell
ipconfig
```

Prendre l'**Adresse IPv4** de la section **« Carte réseau sans fil Wi-Fi »**.
Avec un partage iPhone, elle commence par `172.20.10.` et la passerelle est `172.20.10.1`.

Ignorer les cartes virtuelles : vEthernet (Default Switch), VMware, **vEthernet (WSL)** (piège : `172.20.16.1`).

Commande plus rapide :
```powershell
Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi" | Select-Object IPAddress
```

---

## 6. Lancer le projet (à chaque séance, dans cet ordre)

| # | Où | Commande | Ce qu'on doit voir |
|---|---|---|---|
| 1 | Téléphone + PC | Partage activé, PC connecté dessus | — |
| 2 | Terminal | `ipconfig` → corriger `BROKER` dans `balise.py` si l'IP a changé | IPv4 en `172.20.10.x` |
| 3 | Terminal 1 | `& "C:\Program Files\mosquitto\mosquitto.exe" -c mosquitto.conf -v` | `Opening ipv4 listen socket on port 1883` |
| 4 | Terminal 2 | `python recepteur.py` | `Connecté au broker` |
| 5 | Terminal 3 | `streamlit run dashboard.py` | page sur http://localhost:8501 |
| 6 | Thonny | **Stop**, puis ▶ sur `balise.py` | `Wi-Fi OK`, `Connecté au broker`, puis les mesures |

**Pourquoi la balise en dernier ?**
- Sans broker, `client.connect()` échoue et le programme s'arrête.
- Sans récepteur abonné, les messages sont perdus (Mosquitto ne les garde pas).

Attendre **2 à 3 minutes** que le capteur d'air chauffe avant de faire une démonstration.

**Pour arrêter** : Stop dans Thonny, puis `Ctrl + C` dans chaque terminal.
L'historique reste dans `mesures.csv` ; les nouvelles mesures s'ajoutent à la suite.

**Balise autonome (sans PC)** : dans Thonny, *Fichier → Enregistrer sous → Appareil MicroPython*
→ `main.py`. Elle démarre seule dès qu'elle est alimentée. Ensuite, toujours cliquer sur **Stop**
avant de lancer un autre programme.

---

## 7. Problèmes fréquents

| Symptôme | Cause probable / solution |
|---|---|
| Aucun port COM dans Thonny | Câble USB « charge seule » → prendre un câble de données |
| `ETIMEDOUT` / « le capteur de température ne répond pas » | Fil mal enfoncé (souvent le GND) → appuyer sur les fils, relancer |
| La carte s'éteint (LED rouge éteinte) | Court-circuit 3V3 / GND → débrancher et vérifier le câblage |
| `Wi-Fi OK` n'apparaît jamais | Partage éteint, ou pas en 2,4 GHz, ou mauvais nom / mot de passe |
| Erreur à `client.connect()` (`ECONNABORTED`, `EHOSTUNREACH`) | Mauvaise IP dans `BROKER`, broker arrêté, PC pas sur le même réseau, ou pare-feu |
| `ECONNRESET` pendant l'envoi | Message envoyé sans `.encode()` (problème des accents) |
| Rien n'arrive dans le terminal du récepteur | `balise.py` non lancé, ou Mosquitto fermé |
| Dashboard figé | `recepteur.py` arrêté |
| Erreur d'écriture dans `mesures.csv` | Le fichier est ouvert dans Excel → le fermer |

---

## 8. Pour la suite

- **Niveau normal** : alertes (notification quand l'état passe à Poor), batterie + BMS
  (ne jamais brancher une batterie Li-ion/LiPo directement sur la carte sans circuit adapté).
- **Niveau avancé** : prédiction de la qualité de l'air à partir de l'historique `mesures.csv`,
  Grafana, module RTC, ventilation automatique.
- **À grande échelle** : relier Mosquitto à Apache Kafka pour stocker et traiter les flux de nombreuses balises.

> Ne pas publier le vrai nom du Wi-Fi ni le mot de passe : les remplacer par
> `"NOM_DU_WIFI"` et `"MOT_DE_PASSE"` avant de partager le code.
