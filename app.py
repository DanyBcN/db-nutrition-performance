import streamlit as st
from PIL import Image
from datetime import date
from fpdf import FPDF

st.set_page_config(layout="centered")

# ===============================
# LOGO CENTRATO
# ===============================
logo = Image.open("logo.png")
c1, c2, c3 = st.columns([1,2,1])
with c2:
    st.image(logo, width=250)

st.markdown("---")

# ===============================
# FUNZIONI
# ===============================

def estrai_consonanti(testo):
    return ''.join([c for c in testo.upper() if c in "BCDFGHJKLMNPQRSTVWXYZ"])

def estrai_vocali(testo):
    return ''.join([c for c in testo.upper() if c in "AEIOU"])

def genera_codice_fiscale(nome, cognome, data):
    c = (estrai_consonanti(cognome) + estrai_vocali(cognome) + "XXX")[:3]
    n = (estrai_consonanti(nome) + estrai_vocali(nome) + "XXX")[:3]
    anno = str(data.year)[2:]
    mesi = "ABCDEHLMPRST"
    mese = mesi[data.month - 1]
    giorno = f"{data.day:02d}"
    return (c + n + anno + mese + giorno + "X000").upper()

def genera_pdf(righe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    for r in righe:
        pdf.multi_cell(0,6,r)
    return pdf.output(dest="S").encode("latin-1")

# ===============================
# DATI ANAGRAFICI
# ===============================

st.header("Dati Anagrafici")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")
luogo = st.text_input("Luogo di nascita")
data_nascita = st.date_input(
    "Data di nascita",
    min_value=date(1940,1,1),
    max_value=date.today(),
    format="DD/MM/YYYY"
)

email = st.text_input("Email")
telefono = st.text_input("Telefono")
indirizzo = st.text_input("Indirizzo")

codice_fiscale = None

if nome and cognome:
    codice_fiscale = genera_codice_fiscale(nome, cognome, data_nascita)
    st.write(f"Codice Fiscale: **{codice_fiscale}**")

today = date.today()
eta = today.year - data_nascita.year - (
    (today.month,today.day) < (data_nascita.month,data_nascita.day)
)

st.write(f"Età: **{eta} anni**")

st.markdown("---")

# ===============================
# COMPOSIZIONE CORPOREA
# ===============================

st.header("Composizione Corporea")

peso = st.number_input("Peso (kg)", 30.0, 200.0, step=0.1)
altezza = st.number_input("Altezza (cm)", 120.0, 220.0, step=0.1)
fm = st.number_input("Massa grassa (%)", 3.0, 50.0, step=0.1)

altezza_m = altezza / 100
bmi = peso / (altezza_m**2) if altezza_m > 0 else 0

if bmi < 18.5:
    classe_bmi = "Sottopeso"
elif bmi < 25:
    classe_bmi = "Normopeso"
elif bmi < 30:
    classe_bmi = "Sovrappeso"
else:
    classe_bmi = "Obesità"

st.write(f"BMI: **{bmi:.2f}** ({classe_bmi})")

fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg

st.write(f"Massa grassa: **{fm_kg:.2f} kg**")
st.write(f"Massa magra: **{massa_magra:.2f} kg**")

st.markdown("---")

# ===============================
# TEST FTP
# ===============================

st.header("Test di Potenza")

tipo_test = st.selectbox("Tipo test", ["20 minuti", "2x8 minuti", "FTP diretto"])

ftp = 0

if tipo_test == "20 minuti":
    p = st.number_input("Potenza media 20' (W)", 0.0)
    ftp = p * 0.95

elif tipo_test == "2x8 minuti":
    p1 = st.number_input("8' prova 1 (W)", 0.0)
    p2 = st.number_input("8' prova 2 (W)", 0.0)
    ftp = ((p1 + p2) / 2) * 0.90

else:
    ftp = st.number_input("FTP (W)", 0.0)

if ftp > 0:
    wkg = ftp / peso
    st.write(f"FTP: **{ftp:.2f} W**")
    st.write(f"W/kg: **{wkg:.2f}**")

    st.subheader("Zone di Potenza (Coggan)")
    st.table({
        "Zona":[
            "Z1 Recupero","Z2 Endurance","Z3 Tempo",
            "Z4 Soglia","Z5 VO2max","Z6 Anaerobica","Z7 Neuromuscolare"
        ],
        "Range Watt":[
            f"< {ftp*0.55:.0f}",
            f"{ftp*0.56:.0f}-{ftp*0.75:.0f}",
            f"{ftp*0.76:.0f}-{ftp*0.90:.0f}",
            f"{ftp*0.91:.0f}-{ftp*1.05:.0f}",
            f"{ftp*1.06:.0f}-{ftp*1.20:.0f}",
            f"{ftp*1.21:.0f}-{ftp*1.50:.0f}",
            f"> {ftp*1.50:.0f}"
        ]
    })

st.markdown("---")

# ===============================
# CARDIO
# ===============================

st.header("Frequenza Cardiaca")

uso_cardio = st.selectbox("Ha indossato il cardio?", ["No","Sì"])

fthr = None

if uso_cardio == "Sì":
    fc = st.number_input("FC media test (bpm)", 0)
    if fc > 0:
        fthr = fc
        st.write(f"FTHR: **{fthr} bpm**")

        st.subheader("Zone Cardiache")
        st.table({
            "Zona":["Z1","Z2","Z3","Z4","Z5"],
            "Range bpm":[
                f"< {fthr*0.81:.0f}",
                f"{fthr*0.81:.0f}-{fthr*0.89:.0f}",
                f"{fthr*0.90:.0f}-{fthr*0.93:.0f}",
                f"{fthr*0.94:.0f}-{fthr*0.99:.0f}",
                f"> {fthr:.0f}"
            ]
        })

st.markdown("---")

# ===============================
# PROIEZIONE STRATEGICA
# ===============================

st.header("Proiezione Strategica")

target_fm = st.number_input("Target FM (%)", 3.0, 20.0, step=0.1)
inc_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0, step=0.5)

