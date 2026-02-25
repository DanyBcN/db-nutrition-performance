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

# ======================================================
# GRAFICO BMI
# ======================================================

fig, ax = plt.subplots(figsize=(10,2.2))
ax.set_xlim(15, 40)
ax.set_ylim(0, 1)

ax.axvspan(15, 18.5, color="#4A90E2", alpha=0.35)
ax.axvspan(18.5, 25, color="#27AE60", alpha=0.35)
ax.axvspan(25, 30, color="#F39C12", alpha=0.35)
ax.axvspan(30, 40, color="#E74C3C", alpha=0.35)

ax.axvspan(bmi_min, bmi_max, color="purple", alpha=0.15)

ax.axvline(bmi, color="black", linewidth=2.5)
ax.scatter(bmi, 0.5, s=120, color="black")
ax.text(bmi, 0.8, f"{bmi:.1f}", ha='center', fontsize=11, fontweight='bold')

ax.set_yticks([])
ax.set_xlabel("Indice di Massa Corporea (BMI)")
ax.set_title("Classificazione BMI OMS + Range Atleta")

for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

st.pyplot(fig)
fig.savefig("bmi_chart.png", dpi=300, bbox_inches="tight")

# ======================================================
# GRAFICO MASSA GRASSA
# ======================================================

st.subheader("Valutazione Massa Grassa")

fig2, ax2 = plt.subplots(figsize=(10,2.2))
ax2.set_xlim(0, 30)
ax2.set_ylim(0, 1)

ax2.axvspan(fm_min, fm_max, color="#27AE60", alpha=0.3)
ax2.axvline(fm, color="black", linewidth=2.5)
ax2.scatter(fm, 0.5, s=120, color="black")
ax2.text(fm, 0.8, f"{fm:.1f}%", ha='center', fontsize=11, fontweight='bold')

ax2.set_yticks([])
ax2.set_xlabel("Percentuale Massa Grassa (%)")
ax2.set_title("Valutazione Massa Grassa Atleta")

for spine in ["top", "right", "left"]:
    ax2.spines[spine].set_visible(False)

st.pyplot(fig2)
fig2.savefig("fm_chart.png", dpi=300, bbox_inches="tight")

st.markdown("---")

# ======================================================
# DA QUI IN POI È IDENTICO AL TUO CODICE ORIGINALE
# (FTP, ZONE, PROIEZIONE, PDF COMPLETO)
# ======================================================
