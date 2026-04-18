import subprocess

from audioplayer import AudioAction, AudioPlayer


class Mpg123Player(AudioPlayer):
    def __init__(self, executable: str = "mpg123") -> None:
        super().__init__()
        self.process = subprocess.Popen(
            [executable, "-R", "--remote-err"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._volume_percent = 100.0

    def _send(self, command: str) -> None:
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("mpg123 process is not available")

        if self.process.poll() is not None:
            raise RuntimeError("mpg123 process is no longer running")

        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def load(self, path: str) -> None:
        self._send(f"LOAD {path}")

    def pause(self) -> None:
        self._send("PAUSE")

    def stop(self) -> None:
        self._send("STOP")

    def next(self) -> None:
        self._send("JUMP +1")

    def previous(self) -> None:
        self._send("JUMP -1")

    def action(self, action: AudioAction) -> None:
        if action == AudioAction.TOGGLE_PAUSE:
            self._send("PAUSE")
            return

        raise ValueError(f"unsupported action: {action}")

    def quit(self) -> None:
        if self.process is None:
            return

        if self.process.poll() is None:
            try:
                self._send("QUIT")
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()
                self.process.wait(timeout=2)

        self.process = None
            
    def _clamp_volume(self, volume_percent: float) -> float:
        return max(0.0, min(100.0, volume_percent))
        
    def set_volume(self, volume_percent: float) -> None:
        clamped_volume = self._clamp_volume(volume_percent)
        self._send(f"VOLUME {clamped_volume}")
        self._volume_percent = clamped_volume

    def change_volume(self, delta_percent: float) -> None:
        self.set_volume(self._volume_percent + delta_percent)

    def get_volume(self) -> float:
        return self._volume_percent