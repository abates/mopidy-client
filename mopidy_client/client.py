import asyncio
import json
import logging
from typing import Callable
from functools import partial

from mopidy_client import models, core
from tornado import websocket, escape, gen
from tornado.httpclient import HTTPRequest

from .callbacks import (
    MuteChanged,
    PlaybackStateChanged,
    PlaylistChanged,
    PlaylistDeleted,
    Seeked,
    StreamTitleChanged,
    TrackPlaybackChanged,
    TrackPlaybackStarted,
    VolumeChanged,
    VoidCallback,
)

_LOGGER = logging.getLogger(__name__)


class NotConnectedError(Exception):
    pass


class Client:
    _msg_id = 0

    @classmethod
    def _next_msg_id(cls):
        cls._msg_id += 1
        return cls._msg_id

    @classmethod
    async def test_connection(cls, ws_url):
        client = Client(ws_url)
        client.connect()
        return await client.version()

    def __init__(self, ws_url):
        self._ws_url = ws_url
        self._connected = False
        self._listeners = {}

        self._req = {}
        self.core = core.CoreController(self)
        self.history = core.HistoryController(self)
        self.library = core.LibraryController(self)
        self.mixer = core.MixerController(self)
        self.playback = core.PlaybackController(self)
        self.playlists = core.PlaylistsController(self)
        self.tracklist = core.TracklistController(self)

    def on_event(self, event, handler) -> Callable[[], None]:
        def unsub():
            self._listeners[event].remove(handler)

        self._listeners.setdefault(event, [])
        self._listeners[event].append(handler)

        return unsub

    def on_mute_changed(self, handler: MuteChanged) -> Callable[[], None]:
        return self.on_event("mute_changed", handler)

    def on_options_changed(self, handler: VoidCallback) -> Callable[[], None]:
        return self.on_event("options_changed", handler)

    def on_playback_state_changed(
        self, handler: PlaybackStateChanged
    ) -> Callable[[], None]:
        return self.on_event("playback_state_changed", handler)

    def on_playlist_changed(self, handler: PlaylistChanged) -> Callable[[], None]:
        return self.on_event("playlist_changed", handler)

    def on_playlist_deleted(self, handler: PlaylistDeleted) -> Callable[[], None]:
        return self.on_event("playlist_deleted", handler)

    def on_playlists_loaded(self, handler: VoidCallback) -> Callable[[], None]:
        return self.on_event("playlists_loaded", handler)

    def on_seeked(self, handler: Seeked) -> Callable[[], None]:
        return self.on_event("seeked", handler)

    def on_stream_title_changed(
        self, handler: StreamTitleChanged
    ) -> Callable[[], None]:
        return self.on_event("stream_title_changed", handler)

    def on_track_playback_ended(
        self, handler: TrackPlaybackChanged
    ) -> Callable[[], None]:
        return self.on_event("track_playback_ended", handler)

    def on_track_playback_paused(
        self, handler: TrackPlaybackChanged
    ) -> Callable[[], None]:
        return self.on_event("track_playback_paused", handler)

    def on_track_playback_resumed(
        self, handler: TrackPlaybackChanged
    ) -> Callable[[], None]:
        return self.on_event("track_playback_resumed", handler)

    def on_track_playback_started(
        self, handler: TrackPlaybackStarted
    ) -> Callable[[], None]:
        _LOGGER.debug(
            "Subscribing %s: %s", handler, asyncio.iscoroutinefunction(handler)
        )
        return self.on_event("track_playback_started", handler)

    def on_tracklist_changed(self, handler: VoidCallback) -> Callable[[], None]:
        return self.on_event("tracklist_changed", handler)

    def on_volume_changed(self, handler: VolumeChanged) -> Callable[[], None]:
        return self.on_event("volume_changed", handler)

    async def connect(self, **kwargs):
        request = HTTPRequest(self._ws_url, **kwargs)
        self._ws = await websocket.websocket_connect(
            request, on_message_callback=self.on_message
        )
        self._connected = True

    async def version(self):
        return self.core.version()

    async def dispatch(self, event, data):
        if event in self._listeners:
            _LOGGER.debug("Dispatching event %s", event)
            await asyncio.gather(
                *[listener(**data) for listener in self._listeners[event]]
            )

    def on_message(self, data):
        if not data:
            self._connected = False
            return

        escape.native_str(data)
        # TODO: catch parse exception
        message = json.loads(data, object_hook=models.model_json_decoder)
        if "jsonrpc" in message:
            if "id" in message:
                if message["id"] in self._req:
                    _LOGGER.debug(
                        "JSON-RPC Response(%d) %s", message["id"], message["result"]
                    )
                    fut = self._req.pop(message["id"])
                    fut.set_result(message["result"])
                else:
                    _LOGGER.debug(
                        "Nobody cares about JSON-RPC Response %d", message["id"]
                    )
            else:
                _LOGGER.warn("No ID set in incoming jsonrpc response")
        elif "event" in message:
            event = message.pop("event")
            asyncio.create_task(self.dispatch(event, message))
        else:
            _LOGGER.warn("Received unknown message: %s", data)

    async def call(self, method, **kwargs):
        if not self._connected:
            raise NotConnectedError("Not connected")

        data = {
            "jsonrpc": "2.0",
            "id": self._next_msg_id(),
            "method": method,
            "params": kwargs,
        }

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._req[data["id"]] = fut
        _LOGGER.debug(
            "JSON-RPC Request(%d) %s(%s)",
            data["id"],
            method,
            kwargs if bool(kwargs) else "",
        )
        await self._ws.write_message(json.dumps(data))
        result = await fut
        return result
