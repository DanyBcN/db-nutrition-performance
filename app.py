import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd
import numpy as np

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
# FUNZIONI CODICE FISCALE
# =========================

codici_comuni = {
    "CUNEO": "D205",
    "TORINO": "L219",
    "MILANO": "F205",
    "ROMA": "H501",
}

mesi_cf = "ABCDEHLMPRST"

def consonanti(s):
    return "".join([c for c in s.upper() if c in "BCDFGHJKLMNPQRSTVWXYZ"])

def vocali(s):
    return "".join([c for c in s.upper() if c in "AEIOU"])

def carattere_controllo(cf15):
    dispari = {
        **dict(zip("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        [1,0,5,7,9,13,15,17,19,21,
         1,0,5,7,9,13,15,17,19,21,
         2,4,18,20,11,3,6,8,12,14,
         16,10,22,25,24,23])),
    }

    pari = {c:i for i,c in enumerate("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")}

    s = 0
    for i, c in enumerate(cf15):
        if (i+1) % 2 == 0:
            s += pari[c]
        else:
            s += dispari[c]

    return chr((s % 26) + ord('A'))

def genera_cf(nome, cognome, data, sesso, comune):

    cons_cogn = consonanti(cognome)
    voc_cogn = vocali(cognome)
    cod_cogn = (cons_cogn + voc_cogn + "XXX")[:3]

    cons_nome = consonanti(nome)
    if len(cons_nome) >= 4:
        cod_nome = cons_nome[0] + cons_nome[2] + cons_nome[3]
    else:
        cod_nome = (cons_nome + vocali(nome) + "XXX")[:3]

    anno = str(data.year)[2:]
    mese = mesi_cf[data.month - 1]

    giorno = data.day + (40 if sesso == "F" else 0)
    giorno = f"{giorno:02d}"

    comune = comune.upper()
    codice_catastale = codici_comuni.get(comune, "XXXX")

    cf15 = cod_cogn + cod_nome + anno + mese + giorno + codice_catastale
    controllo = carattere_controllo(cf15)

    return cf15 + controllo

# =========================
# DATI ANAGRAFICI
# =========================

st.header("Dati Anagrafici")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")
sesso = st.selectbox("Sesso", ["M","F"])
comune = st.text_input("Comune di nascita")

data_nascita = st.date_input(
    "Data di nascita",
    min_value=date(1920,1,1),
    max_value=date.today(),
    format="DD/MM/YYYY"
)

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
    elif bmi < 25:
        classificazione = "Normopeso"
    elif bmi < 30:
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
fthr = st.number_input("FTHR (bpm) - opzionale", 0.0, 220.0)

# FTHR stimato se non inserito
if fthr == 0:
    fc_max = 220 - eta
    fthr = 0.95 * fc_max
    st.write(f"FTHR stimato: {fthr:.0f} bpm")

wkg = ftp / peso if peso > 0 else 0
st.write(f"W/kg: {wkg:.2f}")

# =========================
# ZONE POTENZA
# =========================

if ftp > 0:
    st.subheader("Zone Potenza")

    zone = [
        ("Z1 Recupero", 0.00, 0.55),
        ("Z2 Endurance", 0.56, 0.75),
        ("Z3 Tempo", 0.76, 0.90),
        ("Z4 Soglia", 0.91, 1.05),
        ("Z5 VO2max", 1.06, 1.20),
    ]

    dati = []
    for nome_z, min_p, max_p in zone:
        dati.append([nome_z,
                     round(min_p * ftp),
                     round(max_p * ftp)])

    df_zone = pd.DataFrame(dati, columns=["Zona","Da (W)","A (W)"])
    st.table(df_zone)

# =========================
# ZONE CARDIO
# =========================

if fthr > 0:
    st.subheader("Zone Cardio")

    zone_hr = [
        ("Z1", 0.81, 0.89),
        ("Z2", 0.90, 0.93),
        ("Z3", 0.94, 0.99),
        ("Z4", 1.00, 1.05),
    ]

    dati_hr = []
    for nome_z, min_p, max_p in zone_hr:
        dati_hr.append([nome_z,
                        round(min_p * fthr),
                        round(max_p * fthr)])

    df_hr = pd.DataFrame(dati_hr, columns=["Zona","Da (bpm)","A (bpm)"])
    st.table(df_hr)

st.markdown("---")

# =========================
# PDF
# =========================

if st.button("Genera PDF"):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    pdf.cell(0,8,"REPORT VALUTAZIONE CLINICA", ln=True)
    pdf.ln(5)

    pdf.cell(0,8,f"Nome: {nome} {cognome}", ln=True)
    pdf.cell(0,8,f"Data nascita: {data_nascita.strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(0,8,f"Codice Fiscale: {cf}", ln=True)
    pdf.ln(5)

    pdf.cell(0,8,f"BMI: {bmi:.2f} ({classificazione})", ln=True)
    pdf.cell(0,8,f"FTP: {ftp} W", ln=True)
    pdf.cell(0,8,f"W/kg: {wkg:.2f}", ln=True)
    pdf.cell(0,8,f"FTHR: {fthr:.0f} bpm", ln=True)

    pdf.output("report.pdf")

    with open("report.pdf", "rb") as f:
        st.download_button("Scarica PDF", f, file_name="report.pdf")
