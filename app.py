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
        st.success(f"FTP: {ftp:.2f} W")
    
    # ----------------------
    # INDICI
    # ----------------------
    if ftp and peso > 0:
        
        wkg = ftp / peso
        st.write(f"W/kg: {wkg:.2f}")
        
        # ----------------------
        # ANALISI PROFILO
        # ----------------------
        st.markdown("---")
        st.subheader("Analisi Profilo")
        
        if fm_perc > 18 and wkg < 4:
            profilo = "Migliorabile per ricomposizione"
        elif fm_perc <= 12 and wkg >= 4.5:
            profilo = "Ottimizzato"
        elif fm_perc <= 15 and wkg < 4:
            profilo = "Migliorabile per incremento potenza"
        else:
            profilo = "Approccio combinato consigliato"
        
        st.info(f"Classificazione: {profilo}")
        
        # ----------------------
        # TARGET GUIDATO
        # ----------------------
        st.markdown("---")
        st.subheader("Target guidato")
        
        target_fm = st.number_input("Percentuale target FM (%)", min_value=0.0, max_value=100.0, step=0.1)
        incremento_ftp = st.number_input("Incremento FTP (%)", min_value=0.0, step=0.1)
        
        # ----------------------
        # SIMULAZIONE
        # ----------------------
        if st.button("Calcola simulazione"):
            
            nuovo_peso = peso
            nuova_ftp = ftp
            
            if target_fm > 0:
                nuova_fm_kg = peso * target_fm / 100
                massa_mag = peso - fm_kg
                nuovo_peso = massa_mag + nuova_fm_kg
            
            if incremento_ftp > 0:
                nuova_ftp = ftp * (1 + incremento_ftp / 100)
            
            nuovo_wkg = nuova_ftp / nuovo_peso
            
            st.markdown("---")
            st.subheader("Proiezione Strategica")
            
            st.write(f"Nuovo peso teorico: {nuovo_peso:.2f} kg")
            st.write(f"Nuova FTP: {nuova_ftp:.2f} W")
            st.write(f"Nuovo W/kg: {nuovo_wkg:.2f}")
            
            # Classificazione intervento
            if incremento_ftp <= 5 and target_fm <= 2:
                livello = "Conservativo"
            elif incremento_ftp <= 10 and target_fm <= 4:
                livello = "Moderato"
            elif incremento_ftp <= 15 and target_fm <= 6:
                livello = "Aggressivo ma plausibile"
            else:
                livello = "Non realistico"
            
            st.warning(f"Classificazione intervento: {livello}")
