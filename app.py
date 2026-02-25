import streamlit as st
from datetime import date
from fpdf import FPDF
import pandas as pd
import io

st.set_page_config(page_title="Performance Lab", layout="wide")

# Funzione per formattazione PDF professionale
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'REPORT VALUTAZIONE FUNZIONALE E NUTRIZIONALE', 0, 1, 'C')
        self.set_draw_color(50, 50, 50)
        self.line(10, 20, 200, 20)
        self.ln(10)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 8, f"  {title}", 0, 1, 'L', fill=True)
        self.ln(4)

# --- UI STREAMLIT ---
st.title("🚴 Performance & Nutrition Analyzer")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Anagrafica")
    nome = st.text_input("Nome", "Mario")
    cognome = st.text_input("Cognome", "Rossi")
    data_nascita = st.date_input("Data di nascita", date(1990, 1, 1), format="DD/MM/YYYY")
    
    eta = date.today().year - data_nascita.year - ((date.today().month, date.today().day) < (data_nascita.month, data_nascita.day))

with col2:
    st.subheader("Antropometria")
    c_p1, c_p2 = st.columns(2)
    peso = c_p1.number_input("Peso (kg)", 30.0, 150.0, 75.0)
    altezza = c_p2.number_input("Altezza (cm)", 100.0, 220.0, 175.0)
    fm = st.slider("Massa Grassa (%)", 3.0, 40.0, 15.0)

# Calcoli Bioenergetici
altezza_m = altezza / 100
bmi = peso / (altezza_m**2)
fm_kg = peso * (fm/100)
massa_magra = peso - fm_kg

st.divider()

# --- CALCOLO FTP ---
st.subheader("Parametri di Potenza (FTP)")
c_f1, c_f2 = st.columns([1, 2])

with c_f1:
    metodo = st.selectbox("Test eseguito", ["Immissione diretta", "Test 20 min", "Ramp Test"])
    valore_test = st.number_input("Risultato Test (W)", 0, 1000, 250)
    
    if "20 min" in metodo: ftp = valore_test * 0.95
    elif "Ramp" in metodo: ftp = valore_test * 0.75
    else: ftp = valore_test
    
    wkg = ftp / peso

with c_f2:
    if ftp > 0:
        zone_data = [
            ("Z1 - Recovery", 0, 0.55), ("Z2 - Endurance", 0.56, 0.75),
            ("Z3 - Tempo", 0.76, 0.90), ("Z4 - Threshold", 0.91, 1.05),
            ("Z5 - VO₂max", 1.06, 1.20), ("Z6 - Anaerobic", 1.21, 1.50)
        ]
        zone_df = pd.DataFrame([
            {"Zona": z, "Min (W)": int(ftp*a), "Max (W)": int(ftp*b)} for z, a, b in zone_data
        ])
        st.dataframe(zone_df, use_container_width=True, hide_index=True)

st.divider()

# --- GENERAZIONE PDF ---
if st.button("🚀 Genera Report PDF Professionale"):
    pdf = PDF()
    pdf.add_page()
    
    # Sezione Anagrafica e Antropometria
    pdf.chapter_title("DATI DEL SOGGETTO")
    pdf.set_font("Arial", "", 10)
    
    # Tabella dati rapidi
    data_info = [
        ["Paziente:", f"{nome} {cognome}", "Età:", f"{eta} anni"],
        ["Peso:", f"{peso} kg", "Altezza:", f"{altezza} cm"],
        ["BMI:", f"{bmi:.1f}", "Massa Magra:", f"{massa_magra:.1f} kg"]
    ]
    
    for row in data_info:
        pdf.cell(35, 7, row[0], 0)
        pdf.cell(60, 7, row[1], 0)
        pdf.cell(35, 7, row[2], 0)
        pdf.cell(60, 7, row[3], 0)
        pdf.ln()
    
    pdf.ln(5)
    
    # Sezione Performance
    pdf.chapter_title("VALUTAZIONE DELLA PERFORMANCE")
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"FTP Stimata: {int(ftp)} W  ({wkg:.2f} W/kg)", 0, 1)
    pdf.ln(2)
    
    # Tabella Zone Potenza nel PDF
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(70, 8, "Zona di Allenamento", 1, 0, 'C', True)
    pdf.cell(60, 8, "Range Watt (W)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", "", 10)
    for _, row in zone_df.iterrows():
        pdf.cell(70, 7, row['Zona'], 1)
        pdf.cell(60, 7, f"{row['Min (W)']} - {row['Max (W)']} W", 1, 1, 'C')

    # Footer o Note
    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 5, "Nota: I parametri riportati sono stime basate sui test sottomassimali inseriti. Consultare sempre un professionista prima di iniziare programmi di allenamento ad alta intensità.")

    # Output come buffer per il download
    pdf_output = pdf.output(dest='S').encode('latin-1')
    st.download_button(
        label="📥 Scarica Report PDF",
        data=pdf_output,
        file_name=f"Report_{cognome}_{nome}.pdf",
        mime="application/pdf"
    )
