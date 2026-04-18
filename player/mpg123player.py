import subprocess

from audioplayer import AudioPlayer


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
