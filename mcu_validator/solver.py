import json
from pathlib import Path
from z3 import Distinct, Int, Or, Optimize, sat

BOARDS_DIR = Path(__file__).resolve().parent.parent / "boards"

# Loads the matching JSON hardware definition for a board name (e.g. 'esp32-s3-devkitc-1' -> 'esp32-s3.json')
def load_board_data(board_id="esp32-c3"):
    board_id_lower = board_id.lower().replace("_", "-")
    for json_file in sorted(BOARDS_DIR.glob("*.json")):
        if json_file.stem.lower() in board_id_lower:
            return json.loads(json_file.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"No hardware definition found for board '{board_id}' in {BOARDS_DIR}")

# Validates pin requests against the board JSON and computes a minimal-invasive repair via Z3 MaxSMT
def validate_with_z3(requests, active_resources, board_data):
    pins_db = {int(k): v for k, v in board_data["pins"].items()}
    aliases = board_data.get("capability_aliases", {})
    rules = board_data.get("conflict_rules", [])

    # 1. Evaluate active conflict rules
    forbidden_caps = set()
    forbidden_pins = set()
    for rule in rules:
        if rule["when_resource_active"] in active_resources:
            if "forbidden_capability" in rule:
                forbidden_caps.add(rule["forbidden_capability"])
            if "forbidden_pins" in rule:
                forbidden_pins.update(rule["forbidden_pins"])

    # 2. Check current pin assignments for conflicts
    conflicts = []
    seen_pins = {}
    for req in requests:
        p = req["pin"]
        info = pins_db.get(p)
        if not info:
            conflicts.append(f"{req['name']} (GPIO {p}): Pin does not exist on {board_data['mcu']}.")
            continue
        if p in seen_pins:
            conflicts.append(f"{req['name']} (GPIO {p}): Duplicate assignment with {seen_pins[p]}.")
        seen_pins[p] = req["name"]

        if info.get("reserved"):
            conflicts.append(f"{req['name']} (GPIO {p}): Reserved pin! ({info.get('note', 'Reserved')})")
            continue

        target_caps = set(aliases.get(req["cap"], [req["cap"]]))
        matching_caps = target_caps.intersection(info["capabilities"])
        if not matching_caps:
            conflicts.append(f"{req['name']} (GPIO {p}): Does not support capability '{req['cap']}'.")
        elif matching_caps.issubset(forbidden_caps) or p in forbidden_pins:
            conflicts.append(
                f"{req['name']} (GPIO {p}): Conflicts with active {active_resources} ({info.get('note', 'Blocked')})."
            )

    if not conflicts:
        return True, [], {r["name"]: r["pin"] for r in requests}

    # 3. Z3 Optimize (MaxSMT): Compute a minimal-invasive pin reassignment
    opt = Optimize()
    z3_vars = {}
    for req in requests:
        var = Int(req["name"])
        z3_vars[req["name"]] = var
        target_caps = set(aliases.get(req["cap"], [req["cap"]])) - forbidden_caps

        allowed_pins = [
            p for p, info in pins_db.items()
            if not info.get("reserved")
            and p not in forbidden_pins
            and target_caps.intersection(info["capabilities"])
        ]

        if allowed_pins:
            opt.add(Or([var == p for p in allowed_pins]))
        else:
            opt.add(var == -1)

        # Soft Constraint 1 (weight 100): Keep valid original pins unchanged whenever possible
        opt.add_soft(var == req["pin"], weight=100)

        # Soft Constraint 2 (weight 10): Avoid boot/strapping pins during reassignment
        for p in allowed_pins:
            if pins_db[p].get("strapping"):
                opt.add_soft(var != p, weight=10)

    if len(z3_vars) > 1:
        opt.add(Distinct(list(z3_vars.values())))

    suggested = {}
    if opt.check() == sat:
        model = opt.model()
        suggested = {name: model[var].as_long() for name, var in z3_vars.items()}

    return False, conflicts, suggested
