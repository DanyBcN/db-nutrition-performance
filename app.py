import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
from fpdf import FPDF
import os

# ---------------------------------------------------------
# SETUP E DATABASE
# ---------------------------------------------------------
st.set_page_config(page_title="DB Nutrition & Performance", layout="wide", page_icon="🧬")
LOGO_PATH = "Logo NUTRITION AND PERFORMANCE.png"

def init_db():
    conn = sqlite3.connect("performance_lab.db")
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
# LOGICA CLINICA E SCIENTIFICA
# ---------------------------------------------------------
class NutritionScience:
    @staticmethod
    def get_bmi(peso, altezza):
        return peso / (altezza ** 2)

    @staticmethod
    def get_clinical_judgment(profilo, bmi, fm, fm_t):
        # Definiamo i range ottimali per categoria (semplificato per logica interna)
        ranges = {
            "Scalatore (Lightweight)": (5, 10),
            "Passista (Powerhouse)": (9, 14),
            "Triatleta": (8, 12),
            "Granfondista": (10, 15)
        }
        low, high = ranges.get(profilo, (8, 15))
        
        giudizio = f"L'atleta presenta attualmente un BMI di {bmi:.1f} kg/m² e una Fat Mass (FM%) del {fm}%.\n"
        giudizio += f"Considerando la categoria selezionata ({profilo}), il range di FM% ideale è compreso tra il {low}% e il {high}%.\n"
        
        if fm > high:
            giudizio += f"L'attuale composizione corporea risulta superiore al set-point ottimale. L'obiettivo fissato al {fm_t}% è coerente con il miglioramento del rapporto potenza/peso."
        else:
            giudizio += "La composizione corporea è già in un range ottimale; il focus sarà sul mantenimento della massa magra durante l'incremento della potenza soglia."
        return giudizio

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        m_tot = peso + bike_w
        f_res = m_tot * 9.81 * ((pend/100) + 0.005)
        if f_res <= 0 or watt <= 0: return 0
        return (km / ((watt / f_res) * 3.6)) * 60

    @staticmethod
    def get_zones(ftp, lthr):
        pz = [("Z1 Recupero", 0, int(ftp*0.55)), ("Z2 Endurance", int(ftp*0.56), int(ftp*0.75)),
              ("Z3 Tempo", int(ftp*0.76), int(ftp*0.90)), ("Z4 Soglia", int(ftp*0.91), int(ftp*1.05)),
              ("Z5 VO2max", int(ftp*1.06), int(ftp*1.20))]
        hz = [("Z1 Rigenerante", 0, int(lthr*0.81)), ("Z2 Fondo Lento", int(lthr*0.82), int(lthr*0.89)),
              ("Z3 Fondo Medio", int(lthr*0.90), int(lthr*0.93)), ("Z4 Soglia", int(lthr*0.94), int(lthr*1.00)),
              ("Z5 Fuorisoglia", int(lthr*1.01), int(lthr*1.10))]
        return pz, hz

def pdf_safe(t): return str(t).encode('latin-1', 'replace').decode('latin-1')

# ---------------------------------------------------------
# INTERFACCIA
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, use_container_width=True)
    menu = st.radio("Menu", ["Nuova Analisi", "Archivio Atleti"])

