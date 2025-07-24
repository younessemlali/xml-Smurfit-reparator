import streamlit as st
import xml.etree.ElementTree as ET
import re
import io
import zipfile
from xml.dom import minidom

st.set_page_config(page_title="XML Smurfit Reparator V2", page_icon="🔧")

st.title("🔧 XML Smurfit Reparator V2")
st.write("Corrige et met à jour les balises PositionLevel dans vos fichiers XML")

# Pattern pour trouver les valeurs entre guillemets (format: Lettre - Description)
LEVEL_PATTERN = re.compile(r'"([A-Z]\s*-\s*[^"]+)"')

def prettify_xml(elem):
    """Retourne une version pretty-printed du XML."""
    rough_string = ET.tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def find_position_level_value(text):
    """Trouve la valeur de niveau de position dans le texte."""
    if not text:
        return None
    
    # Chercher toutes les correspondances
    matches = LEVEL_PATTERN.findall(text)
    
    # Retourner la dernière correspondance trouvée (généralement la bonne)
    if matches:
        return matches[-1].strip()
    
    return None

def process_xml_robust(content):
    """Traite le XML de manière robuste."""
    try:
        # Parser le XML
        tree = ET.ElementTree(ET.fromstring(content))
        root = tree.getroot()
        
        modifications = []
        total_modified = 0
        
        # Parcourir TOUS les éléments du XML
        for element in root.iter():
            # Chercher les éléments qui contiennent Description
            description_elem = None
            position_level_elem = None
            
            # Chercher Description et PositionLevel parmi les enfants
            for child in element:
                tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                
                if tag_name == 'Description':
                    description_elem = child
                elif tag_name == 'PositionLevel':
                    position_level_elem = child
            
            # Si on a trouvé une Description
            if description_elem is not None:
                # Récupérer tout le texte de Description
                full_text = ''.join(description_elem.itertext())
                
                # Chercher la valeur du niveau
                level_value = find_position_level_value(full_text)
                
                if level_value:
                    # Cas 1: PositionLevel n'existe pas - on le crée
                    if position_level_elem is None:
                        # Créer avec le même namespace que Description si nécessaire
                        if '}' in description_elem.tag:
                            namespace = description_elem.tag.split('}')[0] + '}'
                            new_elem = ET.SubElement(element, namespace + 'PositionLevel')
                        else:
                            new_elem = ET.SubElement(element, 'PositionLevel')
                        
                        new_elem.text = level_value
                        modifications.append(f"Ajouté: {level_value}")
                        total_modified += 1
                    
                    # Cas 2: PositionLevel existe mais avec une valeur différente
                    else:
                        current_value = (position_level_elem.text or '').strip()
                        if current_value != level_value:
                            position_level_elem.text = level_value
                            modifications.append(f"Mis à jour: '{current_value}' → '{level_value}'")
                            total_modified += 1
        
        # Convertir en string avec indentation
        result_xml = ET.tostring(root, encoding='unicode', method='xml')
        
        # Ajouter la déclaration XML si nécessaire
        if not result_xml.startswith('<?xml'):
            result_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + result_xml
        
        return result_xml, total_modified, modifications
        
    except Exception as e:
        return None, 0, [f"Erreur: {str(e)}"]

# Interface utilisateur
uploaded_files = st.file_uploader(
    "Choisissez vos fichiers XML",
    type=['xml'],
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📁 {len(uploaded_files)} fichier(s) chargé(s)")
    
    # Afficher un aperçu du premier fichier pour debug
    with st.expander("🔍 Aperçu du premier fichier (100 premières lignes)"):
        first_file_content = uploaded_files[0].read().decode('utf-8', errors='ignore')
        lines = first_file_content.split('\n')[:100]
        st.code('\n'.join(lines), language='xml')
        uploaded_files[0].seek(0)  # Remettre le curseur au début
    
    if st.button("🚀 Traiter les fichiers", type="primary"):
        all_results = []
        
        for file in uploaded_files:
            # Lire le contenu
            content = file.read().decode('utf-8', errors='ignore')
            
            # Traiter le XML
            result_xml, modified_count, modifications = process_xml_robust(content)
            
            if result_xml:
                # Créer un conteneur pour ce fichier
                with st.container():
                    st.write(f"### 📄 {file.name}")
                    
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        if modified_count > 0:
                            st.success(f"✅ {modified_count} modification(s)")
                        else:
                            st.warning("⚠️ Aucune modification")
                    
                    with col2:
                        # Afficher les détails des modifications
                        if modifications and modified_count > 0:
                            with st.expander("Voir les détails"):
                                for mod in modifications[:10]:  # Limiter à 10 pour l'affichage
                                    st.write(f"• {mod}")
                                if len(modifications) > 10:
                                    st.write(f"... et {len(modifications) - 10} autres")
                    
                    # Bouton de téléchargement pour ce fichier
                    if modified_count > 0:
                        st.download_button(
                            f"💾 Télécharger {file.name} modifié",
                            data=result_xml.encode('utf-8'),
                            file_name=f"modified_{file.name}",
                            mime="text/xml",
                            key=f"download_{file.name}"
                        )
                    
                    st.markdown("---")
                
                all_results.append({
                    'file': file.name,
                    'content': result_xml,
                    'modified': modified_count
                })
            else:
                st.error(f"❌ Erreur avec {file.name}: {modifications[0] if modifications else 'Erreur inconnue'}")
        
        # Option pour télécharger tous les fichiers modifiés
        modified_files = [r for r in all_results if r['modified'] > 0]
        if len(modified_files) > 1:
            st.write("### 📦 Télécharger tous les fichiers modifiés")
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zf:
                for result in modified_files:
                    zf.writestr(f"modified_{result['file']}", result['content'])
            
            zip_buffer.seek(0)
            st.download_button(
                "📦 Télécharger tous les fichiers modifiés (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="all_modified_files.zip",
                mime="application/zip"
            )

else:
    st.info("👆 Chargez des fichiers XML pour commencer")
    
    # Exemple et instructions
    st.write("### 📋 Instructions")
    st.write("""
    Cette application :
    1. **Recherche** les valeurs entre guillemets au format "Lettre - Description" dans les balises `<Description>`
    2. **Ajoute** une balise `<PositionLevel>` si elle n'existe pas
    3. **Met à jour** la balise `<PositionLevel>` si elle existe avec une valeur différente
    
    **Exemple de transformation :**
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Avant :**")
        st.code("""<Job>
  <Description>
    Poste niveau "B - Qualifié"
  </Description>
  <PositionLevel>B</PositionLevel>
</Job>""", language='xml')
    
    with col2:
        st.write("**Après :**")
        st.code("""<Job>
  <Description>
    Poste niveau "B - Qualifié"
  </Description>
  <PositionLevel>B - Qualifié</PositionLevel>
</Job>""", language='xml')
    
    # Fichier de test
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Jobs>
    <Job>
        <Description>Opérateur machine "A - Peu Qualifié"</Description>
        <PositionLevel>A</PositionLevel>
        <Salary>25000</Salary>
    </Job>
    <Job>
        <Description>Technicien senior "C - Très Qualifié"</Description>
        <Salary>45000</Salary>
    </Job>
</Jobs>"""
    
    st.download_button(
        "📥 Télécharger un fichier de test",
        data=test_xml.encode('utf-8'),
        file_name="test_smurfit.xml",
        mime="text/xml"
    )
