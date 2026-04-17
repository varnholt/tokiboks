#include <Arduino.h>
#include <WebServer.h>
#include <WiFi.h>
#include "web_server.h"

static WebServer server(80);

static void handle_root()
{
    server.send(200, "text/html",
        "<!DOCTYPE html><html><head>"
        "<meta charset='utf-8'>"
        "<title>tokiboks</title>"
        "<style>body{font-family:sans-serif;display:flex;justify-content:center;"
        "align-items:center;height:100vh;margin:0;background:#1a1a2e;color:#e0e0e0;}"
        "h1{font-size:3rem;}</style>"
        "</head><body>"
        "<h1>tokiboks &#x2764;</h1>"
        "</body></html>"
    );
}

void web_server_setup()
{
    server.on("/", handle_root);
    server.begin();
    Serial.print("web server: http://");
    Serial.print(WiFi.localIP());
    Serial.println("/");
}

void web_server_loop()
{
    server.handleClient();
}
