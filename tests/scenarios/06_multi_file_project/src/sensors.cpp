#include <Arduino.h>
#include "pins.h"

int readSoilMoisture() {
    return analogRead(SOIL_SENSOR);
}
