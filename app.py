import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from fpdf import FPDF
from io import BytesIO

# Configurazione pagina Streamlit
st.set_page_config(page_title="Valutazione Antropometrica", layout="wide")

# Sidebar: Dati input
st.sidebar.header("📋 Inserisci i tuoi dati")
nome = st.sidebar.text_input("Nome e cognome")
eta = st.sidebar.number_input("Età", min_value=10, max_value=100, value=30)
sesso = st.sidebar.selectbox("Sesso", ["Maschile", "Femminile"])
altezza = st.sidebar.number_input("Altezza (cm)", min_value=50, max_value=250, value=170)
peso = st.sidebar.number_input("Peso (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1)
ftp = st.sidebar.number_input("FTP (Watt)", min_value=0.0, value=200.0, step=1.0)

# Calcoli base antropometrici
if altezza > 0:
    bmi = peso / ((altezza/100) ** 2)
else:
    bmi = 0
if sesso == "Maschile":
    bf = 1.20 * bmi + 0.23 * eta - 16.2
else:
    bf = 1.20 * bmi + 0.23 * eta - 5.4

hr_max = 220 - eta
# Definizione zone cardio basate su % di HR max
hr_zones = [
    ("Z1 (ric.)", f"< {0.60*hr_max:.0f}"),
    ("Z2 (aerob.)", f"{0.60*hr_max:.0f} - {0.70*hr_max:.0f}"),
    ("Z3 (soglia)", f"{0.70*hr_max:.0f} - {0.80*hr_max:.0f}"),
    ("Z4 (VO₂max)", f"{0.80*hr_max:.0f} - {0.90*hr_max:.0f}"),
    ("Z5 (anaerob.)", f"{0.90*hr_max:.0f} - {hr_max:.0f}"),
]
# Definizione zone potenza basate su % di FTP
ftp_zones = [
    ("Z1 (riposo)", f"< {0.55*ftp:.0f} W"),
    ("Z2 (endurance)", f"{0.55*ftp:.0f} - {0.70*ftp:.0f} W"),
    ("Z3 (tempo)", f"{0.70*ftp:.0f} - {0.82*ftp:.0f} W"),
    ("Z4 (soglia)", f"{0.82*ftp:.0f} - {0.89*ftp:.0f} W"),
    ("Z5 (VO₂max)", f"{0.89*ftp:.0f} - {0.94*ftp:.0f} W"),
    ("Z6 (anaerob.)", f"{0.94*ftp:.0f} - {1.05*ftp:.0f} W"),
    ("Z7 (sprint)", f"> {1.05*ftp:.0f} W"),
]

# Funzioni per generare grafici BMI e % massa grassa
def create_bmi_chart(bmi_value):
    categories = [0, 18.5, 25, 30, 100]
    colors = ['#87CEFA', '#90EE90', '#FFD700', '#FA8072']
    labels = ['Sottopeso', 'Normale', 'Sovrappeso', 'Obeso']
    fig, ax = plt.subplots(figsize=(5,3))
    for i in range(len(labels)):
        ax.axvspan(categories[i], categories[i+1], color=colors[i], alpha=0.5)
    ax.axvline(bmi_value, color='red', linewidth=2)
    patches = [Patch(color=colors[i], label=labels[i]) for i in range(len(labels))]
    ax.legend(handles=patches, loc='upper right')
    ax.set_xlim(10, 40)
    ax.set_ylim(0,1)
    ax.set_yticks([])
    ax.set_xlabel("BMI")
    ax.set_title("Indice di Massa Corporea (BMI)")
    ax.text(bmi_value + 0.3, 0.9, f"{bmi_value:.1f}", color='red')
    for spine in ['top','right','left']:
        ax.spines[spine].set_visible(False)
    ax.axhline(0, color='black', linewidth=1)
    plt.tight_layout()
    return fig

def create_bf_chart(bf_value, gender):
    if gender == "Maschile":
        cats = [0, 6, 14, 18, 25, 100]
    else:
        cats = [0, 14, 21, 25, 32, 100]
    labels = ['Essenziale', 'Atletico', 'Forma', 'Media', 'Eccesso']
    colors = ['#ADD8E6', '#90EE90', '#FFD700', '#FFA500', '#FA8072']
    fig, ax = plt.subplots(figsize=(5,3))
    for i in range(len(labels)):
        ax.axvspan(cats[i], cats[i+1], color=colors[i], alpha=0.5)
    ax.axvline(bf_value, color='red', linewidth=2)
    patches = [Patch(color=colors[i], label=labels[i]) for i in range(len(labels))]
    ax.legend(handles=patches, loc='upper right')
    ax.set_xlim(0, 50)
    ax.set_ylim(0,1)
    ax.set_yticks([])
    ax.set_xlabel("% Massa Grassa")
    ax.set_title("% Massa Grassa")
    ax.text(bf_value + 0.3, 0.9, f"{bf_value:.1f}", color='red')
    for spine in ['top','right','left']:
        ax.spines[spine].set_visible(False)
    ax.axhline(0, color='black', linewidth=1)
    plt.tight_layout()
    return fig

# Contenuto principale
st.title("🏋️ Valutazione Antropometrica e Performance")
st.divider()

# Sezione Dati Personali
st.subheader("📋 Dati Personali")
st.markdown(f"- **Nome:** {nome}")
st.markdown(f"- **Età:** {eta} anni")
st.markdown(f"- **Sesso:** {sesso}")
st.markdown(f"- **Peso:** {peso:.1f} kg")
st.markdown(f"- **Altezza:** {altezza:.1f} cm")
st.markdown(f"- **FTP attuale:** {ftp:.0f} W")
st.divider()

# Sezione Antropometria e Zone Allenamento
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚖️ Parametri Antropometrici")
    st.markdown(f"- **BMI:** {bmi:.1f} kg/m²")
    st.markdown(f"- **% Massa Grassa stimata:** {bf:.1f} %")

with col2:
    st.subheader("🎯 Zone di Allenamento")
    st.markdown("**Zone di Potenza (da FTP)**")
    df_power = pd.DataFrame(ftp_zones, columns=["Zona", "Intervallo"])
    st.table(df_power)
    st.markdown("**Zone Cardiache (da HR max)**")
    df_hr = pd.DataFrame(hr_zones, columns=["Zona", "Intervallo"])
    st.table(df_hr)

st.divider()

# Sezione Grafici e Proiezioni
tab1, tab2 = st.tabs(["📊 Grafici BMI/FM", "🔮 Proiezioni"])

with tab1:
    fig_bmi = create_bmi_chart(bmi)
    fig_bf = create_bf_chart(bf, sesso)
    st.pyplot(fig_bmi)
    st.pyplot(fig_bf)

with tab2:
    incremento = st.slider("📈 Miglioramento FTP (%)", min_value=0, max_value=20, value=5)
    new_ftp = ftp * (1 + incremento/100)
    st.write(f"Con un incremento del {incremento}% l'FTP passerebbe da {ftp:.0f} W a circa {new_ftp:.0f} W.")
    st.markdown("**Nuove Zone di Potenza (ipotetiche)**")
    new_zone2 = [
        ("Z1 (riposo)", f"< {0.55*new_ftp:.0f} W"),
        ("Z2 (endurance)", f"{0.55*new_ftp:.0f} - {0.70*new_ftp:.0f} W"),
        ("Z3 (tempo)", f"{0.70*new_ftp:.0f} - {0.82*new_ftp:.0f} W"),
        ("Z4 (soglia)", f"{0.82*new_ftp:.0f} - {0.89*new_ftp:.0f} W"),
        ("Z5 (VO₂max)", f"{0.89*new_ftp:.0f} - {0.94*new_ftp:.0f} W"),
        ("Z6 (anaerob.)", f"{0.94*new_ftp:.0f} - {1.05*new_ftp:.0f} W"),
        ("Z7 (sprint)", f"> {1.05*new_ftp:.0f} W"),
    ]
    df_new = pd.DataFrame(new_zone2, columns=["Zona", "Intervallo"])
    st.table(df_new)

st.divider()

# Genera PDF Report
st.header("🖨️ Report PDF Professionale")

def create_pdf():
    pdf = FPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    # Imposta font Unicode o fallback
    try:
        pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        base_font = "DejaVu"
    except Exception:
        base_font = "Helvetica"
    pdf.add_page()
    pdf.set_font(base_font, 'B', 16)
    # Logo in intestazione (opzionale)
    try:
        pdf.image("logo.png", x=10, y=8, w=30)
    except:
        pass
    pdf.cell(0, 10, "Valutazione Antropometrica e Performance", ln=True, align='C')
    pdf.ln(5)
    pdf.set_draw_color(80, 80, 80)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    # Sezione Dati Personali nel PDF
    pdf.set_font(base_font, 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "Dati Personali", ln=True)
    pdf.set_draw_color(0, 80, 160)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font(base_font, '', 11)
    pdf.cell(0, 6, f"Nome: {nome}", ln=True)
    pdf.cell(0, 6, f"Età: {eta} anni", ln=True)
    pdf.cell(0, 6, f"Sesso: {sesso}", ln=True)
    pdf.cell(0, 6, f"Peso: {peso:.1f} kg", ln=True)
    pdf.cell(0, 6, f"Altezza: {altezza:.1f} cm", ln=True)
    pdf.cell(0, 6, f"FTP: {ftp:.0f} W", ln=True)
    pdf.ln(10)
    # Sezione Antropometria
    pdf.set_font(base_font, 'B', 12)
    pdf.cell(0, 8, "Antropometria", ln=True)
    pdf.set_draw_color(0, 160, 0)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font(base_font, '', 11)
    pdf.cell(0, 6, f"BMI: {bmi:.1f} kg/m^2", ln=True)
    pdf.cell(0, 6, f"% Massa Grassa stimata: {bf:.1f} %", ln=True)
    pdf.ln(10)
    # Sezione Grafici
    pdf.set_font(base_font, 'B', 12)
    pdf.cell(0, 8, "Grafici Antropometrici", ln=True)
    pdf.set_draw_color(160, 0, 0)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    # Creazione delle immagini
    fig_bmi = create_bmi_chart(bmi)
    fig_bf = create_bf_chart(bf, sesso)
    fig_bmi.savefig("bmi_chart.png", dpi=300)
    fig_bf.savefig("bf_chart.png", dpi=300)
    # Inserimento immagini nel PDF
    pdf.image("bmi_chart.png", x=20, w=160)
    pdf.ln(65)
    pdf.image("bf_chart.png", x=20, w=160)
    pdf.ln(70)
    # Sezione FTP e Zone
    pdf.set_font(base_font, 'B', 12)
    pdf.cell(0, 8, "FTP e Zone di Allenamento", ln=True)
    pdf.set_draw_color(255, 140, 0)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    # Tabella Zone Potenza
    pdf.set_font(base_font, 'B', 11)
    pdf.cell(50, 6, "Zona", border=1, align='C', fill=True)
    pdf.cell(60, 6, "Intervallo (W)", border=1, align='C', fill=True)
    pdf.cell(0, 6, "", border=1, ln=True, align='C', fill=True)
    pdf.set_font(base_font, '', 11)
    for zone, interv in ftp_zones:
        pdf.cell(50, 6, zone, border=1)
        pdf.cell(60, 6, interv.replace(" W", ""), border=1)
        pdf.cell(0, 6, "", border=1, ln=True)
    pdf.ln(5)
    # Tabella Zone Cardiache
    pdf.set_font(base_font, 'B', 11)
    pdf.cell(50, 6, "Zona", border=1, align='C', fill=True)
    pdf.cell(60, 6, "Battiti/min", border=1, align='C', fill=True)
    pdf.cell(0, 6, "", border=1, ln=True, align='C', fill=True)
    pdf.set_font(base_font, '', 11)
    for zone, interv in hr_zones:
        pdf.cell(50, 6, zone, border=1)
        pdf.cell(60, 6, interv.replace("< ", "< "), border=1)
        pdf.cell(0, 6, "", border=1, ln=True)
    pdf.ln(10)
    # Sezione Proiezione Miglioramento
    pdf.set_font(base_font, 'B', 12)
    pdf.cell(0, 8, "Proiezione Miglioramento", ln=True)
    pdf.set_draw_color(128, 0, 128)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font(base_font, '', 11)
    pdf.multi_cell(0, 6, f"In caso di un miglioramento del {incremento}% dell'FTP, da {ftp:.0f} W a circa {new_ftp:.0f} W, le zone di potenza si sposterebbero di conseguenza, indicando un potenziale aumento delle prestazioni.")
    # Numerazione pagine e creazione output PDF
    pdf.alias_nb_pages()
    return pdf.output(dest='S').encode('latin-1')

pdf_data = create_pdf()
st.download_button("📄 Scarica Report PDF", data=pdf_data, file_name="report.pdf", mime="application/pdf")
