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
        # f_res: Resistenza totale (Gravità + Attrito volvente stimato a 0.005)
        # g = 9.81 m/s²
        f_res = (float(peso) + float(bike_w)) * 9.81 * ((float(pend)/100) + 0.005)
        if f_res <= 0 or watt <= 0: return 0
        speed_ms = float(watt) / f_res
        return (float(km) * 1000 / speed_ms) / 60

    @staticmethod
    def get_zones(ftp, lthr):
        # Utilizzo dei caratteri Unicode richiesti per i pedici (es. VO₂)
        return [
            ("Z1 Recupero", 0, int(ftp*0.55), 0, int(lthr*0.68)),
            ("Z2 Endurance", int(ftp*0.56), int(ftp*0.75), int(lthr*0.69), int(lthr*0.83)),
            ("Z3 Tempo", int(ftp*0.76), int(ftp*0.90), int(lthr*0.84), int(lthr*0.94)),
            ("Z4 Soglia", int(ftp*0.91), int(ftp*1.05), int(lthr*0.95), int(lthr*1.05)),
            ("Z5 VO₂max", int(ftp*1.06), int(ftp*1.30), int(lthr*1.06), 220)
        ]

def pdf_safe(text):
    if not text: return ""
    # Mappatura per esportazione PDF (che non supporta bene certi caratteri Unicode di base)
    rep = {"à": "a", "è": "e", "é": "e", "ì": "i", "ò": "o", "ù": "u", "²": "2", "₂": "2", "VO₂": "VO2"}
    for k, v in rep.items(): text = text.replace(k, v)
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# ---------------------------------------------------------
# 3. INTERFACCIA E SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    st.markdown("### 🛠️ Controllo Sistema")
    menu = st.radio("NAVIGAZIONE", ["➕ Nuova Valutazione", "📂 Archivio & Edit"])
    st.divider()
    st.caption("Performance Lab Pro v3.1 - Bio-Nutrizione & Sport")

