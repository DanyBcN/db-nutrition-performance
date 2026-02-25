import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd

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
# DATI ANAGRAFICI (RIDOTTI)
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

ftp = st.number_input("FTP (W)", 0.0)
wkg = ftp / peso if peso > 0 else 0

st.write(f"W/kg: {wkg:.2f}")

st.markdown("---")

# ======================================================
# FTHR
# ======================================================

st.header("Frequenza Cardiaca")

fthr = st.number_input("FTHR (bpm)", 0.0)

# ======================================================
# ZONE POTENZA CON DESCRIZIONE
# ======================================================

zone_df = pd.DataFrame()
zone_hr_df = pd.DataFrame()

if ftp > 0:

    zone = [
        ("Z1 Recupero attivo",0.00,0.55),
        ("Z2 Fondo aerobico",0.56,0.75),
        ("Z3 Tempo",0.76,0.90),
        ("Z4 Soglia",0.91,1.05),
        ("Z5 VO2max",1.06,1.20),
        ("Z6 Capacità anaerobica",1.21,1.50),
        ("Z7 Neuromuscolare",1.51,2.00),
    ]

    zone_df = pd.DataFrame(
        [[z, round(a*ftp), round(b*ftp)] for z,a,b in zone],
        columns=["Zona e funzione","Da (W)","A (W)"]
    )

    st.subheader("Zone Potenza")
    st.table(zone_df)

# ======================================================
# ZONE CARDIO CON DESCRIZIONE
# ======================================================

if fthr > 0:

    zone_hr = [
        ("Z1 Recupero",0.81,0.89),
        ("Z2 Aerobico base",0.90,0.93),
        ("Z3 Tempo",0.94,0.99),
        ("Z4 Soglia",1.00,1.05),
        ("Z5 Alta intensità",1.06,1.15),
    ]

    zone_hr_df = pd.DataFrame(
        [[z, round(a*fthr), round(b*fthr)] for z,a,b in zone_hr],
        columns=["Zona e funzione","Da (bpm)","A (bpm)"]
    )

    st.subheader("Zone Cardio")
    st.table(zone_hr_df)

st.markdown("---")

# ======================================================
# PDF
# ======================================================

if st.button("Genera PDF"):

    class PDF(FPDF):

        def header(self):
            self.set_font("Arial","B",16)
            self.cell(0,10,"REPORT PERFORMANCE",0,1,"C")
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
        f"Data di nascita: {data_nascita.strftime('%d %m %Y')}"
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

    pdf.output("report.pdf")

    with open("report.pdf","rb") as f:
        st.download_button("Scarica PDF",f,"report.pdf")
