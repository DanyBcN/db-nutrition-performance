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
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS atleti 
                 (id INTEGER PRIMARY KEY, nome TEXT, cognome TEXT, altezza REAL, sesso TEXT, profilo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visite 
                 (id INTEGER PRIMARY KEY, atleta_id INTEGER, data TEXT, peso REAL, fm REAL, ftp REAL, 
                  lthr INTEGER, peso_t REAL, fm_t REAL, ftp_t REAL, t_att REAL, t_tar REAL,
                  dist_km REAL, grad REAL, bike_w REAL)''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# LOGICA CLINICA
# ---------------------------------------------------------
class NutritionScience:
    @staticmethod
    def get_clinical_judgment(profilo, peso, altezza, fm, fm_t):
        bmi = peso / ((altezza/100)**2)
        ranges = {"Scalatore (Lightweight)": (5, 10), "Passista (Powerhouse)": (9, 14), "Triatleta": (8, 12), "Granfondista": (10, 15)}
        low, high = ranges.get(profilo, (8, 15))
        
        j = f"L'atleta presenta un BMI di {bmi:.1f} kg/m² e una Fat Mass (FM%) del {fm}%.\n"
        j += f"Per la categoria {profilo}, il range ottimale è {low}-{high}%.\n"
        if fm > high:
            j += f"La composizione attuale è superiore al set-point; il target del {fm_t}% è prioritario."
        else:
            j += "La composizione è ottimale; focus su efficienza e potenza."
        return j

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

if menu == "Nuova Analisi":
    st.header("📋 Valutazione Biometrica & Performance")
    
    # 1. RICERCA / INSERIMENTO ATLETA
    conn = get_connection()
    db_atleti = pd.read_sql_query("SELECT DISTINCT cognome FROM atleti", conn)
    lista_cognomi = db_atleti['cognome'].tolist()
    conn.close()

    with st.expander("👤 Anagrafica Atleta", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        # Cognome per primo con suggerimenti
        cognome = c1.selectbox("Cognome (Cerca o scrivi nuovo)", [""] + lista_cognomi, index=0)
        if not cognome: # Se non selezionato, permette inserimento manuale
            cognome = c1.text_input("Inserisci nuovo Cognome")
        
        nome = c2.text_input("Nome")
        data_v = c3.date_input("Data Visita (GG/MM/AAAA)", date.today(), format="DD/MM/YYYY")
        altezza = c4.number_input("Altezza (cm)", 120, 230, 175)
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
        t_att = NutritionScience.estimate_time(ftp, peso, dist_km, grad, bike_w)
        t_tar = NutritionScience.estimate_time(ftp_t, peso_t, dist_km, grad, bike_w)
        giudizio = NutritionScience.get_clinical_judgment(profilo, peso, altezza, fm, fm_t)
        
        st.session_state['res'] = {
            'n': nome, 'c': cognome, 'data': data_v.strftime("%d/%m/%Y"),
            'p': peso, 'fm': fm, 'ftp': ftp, 'lthr': lthr,
            'p_t': peso_t, 'fm_t': fm_t, 'ftp_t': ftp_t, 'prof': profilo,
            't_a': t_att, 't_t': t_tar, 'd': dist_km, 'g': grad, 'b': bike_w,
            'giudizio': giudizio, 'wkg_a': ftp/peso, 'wkg_t': ftp_t/peso_t
        }

    if 'res' in st.session_state:
        r = st.session_state['res']
        st.divider()
        
        # ZONE TARGET
        z_p = [("Z1 Recupero", 0, int(r['ftp_t']*0.55)), ("Z2 Endurance", int(r['ftp_t']*0.56), int(r['ftp_t']*0.75)), ("Z3 Tempo", int(r['ftp_t']*0.76), int(r['ftp_t']*0.90)), ("Z4 Soglia", int(r['ftp_t']*0.91), int(r['ftp_t']*1.05)), ("Z5 VO2max", int(r['ftp_t']*1.06), int(r['ftp_t']*1.20))]
        z_h = [("Z1 Rigenerante", 0, int(r['lthr']*0.81)), ("Z2 Fondo Lento", int(r['lthr']*0.82), int(r['lthr']*0.89)), ("Z3 Fondo Medio", int(r['lthr']*0.90), int(r['lthr']*0.93)), ("Z4 Soglia", int(r['lthr']*0.94), int(r['lthr']*1.00)), ("Z5 Fuorisoglia", int(r['lthr']*1.01), int(r['lthr']*1.10))]
        
        c_z1, c_z2 = st.columns(2)
        with c_z1: st.write("### ⚡ Zone Potenza Target"); st.table(pd.DataFrame(z_p, columns=["Zona", "Min (W)", "Max (W)"]))
        with c_z2: st.write("### ❤️ Zone Cardio Target"); st.table(pd.DataFrame(z_h, columns=["Zona", "Min (bpm)", "Max (bpm)"]))

        st.info(f"**Valutazione Clinica:**\n{r['giudizio']}")

        

        # PERFORMANCE
        st.write("### 🏔️ Analisi Performance in Salita")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("W/kg Prima", f"{r['wkg_a']:.2f}")
        m2.metric("W/kg Dopo", f"{r['wkg_t']:.2f}", f"{r['wkg_t']-r['wkg_a']:.2f}")
        m3.metric("Tempo Prima", f"{r['t_a']:.2f} min")
        m4.metric("Tempo Dopo", f"{r['t_t']:.2f} min", f"-{r['t_a']-r['t_t']:.2f} min", delta_color="normal")

        st.divider()
        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("💾 SALVA IN ARCHIVIO"):
                conn = get_connection(); c = conn.cursor()
                c.execute("INSERT INTO atleti (nome, cognome, profilo, altezza) VALUES (?,?,?,?)", (r['n'], r['c'], r['prof'], altezza))
                a_id = c.lastrowid
                c.execute("INSERT INTO visite (atleta_id, data, peso, fm, ftp, lthr, peso_t, fm_t, ftp_t, t_att, t_tar, dist_km, grad, bike_w) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (a_id, r['data'], r['p'], r['fm'], r['ftp'], r['lthr'], r['p_t'], r['fm_t'], r['ftp_t'], r['t_a'], r['t_t'], r['d'], r['g'], r['b']))
                conn.commit(); conn.close(); st.success("Salvato!")

        with sc2:
            pdf = FPDF()
            pdf.add_page()
            if os.path.exists(LOGO_PATH): pdf.image(LOGO_PATH, x=150, y=8, w=40)
            pdf.set_font("Arial", 'B', 16); pdf.cell(130, 10, pdf_safe(f"REPORT: {r['n']} {r['c']}"), 0, 1)
            pdf.set_font("Arial", '', 10); pdf.cell(130, 7, f"Data: {r['data']}", 0, 1); pdf.ln(10)
            
            pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "1. ZONE TARGET", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 10)
            for i in range(5):
                pdf.cell(95, 8, pdf_safe(f"{z_p[i][0]}: {z_p[i][1]}-{z_p[i][2]} W"), 1, 0)
                pdf.cell(95, 8, pdf_safe(f"{z_h[i][0]}: {z_h[i][1]}-{z_h[i][2]} bpm"), 1, 1)

            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "2. VALUTAZIONE CLINICA", 0, 1)
            pdf.set_font("Arial", '', 11); pdf.multi_cell(190, 7, pdf_safe(r['giudizio']))

            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "3. PERFORMANCE IN SALITA", 0, 1)
            pdf.set_font("Arial", 'B', 10); pdf.cell(60, 10, "Dato", 1, 0, 'L', True); pdf.cell(65, 10, "Attuale", 1, 0, 'C', True); pdf.cell(65, 10, "Target", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 10)
            pdf.cell(60, 10, "Watt / kg", 1); pdf.cell(65, 10, f"{r['wkg_a']:.2f}", 1); pdf.cell(65, 10, f"{r['wkg_t']:.2f}", 1); pdf.ln()
            pdf.cell(60, 10, "Tempo Scalata", 1); pdf.cell(65, 10, f"{r['t_a']:.2f} min", 1); pdf.cell(65, 10, f"{r['t_t']:.2f} min", 1); pdf.ln()
            pdf.set_fill_color(200, 255, 200); pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 10, pdf_safe(f"MIGLIORAMENTO: -{r['t_a']-r['t_t']:.2f} minuti"), 1, 1, 'C', True)

            st.download_button("📄 SCARICA PDF", data=pdf.output(dest='S').encode('latin-1', 'replace'), file_name=f"Report_{r['c']}.pdf")

elif menu == "Archivio Atleti":
    st.header("📂 Archivio")
    conn = get_connection(); atleti = pd.read_sql_query("SELECT * FROM atleti", conn)
    if not atleti.empty:
        sel = st.selectbox("Atleta", atleti.apply(lambda x: f"{x['id']} - {x['cognome']} {x['nome']}", axis=1))
        a_id = sel.split(" - ")[0]
        st.dataframe(pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id}", conn))
    else: st.info("Vuoto.")
