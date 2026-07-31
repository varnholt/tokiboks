#include "api_client.h"
#include <Arduino.h>
#include <HTTPClient.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include "config_store.h"

namespace
{

String base_url;

// '%' is deliberately treated as safe so labels that are already percent-encoded keep working
constexpr auto url_safe_punctuation = "-_.~/:%";

bool is_url_safe(const char character)
{
   const auto is_alphanumeric =
      (character >= 'A' && character <= 'Z') || (character >= 'a' && character <= 'z') || (character >= '0' && character <= '9');
   if (is_alphanumeric)
   {
      return true;
   }

   return strchr(url_safe_punctuation, character) != nullptr;
}

// paths and URLs reach us as free text, so spaces and '&' would otherwise corrupt the request
String url_encode(const String& value)
{
   String encoded;
   encoded.reserve(value.length() + 16);

   for (int32_t index = 0; index < static_cast<int32_t>(value.length()); ++index)
   {
      const auto character = value.charAt(index);
      if (is_url_safe(character))
      {
         encoded += character;
         continue;
      }

      char escape[4] = {};
      snprintf(escape, sizeof(escape), "%%%02X", static_cast<uint8_t>(character));
      encoded += escape;
   }

   return encoded;
}

int32_t http_get(const String& url, const char* label)
{
   HTTPClient http;
   http.setConnectTimeout(1000);
   http.setTimeout(1000);
   http.begin(url);

   const auto start_ms = millis();
   const int32_t code = http.GET();
   Serial.printf("%s  code=%d  ms=%lu\n", label, code, millis() - start_ms);

   if (code > 0)
   {
      Serial.println(http.getString());
   }
   http.end();

   return code;
}

}  // namespace

void api_client_setup()
{
   base_url = "http://" + config_store_server_host() + ":" + String(config_store_server_port()) + "/";
   Serial.print("api server: ");
   Serial.println(base_url);
}

int32_t api_play(const String& path)
{
   return http_get(base_url + "play?path=" + url_encode(path), "play");
}

int32_t api_stop()
{
   return http_get(base_url + "stop", "stop");
}

void api_send_button(int32_t button)
{
   http_get(base_url + "action?id=" + String(button), "button");
}
