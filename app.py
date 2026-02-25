import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import math

st.set_page_config(layout="wide")

# ======================================================
# INIZIALIZZAZIONE VARIABILI (ANTI-ERROR)
# ======================================================

ftp = 0.0
valore_test = 0.0
wkg = 0.0
nuova_ftp = 0.0
nuovo_wkg = 0.0
tempo_vecchio = 0.0
tempo_nuovo = 0.0
giudizio = ""

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

st.write(f"BMI: {bmi:.2f}")
st.write(f"Massa grassa: {fm_kg:.2f} kg")
st.write(f"Massa magra: {massa_magra:.2f} kg")

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
# ZONE POTENZA
# ======================================================

if ftp > 0:

    zone = [
        ("Z1 Recovery attivo",0.00,0.55),
        ("Z2 Fondo aerobico",0.56,0.75),
        ("Z3 Tempo",0.76,0.90),
        ("Z4 Soglia lattato",0.91,1.05),
        ("Z5 VO2max",1.06,1.20),
        ("Z6 Capacita anaerobica",1.21,1.50),
        ("Z7 Neuromuscolare",1.51,2.00),
    ]

    zone_df = pd.DataFrame(
        [[z, round(a*ftp), round(b*ftp)] for z,a,b in zone],
        columns=["Zona","Da (W)","A (W)"]
    )

    st.subheader("Zone Potenza")
    st.table(zone_df)

# ======================================================
# ZONE CARDIO
# ======================================================

st.header("Frequenza Cardiaca")

fthr = st.number_input("FTHR (bpm)", 0.0)

if fthr > 0:

    zone_hr = [
        ("Z1 Recupero",0.81,0.89),
        ("Z2 Aerobico base",0.90,0.93),
        ("Z3 Tempo",0.94,0.99),
        ("Z4 Soglia",1.00,1.05),
        ("Z5 Alta intensita",1.06,1.15),
    ]

    zone_hr_df = pd.DataFrame(
        [[z, round(a*fthr), round(b*fthr)] for z,a,b in zone_hr],
        columns=["Zona","Da (bpm)","A (bpm)"]
    )

    st.subheader("Zone Cardio")
    st.table(zone_hr_df)

st.markdown("---")

# ======================================================
# PROIEZIONE PERFORMANCE
# ======================================================

st.header("Proiezione Performance")

nuovo_peso = st.number_input("Nuovo peso target (kg)", 0.0)
incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0)

if nuovo_peso > 0 and ftp > 0:

    nuova_ftp = ftp * (1 + incremento_ftp/100)
    nuovo_wkg = nuova_ftp / nuovo_peso
    delta_wkg = nuovo_wkg - wkg

    if delta_wkg > 0.3:
        giudizio = "Miglioramento significativo"
    elif delta_wkg > 0.1:
        giudizio = "Miglioramento moderato"
    else:
        giudizio = "Miglioramento lieve"

    lunghezza = 5000
    pendenza = 0.06
    g = 9.81

    def tempo_salita(potenza, peso):
        forza = peso * g * pendenza
        velocita = potenza / forza
        return (lunghezza / velocita) / 60

    tempo_vecchio = tempo_salita(ftp, peso)
    tempo_nuovo = tempo_salita(nuova_ftp, nuovo_peso)

    st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")
    st.write(f"Giudizio: {giudizio}")
    st.write(f"Salita 5 km 6%: da {tempo_vecchio:.1f} min a {tempo_nuovo:.1f} min")

st.markdown("---")

# ======================================================
# PDF PROFESSIONALE CON LOGO E COLORE
# ======================================================

