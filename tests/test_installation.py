"""Esecuzione degli helper da installazioni isolate per entrambi i client."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ClientInstallationTests(unittest.TestCase):
    def test_shared_skill_in_both_client_layouts(self):
        with tempfile.TemporaryDirectory(prefix='app-capture-clients-') as temporary:
            home = Path(temporary)
            work = home / 'unrelated-project'
            work.mkdir()
            for client in ('.claude', '.codex'):
                with self.subTest(client=client):
                    target = home / client / 'skills/rea-app-capture'
                    # Claude Code needs SKILL.md, not Codex UI metadata.
                    target.mkdir(parents=True)
                    for relative in ('SKILL.md', 'README.md', 'requirements-video.txt'):
                        shutil.copy2(ROOT / relative, target / relative)
                    for relative in ('scripts', 'references'):
                        shutil.copytree(ROOT / relative, target / relative,
                                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                    if client == '.codex':
                        shutil.copytree(ROOT / 'agents', target / 'agents')
                    metadata = yaml.safe_load((target / 'SKILL.md').read_text().split('---', 2)[1])
                    self.assertEqual(metadata['name'], target.name)
                    self.assertIsInstance(metadata['description'], str)
                    script = target / 'scripts/evidence_bundle.py'
                    dossier = work / (client[1:] + '-evidence')
                    subprocess.run([sys.executable, str(script), 'init', str(dossier),
                                    '--app', 'Synthetic demo', '--platform', 'web'],
                                   cwd=work, capture_output=True, check=True, timeout=20)
                    payload = dossier / 'assets/sample.txt'
                    payload.write_text('synthetic sample')
                    subprocess.run([sys.executable, str(script), 'add', str(dossier),
                                    'assets/sample.txt', '--kind', 'notes', '--origin', 'synthetic fixture'],
                                   cwd=work, capture_output=True, check=True, timeout=20)
                    result = subprocess.run([sys.executable, str(script), 'validate', str(dossier)],
                                            cwd=work, capture_output=True, check=True, text=True, timeout=20)
                    self.assertTrue(json.loads(result.stdout)['valid'])
                    subprocess.run([sys.executable, str(target / 'scripts/extract_video_frames.py'), '--help'],
                                   cwd=work, capture_output=True, check=True, timeout=20)


if __name__ == '__main__':
    unittest.main()
