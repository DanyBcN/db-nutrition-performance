import streamlit as st
from datetime import date
from PIL import Image
from fpdf import FPDF
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

# ====================================================import streamlit as st
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
# FUNZIONI CODICE FISCALE CORRETTO (STRUTTURA UFFICIALE)
# ======================================================

mesi_cf = "ABCDEHLMPRST"

def consonanti(s):
    return "".join([c for c in s.upper() if c in "BCDFGHJKLMNPQRSTVWXYZ"])

def vocali(s):
    return "".join([c for c in s.upper() if c in "AEIOU"])

def carattere_controllo(cf15):
    valori_dispari = {
        '0':1,'1':0,'2':5,'3':7,'4':9,'5':13,'6':15,'7':17,'8':19,'9':21,
        'A':1,'B':0,'C':5,'D':7,'E':9,'F':13,'G':15,'H':17,'I':19,'J':21,
        'K':2,'L':4,'M':18,'N':20,'O':11,'P':3,'Q':6,'R':8,'S':12,'T':14,
        'U':16,'V':10,'W':22,'X':25,'Y':24,'Z':23
    }

    valori_pari = {c:i for i,c in enumerate("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")}

    s = 0
    for i,c in enumerate(cf15):
        if (i+1) % 2 == 0:
            s += valori_pari[c]
        else:
            s += valori_dispari[c]

    return chr((s % 26) + ord('A'))

def genera_cf(nome, cognome, data, sesso):
    cons_cogn = consonanti(cognome)
    voc_cogn = vocali(cognome)
    cod_cogn = (cons_cogn + voc_cogn + "XXX")[:3]

    cons_nome = consonanti(nome)
    if len(cons_nome) >= 4:
        cod_nome = cons_nome[0] + cons_nome[2] + cons_nome[3]
    else:
        cod_nome = (cons_nome + vocali(nome) + "XXX")[:3]

    anno = str(data.year)[2:]
    mese = mesi_cf[data.month - 1]
    giorno = data.day + (40 if sesso == "F" else 0)
    giorno = f"{giorno:02d}"

    # Codice comune simulato coerente a 4 caratteri (non provincia!)
    codice_comune = "Z404"

    cf15 = cod_cogn + cod_nome + anno + mese + giorno + codice_comune
    controllo = carattere_controllo(cf15)

    return cf15 + controllo

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
if nome and cognome:
    cf = genera_cf(nome, cognome, data_nascita, sesso)

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

# ======================================================
# ZONE POTENZA
# ======================================================

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

    df_zone = pd.DataFrame(dati,columns=["Zona","Da (W)","A (W)"])
    st.table(df_zone)

# ======================================================
# ZONE CARDIO
# ======================================================

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

    df_hr = pd.DataFrame(dati_hr,columns=["Zona","Da (bpm)","A (bpm)"])
    st.table(df_hr)

st.markdown("---")

# ======================================================
# PROIEZIONE
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
# PDF COMPLETO STRUTTURATO
# ======================================================

