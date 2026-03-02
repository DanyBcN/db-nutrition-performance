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
# 2. LOGICA SCIENTIFICA E BENCHMARK
# ---------------------------------------------------------
class BioPerformance:
    @staticmethod
    def calculate_ftp(tipo, valore):
        mapping = {"Manuale": 1.0, "Test 20'": 0.95, "Test 8'": 0.90, "Incrementale": 0.75}
        return valore * mapping.get(tipo, 1.0)

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        # f_res = Forza totale (Gravità + Attrito volvente)
        f_res = (float(peso) + float(bike_w)) * 9.81 * ((float(pend)/100) + 0.005)
        if f_res <= 0 or watt <= 0: return 0
        speed_ms = float(watt) / f_res
        return (float(km) * 1000 / speed_ms) / 60

    @staticmethod
    def get_zones(ftp, lthr):
        return [
            ("Z1 Recupero Attivo", 0, int(ftp*0.55), 0, int(lthr*0.68)),
            ("Z2 Endurance (Longo)", int(ftp*0.56), int(ftp*0.75), int(lthr*0.69), int(lthr*0.83)),
            ("Z3 Tempo", int(ftp*0.76), int(ftp*0.90), int(lthr*0.84), int(lthr*0.94)),
            ("Z4 Soglia Lattacida", int(ftp*0.91), int(ftp*1.05), int(lthr*0.95), int(lthr*1.05)),
            ("Z5 VO₂max", int(ftp*1.06), int(ftp*1.30), int(lthr*1.06), 220)
        ]

    @staticmethod
    def get_benchmarks():
        return pd.DataFrame({
            "Categoria": ["World Tour", "Pro Continental", "Elite/Under23", "Amamatore Top", "Cicloturista"],
            "FM % (Range)": ["5-8%", "7-10%", "8-12%", "10-15%", "15-20%"],
            "W/kg (Soglia)": ["> 6.0", "5.5 - 6.0", "4.5 - 5.5", "3.5 - 4.5", "< 3.0"]
        })

def pdf_safe(text):
    if not text: return ""
    rep = {"à": "a", "è": "e", "é": "e", "ì": "i", "ò": "o", "ù": "u", "²": "2", "₂": "2", "VO₂": "VO2"}
    for k, v in rep.items(): text = text.replace(k, v)
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# ---------------------------------------------------------
# 3. UI SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    st.markdown("---")
    menu = st.radio("MENU PRINCIPALE", ["➕ Nuova Valutazione", "📂 Archivio Storico"])

