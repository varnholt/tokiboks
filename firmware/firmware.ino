#include "wifi_manager.h"
#include "rfid_reader.h"
#include "buttons.h"
#include "api_client.h"
#include "web_server.h"

void setup()
{
    Serial.begin(115200);
    rfid_setup();
    buttons_setup();
    wifi_setup();
    web_server_setup();
}

void loop()
{
    wifi_loop();
    web_server_loop();

    std::array<bool, 4> pressed = buttons_loop();

    for (int i = 0; i < 4; i++)
    {
        if (pressed[i])
        {
            api_send_button(i);
        }
    }

    String uid = rfid_loop();

    if (uid.length() > 0)
    {
        api_send_rfid(uid);
    }
}
