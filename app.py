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

zone_df = pd.DataFrame()
zone_hr_df = pd.DataFrame()

# ======================================================
# DATI ANAGRAFICI
# ======================================================

st.header("Dati Anagrafici")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")

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

st.write(f"Range BMI ideale: {bmi_min}-{bmi_max}")
st.write(f"Valutazione atleta: {giudizio_atleta}")

if fm < fm_min:
    st.warning("Massa grassa sotto range fisiologico atleta.")
elif fm > fm_max:
    st.warning("Massa grassa sopra range ottimale atleta.")

# ======================================================
# GRAFICI
# ======================================================

fig, ax = plt.subplots(figsize=(10,2))
ax.set_xlim(15, 40)
ax.set_ylim(0, 1)

ax.axvspan(15, 18.5, color="#4A90E2", alpha=0.35)
ax.axvspan(18.5, 25, color="#27AE60", alpha=0.35)
ax.axvspan(25, 30, color="#F39C12", alpha=0.35)
ax.axvspan(30, 40, color="#E74C3C", alpha=0.35)

ax.axvspan(bmi_min, bmi_max, color="purple", alpha=0.15)
ax.axvline(bmi, color="black", linewidth=3)
ax.scatter(bmi, 0.5, s=140, color="black")

ax.set_yticks([])
ax.set_xlabel("Indice di Massa Corporea (BMI)")
ax.set_title("Classificazione BMI OMS + Range Atleta")

for spine in ax.spines.values():
    spine.set_visible(False)

st.pyplot(fig)
fig.savefig("bmi_chart.png", dpi=300, bbox_inches="tight")

fig2, ax2 = plt.subplots(figsize=(10,2))
ax2.set_xlim(0, 30)
ax2.set_ylim(0, 1)

ax2.axvspan(fm_min, fm_max, color="#27AE60", alpha=0.3)
ax2.axvline(fm, color="black", linewidth=3)
ax2.scatter(fm, 0.5, s=140, color="black")

ax2.set_yticks([])
ax2.set_xlabel("Percentuale Massa Grassa (%)")
ax2.set_title("Valutazione Massa Grassa Atleta")

for spine in ax2.spines.values():
    spine.set_visible(False)

st.pyplot(fig2)
fig2.savefig("fm_chart.png", dpi=300, bbox_inches="tight")

st.markdown("---")

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

colA, colB = st.columns(2)
colA.metric("FTP", f"{ftp:.2f} W")
colB.metric("W/kg", f"{wkg:.2f}")

st.markdown("---")

# ======================================================
# MODELLO SALITA REALISTICO
# ======================================================

def tempo_salita(potenza, peso):
    g = 9.81
    rho = 1.226
    CdA = 0.32
    Crr = 0.004
    lunghezza = 5000
    pendenza = 0.06

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
# RADAR PERFORMANCE
# ======================================================

if ftp > 0:
    st.subheader("Profilo Performance (Radar)")

    score_wkg = min(wkg / 6, 1)
    score_ftp = min(ftp / 500, 1)
    score_bmi = 1 - abs((bmi - (bmi_min + bmi_max)/2) / 10)
    score_fm = 1 - abs((fm - (fm_min + fm_max)/2) / 20)

    categories = ["W/kg","FTP","BMI","FM"]
    values = [score_wkg, score_ftp, score_bmi, score_fm]
    values += values[:1]

    angles = [n / float(len(categories)) * 2 * math.pi for n in range(len(categories))]
    angles += angles[:1]

    fig_radar, ax_radar = plt.subplots(figsize=(5,5), subplot_kw=dict(polar=True))
    ax_radar.plot(angles, values)
    ax_radar.fill(angles, values, alpha=0.25)
    ax_radar.set_xticks(angles[:-1])
    ax_radar.set_xticklabels(categories)
    ax_radar.set_yticks([])

    st.pyplot(fig_radar)

# ======================================================
# PROIEZIONE
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

    tempo_vecchio = tempo_salita(ftp, peso)
    tempo_nuovo = tempo_salita(nuova_ftp, nuovo_peso)

    st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")
    st.write(f"Giudizio: {giudizio}")
    st.write(f"Salita 5 km 6%: da {tempo_vecchio:.1f} min a {tempo_nuovo:.1f} min")

st.markdown("---")
