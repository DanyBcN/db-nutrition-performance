import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
from datetime import date
from fpdf import FPDF

# ---------------------------------------------------------
# ENGINE SCIENTIFICO (FISICA E BIOMETRIA)
# ---------------------------------------------------------

class ScientificEngine:
    @staticmethod
    def calculate_bmr_cunningham(massa_magra_kg):
        """Equazione di Cunningham: 500 + (22 * FFM)"""
        return 500 + (22 * massa_magra_kg)

    @staticmethod
    def estimate_climb_time(watt, peso_atleta, km, pendenza_pct, peso_bici=8.5):
        """
        Modello fisico della potenza in salita.
        Calcola il tempo basandosi sulla resistenza gravitazionale.
        """
        m_totale = peso_atleta + peso_bici
        g = 9.81
        pendenza_dec = pendenza_pct / 100
        # Forza resistente: Gravità + Attrito volvente (Crr 0.005)
        f_resistenza = m_totale * g * (pendenza_dec + 0.005)
        v_ms = watt / f_resistenza
        v_kh = v_ms * 3.6
        if v_kh <= 0: return 0
        return (km / v_kh) * 60 # minuti

    @staticmethod
    def get_power_zones(ftp):
        zones = [("Z₁ Active Recovery", 0, 0.55), ("Z₂ Endurance", 0.56, 0.75), 
                 ("Z₃ Tempo", 0.76, 0.90), ("Z₄ Lactate Threshold", 0.91, 1.05),
                 ("Z₅ VO₂max", 1.06, 1.20)]
        return [{"Zona": z[0], "Range": f"{int(z[1]*ftp)} - {int(z[2]*ftp)} W"} for z in zones]

# ---------------------------------------------------------
# FUNZIONE PDF (CORRETTA)
# ---------------------------------------------------------

def clean_text(text):
    """Rimuove caratteri unicode non supportati da FPDF standard."""
    rep = {"₂": "2", "⁻": "-", "¹": "1", "·": "*", "₀": "0", "₃": "3", "₄": "4"}
    for k, v in rep.items():
        text = str(text).replace(k, v)
    return text

def create_performance_pdf(atleta, d_att, d_tar, climb):
    pdf = FPDF()
    pdf.add_page()
    
    # Intestazione
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, clean_text(f"REPORT PERFORMANCE: {atleta['nome']} {atleta['cognome']}"), 0, 1, 'C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 7, f"Data: {date.today()}", 0, 1, 'C')
    pdf.ln(10)

    # Scenario Salita
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 10, "Scenario di Valutazione (Salita)", 0, 1, 'L', True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(190, 8, f"Distanza: {climb['km']} km | Pendenza: {climb['grad']}% | Peso Bici: {climb['bici']} kg", 0, 1, 'L')
    pdf.ln(5)

    # Tabella Comparativa (ATTUALE vs TARGET)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(60, 10, "Parametro", 1, 0, 'C', True)
    pdf.cell(65, 10, "Stato Attuale", 1, 0, 'C', True)
    pdf.cell(65, 10, "Obiettivo Desiderato", 1, 1, 'C', True)

    pdf.set_font("Arial", '', 11)
    rows = [
        ("Peso Corporeo", f"{d_att['peso']} kg", f"{d_tar['peso']} kg"),
        ("Massa Grassa (FM%)", f"{d_att['fm']}%", f"{d_tar['fm']}%"),
        ("Potenza FTP", f"{int(d_att['ftp'])} W", f"{int(d_tar['ftp'])} W"),
        ("Potenza Specifica", f"{d_att['wkg']:.2f} W/kg", f"{d_tar['wkg']:.2f} W/kg"),
        ("Tempo Stimato", f"{d_att['tempo']:.2f} min", f"{d_tar['tempo']:.2f} min")
    ]
    
    for r in rows:
        pdf.cell(60, 10, r[0], 1)
        pdf.cell(65, 10, r[1], 1)
        pdf.cell(65, 10, r[2], 1)
        pdf.ln()

    # Differenza
    pdf.ln(10)
    diff = d_att['tempo'] - d_tar['tempo']
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 128, 0)
    pdf.cell(190, 10, f"GUADAGNO PREVISTO: -{diff:.2f} minuti", 0, 1, 'C')
    
    # Restituisce i bytes del PDF
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# ---------------------------------------------------------
# INTERFACCIA STREAMLIT
# ---------------------------------------------------------

