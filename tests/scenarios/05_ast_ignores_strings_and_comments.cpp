#include <Arduino.h>

// SCENARIO 5: AST parser test - WiFi.begin only appears in comments and strings!
// A naive regex/substring parser would falsely detect 'wifi' as active and reject GPIO 5 (ADC2).
// Because WiFi is NOT actually called in the AST, GPIO 5 (ADC2) is completely valid here (SAT).
// WiFi.begin("FakeCommentWiFi", "12345678");

const int SOIL_SENSOR = 5;   // Valid ADC2 pin when Wi-Fi is not active

void setup() {
    Serial.println("Note: Do not call WiFi.begin() when reading ADC2 on GPIO 5");
}

void loop() {
    int reading = analogRead(SOIL_SENSOR);
}
