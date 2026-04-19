from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import mpvplayer
from enum import IntEnum
import threading
import time

class ButtonId(IntEnum):
    BUTTON_BLUE = 0
    BUTTON_RED = 1
    BUTTON_YELLOW = 2
    BUTTON_GREEN = 3

HOST = "0.0.0.0"
PORT = 8000
FADE_OUT_SECONDS = 50

sleep_until = None

player = mpvplayer.MpvPlayer()


def sleep_watchdog():
    global sleep_until
    while True:
        if sleep_until and time.time() >= sleep_until:
            print("sleep timer expired -> stopping playback")
            player.pause()
            player.set_volume(100)
            sleep_until = None
        time.sleep(1)
        
        if sleep_until:    
            delta = sleep_until - time.time()
            
            if delta < FADE_OUT_SECONDS:
                player.set_volume(100.0 * (delta / FADE_OUT_SECONDS))
            else:
                player.set_volume(100.0)
                
            print(sleep_until - time.time())
            

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global sleep_until
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/action":
            action_id = query.get("id", [""])[0].strip()

            try:
                button = ButtonId(int(action_id))
            except (ValueError, KeyError):
                button = None
    
            if button == ButtonId.BUTTON_BLUE:
                print("toggle pause")
                player.pause()

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"pause toggled")
                return

            if button == ButtonId.BUTTON_YELLOW:
                print("button: YELLOW -> next track")
                player.next()
                player.resume_if_paused()
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"next track")
                return

            if button == ButtonId.BUTTON_RED:
                print("button: RED -> previous track")
                player.previous()
                player.resume_if_paused()

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"previous track")
                return
            if button == ButtonId.BUTTON_GREEN:
                sleep_until = time.time() + 1 * 60
                print("button: GREEN -> sleep timer reset to 15 minutes")
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"sleep timer")
                return
                
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"invalid action")
            return

        if parsed.path == "/play":
            path = query.get("path", [""])[0].strip()
            if path:
                player.load(path)
                player.resume_if_paused()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(path.encode("utf-8"))
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"path required")
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"not found")


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"listening on {HOST}:{PORT}")

    try:
        threading.Thread(target=sleep_watchdog, daemon=True).start()
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nctrl+c received, shutting down...")
    finally:
        print("stopping audio player...")
        player.quit()
        server.server_close()
        print("shutdown complete")