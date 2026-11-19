"""Unit tests for the Tree-Sitter C++ AST parser."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcu_validator import load_board, parse_cpp, validate  # noqa: E402


class ParserTests(unittest.TestCase):
    """Tests for AST extraction, filtering, naming heuristics, and edge cases."""

    def _parse_snippet(self, code: str, board_id: str = "esp32-c3"):
        with tempfile.TemporaryDirectory() as tmp:
            sketch = Path(tmp) / "sketch.cpp"
            sketch.write_text(code, encoding="utf-8")
            board = load_board(board_id)
            project = parse_cpp(sketch, board)
            result = validate(project, board)
            return board, project, result

    def test_ignores_non_pin_constants_and_local_variables(self) -> None:
        code = """
        #define BAUD_RATE 115200
        #define DELAY_MS 1000
        #define LED_COUNT 30
        #define I2C_ADDR 66
        #define RX_BUF 128
        #define SDA_TIMEOUT 50
        const int MAX_RETRIES = 3;
        constexpr uint8_t STATUS_LED = 3;

        void setup() {
            int retries = 3;
            for (int i = 0; i < 10; i++) {}
            Serial.begin(BAUD_RATE);
            Wire.begin(I2C_ADDR);
            pinMode(STATUS_LED, OUTPUT);
        }
        """
        _, project, result = self._parse_snippet(code)
        self.assertEqual([r.name for r in project.requests], ["STATUS_LED"])
        self.assertTrue(result.is_valid, msg=f"Unexpected conflicts: {result.conflicts}")

    def test_parses_parenthesized_macros_and_unsigned_suffixes(self) -> None:
        code = """
        #define STATUS_LED (12)
        const uint8_t RELAY_PIN = 4u;
        void setup() {
            pinMode(STATUS_LED, OUTPUT);
            pinMode(RELAY_PIN, OUTPUT);
        }
        """
        _, project, result = self._parse_snippet(code)
        pins = {r.name: r.pin for r in project.requests}
        self.assertEqual(pins, {"STATUS_LED": 12, "RELAY_PIN": 4})
        self.assertFalse(result.is_valid)

    def test_handles_non_utf8_comments_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sketch = Path(tmp) / "latin1.cpp"
            # German umlauts encoded in Windows-1252 / Latin-1 (not valid UTF-8).
            raw_bytes = (
                b"// Sensor f\xfcr Gew\xe4chshaus\n"
                b"#define STATUS_LED 3\n"
                b"void setup() { pinMode(STATUS_LED, OUTPUT); }\n"
            )
            sketch.write_bytes(raw_bytes)
            board = load_board("esp32-c3")
            project = parse_cpp(sketch, board)
            self.assertEqual([r.name for r in project.requests], ["STATUS_LED"])

    def test_detects_direct_numeric_pin_literals(self) -> None:
        code = """
        void setup() {
            WiFi.begin("ssid", "pass");
            pinMode(12, OUTPUT);
        }
        void loop() {
            analogRead(5);
        }
        """
        _, project, result = self._parse_snippet(code)
        self.assertFalse(result.is_valid)
        self.assertEqual({r.pin for r in project.requests}, {12, 5})
        self.assertEqual(len(result.conflicts), 2)

    def test_literal_call_on_named_pin_merges_missing_capability(self) -> None:
        code = """
        const int STATUS_LED = 6;
        void setup() {
            pinMode(STATUS_LED, OUTPUT);
            analogRead(6);  // GPIO 6 does not support ADC on ESP32-C3!
        }
        """
        _, project, result = self._parse_snippet(code)
        self.assertEqual(len(project.requests), 1)
        self.assertEqual(project.requests[0].capabilities, frozenset({"gpio", "adc"}))
        self.assertFalse(result.is_valid)
        self.assertTrue(any("adc" in c for c in result.conflicts))

    def test_user_symbol_named_gpio_12_does_not_collide_with_literal_12(self) -> None:
        code = """
        const int GPIO_12 = 3;
        void setup() {
            pinMode(GPIO_12, OUTPUT);
            pinMode(12, OUTPUT);  // Reserved SPI flash pin
        }
        """
        _, project, result = self._parse_snippet(code)
        self.assertEqual(len(project.requests), 2)
        self.assertEqual(len({r.name for r in project.requests}), 2)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.repair_possible)

    def test_three_way_redefinition_in_same_file_keeps_all_keys_unique(self) -> None:
        code = """
        #ifdef BOARD_A
        #define STATUS_LED 2
        #elif defined(BOARD_B)
        #define STATUS_LED 3
        #else
        #define STATUS_LED 12
        #endif
        void setup() { pinMode(STATUS_LED, OUTPUT); }
        """
        _, project, result = self._parse_snippet(code)
        self.assertEqual(len(project.requests), 3)
        self.assertEqual(len({r.name for r in project.requests}), 3)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.repair_possible)

    def test_name_inference_recognizes_bus_pins_with_pin_suffix(self) -> None:
        code = """
        #define OLED_SDA_PIN 6
        #define BME280_SDA_PIN 6
        #define OLED_SCL_PIN 7
        #define BME280_SCL_PIN 7
        #define SPI_MOSI_PIN 4
        #define UART_RX_PIN 20
        #define PIN_STATUS_LED 3
        const int oledSdaPin = 6;
        void setup() {}
        """
        _, project, result = self._parse_snippet(code)
        by_name = {r.name: r for r in project.requests}
        self.assertEqual(by_name["OLED_SDA_PIN"].capabilities, frozenset({"i2c"}))
        self.assertEqual(by_name["OLED_SDA_PIN"].bus_group, "Wire:sda")
        self.assertEqual(by_name["BME280_SDA_PIN"].bus_group, "Wire:sda")
        self.assertEqual(by_name["oledSdaPin"].bus_group, "Wire:sda")
        self.assertEqual(by_name["OLED_SCL_PIN"].bus_group, "Wire:scl")
        self.assertEqual(by_name["SPI_MOSI_PIN"].capabilities, frozenset({"spi"}))
        self.assertEqual(by_name["SPI_MOSI_PIN"].bus_group, "SPI:mosi")
        self.assertEqual(by_name["UART_RX_PIN"].capabilities, frozenset({"uart"}))
        self.assertEqual(by_name["PIN_STATUS_LED"].capabilities, frozenset({"gpio"}))
        self.assertTrue(result.is_valid, msg=f"Unexpected conflicts: {result.conflicts}")

    def test_serial1_only_checks_rx_tx_pins_not_baud_rate(self) -> None:
        code = """
        #define UART_BAUD 115200
        const int RX_PIN = 18;
        const int TX_PIN = 21;
        void setup() {
            Serial.begin(115200);
            Serial1.begin(UART_BAUD, SERIAL_8N1, RX_PIN, TX_PIN);
        }
        """
        _, project, result = self._parse_snippet(code)
        self.assertEqual({r.name for r in project.requests}, {"RX_PIN", "TX_PIN"})
        self.assertFalse(result.is_valid)

    def test_cross_file_conflicting_redefinition_preserves_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.cpp").write_text(
                "#define SENSOR 4\nvoid a() { pinMode(SENSOR, OUTPUT); }\n",
                encoding="utf-8",
            )
            (root / "b.cpp").write_text(
                "#define SENSOR 6\nvoid b() { analogRead(SENSOR); }\n",
                encoding="utf-8",
            )
            board = load_board("esp32-c3")
            project = parse_cpp(root, board)
            result = validate(project, board)

            self.assertEqual(len(project.requests), 2)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("adc" in c for c in result.conflicts))

    def test_custom_include_dirs_and_source_locations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            headers = root / "custom_headers"
            firmware = root / "firmware"
            headers.mkdir()
            firmware.mkdir()

            (headers / "board_pins.h").write_text("#define STATUS_LED 12\n", encoding="utf-8")
            (firmware / "app.cpp").write_text(
                '#include "board_pins.h"\nvoid setup() { pinMode(STATUS_LED, OUTPUT); }\n',
                encoding="utf-8",
            )

            board = load_board("esp32-c3")
            project = parse_cpp(firmware, board, include_dirs=[headers])
            self.assertEqual(len(project.requests), 1)
            self.assertEqual(project.requests[0].location, "board_pins.h:1")
            result = validate(project, board)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("board_pins.h:1" in c for c in result.conflicts))


if __name__ == "__main__":
    unittest.main(verbosity=2)
