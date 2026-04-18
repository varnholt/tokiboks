#include <Arduino.h>
#include <LittleFS.h>
#include "config_store.h"
#include "secrets.h"

namespace {

String _credentials_json;
String _server_json;

String read_file(const char* path)
{
    if (!LittleFS.exists(path)) { return {}; }
    auto file = LittleFS.open(path, "r");
    const auto content = file.readString();
    file.close();
    return content;
}

String json_str(const String& json, const char* key)
{
    const auto key_token = String('"') + key + '"';
    auto position = json.indexOf(key_token);
    if (position < 0) { return {}; }
    position += key_token.length();
    while (position < (int)json.length() && (json[position] == ':' || json[position] == ' ')) { ++position; }
    if (position >= (int)json.length() || json[position] != '"') { return {}; }
    ++position;
    const auto value_end = json.indexOf('"', position);
    return value_end < 0 ? String{} : json.substring(position, value_end);
}

int json_int(const String& json, const char* key)
{
    const auto key_token = String('"') + key + '"';
    auto position = json.indexOf(key_token);
    if (position < 0) { return -1; }
    position += key_token.length();
    while (position < (int)json.length() && (json[position] == ':' || json[position] == ' ')) { ++position; }
    if (position >= (int)json.length()) { return -1; }
    return json.substring(position).toInt();
}

} // namespace

void config_store_setup()
{
    if (!LittleFS.begin(true)) {
        Serial.println("config: LittleFS mount failed");
    } else {
        Serial.println("config: LittleFS mounted");
    }
    _credentials_json = read_file("/credentials.json");
    _server_json      = read_file("/server.json");
}

String config_store_wifi_ssid()      { return json_str(_credentials_json, "wifi_ssid");      }
String config_store_wifi_password()  { return json_str(_credentials_json, "wifi_password");  }
String config_store_admin_username() { return json_str(_credentials_json, "admin_username"); }
String config_store_admin_password() { return json_str(_credentials_json, "admin_password"); }

String config_store_server_host()
{
    const auto host = json_str(_server_json, "server_host");
#ifdef DEFAULT_SERVER_HOST
    return host.isEmpty() ? DEFAULT_SERVER_HOST : host;
#else
    return host;
#endif
}

int config_store_server_port()
{
    const auto port = json_int(_server_json, "server_port");
#ifdef DEFAULT_SERVER_PORT
    return port > 0 ? port : DEFAULT_SERVER_PORT;
#else
    return port > 0 ? port : 0;
#endif
}

String config_store_find_label(const String& uid)
{
    if (!LittleFS.exists("/mapping.json")) { return {}; }
    auto file = LittleFS.open("/mapping.json", "r");
    if (!file) { return {}; }
    const auto json = file.readString();
    file.close();

    const auto rfid_search_pattern = String(R"("rfid":")") + uid + '"';
    const auto rfid_position = json.indexOf(rfid_search_pattern);
    if (rfid_position < 0) { return {}; }

    const auto entry_start = json.lastIndexOf('{', rfid_position);
    const auto entry_end   = json.indexOf('}', rfid_position);
    if (entry_start < 0 || entry_end < 0) { return {}; }

    const auto entry             = json.substring(entry_start, entry_end + 1);
    const auto label_key_position = entry.indexOf(R"("label":")");
    if (label_key_position < 0) { return {}; }
    const auto label_value_start = label_key_position + 9;
    const auto label_value_end   = entry.indexOf('"', label_value_start);
    return label_value_end < 0 ? String{} : entry.substring(label_value_start, label_value_end);
}
