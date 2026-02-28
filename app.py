import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import math
import matplotlib.pyplot as plt
import os
import sqlite3

# -------------------------------
# DATABASE
# -------------------------------

def init_db(db_path="performance_lab.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS atleti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cognome TEXT,
            data_nascita TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS valutazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atleta_id INTEGER,
            data TEXT,
            peso REAL,
            fm REAL,
            bmi REAL,
            ftp REAL,
            wkg REAL,
            FOREIGN KEY (atleta_id) REFERENCES atleti(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()

# -------------------------------
# FUNZIONI UTILI
# -------------------------------

def tempo_salita(potenza, peso_atleta, lunghezza, pendenza, peso_bici):
    """Calcola il tempo (in minuti) per salire una distanza (m) a potenza costante.
    Implementazione iterativa semplice (equilibrio tra potenza e resistenze).
    """
    try:
        potenza = float(potenza)
        peso_atleta = float(peso_atleta)
    except Exception:
        return 0.0

    if potenza <= 0 or peso_atleta <= 0:
        return 0.0

    peso_tot = peso_atleta + peso_bici
    g = 9.81
    crr = 0.004
    rho = 1.226
    cda = 0.32
    efficienza = 0.97

    v = 4.0  # stima iniziale m/s
    tolleranza = 1e-4

    for _ in range(200):
        forza_grav = peso_tot * g * pendenza
        forza_roll = peso_tot * g * crr
        forza_aero = 0.5 * rho * cda * v ** 2
        forza_tot = forza_grav + forza_roll + forza_aero

        nuova_v = (potenza * efficienza) / forza_tot

        if abs(nuova_v - v) < tolleranza:
            v = nuova_v
            break

        v = nuova_v

    if v <= 0:
        return 0.0

    tempo_min = (lunghezza / v) / 60.0
    return tempo_min


def categoria_bmi_premium(bmi):
    if bmi < 18.5:
        return "Sottopeso", "#AEB6BF"
    elif bmi < 25:
        return "Normopeso", "#1F618D"
    elif bmi < 30:
        return "Sovrappeso", "#B9770E"
    else:
        return "Obesità", "#7B241C"


def salva_valutazione(nome, cognome, data_nascita, peso, fm, bmi, ftp, wkg, db_path="performance_lab.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        SELECT id FROM atleti
        WHERE nome=? AND cognome=? AND data_nascita=?
    """, (nome, cognome, str(data_nascita)))

    atleta = c.fetchone()

    if atleta:
        atleta_id = atleta[0]
    else:
        c.execute("""
            INSERT INTO atleti (nome, cognome, data_nascita)
            VALUES (?, ?, ?)
        """, (nome, cognome, str(data_nascita)))
        atleta_id = c.lastrowid

    c.execute("""
        INSERT INTO valutazioni
        (atleta_id, data, peso, fm, bmi, ftp, wkg)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        atleta_id,
        str(date.today()),
        peso,
        fm,
        bmi,
        ftp,
        wkg
    ))

    conn.commit()
    conn.close()


# -------------------------------
# STREAMLIT CONFIG
# -------------------------------

st.set_page_config(page_title="Performance Lab — Professional", layout="wide", page_icon=":bike:")

# Sidebar: controllo rapido e navigazione
st.sidebar.title("Performance Lab")
st.sidebar.write("App per valutazione antropometrica e performance ciclistica")

with st.sidebar.expander("Azioni rapide"):
    salva_btn = st.button("💾 Salva valutazione")
    pdf_btn = st.button("📄 Genera PDF")
    csv_btn = st.button("⬇️ Esporta CSV")
    reset_btn = st.button("🔁 Reset form")

st.sidebar.markdown("---")

sezione = st.sidebar.radio("Vai a:", ["Dashboard", "Valutazione", "Archivio", "Report"]) 

# Logo al centro
col1, col2, col3 = st.columns([1,2,1])
with col2:
    try:
        st.image("logo.png", width=220)
    except Exception:
        st.markdown("**Performance Lab**")

# -------------------------------
# INPUTS (nella pagina Valutazione sotto forma di form)
# -------------------------------

if sezione == "Valutazione":

    st.header("Valutazione Atleta")

    with st.form(key="valutazione_form"):
        st.subheader("Dati anagrafici")
        cols = st.columns(3)
        nome = cols[0].text_input("Nome")
        cognome = cols[1].text_input("Cognome")
        sesso = cols[2].selectbox("Sesso", ["Uomo", "Donna"]) 

        data_nascita = st.date_input("Data di nascita", min_value=date(1920,1,1), max_value=date.today(), format="DD/MM/YYYY")

        # Antropometria
        st.subheader("Antropometria")
        cols2 = st.columns(3)
        peso = cols2[0].number_input("Peso (kg)", 30.0, 200.0, value=75.0)
        altezza = cols2[1].number_input("Altezza (cm)", 100.0, 220.0, value=175.0)
        fm = cols2[2].number_input("Massa grassa (%)", 3.0, 50.0, value=12.0)

        # FTP
        st.subheader("FTP & Test")
        metodo = st.selectbox("Metodo FTP", ["Immissione diretta","Test 20 minuti","Test 8 minuti","Ramp test"]) 
        valore_test = st.number_input("Valore test (W)", 0.0)

        # Parametri allenamento
        st.subheader("Parametri allenamento")
        kcal_allenamento = st.number_input("Dispendio medio allenamento (kcal)", 0.0)

        submit = st.form_submit_button("Calcola e Mostra risultati")

    if submit:
        # Calcoli
        altezza_m = altezza / 100.0 if altezza > 0 else 0
        bmi = peso / (altezza_m**2) if altezza_m > 0 else 0
        fm_kg = peso * (fm/100.0)
        massa_magra = peso - fm_kg

        # FTP
        if metodo == "Immissione diretta":
            ftp = valore_test
        elif metodo == "Test 20 minuti":
            ftp = valore_test * 0.95
        elif metodo == "Test 8 minuti":
            ftp = valore_test * 0.90
        else:
            ftp = valore_test * 0.75

        wkg = ftp / peso if peso > 0 else 0

        # BMR
        eta = date.today().year - data_nascita.year - ((date.today().month, date.today().day) < (data_nascita.month, data_nascita.day))
        if sesso == "Uomo":
            bmr = 10*peso + 6.25*altezza - 5*eta + 5
        else:
            bmr = 10*peso + 6.25*altezza - 5*eta - 161
        bmr_cunningham = 500 + 22 * massa_magra

        # Display principale con metriche
        st.header("Sintesi")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("BMI", f"{bmi:.1f}")
        m2.metric("FTP (W)", f"{ftp:.0f}")
        m3.metric("W/kg", f"{wkg:.2f}")
        m4.metric("BMR (Cunningham)", f"{bmr_cunningham:.0f} kcal")

        # Classificazione e giudizi
        categoria_bmi = ""
        if bmi < 18.5:
            categoria_bmi = "Sottopeso"
        elif 18.5 <= bmi < 25:
            categoria_bmi = "Normopeso"
        elif 25 <= bmi < 30:
            categoria_bmi = "Sovrappeso"
        else:
            categoria_bmi = "Obesità"

        st.markdown(f"**Classificazione BMI:** {categoria_bmi}")

        # Grafici
        st.subheader("Grafici rapidi")
        fig_bmi, ax = plt.subplots(figsize=(8, 1.6))
        ax.set_xlim(15, 45)
        ax.set_ylim(0, 1)
        ax.axvspan(18.5, 25, color="#1ABC9C", ymin=0.3, ymax=0.7)
        ax.axvline(bmi, ymin=0.2, ymax=0.8, linewidth=3)
        ax.set_yticks([])
        ax.set_xticks([16,18.5,25,30,35,40])
        ax.set_xlabel("BMI")
        for spine in ["top","right","left"]:
            ax.spines[spine].set_visible(False)
        st.pyplot(fig_bmi)

        fig_fm, ax2 = plt.subplots(figsize=(8, 1.6))
        min_range = max(0, 0)
        max_range = max(30, fm + 10)
        ax2.set_xlim(min_range, max_range)
        ax2.set_ylim(0, 1)
        ax2.axvspan(6, 12, color="#1ABC9C", ymin=0.3, ymax=0.7)
        ax2.axvline(fm, ymin=0.2, ymax=0.8, linewidth=3)
        ax2.set_yticks([])
        ax2.set_xlabel("% Massa Grassa")
        for spine in ["top","right","left"]:
            ax2.spines[spine].set_visible(False)
        st.pyplot(fig_fm)

        # Zone potenza
        if ftp > 0:
            zone = [
                ("Z1 Recovery attivo",0.00,0.55),
                ("Z2 Fondo aerobico",0.56,0.75),
                ("Z3 Tempo",0.76,0.90),
                ("Z4 Soglia lattato",0.91,1.05),
                ("Z5 VO2max",1.06,1.20),
                ("Z6 Capacita anaerobica",1.21,1.50),
                ("Z7 Neuromuscolare",1.51,2.00),
            ]
            zone_df = pd.DataFrame([[z, round(a*ftp), round(b*ftp)] for z,a,b in zone], columns=["Zona","Da (W)","A (W)"])
            st.subheader("Zone Potenza")
            st.table(zone_df)
        else:
            zone_df = pd.DataFrame()

        # Pulsanti laterali contestuali
        st.sidebar.markdown("---")
        if st.sidebar.button("📥 Salva e Archivia"):
            salva_valutazione(nome, cognome, data_nascita, peso, fm, bmi, ftp, wkg)
            st.sidebar.success("Valutazione salvata")

        # Proiezione performance
        st.subheader("Simulazione Proiezione")
        nuovo_peso = st.number_input("Nuovo peso target (kg)", 0.0)
        incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0)
        if nuovo_peso > 0 and ftp > 0:
            nuova_ftp = ftp * (1 + incremento_ftp/100.0)
            nuovo_wkg = nuova_ftp / nuovo_peso
            delta_wkg = nuovo_wkg - wkg

            lunghezza = st.number_input("Lunghezza salita (m)", 5000)
            pendenza = st.number_input("Pendenza (%)", 6.0) / 100.0
            peso_bici = st.number_input("Peso bici (kg)", 8.0)

            tempo_vecchio = tempo_salita(ftp, peso, lunghezza, pendenza, peso_bici)
            tempo_nuovo = tempo_salita(nuova_ftp, nuovo_peso, lunghezza, pendenza, peso_bici)
            delta_tempo = tempo_vecchio - tempo_nuovo
            delta_percentuale = ((tempo_vecchio - tempo_nuovo) / tempo_vecchio * 100.0) if tempo_vecchio > 0 else 0.0

            st.write(f"Tempo attuale: {tempo_vecchio:.1f} min — Proiezione: {tempo_nuovo:.1f} min")
            st.write(f"Riduzione tempo: {delta_tempo:.1f} min ({delta_percentuale:.1f}%)")

        # Azioni in basso
        cola, colb, colc = st.columns([1,1,1])
        with cola:
            if st.button("📄 Genera PDF Report"):
                # Riutilizziamo la logica di generazione PDF presente nel progetto originale
                def safe(text):
                    return text.encode("latin-1", "replace").decode("latin-1")

                class PDF(FPDF):
                    def header(self):
                        try:
                            self.image("logo.png", 75, 8, 60)
                            self.ln(30)
                        except Exception:
                            self.ln(20)

                        self.set_font("Arial", "B", 18)
                        self.cell(0, 10, "REPORT PERFORMANCE", 0, 1, "C")
                        self.ln(5)

                    def section_title(self, title):
                        self.set_fill_color(230, 240, 255)
                        self.set_font("Arial", "B", 12)
                        self.cell(0, 8, title, 0, 1, "L", True)
                        self.ln(3)

                    def normal(self, text):
                        self.set_font("Arial", "", 10)
                        self.multi_cell(0, 6, safe(text))
                        self.ln(3)

                pdf = PDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)

                pdf.section_title("Dati Anagrafici")
                pdf.normal(
                    f"Nome: {nome}\n"
                    f"Cognome: {cognome}\n"
                    f"Data di nascita: {data_nascita.strftime('%d/%m/%Y')}\n"
                    f"Eta: {eta if 'eta' in locals() else ''} anni"
                )

                pdf.section_title("Antropometria")
                pdf.normal(
                    f"Peso: {peso:.1f} kg\n"
                    f"Altezza: {altezza:.1f} cm\n"
                    f"BMI: {bmi:.2f} ({categoria_bmi})\n"
                    f"Massa grassa: {fm:.1f}%\n"
                    f"Massa magra: {massa_magra:.2f} kg"
                )

                # immagini grafiche
                try:
                    fig_bmi.savefig("bmi_chart.png", dpi=300, bbox_inches='tight')
                    fig_fm.savefig("fm_chart.png", dpi=300, bbox_inches='tight')
                    pdf.image("bmi_chart.png", x=20, w=170)
                    pdf.ln(6)
                    pdf.image("fm_chart.png", x=20, w=170)
                    pdf.ln(6)
                except Exception:
                    pass

                pdf.section_title("Performance")
                pdf.normal(
                    f"Metodo FTP: {metodo}\n"
                    f"FTP calcolata: {ftp:.2f} W\n"
                    f"W/kg: {wkg:.2f}\n"
                )

                output_name = "report_performance_professionale.pdf"
                pdf.output(output_name)

                with open(output_name, "rb") as f:
                    st.download_button("Scarica PDF", f, file_name=output_name)

        with colb:
            if st.button("💾 Salva in archivio"):
                salva_valutazione(nome, cognome, data_nascita, peso, fm, bmi, ftp, wkg)
                st.success("Valutazione salvata nel database")

        with colc:
            if st.button("⬇️ Esporta dati come CSV"):
                df_export = pd.DataFrame({
                    "nome": [nome],
                    "cognome": [cognome],
                    "data_nascita": [str(data_nascita)],
                    "peso": [peso],
                    "fm": [fm],
                    "bmi": [bmi],
                    "ftp": [ftp],
                    "wkg": [wkg]
                })
                st.download_button("Scarica CSV", df_export.to_csv(index=False).encode('utf-8'), file_name="valutazione.csv", mime="text/csv")


