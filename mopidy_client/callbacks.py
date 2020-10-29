from typing_extensions import Protocol
from mopidy_client import models


class MuteChanged(Protocol):
    def __call__(self, mute: bool) -> None:
        ...


class PlaybackStateChanged(Protocol):
    def __call__(self, old_state: str, new_state: str) -> None:
        ...


class PlaylistChanged(Protocol):
    def __call__(self, playlist: models.Playlist) -> None:
        ...


class PlaylistDeleted(Protocol):
    def __call__(self, uri: str) -> None:
        ...


class Seeked(Protocol):
    def __call__(self, time_position: int) -> None:
        ...


class StreamTitleChanged(Protocol):
    def __call__(self, title: str) -> None:
        ...


class TrackPlaybackStarted(Protocol):
    def __call__(self, tl_track: models.TlTrack) -> None:
        ...


class TrackPlaybackChanged(Protocol):
    def __call__(self, tl_track: models.TlTrack, time_position: int) -> None:
        ...


class VolumeChanged(Protocol):
    def __call(self, volume: int) -> None:
        ...


class VoidCallback(Protocol):
    def __call(self) -> None:
        ...
