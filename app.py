import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd
import matplotlib.pyplot as plt
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
# DATI ANAGRAFICI
# ======================================================

st.header("Dati Anagrafici")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")
sesso = st.selectbox("Sesso", ["M", "F"])
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

# Formato italiano: gg mm aaaa
giorno = f"{data_nascita.day:02d}"
mese = f"{data_nascita.month:02d}"
anno = data_nascita.year
data_nascita_it = f"{giorno} {mese} {anno}"

eta = date.today().year - data_nascita.year - (
    (date.today().month, date.today().day) <
    (data_nascita.month, data_nascita.day)
)

st.write(f"Data di nascita: {data_nascita_it}")
st.write(f"Età: {eta} anni")

st.markdown("---")

# ======================================================
# VALUTAZIONE ANTROPOMETRICA
# ======================================================

st.header("Valutazione Antropometrica")

peso = st.number_input("Peso (kg)", 30.0, 200.0, step=0.1)
altezza = st.number_input("Altezza (cm)", 100.0, 220.0, step=0.1)
fm = st.number_input("Massa grassa (%)", 3.0, 50.0, step=0.1)

altezza_m = altezza / 100
bmi = peso / (altezza_m**2) if altezza_m > 0 else 0
fm_kg = peso * (fm / 100)
massa_magra = peso - fm_kg

if bmi < 18.5:
    classificazione = "Sottopeso"
elif bmi < 25:
    classificazione = "Normopeso"
elif bmi < 30:
    classificazione = "Sovrappeso"
else:
    classificazione = "Obesità"

st.write(f"BMI: {bmi:.2f} ({classificazione})")
st.write(f"Massa grassa: {fm_kg:.2f} kg")
st.write(f"Massa magra: {massa_magra:.2f} kg")

st.markdown("---")

# ======================================================
# CALCOLO FTP
# ======================================================

st.header("Calcolo FTP")

metodo = st.selectbox(
    "Metodo",
    ["Immissione diretta", "Test 20 minuti",
     "Test 8 minuti", "Ramp test"]
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
    step = st.number_input("Ultimo step (W)", 0.0)
    ftp = step * 0.75

wkg = ftp / peso if peso > 0 else 0

st.write(f"FTP: {ftp:.2f} W")
st.write(f"W/kg: {wkg:.2f}")

st.markdown("---")

# ======================================================
# FREQUENZA CARDIACA
# ======================================================

st.header("Frequenza Cardiaca")

fthr_input = st.number_input("FTHR (bpm)", 0.0)
fthr = fthr_input if fthr_input > 0 else 0.95 * (220 - eta)

st.write(f"FTHR: {fthr:.0f} bpm")

# ======================================================
# ZONE POTENZA
# ======================================================

st.subheader("Zone Potenza")

zone = [
    ("Z1", 0.00, 0.55),
    ("Z2", 0.56, 0.75),
    ("Z3", 0.76, 0.90),
    ("Z4", 0.91, 1.05),
    ("Z5", 1.06, 1.20),
    ("Z6", 1.21, 1.50),
    ("Z7", 1.51, 2.00)
]

zone_df = pd.DataFrame(
    [[z, round(a*ftp), round(b*ftp)] for z,a,b in zone],
    columns=["Zona","Da (W)","A (W)"]
)

st.table(zone_df)

# ======================================================
# ZONE CARDIO
# ======================================================

st.subheader("Zone Cardio")

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
# PROIEZIONE STRATEGICA
# ======================================================

st.header("Proiezione Strategica")

target_fm = st.number_input("Target Massa Grassa (%)", 3.0, 20.0, step=0.1)
incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0, step=0.1)

if target_fm < 100:
    nuova_fm_kg = massa_magra * (target_fm/(100-target_fm))
    nuovo_peso = massa_magra + nuova_fm_kg
else:
    nuovo_peso = peso

nuova_ftp = ftp * (1 + incremento_ftp/100)
nuovo_wkg = nuova_ftp / nuovo_peso if nuovo_peso > 0 else 0

