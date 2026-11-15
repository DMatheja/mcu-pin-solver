import sys
from .parser import parse_cpp_file
from .solver import load_board_data, validate_with_z3

# Formats the validation result and generates the LLM repair prompt
def format_report(cpp_path, board_data, active_resources, requests, is_valid, conflicts, suggested):
    lines = [
        "=" * 65,
        f" Checked File   : {cpp_path} ({board_data['mcu']})",
        f" Active Modules : {active_resources}",
        "=" * 65,
    ]
    if is_valid:
        lines.append(" RESULT: SAT (All pins valid! No hardware conflicts detected.)")
    else:
        lines.extend([
            " RESULT: UNSAT (Hardware conflicts detected!)\n",
            "--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---\n",
            f"Your C++ code for the {board_data['mcu']} contains the following hardware errors:",
        ])
        for conflict in conflicts:
            lines.append(f"  - {conflict}")
        lines.append("\nPlease regenerate the code using this exact Z3-verified pin assignment:")
        for req in requests:
            name, old_p = req["name"], req["pin"]
            new_p = suggested.get(name)
            if old_p == new_p:
                lines.append(f"  - {name}: Keep GPIO {old_p} (unchanged)")
            else:
                lines.append(f"  - {name}: Change GPIO {old_p} -> GPIO {new_p}")
        lines.append("\n-----------------------------------------------------")
    return "\n".join(lines)

def validate_file(cpp_path, board_id="esp32-c3"):
    board_data = load_board_data(board_id)
    requests, active_res = parse_cpp_file(cpp_path)
    is_valid, conflicts, suggested = validate_with_z3(requests, active_res, board_data)
    report = format_report(cpp_path, board_data, active_res, requests, is_valid, conflicts, suggested)
    return is_valid, report

def main():
    cpp_file = sys.argv[1] if len(sys.argv) > 1 else "src/main.cpp"
    board_id = sys.argv[2] if len(sys.argv) > 2 else "esp32-c3"
    is_valid, report = validate_file(cpp_file, board_id)
    print(report)
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()
