import pytest
import os
from utils.file_processor import process_xml

def test_process_xml_no_entities(tmp_path):
    # Test that normal XML works
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<root><child>data</child></root>", encoding="utf-8")

    result = process_xml(str(xml_file))
    assert result["success"] is True
    assert result["data"]["root"]["child"] == "data"

def test_process_xml_with_xxe(tmp_path):
    # Test that XML with entities is blocked (or raises an error gracefully handled by the try/except)
    xml_file = tmp_path / "xxe.xml"
    xxe_content = """<!DOCTYPE foo [
<!ELEMENT foo ANY>
<!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<foo>&xxe;</foo>"""
    xml_file.write_text(xxe_content, encoding="utf-8")

    result = process_xml(str(xml_file))
    # It should either fail completely due to the security restriction, or not expand the entity
    # If the parser raises ValueError ("entities are disabled") it will be caught
    assert result["success"] is False
    assert "entities are disabled" in result["error"] or "entities are forbidden" in result["error"]
