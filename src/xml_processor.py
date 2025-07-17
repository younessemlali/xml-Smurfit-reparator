import re
import io
import xml.etree.ElementTree as ET
import defusedxml.ElementTree as DET

QUOTE_RE = re.compile(r'"([^"]+)"')

def process_xml(file_content: bytes):
    root = DET.parse(io.BytesIO(file_content)).getroot()

    added = 0
    for desc in root.iter("Description"):
        text = "".join(desc.itertext())
        match = QUOTE_RE.search(text)
        if match:
            level = match.group(1).strip()
            parent = desc
            # Remonter jusqu’au parent "Job" ou racine
            while parent is not None and parent.find("PositionLevel") is None:
                parent = parent.getparent() or parent
            if parent is not None and parent.find("PositionLevel") is None:
                ET.SubElement(parent, "PositionLevel").text = level
                added += 1

    # Retourner le XML corrigé
    return ET.tostring(root, encoding="utf-8"), added
