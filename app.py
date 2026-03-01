import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import date
from fpdf import FPDF

# ---------------------------------------------------------
# SETUP E DATABASE
# ---------------------------------------------------------
st.set_page_config(page_title="Performance Lab Pro v3.0", layout="wide", page_icon="🧬")

def init_db():
    conn = sqlite3.connect("performance_lab.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS atleti 
                 (id INTEGER PRIMARY KEY, nome TEXT, cognome TEXT, altezza REAL, sesso TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visite 
                 (id INTEGER PRIMARY KEY, atleta_id INTEGER, data TEXT, peso REAL, fm REAL, ftp REAL, 
                  peso_t REAL, fm_t REAL, ftp_t REAL, t_att REAL, t_tar REAL,
                  FOREIGN KEY(atleta_id) REFERENCES atleti(id))''')
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
        # Forza resistente: Gravità + Attrito volvente (Crr 0.005)
        f_resistenza = m_totale * g * (pendenza_dec + 0.005)
        if f_resistenza <= 0 or watt <= 0: return 0
        v_ms = watt / f_resistenza
        v_kh = v_ms * 3.6
        return (km / v_kh) * 60 # minuti

    @staticmethod
    def get_power_zones(ftp):
        zones = [("Z₁ Active Recovery", 0, 0.55), ("Z₂ Endurance", 0.56, 0.75), 
                 ("Z₃ Tempo", 0.76, 0.90), ("Z₄ Soglia Lattacida", 0.91, 1.05),
                 ("Z₅ VO₂max", 1.06, 1.20)]
        return [{"Zona": z[0], "Range": f"{int(z[1]*ftp)} - {int(z[2]*ftp)} W"} for z in zones]

def clean_txt(t):
    return str(t).replace("₂", "2").replace("⁻", "-").replace("¹", "1").replace("·", "*")

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.title("🧬 Performance Lab Pro")
menu = st.sidebar.radio("Navigazione", ["Nuova Valutazione", "Archivio e Trend"])

# ---------------------------------------------------------
# MODULO 1: NUOVA VALUTAZIONE
# ---------------------------------------------------------
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
        
        # Logica coefficienti
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

    if st.button("🚀 ELABORA E SALVA"):
        t_att = ScientificEngine.estimate_climb_time(ftp, peso, dist_km, grad, bike_w)
        t_tar = ScientificEngine.estimate_climb_time(ftp_t, peso_t, dist_km, grad, bike_w)
        
        # Database Save
        conn = sqlite3.connect("performance_lab.db")
        c = conn.cursor()
        c.execute("INSERT INTO atleti (nome, cognome, altezza, sesso) VALUES (?,?,?,?)", (nome, cognome, altezza, sesso))
        a_id = c.lastrowid
        c.execute("""INSERT INTO visite (atleta_id, data, peso, fm, ftp, peso_t, fm_t, ftp_t, t_att, t_tar) 
                     VALUES (?,?,?,?,?,?,?,?,?,?)""", 
                  (a_id, date.today().isoformat(), peso, fm, ftp, peso_t, fm_t, ftp_t, t_att, t_tar))
        conn.commit()
        conn.close()

        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("W·kg⁻¹ Attuale", f"{ftp/peso:.2f}")
        m2.metric("W·kg⁻¹ Target", f"{ftp_t/peso_t:.2f}", f"{(ftp_t/peso_t)-(ftp/peso):.2f}")
        m3.metric("Tempo Attuale", f"{t_att:.2f} min")
        m4.metric("Tempo Target", f"{t_tar:.2f} min", f"-{t_att-t_tar:.2f}", delta_color="inverse")

        # PDF Generation
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, f"Report Atleta: {nome} {cognome}", 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(60, 10, "Parametro", 1); pdf.cell(65, 10, "Attuale", 1); pdf.cell(65, 10, "Obiettivo", 1); pdf.ln()
        pdf.set_font("Arial", '', 11)
        pdf.cell(60, 10, "Peso", 1); pdf.cell(65, 10, f"{peso} kg", 1); pdf.cell(65, 10, f"{peso_t} kg", 1); pdf.ln()
        pdf.cell(60, 10, "FTP", 1); pdf.cell(65, 10, f"{int(ftp)} W", 1); pdf.cell(65, 10, f"{int(ftp_t)} W", 1); pdf.ln()
        pdf.cell(60, 10, "Tempo Salita", 1); pdf.cell(65, 10, f"{t_att:.2f} min", 1); pdf.cell(65, 10, f"{t_tar:.2f} min", 1); pdf.ln()
        
        st.download_button("📄 Scarica Report PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"{cognome}_report.pdf")

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
        st.write("### Storico Visite")
        st.dataframe(visite_df)
        
        if len(visite_df) > 0:
            st.write("### Evoluzione Peso e Massa Grassa")
            st.line_chart(visite_df.set_index('data')[['peso', 'fm']])
            st.write("### Evoluzione Potenza (FTP)")
            st.line_chart(visite_df.set_index('data')[['ftp']])
    else:
        st.info("Nessun dato in archivio.")
    conn.close()

st.sidebar.markdown("---")
st.sidebar.caption(f"Performance Lab Pro v3.0 | © {date.today().year}")