# -------------------------------
# ARCHIVIO
# -------------------------------

elif sezione == "Archivio":
    st.header("Archivio Atleti")
    conn = sqlite3.connect("performance_lab.db")
    c = conn.cursor()
    c.execute("SELECT id, nome, cognome FROM atleti ORDER BY nome, cognome")
    lista_atleti = c.fetchall()

    if not lista_atleti:
        st.info("Nessun atleta salvato. Inserisci una valutazione nella sezione 'Valutazione'.")
    else:
        atleta_scelto = st.selectbox("Seleziona atleta", lista_atleti, format_func=lambda x: f"{x[1]} {x[2]}")
        atleta_id = atleta_scelto[0]

        df = pd.read_sql_query("SELECT * FROM valutazioni WHERE atleta_id=? ORDER BY data", conn, params=(atleta_id,))
        if df.empty:
            st.warning("Nessuna valutazione per questo atleta.")
        else:
            st.subheader("Storico valutazioni")
            st.dataframe(df)

            # grafici storici
            fig1, ax1 = plt.subplots()
            ax1.plot(df["data"], df["peso"], marker="o")
            ax1.set_title("Evoluzione Peso")
            ax1.tick_params(axis='x', rotation=45)
            st.pyplot(fig1)

            fig2, ax2 = plt.subplots()
            ax2.plot(df["data"], df["ftp"], marker="o")
            ax2.set_title("Evoluzione FTP")
            ax2.tick_params(axis='x', rotation=45)
            st.pyplot(fig2)

            # modifica
            st.subheader("Modifica visita")
            visita_scelta = st.selectbox("Seleziona visita", df["id"], format_func=lambda x: df[df["id"]==x]["data"].values[0])
            visita_corrente = df[df["id"]==visita_scelta].iloc[0]

            peso_mod = st.number_input("Peso (kg)", value=float(visita_corrente["peso"]))
            fm_mod = st.number_input("FM (%)", value=float(visita_corrente["fm"]))
            ftp_mod = st.number_input("FTP (W)", value=float(visita_corrente["ftp"]))

            if st.button("Salva modifiche visita"):
                bmi_mod = peso_mod / ((visita_corrente.get('altezza_cm', 175)/100.0)**2) if visita_corrente.get('altezza_cm', None) else peso_mod / 3.0
                wkg_mod = ftp_mod / peso_mod if peso_mod > 0 else 0
                conn.execute("""
                    UPDATE valutazioni
                    SET peso=?, fm=?, bmi=?, ftp=?, wkg=?
                    WHERE id=?
                """, (peso_mod, fm_mod, bmi_mod, ftp_mod, wkg_mod, visita_scelta))
                conn.commit()
                st.success("Visita aggiornata correttamente")

    conn.close()

