import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

# ======================================================
# LOGO CENTRATO
# ======================================================

try:
    logo = Image.open("logo.png")
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.image(logo, width=250)
except:
    pass

st.markdown("---")

# ======================================================
# ANAGRAFICA
# ======================================================

st.header("Dati Anagrafici")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")
sesso = st.selectbox("Sesso", ["M","F"])
comune = st.text_input("Comune di nascita")
provincia = st.text_input("Provincia di nascita (sigla)")

data_nascita = st.date_input(
    "Data di nascita",
    min_value=date(1920,1,1),
    max_value=date.today(),
    format="DD/MM/YYYY"
)

email = st.text_input("Email")
telefono = st.text_input("Telefono")
indirizzo = st.text_input("Indirizzo")

eta = date.today().year - data_nascita.year - (
    (date.today().month, date.today().day) <
    (data_nascita.month, data_nascita.day)
)

st.write(f"Età: {eta} anni")

st.markdown("---")

# ======================================================
# ANTROPOMETRIA
# ======================================================

st.header("Valutazione Antropometrica")

peso = st.number_input("Peso (kg)", 30.0, 200.0)
altezza = st.number_input("Altezza (cm)", 100.0, 220.0)
fm = st.number_input("Massa grassa (%)", 3.0, 50.0)

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

fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg

st.write(f"Massa grassa: {fm_kg:.2f} kg")
st.write(f"Massa magra: {massa_magra:.2f} kg")

st.markdown("---")

# ======================================================
# CALCOLO FTP
# ======================================================

st.header("Calcolo FTP")

metodo = st.selectbox(
    "Metodo calcolo FTP",
    ["Immissione diretta","Test 20 minuti","Test 8 minuti","Ramp test"]
)

ftp = 0

if metodo == "Immissione diretta":
    ftp = st.number_input("Inserisci FTP (W)", 0.0)

elif metodo == "Test 20 minuti":
    p20 = st.number_input("Potenza media 20' (W)", 0.0)
    ftp = p20 * 0.95

elif metodo == "Test 8 minuti":
    p8 = st.number_input("Potenza media 8' (W)", 0.0)
    ftp = p8 * 0.90

elif metodo == "Ramp test":
    ultimo_step = st.number_input("Ultimo step completato (W)", 0.0)
    ftp = ultimo_step * 0.75

st.write(f"FTP calcolata: {ftp:.2f} W")

wkg = ftp / peso if peso > 0 else 0
st.write(f"W/kg: {wkg:.2f}")

st.markdown("---")

# ======================================================
# FTHR
# ======================================================

st.header("Frequenza Cardiaca")

fthr_input = st.number_input("FTHR (bpm) - opzionale", 0.0)

if fthr_input > 0:
    fthr = fthr_input
else:
    fc_max = 220 - eta
    fthr = 0.95 * fc_max
    st.write(f"FTHR stimata: {fthr:.0f} bpm")

# ======================================================
# ZONE POTENZA
# ======================================================

zone_potenza_df = None

if ftp > 0:
    st.subheader("Zone Potenza")

    zone = [
        ("Z1",0.00,0.55),
        ("Z2",0.56,0.75),
        ("Z3",0.76,0.90),
        ("Z4",0.91,1.05),
        ("Z5",1.06,1.20),
        ("Z6",1.21,1.50),
        ("Z7",1.51,2.00),
    ]

    dati=[]
    for z,min_p,max_p in zone:
        dati.append([z,
                     round(min_p*ftp),
                     round(max_p*ftp)])

    zone_potenza_df = pd.DataFrame(dati,columns=["Zona","Da (W)","A (W)"])
    st.table(zone_potenza_df)

# ======================================================
# ZONE CARDIO
# ======================================================

zone_cardio_df = None

if fthr > 0:
    st.subheader("Zone Cardio")

    zone_hr=[
        ("Z1",0.81,0.89),
        ("Z2",0.90,0.93),
        ("Z3",0.94,0.99),
        ("Z4",1.00,1.05),
        ("Z5",1.06,1.15)
    ]

    dati_hr=[]
    for z,min_p,max_p in zone_hr:
        dati_hr.append([z,
                        round(min_p*fthr),
                        round(max_p*fthr)])

    zone_cardio_df = pd.DataFrame(dati_hr,columns=["Zona","Da (bpm)","A (bpm)"])
    st.table(zone_cardio_df)

