import streamlit as st
from PIL import Image
from datetime import date

# ------------------------------
# LOGO
# ------------------------------
logo = Image.open("logo.png")
st.image(logo, width=220)

st.title("DB Nutrition & Performance")
st.markdown("---")

# ------------------------------
# ATTIVAZIONE MODULO
# ------------------------------
st.header("Inserimento dati analitici")
nome = st.text_input("Digita il nome dell’atleta per iniziare")

if nome:

    st.success("Modulo valutazione attivato")

    # ------------------------------
    # ANAGRAFICA
    # ------------------------------
    st.header("1. Anagrafica")

    cognome = st.text_input("Cognome")

    data_nascita = st.date_input(
        "Data di nascita (gg/mm/aaaa)",
        min_value=date(1940, 1, 1),
        max_value=date.today(),
        format="DD/MM/YYYY"
    )

    today = date.today()
    eta = today.year - data_nascita.year - (
        (today.month, today.day) < (data_nascita.month, data_nascita.day)
    )

    st.write(f"Età calcolata: **{eta} anni**")

    # ------------------------------
    # DATI ANTROPOMETRICI
    # ------------------------------
    st.header("2. Composizione corporea")

    peso = st.number_input("Peso (kg)", min_value=30.0, max_value=150.0, step=0.1)
    fat_mass_perc = st.number_input("Massa grassa (%)", min_value=3.0, max_value=50.0, step=0.1)

    fat_mass_kg = peso * (fat_mass_perc / 100)
    massa_magra = peso - fat_mass_kg

    st.write(f"Massa grassa (kg): **{fat_mass_kg:.2f} kg**")
    st.write(f"Massa magra stimata: **{massa_magra:.2f} kg**")

    # ------------------------------
    # PERFORMANCE
    # ------------------------------
    st.header("3. Parametri funzionali")

    ftp = st.number_input("FTP (Watt)", min_value=50, max_value=600, step=1)

    w_kg = ftp / peso if peso > 0 else 0
    st.write(f"Watt/kg attuali: **{w_kg:.2f} W/kg**")

    # ------------------------------
    # TARGET STRATEGICO
    # ------------------------------
    st.header("4. Impostazione Target")

    target_fm = st.number_input("Target massa grassa (%)", min_value=3.0, max_value=20.0, step=0.1)
    incremento_ftp = st.number_input("Incremento FTP (%)", min_value=0.0, max_value=50.0, step=0.5)

    # Nuovo peso mantenendo massa magra costante
    nuova_fm_kg = massa_magra * (target_fm / (100 - target_fm))
    nuovo_peso = massa_magra + nuova_fm_kg

    nuova_ftp = ftp * (1 + incremento_ftp / 100)
    nuovo_wkg = nuova_ftp / nuovo_peso if nuovo_peso > 0 else 0

    # ------------------------------
    # PROIEZIONE
    # ------------------------------
    st.header("5. Proiezione Strategica Personalizzata")

    st.write(f"Nuova percentuale massa grassa: **{target_fm:.1f}%**")
    st.write(f"Nuovo peso teorico: **{nuovo_peso:.2f} kg**")
    st.write(f"Nuova FTP stimata: **{nuova_ftp:.2f} W**")
    st.write(f"Nuovo W/kg: **{nuovo_wkg:.2f} W/kg**")

    # ------------------------------
    # INQUADRAMENTO
    # ------------------------------
    st.header("6. Inquadramento Metabolico-Funzionale")

    st.write("""
    L’integrazione tra composizione corporea e potenza relativa consente 
    di delineare un profilo adattativo specifico, utile per l’ottimizzazione 
    della performance attraverso strategie mirate di ricomposizione corporea 
    e/o incremento della capacità funzionale.
    """)
