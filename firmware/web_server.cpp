#include "web_server.h"
#include <Arduino.h>
#include <LittleFS.h>
#include <WebServer.h>
#include <WiFi.h>
#include "config_store.h"
#include "web_content.h"

namespace
{

WebServer server(80);
String last_rfid;

bool auth_ok()
{
   const auto username = config_store_admin_username();
   const auto password = config_store_admin_password();
   if (username.isEmpty() || password.isEmpty())
   {
      return true;
   }  // not configured yet
   if (server.authenticate(username.c_str(), password.c_str()))
   {
      return true;
   }
   server.requestAuthentication(BASIC_AUTH, "tokiboks");
   return false;
}

void serve_json(const char* path, const char* fallback)
{
   if (LittleFS.exists(path))
   {
      auto file = LittleFS.open(path, "r");
      server.streamFile(file, "application/json");
      file.close();
   }
   else
   {
      server.send(200, "application/json", fallback);
   }
}

void save_json(const char* path)
{
   const auto request_body = server.arg("plain");
   if (request_body.isEmpty())
   {
      server.send(400, "application/json", R"({"error":"empty body"})");
      return;
   }
   auto file = LittleFS.open(path, "w");
   if (!file)
   {
      server.send(500, "application/json", R"({"error":"write failed"})");
      return;
   }
   file.print(request_body);
   file.close();
   server.send(200, "application/json", R"({"ok":true})");
}

String default_mapping()
{
   String json = R"({"entries":[)";
   for (int i = 0; i < 100; ++i)
   {
      if (i > 0)
      {
         json += ',';
      }
      json += R"({"rfid":"","label":""})";
   }
   json += "]}";
   return json;
}

}  // namespace

void web_server_set_last_rfid(const String& uid)
{
   last_rfid = uid;
}

// ---- setup ----

void web_server_setup()
{
   // Static web UI (served from flash)
   server.on(
      "/",
      HTTP_GET,
      []()
      {
         if (!auth_ok())
         {
            return;
         }
         server.send(200, "text/html; charset=utf-8", WEB_HTML);
      }
   );
   server.on(
      "/style.css",
      HTTP_GET,
      []()
      {
         if (!auth_ok())
         {
            return;
         }
         server.send(200, "text/css", WEB_CSS);
      }
   );
   server.on(
      "/app.js",
      HTTP_GET,
      []()
      {
         if (!auth_ok())
         {
            return;
         }
         server.send(200, "application/javascript", WEB_JS);
      }
   );

   // Credentials
   server.on(
      "/api/credentials",
      HTTP_GET,
      []()
      {
         if (!auth_ok())
         {
            return;
         }
         serve_json("/credentials.json", R"({"wifi_ssid":"","wifi_password":"","admin_username":"admin","admin_password":"admin"})");
      }
   );
   server.on(
      "/api/credentials",
      HTTP_POST,
      []()
      {
         if (!auth_ok())
         {
            return;
         }
         save_json("/credentials.json");
      }
   );

   // Server config
   server.on(
      "/api/server-config",
      HTTP_GET,
      []()
      {
         if (!auth_ok())
         {
            return;
         }
         if (LittleFS.exists("/server.json"))
         {
            auto file = LittleFS.open("/server.json", "r");
            server.streamFile(file, "application/json");
            file.close();
         }
         else
         {
            const auto fallback_json =
               String(R"({"server_host":")") + config_store_server_host() + R"(","server_port":)" + config_store_server_port() + "}";
            server.send(200, "application/json", fallback_json);
         }
      }
   );
   server.on(
      "/api/server-config",
      HTTP_POST,
      []()
      {
         if (!auth_ok())
         {
            return;
         }
         save_json("/server.json");
      }
   );

   // Music mapping
   server.on(
      "/api/music-mapping",
      HTTP_GET,
      []()
      {
         if (!auth_ok())
         {
            return;
         }
         serve_json("/mapping.json", default_mapping().c_str());
      }
   );
   server.on(
      "/api/music-mapping",
      HTTP_POST,
      []()
      {
         if (!auth_ok())
         {
            return;
         }
         save_json("/mapping.json");
      }
   );

   // Last scanned RFID (polled by web UI every 2 s)
   server.on(
      "/api/last-rfid",
      HTTP_GET,
      []()
      {
         if (!auth_ok())
         {
            return;
         }
         server.send(200, "application/json", "{\"uid\":\"" + last_rfid + "\"}");
      }
   );

   server.on(
      "/api/restart",
      HTTP_POST,
      []()
      {
         if (!auth_ok())
         {
            return;
         }
         server.send(200, "application/json", R"({"ok":true})");
         delay(100);
         ESP.restart();
      }
   );

   server.begin();
   const auto ip_address = (WiFi.getMode() & WIFI_AP) ? WiFi.softAPIP() : WiFi.localIP();
   Serial.print("web server: http://");
   Serial.print(ip_address);
   Serial.println("/");
}

void web_server_loop()
{
   server.handleClient();
}
