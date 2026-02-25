import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import math
import matplotlib.pyplot as plt
import tempfile
import io
import os

st.set_page_config(layout="wide")

# ======================================================
# LOGO IN PAGINA
# ======================================================
col1, col2, col3 = st.columns([1,2,1])
with col2:
    try:
        st.image("logo.png", width=300)
    except Exception:
        # non bloccare l'app se manca il logo
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

if not nome or not cognome:
    st.info("Inserisci Nome e Cognome per generare un report completo.")
st.markdown("---")

# ======================================================
# ANTROPOMETRIA
# ======================================================
st.header("Valutazione Antropometrica")

peso = st.number_input("Peso (kg)", 30.0, 200.0, value=70.0, step=0.1, format="%.1f")
altezza = st.number_input("Altezza (cm)", 100.0, 220.0, value=175.0, step=0.1, format="%.1f")
fm = st.number_input("Massa grassa (%)", 3.0, 50.0, value=15.0, step=0.1, format="%.1f")

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
st.markdown("---")

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
def make_bmi_figure(bmi, bmi_min, bmi_max):
    fig, ax = plt.subplots(figsize=(10,2.2))
    ax.set_xlim(15, 40)
    ax.set_ylim(0, 1)

    ax.axvspan(15, 18.5, color="#4A90E2", alpha=0.35)
    ax.axvspan(18.5, 25, color="#27AE60", alpha=0.35)
    ax.axvspan(25, 30, color="#F39C12", alpha=0.35)
    ax.axvspan(30, 40, color="#E74C3C", alpha=0.35)

    ax.axvspan(bmi_min, bmi_max, color="purple", alpha=0.15)

    # line & marker
    ax.axvline(bmi, color="black", linewidth=2.5)
    ax.scatter(bmi, 0.5, s=120, color="black")
    ax.text(bmi, 0.8, f"{bmi:.1f}", ha='center', fontsize=11, fontweight='bold')

    ax.set_yticks([])
    ax.set_xlabel("Indice di Massa Corporea (BMI)")
    ax.set_title("Classificazione BMI OMS + Range Atleta")

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return fig

fig = make_bmi_figure(bmi, bmi_min, bmi_max)
st.pyplot(fig)

# ======================================================
# GRAFICO MASSA GRASSA
# ======================================================
def make_fm_figure(fm, fm_min, fm_max):
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
    fig2.tight_layout()
    return fig2

fig2 = make_fm_figure(fm, fm_min, fm_max)
st.pyplot(fig2)
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
    valore_test = st.number_input("FTP (W)", 0.0, value=0.0, step=1.0)
    ftp = valore_test

elif metodo == "Test 20 minuti":
    valore_test = st.number_input("Media 20 min (W)", 0.0, value=0.0, step=1.0)
    ftp = valore_test * 0.95

elif metodo == "Test 8 minuti":
    valore_test = st.number_input("Media 8 min (W)", 0.0, value=0.0, step=1.0)
    ftp = valore_test * 0.90

elif metodo == "Ramp test":
    valore_test = st.number_input("Ultimo step completato (W)", 0.0, value=0.0, step=1.0)
    ftp = valore_test * 0.75

wkg = ftp / peso if peso > 0 else 0

st.write(f"FTP stimata: {ftp:.2f} W")
st.write(f"W/kg: {wkg:.2f}")
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
        [[z, int(round(a*ftp)), int(round(b*ftp))] for z,a,b in zone],
        columns=["Zona","Da (W)","A (W)"]
    )

    st.subheader("Zone Potenza")
    st.table(zone_df)

    # download CSV
    csv_bytes = zone_df.to_csv(index=False).encode("utf-8")
    st.download_button("Scarica Zone Potenza (CSV)", csv_bytes, "zone_potenza.csv", "text/csv")
else:
    st.info("Inserisci un valore di FTP per calcolare le zone potenza.")

# ======================================================
# ZONE CARDIO
# ======================================================
st.header("Frequenza Cardiaca")

fthr = st.number_input("FTHR (bpm)", 0.0, value=0.0, step=1.0)

if fthr > 0:
    zone_hr = [
        ("Z1 Recupero",0.81,0.89),
        ("Z2 Aerobico base",0.90,0.93),
        ("Z3 Tempo",0.94,0.99),
        ("Z4 Soglia",1.00,1.05),
        ("Z5 Alta intensita",1.06,1.15),
    ]

    zone_hr_df = pd.DataFrame(
        [[z, int(round(a*fthr)), int(round(b*fthr))] for z,a,b in zone_hr],
        columns=["Zona","Da (bpm)","A (bpm)"]
    )

    st.subheader("Zone Cardio")
    st.table(zone_hr_df)

    csv_bytes_hr = zone_hr_df.to_csv(index=False).encode("utf-8")
    st.download_button("Scarica Zone Cardio (CSV)", csv_bytes_hr, "zone_cardio.csv", "text/csv")
