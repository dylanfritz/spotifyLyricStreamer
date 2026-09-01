from lyrics import fetch_parsed_lyrics
class Song:
    def __init__(self, song_dict):
        self.raw = song_dict
        self.name = song_dict["item"]["name"]
        self.artist = song_dict["item"]["artists"][0]["name"]
