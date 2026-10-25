# tokiboks

A physical music player controlled by RFID cards and four colored buttons. Tap a card to start playing the album associated with it. The buttons handle playback control and a sleep timer.

The system has three parts:

- **`firmware/`** — Arduino/ESP32 firmware
- **`player/`** — Python music player, runs on a Raspberry Pi (or any host machine)
- **`labels/`** — Tool for generating printable credit-card artwork for the RFID cards

---

## Hardware

- ESP32 development board
- MFRC522 RFID reader (SPI)
- 4 push buttons (blue, red, yellow, green)
- Raspberry Pi (or any machine that can run Python and mpv)

### ESP32 wiring

| MFRC522 | ESP32 |
|---------|-------|
| SDA/SS  | 15    |
| SCK     | 14    |
| MOSI    | 13    |
| MISO    | 26    |
| RST     | 27    |
| 3.3V    | 3.3V  |
| GND     | GND   |

| Button | GPIO |
|--------|------|
| Blue   | 4    |
| Yellow | 2    |
| Red    | 16   |
| Green  | 22   |

Buttons are wired between GPIO and GND (INPUT_PULLUP, active low).

---

## Firmware

### Prerequisites

- [Arduino IDE 2.x](https://www.arduino.cc/en/software)
- ESP32 board support package (add `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json` to board manager URLs)
- Libraries (install via Library Manager): `MFRC522`

### Setup

1. Copy `firmware/secrets.h.example` to `firmware/secrets.h`:

```
cp firmware/secrets.h.example firmware/secrets.h
```

2. Edit `firmware/secrets.h` with your WiFi credentials and player IP:

```cpp
#define WIFI_SSID     "your_ssid"
#define WIFI_PASSWORD "your_password"

#define DEFAULT_SERVER_HOST "192.168.x.x"   // IP of the machine running the player
#define DEFAULT_SERVER_PORT 8000
```

`DEFAULT_SERVER_HOST` and `DEFAULT_SERVER_PORT` are compile-time fallbacks. They can be overridden at runtime via the web UI without reflashing.

3. Open `firmware/firmware.ino` in Arduino IDE, select your ESP32 board and port, and flash.

### First boot

On first boot the firmware tries to connect to WiFi using the credentials from `secrets.h`. If the connection fails or no credentials are set, it starts an open access point named **`tokiboks`**.

Connect to the `tokiboks` network and open `http://192.168.4.1/` to reach the configuration web UI. Set your WiFi credentials and hit **Save**, then **Restart device**. The device will reboot and connect to your network.

### Web UI

Once connected, the device IP is printed to serial. Open it in a browser. The web UI has three tabs:

- **Credentials** — WiFi SSID/password and admin username/password
- **Music Player** — IP address and port of the machine running the player
- **Music Mapping** — maps RFID card UIDs to file paths or URLs. Tap a card while the mapping tab is open to auto-fill the next empty row.

#### Playing from the web UI

Every mapping row has a **▶** button that plays that row on the music player, so an entry can be tested without hunting for its card. It sends whatever is currently *typed* in the row, not what was last saved — handy for trying a path before committing it. **Stop playback** in the table header stops the player.

Both go through the ESP32 (`POST /api/play?path=…`, `POST /api/stop`), which forwards to the player and passes its answer back, so the toast distinguishes the failure modes: a path the player can't find reports *path not found*, an unreachable or stopped player reports *player unreachable*.

Paths are percent-encoded before being sent, so spaces and `&` in filenames work. A `%` in a label is left as-is, so labels that were already encoded by hand keep working.

---

## Player

The player runs on a Raspberry Pi, any Linux/macOS machine, or Windows.

### Linux / Raspberry Pi

#### Prerequisites

```bash
sudo apt install mpv        # Raspberry Pi / Debian
# or: brew install mpv      # macOS
```

### Running

```bash
cd player
python main.py
```

The player listens on port `8000` by default. When the ESP32 scans an RFID card it looks up the label in the web UI mapping and sends a `GET /play?path=<label>` request to the player.

### Feedback sounds

Every `/play` request answers with a short cue before the album starts, so a card tap is never met with silence:

| Cue | When | Response |
|-----|------|----------|
| `player/sounds/success.wav` | path exists, playback starting | `200` |
| `player/sounds/error.wav` | path missing on disk | `404` |
| `player/sounds/error.wav` | request without a path | `400` |

Local paths are checked with `Path.exists()` before mpv is asked to load them — relative paths resolve against the player's working directory. Remote URLs (`http://`, `https://`, `rtsp://`, `rtmp://`) are passed through unchecked, since verifying a stream is not free.

`GET /stop` stops playback and clears any pending sleep timer, since its fade would otherwise carry a reduced volume into whatever plays next.

Cues play through a **second mpv instance** so they don't interrupt the album, which means two processes share the audio device. That works on PulseAudio/PipeWire and on ALSA's `default` (dmix) device; if a setup grabs the card exclusively, the cue instance fails to start, the player logs `cue player unavailable` and carries on without cues.

Replace either file to change the sounds — any format mpv can read works, as long as the filename stays the same. Attribution for the bundled sounds is in `player/sounds/CREDITS.md`.

### Button actions

| Button | Action          |
|--------|-----------------|
| Blue   | Pause / resume  |
| Red    | Previous track  |
| Yellow | Next track      |
| Green  | Sleep timer     |

### Auto-start with systemd

Create `/etc/systemd/system/tokiboks-player.service`:

```ini
[Unit]
Description=tokiboks music player
After=network.target sound.target

[Service]
ExecStart=/usr/bin/python /home/pi/tokiboks/player/main.py
WorkingDirectory=/home/pi/tokiboks/player
Restart=on-failure
User=pi

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable --now tokiboks-player
```

### Windows

`mpv.exe` is already bundled in `player/`. Install [Python 3.10+](https://www.python.org/downloads/) and run from the `player/` directory so Windows can find the bundled binary:

```bat
cd player
python main.py
```

#### Auto-start with Task Scheduler

1. Open **Task Scheduler** and choose **Create Basic Task**
2. Set the trigger to **When the computer starts**
3. Action: **Start a program**
   - Program: `python`
   - Arguments: `main.py`
   - Start in: `C:\path\to\tokiboks\player`
4. Under **Conditions**, uncheck "Start the task only if the computer is on AC power" if running on a laptop

---

## Labels

Tool for generating printable credit-card-sized artwork for the RFID cards. Requires [uv](https://docs.astral.sh/uv/).

```bash
cd labels
uv run create_card.py --help
```

---

## Troubleshooting

### Can't reach the web UI after a reboot

Your PC may have a stale ARP cache entry — it's sending packets to an outdated MAC address. Flush the cache to force re-resolution:

```bash
arp -d *                                    # Linux / macOS
netsh interface ip delete arpcache          # Windows (run as admin)
```

---

## Development

### Web UI

The web UI (HTML/CSS/JS) lives in `firmware/data/`. After editing those files, regenerate the embedded C header:

```bash
python tools/web_to_header.py
```

To develop the web UI without flashing:

```bash
uv run dev_server.py
```

This starts a local server at `http://localhost:8080/` that mirrors the ESP32 API using the same JSON files. Simulate an RFID scan with:

```
http://localhost:8080/test-rfid?uid=ABCD1234
```

The dev server also mirrors `/api/play` and `/api/stop`, forwarding them to whatever player is configured in the **Music Player** tab. The **▶** and **Stop playback** buttons therefore work against a real player without flashing anything.
