import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import math
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# ======================================================
# LOGO IN PAGINA
# ======================================================

col1, col2, col3 = st.columns([1,2,1])
with col2:
    try:
        st.image("logo.png", width=300)
    except:
        pass

# ======================================================
# INIZIALIZZAZIONE VARIABILI (ANTI-ERROR)
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

zone_df = pd.DataFrame()
zone_hr_df = pd.DataFrame()

# ======================================================
# DATI ANAGRAFICI
# ======================================================

st.header("Dati Anagrafici")

colA, colB, colC = st.columns(3)

with colA:
    nome = st.text_input("Nome")

with colB:
    cognome = st.text_input("Cognome")

with colC:
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

col1, col2 = st.columns(2)

with col1:
    peso = st.number_input("Peso (kg)", 30.0, 200.0)
    altezza = st.number_input("Altezza (cm)", 100.0, 220.0)

with col2:
    fm = st.number_input("Massa grassa (%)", 3.0, 50.0)

altezza_m = altezza / 100 if altezza > 0 else 0
bmi = peso / (altezza_m**2) if altezza_m > 0 else 0
fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg

if bmi < 18.5:
    categoria_bmi = "Sottopeso"
elif 18.5 <= bmi < 25:
    categoria_bmi = "Normopeso"
elif 25 <= bmi < 30:
    categoria_bmi = "Sovrappeso"
else:
    categoria_bmi = "Obesità"

colM1, colM2, colM3 = st.columns(3)
colM1.metric("BMI", f"{bmi:.2f}", categoria_bmi)
colM2.metric("Massa grassa", f"{fm_kg:.2f} kg")
colM3.metric("Massa magra", f"{massa_magra:.2f} kg")

# ======================================================
# RANGE BMI ATLETA
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

st.write(f"Range BMI ideale: {bmi_min}-{bmi_max}")
st.write(f"Valutazione atleta: {giudizio_atleta}")

if fm < fm_min:
    st.warning("Massa grassa sotto range fisiologico atleta.")
elif fm > fm_max:
    st.warning("Massa grassa sopra range ottimale atleta.")

# ======================================================
# GRAFICO BMI (MIGLIORATO)
# ======================================================

fig, ax = plt.subplots(figsize=(10,2))
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
ax.text(bmi, 0.8, f"{bmi:.1f}", ha='center', fontsize=11, fontweight='bold')

ax.set_yticks([])
ax.set_xlabel("Indice di Massa Corporea (BMI)")
ax.set_title("Classificazione BMI OMS + Range Atleta")

for spine in ax.spines.values():
    spine.set_visible(False)

st.pyplot(fig)
fig.savefig("bmi_chart.png", dpi=300, bbox_inches="tight")

# ======================================================
# GRAFICO MASSA GRASSA (MIGLIORATO)
# ======================================================

st.subheader("Valutazione Massa Grassa")

fig2, ax2 = plt.subplots(figsize=(10,2))
ax2.set_xlim(0, 30)
ax2.set_ylim(0, 1)

ax2.axvspan(fm_min, fm_max, color="#ABEBC6")
ax2.axvline(fm, linewidth=3)
ax2.scatter(fm, 0.5, s=150)
ax2.text(fm, 0.8, f"{fm:.1f}%", ha='center', fontsize=11, fontweight='bold')

ax2.set_yticks([])
ax2.set_xlabel("Percentuale Massa Grassa (%)")
ax2.set_title("Valutazione Massa Grassa Atleta")

for spine in ax2.spines.values():
    spine.set_visible(False)

st.pyplot(fig2)
fig2.savefig("fm_chart.png", dpi=300, bbox_inches="tight")

st.markdown("---")

# ======================================================
# CALCOLO FTP (IDENTICO MA PIÙ ORDINATO)
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

colF1, colF2 = st.columns(2)
colF1.metric("FTP stimata", f"{ftp:.2f} W")
colF2.metric("W/kg", f"{wkg:.2f}")

# ======================================================
# MODELLO SALITA REALISTICO (UPGRADE)
# ======================================================

def tempo_salita_realistico(potenza, peso, lunghezza=5000, pendenza=0.06):
    g = 9.81
    rho = 1.226
    CdA = 0.32
    Crr = 0.004

    massa_tot = peso + 8
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
# PROIEZIONE PERFORMANCE (CON MODELLO MIGLIORATO)
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

    tempo_vecchio = tempo_salita_realistico(ftp, peso)
    tempo_nuovo = tempo_salita_realistico(nuova_ftp, nuovo_peso)

    st.metric("Nuovo W/kg", f"{nuovo_wkg:.2f}", f"{delta_wkg:.2f}")
    st.write(f"Giudizio: {giudizio}")
    st.write(f"Salita 5 km 6%: da {tempo_vecchio:.1f} min a {tempo_nuovo:.1f} min")

st.markdown("---")

# ======================================================
# PDF (MIGLIORATO GRAFICAMENTE, MA COMPLETO)
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
            self.ln(3)

            self.set_draw_color(30, 90, 160)
            self.set_line_width(1)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(8)

        def section_title(self, title):
            self.set_fill_color(230, 240, 255)
            self.set_font("Arial", "B", 12)
            self.cell(0, 8, title, 0, 1, "L", True)
            self.ln(3)

        def key_value(self, key, value):
            self.set_font("Arial", "B", 10)
            self.cell(60, 6, key)
            self.set_font("Arial", "", 10)
            self.cell(0, 6, safe(value), 0, 1)

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.section_title("Dati Anagrafici")
    pdf.key_value("Nome:", nome)
    pdf.key_value("Cognome:", cognome)
    pdf.key_value("Eta:", f"{eta} anni")

    pdf.section_title("Antropometria")
    pdf.key_value("Peso:", f"{peso:.1f} kg")
    pdf.key_value("BMI:", f"{bmi:.2f} ({categoria_bmi})")
    pdf.key_value("Massa grassa:", f"{fm:.1f}%")

    pdf.section_title("Performance")
    pdf.key_value("FTP:", f"{ftp:.1f} W")
    pdf.key_value("W/kg:", f"{wkg:.2f}")

    pdf.output("report_performance_professionale.pdf")

    with open("report_performance_professionale.pdf", "rb") as f:
        st.download_button(
            "Scarica PDF Professionale",
            f,
            "report_performance_professionale.pdf"
        )
