"""Convenience runner that discovers and runs all tests in `tests/test_*.py`."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

if __name__ == "__main__":
    tests_dir = Path(__file__).resolve().parent
    suite = unittest.defaultTestLoader.discover(start_dir=str(tests_dir), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
