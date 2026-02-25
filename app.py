import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd
from codicefiscale import codicefiscale

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
# GENERAZIONE CODICE FISCALE UFFICIALE
# ======================================================

def genera_cf(nome, cognome, data, sesso, comune):
    try:
        cf = codicefiscale.encode(
            lastname=cognome,
            firstname=nome,
            gender=sesso,
            birthdate=data,
            birthplace=comune
        )
        return cf
    except:
        return "Comune non valido"

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

cf = ""
if nome and cognome and comune:
    cf = genera_cf(nome, cognome, data_nascita, sesso, comune)

st.write(f"Codice Fiscale: {cf}")

st.markdown("---")

# ======================================================
# ANTROPOMETRIA
# ======================================================

st.header("Valutazione Antropometrica")

peso = st.number_input("Peso (kg)", 30.0, 200.0)
altezza = st.number_input("Altezza (cm)", 100.0, 220.0)
fm = st.number_input("Massa grassa (%)", 3.0, 50.0)

altezza_m = altezza / 100
bmi = peso / (altezza_m ** 2) if altezza > 0 else 0

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

zone_potenza = []
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

    for z,min_p,max_p in zone:
        zone_potenza.append([z, round(min_p*ftp), round(max_p*ftp)])

    st.table(pd.DataFrame(zone_potenza,columns=["Zona","Da (W)","A (W)"]))

# ======================================================
# ZONE CARDIO
# ======================================================

zone_cardio = []
if fthr > 0:
    st.subheader("Zone Cardio")

    zone_hr=[
        ("Z1",0.81,0.89),
        ("Z2",0.90,0.93),
        ("Z3",0.94,0.99),
        ("Z4",1.00,1.05),
        ("Z5",1.06,1.15)
    ]

    for z,min_p,max_p in zone_hr:
        zone_cardio.append([z, round(min_p*fthr), round(max_p*fthr)])

    st.table(pd.DataFrame(zone_cardio,columns=["Zona","Da (bpm)","A (bpm)"]))

st.markdown("---")

# ======================================================
# PROIEZIONE STRATEGICA
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
# PDF COMPLETO
# ======================================================

if st.button("Genera PDF Completo"):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    pdf.cell(0,10,"REPORT VALUTAZIONE COMPLETA", ln=True, align="C")
    pdf.ln(5)
    pdf.cell(0,8,f"Data report: {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(5)

    pdf.cell(0,8,f"Nome: {nome} {cognome}", ln=True)
    pdf.cell(0,8,f"Sesso: {sesso}", ln=True)
    pdf.cell(0,8,f"Data nascita: {data_nascita.strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(0,8,f"Comune: {comune} ({provincia})", ln=True)
    pdf.cell(0,8,f"Codice Fiscale: {cf}", ln=True)
    pdf.cell(0,8,f"Email: {email}", ln=True)
    pdf.cell(0,8,f"Telefono: {telefono}", ln=True)
    pdf.cell(0,8,f"Indirizzo: {indirizzo}", ln=True)
    pdf.ln(5)

    pdf.cell(0,8,f"Peso: {peso} kg", ln=True)
    pdf.cell(0,8,f"Altezza: {altezza} cm", ln=True)
    pdf.cell(0,8,f"BMI: {bmi:.2f} ({classificazione})", ln=True)
    pdf.cell(0,8,f"Massa grassa: {fm_kg:.2f} kg", ln=True)
    pdf.cell(0,8,f"Massa magra: {massa_magra:.2f} kg", ln=True)
    pdf.ln(5)

    pdf.cell(0,8,f"Metodo FTP: {metodo}", ln=True)
    pdf.cell(0,8,f"FTP: {ftp:.2f} W", ln=True)
    pdf.cell(0,8,f"W/kg: {wkg:.2f}", ln=True)
    pdf.cell(0,8,f"FTHR: {fthr:.0f} bpm", ln=True)
    pdf.ln(5)

    pdf.cell(0,8,"ZONE POTENZA", ln=True)
    for row in zone_potenza:
        pdf.cell(0,8,f"{row[0]}: {row[1]} - {row[2]} W", ln=True)

    pdf.ln(5)
    pdf.cell(0,8,"ZONE CARDIO", ln=True)
    for row in zone_cardio:
        pdf.cell(0,8,f"{row[0]}: {row[1]} - {row[2]} bpm", ln=True)

    pdf.ln(5)
    pdf.cell(0,8,"PROIEZIONE STRATEGICA", ln=True)
    pdf.cell(0,8,f"Target FM: {target_fm:.2f}%", ln=True)
    pdf.cell(0,8,f"Incremento FTP: {incremento_ftp:.2f}%", ln=True)
    pdf.cell(0,8,f"Nuovo peso: {nuovo_peso:.2f} kg", ln=True)
    pdf.cell(0,8,f"Nuova FTP: {nuova_ftp:.2f} W", ln=True)
    pdf.cell(0,8,f"Nuovo W/kg: {nuovo_wkg:.2f}", ln=True)

    pdf.output("report_completo.pdf")

    with open("report_completo.pdf","rb") as f:
        st.download_button("Scarica PDF Completo",f,"Report_Completo_DB_Nutrition_Performance.pdf")
