#include <Arduino.h>
#include <WebServer.h>
#include <WiFi.h>
#include <LittleFS.h>
#include "web_server.h"
#include "web_content.h"

static WebServer server(80);
static String    last_rfid;

void web_server_set_last_rfid(const String& uid)
{
    last_rfid = uid;
}

// ---- helpers ----

static void serve_json(const char* path, const char* fallback)
{
    if (LittleFS.exists(path)) {
        auto f = LittleFS.open(path, "r");
        server.streamFile(f, "application/json");
        f.close();
    } else {
        server.send(200, "application/json", fallback);
    }
}

static void save_json(const char* path)
{
    const auto body = server.arg("plain");
    if (body.isEmpty()) {
        server.send(400, "application/json", R"({"error":"empty body"})");
        return;
    }
    auto f = LittleFS.open(path, "w");
    if (!f) {
        server.send(500, "application/json", R"({"error":"write failed"})");
        return;
    }
    f.print(body);
    f.close();
    server.send(200, "application/json", R"({"ok":true})");
}

static String default_mapping()
{
    String j = R"({"entries":[)";
    for (int i = 0; i < 100; ++i) {
        if (i > 0) j += ',';
        j += R"({"rfid":"","label":""})";
    }
    j += "]}";
    return j;
}

// ---- setup ----

void web_server_setup()
{
    // Static web UI (served from flash via PROGMEM)
    server.on("/",         HTTP_GET, []() { server.send(200, "text/html; charset=utf-8", WEB_HTML); });
    server.on("/style.css",HTTP_GET, []() { server.send(200, "text/css",                WEB_CSS);  });
    server.on("/app.js",   HTTP_GET, []() { server.send(200, "application/javascript",  WEB_JS);   });

    // Credentials
    server.on("/api/credentials", HTTP_GET, []() {
        serve_json("/credentials.json",
            R"({"wifi_ssid":"","wifi_password":"","admin_username":"admin","admin_password":"admin"})");
    });
    server.on("/api/credentials", HTTP_POST, []() { save_json("/credentials.json"); });

    // Server config
    server.on("/api/server-config", HTTP_GET, []() {
        serve_json("/server.json",
            R"({"server_host":"192.168.0.92","server_port":8000})");
    });
    server.on("/api/server-config", HTTP_POST, []() { save_json("/server.json"); });

    // Music mapping
    server.on("/api/music-mapping", HTTP_GET, []() {
        if (LittleFS.exists("/mapping.json")) {
            auto f = LittleFS.open("/mapping.json", "r");
            server.streamFile(f, "application/json");
            f.close();
        } else {
            server.send(200, "application/json", default_mapping());
        }
    });
    server.on("/api/music-mapping", HTTP_POST, []() { save_json("/mapping.json"); });

    // Last scanned RFID (polled by web UI every 2 s)
    server.on("/api/last-rfid", HTTP_GET, []() {
        server.send(200, "application/json", "{\"uid\":\"" + last_rfid + "\"}");
    });

    server.on("/api/restart", HTTP_POST, []() {
        server.send(200, "application/json", R"({"ok":true})");
        delay(100);
        ESP.restart();
    });

    server.begin();
    const auto ip = (WiFi.getMode() & WIFI_AP) ? WiFi.softAPIP() : WiFi.localIP();
    Serial.print("web server: http://");
    Serial.print(ip);
    Serial.println("/");
}

void web_server_loop()
{
    server.handleClient();
}
