import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from fpdf import FPDF
import os

# ---------------------------------------------------------
# CONFIGURAZIONE GENERALE
# ---------------------------------------------------------
st.set_page_config(
    page_title="DB Nutrition Performance",
    layout="wide",
    page_icon="🧬"
)

DB_NAME = "performance_lab_pro.db"
LOGO_PATH = "Logo NUTRITION AND PERFORMANCE.png"


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------
def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    with get_connection() as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS atleti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cognome TEXT NOT NULL,
                altezza REAL,
                profilo TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS visite (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                atleta_id INTEGER,
                data TEXT,
                peso REAL,
                fm REAL,
                ftp REAL,
                lthr INTEGER,
                peso_t REAL,
                fm_t REAL,
                ftp_t REAL,
                dist_km REAL,
                grad REAL,
                bike_w REAL,
                t_att REAL,
                t_tar REAL,
                FOREIGN KEY(atleta_id) REFERENCES atleti(id)
            )
        """)

        # Migrazione automatica database già esistente
        c.execute("PRAGMA table_info(visite)")
        colonne_visite = [col[1] for col in c.fetchall()]

        if "wkg_att" not in colonne_visite:
            c.execute("ALTER TABLE visite ADD COLUMN wkg_att REAL")

        if "wkg_tar" not in colonne_visite:
            c.execute("ALTER TABLE visite ADD COLUMN wkg_tar REAL")

        conn.commit()


init_db()


# ---------------------------------------------------------
# MOTORE SCIENTIFICO
# ---------------------------------------------------------
class BioPerformance:

    @staticmethod
    def calculate_ftp(tipo, valore):
        mapping = {
            "Manuale": 1.00,
            "Test 20'": 0.95,
            "Test 8'": 0.90,
            "Incrementale": 0.75
        }
        return float(valore) * mapping.get(tipo, 1.00)

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        try:
            watt = float(watt)
            peso = float(peso)
            km = float(km)
            pend = float(pend)
            bike_w = float(bike_w)

            if watt <= 0 or peso <= 0 or km <= 0:
                return 0

            f_res = (peso + bike_w) * 9.81 * ((pend / 100) + 0.005)

            if f_res <= 0:
                return 0

            speed_ms = watt / f_res
            tempo_min = (km * 1000 / speed_ms) / 60

            return tempo_min

        except Exception:
            return 0

    @staticmethod
    def get_power_zones_coggan(ftp):
        ftp = float(ftp)

        return [
            ("Z1 Recupero", 0, round(ftp * 0.55)),
            ("Z2 Endurance", round(ftp * 0.56), round(ftp * 0.75)),
            ("Z3 Tempo", round(ftp * 0.76), round(ftp * 0.90)),
            ("Z4 Soglia", round(ftp * 0.91), round(ftp * 1.05)),
            ("Z5 VO2max", round(ftp * 1.06), round(ftp * 1.20)),
            ("Z6 Capacità anaerobica", round(ftp * 1.21), round(ftp * 1.50)),
            ("Z7 Neuromuscolare", round(ftp * 1.51), "> " + str(round(ftp * 1.50)))
        ]

    @staticmethod
    def get_hr_zones_fthr(fthr):
        fthr = int(fthr)

        return [
            ("Z1 Recupero", 0, round(fthr * 0.80)),
            ("Z2 Endurance", round(fthr * 0.81), round(fthr * 0.89)),
            ("Z3 Tempo", round(fthr * 0.90), round(fthr * 0.93)),
            ("Z4 Soglia", round(fthr * 0.94), round(fthr * 0.99)),
            ("Z5 Sopra soglia", round(fthr * 1.00), "> " + str(round(fthr * 1.00)))
        ]

    @staticmethod
    def get_category_benchmarks():
        data = [
            ["World Tour", "5–7%", "6.0–6.5", 65],
            ["Pro Continental", "7–9%", "5.5–6.0", 68],
            ["Elite / U23", "8–11%", "4.5–5.5", 70],
            ["Amatore Top", "10–14%", "3.5–4.5", 72],
            ["Cicloturista", ">15%", "<3.0", 78]
        ]

        return pd.DataFrame(
            data,
            columns=["Categoria", "Range FM %", "W/kg soglia", "Peso medio kg"]
        )


# ---------------------------------------------------------
# FUNZIONI DI SUPPORTO
# ---------------------------------------------------------
def pdf_safe(text):
    if text is None:
        return ""

    text = str(text)

    replacements = {
        "à": "a",
        "è": "e",
        "é": "e",
        "ì": "i",
        "ò": "o",
        "ù": "u",
        "À": "A",
        "È": "E",
        "É": "E",
        "Ì": "I",
        "Ò": "O",
        "Ù": "U",
        "²": "2",
        "₂": "2",
        "VO₂": "VO2",
        "–": "-",
        "→": "->",
        "≥": ">=",
        "≤": "<=",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.encode("latin-1", "replace").decode("latin-1")


def get_all_atleti():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM atleti ORDER BY cognome ASC, nome ASC",
            conn
        )


def salva_visita(r):
    nome = r["nome"].strip()
    cognome = r["cognome"].strip()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM atleti WHERE LOWER(nome)=LOWER(?) AND LOWER(cognome)=LOWER(?)",
            (nome, cognome)
        )
        row = cursor.fetchone()

        if row:
            atleta_id = row[0]

            cursor.execute(
                """
                UPDATE atleti
                SET altezza=?, profilo=?
                WHERE id=?
                """,
                (r["altezza"], r["profilo"], atleta_id)
            )

        else:
            cursor.execute(
                """
                INSERT INTO atleti (nome, cognome, altezza, profilo)
                VALUES (?, ?, ?, ?)
                """,
                (nome, cognome, r["altezza"], r["profilo"])
            )

            atleta_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO visite (
                atleta_id, data, peso, fm, ftp, lthr,
                peso_t, fm_t, ftp_t,
                dist_km, grad, bike_w,
                t_att, t_tar, wkg_att, wkg_tar
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                atleta_id,
                r["data_iso"],
                r["peso_att"],
                r["fm_att"],
                r["ftp_att"],
                r["lthr"],
                r["peso_tar"],
                r["fm_tar"],
                r["ftp_tar"],
                r["dist"],
                r["grad"],
                r["bike"],
                r["tempo_att"],
                r["tempo_tar"],
                r["wkg_att"],
                r["wkg_tar"]
            )
        )

        conn.commit()


def aggiorna_atleta(atleta_id, nome, cognome, altezza, profilo):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE atleti
            SET nome=?, cognome=?, altezza=?, profilo=?
            WHERE id=?
            """,
            (nome.strip(), cognome.strip(), altezza, profilo, atleta_id)
        )
        conn.commit()


