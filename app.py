import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import matplotlib.pyplot as plt

# ======================================================
# CONFIGURAZIONE PAGINA
# ======================================================

st.set_page_config(layout="wide")

# ======================================================
# FUNZIONE MODELLO SALITA REALISTICO
# ======================================================

def tempo_salita_realistico(potenza, peso):
    peso_tot = peso + 8  # bici
    g = 9.81
    pendenza = 0.06
    Crr = 0.004
    rho = 1.226
    CdA = 0.32
    lunghezza = 5000

    velocita = 5

    for _ in range(50):
        forza_grav = peso_tot * g * pendenza
        forza_roll = peso_tot * g * Crr
        forza_aero = 0.5 * rho * CdA * velocita**2
        forza_tot = forza_grav + forza_roll + forza_aero
        velocita = potenza / forza_tot

    tempo = lunghezza / velocita / 60
    return tempo

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

zone_df = pd.DataFrame()
zone_hr_df = pd.DataFrame()

# ======================================================
# DATI ANAGRAFICI
# ======================================================

st.header("Dati Anagrafici")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")

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

col1, col2 = st.columns(2)

with col1:
    peso = st.number_input("Peso (kg)", 30.0, 200.0)
    altezza = st.number_input("Altezza (cm)", 100.0, 220.0)
    fm = st.number_input("Massa grassa (%)", 3.0, 50.0)

altezza_m = altezza / 100 if altezza > 0 else 0
bmi = peso / (altezza_m**2) if altezza_m > 0 else 0
fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg
ffmi = massa_magra / (altezza_m**2) if altezza_m > 0 else 0

with col2:
    st.metric("BMI", f"{bmi:.2f}")
    st.metric("FFMI", f"{ffmi:.2f}")
    st.metric("Massa Magra", f"{massa_magra:.1f} kg")
    st.metric("Massa Grassa", f"{fm_kg:.1f} kg")

st.markdown("---")

# ======================================================
# CALCOLO FTP
# ======================================================

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

if wkg < 2.5:
    livello = "Principiante"
elif wkg < 3.2:
    livello = "Amatore"
elif wkg < 4.0:
    livello = "Buono"
elif wkg < 5.0:
    livello = "Avanzato"
else:
    livello = "Elite"

st.write(f"Livello prestativo stimato: {livello}")

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
    delta_wkg = nuovo_wkg - wkg

    tempo_vecchio = tempo_salita_realistico(ftp, peso)
    tempo_nuovo = tempo_salita_realistico(nuova_ftp, nuovo_peso)

    if delta_wkg > 0.3:
        giudizio = "Miglioramento significativo"
    elif delta_wkg > 0.1:
        giudizio = "Miglioramento moderato"
    else:
        giudizio = "Miglioramento lieve"

    st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")
    st.write(f"Giudizio: {giudizio}")
    st.write(f"Salita 5 km 6%: da {tempo_vecchio:.1f} min a {tempo_nuovo:.1f} min")

st.markdown("---")

# ======================================================
# PDF
# ======================================================

if st.button("Genera PDF Professionale"):

    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 18)
            self.cell(0, 10, "REPORT PERFORMANCE", 0, 1, "C")
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "", 11)

    pdf.multi_cell(0, 8,
        f"Nome: {nome}\n"
        f"Cognome: {cognome}\n"
        f"Eta: {eta}\n\n"
        f"Peso: {peso:.1f} kg\n"
        f"Altezza: {altezza:.1f} cm\n"
        f"BMI: {bmi:.2f}\n"
        f"FTP: {ftp:.2f} W\n"
        f"W/kg: {wkg:.2f}"
    )

    pdf.output("report_performance.pdf")

    with open("report_performance.pdf", "rb") as f:
        st.download_button(
            "Scarica PDF",
            f,
            "report_performance.pdf"
        )
