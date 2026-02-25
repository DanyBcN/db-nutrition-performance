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

zone_df = pd.DataFrame()
zone_hr_df = pd.DataFrame()

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

    zone_df = pd.DataFrame(dati,columns=["Zona","Da (W)","A (W)"])
    st.table(zone_df)

# ======================================================
# ZONE CARDIO
# ======================================================

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

    zone_hr_df = pd.DataFrame(dati_hr,columns=["Zona","Da (bpm)","A (bpm)"])
    st.table(zone_hr_df)

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
# PDF COMPLETO PROFESSIONALE
# ======================================================

if st.button("Genera PDF"):

    class PDF(FPDF):

        def header(self):
            self.set_font("Arial","B",16)
            self.cell(0,10,"REPORT VALUTAZIONE PERFORMANCE",0,1,"C")
            self.ln(5)

        def section(self,title):
            self.set_font("Arial","B",12)
            self.cell(0,8,title,0,1)
            self.ln(2)

        def normal(self,text):
            self.set_font("Arial","",10)
            self.multi_cell(0,6,text)

        def table(self,df):
            if df.empty:
                return
            self.set_font("Arial","B",9)
            col_width = self.w/(len(df.columns)+1)
            for col in df.columns:
                self.cell(col_width,8,col,1,0,"C")
            self.ln()
            self.set_font("Arial","",9)
            for row in df.values:
                for item in row:
                    self.cell(col_width,8,str(item),1,0,"C")
                self.ln()

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.section("DATI ANAGRAFICI")
    pdf.normal(
        f"Nome: {nome}\n"
        f"Cognome: {cognome}\n"
        f"Sesso: {sesso}\n"
        f"Data di nascita: {data_nascita.strftime('%d %m %Y')}\n"
        f"Email: {email}\n"
        f"Telefono: {telefono}\n"
        f"Indirizzo: {indirizzo}"
    )

    pdf.ln(4)

    pdf.section("ANTROPOMETRIA")
    pdf.normal(
        f"Peso: {peso:.1f} kg\n"
        f"Altezza: {altezza:.1f} cm\n"
        f"BMI: {bmi:.2f} ({classificazione})\n"
        f"Massa grassa: {fm:.1f}% ({fm_kg:.2f} kg)\n"
        f"Massa magra: {massa_magra:.2f} kg"
    )

    pdf.ln(4)

    pdf.section("PERFORMANCE")
    pdf.normal(
        f"FTP: {ftp:.2f} W\n"
        f"W/kg: {wkg:.2f}\n"
        f"FTHR: {fthr:.0f} bpm"
    )

    pdf.ln(4)

    pdf.section("ZONE POTENZA")
    pdf.table(zone_df)

    pdf.ln(4)

    pdf.section("ZONE CARDIO")
    pdf.table(zone_hr_df)

    pdf.ln(4)

    pdf.section("PROIEZIONE")
    pdf.normal(
        f"Nuovo peso stimato: {nuovo_peso:.2f} kg\n"
        f"Nuova FTP stimata: {nuova_ftp:.2f} W\n"
        f"Nuovo W/kg: {nuovo_wkg:.2f}"
    )

    pdf.output("report.pdf")

    with open("report.pdf","rb") as f:
        st.download_button("Scarica PDF",f,"report.pdf")
