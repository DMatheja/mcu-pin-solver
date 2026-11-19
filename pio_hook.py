"""PlatformIO pre-build hook (SCons script) that runs mcu-pin-solver before compilation.

PlatformIO executes this file automatically when `extra_scripts` points to `pio_hook.py`.
If the validator finds any hardware conflict or configuration error, this script aborts
the build BEFORE the C++ compiler starts.
"""

Import("env")  # Provided by PlatformIO's SCons build environment

import inspect
import os
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_PACKAGES = (
    "z3-solver>=4.12.0",
    "tree-sitter>=0.23.0",
    "tree-sitter-cpp>=0.23.0",
)


def _resolve_hook_dir() -> Path:
    """Locate this hook's directory (SCons runs via exec(), so __file__ may be absent)."""
    script_file = globals().get("__file__")
    if script_file:
        return Path(script_file).resolve().parent
    frame = inspect.currentframe()
    if frame is None:
        raise RuntimeError("Could not determine pio_hook.py directory.")
    return Path(inspect.getfile(frame)).resolve().parent


def _ensure_dependencies(python_cmd: str) -> bool:
    """Ensure Z3 and Tree-Sitter are importable, installing them via pip on first run."""
    check = subprocess.run(
        [python_cmd, "-c", "import z3, tree_sitter, tree_sitter_cpp"],
        capture_output=True,
    )
    if check.returncode == 0:
        return True

    print("\n>>> [MCU-Validator] Installing dependencies (first-time setup)...")
    install = subprocess.run([python_cmd, "-m", "pip", "install", *REQUIRED_PACKAGES])
    if install.returncode != 0:
        pkgs = " ".join(f'"{p}"' for p in REQUIRED_PACKAGES)
        print(
            "\n>>> [MCU-Validator] Automatic pip install failed "
            "(e.g. offline or PEP 668 system Python).\n"
            f">>> Please install manually: {python_cmd} -m pip install {pkgs}\n"
        )
        return False
    return True


# PlatformIO may evaluate extra_scripts more than once per build; only validate once.
if not env.get("_MCU_VALIDATOR_RAN"):
    env["_MCU_VALIDATOR_RAN"] = True

    hook_dir = _resolve_hook_dir()
    board_id = env.GetProjectOption("board", "esp32-c3")
    src_dir = Path(env.subst("$PROJECT_SRC_DIR"))
    include_dir = Path(env.subst("$PROJECT_INCLUDE_DIR"))

    # On Windows, prefer the system `py` launcher instead of modifying PlatformIO's private penv.
    python_cmd = shutil.which("py") or sys.executable
    if not _ensure_dependencies(python_cmd):
        env.Exit(1)

    run_env = os.environ.copy()
    existing_py_path = run_env.get("PYTHONPATH", "")
    run_env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(hook_dir), existing_py_path]))

    cmd = [python_cmd, "-m", "mcu_validator.cli", str(src_dir), board_id]
    if include_dir.is_dir():
        cmd.extend(["--include-dir", str(include_dir)])

    print(f"\n>>> [MCU-Validator] Checking hardware constraints for board '{board_id}'...")
    result = subprocess.run(cmd, env=run_env)

    if result.returncode == 1:
        print("\n>>> BUILD STOPPED: Fix the hardware pin conflicts in your C++ code first!\n")
        env.Exit(1)
    elif result.returncode != 0:
        print(
            "\n>>> BUILD STOPPED: MCU-Validator configuration/input error "
            f"(exit code {result.returncode}).\n"
        )
        env.Exit(1)

    print("\n>>> [MCU-Validator] Hardware validation passed (SAT). Starting compiler...\n")
