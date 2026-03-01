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
        eval_text = f"Analisi Biometrica:\n- BMI: {bmi:.1f} kg/m²\n- Massa Magra (FFM): {ffm:.1f} kg\n- Indice FFMI: {ffmi:.1f} kg/m²\n\n"
        eval_text += f"Valutazione Clinica: L'atleta rientra nel profilo '{profilo}'. "
        if fm > 15 and profilo == "Scalatore":
            eval_text += "Si rileva un margine di miglioramento tramite ricomposizione corporea per ottimizzare il rapporto W/kg."
        else:
            eval_text += "Composizione corporea ottimale per le richieste metaboliche della disciplina."
        return eval_text

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        f_res = (peso + bike_w) * 9.81 * ((pend/100) + 0.005)
        if f_res <= 0 or watt <= 0: return 0
        speed_ms = watt / f_res
        time_min = (km * 1000 / speed_ms) / 60
        return time_min

    @staticmethod
    def get_zones(ftp, lthr):
        # Zone Potenza
        z_p = [
            ("Z1 Recupero", 0, int(ftp*0.55)), ("Z2 Endurance", int(ftp*0.56), int(ftp*0.75)),
            ("Z3 Tempo", int(ftp*0.76), int(ftp*0.90)), ("Z4 Soglia", int(ftp*0.91), int(ftp*1.05)),
            ("Z5 VO₂max", int(ftp*1.06), int(ftp*1.20))
        ]
        # Zone Cardio (basate su LTHR)
        z_c = [
            ("Z1 Recupero", 0, int(lthr*0.68)), ("Z2 Endurance", int(lthr*0.69), int(lthr*0.83)),
            ("Z3 Tempo", int(lthr*0.84), int(lthr*0.94)), ("Z4 Soglia", int(lthr*0.95), int(lthr*1.05)),
            ("Z5 VO₂max", int(lthr*1.06), 220)
        ]
        return z_p, z_c

def pdf_safe(text):
    if not text: return ""
    replacements = {"²": "2", "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"}
    for key, val in replacements.items(): text = text.replace(key, val)
    return str(text).encode('latin-1', 'ignore').decode('latin-1')

# ---------------------------------------------------------
# 3. INTERFACCIA
# ---------------------------------------------------------
menu = st.sidebar.radio("NAVIGAZIONE", ["➕ Nuova Valutazione", "📂 Archivio Professionale"])

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
        bike = st.number_input("Peso Bici + Accessori (kg)", 5.0, 15.0, 8.0)

    if st.button("🚀 GENERA ANALISI PRESTAZIONALE", use_container_width=True):
        if not cog or not nome:
            st.error("Inserire Cognome e Nome.")
        else:
            t_a = BioPerformance.estimate_time(ftp_att, p_att, dist, grad, bike)
            t_t = BioPerformance.estimate_time(ftp_tar, p_tar, dist, grad, bike)
            giudizio = BioPerformance.get_eval(profilo, p_att, altezza, fm_att)
            z_p, z_c = BioPerformance.get_zones(ftp_tar, lthr)
            
            st.session_state['report'] = {
                'nome': nome, 'cognome': cog, 'alt': altezza, 'prof': profilo,
                'p_a': p_att, 'fm_a': fm_att, 'ftp_a': ftp_att, 'lthr': lthr,
                'p_t': p_tar, 'fm_t': fm_tar, 'ftp_t': ftp_tar,
                'dist': dist, 'grad': grad, 'bike': bike,
                't_a': t_a, 't_t': t_t, 'giudizio': giudizio, 'data': date.today().isoformat(),
                'z_p': z_p, 'z_c': z_c
            }

    if 'report' in st.session_state:
        r = st.session_state['report']
        st.divider()
        
        # 1. RISULTATI TEMPORALI CHIARI
        st.subheader("⏱️ Risultato della Proiezione")
        c_t1, c_t2, c_t3 = st.columns(3)
        c_t1.metric("Tempo Oggi", f"{r['t_a']:.2f} min")
        c_t2.metric("Tempo con Target", f"{r['t_t']:.2f} min")
        c_t3.metric("Guadagno Stimato", f"-{r['t_a']-r['t_t']:.2f} min", delta_color="normal")
        
        st.info(f"**Analisi Clinica:**\n{r['giudizio']}")

        # 2. TABELLE ZONE
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            st.markdown("### ⚡ Zone Potenza (Target)")
            st.table(pd.DataFrame(r['z_p'], columns=["Zona", "Min (W)", "Max (W)"]))
        with col_z2:
            st.markdown("### ❤️ Zone Cardio (Soglia: " + str(r['lthr']) + " bpm)")
            st.table(pd.DataFrame(r['z_c'], columns=["Zona", "Min (bpm)", "Max (bpm)"]))

        # 3. AZIONI
        c_b1, c_b2 = st.columns(2)
        with c_b1:
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
                st.success("Salvataggio completato!")

        with c_b2:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16); pdf.cell(190, 10, pdf_safe(f"REPORT PERFORMANCE: {r['nome']} {r['cognome']}"), 0, 1, 'C')
            pdf.set_font("Arial", '', 10); pdf.cell(190, 7, pdf_safe(f"Data: {r['data']} | Profilo: {r['prof']}"), 0, 1, 'C'); pdf.ln(10)
            
            # Box Analisi
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "VALUTAZIONE BIOMETRICA E CLINICA", 1, 1, 'L', True)
            pdf.set_font("Arial", '', 11); pdf.multi_cell(190, 8, pdf_safe(r['giudizio']), 1); pdf.ln(5)
            
            # Box Tempi
            pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "PROIEZIONE PERFORMANCE (SCENARIO)", 1, 1, 'L', True)
            pdf.set_font("Arial", '', 11)
            pdf.cell(190, 8, pdf_safe(f"Salita: {r['dist']}km al {r['grad']}% | Bici: {r['bike']}kg"), 1, 1)
            pdf.cell(190, 8, pdf_safe(f"- Tempo con parametri attuali: {r['t_a']:.2f} min"), 1, 1)
            pdf.cell(190, 8, pdf_safe(f"- Tempo con parametri target: {r['t_t']:.2f} min"), 1, 1)
            pdf.set_font("Arial", 'B', 11); pdf.cell(190, 10, pdf_safe(f"MIGLIORAMENTO STIMATO: {r['t_a']-r['t_t']:.2f} minuti"), 1, 1, 'C'); pdf.ln(5)
            
            # Tabelle Zone nel PDF
            pdf.set_font("Arial", 'B', 12); pdf.cell(95, 10, "ZONE POTENZA (W)", 1, 0, 'C', True); pdf.cell(95, 10, "ZONE CARDIO (BPM)", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 10)
            for i in range(len(r['z_p'])):
                pdf.cell(95, 7, f"{r['z_p'][i][0]}: {r['z_p'][i][1]}-{r['z_p'][i][2]} W", 1, 0)
                pdf.cell(95, 7, f"{r['z_c'][i][0]}: {r['z_c'][i][1]}-{r['z_c'][i][2]} bpm", 1, 1)
            
            st.download_button("📄 SCARICA REPORT COMPLETO PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Report_{r['cognome']}.pdf")

