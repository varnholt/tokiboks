#pragma once
#include <Arduino.h>
#include <cstdint>

void api_client_setup();

// return the player's HTTP status code, or a negative HTTPClient error if it could not be reached
int32_t api_play(const String& path);
int32_t api_stop();

void api_send_button(int32_t button);
