from spotifylyricstreamer.client import create_spotify_client
from spotifylyricstreamer.lyrics import fetch_parsed_lyrics
from spotifylyricstreamer.song import Song

import time
from datetime import timedelta

class LyricManager:

    def __init__(self):
        self.client = create_spotify_client()
        self.current_song = None
        self.is_playing = False
        self.current_lyrics = None
        self.current_lyrics_song_name = None


    def update_spotify(self):
        currently_playing = self.client.currently_playing()
        self.current_song = Song(currently_playing)
        self.is_playing = self.current_song.raw.get("is_playing", False)

        return self.current_song

    def get_lyrics(self):
        if (self.current_song is None):
            return
        if (self.current_song.name == self.current_lyrics_song_name):
            print("Song Unchanged... Skipping Lyric Refresh")
            return
        self.current_lyrics_song_name = self.current_song.name


        self.current_lyrics = fetch_parsed_lyrics(song_name=self.current_song.name, artist=self.current_song.artist)