st.markdown("---")

# ======================================================
# PROIEZIONE
# ======================================================

st.header("Proiezione Strategica")

target_fm = st.number_input("Target Massa Grassa (%)", 3.0, 20.0)
incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0)

nuova_fm_kg = massa_magra * (target_fm/(100-target_fm))
nuovo_peso = massa_magra + nuova_fm_kg
nuova_ftp = ftp * (1 + incremento_ftp/100)
nuovo_wkg = nuova_ftp/nuovo_peso if nuovo_peso>0 else 0

st.write(f"Nuovo peso: {nuovo_peso:.2f} kg")
st.write(f"Nuova FTP: {nuova_ftp:.2f} W")
st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")

st.markdown("---")

# ======================================================
# PDF PROFESSIONALE COMPLETO
# ======================================================

if st.button("Genera PDF"):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0,10,"REPORT VALUTAZIONE METABOLICO-FUNZIONALE", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", size=10)

    pdf.cell(0,6,f"Nome: {nome} {cognome}", ln=True)
    pdf.cell(0,6,f"Nato a: {comune} ({provincia})", ln=True)
    pdf.cell(0,6,f"Data nascita: {data_nascita.strftime('%d/%m/%Y')} - Eta: {eta} anni", ln=True)
    pdf.cell(0,6,f"Email: {email}", ln=True)
    pdf.cell(0,6,f"Telefono: {telefono}", ln=True)
    pdf.cell(0,6,f"Indirizzo: {indirizzo}", ln=True)

    pdf.ln(5)
    pdf.cell(0,6,"--- ANTROPOMETRIA ---", ln=True)
    pdf.cell(0,6,f"Peso: {peso} kg", ln=True)
    pdf.cell(0,6,f"Altezza: {altezza} cm", ln=True)
    pdf.cell(0,6,f"BMI: {bmi:.2f} ({classificazione})", ln=True)
    pdf.cell(0,6,f"Massa grassa: {fm_kg:.2f} kg", ln=True)
    pdf.cell(0,6,f"Massa magra: {massa_magra:.2f} kg", ln=True)

    pdf.ln(5)
    pdf.cell(0,6,"--- PERFORMANCE ---", ln=True)
    pdf.cell(0,6,f"Metodo FTP: {metodo}", ln=True)
    pdf.cell(0,6,f"FTP: {ftp:.2f} W", ln=True)
    pdf.cell(0,6,f"W/kg: {wkg:.2f}", ln=True)
    pdf.cell(0,6,f"FTHR: {fthr:.0f} bpm", ln=True)

    pdf.ln(5)

    if zone_potenza_df is not None:
        pdf.cell(0,6,"Zone Potenza:", ln=True)
        for _, row in zone_potenza_df.iterrows():
            pdf.cell(0,6,f"{row['Zona']}: {row['Da (W)']} - {row['A (W)']} W", ln=True)

    pdf.ln(3)

    if zone_cardio_df is not None:
        pdf.cell(0,6,"Zone Cardio:", ln=True)
        for _, row in zone_cardio_df.iterrows():
            pdf.cell(0,6,f"{row['Zona']}: {row['Da (bpm)']} - {row['A (bpm)']} bpm", ln=True)

    pdf.ln(5)
    pdf.cell(0,6,"--- PROIEZIONE ---", ln=True)
    pdf.cell(0,6,f"Nuovo peso: {nuovo_peso:.2f} kg", ln=True)
    pdf.cell(0,6,f"Nuova FTP: {nuova_ftp:.2f} W", ln=True)
    pdf.cell(0,6,f"Nuovo W/kg: {nuovo_wkg:.2f}", ln=True)

    pdf.output("report.pdf")

    with open("report.pdf","rb") as f:
        st.download_button("Scarica PDF",f,"report.pdf")
