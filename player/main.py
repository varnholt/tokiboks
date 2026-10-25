from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import cues
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
REMOTE_SCHEMES = ("http://", "https://", "rtsp://", "rtmp://")

sleep_until = None

player = mpvplayer.MpvPlayer()


def is_playable(path):
    """Remote URLs are handed to mpv unchecked; local paths must exist."""
    if path.lower().startswith(REMOTE_SCHEMES):
        return True

    return Path(path).exists()


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

            if not path:
                print("play request without path")
                cues.play_error()

                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"path required")
                return

            if not is_playable(path):
                print(f"play request for missing path: {path}")
                cues.play_error()

                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"path not found")
                return

            print(f"play: {path}")
            cues.play_success()
            player.load(path)
            player.resume_if_paused()

            self.send_response(200)
            self.end_headers()
            self.wfile.write(path.encode("utf-8"))
            return

        if parsed.path == "/stop":
            print("stop")
            player.stop()

            # a pending sleep timer has nothing left to stop, and its fade would
            # otherwise carry a reduced volume into whatever plays next
            sleep_until = None
            player.set_volume(100)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"stopped")
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"not found")


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"listening on {HOST}:{PORT}")

    try:
        cues.setup()
        threading.Thread(target=sleep_watchdog, daemon=True).start()
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nctrl+c received, shutting down...")
    finally:
        print("stopping audio player...")
        player.quit()
        cues.shutdown()
        server.server_close()
        print("shutdown complete")