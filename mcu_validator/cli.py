"""Command-line interface and LLM-Modulo repair report formatter.

Entry point for humans (`mcu-validate` / `python -m mcu_validator.cli`), CI tests,
and PlatformIO (`pio_hook.py`). Ties together `board.py`, `parser.py`, and `solver.py`.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .board import BOARDS_DIR, BoardSpec, list_boards, load_board
from .parser import ParsedProject, parse_cpp
from .solver import ValidationResult, validate


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point: parse arguments, validate pins, print the report, and exit.

    Exit codes:
        0 = SAT (all pins valid)
        1 = UNSAT (hardware conflict detected — stops PlatformIO builds)
        2 = Input or configuration error (missing path, unknown board, invalid board JSON)
    """
    args = _parse_args(argv)
    boards_dir = Path(args.boards_dir) if args.boards_dir else BOARDS_DIR

    if args.list_boards:
        boards = list_boards(boards_dir)
        print("Available boards:", ", ".join(boards) if boards else "none")
        sys.exit(0)

    try:
        result, report = validate_path(
            args.path,
            args.board,
            boards_dir=boards_dir,
            include_dirs=args.include_dir,
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    print(report)
    sys.exit(0 if result.is_valid else 1)


def validate_path(
    target: str | Path,
    board_id: str = "esp32-c3",
    *,
    boards_dir: Path = BOARDS_DIR,
    include_dirs: Sequence[str | Path] = (),
) -> tuple[ValidationResult, str]:
    """Run the full 4-stage validation pipeline on a file or project folder."""
    board = load_board(board_id, boards_dir=boards_dir)
    project = parse_cpp(target, board, include_dirs=include_dirs)
    result = validate(project, board)
    return result, format_report(target, board, project, result)


def format_report(
    target: str | Path,
    board: BoardSpec,
    project: ParsedProject,
    result: ValidationResult,
) -> str:
    """Format a validation result as a terminal banner (plus LLM repair prompt on UNSAT)."""
    modules = ", ".join(project.active_resources) if project.active_resources else "none"
    pin_summary = _format_pin_summary(project)
    lines = [
        "=" * 65,
        f" Target         : {target} ({board.mcu})",
        f" Active Modules : {modules}",
        f" Checked Pins   : {pin_summary}",
        "=" * 65,
    ]

    if result.is_valid:
        if not project.requests:
            lines.append(
                " RESULT: SAT (Warning: 0 pin assignments were detected in the scanned files.)"
            )
        elif result.warnings:
            count = len(result.warnings)
            noun = "warning" if count == 1 else "warnings"
            lines.append(f" RESULT: SAT (All pins valid, with {count} hardware {noun}.)")
            lines.extend(_format_warning_section(result.warnings))
        else:
            lines.append(" RESULT: SAT (All pins valid! No hardware conflicts detected.)")
        return "\n".join(lines)

    lines.append(" RESULT: UNSAT (Hardware conflicts detected!)")
    if result.warnings:
        lines.extend(_format_warning_section(result.warnings))
    lines.extend([
        "\n--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---\n",
        f"Your C++ code for the {board.mcu} contains the following hardware errors:",
        *(f"  - {conflict}" for conflict in result.conflicts),
        *_format_repair_section(board, project, result),
        "\n-----------------------------------------------------",
    ])
    return "\n".join(lines)


def _format_warning_section(warnings: tuple[str, ...]) -> list[str]:
    """Build non-blocking hardware advisory lines (e.g. boot/strapping pin notices)."""
    if not warnings:
        return []
    return [
        "\nWarnings (non-blocking):",
        *(f"  - {warning}" for warning in warnings),
    ]


def _format_pin_summary(project: ParsedProject) -> str:
    """Render a compact pin count and preview (e.g. '3 (LED=8, SOIL=1, RELAY=4)')."""
    count = len(project.requests)
    if count == 0:
        return "0"
    preview = ", ".join(f"{req.name}={req.pin}" for req in project.requests[:6])
    if count > 6:
        preview += f", ... (+{count - 6} more)"
    return f"{count} ({preview})"


def _format_repair_section(
    board: BoardSpec,
    project: ParsedProject,
    result: ValidationResult,
) -> list[str]:
    """Build the Z3 repair lines showing which pins to keep and which to change."""
    if not result.repair_possible:
        return [
            f"\nNo valid pin assignment exists on {board.mcu}: "
            "the requested pins exceed available hardware capabilities."
        ]

    lines = ["\nPlease regenerate the code using this exact Z3-verified pin assignment:"]
    for req in project.requests:
        new_pin = result.suggested_pins[req.name]
        if req.pin == new_pin:
            lines.append(f"  - {req.name}: Keep GPIO {req.pin} (unchanged)")
        else:
            lines.append(f"  - {req.name}: Change GPIO {req.pin} -> GPIO {new_pin}")
    return lines


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="mcu-validate",
        description="Validate microcontroller pin assignments in C/C++ with Tree-Sitter + Z3.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="src",
        help="Path to a C/C++ file or project source directory (default: src).",
    )
    parser.add_argument(
        "board",
        nargs="?",
        default="esp32-c3",
        help="Target board name (matching a JSON in boards/) or direct path to a board .json file.",
    )
    parser.add_argument(
        "--boards-dir",
        default=None,
        help="Optional directory containing custom board JSON profiles.",
    )
    parser.add_argument(
        "--include-dir",
        action="append",
        default=[],
        help="Additional header directory to scan alongside the source path (repeatable).",
    )
    parser.add_argument(
        "--list-boards",
        action="store_true",
        help="List all available board profiles and exit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()
