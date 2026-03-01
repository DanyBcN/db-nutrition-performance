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
# 2. MOTORE SCIENTIFICO E GESTIONE PDF
# ---------------------------------------------------------
class BioPerformance:
    @staticmethod
    def get_eval(profilo, peso, altezza, fm):
        bmi = peso / ((altezza/100)**2)
        ffm = peso * (1 - fm/100)
        ffmi = ffm / ((altezza/100)**2)
        
        # Uso di Unicode per la visualizzazione a schermo
        eval_text = f"Analisi Biometrica:\n- BMI: {bmi:.1f} kg/m²\n- Massa Magra (FFM): {ffm:.1f} kg\n- Indice FFMI: {ffmi:.1f} kg/m²\n\n"
        eval_text += f"Valutazione Clinica: L'atleta rientra nel profilo '{profilo}'. "
        if fm > 15 and profilo == "Scalatore":
            eval_text += "Si rileva un margine di miglioramento tramite ricomposizione corporea."
        else:
            eval_text += "Composizione corporea in linea con i target prestativi."
        return eval_text

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        f_res = (peso + bike_w) * 9.81 * ((pend/100) + 0.005)
        if f_res <= 0 or watt <= 0: return 0
        speed_ms = watt / f_res
        time_min = (km * 1000 / speed_ms) / 60
        return time_min

def pdf_safe(text):
    """Sostituisce i caratteri Unicode problematici per il PDF con equivalenti standard."""
    if not text: return ""
    replacements = {
        "²": "2", "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
        "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"
    }
    for key, val in replacements.items():
        text = text.replace(key, val)
    return str(text).encode('latin-1', 'ignore').decode('latin-1')

# ---------------------------------------------------------
# 3. INTERFACCIA PRINCIPALE
# ---------------------------------------------------------
menu = st.sidebar.radio("NAVIGAZIONE", ["➕ Nuova Valutazione", "📂 Archivio Professionale"])

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
        st.markdown("**STATO ATTUALE**")
        p_att = st.number_input("Peso (kg)", 40.0, 150.0, 70.0, key="pa")
        fm_att = st.number_input("FM %", 3.0, 40.0, 15.0, key="fma")
        ftp_att = st.number_input("FTP (W)", 50, 600, 250, key="ftpa")
        lthr = st.number_input("LTHR (bpm)", 80, 220, 165)
    with col2:
        st.markdown("**TARGET PRESTATIVO**")
        p_tar = st.number_input("Peso Target (kg)", 40.0, 150.0, 68.0, key="pt")
        fm_tar = st.number_input("FM Target %", 3.0, 40.0, 10.0, key="fmt")
        ftp_tar = st.number_input("FTP Target (W)", 50, 600, 275, key="ftpt")
    with col3:
        st.markdown("**SCENARIO SALITA**")
        dist = st.number_input("Km Salita", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza %", 0.0, 20.0, 7.0)
        bike = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.0)

    if st.button("🚀 ELABORA ANALISI", use_container_width=True):
        if not cog or not nome:
            st.error("Inserire dati anagrafici.")
        else:
            t_a = BioPerformance.estimate_time(ftp_att, p_att, dist, grad, bike)
            t_t = BioPerformance.estimate_time(ftp_tar, p_tar, dist, grad, bike)
            giudizio = BioPerformance.get_eval(profilo, p_att, altezza, fm_att)
            
            st.session_state['report'] = {
                'nome': nome, 'cognome': cog, 'alt': altezza, 'prof': profilo,
                'p_a': p_att, 'fm_a': fm_att, 'ftp_a': ftp_att, 'lthr': lthr,
                'p_t': p_tar, 'fm_t': fm_tar, 'ftp_t': ftp_tar,
                'dist': dist, 'grad': grad, 'bike': bike,
                't_a': t_a, 't_t': t_t, 'giudizio': giudizio, 'data': date.today().isoformat()
            }

    if 'report' in st.session_state:
        r = st.session_state['report']
        st.divider()
        c_res1, c_res2 = st.columns([2, 1])
        with c_res1:
            st.success("### Risultato Valutazione")
            st.write(r['giudizio'])
            zp = [("Z1 Recupero", 0, int(r['ftp_t']*0.55)), ("Z2 Endurance", int(r['ftp_t']*0.56), int(r['ftp_t']*0.75)), 
                  ("Z3 Tempo", int(r['ftp_t']*0.76), int(r['ftp_t']*0.90)), ("Z4 Soglia", int(r['ftp_t']*0.91), int(r['ftp_t']*1.05)), 
                  ("Z5 VO₂max", int(r['ftp_t']*1.06), 600)]
            st.table(pd.DataFrame(zp, columns=["Zona Potenza", "Min (W)", "Max (W)"]))
        with c_res2:
            st.metric("Tempo Target", f"{r['t_t']:.2f} min", f"-{r['t_a']-r['t_t']:.2f} min")
            st.metric("Rapporto W/kg Target", f"{r['ftp_t']/r['p_t']:.2f}")

        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
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
                                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                                   (a_id, r['data'], r['p_a'], r['fm_a'], r['ftp_a'], r['lthr'], r['p_t'], r['fm_t'], r['ftp_t'], r['dist'], r['grad'], r['bike'], r['t_a'], r['t_t']))
                    conn.commit()
                st.balloons()

        with c_btn2:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16); pdf.cell(190, 10, pdf_safe(f"REPORT: {r['nome']} {r['cognome']}"), 0, 1, 'C')
            pdf.set_font("Arial", '', 10); pdf.cell(190, 7, pdf_safe(f"Data: {r['data']} | Profilo: {r['prof']}"), 0, 1, 'C'); pdf.ln(10)
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "VALUTAZIONE BIOMETRICA", 1, 1, 'L', True)
            pdf.set_font("Arial", '', 11); pdf.multi_cell(190, 8, pdf_safe(r['giudizio']), 1); pdf.ln(5)
            pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "PERFORMANCE IN SCENARIO", 1, 1, 'L', True)
            pdf.set_font("Arial", '', 11); pdf.cell(190, 8, pdf_safe(f"Scenario: {r['dist']}km al {r['grad']}% (Bici: {r['bike']}kg)"), 1, 1)
            pdf.cell(95, 8, f"Tempo Attuale: {r['t_a']:.2f} min", 1, 0); pdf.cell(95, 8, f"Tempo Target: {r['t_t']:.2f} min", 1, 1); pdf.ln(5)
            pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "ZONE DI ALLENAMENTO TARGET", 1, 1, 'L', True)
            for z, mi, ma in zp: pdf.cell(190, 7, pdf_safe(f"{z}: {mi} - {ma} Watt"), 1, 1)
            
            # Generazione sicura del PDF
            try:
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button("📄 SCARICA REPORT PDF", data=pdf_bytes, file_name=f"Report_{r['cognome']}.pdf")
            except Exception as e:
                st.error(f"Errore generazione PDF: {e}")

