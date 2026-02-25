import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import matplotlib.pyplot as plt
import math

st.set_page_config(layout="wide")

# ======================================================
# FUNZIONI DI CALCOLO
# ======================================================

def calcola_eta(data_nascita):
    oggi = date.today()
    return oggi.year - data_nascita.year - (
        (oggi.month, oggi.day) < (data_nascita.month, data_nascita.day)
    )

def calcola_bmi(peso, altezza_cm):
    if altezza_cm <= 0:
        return 0
    h = altezza_cm / 100
    return peso / (h ** 2)

def classifica_bmi(bmi):
    if bmi < 18.5:
        return "Sottopeso"
    elif bmi < 25:
        return "Normopeso"
    elif bmi < 30:
        return "Sovrappeso"
    else:
        return "Obesità"

def calcola_ftp(metodo, valore):
    moltiplicatori = {
        "Immissione diretta": 1.0,
        "Test 20 minuti": 0.95,
        "Test 8 minuti": 0.90,
        "Ramp test": 0.75,
    }
    return valore * moltiplicatori.get(metodo, 1)

def calcola_wkg(ftp, peso):
    return ftp / peso if peso > 0 else 0

def tempo_salita_realistico(potenza, peso, lunghezza=5000, pendenza=0.06):
    g = 9.81
    rho = 1.226
    CdA = 0.32
    Crr = 0.004
    
    massa_tot = peso + 8  # bici
    forza_grav = massa_tot * g * pendenza
    forza_roll = massa_tot * g * Crr
    
    v = 5
    
    for _ in range(25):
        forza_aero = 0.5 * rho * CdA * v**2
        forza_tot = forza_grav + forza_roll + forza_aero
        v = potenza / forza_tot
    
    tempo_sec = lunghezza / v
    return tempo_sec / 60

# ======================================================
# HEADER
# ======================================================

col_logo = st.columns([1,2,1])
with col_logo[1]:
    try:
        st.image("logo.png", width=280)
    except:
        pass

st.title("REPORT PERFORMANCE PROFESSIONALE")

# ======================================================
# DATI ANAGRAFICI
# ======================================================

st.header("Dati Anagrafici")

col1, col2, col3 = st.columns(3)

with col1:
    nome = st.text_input("Nome")

with col2:
    cognome = st.text_input("Cognome")

with col3:
    data_nascita = st.date_input(
        "Data di nascita",
        min_value=date(1920,1,1),
        max_value=date.today()
    )

eta = calcola_eta(data_nascita)

st.markdown("---")

# ======================================================
# ANTROPOMETRIA
# ======================================================

st.header("Valutazione Antropometrica")

col1, col2 = st.columns(2)

with col1:
    peso = st.number_input("Peso (kg)", 30.0, 200.0)
    altezza = st.number_input("Altezza (cm)", 100.0, 220.0)

with col2:
    fm = st.number_input("Massa grassa (%)", 3.0, 50.0)

bmi = calcola_bmi(peso, altezza)
categoria_bmi = classifica_bmi(bmi)

fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("BMI", f"{bmi:.2f}", categoria_bmi)
col_m2.metric("Massa grassa (kg)", f"{fm_kg:.2f}")
col_m3.metric("Massa magra (kg)", f"{massa_magra:.2f}")

# ======================================================
# RANGE ATLETA
# ======================================================

st.subheader("Range Atleta")

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

st.write(f"Range BMI ideale: {bmi_min}-{bmi_max}")
st.write(f"Valutazione: {giudizio_atleta}")

if fm < fm_min:
    st.warning("Massa grassa sotto range fisiologico atleta.")
elif fm > fm_max:
    st.warning("Massa grassa sopra range ottimale atleta.")

# ======================================================
# GRAFICO BMI
# ======================================================

fig, ax = plt.subplots(figsize=(10, 1.8))

ax.set_xlim(15, 40)
ax.set_ylim(0, 1)

colori = [
    (15, 18.5, "#AED6F1"),
    (18.5, 25, "#ABEBC6"),
    (25, 30, "#F9E79F"),
    (30, 40, "#F5B7B1"),
]

for x1, x2, c in colori:
    ax.axvspan(x1, x2, color=c)

ax.axvspan(bmi_min, bmi_max, color="purple", alpha=0.15)

ax.axvline(bmi, linewidth=3)
ax.scatter(bmi, 0.5, s=150)

