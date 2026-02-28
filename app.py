# Esempio di miglioramento delle metriche e zone
if submit:
    # ... (calcoli precedenti) ...
    
    # Calcolo FFMI (Fat-Free Mass Index)
    ffmi = massa_magra / (altezza_m**2)
    
    st.header("🔬 Analisi Biometrica Avanzata")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BMI", f"{bmi:.1f} kg·m⁻²")
    m2.metric("FFMI", f"{ffmi:.1f}")
    m3.metric("FTP", f"{ftp:.0f} W")
    m4.metric("Potenza Specifica", f"{wkg:.2f} W·kg⁻¹")

    # Zone di Potenza con nomenclatura scientifica
    st.subheader("⚡ Distribuzione Zone di Potenza (Coggan)")
    zone_data = {
        "Zona": ["Z₁ - Active Recovery", "Z₂ - Endurance", "Z₃ - Tempo", "Z₄ - Lactate Threshold", "Z₅ - VO₂max", "Z₆ - Anaerobic Capacity", "Z₇ - Neuromuscular"],
        "Range %": ["< 55%", "56-75%", "76-90%", "91-105%", "106-120%", "121-150%", "> 150%"],
        "Watt (W)": [
            f"< {0.55*ftp:.0f}",
            f"{0.56*ftp:.0f} - {0.75*ftp:.0f}",
            f"{0.76*ftp:.0f} - {0.90*ftp:.0f}",
            f"{0.91*ftp:.0f} - {1.05*ftp:.0f}",
            f"{1.06*ftp:.0f} - {1.20*ftp:.0f}",
            f"{1.21*ftp:.0f} - {1.50*ftp:.0f}",
            f"> {1.51*ftp:.0f}"
        ]
    }
    st.table(pd.DataFrame(zone_data))
