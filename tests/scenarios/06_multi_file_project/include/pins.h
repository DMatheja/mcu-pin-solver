#pragma once

// Shared hardware pin header (parsed across files by Tree-Sitter AST)
#define STATUS_LED 12        // Conflicts with ESP32-C3 internal SPI flash
const int SOIL_SENSOR = 5;   // ADC2 pin: conflicts when another .cpp calls WiFi.begin
