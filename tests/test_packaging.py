"""Offline structural tests for HACS."""
import importlib.util
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("package_check",ROOT/"tools/check_repository.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class TestPackaging(unittest.TestCase):
    def test_layout(self):
        self.assertEqual(mod.check(ROOT),[])
    def test_mismatched_folder_is_rejected(self):
        self.assertEqual(mod.check(ROOT),[])
if __name__=="__main__":unittest.main()
