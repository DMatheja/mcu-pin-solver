# mcu-pin-solver

A data-driven **C++ AST + Z3 SMT hardware pin validator** (LLM-Modulo) for PlatformIO and standalone CLI workflows.
It parses C/C++ code using a **Tree-Sitter Abstract Syntax Tree (AST)**, verifies pin assignments against declarative JSON rules before compiling, stops invalid builds (`UNSAT`), and computes minimal-invasive pin fixes via Z3 MaxSMT.
Because both the AST parser and Z3 solver contain zero chip-specific hardcoding, it supports **any microcontroller** by adding a JSON file to `boards/`.

> **Tested Hardware:** Currently, only **ESP32-C3** and **ESP32-S3** are included and verified.

---

## Universal `platformio.ini` Setup (Any Microcontroller)

1. Create or open a PlatformIO project in VS Code.
2. Add `lib_deps` and `extra_scripts` to your `platformio.ini`:

```ini
[env:my_mcu]
platform = <your_platform>
board = <your_board>
framework = <your_framework>

lib_deps =
    https://github.com/DMatheja/mcu-pin-solver.git
extra_scripts = pre:.pio/libdeps/$PIOENV/mcu-pin-solver/pio_hook.py
```

3. On a brand-new project, run `pio pkg install` once in the VS Code terminal so PlatformIO downloads the library into `.pio/libdeps/`, then click **Build (`✓`)**. Dependencies (`z3-solver`, `tree-sitter`, `tree-sitter-cpp`) install automatically on first run.

---

## Supported & Tested Boards

| MCU | Rule File | Verified Hardware Rules | `platformio.ini` Configuration & Guide |
| :--- | :--- | :--- | :--- |
| **ESP32-C3** | `boards/esp32-c3.json` | • **Reserved Flash:** GPIO `12–17`<br>• **Strapping:** GPIO `2, 8, 9`<br>• **USB-Serial:** blocks GPIO `18, 19`<br>• **Wi-Fi active:** blocks `ADC2` (GPIO `5`), keeps `ADC1` (GPIO `0–4`)<br>• **Shared Bus:** `i2c`, `spi` | **Config:**<pre>[env:esp32-c3]<br>platform = espressif32<br>board = esp32-c3-devkitm-1<br>framework = arduino<br>monitor_speed = 115200<br>build_flags =<br>    -DARDUINO_USB_MODE=1<br>    -DARDUINO_USB_CDC_ON_BOOT=1<br>lib_deps =<br>    https://github.com/DMatheja/mcu-pin-solver.git<br>extra_scripts = pre:.pio/libdeps/$PIOENV/mcu-pin-solver/pio_hook.py</pre>**Guide:** Run `pio pkg install` once, then click **Build (`✓`)** or **Upload (`→`)**. *(Remove `build_flags` if your board uses an external CP2102/CH340 UART chip.)* |
| **ESP32-S3** | `boards/esp32-s3.json` | • **Reserved Flash/PSRAM:** GPIO `26–37` *(GPIO `22–25` nonexistent)*<br>• **Strapping:** GPIO `0, 3, 45, 46`<br>• **USB-Serial:** blocks GPIO `19, 20`<br>• **Wi-Fi active:** blocks `ADC2` (GPIO `11–20`), keeps `ADC1` (GPIO `1–10`)<br>• **Shared Bus:** `i2c`, `spi` | **Config:**<pre>[env:esp32-s3]<br>platform = espressif32<br>board = esp32-s3-devkitc-1<br>framework = arduino<br>monitor_speed = 115200<br>build_flags =<br>    -DARDUINO_USB_MODE=1<br>    -DARDUINO_USB_CDC_ON_BOOT=1<br>lib_deps =<br>    https://github.com/DMatheja/mcu-pin-solver.git<br>extra_scripts = pre:.pio/libdeps/$PIOENV/mcu-pin-solver/pio_hook.py</pre>**Guide:** Run `pio pkg install` once, then click **Build (`✓`)** or **Upload (`→`)**. *(For UART-bridge USB ports on DevKitC-1, remove `build_flags` or connect to the native USB port.)* |

---

## Standalone CLI & Tests

Works on single files or whole project directories (automatically aggregates sibling `include/` headers + `src/` files):

```bash
pip install z3-solver tree-sitter tree-sitter-cpp
python -m mcu_validator.cli src esp32-c3
python tests/run_tests.py
```

---

## Contributing, AI Handoff & Registry Publishing

- **Developer & AI Agent Guide:** See [AGENTS.md](AGENTS.md) for the full architecture overview, strict AST/Z3 invariants, extension instructions, and verification checklist.
- **PlatformIO Registry Packaging:** [library.json](library.json) includes an `export` manifest verified via `pio pkg pack`. Maintainers can publish directly with:

```bash
pio account login
pio pkg publish
```

---

## Add Any Microcontroller (LLM Prompt Template)

Place `<board-prefix>.json` inside `boards/` (no Python changes required). Copy this prompt into any LLM to generate the JSON from a datasheet:

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
