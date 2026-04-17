#pragma once
#include <Arduino.h>

void rfid_setup();
String rfid_loop(); // returns UID string if a new card is detected, empty string otherwise
