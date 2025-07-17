import re
import io
import xml.etree.ElementTree as ET
import defusedxml.ElementTree as DET
from typing import Tuple, Optional

# Expression régulière pour extraire le contenu entre guillemets
QUOTE_RE = re.compile(r'"([^"]+)"')

def find_parent_element(element: ET.Element, root: ET.Element, target_tag: str = "Job") -> Optional[ET.Element]:
    """
    Trouve l'élément parent approprié pour ajouter PositionLevel.
    Recherche d'abord un parent 'Job', sinon utilise le parent direct.
    """
    # Créer un mapping element -> parent
    parent_map = {c: p for p in root.iter() for c in p}
    
    current = element
    while current is not None:
        parent = parent_map.get(current)
        if parent is None:
            break
            
        # Si on trouve un élément Job, on l'utilise
        if parent.tag == target_tag:
            return parent
            
        current = parent
    
    # Si pas de Job trouvé, retourner le parent direct
    return parent_map.get(element, element)

def process_xml(file_content: bytes) -> Tuple[str, int]:
    """
    Traite un fichier XML pour ajouter les balises PositionLevel manquantes.
    
    Args:
        file_content: Contenu du fichier XML en bytes
        
    Returns:
        Tuple contenant:
        - Le contenu XML corrigé en string
        - Le nombre de balises PositionLevel ajoutées
    """
    try:
        # Parser le XML de manière sécurisée
        root = DET.parse(io.BytesIO(file_content)).getroot()
        
        added_count = 0
        
        # Parcourir toutes les balises Description
        for desc in root.iter("Description"):
            # Extraire le texte complet de l'élément
            text = desc.text or ""
            
            # Chercher du texte entre guillemets
            match = QUOTE_RE.search(text)
            if match:
                position_level_value = match.group(1).strip()
                
                # Trouver le parent approprié
                parent = find_parent_element(desc, root)
                
                if parent is not None:
                    # Vérifier si PositionLevel n'existe pas déjà
                    existing_position_level = parent.find("PositionLevel")
                    
                    if existing_position_level is None:
                        # Créer la nouvelle balise PositionLevel
                        position_level = ET.SubElement(parent, "PositionLevel")
                        position_level.text = position_level_value
                        added_count += 1
                    else:
                        # Optionnel : mettre à jour si la valeur est différente
                        if existing_position_level.text != position_level_value:
                            existing_position_level.text = position_level_value
        
        # Convertir l'arbre XML en string avec indentation
        indent_xml(root)
        xml_string = ET.tostring(root, encoding="unicode", method="xml")
        
        # Ajouter la déclaration XML si elle n'est pas présente
        if not xml_string.startswith("<?xml"):
            xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_string
        
        return xml_string, added_count
        
    except Exception as e:
        raise Exception(f"Erreur lors du traitement XML : {str(e)}")

def indent_xml(elem: ET.Element, level: int = 0) -> None:
    """
    Ajoute une indentation propre au XML pour une meilleure lisibilité.
    """
    indent = "\n" + "  " * level
    
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent

# Fonction utilitaire pour valider le format des position levels
def validate_position_level(value: str) -> bool:
    """
    Valide le format d'un niveau de position.
    Exemple de formats valides : "A - Peu Qualifié", "B - Qualifié", etc.
    """
    # Pattern pour valider le format : Lettre - Description
    pattern = re.compile(r'^[A-Z]\s*-\s*.+$')
    return bool(pattern.match(value))

# Test unitaire simple
if __name__ == "__main__":
    # Exemple de test
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <Job>
            <Description>Poste de niveau "A - Peu Qualifié"</Description>
            <Salary>25000</Salary>
        </Job>
        <Job>
            <Description>Poste senior "C - Très Qualifié"</Description>
            <Salary>45000</Salary>
            <PositionLevel>C - Très Qualifié</PositionLevel>
        </Job>
    </root>"""
    
    result, count = process_xml(test_xml.encode('utf-8'))
    print(f"Balises ajoutées: {count}")
    print("Résultat:")
    print(result)
