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
p20 = 0
p8 = 0
ultimo = 0

if metodo == "Immissione diretta":
    ftp = st.number_input("FTP (W)", 0.0)

elif metodo == "Test 20 minuti":
    p20 = st.number_input("Media 20 min (W)", 0.0)
    ftp = p20 * 0.95

elif metodo == "Test 8 minuti":
    p8 = st.number_input("Media 8 min (W)", 0.0)
    ftp = p8 * 0.90

elif metodo == "Ramp test":
    ultimo = st.number_input("Ultimo step completato (W)", 0.0)
    ftp = ultimo * 0.75

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
        columns=["Zona","Da W","A W"]
    )

    st.subheader("Zone Potenza")
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
        columns=["Zona","Da bpm","A bpm"]
    )

    st.subheader("Zone Cardio")
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

    st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")
    st.write(f"Giudizio: {giudizio}")

    # Simulazione salita
    lunghezza = 5000
    pendenza = 0.06
    g = 9.81

    def tempo_salita(potenza, peso):
        forza = peso * g * pendenza
        velocita = potenza / forza
        tempo = lunghezza / velocita
        return tempo / 60

    tempo_vecchio = tempo_salita(ftp, peso)
    tempo_nuovo = tempo_salita(nuova_ftp, nuovo_peso)

    st.subheader("Simulazione salita 5 km al 6%")
    st.write(f"Tempo attuale: {tempo_vecchio:.1f} min")
    st.write(f"Tempo stimato: {tempo_nuovo:.1f} min")
    st.write(f"Guadagno: {(tempo_vecchio-tempo_nuovo):.1f} min")

st.markdown("---")

# ======================================================
# PDF COMPLETO
# ======================================================

if st.button("Genera PDF Completo"):

    def safe_text(text):
        return text.encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,"REPORT PERFORMANCE COMPLETO",0,1,"C")
    pdf.ln(5)

    pdf.set_font("Arial","",11)

    testo = f"""
Nome: {nome}
Cognome: {cognome}
Data di nascita: {data_nascita.strftime('%d %m %Y')}
Eta: {eta} anni

Peso: {peso:.1f} kg
Altezza: {altezza:.1f} cm
BMI: {bmi:.2f}
Massa grassa: {fm:.1f}% ({fm_kg:.2f} kg)
Massa magra: {massa_magra:.2f} kg

Metodo FTP: {metodo}
FTP: {ftp:.2f} W
W/kg: {wkg:.2f}
"""

    pdf.multi_cell(0,7,safe_text(testo))

    if not zone_df.empty:
        pdf.ln(3)
        pdf.multi_cell(0,7,"ZONE POTENZA")
        for _, row in zone_df.iterrows():
            pdf.multi_cell(0,6,safe_text(f"{row[0]}: {row[1]} - {row[2]} W"))

    if not zone_hr_df.empty:
        pdf.ln(3)
        pdf.multi_cell(0,7,"ZONE CARDIO")
        for _, row in zone_hr_df.iterrows():
            pdf.multi_cell(0,6,safe_text(f"{row[0]}: {row[1]} - {row[2]} bpm"))

    if nuovo_peso > 0 and ftp > 0:
        delta_ftp = nuova_ftp - ftp
        delta_tempo = tempo_vecchio - tempo_nuovo

        testo_proiezione = f"""
PROIEZIONE

Giudizio: {giudizio}

Peso da {peso:.1f} kg a {nuovo_peso:.1f} kg
FTP da {ftp:.1f} W a {nuova_ftp:.1f} W
W/kg da {wkg:.2f} a {nuovo_wkg:.2f}

Salita 5 km 6%:
Tempo da {tempo_vecchio:.1f} min a {tempo_nuovo:.1f} min
Miglioramento: {delta_tempo:.1f} min
"""

        pdf.multi_cell(0,7,safe_text(testo_proiezione))

    pdf.output("report_performance_completo.pdf")

    with open("report_performance_completo.pdf","rb") as f:
        st.download_button(
            "Scarica PDF Completo",
            f,
            "report_performance_completo.pdf"
        )
