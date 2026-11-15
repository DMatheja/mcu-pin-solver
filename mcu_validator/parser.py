import re
from pathlib import Path
import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser

CPP_LANGUAGE = Language(tscpp.language())
AST_PARSER = Parser(CPP_LANGUAGE)

DEFAULT_TRIGGERS = {
    "wifi": ["WiFi.begin", "WiFi.softAP"],
    "usb_serial": ["Serial.begin"],
}

def _node_text(node):
    return node.text.decode("utf-8") if node else ""

def _walk_ast(node):
    yield node
    for child in node.children:
        yield from _walk_ast(child)

# Extracts pin assignments, capabilities, and active peripherals using a C/C++ Abstract Syntax Tree (AST)
def parse_cpp_file(cpp_path, board_data=None):
    source_bytes = Path(cpp_path).read_bytes()
    tree = AST_PARSER.parse(source_bytes)

    pins_in_code = {}
    call_expressions = []

    for node in _walk_ast(tree.root_node):
        # 1. Preprocessor macro definitions: #define PIN_NAME 12
        if node.type == "preproc_def":
            name_node = node.child_by_field_name("name")
            val_node = node.child_by_field_name("value")
            if name_node and val_node:
                val_str = re.sub(r"//.*|/\*.*?\*/", "", _node_text(val_node), flags=re.DOTALL).strip()
                if val_str.isdigit():
                    pins_in_code[_node_text(name_node).strip()] = int(val_str)

        # 2. Pin variable declarations: const int / uint8_t / constexpr PIN_NAME = 12;
        elif node.type == "declaration" and node.parent and node.parent.type != "for_statement":
            type_node = node.child_by_field_name("type")
            if _node_text(type_node).strip() in ("int", "uint8_t"):
                for child in node.children:
                    if child.type == "init_declarator":
                        decl_node = child.child_by_field_name("declarator")
                        val_node = child.child_by_field_name("value")
                        if decl_node and val_node and decl_node.type == "identifier" and val_node.type == "number_literal":
                            val_str = _node_text(val_node).strip()
                            if val_str.isdigit():
                                pins_in_code[_node_text(decl_node).strip()] = int(val_str)

        # 3. Function & method calls: e.g. analogRead(PIN), Wire.begin(SDA, SCL), WiFi.begin(...)
        elif node.type == "call_expression":
            fn_node = node.child_by_field_name("function")
            args_node = node.child_by_field_name("arguments")
            if fn_node and args_node:
                fn_name = re.sub(r"\s+", "", _node_text(fn_node))
                arg_ids = [
                    _node_text(child).strip()
                    for child in _walk_ast(args_node)
                    if child.type == "identifier"
                ]
                call_expressions.append((fn_name, arg_ids))

    # Classify pin capabilities from AST call expressions
    adc_pins, pwm_pins, i2c_pins, spi_pins, uart_pins = set(), set(), set(), set(), set()
    called_functions = set()

    for fn_name, arg_ids in call_expressions:
        called_functions.add(fn_name)
        if fn_name == "analogRead":
            adc_pins.update(arg_ids)
        elif fn_name in ("analogWrite", "ledcAttach", "ledcAttachPin"):
            pwm_pins.update(arg_ids)
        elif re.match(r"^Wire\d*\.(?:begin|setPins)$", fn_name):
            i2c_pins.update(arg_ids)
        elif re.match(r"^SPI\d*\.begin$", fn_name):
            spi_pins.update(arg_ids)
        elif re.match(r"^Serial\d+\.begin$", fn_name):
            uart_pins.update(arg_ids)

    wire_used = any(fn.startswith("Wire") for fn in called_functions)

    requests = []
    for name, pin_number in pins_in_code.items():
        if name in adc_pins:
            cap = "adc"
        elif name in pwm_pins:
            cap = "pwm"
        elif name in i2c_pins or (wire_used and re.search(r"(?:^|_)(?:SDA|SCL)(?:_|$)", name, re.IGNORECASE)):
            cap = "i2c"
        elif name in spi_pins:
            cap = "spi"
        elif name in uart_pins:
            cap = "uart"
        else:
            cap = "gpio"
        requests.append({"name": name, "pin": pin_number, "cap": cap})

    # Match active peripheral triggers against actual AST function calls
    triggers = (board_data or {}).get("resource_triggers", DEFAULT_TRIGGERS)
    active_resources = [
        resource for resource, patterns in triggers.items()
        if any(
            any(fn == pat or fn.endswith("." + pat) for fn in called_functions)
            for pat in patterns
        )
    ]

    return requests, active_resources
