import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd
import numpy as np
from io import BytesIO

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
# DATI ANAGRAFICI
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

peso = st.number_input("Peso (kg)", 30.0, 200.0, step=0.1)
altezza = st.number_input("Altezza (cm)", 100.0, 220.0, step=0.1)
fm = st.number_input("Massa grassa (%)", 3.0, 50.0, step=0.1)

bmi = 0
classificazione = ""

if peso > 0 and altezza > 0:
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

st.markdown("---")

# ======================================================
# ZONE POTENZA
# ======================================================

zone_potenza_df = None

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

    zone_potenza_df = pd.DataFrame(dati,columns=["Zona","Da (W)","A (W)"])
    st.table(zone_potenza_df)

st.markdown("---")

# ======================================================
# ZONE CARDIO
# ======================================================

zone_cardio_df = None

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

    zone_cardio_df = pd.DataFrame(dati_hr,columns=["Zona","Da (bpm)","A (bpm)"])
    st.table(zone_cardio_df)

st.markdown("---")

# ======================================================
# PROIEZIONE STRATEGICA
# ======================================================

st.header("Proiezione Strategica")

target_fm = st.number_input("Target Massa Grassa (%)", 3.0, 20.0, step=0.1)
incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0, step=0.1)

nuova_fm_kg = massa_magra * (target_fm/(100-target_fm))
nuovo_peso = massa_magra + nuova_fm_kg
nuova_ftp = ftp * (1 + incremento_ftp/100)
nuovo_wkg = nuova_ftp/nuovo_peso if nuovo_peso>0 else 0

st.write(f"Nuovo peso: {nuovo_peso:.2f} kg")
st.write(f"Nuova FTP: {nuova_ftp:.2f} W")
st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")

st.markdown("---")

# ======================================================
# PDF CLINICO EXECUTIVE - VERSIONE DEFINITIVA
# ======================================================

if st.button("Genera PDF Clinico Executive"):

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # =========================
    # STILI PERSONALIZZATI
    # =========================

    titolo = ParagraphStyle(
        'Titolo',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12
    )

    sezione = ParagraphStyle(
        'Sezione',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor("#1f3c88"),
        spaceBefore=12,
        spaceAfter=6
    )

    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey
    )

    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black
    )

    # =========================
    # LOGO
    # =========================
    try:
        logo = Image("logo.png", width=4*cm, height=2*cm)
        logo.hAlign = "RIGHT"
        elements.append(logo)
    except:
        pass

    elements.append(Paragraph("REPORT VALUTAZIONE METABOLICO-FUNZIONALE", titolo))
    elements.append(Spacer(1, 0.5*cm))

    # =====================================================
    # DATI ANAGRAFICI STRUTTURATI
    # =====================================================

    elements.append(Paragraph("DATI ANAGRAFICI", sezione))

    dati_anagrafici = [
        [Paragraph("Nome e Cognome", label_style), Paragraph(f"{nome} {cognome}", value_style)],
        [Paragraph("Sesso", label_style), Paragraph(sesso, value_style)],
        [Paragraph("Data di nascita", label_style), Paragraph(f"{data_nascita.strftime('%d/%m/%Y')} ({eta} anni)", value_style)],
        [Paragraph("Luogo di nascita", label_style), Paragraph(f"{comune} ({provincia})", value_style)],
        [Paragraph("Email", label_style), Paragraph(email, value_style)],
        [Paragraph("Telefono", label_style), Paragraph(telefono, value_style)],
        [Paragraph("Indirizzo", label_style), Paragraph(indirizzo, value_style)],
    ]

    tab_anag = Table(dati_anagrafici, colWidths=[5*cm, 9*cm])
    tab_anag.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.8,colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.lightgrey),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),8),
        ('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),6),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))

    elements.append(tab_anag)

    # =====================================================
    # ANTROPOMETRIA
    # =====================================================

    elements.append(Paragraph("VALUTAZIONE ANTROPOMETRICA", sezione))

    dati_antropo = [
        ["Peso (kg)", f"{peso:.2f}"],
        ["Altezza (cm)", f"{altezza:.0f}"],
        ["BMI", f"{bmi:.2f} ({classificazione})"],
        ["Massa grassa (kg)", f"{fm_kg:.2f}"],
        ["Massa magra (kg)", f"{massa_magra:.2f}"],
    ]

    tab_antropo = Table(dati_antropo, colWidths=[7*cm, 7*cm])
    tab_antropo.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
        ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ('ALIGN',(1,0),(-1,-1),'RIGHT'),
        ('LEFTPADDING',(0,0),(-1,-1),8),
        ('RIGHTPADDING',(0,0),(-1,-1),8),
    ]))

    elements.append(tab_antropo)

    # =====================================================
    # ZONE POTENZA CON HEADER PROFESSIONALE
    # =====================================================

    if zone_potenza_df is not None:

        elements.append(Paragraph("ZONE DI POTENZA", sezione))

        dati_zone = [["Zona", "Da (W)", "A (W)"]]
        for _, row in zone_potenza_df.iterrows():
            dati_zone.append([row["Zona"], row["Da (W)"], row["A (W)"]])

        tab_zone = Table(dati_zone, colWidths=[4*cm, 5*cm, 5*cm])
        tab_zone.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1f3c88")),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('GRID',(0,0),(-1,-1),0.4,colors.grey),
            ('ALIGN',(1,1),(-1,-1),'RIGHT'),
            ('LEFTPADDING',(0,0),(-1,-1),8),
            ('RIGHTPADDING',(0,0),(-1,-1),8),
        ]))

        elements.append(tab_zone)

    # =====================================================

    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    st.download_button(
        "Scarica PDF Clinico Executive",
        data=pdf_bytes,
        file_name="report_clinico_executive.pdf",
        mime="application/pdf"
    )
