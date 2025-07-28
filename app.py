import streamlit as st
import re
import io
import zipfile

st.set_page_config(page_title="XML Smurfit Reparator", page_icon="🔧", layout="wide")

st.title("🔧 XML Smurfit Reparator - Version Robuste")
st.markdown("Mise à jour automatique des balises PositionLevel dans vos fichiers XML (ISO-8859-1)")

def detect_xml_encoding(file_bytes):
    """Détecte l'encodage déclaré dans l'en-tête XML."""
    try:
        # Lire le début du fichier pour trouver la déclaration
        header = file_bytes[:500].decode('ascii', errors='ignore')
        
        # Chercher la déclaration d'encodage
        match = re.search(r'encoding\s*=\s*["\']([^"\']+)["\']', header, re.IGNORECASE)
        if match:
            declared_encoding = match.group(1).lower()
            
            # Normaliser les noms d'encodage
            encoding_map = {
                'iso-8859-1': 'iso-8859-1',
                'iso88591': 'iso-8859-1',
                'latin1': 'iso-8859-1',
                'latin-1': 'iso-8859-1',
                'utf-8': 'utf-8',
                'utf8': 'utf-8'
            }
            
            return encoding_map.get(declared_encoding, declared_encoding)
    except:
        pass
    
    # Par défaut pour vos fichiers
    return 'iso-8859-1'

def safe_decode(file_bytes):
    """Décode le fichier de manière sûre en priorisant ISO-8859-1."""
    # D'abord, vérifier l'encodage déclaré dans le XML
    declared_encoding = detect_xml_encoding(file_bytes)
    
    # Liste des encodages à essayer (ISO-8859-1 en premier maintenant)
    encodings = [
        declared_encoding,  # L'encodage déclaré en premier
        'iso-8859-1',       # Votre standard
        'windows-1252',     # Proche de ISO-8859-1
        'utf-8',
        'utf-8-sig',
        'latin-1',
        'cp1252',
        'ascii'
    ]
    
    # Éliminer les doublons tout en préservant l'ordre
    seen = set()
    unique_encodings = []
    for enc in encodings:
        if enc and enc not in seen:
            seen.add(enc)
            unique_encodings.append(enc)
    
    for encoding in unique_encodings:
        try:
            content = file_bytes.decode(encoding)
            # Vérifier que le décodage est cohérent
            content.encode(encoding)  # Si ça ne plante pas, c'est bon
            return content, encoding
        except (UnicodeDecodeError, UnicodeEncodeError, LookupError):
            continue
    
    # En dernier recours, ISO-8859-1 avec remplacement
    return file_bytes.decode('iso-8859-1', errors='replace'), 'iso-8859-1 (avec remplacement)'

