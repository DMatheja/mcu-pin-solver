"""End-to-end regression tests across all C++ scenarios in `tests/scenarios/`."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcu_validator import ParsedProject, PinRequest, load_board, parse_cpp, validate  # noqa: E402


def _revalidate_suggestion(project: ParsedProject, suggested: dict[str, int], board):
    """Apply Z3's suggested pin numbers back to the requests and re-validate."""
    repaired_requests = tuple(
        PinRequest(
            name=req.name,
            pin=suggested[req.name],
            capabilities=req.capabilities,
            bus_group=req.bus_group,
            location=req.location,
        )
        for req in project.requests
    )
    repaired_project = ParsedProject(
        requests=repaired_requests,
        active_resources=project.active_resources,
    )
    return validate(repaired_project, board)


class ScenarioTests(unittest.TestCase):
    """End-to-end validation of all C++ test scenarios via CLI and Python API."""

    SCENARIOS = [
        (ROOT_DIR / "src" / "main.cpp", "esp32-c3", True),
        (SCENARIOS_DIR / "00_flash_and_wifi_conflict.cpp", "esp32-c3", False),
        (SCENARIOS_DIR / "00_flash_and_wifi_conflict.cpp", "esp32-s3", True),
        (SCENARIOS_DIR / "01_valid_sketch.cpp", "esp32-c3", True),
        (SCENARIOS_DIR / "02_usb_serial_conflict.cpp", "esp32-c3", False),
        (SCENARIOS_DIR / "03_duplicate_and_invalid_pin.cpp", "esp32-c3", False),
        (SCENARIOS_DIR / "04_shared_i2c_bus.cpp", "esp32-c3", False),
        (SCENARIOS_DIR / "05_ast_ignores_strings_and_comments.cpp", "esp32-c3", True),
        (SCENARIOS_DIR / "06_multi_file_project" / "src", "esp32-c3", False),
    ]

    def test_cli_exit_codes_and_z3_soundness(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT_DIR), env.get("PYTHONPATH")]))

        for cpp_path, board_id, expect_sat in self.SCENARIOS:
            with self.subTest(path=cpp_path.name, board=board_id):
                proc = subprocess.run(
                    [sys.executable, "-m", "mcu_validator.cli", str(cpp_path), board_id],
                    cwd=ROOT_DIR,
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                actual_sat = proc.returncode == 0
                self.assertEqual(
                    actual_sat,
                    expect_sat,
                    msg=f"CLI output:\n{proc.stdout}\n{proc.stderr}",
                )

                # Every UNSAT scenario with a repair must become SAT after applying Z3's suggestion.
                if not expect_sat:
                    board = load_board(board_id)
                    project = parse_cpp(cpp_path, board)
                    result = validate(project, board)
                    self.assertFalse(result.is_valid)
                    self.assertTrue(result.repair_possible)
                    recheck = _revalidate_suggestion(project, result.suggested_pins, board)
                    self.assertTrue(
                        recheck.is_valid,
                        msg=f"Z3 suggestion was still invalid: {recheck.conflicts}",
                    )

    def test_minimal_invasive_and_strapping_avoidance(self) -> None:
        board = load_board("esp32-c3")
        project = parse_cpp(SCENARIOS_DIR / "00_flash_and_wifi_conflict.cpp", board)
        result = validate(project, board)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.suggested_pins["RELAY_PIN"], 4)  # Valid pin preserved
        self.assertIn(result.suggested_pins["SOIL_SENSOR"], {0, 1, 3})
        self.assertFalse(board.pins[result.suggested_pins["STATUS_LED"]].strapping)
        self.assertFalse(board.pins[result.suggested_pins["STATUS_LED"]].reserved)

    def test_shared_i2c_bus_keeps_bus_coupled_and_moves_only_led(self) -> None:
        board = load_board("esp32-c3")
        project = parse_cpp(SCENARIOS_DIR / "04_shared_i2c_bus.cpp", board)
        result = validate(project, board)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.suggested_pins["OLED_SDA"], 6)
        self.assertEqual(result.suggested_pins["BME280_SDA"], 6)
        self.assertEqual(result.suggested_pins["OLED_SCL"], 7)
        self.assertEqual(result.suggested_pins["BME280_SCL"], 7)
        self.assertNotIn(result.suggested_pins["STATUS_LED"], {6, 7})

    def test_multi_file_project_detects_both_conflicts(self) -> None:
        board = load_board("esp32-c3")
        project = parse_cpp(SCENARIOS_DIR / "06_multi_file_project" / "src", board)
        result = validate(project, board)

        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.conflicts), 2)
        self.assertIn("wifi", project.active_resources)


if __name__ == "__main__":
    unittest.main(verbosity=2)
