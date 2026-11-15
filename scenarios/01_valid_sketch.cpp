#include <Arduino.h>
#include <WiFi.h>

// SZENARIO 1: Komplett gültige Pinbelegung (Erwartung: SAT)
#define STATUS_LED 3         // KORREKT: Normaler GPIO (kein Strapping-Pin)
const int LIGHT_SENSOR = 0;  // KORREKT: GPIO 0 nutzt ADC1 (kompatibel mit Wi-Fi)
const int RELAY_PIN = 10;    // KORREKT: Freier Standard-GPIO

void setup() {
    Serial.begin(115200);
    WiFi.begin("MeinWLAN", "Passwort123");

    pinMode(STATUS_LED, OUTPUT);
    pinMode(RELAY_PIN, OUTPUT);
}

void loop() {
    int licht = analogRead(LIGHT_SENSOR);
    digitalWrite(STATUS_LED, HIGH);
    digitalWrite(RELAY_PIN, LOW);
}
