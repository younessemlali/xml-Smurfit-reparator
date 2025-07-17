import streamlit as st
import re
import xml.etree.ElementTree as ET
import io
import zipfile

st.set_page_config(page_title="XML Reparator", page_icon="🔧")

st.title("🔧 XML Smurfit Reparator")
st.write("Corrige les balises PositionLevel dans vos fichiers XML")

# Expression régulière pour trouver le texte entre guillemets
QUOTE_PATTERN = re.compile(r'"([^"]+)"')

def process_xml_simple(content):
    """Traite un fichier XML et ajoute les balises PositionLevel manquantes."""
    try:
        # Parser le XML
        root = ET.fromstring(content)
        count = 0
        
        # Parcourir toutes les balises Description
        for element in root.iter():
            if element.tag == "Description" and element.text:
                # Chercher du texte entre guillemets
                match = QUOTE_PATTERN.search(element.text)
                if match:
                    value = match.group(1)
                    
                    # Trouver le parent
                    parent = element.getparent() if hasattr(element, 'getparent') else None
                    if parent is None:
                        # Chercher le parent manuellement
                        for p in root.iter():
                            if element in list(p):
                                parent = p
                                break
                    
                    if parent is not None:
                        # Vérifier si PositionLevel n'existe pas déjà
                        if parent.find("PositionLevel") is None:
                            # Créer la nouvelle balise
                            pos_level = ET.SubElement(parent, "PositionLevel")
                            pos_level.text = value
                            count += 1
        
        # Retourner le XML modifié
        return ET.tostring(root, encoding='unicode'), count
    
    except Exception as e:
        return None, str(e)

# Upload de fichiers
files = st.file_uploader(
    "Choisissez vos fichiers XML", 
    type=['xml'], 
    accept_multiple_files=True
)

if files:
    st.write(f"📁 {len(files)} fichier(s) chargé(s)")
    
    if st.button("🚀 Traiter les fichiers"):
        results = []
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for file in files:
                content = file.read().decode('utf-8')
                result_xml, count_or_error = process_xml_simple(content)
                
                if result_xml:
                    # Succès
                    zf.writestr(file.name, result_xml)
                    results.append({
                        'Fichier': file.name,
                        'Statut': '✅',
                        'Balises ajoutées': count_or_error
                    })
                else:
                    # Erreur
                    results.append({
                        'Fichier': file.name,
                        'Statut': '❌',
                        'Erreur': count_or_error
                    })
        
        # Afficher les résultats
        st.write("### 📊 Résultats")
        for r in results:
            if r['Statut'] == '✅':
                st.success(f"{r['Fichier']} - {r['Balises ajoutées']} balise(s) ajoutée(s)")
            else:
                st.error(f"{r['Fichier']} - Erreur: {r.get('Erreur', 'Inconnue')}")
        
        # Télécharger le ZIP
        zip_buffer.seek(0)
        st.download_button(
            "📥 Télécharger les fichiers corrigés",
            data=zip_buffer,
            file_name="xml_corriges.zip",
            mime="application/zip"
        )

else:
    st.info("👆 Chargez des fichiers XML pour commencer")
    
    # Exemple
    st.write("### Exemple de fichier XML")
    example = """<?xml version="1.0"?>
<Jobs>
    <Job>
        <Description>Poste "A - Débutant"</Description>
        <Salary>25000</Salary>
    </Job>
    <Job>
        <Description>Poste "B - Confirmé"</Description>
        <Salary>35000</Salary>
    </Job>
</Jobs>"""
    
    st.code(example, language='xml')
    st.download_button(
        "📥 Télécharger l'exemple",
        data=example,
        file_name="exemple.xml",
        mime="text/xml"
    )
