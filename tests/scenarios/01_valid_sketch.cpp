#include <Arduino.h>
#include <WiFi.h>

// SCENARIO 1: Completely valid pin assignment for ESP32-C3 (expected: SAT)
#define STATUS_LED 3         // Valid normal GPIO (non-strapping)
const int LIGHT_SENSOR = 0;  // Valid ADC1 pin (compatible with active Wi-Fi)
const int RELAY_PIN = 10;    // Valid standard GPIO

void setup() {
    Serial.begin(115200);
    WiFi.begin("MyWiFi", "Password123");

    pinMode(STATUS_LED, OUTPUT);
    pinMode(RELAY_PIN, OUTPUT);
}

void loop() {
    int light = analogRead(LIGHT_SENSOR);
    digitalWrite(STATUS_LED, HIGH);
    digitalWrite(RELAY_PIN, LOW);
}
