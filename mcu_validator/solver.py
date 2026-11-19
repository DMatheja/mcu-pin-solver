"""Hardware rule checker and Z3 MaxSMT minimal-invasive pin repair solver.

Start reading at `validate()` — it runs 3 clear steps:
  1. `_active_restrictions()` — find pins/capabilities blocked by active modules (Wi-Fi, USB).
  2. `_find_conflicts()`      — check whether the current C++ pin assignments break any rule.
  3. `_solve_reassignment()`  — if conflicts exist, ask Z3 MaxSMT for the smallest valid fix.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from z3 import And, ArithRef, Int, Optimize, Or, sat

from .board import BoardSpec
from .parser import ParsedProject, PinRequest

# Z3 MaxSMT soft-constraint priorities (higher weight strictly dominates lower weights):
KEEP_ORIGINAL_WEIGHT = 1000     # 1st priority: keep already-valid pins unchanged
AVOID_STRAPPING_WEIGHT = 20     # 2nd priority: avoid boot/strapping pins on reassignment
SAVE_SPECIAL_PIN_WEIGHT = 5     # 3rd priority: save scarce ADC/USB pins when plain GPIO suffices

# Hardware capabilities worth preserving for signals that actually require them.
SCARCE_CAPABILITIES = frozenset({"adc", "adc1", "adc2", "usb"})


@dataclass(frozen=True)
class ValidationResult:
    """Final result returned by `validate()`."""

    is_valid: bool
    conflicts: tuple[str, ...]      # Human-readable conflict messages (empty when SAT)
    suggested_pins: dict[str, int]  # Signal name -> verified GPIO number
    repair_possible: bool = True    # False only when no valid assignment fits on this MCU
    warnings: tuple[str, ...] = ()  # Non-blocking hardware advisories (e.g. strapping pins)


@dataclass(frozen=True)
class _ActiveRestrictions:
    """Capabilities and physical pins blocked by active modules (e.g. Wi-Fi or USB-Serial)."""

    forbidden_caps: dict[str, str]  # Blocked capability -> reason
    forbidden_pins: dict[int, str]  # Blocked GPIO pin   -> reason


# ---------------------------------------------------------------------------
# Top-level orchestrator (read this first!)
# ---------------------------------------------------------------------------

def validate(project: ParsedProject, board: BoardSpec) -> ValidationResult:
    """Check whether all pin requests fit `board`, and compute a Z3-verified fix if not.

    Raises:
        ValueError: If two `PinRequest` objects in `project.requests` share the same `.name`.
    """
    _ensure_unique_request_names(project.requests)

    restrictions = _active_restrictions(project.active_resources, board)
    conflicts = _find_conflicts(project.requests, board, restrictions)

    if not conflicts:
        kept = {req.name: req.pin for req in project.requests}
        warnings = _find_strapping_warnings(project.requests, board, restrictions)
        return ValidationResult(
            is_valid=True,
            conflicts=(),
            suggested_pins=kept,
            warnings=tuple(warnings),
        )

    suggested = _solve_reassignment(project.requests, board, restrictions)
    warnings = _find_strapping_warnings(
        project.requests,
        board,
        restrictions,
        assigned_pins=suggested,
    )
    return ValidationResult(
        is_valid=False,
        conflicts=tuple(conflicts),
        suggested_pins=suggested or {},
        repair_possible=suggested is not None,
        warnings=tuple(warnings),
    )


# ---------------------------------------------------------------------------
# Step 1: Determine which pins and capabilities are blocked right now
# ---------------------------------------------------------------------------

def _active_restrictions(
    active_resources: tuple[str, ...],
    board: BoardSpec,
) -> _ActiveRestrictions:
    """Evaluate the board's `conflict_rules` against whichever modules are active in code."""
    active = set(active_resources)
    forbidden_caps: dict[str, str] = {}
    forbidden_pins: dict[int, str] = {}

    for rule in board.conflict_rules:
        if rule.when_resource_active not in active:
            continue
        if rule.forbidden_capability:
            forbidden_caps.setdefault(rule.forbidden_capability, rule.reason)
        for pin_num in rule.forbidden_pins:
            forbidden_pins.setdefault(pin_num, rule.reason)

    return _ActiveRestrictions(forbidden_caps=forbidden_caps, forbidden_pins=forbidden_pins)


