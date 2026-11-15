#include <Arduino.h>
#include <Wire.h>

// SCENARIO 4: Shared I2C bus (OLED + BME280 on GPIO 6/7 is valid), but STATUS_LED collides on GPIO 6
#define OLED_SDA 6           // Valid: I2C SDA shared with BME280_SDA
#define OLED_SCL 7           // Valid: I2C SCL shared with BME280_SCL
#define BME280_SDA 6         // Valid: Shared I2C bus line on GPIO 6
#define BME280_SCL 7         // Valid: Shared I2C bus line on GPIO 7
#define STATUS_LED 6         // Error: Standard GPIO cannot share GPIO 6 with I2C SDA!

void setup() {
    Wire.begin(OLED_SDA, OLED_SCL);
    pinMode(STATUS_LED, OUTPUT);
}

void loop() {
    digitalWrite(STATUS_LED, HIGH);
}
