import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
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
# 2. MOTORE SCIENTIFICO
# ---------------------------------------------------------
class BioPerformance:
    @staticmethod
    def calculate_ftp(tipo, valore):
        mapping = {"Manuale": 1.0, "Test 20'": 0.95, "Test 8'": 0.90, "Incrementale": 0.75}
        return valore * mapping.get(tipo, 1.0)

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        f_res = (float(peso) + float(bike_w)) * 9.81 * ((float(pend)/100) + 0.005)
        if f_res <= 0 or watt <= 0: return 0
        speed_ms = float(watt) / f_res
        return (float(km) * 1000 / speed_ms) / 60

    @staticmethod
    def get_zones(ftp, lthr):
        return [
            ("Z1 Recupero", 0, int(ftp*0.55), 0, int(lthr*0.68)),
            ("Z2 Endurance", int(ftp*0.56), int(ftp*0.75), int(lthr*0.69), int(lthr*0.83)),
            ("Z3 Tempo", int(ftp*0.76), int(ftp*0.90), int(lthr*0.84), int(lthr*0.94)),
            ("Z4 Soglia", int(ftp*0.91), int(ftp*1.05), int(lthr*0.95), int(lthr*1.05)),
            ("Z5 VO₂max", int(ftp*1.06), int(ftp*1.30), int(lthr*1.06), 220)
        ]

    @staticmethod
    def get_category_benchmarks():
        data = [
            ["World Tour", "5-7%", "6.0 - 6.5", 65],
            ["Pro Continental", "7-9%", "5.5 - 6.0", 68],
            ["Elite/U23", "8-11%", "4.5 - 5.5", 70],
            ["Amatore Top", "10-14%", "3.5 - 4.5", 72],
            ["Cicloturista", "> 15%", "< 3.0", 78]
        ]
        return pd.DataFrame(data, columns=["Categoria", "Range FM %", "W/kg (Soglia)", "Peso Medio (kg)"])

def pdf_safe(text):
    if not text: return ""
    rep = {"à": "a", "è": "e", "é": "e", "ì": "i", "ò": "o", "ù": "u", "²": "2", "₂": "2", "VO₂": "VO2"}
    for k, v in rep.items(): text = text.replace(k, v)
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# ---------------------------------------------------------
# 3. INTERFACCIA
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    st.markdown("---")
    menu = st.radio("NAVIGAZIONE", ["➕ Nuova Valutazione", "📂 Archivio & Edit"])

