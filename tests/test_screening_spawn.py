"""Only a failed CreateProcess may be repeated; a started worker is never retried."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
import zipfile


class ScreeningSpawnTests(unittest.TestCase):
    def setup_function(self, outcomes):
        root = Path(__file__).resolve().parents[1]
        with zipfile.ZipFile(root / 'TOOLS/semantic_retention/dist/engine.zip') as archive:
            source = archive.read('tmp/retention-v6-20261003/v36-low-commit/job_family_v4.py').decode()
        function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'create_suspended_process')
        create, save, sleep = Mock(side_effect=outcomes), Mock(), Mock()
        namespace = {'_winapi': SimpleNamespace(CreateProcess=create), 'save': save,
                     'probe': SimpleNamespace(ROOT=Path('unused')), 'time': SimpleNamespace(sleep=sleep)}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<spawn-boundary>', 'exec'), namespace)
        return namespace['create_suspended_process'], create, save, sleep

    def sharing_error(self):
        error = PermissionError('sharing violation')
        error.winerror = 32
        return error

    def test_success_not_repeated(self):
        function, create, save, sleep = self.setup_function([(1, 2, 3, 4)])
        self.assertEqual(function('argv'), (1, 2, 3, 4))
        self.assertEqual(create.call_count, 1)
        save.assert_not_called()

    def test_only_pre_creation_failure_recovers(self):
        function, create, save, sleep = self.setup_function([self.sharing_error(), (1, 2, 3, 4)])
        self.assertEqual(function('argv'), (1, 2, 3, 4))
        self.assertEqual(create.call_count, 2)
        self.assertFalse(save.call_args.args[1]['model_request_started'])

    def test_recovery_is_bounded(self):
        function, create, save, sleep = self.setup_function([self.sharing_error()] * 20)
        with self.assertRaises(PermissionError):
            function('argv')
        self.assertEqual(create.call_count, 20)

    def test_other_error_not_retried(self):
        function, create, save, sleep = self.setup_function([PermissionError('denied')])
        with self.assertRaises(PermissionError):
            function('argv')
        self.assertEqual(create.call_count, 1)


if __name__ == '__main__':
    unittest.main()
