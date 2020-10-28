import asyncio
import json
import logging

from mopidy_client import models, core
from pubsub import pub
from tornado import websocket, escape
from tornado.httpclient import HTTPRequest

_LOGGER = logging.getLogger(__name__)

class NotConnectedError(Exception):
    pass

class Client:
    _msg_id = 0

    @classmethod
    def _next_msg_id(cls):
        cls._msg_id += 1
        return cls._msg_id

    def __init__(self, ws_url):
        self._ws_url = ws_url
        self._connected = False

        self._req = {}
        self.history = core.HistoryController(self)
        self.library = core.LibraryController(self)
        self.mixer = core.MixerController(self)
        self.playback = core.PlaybackController(self)
        self.playlists = core.PlaylistsController(self)
        self.tracklist = core.TracklistController(self)

    async def connect(self, **kwargs):
        request = HTTPRequest(self._ws_url, **kwargs)
        self._ws = await websocket.websocket_connect(request, on_message_callback=self.on_message)
        _LOGGER.debug("WS: %s", self._ws.selected_subprotocol)
        self._connected = True

    def on_message(self, data):
        if not data:
            self._connected = False
            return

        _LOGGER.debug("Received message %s", data)
        escape.native_str(data)
        # TODO: catch exception
        message = json.loads(data, object_hook=models.model_json_decoder)
        if "jsonrpc" in message:
            if "id" in message:
                if message["id"] in self._req:
                    fut = self._req.pop(message["id"])
                    fut.set_result(message["result"])
            else:
                _LOGGER.warn("No ID set in incoming jsonrpc response")
        elif "event" in message:
            event = msg_data.pop('event')
            pub.sendMessage(event, **msg_data)
        else:
            _LOGGER.warn("Received unknown message: %s", data)


    async def call(self, method, **kwargs):
        if not self._connected:
            raise NotConnectedError("Not connected")

        data = {
                'jsonrpc': '2.0',
                'id': self._next_msg_id(),
                'method': method,
                'params': kwargs,
        }

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._req[data['id']] = fut
        _LOGGER.debug("Sending %s", json.dumps(data))
        await self._ws.write_message(json.dumps(data))
        _LOGGER.debug("SENT")
        result = await fut
        return result

