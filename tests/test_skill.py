"""Integrità del pacchetto che viene installato come skill."""
from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class SkillPackageTests(unittest.TestCase):
    def test_metadata_and_local_reference_targets(self):
        text = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        parts = text.split('---', 2)
        metadata = yaml.safe_load(parts[1])
        self.assertEqual(metadata['name'], 'rea-app-capture')
        self.assertTrue(metadata['description'].strip())
        for doc in [ROOT / 'SKILL.md', ROOT / 'README.md', *sorted((ROOT / 'references').glob('*.md'))]:
            for link in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
                if '://' not in link and not link.startswith('#'):
                    self.assertTrue((doc.parent / link.split('#')[0]).is_file(), (doc.name, link))
        ui = yaml.safe_load((ROOT / 'agents/openai.yaml').read_text())['interface']
        self.assertIn('$rea-app-capture', ui['default_prompt'])
        self.assertTrue(25 <= len(ui['short_description']) <= 64)

    def test_no_bundled_media_or_private_artifacts(self):
        forbidden = {'.png', '.jpg', '.webp', '.mp4', '.mov', '.pem', '.p12', '.mobileprovision', '.key'}
        for folder in ('scripts', 'references', 'agents'):
            for path in (ROOT / folder).rglob('*'):
                if path.is_file():
                    self.assertNotIn(path.suffix.lower(), forbidden)


if __name__ == '__main__':
    unittest.main()