else:
    st.info("Inserisci la FTHR per calcolare le zone cardio.")
st.markdown("---")

# ======================================================
# PROIEZIONE PERFORMANCE
# ======================================================
st.header("Proiezione Performance")

nuovo_peso = st.number_input("Nuovo peso target (kg)", 0.0, value=peso, step=0.1, format="%.1f")
incremento_ftp = st.number_input("Incremento FTP (%)", 0.0, 50.0, value=0.0, step=0.1, format="%.1f")

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

    lunghezza = 5000
    pendenza = 0.06
    g = 9.81

    def tempo_salita(potenza, peso):
        # semplice stima: velocità = potenza / (forza di salita)
        forza = peso * g * pendenza
        velocita = potenza / forza if forza > 0 else 0.0001
        # tempo in minuti
        return (lunghezza / velocita) / 60 if velocita > 0 else float("inf")

    tempo_vecchio = tempo_salita(ftp, peso)
    tempo_nuovo = tempo_salita(nuova_ftp, nuovo_peso)

    st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")
    st.write(f"Giudizio: {giudizio}")
    st.write(f"Salita 5 km 6%: da {tempo_vecchio:.1f} min a {tempo_nuovo:.1f} min")
else:
    st.info("Per la proiezione inserisci FTP e un nuovo peso target.")
st.markdown("---")

# ======================================================
# GENERAZIONE PDF PROFESSIONALE (USO SAFE TEMPFILE/UTF8)
# ======================================================
def safe(text: str) -> str:
    # fallback per FPDF senza font unicode
    return str(text).encode("latin-1", "replace").decode("latin-1")

def try_add_dejavu_font(pdf_obj: FPDF):
    # tenta di aggiungere DejaVuSans.ttf (deve essere presente nella cartella)
    try:
        if os.path.exists("DejaVuSans.ttf"):
            pdf_obj.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
            return True
    except Exception:
        pass
    return False

