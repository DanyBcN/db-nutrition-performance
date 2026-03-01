import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from fpdf import FPDF

# ... (Database init rimane lo stesso)

class BioPerformance:
    # Benchmark FM per ciclisti (Dati letteratura sportiva)
    @staticmethod
    def get_fm_benchmarks():
        return pd.DataFrame({
            "Categoria": ["Pro World Tour", "Continental/U23", "Elite Amatori", "Granfondista"],
            "Range FM Maschile (%)": ["5 - 8%", "8 - 11%", "10 - 14%", "13 - 17%"],
            "Range FM Femminile (%)": ["12 - 16%", "16 - 20%", "18 - 22%", "21 - 25%"]
        })

    @staticmethod
    def get_eval(profilo, peso, altezza, fm):
        bmi = peso / ((altezza/100)**2)
        ffm = peso * (1 - fm/100)
        eval_text = f"Analisi Biometrica:\n- BMI: {bmi:.1f} kg/m2\n- Massa Magra (FFM): {ffm:.1f} kg\n"
        eval_text += f"Profilo: {profilo}. "
        if fm > 15 and profilo == "Scalatore":
            eval_text += "Si consiglia riduzione della massa grassa per ottimizzare il VAM."
        return eval_text

    @staticmethod
    def estimate_time(watt, peso, km, pend, bike_w):
        f_res = (peso + bike_w) * 9.81 * ((pend/100) + 0.005)
        if f_res <= 0 or watt <= 0: return 0
        speed_ms = watt / f_res
        return (km * 1000 / speed_ms) / 60

# --- LOGICA PDF SICURA ---
def pdf_safe(text):
    if not text: return ""
    return str(text).encode('ascii', 'ignore').decode('ascii')

# --- INTERFACCIA STREAMLIT ---
# ... (Inputs rimangono invariati rispetto all'ultima versione)

if 'report' in st.session_state:
    r = st.session_state['report']
    st.divider()
    
    # 1. CONFRONTO PESO E FAT MASS
    st.subheader("⚖️ Ricomposizione Corporea Target")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Peso Attuale", f"{r['p_a']} kg")
    c2.metric("Peso Target", f"{r['p_t']} kg", f"{r['p_t']-r['p_a']:.1f} kg", delta_color="inverse")
    c3.metric("FM Attuale", f"{r['fm_a']}%")
    c4.metric("FM Target", f"{r['fm_t']}%", f"{r['fm_t']-r['fm_a']:.1f}%", delta_color="inverse")

    # 2. PROIEZIONE TEMPI
    st.subheader("⏱️ Proiezione Performance in Salita")
    ct1, ct2, ct3 = st.columns(3)
    ct1.metric("Tempo Oggi", f"{r['t_a']:.2f} min")
    ct2.metric("Tempo Target", f"{r['t_t']:.2f} min")
    ct3.metric("Guadagno", f"-{r['t_a']-r['t_t']:.2f} min")

    # 3. BENCHMARK CATEGORIE
    with st.expander("📊 Benchmark Fat Mass (FM) per Categoria"):
        st.table(BioPerformance.get_fm_benchmarks())
        st.caption("Nota: I valori possono variare in base alla tecnica di misurazione (BIA, Plicometria, DEXA).")

    # 4. GENERAZIONE PDF AGGIORNATO
    if st.button("📄 GENERA REPORT PDF COMPLETO"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, pdf_safe(f"REPORT: {r['nome']} {r['cognome']}"), 0, 1, 'C')
        
        # Sezione Composizione Corporea nel PDF
        pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, "COMPOSIZIONE CORPOREA (ATTUALE vs TARGET)", 1, 1, 'L', True)
        pdf.set_font("Arial", '', 11)
        pdf.cell(95, 8, pdf_safe(f"Peso Attuale: {r['p_a']} kg"), 1, 0)
        pdf.cell(95, 8, pdf_safe(f"Peso Target: {r['p_t']} kg"), 1, 1)
        pdf.cell(95, 8, pdf_safe(f"FM Attuale: {r['fm_a']}%"), 1, 0)
        pdf.cell(95, 8, pdf_safe(f"FM Target: {r['fm_t']}%"), 1, 1); pdf.ln(5)

        # Tempi
        pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "PROIEZIONE TEMPI", 1, 1, 'L', True)
        pdf.set_font("Arial", '', 11)
        pdf.cell(190, 8, pdf_safe(f"Tempo Attuale: {r['t_a']:.2f} min"), 1, 1)
        pdf.cell(190, 8, pdf_safe(f"Tempo Target: {r['t_t']:.2f} min"), 1, 1)
        pdf.set_font("Arial", 'B', 11); pdf.cell(190, 10, pdf_safe(f"MIGLIORAMENTO: -{r['t_a']-r['t_t']:.2f} minuti"), 1, 1, 'C'); pdf.ln(5)

        # Tabella Zone
        # ... (Stessa logica di stampa zone cardio/potenza del messaggio precedente)
        
        st.download_button("💾 Scarica PDF", data=pdf.output(dest='S').encode('latin-1', 'ignore'), file_name="Report_Atleta.pdf")
