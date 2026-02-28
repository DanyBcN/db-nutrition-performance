import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import math
import matplotlib.pyplot as plt
import os
import sqlite3

def init_db():
    conn = sqlite3.connect("performance_lab.db")
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
# ======================================================
# FUNZIONE TEMPO SALITA (METTILA QUI)
# ======================================================

def tempo_salita(potenza, peso_atleta, lunghezza, pendenza, peso_bici):

    if potenza <= 0 or peso_atleta <= 0:
        return 0

    peso_tot = peso_atleta + peso_bici
    g = 9.81
    crr = 0.004
    rho = 1.226
    cda = 0.32
    efficienza = 0.97

    v = 4
    tolleranza = 0.0001

    for _ in range(100):
        forza_grav = peso_tot * g * pendenza
        forza_roll = peso_tot * g * crr
        forza_aero = 0.5 * rho * cda * v**2
        forza_tot = forza_grav + forza_roll + forza_aero

        nuova_v = (potenza * efficienza) / forza_tot

        if abs(nuova_v - v) < tolleranza:
            break

        v = nuova_v

    tempo = (lunghezza / v) / 60
    return tempo


def categoria_bmi_premium(bmi):
    if bmi < 18.5:
        return "Sottopeso", "#AEB6BF"
    elif bmi < 25:
        return "Normopeso", "#1F618D"
    elif bmi < 30:
        return "Sovrappeso", "#B9770E"
    else:
        return "Obesità", "#7B241C"

def salva_valutazione(nome, cognome, data_nascita, peso, fm, bmi, ftp, wkg):
    conn = sqlite3.connect("performance_lab.db")
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
st.set_page_config(layout="centered")

# ======================================================
# INIZIALIZZAZIONE VARIABILI
# ======================================================

ftp = 0.0
valore_test = 0.0
wkg = 0.0
nuova_ftp = 0.0
nuovo_wkg = 0.0
tempo_vecchio = 0.0
tempo_nuovo = 0.0
giudizio = ""

categoria_bmi = ""
giudizio_atleta = ""
giudizio_fm = ""

zone_df = pd.DataFrame()
zone_hr_df = pd.DataFrame()

bmr = 0.0

# ======================================================
# LOGO
# ======================================================

col1, col2, col3 = st.columns([1,2,1])
with col2:
    try:
        st.image("logo.png", width=300)
    except:
        pass

# ======================================================
# DATI ANAGRAFICI
# ======================================================

st.header("Dati Anagrafici")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")
sesso = st.selectbox("Sesso", ["Uomo", "Donna"])

data_nascita = st.date_input(
    "Data di nascita",
    min_value=date(1920,1,1),
    max_value=date.today(),
    format="DD/MM/YYYY"
)

eta = date.today().year - data_nascita.year - (
    (date.today().month, date.today().day) <
    (data_nascita.month, data_nascita.day)
)

st.markdown("---")

# ======================================================
# ANTROPOMETRIA
# ======================================================

st.header("Valutazione Antropometrica")

peso = st.number_input("Peso (kg)", 30.0, 200.0)
altezza = st.number_input("Altezza (cm)", 100.0, 220.0)
fm = st.number_input("Massa grassa (%)", 3.0, 50.0)

altezza_m = altezza / 100 if altezza > 0 else 0
bmi = peso / (altezza_m**2) if altezza_m > 0 else 0
fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg

# Classificazione OMS
if bmi < 18.5:
    categoria_bmi = "Sottopeso"
elif 18.5 <= bmi < 25:
    categoria_bmi = "Normopeso"
elif 25 <= bmi < 30:
    categoria_bmi = "Sovrappeso"
else:
    categoria_bmi = "Obesità"

st.write(f"BMI: {bmi:.2f} ({categoria_bmi})")
st.write(f"Massa grassa: {fm_kg:.2f} kg")
st.write(f"Massa magra: {massa_magra:.2f} kg")
# ======================================================
# INDICI AVANZATI COMPOSIZIONE CORPOREA
# ======================================================

