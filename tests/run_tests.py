import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"

# Test cases: (file_path, board_id, expect_sat, description)
TEST_CASES = [
    (ROOT_DIR / "src" / "main.cpp", "esp32-c3", True, "Live hardware sketch (LED blink, Wi-Fi hotspot & USB-Serial)"),
    (SCENARIOS_DIR / "00_flash_and_wifi_conflict.cpp", "esp32-c3", False, "ESP32-C3: SPI flash (GPIO 12) & Wi-Fi/ADC2 (GPIO 5)"),
    (SCENARIOS_DIR / "00_flash_and_wifi_conflict.cpp", "esp32-s3", True, "ESP32-S3: Same sketch is valid (GPIO 12 normal GPIO, GPIO 5 is ADC1)"),
    (SCENARIOS_DIR / "01_valid_sketch.cpp", "esp32-c3", True, "Valid ESP32-C3 sketch (positive test)"),
    (SCENARIOS_DIR / "02_usb_serial_conflict.cpp", "esp32-c3", False, "ESP32-C3: USB-Serial conflict on GPIO 18 & 19"),
    (SCENARIOS_DIR / "03_duplicate_and_invalid_pin.cpp", "esp32-c3", False, "ESP32-C3: Duplicate pin, nonexistent GPIO 32 & no ADC on GPIO 6"),
]

run_env = os.environ.copy()
run_env["PYTHONPATH"] = str(ROOT_DIR) + os.pathsep + run_env.get("PYTHONPATH", "")

print("=" * 78)
print(" AUTOMATED TEST RUN: MCU-VALIDATOR (ESP32-C3 & ESP32-S3)")
print("=" * 78)

passed = 0
for cpp_path, board_id, expect_sat, description in TEST_CASES:
    result = subprocess.run(
        [sys.executable, "-m", "mcu_validator.cli", str(cpp_path), board_id],
        cwd=ROOT_DIR,
        env=run_env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    actual_sat = (result.returncode == 0)
    ok = (actual_sat == expect_sat)
    if ok:
        passed += 1

    status_label = "PASS" if ok else "FAIL"
    expected_str = "SAT  " if expect_sat else "UNSAT"
    actual_str = "SAT  " if actual_sat else "UNSAT"

    print(f"[{status_label}] {cpp_path.name:<34} ({board_id}) | Expected: {expected_str} | Actual: {actual_str}")
    print(f"       Scenario: {description}")
    if not ok:
        print("       Output:\n" + result.stdout + "\n" + result.stderr)
    print("-" * 78)

print(f"\nSummary: {passed}/{len(TEST_CASES)} tests passed!")
sys.exit(0 if passed == len(TEST_CASES) else 1)