if st.button("Genera PDF Completo"):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    pdf.cell(0,8,"REPORT VALUTAZIONE COMPLETA", ln=True, align="C")
    pdf.ln(5)

    pdf.cell(0,8,f"Nome: {nome} {cognome}", ln=True)
    pdf.cell(0,8,f"Sesso: {sesso}", ln=True)
    pdf.cell(0,8,f"Data nascita: {data_nascita.strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(0,8,f"Comune: {comune} ({provincia})", ln=True)
    pdf.cell(0,8,f"Codice Fiscale: {cf}", ln=True)
    pdf.cell(0,8,f"BMI: {bmi:.2f} ({classificazione})", ln=True)
    pdf.cell(0,8,f"Massa grassa: {fm_kg:.2f} kg", ln=True)
    pdf.cell(0,8,f"Massa magra: {massa_magra:.2f} kg", ln=True)
    pdf.cell(0,8,f"Metodo FTP: {metodo}", ln=True)
    pdf.cell(0,8,f"FTP: {ftp:.2f} W", ln=True)
    pdf.cell(0,8,f"W/kg: {wkg:.2f}", ln=True)
    pdf.cell(0,8,f"Nuovo W/kg: {nuovo_wkg:.2f}", ln=True)

    pdf.output("report_completo.pdf")

    with open("report_completo.pdf","rb") as f:
        st.download_button("Scarica PDF Completo",f,"report_completo.pdf")==
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
# FUNZIONI CODICE FISCALE (STRUTTURALE CORRETTO)
# ======================================================

mesi_cf = "ABCDEHLMPRST"

def consonanti(s):
    return "".join([c for c in s.upper() if c in "BCDFGHJKLMNPQRSTVWXYZ"])

def vocali(s):
    return "".join([c for c in s.upper() if c in "AEIOU"])

def carattere_controllo(cf15):
    dispari = {
        **dict(zip("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        [1,0,5,7,9,13,15,17,19,21,
         1,0,5,7,9,13,15,17,19,21,
         2,4,18,20,11,3,6,8,12,14,
         16,10,22,25,24,23]))
    }

    pari = {c:i for i,c in enumerate("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")}

    s = 0
    for i, c in enumerate(cf15):
        if (i+1) % 2 == 0:
            s += pari[c]
        else:
            s += dispari[c]

    return chr((s % 26) + ord('A'))

def genera_cf(nome, cognome, data, sesso, provincia):
    cons_cogn = consonanti(cognome)
    voc_cogn = vocali(cognome)
    cod_cogn = (cons_cogn + voc_cogn + "XXX")[:3]

    cons_nome = consonanti(nome)
    if len(cons_nome) >= 4:
        cod_nome = cons_nome[0] + cons_nome[2] + cons_nome[3]
    else:
        cod_nome = (cons_nome + vocali(nome) + "XXX")[:3]

    anno = str(data.year)[2:]
    mese = mesi_cf[data.month - 1]
    giorno = data.day + (40 if sesso == "F" else 0)
    giorno = f"{giorno:02d}"

    codice_prov = provincia.upper().ljust(4,"X")[:4]

    cf15 = cod_cogn + cod_nome + anno + mese + giorno + codice_prov
    controllo = carattere_controllo(cf15)

    return cf15 + controllo

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
if nome and cognome and provincia:
    cf = genera_cf(nome, cognome, data_nascita, sesso, provincia)

st.write(f"Codice Fiscale: {cf}")

st.markdown("---")

# ======================================================
# ANTROPOMETRIA
# ======================================================

st.header("Valutazione Antropometrica")

peso = st.number_input("Peso (kg)", 30.0, 200.0)
altezza = st.number_input("Altezza (cm)", 100.0, 220.0)
fm = st.number_input("Massa grassa (%)", 3.0, 50.0)

bmi = 0
classificazione = ""

if peso and altezza:
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

# ======================================================
# ZONE POTENZA
# ======================================================

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

    st.table(pd.DataFrame(dati,columns=["Zona","Da (W)","A (W)"]))

# ======================================================
# ZONE CARDIO
# ======================================================

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

    st.table(pd.DataFrame(dati_hr,columns=["Zona","Da (bpm)","A (bpm)"]))

st.markdown("---")

# ======================================================
# PROIEZIONE
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

if st.button("Genera PDF"):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    pdf.cell(0,8,"REPORT VALUTAZIONE", ln=True)
    pdf.ln(5)

    pdf.cell(0,8,f"Nome: {nome} {cognome}", ln=True)
    pdf.cell(0,8,f"Data nascita: {data_nascita.strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(0,8,f"Codice Fiscale: {cf}", ln=True)
    pdf.cell(0,8,f"BMI: {bmi:.2f} ({classificazione})", ln=True)
    pdf.cell(0,8,f"FTP: {ftp:.2f} W", ln=True)
    pdf.cell(0,8,f"W/kg: {wkg:.2f}", ln=True)
    pdf.cell(0,8,f"Nuovo W/kg: {nuovo_wkg:.2f}", ln=True)

    pdf.output("report.pdf")

    with open("report.pdf","rb") as f:
        st.download_button("Scarica PDF",f,"report.pdf")
