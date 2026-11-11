# Balise de qualité de l'air intérieur

Projet IoT — Master Data Engineering.

La balise mesure la **température**, l'**humidité** et un **indicateur de qualité de l'air**.
Elle affiche l'état de la pièce sur sa LED (🟢 Good / 🟡 Moderate / 🔴 Poor) et envoie ses
mesures en **MQTT** vers un PC, qui les **enregistre dans PostgreSQL** et les affiche dans **Grafana**.

```
Capteurs → ESP32-C6 → Wi-Fi / MQTT → Mosquitto (Docker) → recepteur.py → PostgreSQL (Docker) → Grafana (Docker)
```

**Niveau minimum atteint** : capteurs + ESP32 + LED + Wi-Fi + MQTT + dashboard.
**Niveau normal** : stockage des données dans une base PostgreSQL et historique (courbes Grafana).

---

## 1. Les fichiers

### Sur la carte (Thonny + MicroPython)

| Fichier | Rôle |
|---|---|
| **`balise.py`** | **Programme final** : mesure, décide l'état, allume la LED, envoie au PC |
| `config.py` | Nom du Wi-Fi, mot de passe, IP du PC — **privé, jamais sur GitHub** |
| `config_exemple.py` | Modèle à copier en `config.py` |

### Sur le PC (VS Code + Python + Docker)

| Fichier | Rôle |
|---|---|
| `docker-compose.yml` | Lance Mosquitto, PostgreSQL, Grafana et pgAdmin |
| `mosquitto.conf` | Réglages du broker MQTT (utilisé par le conteneur Mosquitto) |
| `init.sql` | Crée la table `mesures` au premier démarrage de PostgreSQL |
| **`recepteur.py`** | Reçoit les messages MQTT et les enregistre dans la table `mesures` |
| `grafana/` | Source de données et tableau de bord Grafana, chargés automatiquement |
| `.env` | Mots de passe de PostgreSQL et pgAdmin — **privé, jamais sur GitHub** |

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

Grafana **ne recalcule pas** l'état : il affiche celui envoyé par la balise.
La LED et le tableau de bord affichent donc toujours la même chose.
Les couleurs des valeurs dans Grafana utilisent les mêmes seuils que le tableau ci-dessus.

### Message envoyé par la balise (topic `balise/mesures`, toutes les 5 s)

```json
{"temperature": 23, "humidite": 37, "air": 272, "etat": "Good", "cause": "aucune"}
```

La date et l'heure sont ajoutées par le PC (`recepteur.py`), car la carte ne connaît pas l'heure.
Elles sont enregistrées en **heure locale de Paris** dans la colonne `date_heure`.

### Table `mesures` (PostgreSQL)

| Colonne | Type | Contenu |
|---|---|---|
| `id` | SERIAL | Numéro de la mesure |
| `date_heure` | TIMESTAMP | Date et heure du PC (heure de Paris) |
| `temperature` | REAL | °C |
| `humidite` | REAL | % |
| `air` | INTEGER | Valeur brute du capteur d'air |
| `etat` | VARCHAR(10) | Good / Moderate / Poor |
| `cause` | VARCHAR(50) | Mesures qui ne sont pas Good, ou « aucune » |

---

## 4. Installation (une seule fois)

### Carte

1. Installer **Thonny**. *Outils → Options → Interpréteur* : **MicroPython (ESP32)** + port COM de la carte.
2. *Installer ou mettre à jour MicroPython (esptool)* : famille **ESP32-C6**, variante **Espressif • ESP32-C6**.
3. Vérifier la bibliothèque MQTT dans la console de Thonny : `from umqtt.simple import MQTTClient`.
4. Copier `config_exemple.py` en `config.py`, le remplir, puis enregistrer **`config.py` et `balise.py`** sur la carte.

### PC

1. Installer **Docker Desktop** et le lancer.
2. Installer les bibliothèques Python :
   ```powershell
   pip install paho-mqtt "psycopg[binary]" python-dotenv
   ```
