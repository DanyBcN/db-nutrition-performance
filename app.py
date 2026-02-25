import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd
import math

st.set_page_config(layout="wide")

# ======================================================
# LOGO
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
# DATI ANAGRAFICI
# ======================================================

st.header("Dati Anagrafici")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")

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

st.write(f"Età: {eta} anni")

st.markdown("---")

# ======================================================
# ANTROPOMETRIA
# ======================================================

st.header("Valutazione Antropometrica")

peso = st.number_input("Peso (kg)", 30.0, 200.0)
altezza = st.number_input("Altezza (cm)", 100.0, 220.0)
fm = st.number_input("Massa grassa (%)", 3.0, 50.0)

altezza_m = altezza / 100
bmi = peso / (altezza_m**2) if altezza_m > 0 else 0
fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg

st.write(f"BMI: {bmi:.2f}")
st.write(f"Massa grassa: {fm_kg:.2f} kg")
st.write(f"Massa magra: {massa_magra:.2f} kg")

st.markdown("---")

# ======================================================
# FTP CON METODO
# ======================================================

st.header("Calcolo FTP")

metodo = st.selectbox(
    "Metodo FTP",
    ["Immissione diretta","Test 20 minuti","Test 8 minuti","Ramp test"]
)

ftp = 0

if metodo == "Immissione diretta":
    ftp = st.number_input("FTP (W)", 0.0)

elif metodo == "Test 20 minuti":
    p20 = st.number_input("Media 20' (W)", 0.0)
    ftp = p20 * 0.95

elif metodo == "Test 8 minuti":
    p8 = st.number_input("Media 8' (W)", 0.0)
    ftp = p8 * 0.90

elif metodo == "Ramp test":
    ultimo = st.number_input("Ultimo step completato (W)", 0.0)
    ftp = ultimo * 0.75

wkg = ftp / peso if peso > 0 else 0

st.write(f"FTP stimata: {ftp:.2f} W")
st.write(f"W/kg: {wkg:.2f}")

st.markdown("---")

# ======================================================
# PROIEZIONE AVANZATA
# ======================================================

st.header("Proiezione Performance")

nuovo_peso_input = st.number_input("Nuovo peso target (kg)", 0.0)
incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0)

if nuovo_peso_input > 0:

    nuova_ftp = ftp * (1 + incremento_ftp/100)
    nuovo_wkg = nuova_ftp / nuovo_peso_input

    st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")

    delta = nuovo_wkg - wkg

    if delta > 0.3:
        giudizio = "Miglioramento significativo"
    elif delta > 0.1:
        giudizio = "Miglioramento moderato"
    else:
        giudizio = "Miglioramento lieve"

    st.write(f"Giudizio: {giudizio}")

    # ======================================================
    # SIMULAZIONE SALITA
    # ======================================================

    st.subheader("Simulazione salita 5 km al 6%")

    lunghezza = 5000
    pendenza = 0.06
    g = 9.81

    # velocità stimata (modello semplificato potenza gravitazionale)
    def tempo_salita(potenza, peso):
        forza = peso * g * pendenza
        velocita = potenza / forza
        tempo = lunghezza / velocita
        return tempo / 60  # minuti

    tempo_vecchio = tempo_salita(ftp, peso)
    tempo_nuovo = tempo_salita(nuova_ftp, nuovo_peso_input)

    differenza = tempo_vecchio - tempo_nuovo

    st.write(f"Tempo attuale: {tempo_vecchio:.1f} min")
    st.write(f"Tempo stimato nuovo: {tempo_nuovo:.1f} min")
    st.write(f"Miglioramento: {differenza:.1f} min")

st.markdown("---")

# ======================================================
# PDF COMPLETO
# ======================================================

if st.button("Genera PDF"):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,"REPORT PERFORMANCE AVANZATO",0,1,"C")
    pdf.ln(5)

    pdf.set_font("Arial","",11)

    pdf.multi_cell(0,7,
        f"Nome: {nome} {cognome}\n"
        f"Data di nascita: {data_nascita.strftime('%d %m %Y')}\n\n"
        f"Peso: {peso:.1f} kg\n"
        f"BMI: {bmi:.2f}\n"
        f"Massa grassa: {fm:.1f}%\n\n"
        f"FTP: {ftp:.2f} W\n"
        f"W/kg: {wkg:.2f}\n"
    )

    if nuovo_peso_input > 0:
        pdf.multi_cell(0,7,
            f"\nNuovo peso target: {nuovo_peso_input:.1f} kg\n"
            f"Nuova FTP: {nuova_ftp:.2f} W\n"
            f"Nuovo W/kg: {nuovo_wkg:.2f}\n"
            f"Giudizio: {giudizio}\n"
            f"Tempo salita attuale: {tempo_vecchio:.1f} min\n"
            f"Tempo salita stimato: {tempo_nuovo:.1f} min\n"
            f"Miglioramento: {differenza:.1f} min"
        )

    pdf.output("report_avanzato.pdf")

    with open("report_avanzato.pdf","rb") as f:
        st.download_button("Scarica PDF",f,"report_avanzato.pdf")
