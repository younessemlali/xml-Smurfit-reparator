import streamlit as st
import re
import io
import zipfile

st.set_page_config(page_title="XML Smurfit Reparator", page_icon="🔧", layout="wide")

st.title("🔧 XML Smurfit Reparator - Version Finale")
st.markdown("Mise à jour automatique des balises PositionLevel dans vos fichiers XML")

def process_xml_file(content, debug=False):
    """Traite le contenu XML et retourne le contenu modifié avec le nombre de modifications."""
    lines = content.split('\n')
    modified = False
    modifications_detail = []
    
    if debug:
        st.write("🔍 **Mode debug activé**")
        st.write(f"Nombre de lignes dans le fichier: {len(lines)}")
    
    # Parcourir ligne par ligne
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Détecter une ligne avec Description (SANS namespace maintenant)
        if '<Description>' in line:
            if debug:
                st.info(f"📍 Ligne {i}: Trouvé une balise Description")
                st.code(line)
            
            # Collecter tout le contenu jusqu'à </Description>
            desc_content = line
            start_idx = i
            
            # Si la description continue sur plusieurs lignes
            while '</Description>' not in desc_content and i < len(lines) - 1:
                i += 1
                desc_content += ' ' + lines[i]
            
            # Chercher la valeur entre guillemets
            all_quotes = re.findall(r'"([^"]+)"', desc_content)
            if debug and all_quotes:
                st.write(f"Toutes les valeurs entre guillemets trouvées: {all_quotes}")
            
            # Chercher spécifiquement le pattern "Lettre - Description"
            match = re.search(r'"([A-Z]\s*-\s*[^"]+)"', desc_content)
            
            if match:
                position_value = match.group(1).strip()
                if debug:
                    st.success(f"✅ Valeur trouvée: '{position_value}'")
                
                # Maintenant chercher PositionLevel dans les lignes suivantes
                j = i + 1
                found_position_level = False
                
                # Chercher dans les 20 prochaines lignes max
                while j < min(i + 20, len(lines)):
                    if '<PositionLevel>' in lines[j] and '</PositionLevel>' in lines[j]:
                        found_position_level = True
                        if debug:
                            st.info(f"📍 Ligne {j}: Trouvé PositionLevel")
                            st.code(lines[j])
                        
                        # Extraire la valeur actuelle
                        current_match = re.search(r'<PositionLevel>([^<]*)</PositionLevel>', lines[j])
                        if current_match:
                            current_value = current_match.group(1).strip()
                            if debug:
                                st.write(f"Valeur actuelle: '{current_value}'")
                                st.write(f"Nouvelle valeur: '{position_value}'")
                                st.write(f"Sont-elles différentes? {current_value != position_value}")
                            
                            # Si différent, mettre à jour
                            if current_value != position_value:
                                # Garder l'indentation
                                indent = re.match(r'^(\s*)', lines[j]).group(1)
                                lines[j] = f"{indent}<PositionLevel>{position_value}</PositionLevel>"
                                
                                if debug:
                                    st.warning(f"Modification effectuée:")
                                    st.code(f"Avant: {current_value}")
                                    st.code(f"Après: {position_value}")
                                
                                modified = True
                                modifications_detail.append({
                                    'type': 'update',
                                    'from': current_value,
                                    'to': position_value
                                })
                        break
                    
                    # Si on trouve un nouveau Job, arrêter
                    if '<Job>' in lines[j] or '</Job>' in lines[j]:
                        break
                    
                    j += 1
                
                # Si PositionLevel n'existe pas, l'ajouter
                if not found_position_level:
                    if debug:
                        st.warning(f"⚠️ PositionLevel non trouvé, il faut l'ajouter")
                    
                    # Chercher où l'insérer
                    insert_line = i + 1
                    indent = "    "
                    
                    # Chercher après PositionStatus ou PositionTitle
                    k = i + 1
                    while k < min(i + 20, len(lines)):
                        if '</PositionStatus>' in lines[k]:
                            insert_line = k + 1
                            indent_match = re.match(r'^(\s*)', lines[k])
                            if indent_match:
                                indent = indent_match.group(1)
                            break
                        elif '</PositionTitle>' in lines[k]:
                            insert_line = k + 1
                            indent_match = re.match(r'^(\s*)', lines[k])
                            if indent_match:
                                indent = indent_match.group(1)
                            break
                        k += 1
                    
                    # Insérer la nouvelle ligne SANS namespace
                    new_line = f"{indent}<PositionLevel>{position_value}</PositionLevel>"
                    lines.insert(insert_line, new_line)
                    
                    if debug:
                        st.success(f"✅ Ajout de PositionLevel à la ligne {insert_line}")
                        st.code(new_line)
                    
                    modified = True
                    modifications_detail.append({
                        'type': 'add',
                        'value': position_value
                    })
                    
                    # Ajuster l'index car on a inséré une ligne
                    i += 1
            elif debug:
                st.warning(f"❌ Aucune valeur au format 'X - Description' trouvée")
        
        i += 1
    
    if debug:
        st.write(f"**Résultat final:** {len(modifications_detail)} modification(s)")
    
    return '\n'.join(lines), len(modifications_detail), modifications_detail

