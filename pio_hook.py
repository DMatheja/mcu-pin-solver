Import("env")
import inspect
import os
import shutil
import subprocess
import sys
from pathlib import Path

if not env.get("_MCU_VALIDATOR_RAN"):
    env["_MCU_VALIDATOR_RAN"] = True

    hook_dir = Path(inspect.getfile(inspect.currentframe())).resolve().parent
    board_id = env.GetProjectOption("board", "esp32-c3")
    src_dir = Path(env.subst("$PROJECT_SRC_DIR"))

    python_cmd = shutil.which("py") or sys.executable

    check_deps = subprocess.run(
        [python_cmd, "-c", "import z3, tree_sitter, tree_sitter_cpp"],
        capture_output=True,
    )
    if check_deps.returncode != 0:
        print("\n>>> [MCU-Validator] Installing dependencies (first-time setup)...")
        subprocess.run(
            [python_cmd, "-m", "pip", "install", "z3-solver", "tree-sitter", "tree-sitter-cpp"],
            check=True,
        )

    run_env = os.environ.copy()
    run_env["PYTHONPATH"] = str(hook_dir) + os.pathsep + run_env.get("PYTHONPATH", "")

    print(f"\n>>> [MCU-Validator] Checking hardware constraints for board '{board_id}'...")

    result = subprocess.run(
        [python_cmd, "-m", "mcu_validator.cli", str(src_dir), board_id],
        env=run_env,
    )
    if result.returncode != 0:
        print("\n>>> BUILD STOPPED: Please fix the hardware pin conflicts in your C++ code first!\n")
        env.Exit(1)

    print("\n>>> [MCU-Validator] Hardware validation passed (SAT). Starting compiler...\n")
