import re
from pathlib import Path

# Extracts pin assignments and active peripherals from a C/C++ sketch file
def parse_cpp_file(cpp_path):
    code = Path(cpp_path).read_text(encoding="utf-8")
    # Strip single-line and multi-line comments
    code = re.sub(r"//.*?$", "", code, flags=re.MULTILINE)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)

    pins_in_code = {}
    # Match #define PIN_NAME 12
    for match in re.finditer(r"#define\s+(\w+)\s+(\d+)", code):
        pins_in_code[match.group(1)] = int(match.group(2))
    # Match int / const int / uint8_t / constexpr declarations
    for match in re.finditer(r"(?:const\s+|constexpr\s+)?(?:int|uint8_t)\s+(\w+)\s*=\s*(\d+)", code):
        pins_in_code[match.group(1)] = int(match.group(2))

    requests = []
    for name, pin_number in pins_in_code.items():
        if re.search(rf"analogRead\s*\(\s*{name}\s*\)", code):
            cap = "adc"
        elif re.search(rf"(?:analogWrite|ledcAttach|ledcAttachPin)\s*\(\s*{name}\b", code):
            cap = "pwm"
        else:
            cap = "gpio"
        requests.append({"name": name, "pin": pin_number, "cap": cap})

    active_resources = []
    if "WiFi.begin" in code or "WiFi.softAP" in code:
        active_resources.append("wifi")
    if "Serial.begin" in code:
        active_resources.append("usb_serial")

    return requests, active_resources
