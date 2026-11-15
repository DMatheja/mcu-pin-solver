#include <Arduino.h>
#include <WiFi.h>
#include "pins.h"

int readSoilMoisture();

void setup() {
    pinMode(STATUS_LED, OUTPUT);
    WiFi.begin("MySSID", "MyPassword");
}

void loop() {
    digitalWrite(STATUS_LED, HIGH);
    readSoilMoisture();
    delay(1000);
}
