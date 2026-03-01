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
    def get_eval(profilo, peso, altezza, fm):
        bmi = peso / ((altezza/100)**2)
        ffm = peso * (1 - fm/100)
        ffmi = ffm / ((altezza/100)**2)
        eval_text = f"Analisi Biometrica:\n- BMI: {bmi:.1f} kg/m2\n- Massa Magra (FFM): {ffm:.1f} kg\n- Indice FFMI: {ffmi:.1f} kg/m2\n\n"
        eval_text += f"Valutazione Clinica: L'atleta rientra nel profilo '{profilo}'. "
        if fm > 15 and profilo == "Scalatore":
            eval_text += "Si rileva un margine di miglioramento tramite ricomposizione corporea."
        else:
            eval_text += "Composizione corporea in linea con i target prestativi."
        return eval_text

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        f_res = (float(peso) + float(bike_w)) * 9.81 * ((float(pend)/100) + 0.005)
        if f_res <= 0 or watt <= 0: return 0
        speed_ms = float(watt) / f_res
        return (float(km) * 1000 / speed_ms) / 60

def pdf_safe(text):
    if not text: return ""
    rep = {"à": "a", "è": "e", "é": "e", "ì": "i", "ò": "o", "ù": "u", "²": "2", "₂": "2", "VO₂": "VO2", "VO2": "VO2"}
    for k, v in rep.items(): text = text.replace(k, v)
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# ---------------------------------------------------------
# 3. INTERFACCIA (LOGO NELLA SIDEBAR)
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    st.markdown("---")
    menu = st.radio("NAVIGAZIONE", ["➕ Nuova Valutazione", "📂 Archivio Professionale"])

if menu == "➕ Nuova Valutazione":
    st.header("📋 Protocollo di Valutazione Biometrica")
    
    with get_connection() as conn:
        db_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        exist_cog = c1.selectbox("Atleta Esistente", [""] + sorted(db_atleti['cognome'].unique().tolist()))
        new_cog = c1.text_input("...o Nuovo Cognome")
        cog = new_cog if new_cog else exist_cog
        atleta_data = db_atleti[db_atleti['cognome'] == cog].iloc[0] if cog in db_atleti['cognome'].values else None
        nome = c2.text_input("Nome", value=atleta_data['nome'] if atleta_data is not None else "")
        altezza = c3.number_input("Altezza (cm)", 120, 230, int(atleta_data['altezza']) if atleta_data is not None else 175)
        profilo = c4.selectbox("Profilo Atleta", ["Scalatore", "Passista", "Triatleta", "Granfondista"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Stato Attuale")
        p_att = st.number_input("Peso (kg)", 40.0, 150.0, 70.0)
        fm_att = st.number_input("FM %", 3.0, 40.0, 15.0)
        ftp_att = st.number_input("FTP (W)", 50, 600, 250)
        lthr = st.number_input("LTHR (bpm)", 80, 220, 165)
    with col2:
        st.subheader("Target")
        p_tar = st.number_input("Peso Target (kg)", 40.0, 150.0, 68.0)
        fm_tar = st.number_input("FM Target %", 3.0, 40.0, 10.0)
        ftp_tar = st.number_input("FTP Target (W)", 50, 600, 275)
    with col3:
        st.subheader("Scenario Salita")
        dist = st.number_input("Km Salita", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza %", 0.0, 20.0, 7.0)
        bike = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.0)

    if st.button("🚀 ELABORA ANALISI", use_container_width=True):
        t_a = BioPerformance.estimate_time(ftp_att, p_att, dist, grad, bike)
        t_t = BioPerformance.estimate_time(ftp_tar, p_tar, dist, grad, bike)
        giudizio = BioPerformance.get_eval(profilo, p_att, altezza, fm_att)
        zp = [("Z1 Recupero", 0, int(ftp_tar*0.55)), ("Z2 Endurance", int(ftp_tar*0.56), int(ftp_tar*0.75)), 
              ("Z3 Tempo", int(ftp_tar*0.76), int(ftp_tar*0.90)), ("Z4 Soglia", int(ftp_tar*0.91), int(ftp_tar*1.05)), 
              ("Z5 VO2max", int(ftp_tar*1.06), 600)]
        
        st.session_state['report'] = {
            'nome': nome, 'cognome': cog, 'alt': altezza, 'prof': profilo,
            'p_a': p_att, 'fm_a': fm_att, 'ftp_a': ftp_att, 'lthr': lthr,
            'p_t': p_tar, 'fm_t': fm_tar, 'ftp_t': ftp_tar,
            'dist': dist, 'grad': grad, 'bike': bike,
            't_a': t_a, 't_t': t_t, 'giudizio': giudizio, 'zp': zp, 'data': date.today().strftime("%d/%m/%Y"), 'raw_data': date.today().isoformat()
        }

    if 'report' in st.session_state:
        r = st.session_state['report']
        st.divider()
        c_res1, c_res2 = st.columns([2, 1])
        with c_res1:
            st.success("### Risultato Valutazione")
            st.write(r['giudizio'])
            st.table(pd.DataFrame(r['zp'], columns=["Zona Potenza", "Min (W)", "Max (W)"]))
        with c_res2:
            st.metric("Tempo Target", f"{r['t_t']:.2f} min", f"-{r['t_a']-r['t_t']:.2f} min")
            st.metric("W/kg Target", f"{r['ftp_t']/r['p_t']:.2f}")

        c_save, c_pdf = st.columns(2)
        with c_save:
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
                                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (a_id, r['raw_data'], r['p_a'], r['fm_a'], r['ftp_a'], r['lthr'], r['p_t'], r['fm_t'], r['ftp_t'], r['dist'], r['grad'], r['bike'], r['t_a'], r['t_t']))
                    conn.commit()
                st.success("Salvato!"); st.rerun()

        with c_pdf:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_fill_color(0, 51, 102); pdf.rect(0, 0, 210, 45, 'F')
            if os.path.exists(LOGO_PATH): pdf.image(LOGO_PATH, 10, 8, 38)
            pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 22); pdf.cell(190, 18, "PERFORMANCE LAB PRO", 0, 1, 'R')
            pdf.set_font("Arial", 'I', 10); pdf.cell(190, 5, pdf_safe(f"Report Nutrizionale e Prestativo - {r['data']}"), 0, 1, 'R')
            pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", 'B', 12); pdf.set_fill_color(240, 240, 240)
            pdf.cell(190, 10, pdf_safe(f"ATLETA: {r['nome'].upper()} {r['cognome'].upper()}"), 1, 1, 'L', True)
            pdf.set_font("Arial", '', 11); pdf.multi_cell(190, 8, pdf_safe(r['giudizio']), 1)
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "PERFORMANCE IN SCENARIO", 1, 1, 'L', True)
            pdf.set_font("Arial", 'B', 10); pdf.cell(190, 8, pdf_safe(f"SCENARIO: {r['dist']} km | Pendenza media: {r['grad']}% | Bici: {r['bike']} kg"), 1, 1, 'C')
            pdf.set_font("Arial", '', 11); pdf.cell(63, 8, "Parametro", 1, 0, 'C'); pdf.cell(63, 8, "Attuale", 1, 0, 'C'); pdf.cell(64, 8, "Target", 1, 1, 'C')
            pdf.cell(63, 8, "Peso Corporeo", 1, 0); pdf.cell(63, 8, f"{r['p_a']} kg", 1, 0, 'C'); pdf.cell(64, 8, f"{r['p_t']} kg", 1, 1, 'C')
            pdf.cell(63, 8, "Tempo Scalata", 1, 0); pdf.cell(63, 8, f"{r['t_a']:.2f} min", 1, 0, 'C'); pdf.cell(64, 8, f"{r['t_t']:.2f} min", 1, 1, 'C')
            pdf.set_font("Arial", 'B', 12); pdf.set_text_color(200, 0, 0); pdf.cell(190, 12, pdf_safe(f"MIGLIORAMENTO SCALATA: -{r['t_a']-r['t_t']:.2f} MINUTI"), 1, 1, 'C')
            pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "ZONE DI ALLENAMENTO TARGET", 1, 1, 'L', True)
            for z, mi, ma in r['zp']: pdf.cell(190, 7, f"{z}: {mi} - {ma} Watt", 1, 1)
            st.download_button("📄 SCARICA PDF", data=pdf.output(dest='S').encode('latin-1', 'ignore'), file_name=f"Report_{r['cognome']}.pdf", use_container_width=True)

