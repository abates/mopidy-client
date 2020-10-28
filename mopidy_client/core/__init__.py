class BaseController:
    def __init__(self, name, client):
        self._name = name
        self._client = client

    def call(self, method, **kwargs):
        method = f"core.{self._name}.{method}"
        return self._client.call(method, **kwargs) 

    def __getattr__(self, method_name, **kwargs):
        def meth(self, **kwargs):
            return self.call(method_name, **kwargs)

        return meth.__get__(self)

class HistoryController(BaseController):
    def __init__(self, client):
        super().__init__("history", client)

class LibraryController(BaseController):
    def __init__(self, client):
        super().__init__("library", client)

class MixerController(BaseController):
    def __init__(self, client):
        super().__init__("mixer", client)

class PlaybackController(BaseController):
    def __init__(self, client):
        super().__init__("playback", client)

class PlaylistsController(BaseController):
    def __init__(self, client):
        super().__init__("playlists", client)

class TracklistController(BaseController):
    def __init__(self, client):
        super().__init__("tracklist", client)
