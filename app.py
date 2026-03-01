import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from fpdf import FPDF
import os

# ---------------------------------------------------------
# SETUP E DATABASE
# ---------------------------------------------------------
st.set_page_config(page_title="DB Nutrition & Performance", layout="wide", page_icon="🧬")
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
# LOGICA SCIENTIFICA
# ---------------------------------------------------------
class NutritionScience:
    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
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
    st.header("📋 Nuova Valutazione Biometrica")
    with get_connection() as conn:
        db_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    with st.expander("👤 Anagrafica Atleta", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        cog_sel = c1.selectbox("Seleziona Cognome", [""] + sorted(db_atleti['cognome'].unique().tolist()))
        cog_man = c1.text_input("...o Nuovo Cognome")
        final_cog = cog_man if cog_man else cog_sel
        
        atleta_ex = db_atleti[db_atleti['cognome'] == final_cog].iloc[0] if final_cog in db_atleti['cognome'].values else None
        nome = c2.text_input("Nome", value=atleta_ex['nome'] if atleta_ex is not None else "")
        data_v = c3.date_input("Data Visita", date.today())
        altezza = c4.number_input("Altezza (cm)", 120, 230, int(atleta_ex['altezza']) if atleta_ex is not None else 175)
        profilo = c5.selectbox("Profilo", ["Scalatore (Lightweight)", "Passista (Powerhouse)", "Triatleta", "Granfondista"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🧱 Stato Attuale")
        peso = st.number_input("Peso (kg)", 40.0, 150.0, 70.0)
        fm = st.number_input("Massa Grassa (%)", 3.0, 40.0, 15.0)
        ftp = st.number_input("FTP (W)", 50, 600, 250)
        lthr = st.number_input("LTHR (bpm)", 80, 220, 165)
    with col2:
        st.subheader("🎯 Target")
        peso_t = st.number_input("Peso Target", 40.0, 150.0, 68.0)
        fm_t = st.number_input("FM Target %", 3.0, 40.0, 10.0)
        ftp_t = st.number_input("FTP Target (W)", 50, 600, 270)
    with col3:
        st.subheader("🏔️ Scenario Salita")
        dist_km = st.number_input("Distanza (km)", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza (%)", 0.0, 20.0, 7.0)
        bike_w = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.0)

    if st.button("🚀 GENERA ANALISI E PDF"):
        t_a = NutritionScience.estimate_time(ftp, peso, dist_km, grad, bike_w)
        t_t = NutritionScience.estimate_time(ftp_t, peso_t, dist_km, grad, bike_w)
        wkg_a, wkg_t = ftp/peso, ftp_t/peso_t
        
        st.session_state['res'] = {
            'n': nome, 'c': final_cog, 'data': data_v.strftime("%Y-%m-%d"), 'alt': altezza, 'prof': profilo,
            'p': peso, 'fm': fm, 'ftp': ftp, 'lthr': lthr, 'p_t': peso_t, 'fm_t': fm_t, 'ftp_t': ftp_t,
            't_a': t_a, 't_t': t_t, 'd': dist_km, 'g': grad, 'b': bike_w, 'wkg_a': wkg_a, 'wkg_t': wkg_t
        }

    if 'res' in st.session_state:
        r = st.session_state['res']
        st.divider()
        st.metric("Miglioramento Stimato", f"{r['t_t']:.2f} min", f"-{r['t_a']-r['t_t']:.2f} min rispetto ad oggi")
        
        c_save, c_pdf = st.columns(2)
        with c_save:
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
                st.success("Dati archiviati con successo!")

        with c_pdf:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16); pdf.cell(190, 10, pdf_safe(f"REPORT: {r['n']} {r['c']}"), 0, 1, 'C')
            pdf.set_font("Arial", '', 11); pdf.cell(190, 7, f"Data: {r['data']} | Altezza: {r['alt']}cm", 0, 1, 'C'); pdf.ln(10)
            
            pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "PREVISIONE PERFORMANCE IN SALITA", 1, 1, 'L', True)
            pdf.set_font("Arial", '', 11)
            pdf.cell(190, 8, pdf_safe(f"Scenario: Lunghezza {r['d']} km | Pendenza media {r['g']}% | Peso Bici {r['b']} kg"), 1, 1)
            pdf.cell(95, 8, f"Tempo Attuale: {r['t_a']:.2f} min", 1, 0); pdf.cell(95, 8, f"Tempo Target: {r['t_t']:.2f} min", 1, 1)
            pdf.cell(190, 10, pdf_safe(f"MIGLIORAMENTO: -{r['t_a']-r['t_t']:.2f} minuti"), 1, 1, 'C')
            
            st.download_button("📄 SCARICA PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Report_{r['c']}.pdf")

# ---------------------------------------------------------
# SEZIONE: ARCHIVIO (CON MODIFICA E CONFRONTO DINAMICO)
# ---------------------------------------------------------
elif menu == "Archivio Atleti":
    st.header("📂 Archivio Storico Atleti")
    with get_connection() as conn:
        at = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    if not at.empty:
        sel_atleta = st.selectbox("Seleziona un atleta per visualizzare i dettagli", at.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}", axis=1))
        a_id = sel_atleta.split(" - ")[0]
        curr_atleta = at[at['id'] == int(a_id)].iloc[0]

        # 1. TAB: MODIFICA ANAGRAFICA
        with st.expander("📝 MODIFICA ANAGRAFICA ATLETA"):
            c1, c2, c3, c4 = st.columns(4)
            unome = c1.text_input("Nome", curr_atleta['nome'])
            ucog = c2.text_input("Cognome", curr_atleta['cognome'])
            ualt = c3.number_input("Altezza (cm)", 120, 230, int(curr_atleta['altezza']))
            uprof = c4.selectbox("Profilo", ["Scalatore (Lightweight)", "Passista (Powerhouse)", "Triatleta", "Granfondista"], index=0)
            if st.button("💾 Salva Modifiche Anagrafica"):
                with get_connection() as conn:
                    conn.execute("UPDATE atleti SET nome=?, cognome=?, altezza=?, profilo=? WHERE id=?", (unome, ucog, ualt, uprof, a_id))
                    conn.commit()
                st.success("Anagrafica aggiornata!")
                st.rerun()

        st.divider()

        # 2. SELEZIONE VISITE PER CONFRONTO
        with get_connection() as conn:
            visite = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id} ORDER BY data DESC", conn)
        
        if not visite.empty:
            st.subheader("⚖️ Confronto Dinamico Visite")
            st.write("Seleziona due o più visite per confrontare l'evoluzione dei dati:")
            
            # Creiamo una lista di etichette leggibili per il multiselect
            visite['label'] = visite.apply(lambda x: f"Data: {x['data']} | Peso: {x['peso']}kg | FTP: {x['ftp']}W", axis=1)
            scelte = st.multiselect("Scegli le visite da comparare", visite['label'].tolist(), default=visite['label'].tolist()[:min(2, len(visite))])
            
            if len(scelte) >= 2:
                df_comp = visite[visite['label'].isin(scelte)].sort_values(by='data')
                
                # Visualizzazione delta tra la più vecchia e la più recente tra quelle selezionate
                v_old = df_comp.iloc[0]
                v_new = df_comp.iloc[-1]
                
                st.info(f"Confronto tra la visita del **{v_old['data']}** e quella del **{v_new['data']}**")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Peso", f"{v_new['peso']} kg", f"{v_new['peso']-v_old['peso']:.1f} kg", delta_color="inverse")
                m2.metric("FM%", f"{v_new['fm']}%", f"{v_new['fm']-v_old['fm']:.1f}%", delta_color="inverse")
                m3.metric("FTP", f"{v_new['ftp']} W", f"{v_new['ftp']-v_old['ftp']:.0f} W")
                m4.metric("W/kg", f"{v_new['ftp']/v_new['peso']:.2f}", f"{(v_new['ftp']/v_new['peso'])-(v_old['ftp']/v_old['peso']):.2f}")

                # Tabella dettagliata del confronto
                st.dataframe(df_comp.drop(columns=['label', 'atleta_id', 'id']), use_container_width=True)
            else:
                st.warning("Seleziona almeno 2 visite per attivare il confronto metrico.")
                st.dataframe(visite.drop(columns=['label', 'atleta_id', 'id']), use_container_width=True)
        else:
            st.info("Nessuna visita registrata per questo atleta.")
    else:
        st.info("Il database atleti è vuoto.")
