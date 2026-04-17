#include <Arduino.h>
#include <WiFi.h>
#include "wifi_manager.h"
#include "secrets.h"

static const char* ssid = WIFI_SSID;
static const char* password = WIFI_PASSWORD;

static wl_status_t _wifi_status = WL_IDLE_STATUS;

void wifi_setup()
{
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    Serial.print("connecting");

    int attempt = 0;

    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
        attempt++;

        if (attempt > 30)
        {
            Serial.println(" wifi connection failed");
            ESP.restart();
        }
    }

    Serial.println();
    Serial.println("connected");
    Serial.print("Tokiboks IP is: ");
    Serial.println(WiFi.localIP());
}

void wifi_loop()
{
    wl_status_t current = WiFi.status();

    if (current != _wifi_status)
    {
        _wifi_status = current;
        Serial.print("wifi status changed to: ");
        Serial.println(static_cast<int>(_wifi_status));
    }
}
