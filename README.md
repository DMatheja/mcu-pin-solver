# mcu-pin-solver

A data-driven **Z3 SMT hardware pin validator** (LLM-Modulo) for C/C++ microcontroller code.
It verifies pin assignments against declarative JSON hardware rules before compiling, stops invalid builds (`UNSAT`), and computes minimal-invasive pin fixes.
Because the Z3 solver contains zero chip-specific hardcoding, it works with **any microcontroller** (ESP32, STM32, RP2040, AVR, nRF52, etc.) simply by adding a JSON file to `boards/`.

---

## Use in Any PlatformIO Project

Add these lines to your project's `platformio.ini` (replace `board` with your target):

```ini
[env:my_board]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino

lib_deps =
    https://github.com/DMatheja/mcu-pin-solver.git
extra_scripts = pre:.pio/libdeps/$PIOENV/mcu-pin-solver/pio_hook.py
```

*First build in a new project:* run `pio pkg install` once so PlatformIO downloads the library into `.pio/libdeps/`.

---

## Standalone CLI & Tests

```bash
pip install z3-solver
python -m mcu_validator.cli src/main.cpp esp32-c3
python tests/run_tests.py
```

---

## Add Any Microcontroller (LLM Prompt Template)

To support a new MCU (e.g., `rp2040`, `stm32f103`, `esp32-p4`, `atmega328p`), place `<board-prefix>.json` inside `boards/`. No Python code changes are required.

Copy this prompt into any LLM to generate a matching board JSON from a datasheet:

```text
Create a hardware constraint JSON file for the <INSERT MICROCONTROLLER NAME, e.g. Raspberry Pi RP2040> compatible with mcu-pin-solver.

Follow this exact JSON schema and rules:
1. Top-level keys: "mcu", "description", "pins", "capability_aliases", "conflict_rules".
2. "pins": Object keyed by pin number as string (only include physically exposed GPIOs/pins). Each pin object must contain:
   - "capabilities": list from ["gpio", "adc", "adc1", "adc2", "pwm", "i2c", "spi", "uart", "usb", "jtag"]
   - "strapping": boolean (true if boot/strapping pin)
   - "reserved": boolean (true if unusable internal flash/PSRAM/system pin; set "capabilities": [])
   - "note": optional short English reason
3. "capability_aliases": map generic names to hardware banks if applicable (e.g. {"adc": ["adc1", "adc2"]}).
4. "conflict_rules": array of rules triggered by active modules ("wifi", "usb_serial"):
   - {"id": "RULE_ID", "when_resource_active": "<module>", "forbidden_capability": "<cap>" OR "forbidden_pins": [..], "reason": "<English explanation>"}

Return only valid JSON with no markdown commentary.
```
