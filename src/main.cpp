#include <Arduino.h>
#include <WiFi.h>

// Live ESP32-C3 demo sketch (Z3 status: SAT)
// Test UNSAT blocking by changing STATUS_LED to 12 (SPI flash) or SOIL_SENSOR to 5 (ADC2 + Wi-Fi).
#define STATUS_LED 8
const int SOIL_SENSOR = 1;
const int RELAY_PIN = 4;

const char* HOTSPOT_NAME = "ESP32-C3-PinSolver";
const char* HOTSPOT_PASS = "12345678";

bool ledState = false;
unsigned long counter = 0;

void setup() {
    Serial.begin(115200);
    delay(1000);

    pinMode(STATUS_LED, OUTPUT);
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, LOW);

    WiFi.mode(WIFI_AP);
    WiFi.softAP(HOTSPOT_NAME, HOTSPOT_PASS);

    Serial.println("\n=======================================================");
    Serial.println(" MCU-VALIDATOR PIPELINE ACTIVE (Z3 Check: SAT)");
    Serial.print(" Wi-Fi Hotspot Started : ");
    Serial.println(HOTSPOT_NAME);
    Serial.print(" Hotspot IP Address    : ");
    Serial.println(WiFi.softAPIP());
    Serial.println("=======================================================\n");
}

void loop() {
    ledState = !ledState;
    digitalWrite(STATUS_LED, ledState ? HIGH : LOW);

    int sensorValue = analogRead(SOIL_SENSOR);
    int connectedClients = WiFi.softAPgetStationNum();
    counter++;

    Serial.print("[Heartbeat #");
    Serial.print(counter);
    Serial.print("] Hotspot: '");
    Serial.print(HOTSPOT_NAME);
    Serial.print("' (Clients: ");
    Serial.print(connectedClients);
    Serial.print(") | LED (GPIO 8): ");
    Serial.print(ledState ? "ON " : "OFF");
    Serial.print(" | ADC1 (GPIO 1): ");
    Serial.println(sensorValue);

    delay(1000);
}
