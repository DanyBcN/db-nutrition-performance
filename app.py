import streamlit as st
from datetime import datetime

st.set_page_config(page_title="DB Nutrition & Performance", layout="centered")

st.title("DB Nutrition & Performance")
st.markdown("---")

# =========================
# ATTIVAZIONE
# =========================

st.header("Inserimento dati analitici")

nome = st.text_input("Digita il nome dell’atleta per iniziare")

if nome:

    st.success("Modulo valutazione attivato")

    # =========================
    # ANAGRAFICA
    # =========================

    st.subheader("Anagrafica")

    cognome = st.text_input("Cognome")

    data_nascita = st.date_input(
        "Data di nascita (gg/mm/aaaa)",
        value=datetime(1990, 1, 1),
        min_value=datetime(1950, 1, 1),
        max_value=datetime.today(),
        format="DD/MM/YYYY"
    )

    oggi = datetime.today()

    eta = oggi.year - data_nascita.year - (
        (oggi.month, oggi.day) < (data_nascita.month, data_nascita.day)
    )

    st.info(f"Età calcolata: {eta} anni")

    st.markdown("---")

    # =========================
    # COMPOSIZIONE CORPOREA
    # =========================

    st.subheader("Composizione corporea")

    peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
    fm_perc = st.number_input("Fat Mass (%)", min_value=0.0, max_value=100.0, step=0.1)
    ffm = st.number_input("FFM (kg)", min_value=0.0, step=0.1)
    massa_muscolare = st.number_input("Massa muscolare (kg)", min_value=0.0, step=0.1)

    fm_kg = None
    if peso > 0 and fm_perc > 0:
        fm_kg = peso * fm_perc / 100
        st.info(f"Fat Mass calcolata: {fm_kg:.2f} kg")

    st.markdown("---")

    # =========================
    # TEST DI POTENZA
    # =========================

    st.subheader("Test di Potenza")

    tipo_test = st.selectbox(
        "Tipo test",
        ["Seleziona", "20 minuti", "2x8 minuti", "FTP disponibile"]
    )

    ftp = None

    if tipo_test == "20 minuti":
        media_20 = st.number_input("Potenza media 20' (W)", min_value=0.0)
        if media_20 > 0:
            ftp = media_20 * 0.95

    elif tipo_test == "2x8 minuti":
        p1 = st.number_input("8' prova 1 (W)", min_value=0.0)
        p2 = st.number_input("8' prova 2 (W)", min_value=0.0)
        if p1 > 0 and p2 > 0:
            ftp = ((p1 + p2) / 2) * 0.90

    elif tipo_test == "FTP disponibile":
        ftp_input = st.number_input("Inserisci FTP (W)", min_value=0.0)
        if ftp_input > 0:
            ftp = ftp_input

    if ftp:
        st.success(f"FTP calcolata: {ftp:.2f} W")

    st.markdown("---")

    # =========================
    # FREQUENZA CARDIACA
    # =========================

    st.subheader("Frequenza Cardiaca")

    uso_cardio = st.selectbox("Ha indossato il cardio?", ["No", "Sì"])

    fthr = None

    if uso_cardio == "Sì":
        fc_media = st.number_input("FC media del test (bpm)", min_value=0)
        if fc_media > 0:
            fthr = fc_media
            st.info(f"FTHR calcolata: {fthr:.0f} bpm")

    # =========================
    # ELABORAZIONE
    # =========================

    if ftp and peso > 0 and fm_kg is not None:

        wkg = ftp / peso
        wkg_ffm = ftp / ffm if ffm > 0 else None
        pot_spec = ftp / massa_muscolare if massa_muscolare > 0 else None

        # =========================
        # REFERTO
        # =========================

        st.markdown("---")
        st.header("REFERTO ANALITICO")

        st.markdown("### 1. Parametri Antropometrici")
        st.write(f"Nome: {nome} {cognome}")
        st.write(f"Età: {eta} anni")
        st.write(f"Peso: {peso:.2f} kg")
        st.write(f"Massa grassa: {fm_perc:.1f}% ({fm_kg:.2f} kg)")
        st.write(f"Massa magra (FFM): {ffm:.2f} kg")

        st.markdown("### 2. Valutazione Funzionale")
        st.write(f"Functional Threshold Power (FTP): {ftp:.2f} W")

        st.markdown("### 3. Indici di Performance Relativa")
        st.write(f"W/kg: {wkg:.2f}")
        if wkg_ffm:
            st.write(f"W/kg FFM: {wkg_ffm:.2f}")
        if pot_spec:
            st.write(f"Potenza specifica muscolare: {pot_spec:.2f}")

        # =========================
        # PROIEZIONE STRATEGICA
        # =========================

        st.markdown("---")
        st.subheader("Impostazione Target")

        target_fm = st.number_input("Target massa grassa (%)", min_value=0.0, step=0.1)
        incremento_ftp = st.number_input("Incremento FTP (%)", min_value=0.0, step=0.1)

        if st.button("Calcola Proiezione"):

            nuovo_peso = peso
            nuova_ftp = ftp

            if target_fm > 0:
                massa_mag = peso - fm_kg
                nuova_fm_kg = peso * target_fm / 100
                nuovo_peso = massa_mag + nuova_fm_kg

            if incremento_ftp > 0:
                nuova_ftp = ftp * (1 + incremento_ftp / 100)

            nuovo_wkg = nuova_ftp / nuovo_peso

            st.markdown("### 4. Proiezione Strategica Personalizzata")

            if target_fm > 0:
                st.write(f"Nuova percentuale massa grassa: {target_fm:.1f}%")
                st.write(f"Nuovo peso teorico: {nuovo_peso:.2f} kg")

            if incremento_ftp > 0:
                st.write(f"Nuova FTP stimata: {nuova_ftp:.2f} W")

            st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")
