"""Tree-Sitter C++ AST analyzer that extracts pin requests and active peripherals.

Start reading at `parse_cpp()` — it shows the full 4-step pipeline from top to bottom.
Each helper section below implements one step in execution order.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter_cpp as tscpp
from tree_sitter import Language, Node, Parser

from .board import BoardSpec

# Compiled Tree-Sitter C++ grammar (immutable; each scan creates its own Parser instance).
CPP_LANGUAGE = Language(tscpp.language())

HEADER_EXTS = frozenset({".h", ".hpp"})
CPP_EXTS = HEADER_EXTS | {".c", ".cpp", ".ino"}
IGNORED_DIRS = frozenset({".git", ".pio", ".venv", "__pycache__", "build", "test", "tests", "venv"})
PIN_VAR_TYPES = frozenset({"int", "unsigned int", "uint8_t", "int8_t", "byte"})

# Arduino / ESP32 functions where argument #0 is a hardware pin.
ARG0_CAPABILITIES: dict[str, str] = {
    "pinMode": "gpio",
    "digitalWrite": "gpio",
    "digitalRead": "gpio",
    "digitalPinToInterrupt": "gpio",
    "pulseIn": "gpio",
    "tone": "gpio",
    "noTone": "gpio",
    "analogRead": "adc",
    "analogReadMilliVolts": "adc",
    "analogWrite": "pwm",
    "ledcAttach": "pwm",
    "ledcAttachPin": "pwm",
}

# Suffixes that indicate a non-pin setting (e.g. BAUD_RATE, DELAY_MS, I2C_ADDR, LED_COUNT).
NON_PIN_SUFFIXES = frozenset({
    "ADDR", "BAUD", "CH", "CHANNEL", "COUNT", "DELAY", "FREQ", "HZ", "ID",
    "INTERVAL", "LEN", "LIMIT", "MASK", "MAX", "MIN", "MODE", "MS", "NUM",
    "OFFSET", "PERIOD", "PORT", "RATE", "SIZE", "SPEED", "TIMEOUT", "TYPE", "US",
})

WIRE_CALL_RE = re.compile(r"^(Wire\d*)\.(?:begin|setPins)$")
SPI_CALL_RE = re.compile(r"^(SPI\d*)\.begin$")
SERIAL_CALL_RE = re.compile(r"^Serial\d*\.begin$")
COMMENT_RE = re.compile(r"//.*|/\*.*?\*/", re.DOTALL)
WORD_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z]|_|\d|$)|[A-Z]?[a-z]+|\d+")


@dataclass(frozen=True)
class PinRequest:
    """One hardware pin assignment extracted from C/C++ code.

    Example:
        PinRequest(name="SOIL_SENSOR", pin=5, capabilities=frozenset({"adc"}), location="pins.h:5")
    """

    name: str                      # Unique signal key (e.g. "SOIL_SENSOR" or "GPIO_12")
    pin: int                       # Assigned GPIO number from the C++ code
    capabilities: frozenset[str]   # Required features (e.g. {"adc"}, {"i2c"})
    bus_group: str | None = None   # Shared bus line identity (e.g. "Wire:sda", "SPI:mosi")
    location: str = ""             # Source file:line like "pins.h:4" (empty if created manually)


@dataclass(frozen=True)
class ParsedProject:
    """Complete parser output handed to the solver."""

    requests: tuple[PinRequest, ...]
    active_resources: tuple[str, ...]


@dataclass(frozen=True)
class _PinDefinition:
    """One top-level integer constant discovered during AST scanning."""

    key: str           # Globally unique signal name
    raw_name: str      # Original C++ identifier
    pin: int
    source_file: Path
    line: int          # 1-based line number


@dataclass(frozen=True)
class _LiteralPinUse:
    """One direct numeric pin argument (e.g. `pinMode(12, OUTPUT)` or `Wire.begin(6, 7)`)."""

    pin: int
    capability: str
    bus_group: str | None
    location: str


@dataclass
class _SourceScan:
    """Mutable working notebook filled while walking all C/C++ files in Step 2."""

    definitions: list[_PinDefinition] = field(default_factory=list)
    used_keys: set[str] = field(default_factory=set)
    seen_values: dict[str, set[int]] = field(default_factory=dict)
    called_functions: set[str] = field(default_factory=set)
    caps_by_name: dict[str, set[str]] = field(default_factory=dict)
    caps_by_file_and_name: dict[tuple[Path, str], set[str]] = field(default_factory=dict)
    bus_by_name: dict[str, set[str]] = field(default_factory=dict)
    bus_by_file_and_name: dict[tuple[Path, str], set[str]] = field(default_factory=dict)
    literal_uses: list[_LiteralPinUse] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level orchestrator (read this first!)
# ---------------------------------------------------------------------------

def parse_cpp(
    cpp_path: str | Path,
    board: BoardSpec | None = None,
    include_dirs: Sequence[str | Path] = (),
) -> ParsedProject:
    """Analyze a C/C++ file or project folder and extract its pin requirements.

    Steps:
        1. Resolve all `.h/.hpp/.c/.cpp/.ino` files to inspect.
        2. Parse each file with Tree-Sitter to collect constants and API calls.
        3. Match constants and numeric pin calls to required hardware capabilities.
        4. Detect which board peripherals (like Wi-Fi or USB-Serial) are active.
    """
    files = _resolve_source_files(cpp_path, include_dirs)
    scan = _scan_files(files)
    requests = _build_pin_requests(scan)
    active_resources = _detect_active_resources(scan.called_functions, board)
    return ParsedProject(requests=requests, active_resources=active_resources)


# ---------------------------------------------------------------------------
# Step 1: Resolve which C/C++ files belong to the target path
# ---------------------------------------------------------------------------

def _resolve_source_files(
    target: str | Path,
    include_dirs: Sequence[str | Path] = (),
) -> list[Path]:
    """Turn a single file or project directory (plus optional include dirs) into sorted files."""
    path = Path(target)
    if path.is_file():
        files = [path]
        extra_dirs = [Path(d) for d in include_dirs if Path(d).is_dir()]
        if not extra_dirs:
            return files
        found = _dedupe_paths([*files, *_collect_files_in_dirs(extra_dirs)])
        return _sort_headers_first(found)

    if not path.is_dir():
        raise FileNotFoundError(f"Source path not found: {target}")

    dirs = _project_search_dirs(path)
    for inc in include_dirs:
        inc_path = Path(inc)
        if inc_path.is_dir():
            dirs.append(inc_path)

    found = _dedupe_paths(_collect_files_in_dirs(dirs))
    return _sort_headers_first(found)


def _project_search_dirs(path: Path) -> list[Path]:
    """Choose search folders for a PlatformIO-style layout (auto-including sibling `include/`)."""
    resolved = path.resolve()
    if resolved.name == "src" and (resolved.parent / "include").is_dir():
        return [resolved.parent / "include", resolved]
    if (resolved / "include").is_dir() or (resolved / "src").is_dir():
        return [d for d in (resolved / "include", resolved / "src") if d.is_dir()]
    return [resolved]


def _collect_files_in_dirs(dirs: Iterable[Path]) -> Iterator[Path]:
    """Yield all C/C++ source and header files inside `dirs`, skipping build/test folders."""
    for directory in dirs:
        for candidate in directory.rglob("*"):
            if (
                candidate.is_file()
                and candidate.suffix.lower() in CPP_EXTS
                # Check only the relative path so testing inside `tests/scenarios/...` still works.
                and IGNORED_DIRS.isdisjoint(candidate.relative_to(directory).parts)
            ):
                yield candidate


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    """Remove duplicate paths while keeping original order."""
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        key = path.resolve()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def _sort_headers_first(paths: list[Path]) -> list[Path]:
    """Sort `.h`/`.hpp` headers ahead of `.c`/`.cpp`/`.ino` files, then alphabetically."""
    return sorted(paths, key=lambda p: (0 if p.suffix.lower() in HEADER_EXTS else 1, str(p)))


# ---------------------------------------------------------------------------
# Step 2: Walk each file's Tree-Sitter AST to collect definitions & API calls
# ---------------------------------------------------------------------------

def _scan_files(files: list[Path]) -> _SourceScan:
    """Parse every C/C++ file with Tree-Sitter and record all constants and function calls."""
    parser = Parser(CPP_LANGUAGE)
    scan = _SourceScan()
    for file_path in files:
        root = parser.parse(file_path.read_bytes()).root_node
        for name, pin, line in _extract_definitions(root):
            _record_definition(scan, name, pin, file_path, line)
        for fn_name, args, line in _extract_calls(root):
            _record_call(scan, fn_name, args, file_path, line)
    return scan


def _extract_definitions(root: Node) -> list[tuple[str, int, int]]:
    """Find top-level integer constants (`#define NAME 12` and global `const int NAME = 12;`)."""
    defs: list[tuple[str, int, int]] = []
    # Skipping function bodies prevents local loop/counter variables from looking like pins.
    for node in _walk(root, skip_functions=True):
        if node.type == "preproc_def":
            name = _text(node.child_by_field_name("name")).strip()
            pin = _parse_uint(_text(node.child_by_field_name("value")))
            if name and pin is not None:
                defs.append((name, pin, node.start_point.row + 1))
        elif node.type == "declaration":
            defs.extend(_declaration_constants(node))
    return defs


def _declaration_constants(node: Node) -> Iterator[tuple[str, int, int]]:
    """Yield `(name, value, line)` pairs from one integer variable declaration node."""
    type_text = " ".join(_text(node.child_by_field_name("type")).split())
    if type_text not in PIN_VAR_TYPES:
        return
    for child in node.children:
        if child.type != "init_declarator":
            continue
        decl = child.child_by_field_name("declarator")
        val = child.child_by_field_name("value")
        if decl and val and decl.type == "identifier" and val.type == "number_literal":
            pin = _parse_uint(_text(val))
            if pin is not None:
                yield (_text(decl).strip(), pin, child.start_point.row + 1)


def _record_definition(
    scan: _SourceScan,
    name: str,
    pin: int,
    file_path: Path,
    line: int,
) -> None:
    """Save a constant definition while giving conflicting redefinitions guaranteed-unique keys."""
    seen_pins = scan.seen_values.get(name)
    if seen_pins is None:
        scan.seen_values[name] = {pin}
        key = _reserve_unique_key(name, scan.used_keys)
        scan.definitions.append(_PinDefinition(key, name, pin, file_path, line))
    elif pin not in seen_pins:
        seen_pins.add(pin)
        key = _reserve_unique_key(f"{name} ({file_path.name})", scan.used_keys)
        scan.definitions.append(_PinDefinition(key, name, pin, file_path, line))


def _extract_calls(root: Node) -> Iterator[tuple[str, list[Node], int]]:
    """Yield `(fn_name, arg_nodes, line)` for every real C/C++ call (ignoring comments/strings)."""
    for node in _walk(root):
        if node.type != "call_expression":
            continue
        fn_node = node.child_by_field_name("function")
        args_node = node.child_by_field_name("arguments")
        if fn_node and args_node:
            fn_name = re.sub(r"\s+", "", _text(fn_node))
            args = [c for c in args_node.named_children if c.type != "comment"]
            yield (fn_name, args, node.start_point.row + 1)


def _record_call(
    scan: _SourceScan,
    fn_name: str,
    args: list[Node],
    file_path: Path,
    line: int,
) -> None:
    """Record a function call and tag its pin arguments with capabilities and bus roles."""
    scan.called_functions.add(fn_name)
    for cap, bus_group, arg in _pin_args_for_call(fn_name, args):
        if arg.type == "identifier":
            ident = _text(arg).strip()
            scan.caps_by_name.setdefault(ident, set()).add(cap)
            scan.caps_by_file_and_name.setdefault((file_path, ident), set()).add(cap)
            if bus_group is not None:
                scan.bus_by_name.setdefault(ident, set()).add(bus_group)
                scan.bus_by_file_and_name.setdefault((file_path, ident), set()).add(bus_group)
        elif arg.type == "number_literal":
            pin = _parse_uint(_text(arg))
            if pin is not None:
                loc = f"{file_path.name}:{line}"
                scan.literal_uses.append(_LiteralPinUse(pin, cap, bus_group, loc))


def _pin_args_for_call(
    fn_name: str,
    args: list[Node],
) -> Iterator[tuple[str, str | None, Node]]:
    """Yield `(capability, bus_group, arg_node)` for positional pin arguments of known APIs."""
    if not args:
        return
    if fn_name in ARG0_CAPABILITIES:
        yield (ARG0_CAPABILITIES[fn_name], None, args[0])
        return

    wire_match = WIRE_CALL_RE.match(fn_name)
    if wire_match and len(args) >= 2:
        # 1-arg Wire.begin(addr) is an I2C slave address, not pin numbers.
        bus = wire_match.group(1)
        yield ("i2c", f"{bus}:sda", args[0])
        yield ("i2c", f"{bus}:scl", args[1])
        return

    spi_match = SPI_CALL_RE.match(fn_name)
    if spi_match:
        # SPI.begin(sck, miso, mosi, ss): clock/data lines share the bus; CS/SS is exclusive GPIO.
        bus = spi_match.group(1)
        for role, arg in zip(("sck", "miso", "mosi"), args[:3]):
            yield ("spi", f"{bus}:{role}", arg)
        if len(args) >= 4:
            yield ("gpio", None, args[3])
        return

    if SERIAL_CALL_RE.match(fn_name) and len(args) >= 3:
        # Serial1.begin(baud, config, rxPin, txPin): skip baud rate & serial config.
        for arg in args[2:4]:
            yield ("uart", None, arg)


# ---------------------------------------------------------------------------
# Step 3 & 4: Build PinRequests and detect active peripheral modules
# ---------------------------------------------------------------------------

def _build_pin_requests(scan: _SourceScan) -> tuple[PinRequest, ...]:
    """Combine collected definitions and direct numeric calls into solver-ready `PinRequest`s."""
    requests: list[PinRequest] = []
    used_keys = set(scan.used_keys)

    for defn in scan.definitions:
        caps, bus_group = _capabilities_and_bus_for(scan, defn)
        if not caps:
            continue  # Skip non-pin constants like BAUD_RATE or DELAY_MS
        requests.append(
            PinRequest(
                name=defn.key,
                pin=defn.pin,
                capabilities=frozenset(caps),
                bus_group=bus_group,
                location=f"{defn.source_file.name}:{defn.line}",
            )
        )

    _merge_or_append_literal_uses(requests, scan.literal_uses, used_keys)
    return tuple(requests)


def _capabilities_and_bus_for(
    scan: _SourceScan,
    defn: _PinDefinition,
) -> tuple[set[str], str | None]:
    """Infer required capabilities and optional shared-bus role for one constant definition."""
    conflicted = len(scan.seen_values.get(defn.raw_name, ())) > 1
    file_key = (defn.source_file, defn.raw_name)

    if conflicted:
        caps = set(
            scan.caps_by_file_and_name.get(file_key) or scan.caps_by_name.get(defn.raw_name, set())
        )
        bus_groups = set(
            scan.bus_by_file_and_name.get(file_key) or scan.bus_by_name.get(defn.raw_name, set())
        )
    else:
        caps = set(scan.caps_by_name.get(defn.raw_name, set()))
        bus_groups = set(scan.bus_by_name.get(defn.raw_name, set()))

    if not caps:
        inferred_cap, inferred_bus = _infer_from_name(defn.raw_name)
        if inferred_cap:
            caps.add(inferred_cap)
        if inferred_bus:
            bus_groups.add(inferred_bus)

    bus_group: str | None = None
    if len(bus_groups) == 1:
        bus_group = next(iter(bus_groups))
    elif len(bus_groups) > 1:
        # Used in conflicting bus roles (e.g. both SDA and SCL) -> cannot share with other signals.
        bus_group = f"mixed:{defn.key}"

    return caps, bus_group


def _infer_from_name(name: str) -> tuple[str | None, str | None]:
    """Fallback heuristic for pin constants not passed directly to an Arduino pin call."""
    words = [w.upper() for w in WORD_RE.findall(name)]
    if not words or words[-1] in NON_PIN_SUFFIXES:
        return None, None

    # Allow both `OLED_SDA` and `OLED_SDA_PIN` by peeking past a trailing PIN/GPIO word.
    role_word = words[-2] if len(words) >= 2 and words[-1] in ("PIN", "GPIO") else words[-1]

    if role_word == "SDA":
        return "i2c", "Wire:sda"
    if role_word == "SCL":
        return "i2c", "Wire:scl"
    if role_word == "MOSI":
        return "spi", "SPI:mosi"
    if role_word == "MISO":
        return "spi", "SPI:miso"
    if role_word in ("SCK", "SCLK"):
        return "spi", "SPI:sck"
    if role_word in ("RX", "TX", "RXD", "TXD"):
        return "uart", None
    if role_word in ("CS", "SS") or "PIN" in words or "GPIO" in words:
        return "gpio", None
    return None, None


def _merge_or_append_literal_uses(
    requests: list[PinRequest],
    literal_uses: list[_LiteralPinUse],
    used_keys: set[str],
) -> None:
    """Attach direct numeric pin calls to matching named pins, or emit new `GPIO_<n>` requests."""
    grouped: dict[tuple[int, str | None], tuple[set[str], str]] = {}
    for use in literal_uses:
        group_key = (use.pin, use.bus_group)
        if group_key not in grouped:
            grouped[group_key] = ({use.capability}, use.location)
        else:
            grouped[group_key][0].add(use.capability)

    ordered_groups = sorted(
        grouped.items(),
        key=lambda item: (item[0][0], item[0][1] or ""),
    )
    for (pin, bus_group), (caps, location) in ordered_groups:
        # If a named constant already owns this exact pin + bus role, merge extra capabilities
        # so e.g. `const int LED = 6; analogRead(6);` checks ADC on GPIO 6 without false duplicates.
        matched_idx = next(
            (i for i, req in enumerate(requests) if req.pin == pin and req.bus_group == bus_group),
            None,
        )
        if matched_idx is not None:
            existing = requests[matched_idx]
            requests[matched_idx] = PinRequest(
                name=existing.name,
                pin=existing.pin,
                capabilities=existing.capabilities | frozenset(caps),
                bus_group=existing.bus_group,
                location=existing.location,
            )
            continue

        base_name = f"GPIO_{pin}"
        if base_name in used_keys and bus_group is not None:
            base_name = f"GPIO_{pin} ({bus_group})"
        key = _reserve_unique_key(base_name, used_keys)
        requests.append(
            PinRequest(
                name=key,
                pin=pin,
                capabilities=frozenset(caps),
                bus_group=bus_group,
                location=location,
            )
        )


def _detect_active_resources(
    called_functions: set[str],
    board: BoardSpec | None,
) -> tuple[str, ...]:
    """Match called C++ functions against the board's `resource_triggers`."""
    if board is None:
        return ()
    return tuple(
        resource
        for resource, patterns in board.resource_triggers.items()
        if any(fn == pat or fn.endswith("." + pat) for pat in patterns for fn in called_functions)
    )


