#include <Arduino.h>
#include <HTTPClient.h>
#include "api_client.h"

static const String BASE_URL = "http://192.168.0.92:8000/";

static void http_get(const String& url, const char* label)
{
    HTTPClient http;
    http.setConnectTimeout(1000);
    http.setTimeout(1000);
    http.begin(url);

    uint32_t start_ms = millis();
    int code = http.GET();
    uint32_t elapsed_ms = millis() - start_ms;

    Serial.print(label);
    Serial.print(" http code: ");
    Serial.println(code);

    Serial.print(label);
    Serial.print(" http time ms: ");
    Serial.println(elapsed_ms);

    if (code > 0)
    {
        Serial.println(http.getString());
    }

    http.end();
}

void api_send_rfid(const String& uid_string)
{
    http_get(BASE_URL + "rfid?uid=" + uid_string, "rfid");
}

void api_send_button(int32_t button)
{
    http_get(BASE_URL + "action?id=" + String(button), "button");
}
