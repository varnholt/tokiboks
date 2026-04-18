#include <Arduino.h>
#include <LittleFS.h>
#include "config_store.h"

static String _creds;
static String _server;

static String read_file(const char* path)
{
    if (!LittleFS.exists(path)) return {};
    auto f = LittleFS.open(path, "r");
    const auto s = f.readString();
    f.close();
    return s;
}

static String json_str(const String& json, const char* key)
{
    const auto search = String('"') + key + '"';
    auto pos = json.indexOf(search);
    if (pos < 0) return {};
    pos += search.length();
    while (pos < (int)json.length() && (json[pos] == ':' || json[pos] == ' ')) ++pos;
    if (pos >= (int)json.length() || json[pos] != '"') return {};
    ++pos;
    const auto end = json.indexOf('"', pos);
    return end < 0 ? String{} : json.substring(pos, end);
}

static int json_int(const String& json, const char* key)
{
    const auto search = String('"') + key + '"';
    auto pos = json.indexOf(search);
    if (pos < 0) return -1;
    pos += search.length();
    while (pos < (int)json.length() && (json[pos] == ':' || json[pos] == ' ')) ++pos;
    if (pos >= (int)json.length()) return -1;
    return json.substring(pos).toInt();
}

void config_store_setup()
{
    if (!LittleFS.begin(true))
        Serial.println("config: LittleFS mount failed");
    else
        Serial.println("config: LittleFS mounted");
    _creds  = read_file("/credentials.json");
    _server = read_file("/server.json");
}

String config_store_wifi_ssid()      { return json_str(_creds, "wifi_ssid");      }
String config_store_wifi_password()  { return json_str(_creds, "wifi_password");  }
String config_store_admin_username() { return json_str(_creds, "admin_username"); }
String config_store_admin_password() { return json_str(_creds, "admin_password"); }

String config_store_server_host()
{
    const auto h = json_str(_server, "server_host");
    return h.isEmpty() ? "192.168.0.92" : h;
}

int config_store_server_port()
{
    const auto p = json_int(_server, "server_port");
    return p > 0 ? p : 8000;
}

String config_store_find_label(const String& uid)
{
    if (!LittleFS.exists("/mapping.json")) return {};
    auto f = LittleFS.open("/mapping.json", "r");
    if (!f) return {};
    const auto json = f.readString();
    f.close();

    const auto needle = String(R"("rfid":")") + uid + '"';
    const auto pos = json.indexOf(needle);
    if (pos < 0) return {};

    const auto entry_start = json.lastIndexOf('{', pos);
    const auto entry_end   = json.indexOf('}', pos);
    if (entry_start < 0 || entry_end < 0) return {};

    const auto entry = json.substring(entry_start, entry_end + 1);
    const auto lp_raw = entry.indexOf(R"("label":")");
    if (lp_raw < 0) return {};
    const auto lp = lp_raw + 9;
    const auto le = entry.indexOf('"', lp);
    return le < 0 ? String{} : entry.substring(lp, le);
}
