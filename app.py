import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from fpdf import FPDF
import os

# ---------------------------------------------------------
# SETUP E DATABASE
# ---------------------------------------------------------
st.set_page_config(page_title="DB Nutrition & Performance Pro", layout="wide", page_icon="🧬")
LOGO_PATH = "Logo NUTRITION AND PERFORMANCE.png"

def init_db():
    conn = sqlite3.connect("performance_lab.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS atleti 
                 (id INTEGER PRIMARY KEY, nome TEXT, cognome TEXT, altezza REAL, sesso TEXT, profilo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visite 
                 (id INTEGER PRIMARY KEY, atleta_id INTEGER, data TEXT, peso REAL, fm REAL, ftp REAL, 
                  lthr INTEGER, peso_t REAL, fm_t REAL, ftp_t REAL, t_att REAL, t_tar REAL,
                  dist_km REAL, grad REAL, bike_w REAL, nota_dna TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# LOGICA SCIENTIFICA
# ---------------------------------------------------------
class CyclingScience:
    @staticmethod
    def estimate_time(watt, peso_atleta, km, pendenza, bike_w):
        m_tot = peso_atleta + bike_w
        g = 9.81
        f_res = m_tot * g * ((pendenza/100) + 0.005)
        if f_res <= 0 or watt <= 0: return 0
        v_ms = watt / f_res
        return (km / (v_ms * 3.6)) * 60

    @staticmethod
    def get_zones(ftp, lthr):
        p_z = [("Z1 Recupero", 0, int(ftp*0.55)), ("Z2 Endurance", int(ftp*0.56), int(ftp*0.75)),
               ("Z3 Tempo", int(ftp*0.76), int(ftp*0.90)), ("Z4 Soglia", int(ftp*0.91), int(ftp*1.05)),
               ("Z5 VO2max", int(ftp*1.06), int(ftp*1.20))]
        h_z = [("Z1 Rigenerante", 0, int(lthr*0.81)), ("Z2 Fondo Lento", int(lthr*0.82), int(lthr*0.89)),
               ("Z3 Fondo Medio", int(lthr*0.90), int(lthr*0.93)), ("Z4 Soglia", int(lthr*0.94), int(lthr*1.00)),
               ("Z5 Fuorisoglia", int(lthr*1.01), int(lthr*1.10))]
        return p_z, h_z

def pdf_safe(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# ---------------------------------------------------------
# INTERFACCIA
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, use_container_width=True)
    menu = st.radio("Menu", ["Nuova Analisi", "Archivio Atleti"])

if menu == "Nuova Analisi":
    st.header("📋 Valutazione Performance & Composizione Corporea")
    
    with st.expander("👤 Anagrafica e Profilo", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        nome = c1.text_input("Nome")
        cognome = c2.text_input("Cognome")
        profilo = c3.selectbox("Profilo Atleta", ["Scalatore (Lightweight)", "Passista (Powerhouse)", "Triatleta", "Granfondista"])
        lthr_in = c4.number_input("LTHR (bpm)", 100, 210, 168)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🧱 Dati Attuali")
        peso = st.number_input("Peso (kg)", 40.0, 120.0, 72.0)
        fm = st.number_input("Massa Grassa (%)", 3.0, 35.0, 14.0)
        ftp = st.number_input("FTP Attuale (W)", 50, 600, 280)
        
    with col2:
        st.subheader("🎯 Target")
        peso_t = st.number_input("Peso Target (kg)", 40.0, 120.0, 70.0)
        fm_t = st.number_input("FM% Target", 3.0, 35.0, 10.0)
        ftp_t = st.number_input("FTP Target (W)", 50, 600, 310)

    with col3:
        st.subheader("🏔️ Scenario Scalata")
        dist_km = st.number_input("Lunghezza (km)", 0.1, 50.0, 12.0)
        grad = st.number_input("Pendenza (%)", 0.0, 20.0, 7.5)
        bike_w = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.0)

    nota_dna = st.text_area("🧬 Valutazione DNA e Rapporto Massa Grassa/Sport", 
                            "L'atleta presenta una predisposizione genetica a... La FM% attuale risulta superiore al set-point ottimale per la categoria scelta.")

    if st.button("🚀 GENERA REPORT"):
        t_att = CyclingScience.estimate_time(ftp, peso, dist_km, grad, bike_w)
        t_tar = CyclingScience.estimate_time(ftp_t, peso_t, dist_km, grad, bike_w)
        st.session_state['data'] = {
            'n': nome, 'c': cognome, 'prof': profilo, 'p': peso, 'fm': fm, 'ftp': ftp, 
            'p_t': peso_t, 'fm_t': fm_t, 'ftp_t': ftp_t, 'lthr': lthr_in,
            't_a': t_att, 't_t': t_tar, 'd': dist_km, 'g': grad, 'b': bike_w, 'dna': nota_dna
        }

    if 'data' in st.session_state:
        d = st.session_state['data']
        pz, hz = CyclingScience.get_zones(d['ftp_t'], d['lthr'])
        
        st.divider()
        st.subheader("🏁 Risultati della Proiezione")
        
        # TABELLE ZONE IMMEDIATE
        zc1, zc2 = st.columns(2)
        with zc1:
            st.write("### ⚡ Zone Potenza Target")
            st.table(pd.DataFrame(pz, columns=["Zona", "Min (W)", "Max (W)"]))
        with zc2:
            st.write("### ❤️ Zone Cardio Target")
            st.table(pd.DataFrame(hz, columns=["Zona", "Min (bpm)", "Max (bpm)"]))

        # W/KG E SCENARIO
        st.write("### 🏔️ Analisi Performance in Salita")
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("W/kg Attuale", f"{d['ftp']/d['p']:.2f}")
        c_m2.metric("W/kg Target", f"{d['ftp_t']/d['p_t']:.2f}", f"{(d['ftp_t']/d['p_t'])-(d['ftp']/d['p']):.2f}")
        c_m3.metric("Guadagno Tempo", f"{d['t_a']-d['t_t']:.2f} min", delta_color="normal")

        # PDF GENERATION
        if st.button("📄 SCARICA REPORT PDF"):
            pdf = FPDF()
            pdf.add_page()
            if os.path.exists(LOGO_PATH): pdf.image(LOGO_PATH, x=150, y=8, w=40)
            
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(130, 10, pdf_safe(f"REPORT PERFORMANCE: {d['n']} {d['c']}"), 0, 1)
            pdf.set_font("Arial", 'I', 11); pdf.cell(130, 7, f"Profilo: {d['prof']}", 0, 1); pdf.ln(5)

            # 1. ZONE (PRIORITÀ)
            pdf.set_fill_color(200, 220, 255); pdf.set_font("Arial", 'B', 12)
            pdf.cell(190, 10, "1. ZONE DI ALLENAMENTO TARGET", 1, 1, 'C', True)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(95, 8, "POTENZA (W)", 1, 0, 'C'); pdf.cell(95, 8, "CARDIO (bpm)", 1, 1, 'C')
            pdf.set_font("Arial", '', 10)
            for i in range(5):
                pdf.cell(95, 8, pdf_safe(f"{pz[i][0]}: {pz[i][1]}-{pz[i][2]} W"), 1, 0)
                pdf.cell(95, 8, pdf_safe(f"{hz[i][0]}: {hz[i][1]}-{hz[i][2]} bpm"), 1, 1)
            
            # 2. VALUTAZIONE DNA/FM
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "2. VALUTAZIONE COMPOSIZIONE CORPOREA & DNA", 0, 1)
            pdf.set_font("Arial", '', 11); pdf.multi_cell(190, 7, pdf_safe(d['dna']))
            
            # 3. PERFORMANCE SCENARIO
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "3. SCENARIO PERFORMANCE IN SALITA", 0, 1)
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(190, 7, pdf_safe(f"Scenario: Scalata di {d['d']} km al {d['g']}% (Peso Bici: {d['b']} kg)"))
            
            pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(240, 240, 240)
            pdf.cell(60, 10, "Parametro", 1, 0, 'L', True); pdf.cell(65, 10, "Attuale", 1, 0, 'C', True); pdf.cell(65, 10, "Target", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 10)
            pdf.cell(60, 10, "Watt / kg", 1); pdf.cell(65, 10, f"{d['ftp']/d['p']:.2f}", 1); pdf.cell(65, 10, f"{d['ftp_t']/d['p_t']:.2f}", 1); pdf.ln()
            pdf.cell(60, 10, "Tempo Stimato", 1); pdf.cell(65, 10, f"{d['t_a']:.2f} min", 1); pdf.cell(65, 10, f"{d['t_t']:.2f} min", 1); pdf.ln()
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 10, pdf_safe(f"DIFFERENZA TEMPO: -{d['t_a']-d['t_t']:.2f} minuti"), 1, 1, 'C')

            st.download_button("💾 SCARICA PDF", data=pdf.output(dest='S').encode('latin-1', 'replace'), file_name=f"Report_{d['c']}.pdf")

        if st.button("💾 SALVA IN ARCHIVIO"):
            conn = sqlite3.connect("performance_lab.db"); c = conn.cursor()
            c.execute("INSERT INTO atleti (nome, cognome, profilo) VALUES (?,?,?)", (d['n'], d['c'], d['prof']))
            a_id = c.lastrowid
            c.execute("""INSERT INTO visite (atleta_id, data, peso, fm, ftp, lthr, peso_t, fm_t, ftp_t, t_att, t_tar, dist_km, grad, bike_w, nota_dna) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                      (a_id, date.today().isoformat(), d['p'], d['fm'], d['ftp'], d['lthr'], d['p_t'], d['fm_t'], d['ftp_t'], d['t_a'], d['t_t'], d['d'], d['g'], d['b'], d['dna']))
            conn.commit(); conn.close(); st.success("Dati salvati in archivio!")

elif menu == "Archivio Atleti":
    st.header("📂 Gestione Archivio")
    conn = sqlite3.connect("performance_lab.db")
    df_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)
    if not df_atleti.empty:
        sel = st.selectbox("Seleziona Atleta", df_atleti.apply(lambda x: f"{x['id']} - {x['nome']} {x['cognome']}", axis=1))
        a_id = sel.split(" - ")[0]
        
        # RICHIESTA MODIFICA
        st.write("### Storico Visite")
        v_df = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id}", conn)
        st.dataframe(v_df)
        
        if st.button("🔴 Elimina Atleta"):
            conn.execute(f"DELETE FROM visite WHERE atleta_id={a_id}"); conn.execute(f"DELETE FROM atleti WHERE id={a_id}")
            conn.commit(); st.rerun()
    else: st.info("Nessun dato presente.")
    conn.close()