st.set_page_config(page_title="Performance Lab Pro", layout="wide")
st.title("🧬 Performance Lab Pro v2.6")

# Layout a 3 colonne per gli input
col_curr, col_goal, col_climb = st.columns(3)

with col_curr:
    st.subheader("🧱 Stato Attuale")
    nome = st.text_input("Nome")
    cognome = st.text_input("Cognome")
    peso = st.number_input("Peso Attuale (kg)", 30.0, 150.0, 75.0, step=0.1)
    fm = st.number_input("Massa Grassa Attuale (%)", 3.0, 45.0, 15.0, step=0.1)
    
    proto = st.selectbox("Protocollo FTP", ["Manuale", "Test 20 min", "Test 8 min", "Ramp Test"])
    val_t = st.number_input("Risultato Test (W)", 0, 1000, 250)
    
    if proto == "Test 20 min": ftp_curr = val_t * 0.95
    elif proto == "Test 8 min": ftp_curr = val_t * 0.90
    elif proto == "Ramp Test": ftp_curr = val_t * 0.75
    else: ftp_curr = float(val_t)

with col_goal:
    st.subheader("🎯 Target Desiderati")
    st.write("Inserisci i parametri obiettivo:")
    peso_target = st.number_input("Peso Obiettivo (kg)", 30.0, 150.0, peso - 2.0, step=0.1)
    fm_target = st.number_input("FM% Obiettivo", 3.0, 45.0, fm - 2.0, step=0.1)
    watt_plus = st.number_input("Incremento Potenza (+ W)", 0, 150, 20)
    ftp_target = ftp_curr + watt_plus
    fthr = st.number_input("FTHR desiderata (bpm)", 100, 210, 165)

with col_climb:
    st.subheader("🏔️ Segmento Salita")
    dist_km = st.number_input("Chilometri Salita", 0.1, 50.0, 10.0, step=0.1)
    grad = st.number_input("Pendenza Media (%)", 0.0, 25.0, 7.0, step=0.1)
    bike_w = st.number_input("Peso Bici + Accessori (kg)", 5.0, 15.0, 8.5, step=0.1)

st.divider()

if st.button("🚀 ELABORA E GENERA REPORT"):
    # Calcoli Biometrici
    ffm_curr = peso * (1 - (fm/100))
    bmr = ScientificEngine.calculate_bmr_cunningham(ffm_curr)
    wkg_curr = ftp_curr / peso
    wkg_tar = ftp_target / peso_target
    
    # Calcoli Performance
    t_curr = ScientificEngine.estimate_climb_time(ftp_curr, peso, dist_km, grad, bike_w)
    t_tar = ScientificEngine.estimate_climb_time(ftp_target, peso_target, dist_km, grad, bike_w)
    
    # Visualizzazione UI
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("W·kg⁻¹ Attuale", f"{wkg_curr:.2f}")
    m2.metric("W·kg⁻¹ Obiettivo", f"{wkg_tar:.2f}", f"{wkg_tar-wkg_curr:.2f}")
    m3.metric("Tempo Attuale", f"{t_curr:.2f} min")
    m4.metric("Tempo Obiettivo", f"{t_tar:.2f} min", f"-{t_curr-t_tar:.2f}", delta_color="inverse")

    # Dati per PDF
    atleta = {"nome": nome, "cognome": cognome}
    d_att = {"peso": peso, "fm": fm, "ftp": ftp_curr, "wkg": wkg_curr, "tempo": t_curr}
    d_tar = {"peso": peso_target, "fm": fm_target, "ftp": ftp_target, "wkg": wkg_tar, "tempo": t_tar}
    climb = {"km": dist_km, "grad": grad, "bici": bike_w}

    # Generazione PDF
    try:
        pdf_bytes = create_performance_pdf(atleta, d_att, d_tar, climb)
        st.download_button(
            label="📄 Scarica Report PDF Professionale",
            data=pdf_bytes,
            file_name=f"Analisi_{cognome}.pdf",
            mime="application/pdf"
        )
        st.success("Report generato correttamente!")
    except Exception as e:
        st.error(f"Errore nella creazione del PDF: {e}")

    # Zone di Potenza Target
    st.write("### 📊 Zone di Allenamento Obiettivo")
    st.table(pd.DataFrame(ScientificEngine.get_power_zones(ftp_target)))
