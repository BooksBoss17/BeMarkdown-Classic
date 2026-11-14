"""Installation-path differences must not authorize changed model libraries."""
import base64
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'SOURCE/bemarkdown/src/bemarkdown/stage_forecasts.py'
spec = importlib.util.spec_from_file_location('tested_forecasts', SOURCE)
forecasts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(forecasts)


class PortableRecordTests(unittest.TestCase):
    def setUp(self):
        self.recipe = {'schema': 'windows-wheel-record-installation-v1',
                       'dist_info_dir': 'example-1.dist-info',
                       'generated_entrypoint_files': ['../../Scripts/example.exe']}
        self.payload = 'example/core.py,sha256=AAAA,100\n'

    def identity(self, text):
        return forecasts.portable_record_identity(text, self.recipe)

    def test_installer_and_console_launcher_changes_only(self):
        left = self.payload + '../../Scripts/example.exe,sha256=OLD,1\nexample-1.dist-info/INSTALLER,sha256=UV,2\n'
        right = self.payload + '../../Scripts/example.exe,sha256=NEW,2\nexample-1.dist-info/INSTALLER,sha256=PIP,3\n'
        self.assertEqual(self.identity(left), self.identity(right))

    def test_payload_hash_change_rejected_by_frozen_identity(self):
        self.assertNotEqual(self.identity(self.payload), self.identity(self.payload.replace('AAAA', 'BBBB')))

    def test_unregistered_script_is_not_ignored(self):
        self.assertNotEqual(self.identity(self.payload), self.identity(self.payload + '../../Scripts/unknown.exe,sha256=AAAA,1\n'))

    def test_duplicate_payload_rejected(self):
        with self.assertRaises(forecasts.ForecastAdmissionError):
            self.identity(self.payload + self.payload)

    def test_generated_bytecode_duplicates_do_not_change_payload(self):
        row = 'example/__pycache__/core.cpython-311.pyc,,\n'
        self.assertEqual(self.identity(self.payload), self.identity(self.payload + row + row))

    def test_unknown_recipe_rejected(self):
        self.recipe['schema'] = 'allow-everything'
        with self.assertRaises(forecasts.ForecastAdmissionError):
            self.identity(self.payload)

    def test_real_loader_tampering_still_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            metadata = root / 'example-1.dist-info'
            metadata.mkdir()
            (root / 'example').mkdir()
            code = root / 'example/core.py'
            code.write_bytes(b'answer = 1\n')
            (metadata / 'METADATA').write_bytes(b'Metadata-Version: 2.1\nName: example\nVersion: 1\n')
            record = metadata / 'RECORD'
            record.write_text(self.payload, encoding='utf-8')
            sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            recipe = dict(self.recipe, sha256=self.identity(self.payload))
            required = {'example': {'version': '1', 'metadata_sha256': sha(metadata / 'METADATA'),
                                   'record_sha256': sha(record), 'loader_files': {'example/core.py': sha(code)},
                                   'portable_record': recipe}}
            record.write_text(self.payload + 'example-1.dist-info/INSTALLER,sha256=PIP,3\n', encoding='utf-8')
            actual = forecasts.dependency_identity([root], required)
            self.assertNotEqual(actual['example']['record_sha256'], required['example']['record_sha256'])
            code.write_bytes(b'answer = 2\n')
            with self.assertRaises(forecasts.ForecastAdmissionError):
                forecasts.dependency_identity([root], required)


if __name__ == '__main__':
    unittest.main()