def aggiorna_visita(
    visita_id,
    peso,
    fm,
    ftp,
    lthr,
    peso_t,
    fm_t,
    ftp_t,
    dist_km,
    grad,
    bike_w
):
    t_att = BioPerformance.estimate_time(ftp, peso, dist_km, grad, bike_w)
    t_tar = BioPerformance.estimate_time(ftp_t, peso_t, dist_km, grad, bike_w)

    wkg_att = ftp / peso if peso > 0 else 0
    wkg_tar = ftp_t / peso_t if peso_t > 0 else 0

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE visite
            SET peso=?,
                fm=?,
                ftp=?,
                lthr=?,
                peso_t=?,
                fm_t=?,
                ftp_t=?,
                dist_km=?,
                grad=?,
                bike_w=?,
                t_att=?,
                t_tar=?,
                wkg_att=?,
                wkg_tar=?
            WHERE id=?
            """,
            (
                peso,
                fm,
                ftp,
                lthr,
                peso_t,
                fm_t,
                ftp_t,
                dist_km,
                grad,
                bike_w,
                t_att,
                t_tar,
                wkg_att,
                wkg_tar,
                visita_id
            )
        )
        conn.commit()


def create_pdf(r):
    pdf = FPDF()
    pdf.add_page()

    if os.path.exists(LOGO_PATH):
        try:
            pdf.image(LOGO_PATH, 10, 8, 45)
            pdf.ln(30)
        except Exception:
            pdf.ln(10)
    else:
        pdf.ln(10)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(
        0,
        10,
        pdf_safe(f"REPORT PERFORMANCE: {r['nome']} {r['cognome']}"),
        0,
        1,
        "C"
    )

    pdf.set_font("Arial", "", 11)
    pdf.cell(
        0,
        7,
        pdf_safe(f"Data: {r['data']} | Profilo: {r['profilo']} | Altezza: {r['altezza']} cm"),
        0,
        1,
        "C"
    )

    pdf.ln(8)

    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "1. PARAMETRI ANTROPOMETRICI", 1, 1, "L", True)

    pdf.set_font("Arial", "", 10)
    pdf.cell(63, 8, pdf_safe(f"Peso attuale: {r['peso_att']:.1f} kg"), 1)
    pdf.cell(63, 8, pdf_safe(f"FM attuale: {r['fm_att']:.1f}%"), 1)
    pdf.cell(64, 8, pdf_safe(f"BMI attuale: {r['bmi_att']:.1f}"), 1, 1)

    pdf.cell(63, 8, pdf_safe(f"Peso target: {r['peso_tar']:.1f} kg"), 1)
    pdf.cell(63, 8, pdf_safe(f"FM target: {r['fm_tar']:.1f}%"), 1)
    pdf.cell(64, 8, pdf_safe(f"BMI target: {r['bmi_tar']:.1f}"), 1, 1)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "2. VALUTAZIONE FUNZIONALE", 1, 1, "L", True)

    pdf.set_font("Arial", "", 10)
    pdf.cell(63, 8, pdf_safe(f"Protocollo: {r['tipo_test']}"), 1)
    pdf.cell(63, 8, pdf_safe(f"FTP attuale: {r['ftp_att']:.0f} W"), 1)
    pdf.cell(64, 8, pdf_safe(f"FTP target: {r['ftp_tar']:.0f} W"), 1, 1)

    pdf.cell(63, 8, pdf_safe(f"W/kg attuale: {r['wkg_att']:.2f}"), 1)
    pdf.cell(63, 8, pdf_safe(f"W/kg target: {r['wkg_tar']:.2f}"), 1)
    pdf.cell(64, 8, pdf_safe(f"Delta W/kg: {r['wkg_delta']:+.2f}"), 1, 1)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "3. SCENARIO SALITA", 1, 1, "L", True)

    pdf.set_font("Arial", "", 10)
    pdf.cell(
        0,
        8,
        pdf_safe(f"Parametri: {r['dist']:.1f} km | {r['grad']:.1f}% | Bici {r['bike']:.1f} kg"),
        1,
        1
    )

    pdf.cell(95, 8, pdf_safe(f"Tempo attuale: {r['tempo_att']:.2f} min"), 1)
    pdf.cell(95, 8, pdf_safe(f"Tempo target: {r['tempo_tar']:.2f} min"), 1, 1)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, pdf_safe(f"Differenza: {r['tempo_delta']:+.2f} min"), 1, 1, "C")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "4. ZONE DI POTENZA - FTP ATTUALE", 1, 1, "L", True)

    pdf.set_font("Arial", "B", 9)
    pdf.cell(80, 7, "Zona", 1)
    pdf.cell(55, 7, "Watt Min", 1)
    pdf.cell(55, 7, "Watt Max", 1, 1)

    pdf.set_font("Arial", "", 9)
    for z in r["zones_power_att"]:
        pdf.cell(80, 7, pdf_safe(z[0]), 1)
        pdf.cell(55, 7, str(z[1]), 1)
        pdf.cell(55, 7, str(z[2]), 1, 1)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "5. ZONE DI POTENZA - FTP TARGET", 1, 1, "L", True)

    pdf.set_font("Arial", "B", 9)
    pdf.cell(80, 7, "Zona", 1)
    pdf.cell(55, 7, "Watt Min", 1)
    pdf.cell(55, 7, "Watt Max", 1, 1)

    pdf.set_font("Arial", "", 9)
    for z in r["zones_power_tar"]:
        pdf.cell(80, 7, pdf_safe(z[0]), 1)
        pdf.cell(55, 7, str(z[1]), 1)
        pdf.cell(55, 7, str(z[2]), 1, 1)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "6. ZONE CARDIACHE - FTHR / LTHR", 1, 1, "L", True)

    pdf.set_font("Arial", "B", 9)
    pdf.cell(80, 7, "Zona", 1)
    pdf.cell(55, 7, "BPM Min", 1)
    pdf.cell(55, 7, "BPM Max", 1, 1)

    pdf.set_font("Arial", "", 9)
    for z in r["zones_hr"]:
        pdf.cell(80, 7, pdf_safe(z[0]), 1)
        pdf.cell(55, 7, str(z[1]), 1)
        pdf.cell(55, 7, str(z[2]), 1, 1)

    return pdf.output(dest="S").encode("latin-1", "ignore")


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)

    st.markdown("---")

    menu = st.radio(
        "NAVIGAZIONE",
        [
            "➕ Nuova Valutazione",
            "📂 Archivio & Edit"
        ]
    )


# ---------------------------------------------------------
# NUOVA VALUTAZIONE
# ---------------------------------------------------------
if menu == "➕ Nuova Valutazione":

    st.header("📋 Inserimento Protocollo Valutazione")

    with st.container(border=True):
        st.subheader("👤 Anagrafica atleta")

        c1, c2, c3, c4 = st.columns([2, 2, 1, 2])

        cognome = c1.text_input(
            "Cognome",
            value="",
            key="cognome_input"
        ).strip()

        nome = c2.text_input(
            "Nome",
            value="",
            key="nome_input"
        ).strip()

        altezza = c3.number_input(
            "Altezza (cm)",
            min_value=120,
            max_value=230,
            value=175,
            step=1,
            key="altezza_input"
        )

        profilo = c4.selectbox(
            "Profilo atleta",
            ["Scalatore", "Passista", "Triatleta", "Granfondista", "Altro"],
            key="profilo_input"
        )

        data_visita = st.date_input(
            "Data analisi",
            value=date.today(),
            key="data_visita_input"
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📊 1. Stato attuale")

        p_att = st.number_input(
            "Peso attuale (kg)",
            min_value=40.0,
            max_value=150.0,
            value=70.0,
            step=0.1,
            key="p_att_input"
        )

        fm_att = st.number_input(
            "FM attuale (%)",
            min_value=3.0,
            max_value=45.0,
            value=15.0,
            step=0.1,
            key="fm_att_input"
        )

        tipo_test = st.selectbox(
            "Tipo test FTP",
            ["Manuale", "Test 20'", "Test 8'", "Incrementale"],
            key="tipo_test_input"
        )

        val_test = st.number_input(
            "Watt test / FTP manuale",
            min_value=50,
            max_value=700,
            value=250,
            step=1,
            key="val_test_input"
        )

        ftp_att = BioPerformance.calculate_ftp(tipo_test, val_test)

        lthr = st.number_input(
            "FTHR / LTHR (bpm)",
            min_value=80,
            max_value=220,
            value=160,
            step=1,
            key="lthr_input"
        )

        bmi_att = p_att / ((altezza / 100) ** 2)

    with col2:
        st.subheader("🎯 2. Target")

        p_tar = st.number_input(
            "Peso target (kg)",
            min_value=40.0,
            max_value=150.0,
            value=68.0,
            step=0.1,
            key="p_tar_input"
        )

        fm_tar = st.number_input(
            "FM target (%)",
            min_value=3.0,
            max_value=40.0,
            value=10.0,
            step=0.1,
            key="fm_tar_input"
        )

        ftp_tar = st.number_input(
            "FTP target (W)",
            min_value=50,
            max_value=700,
            value=280,
            step=1,
            key="ftp_tar_input"
        )

        bmi_tar = p_tar / ((altezza / 100) ** 2)

    with col3:
        st.subheader("🏔️ 3. Scenario salita")

        dist = st.number_input(
            "Km salita",
            min_value=0.1,
            max_value=50.0,
            value=10.0,
            step=0.1,
            key="dist_input"
        )

        grad = st.number_input(
            "Pendenza media (%)",
            min_value=0.0,
            max_value=25.0,
            value=7.0,
            step=0.1,
            key="grad_input"
        )

        bike = st.number_input(
            "Peso bici (kg)",
            min_value=5.0,
            max_value=20.0,
            value=7.5,
            step=0.1,
            key="bike_input"
        )

    if st.button("🚀 ELABORA E STAMPA OUTPUT", use_container_width=True):

        if not nome or not cognome:
            st.error("Inserire nome e cognome prima di elaborare.")
            st.stop()

        tempo_att = BioPerformance.estimate_time(
            ftp_att,
            p_att,
            dist,
            grad,
            bike
        )

        tempo_tar = BioPerformance.estimate_time(
            ftp_tar,
            p_tar,
            dist,
            grad,
            bike
        )

        wkg_att = ftp_att / p_att
        wkg_tar = ftp_tar / p_tar
        wkg_delta = wkg_tar - wkg_att

        st.session_state["rep"] = {
            "nome": nome,
            "cognome": cognome,
            "altezza": altezza,
            "profilo": profilo,
            "data": data_visita.strftime("%d/%m/%Y"),
            "data_iso": data_visita.isoformat(),

            "peso_att": p_att,
            "fm_att": fm_att,
            "ftp_att": ftp_att,
            "lthr": lthr,
            "bmi_att": bmi_att,
            "tipo_test": tipo_test,

            "peso_tar": p_tar,
            "fm_tar": fm_tar,
            "ftp_tar": ftp_tar,
            "bmi_tar": bmi_tar,

            "dist": dist,
            "grad": grad,
            "bike": bike,

            "tempo_att": tempo_att,
            "tempo_tar": tempo_tar,
            "tempo_delta": tempo_tar - tempo_att,

            "wkg_att": wkg_att,
            "wkg_tar": wkg_tar,
            "wkg_delta": wkg_delta,

            "zones_power_att": BioPerformance.get_power_zones_coggan(ftp_att),
            "zones_power_tar": BioPerformance.get_power_zones_coggan(ftp_tar),
            "zones_hr": BioPerformance.get_hr_zones_fthr(lthr)
        }

    if "rep" in st.session_state:
        r = st.session_state["rep"]

        if "peso_att" not in r:
            del st.session_state["rep"]
            st.warning("Memoria precedente eliminata. Reinserire i dati e premere nuovamente ELABORA.")
            st.stop()

        st.divider()
        st.subheader("🧬 Analisi Biometrica e Funzionale")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "Peso",
                f"{r['peso_att']:.1f} kg",
                f"Target: {r['peso_tar']:.1f} kg"
            )
            st.write(
                f"**BMI:** {r['bmi_att']:.1f} → **{r['bmi_tar']:.1f}**"
            )

        with c2:
            fm_kg_att = r["peso_att"] * (r["fm_att"] / 100)
            fm_kg_tar = r["peso_tar"] * (r["fm_tar"] / 100)

            st.metric(
                "FM %",
                f"{r['fm_att']:.1f} %",
                f"Target: {r['fm_tar']:.1f} %"
            )
            st.write(
                f"**Massa grassa:** {fm_kg_att:.1f} kg → **{fm_kg_tar:.1f} kg**"
            )

        with c3:
            st.metric(
                "FTP attuale",
                f"{r['ftp_att']:.0f} W",
                f"Target: {r['ftp_tar']:.0f} W"
            )
            st.write(
                f"**Protocollo:** {r['tipo_test']}"
            )

        with c4:
            st.metric(
                "Rapporto W/kg",
                f"{r['wkg_att']:.2f}",
                f"Target: {r['wkg_tar']:.2f}"
            )
            st.write(
                f"**Delta:** {r['wkg_delta']:+.2f} W/kg"
            )

        st.subheader("🏔️ Analisi Scenario Salita")

        s1, s2 = st.columns(2)

        with s1:
            st.info(
                f"**Input:** {r['dist']:.1f} km | "
                f"{r['grad']:.1f}% | "
                f"Bici {r['bike']:.1f} kg"
            )

        with s2:
            st.success(
                f"**Tempo attuale:** {r['tempo_att']:.2f} min  \n"
                f"**Tempo target:** {r['tempo_tar']:.2f} min  \n"
                f"**Differenza:** {r['tempo_delta']:+.2f} min"
            )

        st.subheader("⚡ Zone di Potenza Coggan - FTP attuale")

        st.table(
            pd.DataFrame(
                r["zones_power_att"],
                columns=["Zona", "Watt Min", "Watt Max"]
            )
        )

        st.subheader("🎯 Zone di Potenza Coggan - FTP target")

        st.table(
            pd.DataFrame(
                r["zones_power_tar"],
                columns=["Zona", "Watt Min", "Watt Max"]
            )
        )

        st.subheader("❤️ Zone Cardiache su FTHR / LTHR")

        st.table(
            pd.DataFrame(
                r["zones_hr"],
                columns=["Zona", "BPM Min", "BPM Max"]
            )
        )

        st.subheader("🏁 Benchmark di Categoria")

        st.table(BioPerformance.get_category_benchmarks())

        save_col, pdf_col = st.columns(2)

        with save_col:
            if st.button("💾 SALVA IN ARCHIVIO", use_container_width=True):

                if not r["nome"].strip() or not r["cognome"].strip():
                    st.error("Nome e cognome obbligatori per il salvataggio.")
                    st.stop()

                salva_visita(r)
                st.success(
                    f"Valutazione di {r['nome']} {r['cognome']} salvata correttamente in archivio."
                )

        with pdf_col:
            pdf_bytes = create_pdf(r)

            st.download_button(
                "📄 SCARICA PDF COMPLETO",
                data=pdf_bytes,
                file_name=f"Analisi_{r['cognome']}_{r['nome']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )


# ---------------------------------------------------------
# ARCHIVIO
# ---------------------------------------------------------
elif menu == "📂 Archivio & Edit":

    st.header("🗄️ Gestione Archivio")

    atleti = get_all_atleti()

    if atleti.empty:
        st.info("Nessun atleta presente in archivio.")

    else:
        atleti["label"] = atleti.apply(
            lambda x: f"{x['id']} - {x['cognome']} {x['nome']}",
            axis=1
        )

        selected = st.selectbox(
            "Seleziona atleta",
            atleti["label"].tolist()
        )

        atleta_id = int(selected.split(" - ")[0])

        atleta_row = atleti[atleti["id"] == atleta_id].iloc[0]

        st.subheader(
            f"👤 {atleta_row['cognome']} {atleta_row['nome']}"
        )

        st.write(
            f"**Altezza:** {atleta_row['altezza']} cm  \n"
            f"**Profilo:** {atleta_row['profilo']}"
        )

        st.divider()
        st.subheader("🧾 Modifica dati anagrafici atleta")

        col_a1, col_a2, col_a3, col_a4 = st.columns([2, 2, 1, 2])

        edit_cognome = col_a1.text_input(
            "Cognome atleta",
            value=str(atleta_row["cognome"]),
            key=f"edit_cognome_{atleta_id}"
        )

        edit_nome = col_a2.text_input(
            "Nome atleta",
            value=str(atleta_row["nome"]),
            key=f"edit_nome_{atleta_id}"
        )

        edit_altezza = col_a3.number_input(
            "Altezza atleta (cm)",
            min_value=120,
            max_value=230,
            value=int(atleta_row["altezza"]) if pd.notna(atleta_row["altezza"]) else 175,
            step=1,
            key=f"edit_altezza_{atleta_id}"
        )

        edit_profilo = col_a4.selectbox(
            "Profilo atleta",
            ["Scalatore", "Passista", "Triatleta", "Granfondista", "Altro"],
            index=["Scalatore", "Passista", "Triatleta", "Granfondista", "Altro"].index(atleta_row["profilo"])
            if atleta_row["profilo"] in ["Scalatore", "Passista", "Triatleta", "Granfondista", "Altro"]
            else 0,
            key=f"edit_profilo_{atleta_id}"
        )

        if st.button("💾 AGGIORNA ANAGRAFICA ATLETA", use_container_width=True):
            if not edit_nome.strip() or not edit_cognome.strip():
                st.error("Nome e cognome non possono essere vuoti.")
                st.stop()

            aggiorna_atleta(
                atleta_id,
                edit_nome,
                edit_cognome,
                edit_altezza,
                edit_profilo
            )

            st.success("Anagrafica atleta aggiornata correttamente.")
            st.rerun()

        with get_connection() as conn:
            visite = pd.read_sql_query(
                """
                SELECT 
                    id,
                    data,
                    peso,
                    fm,
                    ftp,
                    lthr,
                    peso_t,
                    fm_t,
                    ftp_t,
                    dist_km,
                    grad,
                    bike_w,
                    t_att,
                    t_tar,
                    wkg_att,
                    wkg_tar
                FROM visite
                WHERE atleta_id=?
                ORDER BY data DESC, id DESC
                """,
                conn,
                params=(atleta_id,)
            )

        st.divider()
        st.subheader("📋 Visite salvate")

        if visite.empty:
            st.warning("Nessuna visita registrata per questo atleta.")

        else:
            st.dataframe(
                visite,
                hide_index=True,
                use_container_width=True
            )

            st.divider()
            st.subheader("✏️ Modifica visita salvata e sovrascrivi")

            visita_id = st.selectbox(
                "Seleziona ID visita da modificare",
                visite["id"].tolist(),
                key="visita_modifica_id"
            )

            visita_sel = visite[visite["id"] == visita_id].iloc[0]

            colm1, colm2, colm3 = st.columns(3)

            with colm1:
                nuovo_peso = st.number_input(
                    "Peso attuale (kg)",
                    min_value=40.0,
                    max_value=150.0,
                    value=float(visita_sel["peso"]),
                    step=0.1,
                    key=f"edit_peso_{visita_id}"
                )

                nuova_fm = st.number_input(
                    "FM attuale (%)",
                    min_value=3.0,
                    max_value=45.0,
                    value=float(visita_sel["fm"]),
                    step=0.1,
                    key=f"edit_fm_{visita_id}"
                )

                nuova_ftp = st.number_input(
                    "FTP attuale (W)",
                    min_value=50,
                    max_value=700,
                    value=int(visita_sel["ftp"]),
                    step=1,
                    key=f"edit_ftp_{visita_id}"
                )

                nuova_lthr = st.number_input(
                    "FTHR / LTHR (bpm)",
                    min_value=80,
                    max_value=220,
                    value=int(visita_sel["lthr"]),
                    step=1,
                    key=f"edit_lthr_{visita_id}"
                )

            with colm2:
                nuovo_peso_t = st.number_input(
                    "Peso target (kg)",
                    min_value=40.0,
                    max_value=150.0,
                    value=float(visita_sel["peso_t"]),
                    step=0.1,
                    key=f"edit_peso_t_{visita_id}"
                )

                nuova_fm_t = st.number_input(
                    "FM target (%)",
                    min_value=3.0,
                    max_value=40.0,
                    value=float(visita_sel["fm_t"]),
                    step=0.1,
                    key=f"edit_fm_t_{visita_id}"
                )

                nuova_ftp_t = st.number_input(
                    "FTP target (W)",
                    min_value=50,
                    max_value=700,
                    value=int(visita_sel["ftp_t"]),
                    step=1,
                    key=f"edit_ftp_t_{visita_id}"
                )

            with colm3:
                nuova_dist = st.number_input(
                    "Km salita",
                    min_value=0.1,
                    max_value=50.0,
                    value=float(visita_sel["dist_km"]),
                    step=0.1,
                    key=f"edit_dist_{visita_id}"
                )

                nuova_grad = st.number_input(
                    "Pendenza media (%)",
                    min_value=0.0,
                    max_value=25.0,
                    value=float(visita_sel["grad"]),
                    step=0.1,
                    key=f"edit_grad_{visita_id}"
                )

                nuova_bike = st.number_input(
                    "Peso bici (kg)",
                    min_value=5.0,
                    max_value=20.0,
                    value=float(visita_sel["bike_w"]),
                    step=0.1,
                    key=f"edit_bike_{visita_id}"
                )

            nuovo_t_att = BioPerformance.estimate_time(
                nuova_ftp,
                nuovo_peso,
                nuova_dist,
                nuova_grad,
                nuova_bike
            )

            nuovo_t_tar = BioPerformance.estimate_time(
                nuova_ftp_t,
                nuovo_peso_t,
                nuova_dist,
                nuova_grad,
                nuova_bike
            )

            nuovo_wkg_att = nuova_ftp / nuovo_peso
            nuovo_wkg_tar = nuova_ftp_t / nuovo_peso_t

            st.info(
                f"Nuovo W/kg attuale: **{nuovo_wkg_att:.2f}** | "
                f"Nuovo W/kg target: **{nuovo_wkg_tar:.2f}** | "
                f"Tempo attuale: **{nuovo_t_att:.2f} min** | "
                f"Tempo target: **{nuovo_t_tar:.2f} min**"
            )

            zc1, zc2 = st.columns(2)

            with zc1:
                st.write("**Zone Coggan aggiornate - FTP attuale**")
                st.table(
                    pd.DataFrame(
                        BioPerformance.get_power_zones_coggan(nuova_ftp),
                        columns=["Zona", "Watt Min", "Watt Max"]
                    )
                )

            with zc2:
                st.write("**Zone cardiache aggiornate**")
                st.table(
                    pd.DataFrame(
                        BioPerformance.get_hr_zones_fthr(nuova_lthr),
                        columns=["Zona", "BPM Min", "BPM Max"]
                    )
                )

            if st.button("💾 AGGIORNA VISITA SELEZIONATA", use_container_width=True):
                aggiorna_visita(
                    int(visita_id),
                    nuovo_peso,
                    nuova_fm,
                    nuova_ftp,
                    nuova_lthr,
                    nuovo_peso_t,
                    nuova_fm_t,
                    nuova_ftp_t,
                    nuova_dist,
                    nuova_grad,
                    nuova_bike
                )

                st.success("Visita aggiornata e sovrascritta correttamente.")
                st.rerun()

        st.divider()
        st.subheader("🗑️ Eliminazione dati")

        delete_col1, delete_col2 = st.columns(2)

        with delete_col1:
            if st.button("🗑️ ELIMINA ATLETA E TUTTE LE VISITE", use_container_width=True):
                with get_connection() as conn:
                    conn.execute(
                        "DELETE FROM visite WHERE atleta_id=?",
                        (atleta_id,)
                    )
                    conn.execute(
                        "DELETE FROM atleti WHERE id=?",
                        (atleta_id,)
                    )
                    conn.commit()

                st.success("Atleta eliminato correttamente.")
                st.rerun()

        with delete_col2:
            if not visite.empty:
                visita_da_eliminare = st.selectbox(
                    "Seleziona visita da eliminare",
                    visite["id"].tolist(),
                    key="visita_da_eliminare"
                )

                if st.button("🗑️ ELIMINA SOLO VISITA", use_container_width=True):
                    with get_connection() as conn:
                        conn.execute(
                            "DELETE FROM visite WHERE id=?",
                            (int(visita_da_eliminare),)
                        )
                        conn.commit()

                    st.success("Visita eliminata correttamente.")
                    st.rerun()