st.subheader("Indici Avanzati Composizione Corporea")

ffmi = massa_magra / (altezza_m**2) if altezza_m > 0 else 0
fmi = fm_kg / (altezza_m**2) if altezza_m > 0 else 0
ratio_mm_mg = massa_magra / fm_kg if fm_kg > 0 else 0

st.write(f"FFMI (Fat Free Mass Index): {ffmi:.2f}")
st.write(f"FMI (Fat Mass Index): {fmi:.2f}")
st.write(f"Rapporto Massa Magra / Massa Grassa: {ratio_mm_mg:.2f}")
# =========================
# METABOLISMO BASALE
# =========================

if peso > 0 and altezza > 0:
    if sesso == "Uomo":
        bmr = 10*peso + 6.25*altezza - 5*eta + 5
    else:
        bmr = 10*peso + 6.25*altezza - 5*eta - 161

    st.write(f"Metabolismo basale stimato: {bmr:.0f} kcal")
# BMR Cunningham (specifico per atleta)
bmr_cunningham = 500 + 22 * massa_magra
st.write(f"BMR Cunningham: {bmr_cunningham:.0f} kcal")
# ======================================================
# FABBISOGNO ENERGETICO
# ======================================================

st.subheader("Fabbisogno Energetico")

livello_attivita = st.selectbox(
    "Livello attività",
    ["Sedentario","Moderato","Intenso","Atleta competitivo"]
)

fattori = {
    "Sedentario":1.4,
    "Moderato":1.6,
    "Intenso":1.8,
    "Atleta competitivo":2.0
}

tdee = bmr_cunningham * fattori[livello_attivita]
st.write(f"Fabbisogno energetico stimato (TDEE): {tdee:.0f} kcal")

kcal_allenamento = st.number_input("Dispendio medio allenamento (kcal)", 0.0)

energia_disponibile = (
    (tdee - kcal_allenamento) / massa_magra
    if massa_magra > 0 else 0
)

st.write(f"Disponibilità energetica: {energia_disponibile:.1f} kcal/kg FFM")

if energia_disponibile < 30:
    st.error("⚠ Possibile rischio RED-S (bassa disponibilità energetica)")
elif energia_disponibile < 45:
    st.warning("Disponibilità energetica borderline")
else:
    st.success("Disponibilità energetica ottimale")
# ======================================================
# RANGE ATLETA
# ======================================================

st.subheader("Range BMI Ideale Atleta")

tipo_sport = st.selectbox(
    "Tipologia atleta",
    ["Endurance", "Sport di squadra", "Forza/Potenza"]
)

if tipo_sport == "Endurance":
    bmi_min, bmi_max = 19, 22
    fm_min, fm_max = 6, 12
elif tipo_sport == "Sport di squadra":
    bmi_min, bmi_max = 21, 24
    fm_min, fm_max = 8, 15
else:
    bmi_min, bmi_max = 23, 27
    fm_min, fm_max = 10, 18

if bmi < bmi_min:
    giudizio_atleta = "Inferiore al range ideale atleta"
elif bmi > bmi_max:
    giudizio_atleta = "Superiore al range ideale atleta"
else:
    giudizio_atleta = "Nel range ideale atleta"

if fm < fm_min:
    giudizio_fm = "Inferiore al range ideale"
elif fm > fm_max:
    giudizio_fm = "Superiore al range ideale"
else:
    giudizio_fm = "Nel range ideale"

st.write(f"Range BMI ideale: {bmi_min}-{bmi_max}")
st.write(f"Valutazione atleta: {giudizio_atleta}")
st.write(f"Range FM ideale: {fm_min}-{fm_max}%")
st.write(f"Valutazione massa grassa: {giudizio_fm}")

# ======================================================
# GRAFICO BMI DINAMICO
# ======================================================

st.subheader("Valutazione BMI Grafica")

fig_bmi, ax = plt.subplots(figsize=(10, 2.5))

