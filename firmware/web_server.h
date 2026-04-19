#pragma once
#include <Arduino.h>

void web_server_setup();
void web_server_loop();
void web_server_set_last_rfid(const String& uid);
