#include <Arduino.h>

// SZENARIO 2: USB-Serial blockiert GPIO 18 und 19 (Erwartung: UNSAT)
#define STEP_PIN 18          // FEHLER: GPIO 18 ist USB D- (kollidiert mit Serial.begin)
#define DIR_PIN 19           // FEHLER: GPIO 19 ist USB D+ (kollidiert mit Serial.begin)
const int ENABLE_PIN = 6;    // KORREKT: GPIO 6 ist frei und soll bleiben

void setup() {
    Serial.begin(115200);    // Aktiviert 'usb_serial' -> sperrt GPIO 18 & 19

    pinMode(STEP_PIN, OUTPUT);
    pinMode(DIR_PIN, OUTPUT);
    pinMode(ENABLE_PIN, OUTPUT);
}

void loop() {
    digitalWrite(STEP_PIN, HIGH);
}
