import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd
import numpy as np
import string

st.set_page_config(layout="wide")

# =========================
# DATABASE COMUNI (estratto essenziale)
# =========================

codici_comuni = {
    "CUNEO": "D205",
    "TORINO": "L219",
    "MILANO": "F205",
    "ROMA": "H501",
    "GENOVA": "D969",
    "BOLOGNA": "A944",
    "FIRENZE": "D612",
    "NAPOLI": "F839"
}

# =========================
# FUNZIONI CODICE FISCALE
# =========================

def estrai_consonanti(s):
    return "".join([c for c in s.upper() if c in "BCDFGHJKLMNPQRSTVWXYZ"])

def estrai_vocali(s):
    return "".join([c for c in s.upper() if c in "AEIOU"])

def genera_cf(nome, cognome, data, sesso, comune):

    cognome = cognome.upper()
    nome = nome.upper()
    comune = comune.upper()

    cons_cogn = estrai_consonanti(cognome)
    voc_cogn = estrai_vocali(cognome)
    cod_cogn = (cons_cogn + voc_cogn + "XXX")[:3]

    cons_nome = estrai_consonanti(nome)
    if len(cons_nome) >= 4:
        cod_nome = cons_nome[0] + cons_nome[2] + cons_nome[3]
    else:
        cod_nome = (cons_nome + estrai_vocali(nome) + "XXX")[:3]

    anno = str(data.year)[2:]

    mesi = "ABCDEHLMPRST"
    mese = mesi[data.month - 1]

    giorno = data.day
    if sesso == "F":
        giorno += 40
    giorno = f"{giorno:02d}"

    codice_catastale = codici_comuni.get(comune, "XXXX")

    return cod_cogn + cod_nome + anno + mese + giorno + codice_catastale

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

with col2:
    data_nascita = st.date_input("Data di nascita",
                                 min_value=date(1920,1,1),
                                 max_value=date.today())
    email = st.text_input("Email")
    telefono = st.text_input("Telefono")
    indirizzo = st.text_input("Indirizzo")

eta = date.today().year - data_nascita.year
st.write(f"Età: {eta} anni")

cf = ""
if nome and cognome and comune:
    cf = genera_cf(nome, cognome, data_nascita, sesso, comune)

st.write(f"Codice Fiscale: {cf}")

st.markdown("---")

# =========================
# ANTROPOMETRIA
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
        "Z1 Recupero": 0.55 * ftp,
        "Z2 Endurance": 0.75 * ftp,
        "Z3 Tempo": 0.90 * ftp,
        "Z4 Soglia": 1.05 * ftp,
        "Z5 VO2max": 1.20 * ftp
    }

    df_potenza = pd.DataFrame(zone_potenza.items(), columns=["Zona","Limite W"])
    st.table(df_potenza)

# =========================
# ZONE CARDIO
# =========================

if fthr > 0:
    st.subheader("Zone Cardio")

    zone_cardio = {
        "Z1": 0.81 * fthr,
        "Z2": 0.89 * fthr,
        "Z3": 0.93 * fthr,
        "Z4": 0.99 * fthr,
        "Z5": 1.05 * fthr
    }

    df_cardio = pd.DataFrame(zone_cardio.items(), columns=["Zona","Limite bpm"])
    st.table(df_cardio)

st.markdown("---")

# =========================
# PDF
# =========================

if st.button("Genera PDF"):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    pdf.cell(0,8,"REPORT VALUTAZIONE", ln=True)
    pdf.ln(5)

    pdf.cell(0,8,f"Nome: {nome} {cognome}", ln=True)
    pdf.cell(0,8,f"Codice Fiscale: {cf}", ln=True)
    pdf.cell(0,8,f"BMI: {bmi:.2f} ({classificazione})", ln=True)
    pdf.cell(0,8,f"FTP: {ftp} W", ln=True)
    pdf.cell(0,8,f"W/kg: {wkg:.2f}", ln=True)
    pdf.cell(0,8,f"FTHR: {fthr} bpm", ln=True)

    pdf.output("report.pdf")

    with open("report.pdf", "rb") as f:
        st.download_button("Scarica PDF", f, file_name="report.pdf")
