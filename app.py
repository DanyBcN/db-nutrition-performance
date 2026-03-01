import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
from fpdf import FPDF
import os

# ---------------------------------------------------------
# 1. CONFIGURAZIONE E DATABASE
# ---------------------------------------------------------
st.set_page_config(page_title="Performance Lab Pro v3", layout="wide", page_icon="🧬")
DB_NAME = "performance_lab_pro.db"
LOGO_PATH = "Logo NUTRITION AND PERFORMANCE.png"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS atleti 
                     (id INTEGER PRIMARY KEY, nome TEXT, cognome TEXT, altezza REAL, profilo TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS visite 
                     (id INTEGER PRIMARY KEY, atleta_id INTEGER, data TEXT, 
                      peso REAL, fm REAL, ftp REAL, lthr INTEGER, 
                      peso_t REAL, fm_t REAL, ftp_t REAL, 
                      dist_km REAL, grad REAL, bike_w REAL,
                      t_att REAL, t_tar REAL, FOREIGN KEY(atleta_id) REFERENCES atleti(id))''')
        conn.commit()

init_db()

# ---------------------------------------------------------
# 2. LOGICA SCIENTIFICA E UTILITY
# ---------------------------------------------------------
class BioPerformance:
    @staticmethod
    def get_fm_benchmarks():
        return [
            ["Categoria", "Uomo (FM %)", "Donna (FM %)"],
            ["Pro World Tour", "5 - 8%", "12 - 16%"],
            ["Continental/U23", "8 - 11%", "16 - 20%"],
            ["Elite Amatori", "10 - 14%", "18 - 22%"],
            ["Granfondista", "13 - 17%", "21 - 25%"]
        ]

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        f_res = (peso + bike_w) * 9.81 * ((pend/100) + 0.005)
        if f_res <= 0 or watt <= 0: return 0
        speed_ms = watt / f_res
        return (km * 1000 / speed_ms) / 60

    @staticmethod
    def get_zones(ftp, lthr):
        return [
            ("Z1 Recupero", 0, int(ftp*0.55), 0, int(lthr*0.68)),
            ("Z2 Endurance", int(ftp*0.56), int(ftp*0.75), int(lthr*0.69), int(lthr*0.83)),
            ("Z3 Tempo", int(ftp*0.76), int(ftp*0.90), int(lthr*0.84), int(lthr*0.94)),
            ("Z4 Soglia", int(ftp*0.91), int(ftp*1.05), int(lthr*0.95), int(lthr*1.05)),
            ("Z5 VO2max", int(ftp*1.06), int(ftp*1.20), int(lthr*1.06), 220)
        ]

def pdf_safe(text):
    if not text: return ""
    rep = {"à": "a", "è": "e", "é": "e", "ì": "i", "ò": "o", "ù": "u", "²": "2", "₀": "0", "₁": "1", "₂": "2", "₃": "3"}
    for k, v in rep.items(): text = text.replace(k, v)
    return str(text).encode('ascii', 'ignore').decode('ascii')

# ---------------------------------------------------------
# 3. INTERFACCIA STREAMLIT
# ---------------------------------------------------------

# Logo e Header Programma
if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=300)
else:
    st.markdown("<h1 style='color:#003366;'>🧬 PERFORMANCE LAB PRO</h1>", unsafe_allow_html=True)

st.markdown("---")

menu = st.sidebar.radio("MENÙ PRINCIPALE", ["➕ Nuova Valutazione", "📂 Archivio Storico"])

if menu == "➕ Nuova Valutazione":
    st.header("📝 Protocollo Clinico & Analisi")
    
    with get_connection() as conn:
        db_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        exist_cog = c1.selectbox("Seleziona Atleta", [""] + sorted(db_atleti['cognome'].unique().tolist()))
        new_cog = c1.text_input("...o Nuovo Cognome")
        cog = new_cog if new_cog else exist_cog
        at_data = db_atleti[db_atleti['cognome'] == cog].iloc[0] if cog in db_atleti['cognome'].values else None
        nome = c2.text_input("Nome", value=at_data['nome'] if at_data is not None else "")
        altezza = c3.number_input("Altezza (cm)", 120, 230, int(at_data['altezza']) if at_data is not None else 175)
        profilo = c4.selectbox("Profilo", ["Scalatore", "Passista", "Granfondista", "Triatleta"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("### ATTUALE")
        p_att = st.number_input("Peso (kg)", 40.0, 150.0, 70.0)
        fm_att = st.number_input("Massa Grassa %", 3.0, 40.0, 15.0)
        ftp_att = st.number_input("FTP (W)", 50, 600, 250)
        lthr = st.number_input("LTHR (bpm)", 80, 220, 165)
    with col2:
        st.success("### TARGET")
        p_tar = st.number_input("Peso Target (kg)", 40.0, 150.0, 68.0)
        fm_tar = st.number_input("FM Target %", 3.0, 40.0, 10.0)
        ftp_tar = st.number_input("FTP Target (W)", 50, 600, 275)
    with col3:
        st.warning("### SCENARIO")
        dist = st.number_input("Distanza (Km)", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza (%)", 0.0, 20.0, 7.0)
        bike = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.0)

    if st.button("🚀 ELABORA REPORT PROFESSIONALE", use_container_width=True):
        t_a = BioPerformance.estimate_time(ftp_att, p_att, dist, grad, bike)
        t_t = BioPerformance.estimate_time(ftp_tar, p_tar, dist, grad, bike)
        zones = BioPerformance.get_zones(ftp_tar, lthr)
        data_ita = date.today().strftime("%d/%m/%Y")
        
        st.session_state['report'] = {
            'nome': nome, 'cognome': cog, 'alt': altezza, 'prof': profilo,
            'p_a': p_att, 'fm_a': fm_att, 'ftp_a': ftp_att, 'lthr': lthr,
            'p_t': p_tar, 'fm_t': fm_tar, 'ftp_t': ftp_tar,
            'dist': dist, 'grad': grad, 'bike': bike,
            't_a': t_a, 't_t': t_t, 'zones': zones, 'data': data_ita, 'raw_data': date.today().isoformat()
        }

    if 'report' in st.session_state:
        r = st.session_state['report']
        st.divider()
        st.subheader(f"📊 Analisi {r['nome']} {r['cognome']} del {r['data']}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Peso", f"{r['p_a']} -> {r['p_t']} kg", f"{r['p_t']-r['p_a']:.1f} kg", delta_color="inverse")
        m2.metric("FM", f"{r['fm_a']}% -> {r['fm_t']}%", f"{r['fm_t']-r['fm_a']:.1f}%", delta_color="inverse")
        m3.metric("Tempo Scalata", f"{r['t_a']:.2f} min", f"-{r['t_a']-r['t_t']:.2f} min")
        m4.metric("Potenza Specifica", f"{r['ftp_t']/r['p_t']:.2f} W/kg")

        st.table(pd.DataFrame(r['zones'], columns=["Zona", "Watt Min", "Watt Max", "BPM Min", "BPM Max"]))
        
        with st.expander("📊 Benchmark Composizione Corporea"):
            st.table(pd.DataFrame(BioPerformance.get_fm_benchmarks()[1:], columns=BioPerformance.get_fm_benchmarks()[0]))

        c_save, c_pdf = st.columns(2)
        with c_save:
            if st.button("💾 SALVA VISITA"):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM atleti WHERE cognome=? AND nome=?", (r['cognome'], r['nome']))
                    row = cursor.fetchone()
                    a_id = row[0] if row else None
                    if not a_id:
                        cursor.execute("INSERT INTO atleti (nome, cognome, altezza, profilo) VALUES (?,?,?,?)", (r['nome'], r['cognome'], r['alt'], r['prof']))
                        a_id = cursor.lastrowid
                    cursor.execute("""INSERT INTO visite (atleta_id, data, peso, fm, ftp, lthr, peso_t, fm_t, ftp_t, dist_km, grad, bike_w, t_att, t_tar) 
                                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (a_id, r['raw_data'], r['p_a'], r['fm_a'], r['ftp_a'], r['lthr'], r['p_t'], r['fm_t'], r['ftp_t'], r['dist'], r['grad'], r['bike'], r['t_a'], r['t_t']))
                    conn.commit()
                st.success("Dati archiviati!")

        with c_pdf:
            pdf = FPDF()
            pdf.add_page()
            
            # Header PDF Blu con LOGO
            pdf.set_fill_color(0, 51, 102); pdf.rect(0, 0, 210, 45, 'F')
            if os.path.exists(LOGO_PATH):
                pdf.image(LOGO_PATH, 10, 8, 33)
            
            pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 22)
            pdf.cell(190, 15, "PERFORMANCE LAB PRO", 0, 1, 'R')
            pdf.set_font("Arial", 'I', 10)
            pdf.cell(190, 5, f"Analisi Nutrizionale e Prestativa - {r['data']}", 0, 1, 'R')
            pdf.ln(25)
            
            # Sezioni PDF
            pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", 'B', 12); pdf.set_fill_color(240, 240, 240)
            pdf.cell(190, 10, pdf_safe(f"ATLETA: {r['nome']} {r['cognome']}"), 1, 1, 'L', True)
            pdf.set_font("Arial", '', 11)
            pdf.cell(95, 8, f"Peso: {r['p_a']}kg -> {r['p_t']}kg", 1, 0)
            pdf.cell(95, 8, f"FM: {r['fm_a']}% -> {r['fm_t']}%", 1, 1)
            pdf.cell(190, 8, f"Miglioramento Scalata: -{r['t_a']-r['t_t']:.2f} minuti", 1, 1); pdf.ln(5)

            # Zone
            pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "ZONE DI ALLENAMENTO", 1, 1, 'L', True)
            pdf.set_font("Arial", '', 10)
            for z in r['zones']:
                pdf.cell(50, 7, pdf_safe(z[0]), 1, 0)
                pdf.cell(70, 7, f"{z[1]}-{z[2]} Watt", 1, 0, 'C')
                pdf.cell(70, 7, f"{z[3]}-{z[4]} BPM", 1, 1, 'C')
            pdf.ln(5)

            # Benchmark
            pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "RIFERIMENTI MASSA GRASSA CATEGORIE PRO", 1, 1, 'L', True)
            pdf.set_font("Arial", '', 9)
            for b in BioPerformance.get_fm_benchmarks():
                pdf.cell(63, 7, pdf_safe(b[0]), 1, 0); pdf.cell(63, 7, b[1], 1, 0, 'C'); pdf.cell(64, 7, b[2], 1, 1, 'C')

            st.download_button("📄 SCARICA PDF COMPLETO", data=pdf.output(dest='S').encode('latin-1', 'ignore'), file_name=f"Report_{r['cognome']}.pdf", use_container_width=True)

elif menu == "📂 Archivio Storico":
    st.header("🗄️ Database Atleti")
    # ... (Stessa logica archivio precedente)
