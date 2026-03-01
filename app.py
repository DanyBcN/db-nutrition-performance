import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from fpdf import FPDF

# ---------------------------------------------------------
# SETUP E DATABASE
# ---------------------------------------------------------
st.set_page_config(page_title="Performance Lab Pro v3.2", layout="wide", page_icon="🧬")

def init_db():
    conn = sqlite3.connect("performance_lab.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS atleti 
                 (id INTEGER PRIMARY KEY, nome TEXT, cognome TEXT, altezza REAL, sesso TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visite 
                 (id INTEGER PRIMARY KEY, atleta_id INTEGER, data TEXT, peso REAL, fm REAL, ftp REAL, 
                  lthr INTEGER, peso_t REAL, fm_t REAL, ftp_t REAL, t_att REAL, t_tar REAL)''')
    
    # Migrazione dinamica per colonne mancanti
    columns = [col[1] for col in c.execute("PRAGMA table_info(visite)")]
    for col_name in ["lthr", "peso_t", "fm_t", "ftp_t", "t_att", "t_tar"]:
        if col_name not in columns:
            c.execute(f"ALTER TABLE visite ADD COLUMN {col_name} REAL")
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
        f_resistenza = m_totale * g * (pendenza_dec + 0.005) 
        if f_resistenza <= 0 or watt <= 0: return 0
        v_ms = watt / f_resistenza
        v_kh = v_ms * 3.6
        return (km / v_kh) * 60

    @staticmethod
    def get_power_zones(ftp):
        return [
            ("Z₁ Recupero", 0, int(ftp * 0.55)),
            ("Z₂ Endurance", int(ftp * 0.56), int(ftp * 0.75)),
            ("Z₃ Tempo", int(ftp * 0.76), int(ftp * 0.90)),
            ("Z₄ Soglia", int(ftp * 0.91), int(ftp * 1.05)),
            ("Z₅ VO₂max", int(ftp * 1.06), int(ftp * 1.20))
        ]

    @staticmethod
    def get_hr_zones(lthr):
        return [
            ("Z₁ Rigenerante", 0, int(lthr * 0.81)),
            ("Z₂ Fondo Lento", int(lthr * 0.82), int(lthr * 0.89)),
            ("Z₃ Fondo Medio", int(lthr * 0.90), int(lthr * 0.93)),
            ("Z₄ Soglia (LTHR)", int(lthr * 0.94), int(lthr * 1.00)),
            ("Z₅ Fuorisoglia", int(lthr * 1.01), int(lthr * 1.10))
        ]

def clean(t): return str(t).encode('latin-1', 'replace').decode('latin-1')

# ---------------------------------------------------------
# UI PRINCIPALE
# ---------------------------------------------------------
menu = st.sidebar.radio("Navigazione", ["Nuova Valutazione", "Archivio e Trend"])

if menu == "Nuova Valutazione":
    st.header("📋 Analisi Biometrica e Programmazione Target")
    
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
        lthr = st.number_input("Frequenza Cardiaca di Soglia (LTHR/bpm)", 80, 220, 165)
        
        if proto == "Test 20 min": ftp = val_t * 0.95
        elif proto == "Test 8 min": ftp = val_t * 0.90
        elif proto == "Ramp Test": ftp = val_t * 0.75
        else: ftp = float(val_t)

    with col_b:
        st.subheader("🎯 Target Desiderati")
        peso_t = st.number_input("Peso Target (kg)", 30.0, 150.0, peso - 2.0)
        fm_t = st.number_input("FM% Target", 3.0, 45.0, fm - 2.0)
        watt_plus = st.number_input("Incremento Potenza (+ W)", 0, 150, 15)
        ftp_t = ftp + watt_plus

    with col_c:
        st.subheader("🏔️ Scenario Salita")
        dist_km = st.number_input("Distanza (km)", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza (%)", 0.0, 25.0, 7.0)
        bike_w = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.0)

    if st.button("🚀 ELABORA PARAMETRI"):
        t_att = ScientificEngine.estimate_climb_time(ftp, peso, dist_km, grad, bike_w)
        t_tar = ScientificEngine.estimate_climb_time(ftp_t, peso_t, dist_km, grad, bike_w)
        
        st.session_state['res'] = {
            't_att': t_att, 't_tar': t_tar, 'ftp': ftp, 'ftp_t': ftp_t,
            'peso': peso, 'peso_t': peso_t, 'fm': fm, 'fm_t': fm_t, 'lthr': lthr
        }

    if 'res' in st.session_state:
        r = st.session_state['res']
        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("W·kg⁻¹ Attuale", f"{r['ftp']/r['peso']:.2f}")
        m2.metric("W·kg⁻¹ Target", f"{r['ftp_t']/r['peso_t']:.2f}", f"{(r['ftp_t']/r['peso_t'])-(r['ftp']/r['peso']):.2f}")
        m3.metric("Tempo Attuale", f"{r['t_att']:.2f} min")
        m4.metric("Tempo Target", f"{r['t_tar']:.2f} min", f"-{r['t_att']-r['t_tar']:.2f}", delta_color="inverse")

        # Visualizzazione Zone
        z_col1, z_col2 = st.columns(2)
        with z_col1:
            st.write("### ⚡ Zone Potenza (Target)")
            p_zones = ScientificEngine.get_power_zones(r['ftp_t'])
            st.table(pd.DataFrame(p_zones, columns=["Zona", "Da (W)", "A (W)"]))
        with z_col2:
            st.write("### ❤️ Zone Cardio (LTHR)")
            h_zones = ScientificEngine.get_hr_zones(r['lthr'])
            st.table(pd.DataFrame(h_zones, columns=["Zona", "Da (bpm)", "A (bpm)"]))

        # Azioni Finali
        st.divider()
        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("💾 SALVA IN ARCHIVIO"):
                conn = sqlite3.connect("performance_lab.db")
                c = conn.cursor()
                c.execute("INSERT INTO atleti (nome, cognome, altezza, sesso) VALUES (?,?,?,?)", (nome, cognome, altezza, sesso))
                a_id = c.lastrowid
                c.execute("""INSERT INTO visite (atleta_id, data, peso, fm, ftp, lthr, peso_t, fm_t, ftp_t, t_att, t_tar) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?)""", 
                          (a_id, date.today().isoformat(), r['peso'], r['fm'], r['ftp'], r['lthr'],
                           r['peso_t'], r['fm_t'], r['ftp_t'], r['t_att'], r['t_tar']))
                conn.commit()
                conn.close()
                st.success("Archiviato!")

        with btn2:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, clean(f"Performance Report: {nome} {cognome}"), 0, 1, 'C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(190, 10, f"Data: {date.today()}", 0, 1, 'C')
            pdf.ln(5)
            
            # Tabella Comparativa
            pdf.set_fill_color(230, 230, 230)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(60, 10, "Parametro", 1, 0, 'L', True); pdf.cell(65, 10, "Attuale", 1, 0, 'C', True); pdf.cell(65, 10, "Obiettivo", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 11)
            rows = [("Peso", f"{r['peso']} kg", f"{r['peso_t']} kg"), 
                    ("FTP", f"{int(r['ftp'])} W", f"{int(r['ftp_t'])} W"),
                    ("Potenza Spec.", f"{r['ftp']/r['peso']:.2f} W/kg", f"{r['ftp_t']/res['peso_t'] if 'res' in locals() else r['ftp_t']/r['peso_t']:.2f} W/kg"),
                    ("Tempo Scalata", f"{r['t_att']:.2f} min", f"{r['t_tar']:.2f} min")]
            for row in rows:
                pdf.cell(60, 10, row[0], 1); pdf.cell(65, 10, row[1], 1); pdf.cell(65, 10, row[2], 1); pdf.ln()
            
            # Zone nel PDF
            pdf.ln(10); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "Zone di Allenamento Target", 0, 1, 'L')
            pdf.set_font("Arial", '', 10)
            for z, start, end in ScientificEngine.get_power_zones(r['ftp_t']):
                pdf.cell(95, 8, f"{z}: {start}-{end} W", 1)
                pdf.ln()

            st.download_button("📄 SCARICA PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Report_{cognome}.pdf")

elif menu == "Archivio e Trend":
    st.header("📂 Storico Atleti")
    conn = sqlite3.connect("performance_lab.db")
    atleti_df = pd.read_sql_query("SELECT * FROM atleti", conn)
    if not atleti_df.empty:
        scelta = st.selectbox("Seleziona Atleta", atleti_df.apply(lambda r: f"{r['id']} - {r['nome']} {r['cognome']}", axis=1))
        a_id = scelta.split(" - ")[0]
        v_df = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id}", conn)
        st.dataframe(v_df)
    else:
        st.info("Archivio vuoto.")
    conn.close()