def process_xml_robust(content):
    """Traite le XML ligne par ligne pour une robustesse maximale."""
    lines = content.split('\n')
    result_lines = []
    modifications = []
    i = 0
    
    while i < len(lines):
        current_line = lines[i]
        result_lines.append(current_line)
        
        # Détecter une balise Description (avec ou sans namespace)
        if re.search(r'<[^/>]*Description>', current_line):
            # Collecter tout le contenu de Description
            desc_content = current_line
            desc_start = i
            
            # Si Description n'est pas fermée sur la même ligne
            if not re.search(r'</[^>]*Description>', current_line):
                i += 1
                while i < len(lines):
                    result_lines.append(lines[i])
                    desc_content += ' ' + lines[i]
                    if re.search(r'</[^>]*Description>', lines[i]):
                        break
                    i += 1
            
            # Chercher la valeur entre guillemets (format: X - Description)
            matches = re.findall(r'"([A-Z]\s*-\s*[^"]+)"', desc_content)
            
            if matches:
                new_value = matches[-1].strip()
                
                # Chercher PositionLevel dans les 15 lignes suivantes
                found = False
                j = i + 1
                search_limit = min(i + 16, len(lines))
                
                while j < search_limit:
                    if j < len(lines):
                        line = lines[j]
                        
                        # Si on trouve PositionLevel
                        position_match = re.search(r'(<[^/>]*PositionLevel>)([^<]*)(</[^>]*PositionLevel>)', line)
                        if position_match:
                            found = True
                            current_value = position_match.group(2).strip()
                            
                            # Si la valeur est différente, la mettre à jour
                            if current_value != new_value:
                                # Créer la nouvelle ligne en préservant l'indentation
                                new_line = line.replace(
                                    position_match.group(0),
                                    position_match.group(1) + new_value + position_match.group(3)
                                )
                                
                                # Remplacer dans le résultat
                                result_index = len(result_lines) + (j - i) - 1
                                if result_index < len(result_lines):
                                    result_lines[result_index] = new_line
                                else:
                                    # On ajoutera la ligne modifiée quand on y arrivera
                                    lines[j] = new_line
                                
                                modifications.append({
                                    'type': 'update',
                                    'old': current_value,
                                    'new': new_value
                                })
                            break
                        
                        # Si on trouve une nouvelle section, arrêter
                        if re.search(r'<[^/>]*(?:Job|WorkSite|Position)>', line):
                            break
                    j += 1
                
                # Si PositionLevel n'existe pas, l'ajouter
                if not found:
                    # Trouver où l'insérer (après PositionStatus ou PositionTitle)
                    insert_after = i
                    indent = "    "  # Indentation par défaut
                    
                    j = i + 1
                    while j < min(i + 16, len(lines)):
                        if j < len(lines):
                            line = lines[j]
                            
                            # Récupérer l'indentation
                            indent_match = re.match(r'^(\s*)', line)
                            if indent_match:
                                indent = indent_match.group(1)
                            
                            # Insérer après ces balises
                            if re.search(r'</[^>]*(?:PositionStatus|PositionTitle|PositionCharacteristics)>', line):
                                insert_after = j
                                break
                        j += 1
                    
                    # Déterminer le namespace
                    ns_match = re.search(r'<([^:>/\s]+:)?Description>', desc_content)
                    namespace = ns_match.group(1) if ns_match and ns_match.group(1) else ''
                    
                    # Créer la nouvelle ligne
                    new_line = f'{indent}<{namespace}PositionLevel>{new_value}</{namespace}PositionLevel>'
                    
                    # Calculer où insérer dans result_lines
                    insert_index = len(result_lines) + (insert_after - i)
                    if insert_index <= len(result_lines):
                        result_lines.insert(insert_index, new_line)
                    else:
                        # Insérer dans lines pour plus tard
                        lines.insert(insert_after + 1, new_line)
                    
                    modifications.append({
                        'type': 'add',
                        'value': new_value
                    })
        
        i += 1
    
    return '\n'.join(result_lines), modifications

