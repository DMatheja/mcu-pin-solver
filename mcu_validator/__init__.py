"""Data-driven C++ AST + Z3 SMT hardware pin validator for microcontrollers."""

from .board import BoardSpec, ConflictRule, PinSpec, list_boards, load_board
from .parser import ParsedProject, PinRequest, parse_cpp
from .solver import ValidationResult, validate

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "BoardSpec",
    "ConflictRule",
    "PinSpec",
    "list_boards",
    "load_board",
    "ParsedProject",
    "PinRequest",
    "parse_cpp",
    "ValidationResult",
    "validate",
]