if st.button("Genera PDF Completo"):

    def safe(text):
        return text.encode("latin-1","replace").decode("latin-1")

    class PDF(FPDF):

        def header(self):
            # LOGO (se presente)
            try:
                self.image("logo.png", 80, 8, 50)
                self.ln(25)
            except:
                self.ln(15)

            # Titolo
            self.set_font("Arial","B",18)
            self.cell(0,10,"REPORT PERFORMANCE",0,1,"C")
            self.ln(3)

            # Linea colorata
            self.set_draw_color(30,90,160)
            self.set_line_width(1)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(8)

        def section_title(self, title):
            self.set_fill_color(230,240,255)
            self.set_font("Arial","B",12)
            self.cell(0,8,title,0,1,"L",True)
            self.ln(2)

        def normal(self, text):
            self.set_font("Arial","",10)
            self.multi_cell(0,6,safe(text))
            self.ln(2)

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ======================================================
    # DATI PRINCIPALI
    # ======================================================

    pdf.section_title("Dati Anagrafici")
    pdf.normal(
        f"Nome: {nome}\n"
        f"Cognome: {cognome}\n"
        f"Data di nascita: {data_nascita.strftime('%d %m %Y')}\n"
        f"Eta: {eta} anni"
    )

    pdf.section_title("Antropometria")
    pdf.normal(
        f"Peso: {peso:.1f} kg\n"
        f"Altezza: {altezza:.1f} cm\n"
        f"BMI: {bmi:.2f}\n"
        f"Massa grassa: {fm:.1f}% ({fm_kg:.2f} kg)\n"
        f"Massa magra: {massa_magra:.2f} kg"
    )

    pdf.section_title("Performance")
    pdf.normal(
        f"Metodo FTP: {metodo}\n"
        f"Valore test inserito: {valore_test:.2f} W\n"
        f"FTP calcolata: {ftp:.2f} W\n"
        f"W/kg: {wkg:.2f}"
    )

    # ======================================================
    # TABELLA ZONE POTENZA
    # ======================================================

    if not zone_df.empty:

        pdf.section_title("Zone Potenza")

        pdf.set_font("Arial","B",10)
        pdf.set_fill_color(200,220,255)

        pdf.cell(80,8,"Zona",1,0,"C",True)
        pdf.cell(40,8,"Da (W)",1,0,"C",True)
        pdf.cell(40,8,"A (W)",1,1,"C",True)

        pdf.set_font("Arial","",10)

        for _, row in zone_df.iterrows():
            pdf.cell(80,8,safe(str(row["Zona"])),1)
            pdf.cell(40,8,str(row["Da (W)"]),1)
            pdf.cell(40,8,str(row["A (W)"]),1)
            pdf.ln()

    # ======================================================
    # TABELLA ZONE CARDIO
    # ======================================================

    if not zone_hr_df.empty:

        pdf.section_title("Zone Cardio")

        pdf.set_font("Arial","B",10)
        pdf.set_fill_color(200,220,255)

        pdf.cell(80,8,"Zona",1,0,"C",True)
        pdf.cell(40,8,"Da (bpm)",1,0,"C",True)
        pdf.cell(40,8,"A (bpm)",1,1,"C",True)

        pdf.set_font("Arial","",10)

        for _, row in zone_hr_df.iterrows():
            pdf.cell(80,8,safe(str(row["Zona"])),1)
            pdf.cell(40,8,str(row["Da (bpm)"]),1)
            pdf.cell(40,8,str(row["A (bpm)"]),1)
            pdf.ln()

    # ======================================================
    # PROIEZIONE RISCRITTA COME VUOI TU
    # ======================================================

    if nuovo_peso > 0 and ftp > 0:

        delta_ftp = nuova_ftp - ftp
        delta_tempo = tempo_vecchio - tempo_nuovo

        pdf.section_title("Proiezione Miglioramento")

        testo_proj = (
            f"Se il peso passasse da {peso:.1f} kg a {nuovo_peso:.1f} kg "
            f"e la FTP da {ftp:.1f} W a {nuova_ftp:.1f} W, "
            f"si avrebbe un incremento del rapporto W/kg "
            f"da {wkg:.2f} a {nuovo_wkg:.2f}.\n\n"
            f"Su una salita di 5 chilometri con pendenza media del 6%, "
            f"il tempo stimato passerebbe da {tempo_vecchio:.1f} minuti "
            f"a {tempo_nuovo:.1f} minuti, "
            f"con un miglioramento complessivo stimato di "
            f"{delta_tempo:.1f} minuti."
        )

        pdf.normal(testo_proj)

    pdf.output("report_performance_professionale.pdf")

    with open("report_performance_professionale.pdf","rb") as f:
        st.download_button(
            "Scarica PDF Professionale",
            f,
            "report_performance_professionale.pdf"
        )
