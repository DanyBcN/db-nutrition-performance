import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from fpdf import FPDF
import os

# ---------------------------------------------------------
# SETUP E DATABASE
# ---------------------------------------------------------
st.set_page_config(page_title="DB Nutrition and Performance", layout="wide", page_icon="🧬")

LOGO_PATH = "Logo NUTRITION AND PERFORMANCE.png"

def init_db():
    conn = sqlite3.connect("performance_lab.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS atleti 
                 (id INTEGER PRIMARY KEY, nome TEXT, cognome TEXT, altezza REAL, sesso TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visite 
                 (id INTEGER PRIMARY KEY, atleta_id INTEGER, data TEXT, peso REAL, fm REAL, ftp REAL, 
                  lthr INTEGER, peso_t REAL, fm_t REAL, ftp_t REAL, t_att REAL, t_tar REAL,
                  dist_km REAL, grad REAL, bike_w REAL)''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# ENGINE SCIENTIFICO
# ---------------------------------------------------------
class ScientificEngine:
    @staticmethod
    def estimate_climb_time(watt, peso_atleta, km, pendenza_pct, peso_bici):
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

def pdf_safe(text):
    return str(text).replace('·', '*').replace('⁻¹', '/kg').replace('²', '2').replace('₁', '1').replace('₂', '2').replace('₃', '3').replace('₄', '4').replace('₅', '5').encode('latin-1', 'replace').decode('latin-1')

# ---------------------------------------------------------
# UI SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    st.title("Performance Lab")
    menu = st.radio("Navigazione", ["Nuova Valutazione", "Gestione Archivio"])

# ---------------------------------------------------------
# NUOVA VALUTAZIONE
# ---------------------------------------------------------
if menu == "Nuova Valutazione":
    st.header("🧬 Analisi Biometrica e Programmazione Target")
    
    with st.expander("👤 Anagrafica Atleta", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        n_in = c1.text_input("Nome", "Atleta")
        c_in = c2.text_input("Cognome", "Esempio")
        altezza = c3.number_input("Altezza (cm)", 100, 250, 175) / 100
        sesso = c4.selectbox("Sesso", ["M", "F"])

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.subheader("🧱 Stato Attuale")
        peso = st.number_input("Peso (kg)", 30.0, 150.0, 75.0)
        fm = st.number_input("Massa Grassa (%)", 3.0, 45.0, 15.0)
        proto = st.selectbox("Protocollo FTP", ["Manuale", "Test 20 min", "Test 8 min", "Ramp Test"])
        val_t = st.number_input("Risultato Test (W)", 0, 1000, 250)
        lthr_in = st.number_input("FC Soglia (LTHR bpm)", 80, 220, 165)
        
        if proto == "Test 20 min": ftp_calc = val_t * 0.95
        elif proto == "Test 8 min": ftp_calc = val_t * 0.90
        elif proto == "Ramp Test": ftp_calc = val_t * 0.75
        else: ftp_calc = float(val_t)

    with col_b:
        st.subheader("🎯 Target Desiderati")
        peso_t = st.number_input("Peso Target (kg)", 30.0, 150.0, peso - 2.0)
        fm_t = st.number_input("FM% Target", 3.0, 45.0, fm - 2.0)
        watt_plus = st.number_input("Incremento Potenza (+ W)", 0, 150, 15)
        ftp_t_calc = ftp_calc + watt_plus

    with col_c:
        st.subheader("🏔️ Scenario Salita")
        dist_km = st.number_input("Chilometri Salita", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza (%)", 0.0, 25.0, 7.0)
        bike_w = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.5)

    if st.button("🚀 ELABORA PARAMETRI"):
        t_att = ScientificEngine.estimate_climb_time(ftp_calc, peso, dist_km, grad, bike_w)
        t_tar = ScientificEngine.estimate_climb_time(ftp_t_calc, peso_t, dist_km, grad, bike_w)
        
        # Salvataggio nello stato della sessione per non perdere i dati
        st.session_state['res'] = {
            'nome': n_in, 'cognome': c_in, 'peso': peso, 'fm': fm, 'ftp': ftp_calc, 
            'peso_t': peso_t, 'fm_t': fm_t, 'ftp_t': ftp_t_calc, 'lthr': lthr_in,
            't_att': t_att, 't_tar': t_tar, 'dist': dist_km, 'grad': grad, 
            'bike': bike_w, 'proto': proto
        }

    # SE I RISULTATI ESISTONO, MOSTRALI
    if 'res' in st.session_state:
        r = st.session_state['res']
        st.divider()
        
        # 1. METRICHE PRINCIPALI
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("W/kg Attuale", f"{r['ftp']/r['peso']:.2f}")
        m2.metric("W/kg Target", f"{r['ftp_t']/r['peso_t']:.2f}", f"{(r['ftp_t']/r['peso_t'])-(r['ftp']/r['peso']):.2f}")
        m3.metric("Tempo Attuale", f"{r['t_att']:.2f} min")
        m4.metric("Tempo Target", f"{r['t_tar']:.2f} min", f"-{r['t_att']-r['t_tar']:.2f}", delta_color="inverse")

        

        # 2. TABELLE ZONE
        st.write(f"### 📊 Report per {r['nome']} {r['cognome']}")
        st.info(f"Scenario: Salita di **{r['dist']} km** al **{r['grad']}%** (Peso Bici: {r['bike']} kg)")
        
        zc1, zc2 = st.columns(2)
        with zc1:
            st.write("#### ⚡ Zone Potenza Target")
            st.table(pd.DataFrame(ScientificEngine.get_power_zones(r['ftp_t']), columns=["Zona", "Min (W)", "Max (W)"]))
        with zc2:
            st.write("#### ❤️ Zone Cardio (LTHR)")
            st.table(pd.DataFrame(ScientificEngine.get_hr_zones(r['lthr']), columns=["Zona", "Min (bpm)", "Max (bpm)"]))

        # 3. AZIONI (SALVA E PDF)
        st.divider()
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button("💾 SALVA IN ARCHIVIO"):
                conn = sqlite3.connect("performance_lab.db"); c = conn.cursor()
                c.execute("INSERT INTO atleti (nome, cognome, altezza, sesso) VALUES (?,?,?,?)", (r['nome'], r['cognome'], altezza, sesso))
                a_id = c.lastrowid
                c.execute("""INSERT INTO visite (atleta_id, data, peso, fm, ftp, lthr, peso_t, fm_t, ftp_t, t_att, t_tar, dist_km, grad, bike_w) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                          (a_id, date.today().isoformat(), r['peso'], r['fm'], r['ftp'], r['lthr'],
                           r['peso_t'], r['fm_t'], r['ftp_t'], r['t_att'], r['t_tar'], r['dist'], r['grad'], r['bike']))
                conn.commit(); conn.close()
                st.success("Archiviato!")

        with btn_col2:
            pdf = FPDF()
            pdf.add_page()
            if os.path.exists(LOGO_PATH):
                pdf.image(LOGO_PATH, x=150, y=8, w=45) 
            
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(130, 10, pdf_safe(f"Performance Report: {r['nome']} {r['cognome']}"), 0, 1)
            pdf.set_font("Arial", '', 10); pdf.cell(130, 7, f"Data: {date.today()}", 0, 1); pdf.ln(10)

            pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "1. Scenario", 0, 1)
            pdf.set_font("Arial", '', 11); pdf.multi_cell(190, 7, pdf_safe(f"Simulazione su salita di {r['dist']} km al {r['grad']}% con {r['bike']} kg di attrezzatura."))
            
            # Tabella Dati
            pdf.ln(5); pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 11)
            pdf.cell(60, 10, "Parametro", 1, 0, 'L', True); pdf.cell(65, 10, "Attuale", 1, 0, 'C', True); pdf.cell(65, 10, "Obiettivo", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 11)
            rows = [
                ("Peso", f"{r['peso']} kg", f"{r['peso_t']} kg"),
                ("FTP", f"{int(r['ftp'])} W", f"{int(r['ftp_t'])} W"),
                ("W/kg", f"{r['ftp']/r['peso']:.2f}", f"{r['ftp_t']/r['peso_t']:.2f}"),
                ("Tempo", f"{r['t_att']:.2f} min", f"{r['t_tar']:.2f} min")
            ]
            for row in rows:
                pdf.cell(60, 10, pdf_safe(row[0]), 1); pdf.cell(65, 10, pdf_safe(row[1]), 1); pdf.cell(65, 10, pdf_safe(row[2]), 1); pdf.ln()

            # Zone
            pdf.ln(10); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "2. Zone Target", 0, 1)
            pz = ScientificEngine.get_power_zones(r['ftp_t'])
            hz = ScientificEngine.get_hr_zones(r['lthr'])
            for i in range(5):
                pdf.cell(95, 8, pdf_safe(f"{pz[i][0]}: {pz[i][1]}-{pz[i][2]} W"), 1, 0)
                pdf.cell(95, 8, pdf_safe(f"{hz[i][0]}: {hz[i][1]}-{hz[i][2]} bpm"), 1, 1)

            st.download_button("📄 SCARICA PDF", data=pdf.output(dest='S').encode('latin-1', 'replace'), file_name=f"Report_{r['cognome']}.pdf")

# ---------------------------------------------------------
# GESTIONE ARCHIVIO
# ---------------------------------------------------------
elif menu == "Gestione Archivio":
    st.header("📂 Archivio")
    conn = sqlite3.connect("performance_lab.db"); df_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)
    if not df_atleti.empty:
        sel = st.selectbox("Atleta", df_atleti.apply(lambda x: f"{x['id']} - {x['nome']} {x['cognome']}", axis=1))
        a_id = sel.split(" - ")[0]
        if st.button("Elimina"):
            conn.execute(f"DELETE FROM visite WHERE atleta_id={a_id}"); conn.execute(f"DELETE FROM atleti WHERE id={a_id}"); conn.commit(); st.rerun()
        st.dataframe(pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id}", conn))
    else: st.info("Vuoto.")
    conn.close()
