# MCU-Validator (`mcu-pin-solver`)

## Project Overview

This library automatically checks your ESP32-C3 or ESP32-S3 C++ code **before** PlatformIO compiles or uploads it.
Using the **Microsoft Z3 SMT-Solver**, it prevents common hardware mistakes (for example: using internal SPI-Flash pins, colliding pins, nonexistent GPIOs, or using `ADC2` together with Wi-Fi).

- **Valid pins (`SAT`):** PlatformIO compiles and uploads your code as normal.
- **Pin conflict (`UNSAT`):** PlatformIO stops the build immediately and prints a ready-to-copy prompt telling you (or your AI assistant) which pins to fix.

---

## Quick Start: Use in Any New Project (from GitHub)

You do **not** need to copy any Python or JSON files into your new ESP32 projects.
In any new PlatformIO project on any computer, just add these two settings to your project's `platformio.ini`:

```ini
[env:esp32-s3-devkitc-1]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino

lib_deps =
    https://github.com/DMatheja/mcu-pin-solver.git
extra_scripts = pre:.pio/libdeps/$PIOENV/mcu-pin-solver/pio_hook.py
```

PlatformIO automatically downloads the library into `.pio/libdeps/`, detects your board from `platformio.ini` (`esp32-c3` or `esp32-s3`), installs `z3-solver` if needed on the first run, and checks all files in `src/` before compiling.

*(Note: On the very first build of a brand-new project, if PlatformIO has not downloaded `lib_deps` yet, run Build once or run `pio pkg install` so `.pio/libdeps/` exists.)*

---

## Repository Structure

- `mcu_validator/` — Compact Python package (`parser.py`, `solver.py`, `cli.py`).
- `boards/` — Declarative JSON hardware databases (`esp32-c3.json`, `esp32-s3.json`).
- `pio_hook.py` — Invisible PlatformIO pre-build hook (auto-detects the board and scans `src/`).
- `library.json` — PlatformIO library manifest.
- `pyproject.toml` — Standard Python package setup (`mcu-validate` CLI).
- `validator.py` — Simple CLI entry point.
- `test_sketch.cpp` — Active ESP32-C3 live demo (onboard LED blink, Wi-Fi hotspot, USB feedback).
- `run_tests.py` — Automated test runner for all ESP32-C3 and ESP32-S3 scenarios.
- `scenarios/` — Isolated C++ test sketches (`00`–`03`).

---

## Step 1: Open This Repository in VS Code

1. Open **VS Code**.
2. Click **File → Open Folder...** and select this repository folder.
3. Wait a few seconds until the **PlatformIO** extension finishes loading (you will see the PlatformIO icons in the bottom status bar).
4. Click the **Explorer** icon on the top left (or press `Ctrl + Shift + E`) to inspect `test_sketch.cpp` or `scenarios/`.

---

## Step 2: Build & Upload the Working Demo (`SAT`) to your ESP32-C3

The included `test_sketch.cpp` is a **valid (`SAT`) live test** that blinks the onboard LED (`GPIO 8`), starts a Wi-Fi hotspot, reads `ADC1` (`GPIO 1`), and sends status messages over USB every second.

1. Connect your **ESP32-C3** board to your PC using a USB cable.
2. Click the **Build** checkmark icon (`✓`) in the bottom VS Code status bar (or press `Ctrl + Alt + B`) to compile:
   - First, Z3 checks `test_sketch.cpp` for `esp32-c3-devkitm-1` and prints `RESULT: SAT`.
   - Then PlatformIO compiles the firmware (`[SUCCESS]`).
3. Click the **Upload** right-arrow icon (`→`) in the bottom status bar to flash the firmware onto your ESP32-C3.
4. Click the **Serial Monitor** plug icon (`🔌`) in the bottom status bar (`115200` baud):
   - Every second you will see:
     `[Heartbeat #1] Hotspot: 'ESP32-C3-PinSolver' (Clients: 0) | LED (GPIO 8): AN | ADC1 (GPIO 1): ...`
5. Check the hardware:
   - The onboard LED (`GPIO 8`) blinks every second.
   - On your phone or laptop Wi-Fi list, you will see **`ESP32-C3-PinSolver`** (password: **`12345678`**).

---

## Step 3: Test the Z3 Gatekeeper (`UNSAT` — Block Invalid Pins)

Try creating a hardware conflict on purpose to watch Z3 stop the compiler:

1. Open `test_sketch.cpp`.
2. Change `#define STATUS_LED 8` to `#define STATUS_LED 12` *(SPI-Flash pin)* **or** change `const int SOIL_SENSOR = 1;` to `5` *(ADC2 pin, which conflicts with Wi-Fi on ESP32-C3)*.
3. Save (`Ctrl + S`) and click **Build (`✓`)** or **Upload (`→`)**.
4. PlatformIO stops immediately before compiling and prints the Z3 repair prompt.
5. Change the pin back to `8` (or `1`) and save again so your sketch stays valid.

---

## Step 4: Run All Automated Test Scenarios

You can verify all ESP32-C3 and ESP32-S3 test cases at once in the VS Code terminal:

```powershell
python run_tests.py
```

To test a single file manually with a specific board:

```powershell
python validator.py scenarios/03_duplicate_and_invalid_pin.cpp esp32-c3
python validator.py scenarios/00_flash_and_wifi_conflict.cpp esp32-s3
```

---

## Troubleshooting (Serial Monitor is Empty)

`platformio.ini` currently includes these flags for ESP32-C3 boards with a direct USB port on the chip:

```ini
build_flags =
    -DARDUINO_USB_MODE=1
    -DARDUINO_USB_CDC_ON_BOOT=1
```

If your ESP32-C3 board uses a **separate USB-to-UART chip** (such as CP2102 or CH340) and the Serial Monitor stays blank after uploading:
1. Open `platformio.ini` and remove (or comment out with `;`) those `build_flags` lines.
2. Save and click **Upload (`→`)** again.
