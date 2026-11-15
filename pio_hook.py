Import("env")
import inspect
import shutil
import subprocess
import sys
from pathlib import Path

# Directory where pio_hook.py (and mcu_validator/) is located
hook_dir = Path(inspect.getfile(inspect.currentframe())).resolve().parent
validator_script = hook_dir / "validator.py"

# Read target board and source directory directly from PlatformIO
board_id = env.GetProjectOption("board", "esp32-c3")
src_dir = Path(env.subst("$PROJECT_SRC_DIR"))

# Prefer Windows system Python launcher 'py' if available, else PlatformIO's Python
python_cmd = shutil.which("py") or sys.executable

# Ensure z3-solver is installed on the current machine (auto-installs on first run on a new PC)
check_z3 = subprocess.run([python_cmd, "-c", "import z3"], capture_output=True)
if check_z3.returncode != 0:
    print("\n>>> [MCU-Validator] Installing z3-solver (first-time setup)...")
    subprocess.run([python_cmd, "-m", "pip", "install", "z3-solver"], check=True)

# Find all C++ / Arduino files in src_dir (ignoring scenarios/ and .pio/)
cpp_files = [
    p for p in sorted(src_dir.rglob("*"))
    if p.suffix in (".cpp", ".ino")
    and "scenarios" not in p.parts
    and ".pio" not in p.parts
]

print(f"\n>>> [MCU-Validator] Checking hardware constraints for board '{board_id}'...")

for sketch_file in cpp_files:
    result = subprocess.run([python_cmd, str(validator_script), str(sketch_file), board_id])
    if result.returncode != 0:
        print("\n>>> BUILD STOPPED: Please fix the hardware pin conflicts in your C++ code first!\n")
        env.Exit(1)

print("\n>>> [MCU-Validator] Hardware validation passed (SAT). Starting compiler...\n")
