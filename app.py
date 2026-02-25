import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

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
# INIZIALIZZAZIONE
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
giudizio_atleta = ""
classe_sarcopenia = ""

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

sesso = st.selectbox("Sesso biologico", ["Maschio", "Femmina"])
resistenza = st.number_input("Resistenza BIA (ohm)", 0.0)

# ======================================================
# PAL
# ======================================================

pal_dict = {
    "Sedentario (1.2)": 1.2,
    "Leggero (1.375)": 1.375,
    "Moderato (1.55)": 1.55,
    "Intenso (1.725)": 1.725,
    "Molto intenso (1.9)": 1.9
}

pal_label = st.selectbox("Livello attività (PAL)", list(pal_dict.keys()))
pal = pal_dict[pal_label]

# ======================================================
# CALCOLI ANTROPOMETRICI
# ======================================================

altezza_m = altezza / 100
bmi = peso / (altezza_m**2)
fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg

# SMM Janssen
sesso_num = 1 if sesso == "Maschio" else 0

if resistenza > 0:
    smm = (0.401 * (altezza**2 / resistenza)) + (3.825 * sesso_num) - (0.071 * eta) + 5.102
else:
    smm = 0

smi = smm / (altezza_m**2) if altezza_m > 0 else 0

# Cutoff sarcopenia
if sesso == "Maschio":
    classe_sarcopenia = "Sarcopenia probabile" if smi < 7 else "Normale"
else:
    classe_sarcopenia = "Sarcopenia probabile" if smi < 5.5 else "Normale"

# BMR
if sesso == "Maschio":
    bmr = (10 * peso) + (6.25 * altezza) - (5 * eta) + 5
else:
    bmr = (10 * peso) + (6.25 * altezza) - (5 * eta) - 161

tdee = bmr * pal

# BMI categoria OMS
if bmi < 18.5:
    categoria_bmi = "Sottopeso"
elif bmi < 25:
    categoria_bmi = "Normopeso"
elif bmi < 30:
    categoria_bmi = "Sovrappeso"
else:
    categoria_bmi = "Obesità"

# ======================================================
# OUTPUT ANTROPOMETRIA
# ======================================================

st.write(f"BMI: {bmi:.2f} ({categoria_bmi})")
st.write(f"Massa grassa: {fm_kg:.2f} kg")
st.write(f"Massa magra: {massa_magra:.2f} kg")

if smm > 0:
    st.write(f"SMM (Janssen): {smm:.2f} kg")
    st.write(f"SMI: {smi:.2f} kg/m² ({classe_sarcopenia})")

st.write(f"BMR: {bmr:.0f} kcal/die")
st.write(f"TDEE stimato: {tdee:.0f} kcal/die")

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
# PDF
# ======================================================

if st.button("Genera PDF Professionale"):

    def safe(text):
        return text.encode("latin-1", "replace").decode("latin-1")

    class PDF(FPDF):
        def header(self):
            try:
                self.image("logo.png", 75, 8, 60)
                self.ln(30)
            except:
                self.ln(20)
            self.set_font("Arial", "B", 16)
            self.cell(0, 10, "REPORT PERFORMANCE", 0, 1, "C")
            self.ln(5)

        def section(self, title):
            self.set_font("Arial", "B", 12)
            self.cell(0, 8, title, 0, 1)
            self.ln(3)

        def normal(self, text):
            self.set_font("Arial", "", 10)
            self.multi_cell(0, 6, safe(text))
            self.ln(3)

    pdf = PDF()
    pdf.add_page()

    pdf.section("Dati Anagrafici")
    pdf.normal(
        f"Nome: {nome}\n"
        f"Cognome: {cognome}\n"
        f"Data di nascita: {data_nascita.strftime('%d/%m/%Y')}\n"
        f"Eta: {eta} anni"
    )

    pdf.section("Antropometria Completa")
    pdf.normal(
        f"Peso: {peso:.1f} kg\n"
        f"Altezza: {altezza:.1f} cm\n"
        f"BMI: {bmi:.2f} ({categoria_bmi})\n"
        f"Massa grassa: {fm:.1f}% ({fm_kg:.2f} kg)\n"
        f"Massa magra: {massa_magra:.2f} kg\n"
        f"SMM (Janssen): {smm:.2f} kg\n"
        f"SMI: {smi:.2f} kg/m² ({classe_sarcopenia})\n"
        f"BMR: {bmr:.0f} kcal/die\n"
        f"TDEE: {tdee:.0f} kcal/die\n"
        f"FTP: {ftp:.2f} W\n"
        f"W/kg: {wkg:.2f}"
    )

    pdf.output("report_performance_professionale.pdf")

    with open("report_performance_professionale.pdf", "rb") as f:
        st.download_button(
            "Scarica PDF Professionale",
            f,
            "report_performance_professionale.pdf"
        )
