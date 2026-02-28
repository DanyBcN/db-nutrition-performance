import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import math
import matplotlib.pyplot as plt
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
st.set_page_config(layout="wide")

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

## ======================================================
# GRAFICO BMI MIGLIORATO
# ======================================================

st.subheader("Valutazione BMI")

fig, ax = plt.subplots(figsize=(10, 2.2))

ax.set_xlim(15, 35)
ax.set_ylim(0, 1)

# Range atleta
ax.axvspan(bmi_min, bmi_max, color="#27AE60", alpha=0.3)

# Colore punto BMI
if bmi < bmi_min:
    color_bmi = "blue"
elif bmi > bmi_max:
    color_bmi = "red"
else:
    color_bmi = "green"

ax.axvline(bmi, color=color_bmi, linewidth=3)
ax.scatter(bmi, 0.5, s=150, color=color_bmi)
ax.text(bmi, 0.8, f"{bmi:.1f}", ha='center', fontsize=11, fontweight='bold')

ax.set_yticks([])
ax.set_xlabel("BMI")
ax.set_title("Valutazione BMI Atleta")

for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

st.pyplot(fig)

fig.savefig("bmi_chart.png", dpi=400, bbox_inches="tight", pad_inches=0.3)

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
fig2.savefig("fm_chart.png", dpi=400, bbox_inches="tight", pad_inches=0.3)
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

    # ==================================================
    # DATI ANAGRAFICI
    # ==================================================
    pdf.section_title("Dati Anagrafici")
    pdf.normal(
        f"Nome: {nome}\n"
        f"Cognome: {cognome}\n"
        f"Data di nascita: {data_nascita.strftime('%d/%m/%Y')}\n"
        f"Eta: {eta} anni"
    )

    # ==================================================
    # ANTROPOMETRIA
    # ==================================================
    pdf.section_title("Antropometria")
    pdf.normal(
    f"Peso: {peso:.1f} kg\n"
    f"Altezza: {altezza:.1f} cm\n"
    f"BMI: {bmi:.2f} ({categoria_bmi})\n"
    f"Massa grassa: {fm:.1f}% ({fm_kg:.2f} kg)\n"
    f"Massa magra: {massa_magra:.2f} kg\n"
    f"BMR Mifflin: {bmr:.0f} kcal\n"
    f"BMR Cunningham: {bmr_cunningham:.0f} kcal\n"
    f"TDEE stimato: {tdee:.0f} kcal\n"
    f"Disponibilità energetica: {energia_disponibile:.1f} kcal/kg FFM\n\n"
    f"FFMI: {ffmi:.2f}\n"
    f"FMI: {fmi:.2f}\n"
    f"Rapporto MM/MG: {ratio_mm_mg:.2f}\n\n"
    f"Range BMI atleta ({tipo_sport}): {bmi_min}-{bmi_max}\n"
    f"Valutazione atleta: {giudizio_atleta}\n"
    f"Range FM atleta: {fm_min}-{fm_max}%\n"
    f"Valutazione massa grassa: {giudizio_fm}"
)

    pdf.section_title("Grafico BMI")
    pdf.image("bmi_chart.png", x=15, w=180)

    pdf.section_title("Grafico Massa Grassa")
    pdf.image("fm_chart.png", x=30, w=150)

    # ==================================================
    # PERFORMANCE
    # ==================================================
    pdf.section_title("Performance")
    pdf.normal(
    f"Metodo FTP: {metodo}\n"
    f"Valore test inserito: {valore_test:.2f} W\n"
    f"FTP calcolata: {ftp:.2f} W\n"
    f"W/kg: {wkg:.2f}\n"
    f"Livello ciclista stimato: {livello_ciclista}"
)

    # ==================================================
    # ZONE POTENZA
    # ==================================================
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

    # ==================================================
    # ZONE CARDIO
    # ==================================================
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

    # ==================================================
    # PROIEZIONE
    # ==================================================
    if nuovo_peso > 0 and ftp > 0:

        pdf.section_title("Proiezione Miglioramento")

        delta_tempo = tempo_vecchio - tempo_nuovo
       
        delta_tempo = tempo_vecchio - tempo_nuovo
delta_percentuale = ((tempo_vecchio - tempo_nuovo) / tempo_vecchio) * 100

testo_proj = (
    f"Peso attuale: {peso:.1f} kg\n"
    f"Peso target: {nuovo_peso:.1f} kg\n"
    f"Variazione peso: {peso - nuovo_peso:.1f} kg\n\n"
    
    f"FTP attuale: {ftp:.1f} W\n"
    f"FTP prevista: {nuova_ftp:.1f} W\n\n"
    
    f"W/kg attuale: {wkg:.2f}\n"
    f"W/kg previsto: {nuovo_wkg:.2f}\n\n"
    
    f"--- SIMULAZIONE SALITA ---\n"
    f"Lunghezza: {lunghezza/1000:.1f} km\n"
    f"Pendenza media: {pendenza*100:.1f}%\n\n"
    
    f"Tempo stimato con dati attuali: {tempo_vecchio:.1f} min\n"
    f"Tempo stimato con nuovo peso/FTP: {tempo_nuovo:.1f} min\n\n"
    
    f"Miglioramento assoluto: {delta_tempo:.1f} minuti\n"
    f"Riduzione percentuale del tempo: {delta_percentuale:.1f}%\n"
)

        pdf.normal(testo_proj)

    pdf.output("report_performance_professionale.pdf")

    with open("report_performance_professionale.pdf", "rb") as f:
        st.download_button(
            "Scarica PDF Professionale",
            f,
            "report_performance_professionale.pdf"
        )
 
