"""Unit tests for the CLI entry point, flags, exit codes, and report formatting."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcu_validator import __version__  # noqa: E402
from mcu_validator.cli import validate_path  # noqa: E402


def _run_cli(*args: str, strict_warnings: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT_DIR), env.get("PYTHONPATH")]))
    cmd = [sys.executable]
    if strict_warnings:
        cmd.extend(["-W", "error"])
    cmd.extend(["-m", "mcu_validator.cli", *args])
    return subprocess.run(
        cmd,
        cwd=ROOT_DIR,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class CliTests(unittest.TestCase):
    """Tests for `mcu-validate` / `python -m mcu_validator.cli`."""

    def test_list_boards_flag(self) -> None:
        proc = _run_cli("--list-boards")
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("esp32-c3", proc.stdout)
        self.assertIn("esp32-s3", proc.stdout)

    def test_version_flag(self) -> None:
        proc = _run_cli("--version")
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn(__version__, proc.stdout)

    def test_no_runtime_warning_on_module_execution(self) -> None:
        proc = _run_cli("src/main.cpp", "esp32-c3", strict_warnings=True)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("Checked Pins   : 3", proc.stdout)

    def test_unknown_board_exits_with_code_2(self) -> None:
        proc = _run_cli("src/main.cpp", "unknown-mcu-999")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Error:", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_malformed_board_json_exits_with_code_2_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_board = Path(tmp) / "bad.json"
            bad_board.write_text("{broken json", encoding="utf-8")
            proc = _run_cli("src/main.cpp", str(bad_board))
            self.assertEqual(proc.returncode, 2)
            self.assertIn("Invalid JSON", proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)

    def test_custom_boards_dir_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            boards_dir = Path(tmp) / "my_boards"
            boards_dir.mkdir()
            (boards_dir / "tiny-mcu.json").write_text(
                json.dumps({"mcu": "TINY-MCU", "pins": {"3": {"capabilities": ["gpio"]}}}),
                encoding="utf-8",
            )
            sketch = Path(tmp) / "blink.cpp"
            sketch.write_text(
                "#define LED_PIN 3\nvoid setup() { pinMode(LED_PIN, OUTPUT); }\n",
                encoding="utf-8",
            )
            proc = _run_cli(str(sketch), "tiny-mcu", "--boards-dir", str(boards_dir))
            self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
            self.assertIn("TINY-MCU", proc.stdout)

    def test_warns_clearly_when_zero_pins_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty_sketch = Path(tmp) / "empty.cpp"
            empty_sketch.write_text("void setup() {}\nvoid loop() {}\n", encoding="utf-8")
            result, report = validate_path(empty_sketch, "esp32-c3")
            self.assertTrue(result.is_valid)
            self.assertIn("Checked Pins   : 0", report)
            self.assertIn("0 pin assignments were detected", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
