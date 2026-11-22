from datetime import timedelta

class Song:
    def __init__(self, song_dict):
        if not isinstance(song_dict, dict):
            song_dict = {}
        self.raw = song_dict
        # "item" is None for ads / some podcasts, "artists" can be empty
        item = self.raw.get("item") or {}
        artists = item.get("artists") or [{}]

        self.name = item.get("name", None)
        self.artist = artists[0].get("name", None)

        self.duration_ms = item.get("duration_ms", 0)
        self.progress_ms = self.raw.get("progress_ms", 0)

        self.duration_td = timedelta(milliseconds=self.duration_ms)
        self.progress_td = timedelta(milliseconds=self.progress_ms)
