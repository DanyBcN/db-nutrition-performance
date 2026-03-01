import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
from datetime import date

# ---------------------------------------------------------
# SETUP & ENGINE SCIENTIFICO
# ---------------------------------------------------------

st.set_page_config(page_title="Performance Lab Pro", layout="wide", page_icon="🧬")

class ScientificEngine:
    @staticmethod
    def calculate_bmr_cunningham(massa_magra_kg):
        """Equazione di Cunningham: ideale per atleti con massa magra nota."""
        return 500 + (22 * massa_magra_kg)

    @staticmethod
    def calculate_ffmi(massa_magra_kg, altezza_m):
        """Calcolo Fat-Free Mass Index e FFMI Normalizzato."""
        ffmi = massa_magra_kg / (altezza_m ** 2)
        ffmi_norm = ffmi + 6.1 * (1.8 - altezza_m)
        return ffmi, ffmi_norm

    @staticmethod
    def estimate_vo2max(ftp, peso):
        """Stima indiretta VO₂max basata sulla potenza alla soglia (ml·kg⁻¹·min⁻¹)."""
        return (ftp * 10.8 / peso) + 7

    @staticmethod
    def get_power_zones(ftp):
        """Zone di potenza Coggan."""
        zones = [
            ("Z₁ Active Recovery", 0, 0.55),
            ("Z₂ Endurance", 0.56, 0.75),
            ("Z₃ Tempo", 0.76, 0.90),
            ("Z₄ Lactate Threshold", 0.91, 1.05),
            ("Z₅ VO₂max", 1.06, 1.20),
            ("Z₆ Anaerobic Capacity", 1.21, 1.50),
            ("Z₇ Neuromuscular", 1.51, 2.50)
        ]
        return [{"Zona": z[0], "Range": f"{int(z[1]*ftp)} - {int(z[2]*ftp)} W"} for z in zones]

    @staticmethod
    def get_hr_zones(fthr):
        """Zone FC basate sulla frequenza cardiaca di soglia (FTHR)."""
        zones = [
            ("Z₁ Active Recovery", 0, 0.68),
            ("Z₂ Endurance", 0.69, 0.83),
            ("Z₃ Tempo", 0.84, 0.94),
            ("Z₄ Lactate Threshold", 0.95, 1.05),
            ("Z₅ VO₂max", 1.06, 1.15)
        ]
        return [{"Zona": z[0], "Range": f"{int(z[1]*fthr)} - {int(z[2]*fthr)} bpm"} for z in zones]

# ---------------------------------------------------------
# DATABASE MANAGEMENT
# ---------------------------------------------------------

