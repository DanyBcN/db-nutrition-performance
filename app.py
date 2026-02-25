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
# ZONE (SEMPRE VISIBILI)
# ======================================================

st.subheader("Zone Potenza")

zone = [("Z1",0.00,0.55),("Z2",0.56,0.75),("Z3",0.76,0.90),
        ("Z4",0.91,1.05),("Z5",1.06,1.20),
        ("Z6",1.21,1.50),("Z7",1.51,2.00)]

dati_zone=[]
for z,a,b in zone:
    dati_zone.append([z, round(a*ftp) if ftp>0 else 0,
                         round(b*ftp) if ftp>0 else 0])

st.table(pd.DataFrame(dati_zone,
         columns=["Zona","Da (W)","A (W)"]))

st.subheader("Zone Cardio")

zone_hr=[("Z1",0.81,0.89),("Z2",0.90,0.93),
         ("Z3",0.94,0.99),("Z4",1.00,1.05),
         ("Z5",1.06,1.15)]

dati_hr=[]
for z,a,b in zone_hr:
    dati_hr.append([z, round(a*fthr) if fthr>0 else 0,
                       round(b*fthr) if fthr>0 else 0])

st.table(pd.DataFrame(dati_hr,
         columns=["Zona","Da (bpm)","A (bpm)"]))

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
# PDF PREMIUM ELEGANTE
# ======================================================