elif menu == "📂 Archivio Professionale":
    st.header("🗄️ Database Atleti e Storico")
    with get_connection() as conn:
        at = pd.read_sql_query("SELECT * FROM atleti", conn)
    if not at.empty:
        sel_atleta = st.selectbox("Seleziona Atleta", at.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}", axis=1))
        a_id = int(sel_atleta.split(" - ")[0])
        curr = at[at['id'] == a_id].iloc[0]
        with st.expander("⚙️ Modifica o Elimina Atleta"):
            c1, c2, c3, c4 = st.columns(4)
            un, uc = c1.text_input("Nome", curr['nome']), c2.text_input("Cognome", curr['cognome'])
            ua = c3.number_input("Altezza", 120, 230, int(curr['altezza']))
            up = c4.selectbox("Profilo", ["Scalatore", "Passista", "Triatleta", "Granfondista"], index=0)
            if st.button("✅ SALVA MODIFICHE"):
                with get_connection() as conn:
                    conn.execute("UPDATE atleti SET nome=?, cognome=?, altezza=?, profilo=? WHERE id=?", (un, uc, ua, up, a_id))
                    conn.commit()
                st.success("Aggiornato!"); st.rerun()
        with get_connection() as conn:
            vi = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id} ORDER BY data DESC", conn)
        if not vi.empty:
            st.dataframe(vi.drop(columns=['atleta_id']), hide_index=True)
            if st.button("🗑️ ELIMINA ULTIMA VISITA"):
                with get_connection() as conn:
                    conn.execute(f"DELETE FROM visite WHERE id=(SELECT max(id) FROM visite WHERE atleta_id={a_id})")
                    conn.commit()
                st.rerun()
    else:
        st.warning("Archivio vuoto.")
