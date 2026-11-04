"""Check shipped assets and local links without network access."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_all_shipped_svgs_are_valid_and_self_contained(self):
        files = list((ROOT/'assets').glob('*.svg')) + list((ROOT/'preview/demo').glob('*.svg'))
        self.assertTrue(files)
        for path in files:
            with self.subTest(path=path.name):
                svg = ET.parse(path).getroot()
                self.assertEqual(svg.tag, '{http://www.w3.org/2000/svg}svg')
                for element in svg.iter():
                    self.assertNotIn(element.tag.rsplit('}', 1)[-1], ('script', 'foreignObject', 'image'))
                    for key, value in element.attrib.items():
                        self.assertFalse(key.lower().startswith('on'))
                        if key.rsplit('}', 1)[-1] == 'href':
                            self.assertTrue(value.startswith('#'))

    def test_readme_and_preview_images_resolve_inside_package(self):
        for path in (ROOT/'README.md', ROOT/'preview/index.html'):
            for reference in re.findall(r'(?:src|srcset)="([^"]+)"', path.read_text(encoding='utf-8')):
                with self.subTest(path=path.name, reference=reference):
                    target = (path.parent/reference).resolve()
                    self.assertTrue(target.is_relative_to(ROOT))
                    self.assertTrue(target.is_file())
