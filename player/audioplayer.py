import abc
import enum
import subprocess


class AudioAction(enum.IntEnum):
    TOGGLE_PAUSE = 0


class AudioPlayer(abc.ABC):
    def __init__(self) -> None:
        self.process: subprocess.Popen[str] | None = None

    @abc.abstractmethod
    def load(self, path: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def pause(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def next(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def previous(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def action(self, action: AudioAction) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def quit(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def set_volume(self, volume_percent: float) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def change_volume(self, delta_percent: float) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_volume(self) -> float:
        raise NotImplementedError
        
    @abc.abstractmethod
    def resume_if_paused(self) -> None:
        raise NotImplementedError

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def __enter__(self) -> "AudioPlayer":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.quit()