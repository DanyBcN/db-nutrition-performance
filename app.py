import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd

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
# FUNZIONI CODICE FISCALE
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

metodo = st.selectbox("Metodo calcolo FTP",
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
# ZONE
# ======================================================

zone = [("Z1",0.00,0.55),("Z2",0.56,0.75),("Z3",0.76,0.90),
        ("Z4",0.91,1.05),("Z5",1.06,1.20),
        ("Z6",1.21,1.50),("Z7",1.51,2.00)]

zone_hr=[("Z1",0.81,0.89),("Z2",0.90,0.93),
         ("Z3",0.94,0.99),("Z4",1.00,1.05),
         ("Z5",1.06,1.15)]

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

# ======================================================
# PDF PREMIUM STUDIO PRIVATO
# ======================================================

if st.button("Genera PDF Premium"):

    class PDF(FPDF):
        def header(self):
            try:
                self.image("logo.png", 80, 8, 50)
                self.ln(30)
            except:
                self.ln(15)
            self.set_font("Arial","B",14)
            self.cell(0,10,"REPORT VALUTAZIONE METABOLICO-FUNZIONALE",0,1,"C")
            self.ln(5)

        def footer(self):
            self.set_y(-10)
            self.set_font("Arial","I",8)
            self.cell(0,5,f"Pagina {self.page_no()}",0,0,"C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # ==================================================
    # DATI ANAGRAFICI
    # ==================================================
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"DATI ANAGRAFICI",0,1)
    pdf.set_font("Arial", size=10)

    pdf.cell(95,8,f"Nome: {nome}",1)
    pdf.cell(95,8,f"Cognome: {cognome}",1,1)

    pdf.cell(95,8,f"Sesso: {sesso}",1)
    pdf.cell(95,8,f"Eta: {eta} anni",1,1)

    pdf.cell(95,8,f"Data nascita: {data_nascita.strftime('%d/%m/%Y')}",1)
    pdf.cell(95,8,f"Codice Fiscale: {cf}",1,1)

    pdf.cell(95,8,f"Comune: {comune}",1)
    pdf.cell(95,8,f"Provincia: {provincia}",1,1)

    pdf.cell(190,8,f"Email: {email}",1,1)
    pdf.cell(190,8,f"Telefono: {telefono}",1,1)
    pdf.cell(190,8,f"Indirizzo: {indirizzo}",1,1)

    pdf.ln(5)

    # ==================================================
    # ANTROPOMETRIA
    # ==================================================
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"VALUTAZIONE ANTROPOMETRICA",0,1)
    pdf.set_font("Arial", size=10)

    pdf.cell(63,8,f"Peso: {peso:.2f} kg",1)
    pdf.cell(63,8,f"Altezza: {altezza:.0f} cm",1)
    pdf.cell(64,8,f"BMI: {bmi:.2f}",1,1)

    pdf.cell(95,8,f"Classificazione: {classificazione}",1)
    pdf.cell(95,8,f"FM%: {fm:.2f}",1,1)

    pdf.cell(95,8,f"Massa grassa: {fm_kg:.2f} kg",1)
    pdf.cell(95,8,f"Massa magra: {massa_magra:.2f} kg",1,1)

    pdf.ln(5)

    # ==================================================
    # PERFORMANCE
    # ==================================================
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"PERFORMANCE",0,1)
    pdf.set_font("Arial", size=10)

    pdf.cell(95,8,f"Metodo FTP: {metodo}",1)
    pdf.cell(95,8,f"FTP: {ftp:.2f} W",1,1)

    pdf.cell(95,8,f"W/kg: {wkg:.2f}",1)
    pdf.cell(95,8,f"FTHR: {fthr:.0f} bpm",1,1)

    pdf.ln(5)

    # ==================================================
    # ZONE POTENZA
    # ==================================================
    if ftp > 0:

        pdf.set_font("Arial","B",12)
        pdf.cell(0,8,"ZONE DI POTENZA",0,1)

        pdf.set_font("Arial","B",10)
        pdf.cell(40,8,"Zona",1)
        pdf.cell(75,8,"Da (W)",1)
        pdf.cell(75,8,"A (W)",1,1)

        pdf.set_font("Arial", size=10)

        for z,a,b in zone:
            pdf.cell(40,8,z,1)
            pdf.cell(75,8,str(round(a*ftp)),1)
            pdf.cell(75,8,str(round(b*ftp)),1,1)

        pdf.ln(5)

    # ==================================================
    # ZONE CARDIO
    # ==================================================
    if fthr > 0:

        pdf.set_font("Arial","B",12)
        pdf.cell(0,8,"ZONE CARDIO",0,1)

        pdf.set_font("Arial","B",10)
        pdf.cell(40,8,"Zona",1)
        pdf.cell(75,8,"Da (bpm)",1)
        pdf.cell(75,8,"A (bpm)",1,1)

        pdf.set_font("Arial", size=10)

        for z,a,b in zone_hr:
            pdf.cell(40,8,z,1)
            pdf.cell(75,8,str(round(a*fthr)),1)
            pdf.cell(75,8,str(round(b*fthr)),1,1)

        pdf.ln(5)

    # ==================================================
    # PROIEZIONE
    # ==================================================
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8,"PROIEZIONE STRATEGICA",0,1)
    pdf.set_font("Arial", size=10)

    pdf.cell(95,8,f"Target FM: {target_fm:.2f}%",1)
    pdf.cell(95,8,f"Incremento FTP: {incremento_ftp:.2f}%",1,1)

    pdf.cell(95,8,f"Nuovo peso: {nuovo_peso:.2f} kg",1)
    pdf.cell(95,8,f"Nuova FTP: {nuova_ftp:.2f} W",1,1)

    pdf.cell(190,8,f"Nuovo W/kg: {nuovo_wkg:.2f}",1,1)

    # Output Cloud Safe
    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    st.download_button(
        "Scarica PDF Premium",
        data=pdf_bytes,
        file_name="report_premium.pdf",
        mime="application/pdf"
    )
