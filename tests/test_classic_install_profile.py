"""A matching version alone must not hide an incomplete installation."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClassicInstallProfile(unittest.TestCase):
    def test_ready_summary_cannot_hide_failed_capability(self):
        validator = load('verify_runtime_profile')
        with self.assertRaises(RuntimeError):
            validator.require_doctor_ready({'readiness': 'READY_FULL', 'capabilities': {
                'paddle_model_suite': {'status': 'FAIL', 'reason': 'Fingerprint mismatch'}}})

    def test_complete_doctor_is_accepted(self):
        load('verify_runtime_profile').require_doctor_ready({
            'readiness': 'READY_FULL', 'capabilities': {'core': {'status': 'PASS'}}})

    def test_qwen_lock_covers_forecast_dependencies(self):
        import json
        qwen = load('install_qwen_runtime')
        expected = qwen.expected_versions(ROOT / 'TOOLS/bemarkdown')
        forecast = json.loads((ROOT / 'SOURCE/bemarkdown/src/bemarkdown/runtime/RESOURCE_FORECASTS_6GB.json').read_text(encoding='utf-8'))
        required = {k: v['version'] for k, v in forecast['dependency_profiles']['qwen']['distributions'].items()}
        self.assertEqual(expected, required)

    def test_sharing_violation_retries_only_failed_creation(self):
        runtime = load('runtime_setup')
        error = PermissionError('temporary sharing violation')
        error.winerror = 32
        with patch.object(runtime.subprocess, 'run', side_effect=[error, 'completed']) as run, patch.object(runtime.time, 'sleep'):
            self.assertEqual(runtime.readonly_probe(['python', '-c', 'pass']), 'completed')
            self.assertEqual(run.call_count, 2)

    def test_other_spawn_error_is_not_retried(self):
        runtime = load('runtime_setup')
        with patch.object(runtime.subprocess, 'run', side_effect=PermissionError('denied')) as run:
            with self.assertRaises(PermissionError):
                runtime.readonly_probe(['python'])
            self.assertEqual(run.call_count, 1)

    def test_other_python_patch_rejected(self):
        qwen = load('install_qwen_runtime')
        with patch.object(qwen, 'query', return_value={'python': '3.12.14', 'versions': {'torch': 'test'}}):
            with self.assertRaises(RuntimeError):
                qwen.verify('unused', {'torch': 'test'})

    def test_missing_dependency_rejected(self):
        qwen = load('install_qwen_runtime')
        with patch.object(qwen, 'query', return_value={'python': qwen.PYTHON_VERSION, 'versions': {}}):
            with self.assertRaises(RuntimeError):
                qwen.verify('unused', {'numpy': '2.5.4'})


if __name__ == '__main__':
    unittest.main()
