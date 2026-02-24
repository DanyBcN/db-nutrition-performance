import streamlit as st
from PIL import Image
from datetime import date
from fpdf import FPDF
import io
import hashlib

# ------------------------------
# CONFIG
# ------------------------------
st.set_page_config(layout="centered")

# ------------------------------
# LOGO CENTRATO
# ------------------------------
logo = Image.open("logo.png")
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image(logo, width=250)

st.markdown("---")

# ------------------------------
# FUNZIONI
# ------------------------------

def calcola_codice_fiscale(nome, cognome, data_nascita, luogo):
    base = nome + cognome + luogo + str(data_nascita)
    return hashlib.md5(base.encode()).hexdigest()[:16].upper()

def genera_pdf(contenuto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    for riga in contenuto:
        pdf.multi_cell(0, 6, riga)
    return pdf.output(dest="S").encode("latin-1")

# ------------------------------
# INSERIMENTO DATI
# ------------------------------

st.header("Inserimento dati anagrafici")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")
luogo_nascita = st.text_input("Luogo di nascita")
data_nascita = st.date_input(
    "Data di nascita (gg/mm/aaaa)",
    min_value=date(1940,1,1),
    max_value=date.today(),
    format="DD/MM/YYYY"
)

email = st.text_input("Email")
telefono = st.text_input("Telefono")
indirizzo = st.text_input("Indirizzo di residenza")

if nome and cognome and luogo_nascita:
    codice_fiscale = calcola_codice_fiscale(nome, cognome, data_nascita, luogo_nascita)
    st.write(f"Codice Fiscale generato: **{codice_fiscale}**")

today = date.today()
eta = today.year - data_nascita.year - (
    (today.month, today.day) < (data_nascita.month, data_nascita.day)
)

st.write(f"Età: **{eta} anni**")

st.markdown("---")

# ------------------------------
# ANTROPOMETRIA
# ------------------------------

st.header("Composizione corporea")

peso = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, step=0.1)
altezza_cm = st.number_input("Altezza (cm)", min_value=120.0, max_value=220.0, step=0.1)
fm_perc = st.number_input("Massa grassa (%)", min_value=3.0, max_value=50.0, step=0.1)

altezza_m = altezza_cm / 100
bmi = peso / (altezza_m**2) if altezza_m > 0 else 0

if bmi < 18.5:
    bmi_class = "Sottopeso"
elif bmi < 25:
    bmi_class = "Normopeso"
elif bmi < 30:
    bmi_class = "Sovrappeso"
else:
    bmi_class = "Obesità"

st.write(f"BMI: **{bmi:.2f}** ({bmi_class})")

fm_kg = peso * (fm_perc / 100)
massa_magra = peso - fm_kg

st.write(f"Massa grassa: **{fm_kg:.2f} kg**")
st.write(f"Massa magra: **{massa_magra:.2f} kg**")

st.markdown("---")

# ------------------------------
# FTP
# ------------------------------

st.header("Test di Potenza")

tipo_test = st.selectbox(
    "Tipo test",
    ["20 minuti", "2x8 minuti", "FTP disponibile"]
)

ftp = 0

if tipo_test == "20 minuti":
    media20 = st.number_input("Potenza media 20' (W)", min_value=0.0)
    ftp = media20 * 0.95

elif tipo_test == "2x8 minuti":
    p1 = st.number_input("8' prova 1 (W)", min_value=0.0)
    p2 = st.number_input("8' prova 2 (W)", min_value=0.0)
    ftp = ((p1 + p2) / 2) * 0.90

elif tipo_test == "FTP disponibile":
    ftp = st.number_input("FTP (W)", min_value=0.0)

if ftp > 0:
    wkg = ftp / peso
    st.write(f"FTP: **{ftp:.2f} W**")
    st.write(f"W/kg: **{wkg:.2f} W/kg**")

st.markdown("---")

# ------------------------------
# FREQUENZA CARDIACA
# ------------------------------

st.header("Frequenza Cardiaca")

uso_cardio = st.selectbox("Ha indossato il cardio?", ["No", "Sì"])

if uso_cardio == "Sì":
    fc_media = st.number_input("FC media test (bpm)", min_value=0)
    if fc_media > 0:
        st.write(f"FTHR: **{fc_media} bpm**")

st.markdown("---")

# ------------------------------
# PROIEZIONE
# ------------------------------

st.header("Proiezione Strategica")

target_fm = st.number_input("Target massa grassa (%)", min_value=3.0, max_value=20.0, step=0.1)
incremento_ftp = st.number_input("Incremento FTP (%)", min_value=0.0, max_value=50.0, step=0.5)

nuova_fm_kg = massa_magra * (target_fm / (100 - target_fm))
nuovo_peso = massa_magra + nuova_fm_kg
nuova_ftp = ftp * (1 + incremento_ftp / 100)
nuovo_wkg = nuova_ftp / nuovo_peso if nuovo_peso > 0 else 0

st.write(f"Nuovo peso: **{nuovo_peso:.2f} kg**")
st.write(f"Nuova FTP: **{nuova_ftp:.2f} W**")
st.write(f"Nuovo W/kg: **{nuovo_wkg:.2f} W/kg**")

st.markdown("---")

# ------------------------------
# PDF DOWNLOAD
# ------------------------------

if st.button("Genera PDF"):
    contenuto = [
        f"Nome: {nome} {cognome}",
        f"Codice Fiscale: {codice_fiscale}",
        f"Età: {eta}",
        f"Peso: {peso} kg",
        f"Altezza: {altezza_cm} cm",
        f"BMI: {bmi:.2f} ({bmi_class})",
        f"FTP: {ftp:.2f} W",
        f"W/kg: {wkg:.2f}",
        f"Nuovo W/kg: {nuovo_wkg:.2f}"
    ]
    pdf_bytes = genera_pdf(contenuto)

    st.download_button(
        label="Scarica PDF",
        data=pdf_bytes,
        file_name="DB_Nutrition_Performance_Report.pdf",
        mime="application/pdf"
    )
