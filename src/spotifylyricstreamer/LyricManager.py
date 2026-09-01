from client import create_spotify_client
from lyrics import fetch_parsed_lyrics
from song import Song

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
        self.current_song = Song(self.client.currently_playing())
        self.is_playing = self.current_song.raw["is_playing"]

        return self.current_song

    def get_lyrics(self):
        if (self.current_song is None):
            return
        if (self.current_song.name == self.current_lyrics_song_name):
            print("Song Unchanged... Skipping Lyric Refresh")
            return
        self.current_lyrics_song_name = self.current_song.name


        self.current_lyrics = fetch_parsed_lyrics(song_name=self.current_song.name, artist=self.current_song.artist)

manager = LyricManager()
manager.update_spotify()
manager.get_lyrics()

print(manager.current_song.name)
print(manager.current_song.artist)
print(manager.current_lyrics)


def time_elapsed(start, now) -> timedelta:
    sec_elapsed = now-start
    return timedelta(seconds=sec_elapsed)

#put in while true after testing
#new song
manager.update_spotify()
start = time.monotonic()
print("NEW SONG: ")
print(manager.current_song.name)
print(manager.current_song.artist)

manager.get_lyrics()
#find where we are in it right now
now = time.monotonic()
current_progress = manager.current_song.progress_td + time_elapsed(start=start, now=now)
current_index = 0
for i, (ts, _) in enumerate(manager.current_lyrics):
    if ts > current_progress:
        current_index = max(0, i - 1)
        break   

print(manager.current_lyrics[current_index][1])


while (current_progress < manager.current_song.duration_td):
    old_now = now
    now = time.monotonic()
    current_progress = current_progress + time_elapsed(old_now, now)
    if current_progress > manager.current_lyrics[current_index+1][0]:
        current_index += 1

        print(manager.current_lyrics[current_index][1])

    if current_index == len(manager.current_lyrics)-1:
        print("END OF SONG")
        break

    time.sleep(0.05)
