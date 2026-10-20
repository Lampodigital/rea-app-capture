"""Verifiche dell'inventario con dossier sintetici isolati."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/evidence_bundle.py'


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'dossier'
        self.run_cli('init', self.root, '--app', 'Synthetic app', '--platform', 'ios')
        self.file = self.root / 'assets/example.txt'
        self.file.write_text('synthetic evidence', encoding='utf-8')

    def run_cli(self, *args, code=0):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        return result.stdout.strip()

    def add_file(self, file='assets/example.txt', *args, code=0):
        return self.run_cli('add', self.root, file, '--kind', 'notes', '--origin', 'synthetic fixture', *args, code=code)

    def read(self):
        return json.loads((self.root / 'manifest.json').read_text())

    def write(self, data):
        (self.root / 'manifest.json').write_text(json.dumps(data), encoding='utf-8')

    def invalid(self):
        report = json.loads(self.run_cli('validate', self.root, code=1))
        self.assertFalse(report['valid'])
        self.assertTrue(report['errors'])
        return report

    def test_init_and_register_preserves_content(self):
        self.assertTrue(json.loads(self.run_cli('validate', self.root))['valid'])
        identifier = self.add_file()
        self.assertTrue(identifier.startswith('art_'))
        record = self.read()['artifacts'][0]
        self.assertEqual(record['path'], 'assets/example.txt')
        self.assertEqual(record['bytes'], len(b'synthetic evidence'))
        self.assertEqual(self.file.read_text(), 'synthetic evidence')
        self.assertTrue(json.loads(self.run_cli('validate', self.root))['valid'])
        if os.name == 'posix':
            self.assertEqual(self.root.stat().st_mode & 0o777, 0o700)
            self.assertEqual((self.root / 'manifest.json').stat().st_mode & 0o777, 0o600)

    def test_existing_destination_not_overwritten(self):
        before = (self.root / 'manifest.json').read_bytes()
        self.run_cli('init', self.root, '--app', 'other', '--platform', 'ios', code=2)
        self.assertEqual((self.root / 'manifest.json').read_bytes(), before)

    def test_normalize_and_reject_path_aliases(self):
        self.add_file('assets/./example.txt')
        self.assertEqual(self.read()['artifacts'][0]['path'], 'assets/example.txt')
        for alias in ('assets/example.txt', './assets/example.txt', 'assets//example.txt'):
            with self.subTest(alias=alias):
                self.add_file(alias, code=2)
        self.assertEqual(len(self.read()['artifacts']), 1)

    def test_legacy_alias_manifest_is_invalid(self):
        self.add_file()
        data = self.read()
        other = copy.deepcopy(data['artifacts'][0])
        other.update(id='legacy-second', path='assets/./example.txt')
        data['artifacts'].append(other)
        self.write(data)
        self.invalid()
        self.add_file(code=2)

    def test_external_paths_directories_and_self_are_rejected(self):
        outside = self.base / 'outside.txt'
        outside.write_text('outside')
        for path in ('../outside.txt', str(outside), 'assets', 'manifest.json', 'missing.txt'):
            with self.subTest(path=path):
                self.add_file(path, code=2)

    def test_symlink_escape_and_internal_alias(self):
        outside = self.base / 'outside.txt'
        outside.write_text('outside')
        (self.root / 'assets/escape').symlink_to(outside)
        self.add_file('assets/escape', code=2)
        self.add_file()
        (self.root / 'assets/alias').symlink_to(self.file)
        self.add_file('assets/alias', code=2)
        (self.root / 'manifest.json').unlink()
        external_manifest = self.base / 'outside-manifest.json'
        external_manifest.write_text('{}')
        (self.root / 'manifest.json').symlink_to(external_manifest)
        self.invalid()
        self.add_file(code=2)
        self.assertEqual(external_manifest.read_text(), '{}')

    def test_changed_and_missing_files(self):
        self.add_file()
        self.file.write_text('changed')
        self.invalid()
        self.file.unlink()
        self.invalid()

    def test_parent_metadata_and_cycles(self):
        parent = self.add_file()
        child = self.root / 'crops/child.txt'
        child.write_text('synthetic crop')
        self.add_file('crops/child.txt', '--parent', parent, '--timestamp', '1.25', '--crop', '0,0,10,20')
        self.assertTrue(json.loads(self.run_cli('validate', self.root))['valid'])
        data = self.read()
        data['artifacts'][0]['parent'] = data['artifacts'][1]['id']
        self.write(data)
        self.invalid()
        data['artifacts'][0]['parent'] = 'missing-parent'
        self.write(data)
        self.invalid()

    def test_parent_is_required_and_must_exist(self):
        for args in (('--timestamp', '0'), ('--crop', '0,0,1,1'), ('--parent', 'missing')):
            self.add_file('assets/example.txt', *args, code=2)
        self.assertEqual(self.read()['artifacts'], [])

    def test_bad_cli_metadata_does_not_mutate_manifest(self):
        before = self.read()
        for args in (('--timestamp', 'nan'), ('--timestamp', '-1'), ('--crop', '0,0,0,1'), ('--origin', ' ')):
            self.add_file('assets/example.txt', *args, code=2)
        self.assertEqual(before, self.read())

    def test_malformed_json_and_schema_have_structured_errors(self):
        self.add_file()
        valid = self.read()
        bad_values = [[], None, 1, 'text', {}, {'schema_version': 1, 'artifacts': [None]},
                      {**valid, 'artifacts': {}}, {**valid, 'schema_version': True}]
        for value in bad_values:
            with self.subTest(value=value):
                self.write(value)
                self.invalid()
                self.add_file(code=2)
        for text in ('{broken', '{"schema_version":NaN}', ''):
            (self.root / 'manifest.json').write_text(text)
            self.invalid()

    def test_invalid_artifact_field_types_are_rejected(self):
        self.add_file()
        valid = self.read()
        replacements = {'id': [], 'path': 1, 'origin': '', 'kind': [], 'sha256': 'wrong', 'bytes': True,
                        'timestamp': '1', 'crop': [0, 0, True, 2], 'parent': {}, 'url': [], 'note': None}
        for field, value in replacements.items():
            with self.subTest(field=field):
                data = copy.deepcopy(valid)
                data['artifacts'][0][field] = value
                self.write(data)
                self.invalid()
        data = copy.deepcopy(valid)
        data['artifacts'][0].update(timestamp=10 ** 1000, parent='missing')
        self.write(data)
        self.invalid()

    def test_duplicate_ids_and_old_id_prefix(self):
        self.add_file()
        data = self.read()
        data['artifacts'][0]['id'] = 'ev_' + 'a' * 32
        self.write(data)
        self.assertTrue(json.loads(self.run_cli('validate', self.root))['valid'])
        data['artifacts'].append(copy.deepcopy(data['artifacts'][0]))
        self.write(data)
        self.invalid()


if __name__ == '__main__':
    unittest.main()
