import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(layout="wide")

# ======================================================
# CONFIGURAZIONE DATABASE
# ======================================================

DB_FILE = "database_pazienti.csv"

if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=[
        "Nome","Cognome","Data","Peso","Altezza",
        "FM%","BMI","FFMI","FTP","Wkg"
    ])
    df_init.to_csv(DB_FILE, index=False)

# ======================================================
# FUNZIONE MODELLO SALITA REALISTICO
# ======================================================

def tempo_salita_realistico(potenza, peso):
    peso_tot = peso + 8
    g = 9.81
    pendenza = 0.06
    Crr = 0.004
    rho = 1.226
    CdA = 0.32
    lunghezza = 5000

    velocita = 5

    for _ in range(50):
        forza_grav = peso_tot * g * pendenza
        forza_roll = peso_tot * g * Crr
        forza_aero = 0.5 * rho * CdA * velocita**2
        forza_tot = forza_grav + forza_roll + forza_aero
        velocita = potenza / forza_tot

    return lunghezza / velocita / 60

# ======================================================
# DATI ANAGRAFICI
# ======================================================

st.title("Performance & Nutrition Pro 3.0")

nome = st.text_input("Nome")
cognome = st.text_input("Cognome")
data_nascita = st.date_input("Data di nascita")

eta = date.today().year - data_nascita.year - (
    (date.today().month, date.today().day) <
    (data_nascita.month, data_nascita.day)
)

st.markdown("---")

# ======================================================
# ANTROPOMETRIA
# ======================================================

col1, col2 = st.columns(2)

with col1:
    peso = st.number_input("Peso (kg)", 30.0, 200.0)
    altezza = st.number_input("Altezza (cm)", 100.0, 220.0)
    fm = st.number_input("Massa grassa (%)", 3.0, 50.0)

altezza_m = altezza / 100 if altezza > 0 else 0
bmi = peso / (altezza_m**2) if altezza_m > 0 else 0
fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg
ffmi = massa_magra / (altezza_m**2) if altezza_m > 0 else 0

with col2:
    st.metric("BMI", f"{bmi:.2f}")
    st.metric("FFMI", f"{ffmi:.2f}")
    st.metric("Massa Magra", f"{massa_magra:.1f} kg")
    st.metric("Massa Grassa", f"{fm_kg:.1f} kg")

# ======================================================
# GRAFICO BMI
# ======================================================

fig_bmi, ax = plt.subplots(figsize=(8,2))
ax.set_xlim(15, 40)
ax.axvline(bmi, linewidth=3)
ax.set_yticks([])
st.pyplot(fig_bmi)
fig_bmi.savefig("bmi_chart.png", dpi=300, bbox_inches="tight")

# ======================================================
# CALCOLO FTP
# ======================================================

st.header("FTP & Zone")

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
else:
    valore_test = st.number_input("Ultimo step completato (W)", 0.0)
    ftp = valore_test * 0.75

wkg = ftp / peso if peso > 0 else 0

st.write(f"FTP: {ftp:.2f} W")
st.write(f"W/kg: {wkg:.2f}")

# ======================================================
# ZONE POTENZA
# ======================================================

if ftp > 0:
    zone = [
        ("Z1",0.00,0.55),
        ("Z2",0.56,0.75),
        ("Z3",0.76,0.90),
        ("Z4",0.91,1.05),
        ("Z5",1.06,1.20),
    ]
    zone_df = pd.DataFrame(
        [[z, round(a*ftp), round(b*ftp)] for z,a,b in zone],
        columns=["Zona","Da (W)","A (W)"]
    )
    st.table(zone_df)

# ======================================================
# ZONE CARDIO
# ======================================================

fthr = st.number_input("FTHR (bpm)", 0.0)

if fthr > 0:
    zone_hr = [
        ("Z1",0.81,0.89),
        ("Z2",0.90,0.93),
        ("Z3",0.94,0.99),
        ("Z4",1.00,1.05),
        ("Z5",1.06,1.15),
    ]
    zone_hr_df = pd.DataFrame(
        [[z, round(a*fthr), round(b*fthr)] for z,a,b in zone_hr],
        columns=["Zona","Da (bpm)","A (bpm)"]
    )
    st.table(zone_hr_df)

# ======================================================
# PROIEZIONE PERFORMANCE
# ======================================================

st.header("Proiezione")

nuovo_peso = st.number_input("Nuovo peso target (kg)", 0.0)
incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0)

if nuovo_peso > 0 and ftp > 0:
    nuova_ftp = ftp * (1 + incremento_ftp/100)
    tempo_vecchio = tempo_salita_realistico(ftp, peso)
    tempo_nuovo = tempo_salita_realistico(nuova_ftp, nuovo_peso)

    st.write(f"Tempo salita: {tempo_vecchio:.1f} → {tempo_nuovo:.1f} min")

# ======================================================
# SALVATAGGIO PAZIENTE
# ======================================================

if st.button("Salva Paziente nel Database"):
    df = pd.read_csv(DB_FILE)
    new_row = {
        "Nome": nome,
        "Cognome": cognome,
        "Data": date.today(),
        "Peso": peso,
        "Altezza": altezza,
        "FM%": fm,
        "BMI": bmi,
        "FFMI": ffmi,
        "FTP": ftp,
        "Wkg": wkg
    }
    df = pd.concat([df, pd.DataFrame([new_row])])
    df.to_csv(DB_FILE, index=False)
    st.success("Paziente salvato correttamente")

# ======================================================
# VISUALIZZAZIONE DATABASE
# ======================================================

if st.checkbox("Visualizza Database Pazienti"):
    df = pd.read_csv(DB_FILE)
    st.dataframe(df)

# ======================================================
# PDF PROFESSIONALE
# ======================================================

if st.button("Genera PDF Professionale"):

    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 16)
            self.cell(0, 10, "REPORT PERFORMANCE PRO 3.0", 0, 1, "C")
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "", 11)

    pdf.multi_cell(0, 8,
        f"{nome} {cognome}\n"
        f"Eta: {eta}\n"
        f"Peso: {peso} kg\n"
        f"BMI: {bmi:.2f}\n"
        f"FTP: {ftp:.2f} W\n"
        f"W/kg: {wkg:.2f}"
    )

    pdf.image("bmi_chart.png", x=30, w=150)

    if ftp > 0:
        pdf.ln(5)
        pdf.multi_cell(0,8,"Zone Potenza")
        for _, row in zone_df.iterrows():
            pdf.cell(0,6,f"{row['Zona']} {row['Da (W)']} - {row['A (W)']} W",0,1)

    pdf.output("report_performance_pro3.pdf")

    with open("report_performance_pro3.pdf","rb") as f:
        st.download_button("Scarica PDF", f, "report_performance_pro3.pdf")
