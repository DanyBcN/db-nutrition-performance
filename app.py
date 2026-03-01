import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
from datetime import date
from fpdf import FPDF

# ---------------------------------------------------------
# ENGINE SCIENTIFICO
# ---------------------------------------------------------

class ScientificEngine:
    @staticmethod
    def calculate_bmr_cunningham(massa_magra_kg):
        """Equazione di Cunningham: metabolismo basale basato sulla FFM."""
        return 500 + (22 * massa_magra_kg)

    @staticmethod
    def calculate_ffmi(massa_magra_kg, altezza_m):
        """Calcolo Fat-Free Mass Index Normalizzato."""
        ffmi = massa_magra_kg / (altezza_m ** 2)
        ffmi_norm = ffmi + 6.1 * (1.8 - altezza_m)
        return ffmi, ffmi_norm

    @staticmethod
    def estimate_climb_time(watt, peso_atleta, km, pendenza_pct, peso_bici=8.5):
        """Modello fisico della potenza in salita (resistenza gravitazionale)."""
        m_totale = peso_atleta + peso_bici
        g = 9.81
        pendenza_dec = pendenza_pct / 100
        # Resistenza (Gravità + Attrito volvente medio Crr 0.005)
        f_resistenza = m_totale * g * (pendenza_dec + 0.005)
        v_ms = watt / f_resistenza
        v_kh = v_ms * 3.6
        if v_kh <= 0: return 0
        tempo_minuti = (km / v_kh) * 60
        return tempo_minuti

    @staticmethod
    def get_power_zones(ftp):
        zones = [("Z₁ Rec.", 0, 0.55), ("Z₂ End.", 0.56, 0.75), ("Z₃ Tempo", 0.76, 0.90),
                 ("Z₄ Soglia", 0.91, 1.05), ("Z₅ VO₂max", 1.06, 1.20)]
        return [{"Zona": z[0], "Range": f"{int(z[1]*ftp)}-{int(z[2]*ftp)} W"} for z in zones]

    @staticmethod
    def get_hr_zones(fthr):
        zones = [("Z₁", 0, 0.68), ("Z₂", 0.69, 0.83), ("Z₃", 0.84, 0.94),
                 ("Z₄ (Soglia)", 0.95, 1.05), ("Z₅", 1.06, 1.15)]
        return [{"Zona": z[0], "Range": f"{int(z[1]*fthr)}-{int(z[2]*fthr)} bpm"} for z in zones]

# ---------------------------------------------------------
# UTILITY PDF
# ---------------------------------------------------------

def clean_unicode(text):
    """Sostituisce caratteri speciali per compatibilità PDF latin-1."""
    rep = {"₂": "2", "⁻": "-", "¹": "1", "·": "*", "₀": "0", "₃": "3", "₄": "4"}
    for k, v in rep.items():
        text = text.replace(k, v)
    return text

def generate_pdf(atleta, d_att, d_tar, climb_info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, clean_unicode(f"REPORT PERFORMANCE: {atleta['nome']} {atleta['cognome']}"), 0, 1, 'C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 7, f"Data: {date.today()}", 0, 1, 'C')
    pdf.ln(10)

    # Dati Salita
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "Scenario di Salita", 0, 1, 'L')
    pdf.set_font("Arial", '', 11)
    pdf.cell(190, 7, f"Distanza: {climb_info['km']} km | Pendenza: {climb_info['grad']}% | Peso Bici: {climb_info['bici']} kg", 0, 1, 'L')
    pdf.ln(5)

    # Tabella Comparativa
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(60, 10, "Parametro", 1, 0, 'C', True)
    pdf.cell(65, 10, "Stato Attuale", 1, 0, 'C', True)
    pdf.cell(65, 10, "Stato Target", 1, 1, 'C', True)

    pdf.set_font("Arial", '', 11)
    data_rows = [
        ("Peso Corporeo", f"{d_att['peso']} kg", f"{d_tar['peso']} kg"),
        ("Massa Grassa (FM%)", f"{d_att['fm']}%", f"{d_tar['fm']}%"),
        ("Potenza FTP", f"{int(d_att['ftp'])} W", f"{int(d_tar['ftp'])} W"),
        ("Potenza Specifica", f"{d_att['wkg']:.2f} W/kg", f"{d_tar['wkg']:.2f} W/kg"),
        ("Tempo di Scalata", f"{d_att['tempo']:.2f} min", f"{d_tar['tempo']:.2f} min")
    ]
    for r in data_rows:
        pdf.cell(60, 10, r[0], 1)
        pdf.cell(65, 10, r[1], 1)
        pdf.cell(65, 10, r[2], 1)
        pdf.ln()

    pdf.ln(10)
    diff = d_att['tempo'] - d_tar['tempo']
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(190, 10, f"MIGLIORAMENTO STIMATO: -{diff:.2f} minuti", 0, 1, 'C')
    
    return pdf.output(dest='S')

# ---------------------------------------------------------
# INTERFACCIA STREAMLIT
# ---------------------------------------------------------

