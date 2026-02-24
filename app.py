import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd
import numpy as np
from codicefiscale import codicefiscale

st.set_page_config(layout="wide")

# =========================
# LOGO CENTRATO
# =========================

try:
    logo = Image.open("logo.png")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(logo, width=250)
except:
    pass

st.markdown("---")

# =========================
# DATI ANAGRAFICI
# =========================

st.header("Dati Anagrafici")

col1, col2 = st.columns(2)

with col1:
    nome = st.text_input("Nome")
    cognome = st.text_input("Cognome")
    sesso = st.selectbox("Sesso", ["M","F"])
    comune = st.text_input("Comune di nascita")
    provincia = st.text_input("Provincia (sigla es. CN)")

with col2:
    data_nascita = st.date_input("Data di nascita", 
                                 min_value=date(1920,1,1), 
                                 max_value=date.today())
    email = st.text_input("Email")
    telefono = st.text_input("Telefono")
    indirizzo = st.text_input("Indirizzo")

eta = date.today().year - data_nascita.year
st.write(f"Età: {eta} anni")

# =========================
# CODICE FISCALE UFFICIALE
# =========================

cf = ""
if nome and cognome and comune and provincia:
    try:
        cf = codicefiscale.encode(
            lastname=cognome,
            firstname=nome,
            gender=sesso,
            birthdate=data_nascita,
            birthplace=comune
        )
    except:
        cf = "Errore comune non riconosciuto"

st.write(f"Codice Fiscale: {cf}")

st.markdown("---")

# =========================
# DATI ANTROPOMETRICI
# =========================

st.header("Valutazione Antropometrica")

peso = st.number_input("Peso (kg)", 30.0, 200.0)
altezza = st.number_input("Altezza (cm)", 100.0, 220.0)

bmi = 0
classificazione = ""

if peso and altezza:
    altezza_m = altezza / 100
    bmi = peso / (altezza_m ** 2)

    if bmi < 18.5:
        classificazione = "Sottopeso"
    elif 18.5 <= bmi < 25:
        classificazione = "Normopeso"
    elif 25 <= bmi < 30:
        classificazione = "Sovrappeso"
    else:
        classificazione = "Obesità"

    st.write(f"BMI: {bmi:.2f} ({classificazione})")

st.markdown("---")

# =========================
# PERFORMANCE
# =========================

st.header("Performance")

ftp = st.number_input("FTP (W)", 0.0, 1000.0)
fthr = st.number_input("FTHR (bpm)", 0.0, 220.0)

wkg = 0
if peso > 0:
    wkg = ftp / peso
    st.write(f"W/kg: {wkg:.2f}")

# =========================
# ZONE POTENZA
# =========================

if ftp > 0:
    st.subheader("Zone Potenza")

    zone_potenza = {
        "Z1 Recupero": (0.55 * ftp),
        "Z2 Endurance": (0.75 * ftp),
        "Z3 Tempo": (0.90 * ftp),
        "Z4 Soglia": (1.05 * ftp),
        "Z5 VO2max": (1.20 * ftp)
    }

    df_potenza = pd.DataFrame(zone_potenza.items(), columns=["Zona","Limite W"])
    st.table(df_potenza)

# =========================
# ZONE CARDIO
# =========================

if fthr > 0:
    st.subheader("Zone Cardio")

    zone_cardio = {
        "Z1": (0.81 * fthr),
        "Z2": (0.89 * fthr),
        "Z3": (0.93 * fthr),
        "Z4": (0.99 * fthr),
        "Z5": (1.05 * fthr)
    }

    df_cardio = pd.DataFrame(zone_cardio.items(), columns=["Zona","Limite bpm"])
    st.table(df_cardio)

st.markdown("---")

# =========================
# PDF COMPLETO
# =========================

if st.button("Genera PDF"):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    pdf.cell(0,8,"REPORT VALUTAZIONE", ln=True)
    pdf.ln(5)

    pdf.cell(0,8,f"Nome: {nome} {cognome}", ln=True)
    pdf.cell(0,8,f"Codice Fiscale: {cf}", ln=True)
    pdf.cell(0,8,f"Email: {email}", ln=True)
    pdf.cell(0,8,f"Telefono: {telefono}", ln=True)
    pdf.cell(0,8,f"Indirizzo: {indirizzo}", ln=True)
    pdf.ln(5)

    pdf.cell(0,8,f"BMI: {bmi:.2f} ({classificazione})", ln=True)
    pdf.cell(0,8,f"FTP: {ftp} W", ln=True)
    pdf.cell(0,8,f"W/kg: {wkg:.2f}", ln=True)
    pdf.cell(0,8,f"FTHR: {fthr} bpm", ln=True)

    pdf.output("report.pdf")

    with open("report.pdf", "rb") as f:
        st.download_button("Scarica PDF", f, file_name="report.pdf")