ax.set_yticks([])
ax.set_xlabel("BMI")
ax.set_title("Classificazione OMS + Range Atleta")

for spine in ax.spines.values():
    spine.set_visible(False)

st.pyplot(fig)
fig.savefig("bmi_chart.png", dpi=300, bbox_inches="tight")

# ======================================================
# FTP
# ======================================================

st.header("Calcolo FTP")

metodo = st.selectbox(
    "Metodo FTP",
    ["Immissione diretta","Test 20 minuti","Test 8 minuti","Ramp test"]
)

valore_test = st.number_input("Valore test (W)", 0.0)

ftp = calcola_ftp(metodo, valore_test)
wkg = calcola_wkg(ftp, peso)

colp1, colp2 = st.columns(2)
colp1.metric("FTP stimata", f"{ftp:.1f} W")
colp2.metric("W/kg", f"{wkg:.2f}")

# ======================================================
# ZONE POTENZA
# ======================================================

if ftp > 0:

    zone = [
        ("Z1 Recovery",0.00,0.55),
        ("Z2 Fondo",0.56,0.75),
        ("Z3 Tempo",0.76,0.90),
        ("Z4 Soglia",0.91,1.05),
        ("Z5 VO2max",1.06,1.20),
        ("Z6 Anaerobica",1.21,1.50),
        ("Z7 Neuromuscolare",1.51,2.00),
    ]

    zone_df = pd.DataFrame(
        [[z, round(a*ftp), round(b*ftp)] for z,a,b in zone],
        columns=["Zona","Da (W)","A (W)"]
    )

    st.subheader("Zone Potenza")
    st.dataframe(zone_df, use_container_width=True)

# ======================================================
# PROIEZIONE
# ======================================================

st.header("Proiezione Performance")

nuovo_peso = st.number_input("Nuovo peso target (kg)", 0.0)
incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0)

if nuovo_peso > 0 and ftp > 0:

    nuova_ftp = ftp * (1 + incremento_ftp/100)
    nuovo_wkg = nuova_ftp / nuovo_peso

    tempo_vecchio = tempo_salita_realistico(ftp, peso)
    tempo_nuovo = tempo_salita_realistico(nuova_ftp, nuovo_peso)

    delta_tempo = tempo_vecchio - tempo_nuovo

    st.metric("Nuovo W/kg", f"{nuovo_wkg:.2f}", f"{nuovo_wkg-wkg:.2f}")
    st.write(f"Salita 5 km 6%: da {tempo_vecchio:.1f} min a {tempo_nuovo:.1f} min")
    st.success(f"Miglioramento stimato: {delta_tempo:.1f} minuti")

# ======================================================
# PDF PROFESSIONALE
# ======================================================

if st.button("Genera PDF Professionale"):

    def safe(text):
        return text.encode("latin-1", "replace").decode("latin-1")

    class PDF(FPDF):

        def header(self):
            try:
                self.image("logo.png", 70, 8, 70)
                self.ln(35)
            except:
                self.ln(20)

            self.set_font("Arial", "B", 18)
            self.cell(0, 10, "REPORT PERFORMANCE", 0, 1, "C")
            self.ln(5)

        def section(self, title):
            self.set_font("Arial", "B", 12)
            self.cell(0, 8, title, 0, 1)
            self.ln(2)

        def kv(self, key, value):
            self.set_font("Arial", "B", 10)
            self.cell(50, 6, key)
            self.set_font("Arial", "", 10)
            self.cell(0, 6, safe(value), 0, 1)

    pdf = PDF()
    pdf.add_page()

    pdf.section("Dati Anagrafici")
    pdf.kv("Nome:", nome)
    pdf.kv("Cognome:", cognome)
    pdf.kv("Eta:", f"{eta} anni")

    pdf.section("Antropometria")
    pdf.kv("Peso:", f"{peso:.1f} kg")
    pdf.kv("BMI:", f"{bmi:.2f} ({categoria_bmi})")
    pdf.kv("Massa grassa:", f"{fm:.1f}%")

    pdf.section("Performance")
    pdf.kv("FTP:", f"{ftp:.1f} W")
    pdf.kv("W/kg:", f"{wkg:.2f}")

    pdf.output("report_performance_professionale.pdf")

    with open("report_performance_professionale.pdf", "rb") as f:
        st.download_button(
            "Scarica PDF",
            f,
            "report_performance_professionale.pdf"
        )
