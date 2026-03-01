import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from fpdf import FPDF
import os

# ---------------------------------------------------------
# SETUP E DATABASE (AUTO-REPAIR SCHEMA)
# ---------------------------------------------------------
st.set_page_config(page_title="DB Nutrition & Performance", layout="wide", page_icon="🧬")
LOGO_PATH = "Logo NUTRITION AND PERFORMANCE.png"

def get_connection():
    return sqlite3.connect("performance_lab.db")

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS atleti (id INTEGER PRIMARY KEY, nome TEXT, cognome TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS visite (id INTEGER PRIMARY KEY, atleta_id INTEGER, data TEXT)''')
        
        # Migrazione ATLETI
        c.execute("PRAGMA table_info(atleti)")
        cols_atleti = [column[1] for column in c.fetchall()]
        for col, tipo in {'altezza': 'REAL', 'sesso': 'TEXT', 'profilo': 'TEXT'}.items():
            if col not in cols_atleti: c.execute(f"ALTER TABLE atleti ADD COLUMN {col} {tipo}")
        
        # Migrazione VISITE
        c.execute("PRAGMA table_info(visite)")
        cols_visite = [column[1] for column in c.fetchall()]
        migr_v = {
            'peso': 'REAL', 'fm': 'REAL', 'ftp': 'REAL', 'lthr': 'INTEGER',
            'peso_t': 'REAL', 'fm_t': 'REAL', 'ftp_t': 'REAL', 
            't_att': 'REAL', 't_tar': 'REAL', 'dist_km': 'REAL', 'grad': 'REAL', 'bike_w': 'REAL'
        }
        for col, tipo in migr_v.items():
            if col not in cols_visite: c.execute(f"ALTER TABLE visite ADD COLUMN {col} {tipo}")
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
        ranges = {"Scalatore (Lightweight)": (5, 10), "Passista (Powerhouse)": (9, 14), "Triatleta": (8, 12), "Granfondista": (10, 15)}
        low, high = ranges.get(profilo, (8, 15))
        
        j = f"L'atleta presenta un BMI di {bmi:.1f} kg/m² e una Fat Mass (FM%) del {fm}%.\n"
        j += f"Massa Magra stimata (FFM): {ffm:.1f} kg con un indice FFMI di {ffmi:.1f}.\n"
        j += f"Per il profilo {profilo}, il range ottimale di riferimento è {low}-{high}%.\n"
        if fm > high: j += f"Composizione corporea superiore al target; riduzione adiposa prioritaria."
        elif ffmi < 17: j += "ATTENZIONE: Indice FFMI ridotto, monitorare apporto proteico e carichi."
        else: j += "Composizione ottimale; focus su efficienza neuromuscolare."
        return j

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        f_res = (peso + bike_w) * 9.81 * ((pend/100) + 0.005)
        return (km / ((watt / f_res) * 3.6)) * 60 if f_res > 0 and watt > 0 else 0

def pdf_safe(t): return str(t).encode('latin-1', 'replace').decode('latin-1')

# ---------------------------------------------------------
# UI STREAMLIT
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, use_container_width=True)
    menu = st.radio("Menu", ["Nuova Analisi", "Archivio Atleti"])

if menu == "Nuova Analisi":
    st.header("📋 Valutazione Biometrica & Performance")
    with get_connection() as conn: db_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)
    lista_cognomi = sorted(db_atleti['cognome'].unique().tolist())

    with st.expander("👤 Anagrafica Atleta", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        cog_sel = c1.selectbox("Cognome registrato", [""] + lista_cognomi)
        cog_man = c1.text_input("...o Nuovo")
        final_cog = cog_man if cog_man else cog_sel
        atleta_ex = db_atleti[db_atleti['cognome'] == final_cog].iloc[0] if final_cog in lista_cognomi else None
        nome = c2.text_input("Nome", value=atleta_ex['nome'] if atleta_ex is not None else "")
        data_v = c3.date_input("Data Visita", date.today(), format="DD/MM/YYYY")
        altezza = c4.number_input("Altezza (cm)", 120, 230, int(atleta_ex['altezza']) if atleta_ex is not None else 175)
        profilo = c5.selectbox("Specializzazione", ["Scalatore (Lightweight)", "Passista (Powerhouse)", "Triatleta", "Granfondista"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🧱 Stato Attuale")
        peso, fm = st.number_input("Peso (kg)", 40.0, 150.0, 70.0), st.number_input("Massa Grassa (%)", 3.0, 40.0, 15.0)
        ftp, lthr = st.number_input("FTP (W)", 50, 600, 250), st.number_input("LTHR (bpm)", 80, 220, 165)
    with col2:
        st.subheader("🎯 Target")
        peso_t, fm_t = st.number_input("Peso Target (kg)", 40.0, 150.0, 68.0), st.number_input("FM% Target", 3.0, 40.0, 10.0)
        ftp_t = st.number_input("FTP Target (W)", 50, 600, 275)
    with col3:
        st.subheader("🏔️ Scenario Salita")
        dist_km, grad = st.number_input("Distanza (km)", 0.1, 50.0, 10.0), st.number_input("Pendenza (%)", 0.0, 20.0, 7.0)
        bike_w = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.0)

    if st.button("🚀 GENERA ANALISI"):
        if not final_cog or not nome: st.error("Dati mancanti.")
        else:
            t_a, t_t = NutritionScience.estimate_time(ftp, peso, dist_km, grad, bike_w), NutritionScience.estimate_time(ftp_t, peso_t, dist_km, grad, bike_w)
            st.session_state['res'] = {
                'n': nome, 'c': final_cog, 'data': data_v.strftime("%d/%m/%Y"), 'alt': altezza, 'prof': profilo,
                'p': peso, 'fm': fm, 'ftp': ftp, 'lthr': lthr, 'p_t': peso_t, 'fm_t': fm_t, 'ftp_t': ftp_t,
                't_a': t_a, 't_t': t_t, 'd': dist_km, 'g': grad, 'b': bike_w, 'wkg_a': ftp/peso, 'wkg_t': ftp_t/peso_t,
                'giudizio': NutritionScience.get_clinical_judgment(profilo, peso, altezza, fm, fm_t)
            }

    if 'res' in st.session_state:
        r = st.session_state['res']
        st.divider()
        zp = [("Z1 Recupero", 0, int(r['ftp_t']*0.55)), ("Z2 Endurance", int(r['ftp_t']*0.56), int(r['ftp_t']*0.75)), ("Z3 Tempo", int(r['ftp_t']*0.76), int(r['ftp_t']*0.90)), ("Z4 Soglia", int(r['ftp_t']*0.91), int(r['ftp_t']*1.05)), ("Z5 VO2max", int(r['ftp_t']*1.06), int(r['ftp_t']*1.20))]
        zh = [("Z1 Rigenerante", 0, int(r['lthr']*0.81)), ("Z2 Fondo Lento", int(r['lthr']*0.82), int(r['lthr']*0.89)), ("Z3 Fondo Medio", int(r['lthr']*0.90), int(r['lthr']*0.93)), ("Z4 Soglia", int(r['lthr']*0.94), int(r['lthr']*1.00)), ("Z5 Fuorisoglia", int(r['lthr']*1.01), int(r['lthr']*1.10))]
        
        c_z1, c_z2 = st.columns(2)
        with c_z1: st.write("### ⚡ Potenza Target"); st.table(pd.DataFrame(zp, columns=["Zona", "Min (W)", "Max (W)"]))
        with c_z2: st.write("### ❤️ Cardio Target"); st.table(pd.DataFrame(zh, columns=["Zona", "Min (bpm)", "Max (bpm)"]))
        st.info(f"**Valutazione Clinica:**\n{r['giudizio']}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("W/kg Prima", f"{r['wkg_a']:.2f}"); m2.metric("W/kg Dopo", f"{r['wkg_t']:.2f}", f"{r['wkg_t']-r['wkg_a']:.2f}")
        m3.metric("Tempo Prima", f"{r['t_a']:.2f} min"); m4.metric("Tempo Dopo", f"{r['t_t']:.2f} min", f"-{r['t_a']-r['t_t']:.2f}")

        st.divider()
        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("💾 SALVA IN ARCHIVIO"):
                with get_connection() as conn:
                    c = conn.cursor()
                    c.execute("SELECT id FROM atleti WHERE cognome=? AND nome=?", (r['c'], r['n']))
                    row = c.fetchone()
                    if row: a_id = row[0]
                    else:
                        c.execute("INSERT INTO atleti (nome, cognome, profilo, altezza) VALUES (?,?,?,?)", (r['n'], r['c'], r['prof'], r['alt']))
                        a_id = c.lastrowid
                    c.execute("""INSERT INTO visite (atleta_id, data, peso, fm, ftp, lthr, peso_t, fm_t, ftp_t, t_att, t_tar, dist_km, grad, bike_w) 
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (a_id, r['data'], r['p'], r['fm'], r['ftp'], r['lthr'], r['p_t'], r['fm_t'], r['ftp_t'], r['t_a'], r['t_t'], r['d'], r['g'], r['b']))
                    conn.commit()
                st.success("Salvato!")

        with sc2:
            pdf = FPDF()
            pdf.add_page()
            if os.path.exists(LOGO_PATH): pdf.image(LOGO_PATH, x=150, y=8, w=40)
            pdf.set_font("Arial", 'B', 16); pdf.cell(130, 10, pdf_safe(f"REPORT: {r['n']} {r['c']}"), 0, 1)
            pdf.set_font("Arial", '', 10); pdf.cell(130, 7, f"Data: {r['data']} | Altezza: {r['alt']}cm | Profilo: {r['prof']}", 0, 1); pdf.ln(10)
            
            # Sezione 1: Valutazione
            pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "1. VALUTAZIONE CLINICA BIOMETRICA", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 11); pdf.multi_cell(190, 8, pdf_safe(r['giudizio']), 1); pdf.ln(5)

            # Sezione 2: Zone
            pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "2. ZONE DI ALLENAMENTO TARGET (Basate su FTP Target)", 1, 1, 'C', True)
            pdf.set_font("Arial", 'B', 10); pdf.cell(95, 8, "Potenza (W)", 1, 0, 'C'); pdf.cell(95, 8, "Cardio (bpm)", 1, 1, 'C')
            pdf.set_font("Arial", '', 9)
            for i in range(5):
                pdf.cell(95, 7, pdf_safe(f"{zp[i][0]}: {zp[i][1]}-{zp[i][2]} W"), 1, 0)
                pdf.cell(95, 7, pdf_safe(f"{zh[i][0]}: {zh[i][1]}-{zh[i][2]} bpm"), 1, 1)
            pdf.ln(5)

            # Sezione 3: Performance
            pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "3. PREVISIONE PERFORMANCE IN SALITA", 1, 1, 'C', True)
            pdf.set_font("Arial", 'B', 10); pdf.cell(60, 8, "Parametro", 1, 0, 'C'); pdf.cell(65, 8, "Stato Attuale", 1, 0, 'C'); pdf.cell(65, 8, "Stato Target", 1, 1, 'C')
            pdf.set_font("Arial", '', 10)
            data_perf = [("Peso Sistema", f"{r['p']+r['b']} kg", f"{r['p_t']+r['b']} kg"), ("Rapporto W/Kg", f"{r['wkg_a']:.2f}", f"{r['wkg_t']:.2f}"), ("Tempo Scalata", f"{r['t_a']:.2f} min", f"{r['t_t']:.2f} min")]
            for row in data_perf:
                pdf.cell(60, 8, row[0], 1); pdf.cell(65, 8, row[1], 1, 0, 'C'); pdf.cell(65, 8, row[2], 1, 1, 'C')
            
            pdf.set_fill_color(200, 255, 200); pdf.set_font("Arial", 'B', 11)
            diff = r['t_a']-r['t_t']
            pdf.cell(190, 10, pdf_safe(f"MIGLIORAMENTO ESTIMATO: - {diff:.2f} minuti"), 1, 1, 'C', True)
            
            st.download_button("📄 SCARICA REPORT COMPLETO", data=pdf.output(dest='S').encode('latin-1', 'replace'), file_name=f"Report_{r['c']}.pdf")

elif menu == "Archivio Atleti":
    st.header("📂 Archivio")
    with get_connection() as conn: at = pd.read_sql_query("SELECT * FROM atleti", conn)
    if not at.empty:
        sel = st.selectbox("Atleta", at.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}", axis=1))
        a_id = sel.split(" - ")[0]
        with get_connection() as conn: st.dataframe(pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id} ORDER BY data DESC", conn), use_container_width=True)
