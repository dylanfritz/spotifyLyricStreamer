from datetime import timedelta
class Song:
    def __init__(self, song_dict):
        self.raw = song_dict
        self.name = song_dict["item"]["name"]
        self.artist = song_dict["item"]["artists"][0]["name"]


        self.duration_ms = song_dict["item"]["duration_ms"]
        self.progress_ms = song_dict["progress_ms"]

        self.duration_td = timedelta(milliseconds=self.duration_ms)
        self.progress_td = timedelta(milliseconds=self.progress_ms)
