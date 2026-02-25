def create_pdf(nome, eta, sesso, peso, altezza, ftp, bmi, bf, incremento, new_ftp, ftp_zones, hr_zones, fig_bmi, fig_bf):

    pdf = FPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ----------------------------
    # FONT (Unicode se disponibile)
    # ----------------------------
    try:
        pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
        base_font = "DejaVu"
    except:
        base_font = "Helvetica"

    pdf.add_page()

    # ----------------------------
    # HEADER
    # ----------------------------
    try:
        pdf.image("logo.png", x=10, y=8, w=25)
    except:
        pass

    pdf.set_font(base_font, "B", 18)
    pdf.cell(0, 12, "REPORT PERFORMANCE SPORTIVA", ln=True, align="C")
    pdf.ln(3)

    pdf.set_draw_color(40, 80, 160)
    pdf.set_line_width(1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)

    # ----------------------------
    # DATI PERSONALI
    # ----------------------------
    pdf.set_font(base_font, "B", 13)
    pdf.set_text_color(30, 60, 120)
    pdf.cell(0, 8, "Dati Anagrafici", ln=True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font(base_font, "", 11)
    pdf.ln(3)

    pdf.multi_cell(0, 6,
        f"Nome: {nome}\n"
        f"Eta: {eta} anni\n"
        f"Sesso: {sesso}\n"
        f"Peso: {peso:.1f} kg\n"
        f"Altezza: {altezza:.1f} cm\n"
        f"FTP: {ftp:.0f} W"
    )

    pdf.ln(6)

    # ----------------------------
    # ANTROPOMETRIA
    # ----------------------------
    pdf.set_font(base_font, "B", 13)
    pdf.set_text_color(30, 120, 60)
    pdf.cell(0, 8, "Valutazione Antropometrica", ln=True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font(base_font, "", 11)
    pdf.ln(3)

    pdf.multi_cell(0, 6,
        f"BMI: {bmi:.2f}\n"
        f"Massa grassa stimata: {bf:.1f}%"
    )

    pdf.ln(6)

    # ----------------------------
    # GRAFICI IN MEMORIA (NO FILE)
    # ----------------------------
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png") as tmp1:
        fig_bmi.savefig(tmp1.name, dpi=300, bbox_inches="tight")
        pdf.image(tmp1.name, x=20, w=170)

    pdf.ln(5)

    with tempfile.NamedTemporaryFile(suffix=".png") as tmp2:
        fig_bf.savefig(tmp2.name, dpi=300, bbox_inches="tight")
        pdf.image(tmp2.name, x=20, w=170)

    pdf.ln(10)

    # ----------------------------
    # ZONE POTENZA
    # ----------------------------
    pdf.set_font(base_font, "B", 13)
    pdf.set_text_color(120, 60, 0)
    pdf.cell(0, 8, "Zone di Potenza", ln=True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font(base_font, "", 10)
    pdf.ln(4)

    for zona, intervallo in ftp_zones:
        pdf.cell(60, 6, zona, border=1)
        pdf.cell(0, 6, intervallo, border=1, ln=True)

    pdf.ln(6)

    # ----------------------------
    # ZONE CARDIO
    # ----------------------------
    pdf.set_font(base_font, "B", 13)
    pdf.set_text_color(120, 0, 60)
    pdf.cell(0, 8, "Zone Cardiache", ln=True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font(base_font, "", 10)
    pdf.ln(4)

    for zona, intervallo in hr_zones:
        pdf.cell(60, 6, zona, border=1)
        pdf.cell(0, 6, intervallo, border=1, ln=True)

    pdf.ln(8)

    # ----------------------------
    # PROIEZIONE
    # ----------------------------
    pdf.set_font(base_font, "B", 13)
    pdf.set_text_color(80, 0, 120)
    pdf.cell(0, 8, "Proiezione Miglioramento", ln=True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font(base_font, "", 11)
    pdf.ln(4)

    pdf.multi_cell(0, 6,
        f"Con un incremento del {incremento}% l'FTP passerebbe "
        f"da {ftp:.0f} W a circa {new_ftp:.0f} W.\n"
        "Le zone di potenza si sposterebbero proporzionalmente "
        "indicando un miglioramento prestativo stimato."
    )

    # ----------------------------
    # OUTPUT STABILE STREAMLIT CLOUD
    # ----------------------------
    pdf_bytes = pdf.output(dest="S")

    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode("latin-1")

    return pdf_bytes
