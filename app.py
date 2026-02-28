if submit:
    # --- CALCOLI AVANZATI ---
    # FFMI (Fat-Free Mass Index) e FFMI Normalizzato (per 1.80m)
    ffmi = massa_magra / (altezza_m**2)
    ffmi_norm = ffmi + 6.1 * (1.8 - altezza_m)
    
    # Rapporto Potenza/Peso e stima VO₂max (metodo Daniels/Storer)
    wkg = ftp / peso
    vo2_est = (ftp * 10.8 / peso) + 7  # Stima indiretta in ml·kg⁻¹·min⁻¹

    # --- UI: DASHBOARD RISULTATI ---
    st.markdown("---")
    st.header("🔬 Analisi Biomeccanica e Metabolica")

    # Primo Blocco: Composizione Corporea
    with st.container():
        st.subheader("📊 Composizione Corporea Avanzata")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("BMI", f"{bmi:.1f} kg·m⁻²")
        c2.metric("Massa Magra (FFM)", f"{massa_magra:.1f} kg")
        c3.metric("FFMI", f"{ffmi:.2f}")
        c4.metric("FFMI Norm.", f"{ffmi_norm:.2f}", help="Normalizzato su altezza 1.80m")
        
        # Interpretazione clinica FFMI
        if ffmi_norm > 22:
            st.info("💡 **Nota Clinica:** L'atleta presenta un indice di massa magra elevato, tipico di discipline di potenza o atleti d'elite.")

    st.write(" ")

    # Secondo Blocco: Performance & Power Output
    with st.container():
        st.subheader("⚡ Profilo di Potenza (Power Profile)")
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("FTP Target", f"{ftp:.0f} W")
        p2.metric("Specific Power", f"{wkg:.2f} W·kg⁻¹")
        p3.metric("VO₂max Est.", f"{vo2_est:.1f} ml·kg⁻¹·min⁻¹")
        p4.metric("BMR (Cunningham)", f"{bmr_cunningham:.0f} kcal·d⁻¹")

    st.write(" ")

    # Terzo Blocco: Zone di Allenamento
    with st.expander("📌 Ripartizione Zone di Carico Metabolico (Modello Coggan)", expanded=True):
        zone_data = {
            "Livello": ["Z₁", "Z₂", "Z₃", "Z₄", "Z₅", "Z₆", "Z₇"],
            "Descrizione Fisiologica": [
                "Active Recovery (Recupero)", 
                "Endurance (Fondo Aerobico)", 
                "Tempo (Ritmo)", 
                "Lactate Threshold (Soglia)", 
                "VO₂max (Potenza Aerobica)", 
                "Anaerobic Capacity", 
                "Neuromuscular Power"
            ],
            "Intensità (% FTP)": ["< 55%", "56-75%", "76-90%", "91-105%", "106-120%", "121-150%", "> 150%"],
            "Range Potenza (W)": [
                f"0 - {0.55*ftp:.0f}",
                f"{0.56*ftp:.0f} - {0.75*ftp:.0f}",
                f"{0.76*ftp:.0f} - {0.90*ftp:.0f}",
                f"{0.91*ftp:.0f} - {1.05*ftp:.0f}",
                f"{1.06*ftp:.0f} - {1.20*ftp:.0f}",
                f"{1.21*ftp:.0f} - {1.50*ftp:.0f}",
                f"> {1.51*ftp:.0f}"
            ]
        }
        df_zones = pd.DataFrame(zone_data)
        st.table(df_zones)

    # Nota scientifica a piè di pagina
    st.caption("I calcoli metabolici utilizzano l'equazione di Cunningham per il BMR e il modello di Coggan per i domini di potenza.")