# Range totale
ax.set_xlim(15, 45)
ax.set_ylim(0, 1)

# Segmenti OMS
categorie = [
    (15, 16, "#8B0000"),
    (16, 17, "#E74C3C"),
    (17, 18.5, "#F39C12"),
    (18.5, 25, "#1ABC9C"),
    (25, 30, "#16A085"),
    (30, 35, "#F39C12"),
    (35, 40, "#E67E22"),
    (40, 45, "#C0392B"),
]

for start, end, color in categorie:
    ax.axvspan(start, end, ymin=0.3, ymax=0.7, color=color)

# Linea indicatore BMI
ax.axvline(bmi, ymin=0.2, ymax=0.8, linewidth=3)
ax.text(bmi, 0.85, f"{bmi:.1f}", ha="center", fontsize=12, fontweight="bold")

# Pulizia grafica
ax.set_yticks([])
ax.set_xticks([16,18.5,25,30,35,40])
ax.set_xlabel("BMI")

for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

plt.tight_layout()

st.pyplot(fig_bmi)
fig_bmi.savefig("bmi_chart.png", dpi=400, bbox_inches="tight")
# ======================================================
# GRAFICO MASSA GRASSA
# ======================================================
# ======================================================
# GRAFICO MASSA GRASSA DINAMICO (STILE BMI)
# ======================================================

st.subheader("Valutazione Massa Grassa")

fig_fm, ax = plt.subplots(figsize=(10, 2.2))

# Range dinamico centrato sul valore
min_range = max(0, fm_min - 5)
max_range = fm_max + 10

ax.set_xlim(min_range, max_range)
ax.set_ylim(0, 1)

# Segmenti
segmenti_fm = [
    (min_range, fm_min, "#E74C3C"),      # sotto range
    (fm_min, fm_max, "#1ABC9C"),         # ideale
    (fm_max, max_range, "#F39C12"),      # sopra range
]

for start, end, color in segmenti_fm:
    ax.axvspan(start, end, ymin=0.3, ymax=0.7, color=color)

# Indicatore valore
ax.axvline(fm, ymin=0.2, ymax=0.8, linewidth=3)
ax.text(fm, 0.85, f"{fm:.1f}%", ha="center", fontsize=12, fontweight="bold")

# Pulizia
ax.set_yticks([])
ax.set_xticks([fm_min, fm_max])
ax.set_xlabel("Percentuale Massa Grassa (%)")

for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

plt.tight_layout()

st.pyplot(fig_fm)
fig_fm.savefig("fm_chart.png", dpi=400, bbox_inches="tight")
# ======================================================
# CALCOLO FTP
# ======================================================

st.header("Calcolo FTP")

metodo = st.selectbox(
    "Metodo FTP",
    ["Immissione diretta","Test 20 minuti","Test 8 minuti","Ramp test"]
)

if metodo == "Immissione diretta":
    valore_test = st.number_input("FTP (W)", 0.0)
    ftp = valore_test
elif metodo == "Test 20 minuti":
    valore_test = st.number_input("Media 20 min (W)", 0.0)
    ftp = valore_test * 0.95
elif metodo == "Test 8 minuti":
    valore_test = st.number_input("Media 8 min (W)", 0.0)
    ftp = valore_test * 0.90
elif metodo == "Ramp test":
    valore_test = st.number_input("Ultimo step completato (W)", 0.0)
    ftp = valore_test * 0.75

wkg = ftp / peso if peso > 0 else 0

st.write(f"FTP stimata: {ftp:.2f} W")
st.write(f"W/kg: {wkg:.2f}")
# ======================================================
# INDICI PERFORMANCE AVANZATI
# ======================================================

st.subheader("Indicatori Performance Avanzati")

vo2max = (ftp / peso) * 10.8 + 7 if peso > 0 else 0
wkg_ffm = ftp / massa_magra if massa_magra > 0 else 0
cp = ftp * 1.05

