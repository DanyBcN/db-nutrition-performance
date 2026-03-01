import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
from datetime import date
from fpdf import FPDF
import base64

# ---------------------------------------------------------
# SETUP & ENGINE SCIENTIFICO
# ---------------------------------------------------------

st.set_page_config(page_title="Performance Lab Pro v2.2", layout="wide", page_icon="🧬")

class ScientificEngine:
    @staticmethod
    def calculate_bmr_cunningham(massa_magra_kg):
        return 500 + (22 * massa_magra_kg)

    @staticmethod
    def calculate_ffmi(massa_magra_kg, altezza_m):
        ffmi = massa_magra_kg / (altezza_m ** 2)
        ffmi_norm = ffmi + 6.1 * (1.8 - altezza_m)
        return ffmi, ffmi_norm

    @staticmethod
    def estimate_vo2max(ftp, peso):
        return (ftp * 10.8 / peso) + 7

    @staticmethod
    def estimate_climb_time(watt, peso_atleta, km, pendenza_pct, peso_bici=8.0):
        """
        Modello fisico semplificato per la salita.
        P = F * v -> v = P / F
        F_gravità = m * g * sin(theta)
        """
        m_totale = peso_atleta + peso_bici
        g = 9.81
        pendenza_dec = pendenza_pct / 100
        
        # Forza resistente (principalmente gravità e attrito volvente Crr=0.005)
        f_resistenza = m_totale * g * (pendenza_dec + 0.005)
        
        # Velocità in m/s (ignorando aero sotto i 20km/h in salita ripida)
        v_ms = watt / f_resistenza
        v_kh = v_ms * 3.6
        
        tempo_ore = km / v_kh
        return tempo_ore * 60  # Ritorna minuti

    @staticmethod
    def get_power_zones(ftp):
        zones = [("Z₁ Active Recovery", 0, 0.55), ("Z₂ Endurance", 0.56, 0.75),
                 ("Z₃ Tempo", 0.76, 0.90), ("Z₄ Lactate Threshold", 0.91, 1.05),
                 ("Z₅ VO₂max", 1.06, 1.20), ("Z₆ Anaerobic Capacity", 1.21, 1.50)]
        return [{"Zona": z[0], "Range": f"{int(z[1]*ftp)} - {int(z[2]*ftp)} W"} for z in zones]

# ---------------------------------------------------------
# GENERATORE PDF
# ---------------------------------------------------------

def create_pdf(atleta, dati_attuali, dati_target):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, f"Performance Report: {atleta['nome']} {atleta['cognome']}", 0, 1, 'C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 10, f"Data Valutazione: {date.today().isoformat()}", 0, 1, 'C')
    pdf.ln(10)

    # Tabella Comparativa
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, "Parametro", 1)
    pdf.cell(65, 10, "Attuale (Stato A)", 1)
    pdf.cell(65, 10, "Obiettivo (Stato B)", 1)
    pdf.ln()

    pdf.set_font("Arial", '', 11)
    metrics = [
        ("Peso Corporeo", f"{dati_attuali['peso']} kg", f"{dati_target['peso']} kg"),
        ("Massa Grassa", f"{dati_attuali['fm']}%", f"{dati_target['fm']}%"),
        ("Potenza Soglia (FTP)", f"{int(dati_attuali['ftp'])} W", f"{int(dati_target['ftp'])} W"),
        ("Potenza Specifica", f"{dati_attuali['wkg']:.2f} W·kg⁻¹", f"{dati_target['wkg']:.2f} W·kg⁻¹"),
        ("Tempo Scalata", f"{dati_attuali['tempo']:.2f} min", f"{dati_target['tempo']:.2f} min"),
    ]

    for m in metrics:
        pdf.cell(60, 10, m[0], 1)
        pdf.cell(65, 10, m[1], 1)
        pdf.cell(65, 10, m[2], 1)
        pdf.ln()

    pdf.ln(5)
    diff_tempo = dati_attuali['tempo'] - dati_target['tempo']
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"Guadagno Temporale Stimato: {diff_tempo:.2f} minuti", 0, 1, 'L')
    
    return pdf.output(dest='S').encode('latin-1')