st.write(f"Nuovo peso: {nuovo_peso:.2f} kg")
st.write(f"Nuova FTP: {nuova_ftp:.2f} W")
st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")

st.markdown("---")

# ======================================================
# PDF REPORT
# ======================================================

if st.button("Genera PDF Performance"):

    class PDF(FPDF):

        def header(self):
            try:
                self.image("logo.png", 75, 8, 60)
                self.ln(30)
            except:
                self.ln(20)

            self.set_font("Arial","B",18)
            self.cell(0,10,"PERFORMANCE REPORT",0,1,"C")
            self.ln(5)

        def section_title(self, title):
            self.set_font("Arial","B",13)
            self.cell(0,8,title,0,1)
            self.ln(2)

        def normal_text(self, text):
            self.set_font("Arial","",10)
            self.multi_cell(0,6,text)

        def table(self, dataframe):
            self.set_font("Arial","B",9)
            col_width = self.w / (len(dataframe.columns) + 1)

            for col in dataframe.columns:
                self.cell(col_width,8,col,1,0,"C")
            self.ln()

            self.set_font("Arial","",9)
            for row in dataframe.values:
                for item in row:
                    self.cell(col_width,8,str(item),1,0,"C")
                self.ln()

        def footer(self):
            self.set_y(-12)
            self.set_font("Arial","I",8)
            self.cell(0,5,f"Pagina {self.page_no()}",0,0,"C")


    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ======================================================
    # ANAGRAFICA
    # ======================================================

    pdf.section_title("DATI ANAGRAFICI")

    pdf.normal_text(
        f"Nome: {nome}\n"
        f"Cognome: {cognome}\n"
        f"Data di nascita: {data_nascita_it}\n"
        f"Sesso: {sesso}\n"
        f"Email: {email}\n"
        f"Telefono: {telefono}\n"
        f"Indirizzo: {indirizzo}"
    )

    pdf.ln(4)

    # ======================================================
    # ANTROPOMETRIA
    # ======================================================

    pdf.section_title("VALUTAZIONE ANTROPOMETRICA")

    pdf.normal_text(
        f"Peso: {peso:.1f} kg\n"
        f"Altezza: {altezza:.1f} cm\n"
        f"BMI: {bmi:.2f} ({classificazione})\n"
        f"Massa Grassa: {fm:.1f}% ({fm_kg:.2f} kg)\n"
        f"Massa Magra: {massa_magra:.2f} kg"
    )

    pdf.ln(4)

    # ======================================================
    # PERFORMANCE
    # ======================================================

    pdf.section_title("PARAMETRI PERFORMANCE")

    pdf.normal_text(
        f"FTP: {ftp:.0f} W\n"
        f"W/kg: {wkg:.2f}\n"
        f"FTHR: {fthr:.0f} bpm"
    )

    pdf.ln(4)

    # ======================================================
    # TABELLE
    # ======================================================

    pdf.section_title("ZONE POTENZA (FTP)")
    pdf.table(zone_df)

    pdf.ln(5)

    pdf.section_title("ZONE CARDIO (FTHR)")
    pdf.table(zone_hr_df)

    pdf.ln(5)

    # ======================================================
    # GRAFICO
    # ======================================================

    plt.figure(figsize=(6,3))
    plt.bar(zone_df["Zona"], zone_df["A (W)"])
    plt.title("Distribuzione Zone FTP")
    plt.tight_layout()
    plt.savefig("chart.png")
    plt.close()

    pdf.section_title("DISTRIBUZIONE ZONE FTP")
    pdf.image("chart.png", x=pdf.l_margin, w=170)
    os.remove("chart.png")

    # ======================================================
    # OUTPUT
    # ======================================================

    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    st.download_button(
        "Scarica PDF Completo",
        data=pdf_bytes,
        file_name="report_performance_completo.pdf",
        mime="application/pdf"
    )
