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

st.header("Inserimento dati analitici")
nome = st.text_input("Digita il nome dell’atleta per iniziare")

if nome:

    # ------------------------------
    # ANAGRAFICA
    # ------------------------------
    st.subheader("1. Anagrafica")

    cognome = st.text_input("Cognome")

    data_nascita = st.date_input(
        "Data di nascita (gg/mm/aaaa)",
        min_value=date(1940,1,1),
        max_value=date.today(),
        format="DD/MM/YYYY"
    )

    today = date.today()
    eta = today.year - data_nascita.year - (
        (today.month, today.day) < (data_nascita.month, data_nascita.day)
    )

    st.write(f"Età: **{eta} anni**")

    # ------------------------------
    # COMPOSIZIONE CORPOREA
    # ------------------------------
    st.subheader("2. Composizione corporea")

    peso = st.number_input("Peso (kg)", min_value=30.0, max_value=150.0, step=0.1)
    fm_perc = st.number_input("Massa grassa (%)", min_value=3.0, max_value=50.0, step=0.1)

    fm_kg = peso * (fm_perc / 100)
    massa_magra = peso - fm_kg

    st.write(f"Massa grassa: **{fm_kg:.2f} kg**")
    st.write(f"Massa magra: **{massa_magra:.2f} kg**")

    # ------------------------------
    # TEST DI POTENZA
    # ------------------------------
    st.subheader("3. Test di Potenza")

    tipo_test = st.selectbox(
        "Tipo test",
        ["20 minuti", "2x8 minuti", "FTP disponibile"]
    )

    ftp = 0

    if tipo_test == "20 minuti":
        media20 = st.number_input("Potenza media 20' (W)", min_value=0.0)
        ftp = media20 * 0.95

    elif tipo_test == "2x8 minuti":
        p1 = st.number_input("8' prova 1 (W)", min_value=0.0)
        p2 = st.number_input("8' prova 2 (W)", min_value=0.0)
        ftp = ((p1 + p2) / 2) * 0.90

    elif tipo_test == "FTP disponibile":
        ftp = st.number_input("FTP (W)", min_value=0.0)

    if ftp > 0:
        st.write(f"FTP calcolata: **{ftp:.2f} W**")
        wkg = ftp / peso
        st.write(f"W/kg attuale: **{wkg:.2f} W/kg**")

    # ------------------------------
    # FREQUENZA CARDIACA
    # ------------------------------
    st.subheader("4. Frequenza Cardiaca")

    uso_cardio = st.selectbox("Ha indossato il cardio?", ["No", "Sì"])

    if uso_cardio == "Sì":
        fc_media = st.number_input("FC media test (bpm)", min_value=0)
        fthr = fc_media

        if fthr > 0:
            st.write(f"FTHR: **{fthr} bpm**")

            st.write("Zone cardiache:")
            st.write(f"Z1 (<81%): {fthr*0.81:.0f} bpm")
            st.write(f"Z2 (81-89%): {fthr*0.89:.0f} bpm")
            st.write(f"Z3 (90-93%): {fthr*0.93:.0f} bpm")
            st.write(f"Z4 (94-99%): {fthr*0.99:.0f} bpm")
            st.write(f"Z5 (>100%): > {fthr:.0f} bpm")

    # ------------------------------
    # TARGET
    # ------------------------------
    st.subheader("5. Proiezione Strategica")

    target_fm = st.number_input("Target massa grassa (%)", min_value=3.0, max_value=20.0, step=0.1)
    incremento_ftp = st.number_input("Incremento FTP (%)", min_value=0.0, max_value=50.0, step=0.5)

    nuova_fm_kg = massa_magra * (target_fm / (100 - target_fm))
    nuovo_peso = massa_magra + nuova_fm_kg

    nuova_ftp = ftp * (1 + incremento_ftp / 100)
    nuovo_wkg = nuova_ftp / nuovo_peso if nuovo_peso > 0 else 0

    st.write(f"Nuovo peso: **{nuovo_peso:.2f} kg**")
    st.write(f"Nuova FTP: **{nuova_ftp:.2f} W**")
    st.write(f"Nuovo W/kg: **{nuovo_wkg:.2f} W/kg**")