st.write(f"VO2max stimato: {vo2max:.1f} ml/kg/min")
st.write(f"W/kg massa magra: {wkg_ffm:.2f}")
st.write(f"Potenza critica stimata: {cp:.0f} W")
# ======================================================
# CLASSIFICAZIONE W/kg
# ======================================================

livello_ciclista = ""

if wkg < 2.0:
    livello_ciclista = "Principiante"
elif wkg < 3.0:
    livello_ciclista = "Amatore base"
elif wkg < 4.0:
    livello_ciclista = "Amatore intermedio"
elif wkg < 5.0:
    livello_ciclista = "Amatore avanzato"
elif wkg < 6.0:
    livello_ciclista = "Elite nazionale"
else:
    livello_ciclista = "Elite internazionale"

if ftp > 0:
    st.subheader("Classificazione Livello Ciclista")
    st.write(f"Livello stimato: {livello_ciclista}")
st.markdown("---")

# ======================================================
# ZONE POTENZA
# ======================================================

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

    zone_df = pd.DataFrame(
        [[z, round(a*ftp), round(b*ftp)] for z,a,b in zone],
        columns=["Zona","Da (W)","A (W)"]
    )

    st.subheader("Zone Potenza")
    st.table(zone_df)

# ======================================================
# ZONE CARDIO
# ======================================================

st.header("Frequenza Cardiaca")

fthr = st.number_input("FTHR (bpm)", 0.0)

if fthr > 0:

    zone_hr = [
        ("Z1 Recupero",0.81,0.89),
        ("Z2 Aerobico base",0.90,0.93),
        ("Z3 Tempo",0.94,0.99),
        ("Z4 Soglia",1.00,1.05),
        ("Z5 Alta intensita",1.06,1.15),
    ]

    zone_hr_df = pd.DataFrame(
        [[z, round(a*fthr), round(b*fthr)] for z,a,b in zone_hr],
        columns=["Zona","Da (bpm)","A (bpm)"]
    )

    st.subheader("Zone Cardio")
    st.table(zone_hr_df)

st.markdown("---")
if st.button("Salva Valutazione in Archivio"):
    salva_valutazione(nome, cognome, data_nascita, peso, fm, bmi, ftp, wkg)
    st.success("Valutazione salvata nel database")
# ======================================================
# PROIEZIONE PERFORMANCE
# ======================================================

st.header("Proiezione Performance")

nuovo_peso = st.number_input("Nuovo peso target (kg)", 0.0)
incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0)

if nuovo_peso > 0 and ftp > 0:

    nuova_ftp = ftp * (1 + incremento_ftp/100)
    nuovo_wkg = nuova_ftp / nuovo_peso
    delta_wkg = nuovo_wkg - wkg

    if delta_wkg > 0.3:
        giudizio = "Miglioramento significativo"
    elif delta_wkg > 0.1:
        giudizio = "Miglioramento moderato"
    else:
        giudizio = "Miglioramento lieve"

    lunghezza = st.number_input("Lunghezza salita (m)", 5000)
    pendenza = st.number_input("Pendenza (%)", 6.0) / 100
    peso_bici = st.number_input("Peso bici (kg)", 8.0)

    tempo_vecchio = tempo_salita(ftp, peso, lunghezza, pendenza, peso_bici)
    tempo_nuovo = tempo_salita(nuova_ftp, nuovo_peso, lunghezza, pendenza, peso_bici)

    delta_tempo = tempo_vecchio - tempo_nuovo
    delta_percentuale = ((tempo_vecchio - tempo_nuovo) / tempo_vecchio) * 100

    st.subheader("Simulazione salita")

    st.write(f"Salita: {lunghezza/1000:.1f} km al {pendenza*100:.1f}%")
    st.write(f"Tempo stimato con dati attuali: {tempo_vecchio:.1f} min")
    st.write(f"Tempo stimato con peso target e nuova FTP: {tempo_nuovo:.1f} min")
    st.write(f"Miglioramento assoluto: {delta_tempo:.1f} minuti")
    st.write(f"Riduzione percentuale del tempo: {delta_percentuale:.1f}%")
    st.markdown("---")