3. Créer le fichier `.env` à côté de `docker-compose.yml` (choisir ses propres mots de passe) :
   ```
   POSTGRES_PASSWORD=un_mot_de_passe
   PGADMIN_PASSWORD=un_autre_mot_de_passe
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   SMTP_USER=adresse.expediteur@gmail.com
   SMTP_PASSWORD=motdepassedapplication
   ALERT_EMAIL_TO=adresse.destinataire@gmail.com
   ```
   Pour `SMTP_PASSWORD` : activer la validation en deux étapes du compte Google, puis créer un
   **mot de passe d'application** sur https://myaccount.google.com/apppasswords (16 lettres, sans espaces).
   Ce n'est pas le mot de passe Gmail normal ; il se garde comme un mot de passe.
   Pour l'URL Discord : dans le salon, *Modifier le salon → Intégrations → Webhooks → Nouveau webhook
   → Copier l'URL du webhook*. Elle se garde comme un mot de passe.
4. Autoriser le port MQTT dans le pare-feu (PowerShell **administrateur**) :
   ```powershell
   New-NetFirewallRule -DisplayName "Mosquitto MQTT" -Direction Inbound -Protocol TCP -LocalPort 1883 -Action Allow
   ```
5. Si **Mosquitto** ou **PostgreSQL** sont aussi installés sur Windows, ils prennent les ports 1883 et 5432
   et empêchent Docker de démarrer. Les arrêter, et passer PostgreSQL en démarrage manuel (PowerShell **administrateur**) :
   ```powershell
   Set-Service postgresql-x64-18 -StartupType Manual
   ```

### `mosquitto.conf`

```
listener 1883
allow_anonymous true
```

- `listener 1883` : écouter sur le port 1883, sur toutes les connexions du PC (y compris le Wi-Fi).
- `allow_anonymous true` : accepter les connexions sans identifiant.
  Pratique pour le projet, mais pas sécurisé (amélioration possible : mots de passe + TLS).

Ce fichier est **indispensable** : `docker-compose.yml` le monte dans le conteneur Mosquitto.
Sans lui, Mosquitto 2 n'accepte que les connexions venant de son propre conteneur.

### Réseau

- Utiliser le **partage de connexion du téléphone** en **2,4 GHz**
  (iPhone : activer « Maximiser la compatibilité »). L'ESP32 ne voit pas le 5 GHz.
- Le **PC et la carte doivent être sur le même réseau**.
- Dans `config.py`, remplir `NOM_WIFI`, `MOT_DE_PASSE` et `BROKER` (adresse IP du PC).

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
| 2 | Terminal | `ipconfig` → corriger `BROKER` dans `config.py` si l'IP a changé | IPv4 en `172.20.10.x` |
| 3 | Terminal 1 | `docker compose up -d` | 4 conteneurs `Started` ou `Running` |
| 4 | Terminal 2 | `python recepteur.py` | `Connecté à PostgreSQL` puis `Connecté au broker` |
| 5 | Navigateur | http://localhost:3000 → *Dashboards* → **Balise qualité de l'air** | le tableau de bord |
| 6 | Thonny | **Stop**, puis ▶ sur `balise.py` | `Wi-Fi OK`, `Connecté au broker`, puis les mesures |

**Pourquoi la balise en dernier ?**
- Sans broker, `client.connect()` échoue et le programme s'arrête.
- Sans récepteur abonné, les messages sont perdus (Mosquitto ne les garde pas).

Attendre **2 à 3 minutes** que le capteur d'air chauffe avant de faire une démonstration.

### Arrêter le projet

**Stop** dans Thonny, `Ctrl + C` dans le terminal du récepteur, puis `docker compose stop`.
L'historique reste dans PostgreSQL ; les nouvelles mesures s'ajoutent à la suite.
⚠️ Ne pas utiliser `docker compose down -v` : le `-v` **efface la base de données**.

**Balise autonome (sans PC)** : dans Thonny, *Fichier → Enregistrer sous → Appareil MicroPython*
→ `main.py`. Elle démarre seule dès qu'elle est alimentée. Ensuite, toujours cliquer sur **Stop**
avant de lancer un autre programme.

---

## 7. Voir les données

### Grafana — le tableau de bord (http://localhost:3000)

- Première connexion : `admin` / `admin`, puis choisir un nouveau mot de passe.
- *Dashboards* → **Balise qualité de l'air** : état, cause, valeurs actuelles, courbes et dernières mesures.
  Il se rafraîchit toutes les 5 s.
- La source de données PostgreSQL et le tableau de bord sont créés automatiquement à partir du dossier `grafana/`.
  Dans Grafana, l'hôte de la base est `postgres:5432` (le nom du service Docker), pas `localhost`.

### Alerte Discord

