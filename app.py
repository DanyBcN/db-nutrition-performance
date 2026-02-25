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

# Genera PDF definitivo (ReportLab, versione "prende tutti i dati")
if st.button("Genera PDF Clinico Definitivo"):

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.lib.pagesizes import A4
    from io import BytesIO
    from datetime import date as _date

    # --- Buffer PDF ---
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # --- Styles ---
    styles = getSampleStyleSheet()
    titolo_style = ParagraphStyle("Titolo", parent=styles["Heading1"], fontSize=16, spaceAfter=6, alignment=1)
    sezione_style = ParagraphStyle("Sezione", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#1f3c88"), spaceBefore=8, spaceAfter=4)
    label_style = ParagraphStyle("Label", parent=styles["Normal"], fontSize=9, textColor=colors.grey)
    value_style = ParagraphStyle("Value", parent=styles["Normal"], fontSize=10, textColor=colors.black)

    # --- Helper: safe string ---
    def safe(x):
        return str(x) if (x is not None and str(x).strip() != "") else "-"

    # --- Ricalcola età (in caso sia necessario) ---
    try:
        today = _date.today()
        eta_calcolata = today.year - data_nascita.year - ((today.month, today.day) < (data_nascita.month, data_nascita.day))
        eta_to_show = eta_calcolata
    except Exception:
        eta_to_show = safe(eta)  # fallback se data_nascita non valida

    # --- Header / Footer callback ---
    def _header_footer(canvas, doc):
        canvas.saveState()
        # header: logo a destra e titolo piccolo
        try:
            logo_path = "logo.png"
            canvas.drawImage(logo_path, doc.pagesize[0] - doc.rightMargin - (3.8*cm), doc.pagesize[1] - doc.topMargin + (0.2*cm), width=3.8*cm, height=1.6*cm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
        canvas.setFont("Helvetica", 8)
        canvas.drawString(doc.leftMargin, doc.pagesize[1] - doc.topMargin + 0.2*cm, "Report valutazione metabolico-funzionale")
        # footer: numero pagina
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.drawCentredString(doc.pagesize[0]/2.0, doc.bottomMargin/2.0, f"Pagina {doc.page}")
        canvas.restoreState()

    # --- Build elements ---
    elements = []

    # Logo + titolo (centrato)
    try:
        logo = Image("logo.png", width=6*cm, height=2.4*cm)
        logo.hAlign = "CENTER"
        elements.append(logo)
    except Exception:
        pass

    elements.append(Paragraph("REPORT VALUTAZIONE METABOLICO-FUNZIONALE", titolo_style))
    elements.append(Spacer(1, 0.2*cm))

    # --- DATI ANAGRAFICI (2 colonne: label / value) ---
    elements.append(Paragraph("DATI ANAGRAFICI", sezione_style))

    dati_anagrafici = [
        [Paragraph("Nome", label_style), Paragraph(f"{safe(nome)} {safe(cognome)}", value_style)],
        [Paragraph("Sesso", label_style), Paragraph(safe(sesso), value_style)],
        [Paragraph("Data di nascita", label_style), Paragraph(f"{data_nascita.strftime('%d/%m/%Y') if hasattr(data_nascita,'strftime') else safe(data_nascita)} ({eta_to_show} anni)", value_style)],
        [Paragraph("Luogo di nascita", label_style), Paragraph(f"{safe(comune)} ({safe(provincia)})", value_style)],
        [Paragraph("Email", label_style), Paragraph(safe(email), value_style)],
        [Paragraph("Telefono", label_style), Paragraph(safe(telefono), value_style)],
        [Paragraph("Indirizzo", label_style), Paragraph(safe(indirizzo), value_style)],
    ]

    tab_anag = Table(dati_anagrafici, colWidths=[5.2*cm, 9.8*cm], repeatRows=0)
    tab_anag.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.6,colors.HexColor("#d9d9d9")),
        ('INNERGRID',(0,0),(-1,-1),0.4,colors.HexColor("#e6e6e6")),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),6),
        ('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),4),
        ('BOTTOMPADDING',(0,0),(-1,-1),4),
    ]))
    elements.append(tab_anag)
    elements.append(Spacer(1, 0.3*cm))

    # --- ANTROPOMETRIA ---
    elements.append(Paragraph("VALUTAZIONE ANTROPOMETRICA", sezione_style))

    dati_antropo = [
        [Paragraph("Peso (kg)", label_style), Paragraph(f"{peso:.2f}" if peso is not None else "-", value_style), Paragraph("Massa grassa (%)", label_style), Paragraph(f"{fm:.2f}" if fm is not None else "-", value_style)],
        [Paragraph("Altezza (cm)", label_style), Paragraph(f"{altezza:.0f}" if altezza is not None else "-", value_style), Paragraph("Massa grassa (kg)", label_style), Paragraph(f"{fm_kg:.2f}" if 'fm_kg' in locals() else "-", value_style)],
        [Paragraph("BMI", label_style), Paragraph(f"{bmi:.2f} ({classificazione})" if 'bmi' in locals() else "-", value_style), Paragraph("Massa magra (kg)", label_style), Paragraph(f"{massa_magra:.2f}" if 'massa_magra' in locals() else "-", value_style)],
    ]

    tab_ant = Table(dati_antropo, colWidths=[3.6*cm, 4.4*cm, 3.6*cm, 4.4*cm], repeatRows=0)
    tab_ant.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor("#e0e0e0")),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ALIGN',(1,0),(1,-1),'RIGHT'),
        ('ALIGN',(3,0),(3,-1),'RIGHT'),
        ('LEFTPADDING',(0,0),(-1,-1),6),
        ('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))
    elements.append(tab_ant)
    elements.append(Spacer(1, 0.3*cm))

    # --- PERFORMANCE ---
    elements.append(Paragraph("PERFORMANCE", sezione_style))

    dati_perf = [
        ["Metodo FTP", safe(metodo)],
        ["FTP (W)", f"{ftp:.2f}" if ftp is not None else "-"],
        ["W/kg", f"{wkg:.2f}" if wkg is not None else "-"],
        ["FTHR (bpm)", f"{fthr:.0f}" if fthr is not None else "-"],
    ]
    tab_perf = Table(dati_perf, colWidths=[5.2*cm, 9.8*cm], repeatRows=0)
    tab_perf.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor("#e0e0e0")),
        ('LEFTPADDING',(0,0),(-1,-1),6),
        ('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))
    elements.append(tab_perf)
    elements.append(Spacer(1, 0.3*cm))

    # --- ZONE POTENZA (tabella con header ripetuto se spezza pagina) ---
    if zone_potenza_df is not None and not zone_potenza_df.empty:
        elements.append(Paragraph("ZONE DI POTENZA", sezione_style))
        dati_zone = [["Zona", "Da (W)", "A (W)"]]
        for _, row in zone_potenza_df.iterrows():
            dati_zone.append([safe(row["Zona"]), safe(row["Da (W)"]), safe(row["A (W)"])])
        tab_zone = Table(dati_zone, colWidths=[4*cm, 5.6*cm, 5.6*cm], repeatRows=1)
        tab_zone.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1f3c88")),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('GRID',(0,0),(-1,-1),0.5,colors.HexColor("#d9d9d9")),
            ('ALIGN',(1,1),(-1,-1),'RIGHT'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LEFTPADDING',(0,0),(-1,-1),6),
            ('RIGHTPADDING',(0,0),(-1,-1),6),
        ]))
        elements.append(KeepTogether(tab_zone))
        elements.append(Spacer(1, 0.3*cm))

    # --- ZONE CARDIO ---
    if zone_cardio_df is not None and not zone_cardio_df.empty:
        elements.append(Paragraph("ZONE CARDIO", sezione_style))
        dati_hr = [["Zona", "Da (bpm)", "A (bpm)"]]
        for _, row in zone_cardio_df.iterrows():
            dati_hr.append([safe(row["Zona"]), safe(row["Da (bpm)"]), safe(row["A (bpm)"])])
        tab_hr = Table(dati_hr, colWidths=[4*cm, 5.6*cm, 5.6*cm], repeatRows=1)
        tab_hr.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1f3c88")),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('GRID',(0,0),(-1,-1),0.5,colors.HexColor("#d9d9d9")),
            ('ALIGN',(1,1),(-1,-1),'RIGHT'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LEFTPADDING',(0,0),(-1,-1),6),
            ('RIGHTPADDING',(0,0),(-1,-1),6),
        ]))
        elements.append(KeepTogether(tab_hr))
        elements.append(Spacer(1, 0.3*cm))

    # --- PROIEZIONE STRATEGICA (mostra anche target FM% e incremento FTP) ---
    elements.append(Paragraph("PROIEZIONE STRATEGICA", sezione_style))
    dati_proj = [
        ["Target Massa Grassa (%)", f"{target_fm:.2f}" if 'target_fm' in locals() else safe(target_fm) if 'target_fm' in globals() else "-"],
        ["Incremento FTP (%)", f"{incremento_ftp:.2f}" if 'incremento_ftp' in locals() else safe(incremento_ftp) if 'incremento_ftp' in globals() else "-"],
        ["Nuovo peso (kg)", f"{nuovo_peso:.2f}" if 'nuovo_peso' in locals() else "-"],
        ["Nuova FTP (W)", f"{nuova_ftp:.2f}" if 'nuova_ftp' in locals() else "-"],
        ["Nuovo W/kg", f"{nuovo_wkg:.2f}" if 'nuovo_wkg' in locals() else "-"],
    ]
    tab_proj = Table(dati_proj, colWidths=[6*cm, 9*cm], repeatRows=0)
    tab_proj.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor("#e0e0e0")),
        ('LEFTPADDING',(0,0),(-1,-1),6),
        ('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))
    elements.append(tab_proj)

    # --- Build PDF con header/footer su ogni pagina ---
    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    st.download_button(
        "Scarica PDF Clinico Definitivo",
        data=pdf_bytes,
        file_name="report_clinico_definitivo.pdf",
        mime="application/pdf"
    )