# --- SEZIONE: NUOVA VALUTAZIONE ---
if menu == "➕ Nuova Valutazione":
    st.header("📋 Protocollo di Valutazione Biomeccanica")
    
    with get_connection() as conn:
        db_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)

    with st.container(border=True):
        st.subheader("👤 Dati Anagrafici")
        c1, c2 = st.columns(2)
        
        exist_cog = c1.selectbox("Cerca Atleta Esistente", [""] + sorted(db_atleti['cognome'].unique().tolist()))
        new_cog = c1.text_input("...o Cognome Nuovo")
        cog = new_cog if new_cog else exist_cog
        
        atl_data = db_atleti[db_atleti['cognome'] == cog].iloc[0] if cog in db_atleti['cognome'].values else None
        nome = c2.text_input("Nome", value=atl_data['nome'] if atl_data is not None else "")
        
        col_an, col_pr = st.columns(2)
        altezza = col_an.number_input("Altezza (cm)", 120, 230, int(atl_data['altezza']) if atl_data is not None else 175)
        data_visita = col_an.date_input("Data Analisi", date.today())
        profilo = col_pr.selectbox("Profilo Atleta", ["Scalatore", "Passista", "Triatleta", "Granfondista"], 
                                   index=["Scalatore", "Passista", "Triatleta", "Granfondista"].index(atl_data['profilo']) if atl_data is not None else 0)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("📊 Stato Attuale")
        p_att = st.number_input("Peso (kg)", 40.0, 150.0, 70.0, step=0.1)
        fm_att = st.number_input("Massa Grassa (FM %)", 3.0, 45.0, 15.0, step=0.1)
        tipo_test = st.selectbox("Tipo Test FTP", ["Manuale", "Test 20'", "Test 8'", "Incrementale"])
        val_test = st.number_input("Watt Test", 50, 600, 250)
        ftp_att = BioPerformance.calculate_ftp(tipo_test, val_test)
        lthr = st.number_input("Soglia LTHR (bpm)", 80, 220, 160)
        st.metric("FTP Stimata", f"{ftp_att:.0f} W", f"{ftp_att/p_att:.2f} W/kg")

    with col2:
        st.subheader("🎯 Target")
        p_tar = st.number_input("Peso Target (kg)", 40.0, 150.0, 68.0, step=0.1)
        fm_tar = st.number_input("FM Target %", 3.0, 40.0, 10.0, step=0.1)
        ftp_tar = st.number_input("FTP Target (W)", 50, 600, 280)
        st.metric("Target W/kg", f"{ftp_tar/p_tar:.2f} W/kg", delta=f"{(ftp_tar/p_tar)-(ftp_att/p_att):.2f}")

    with col3:
        st.subheader("🏔️ Scenario Salita")
        dist = st.number_input("Km Salita", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza %", 0.0, 20.0, 7.0)
        bike = st.number_input("Peso Bici + Kit (kg)", 5.0, 15.0, 7.5)

    if st.button("🚀 ELABORA PERFORMANCE", use_container_width=True):
        t_a = BioPerformance.estimate_time(ftp_att, p_att, dist, grad, bike)
        t_t = BioPerformance.estimate_time(ftp_tar, p_tar, dist, grad, bike)
        bmi_a = p_att / ((altezza/100)**2)
        bmi_t = p_tar / ((altezza/100)**2)
        
        st.session_state['rep'] = {
            'nome': nome, 'cognome': cog, 'alt': altezza, 'prof': profilo, 'data': data_visita.strftime("%d/%m/%Y"),
            'p_a': p_att, 'fm_a': fm_att, 'ftp_a': ftp_att, 'lthr': lthr, 'bmi_a': bmi_a,
            'p_t': p_tar, 'fm_t': fm_tar, 'ftp_t': ftp_tar, 'bmi_t': bmi_t,
            'dist': dist, 'grad': grad, 'bike': bike, 't_a': t_a, 't_t': t_t,
            'raw_data': data_visita.isoformat(), 'zones': BioPerformance.get_zones(ftp_tar, lthr)
        }

    if 'rep' in st.session_state:
        r = st.session_state['rep']
        st.divider()
        
        c_bio, c_perf = st.columns(2)
        with c_bio:
            st.info("**📋 Analisi Biometrica**")
            st.write(f"- BMI: {r['bmi_a']:.1f} → {r['bmi_t']:.1f}")
            st.write(f"- Peso: {r['p_a']} kg → {r['p_t']} kg")
            st.write(f"- Massa Grassa: {r['fm_a']}% → {r['fm_t']}%")
        with c_perf:
            st.info("**🚴 Performance Scenario**")
            st.write(f"- Scenario: {r['dist']} km @ {r['grad']}%")
            st.write(f"- Tempo Attuale: {r['t_a']:.2f} min")
            st.write(f"- Tempo Target: {r['t_t']:.2f} min")
            st.metric("Guadagno Cronometrico", f"-{r['t_a']-r['t_t']:.2f} min", delta_color="normal")

        st.subheader("⚡ Zone di Potenza & FC (Target)")
        df_zones = pd.DataFrame(r['zones'], columns=["Zona", "Watt Min", "Watt Max", "BPM Min", "BPM Max"])
        st.table(df_zones)

        # Salvataggio e PDF (Logica invariata ma pulita)
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("💾 SALVA IN ARCHIVIO", use_container_width=True):
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
            st.success("Dati archiviati!"); st.rerun()

        # Generazione PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_fill_color(0, 51, 102); pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 18); pdf.cell(190, 15, "REPORT PERFORMANCE LAB", 0, 1, 'R')
        pdf.set_font("Arial", '', 10); pdf.cell(190, 5, pdf_safe(f"Atleta: {r['nome']} {r['cognome']} | Data: {r['data']}"), 0, 1, 'R')
        pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, "1. PARAMETRI BIOMETRICI", 1, 1, 'L', False)
        pdf.set_font("Arial", '', 10)
        pdf.cell(95, 8, f"Peso Attuale: {r['p_a']}kg / Target: {r['p_t']}kg", 1); pdf.cell(95, 8, f"FM Attuale: {r['fm_a']}% / Target: {r['fm_t']}%", 1, 1)
        pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "2. SIMULAZIONE PERFORMANCE", 1, 1, 'L', False)
        pdf.set_font("Arial", '', 10); pdf.cell(190, 8, pdf_safe(f"Percorso: {r['dist']}km al {r['grad']}% - Peso Sistema: {r['p_a']+r['bike']}kg"), 1, 1)
        pdf.cell(95, 8, f"Tempo Attuale: {r['t_a']:.2f} min", 1); pdf.cell(95, 8, f"Tempo Target: {r['t_t']:.2f} min", 1, 1)
        pdf.set_font("Arial", 'B', 11); pdf.cell(190, 10, f"MIGLIORAMENTO STIMATO: -{r['t_a']-r['t_t']:.2f} min", 1, 1, 'C')
        pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "3. ZONE DI ALLENAMENTO (TARGET)", 1, 1, 'L', False)
        for z in r['zones']:
            pdf.cell(60, 7, pdf_safe(z[0]), 1); pdf.cell(65, 7, f"{z[1]}-{z[2]} W", 1); pdf.cell(65, 7, f"{z[3]}-{z[4]} bpm", 1, 1)
        
        col_btn2.download_button("📄 SCARICA REPORT PDF", data=pdf.output(dest='S').encode('latin-1', 'ignore'), file_name=f"Report_{r['cognome']}.pdf", use_container_width=True)

# --- SEZIONE: ARCHIVIO ---
elif menu == "📂 Archivio & Edit":
    st.header("🗄️ Database Atleti")
    with get_connection() as conn:
        at = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    if not at.empty:
        c1, c2 = st.columns([3, 1])
        sel_atl = c1.selectbox("Seleziona l'atleta", at.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}", axis=1))
        a_id = int(sel_atl.split(" - ")[0])
        
        if c2.button("🗑️ ELIMINA TUTTO", help="Elimina atleta e tutte le visite"):
            with get_connection() as conn:
                conn.execute(f"DELETE FROM visite WHERE atleta_id={a_id}")
                conn.execute(f"DELETE FROM atleti WHERE id={a_id}")
                conn.commit()
            st.rerun()

        with get_connection() as conn:
            vi = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id} ORDER BY data DESC", conn)

        if not vi.empty:
            st.subheader("🗓️ Storico Valutazioni")
            st.dataframe(vi, use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("⚖️ Analisi Evolutiva")
            c_v1, c_v2 = st.columns(2)
            v1_id = c_v1.selectbox("Visita Iniziale (A)", vi['id'])
            v2_id = c_v2.selectbox("Visita Recente (B)", vi['id'])
            
            if st.button("📊 CONFRONTA PROGRESSI"):
                v1 = vi[vi['id']==v1_id].iloc[0]
                v2 = vi[vi['id']==v2_id].iloc[0]
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Delta Peso", f"{v2['peso']} kg", f"{v2['peso']-v1['peso']:.1f} kg", delta_color="inverse")
                m2.metric("Delta FM", f"{v2['fm']}%", f"{v2['fm']-v1['fm']:.1f}%", delta_color="inverse")
                m3.metric("Delta FTP", f"{v2['ftp']} W", f"{v2['ftp']-v1['ftp']:.0f} W")
    else:
        st.info("Nessun dato presente in archivio.")
