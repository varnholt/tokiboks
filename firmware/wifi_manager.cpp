#include "wifi_manager.h"
#include <Arduino.h>
#include <WiFi.h>
#include "config_store.h"
#include "secrets.h"

static wl_status_t _wifi_status = WL_IDLE_STATUS;

static void start_ap_mode()
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

void wifi_setup()
{
   auto ssid = config_store_wifi_ssid();
   auto pass = config_store_wifi_password();

   if (ssid.isEmpty())
   {
      ssid = WIFI_SSID;
      pass = WIFI_PASSWORD;
   }

   if (String(ssid).isEmpty())
   {
      start_ap_mode();
      return;
   }

   WiFi.mode(WIFI_STA);
   WiFi.begin(ssid.c_str(), pass.c_str());
   Serial.print("connecting");

   for (int attempt = 0; WiFi.status() != WL_CONNECTED; ++attempt)
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
   const auto current = WiFi.status();
   if (current != _wifi_status)
   {
      _wifi_status = current;
      Serial.print("wifi status: ");
      Serial.println(static_cast<int>(_wifi_status));
   }
}
