#pragma once
#include <Arduino.h>

void api_send_rfid(const String& uid_string);
void api_send_button(int32_t button);