# ---------------------------------------------------------------------------
# Step 2: Check current pin assignments for hardware conflicts
# ---------------------------------------------------------------------------

def _find_conflicts(
    requests: tuple[PinRequest, ...],
    board: BoardSpec,
    restrictions: _ActiveRestrictions,
) -> list[str]:
    """Validate every requested pin against the board and collect all conflict messages."""
    conflicts: list[str] = []
    seen_on_pin: dict[int, list[PinRequest]] = {}

    for req in requests:
        conflicts.extend(_check_single_pin(req, seen_on_pin.get(req.pin, ()), board, restrictions))
        if req.pin in board.pins:
            seen_on_pin.setdefault(req.pin, []).append(req)

    return conflicts


def _check_single_pin(
    req: PinRequest,
    previous_on_pin: Sequence[PinRequest],
    board: BoardSpec,
    restrictions: _ActiveRestrictions,
) -> list[str]:
    """Run all hardware checks for one `PinRequest`."""
    label = _pin_label(req)
    spec = board.pins.get(req.pin)
    if spec is None:
        return [f"{label}: Pin does not exist on {board.mcu}."]

    errors: list[str] = []
    for prev in previous_on_pin:
        if not _can_share_bus(req, prev, board.shared_capabilities):
            errors.append(f"{label}: Collides with {prev.name} (not a shared bus line).")
            break

    if spec.reserved:
        errors.append(f"{label}: Reserved pin ({spec.note or 'system use'}).")
        return errors

    if req.pin in restrictions.forbidden_pins:
        errors.append(f"{label}: {restrictions.forbidden_pins[req.pin]}")
        return errors

    errors.extend(_check_capabilities(req, spec.capabilities, board, restrictions.forbidden_caps))
    return errors


def _check_capabilities(
    req: PinRequest,
    pin_caps: frozenset[str],
    board: BoardSpec,
    forbidden_caps: dict[str, str],
) -> list[str]:
    """Verify that a pin supports every required capability without hitting blocked banks."""
    label = _pin_label(req)
    errors: list[str] = []
    for cap in sorted(req.capabilities):
        matching = board.expand_capability(cap) & pin_caps
        if not matching:
            errors.append(f"{label}: Does not support capability '{cap}'.")
        elif matching <= forbidden_caps.keys():
            reason = forbidden_caps[min(matching)]
            errors.append(f"{label}: {reason}")
    return errors


def _find_strapping_warnings(
    requests: tuple[PinRequest, ...],
    board: BoardSpec,
    restrictions: _ActiveRestrictions,
    assigned_pins: dict[str, int] | None = None,
) -> list[str]:
    """Collect non-blocking advisories for signals placed on boot/strapping pins.

    When `assigned_pins` is provided (after Z3 repair), checks the resulting assignment so
    already-rejected pins are not warned about twice while unavoidable strapping assignments
    are still surfaced.
    """
    warnings: list[str] = []
    for req in requests:
        pin_num = assigned_pins[req.name] if assigned_pins is not None else req.pin
        spec = board.pins.get(pin_num)
        if spec is None or not spec.strapping:
            continue
        if spec.reserved or pin_num in restrictions.forbidden_pins:
            continue

        reassigned = assigned_pins is not None and pin_num != req.pin
        label = _pin_label(req, pin_override=pin_num if reassigned else None)
        detail = _strapping_detail(spec.note)
        warnings.append(
            f"{label}: {detail}. External pull-up/down circuitry may affect boot behavior."
        )
    return warnings


# ---------------------------------------------------------------------------
# Step 3: Compute a minimal-invasive reassignment with Z3 MaxSMT (Optimize)
# ---------------------------------------------------------------------------

def _solve_reassignment(
    requests: tuple[PinRequest, ...],
    board: BoardSpec,
    restrictions: _ActiveRestrictions,
) -> dict[str, int] | None:
    """Ask Z3 MaxSMT for a valid pin assignment changing as few pins as possible."""
    opt = Optimize()
    z3_vars: list[ArithRef] = []

    for idx, req in enumerate(requests):
        allowed = _allowed_pins_for(req, board, restrictions)
        if not allowed:
            return None  # Impossible: zero pins on this chip can satisfy this signal
        var = Int(f"pin_{idx}")
        z3_vars.append(var)
        _add_pin_constraints(opt, var, req, allowed, board)

    _add_pairwise_constraints(opt, requests, z3_vars, board)

    if opt.check() != sat:
        return None
    model = opt.model()
    return {req.name: model[var].as_long() for req, var in zip(requests, z3_vars)}


