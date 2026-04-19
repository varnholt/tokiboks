#include "api_client.h"
#include "buttons.h"
#include "config_store.h"
#include "rfid_reader.h"
#include "web_server.h"
#include "wifi_manager.h"

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
   for (int32_t i = 0; i < static_cast<int32_t>(pressed.size()); ++i)
   {
      if (pressed[i])
      {
         api_send_button(i);
      }
   }

   const auto uid = rfid_loop();
   if (!uid.isEmpty())
   {
      web_server_set_last_rfid(uid);

      const auto label = config_store_find_label(uid);
      if (!label.isEmpty())
      {
         api_play(label);
      }
      else
      {
         Serial.print("rfid not mapped: ");
         Serial.println(uid);
      }
   }
}
