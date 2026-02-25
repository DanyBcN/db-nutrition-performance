import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from fpdf import FPDF
import tempfile

# --------------------------------------------------
# CONFIG PAGINA
# --------------------------------------------------

st.set_page_config(
    page_title="Report Performance Sportiva",
    layout="wide"
)

# --------------------------------------------------
# SIDEBAR INPUT
# --------------------------------------------------

st.sidebar.header("Dati Atleta")

nome = st.sidebar.text_input("Nome e Cognome")
eta = st.sidebar.number_input("Età", 10, 90, 30)
sesso = st.sidebar.selectbox("Sesso", ["Maschile", "Femminile"])
altezza = st.sidebar.number_input("Altezza (cm)", 120, 220, 175)
peso = st.sidebar.number_input("Peso (kg)", 40.0, 150.0, 70.0)
ftp = st.sidebar.number_input("FTP (W)", 0.0, 600.0, 250.0)

# --------------------------------------------------
# CALCOLI ANTROPOMETRICI
# --------------------------------------------------

bmi = peso / ((altezza / 100) ** 2)

if sesso == "Maschile":
    bf = 1.20 * bmi + 0.23 * eta - 16.2
else:
    bf = 1.20 * bmi + 0.23 * eta - 5.4

hr_max = 220 - eta

ftp_zones = [
    ("Z1 Recovery", f"< {0.55*ftp:.0f} W"),
    ("Z2 Endurance", f"{0.55*ftp:.0f} - {0.70*ftp:.0f} W"),
    ("Z3 Tempo", f"{0.70*ftp:.0f} - {0.82*ftp:.0f} W"),
    ("Z4 Soglia", f"{0.82*ftp:.0f} - {0.89*ftp:.0f} W"),
    ("Z5 VO2max", f"{0.89*ftp:.0f} - {0.94*ftp:.0f} W"),
    ("Z6 Anaerobica", f"{0.94*ftp:.0f} - {1.05*ftp:.0f} W"),
    ("Z7 Sprint", f"> {1.05*ftp:.0f} W"),
]

hr_zones = [
    ("Z1 Recupero", f"< {0.60*hr_max:.0f} bpm"),
    ("Z2 Aerobica", f"{0.60*hr_max:.0f} - {0.70*hr_max:.0f} bpm"),
    ("Z3 Soglia", f"{0.70*hr_max:.0f} - {0.80*hr_max:.0f} bpm"),
    ("Z4 VO2max", f"{0.80*hr_max:.0f} - {0.90*hr_max:.0f} bpm"),
    ("Z5 Massimale", f"{0.90*hr_max:.0f} - {hr_max:.0f} bpm"),
]

# --------------------------------------------------
# GRAFICI
# --------------------------------------------------

def create_bmi_chart():
    fig, ax = plt.subplots(figsize=(6,2.5))
    ax.axvspan(0,18.5, alpha=0.3)
    ax.axvspan(18.5,25, alpha=0.3)
    ax.axvspan(25,30, alpha=0.3)
    ax.axvspan(30,50, alpha=0.3)
    ax.axvline(bmi, linewidth=2)
    ax.set_xlim(10,40)
    ax.set_yticks([])
    ax.set_title("BMI")
    ax.text(bmi,0.5,f"{bmi:.1f}")
    for s in ["top","right","left"]:
        ax.spines[s].set_visible(False)
    return fig

def create_bf_chart():
    fig, ax = plt.subplots(figsize=(6,2.5))
    ax.axvline(bf, linewidth=2)
    ax.set_xlim(0,50)
    ax.set_yticks([])
    ax.set_title("Massa Grassa %")
    ax.text(bf,0.5,f"{bf:.1f}%")
    for s in ["top","right","left"]:
        ax.spines[s].set_visible(False)
    return fig

# --------------------------------------------------
# INTERFACCIA PRINCIPALE
# --------------------------------------------------

st.title("Report Performance Sportiva")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Dati Antropometrici")
    st.write(f"**BMI:** {bmi:.2f}")
    st.write(f"**Massa grassa stimata:** {bf:.1f}%")

with col2:
    st.subheader("FTP")
    st.write(f"**FTP attuale:** {ftp:.0f} W")

st.divider()

tab1, tab2 = st.tabs(["Grafici", "Zone Allenamento"])

with tab1:
    fig_bmi = create_bmi_chart()
    fig_bf = create_bf_chart()
    st.pyplot(fig_bmi)
    st.pyplot(fig_bf)

with tab2:
    st.subheader("Zone Potenza")
    st.table(pd.DataFrame(ftp_zones, columns=["Zona","Intervallo"]))
    st.subheader("Zone Cardiache")
    st.table(pd.DataFrame(hr_zones, columns=["Zona","Intervallo"]))

st.divider()

# --------------------------------------------------
# PROIEZIONE
# --------------------------------------------------

incremento = st.slider("Incremento FTP (%)", 0, 20, 5)
new_ftp = ftp * (1 + incremento/100)

st.write(f"FTP stimata dopo miglioramento: **{new_ftp:.0f} W**")

st.divider()

# --------------------------------------------------
# PDF PROFESSIONALE
# --------------------------------------------------

def create_pdf():

    pdf = FPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Font Unicode
    try:
        pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
        font = "DejaVu"
    except:
        font = "Helvetica"

    pdf.add_page()

    # Header
    pdf.set_font(font, "B", 18)
    pdf.cell(0, 10, "REPORT PERFORMANCE SPORTIVA", ln=True, align="C")
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    pdf.set_font(font, "", 12)
    pdf.multi_cell(0, 6,
        f"Nome: {nome}\n"
        f"Età: {eta}\n"
        f"Sesso: {sesso}\n"
        f"Peso: {peso:.1f} kg\n"
        f"Altezza: {altezza:.1f} cm\n"
        f"FTP: {ftp:.0f} W\n"
        f"BMI: {bmi:.2f}\n"
        f"Massa grassa: {bf:.1f}%"
    )

    pdf.ln(6)

    # Grafici temporanei
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp1:
        fig_bmi.savefig(tmp1.name, dpi=300, bbox_inches="tight")
        pdf.image(tmp1.name, w=170)

    pdf.ln(4)

    with tempfile.NamedTemporaryFile(suffix=".png") as tmp2:
        fig_bf.savefig(tmp2.name, dpi=300, bbox_inches="tight")
        pdf.image(tmp2.name, w=170)

    pdf.ln(6)

    pdf.set_font(font, "B", 13)
    pdf.cell(0, 8, "Zone Potenza", ln=True)
    pdf.set_font(font, "", 10)

    for z, i in ftp_zones:
        pdf.cell(60,6,z,1)
        pdf.cell(0,6,i,1,ln=True)

    pdf.ln(4)

    pdf.set_font(font, "B", 13)
    pdf.cell(0, 8, "Zone Cardiache", ln=True)
    pdf.set_font(font, "", 10)

    for z, i in hr_zones:
        pdf.cell(60,6,z,1)
        pdf.cell(0,6,i,1,ln=True)

    pdf.ln(6)

    pdf.set_font(font, "", 11)
    pdf.multi_cell(0,6,
        f"Con un incremento del {incremento}% "
        f"l'FTP passerebbe da {ftp:.0f} W a {new_ftp:.0f} W."
    )

    pdf_bytes = pdf.output(dest="S")

    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode("latin-1")

    return pdf_bytes


if st.button("Genera PDF Professionale"):
    pdf_data = create_pdf()

    st.download_button(
        "Scarica PDF",
        data=pdf_data,
        file_name="report_performance.pdf",
        mime="application/pdf"
    )
