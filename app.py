import streamlit as st

st.set_page_config(page_title="DB Nutrition & Performance", layout="centered")

st.title("DB Nutrition & Performance")

st.markdown("---")

st.header("Attivazione sistema")

trigger = st.text_input("Scrivi 'NUOVO ATLETA' per attivare il sistema")

if trigger == "NUOVO ATLETA":
    st.success("Sistema attivato correttamente.")
    st.subheader("Anagrafica")
    nome = st.text_input("Nome")
    cognome = st.text_input("Cognome")
    eta = st.number_input("Età", min_value=0, step=1)
