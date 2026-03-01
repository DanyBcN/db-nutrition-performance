import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from fpdf import FPDF
import os

# ---------------------------------------------------------
# SETUP E DATABASE (VERSIONE ROBUSTA)
# ---------------------------------------------------------
st.set_page_config(page_title="Performance Lab Pro", layout="wide", page_icon="🧬")
LOGO_PATH = "Logo NUTRITION AND PERFORMANCE.png"

def get_connection():
    return sqlite3.connect("performance_lab.db")

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS atleti 
                     (id INTEGER PRIMARY KEY, nome TEXT, cognome TEXT, altezza REAL, sesso TEXT, profilo TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS visite 
                     (id INTEGER PRIMARY KEY, atleta_id INTEGER, data TEXT, peso REAL, fm REAL, ftp REAL, 
                      lthr INTEGER, peso_t REAL, fm_t REAL, ftp_t REAL, t_att REAL, t_tar REAL,
                      dist_km REAL, grad REAL, bike_w REAL)''')
        conn.commit()

init_db()

# ---------------------------------------------------------
# LOGICA CLINICA
# ---------------------------------------------------------
class NutritionScience:
    @staticmethod
    def get_clinical_judgment(profilo, peso, altezza, fm, fm_t):
        bmi = peso / ((altezza/100)**2)
        ffm = peso * (1 - fm/100)
        ffmi = ffm / ((altezza/100)**2)
        
        # Uso di Unicode per pedici e apici come richiesto
        msg = f"--- ANALISI CLINICA ---\n"
        msg += f"BMI: {bmi:.1f} kg/m² | FM: {fm}% | FFMI: {ffmi:.1f}\n"
        msg += f"Massa Magra (FFM): {ffm:.1f} kg\n\n"
        msg += f"Specializzazione: {profilo}\n"
        
        if fm > 15:
            msg += "Priorità: Ottimizzazione della composizione corporea (ricomposizione) per incrementare il rapporto W/kg."
        else:
            msg += "Composizione ottimale. Focus su efficienza metabolica e gestione dei carboidrati intra-workout."
        return msg

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        # Formula fisica potenza/gravità
        f_res = (peso + bike_w) * 9.81 * ((pend/100) + 0.005)
        return (km / ((watt / f_res) * 3.6)) * 60 if f_res > 0 and watt > 0 else 0

def pdf_safe(t): return str(t).encode('latin-1', 'replace').decode('latin-1')

# ---------------------------------------------------------
# UI SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, use_container_width=True)
    menu = st.radio("Menu", ["Nuova Analisi", "Archivio Atleti"])

# ---------------------------------------------------------
# SEZIONE: NUOVA ANALISI
# ---------------------------------------------------------
if menu == "Nuova Analisi":
    st.header("📋 Valutazione Atleta")
    with get_connection() as conn:
        db_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    with st.expander("👤 Anagrafica", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        cog_sel = c1.selectbox("Seleziona da Archivio", [""] + sorted(db_atleti['cognome'].unique().tolist()))
        cog_man = c1.text_input("...o Nuovo Cognome")
        final_cog = cog_man if cog_man else cog_sel
        
        atleta_ex = db_atleti[db_atleti['cognome'] == final_cog].iloc[0] if final_cog in db_atleti['cognome'].values else None
        
        nome = c2.text_input("Nome", value=atleta_ex['nome'] if atleta_ex is not None else "")
        data_v = c3.date_input("Data Visita", date.today())
        altezza = c4.number_input("Altezza (cm)", 120, 230, int(atleta_ex['altezza']) if atleta_ex is not None else 175)
        profilo_idx = ["Scalatore", "Passista", "Triatleta", "Granfondista"].index(atleta_ex['profilo']) if (atleta_ex is not None and atleta_ex['profilo'] in ["Scalatore", "Passista", "Triatleta", "Granfondista"]) else 0
        profilo = c5.selectbox("Profilo", ["Scalatore", "Passista", "Triatleta", "Granfondista"], index=profilo_idx)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🧱 Stato Attuale")
        peso = st.number_input("Peso (kg)", 40.0, 150.0, 70.0)
        fm = st.number_input("Massa Grassa %", 3.0, 40.0, 15.0)
        ftp = st.number_input("FTP (W)", 50, 600, 250)
        lthr = st.number_input("LTHR (bpm)", 80, 220, 165)
    with col2:
        st.subheader("🎯 Target")
        peso_t = st.number_input("Peso Target", 40.0, 150.0, 68.0)
        fm_t = st.number_input("FM Target %", 3.0, 40.0, 10.0)
        ftp_t = st.number_input("FTP Target", 50, 600, 270)
    with col3:
        st.subheader("🏔️ Scenario Salita")
        dist_km = st.number_input("Km Salita", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza %", 0.0, 20.0, 7.0)
        bike_w = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.0)

    if st.button("🚀 GENERA ANALISI"):
        if not final_cog or not nome:
            st.error("Inserire Nome e Cognome per procedere.")
        else:
            # Calcolo risultati
            t_a = NutritionScience.estimate_time(ftp, peso, dist_km, grad, bike_w)
            t_t = NutritionScience.estimate_time(ftp_t, peso_t, dist_km, grad, bike_w)
            giudizio_clinico = NutritionScience.get_clinical_judgment(profilo, peso, altezza, fm, fm_t)
            
            # Salvataggio in sessione di TUTTE le chiavi necessarie
            st.session_state['res'] = {
                'n': nome, 'c': final_cog, 'data': data_v.strftime("%Y-%m-%d"), 'alt': altezza, 'prof': profilo,
                'p': peso, 'fm': fm, 'ftp': ftp, 'lthr': lthr, 'p_t': peso_t, 'fm_t': fm_t, 'ftp_t': ftp_t,
                't_a': t_a, 't_t': t_t, 'd': dist_km, 'g': grad, 'b': bike_w, 
                'giudizio': giudizio_clinico
            }

    # Visualizzazione Risultati (Solo se 'res' esiste)
    if 'res' in st.session_state:
        r = st.session_state['res']
        st.divider()
        
        c_out1, c_out2 = st.columns([2, 1])
        with c_out1:
            st.info(f"### Valutazione Clinica\n{r.get('giudizio', 'Dati non disponibili')}")
        with c_out2:
            st.metric("Tempo Scalata Target", f"{r['t_t']:.2f} min", f"-{r['t_a']-r['t_t']:.2f} min")
        
        # Zone di Potenza
        zp = [("Z1 Recupero", 0, int(r['ftp_t']*0.55)), ("Z2 Endurance", int(r['ftp_t']*0.56), int(r['ftp_t']*0.75)), ("Z3 Tempo", int(r['ftp_t']*0.76), int(r['ftp_t']*0.90)), ("Z4 Soglia", int(r['ftp_t']*0.91), int(r['ftp_t']*1.05)), ("Z5 VO2max", int(r['ftp_t']*1.06), 600)]
        st.write("### ⚡ Zone Potenza Target (W)")
        st.table(pd.DataFrame(zp, columns=["Zona", "Min", "Max"]))

        # Bottoni Finali
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("💾 SALVA IN ARCHIVIO"):
                with get_connection() as conn:
                    c = conn.cursor()
                    c.execute("SELECT id FROM atleti WHERE cognome=? AND nome=?", (r['c'], r['n']))
                    row = c.fetchone()
                    a_id = row[0] if row else None
                    if not row:
                        c.execute("INSERT INTO atleti (nome, cognome, profilo, altezza) VALUES (?,?,?,?)", (r['n'], r['c'], r['prof'], r['alt']))
                        a_id = c.lastrowid
                    c.execute("INSERT INTO visite (atleta_id, data, peso, fm, ftp, lthr, peso_t, fm_t, ftp_t, t_att, t_tar, dist_km, grad, bike_w) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (a_id, r['data'], r['p'], r['fm'], r['ftp'], r['lthr'], r['p_t'], r['fm_t'], r['ftp_t'], r['t_a'], r['t_t'], r['d'], r['g'], r['b']))
                    conn.commit()
                st.success("Dati salvati correttamente!")

        with c_btn2:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16); pdf.cell(190, 10, pdf_safe(f"REPORT: {r['n']} {r['c']}"), 0, 1, 'C')
            pdf.set_font("Arial", '', 10); pdf.cell(190, 7, f"Data: {r['data']} | Altezza: {r['alt']}cm", 0, 1, 'C'); pdf.ln(10)
            
            pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "VALUTAZIONE BIOMETRICA", 1, 1, 'L', True)
            pdf.set_font("Arial", '', 11); pdf.multi_cell(190, 8, pdf_safe(r.get('giudizio', '')), 1); pdf.ln(5)
            
            pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "DETTAGLIO PERFORMANCE IN SALITA", 1, 1, 'L', True)
            pdf.set_font("Arial", '', 11)
            pdf.cell(190, 8, pdf_safe(f"Scenario: Lunghezza {r['d']} km | Pendenza {r['g']}% | Peso Bici {r['b']} kg"), 1, 1)
            pdf.cell(95, 8, f"Tempo Attuale: {r['t_a']:.2f} min", 1, 0); pdf.cell(95, 8, f"Tempo Target: {r['t_t']:.2f} min", 1, 1)
            pdf.set_font("Arial", 'B', 11); pdf.cell(190, 10, pdf_safe(f"MIGLIORAMENTO: - {r['t_a']-r['t_t']:.2f} min"), 1, 1, 'C'); pdf.ln(5)
            
            pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "ZONE DI POTENZA (TARGET)", 1, 1, 'L', True)
            for z, mi, ma in zp: pdf.cell(190, 7, f"{z}: {mi} - {ma} Watt", 1, 1)
            
            st.download_button("📄 SCARICA REPORT COMPLETO", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Report_{r['c']}.pdf")

# ---------------------------------------------------------
# SEZIONE: ARCHIVIO
# ---------------------------------------------------------
elif menu == "Archivio Atleti":
    st.header("📂 Archivio Storico")
    with get_connection() as conn: at = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    if not at.empty:
        sel = st.selectbox("Atleta", at.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}", axis=1))
        a_id = sel.split(" - ")[0]
        curr = at[at['id'] == int(a_id)].iloc[0]

        with st.expander("📝 Modifica Anagrafica"):
            un, uc, ua = st.text_input("Nome", curr['nome']), st.text_input("Cognome", curr['cognome']), st.number_input("Altezza", 120, 230, int(curr['altezza']))
            up = st.selectbox("Profilo", ["Scalatore", "Passista", "Triatleta", "Granfondista"])
            if st.button("Salva Modifiche"):
                with get_connection() as conn:
                    conn.execute("UPDATE atleti SET nome=?, cognome=?, altezza=?, profilo=? WHERE id=?", (un, uc, ua, up, a_id))
                    conn.commit()
                st.rerun()

        with get_connection() as conn: vi = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id} ORDER BY data DESC", conn)
        
        if not vi.empty:
            vi['label'] = vi.apply(lambda x: f"{x['data']} | Peso: {x['peso']}kg", axis=1)
            scelte = st.multiselect("Confronta visite", vi['label'].tolist(), default=vi['label'].tolist()[:min(2, len(vi))])
            
            if len(scelte) >= 2:
                df_c = vi[vi['label'].isin(scelte)].sort_values(by='data')
                v1, v2 = df_c.iloc[0], df_c.iloc[-1]
                st.subheader(f"Evoluzione: {v1['data']} ➔ {v2['data']}")
                m1, m2, m3 = st.columns(3)
                m1.metric("Peso", f"{v2['peso']} kg", f"{v2['peso']-v1['peso']:.1f} kg", delta_color="inverse")
                m2.metric("FM %", f"{v2['fm']}%", f"{v2['fm']-v1['fm']:.1f}%", delta_color="inverse")
                m3.metric("FTP", f"{v2['ftp']} W", f"{v2['ftp']-v1['ftp']:.0f} W")
                st.dataframe(df_c.drop(columns=['label', 'atleta_id', 'id']), use_container_width=True)
            else:
                st.dataframe(vi.drop(columns=['label', 'atleta_id', 'id']), use_container_width=True)
