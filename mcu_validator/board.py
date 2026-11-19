"""Board hardware profiles loaded and validated from declarative JSON files.

Every microcontroller's physical rules (exposed GPIOs, reserved flash pins,
capabilities, active-peripheral conflicts) live in `mcu_validator/boards/*.json`.
This module parses and validates one JSON file into typed dataclasses so the
rest of the codebase never works with untyped dictionaries.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# Bundled board profiles shipped inside the `mcu_validator` package.
BOARDS_DIR = Path(__file__).resolve().parent / "boards"


@dataclass(frozen=True)
class PinSpec:
    """Hardware properties of one physical GPIO pin on the microcontroller.

    Example:
        PinSpec(number=5, capabilities=frozenset({"gpio", "adc2"}), note="ADC2 + Wi-Fi conflict")
    """

    number: int
    capabilities: frozenset[str]  # Supported features (e.g. {"gpio", "adc1", "pwm"})
    strapping: bool = False       # Boot/strapping pin (prefer avoiding during repair)
    reserved: bool = False        # Internal system pin like SPI flash (must never be used)
    note: str = ""                # Optional short explanation shown in conflict messages


@dataclass(frozen=True)
class ConflictRule:
    """Rule blocking a capability or specific pins whenever a peripheral is active.

    Example:
        When "wifi" is active -> forbid capability "adc2".
        When "usb_serial" is active -> forbid pins {18, 19}.
    """

    id: str
    when_resource_active: str
    reason: str
    forbidden_capability: str | None = None
    forbidden_pins: frozenset[int] = frozenset()


@dataclass(frozen=True)
class BoardSpec:
    """Complete hardware rulebook for one microcontroller (loaded from a board JSON)."""

    mcu: str
    description: str
    pins: dict[int, PinSpec]
    capability_aliases: dict[str, frozenset[str]]
    shared_capabilities: frozenset[str]
    resource_triggers: dict[str, tuple[str, ...]]
    conflict_rules: tuple[ConflictRule, ...]

    def expand_capability(self, cap: str) -> frozenset[str]:
        """Expand a generic capability alias (e.g. 'adc' -> {'adc1', 'adc2'})."""
        return self.capability_aliases.get(cap, frozenset({cap}))

    @classmethod
    def from_dict(cls, data: object) -> BoardSpec:
        """Validate a raw JSON dictionary and build a typed `BoardSpec`.

        Raises:
            ValueError: If required fields are missing or have invalid types.
        """
        if not isinstance(data, dict):
            raise ValueError("Board profile JSON must be an object at the top level.")

        mcu = data.get("mcu")
        if not isinstance(mcu, str) or not mcu.strip():
            raise ValueError("Board profile must define a non-empty string 'mcu'.")

        description = data.get("description", "")
        if not isinstance(description, str):
            raise ValueError(f"Board '{mcu}': 'description' must be a string.")

        pins = _parse_pins(data.get("pins"), mcu)
        aliases = _parse_string_list_map(
            data.get("capability_aliases", {}), "capability_aliases", mcu
        )
        shared = frozenset(
            _parse_string_list(data.get("shared_capabilities", []), "shared_capabilities", mcu)
        )
        triggers = _parse_string_list_map(
            data.get("resource_triggers", {}), "resource_triggers", mcu
        )
        rules = _parse_conflict_rules(data.get("conflict_rules", []), triggers, mcu)

        return cls(
            mcu=mcu,
            description=description,
            pins=pins,
            capability_aliases={k: frozenset(v) for k, v in aliases.items()},
            shared_capabilities=shared,
            resource_triggers={k: tuple(v) for k, v in triggers.items()},
            conflict_rules=rules,
        )


def list_boards(boards_dir: Path = BOARDS_DIR) -> tuple[str, ...]:
    """Return sorted board profile names available in `boards_dir`."""
    if not boards_dir.is_dir():
        return ()
    return tuple(sorted(p.stem for p in boards_dir.glob("*.json")))


def load_board(board_id: str = "esp32-c3", boards_dir: Path = BOARDS_DIR) -> BoardSpec:
    """Find, load, and validate the JSON hardware profile matching `board_id`.

    `board_id` may be either:
      - A PlatformIO/MCU name such as `"esp32-c3-devkitm-1"` or `"ESP32_S3"` (matched
        against `*.json` stems in `boards_dir`, longest match first), or
      - A direct path to a `.json` board profile file.

    Raises:
        FileNotFoundError: If no matching board JSON exists.
        ValueError: If the JSON syntax or board schema is invalid.
    """
    direct_path = Path(board_id)
    if direct_path.suffix.lower() == ".json" and direct_path.is_file():
        return _load_board_file(direct_path)

    normalized = _normalize_name(board_id)
    candidates = sorted(
        boards_dir.glob("*.json") if boards_dir.is_dir() else (),
        key=lambda p: (-len(_normalize_name(p.stem)), _normalize_name(p.stem)),
    )
    for json_file in candidates:
        if _normalize_name(json_file.stem) in normalized:
            return _load_board_file(json_file)

    available = ", ".join(list_boards(boards_dir)) or "none"
    raise FileNotFoundError(
        f"No board profile matching '{board_id}' in {boards_dir} (available: {available})."
    )


# ---------------------------------------------------------------------------
# Internal schema validation helpers
# ---------------------------------------------------------------------------

def _normalize_name(name: str) -> str:
    """Normalize board names and file stems so 'ESP32_C3' matches 'esp32-c3'."""
    return name.strip().lower().replace("_", "-")


def _load_board_file(json_file: Path) -> BoardSpec:
    """Read a JSON board file and convert JSON/schema errors into clear ValueErrors."""
    try:
        raw_data = json.loads(json_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in board profile '{json_file}': {exc}") from exc
    return BoardSpec.from_dict(raw_data)


def _parse_pins(raw_pins: object, mcu: str) -> dict[int, PinSpec]:
    """Validate the 'pins' mapping and convert string keys to integer GPIO numbers."""
    if not isinstance(raw_pins, dict):
        raise ValueError(f"Board '{mcu}': 'pins' must be an object mapping pin numbers to specs.")

    pins: dict[int, PinSpec] = {}
    for raw_num, info in raw_pins.items():
        if not isinstance(raw_num, str) or not raw_num.isdigit():
            raise ValueError(
                f"Board '{mcu}': pin key '{raw_num}' must be a non-negative integer string."
            )
        if not isinstance(info, dict):
            raise ValueError(f"Board '{mcu}': pin '{raw_num}' entry must be an object.")

        num = int(raw_num)
        caps = _parse_string_list(info.get("capabilities", []), f"pins.{raw_num}.capabilities", mcu)
        strapping = _parse_bool(info.get("strapping", False), f"pins.{raw_num}.strapping", mcu)
        reserved = _parse_bool(info.get("reserved", False), f"pins.{raw_num}.reserved", mcu)
        note = info.get("note", "")
        if not isinstance(note, str):
            raise ValueError(f"Board '{mcu}': 'pins.{raw_num}.note' must be a string.")

        pins[num] = PinSpec(
            number=num,
            capabilities=frozenset(caps),
            strapping=strapping,
            reserved=reserved,
            note=note,
        )
    return pins


def _parse_conflict_rules(
    raw_rules: object,
    triggers: dict[str, list[str]],
    mcu: str,
) -> tuple[ConflictRule, ...]:
    """Validate 'conflict_rules' entries and check that their trigger modules exist."""
    if not isinstance(raw_rules, list):
        raise ValueError(f"Board '{mcu}': 'conflict_rules' must be a list.")

    rules: list[ConflictRule] = []
    for idx, rule in enumerate(raw_rules):
        if not isinstance(rule, dict):
            raise ValueError(f"Board '{mcu}': conflict_rules[{idx}] must be an object.")

        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise ValueError(f"Board '{mcu}': conflict_rules[{idx}] needs a non-empty string 'id'.")

        resource = rule.get("when_resource_active")
        if not isinstance(resource, str) or not resource.strip():
            raise ValueError(
                f"Board '{mcu}': rule '{rule_id}' needs a string 'when_resource_active'."
            )
        if resource not in triggers:
            raise ValueError(
                f"Board '{mcu}': rule '{rule_id}' references unknown resource '{resource}' "
                f"(not defined in 'resource_triggers')."
            )

        forbidden_cap = rule.get("forbidden_capability")
        if forbidden_cap is not None and not isinstance(forbidden_cap, str):
            raise ValueError(
                f"Board '{mcu}': rule '{rule_id}' 'forbidden_capability' must be a string."
            )

        raw_forbidden_pins = rule.get("forbidden_pins", [])
        if not isinstance(raw_forbidden_pins, list) or not all(
            isinstance(p, int) and not isinstance(p, bool) and p >= 0 for p in raw_forbidden_pins
        ):
            raise ValueError(
                f"Board '{mcu}': rule '{rule_id}' 'forbidden_pins' must be "
                "a list of non-negative integers."
            )

        if forbidden_cap is None and not raw_forbidden_pins:
            raise ValueError(
                f"Board '{mcu}': rule '{rule_id}' must specify "
                "'forbidden_capability' or 'forbidden_pins'."
            )

        reason = rule.get("reason", f"Blocked by active '{resource}'.")
        if not isinstance(reason, str):
            raise ValueError(f"Board '{mcu}': rule '{rule_id}' 'reason' must be a string.")

        rules.append(
            ConflictRule(
                id=rule_id,
                when_resource_active=resource,
                reason=reason,
                forbidden_capability=forbidden_cap,
                forbidden_pins=frozenset(raw_forbidden_pins),
            )
        )
    return tuple(rules)


def _parse_string_list(value: object, field_name: str, mcu: str) -> list[str]:
    """Ensure a JSON value is a list of strings (rejecting bare strings like 'gpio')."""
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Board '{mcu}': '{field_name}' must be a list of strings.")
    return value


def _parse_string_list_map(value: object, field_name: str, mcu: str) -> dict[str, list[str]]:
    """Ensure a JSON value is a dict mapping string keys to lists of strings."""
    if not isinstance(value, dict):
        raise ValueError(f"Board '{mcu}': '{field_name}' must be an object.")
    result: dict[str, list[str]] = {}
    for key, items in value.items():
        if not isinstance(key, str):
            raise ValueError(f"Board '{mcu}': keys in '{field_name}' must be strings.")
        result[key] = _parse_string_list(items, f"{field_name}.{key}", mcu)
    return result


def _parse_bool(value: object, field_name: str, mcu: str) -> bool:
    """Ensure a JSON value is strictly a boolean."""
    if not isinstance(value, bool):
        raise ValueError(f"Board '{mcu}': '{field_name}' must be a boolean.")
    return value
