import streamlit as st
import re
import io
import zipfile

st.set_page_config(page_title="XML Smurfit Reparator", page_icon="🔧")

st.title("🔧 XML Smurfit Reparator")
st.write("Corrige et met à jour les balises PositionLevel dans vos fichiers XML")

def process_xml_as_text(content):
    """
    Traite le XML comme du texte pour préserver le format exact et les accents.
    """
    try:
        lines = content.split('\n')
        modified_lines = []
        modifications = []
        total_modified = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            modified_lines.append(line)
            
            # Chercher une ligne contenant <Description> ou <ns0:Description>
            if re.search(r'<(?:ns\d+:)?Description>', line):
                # Récupérer tout le contenu de Description
                description_content = line
                desc_line_index = len(modified_lines) - 1
                
                # Si Description n'est pas fermée sur cette ligne
                if not re.search(r'</(?:ns\d+:)?Description>', line):
                    j = i + 1
                    while j < len(lines):
                        modified_lines.append(lines[j])
                        description_content += ' ' + lines[j]
                        if re.search(r'</(?:ns\d+:)?Description>', lines[j]):
                            i = j
                            break
                        j += 1
                
                # Chercher les valeurs entre guillemets (format: Lettre - Description)
                pattern = r'"([A-Z]\s*-\s*[^"]+)"'
                matches = re.findall(pattern, description_content)
                
                if matches:
                    # Prendre la dernière valeur trouvée
                    new_value = matches[-1].strip()
                    
                    # Chercher si PositionLevel existe dans les prochaines lignes
                    position_level_found = False
                    position_level_index = -1
                    
                    # Regarder les prochaines lignes (max 20)
                    for k in range(1, min(21, len(lines) - i)):
                        if i + k < len(lines):
                            next_line = lines[i + k]
                            
                            # Si on trouve PositionLevel
                            if re.search(r'<(?:ns\d+:)?PositionLevel>', next_line):
                                position_level_found = True
                                position_level_index = i + k
                                
                                # Extraire la valeur actuelle
                                current_match = re.search(r'<(?:ns\d+:)?PositionLevel>([^<]*)</(?:ns\d+:)?PositionLevel>', next_line)
                                if current_match:
                                    current_value = current_match.group(1).strip()
                                    
                                    if current_value != new_value:
                                        # Remplacer la valeur en gardant le format exact
                                        new_line = re.sub(
                                            r'(<(?:ns\d+:)?PositionLevel>)[^<]*(</(?:ns\d+:)?PositionLevel>)',
                                            r'\1' + new_value + r'\2',
                                            next_line
                                        )
                                        
                                        # Mettre à jour dans modified_lines
                                        future_index = len(modified_lines) + k - 1
                                        if future_index < len(modified_lines):
                                            modified_lines[future_index] = new_line
                                        else:
                                            # On devra le modifier quand on y arrivera
                                            lines[position_level_index] = new_line
                                        
                                        modifications.append(f"Mis à jour: '{current_value}' → '{new_value}'")
                                        total_modified += 1
                                break
                            
                            # Si on trouve un autre Job ou WorkSite, arrêter
                            if re.search(r'<(?:ns\d+:)?(?:Job|WorkSite)>', next_line):
                                break
                    
                    # Si PositionLevel n'existe pas, l'ajouter
                    if not position_level_found:
                        # Chercher où l'insérer (après PositionStatus de préférence)
                        insert_index = -1
                        indent = ""
                        
                        for k in range(1, min(21, len(lines) - i)):
                            if i + k < len(lines):
                                next_line = lines[i + k]
                                
                                # Récupérer l'indentation
                                indent_match = re.match(r'^(\s*)', next_line)
                                if indent_match:
                                    indent = indent_match.group(1)
                                
                                # Insérer après PositionStatus
                                if re.search(r'</(?:ns\d+:)?PositionStatus>', next_line):
                                    insert_index = i + k
                                    break
                                
                                # Ou après PositionTitle
                                elif re.search(r'</(?:ns\d+:)?PositionTitle>', next_line):
                                    insert_index = i + k
                                    break
                        
                        if insert_index > 0:
                            # Déterminer le préfixe namespace à utiliser
                            ns_prefix = ""
                            ns_match = re.search(r'<(ns\d+:)?Description>', description_content)
                            if ns_match and ns_match.group(1):
                                ns_prefix = ns_match.group(1)
                            
                            # Créer la nouvelle ligne
                            new_position_level = f'{indent}<{ns_prefix}PositionLevel>{new_value}</{ns_prefix}PositionLevel>'
                            
                            # L'ajouter à la bonne position
                            future_index = len(modified_lines) + (insert_index - i)
                            if future_index <= len(modified_lines):
                                modified_lines.insert(future_index, new_position_level)
                            else:
                                # On devra l'ajouter plus tard
                                lines.insert(insert_index + 1, new_position_level)
                            
                            modifications.append(f"Ajouté: '{new_value}'")
                            total_modified += 1
            
            i += 1
        
        # Reconstruire le contenu
        result = '\n'.join(modified_lines)
        
        return result, total_modified, modifications
        
    except Exception as e:
        return None, 0, [f"Erreur: {str(e)}"]