# ---------------------------------------------------------
# SEZIONE: NUOVA VALUTAZIONE
# ---------------------------------------------------------
if menu == "➕ Nuova Valutazione":
    st.header("🔬 Protocollo di Valutazione Integrata")
    
    with get_connection() as conn:
        db_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)

    # --- INPUT ATLETA ---
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        # Logica autoproposta cognome
        cognomi_esistenti = sorted(db_atleti['cognome'].unique().tolist())
        cog = c1.selectbox("Cerca Cognome in Archivio", [""] + cognomi_esistenti)
        nuovo_cog = c1.text_input("...oppure inserisci nuovo Cognome")
        final_cog = nuovo_cog if nuovo_cog else cog
        
        atl_match = db_atleti[db_atleti['cognome'] == final_cog].iloc[0] if final_cog in db_atleti['cognome'].values else None
        
        nome = c2.text_input("Nome", value=atl_match['nome'] if atl_match is not None else "")
        altezza = c3.number_input("Altezza (cm)", 120, 230, int(atl_match['altezza']) if atl_match is not None else 175)
        data_v = st.date_input("Data Analisi", date.today())
        profilo = st.selectbox("Profilo Atleta", ["Scalatore", "Passista", "Triatleta", "Granfondista"])

    # --- 3 STATI DI INPUT ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("1️⃣ Stato Attuale")
        p_att = st.number_input("Peso (kg)", 30.0, 150.0, 70.0, key="p_a")
        fm_att = st.number_input("FM %", 3.0, 50.0, 15.0, key="fm_a")
        tipo_test = st.selectbox("Protocollo FTP", ["Manuale", "Test 20'", "Test 8'", "Incrementale"])
        val_test = st.number_input("Watt rilevati", 50, 700, 250)
        ftp_att = BioPerformance.calculate_ftp(tipo_test, val_test)
        lthr = st.number_input("LTHR (bpm)", 80, 220, 160)
        bmi_att = p_att / ((altezza/100)**2)
        st.caption(f"BMI attuale: {bmi_att:.1f} | FTP: {ftp_att:.0f}W")

    with col2:
        st.subheader("2️⃣ Target")
        p_tar = st.number_input("Peso Target (kg)", 30.0, 150.0, 68.0)
        fm_tar = st.number_input("FM Target %", 3.0, 50.0, 10.0)
        ftp_tar = st.number_input("FTP Target (W)", 50, 700, 280)
        bmi_tar = p_tar / ((altezza/100)**2)

    with col3:
        st.subheader("3️⃣ Scenario Salita")
        dist = st.number_input("Km Salita", 0.1, 100.0, 10.0)
        grad = st.number_input("Pendenza Media %", 0.0, 25.0, 7.0)
        bike = st.number_input("Peso Bici (kg)", 5.0, 20.0, 7.5)

    if st.button("🚀 ELABORA ANALISI BIOMETRICA E PERFORMANCE", use_container_width=True):
        t_att = BioPerformance.estimate_time(ftp_att, p_att, dist, grad, bike)
        t_tar = BioPerformance.estimate_time(ftp_tar, p_tar, dist, grad, bike)
        
        st.session_state['report'] = {
            'nome': nome, 'cognome': final_cog, 'alt': altezza, 'prof': profilo, 'data': data_v.strftime("%d/%m/%Y"),
            'p_a': p_att, 'fm_a': fm_att, 'ftp_a': ftp_att, 'lthr': lthr, 'bmi_a': bmi_att,
            'p_t': p_tar, 'fm_t': fm_tar, 'ftp_t': ftp_tar, 'bmi_t': bmi_tar,
            'dist': dist, 'grad': grad, 'bike': bike, 't_a': t_att, 't_t': t_tar,
            'raw_data': data_v.isoformat(), 'zones': BioPerformance.get_zones(ftp_tar, lthr)
        }

    # --- OUTPUT RISULTATI ---
    if 'report' in st.session_state:
        r = st.session_state['report']
        st.divider()
        
        st.subheader("📊 Risultati dell'Analisi")
        c_bio, c_perf = st.columns(2)
        
        with c_bio:
            st.markdown("#### Analisi Biometrica")
            st.write(f"**BMI:** {r['bmi_a']:.1f} (Attuale) → **{r['bmi_t']:.1f} (Ideale)**")
            st.write(f"**Peso:** {r['p_a']} kg → **{r['p_t']} kg**")
            st.write(f"**FM:** {r['fm_a']}% → **{r['fm_t']}%**")
            st.write(f"**Massa Grassa Assoluta:** {r['p_a']*(r['fm_a']/100):.1f} kg → **{r['p_t']*(r['fm_t']/100):.1f} kg**")

        with c_perf:
            st.markdown("#### Scenario Salita")
            st.write(f"Percorso: {r['dist']} km al {r['grad']}%")
            st.write(f"Tempo Attuale: **{r['t_a']:.2f} min** ({r['ftp_a']/r['p_a']:.2f} W/kg)")
            st.write(f"Tempo Target: **{r['t_t']:.2f} min** ({r['ftp_t']/r['p_t']:.2f} W/kg)")
            st.metric("Guadagno Stimato", f"-{r['t_a']-r['t_t']:.2f} min", delta_color="normal")

        # --- TABELLA ZONE ---
        st.markdown("#### ⚡ Zone di Allenamento Target")
        st.table(pd.DataFrame(r['zones'], columns=["Zona", "Watt Min", "Watt Max", "BPM Min", "BPM Max"]))

        # --- BENCHMARK ---
        st.markdown("#### 🏁 Benchmark di Riferimento")
        bench = BioPerformance.get_benchmarks()
        st.table(bench)
        
        # --- BOTTONI AZIONE ---
        ca, cb = st.columns(2)
        if ca.button("💾 SALVA ATLETA E VISITA IN ARCHIVIO", use_container_width=True):
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM atleti WHERE cognome=? AND nome=?", (r['cognome'], r['nome']))
                res = cursor.fetchone()
                atleta_id = res[0] if res else None
                if not atleta_id:
                    cursor.execute("INSERT INTO atleti (nome, cognome, altezza, profilo) VALUES (?,?,?,?)", (r['nome'], r['cognome'], r['alt'], r['prof']))
                    atleta_id = cursor.lastrowid
                cursor.execute("""INSERT INTO visite (atleta_id, data, peso, fm, ftp, lthr, peso_t, fm_t, ftp_t, dist_km, grad, bike_w, t_att, t_tar) 
                                  VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                               (atleta_id, r['raw_data'], r['p_a'], r['fm_a'], r['ftp_a'], r['lthr'], r['p_t'], r['fm_t'], r['ftp_t'], r['dist'], r['grad'], r['bike'], r['t_a'], r['t_t']))
                conn.commit()
            st.success("Dati archiviati correttamente!"); st.rerun()

        # PDF GENERATION
        pdf = FPDF()
        pdf.add_page()
        if os.path.exists(LOGO_PATH):
            pdf.image(LOGO_PATH, 10, 8, 33)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(80); pdf.cell(30, 10, 'REPORT VALUTAZIONE ATLETA', 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, f"Atleta: {r['nome']} {r['cognome']} - Data: {r['data']}", 0, 1)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 10, f"Profilo: {r['prof']} | Altezza: {r['alt']} cm", 0, 1)
        pdf.ln(5)
        pdf.set_fill_color(200, 220, 255); pdf.cell(0, 10, "ANALISI BIOMETRICA E TARGET", 1, 1, 'L', True)
        pdf.cell(95, 8, f"Peso Attuale: {r['p_a']} kg", 1); pdf.cell(95, 8, f"Peso Target: {r['p_t']} kg", 1, 1)
        pdf.cell(95, 8, f"FM Attuale: {r['fm_a']}%", 1); pdf.cell(95, 8, f"FM Target: {r['fm_t']}%", 1, 1)
        pdf.cell(95, 8, f"FTP Attuale: {r['ftp_a']} W", 1); pdf.cell(95, 8, f"FTP Target: {r['ftp_t']} W", 1, 1)
        pdf.ln(5)
        pdf.cell(0, 10, "SCENARIO PERFORMANCE", 1, 1, 'L', True)
        pdf.cell(0, 8, pdf_safe(f"Salita di {r['dist']}km al {r['grad']}%"), 1, 1)
        pdf.cell(95, 8, f"Tempo Attuale: {r['t_a']:.2f} min", 1); pdf.cell(95, 8, f"Tempo Target: {r['t_t']:.2f} min", 1, 1)
        pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, f"DIFFERENZA: -{r['t_a']-r['t_t']:.2f} minuti", 1, 1, 'C')
        
        cb.download_button("📄 SCARICA REPORT PDF", data=pdf.output(dest='S').encode('latin-1', 'ignore'), file_name=f"Report_{r['cognome']}.pdf", use_container_width=True)

# ---------------------------------------------------------
# SEZIONE: ARCHIVIO
# ---------------------------------------------------------
elif menu == "📂 Archivio Storico":
    st.header("🗄️ Gestione Archivio Atleti")
    with get_connection() as conn:
        atleti = pd.read_sql_query("SELECT * FROM atleti", conn)

    if not atleti.empty:
        col_sel, col_del = st.columns([3, 1])
        atleta_scelto = col_sel.selectbox("Seleziona Atleta", atleti.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}", axis=1))
        a_id = int(atleta_scelto.split(" - ")[0])
        
        if col_del.button("🗑️ ELIMINA ATLETA"):
            with get_connection() as conn:
                conn.execute(f"DELETE FROM visite WHERE atleta_id={a_id}")
                conn.execute(f"DELETE FROM atleti WHERE id={a_id}")
                conn.commit()
            st.rerun()

        with get_connection() as conn:
            visite = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id} ORDER BY data DESC", conn)

        st.subheader("🗓️ Storico Valutazioni")
        st.dataframe(visite, hide_index=True)

        # --- COMPARAZIONE ---
        st.divider()
        st.subheader("⚖️ Comparazione Visite")
        v_ids = visite['id'].tolist()
        if len(v_ids) >= 2:
            c_a, c_b = st.columns(2)
            v1 = c_a.selectbox("Seleziona Visita Pre", v_ids)
            v2 = c_b.selectbox("Seleziona Visita Post", v_ids)
            
            if st.button("📊 GENERA REPORT COMPARATIVO"):
                d1 = visite[visite['id'] == v1].iloc[0]
                d2 = visite[visite['id'] == v2].iloc[0]
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Peso", f"{d2['peso']} kg", f"{d2['peso']-d1['peso']:.1f} kg", delta_color="inverse")
                m2.metric("FM", f"{d2['fm']}%", f"{d2['fm']-d1['fm']:.1f}%", delta_color="inverse")
                m3.metric("FTP", f"{d2['ftp']} W", f"{d2['ftp']-d1['ftp']:.0f} W")
                
                # PDF Comparativo
                pdf_c = FPDF()
                pdf_c.add_page()
                pdf_c.set_font("Arial", 'B', 16); pdf_c.cell(0, 10, "REPORT COMPARATIVO PERIODICO", 0, 1, 'C')
                pdf_c.ln(10)
                pdf_c.set_font("Arial", '', 11)
                pdf_c.cell(60, 10, "Parametro", 1); pdf_c.cell(60, 10, f"Data {d1['data']}", 1); pdf_c.cell(60, 10, f"Data {d2['data']}", 1, 1)
                pdf_c.cell(60, 10, "Peso (kg)", 1); pdf_c.cell(60, 10, str(d1['peso']), 1); pdf_c.cell(60, 10, str(d2['peso']), 1, 1)
                pdf_c.cell(60, 10, "FM (%)", 1); pdf_c.cell(60, 10, str(d1['fm']), 1); pdf_c.cell(60, 10, str(d2['fm']), 1, 1)
                pdf_c.cell(60, 10, "FTP (W)", 1); pdf_c.cell(60, 10, str(d1['ftp']), 1); pdf_c.cell(60, 10, str(d2['ftp']), 1, 1)
                
                st.download_button("📄 SCARICA COMPARAZIONE PDF", data=pdf_c.output(dest='S').encode('latin-1', 'ignore'), file_name="Comparazione.pdf")
        
        # --- ELIMINA SINGOLA VISITA ---
        with st.expander("⚙️ Gestione Singola Visita"):
            v_to_del = st.selectbox("ID Visita da eliminare", v_ids)
            if st.button("❌ CANCELLA VALUTAZIONE"):
                with get_connection() as conn:
                    conn.execute(f"DELETE FROM visite WHERE id={v_to_del}")
                    conn.commit()
                st.rerun()
    else:
        st.info("Nessun atleta in archivio.")
