#include <Arduino.h>

// SZENARIO 3: Doppelbelegung, nicht existierender Pin & fehlendes ADC (Erwartung: UNSAT)
#define BUZZER_PIN 7         // KORREKT, aber doppelt vergeben mit SERVO_PIN
#define SERVO_PIN 7          // FEHLER 1: Doppelbelegung auf GPIO 7!
const int PIR_SENSOR = 32;   // FEHLER 2: GPIO 32 existiert auf dem ESP32-C3 nicht (Halluzination vom ESP32-WROOM)
const int POTI_PIN = 6;      // FEHLER 3: GPIO 6 hat keinen Analog-Digital-Wandler (kein ADC)

void setup() {
    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(SERVO_PIN, OUTPUT);
    pinMode(PIR_SENSOR, INPUT);
}

void loop() {
    int poti = analogRead(POTI_PIN);
    digitalWrite(BUZZER_PIN, HIGH);
}
