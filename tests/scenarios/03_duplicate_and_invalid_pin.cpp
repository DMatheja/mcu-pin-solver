#include <Arduino.h>

// SCENARIO 3: Duplicate pin, nonexistent pin, and missing ADC capability (expected: UNSAT)
#define BUZZER_PIN 7         // Valid pin, but collides with SERVO_PIN
#define SERVO_PIN 7          // Error 1: Duplicate assignment on GPIO 7
const int PIR_SENSOR = 32;   // Error 2: GPIO 32 does not exist on ESP32-C3
const int POTI_PIN = 6;      // Error 3: GPIO 6 has no ADC capability

void setup() {
    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(SERVO_PIN, OUTPUT);
    pinMode(PIR_SENSOR, INPUT);
}

void loop() {
    int pot = analogRead(POTI_PIN);
    digitalWrite(BUZZER_PIN, HIGH);
}
