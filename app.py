import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import math

st.set_page_config(layout="wide")

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
# CALCOLO FTP
# ======================================================

st.header("Calcolo FTP")

metodo = st.selectbox(
    "Metodo FTP",
    ["Immissione diretta","Test 20 minuti","Test 8 minuti","Ramp test"]
)

ftp = 0
valore_test = 0

if metodo == "Immissione diretta":
    ftp = st.number_input("FTP (W)", 0.0)
    valore_test = ftp

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

st.markdown("---")

# ======================================================
# ZONE POTENZA
# ======================================================

zone_df = pd.DataFrame()

if ftp > 0:

    zone = [
        ("Z1 Recovery attivo",0.00,0.55),
        ("Z2 Fondo aerobico",0.56,0.75),
        ("Z3 Tempo",0.76,0.90),
        ("Z4 Soglia lattato",0.91,1.05),
        ("Z5 VO2max",1.06,1.20),
        ("Z6 Capacita anaerobica",1.21,1.50),
        ("Z7 Neuromuscolare",1.51,2.00),
    ]

    zone_df = pd.DataFrame(
        [[z, round(a*ftp), round(b*ftp)] for z,a,b in zone],
        columns=["Zona","Da (W)","A (W)"]
    )

    st.table(zone_df)

# ======================================================
# ZONE CARDIO
# ======================================================

st.header("Frequenza Cardiaca")

fthr = st.number_input("FTHR (bpm)", 0.0)

zone_hr_df = pd.DataFrame()

if fthr > 0:

    zone_hr = [
        ("Z1 Recupero",0.81,0.89),
        ("Z2 Aerobico base",0.90,0.93),
        ("Z3 Tempo",0.94,0.99),
        ("Z4 Soglia",1.00,1.05),
        ("Z5 Alta intensita",1.06,1.15),
    ]

    zone_hr_df = pd.DataFrame(
        [[z, round(a*fthr), round(b*fthr)] for z,a,b in zone_hr],
        columns=["Zona","Da (bpm)","A (bpm)"]
    )

    st.table(zone_hr_df)

st.markdown("---")

# ======================================================
# PROIEZIONE PERFORMANCE
# ======================================================

st.header("Proiezione Performance")

nuovo_peso = st.number_input("Nuovo peso target (kg)", 0.0)
incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0)

nuova_ftp = 0
nuovo_wkg = 0
tempo_vecchio = 0
tempo_nuovo = 0
giudizio = ""

if nuovo_peso > 0 and ftp > 0:

    nuova_ftp = ftp * (1 + incremento_ftp/100)
    nuovo_wkg = nuova_ftp / nuovo_peso
    delta_wkg = nuovo_wkg - wkg

    if delta_wkg > 0.3:
        giudizio = "Miglioramento significativo"
    elif delta_wkg > 0.1:
        giudizio = "Miglioramento moderato"
    else:
        giudizio = "Miglioramento lieve"

    lunghezza = 5000
    pendenza = 0.06
    g = 9.81

    def tempo_salita(potenza, peso):
        forza = peso * g * pendenza
        velocita = potenza / forza
        return (lunghezza / velocita) / 60

    tempo_vecchio = tempo_salita(ftp, peso)
    tempo_nuovo = tempo_salita(nuova_ftp, nuovo_peso)

    st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")
    st.write(f"Giudizio: {giudizio}")
    st.write(f"Salita 5 km 6%: da {tempo_vecchio:.1f} min a {tempo_nuovo:.1f} min")

st.markdown("---")

# ======================================================
# PDF COMPLETO DEFINITIVO
# ======================================================

if st.button("Genera PDF Completo"):

    def safe(text):
        return text.encode("latin-1","replace").decode("latin-1")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,"REPORT PERFORMANCE COMPLETO",0,1,"C")
    pdf.ln(5)

    pdf.set_font("Arial","",11)

    pdf.multi_cell(0,7,safe(
        f"Nome: {nome}\n"
        f"Cognome: {cognome}\n"
        f"Data di nascita: {data_nascita.strftime('%d %m %Y')}\n"
        f"Eta: {eta} anni\n\n"
        f"Peso: {peso:.1f} kg\n"
        f"Altezza: {altezza:.1f} cm\n"
        f"BMI: {bmi:.2f}\n"
        f"Massa grassa: {fm:.1f}% ({fm_kg:.2f} kg)\n"
        f"Massa magra: {massa_magra:.2f} kg\n\n"
        f"Metodo FTP: {metodo}\n"
        f"Valore test inserito: {valore_test:.2f} W\n"
        f"FTP calcolata: {ftp:.2f} W\n"
        f"W/kg: {wkg:.2f}\n"
    ))

    # Tabelle FTP
    if not zone_df.empty:
        pdf.ln(4)
        pdf.set_font("Arial","B",12)
        pdf.cell(0,8,"Zone Potenza",0,1)
        pdf.set_font("Arial","",10)

        for _, row in zone_df.iterrows():
            pdf.multi_cell(0,6,safe(
                f"{row['Zona']}: {row['Da (W)']} - {row['A (W)']} W"
            ))

    # Tabelle Cardio
    if not zone_hr_df.empty:
        pdf.ln(4)
        pdf.set_font("Arial","B",12)
        pdf.cell(0,8,"Zone Cardio",0,1)
        pdf.set_font("Arial","",10)

        for _, row in zone_hr_df.iterrows():
            pdf.multi_cell(0,6,safe(
                f"{row['Zona']}: {row['Da (bpm)']} - {row['A (bpm)']} bpm"
            ))

    # Proiezione
    if nuovo_peso > 0 and ftp > 0:

        delta_ftp = nuova_ftp - ftp
        delta_tempo = tempo_vecchio - tempo_nuovo

        pdf.ln(4)
        pdf.set_font("Arial","B",12)
        pdf.cell(0,8,"Proiezione e Miglioramento",0,1)
        pdf.set_font("Arial","",10)

        pdf.multi_cell(0,7,safe(
            f"Giudizio: {giudizio}\n\n"
            f"Peso da {peso:.1f} kg a {nuovo_peso:.1f} kg\n"
            f"FTP da {ftp:.1f} W a {nuova_ftp:.1f} W (+{delta_ftp:.1f} W)\n"
            f"W/kg da {wkg:.2f} a {nuovo_wkg:.2f}\n\n"
            f"Salita 5 km 6%:\n"
            f"Tempo da {tempo_vecchio:.1f} min a {tempo_nuovo:.1f} min\n"
            f"Miglioramento stimato: {delta_tempo:.1f} min"
        ))

    pdf.output("report_performance_completo.pdf")

    with open("report_performance_completo.pdf","rb") as f:
        st.download_button(
            "Scarica PDF Completo",
            f,
            "report_performance_completo.pdf"
        )
