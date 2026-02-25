import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import math
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# ======================================================
# LOGO IN ALTO (NO DISTORSIONE)
# ======================================================

col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("logo.png", width=300)

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

st.write(f"BMI: {bmi:.2f}")
st.write(f"Classificazione: {categoria_bmi}")
st.write(f"Massa grassa: {fm_kg:.2f} kg")
st.write(f"Massa magra: {massa_magra:.2f} kg")

# ======================================================
# GRAFICO BMI
# ======================================================

fig, ax = plt.subplots()

ax.set_xlim(15, 40)
ax.set_ylim(0, 1)

ax.axvspan(15, 18.5)
ax.axvspan(18.5, 25)
ax.axvspan(25, 30)
ax.axvspan(30, 40)

ax.axvline(bmi)

ax.set_yticks([])
ax.set_xlabel("BMI")

st.pyplot(fig)

fig.savefig("bmi_chart.png", bbox_inches="tight")

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

st.markdown("---")

# ======================================================
# GENERAZIONE PDF
# ======================================================

if st.button("Genera PDF Professionale"):

    def safe(text):
        return text.encode("latin-1","replace").decode("latin-1")

    class PDF(FPDF):

        def header(self):
            try:
                self.image("logo.png", 60, 8, 90)
                self.ln(35)
            except:
                self.ln(20)

            self.set_font("Arial","B",18)
            self.cell(0,10,"REPORT PERFORMANCE",0,1,"C")
            self.ln(5)

        def section_title(self, title):
            self.set_font("Arial","B",12)
            self.cell(0,8,title,0,1)
            self.ln(3)

        def normal(self, text):
            self.set_font("Arial","",10)
            self.multi_cell(0,6,safe(text))
            self.ln(3)

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # DATI
    pdf.section_title("Dati Anagrafici")
    pdf.normal(
        f"Nome: {nome}\n"
        f"Cognome: {cognome}\n"
        f"Data di nascita: {data_nascita.strftime('%d/%m/%Y')}\n"
        f"Eta: {eta} anni"
    )

    # ANTROPOMETRIA
    pdf.section_title("Antropometria")
    pdf.normal(
        f"Peso: {peso:.1f} kg\n"
        f"Altezza: {altezza:.1f} cm\n"
        f"BMI: {bmi:.2f}\n"
        f"Classificazione: {categoria_bmi}\n"
        f"Massa grassa: {fm:.1f}% ({fm_kg:.2f} kg)\n"
        f"Massa magra: {massa_magra:.2f} kg"
    )

    pdf.section_title("Grafico BMI")
    pdf.image("bmi_chart.png", x=35, w=140)

    pdf.output("report_performance_professionale.pdf")

    with open("report_performance_professionale.pdf","rb") as f:
        st.download_button(
            "Scarica PDF Professionale",
            f,
            "report_performance_professionale.pdf"
        )
