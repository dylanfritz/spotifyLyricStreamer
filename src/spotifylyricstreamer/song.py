from datetime import timedelta
class Song:
    def __init__(self, song_dict):
        self.raw = song_dict or {}
        self.name = self.raw.get("item", {}).get("name", None)
        self.artist = (self.raw.get("item", {}).get("artists", [{}])[0]).get("name", None)



        self.duration_ms = self.raw.get("item", {}).get("duration_ms", 0)
        self.progress_ms = self.raw.get("progress_ms", 0)

        self.duration_td = timedelta(milliseconds=self.duration_ms)
        self.progress_td = timedelta(milliseconds=self.progress_ms)



