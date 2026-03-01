# ---------------------------------------------------------
# UTILITY PER CODIFICA PDF
# ---------------------------------------------------------

def clean_text_for_pdf(text):
    """Converte i caratteri Unicode in ASCII standard per compatibilità FPDF latin-1."""
    replacements = {
        "₂": "2", "⁻": "-", "¹": "1", "·": "*", 
        "₀": "0", "₃": "3", "₄": "4", "₅": "5",
        "₆": "6", "₇": "7", "₈": "8", "₉": "9"
    }
    for uni, asc in replacements.items():
        text = text.replace(uni, asc)
    return text

# ---------------------------------------------------------
# GENERATORE PDF AGGIORNATO
# ---------------------------------------------------------

def create_pdf(atleta, dati_attuali, dati_target):
    # Usiamo fpdf o fpdf2 (consigliata fpdf2 per Streamlit)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Titolo
    pdf.cell(190, 10, clean_text_for_pdf(f"Performance Report: {atleta['nome']} {atleta['cognome']}"), 0, 1, 'C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 10, f"Data Valutazione: {date.today().isoformat()}", 0, 1, 'C')
    pdf.ln(10)

    # Tabella Comparativa
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, "Parametro", 1, 0, 'C', True)
    pdf.cell(65, 10, "Attuale (Stato A)", 1, 0, 'C', True)
    pdf.cell(65, 10, "Obiettivo (Stato B)", 1, 1, 'C', True)

    pdf.set_font("Arial", '', 11)
    
    # Lista metriche con pulizia caratteri
    metrics = [
        ("Peso Corporeo", f"{dati_attuali['peso']} kg", f"{dati_target['peso']} kg"),
        ("Massa Grassa", f"{dati_attuali['fm']}%", f"{dati_target['fm']}%"),
        ("Potenza Soglia (FTP)", f"{int(dati_attuali['ftp'])} W", f"{int(dati_target['ftp'])} W"),
        ("Potenza Specifica", f"{dati_attuali['wkg']:.2f} W/kg", f"{dati_target['wkg']:.2f} W/kg"),
        ("Tempo Scalata", f"{dati_attuali['tempo']:.2f} min", f"{dati_target['tempo']:.2f} min"),
    ]

    for label, val_a, val_b in metrics:
        pdf.cell(60, 10, clean_text_for_pdf(label), 1)
        pdf.cell(65, 10, clean_text_for_pdf(val_a), 1)
        pdf.cell(65, 10, clean_text_for_pdf(val_b), 1)
        pdf.ln()

    pdf.ln(10)
    
    # Conclusioni Scientifiche
    diff_tempo = dati_attuali['tempo'] - dati_target['tempo']
    diff_wkg = dati_target['wkg'] - dati_attuali['wkg']
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 102, 204)
    pdf.multi_cell(190, 10, clean_text_for_pdf(
        f"ANALISI DEI RISULTATI:\n"
        f"Il miglioramento del rapporto potenza/peso (+{diff_wkg:.2f} W/kg) "
        f"permette un risparmio cronometrico stimato di {diff_tempo:.2f} minuti sulla salita indicata."
    ), 0, 'L')
    
    # Ritorna i bytes direttamente (compatibile con Streamlit download_button)
    return pdf.output()

# ---------------------------------------------------------
# NEL CORPO PRINCIPALE (Modifica il Button)
# ---------------------------------------------------------

# ... dentro "if st.button('🚀 Elabora Analisi Scientifica'):" ...

        # Generazione PDF (senza .encode('latin-1') esterno)
        pdf_bytes = create_pdf(atleta_info, d_att, d_tar)
        
        st.download_button(
            label="📄 Scarica Report PDF Professionale",
            data=bytes(pdf_bytes), # Assicuriamoci che siano bytes
            file_name=f"Report_{cognome}_{date.today().isoformat()}.pdf",
            mime="application/pdf"
        )
