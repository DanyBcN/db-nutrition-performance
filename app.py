import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd
import numpy as np
from io import BytesIO

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
# DATI ANAGRAFICI
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

peso = st.number_input("Peso (kg)", 30.0, 200.0, step=0.1)
altezza = st.number_input("Altezza (cm)", 100.0, 220.0, step=0.1)
fm = st.number_input("Massa grassa (%)", 3.0, 50.0, step=0.1)

bmi = 0
classificazione = ""

if peso > 0 and altezza > 0:
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

st.markdown("---")

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

st.markdown("---")

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
# PROIEZIONE STRATEGICA
# ======================================================

st.header("Proiezione Strategica")

target_fm = st.number_input("Target Massa Grassa (%)", 3.0, 20.0, step=0.1)
incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0, step=0.1)

nuova_fm_kg = massa_magra * (target_fm/(100-target_fm))
nuovo_peso = massa_magra + nuova_fm_kg
nuova_ftp = ftp * (1 + incremento_ftp/100)
nuovo_wkg = nuova_ftp/nuovo_peso if nuovo_peso>0 else 0

st.write(f"Nuovo peso: {nuovo_peso:.2f} kg")
st.write(f"Nuova FTP: {nuova_ftp:.2f} W")
st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")

st.markdown("---")

## ======================================================
# PDF CLINICO PROFESSIONALE DEFINITIVO
# ======================================================

if st.button("Genera PDF Clinico Professionale"):

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # -------------------------
    # LOGO
    # -------------------------
    try:
        pdf.image("logo.png", x=70, w=70)
        pdf.ln(30)
    except:
        pdf.ln(15)

    # -------------------------
    # TITOLO
    # -------------------------
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "REPORT VALUTAZIONE METABOLICO-FUNZIONALE", ln=True, align="C")
    pdf.ln(8)

    # =====================================================
    # DATI ANAGRAFICI - 2 COLONNE
    # =====================================================

    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(230,230,230)
    pdf.cell(0, 8, "DATI ANAGRAFICI", ln=True, fill=True)

    pdf.set_font("Arial", size=10)

    col_width = 95
    row_height = 8

    pdf.cell(col_width, row_height, f"Nome: {nome} {cognome}", border=1)
    pdf.cell(col_width, row_height, f"Sesso: {sesso}", border=1, ln=True)

    pdf.cell(col_width, row_height, f"Data nascita: {data_nascita.strftime('%d/%m/%Y')}", border=1)
    pdf.cell(col_width, row_height, f"Eta: {eta} anni", border=1, ln=True)

    pdf.cell(col_width, row_height, f"Luogo nascita: {comune} ({provincia})", border=1)
    pdf.cell(col_width, row_height, f"Telefono: {telefono}", border=1, ln=True)

    pdf.cell(190, row_height, f"Email: {email}", border=1, ln=True)
    pdf.cell(190, row_height, f"Indirizzo: {indirizzo}", border=1, ln=True)

    pdf.ln(8)

    # =====================================================
    # ANTROPOMETRIA
    # =====================================================

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "VALUTAZIONE ANTROPOMETRICA", ln=True, fill=True)

    pdf.set_font("Arial", size=10)

    pdf.cell(63, row_height, f"Peso: {peso:.2f} kg", border=1)
    pdf.cell(63, row_height, f"Altezza: {altezza:.0f} cm", border=1)
    pdf.cell(64, row_height, f"BMI: {bmi:.2f}", border=1, ln=True)

    pdf.cell(95, row_height, f"Classificazione: {classificazione}", border=1)
    pdf.cell(95, row_height, f"Massa grassa: {fm_kg:.2f} kg", border=1, ln=True)

    pdf.cell(190, row_height, f"Massa magra: {massa_magra:.2f} kg", border=1, ln=True)

    pdf.ln(8)

    # =====================================================
    # PERFORMANCE
    # =====================================================

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "PERFORMANCE", ln=True, fill=True)

    pdf.set_font("Arial", size=10)

    pdf.cell(95, row_height, f"Metodo FTP: {metodo}", border=1)
    pdf.cell(95, row_height, f"FTP: {ftp:.2f} W", border=1, ln=True)

    pdf.cell(95, row_height, f"W/kg: {wkg:.2f}", border=1)
    pdf.cell(95, row_height, f"FTHR: {fthr:.0f} bpm", border=1, ln=True)

    pdf.ln(8)

    # =====================================================
    # TABELLA ZONE POTENZA
    # =====================================================

    if zone_potenza_df is not None:

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "ZONE DI POTENZA", ln=True, fill=True)

        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, row_height, "Zona", border=1)
        pdf.cell(75, row_height, "Da (W)", border=1)
        pdf.cell(75, row_height, "A (W)", border=1, ln=True)

        pdf.set_font("Arial", size=10)

        for _, row in zone_potenza_df.iterrows():
            pdf.cell(40, row_height, str(row["Zona"]), border=1)
            pdf.cell(75, row_height, str(row["Da (W)"]), border=1)
            pdf.cell(75, row_height, str(row["A (W)"]), border=1, ln=True)

        pdf.ln(8)

    # =====================================================
    # TABELLA ZONE CARDIO
    # =====================================================

    if zone_cardio_df is not None:

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "ZONE CARDIO", ln=True, fill=True)

        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, row_height, "Zona", border=1)
        pdf.cell(75, row_height, "Da (bpm)", border=1)
        pdf.cell(75, row_height, "A (bpm)", border=1, ln=True)

        pdf.set_font("Arial", size=10)

        for _, row in zone_cardio_df.iterrows():
            pdf.cell(40, row_height, str(row["Zona"]), border=1)
            pdf.cell(75, row_height, str(row["Da (bpm)"]), border=1)
            pdf.cell(75, row_height, str(row["A (bpm)"]), border=1, ln=True)

        pdf.ln(8)

    # =====================================================
    # PROIEZIONE
    # =====================================================

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "PROIEZIONE STRATEGICA", ln=True, fill=True)

    pdf.set_font("Arial", size=10)

    pdf.cell(95, row_height, f"Nuovo peso: {nuovo_peso:.2f} kg", border=1)
    pdf.cell(95, row_height, f"Nuova FTP: {nuova_ftp:.2f} W", border=1, ln=True)

    pdf.cell(190, row_height, f"Nuovo W/kg: {nuovo_wkg:.2f}", border=1, ln=True)

    # Footer
    pdf.set_y(-12)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 6, f"Pagina {pdf.page_no()}", align="C")

    # Output Cloud Safe
    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    st.download_button(
        "Scarica PDF Clinico Professionale",
        data=pdf_bytes,
        file_name="report_clinico_professionale.pdf",
        mime="application/pdf"
    )
