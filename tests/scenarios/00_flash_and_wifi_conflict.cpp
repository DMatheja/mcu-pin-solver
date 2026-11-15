#include <Arduino.h>
#include <WiFi.h>

// SCENARIO 0: Reserved SPI flash pin + ADC2/Wi-Fi conflict on ESP32-C3 (valid on ESP32-S3)
#define STATUS_LED 12        // ESP32-C3 error: internal SPI flash (valid GPIO on ESP32-S3)
const int SOIL_SENSOR = 5;   // ESP32-C3 error: ADC2 conflicts with Wi-Fi (ADC1 on ESP32-S3)
const int RELAY_PIN = 4;     // Valid standard GPIO on both MCUs

void setup() {
    Serial.begin(115200);
    WiFi.begin("MyWiFi", "Password123");

    pinMode(STATUS_LED, OUTPUT);
    pinMode(RELAY_PIN, OUTPUT);
}

void loop() {
    int reading = analogRead(SOIL_SENSOR);
    digitalWrite(STATUS_LED, HIGH);
    digitalWrite(RELAY_PIN, LOW);
}