# ======================================================
# ARCHIVIO ATLETI
# ======================================================

st.header("Archivio Atleti")

conn = sqlite3.connect("performance_lab.db")

df = None

c = conn.cursor()
c.execute("SELECT id, nome, cognome FROM atleti")
lista_atleti = c.fetchall()

if lista_atleti:

    atleta_scelto = st.selectbox(
        "Seleziona atleta",
        lista_atleti,
        format_func=lambda x: f"{x[1]} {x[2]}"
    )

    atleta_id = atleta_scelto[0]

    df = pd.read_sql_query(
        "SELECT * FROM valutazioni WHERE atleta_id=? ORDER BY data",
        conn,
        params=(atleta_id,)
    )

    if not df.empty:

        st.subheader("Storico Valutazioni")
        st.dataframe(df)

        # =========================
        # GRAFICI
        # =========================
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

        # ======================================================
        # MODIFICA VISITA
        # ======================================================

        st.subheader("Modifica Visita")

        visita_scelta = st.selectbox(
            "Seleziona visita",
            df["id"],
            format_func=lambda x: df[df["id"] == x]["data"].values[0]
        )

        visita_corrente = df[df["id"] == visita_scelta].iloc[0]

        peso_mod = st.number_input(
            "Peso (kg)", value=float(visita_corrente["peso"]), key="peso_mod"
        )

        fm_mod = st.number_input(
            "FM (%)", value=float(visita_corrente["fm"]), key="fm_mod"
        )

        ftp_mod = st.number_input(
            "FTP (W)", value=float(visita_corrente["ftp"]), key="ftp_mod"
        )

        bmi_mod = peso_mod / (altezza_m**2) if altezza_m > 0 else 0
        wkg_mod = ftp_mod / peso_mod if peso_mod > 0 else 0

        if st.button("Salva Modifiche Visita"):

            conn.execute("""
                UPDATE valutazioni
                SET peso=?, fm=?, bmi=?, ftp=?, wkg=?
                WHERE id=?
            """, (peso_mod, fm_mod, bmi_mod, ftp_mod, wkg_mod, visita_scelta))

            conn.commit()
            st.success("Visita aggiornata correttamente")

conn.close()
        # =========================
        # GRAFICO PESO
        # =========================
        fig1, ax1 = plt.subplots()
        ax1.plot(df["data"], df["peso"], marker="o")
        ax1.set_title("Evoluzione Peso")
        ax1.set_ylabel("Peso (kg)")
        ax1.tick_params(axis='x', rotation=45)
        st.pyplot(fig1)

        # =========================
        # GRAFICO FTP
        # =========================
        fig2, ax2 = plt.subplots()
        ax2.plot(df["data"], df["ftp"], marker="o")
        ax2.set_title("Evoluzione FTP")
        ax2.set_ylabel("FTP (W)")
        ax2.tick_params(axis='x', rotation=45)
        st.pyplot(fig2)

        # =========================
        # GRAFICO W/kg
        # =========================
        fig3, ax3 = plt.subplots()
        ax3.plot(df["data"], df["wkg"], marker="o")
        ax3.set_title("Evoluzione W/kg")
        ax3.set_ylabel("W/kg")
        ax3.tick_params(axis='x', rotation=45)
        st.pyplot(fig3)

conn.close()
# ======================================================
# PDF PROFESSIONALE
# ======================================================

