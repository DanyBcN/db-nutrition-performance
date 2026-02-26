import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# ======================================================
# INIZIALIZZAZIONE VARIABILI
# ======================================================

ftp = 0.0
valore_test = 0.0
wkg = 0.0
nuova_ftp = 0.0
nuovo_wkg = 0.0
tempo_vecchio = 0.0
tempo_nuovo = 0.0
giudizio = ""
categoria_bmi = ""
giudizio_atleta = ""
giudizio_fm = ""
zone_df = pd.DataFrame()
zone_hr_df = pd.DataFrame()
bmr = 0.0

# ======================================================
# LOGO
# ======================================================

col1, col2, col3 = st.columns([1,2,1])
with col2:
    try:
        st.image("logo.png", width=300)
    except:
        pass

# ======================================================
# DATI ANAGRAFICI
# ======================================================

st.header("Dati Anagrafici")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")
sesso = st.selectbox("Sesso", ["Uomo", "Donna"])

data_nascita = st.date_input(
    "Data di nascita",
    min_value=date(1920,1,1),
    max_value=date.today(),
    format="DD/MM/YYYY"
)

eta = date.today().year - data_nascita.year - (
    (date.today().month, date.today().day) <
    (data_nascita.month, data_nascita.day)
)

st.markdown("---")

# ======================================================
# ANTROPOMETRIA
# ======================================================

st.header("Valutazione Antropometrica")

peso = st.number_input("Peso (kg)", 30.0, 200.0)
altezza = st.number_input("Altezza (cm)", 100.0, 220.0)
fm = st.number_input("Massa grassa (%)", 3.0, 50.0)

altezza_m = altezza / 100 if altezza > 0 else 0
bmi = peso / (altezza_m**2) if altezza_m > 0 else 0
fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg

# Classificazione OMS
if bmi < 18.5:
    categoria_bmi = "Sottopeso"
elif 18.5 <= bmi < 25:
    categoria_bmi = "Normopeso"
elif 25 <= bmi < 30:
    categoria_bmi = "Sovrappeso"
else:
    categoria_bmi = "Obesità"

st.write(f"BMI: {bmi:.2f} ({categoria_bmi})")
st.write(f"Massa grassa: {fm_kg:.2f} kg")
st.write(f"Massa magra: {massa_magra:.2f} kg")

# =========================
# BMR
# =========================

if peso > 0 and altezza > 0:
    if sesso == "Uomo":
        bmr = 10*peso + 6.25*altezza - 5*eta + 5
    else:
        bmr = 10*peso + 6.25*altezza - 5*eta - 161

    st.write(f"Metabolismo basale stimato: {bmr:.0f} kcal")

# ======================================================
# RANGE ATLETA
# ======================================================

st.subheader("Range BMI Ideale Atleta")

tipo_sport = st.selectbox(
    "Tipologia atleta",
    ["Endurance", "Sport di squadra", "Forza/Potenza"]
)

if tipo_sport == "Endurance":
    bmi_min, bmi_max = 19, 22
    fm_min, fm_max = 6, 12
elif tipo_sport == "Sport di squadra":
    bmi_min, bmi_max = 21, 24
    fm_min, fm_max = 8, 15
else:
    bmi_min, bmi_max = 23, 27
    fm_min, fm_max = 10, 18

if bmi < bmi_min:
    giudizio_atleta = "Inferiore al range ideale atleta"
elif bmi > bmi_max:
    giudizio_atleta = "Superiore al range ideale atleta"
else:
    giudizio_atleta = "Nel range ideale atleta"

if fm < fm_min:
    giudizio_fm = "Inferiore al range ideale"
elif fm > fm_max:
    giudizio_fm = "Superiore al range ideale"
else:
    giudizio_fm = "Nel range ideale"

st.write(f"Range BMI ideale: {bmi_min}-{bmi_max}")
st.write(f"Valutazione atleta: {giudizio_atleta}")
st.write(f"Range FM ideale: {fm_min}-{fm_max}%")
st.write(f"Valutazione massa grassa: {giudizio_fm}")

# ======================================================
# FTP
# ======================================================

st.markdown("---")
st.header("Calcolo FTP")

metodo = st.selectbox(
    "Metodo FTP",
    ["Immissione diretta","Test 20 minuti","Test 8 minuti","Ramp test"]
)

if metodo == "Immissione diretta":
    valore_test = st.number_input("FTP (W)", 0.0)
    ftp = valore_test
elif metodo == "Test 20 minuti":
    valore_test = st.number_input("Media 20 min (W)", 0.0)
    ftp = valore_test * 0.95
elif metodo == "Test 8 minuti":
    valore_test = st.number_input("Media 8 min (W)", 0.0)
    ftp = valore_test * 0.90
elif metodo == "Ramp test":
    valore_test = st.number_input("Ultimo step completato (W)", 0.0)
    ftp = valore_test * 0.75

wkg = ftp / peso if peso > 0 else 0

st.write(f"FTP stimata: {ftp:.2f} W")
st.write(f"W/kg: {wkg:.2f}")

# ======================================================
# PDF
# ======================================================

if st.button("Genera PDF Professionale"):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, "REPORT PERFORMANCE", ln=True)

    pdf.cell(0, 8, f"Nome: {nome}", ln=True)
    pdf.cell(0, 8, f"Cognome: {cognome}", ln=True)
    pdf.cell(0, 8, f"Eta: {eta} anni", ln=True)
    pdf.cell(0, 8, f"Peso: {peso:.1f} kg", ln=True)
    pdf.cell(0, 8, f"BMI: {bmi:.2f}", ln=True)
    pdf.cell(0, 8, f"BMR: {bmr:.0f} kcal", ln=True)
    pdf.cell(0, 8, f"FTP: {ftp:.2f} W", ln=True)
    pdf.cell(0, 8, f"W/kg: {wkg:.2f}", ln=True)

    pdf.output("report_performance_professionale.pdf")

    with open("report_performance_professionale.pdf", "rb") as f:
        st.download_button(
            "Scarica PDF Professionale",
            f,
            "report_performance_professionale.pdf"
        )