# ---------------------------------------------------------
# INTERFACCIA STREAMLIT
# ---------------------------------------------------------

st.sidebar.title("🧬 Performance Lab Pro")
menu = st.sidebar.radio("Navigazione", ["Nuova Valutazione", "Archivio Atleti"])

if menu == "Nuova Valutazione":
    st.header("📋 Analisi Biometrica e Predizione Performance")
    
    with st.expander("Anagrafica Atleta", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        nome = col1.text_input("Nome")
        cognome = col2.text_input("Cognome")
        sesso = col3.selectbox("Sesso", ["M", "F"])
        altezza = col4.number_input("Altezza (cm)", 120, 230, 175) / 100

    col_l, col_m, col_r = st.columns(3)

    with col_l:
        st.subheader("🧱 Stato Attuale")
        peso = st.number_input("Peso (kg)", 30.0, 150.0, 75.0)
        fm = st.slider("FM %", 3.0, 40.0, 15.0)
        ftp = st.number_input("FTP Attuale (W)", 50, 600, 250)
        fthr = st.number_input("FTHR (bpm)", 100, 210, 165)
        
    with col_m:
        st.subheader("🎯 Target")
        peso_t = st.number_input("Peso Target (kg)", 30.0, 150.0, 72.0)
        fm_t = st.slider("FM % Target", 3.0, 40.0, 12.0)
        inc_w = st.number_input("Incremento Potenza (+W)", 0, 100, 15)
        ftp_t = ftp + inc_w

    with col_r:
        st.subheader("🏔️ Segmento di Salita")
        dist_km = st.number_input("Lunghezza Salita (km)", 0.1, 50.0, 10.0)
        pendenza = st.number_input("Pendenza Media (%)", 0.0, 25.0, 7.0)
        peso_bici = st.number_input("Peso Equipaggiamento (kg)", 5.0, 15.0, 8.5)

    if st.button("🚀 Elabora Analisi Scientifica"):
        # Calcoli Stato Attuale
        t_attuale = ScientificEngine.estimate_climb_time(ftp, peso, dist_km, pendenza, peso_bici)
        wkg_attuale = ftp / peso
        
        # Calcoli Stato Target
        t_target = ScientificEngine.estimate_climb_time(ftp_t, peso_t, dist_km, pendenza, peso_bici)
        wkg_target = ftp_t / peso_t
        
        st.divider()
        
        # Visualizzazione Metriche
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("W·kg⁻¹ Attuale", f"{wkg_attuale:.2f}")
        c2.metric("W·kg⁻¹ Target", f"{wkg_target:.2f}", f"{wkg_target-wkg_attuale:.2f}")
        c3.metric("Tempo Attuale", f"{t_attuale:.2f} min")
        c4.metric("Tempo Target", f"{t_target:.2f} min", f"-{t_attuale-t_target:.2f}", delta_color="inverse")

        # Report PDF
        atleta_info = {"nome": nome, "cognome": cognome}
        d_att = {"peso": peso, "fm": fm, "ftp": ftp, "wkg": wkg_attuale, "tempo": t_attuale}
        d_tar = {"peso": peso_t, "fm": fm_t, "ftp": ftp_t, "wkg": wkg_target, "tempo": t_target}
        
        pdf_data = create_pdf(atleta_info, d_att, d_tar)
        st.download_button(label="📄 Scarica Report PDF", 
                           data=pdf_data, 
                           file_name=f"Report_{cognome}_{date.today()}.pdf", 
                           mime="application/pdf")

        # Dettaglio Zone
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            st.write("**Zone di Potenza Target**")
            st.table(ScientificEngine.get_power_zones(ftp_t))
        with col_z2:
            st.write("**Composizione Corporea Proiettata**")
            fig, ax = plt.subplots()
            ax.pie([fm_t, 100-fm_t], labels=['FM Target', 'FFM Target'], autopct='%1.1f%%', colors=['#e74c3c','#2ecc71'])
            st.pyplot(fig)

st.sidebar.markdown("---")
st.sidebar.caption(f"Performance Lab Pro v2.2 | © {date.today().year}")
