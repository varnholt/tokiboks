#include "api_client.h"
#include <Arduino.h>
#include <HTTPClient.h>
#include <cstdint>
#include "config_store.h"

namespace
{

String base_url;

void http_get(const String& url, const char* label)
{
   HTTPClient http;
   http.setConnectTimeout(1000);
   http.setTimeout(1000);
   http.begin(url);

   const auto start_ms = millis();
   const auto code = http.GET();
   Serial.printf("%s  code=%d  ms=%lu\n", label, code, millis() - start_ms);

   if (code > 0)
   {
      Serial.println(http.getString());
   }
   http.end();
}

}  // namespace

void api_client_setup()
{
   base_url = "http://" + config_store_server_host() + ":" + String(config_store_server_port()) + "/";
   Serial.print("api server: ");
   Serial.println(base_url);
}

void api_play(const String& path)
{
   http_get(base_url + "play?path=" + path, "play");
}

void api_send_button(int32_t button)
{
   http_get(base_url + "action?id=" + String(button), "button");
}