st.set_page_config(page_title="Performance Lab Pro", layout="wide", page_icon="🧬")
st.title("🧬 Performance Lab Pro v2.5")

with st.sidebar:
    st.header("⚙️ Impostazioni")
    menu = st.radio("Navigazione", ["Analisi e Predizione", "Archivio Atleti"])

if menu == "Analisi e Predizione":
    with st.expander("👤 Anagrafica Atleta", expanded=True):
        c_an1, c_an2, c_an3, c_an4 = st.columns(4)
        nome = c_an1.text_input("Nome")
        cognome = c_an2.text_input("Cognome")
        altezza = c_an3.number_input("Altezza (cm)", 100, 230, 175) / 100
        sesso = c_an4.selectbox("Sesso", ["M", "F"])

    col_att, col_tar, col_cli = st.columns(3)

    with col_att:
        st.subheader("🧱 Stato Attuale")
        peso = st.number_input("Peso (kg)", 30.0, 150.0, 70.0, step=0.1)
        fm = st.number_input("Massa Grassa (FM%)", 3.0, 45.0, 12.0, step=0.1)
        
        protocollo = st.selectbox("Protocollo Test FTP", ["Manuale", "Test 20 min", "Test 8 min", "Ramp Test"])
        val_test = st.number_input("Risultato Test (Watt)", 0, 1000, 250)
        
        if protocollo == "Test 20 min": ftp = val_test * 0.95
        elif protocollo == "Test 8 min": ftp = val_test * 0.90
        elif protocollo == "Ramp Test": ftp = val_test * 0.75
        else: ftp = float(val_test)
        
        fthr = st.number_input("FTHR (bpm)", 80, 220, 160)

    with col_tar:
        st.subheader("🎯 Obiettivi (Target)")
        peso_t = st.number_input("Peso Desiderato (kg)", 30.0, 150.0, peso, step=0.1)
        fm_t = st.number_input("FM% Desiderata", 3.0, 45.0, fm, step=0.1)
        ftp_inc = st.number_input("Incremento FTP (+ Watt)", 0, 150, 20)
        ftp_t = ftp + ftp_inc

    with col_cli:
        st.subheader("🏔️ Scenario Salita")
        dist_km = st.number_input("Lunghezza (km)", 0.1, 100.0, 10.0, step=0.1)
        grad = st.number_input("Pendenza Media (%)", 0.0, 25.0, 7.0, step=0.1)
        peso_bici = st.number_input("Peso Equipaggiamento (kg)", 5.0, 20.0, 8.5, step=0.1)

    if st.button("🚀 ELABORA ANALISI SCIENTIFICA"):
        # Logica di calcolo
        m_magra_kg = peso * (1 - (fm/100))
        bmr = ScientificEngine.calculate_bmr_cunningham(m_magra_kg)
        wkg_att = ftp / peso
        wkg_tar = ftp_t / peso_t
        
        t_att = ScientificEngine.estimate_climb_time(ftp, peso, dist_km, grad, peso_bici)
        t_tar = ScientificEngine.estimate_climb_time(ftp_t, peso_t, dist_km, grad, peso_bici)
        
        # Visualizzazione Metriche
        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("W·kg⁻¹ Attuale", f"{wkg_att:.2f}")
        m2.metric("W·kg⁻¹ Target", f"{wkg_tar:.2f}", f"{wkg_tar-wkg_att:.2f}")
        m3.metric("Tempo Attuale", f"{t_att:.2f} min")
        m4.metric("Tempo Target", f"{t_tar:.2f} min", f"-{t_att-t_tar:.2f}", delta_color="inverse")

        # Layout Risultati Dettagliati
        res_l, res_r = st.columns(2)
        with res_l:
            st.write("### 📊 Zone di Potenza Target")
            st.table(ScientificEngine.get_power_zones(ftp_t))
            st.info(f"Metabolismo Basale (Cunningham): **{bmr:.0f} kcal/die**")

        with res_r:
            st.write("### ❤️ Zone Cardio (FTHR)")
            st.table(ScientificEngine.get_hr_zones(fthr))

        # PDF Report
        st.divider()
        d_att_dict = {"peso": peso, "fm": fm, "ftp": ftp, "wkg": wkg_att, "tempo": t_att}
        d_tar_dict = {"peso": peso_t, "fm": fm_t, "ftp": ftp_t, "wkg": wkg_tar, "tempo": t_tar}
        climb_info = {"km": dist_km, "grad": grad, "bici": peso_bici}
        atleta_dict = {"nome": nome, "cognome": cognome}
        
        try:
            pdf_out = generate_pdf(atleta_dict, d_att_dict, d_tar_dict, climb_info)
            st.download_button(
                label="📄 Scarica Report PDF",
                data=pdf_out,
                file_name=f"Report_{cognome}_{date.today()}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Errore generazione PDF: {e}")

# ---------------------------------------------------------
# DATABASE (Esempio rapido per inizializzazione)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect("performance_lab.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS visite 
                 (id INTEGER PRIMARY KEY, atleta TEXT, data TEXT, wkg_att REAL, wkg_tar REAL)''')
    conn.commit()
    conn.close()

init_db()