def _allowed_pins_for(
    req: PinRequest,
    board: BoardSpec,
    restrictions: _ActiveRestrictions,
) -> list[int]:
    """List every physical GPIO number on `board` that can legally host `req`."""
    return [
        pin_num
        for pin_num, spec in board.pins.items()
        if not spec.reserved
        and pin_num not in restrictions.forbidden_pins
        and all(
            (board.expand_capability(cap) - restrictions.forbidden_caps.keys()) & spec.capabilities
            for cap in req.capabilities
        )
    ]


def _add_pin_constraints(
    opt: Optimize,
    var: ArithRef,
    req: PinRequest,
    allowed: list[int],
    board: BoardSpec,
) -> None:
    """Add hard domain rules and prioritized soft preferences for one Z3 pin variable."""
    # Hard rule: pin MUST be one of the valid candidate GPIOs.
    opt.add(Or([var == p for p in allowed]))

    # Soft rule 1: Prefer keeping the original pin unchanged if it is valid.
    if req.pin in allowed:
        opt.add_soft(var == req.pin, weight=KEEP_ORIGINAL_WEIGHT)

    # Soft rule 2: Prefer avoiding boot/strapping pins.
    strapping_pins = [p for p in allowed if board.pins[p].strapping]
    if strapping_pins and len(strapping_pins) < len(allowed):
        opt.add_soft(And([var != p for p in strapping_pins]), weight=AVOID_STRAPPING_WEIGHT)

    # Soft rule 3: Save scarce pins (ADC/USB) when this signal doesn't need those capabilities.
    needed_caps = set().union(*(board.expand_capability(cap) for cap in req.capabilities))
    avoid_caps = SCARCE_CAPABILITIES - needed_caps
    scarce_pins = [p for p in allowed if board.pins[p].capabilities & avoid_caps]
    if scarce_pins and len(scarce_pins) < len(allowed):
        opt.add_soft(And([var != p for p in scarce_pins]), weight=SAVE_SPECIAL_PIN_WEIGHT)


def _add_pairwise_constraints(
    opt: Optimize,
    requests: tuple[PinRequest, ...],
    z3_vars: list[ArithRef],
    board: BoardSpec,
) -> None:
    """Enforce pin uniqueness while keeping signals on the same shared bus line coupled together."""
    for i, req_a in enumerate(requests):
        for j in range(i + 1, len(requests)):
            req_b = requests[j]
            if _can_share_bus(req_a, req_b, board.shared_capabilities) and req_a.pin == req_b.pin:
                opt.add(z3_vars[i] == z3_vars[j])
            else:
                opt.add(z3_vars[i] != z3_vars[j])


def _can_share_bus(a: PinRequest, b: PinRequest, shared_caps: frozenset[str]) -> bool:
    """Return True only when both signals share the same single shareable bus capability & line."""
    return (
        a.capabilities == b.capabilities
        and len(a.capabilities) == 1
        and next(iter(a.capabilities)) in shared_caps
        and a.bus_group == b.bus_group
    )


def _pin_label(req: PinRequest, *, pin_override: int | None = None) -> str:
    """Format a signal name with its GPIO number and optional file:line location."""
    if pin_override is not None:
        pin_text = f"suggested GPIO {pin_override}"
    else:
        pin_text = f"GPIO {req.pin}"
    if req.location:
        return f"{req.name} ({pin_text}, {req.location})"
    return f"{req.name} ({pin_text})"


def _strapping_detail(note: str) -> str:
    """Format a board pin's note so strapping warnings always read clearly."""
    cleaned = note.strip().rstrip(".")
    if not cleaned:
        return "Strapping pin"
    if "strapping" in cleaned.lower():
        return cleaned
    return f"Strapping pin ({cleaned})"


def _ensure_unique_request_names(requests: tuple[PinRequest, ...]) -> None:
    """Guard against duplicate signal names so `suggested_pins` never silently drops a signal."""
    seen: set[str] = set()
    for req in requests:
        if req.name in seen:
            raise ValueError(
                f"Duplicate PinRequest name '{req.name}'; each request must be unique."
            )
        seen.add(req.name)
