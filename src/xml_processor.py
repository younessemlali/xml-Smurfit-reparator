import re
import io
from lxml import etree

QUOTE_RE = re.compile(r'"([^"]+)"')

def process_xml(file_content: bytes):
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(io.BytesIO(file_content), parser)
    root = tree.getroot()

    added = 0
    for desc in root.xpath("//Description"):
        text = "".join(desc.itertext())
        match = QUOTE_RE.search(text)
        if match:
            level = match.group(1).strip()
            parent = desc.getparent()
            if parent.find("PositionLevel") is None:
                etree.SubElement(parent, "PositionLevel").text = level
                added += 1

    output = etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="utf-8")
    return output, added