if st.button("Genera PDF Professionale"):

    def safe(text):
        return text.encode("latin-1", "replace").decode("latin-1")

    class PDF(FPDF):
        def header(self):
            try:
                self.image("logo.png", 75, 8, 60)
                self.ln(30)
            except:
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

    # DATI
    pdf.section_title("Dati Anagrafici")
    pdf.normal(
        f"Nome: {nome}\n"
        f"Cognome: {cognome}\n"
        f"Data di nascita: {data_nascita.strftime('%d/%m/%Y')}\n"
        f"Eta: {eta} anni"
    )

    # ANTROPOMETRIA
    pdf.section_title("Antropometria")
    pdf.normal(
        f"Peso: {peso:.1f} kg\n"
        f"Altezza: {altezza:.1f} cm\n"
        f"BMI: {bmi:.2f} ({categoria_bmi})\n"
        f"Massa grassa: {fm:.1f}%\n"
        f"Massa magra: {massa_magra:.2f} kg"
    )

    # COMPOSIZIONE CORPOREA
    pdf.section_title("Composizione Corporea")

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 8, f"BMI {bmi:.1f}  |  {categoria_bmi}", 0, 1, "L")
    pdf.ln(2)
    pdf.image("bmi_chart.png", x=20, w=170)
    pdf.ln(6)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 8, f"Massa Grassa {fm:.1f}%  |  Range atleta {fm_min}-{fm_max}%", 0, 1, "L")
    pdf.ln(2)
    pdf.image("fm_chart.png", x=20, w=170)
    pdf.ln(6)

    # PERFORMANCE
    pdf.section_title("Performance")
    pdf.normal(
        f"Metodo FTP: {metodo}\n"
        f"FTP calcolata: {ftp:.2f} W\n"
        f"W/kg: {wkg:.2f}\n"
        f"Livello ciclista stimato: {livello_ciclista}"
    )

    # ZONE POTENZA
    if not zone_df.empty:
        pdf.section_title("Zone Potenza")

        pdf.set_font("Arial", "B", 10)
        pdf.cell(90, 8, "Zona", 1)
        pdf.cell(30, 8, "Da (W)", 1)
        pdf.cell(30, 8, "A (W)", 1)
        pdf.ln()

        pdf.set_font("Arial", "", 10)
        for _, row in zone_df.iterrows():
            pdf.cell(90, 8, safe(str(row["Zona"])), 1)
            pdf.cell(30, 8, str(row["Da (W)"]), 1)
            pdf.cell(30, 8, str(row["A (W)"]), 1)
            pdf.ln()

    # ZONE CARDIO
    if not zone_hr_df.empty:
        pdf.section_title("Zone Cardio")

        pdf.set_font("Arial", "B", 10)
        pdf.cell(90, 8, "Zona", 1)
        pdf.cell(30, 8, "Da (bpm)", 1)
        pdf.cell(30, 8, "A (bpm)", 1)
        pdf.ln()

        pdf.set_font("Arial", "", 10)
        for _, row in zone_hr_df.iterrows():
            pdf.cell(90, 8, safe(str(row["Zona"])), 1)
            pdf.cell(30, 8, str(row["Da (bpm)"]), 1)
            pdf.cell(30, 8, str(row["A (bpm)"]), 1)
            pdf.ln()

    # PROIEZIONE
    if nuovo_peso > 0 and ftp > 0:
        pdf.section_title("Proiezione Miglioramento")

        delta_tempo_pdf = tempo_vecchio - tempo_nuovo
        delta_percentuale_pdf = (
            (tempo_vecchio - tempo_nuovo) / tempo_vecchio * 100
            if tempo_vecchio > 0 else 0
        )

        testo_proj = (
            f"Peso attuale: {peso:.1f} kg\n"
            f"Peso target: {nuovo_peso:.1f} kg\n\n"
            f"FTP attuale: {ftp:.1f} W\n"
            f"FTP prevista: {nuova_ftp:.1f} W\n\n"
            f"W/kg attuale: {wkg:.2f}\n"
            f"W/kg previsto: {nuovo_wkg:.2f}\n\n"
            f"Miglioramento tempo salita: {delta_tempo_pdf:.1f} min ({delta_percentuale_pdf:.1f}%)"
        )

        pdf.normal(testo_proj)

    pdf.output("report_performance_professionale.pdf")

    with open("report_performance_professionale.pdf", "rb") as f:
        st.download_button(
            "Scarica PDF Professionale",
            f,
            "report_performance_professionale.pdf"
        )
