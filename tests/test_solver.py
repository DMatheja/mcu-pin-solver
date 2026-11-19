"""Unit tests for the hardware rule checker and Z3 MaxSMT solver."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcu_validator import ParsedProject, PinRequest, load_board, parse_cpp, validate  # noqa: E402
from mcu_validator.cli import format_report  # noqa: E402


class SolverTests(unittest.TestCase):
    """Tests for conflict detection, shared bus coupling, and Z3 repair priorities."""

    def _check_snippet(self, code: str, board_id: str = "esp32-c3"):
        with tempfile.TemporaryDirectory() as tmp:
            sketch = Path(tmp) / "sketch.cpp"
            sketch.write_text(code, encoding="utf-8")
            board = load_board(board_id)
            project = parse_cpp(sketch, board)
            result = validate(project, board)
            return board, project, result

    def test_rejects_i2c_sda_and_scl_on_same_pin(self) -> None:
        code = """
        #define OLED_SDA 6
        #define OLED_SCL 6
        void setup() {
            Wire.begin(OLED_SDA, OLED_SCL);
        }
        """
        _, _, result = self._check_snippet(code)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.repair_possible)
        self.assertNotEqual(result.suggested_pins["OLED_SDA"], result.suggested_pins["OLED_SCL"])

    def test_rejects_literal_wire_begin_with_same_sda_and_scl(self) -> None:
        code = """
        void setup() {
            Wire.begin(6, 6);
        }
        """
        _, project, result = self._check_snippet(code)
        self.assertEqual(len(project.requests), 2)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.repair_possible)
        pins = list(result.suggested_pins.values())
        self.assertNotEqual(pins[0], pins[1])

    def test_rejects_wire_and_wire1_on_same_pins(self) -> None:
        code = """
        #define SDA_A 6
        #define SCL_A 7
        #define SDA_B 6
        #define SCL_B 7
        void setup() {
            Wire.begin(SDA_A, SCL_A);
            Wire1.begin(SDA_B, SCL_B);
        }
        """
        _, _, result = self._check_snippet(code)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.repair_possible)
        self.assertEqual(len(set(result.suggested_pins.values())), 4)

    def test_spi_shares_clock_data_but_forbids_shared_chip_select_or_sck_mosi_overlap(self) -> None:
        code_cs_conflict = """
        #define SPI_SCK 6
        #define SPI_MISO 7
        #define SPI_MOSI 4
        #define SD_CS 10
        #define TFT_CS 10
        void setup() {
            SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI, SD_CS);
            pinMode(TFT_CS, OUTPUT);
        }
        """
        _, _, result = self._check_snippet(code_cs_conflict)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("TFT_CS" in c and "SD_CS" in c for c in result.conflicts))

        code_sck_mosi_conflict = """
        #define SPI_SCK 6
        #define SPI_MISO 7
        #define SPI_MOSI 6
        void setup() {
            SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
        }
        """
        _, _, result2 = self._check_snippet(code_sck_mosi_conflict)
        self.assertFalse(result2.is_valid)
        self.assertNotEqual(result2.suggested_pins["SPI_SCK"], result2.suggested_pins["SPI_MOSI"])

    def test_prefers_plain_gpio_over_scarce_adc_pins_when_reassigning_led(self) -> None:
        code = """
        #define STATUS_LED 12
        void setup() {
            Serial.begin(115200);
            pinMode(STATUS_LED, OUTPUT);
        }
        """
        board, _, result = self._check_snippet(code)
        self.assertFalse(result.is_valid)
        chosen = result.suggested_pins["STATUS_LED"]
        pin_spec = board.pins[chosen]
        self.assertFalse(pin_spec.strapping)
        self.assertFalse(pin_spec.capabilities & {"adc1", "adc2", "usb"})

    def test_unrepairable_sketch_reports_cleanly_without_gpio_none(self) -> None:
        # ESP32-C3 only has 5 ADC1 pins (GPIO 0..4), so 6 ADC pins with Wi-Fi cannot fit.
        code = """
        const int S0 = 0;
        const int S1 = 1;
        const int S2 = 2;
        const int S3 = 3;
        const int S4 = 4;
        const int S5 = 5;
        void setup() { WiFi.begin("a", "b"); }
        void loop() {
            analogRead(S0); analogRead(S1); analogRead(S2);
            analogRead(S3); analogRead(S4); analogRead(S5);
        }
        """
        board, project, result = self._check_snippet(code)
        self.assertFalse(result.is_valid)
        self.assertFalse(result.repair_possible)
        report = format_report("sketch.cpp", board, project, result)
        self.assertNotIn("GPIO None", report)
        self.assertIn("No valid pin assignment exists", report)

    def test_empty_project_is_valid(self) -> None:
        board = load_board("esp32-c3")
        result = validate(ParsedProject(requests=(), active_resources=()), board)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.suggested_pins, {})

    def test_duplicate_request_names_raise_value_error(self) -> None:
        board = load_board("esp32-c3")
        project = ParsedProject(
            requests=(
                PinRequest("LED", 3, frozenset({"gpio"})),
                PinRequest("LED", 4, frozenset({"gpio"})),
            ),
            active_resources=(),
        )
        with self.assertRaisesRegex(ValueError, "Duplicate PinRequest name"):
            validate(project, board)


if __name__ == "__main__":
    unittest.main(verbosity=2)
