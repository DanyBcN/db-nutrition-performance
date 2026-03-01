import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import date
from fpdf import FPDF

# ---------------------------------------------------------
# SETUP E DATABASE (CON CORREZIONE OPERATIONALERROR)
# ---------------------------------------------------------
st.set_page_config(page_title="Performance Lab Pro v3.1", layout="wide", page_icon="🧬")

def init_db():
    conn = sqlite3.connect("performance_lab.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS atleti 
                 (id INTEGER PRIMARY KEY, nome TEXT, cognome TEXT, altezza REAL, sesso TEXT)''')
    
    # Creazione tabella visite con tutte le colonne necessarie
    c.execute('''CREATE TABLE IF NOT EXISTS visite 
                 (id INTEGER PRIMARY KEY, atleta_id INTEGER, data TEXT, peso REAL, fm REAL, ftp REAL, 
                  peso_t REAL, fm_t REAL, ftp_t REAL, t_att REAL, t_tar REAL)''')
    
    # Fix per OperationalError: aggiunge colonne se non esistono (migrazione dinamica)
    columns = [col[1] for col in c.execute("PRAGMA table_info(visite)")]
    needed = ["peso_t", "fm_t", "ftp_t", "t_att", "t_tar"]
    for n in needed:
        if n not in columns:
            c.execute(f"ALTER TABLE visite ADD COLUMN {n} REAL")
            
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# ENGINE SCIENTIFICO
# ---------------------------------------------------------
class ScientificEngine:
    @staticmethod
    def estimate_climb_time(watt, peso_atleta, km, pendenza_pct, peso_bici=8.5):
        m_totale = peso_atleta + peso_bici
        g = 9.81
        pendenza_dec = pendenza_pct / 100
        f_resistenza = m_totale * g * (pendenza_dec + 0.005) # Gravità + Crr
        if f_resistenza <= 0 or watt <= 0: return 0
        v_ms = watt / f_resistenza
        v_kh = v_ms * 3.6
        return (km / v_kh) * 60 # minuti

    @staticmethod
    def get_power_zones(ftp):
        zones = [("Z₁ Rec.", 0, 0.55), ("Z₂ End.", 0.56, 0.75), 
                 ("Z₃ Tempo", 0.76, 0.90), ("Z₄ Soglia", 0.91, 1.05),
                 ("Z₅ VO₂max", 1.06, 1.20)]
        return [{"Zona": z[0], "Range": f"{int(z[1]*ftp)} - {int(z[2]*ftp)} W"} for z in zones]

# ---------------------------------------------------------
# NAVIGAZIONE
# ---------------------------------------------------------
st.sidebar.title("🧬 Performance Lab Pro")
menu = st.sidebar.radio("Navigazione", ["Nuova Valutazione", "Archivio e Trend"])

if menu == "Nuova Valutazione":
    st.header("📋 Analisi Biometrica e Predizione Performance")
    
    with st.expander("👤 Anagrafica Atleta", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        nome = c1.text_input("Nome")
        cognome = c2.text_input("Cognome")
        altezza = c3.number_input("Altezza (cm)", 100, 250, 175) / 100
        sesso = c4.selectbox("Sesso", ["M", "F"])

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.subheader("🧱 Stato Attuale")
        peso = st.number_input("Peso (kg)", 30.0, 150.0, 75.0)
        fm = st.number_input("Massa Grassa (%)", 3.0, 45.0, 15.0)
        proto = st.selectbox("Protocollo FTP", ["Manuale", "Test 20 min", "Test 8 min", "Ramp Test"])
        val_t = st.number_input("Risultato Test (W)", 0, 1000, 250)
        
        if proto == "Test 20 min": ftp = val_t * 0.95
        elif proto == "Test 8 min": ftp = val_t * 0.90
        elif proto == "Ramp Test": ftp = val_t * 0.75
        else: ftp = float(val_t)

    with col_b:
        st.subheader("🎯 Target Desiderati")
        peso_t = st.number_input("Peso Obiettivo (kg)", 30.0, 150.0, peso - 2.0)
        fm_t = st.number_input("FM% Obiettivo", 3.0, 45.0, fm - 2.0)
        watt_plus = st.number_input("Incremento Potenza (+ W)", 0, 100, 15)
        ftp_t = ftp + watt_plus

    with col_c:
        st.subheader("🏔️ Scenario Salita")
        dist_km = st.number_input("Distanza Salita (km)", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza (%)", 0.0, 25.0, 7.0)
        bike_w = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.0)

    # Variabile di stato per mostrare i risultati dopo l'elaborazione
    if st.button("🚀 ELABORA"):
        t_att = ScientificEngine.estimate_climb_time(ftp, peso, dist_km, grad, bike_w)
        t_tar = ScientificEngine.estimate_climb_time(ftp_t, peso_t, dist_km, grad, bike_w)
        
        st.session_state['results'] = {
            't_att': t_att, 't_tar': t_tar, 'ftp': ftp, 'ftp_t': ftp_t,
            'peso': peso, 'peso_t': peso_t, 'fm': fm, 'fm_t': fm_t
        }

    if 'results' in st.session_state:
        res = st.session_state['results']
        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("W·kg⁻¹ Attuale", f"{res['ftp']/res['peso']:.2f}")
        m2.metric("W·kg⁻¹ Target", f"{res['ftp_t']/res['peso_t']:.2f}", f"{(res['ftp_t']/res['peso_t'])-(res['ftp']/res['peso']):.2f}")
        m3.metric("Tempo Attuale", f"{res['t_att']:.2f} min")
        m4.metric("Tempo Target", f"{res['t_tar']:.2f} min", f"-{res['t_att']-res['t_tar']:.2f}", delta_color="inverse")

        

        c_save1, c_save2 = st.columns(2)
        with c_save1:
            if st.button("💾 SALVA IN ARCHIVIO"):
                conn = sqlite3.connect("performance_lab.db")
                c = conn.cursor()
                c.execute("INSERT INTO atleti (nome, cognome, altezza, sesso) VALUES (?,?,?,?)", (nome, cognome, altezza, sesso))
                a_id = c.lastrowid
                c.execute("""INSERT INTO visite (atleta_id, data, peso, fm, ftp, peso_t, fm_t, ftp_t, t_att, t_tar) 
                             VALUES (?,?,?,?,?,?,?,?,?,?)""", 
                          (a_id, date.today().isoformat(), res['peso'], res['fm'], res['ftp'], 
                           res['peso_t'], res['fm_t'], res['ftp_t'], res['t_att'], res['t_tar']))
                conn.commit()
                conn.close()
                st.success("✅ Dati salvati con successo!")
        
        with c_save2:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, f"Report Atleta: {nome} {cognome}", 0, 1, 'C')
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(60, 10, "Parametro", 1); pdf.cell(65, 10, "Attuale", 1); pdf.cell(65, 10, "Obiettivo", 1); pdf.ln()
            pdf.set_font("Arial", '', 11)
            pdf.cell(60, 10, "Peso", 1); pdf.cell(65, 10, f"{res['peso']} kg", 1); pdf.cell(65, 10, f"{res['peso_t']} kg", 1); pdf.ln()
            pdf.cell(60, 10, "W/kg", 1); pdf.cell(65, 10, f"{res['ftp']/res['peso']:.2f}", 1); pdf.cell(65, 10, f"{res['ftp_t']/res['peso_t']:.2f}", 1); pdf.ln()
            pdf.cell(60, 10, "Tempo Salita", 1); pdf.cell(65, 10, f"{res['t_att']:.2f} min", 1); pdf.cell(65, 10, f"{res['t_tar']:.2f} min", 1); pdf.ln()
            
            st.download_button("📄 SCARICA REPORT PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"{cognome}_report.pdf")

# ---------------------------------------------------------
# MODULO 2: ARCHIVIO E TREND
# ---------------------------------------------------------
elif menu == "Archivio e Trend":
    st.header("📂 Archivio Storico Atleti")
    conn = sqlite3.connect("performance_lab.db")
    atleti_df = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    if not atleti_df.empty:
        scelta = st.selectbox("Seleziona Atleta", atleti_df.apply(lambda r: f"{r['id']} - {r['nome']} {r['cognome']}", axis=1))
        a_id = scelta.split(" - ")[0]
        visite_df = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id}", conn)
        st.dataframe(visite_df)
        
        if not visite_df.empty:
            st.write("### Evoluzione W·kg⁻¹")
            visite_df['wkg'] = visite_df['ftp'] / visite_df['peso']
            st.line_chart(visite_df.set_index('data')['wkg'])
    else:
        st.info("Nessun dato in archivio.")
    conn.close()

st.sidebar.markdown("---")
st.sidebar.caption(f"Performance Lab Pro v3.1 | © {date.today().year}")
