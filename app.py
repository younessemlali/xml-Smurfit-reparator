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

def safe_read_file(file):
    """Lit un fichier uploadé en gérant les problèmes d'encodage."""
    content = file.read()
    
    # Si c'est déjà une string, la retourner
    if isinstance(content, str):
        return content
    
    # Essayer différents encodages
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    
    # En dernier recours, ignorer les erreurs
    return content.decode('utf-8', errors='ignore')

def process_xml_simple(content):
    """Traite un fichier XML et ajoute les balises PositionLevel manquantes."""
    try:
        # Parser le XML
        root = ET.fromstring(content)
        count = 0
        
        # Créer un mapping parent-enfant pour trouver les parents
        parent_map = {}
        for parent in root.iter():
            for child in parent:
                parent_map[child] = parent
        
        # Parcourir toutes les balises Description
        for desc in root.iter('Description'):
            if desc.text:
                # Chercher du texte entre guillemets
                match = QUOTE_PATTERN.search(desc.text)
                if match:
                    value = match.group(1)
                    
                    # Trouver le parent
                    parent = parent_map.get(desc, None)
                    
                    if parent is not None:
                        # Vérifier si PositionLevel n'existe pas déjà
                        if parent.find("PositionLevel") is None:
                            # Créer la nouvelle balise
                            pos_level = ET.SubElement(parent, "PositionLevel")
                            pos_level.text = value
                            count += 1
        
        # Retourner le XML modifié avec déclaration
        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        if not xml_str.startswith('<?xml'):
            xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        
        return xml_str, count
    
    except ET.ParseError as e:
        return None, f"Erreur de parsing XML: {str(e)}"
    except Exception as e:
        return None, f"Erreur: {str(e)}"

# Upload de fichiers
files = st.file_uploader(
    "Choisissez vos fichiers XML", 
    type=['xml'], 
    accept_multiple_files=True
)

if files:
    st.write(f"📁 {len(files)} fichier(s) chargé(s)")
    
    if st.button("🚀 Traiter les fichiers", type="primary"):
        results = []
        zip_buffer = io.BytesIO()
        
        progress = st.progress(0)
        
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for idx, file in enumerate(files):
                # Mise à jour de la progression
                progress.progress((idx + 1) / len(files))
                
                # Lire le fichier avec gestion d'encodage
                content = safe_read_file(file)
                
                # Traiter le XML
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
        
        progress.empty()
        
        # Afficher les résultats
        st.write("### 📊 Résultats")
        
        success_count = sum(1 for r in results if r['Statut'] == '✅')
        total_tags = sum(r.get('Balises ajoutées', 0) for r in results if r['Statut'] == '✅')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Fichiers traités", len(files))
        with col2:
            st.metric("Succès", success_count)
        with col3:
            st.metric("Balises ajoutées", total_tags)
        
        # Détails par fichier
        for r in results:
            if r['Statut'] == '✅':
                st.success(f"✅ **{r['Fichier']}** - {r['Balises ajoutées']} balise(s) ajoutée(s)")
            else:
                st.error(f"❌ **{r['Fichier']}** - {r.get('Erreur', 'Erreur inconnue')}")
        
        # Télécharger le ZIP
        if success_count > 0:
            zip_buffer.seek(0)
            st.download_button(
                "📥 Télécharger les fichiers corrigés (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="xml_corriges.zip",
                mime="application/zip"
            )

else:
    st.info("👆 Chargez des fichiers XML pour commencer")
    
    # Exemple
    st.write("### 📝 Exemple de fichier XML")
    st.write("L'application transforme ceci :")
    
    example_before = """<Job>
    <Description>Poste "A - Débutant"</Description>
    <Salary>25000</Salary>
</Job>"""
    
    example_after = """<Job>
    <Description>Poste "A - Débutant"</Description>
    <Salary>25000</Salary>
    <PositionLevel>A - Débutant</PositionLevel>
</Job>"""
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Avant :**")
        st.code(example_before, language='xml')
    
    with col2:
        st.write("**Après :**")
        st.code(example_after, language='xml')
    
    # Fichier d'exemple complet
    example_full = """<?xml version="1.0" encoding="UTF-8"?>
<Jobs>
    <Job>
        <Description>Poste "A - Débutant"</Description>
        <Salary>25000</Salary>
    </Job>
    <Job>
        <Description>Poste "B - Confirmé"</Description>
        <Salary>35000</Salary>
    </Job>
    <Job>
        <Description>Manager "C - Expert"</Description>
        <Salary>45000</Salary>
    </Job>
</Jobs>"""
    
    st.download_button(
        "📥 Télécharger un fichier d'exemple",
        data=example_full.encode('utf-8'),
        file_name="exemple_smurfit.xml",
        mime="text/xml"
    )
