#include "config_store.h"
#include "wifi_manager.h"
#include "rfid_reader.h"
#include "buttons.h"
#include "api_client.h"
#include "web_server.h"

void setup()
{
    Serial.begin(115200);

    // mount LittleFS, cache credentials + server config
    config_store_setup();   
    rfid_setup();
    buttons_setup();

    // read WiFi credentials from config_store
    wifi_setup();           
    web_server_setup();

    // read server URL from config_store
    api_client_setup();     
}

void loop()
{
    wifi_loop();
    web_server_loop();

    const auto pressed = buttons_loop();
    for (int i = 0; i < 4; ++i) {
        if (pressed[i]) api_send_button(i);
    }

    const auto uid = rfid_loop();
    if (uid.length() > 0) {
        auto uid_upper = uid;
        uid_upper.toUpperCase();

        web_server_set_last_rfid(uid_upper);

        const auto label = config_store_find_label(uid_upper);
        if (label.length() > 0) {
            api_play(label);
        } else {
            Serial.print("rfid not mapped: ");
            Serial.println(uid_upper);
        }
    }
}
