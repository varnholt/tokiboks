"""Short feedback cues (request acknowledged / request failed).

Cues run through their own mpv instance. The music instance must not be reused:
`loadfile <cue> replace` would tear down whatever album is currently playing.

Nothing in here raises — a broken cue must never stop the music from playing.
"""
from __future__ import annotations

from pathlib import Path

import mpvplayer

SOUNDS_DIR = Path(__file__).resolve().parent / "sounds"
CUE_VOLUME = 70.0

_cue_player: mpvplayer.MpvPlayer | None = None


def setup() -> None:
    """Start the cue instance up front so the first card tap doesn't pay for it."""
    _ensure_cue_player()


def play_success() -> None:
    """Acknowledge a play request that is about to start."""
    _play("success")


def play_error() -> None:
    """Signal a play request that was understood but cannot be fulfilled."""
    _play("error")


def shutdown() -> None:
    global _cue_player

    if _cue_player is None:
        return

    try:
        _cue_player.quit()
    except Exception as error:
        print(f"cue player shutdown failed: {error}")

    _cue_player = None


def _ensure_cue_player() -> mpvplayer.MpvPlayer | None:
    global _cue_player

    if _cue_player is not None and _cue_player.is_running():
        return _cue_player

    try:
        _cue_player = mpvplayer.MpvPlayer()
        _cue_player.set_volume(CUE_VOLUME)
    except Exception as error:
        # a second mpv can fail to open an exclusive audio device — cues are optional
        print(f"cue player unavailable: {error}")
        _cue_player = None

    return _cue_player


def _play(name: str) -> None:
    sound_path = SOUNDS_DIR / f"{name}.wav"

    if not sound_path.is_file():
        print(f"cue file missing: {sound_path}")
        return

    player = _ensure_cue_player()

    if player is None:
        return

    try:
        player.load(str(sound_path))
    except Exception as error:
        print(f"cue playback failed: {error}")