# Configuration de l'uploader avec des paramètres robustes
st.markdown("### 📁 Sélection des fichiers")
uploaded_files = st.file_uploader(
    "Glissez vos fichiers XML ici ou cliquez pour parcourir",
    type=['xml'],
    accept_multiple_files=True,
    help="Formats supportés : .xml (encodage ISO-8859-1 recommandé)"
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} fichier(s) chargé(s)")
    
    # Bouton de traitement
    if st.button("🚀 Lancer le traitement", type="primary", use_container_width=True):
        st.markdown("---")
        st.markdown("### 📊 Résultats du traitement")
        
        # Créer des colonnes pour les statistiques globales
        total_files = len(uploaded_files)
        total_modifications = 0
        successful_files = 0
        all_processed_files = []
        
        # Barre de progression
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Traiter chaque fichier
        for idx, file in enumerate(uploaded_files):
            status_text.text(f"Traitement de {file.name}...")
            
            with st.container():
                # Lire le fichier
                file_bytes = file.read()
                content, encoding = safe_decode(file_bytes)
                
                # Traiter le XML
                try:
                    result_content, modifications = process_xml_robust(content)
                    
                    # Compter les modifications
                    nb_updates = sum(1 for m in modifications if m['type'] == 'update')
                    nb_adds = sum(1 for m in modifications if m['type'] == 'add')
                    total_mods = nb_updates + nb_adds
                    
                    if total_mods > 0:
                        total_modifications += total_mods
                        successful_files += 1
                        all_processed_files.append({
                            'name': file.name,
                            'content': result_content,
                            'encoding': encoding,
                            'modifications': total_mods
                        })
                    
                    # Afficher les résultats
                    col1, col2, col3 = st.columns([4, 2, 1])
                    
                    with col1:
                        if total_mods > 0:
                            st.markdown(f"**✅ {file.name}**")
                            st.caption(f"Encodage: {encoding} | Mises à jour: {nb_updates} | Ajouts: {nb_adds}")
                        else:
                            st.markdown(f"**ℹ️ {file.name}**")
                            st.caption(f"Encodage: {encoding} | Aucune modification nécessaire")
                    
                    with col2:
                        if total_mods > 0 and modifications:
                            with st.expander("Voir les détails"):
                                for mod in modifications[:5]:
                                    if mod['type'] == 'update':
                                        st.write(f"• Mis à jour : `{mod['old']}` → `{mod['new']}`")
                                    else:
                                        st.write(f"• Ajouté : `{mod['value']}`")
                                if len(modifications) > 5:
                                    st.write(f"... et {len(modifications) - 5} autres")
                    
                    with col3:
                        # Bouton de téléchargement - Préserver l'encodage original
                        if encoding.startswith('iso-8859-1'):
                            output_data = result_content.encode('iso-8859-1', errors='ignore')
                        else:
                            output_data = result_content.encode(encoding.split()[0], errors='ignore')
                        
                        st.download_button(
                            "📥",
                            data=output_data,
                            file_name=f"modified_{file.name}",
                            mime="application/xml",
                            key=f"dl_{idx}",
                            help="Télécharger le fichier modifié"
                        )
                    
                except Exception as e:
                    st.error(f"❌ **{file.name}** - Erreur : {str(e)}")
                
                if idx < len(uploaded_files) - 1:
                    st.divider()
            
            # Mise à jour de la progression
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        # Nettoyer la barre de progression
        progress_bar.empty()
        status_text.empty()
        
        # Résumé final
        st.markdown("---")
        st.markdown("### 📈 Résumé")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Fichiers traités", total_files)
        with col2:
            st.metric("Fichiers modifiés", successful_files)
        with col3:
            st.metric("Total modifications", total_modifications)
        
        # Option de téléchargement groupé si plusieurs fichiers modifiés
        if len(all_processed_files) > 1:
            st.markdown("---")
            st.markdown("### 📦 Téléchargement groupé")
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_info in all_processed_files:
                    # Encoder selon l'encodage original
                    if file_info['encoding'].startswith('iso-8859-1'):
                        file_data = file_info['content'].encode('iso-8859-1', errors='ignore')
                    else:
                        file_data = file_info['content'].encode('utf-8', errors='ignore')
                    
                    zf.writestr(f"modified_{file_info['name']}", file_data)
            
            zip_buffer.seek(0)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    "📦 Télécharger tous les fichiers modifiés (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="xml_modifications.zip",
                    mime="application/zip",
                    use_container_width=True
                )

else:
    # Instructions
    st.info("👆 Commencez par charger vos fichiers XML")
    
    with st.expander("📖 Mode d'emploi", expanded=True):
        st.markdown("""
        ### Comment utiliser cette application ?
        
        1. **Chargez vos fichiers XML** en cliquant sur le bouton ci-dessus
        2. **Cliquez sur "Lancer le traitement"**
        3. **Téléchargez les fichiers modifiés** individuellement ou en groupe (ZIP)
        
        ### Que fait l'application ?
        
        - Recherche les valeurs entre guillemets au format `"X - Description"` dans les balises Description
        - Met à jour les balises PositionLevel existantes avec la valeur complète
        - Ajoute les balises PositionLevel manquantes
        - **Préserve l'encodage ISO-8859-1** et tous les caractères accentués
        - Conserve le format XML original (namespaces, indentation)
        
        ### Exemple de transformation
        
        **Avant :**
        ```xml
        <Description>Poste "B - Qualifié"</Description>
        <PositionLevel>B</PositionLevel>
        ```
        
        **Après :**
        ```xml
        <Description>Poste "B - Qualifié"</Description>
        <PositionLevel>B - Qualifié</PositionLevel>
        ```
        """)
    
    # Fichier de test
    st.markdown("### 🧪 Fichier de test")
    test_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
<Jobs>
    <Job>
        <Description>Opérateur machine "A - Peu Qualifié"</Description>
        <PositionLevel>A</PositionLevel>
    </Job>
    <Job>
        <Description>Technicien "B - Qualifié"</Description>
    </Job>
    <Job>
        <Description>Ingénieur système "C - Très Qualifié"</Description>
        <PositionLevel>C</PositionLevel>
    </Job>
</Jobs>"""
    
    st.download_button(
        "📥 Télécharger un fichier de test ISO-8859-1",
        data=test_content.encode('iso-8859-1'),
        file_name="test_smurfit.xml",
        mime="application/xml"
    )
