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
               ("Z5 VO2max", int(ftp*1.06), int(ftp*1.20))]
        z_c = [("Z1 Recupero", 0, int(lthr*0.68)), ("Z2 Endurance", int(lthr*0.69), int(lthr*0.83)),
               ("Z3 Tempo", int(lthr*0.84), int(lthr*0.94)), ("Z4 Soglia", int(lthr*0.95), int(lthr*1.05)),
               ("Z5 VO2max", int(lthr*1.06), 220)]
        return z_p, z_c

def pdf_safe(text):
    if not text: return ""
    rep = {"²": "2", "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9", "à": "a", "è": "e", "é": "e", "ì": "i", "ò": "o", "ù": "u"}
    for k, v in rep.items(): text = text.replace(k, v)
    return str(text).encode('ascii', 'ignore').decode('ascii')

# 3. INTERFACCIA
menu = st.sidebar.radio("NAVIGAZIONE", ["➕ Nuova Valutazione", "📂 Archivio"])

if menu == "➕ Nuova Valutazione":
    st.header("📋 Protocollo di Valutazione e Scenario")
    
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
        profilo = c4.selectbox("Profilo Atleta", ["Scalatore", "Passista", "Triatleta", "Granfondista"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**SITUAZIONE ATTUALE (Oggi)**")
        p_att = st.number_input("Peso Odierno (kg)", 40.0, 150.0, 70.0)
        fm_att = st.number_input("Massa Grassa %", 3.0, 40.0, 15.0)
        ftp_att = st.number_input("FTP Attuale (W)", 50, 600, 250)
        lthr = st.number_input("Soglia Cardio (LTHR)", 80, 220, 165)
    with col2:
        st.markdown("**TARGET PROGRAMMATO**")
        p_tar = st.number_input("Peso Obiettivo (kg)", 40.0, 150.0, 68.0)
        fm_tar = st.number_input("Massa Grassa Target %", 3.0, 40.0, 10.0)
        ftp_tar = st.number_input("FTP Obiettivo (W)", 50, 600, 275)
    with col3:
        st.markdown("**SCENARIO DI TEST (Salita)**")
        dist = st.number_input("Lunghezza (Km)", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza Media (%)", 0.0, 20.0, 7.0)
        bike = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.0)

    if st.button("🚀 GENERA ANALISI PRESTAZIONALE", use_container_width=True):
        if not cog or not nome:
            st.error("Inserire Cognome e Nome.")
        else:
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
        
        # 1. METRICHE FISICHE E TEMPORALI
        st.subheader("⏱️ Risultati e Proiezioni")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Peso", f"{r['p_a']} → {r['p_t']} kg", f"{r['p_t']-r['p_a']:.1f} kg", delta_color="inverse")
        m2.metric("Massa Grassa", f"{r['fm_a']}% → {r['fm_t']}%", f"{r['fm_t']-r['fm_a']:.1f}%", delta_color="inverse")
        m3.metric("Tempo Scalata", f"{r['t_a']:.2f} min", f"-{r['t_a']-r['t_t']:.2f} min", delta_color="normal")
        m4.metric("W/kg Target", f"{r['ftp_t']/r['p_t']:.2f}")

        # 2. TABELLE ZONE
        colz1, colz2 = st.columns(2)
        with colz1:
            st.markdown("### ⚡ Zone Potenza (Target)")
            st.table(pd.DataFrame(r['z_p'], columns=["Zona", "Min (W)", "Max (W)"]))
        with colz2:
            st.markdown(f"### ❤️ Zone Cardio (Soglia: {r['lthr']} bpm)")
            st.table(pd.DataFrame(r['z_c'], columns=["Zona", "Min (bpm)", "Max (bpm)"]))

        st.markdown("### 📊 Benchmark FM Categorie")
        st.table(BioPerformance.get_fm_benchmarks())

        # 3. PULSANTI AZIONE
        c_act1, c_act2 = st.columns(2)
        with c_act1:
            if st.button("💾 SALVA IN ARCHIVIO"):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM atleti WHERE cognome=? AND nome=?", (r['cognome'], r['nome']))
                    row = cursor.fetchone()
                    a_id = row[0] if row else None
                    if not a_id:
                        cursor.execute("INSERT INTO atleti (nome, cognome, altezza, profilo) VALUES (?,?,?,?)", (r['nome'], r['cognome'], r['alt'], r['prof']))
                        a_id = cursor.lastrowid
                    cursor.execute("""INSERT INTO visite (atleta_id, data, peso, fm, ftp, lthr, peso_t, fm_t, ftp_t, dist_km, grad, bike_w, t_att, t_tar) 
                                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (a_id, r['data'], r['p_a'], r['fm_a'], r['ftp_a'], r['lthr'], r['p_t'], r['fm_t'], r['ftp_t'], r['dist'], r['grad'], r['bike'], r['t_a'], r['t_t']))
                    conn.commit()
                st.success("Visita salvata correttamente!")

        with c_act2:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, pdf_safe(f"REPORT PERFORMANCE: {r['nome']} {r['cognome']}"), 0, 1, 'C')
            pdf.set_font("Arial", '', 11); pdf.ln(5)
            
            # Sezione Biometrica
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 12)
            pdf.cell(190, 10, "ANALISI BIOMETRICA E PERFORMANCE", 1, 1, 'L', True)
            pdf.set_font("Arial", '', 11)
            pdf.cell(95, 8, pdf_safe(f"Peso: {r['p_a']}kg -> {r['p_t']}kg"), 1, 0)
            pdf.cell(95, 8, pdf_safe(f"FM: {r['fm_a']}% -> {r['fm_t']}%"), 1, 1)
            pdf.cell(190, 8, pdf_safe(f"Tempo Salita Oggi: {r['t_a']:.2f} min"), 1, 1)
            pdf.cell(190, 8, pdf_safe(f"Tempo Salita Target: {r['t_t']:.2f} min"), 1, 1)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 10, pdf_safe(f"DIFFERENZA: -{r['t_a']-r['t_t']:.2f} minuti"), 1, 1, 'C'); pdf.ln(5)
            
            # Zone
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(95, 10, "ZONE POTENZA (W)", 1, 0, 'C', True); pdf.cell(95, 10, "ZONE CARDIO (BPM)", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 10)
            for i in range(len(r['z_p'])):
                pdf.cell(95, 7, pdf_safe(f"{r['z_p'][i][0]}: {r['z_p'][i][1]}-{r['z_p'][i][2]} W"), 1, 0)
                pdf.cell(95, 7, pdf_safe(f"{r['z_c'][i][0]}: {r['z_c'][i][1]}-{r['z_c'][i][2]} bpm"), 1, 1)
            
            st.download_button("📄 SCARICA PDF COMPLETO", data=pdf.output(dest='S').encode('latin-1', 'ignore'), file_name=f"Report_{r['cognome']}.pdf")

elif menu == "📂 Archivio":
    st.header("🗄️ Archivio Storico Atleti")
    with get_connection() as conn: at = pd.read_sql_query("SELECT * FROM atleti", conn)
    if not at.empty:
        sel_atleta = st.selectbox("Seleziona Atleta", at.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}", axis=1))
        a_id = int(sel_atleta.split(" - ")[0])
        with get_connection() as conn:
            vi = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id} ORDER BY data DESC", conn)
        if not vi.empty:
            st.dataframe(vi.drop(columns=['atleta_id']), hide_index=True)
