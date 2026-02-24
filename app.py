import streamlit as st

st.set_page_config(page_title="DB Nutrition & Performance", layout="centered")

st.title("DB Nutrition & Performance")

st.markdown("---")

st.header("Attivazione sistema")

trigger = st.text_input("Scrivi 'NUOVO ATLETA' per attivare il sistema")

if trigger == "NUOVO ATLETA":
    
    st.success("Sistema attivato correttamente.")
    
    # ----------------------
    # ANAGRAFICA
    # ----------------------
    st.subheader("Anagrafica")
    nome = st.text_input("Nome")
    cognome = st.text_input("Cognome")
    eta = st.number_input("Età", min_value=0, step=1)
    
    st.markdown("---")
    
    # ----------------------
    # COMPOSIZIONE CORPOREA
    # ----------------------
    st.subheader("Composizione corporea")
    
    peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
    altezza = st.number_input("Altezza (cm)", min_value=0.0, step=0.1)
    fm_perc = st.number_input("Fat Mass (%)", min_value=0.0, max_value=100.0, step=0.1)
    ffm = st.number_input("FFM (kg)", min_value=0.0, step=0.1)
    massa_muscolare = st.number_input("Massa muscolare (kg)", min_value=0.0, step=0.1)
    
    fm_kg = None
    if peso > 0 and fm_perc > 0:
        fm_kg = peso * fm_perc / 100
        st.info(f"Fat Mass calcolata: {fm_kg:.2f} kg")
    
    st.markdown("---")
    
    # ----------------------
    # TEST DI POTENZA
    # ----------------------
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
            st.success(f"FTP calcolata (95%): {ftp:.2f} W")
    
    elif tipo_test == "2x8 minuti":
        p1 = st.number_input("8' prova 1 (W)", min_value=0.0)
        p2 = st.number_input("8' prova 2 (W)", min_value=0.0)
        if p1 > 0 and p2 > 0:
            ftp = ((p1 + p2) / 2) * 0.90
            st.success(f"FTP calcolata (90% media): {ftp:.2f} W")
    
    elif tipo_test == "FTP disponibile":
        ftp_input = st.number_input("Inserisci FTP (W)", min_value=0.0)
        if ftp_input > 0:
            ftp = ftp_input
            st.success(f"FTP inserita: {ftp:.2f} W")
    
    # ----------------------
    # INDICI AVANZATI
    # ----------------------
    if ftp and peso > 0:
        st.markdown("---")
        st.subheader("Indici di Performance")
        
        wkg = ftp / peso
        st.write(f"W/kg: {wkg:.2f}")
        
        if ffm > 0:
            wkg_ffm = ftp / ffm
            st.write(f"W/kg FFM: {wkg_ffm:.2f}")
        
        if massa_muscolare > 0:
            pot_spec = ftp / massa_muscolare
            st.write(f"Potenza specifica muscolare: {pot_spec:.2f}")
        
        # ----------------------
        # ZONE DI POTENZA (COGGAN)
        # ----------------------
        st.markdown("---")
        st.subheader("Zone di Potenza (Coggan)")
        
        zone = {
            "Z1 (<55%)": (0, ftp * 0.55),
            "Z2 (56-75%)": (ftp * 0.56, ftp * 0.75),
            "Z3 (76-90%)": (ftp * 0.76, ftp * 0.90),
            "Z4 (91-105%)": (ftp * 0.91, ftp * 1.05),
            "Z5 (106-120%)": (ftp * 1.06, ftp * 1.20),
            "Z6 (121-150%)": (ftp * 1.21, ftp * 1.50),
            "Z7 (>150%)": (ftp * 1.50, ftp * 2)
        }
        
        for nome_zona, valori in zone.items():
            st.write(f"{nome_zona}: {valori[0]:.0f} - {valori[1]:.0f} W")
