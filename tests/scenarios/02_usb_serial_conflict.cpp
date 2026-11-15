#include <Arduino.h>

// SCENARIO 2: USB-Serial blocks GPIO 18 and 19 on ESP32-C3 (expected: UNSAT)
#define STEP_PIN 18          // Error: GPIO 18 is USB D- (conflicts with Serial.begin)
#define DIR_PIN 19           // Error: GPIO 19 is USB D+ (conflicts with Serial.begin)
const int ENABLE_PIN = 6;    // Valid free GPIO (should be preserved by Z3)

void setup() {
    Serial.begin(115200);    // Activates 'usb_serial' -> blocks GPIO 18 & 19

    pinMode(STEP_PIN, OUTPUT);
    pinMode(DIR_PIN, OUTPUT);
    pinMode(ENABLE_PIN, OUTPUT);
}

void loop() {
    digitalWrite(STEP_PIN, HIGH);
}
