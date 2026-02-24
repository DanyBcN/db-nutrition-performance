import streamlit as st

st.set_page_config(page_title="DB Nutrition & Performance", layout="centered")

st.title("DB Nutrition & Performance")
st.markdown("---")

st.header("Attivazione sistema")

trigger = st.text_input("Scrivi 'NUOVO ATLETA' per attivare il sistema")

if trigger == "NUOVO ATLETA":

    st.success("Sistema attivato correttamente.")

    # =========================
    # RACCOLTA DATI
    # =========================
    st.subheader("Anagrafica")
    nome = st.text_input("Nome")
    cognome = st.text_input("Cognome")
    eta = st.number_input("Età", min_value=0, step=1)

    st.markdown("---")

    st.subheader("Composizione corporea")
    peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
    fm_perc = st.number_input("Fat Mass (%)", min_value=0.0, max_value=100.0, step=0.1)
    ffm = st.number_input("FFM (kg)", min_value=0.0, step=0.1)
    massa_muscolare = st.number_input("Massa muscolare (kg)", min_value=0.0, step=0.1)

    fm_kg = None
    if peso > 0 and fm_perc > 0:
        fm_kg = peso * fm_perc / 100

    st.markdown("---")

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

    # =========================
    # ELABORAZIONE
    # =========================
    if ftp and peso > 0 and fm_kg is not None:

        wkg = ftp / peso
        wkg_ffm = ftp / ffm if ffm > 0 else None
        pot_spec = ftp / massa_muscolare if massa_muscolare > 0 else None

        # Classificazione profilo
        if fm_perc > 18 and wkg < 4:
            profilo = "Migliorabile per ricomposizione"
        elif fm_perc <= 12 and wkg >= 4.5:
            profilo = "Ottimizzato"
        elif fm_perc <= 15 and wkg < 4:
            profilo = "Migliorabile per incremento potenza"
        else:
            profilo = "Approccio combinato consigliato"

        # =========================
        # OUTPUT REFERTO
        # =========================

        st.markdown("---")
        st.header("REFERTO ANALITICO")

        st.markdown("### 1. Parametri Antropometrici")
        st.write(f"Peso: {peso:.2f} kg")
        st.write(f"Massa grassa: {fm_perc:.1f}% ({fm_kg:.2f} kg)")
        st.write(f"Massa magra (FFM): {ffm:.2f} kg")

        st.markdown("### 2. Valutazione Funzionale")
        st.write(f"Functional Threshold Power (FTP): {ftp:.2f} W")

        st.markdown("### 3. Zone di Allenamento – Potenza")
        zone = {
            "Z1 (<55%)": (0, ftp * 0.55),
            "Z2 (56–75%)": (ftp * 0.56, ftp * 0.75),
            "Z3 (76–90%)": (ftp * 0.76, ftp * 0.90),
            "Z4 (91–105%)": (ftp * 0.91, ftp * 1.05),
            "Z5 (106–120%)": (ftp * 1.06, ftp * 1.20),
            "Z6 (121–150%)": (ftp * 1.21, ftp * 1.50),
            "Z7 (>150%)": (ftp * 1.50, ftp * 2),
        }

        for nome_zona, valori in zone.items():
            st.write(f"{nome_zona}: {valori[0]:.0f} – {valori[1]:.0f} W")

        st.markdown("### 4. Indici di Performance Relativa")
        st.write(f"W/kg: {wkg:.2f}")
        if wkg_ffm:
            st.write(f"W/kg FFM: {wkg_ffm:.2f}")
        if pot_spec:
            st.write(f"Potenza specifica muscolare: {pot_spec:.2f}")

        st.markdown("### 5. Analisi Interpretativa Specialistica")
        st.write(f"Classificazione del profilo fisiologico: {profilo}")

        st.markdown("### 6. Inquadramento Metabolico-Funzionale")
        st.write(
            "L’integrazione tra composizione corporea e potenza relativa "
            "consente di delineare un profilo adattativo specifico, "
            "utile per l’ottimizzazione della performance attraverso "
            "strategie mirate di ricomposizione corporea e/o incremento della capacità funzionale."
        )

        st.markdown("### 7. Proiezione Strategica Personalizzata")
        st.write(
            "Eventuali interventi correttivi dovranno essere modulati "
            "in funzione del rapporto tra massa grassa, massa magra "
            "e potenza espressa, mantenendo coerenza con i principi "
            "di fisiologia dell’esercizio e adattamento metabolico."
        )
