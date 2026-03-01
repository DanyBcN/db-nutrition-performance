import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from fpdf import FPDF
import os

# ---------------------------------------------------------
# CONFIGURAZIONE
# ---------------------------------------------------------
st.set_page_config(page_title="Performance Lab Pro", layout="wide", page_icon="🧬")

DB_NAME = "performance_lab_pro.db"
LOGO_PATH = "Logo NUTRITION AND PERFORMANCE.png"

# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------
def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    with get_connection() as conn:
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS atleti (
                        id INTEGER PRIMARY KEY,
                        nome TEXT,
                        cognome TEXT,
                        altezza REAL,
                        profilo TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS visite (
                        id INTEGER PRIMARY KEY,
                        atleta_id INTEGER,
                        data TEXT,
                        peso REAL,
                        fm REAL,
                        ftp REAL,
                        lthr INTEGER,
                        peso_t REAL,
                        fm_t REAL,
                        ftp_t REAL,
                        dist REAL,
                        grad REAL,
                        bike REAL,
                        t_att REAL,
                        t_tar REAL,
                        FOREIGN KEY(atleta_id) REFERENCES atleti(id))''')
        conn.commit()

init_db()

# ---------------------------------------------------------
# MOTORE SCIENTIFICO
# ---------------------------------------------------------
class BioPerformance:

    @staticmethod
    def calculate_ftp(tipo, valore):
        if tipo == "Manuale":
            return valore
        if tipo == "Test 20'":
            return valore * 0.95
        if tipo == "Test 8'":
            return valore * 0.90
        if tipo == "Incrementale (MAP)":
            return valore * 0.75
        return valore

    @staticmethod
    def estimate_time(watt, peso, km, grad, bike):
        forza = (peso + bike) * 9.81 * ((grad/100) + 0.005)
        if forza <= 0 or watt <= 0:
            return 0
        vel = watt / forza
        tempo = (km * 1000) / vel
        return tempo / 60

    @staticmethod
    def get_zones(ftp, lthr):
        return [
            ("Z1 Recupero", 0, int(ftp*0.55), 0, int(lthr*0.68)),
            ("Z2 Endurance", int(ftp*0.56), int(ftp*0.75), int(lthr*0.69), int(lthr*0.83)),
            ("Z3 Tempo", int(ftp*0.76), int(ftp*0.90), int(lthr*0.84), int(lthr*0.94)),
            ("Z4 Soglia", int(ftp*0.91), int(ftp*1.05), int(lthr*0.95), int(lthr*1.05)),
            ("Z5 VO2max", int(ftp*1.06), int(ftp*1.20), int(lthr*1.06), 220),
        ]

def pdf_safe(text):
    rep = {"à":"a","è":"e","é":"e","ì":"i","ò":"o","ù":"u"}
    for k,v in rep.items():
        text = text.replace(k,v)
    return text

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    st.markdown("---")
    menu = st.radio("MENU", ["Nuova Valutazione", "Archivio"])

# ---------------------------------------------------------
# NUOVA VALUTAZIONE
# ---------------------------------------------------------
if menu == "Nuova Valutazione":

    st.header("Protocollo di Valutazione Biometrica")

    with get_connection() as conn:
        db_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)

    cognomi = sorted(db_atleti['cognome'].dropna().unique().tolist())
    cognome = st.text_input("Cognome")

    suggerimenti = [c for c in cognomi if cognome.lower() in c.lower()]
    if suggerimenti:
        st.info(f"Cognome già presente: {suggerimenti}")

    nome = st.text_input("Nome")
    altezza = st.number_input("Altezza (cm)", 120, 230, 175)
    data_analisi = st.date_input("Data Analisi", date.today())
    profilo = st.selectbox("Profilo", ["Scalatore","Passista","Triatleta","Granfondista"])

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Stato Attuale")
        peso = st.number_input("Peso (kg)",40.0,150.0,70.0)
        fm = st.number_input("FM (%)",3.0,45.0,15.0)
        metodo = st.selectbox("Metodo FTP",["Manuale","Test 20'","Test 8'","Incrementale (MAP)"])
        valore = st.number_input("Valore Test (W)",50,600,250)
        ftp = BioPerformance.calculate_ftp(metodo,valore)
        lthr = st.number_input("LTHR (bpm)",80,220,160)
        st.caption(f"FTP calcolata: {ftp:.0f} W")

    with col2:
        st.subheader("Target")
        peso_t = st.number_input("Peso Target",40.0,150.0,68.0)
        fm_t = st.number_input("FM Target",3.0,40.0,10.0)
        ftp_t = st.number_input("FTP Target",50,600,280)

    with col3:
        st.subheader("Scenario Salita")
        dist = st.number_input("Km Salita",0.1,50.0,10.0)
        grad = st.number_input("Pendenza (%)",0.0,20.0,7.0)
        bike = st.number_input("Peso Bici (kg)",5.0,15.0,7.5)

    if st.button("Genera Analisi"):

        t_att = BioPerformance.estimate_time(ftp,peso,dist,grad,bike)
        t_tar = BioPerformance.estimate_time(ftp_t,peso_t,dist,grad,bike)

        bmi = peso/((altezza/100)**2)
        bmi_t = peso_t/((altezza/100)**2)

        wkg_a = ftp/peso
        wkg_t = ftp_t/peso_t

        st.subheader("Analisi Biometrica")
        st.write(f"BMI Attuale: {bmi:.2f}")
        st.write(f"BMI Target: {bmi_t:.2f}")
        st.write(f"Peso: {peso} → {peso_t}")
        st.write(f"FM: {fm}% → {fm_t}%")

        st.subheader("Performance Salita")
        st.write(f"{dist} km @ {grad}%")
        st.write(f"Tempo Attuale: {t_att:.2f} min ({wkg_a:.2f} w/kg)")
        st.write(f"Tempo Target: {t_tar:.2f} min ({wkg_t:.2f} w/kg)")
        st.success(f"Miglioramento: {t_att-t_tar:.2f} minuti")

        st.subheader("Zone Allenamento")
        zones = BioPerformance.get_zones(ftp_t,lthr)
        for z in zones:
            st.write(f"{z[0]} | {z[1]}-{z[2]} W | {z[3]}-{z[4]} bpm")

        # PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial","B",16)
        pdf.cell(0,10,"PERFORMANCE LAB PRO",0,1,"C")
        pdf.set_font("Arial","",12)
        pdf.cell(0,8,f"Atleta: {nome} {cognome}",0,1)
        pdf.cell(0,8,f"Data: {data_analisi}",0,1)
        pdf.ln(5)
        pdf.cell(0,8,f"BMI: {bmi:.2f} -> {bmi_t:.2f}",0,1)
        pdf.cell(0,8,f"Tempo salita: {t_att:.2f} -> {t_tar:.2f} min",0,1)

        st.download_button("Scarica PDF",
                           data=pdf.output(dest="S").encode("latin-1","ignore"),
                           file_name=f"Report_{cognome}.pdf")

# ---------------------------------------------------------
# ARCHIVIO
# ---------------------------------------------------------
if menu == "Archivio":

    st.header("Archivio Atleti")

    with get_connection() as conn:
        atleti = pd.read_sql_query("SELECT * FROM atleti", conn)

    if not atleti.empty:
        sel = st.selectbox("Seleziona atleta",
                           atleti.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}",axis=1))
        a_id = int(sel.split(" - ")[0])

        with get_connection() as conn:
            visite = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id}", conn)

        st.dataframe(visite)

        with st.expander("Elimina Visita"):
            vid = st.selectbox("ID Visita",visite['id'])
            if st.button("Elimina"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM visite WHERE id=?",(vid,))
                    conn.commit()
                st.success("Eliminata")
                st.rerun()

        with st.expander("Elimina Atleta"):
            if st.button("Elimina Atleta Completo"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM visite WHERE atleta_id=?",(a_id,))
                    conn.execute("DELETE FROM atleti WHERE id=?",(a_id,))
                    conn.commit()
                st.success("Atleta eliminato")
                st.rerun()
    else:
        st.info("Nessun atleta presente.")