def init_db():
    conn = sqlite3.connect("performance_lab.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS atleti 
                 (id INTEGER PRIMARY KEY, nome TEXT, cognome TEXT, data_nascita TEXT, sesso TEXT, altezza REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visite 
                 (id INTEGER PRIMARY KEY, atleta_id INTEGER, data TEXT, peso REAL, fm REAL, ftp REAL, fthr REAL,
                 FOREIGN KEY(atleta_id) REFERENCES atleti(id))''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# INTERFACCIA UTENTE (SIDEBAR)
# ---------------------------------------------------------

st.sidebar.title("🧬 Performance Lab Pro")
menu = st.sidebar.radio("Navigazione", ["Nuova Valutazione", "Archivio Atleti", "Dashboard Statistica"])

# ---------------------------------------------------------
# MODULO: NUOVA VALUTAZIONE
# ---------------------------------------------------------

if menu == "Nuova Valutazione":
    st.header("📋 Protocollo di Valutazione Biometrica")
    
    with st.expander("Anagrafica Atleta", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        nome = col1.text_input("Nome")
        cognome = col2.text_input("Cognome")
        sesso = col3.selectbox("Sesso", ["M", "F"])
        altezza = col4.number_input("Altezza (cm)", 120, 230, 175) / 100

    col_left, col_mid, col_right = st.columns(3)

    with col_left:
        st.subheader("🧱 Antropometria")
        peso = st.number_input("Peso Corporeo (kg)", 30.0, 200.0, 70.0)
        fm = st.slider("Massa Grassa (%)", 3.0, 40.0, 12.0)
        
    with col_mid:
        st.subheader("⚡ Performance")
        metodo_ftp = st.selectbox("Protocollo Test", ["Diretto", "Test 20 min", "Ramp Test"])
        valore_test = st.number_input("Risultato Test (Watt)", 0, 1000, 250)
        fthr = st.number_input("FTHR (bpm)", 100, 220, 165)
        
        if metodo_ftp == "Test 20 min": ftp = valore_test * 0.95
        elif metodo_ftp == "Ramp Test": ftp = valore_test * 0.75
        else: ftp = valore_test

    with col_right:
        st.subheader("🎯 Goal Setting")
        peso_target = st.number_input("Peso Desiderato (kg)", 30.0, 200.0, peso)
        fm_target = st.slider("FM% Desiderata", 3.0, 40.0, fm)
        watt_inc = st.number_input("Incremento Watt (+)", 0, 100, 20)

    if st.button("🚀 Elabora Analisi Scientifica"):
        # Calcoli Scientifici Correnti
        massa_grassa_kg = peso * (fm / 100)
        massa_magra_kg = peso - massa_grassa_kg
        bmi = peso / (altezza ** 2)
        ffmi, ffmi_norm = ScientificEngine.calculate_ffmi(massa_magra_kg, altezza)
        bmr = ScientificEngine.calculate_bmr_cunningham(massa_magra_kg)
        wkg_current = ftp / peso
        vo2 = ScientificEngine.estimate_vo2max(ftp, peso)

        # Calcoli Proiezioni
        ftp_target = ftp + watt_inc
        wkg_target = ftp_target / peso_target
        delta_peso = peso - peso_target
        delta_fm = fm - fm_target

        # Visualizzazione Risultati
        st.divider()
        st.subheader("🔬 Report Analitico Attuale")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("BMI", f"{bmi:.1f} kg·m⁻²")
        m2.metric("FFMI Norm.", f"{ffmi_norm:.2f}")
        m3.metric("Potenza Specifica", f"{wkg_current:.2f} W·kg⁻¹")
        m4.metric("VO₂max Est.", f"{vo2:.1f} ml·kg⁻¹")

        st.subheader("🎯 Obiettivi e Proiezioni")
        c_goal1, c_goal2, c_goal3 = st.columns(3)
        c_goal1.metric("Delta Peso", f"{-delta_peso:.1f} kg", delta_color="inverse")
        c_goal2.metric("Delta FM%", f"{-delta_fm:.1f} %", delta_color="inverse")
        c_goal3.metric("W·kg⁻¹ Target", f"{wkg_target:.2f} W·kg⁻¹", f"+{wkg_target - wkg_current:.2f}")

        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Distribuzione Zone di Potenza (Watt)**")
            st.table(pd.DataFrame(ScientificEngine.get_power_zones(ftp)))
            st.info(f"**Metabolismo Basale (Cunningham):** {bmr:.0f} kcal/die")

        with c2:
            st.write("**Distribuzione Zone Cardio (BPM)**")
            st.table(pd.DataFrame(ScientificEngine.get_hr_zones(fthr)))
            # Grafico composizione corporea attuale
            fig, ax = plt.subplots(figsize=(5, 3))
            ax.pie([fm, 100-fm], labels=['FM', 'FFM'], autopct='%1.1f%%', colors=['#ff9999','#66b3ff'])
            ax.set_title("Composizione Corporea Attuale")
            st.pyplot(fig)

        # Salvataggio
        if st.button("💾 Salva in Database"):
            conn = sqlite3.connect("performance_lab.db")
            c = conn.cursor()
            c.execute("INSERT INTO atleti (nome, cognome, altezza, sesso) VALUES (?,?,?,?)", (nome, cognome, altezza, sesso))
            atleta_id = c.lastrowid
            c.execute("INSERT INTO visite (atleta_id, data, peso, fm, ftp, fthr) VALUES (?,?,?,?,?,?)", 
                      (atleta_id, date.today().isoformat(), peso, fm, ftp, fthr))
            conn.commit()
            conn.close()
            st.success("Dati archiviati con successo!")

# ---------------------------------------------------------
# MODULO: ARCHIVIO & TRENDS
# ---------------------------------------------------------

elif menu == "Archivio Atleti":
    st.header("📂 Archivio Storico")
    conn = sqlite3.connect("performance_lab.db")
    atleti_df = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    if not atleti_df.empty:
        scelta = st.selectbox("Seleziona Atleta", atleti_df.apply(lambda r: f"{r['id']} - {r['nome']} {r['cognome']}", axis=1))
        atleta_id = scelta.split(" - ")[0]
        
        visite_df = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={atleta_id} ORDER BY data ASC", conn)
        
        if not visite_df.empty:
            st.subheader("Evoluzione Performance")
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.line_chart(visite_df.set_index('data')[['peso', 'fm']])
            with col_b:
                st.line_chart(visite_df.set_index('data')[['ftp', 'fthr']])
                
            st.dataframe(visite_df)
        else:
            st.warning("Nessuna visita registrata per questo atleta.")
    else:
        st.info("Database vuoto.")
    conn.close()

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.caption(f"Performance Lab Pro v2.1 | © {date.today().year}")
