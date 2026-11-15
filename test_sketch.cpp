#include <Arduino.h>
#include <WiFi.h>

// ============================================================================
// LIVE-HARDWARE-TEST FÜR DEN ESP32-C3 (Z3-Status: SAT -> Kompiliert & Lädt hoch!)
//
// So testest du den Z3-Türsteher (UNSAT):
//   - Ändere testweise STATUS_LED von 8 auf 12 (verbotener SPI-Flash-Pin)
//   - ODER ändere SOIL_SENSOR von 1 auf 5 (ADC2 kollidiert mit Wi-Fi-Hotspot)
//   -> Klicke dann auf Build (✓): Z3 stoppt den Compiler sofort!
// ============================================================================

#define STATUS_LED 8         // KORREKT: Eingebaute LED auf den meisten ESP32-C3 Boards (GPIO 8)
const int SOIL_SENSOR = 1;   // KORREKT: GPIO 1 nutzt ADC1 (funktioniert gleichzeitig mit Wi-Fi!)
const int RELAY_PIN = 4;     // KORREKT: Freier Standard-GPIO

const char* HOTSPOT_NAME = "ESP32-C3-PinSolver";
const char* HOTSPOT_PASS = "12345678"; // Mindestens 8 Zeichen für WPA2

bool ledState = false;
unsigned long counter = 0;

void setup() {
    Serial.begin(115200);
    delay(1000);

    pinMode(STATUS_LED, OUTPUT);
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, LOW);

    // Wi-Fi Access Point (Hotspot) starten
    WiFi.mode(WIFI_AP);
    WiFi.softAP(HOTSPOT_NAME, HOTSPOT_PASS);

    Serial.println("\n=======================================================");
    Serial.println(" MCU-VALIDATOR PIPELINE AKTIV (Z3-Check: SAT)");
    Serial.print(" WLAN-Hotspot gestartet : ");
    Serial.println(HOTSPOT_NAME);
    Serial.print(" Hotspot IP-Adresse     : ");
    Serial.println(WiFi.softAPIP());
    Serial.println("=======================================================\n");
}

void loop() {
    ledState = !ledState;
    digitalWrite(STATUS_LED, ledState ? HIGH : LOW);

    int sensorWert = analogRead(SOIL_SENSOR);
    int verbundeneGeraete = WiFi.softAPgetStationNum();
    counter++;

    Serial.print("[Heartbeat #");
    Serial.print(counter);
    Serial.print("] Hotspot: '");
    Serial.print(HOTSPOT_NAME);
    Serial.print("' (Clients: ");
    Serial.print(verbundeneGeraete);
    Serial.print(") | LED (GPIO 8): ");
    Serial.print(ledState ? "AN " : "AUS");
    Serial.print(" | ADC1 (GPIO 1): ");
    Serial.println(sensorWert);

    delay(1000);
}
