from client import create_spotify_client
from lyrics import fetch_parsed_lyrics
from song import Song

class LyricManager:

    def __init__(self):
        self.client = create_spotify_client()
        self.current_song = None
        self.is_playing = False
        self.current_lyrics = None
        self.current_lyrics_song = None


    def update_spotify(self):
        self.current_song = Song(self.client.currently_playing())
        self.is_playing = self.current_song.raw["is_playing"]

    def get_lyrics(self):
        if (self.current_song is None):
            return
        if (self.current_song.name == self.current_lyrics_song):
            print("Song Unchanged... Skipping Lyric Refresh")
            return
        self.current_lyrics_song = self.current_song.name
        song = self.current_song.raw

        self.current_lyrics = fetch_parsed_lyrics(song_name=song["item"]["name"], artist=song["item"]["artists"][0]["name"])

manager = LyricManager()
manager.update_spotify()
manager.get_lyrics()
manager.get_lyrics()

print(manager.current_song.name)
print(manager.current_song.artist)
print(manager.current_lyrics)