# ---------------------------------------------------------------------------
# Small AST & string utilities
# ---------------------------------------------------------------------------

def _reserve_unique_key(base: str, used_keys: set[str]) -> str:
    """Return `base` if unused, or append ` #2`, ` #3`, ... until globally unique."""
    if base not in used_keys:
        used_keys.add(base)
        return base
    suffix = 2
    while f"{base} #{suffix}" in used_keys:
        suffix += 1
    unique = f"{base} #{suffix}"
    used_keys.add(unique)
    return unique


def _text(node: Node | None) -> str:
    """Decode the source text of a Tree-Sitter AST node safely (tolerating non-UTF-8 comments)."""
    return node.text.decode("utf-8", errors="replace") if node and node.text else ""


def _walk(node: Node, *, skip_functions: bool = False) -> Iterator[Node]:
    """Recursively visit AST nodes, optionally skipping function bodies."""
    if skip_functions and node.type in ("function_definition", "compound_statement"):
        return
    yield node
    for child in node.children:
        yield from _walk(child, skip_functions=skip_functions)


def _parse_uint(raw: str) -> int | None:
    """Strip inline comments, outer parentheses, and integer suffixes; return a non-negative int."""
    cleaned = COMMENT_RE.sub("", raw).strip()
    while cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1].strip()
    cleaned = cleaned.rstrip("uUlL")
    return int(cleaned) if cleaned.isdigit() else None
