#include "wifi_manager.h"
#include <Arduino.h>
#include <WiFi.h>
#include <cstdint>
#include "config_store.h"
#include "secrets.h"

namespace
{

wl_status_t _wifi_status = WL_IDLE_STATUS;

void start_ap_mode()
{
   constexpr auto ap_ssid = "tokiboks";
   WiFi.mode(WIFI_AP);
   WiFi.softAP(ap_ssid);  // open network, no password
   Serial.println("\nwifi: no credentials — AP mode started");
   Serial.print("connect to SSID '");
   Serial.print(ap_ssid);
   Serial.print("' then open: http://");
   Serial.println(WiFi.softAPIP());
}

}  // namespace

void wifi_setup()
{
   auto ssid = config_store_wifi_ssid();
   auto password = config_store_wifi_password();

   if (ssid.isEmpty())
   {
      ssid = WIFI_SSID;
      password = WIFI_PASSWORD;
   }

   if (ssid.isEmpty())
   {
      start_ap_mode();
      return;
   }

   WiFi.mode(WIFI_STA);
   WiFi.begin(ssid.c_str(), password.c_str());
   Serial.print("connecting");

   for (int32_t attempt = 0; WiFi.status() != WL_CONNECTED; ++attempt)
   {
      delay(500);
      Serial.print(".");
      if (attempt > 30)
      {
         start_ap_mode();
         return;
      }
   }

   Serial.println();
   Serial.println("connected");
   Serial.print("ip: ");
   Serial.println(WiFi.localIP());
}

void wifi_loop()
{
   const auto current_status = WiFi.status();
   if (current_status != _wifi_status)
   {
      _wifi_status = current_status;
      Serial.print("wifi status: ");
      Serial.println(static_cast<int32_t>(_wifi_status));
   }
}
