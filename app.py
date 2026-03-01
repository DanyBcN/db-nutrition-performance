import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from fpdf import FPDF

# 1. CONFIGURAZIONE E DATABASE
st.set_page_config(page_title="Performance Lab Pro v3", layout="wide", page_icon="🧬")
DB_NAME = "performance_lab_pro.db"

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

# 2. MOTORE SCIENTIFICO
class BioPerformance:
    @staticmethod
    def get_fm_benchmarks():
        return pd.DataFrame({
            "Categoria": ["Pro World Tour", "Continental/U23", "Elite Amatori", "Granfondista"],
            "Uomo (FM %)": ["5 - 8%", "8 - 11%", "10 - 14%", "13 - 17%"],
            "Donna (FM %)": ["12 - 16%", "16 - 20%", "18 - 22%", "21 - 25%"]
        })

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        f_res = (peso + bike_w) * 9.81 * ((pend/100) + 0.005)
        if f_res <= 0 or watt <= 0: return 0
        speed_ms = watt / f_res
        return (km * 1000 / speed_ms) / 60

    @staticmethod
    def get_zones(ftp, lthr):
        z_p = [("Z1 Recupero", 0, int(ftp*0.55)), ("Z2 Endurance", int(ftp*0.56), int(ftp*0.75)),
               ("Z3 Tempo", int(ftp*0.76), int(ftp*0.90)), ("Z4 Soglia", int(ftp*0.91), int(ftp*1.05)),
               ("Z5 VO₂max", int(ftp*1.06), int(ftp*1.20))]
        z_c = [("Z1 Recupero", 0, int(lthr*0.68)), ("Z2 Endurance", int(lthr*0.69), int(lthr*0.83)),
               ("Z3 Tempo", int(lthr*0.84), int(lthr*0.94)), ("Z4 Soglia", int(lthr*0.95), int(lthr*1.05)),
               ("Z5 VO₂max", int(lthr*1.06), 220)]
        return z_p, z_c

def pdf_safe(text):
    if not text: return ""
    rep = {"²": "2", "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9", "à": "a", "è": "e", "é": "e", "ì": "i", "ò": "o", "ù": "u", "VO₂max": "VO2max"}
    for k, v in rep.items(): text = text.replace(k, v)
    return str(text).encode('ascii', 'ignore').decode('ascii')

# 3. INTERFACCIA
menu = st.sidebar.radio("NAVIGAZIONE", ["➕ Nuova Valutazione", "📂 Archivio"])

if menu == "➕ Nuova Valutazione":
    st.header("📋 Protocollo di Valutazione")
    
    with get_connection() as conn:
        db_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        exist_cog = c1.selectbox("Atleta Registrato", [""] + sorted(db_atleti['cognome'].unique().tolist()))
        new_cog = c1.text_input("...o Nuovo Cognome")
        cog = new_cog if new_cog else exist_cog
        atleta_data = db_atleti[db_atleti['cognome'] == cog].iloc[0] if cog in db_atleti['cognome'].values else None
        nome = c2.text_input("Nome", value=atleta_data['nome'] if atleta_data is not None else "")
        altezza = c3.number_input("Altezza (cm)", 120, 230, int(atleta_data['altezza']) if atleta_data is not None else 175)
        profilo = c4.selectbox("Profilo", ["Scalatore", "Passista", "Granfondista"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Oggi")
        p_att = st.number_input("Peso (kg)", 40.0, 150.0, 70.0)
        fm_att = st.number_input("FM (%)", 3.0, 40.0, 15.0)
        ftp_att = st.number_input("FTP (W)", 50, 600, 250)
        lthr = st.number_input("Soglia Cardio", 80, 220, 165)
    with col2:
        st.subheader("Target")
        p_tar = st.number_input("Peso Obbiettivo (kg)", 40.0, 150.0, 68.0)
        fm_tar = st.number_input("FM Obbiettivo (%)", 3.0, 40.0, 10.0)
        ftp_tar = st.number_input("FTP Obbiettiva (W)", 50, 600, 275)
    with col3:
        st.subheader("Salita")
        dist = st.number_input("Km", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza %", 0.0, 20.0, 7.0)
        bike = st.number_input("Peso Bici", 5.0, 15.0, 8.0)

    if st.button("🚀 GENERA ANALISI", use_container_width=True):
        t_a = BioPerformance.estimate_time(ftp_att, p_att, dist, grad, bike)
        t_t = BioPerformance.estimate_time(ftp_tar, p_tar, dist, grad, bike)
        z_p, z_c = BioPerformance.get_zones(ftp_tar, lthr)
        st.session_state['report'] = {
            'nome': nome, 'cognome': cog, 'alt': altezza, 'prof': profilo,
            'p_a': p_att, 'fm_a': fm_att, 'ftp_a': ftp_att, 'lthr': lthr,
            'p_t': p_tar, 'fm_t': fm_tar, 'ftp_t': ftp_tar,
            'dist': dist, 'grad': grad, 'bike': bike,
            't_a': t_a, 't_t': t_t, 'z_p': z_p, 'z_c': z_c, 'data': date.today().isoformat()
        }

    if 'report' in st.session_state:
        r = st.session_state['report']
        st.divider()
        
        # VISUALIZZAZIONE DATI FISICI
        st.subheader("⚖️ Composizione Corporea e Performance")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Peso", f"{r['p_a']} -> {r['p_t']} kg", f"{r['p_t']-r['p_a']:.1f}")
        m2.metric("Massa Grassa", f"{r['fm_a']}% -> {r['fm_t']}%", f"{r['fm_t']-r['fm_a']:.1f}%")
        m3.metric("Tempo Scalata", f"{r['t_a']:.2f} min", f"-{r['t_a']-r['t_t']:.2f} min", delta_color="normal")
        m4.metric("W/kg Target", f"{r['ftp_t']/r['p_t']:.2f}")

        # TABELLE
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            st.write("### ⚡ Zone Potenza (W)")
            st.table(pd.DataFrame(r['z_p'], columns=["Zona", "Min", "Max"]))
        with col_z2:
            st.write("### ❤️ Zone Cardio (bpm)")
            st.table(pd.DataFrame(r['z_c'], columns=["Zona", "Min", "Max"]))

        st.write("### 📊 Benchmark FM Categorie")
        st.table(BioPerformance.get_fm_benchmarks())

        # PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, pdf_safe(f"REPORT: {r['nome']} {r['cognome']}"), 0, 1, 'C')
        pdf.set_font("Arial", '', 11)
        pdf.cell(190, 10, pdf_safe(f"Peso: {r['p_a']}kg -> {r['p_t']}kg | FM: {r['fm_a']}% -> {r['fm_t']}%"), 1, 1)
        pdf.cell(190, 10, pdf_safe(f"Tempo Oggi: {r['t_a']:.2f} min | Target: {r['t_t']:.2f} min"), 1, 1)
        pdf.cell(190, 10, pdf_safe(f"Guadagno Stimato: {r['t_a']-r['t_t']:.2f} minuti"), 1, 1)
        
        st.download_button("📄 SCARICA PDF", data=pdf.output(dest='S').encode('latin-1', 'ignore'), file_name="Report.pdf")

elif menu == "📂 Archivio":
    st.write("Sezione Archivio")
