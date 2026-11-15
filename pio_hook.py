Import("env")
import inspect
import os
import shutil
import subprocess
import sys
from pathlib import Path

hook_dir = Path(inspect.getfile(inspect.currentframe())).resolve().parent
board_id = env.GetProjectOption("board", "esp32-c3")
src_dir = Path(env.subst("$PROJECT_SRC_DIR"))

python_cmd = shutil.which("py") or sys.executable

check_z3 = subprocess.run([python_cmd, "-c", "import z3"], capture_output=True)
if check_z3.returncode != 0:
    print("\n>>> [MCU-Validator] Installing z3-solver (first-time setup)...")
    subprocess.run([python_cmd, "-m", "pip", "install", "z3-solver"], check=True)

run_env = os.environ.copy()
run_env["PYTHONPATH"] = str(hook_dir) + os.pathsep + run_env.get("PYTHONPATH", "")

cpp_files = [
    p for p in sorted(src_dir.rglob("*"))
    if p.suffix in (".cpp", ".ino")
    and "tests" not in p.parts
    and ".pio" not in p.parts
]

print(f"\n>>> [MCU-Validator] Checking hardware constraints for board '{board_id}'...")

for sketch_file in cpp_files:
    result = subprocess.run(
        [python_cmd, "-m", "mcu_validator.cli", str(sketch_file), board_id],
        env=run_env,
    )
    if result.returncode != 0:
        print("\n>>> BUILD STOPPED: Please fix the hardware pin conflicts in your C++ code first!\n")
        env.Exit(1)

print("\n>>> [MCU-Validator] Hardware validation passed (SAT). Starting compiler...\n")