# -------------------------------
# DASHBOARD
# -------------------------------

elif sezione == "Dashboard":
    st.title("Dashboard sintetica")
    conn = sqlite3.connect("performance_lab.db")
    df_all = pd.read_sql_query("SELECT v.*, a.nome, a.cognome FROM valutazioni v JOIN atleti a ON v.atleta_id=a.id ORDER BY v.data DESC", conn)
    if df_all.empty:
        st.info("Nessun dato disponibile. Inserisci valutazioni nella sezione Valutazione.")
    else:
        st.metric("Valutazioni totali", len(df_all))
        st.dataframe(df_all.head(50))

        # Top performance W/kg
        df_all['wkg'] = df_all['wkg'].astype(float)
        top = df_all.sort_values('wkg', ascending=False).head(5)
        st.subheader("Top 5 W/kg (recenti)")
        st.table(top[['nome','cognome','data','ftp','wkg']])

    conn.close()

# -------------------------------
# REPORT (sezione dedicata)
# -------------------------------

elif sezione == "Report":
    st.header("Generazione report e export")
    st.write("Scegli un atleta dall'archivio per generare report personalizzati o esportare dataset completi.")

    conn = sqlite3.connect("performance_lab.db")
    c = conn.cursor()
    c.execute("SELECT id, nome, cognome FROM atleti ORDER BY nome, cognome")
    lista_atleti = c.fetchall()

    atleta_sel = st.selectbox("Seleziona atleta (report)", [None] + lista_atleti, format_func=lambda x: "" if x is None else f"{x[1]} {x[2]}")
    if atleta_sel:
        atleta_id = atleta_sel[0]
        df = pd.read_sql_query("SELECT * FROM valutazioni WHERE atleta_id=? ORDER BY data", conn, params=(atleta_id,))
        st.dataframe(df)
        if st.button("Esporta storico CSV"):
            st.download_button("Scarica CSV storico", df.to_csv(index=False).encode('utf-8'), file_name=f"storico_atleta_{atleta_id}.csv", mime="text/csv")

    conn.close()

# Footer
st.markdown("---")
st.caption("Made with ❤️ — Performance Lab — versione professionale con UI migliorata")
