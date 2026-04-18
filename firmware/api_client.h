#pragma once
#include <Arduino.h>

void api_client_setup();
void api_play(const String& path);
void api_send_button(int32_t button);
