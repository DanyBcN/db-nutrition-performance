import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from fpdf import FPDF
import os

# ---------------------------------------------------------
# SETUP E DATABASE (CON RIPARAZIONE AUTOMATICA SCHEMA)
# ---------------------------------------------------------
st.set_page_config(page_title="DB Nutrition & Performance", layout="wide", page_icon="🧬")
LOGO_PATH = "Logo NUTRITION AND PERFORMANCE.png"

def get_connection():
    return sqlite3.connect("performance_lab.db")

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        
        # 1. Creazione tabelle base (se non esistono)
        c.execute('''CREATE TABLE IF NOT EXISTS atleti 
                     (id INTEGER PRIMARY KEY, nome TEXT, cognome TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS visite 
                     (id INTEGER PRIMARY KEY, atleta_id INTEGER, data TEXT)''')
        
        # 2. Migrazione Tabella ATLETI: aggiunta colonne mancanti
        c.execute("PRAGMA table_info(atleti)")
        cols_atleti = [column[1] for column in c.fetchall()]
        migrazioni_atleti = {
            'altezza': 'REAL',
            'sesso': 'TEXT',
            'profilo': 'TEXT'
        }
        for col, tipo in migrazioni_atleti.items():
            if col not in cols_atleti:
                c.execute(f"ALTER TABLE atleti ADD COLUMN {col} {tipo}")
        
        # 3. Migrazione Tabella VISITE: aggiunta colonne mancanti (Risolve dist_km, grad, ecc.)
        c.execute("PRAGMA table_info(visite)")
        cols_visite = [column[1] for column in c.fetchall()]
        migrazioni_visite = {
            'peso': 'REAL', 'fm': 'REAL', 'ftp': 'REAL', 'lthr': 'INTEGER',
            'peso_t': 'REAL', 'fm_t': 'REAL', 'ftp_t': 'REAL', 
            't_att': 'REAL', 't_tar': 'REAL', 
            'dist_km': 'REAL', 'grad': 'REAL', 'bike_w': 'REAL'
        }
        for col, tipo in migrazioni_visite.items():
            if col not in cols_visite:
                c.execute(f"ALTER TABLE visite ADD COLUMN {col} {tipo}")
        
        conn.commit()

init_db()