# --- SEZIONE: ARCHIVIO PROFESSIONALE ---
elif menu == "📂 Archivio Professionale":
    st.header("🗄️ Database Atleti e Storico Visite")
    with get_connection() as conn:
        at = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    if not at.empty:
        sel_atleta = st.selectbox("Seleziona Atleta", at.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}", axis=1))
        a_id = int(sel_atleta.split(" - ")[0])
        curr = at[at['id'] == a_id].iloc[0]

        with st.expander("⚙️ Modifica o Elimina Atleta"):
            c1, c2, c3, c4 = st.columns(4)
            un = c1.text_input("Nome", curr['nome'])
            uc = c2.text_input("Cognome", curr['cognome'])
            ua = c3.number_input("Altezza", 120, 230, int(curr['altezza']))
            up = c4.selectbox("Profilo", ["Scalatore", "Passista", "Triatleta", "Granfondista"], index=["Scalatore", "Passista", "Triatleta", "Granfondista"].index(curr['profilo']) if curr['profilo'] else 0)
            
            cb1, cb2 = st.columns(2)
            if cb1.button("✅ SALVA MODIFICHE"):
                with get_connection() as conn:
                    conn.execute("UPDATE atleti SET nome=?, cognome=?, altezza=?, profilo=? WHERE id=?", (un, uc, ua, up, a_id))
                    conn.commit()
                st.rerun()
            if cb2.button("⚠️ ELIMINA ATLETA"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM visite WHERE atleta_id=?", (a_id,))
                    conn.execute("DELETE FROM atleti WHERE id=?", (a_id,))
                    conn.commit()
                st.rerun()

        st.divider()
        with get_connection() as conn:
            vi = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id} ORDER BY data DESC", conn)
        
        if not vi.empty:
            st.subheader("📈 Analisi Storica e Confronto")
            vi['label'] = vi.apply(lambda x: f"ID:{x['id']} | Data: {x['data']} | {x['peso']}kg", axis=1)
            scelte = st.multiselect("Seleziona visite da comparare", vi['label'].tolist(), default=vi['label'].tolist()[:min(2, len(vi))])
            
            if len(scelte) >= 2:
                df_c = vi[vi['label'].isin(scelte)].sort_values(by='data')
                v_old, v_new = df_c.iloc[0], df_c.iloc[-1]
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Peso", f"{v_new['peso']} kg", f"{v_new['peso']-v_old['peso']:.1f} kg", delta_color="inverse")
                m2.metric("FM", f"{v_new['fm']}%", f"{v_new['fm']-v_old['fm']:.1f}%", delta_color="inverse")
                m3.metric("FTP", f"{v_new['ftp']} W", f"{v_new['ftp']-v_old['ftp']:.0f} W")
                m4.metric("W/kg", f"{v_new['ftp']/v_new['peso']:.2f}", f"{(v_new['ftp']/v_new['peso'])-(v_old['ftp']/v_old['peso']):.2f}")
                st.dataframe(df_c.drop(columns=['label', 'atleta_id']), hide_index=True)
            else:
                st.dataframe(vi.drop(columns=['label', 'atleta_id']), hide_index=True)

            with st.expander("🗑️ Elimina una singola visita"):
                vis_to_del = st.selectbox("Seleziona ID visita da eliminare", vi['id'].tolist())
                if st.button("Elimina Visita"):
                    with get_connection() as conn:
                        conn.execute(f"DELETE FROM visite WHERE id={vis_to_del}")
                        conn.commit()
                    st.rerun()
