# mcu-pin-solver

A data-driven **C++ AST + Z3 SMT hardware pin validator** (LLM-Modulo) for PlatformIO and standalone CLI workflows.

Before the C++ compiler runs, `mcu-pin-solver` parses your C/C++ project into a **Tree-Sitter Abstract Syntax Tree (AST)**, checks every pin assignment against declarative JSON hardware rules, stops invalid builds (`UNSAT`), and computes a minimal-invasive pin reassignment using **Z3 MaxSMT**.

Because all chip-specific hardware knowledge lives in `mcu_validator/boards/*.json`, adding a new microcontroller requires zero Python changes.

> **Tested Hardware:** Includes verified profiles for **ESP32-C3** and **ESP32-S3**.

---

## How It Works (Beginner's Reading Guide)

If you are new to this repository, read the 4 modules in `mcu_validator/` in this exact order — each file starts with its top-level function so you can read top-down:

```text
  C++ project (src/ + include/)          mcu_validator/boards/<mcu>.json
               │                                        │
               ▼                                        ▼
       2. parser.py                             1. board.py
   (Tree-Sitter C++ AST)                    (Validated BoardSpec)
               │                                        │
               └──────────────────┬─────────────────────┘
                                  ▼
                            3. solver.py
                   (Rule checks + Z3 MaxSMT repair)
                                  │
                                  ▼
                            4. cli.py  ◄──  pio_hook.py (PlatformIO pre-build)
                   (Report + LLM-Modulo repair prompt)
```

1. **`mcu_validator/board.py`** — Loads and validates a chip's JSON rulebook (`BoardSpec`, `PinSpec`, `ConflictRule`).
2. **`mcu_validator/parser.py`** — Parses C/C++ files with `tree-sitter-cpp` to extract pin constants, direct numeric pin calls, required capabilities (`gpio`, `adc`, `pwm`, `i2c`, `spi`, `uart`), shared bus roles (`Wire:sda`, `SPI:mosi`, ...), and active peripherals (`wifi`, `usb_serial`).
3. **`mcu_validator/solver.py`** — Checks all hard hardware rules; when conflicts exist, runs Z3 `Optimize` (MaxSMT) with three prioritized soft goals:
   - Keep already-valid original pins unchanged (weight `1000`)
   - Avoid boot/strapping pins (weight `20`)
   - Preserve scarce ADC/USB pins when a plain GPIO is enough (weight `5`)
4. **`mcu_validator/cli.py`** — CLI entrypoint (`mcu-validate` / `python -m mcu_validator.cli`) that prints the validation summary and copy-paste LLM-Modulo repair prompt.

`pio_hook.py` connects this CLI to PlatformIO as a pre-build SCons hook.

---

## PlatformIO Setup

Add `lib_deps` and `extra_scripts` to your project's `platformio.ini`:

```ini
[env:esp32-c3]
platform = espressif32
board = esp32-c3-devkitm-1
framework = arduino
monitor_speed = 115200
build_flags =
    -DARDUINO_USB_MODE=1
    -DARDUINO_USB_CDC_ON_BOOT=1
lib_deps =
    dmatheja/mcu-pin-solver@^0.2.0
extra_scripts = pre:.pio/libdeps/$PIOENV/mcu-pin-solver/pio_hook.py
```

*(For ESP32-S3 use `board = esp32-s3-devkitc-1`. Remove `build_flags` if your board uses an external USB-UART bridge chip.)*

Run `pio pkg install` once on a fresh project, then click **Build (`✓`)**. Python dependencies (`z3-solver`, `tree-sitter`, `tree-sitter-cpp`) install automatically on first run.

---

## Supported & Tested Boards

| MCU | Rule File | Key Hardware Rules |
| :--- | :--- | :--- |
| **ESP32-C3** | `mcu_validator/boards/esp32-c3.json` | • **Reserved Flash:** GPIO `11–17`<br>• **Strapping:** GPIO `2, 8, 9`<br>• **USB-Serial active:** blocks GPIO `18, 19`<br>• **Wi-Fi active:** blocks `ADC2` (GPIO `5`), keeps `ADC1` (GPIO `0–4`)<br>• **Shared Bus:** `i2c`, `spi` |
| **ESP32-S3** | `mcu_validator/boards/esp32-s3.json` | • **Reserved Flash/PSRAM:** GPIO `26–37` *(GPIO `22–25` nonexistent)*<br>• **Strapping:** GPIO `0, 3, 45, 46`<br>• **USB-Serial active:** blocks GPIO `19, 20`<br>• **Wi-Fi active:** blocks `ADC2` (GPIO `11–20`), keeps `ADC1` (GPIO `1–10`)<br>• **Shared Bus:** `i2c`, `spi` |

---

## Standalone CLI & Tests

Install locally with `pip` (bundles all board profiles automatically):

```bash
pip install .
mcu-validate --list-boards
mcu-validate src esp32-c3
```

Useful options:

```bash
mcu-validate path/to/sketch.cpp esp32-s3           # Validate a single file
mcu-validate src ./my_custom_board.json            # Use a custom board JSON file directly
mcu-validate src esp32-c3 --boards-dir ./boards    # Load boards from a custom folder
mcu-validate firmware esp32-c3 --include-dir inc   # Include an extra header directory
```

Run the test suite (organized by module in `tests/test_*.py`):

```bash
python -m unittest discover -s tests -v
# or:
python tests/run_tests.py
```

---

## Adding a New Microcontroller

Drop a `<board-prefix>.json` file into `mcu_validator/boards/` (or pass its path directly on the CLI). Every loaded board JSON is schema-validated at load time so typos or wrong types fail with clear errors. You can use this LLM prompt with a datasheet:

```text
Create a hardware constraint JSON file for the <INSERT MICROCONTROLLER NAME, e.g. Raspberry Pi RP2040> compatible with mcu-pin-solver.

Follow this exact JSON schema and rules:
1. Top-level keys: "mcu", "description", "pins", "capability_aliases", "shared_capabilities", "resource_triggers", "conflict_rules".
2. "pins": Object keyed by pin number as string (only include physically exposed GPIOs/pins). Each pin object must contain:
   - "capabilities": list from ["gpio", "adc", "adc1", "adc2", "pwm", "i2c", "spi", "uart", "usb", "jtag"]
   - "strapping": boolean (true if boot/strapping pin)
   - "reserved": boolean (true if unusable internal flash/PSRAM/system pin; set "capabilities": [])
   - "note": optional short English reason
3. "capability_aliases": map generic names to hardware banks if applicable (e.g. {"adc": ["adc1", "adc2"]}).
4. "shared_capabilities": list of bus capabilities that multiple peripherals may safely share on the same pin (e.g. ["i2c", "spi"]).
5. "resource_triggers": map active peripheral names to C/C++ AST call targets that activate them (e.g. {"wifi": ["WiFi.begin", "WiFi.softAP"], "usb_serial": ["Serial.begin"]}).
6. "conflict_rules": array of rules triggered by keys in "resource_triggers":
   - {"id": "RULE_ID", "when_resource_active": "<module>", "forbidden_capability": "<cap>" OR "forbidden_pins": [..], "reason": "<English explanation>"}

Return only valid JSON with no markdown commentary.
```

---

## Publishing (Maintainers)

```bash
pio pkg pack
pio account login
pio pkg publish
```
