import re
from pathlib import Path

DEFAULT_TRIGGERS = {
    "wifi": ["WiFi.begin", "WiFi.softAP"],
    "usb_serial": ["Serial.begin"],
}

# Extracts pin assignments, capabilities, and active peripherals from a C/C++ sketch file
def parse_cpp_file(cpp_path, board_data=None):
    code = Path(cpp_path).read_text(encoding="utf-8")
    # Strip single-line and multi-line comments
    code = re.sub(r"//.*?$", "", code, flags=re.MULTILINE)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)

    pins_in_code = {}
    for match in re.finditer(r"#define\s+(\w+)\s+(\d+)", code):
        pins_in_code[match.group(1)] = int(match.group(2))
    for match in re.finditer(r"(?:const\s+|constexpr\s+)?(?:int|uint8_t)\s+(\w+)\s*=\s*(\d+)", code):
        pins_in_code[match.group(1)] = int(match.group(2))

    # Collect arguments passed to bus initialization calls (Wire, SPI, Serial1/2)
    i2c_args = set()
    for match in re.finditer(r"Wire\d*\.(?:begin|setPins)\s*\(([^)]+)\)", code):
        i2c_args.update(arg.strip() for arg in match.group(1).split(","))

    spi_args = set()
    for match in re.finditer(r"SPI\d*\.begin\s*\(([^)]+)\)", code):
        spi_args.update(arg.strip() for arg in match.group(1).split(","))

    uart_args = set()
    for match in re.finditer(r"Serial\d+\.begin\s*\(([^)]+)\)", code):
        uart_args.update(arg.strip() for arg in match.group(1).split(","))

    requests = []
    for name, pin_number in pins_in_code.items():
        if re.search(rf"analogRead\s*\(\s*{name}\s*\)", code):
            cap = "adc"
        elif re.search(rf"(?:analogWrite|ledcAttach|ledcAttachPin)\s*\(\s*{name}\b", code):
            cap = "pwm"
        elif name in i2c_args or ("Wire." in code and re.search(r"(?:^|_)(?:SDA|SCL)(?:_|$)", name, re.IGNORECASE)):
            cap = "i2c"
        elif name in spi_args:
            cap = "spi"
        elif name in uart_args:
            cap = "uart"
        else:
            cap = "gpio"
        requests.append({"name": name, "pin": pin_number, "cap": cap})

    triggers = (board_data or {}).get("resource_triggers", DEFAULT_TRIGGERS)
    active_resources = [
        resource for resource, patterns in triggers.items()
        if any(pattern in code for pattern in patterns)
    ]

    return requests, active_resources
