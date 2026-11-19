"""Unit tests for board JSON loading, matching, and schema validation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcu_validator.board import BOARDS_DIR, BoardSpec, list_boards, load_board  # noqa: E402


class BoardProfileTests(unittest.TestCase):
    """Tests for shipped board profiles and `load_board()` resolution."""

    def test_all_shipped_boards_are_valid_and_consistent(self) -> None:
        boards = list_boards(BOARDS_DIR)
        self.assertIn("esp32-c3", boards)
        self.assertIn("esp32-s3", boards)

        for board_name in boards:
            with self.subTest(board=board_name):
                spec = load_board(board_name)
                self.assertTrue(spec.pins, "Board profile should declare at least one pin.")
                for pin_num, pin_spec in spec.pins.items():
                    if pin_spec.reserved:
                        self.assertEqual(
                            pin_spec.capabilities,
                            frozenset(),
                            msg=(
                                f"{board_name} reserved GPIO {pin_num} "
                                "should have empty capabilities."
                            ),
                        )
                for rule in spec.conflict_rules:
                    self.assertIn(rule.when_resource_active, spec.resource_triggers)
                    for forbidden_pin in rule.forbidden_pins:
                        self.assertIn(forbidden_pin, spec.pins)

    def test_longest_board_prefix_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            boards_dir = Path(tmp)
            (boards_dir / "esp32.json").write_text(
                json.dumps({"mcu": "GENERIC", "pins": {}}), encoding="utf-8"
            )
            (boards_dir / "esp32-c3.json").write_text(
                json.dumps({"mcu": "ESP32-C3", "pins": {}}), encoding="utf-8"
            )

            loaded = load_board("esp32-c3-devkitm-1", boards_dir=boards_dir)
            self.assertEqual(loaded.mcu, "ESP32-C3")

    def test_normalizes_underscores_in_both_board_id_and_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            boards_dir = Path(tmp)
            (boards_dir / "esp32_c6.json").write_text(
                json.dumps({"mcu": "ESP32-C6", "pins": {}}), encoding="utf-8"
            )

            loaded = load_board("ESP32-C6-DevKitC-1", boards_dir=boards_dir)
            self.assertEqual(loaded.mcu, "ESP32-C6")

    def test_loads_direct_json_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            custom_json = Path(tmp) / "custom_chip.json"
            custom_json.write_text(
                json.dumps({"mcu": "CUSTOM-MCU", "pins": {"0": {"capabilities": ["gpio"]}}}),
                encoding="utf-8",
            )
            loaded = load_board(str(custom_json))
            self.assertEqual(loaded.mcu, "CUSTOM-MCU")
            self.assertIn(0, loaded.pins)

    def test_unknown_board_raises_file_not_found(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_board("unknown-mcu-999")


class BoardSchemaValidationTests(unittest.TestCase):
    """Ensure malformed or LLM-mistyped board JSON files fail loudly with clear errors."""

    def test_rejects_string_capabilities_instead_of_list(self) -> None:
        raw = {"mcu": "TEST", "pins": {"0": {"capabilities": "gpio"}}}
        with self.assertRaisesRegex(ValueError, "list of strings"):
            BoardSpec.from_dict(raw)

    def test_rejects_string_entries_in_forbidden_pins(self) -> None:
        raw = {
            "mcu": "TEST",
            "pins": {"18": {"capabilities": ["gpio"]}},
            "resource_triggers": {"usb": ["Serial.begin"]},
            "conflict_rules": [
                {"id": "R1", "when_resource_active": "usb", "forbidden_pins": ["18"]}
            ],
        }
        with self.assertRaisesRegex(ValueError, "non-negative integers"):
            BoardSpec.from_dict(raw)

    def test_rejects_bool_entries_in_forbidden_pins(self) -> None:
        raw = {
            "mcu": "TEST",
            "pins": {"1": {"capabilities": ["gpio"]}},
            "resource_triggers": {"usb": ["Serial.begin"]},
            "conflict_rules": [
                {"id": "R1", "when_resource_active": "usb", "forbidden_pins": [True]}
            ],
        }
        with self.assertRaisesRegex(ValueError, "non-negative integers"):
            BoardSpec.from_dict(raw)

    def test_rejects_rule_referencing_unknown_resource(self) -> None:
        raw = {
            "mcu": "TEST",
            "pins": {"5": {"capabilities": ["adc2"]}},
            "resource_triggers": {"wifi": ["WiFi.begin"]},
            "conflict_rules": [
                {"id": "R1", "when_resource_active": "wi_fi", "forbidden_capability": "adc2"}
            ],
        }
        with self.assertRaisesRegex(ValueError, "unknown resource"):
            BoardSpec.from_dict(raw)

    def test_rejects_rule_without_forbidden_target(self) -> None:
        raw = {
            "mcu": "TEST",
            "pins": {},
            "resource_triggers": {"wifi": ["WiFi.begin"]},
            "conflict_rules": [{"id": "EMPTY_RULE", "when_resource_active": "wifi"}],
        }
        with self.assertRaisesRegex(ValueError, "forbidden_capability"):
            BoardSpec.from_dict(raw)

    def test_rejects_non_integer_pin_key(self) -> None:
        raw = {"mcu": "TEST", "pins": {"GPIO5": {"capabilities": ["gpio"]}}}
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            BoardSpec.from_dict(raw)

    def test_invalid_json_syntax_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_json = Path(tmp) / "broken.json"
            bad_json.write_text("{not valid json", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid JSON"):
                load_board(str(bad_json))


if __name__ == "__main__":
    unittest.main(verbosity=2)
