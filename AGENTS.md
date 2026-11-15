# AGENTS.md — Developer & AI Agent Handoff Guide

This document describes the architecture, strict invariants, extension workflows, and verification commands for **mcu-pin-solver**, enabling human developers and AI coding agents to extend the project safely without prior chat context.

---

## 1. Repository Layout & Data Flow

```text
pio_hook.py                  # PlatformIO SCons pre-build hook (auto-deps + calls CLI on $PROJECT_SRC_DIR)
mcu_validator/
  __init__.py                # Exports parse_cpp_file, load_board_data, validate_with_z3
  cli.py                     # Loads board JSON, invokes parser + solver, prints SAT/UNSAT report & prompt
  parser.py                  # Tree-Sitter C++ AST analyzer (single file or multi-file src/ + include/)
  solver.py                  # Rule validation + Z3 Optimize (MaxSMT) minimal-invasive repair solver
boards/
  esp32-c3.json              # Declarative hardware rulebook for ESP32-C3 variants
  esp32-s3.json              # Declarative hardware rulebook for ESP32-S3 variants
tests/
  run_tests.py               # Automated test runner (executes mcu_validator.cli across all scenarios)
  scenarios/                 # Positive, negative, shared-bus, AST-comment, and multi-file test projects
library.json                 # PlatformIO package manifest (extraScript, srcFilter, export whitelist)
pyproject.toml               # Python package configuration & runtime dependencies
.github/workflows/ci.yml     # GitHub Actions CI running python tests/run_tests.py on Ubuntu (Python 3.11)
src/main.cpp                 # Standalone ESP32-C3 hardware demo sketch for local `pio run` testing
```

**Execution Pipeline:**
1. PlatformIO runs [`pio_hook.py`](pio_hook.py) once per build (`_MCU_VALIDATOR_RAN` guard) using `$PROJECT_SRC_DIR` and the configured `board`.
2. [`mcu_validator/cli.py`](mcu_validator/cli.py) resolves the matching `boards/*.json` profile via `load_board_data(board_id)`.
3. [`mcu_validator/parser.py`](mcu_validator/parser.py) resolves `.h/.hpp/.c/.cpp/.ino` files (supporting both single files and multi-file projects spanning `src/` and sibling `include/`) and walks each `tree-sitter-cpp` AST to emit `(requests, active_resources)`.
4. [`mcu_validator/solver.py`](mcu_validator/solver.py) checks hard rules and, upon conflict, runs Z3 `Optimize` to produce a minimal-invasive pin reassignment suggestion.
5. On `UNSAT`, `cli.py` exits with code `1`, stopping PlatformIO before invoking the C++ compiler and printing an LLM-Modulo repair prompt.

---

## 2. Strict Architectural Invariants (Must Not Break)

1. **Zero Chip-Specific Logic in Python:**
   All GPIO numbers, reserved flash/PSRAM ranges, strapping flags, peripheral conflicts, and resource triggers must live strictly in `boards/*.json`. Never hardcode board names or GPIO numbers in `parser.py`, `solver.py`, or `cli.py`.
2. **AST-First Parsing (`tree-sitter-cpp`):**
   Extract C/C++ structure (`preproc_def`, `declaration` -> `init_declarator` outside `for_statement`, `call_expression`) strictly via the Tree-Sitter AST (`CPP_LANGUAGE`). Only apply local regexes (`re`) to normalize short strings already isolated from an AST node (inline comments inside `preproc_arg`, whitespace inside function identifiers, numbered bus names like `Wire1`/`SPI2`/`Serial1`, or `SDA`/`SCL` fallback identifiers). Never scan raw source files with regexes.
3. **Cross-File Redefinition Safety (`_record_pin`):**
   When parsing multi-file projects, identical redefinitions across headers/sources are deduplicated cleanly, while conflicting redefinitions with different pin numbers are stored under `f"{name} ({file_path.name})"` so hardware collisions cannot be silently overwritten.
4. **Pairwise Shared-Bus Coupling in Z3 (`shared_capabilities`):**
   Do not replace the pairwise loop in `validate_with_z3` with a global `z3.Distinct(...)`. Signals sharing a `shared_capabilities` bus (e.g., multiple I2C or SPI devices initially placed on the same pin) must be coupled with `var_a == var_b`; all other signal pairs require `var_a != var_b`.
