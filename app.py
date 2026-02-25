import streamlit as st
from datetime import date
import pandas as pd
from PIL import Image
from io import BytesIO

st.set_page_config(layout="wide")

# ======================================================
# HEADER APP
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
provincia = st.text_input("Provincia (sigla)")
data_nascita = st.date_input("Data di nascita")
email = st.text_input("Email")
telefono = st.text_input("Telefono")
indirizzo = st.text_input("Indirizzo")

# Normalizzazione nome completo
if nome and cognome:
    full_name = f"{nome.strip()} {cognome.strip()}"
elif nome:
    full_name = nome.strip()
elif cognome:
    full_name = cognome.strip()
else:
    full_name = "-"

eta = date.today().year - data_nascita.year - (
    (date.today().month, date.today().day) <
    (data_nascita.month, data_nascita.day)
)

st.markdown("---")

# ======================================================
# ANTROPOMETRIA
# ======================================================

st.header("Valutazione Antropometrica")

peso = st.number_input("Peso (kg)", 30.0, 200.0, step=0.1)
altezza = st.number_input("Altezza (cm)", 100.0, 220.0, step=0.1)
fm = st.number_input("Massa grassa (%)", 3.0, 50.0, step=0.1)

altezza_m = altezza / 100
bmi = peso / (altezza_m ** 2)
fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg

if bmi < 18.5:
    classificazione = "Sottopeso"
elif bmi < 25:
    classificazione = "Normopeso"
elif bmi < 30:
    classificazione = "Sovrappeso"
else:
    classificazione = "Obesità"

st.markdown("---")

# ======================================================
# FTP
# ======================================================

st.header("Calcolo FTP")

metodo = st.selectbox(
    "Metodo",
    ["Immissione diretta","Test 20 minuti","Test 8 minuti","Ramp test"]
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

# ======================================================
# ZONE
# ======================================================

zone_potenza = [
    ("Z1",0.00,0.55),
    ("Z2",0.56,0.75),
    ("Z3",0.76,0.90),
    ("Z4",0.91,1.05),
    ("Z5",1.06,1.20),
    ("Z6",1.21,1.50),
    ("Z7",1.51,2.00),
]

zone_hr = [
    ("Z1",0.81,0.89),
    ("Z2",0.90,0.93),
    ("Z3",0.94,0.99),
    ("Z4",1.00,1.05),
    ("Z5",1.06,1.15),
]

# ======================================================
# PDF EXECUTIVE
# ======================================================

if st.button("Genera PDF Executive"):

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.lib.pagesizes import A4

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"<b>{full_name}</b>", styles["Title"]))
    elements.append(Spacer(1, 0.5*cm))

    # KPI BOX
    kpi_data = [
        ["BMI", f"{bmi:.2f}"],
        ["FTP (W)", f"{ftp:.2f}"],
        ["W/kg", f"{wkg:.2f}"],
        ["FM %", f"{fm:.2f}"],
    ]

    kpi_table = Table(kpi_data, colWidths=[5*cm,5*cm])
    kpi_table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),1,colors.grey),
        ('BACKGROUND',(0,0),(-1,-1),colors.whitesmoke),
        ('ALIGN',(1,0),(-1,-1),'RIGHT')
    ]))

    elements.append(kpi_table)
    elements.append(Spacer(1, 0.5*cm))

    # ZONE POTENZA
    zp = [["Zona","Da (W)","A (W)"]]
    for z,a,b in zone_potenza:
        zp.append([z, round(a*ftp), round(b*ftp)])

    zp_table = Table(zp)
    zp_table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)
    ]))

    elements.append(zp_table)
    elements.append(Spacer(1, 0.5*cm))

    # ZONE HR
    zh = [["Zona","Da (bpm)","A (bpm)"]]
    for z,a,b in zone_hr:
        zh.append([z, round(a*fthr), round(b*fthr)])

    zh_table = Table(zh)
    zh_table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ('BACKGROUND',(0,0),(-1,0),colors.lightgrey)
    ]))

    elements.append(zh_table)

    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    st.download_button(
        "Scarica PDF Executive",
        data=pdf_bytes,
        file_name="report_executive.pdf",
        mime="application/pdf"
    )
