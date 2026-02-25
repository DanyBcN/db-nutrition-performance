import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import matplotlib.pyplot as plt
import math

st.set_page_config(layout="wide")

# ======================================================
# FUNZIONI SCIENTIFICHE
# ======================================================

def calcola_bmi(peso, altezza_cm):
    h = altezza_cm / 100
    return peso / (h**2) if h > 0 else 0

def calcola_ffmi(massa_magra, altezza_cm):
    h = altezza_cm / 100
    return massa_magra / (h**2) if h > 0 else 0

def calcola_vo2max(wkg):
    return (wkg * 10.8) + 7 if wkg > 0 else 0

def categoria_wkg(wkg):
    if wkg < 2.5: return "Principiante"
    elif wkg < 3.5: return "Amatore"
    elif wkg < 4.5: return "Buon livello"
    elif wkg < 5.5: return "Elite"
    else: return "Professionista"

def tempo_salita_realistico(potenza, peso):
    lunghezza = 5000
    pendenza = 0.06
    g = 9.81
    rho = 1.225
    CdA = 0.32
    Crr = 0.004

    forza_grav = peso * g * pendenza
    forza_roll = peso * g * Crr

    velocita = 5
    for _ in range(15):
        forza_aero = 0.5 * rho * CdA * velocita**2
        velocita = potenza / (forza_grav + forza_roll + forza_aero)

    return (lunghezza / velocita) / 60

# ======================================================
# DATI ANAGRAFICI
# ======================================================

st.header("Dati Anagrafici")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")
sesso = st.selectbox("Sesso", ["Maschio", "Femmina"])

data_nascita = st.date_input(
    "Data di nascita",
    min_value=date(1920,1,1),
    max_value=date.today()
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

bmi = calcola_bmi(peso, altezza)
fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg
ffmi = calcola_ffmi(massa_magra, altezza)

# Classificazione BMI
if bmi < 18.5: categoria_bmi = "Sottopeso"
elif bmi < 25: categoria_bmi = "Normopeso"
elif bmi < 30: categoria_bmi = "Sovrappeso"
else: categoria_bmi = "Obesità"

st.write(f"BMI: {bmi:.2f} ({categoria_bmi})")
st.write(f"Massa magra: {massa_magra:.2f} kg")
st.write(f"FFMI: {ffmi:.2f}")

# ======================================================
# METABOLISMO
# ======================================================

if sesso == "Maschio":
    bmr = 10*peso + 6.25*altezza - 5*eta + 5
else:
    bmr = 10*peso + 6.25*altezza - 5*eta - 161

st.write(f"Metabolismo basale (Mifflin): {bmr:.0f} kcal")

st.markdown("---")

# ======================================================
# FTP
# ======================================================

st.header("Calcolo FTP")

metodo = st.selectbox(
    "Metodo FTP",
    ["Immissione diretta","Test 20 minuti","Test 8 minuti","Ramp test"]
)

valore_test = st.number_input("Valore test (W)", 0.0)

if metodo == "Immissione diretta":
    ftp = valore_test
elif metodo == "Test 20 minuti":
    ftp = valore_test * 0.95
elif metodo == "Test 8 minuti":
    ftp = valore_test * 0.90
else:
    ftp = valore_test * 0.75

wkg = ftp / peso if peso > 0 else 0
vo2max = calcola_vo2max(wkg)
cat_w = categoria_wkg(wkg)

st.write(f"FTP: {ftp:.1f} W")
st.write(f"W/kg: {wkg:.2f}")
st.write(f"VO2max stimato: {vo2max:.1f} ml/kg/min")
st.write(f"Categoria performance: {cat_w}")

st.markdown("---")

# ======================================================
# PROIEZIONE PERFORMANCE
# ======================================================

st.header("Proiezione Performance")

nuovo_peso = st.number_input("Nuovo peso target (kg)", 0.0)
incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0)

if nuovo_peso > 0 and ftp > 0:

    nuova_ftp = ftp * (1 + incremento_ftp/100)
    nuovo_wkg = nuova_ftp / nuovo_peso

    tempo_vecchio = tempo_salita_realistico(ftp, peso)
    tempo_nuovo = tempo_salita_realistico(nuova_ftp, nuovo_peso)

    st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")
    st.write(f"Salita 5 km 6%: {tempo_vecchio:.1f} → {tempo_nuovo:.1f} min")

st.markdown("---")

# ======================================================
# PDF PROFESSIONALE
# ======================================================

if st.button("Genera PDF Professionale"):

    def safe(text):
        return text.encode("latin-1", "replace").decode("latin-1")

    class PDF(FPDF):

        def header(self):
            self.set_font("Helvetica", "B", 18)
            self.cell(0, 10, "REPORT PERFORMANCE CLINICA", 0, 1, "C")
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.cell(0, 10, f"Pagina {self.page_no()}", 0, 0, "C")

        def section(self, title):
            self.set_font("Helvetica", "B", 12)
            self.cell(0, 8, title, 0, 1)
            self.ln(2)

        def body(self, text):
            self.set_font("Helvetica", "", 10)
            self.multi_cell(0, 6, safe(text))
            self.ln(3)

    pdf = PDF()
    pdf.add_page()

    pdf.section("Dati Anagrafici")
    pdf.body(
        f"{nome} {cognome}\n"
        f"Eta: {eta} anni\n"
        f"Sesso: {sesso}"
    )

    pdf.section("Antropometria")
    pdf.body(
        f"Peso: {peso:.1f} kg\n"
        f"Altezza: {altezza:.1f} cm\n"
        f"BMI: {bmi:.2f} ({categoria_bmi})\n"
        f"FFMI: {ffmi:.2f}\n"
        f"Massa grassa: {fm:.1f}%\n"
        f"BMR: {bmr:.0f} kcal"
    )

    pdf.section("Performance")
    pdf.body(
        f"Metodo FTP: {metodo}\n"
        f"FTP: {ftp:.1f} W\n"
        f"W/kg: {wkg:.2f}\n"
        f"VO2max stimato: {vo2max:.1f}\n"
        f"Categoria: {cat_w}"
    )

    if nuovo_peso > 0 and ftp > 0:
        pdf.section("Proiezione")
        pdf.body(
            f"Nuovo peso: {nuovo_peso:.1f} kg\n"
            f"Nuova FTP: {nuova_ftp:.1f} W\n"
            f"Nuovo W/kg: {nuovo_wkg:.2f}\n"
            f"Tempo salita: {tempo_vecchio:.1f} → {tempo_nuovo:.1f} min"
        )

    pdf.output("report_clinica_premium.pdf")

    with open("report_clinica_premium.pdf", "rb") as f:
        st.download_button(
            "Scarica PDF",
            f,
            "report_clinica_premium.pdf"
        )