# Interface
st.markdown("### 📁 Sélection des fichiers")
uploaded_files = st.file_uploader(
    "Glissez vos fichiers XML ici ou cliquez pour parcourir",
    type=['xml'],
    accept_multiple_files=True,
    help="Formats supportés : .xml"
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} fichier(s) chargé(s)")
    
    # Options
    col1, col2 = st.columns(2)
    with col1:
        show_preview = st.checkbox("👁️ Afficher un aperçu du premier fichier", value=False)
    with col2:
        debug_mode = st.checkbox("🔍 Mode debug (affiche les détails du traitement)", value=False)
    
    if show_preview and uploaded_files:
        with st.expander("Aperçu du fichier"):
            preview_content = uploaded_files[0].read().decode('iso-8859-1', errors='replace')
            st.text(preview_content[:2000] + "..." if len(preview_content) > 2000 else preview_content)
            uploaded_files[0].seek(0)
    
    if st.button("🚀 Lancer le traitement", type="primary", use_container_width=True):
        st.markdown("---")
        st.markdown("### 📊 Résultats du traitement")
        
        total_files = len(uploaded_files)
        total_modifications = 0
        processed_files = []
        
        # Traiter chaque fichier
        for idx, file in enumerate(uploaded_files):
            # Lire le fichier en ISO-8859-1
            file_bytes = file.read()
            
            # Essayer ISO-8859-1 d'abord (votre standard)
            try:
                content = file_bytes.decode('iso-8859-1')
                encoding = 'iso-8859-1'
            except:
                # Fallback UTF-8
                try:
                    content = file_bytes.decode('utf-8')
                    encoding = 'utf-8'
                except:
                    content = file_bytes.decode('utf-8', errors='replace')
                    encoding = 'utf-8 (avec corrections)'
            
            # Traiter le fichier
            try:
                modified_content, mod_count, modifications = process_xml_file(content, debug=debug_mode)
                total_modifications += mod_count
                
                # Sauvegarder pour le ZIP
                processed_files.append({
                    'name': file.name,
                    'content': modified_content,
                    'encoding': encoding,
                    'count': mod_count
                })
                
                # Afficher les résultats
                col1, col2, col3 = st.columns([4, 2, 1])
                
                with col1:
                    if mod_count > 0:
                        st.success(f"**✅ {file.name}**")
                        st.caption(f"Encodage: {encoding} | {mod_count} modification(s)")
                    else:
                        st.info(f"**ℹ️ {file.name}**")
                        st.caption(f"Encodage: {encoding} | Aucune modification nécessaire")
                
                with col2:
                    if mod_count > 0:
                        with st.expander("Détails"):
                            for mod in modifications[:5]:
                                if mod['type'] == 'update':
                                    st.write(f"• Mis à jour: `{mod['from']}` → `{mod['to']}`")
                                else:
                                    st.write(f"• Ajouté: `{mod['value']}`")
                            if len(modifications) > 5:
                                st.write(f"... +{len(modifications) - 5} autres")
                
                with col3:
                    # Toujours permettre le téléchargement
                    if encoding == 'iso-8859-1':
                        output_bytes = modified_content.encode('iso-8859-1', errors='ignore')
                    else:
                        output_bytes = modified_content.encode('utf-8', errors='ignore')
                    
                    st.download_button(
                        "📥",
                        data=output_bytes,
                        file_name=f"modified_{file.name}",
                        mime="application/xml",
                        key=f"dl_{idx}"
                    )
                
            except Exception as e:
                st.error(f"❌ Erreur avec {file.name}: {str(e)}")
                st.exception(e)
            
            if idx < len(uploaded_files) - 1:
                st.divider()
        
        # Résumé
        st.markdown("---")
        st.markdown("### 📈 Résumé")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Fichiers traités", total_files)
        with col2:
            st.metric("Fichiers modifiés", sum(1 for f in processed_files if f['count'] > 0))
        with col3:
            st.metric("Total modifications", total_modifications)
        
        # ZIP si plusieurs fichiers
        if len(processed_files) > 1:
            st.markdown("---")
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zf:
                for file_info in processed_files:
                    if file_info['encoding'] == 'iso-8859-1':
                        file_bytes = file_info['content'].encode('iso-8859-1', errors='ignore')
                    else:
                        file_bytes = file_info['content'].encode('utf-8', errors='ignore')
                    zf.writestr(f"modified_{file_info['name']}", file_bytes)
            
            zip_buffer.seek(0)
            st.download_button(
                "📦 Télécharger tous les fichiers (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="xml_modifications.zip",
                mime="application/zip",
                use_container_width=True
            )

else:
    st.info("👆 Chargez vos fichiers XML pour commencer")
    
    # Test
    st.markdown("### 🧪 Fichier de test")
    test_xml = """<?xml version="1.0" encoding="ISO-8859-1"?>
<Jobs>
    <Job>
        <Description>Poste niveau "A - Peu Qualifié"</Description>
        <PositionLevel>A</PositionLevel>
    </Job>
    <Job>
        <Description>Manager "B - Qualifié"</Description>
        <PositionLevel>B</PositionLevel>
    </Job>
</Jobs>"""
    
    st.download_button(
        "📥 Télécharger fichier test",
        data=test_xml.encode('iso-8859-1'),
        file_name="test.xml",
        mime="application/xml"
    )