if st.button("Genera PDF Professionale"):
    # validazioni base
    if not nome or not cognome:
        st.warning("Inserisci Nome e Cognome prima di generare il PDF.")
    else:
        # salviamo le figure su file temporanei per inserirle nel PDF
        tmp_files = []
        try:
            # salva BMI chart
            tmp_bmi = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            fig.savefig(tmp_bmi.name, dpi=300, bbox_inches="tight")
            tmp_files.append(tmp_bmi.name)
            tmp_bmi.close()

            # salva FM chart
            tmp_fm = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            fig2.savefig(tmp_fm.name, dpi=300, bbox_inches="tight")
            tmp_files.append(tmp_fm.name)
            tmp_fm.close()

            # costruzione PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            # tenta aggiungere font unicode
            has_dejavu = try_add_dejavu_font(pdf)
            if has_dejavu:
                default_font = ("DejaVu", "")
            else:
                default_font = ("Arial", "")

            pdf.add_page()

            # header manuale (simile al tuo)
            try:
                if os.path.exists("logo.png"):
                    pdf.image("logo.png", 75, 8, 60)
                    pdf.ln(30)
                else:
                    pdf.ln(20)
            except Exception:
                pdf.ln(20)

            pdf.set_font(default_font[0], "B", 18)
            pdf.cell(0, 10, "REPORT PERFORMANCE", 0, 1, "C")
            pdf.ln(3)
            pdf.set_draw_color(30, 90, 160)
            pdf.set_line_width(1)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(8)

            def section_title(title):
                pdf.set_fill_color(230, 240, 255)
                pdf.set_font(default_font[0], "B", 12)
                text = title if has_dejavu else safe(title)
                pdf.cell(0, 8, text, 0, 1, "L", True)
                pdf.ln(3)

            def normal(text):
                pdf.set_font(default_font[0], "", 10)
                t = text if has_dejavu else safe(text)
                pdf.multi_cell(0, 6, t)
                pdf.ln(3)

            # DATI
            section_title("Dati Anagrafici")
            normal(
                f"Nome: {nome}\n"
                f"Cognome: {cognome}\n"
                f"Data di nascita: {data_nascita.strftime('%d/%m/%Y')}\n"
                f"Eta: {eta} anni"
            )

            # ANTROPOMETRIA
            section_title("Antropometria")
            normal(
                f"Peso: {peso:.1f} kg\n"
                f"Altezza: {altezza:.1f} cm\n"
                f"BMI: {bmi:.2f} ({categoria_bmi})\n"
                f"Range BMI atleta ({tipo_sport}): {bmi_min}-{bmi_max}\n"
                f"Valutazione atleta: {giudizio_atleta}\n"
                f"Massa grassa: {fm:.1f}% ({fm_kg:.2f} kg)\n"
                f"Massa magra: {massa_magra:.2f} kg"
            )

            # GRAFICI
            section_title("Grafico BMI")
            try:
                pdf.image(tmp_files[0], x=30, w=150)
            except Exception:
                normal("Immagine BMI non disponibile.")

            section_title("Grafico Massa Grassa")
            try:
                pdf.image(tmp_files[1], x=30, w=150)
            except Exception:
                normal("Immagine massa grassa non disponibile.")

            # PERFORMANCE
            section_title("Performance")
            normal(
                f"Metodo FTP: {metodo}\n"
                f"Valore test inserito: {valore_test:.2f} W\n"
                f"FTP calcolata: {ftp:.2f} W\n"
                f"W/kg: {wkg:.2f}"
            )

            # ZONE POTENZA
            if not zone_df.empty:
                section_title("Zone Potenza")
                pdf.set_font(default_font[0], "B", 10)
                pdf.set_fill_color(200, 220, 255)
                # intestazioni
                header_names = ["Zona", "Da (W)", "A (W)"]
                widths = [90, 30, 30]
                for h, w in zip(header_names, widths):
                    text = h if has_dejavu else safe(h)
                    pdf.cell(w, 8, text, 1, 0, "C", True)
                pdf.ln()
                pdf.set_font(default_font[0], "", 10)
                for _, row in zone_df.iterrows():
                    pdf.cell(widths[0], 8, (row["Zona"] if has_dejavu else safe(row["Zona"])), 1)
                    pdf.cell(widths[1], 8, str(row["Da (W)"]), 1)
                    pdf.cell(widths[2], 8, str(row["A (W)"]), 1)
                    pdf.ln()

            # ZONE CARDIO
            if not zone_hr_df.empty:
                section_title("Zone Cardio")
                pdf.set_font(default_font[0], "B", 10)
                pdf.set_fill_color(200, 220, 255)
                header_names = ["Zona", "Da (bpm)", "A (bpm)"]
                widths = [90, 30, 30]
                for h, w in zip(header_names, widths):
                    pdf.cell(w, 8, (h if has_dejavu else safe(h)), 1, 0, "C", True)
                pdf.ln()
                pdf.set_font(default_font[0], "", 10)
                for _, row in zone_hr_df.iterrows():
                    pdf.cell(widths[0], 8, (row["Zona"] if has_dejavu else safe(row["Zona"])), 1)
                    pdf.cell(widths[1], 8, str(row["Da (bpm)"]), 1)
                    pdf.cell(widths[2], 8, str(row["A (bpm)"]), 1)
                    pdf.ln()

            # PROIEZIONE
            if nuovo_peso > 0 and ftp > 0:
                pdf.ln(6)
                delta_tempo = tempo_vecchio - tempo_nuovo
                section_title("Proiezione Miglioramento")
                testo_proj = (
                    f"Se il peso passasse da {peso:.1f} kg a {nuovo_peso:.1f} kg "
                    f"e se avesse un incremento della FTP del {incremento_ftp:.1f}%, "
                    f"passando quindi da {ftp:.1f} W a {nuova_ftp:.1f} W, "
                    f"si avrebbe un incremento del rapporto W/kg "
                    f"da {wkg:.2f} a {nuovo_wkg:.2f}.\n"
                    f"Su una salita di 5 chilometri con pendenza media del 6%, "
                    f"il tempo stimato passerebbe da {tempo_vecchio:.1f} minuti "
                    f"a {tempo_nuovo:.1f} minuti, "
                    f"con un miglioramento complessivo stimato di "
                    f"{delta_tempo:.1f} minuti."
                )
                normal(testo_proj)

            # output PDF su buffer
            pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace') if not has_dejavu else pdf.output(dest='S').encode('latin-1', 'replace')
            # Streamlit download button
            st.download_button("Scarica PDF Professionale",
                               data=pdf_bytes,
                               file_name="report_performance_professionale.pdf",
                               mime="application/pdf")
        finally:
            # pulizia file temporanei
            for fpath in tmp_files:
                try:
                    os.remove(fpath)
                except Exception:
                    pass