if st.button("Genera PDF Premium Elegante"):

    class PDF(FPDF):

        def header(self):
            try:
                self.image("logo.png", 80, 8, 50)
                self.ln(28)
            except:
                self.ln(15)

            self.set_font("Arial","B",16)
            self.cell(0,10,"VALUTAZIONE METABOLICO-FUNZIONALE",0,1,"C")
            self.set_font("Arial","",10)
            self.cell(0,6,f"{nome} {cognome}",0,1,"C")
            self.ln(5)

        def footer(self):
            self.set_y(-12)
            self.set_font("Arial","I",8)
            self.cell(0,5,f"Pagina {self.page_no()}",0,0,"C")

        def section_title(self, title):
            self.set_font("Arial","B",12)
            self.set_fill_color(230,230,230)
            self.cell(0,8,title,0,1,"L",True)
            self.ln(2)

        def kpi_box(self, label, value, x, y, w, h):
            self.set_xy(x,y)
            self.set_fill_color(245,245,245)
            self.rect(x,y,w,h,"DF")
            self.set_font("Arial","B",10)
            self.cell(w,h/2,label,0,2,"C")
            self.set_font("Arial","B",14)
            self.cell(w,h/2,value,0,2,"C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ==================================================
    # KPI SECTION
    # ==================================================
    pdf.section_title("INDICATORI PRINCIPALI")

    y_start = pdf.get_y()
    box_width = 45
    box_height = 20
    spacing = 5
    x_start = 20

    pdf.kpi_box("BMI", f"{bmi:.2f}", x_start, y_start, box_width, box_height)
    pdf.kpi_box("FTP (W)", f"{ftp:.0f}", x_start+box_width+spacing, y_start, box_width, box_height)
    pdf.kpi_box("W/kg", f"{wkg:.2f}", x_start+2*(box_width+spacing), y_start, box_width, box_height)
    pdf.kpi_box("FM %", f"{fm:.1f}", x_start+3*(box_width+spacing), y_start, box_width, box_height)

    pdf.ln(box_height + 10)

    # ==================================================
    # DATI ANAGRAFICI
    # ==================================================
    pdf.section_title("DATI ANAGRAFICI")

    pdf.set_font("Arial","",10)
    pdf.multi_cell(0,6,f"Sesso: {sesso}")
    pdf.multi_cell(0,6,f"Data nascita: {data_nascita.strftime('%d/%m/%Y')} - Eta: {eta}")
    pdf.multi_cell(0,6,f"Comune: {comune} ({provincia})")
    pdf.multi_cell(0,6,f"Codice Fiscale: {cf}")
    pdf.ln(4)

    # ==================================================
    # ANTROPOMETRIA
    # ==================================================
    pdf.section_title("VALUTAZIONE ANTROPOMETRICA")

    pdf.multi_cell(0,6,f"Peso: {peso:.2f} kg")
    pdf.multi_cell(0,6,f"Altezza: {altezza:.0f} cm")
    pdf.multi_cell(0,6,f"BMI: {bmi:.2f} ({classificazione})")
    pdf.multi_cell(0,6,f"Massa grassa: {fm_kg:.2f} kg")
    pdf.multi_cell(0,6,f"Massa magra: {massa_magra:.2f} kg")
    pdf.ln(4)

    # ======================================================
# PDF PERFORMANCE ÉLITE
# ======================================================

if st.button("Genera PDF Élite"):

    import matplotlib.pyplot as plt
    import os

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

        def section_title(self, title):
            self.set_font("Arial","B",12)
            self.set_fill_color(240,240,240)
            self.cell(0,8,title,0,1,"L",True)
            self.ln(3)

        def kpi_box(self, label, value, x, y):
            w = 40
            h = 22
            self.set_xy(x,y)
            self.set_fill_color(245,245,245)
            self.rect(x,y,w,h,"DF")

            self.set_font("Arial","B",9)
            self.cell(w,h/2,label,0,2,"C")

            self.set_font("Arial","B",14)
            self.cell(w,h/2,value,0,2,"C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ==================================================
    # KPI CENTRATI
    # ==================================================
    pdf.section_title("KEY PERFORMANCE INDICATORS")

    y = pdf.get_y()
    page_width = pdf.w - 2 * pdf.l_margin
    total_width = 4*40 + 3*10
    start_x = (page_width - total_width)/2 + pdf.l_margin

    pdf.kpi_box("BMI", f"{bmi:.2f}", start_x, y)
    pdf.kpi_box("FTP", f"{ftp:.0f} W", start_x+50, y)
    pdf.kpi_box("W/kg", f"{wkg:.2f}", start_x+100, y)
    pdf.kpi_box("FM%", f"{fm:.1f}", start_x+150, y)

    pdf.ln(30)

    # ==================================================
    # ZONE COLOR BAR
    # ==================================================
    pdf.section_title("ZONE DI POTENZA")

    zone_colors = [
        (0,180,0),     # verde
        (120,200,0),
        (200,200,0),
        (255,165,0),
        (255,120,0),
        (255,60,0),
        (220,0,0)      # rosso
    ]

    zone = [
        ("Z1",0.00,0.55),("Z2",0.56,0.75),("Z3",0.76,0.90),
        ("Z4",0.91,1.05),("Z5",1.06,1.20),
        ("Z6",1.21,1.50),("Z7",1.51,2.00)
    ]

    bar_width = (pdf.w - 2*pdf.l_margin) / len(zone)
    y_bar = pdf.get_y()

    for i,(z,a,b) in enumerate(zone):
        pdf.set_fill_color(*zone_colors[i])
        pdf.rect(pdf.l_margin + i*bar_width, y_bar, bar_width, 10, "F")

    pdf.ln(15)

    # ==================================================
    # TABELLA ZONE POTENZA
    # ==================================================
    pdf.set_font("Arial","B",10)
    pdf.cell(40,8,"Zona",1)
    pdf.cell(60,8,"Da (W)",1)
    pdf.cell(60,8,"A (W)",1,1)

    pdf.set_font("Arial","",10)

    for z,a,b in zone:
        pdf.cell(40,8,z,1)
        pdf.cell(60,8,str(round(a*ftp)),1)
        pdf.cell(60,8,str(round(b*ftp)),1,1)

    pdf.ln(6)

    # ==================================================
    # GRAFICO AUTOMATICO
    # ==================================================
    zone_labels = [z for z,_,_ in zone]
    zone_values = [round(b*ftp) for _,_,b in zone]

    plt.figure(figsize=(6,3))
    plt.bar(zone_labels, zone_values)
    plt.title("Distribuzione Zone FTP")
    plt.tight_layout()
    plt.savefig("zones_chart.png")
    plt.close()

    pdf.image("zones_chart.png", x=pdf.l_margin, w=170)
    os.remove("zones_chart.png")

    pdf.ln(10)

    # ==================================================
    # PROIEZIONE
    # ==================================================
    pdf.section_title("PROIEZIONE STRATEGICA")

    pdf.set_font("Arial","",10)
    pdf.multi_cell(0,6,f"Target FM: {target_fm:.2f}%")
    pdf.multi_cell(0,6,f"Incremento FTP: {incremento_ftp:.2f}%")
    pdf.multi_cell(0,6,f"Nuovo peso: {nuovo_peso:.2f} kg")
    pdf.multi_cell(0,6,f"Nuova FTP: {nuova_ftp:.2f} W")
    pdf.multi_cell(0,6,f"Nuovo W/kg: {nuovo_wkg:.2f}")

    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    st.download_button(
        "Scarica PDF Performance Élite",
        data=pdf_bytes,
        file_name="report_performance_elite.pdf",
        mime="application/pdf"
    )