# Interface utilisateur
uploaded_files = st.file_uploader(
    "Choisissez vos fichiers XML",
    type=['xml'],
    accept_multiple_files=True,
    key="xml_uploader"
)

if uploaded_files:
    st.write(f"📁 {len(uploaded_files)} fichier(s) chargé(s)")
    
    if st.button("🚀 Traiter les fichiers", type="primary"):
        st.write("---")
        
        all_results = []
        
        for file in uploaded_files:
            # Lire le contenu en préservant l'encodage UTF-8
            content = file.read().decode('utf-8', errors='strict')
            
            # Traiter le XML
            result_content, modified_count, modifications = process_xml_as_text(content)
            
            if result_content:
                # Afficher les résultats pour ce fichier
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if modified_count > 0:
                        st.success(f"✅ **{file.name}** - {modified_count} modification(s) effectuée(s)")
                    else:
                        st.info(f"ℹ️ **{file.name}** - Aucune modification nécessaire")
                
                with col2:
                    # Bouton de téléchargement individuel
                    st.download_button(
                        "💾 Télécharger",
                        data=result_content.encode('utf-8'),
                        file_name=f"modified_{file.name}",
                        mime="text/xml",
                        key=f"dl_{file.name}"
                    )
                
                # Afficher les détails si modifications
                if modifications and modified_count > 0:
                    with st.expander(f"Détails des modifications pour {file.name}"):
                        for mod in modifications:
                            st.write(f"• {mod}")
                
                all_results.append({
                    'name': file.name,
                    'content': result_content,
                    'count': modified_count
                })
            else:
                st.error(f"❌ **{file.name}** - {modifications[0] if modifications else 'Erreur inconnue'}")
        
        # Option ZIP si plusieurs fichiers modifiés
        modified_files = [r for r in all_results if r['count'] > 0]
        if len(modified_files) > 1:
            st.write("---")
            st.write("### 📦 Téléchargement groupé")
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for result in modified_files:
                    zf.writestr(f"modified_{result['name']}", result['content'].encode('utf-8'))
            
            zip_buffer.seek(0)
            st.download_button(
                "📦 Télécharger tous les fichiers modifiés (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="xml_modifies.zip",
                mime="application/zip"
            )

else:
    st.info("👆 Chargez des fichiers XML pour commencer")
    
    # Exemple
    st.write("### 📋 Comment ça marche ?")
    st.write("""
    L'application :
    1. Recherche les valeurs entre guillemets au format **"Lettre - Description"** dans les balises Description
    2. Met à jour ou ajoute la balise PositionLevel avec cette valeur complète
    3. Préserve exactement le format XML original (namespaces, accents, indentation)
    """)
    
    # Exemple visuel
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Avant :**")
        st.code("""<ns0:Description>
  Poste "A - Peu Qualifié"
</ns0:Description>
<ns0:PositionLevel>A</ns0:PositionLevel>""", language='xml')
    
    with col2:
        st.write("**Après :**")
        st.code("""<ns0:Description>
  Poste "A - Peu Qualifié"
</ns0:Description>
<ns0:PositionLevel>A - Peu Qualifié</ns0:PositionLevel>""", language='xml')