if menu == "➕ Nuova Valutazione":
    st.header("📋 Inserimento Protocollo Valutazione")
    
    with get_connection() as conn:
        db_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)

    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        exist_cog = c1.selectbox("Cerca Cognome Esistente", [""] + sorted(db_atleti['cognome'].unique().tolist()))
        new_cog = c2.text_input("...o Inserisci Nuovo")
        cog = new_cog if new_cog else exist_cog
        
        atl_data = db_atleti[db_atleti['cognome'] == cog].iloc[0] if cog in db_atleti['cognome'].values else None
        nome = st.text_input("Nome", value=atl_data['nome'] if atl_data is not None else "")
        
        col_an, col_pr = st.columns(2)
        altezza = col_an.number_input("Altezza (cm)", 120, 230, int(atl_data['altezza']) if atl_data is not None else 175)
        data_visita = col_an.date_input("Data Analisi", date.today())
        profilo = col_pr.selectbox("Profilo Atleta", ["Scalatore", "Passista", "Triatleta", "Granfondista"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("📊 1. Stato Attuale")
        p_att = st.number_input("Peso (kg)", 40.0, 150.0, 70.0, step=0.1)
        fm_att = st.number_input("FM %", 3.0, 45.0, 15.0, step=0.1)
        tipo_test = st.selectbox("Tipo Test FTP", ["Manuale", "Test 20'", "Test 8'", "Incrementale"])
        val_test = st.number_input("Watt Test", 50, 700, 250)
        ftp_att = BioPerformance.calculate_ftp(tipo_test, val_test)
        lthr = st.number_input("LTHR (bpm)", 80, 220, 160)
        bmi_att = p_att / ((altezza/100)**2)

    with col2:
        st.subheader("🎯 2. Target")
        p_tar = st.number_input("Peso Target (kg)", 40.0, 150.0, 68.0, step=0.1)
        fm_tar = st.number_input("FM Target %", 3.0, 40.0, 10.0, step=0.1)
        ftp_tar = st.number_input("FTP Target (W)", 50, 700, 280)
        bmi_tar = p_tar / ((altezza/100)**2)

    with col3:
        st.subheader("🏔️ 3. Scenario Salita")
        dist = st.number_input("Km Salita", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza %", 0.0, 20.0, 7.0)
        bike = st.number_input("Peso Bici (kg)", 5.0, 15.0, 7.5)

    if st.button("🚀 ELABORA E STAMPA OUTPUT", use_container_width=True):
        t_a = BioPerformance.estimate_time(ftp_att, p_att, dist, grad, bike)
        t_t = BioPerformance.estimate_time(ftp_tar, p_tar, dist, grad, bike)
        
        st.session_state['rep'] = {
            'nome': nome, 'cognome': cog, 'alt': altezza, 'prof': profilo, 'data': data_visita.strftime("%d/%m/%Y"),
            'p_a': p_att, 'fm_a': fm_att, 'ftp_a': ftp_att, 'lthr': lthr, 'bmi_a': bmi_att, 'test': tipo_test,
            'p_t': p_tar, 'fm_t': fm_tar, 'ftp_t': ftp_tar, 'bmi_t': bmi_tar,
            'dist': dist, 'grad': grad, 'bike': bike, 't_a': t_a, 't_t': t_t,
            'raw_data': data_visita.isoformat(), 'zones': BioPerformance.get_zones(ftp_tar, lthr)
        }

    # --- OUTPUT SCHERMO (DENTRO L'IF MENU) ---
    if 'rep' in st.session_state:
        r = st.session_state['rep']
        st.divider()
        
        st.subheader("🧬 Analisi Biometrica e Funzionale")
        wkg_att = r['ftp_a'] / r['p_a']
        wkg_tar = r['ftp_t'] / r['p_t']
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Peso", f"{r['p_a']} kg", f"Target: {r['p_t']} kg")
            st.write(f"**BMI:** {r['bmi_a']:.1f} → **{r['bmi_t']:.1f}**")
        with c2:
            st.metric("FM %", f"{r['fm_a']} %", f"Target: {r['fm_t']} %")
            st.write(f"**Massa Grassa:** {r['p_a']*(r['fm_a']/100):.1f}kg → **{r['p_t']*(r['fm_t']/100):.1f}kg**")
        with c3:
            st.metric("FTP (Potenza)", f"{int(r['ftp_a'])} W", f"Target: {int(r['ftp_t'])} W")
            st.write(f"**Protocollo:** {r['test']}")
        with c4:
            st.metric("Rapporto W/kg", f"{wkg_att:.2f}", f"Target: {wkg_tar:.2f}")
            st.write(f"**Delta:** {wkg_tar - wkg_att:+.2f} W/kg")

        st.subheader("🏔️ Analisi Scenario Salita")
        cs1, cs2 = st.columns(2)
        with cs1:
            st.info(f"**Input:** {r['dist']} km | {r['grad']}% | Bici {r['bike']} kg")
        with cs2:
            st.success(f"**Tempo Attuale:** {r['t_a']:.2f} min  \n**Tempo Target:** {r['t_t']:.2f} min  \n**Differenza:** -{r['t_a']-r['t_t']:.2f} min")

        st.subheader("⚡ Zone di Potenza & FC (Target)")
        st.table(pd.DataFrame(r['zones'], columns=["Zona", "Watt Min", "Watt Max", "BPM Min", "BPM Max"]))

        st.subheader("🏁 Posizionamento Rispetto alle Categorie")
        bench_df = BioPerformance.get_category_benchmarks()
        st.table(bench_df)

        ca, cb = st.columns(2)
        if ca.button("💾 SALVA IN ARCHIVIO"):
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
            st.success("Dati salvati!")

        # GENERAZIONE PDF
        pdf = FPDF()
        pdf.add_page()
        if os.path.exists(LOGO_PATH):
            pdf.image(LOGO_PATH, 10, 8, 40)
        pdf.ln(35)
        pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, pdf_safe(f"REPORT: {r['nome']} {r['cognome']}"), 0, 1, 'C')
        pdf.set_font("Arial", '', 10); pdf.cell(0, 5, f"Data: {r['data']} | Profilo: {r['prof']} | Altezza: {r['alt']}cm", 0, 1, 'C')
        
        pdf.ln(10); pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "1. STATO ATTUALE (INPUT)", 1, 1, 'L', True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(63, 8, f"Peso: {r['p_a']} kg", 1); pdf.cell(63, 8, f"FM: {r['fm_a']}%", 1); pdf.cell(64, 8, f"BMI: {r['bmi_a']:.1f}", 1, 1)
        pdf.cell(63, 8, f"FTP: {r['ftp_a']} W ({r['test']})", 1); pdf.cell(63, 8, f"LTHR: {r['lthr']} bpm", 1); pdf.cell(64, 8, f"W/kg: {r['ftp_a']/r['p_a']:.2f}", 1, 1)

        pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "2. TARGET DEFINITI", 1, 1, 'L', True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(63, 8, f"Peso Target: {r['p_t']} kg", 1); pdf.cell(63, 8, f"FM Target: {r['fm_t']}%", 1); pdf.cell(64, 8, f"FTP Target: {r['ftp_t']} W", 1, 1)

        pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "3. ANALISI PERFORMANCE", 1, 1, 'L', True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, pdf_safe(f"Salita di {r['dist']}km al {r['grad']}%"), 1, 1)
        pdf.cell(95, 8, f"Tempo Attuale: {r['t_a']:.2f} min", 1); pdf.cell(95, 8, f"Tempo Target: {r['t_t']:.2f} min", 1, 1)
        pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, f"DIFFERENZA: -{r['t_a']-r['t_t']:.2f} min", 1, 1, 'C')

        cb.download_button("📄 SCARICA PDF", data=pdf.output(dest='S').encode('latin-1', 'ignore'), file_name=f"Report_{r['cognome']}.pdf", use_container_width=True)

elif menu == "📂 Archivio & Edit":
    st.header("🗄️ Gestione Archivio")
    with get_connection() as conn:
        at = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    if not at.empty:
        sel_atl = st.selectbox("Seleziona l'atleta", at.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}", axis=1))
        a_id = int(sel_atl.split(" - ")[0])
        with get_connection() as conn:
            vi = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id} ORDER BY data DESC", conn)
        st.dataframe(vi, hide_index=True)
        
        if st.button("🗑️ ELIMINA ATLETA"):
            with get_connection() as conn:
                conn.execute(f"DELETE FROM visite WHERE atleta_id={a_id}")
                conn.execute(f"DELETE FROM atleti WHERE id={a_id}")
                conn.commit()
            st.rerun()
