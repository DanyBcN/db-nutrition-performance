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
    
    if peso > 0 and fm_perc > 0:
        fm_kg = peso * fm_perc / 100
        st.info(f"Fat Mass calcolata: {fm_kg:.2f} kg")