- Grafana vérifie toutes les 20 secondes la dernière mesure ; si elle est **Poor**, un message est envoyé sur Discord
  **et par e-mail** (« ⚠️ Qualité de l'air : mauvaise », avec la cause et « Pensez à aérer la pièce. »).
- L'e-mail part du compte Gmail `SMTP_USER` vers `ALERT_EMAIL_TO` (réglages dans `.env`).
- Un seul message par épisode : pas de message quand l'air redevient bon, et un rappel seulement
  si l'état reste Poor pendant 24 h.
- Tout est défini dans `grafana/provisioning/alerting/discord.yml` (le texte du message y est écrit une seule fois,
  pour Discord et l'e-mail) ; l'URL du webhook et les identifiants Gmail viennent de `.env`.
- Pour tester : approcher du parfum ou de l'alcool du capteur d'air (valeur > 1000 → Poor).

### pgAdmin — la base de données (http://localhost:5050)

- Connexion : `admin@example.com` + le `PGADMIN_PASSWORD` du fichier `.env`.
- *Register → Server* : hôte **`postgres`**, port `5432`, base `balise`, utilisateur **`balise`**,
  mot de passe = `POSTGRES_PASSWORD` du fichier `.env`.
- Les données : *Databases → balise → Schemas → public → Tables → mesures* → clic droit → *View/Edit Data*.

---

## 8. Problèmes fréquents

| Symptôme | Cause probable / solution |
|---|---|
| Aucun port COM dans Thonny | Câble USB « charge seule » → prendre un câble de données |
| `ETIMEDOUT` / « le capteur de température ne répond pas » | Fil mal enfoncé (souvent le GND) → appuyer sur les fils, relancer |
| La carte s'éteint (LED rouge éteinte) | Court-circuit 3V3 / GND → débrancher et vérifier le câblage |
| `Wi-Fi OK` n'apparaît jamais | Partage éteint, ou pas en 2,4 GHz, ou mauvais nom / mot de passe |
| `ImportError: no module named 'config'` sur la carte | `config.py` n'a pas été copié sur la carte |
| Erreur à `client.connect()` (`ECONNABORTED`, `EHOSTUNREACH`) | Mauvaise IP dans `BROKER`, conteneurs arrêtés, PC pas sur le même réseau, ou pare-feu |
| `ECONNRESET` pendant l'envoi | Message envoyé sans `.encode()` (problème des accents) |
| `docker compose up` : `port is already allocated` | Mosquitto ou PostgreSQL Windows tourne encore → l'arrêter (voir installation, étape 5) |
| `password authentication failed for user "balise"` | Le mot de passe de `.env` a changé après la création de la base (il n'est lu qu'au premier démarrage) |
| Rien n'arrive dans le terminal du récepteur | `balise.py` non lancé, ou conteneurs arrêtés |
| Tableau de bord Grafana figé | `recepteur.py` arrêté |

---

## 9. Évolution du projet

- **Version 1** : Mosquitto installé sur Windows, `recepteur.py` écrivait les mesures dans un fichier
  `mesures.csv`, et un tableau de bord **Streamlit** (`dashboard.py`) lisait ce fichier.
  Le code de cette version reste dans l'historique Git (commit `9d1ad54`).
- **Version 2** : tout tourne dans **Docker** (Mosquitto, PostgreSQL, Grafana, pgAdmin).
  `recepteur.py` enregistre dans **PostgreSQL**, et **Grafana** remplace Streamlit.
  Les mots de passe sont sortis du code (`config.py` et `.env`, ignorés par Git).
  **Alerte Discord et e-mail** envoyée par Grafana quand l'état passe à Poor.
  Sécurité : PostgreSQL, Grafana et pgAdmin ne sont accessibles que depuis le PC (`127.0.0.1`) ;
  seul Mosquitto (1883) est ouvert au réseau, pour la carte.

Les mesures de la version 1 (fichiers CSV) sont gardées en local pour le rapport, mais ne sont pas sur GitHub.

---

## 10. Pour la suite

- **Niveau normal** : batterie + BMS
  (ne jamais brancher une batterie Li-ion/LiPo directement sur la carte sans circuit adapté).
- **Niveau avancé** : prédiction de la qualité de l'air à partir de l'historique de la table `mesures`,
  module RTC, ventilation automatique.
- **À grande échelle** : relier Mosquitto à Apache Kafka pour stocker et traiter les flux de nombreuses balises.

> Ne jamais publier le vrai nom du Wi-Fi ni les mots de passe : ils restent dans `config.py` et `.env`,
> qui sont ignorés par Git.
