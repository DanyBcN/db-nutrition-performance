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
# CODICE FISCALE
# ======================================================

mesi_cf = "ABCDEHLMPRST"

def consonanti(s):
    return "".join([c for c in s.upper() if c in "BCDFGHJKLMNPQRSTVWXYZ"])

def vocali(s):
    return "".join([c for c in s.upper() if c in "AEIOU"])

def carattere_controllo(cf15):
    dispari = dict(zip("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        [1,0,5,7,9,13,15,17,19,21,
         1,0,5,7,9,13,15,17,19,21,
         2,4,18,20,11,3,6,8,12,14,
         16,10,22,25,24,23]))
    pari = {c:i for i,c in enumerate("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
    s = 0
    for i,c in enumerate(cf15):
        s += pari[c] if (i+1)%2==0 else dispari[c]
    return chr((s % 26) + ord('A'))

def genera_cf(nome,cognome,data,sesso,provincia):
    cons_cogn = consonanti(cognome)
    cod_cogn = (cons_cogn + vocali(cognome) + "XXX")[:3]
    cons_nome = consonanti(nome)
    if len(cons_nome) >= 4:
        cod_nome = cons_nome[0] + cons_nome[2] + cons_nome[3]
    else:
        cod_nome = (cons_nome + vocali(nome) + "XXX")[:3]
    anno = str(data.year)[2:]
    mese = mesi_cf[data.month-1]
    giorno = data.day + (40 if sesso=="F" else 0)
    giorno = f"{giorno:02d}"
    codice_prov = provincia.upper().ljust(4,"X")[:4]
    cf15 = cod_cogn + cod_nome + anno + mese + giorno + codice_prov
    return cf15 + carattere_controllo(cf15)

# ======================================================
# DATI ANAGRAFICI
# ======================================================

st.header("Dati Anagrafici")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")
sesso = st.selectbox("Sesso",["M","F"])
comune = st.text_input("Comune di nascita")
provincia = st.text_input("Provincia di nascita (sigla)")
data_nascita = st.date_input("Data di nascita",
                             min_value=date(1920,1,1),
                             max_value=date.today())

email = st.text_input("Email")
telefono = st.text_input("Telefono")
indirizzo = st.text_input("Indirizzo")

eta = date.today().year - data_nascita.year - (
    (date.today().month,date.today().day) <
    (data_nascita.month,data_nascita.day)
)

cf = genera_cf(nome,cognome,data_nascita,sesso,provincia) if nome and cognome and provincia else ""

st.write(f"Età: {eta} anni")
st.write(f"Codice Fiscale: {cf}")

st.markdown("---")

# ======================================================
# ANTROPOMETRIA
# ======================================================

st.header("Valutazione Antropometrica")

peso = st.number_input("Peso (kg)",30.0,200.0,step=0.1)
altezza = st.number_input("Altezza (cm)",100.0,220.0,step=0.1)
fm = st.number_input("Massa grassa (%)",3.0,50.0,step=0.1)

altezza_m = altezza/100
bmi = peso/(altezza_m**2)
fm_kg = peso*(fm/100)
massa_magra = peso - fm_kg

if bmi < 18.5:
    classificazione="Sottopeso"
elif bmi <25:
    classificazione="Normopeso"
elif bmi <30:
    classificazione="Sovrappeso"
else:
    classificazione="Obesità"

st.write(f"BMI: {bmi:.2f} ({classificazione})")
st.write(f"Massa grassa: {fm_kg:.2f} kg")
st.write(f"Massa magra: {massa_magra:.2f} kg")

st.markdown("---")

# ======================================================
# FTP
# ======================================================

st.header("Calcolo FTP")

metodo = st.selectbox("Metodo",
                      ["Immissione diretta","Test 20 minuti",
                       "Test 8 minuti","Ramp test"])

ftp=0
if metodo=="Immissione diretta":
    ftp=st.number_input("FTP (W)",0.0)
elif metodo=="Test 20 minuti":
    p20=st.number_input("Media 20' (W)",0.0)
    ftp=p20*0.95
elif metodo=="Test 8 minuti":
    p8=st.number_input("Media 8' (W)",0.0)
    ftp=p8*0.90
elif metodo=="Ramp test":
    step=st.number_input("Ultimo step (W)",0.0)
    ftp=step*0.75

wkg=ftp/peso if peso>0 else 0

st.write(f"FTP: {ftp:.2f} W")
st.write(f"W/kg: {wkg:.2f}")

st.markdown("---")

# ======================================================
# FTHR
# ======================================================

st.header("Frequenza Cardiaca")

fthr_input = st.number_input("FTHR (bpm)",0.0)
fthr = fthr_input if fthr_input>0 else 0.95*(220-eta)

st.write(f"FTHR: {fthr:.0f} bpm")

# ======================================================
# ZONE VISIBILI
# ======================================================

st.subheader("Zone Potenza")

zone = [("Z1",0.00,0.55),("Z2",0.56,0.75),("Z3",0.76,0.90),
        ("Z4",0.91,1.05),("Z5",1.06,1.20),
        ("Z6",1.21,1.50),("Z7",1.51,2.00)]

zone_df = pd.DataFrame(
    [[z, round(a*ftp) if ftp>0 else 0,
      round(b*ftp) if ftp>0 else 0] for z,a,b in zone],
    columns=["Zona","Da (W)","A (W)"]
)

st.table(zone_df)

st.subheader("Zone Cardio")

zone_hr=[("Z1",0.81,0.89),("Z2",0.90,0.93),
         ("Z3",0.94,0.99),("Z4",1.00,1.05),
         ("Z5",1.06,1.15)]

zone_hr_df = pd.DataFrame(
    [[z, round(a*fthr) if fthr>0 else 0,
      round(b*fthr) if fthr>0 else 0] for z,a,b in zone_hr],
    columns=["Zona","Da (bpm)","A (bpm)"]
)

st.table(zone_hr_df)

st.markdown("---")

# ======================================================
# PROIEZIONE
# ======================================================

st.header("Proiezione Strategica")

target_fm=st.number_input("Target Massa Grassa (%)",3.0,20.0,step=0.1)
incremento_ftp=st.number_input("Incremento FTP (%)",0.0,50.0,step=0.1)

nuova_fm_kg = massa_magra*(target_fm/(100-target_fm))
nuovo_peso = massa_magra+nuova_fm_kg
nuova_ftp = ftp*(1+incremento_ftp/100)
nuovo_wkg = nuova_ftp/nuovo_peso if nuovo_peso>0 else 0

st.write(f"Nuovo peso: {nuovo_peso:.2f} kg")
st.write(f"Nuova FTP: {nuova_ftp:.2f} W")
st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")

# ======================================================
# PDF ÉLITE
# ======================================================

if st.button("Genera PDF Élite"):

    class PDF(FPDF):
        def header(self):
            try:
                self.image("logo.png", 80, 8, 50)
                self.ln(28)
            except:
                self.ln(18)
            self.set_font("Arial","B",16)
            self.cell(0,10,"PERFORMANCE REPORT",0,1,"C")
            self.set_font("Arial","",11)
            self.cell(0,6,f"{nome} {cognome}",0,1,"C")
            self.ln(6)

        def footer(self):
            self.set_y(-12)
            self.set_font("Arial","I",8)
            self.cell(0,5,f"Pagina {self.page_no()}",0,0,"C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"KPI",0,1)

    pdf.set_font("Arial","",10)
    pdf.multi_cell(0,6,f"BMI: {bmi:.2f}")
    pdf.multi_cell(0,6,f"FTP: {ftp:.0f} W")
    pdf.multi_cell(0,6,f"W/kg: {wkg:.2f}")
    pdf.multi_cell(0,6,f"FM%: {fm:.1f}")

    # Grafico
    plt.figure(figsize=(6,3))
    plt.bar(zone_df["Zona"], zone_df["A (W)"])
    plt.title("Distribuzione Zone FTP")
    plt.tight_layout()
    plt.savefig("chart.png")
    plt.close()

    pdf.image("chart.png", x=pdf.l_margin, w=170)
    os.remove("chart.png")

    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    st.download_button("Scarica PDF Performance Élite",
                       data=pdf_bytes,
                       file_name="report_performance_elite.pdf",
                       mime="application/pdf")
