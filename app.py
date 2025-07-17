import streamlit as st
import pandas as pd
import time
import io
import zipfile
import datetime as dt
import matplotlib.pyplot as plt

from src.xml_processor import process_xml

st.set_page_config(page_title="XML Smurfit Reparator", layout="wide")
st.title("📦 XML Smurfit Reparator – PositionLevel Fixer")
st.markdown("Chargez vos fichiers XML pour corriger automatiquement les balises manquantes.")

uploaded_files = st.file_uploader(
    "Sélectionnez un ou plusieurs fichiers XML",
    type=["xml"],
    accept_multiple_files=True
)

if st.button("Lancer le traitement") and uploaded_files:
    logs = []
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zf:
        progress_bar = st.progress(0)
        for idx, file in enumerate(uploaded_files, 1):
            start = time.time()
            try:
                corrected, added = process_xml(file.read())
                zf.writestr(file.name, corrected.decode("utf-8"))
                status = "✅ OK"
            except Exception as e:
                added = 0
                status = f"❌ Erreur : {e}"
            duration = round(time.time() - start, 2)
            logs.append({
                "Fichier": file.name,
                "Statut": status,
                "Balises ajoutées": added,
                "Durée (s)": duration
            })
            progress_bar.progress(idx / len(uploaded_files))

    progress_bar.empty()
    st.success("Traitement terminé !")

    df_logs = pd.DataFrame(logs)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 Tableau de monitoring")
        st.dataframe(df_logs, use_container_width=True)

    with col2:
        st.subheader("📈 Résumé visuel")
        fig, ax = plt.subplots(figsize=(4, 3))
        df_logs["Balises ajoutées"].plot(kind="bar", ax=ax, color="#4CAF50")
        ax.set_title("Balises ajoutées")
        ax.set_ylabel("Nombre")
        ax.set_xticklabels(df_logs["Fichier"], rotation=45, ha="right")
        st.pyplot(fig)

    csv = df_logs.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Télécharger les logs (CSV)",
        data=csv,
        file_name=f"logs_{datetime.date.today().isoformat()}.csv",
        mime="text/csv"
    )

    zip_buffer.seek(0)
    st.download_button(
        label="📦 Télécharger les fichiers corrigés (ZIP)",
        data=zip_buffer,
        file_name=f"xml_corriges_{datetime.date.today().isoformat()}.zip",
        mime="application/zip"
    )
