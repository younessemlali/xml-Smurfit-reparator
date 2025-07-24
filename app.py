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
        # Enregistrer les namespaces présents dans le document
        namespaces = {}
        
        # Pré-parser pour extraire les namespaces
        for event, elem in ET.iterparse(io.StringIO(content), events=['start-ns']):
            prefix, uri = elem
            if prefix:
                namespaces[prefix] = uri
            else:
                # Namespace par défaut
                namespaces['default'] = uri
        
        # Parser le XML
        root = ET.fromstring(content)
        count = 0
        
        # Si on a un namespace par défaut, l'enregistrer
        if 'default' in namespaces:
            ET.register_namespace('', namespaces['default'])
        
        # Enregistrer tous les autres namespaces
        for prefix, uri in namespaces.items():
            if prefix != 'default':
                ET.register_namespace(prefix, uri)
        
        # Créer un mapping parent-enfant pour trouver les parents
        parent_map = {}
        for parent in root.iter():
            for child in parent:
                parent_map[child] = parent
        
        # Parcourir toutes les balises Description (avec ou sans namespace)
        for desc in root.iter():
            # Vérifier si c'est une balise Description (ignorer le namespace)
            tag_name = desc.tag.split('}')[-1] if '}' in desc.tag else desc.tag
            
            if tag_name == 'Description':
                # Obtenir TOUT le texte de l'élément Description (y compris les sous-éléments)
                full_text = ''.join(desc.itertext())
                
                if full_text:
                    # Chercher du texte entre guillemets
                    match = QUOTE_PATTERN.search(full_text)
                    if match:
                        value = match.group(1)
                        
                        # Trouver le parent
                        parent = parent_map.get(desc, None)
                        
                        if parent is not None:
                            # Vérifier si PositionLevel n'existe pas déjà
                            position_level_exists = False
                            for child in parent:
                                child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                                if child_tag == 'PositionLevel':
                                    position_level_exists = True
                                    break
                            
                            if not position_level_exists:
                                # Créer la nouvelle balise avec le même namespace que le parent
                                if '}' in parent.tag:
                                    # Extraire le namespace du parent
                                    namespace = parent.tag.split('}')[0] + '}'
                                    pos_level = ET.SubElement(parent, namespace + "PositionLevel")
                                else:
                                    pos_level = ET.SubElement(parent, "PositionLevel")
                                
                                pos_level.text = value
                                count += 1
        
        # Retourner le XML modifié en préservant la déclaration et l'encodage
        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        
        # Préserver la déclaration XML originale si elle existe
        if content.strip().startswith('<?xml'):
            original_declaration = content.split('?>')[0] + '?>'
            if not xml_str.startswith('<?xml'):
                xml_str = original_declaration + '\n' + xml_str
        elif not xml_str.startswith('<?xml'):
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
        processed_files = {}  # Stocker les fichiers traités
        
        progress = st.progress(0)
        
        for idx, file in enumerate(files):
            # Mise à jour de la progression
            progress.progress((idx + 1) / len(files))
            
            # Lire le fichier avec gestion d'encodage
            content = safe_read_file(file)
            
            # Traiter le XML
            result_xml, count_or_error = process_xml_simple(content)
            
            if result_xml:
                # Succès - stocker le contenu traité
                processed_files[file.name] = result_xml
                results.append({
                    'Fichier': file.name,
                    'Statut': '✅',
                    'Balises ajoutées': count_or_error,
                    'Contenu': result_xml
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
        
        # Section de téléchargement
        if success_count > 0:
            st.write("### 📥 Télécharger les fichiers corrigés")
            
            # Option 1: Télécharger individuellement
            if len(processed_files) == 1:
                # Un seul fichier - bouton direct
                file_name, content = list(processed_files.items())[0]
                st.download_button(
                    f"📄 Télécharger {file_name}",
                    data=content.encode('utf-8'),
                    file_name=f"corrected_{file_name}",
                    mime="text/xml"
                )
            else:
                # Plusieurs fichiers - créer des colonnes
                st.write("**Télécharger individuellement :**")
                
                # Organiser en colonnes (3 par ligne)
                for i in range(0, len(processed_files), 3):
                    cols = st.columns(3)
                    for j, (file_name, content) in enumerate(list(processed_files.items())[i:i+3]):
                        if j < len(cols):
                            with cols[j]:
                                st.download_button(
                                    f"📄 {file_name}",
                                    data=content.encode('utf-8'),
                                    file_name=f"corrected_{file_name}",
                                    mime="text/xml",
                                    key=f"download_{file_name}"
                                )
                
                # Option 2: Télécharger tout en ZIP (optionnel)
                st.write("**Ou télécharger tout en une fois :**")
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zf:
                    for file_name, content in processed_files.items():
                        zf.writestr(f"corrected_{file_name}", content)
                
                zip_buffer.seek(0)
                st.download_button(
                    "📦 Télécharger tous les fichiers (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="xml_corriges.zip",
                    mime="application/zip"
                )
        
        # Détails par fichier
        st.write("### 📋 Détails du traitement")
        for r in results:
            if r['Statut'] == '✅':
                msg = f"✅ **{r['Fichier']}** - {r['Balises ajoutées']} balise(s) ajoutée(s)"
                
                # Ajouter les stats si disponibles
                if 'Stats' in r and r['Stats']:
                    stats = r['Stats']
                    msg += f"\n   - Descriptions trouvées : {stats['descriptions']}"
                    msg += f"\n   - PositionLevel déjà présents : {stats['already_present']}"
                    msg += f"\n   - PositionLevel ajoutés : {stats['added']}"
                
                st.success(msg)
            else:
                st.error(f"❌ **{r['Fichier']}** - {r.get('Erreur', 'Erreur inconnue')}")

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
