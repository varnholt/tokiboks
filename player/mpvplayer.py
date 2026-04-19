import json
import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path

from audioplayer import AudioAction, AudioPlayer


class MpvPlayer(AudioPlayer):
    def __init__(
        self,
        executable: str = "mpv",
        ipc_path: str | None = None,
    ) -> None:
        super().__init__()

        self.ipc_path = ipc_path if ipc_path is not None else self._make_ipc_path()

        self.process = subprocess.Popen(
            [
                executable,
                "--idle=yes",
                "--no-video",
                "--input-terminal=no",
                f"--input-ipc-server={self.ipc_path}",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        self._wait_for_ipc()

    def _make_ipc_path(self) -> str:
        if os.name == "nt":
            unique_name = f"mpvpipe-{os.getpid()}-{time.time_ns()}"
            return rf"\\.\pipe\{unique_name}"

        temp_dir = Path(tempfile.gettempdir())
        return str(temp_dir / f"mpv-socket-{os.getpid()}-{time.time_ns()}")

    def _wait_for_ipc(self, timeout_seconds: float = 3.0) -> None:
        start_time = time.monotonic()

        while True:
            if self.process is None:
                raise RuntimeError("mpv process is not available")

            if self.process.poll() is not None:
                raise RuntimeError("mpv exited before IPC became ready")

            try:
                self._send_command(["get_property", "idle-active"])
                return
            except Exception:
                if time.monotonic() - start_time > timeout_seconds:
                    raise RuntimeError("timed out waiting for mpv IPC")
                time.sleep(0.05)

    def _send_command(self, command: list[object]) -> dict | None:
        if self.process is None:
            raise RuntimeError("mpv process is not available")

        if self.process.poll() is not None:
            raise RuntimeError("mpv process is no longer running")

        payload = (json.dumps({"command": command}) + "\n").encode("utf-8")

        if os.name == "nt":
            return self._send_command_windows(payload)

        return self._send_command_posix(payload)

    def _send_command_posix(self, payload: bytes) -> dict | None:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            client.connect(self.ipc_path)
            client.sendall(payload)

            reader = client.makefile("rb")
            while True:
                line = reader.readline()
                if not line:
                    return None
                parsed = json.loads(line.decode("utf-8", errors="replace"))
                if "event" not in parsed:
                    return parsed
        finally:
            client.close()

    def _send_command_windows(self, payload: bytes) -> dict | None:
        import pathlib

        pipe_path = pathlib.Path(self.ipc_path)

        with pipe_path.open("r+b", buffering=0) as pipe_handle:
            pipe_handle.write(payload)
            response = pipe_handle.readline()

        if response == b"":
            return None

        return json.loads(response.decode("utf-8", errors="replace"))

    def _get_property(self, property_name: str) -> object | None:
        response = self._send_command(["get_property", property_name])

        if response is None:
            return None

        return response.get("data")

    def _clamp_volume(self, volume_percent: float) -> float:
        return max(0.0, min(100.0, volume_percent))

    def set_volume(self, volume_percent: float) -> None:
        clamped_volume = self._clamp_volume(volume_percent)
        self._send_command(["set_property", "volume", clamped_volume])

    def change_volume(self, delta_percent: float) -> None:
        current_volume = self.get_volume()
        self.set_volume(current_volume + delta_percent)

    def get_volume(self) -> float:
        value = self._get_property("volume")
        if value is None:
            raise RuntimeError("failed to get mpv volume")
        return float(value)
        
    def load(self, path: str) -> None:
        self._send_command(["loadfile", path, "replace"])

    def pause(self) -> None:
        self._send_command(["cycle", "pause"])

    def stop(self) -> None:
        self._send_command(["stop"])

    def next(self) -> None:
        self._send_command(["playlist-next"])

    def previous(self) -> None:
        self._send_command(["playlist-prev"])
       
    def resume_if_paused(self) -> None:
        paused = self._get_property("pause")

        if paused:
            self.pause()

    def action(self, action: AudioAction) -> None:
        if action == AudioAction.TOGGLE_PAUSE:
            self._send_command(["cycle", "pause"])
            return

        raise ValueError(f"unsupported action: {action}")

    def quit(self) -> None:
        if self.process is None:
            return

        if self.process.poll() is None:
            try:
                self._send_command(["quit"])
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()
                self.process.wait(timeout=2)

        if os.name != "nt":
            try:
                Path(self.ipc_path).unlink(missing_ok=True)
            except Exception:
                pass

        self.process = None