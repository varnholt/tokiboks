#include <Arduino.h>
#include <HTTPClient.h>
#include "api_client.h"
#include "config_store.h"

static String BASE_URL;

void api_client_setup()
{
    BASE_URL = "http://" + config_store_server_host()
             + ":" + String(config_store_server_port()) + "/";
    Serial.print("api server: ");
    Serial.println(BASE_URL);
}

static void http_get(const String& url, const char* label)
{
    HTTPClient http;
    http.setConnectTimeout(1000);
    http.setTimeout(1000);
    http.begin(url);

    const auto start_ms = millis();
    const auto code     = http.GET();
    Serial.printf("%s  code=%d  ms=%lu\n", label, code, millis() - start_ms);

    if (code > 0) Serial.println(http.getString());
    http.end();
}

void api_play(const String& path)
{
    http_get(BASE_URL + "play?path=" + path, "play");
}

void api_send_button(int32_t button)
{
    http_get(BASE_URL + "action?id=" + String(button), "button");
}
