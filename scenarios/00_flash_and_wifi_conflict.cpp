#include <Arduino.h>
#include <WiFi.h>

#define STATUS_LED 12        // FEHLER 1: Pin 12 ist für den Flash-Speicher reserviert!
const int SOIL_SENSOR = 5;   // FEHLER 2: Pin 5 ist ADC2 (funktioniert nicht mit Wi-Fi)!
const int RELAY_PIN = 4;     // KORREKT: Pin 4 ist frei und soll von Z3 behalten werden!

void setup() {
    Serial.begin(115200);
    WiFi.begin("MeinWLAN", "Passwort123");

    pinMode(STATUS_LED, OUTPUT);
    pinMode(RELAY_PIN, OUTPUT);
}

void loop() {
    int wert = analogRead(SOIL_SENSOR);
    digitalWrite(STATUS_LED, HIGH);
    digitalWrite(RELAY_PIN, LOW);
}