if menu == "Nuova Analisi":
    st.header("📋 Valutazione Biometrica & Performance")
    
    with st.expander("👤 Anagrafica e Data Visita", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        nome = c1.text_input("Nome")
        cognome = c2.text_input("Cognome")
        data_visita = c3.date_input("Data Visita", date.today())
        altezza_cm = c4.number_input("Altezza (cm)", 120, 230, 175)
        profilo = c5.selectbox("Specializzazione", ["Scalatore (Lightweight)", "Passista (Powerhouse)", "Triatleta", "Granfondista"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🧱 Dati Attuali")
        peso = st.number_input("Peso (kg)", 40.0, 150.0, 70.0)
        fm = st.number_input("Massa Grassa (%)", 3.0, 40.0, 15.0)
        ftp = st.number_input("FTP (Watt)", 50, 600, 250)
        lthr = st.number_input("LTHR (bpm)", 80, 220, 165)
        
    with col2:
        st.subheader("🎯 Target")
        peso_t = st.number_input("Peso Target (kg)", 40.0, 150.0, 68.0)
        fm_t = st.number_input("FM% Target", 3.0, 40.0, 10.0)
        ftp_t = st.number_input("FTP Target (Watt)", 50, 600, 275)

    with col3:
        st.subheader("🏔️ Scenario Scalata")
        dist_km = st.number_input("Distanza (km)", 0.1, 50.0, 10.0)
        grad = st.number_input("Pendenza (%)", 0.0, 20.0, 7.0)
        bike_w = st.number_input("Peso Bici (kg)", 5.0, 15.0, 8.0)

    if st.button("🚀 GENERA ANALISI"):
        bmi = NutritionScience.get_bmi(peso, altezza_cm/100)
        t_att = NutritionScience.estimate_time(ftp, peso, dist_km, grad, bike_w)
        t_tar = NutritionScience.estimate_time(ftp_t, peso_t, dist_km, grad, bike_w)
        giudizio = NutritionScience.get_clinical_judgment(profilo, bmi, fm, fm_t)
        
        st.session_state['res'] = {
            'nome': nome, 'cognome': cognome, 'data': data_visita.isoformat(),
            'peso': peso, 'fm': fm, 'ftp': ftp, 'lthr': lthr, 'bmi': bmi,
            'peso_t': peso_t, 'fm_t': fm_t, 'ftp_t': ftp_t, 'prof': profilo,
            't_att': t_att, 't_tar': t_tar, 'dist': dist_km, 'grad': grad, 'bike': bike_w,
            'giudizio': giudizio
        }

    if 'res' in st.session_state:
        r = st.session_state['res']
        pz, hz = NutritionScience.get_zones(r['ftp_t'], r['lthr'])
        
        st.divider()
        st.subheader("📊 Output Professionale")
        
        # 1. ZONE TARGET
        zc1, zc2 = st.columns(2)
        with zc1:
            st.write("### ⚡ Zone Potenza Target")
            st.table(pd.DataFrame(pz, columns=["Zona", "Min (W)", "Max (W)"]))
        with zc2:
            st.write("### ❤️ Zone Cardio Target")
            st.table(pd.DataFrame(hz, columns=["Zona", "Min (bpm)", "Max (bpm)"]))

        # 2. GIUDIZIO NUTRIZIONALE
        st.info(f"**Valutazione Clinica:**\n\n{r['giudizio']}")

        # 3. ANALISI PERFORMANCE
        st.write("### 🏔️ Analisi Performance in Salita")
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Tempo Prima", f"{r['t_att']:.2f} min")
        c_m2.metric("Tempo Dopo", f"{r['t_tar']:.2f} min")
        c_m3.metric("Differenza", f"-{r['t_att']-r['t_tar']:.2f} min", delta_color="normal")

        # 4. DOWNLOAD E SALVATAGGIO
        st.divider()
        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("💾 SALVA IN ARCHIVIO"):
                conn = sqlite3.connect("performance_lab.db"); c = conn.cursor()
                c.execute("INSERT INTO atleti (nome, cognome, profilo) VALUES (?,?,?)", (r['nome'], r['cognome'], r['prof']))
                a_id = c.lastrowid
                c.execute("""INSERT INTO visite (atleta_id, data, peso, fm, ftp, lthr, peso_t, fm_t, ftp_t, t_att, t_tar, dist_km, grad, bike_w) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                          (a_id, r['data'], r['peso'], r['fm'], r['ftp'], r['lthr'], r['peso_t'], r['fm_t'], r['ftp_t'], r['t_att'], r['t_tar'], r['dist'], r['grad'], r['bike']))
                conn.commit(); conn.close(); st.success("Dati archiviati con successo!")

        with sc2:
            pdf = FPDF()
            pdf.add_page()
            if os.path.exists(LOGO_PATH): pdf.image(LOGO_PATH, x=150, y=8, w=40)
            pdf.set_font("Arial", 'B', 16); pdf.cell(130, 10, pdf_safe(f"REPORT: {r['nome']} {r['cognome']}"), 0, 1)
            pdf.set_font("Arial", '', 10); pdf.cell(130, 7, f"Data Visita: {r['data']}", 0, 1); pdf.ln(10)

            # Zone
            pdf.set_fill_color(220, 220, 220); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "1. ZONE DI ALLENAMENTO TARGET", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 10)
            for i in range(5):
                pdf.cell(95, 8, pdf_safe(f"{pz[i][0]}: {pz[i][1]}-{pz[i][2]} W"), 1, 0)
                pdf.cell(95, 8, pdf_safe(f"{hz[i][0]}: {hz[i][1]}-{hz[i][2]} bpm"), 1, 1)
            
            # Giudizio
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "2. VALUTAZIONE NUTRIZIONALE E COMPOSIZIONE CORPOREA", 0, 1)
            pdf.set_font("Arial", '', 11); pdf.multi_cell(190, 7, pdf_safe(r['giudizio']))

            # Performance
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "3. ANALISI DELLA PERFORMANCE IN SALITA", 0, 1)
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(190, 7, pdf_safe(f"Scenario: {r['dist']} km al {r['grad']}% con {r['bike']} kg di bici."))
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(60, 10, "Tempo Stato Attuale", 1); pdf.cell(130, 10, f"{r['t_att']:.2f} minuti", 1, 1, 'C')
            pdf.cell(60, 10, "Tempo Stato Target", 1); pdf.cell(130, 10, f"{r['t_tar']:.2f} minuti", 1, 1, 'C')
            pdf.set_fill_color(200, 255, 200)
            pdf.cell(60, 10, "MIGLIORAMENTO", 1, 0, 'L', True); pdf.cell(130, 10, f"-{r['t_att']-r['t_tar']:.2f} minuti", 1, 1, 'C', True)

            st.download_button("📄 SCARICA PDF", data=pdf.output(dest='S').encode('latin-1', 'replace'), file_name=f"Report_{r['cognome']}.pdf")

elif menu == "Archivio Atleti":
    st.header("📂 Gestione Storico")
    conn = sqlite3.connect("performance_lab.db")
    atleti = pd.read_sql_query("SELECT * FROM atleti", conn)
    if not atleti.empty:
        sel = st.selectbox("Atleta", atleti.apply(lambda x: f"{x['id']} - {x['nome']} {x['cognome']}", axis=1))
        a_id = sel.split(" - ")[0]
        st.dataframe(pd.read_sql_query(f"SELECT * FROM visite WHERE atleta_id={a_id}", conn))
    else: st.info("Archivio vuoto.")