# --- SEZIONE ARCHIVIO (CRUD PROFESSIONALE) ---
elif menu == "📂 Archivio Professionale":
    st.header("🗄️ Gestione Archivio Atleti")
    with get_connection() as conn: at = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    if not at.empty:
        sel_atleta = st.selectbox("Seleziona Atleta", at.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}", axis=1))
        a_id = int(sel_atleta.split(" - ")[0])
        curr = at[at['id'] == a_id].iloc[0]

        with st.expander("⚙️ Modifica Anagrafica o Elimina Atleta"):
            c1, c2, c3, c4 = st.columns(4)
            un, uc, ua = c1.text_input("Nome", curr['nome']), c2.text_input("Cognome", curr['cognome']), c3.number_input("Altezza", 120, 230, int(curr['altezza']))
            up = c4.selectbox("Profilo", ["Scalatore", "Passista", "Triatleta", "Granfondista"], index=["Scalatore", "Passista", "Triatleta", "Granfondista"].index(curr['profilo']) if curr['profilo'] else 0)
            if st.button("✅ AGGIORNA ATLETA"):
                with get_connection() as conn:
                    conn.execute("UPDATE atleti SET nome=?, cognome=?, altezza=?, profilo=? WHERE id=?", (un, uc, ua, up, a_id))
                    conn.commit()
                st.rerun()
            if st.button("🗑️ ELIMINA TUTTO (ATLETA E VISITE)"):
                with get_connection() as conn:
                    conn.execute(f"DELETE FROM visite WHERE atleta_id={a_id}"); conn.execute(f"DELETE FROM atleti WHERE id={a_id}"); conn.commit()
                st.rerun()

        st.divider()
        with get_connection() as conn:
            vi = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id} ORDER BY data DESC", conn)
        
        if not vi.empty:
            st.subheader("📈 Storico e Confronto Visite")
            vi['label'] = vi.apply(lambda x: f"ID:{x['id']} | Data: {x['data']} | {x['peso']}kg", axis=1)
            scelte = st.multiselect("Seleziona visite da comparare", vi['label'].tolist(), default=vi['label'].tolist()[:min(2, len(vi))])
            
            if len(scelte) >= 2:
                df_c = vi[vi['label'].isin(scelte)].sort_values(by='data')
                v_o, v_n = df_c.iloc[0], df_c.iloc[-1]
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Peso", f"{v_n['peso']} kg", f"{v_n['peso']-v_o['peso']:.1f} kg", delta_color="inverse")
                m2.metric("FM", f"{v_n['fm']}%", f"{v_n['fm']-v_o['fm']:.1f}%", delta_color="inverse")
                m3.metric("FTP", f"{v_n['ftp']} W", f"{v_n['ftp']-v_o['ftp']:.0f} W")
                m4.metric("W/kg", f"{v_n['ftp']/v_n['peso']:.2f}", f"{(v_n['ftp']/v_n['peso'])-(v_o['ftp']/v_o['peso']):.2f}")
                st.dataframe(df_c.drop(columns=['label', 'atleta_id']), hide_index=True)
            else:
                st.dataframe(vi.drop(columns=['label', 'atleta_id']), hide_index=True)

            with st.expander("🗑️ Elimina singola visita"):
                vis_del = st.selectbox("ID visita da rimuovere", vi['id'].tolist())
                if st.button("Elimina Visita"):
                    with get_connection() as conn: conn.execute(f"DELETE FROM visite WHERE id={vis_del}"); conn.commit()
                    st.rerun()
