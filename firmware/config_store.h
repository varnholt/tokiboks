#pragma once
#include <Arduino.h>

void   config_store_setup();

String config_store_wifi_ssid();
String config_store_wifi_password();
String config_store_server_host();
int    config_store_server_port();
String config_store_admin_username();
String config_store_admin_password();
String config_store_find_label(const String& uid);
