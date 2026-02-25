import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd
import os

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

altezza_m = altezza / 100
bmi = peso / (altezza_m**2) if altezza_m > 0 else 0

if bmi < 18.5:
    classificazione = "Sottopeso"
elif bmi < 25:
    classificazione = "Normopeso"
elif bmi < 30:
    classificazione = "Sovrappeso"
else:
    classificazione = "Obesità"

fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg

st.write(f"BMI: {bmi:.2f} ({classificazione})")
st.write(f"Massa grassa: {fm_kg:.2f} kg")
st.write(f"Massa magra: {massa_magra:.2f} kg")

st.markdown("---")

# ======================================================
# FTP
# ======================================================

st.header("Calcolo FTP")

metodo = st.selectbox(
    "Metodo calcolo FTP",
    ["Immissione diretta","Test 20 minuti","Test 8 minuti","Ramp test"]
)

ftp = 0

if metodo == "Immissione diretta":
    ftp = st.number_input("FTP (W)", 0.0)
elif metodo == "Test 20 minuti":
    ftp = st.number_input("Media 20' (W)", 0.0) * 0.95
elif metodo == "Test 8 minuti":
    ftp = st.number_input("Media 8' (W)", 0.0) * 0.90
elif metodo == "Ramp test":
    ftp = st.number_input("Ultimo step (W)", 0.0) * 0.75

wkg = ftp / peso if peso > 0 else 0

st.write(f"FTP: {ftp:.2f} W")
st.write(f"W/kg: {wkg:.2f}")

st.markdown("---")

# ======================================================
# FTHR
# ======================================================

st.header("Frequenza Cardiaca")

fthr_input = st.number_input("FTHR (bpm)", 0.0)

if fthr_input > 0:
    fthr = fthr_input
else:
    fthr = 0.95 * (220 - eta)

st.write(f"FTHR: {fthr:.0f} bpm")

# ======================================================
# ZONE
# ======================================================

zone_df = pd.DataFrame()
zone_hr_df = pd.DataFrame()

if ftp > 0:
    zone = [
        ("Z1",0.00,0.55),
        ("Z2",0.56,0.75),
        ("Z3",0.76,0.90),
        ("Z4",0.91,1.05),
        ("Z5",1.06,1.20),
        ("Z6",1.21,1.50),
        ("Z7",1.51,2.00),
    ]

    zone_df = pd.DataFrame(
        [[z, round(a*ftp), round(b*ftp)] for z,a,b in zone],
        columns=["Zona","Da (W)","A (W)"]
    )

    st.table(zone_df)

if fthr > 0:
    zone_hr = [
        ("Z1",0.81,0.89),
        ("Z2",0.90,0.93),
        ("Z3",0.94,0.99),
        ("Z4",1.00,1.05),
        ("Z5",1.06,1.15)
    ]

    zone_hr_df = pd.DataFrame(
        [[z, round(a*fthr), round(b*fthr)] for z,a,b in zone_hr],
        columns=["Zona","Da (bpm)","A (bpm)"]
    )

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
# PDF DEFINITIVO COMPLETO
# ======================================================

if st.button("Genera PDF Completo"):

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
        f"Comune di nascita: {comune}\n"
        f"Provincia: {provincia}\n"
        f"Email: {email}\n"
        f"Telefono: {telefono}\n"
        f"Indirizzo: {indirizzo}"
    )

    pdf.section("ANTROPOMETRIA")
    pdf.normal(
        f"Peso: {peso:.1f} kg\n"
        f"Altezza: {altezza:.1f} cm\n"
        f"BMI: {bmi:.2f} ({classificazione})\n"
        f"Massa grassa: {fm:.1f}% ({fm_kg:.2f} kg)\n"
        f"Massa magra: {massa_magra:.2f} kg"
    )

    pdf.section("PERFORMANCE")
    pdf.normal(
        f"FTP: {ftp:.2f} W\n"
        f"W/kg: {wkg:.2f}\n"
        f"FTHR: {fthr:.0f} bpm"
    )

    pdf.section("ZONE POTENZA")
    pdf.table(zone_df)

    pdf.section("ZONE CARDIO")
    pdf.table(zone_hr_df)

    pdf.section("PROIEZIONE E INTERPRETAZIONE")

    delta_wkg = nuovo_wkg - wkg
    delta_ftp = nuova_ftp - ftp

    pdf.normal(
        f"Con un peso che passa da {peso:.1f} kg a {nuovo_peso:.1f} kg "
        f"e una riduzione della massa grassa dal {fm:.1f}% al {target_fm:.1f}%, "
        f"il rapporto W/kg migliorerebbe da {wkg:.2f} a {nuovo_wkg:.2f} "
        f"(+{delta_wkg:.2f}).\n\n"
        f"Con un incremento della FTP da {ftp:.1f} W a {nuova_ftp:.1f} W "
        f"si avrebbe un miglioramento assoluto di {delta_ftp:.1f} W."
    )

    pdf.output("report_completo.pdf")

    with open("report_completo.pdf","rb") as f:
        st.download_button("Scarica PDF Completo",f,"report_completo.pdf")