nuova_fm_kg = massa_magra * (target_fm/(100-target_fm))
nuovo_peso = massa_magra + nuova_fm_kg
nuova_ftp = ftp * (1 + inc_ftp/100)
nuovo_wkg = nuova_ftp/nuovo_peso if nuovo_peso>0 else 0

st.write(f"Nuovo peso: **{nuovo_peso:.2f} kg**")
st.write(f"Nuova FTP: **{nuova_ftp:.2f} W**")
st.write(f"Nuovo W/kg: **{nuovo_wkg:.2f}**")

st.markdown("---")

# ===============================
# PDF COMPLETO
# ===============================

if st.button("Genera PDF"):

    if not nome or not cognome:
        st.warning("Inserire almeno nome e cognome.")
    else:

        cf = genera_codice_fiscale(nome, cognome, data_nascita)

        righe = [
            "----- REPORT DB NUTRITION & PERFORMANCE -----",
            "",
            "DATI ANAGRAFICI",
            f"Nome: {nome} {cognome}",
            f"Luogo: {luogo}",
            f"Data nascita: {data_nascita.strftime('%d/%m/%Y')}",
            f"Codice Fiscale: {cf}",
            f"Email: {email}",
            f"Telefono: {telefono}",
            f"Indirizzo: {indirizzo}",
            "",
            "COMPOSIZIONE CORPOREA",
            f"Peso: {peso} kg",
            f"Altezza: {altezza} cm",
            f"BMI: {bmi:.2f} ({classe_bmi})",
            f"Massa magra: {massa_magra:.2f} kg",
            "",
            "PERFORMANCE",
            f"FTP: {ftp:.2f} W",
            f"W/kg: {ftp/peso if ftp>0 else 0:.2f}",
            f"Nuovo W/kg: {nuovo_wkg:.2f}"
        ]

        pdf_bytes = genera_pdf(righe)

        st.download_button(
            "Scarica PDF",
            pdf_bytes,
            "Report_DB_Nutrition_Performance.pdf",
            "application/pdf"
        )
