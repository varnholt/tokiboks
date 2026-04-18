# tokiboks

A physical music player controlled by RFID cards and four colored buttons. Tap a card to start playing the album associated with it. The buttons handle playback control and a sleep timer.

The system has three parts: firmware running on an ESP32, a Python music player running on a host machine, and a tool for generating printable artwork for the RFID cards.

## firmware/

Arduino/ESP32 firmware. On boot it connects to WiFi and starts a web server. It reads RFID cards and monitors four buttons, sending HTTP requests to the player whenever a card is scanned or a button is pressed.

Copy `secrets.h.example` to `secrets.h` and fill in your WiFi credentials before building.

## player/

Python HTTP server that receives playback commands from the firmware. It plays audio files using mpv. The four buttons are mapped to: pause/play (blue), previous track (red), next track (yellow), and sleep timer (green).

## labels/

Python tool for generating printable credit-card-sized artwork for the RFID cards. Takes album front/back cover images and produces images sized to the portrait credit card ratio, with an optional RFID icon, color palette bottom strip, cutting guides, and PDF output for printing.