5. **MaxSMT Weight Hierarchy (`z3.Optimize`):**
   Keep valid original pin assignments unchanged (`weight=100`) and penalize strapping pins during reassignment (`weight=10`). Hard constraints (`allowed_pins` disjunction and pairwise distinctiveness/sharing) must never be weakened.
6. **Clean Library Packaging:**
   - Keep `"srcFilter": ["-<*>"]` in [`library.json`](library.json) so downstream PlatformIO projects consuming `mcu-pin-solver` via `lib_deps` never compile `src/main.cpp` as library code.
   - Keep `"export": { "include": [...] }` in [`library.json`](library.json) so `pio pkg pack` / `pio pkg publish` ships only runtime assets (`boards/`, `mcu_validator/`, `pio_hook.py`, `library.json`, `README.md`, `LICENSE`).
   - Do not import `.cli` inside [`mcu_validator/__init__.py`](mcu_validator/__init__.py) to avoid Python `runpy` `RuntimeWarning` when invoked via `python -m mcu_validator.cli`.

---

## 3. How to Extend the Project

### 3.1 Add a New Microcontroller (`boards/<mcu>.json`)
`load_board_data(board_id)` matches any `boards/<stem>.json` whose lowercase stem appears as a substring in `board_id.lower().replace("_", "-")` (e.g., `esp32-s3-devkitc-1` -> `boards/esp32-s3.json`).
Create `boards/<prefix>.json` using these top-level keys:
- `"mcu"`, `"description"`
- `"pins"`: map stringified GPIO indices to `{"capabilities": [...], "strapping": bool, "reserved": bool, "note": "..."}`
- `"capability_aliases"`: e.g. `{"adc": ["adc1", "adc2"]}`
- `"shared_capabilities"`: e.g. `["i2c", "spi"]`
- `"resource_triggers"`: map resource keys to AST call patterns matched by exact name or suffix `.<pattern>` (e.g. `{"wifi": ["WiFi.begin", "WiFi.softAP"]}`)
- `"conflict_rules"`: list of `{"id", "when_resource_active", "forbidden_capability" | "forbidden_pins", "reason"}`

Add a corresponding positive/negative scenario in [`tests/run_tests.py`](tests/run_tests.py) to verify the new JSON against real conflicts.

### 3.2 Support New C++ Pin Patterns or Capabilities (`mcu_validator/parser.py`)
- **Additional declaration types or call patterns:** Inspect the Tree-Sitter AST node types produced by `tree-sitter-cpp` (e.g., `constexpr`, `enum`, PWM/CAN/I2S init calls) and extend the node loop and capability classification inside `parse_cpp_file`.
- Keep unknown peripherals defaulting to `"gpio"` unless explicitly classified so generic digital pins continue to work out of the box.

### 3.3 Support New Hardware Constraint Categories (`mcu_validator/solver.py`)
- Extend `boards/*.json` schemas backward-compatibly using `.get("<new_field>", default)`.
- Translate new JSON rules into additional hard or weighted soft constraints inside `validate_with_z3`, preserving existing behavior for boards that omit optional fields.

---

## 4. Verification & Release Commands

Always run all checks from the repository root (`mvp_pin-solver/`):

```bash
# 1. Automated Python test suite (must pass all scenarios)
python tests/run_tests.py

# 2. Standalone CLI test (single file or multi-file src/ directory)
python -m mcu_validator.cli src esp32-c3

# 3. Local PlatformIO pre-build hook + firmware compilation test (requires PlatformIO CLI)
pio run

# 4. Validate PlatformIO Registry tarball packaging (delete tarball after inspection)
pio pkg pack

# 5. Publish to PlatformIO Registry (interactive login required once)
pio account login
pio pkg publish
```

> **Windows Note:** PlatformIO's embedded Python (`penv`) is bypassed by [`pio_hook.py`](pio_hook.py) via `shutil.which("py") or sys.executable` and auto-installs `z3-solver`, `tree-sitter`, and `tree-sitter-cpp` if missing. Ensure those three packages remain synchronized across [`pyproject.toml`](pyproject.toml), [`pio_hook.py`](pio_hook.py), and [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