# ---------------------------------------------------------
# LOGICA CLINICA E SCIENTIFICA
# ---------------------------------------------------------
class NutritionScience:
    @staticmethod
    def get_clinical_judgment(profilo, peso, altezza, fm, fm_t):
        bmi = peso / ((altezza/100)**2)
        ffm = peso * (1 - fm/100)  # Fat-Free Mass
        ffmi = ffm / ((altezza/100)**2)  # Fat-Free Mass Index
        
        ranges = {
            "Scalatore (Lightweight)": (5, 10), 
            "Passista (Powerhouse)": (9, 14), 
            "Triatleta": (8, 12), 
            "Granfondista": (10, 15)
        }
        low, high = ranges.get(profilo, (8, 15))
        
        j = f"BMI: {bmi:.1f} kg/m² | FM: {fm}% | FFM: {ffm:.1f} kg (FFMI: {ffmi:.1f}).\n"
        j += f"Range ottimale per {profilo}: {low}-{high}%.\n"
        
        if fm > high:
            j += f"La composizione è superiore al target; la riduzione della FM al {fm_t}% è prioritaria."
        elif ffmi < 17:
            j += "ATTENZIONE: FFMI basso. Rischio di deplezione della massa magra."
        else:
            j += "Composizione ottimale; focus su efficienza e potenza."
        return j

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        # Fisica: Forza = m * g * (pendenza + attrito)
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
    
    with get_connection() as conn:
        db_atleti = pd.read_sql_query("SELECT * FROM atleti", conn)
    lista_cognomi = sorted(db_atleti['cognome'].unique().tolist())

    with st.expander("👤 Anagrafica Atleta", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        cognome_sel = c1.selectbox("Cognome registrato", [""] + lista_cognomi)
        cognome_man = c1.text_input("...o Nuovo Cognome")
        final_cognome = cognome_man if cognome_man else cognome_sel
        
        atleta_esistente = db_atleti[db_atleti['cognome'] == final_cognome].iloc[0] if final_cognome in lista_cognomi else None
        
        nome = c2.text_input("Nome", value=atleta_esistente['nome'] if atleta_esistente is not None else "")
        data_v = c3.date_input("Data Visita", date.today(), format="DD/MM/YYYY")
        altezza = c4.number_input("Altezza (cm)", 120, 230, int(atleta_esistente['altezza']) if atleta_esistente is not None else 175)
        profilo = c5.selectbox("Specializzazione", ["Scalatore (Lightweight)", "Passista (Powerhouse)", "Triatleta", "Granfondista"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🧱 Stato Attuale")
        peso = st.number_input("Peso (kg)", 40.0, 150.0, 70.0)
        fm = st.number_input("Massa Grassa (%)", 3.0, 40.0, 15.0)
        ftp = st.number_input("FTP (W)", 50, 600, 250)
        lthr = st.number_input("LTHR (bpm)", 80, 220, 165)
        
    with col2:
        st.subheader("🎯 Target")
        peso_t = st.number_input("Peso Target (kg)", 40.0, 150.0, 68.0)
        fm_t = st.number_input("FM% Target", 3.0, 40.0, 10.0)
        ftp_t = st.number_input("FTP Target (W)", 50, 600, 275)

    with col3:
        st.subheader("🏔️ Scenario Salita")
        dist_km = st.number_input("Distanza (km)", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza (%)", 0.0, 20.0, 7.0)
        bike_w = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.0)

    if st.button("🚀 GENERA ANALISI"):
        if not final_cognome or not nome:
            st.error("Inserire Nome e Cognome.")
        else:
            t_att = NutritionScience.estimate_time(ftp, peso, dist_km, grad, bike_w)
            t_tar = NutritionScience.estimate_time(ftp_t, peso_t, dist_km, grad, bike_w)
            giudizio = NutritionScience.get_clinical_judgment(profilo, peso, altezza, fm, fm_t)
            
            st.session_state['res'] = {
                'n': nome, 'c': final_cognome, 'data': data_v.strftime("%d/%m/%Y"),
                'p': peso, 'fm': fm, 'ftp': ftp, 'lthr': lthr, 'alt': altezza,
                'p_t': peso_t, 'fm_t': fm_t, 'ftp_t': ftp_t, 'prof': profilo,
                't_a': t_att, 't_t': t_tar, 'd': dist_km, 'g': grad, 'b': bike_w,
                'giudizio': giudizio, 'wkg_a': ftp/peso, 'wkg_t': ftp_t/peso_t
            }

    if 'res' in st.session_state:
        r = st.session_state['res']
        st.divider()
        
        # Zone di Potenza e Cardio
        z_p = [("Z1 Recupero", 0, int(r['ftp_t']*0.55)), ("Z2 Endurance", int(r['ftp_t']*0.56), int(r['ftp_t']*0.75)), ("Z3 Tempo", int(r['ftp_t']*0.76), int(r['ftp_t']*0.90)), ("Z4 Soglia", int(r['ftp_t']*0.91), int(r['ftp_t']*1.05)), ("Z5 VO2max", int(r['ftp_t']*1.06), int(r['ftp_t']*1.20))]
        z_h = [("Z1 Rigenerante", 0, int(r['lthr']*0.81)), ("Z2 Fondo Lento", int(r['lthr']*0.82), int(r['lthr']*0.89)), ("Z3 Fondo Medio", int(r['lthr']*0.90), int(r['lthr']*0.93)), ("Z4 Soglia", int(r['lthr']*0.94), int(r['lthr']*1.00)), ("Z5 Fuorisoglia", int(r['lthr']*1.01), int(r['lthr']*1.10))]
        
        c_z1, c_z2 = st.columns(2)
        with c_z1: st.write("### ⚡ Potenza Target"); st.table(pd.DataFrame(z_p, columns=["Zona", "Min (W)", "Max (W)"]))
        with c_z2: st.write("### ❤️ Cardio Target"); st.table(pd.DataFrame(z_h, columns=["Zona", "Min (bpm)", "Max (bpm)"]))

        st.info(f"**Valutazione Clinica:**\n{r['giudizio']}")

        st.write("### 🏔️ Analisi Performance")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("W/kg Prima", f"{r['wkg_a']:.2f}")
        m2.metric("W/kg Dopo", f"{r['wkg_t']:.2f}", f"{r['wkg_t']-r['wkg_a']:.2f}")
        m3.metric("Tempo Prima", f"{r['t_a']:.2f} min")
        m4.metric("Tempo Dopo", f"{r['t_t']:.2f} min", f"-{r['t_a']-r['t_t']:.2f} min")

        st.divider()
        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("💾 SALVA IN ARCHIVIO"):
                try:
                    with get_connection() as conn:
                        c = conn.cursor()
                        c.execute("SELECT id FROM atleti WHERE cognome=? AND nome=?", (r['c'], r['n']))
                        atleta_db = c.fetchone()
                        if atleta_db:
                            a_id = atleta_db[0]
                            c.execute("UPDATE atleti SET altezza=?, profilo=? WHERE id=?", (r['alt'], r['prof'], a_id))
                        else:
                            c.execute("INSERT INTO atleti (nome, cognome, profilo, altezza) VALUES (?,?,?,?)", (r['n'], r['c'], r['prof'], r['alt']))
                            a_id = c.lastrowid
                        
                        c.execute("""INSERT INTO visite (atleta_id, data, peso, fm, ftp, lthr, peso_t, fm_t, ftp_t, t_att, t_tar, dist_km, grad, bike_w) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                                  (a_id, r['data'], r['p'], r['fm'], r['ftp'], r['lthr'], r['p_t'], r['fm_t'], r['ftp_t'], r['t_a'], r['t_t'], r['d'], r['g'], r['b']))
                        conn.commit()
                        st.success(f"Dati di {r['n']} {r['c']} salvati!")
                except Exception as e:
                    st.error(f"Errore DB: {e}")

        with sc2:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(130, 10, pdf_safe(f"REPORT: {r['n']} {r['c']}"), 0, 1)
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(190, 7, pdf_safe(r['giudizio']))
            st.download_button("📄 SCARICA PDF", data=pdf.output(dest='S').encode('latin-1', 'replace'), file_name=f"Report_{r['c']}.pdf")

elif menu == "Archivio Atleti":
    st.header("📂 Archivio Storico")
    with get_connection() as conn:
        atleti = pd.read_sql_query("SELECT * FROM atleti", conn)
    
    if not atleti.empty:
        sel = st.selectbox("Seleziona Atleta", atleti.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}", axis=1))
        a_id = sel.split(" - ")[0]
        with get_connection() as conn:
            visite_df = pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id} ORDER BY id DESC", conn)
        st.dataframe(visite_df, use_container_width=True)
    else:
        st.info("Archivio vuoto.")
