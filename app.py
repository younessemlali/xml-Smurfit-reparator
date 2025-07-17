import streamlit as st
import pandas as pd
import time
import io
import zipfile
import datetime
import matplotlib.pyplot as plt

from src.xml_processor import process_xml

# Configuration de la page
st.set_page_config(
    page_title="XML Smurfit Reparator",
    page_icon="📦",
    layout="wide"
)

# En-tête de l'application
st.title("📦 XML Smurfit Reparator – PositionLevel Fixer")
st.markdown("Chargez vos fichiers XML pour corriger automatiquement les balises `<PositionLevel>` manquantes.")

# Zone de chargement des fichiers
uploaded_files = st.file_uploader(
    "Sélectionnez un ou plusieurs fichiers XML",
    type=["xml"],
    accept_multiple_files=True,
    help="Les fichiers XML doivent contenir des balises Description avec des valeurs entre guillemets"
)

# Afficher le nombre de fichiers chargés
if uploaded_files:
    st.info(f"📁 {len(uploaded_files)} fichier(s) chargé(s)")
    
    # Afficher les noms des fichiers
    with st.expander("Voir les fichiers chargés"):
        for file in uploaded_files:
            st.write(f"- {file.name}")

# Bouton de traitement - visible uniquement si des fichiers sont chargés
if uploaded_files:
    if st.button("🚀 Lancer le traitement", type="primary", use_container_width=True):
        logs = []
        zip_buffer = io.BytesIO()
        
        # Création du fichier ZIP avec les fichiers corrigés
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, file in enumerate(uploaded_files, 1):
                status_text.text(f"Traitement de {file.name}...")
                start_time = time.time()
                
                try:
                    # Traitement du fichier XML
                    corrected_content, added_count = process_xml(file.read())
                    
                    # Ajout du fichier corrigé au ZIP
                    zf.writestr(file.name, corrected_content)
                    
                    status = "✅ Succès"
                    error_msg = None
                    
                except Exception as e:
                    added_count = 0
                    status = "❌ Erreur"
                    error_msg = str(e)
                    # Ajouter le fichier original en cas d'erreur
                    file.seek(0)
                    zf.writestr(f"ERREUR_{file.name}", file.read())
                
                # Calcul de la durée
                duration = round(time.time() - start_time, 3)
                
                # Ajout aux logs
                log_entry = {
                    "Fichier": file.name,
                    "Statut": status,
                    "Balises ajoutées": added_count,
                    "Durée (s)": duration
                }
                if error_msg:
                    log_entry["Détails"] = error_msg
                
                logs.append(log_entry)
                
                # Mise à jour de la barre de progression
                progress_bar.progress(idx / len(uploaded_files))
        
        # Nettoyage de l'interface
        progress_bar.empty()
        status_text.empty()
        
        # Message de succès
        st.success(f"✅ Traitement terminé ! {len(uploaded_files)} fichier(s) traité(s).")
        
        # Création du DataFrame des logs
        df_logs = pd.DataFrame(logs)
        
        # Affichage en colonnes
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Tableau de monitoring")
            st.dataframe(
                df_logs,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Balises ajoutées": st.column_config.NumberColumn(
                        "Balises ajoutées",
                        help="Nombre de balises PositionLevel ajoutées",
                        format="%d"
                    ),
                    "Durée (s)": st.column_config.NumberColumn(
                        "Durée (s)",
                        help="Temps de traitement en secondes",
                        format="%.3f"
                    )
                }
            )
        
        with col2:
            st.subheader("📈 Résumé visuel")
            
            # Statistiques
            total_added = df_logs["Balises ajoutées"].sum()
            success_count = len(df_logs[df_logs["Statut"] == "✅ Succès"])
            error_count = len(df_logs[df_logs["Statut"] == "❌ Erreur"])
            
            st.metric("Total balises ajoutées", total_added)
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.metric("Succès", success_count, delta_color="normal")
            with col2_2:
                st.metric("Erreurs", error_count, delta_color="inverse")
            
            # Graphique si des balises ont été ajoutées
            if total_added > 0:
                fig, ax = plt.subplots(figsize=(6, 4))
                df_success = df_logs[df_logs["Balises ajoutées"] > 0]
                
                if not df_success.empty:
                    bars = ax.bar(range(len(df_success)), df_success["Balises ajoutées"], color="#4CAF50")
                    ax.set_xlabel("Fichiers")
                    ax.set_ylabel("Nombre de balises ajoutées")
                    ax.set_title("Balises ajoutées par fichier")
                    ax.set_xticks(range(len(df_success)))
                    ax.set_xticklabels([f"Fichier {i+1}" for i in range(len(df_success))], rotation=45, ha="right")
                    
                    # Ajout des valeurs sur les barres
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{int(height)}',
                               ha='center', va='bottom')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
        
        # Section de téléchargement
        st.markdown("---")
        st.subheader("📥 Téléchargements")
        
        col_download1, col_download2 = st.columns(2)
        
        with col_download1:
            # Bouton de téléchargement des logs CSV
            csv = df_logs.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📊 Télécharger les logs (CSV)",
                data=csv,
                file_name=f"logs_xml_repair_{datetime.date.today().isoformat()}.csv",
                mime="text/csv"
            )
        
        with col_download2:
            # Bouton de téléchargement du ZIP
            zip_buffer.seek(0)
            st.download_button(
                label="📦 Télécharger les fichiers corrigés (ZIP)",
                data=zip_buffer,
                file_name=f"xml_corriges_{datetime.date.today().isoformat()}.zip",
                mime="application/zip"
            )
else:
    # Instructions si aucun fichier n'est chargé
    st.info("👆 Veuillez charger un ou plusieurs fichiers XML pour commencer.")
    
    # Exemple d'utilisation
    with st.expander("📖 Comment utiliser cette application ?"):
        st.markdown("""
        1. **Chargez vos fichiers XML** en utilisant le bouton ci-dessus
        2. **Cliquez sur "Lancer le traitement"** pour démarrer la correction
        3. **Consultez les résultats** dans le tableau de monitoring
        4. **Téléchargez** les fichiers corrigés et/ou les logs
        
        ### Format attendu
        L'application recherche des balises `<Description>` contenant du texte avec des valeurs entre guillemets, par exemple :
        ```xml
        <Description>Poste de niveau "A - Peu Qualifié"</Description>
        ```
        
        Elle créera alors une balise `<PositionLevel>` avec la valeur extraite :
        ```xml
        <PositionLevel>A - Peu Qualifié</PositionLevel>
        ```
        """)
    
    # Fichier d'exemple pour tester
    st.markdown("### 🧪 Fichier de test")
    st.markdown("Vous pouvez créer un fichier XML de test avec ce contenu :")
    
    example_xml = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <Job>
        <Description>Poste de niveau "A - Peu Qualifié"</Description>
        <Salary>25000</Salary>
    </Job>
    <Job>
        <Description>Poste senior "C - Très Qualifié"</Description>
        <Salary>45000</Salary>
    </Job>
</root>"""
    
    st.code(example_xml, language="xml")
    
    # Bouton pour télécharger l'exemple
    st.download_button(
        label="📥 Télécharger le fichier d'exemple",
        data=example_xml.encode("utf-8"),
        file_name="exemple_test.xml",
        mime="text/xml"
    )
