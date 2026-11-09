import os
import pandas as pd
import streamlit as st

FICHIER = "mesures.csv"

st.set_page_config(page_title="Balise qualité de l'air", layout="wide")
st.title("Balise de qualité de l'air intérieur")


@st.fragment(run_every=5)          # cette partie se recharge toute seule toutes les 5 s
def afficher():
    # 1. Lire l'historique
    if not os.path.exists(FICHIER):
        st.warning("Pas encore de données : lancez recepteur.py et la balise.")
        return
    df = pd.read_csv(FICHIER, parse_dates=["date_heure"])
    if df.empty:
        st.warning("Le fichier est encore vide.")
        return

    # 2. La dernière mesure
    derniere = df.iloc[-1]

    # 3. Bandeau de couleur selon l'état
    texte = "État : " + derniere["etat"] + "  |  Cause : " + str(derniere["cause"])
    if derniere["etat"] == "Good":
        st.success(texte)
    elif derniere["etat"] == "Moderate":
        st.warning(texte)
    else:
        st.error(texte)

    # 4. Les valeurs actuelles
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Température", f"{derniere['temperature']} °C")
    col2.metric("Humidité", f"{derniere['humidite']} %")
    col3.metric("Air", f"{derniere['air']}")
    col4.metric("Dernière mesure", derniere["date_heure"].strftime("%H:%M:%S"))

    # 5. Les graphiques (100 dernières mesures)
    historique = df.tail(100).set_index("date_heure")
    g1, g2, g3 = st.columns(3)
    g1.subheader("Température (°C)")
    g1.line_chart(historique["temperature"])
    g2.subheader("Humidité (%)")
    g2.line_chart(historique["humidite"])
    g3.subheader("Air")
    g3.line_chart(historique["air"])

    # 6. Le tableau des dernières mesures (la plus récente en haut)
    st.subheader("Dernières mesures")
    st.dataframe(df.tail(10).iloc[::-1])


afficher()