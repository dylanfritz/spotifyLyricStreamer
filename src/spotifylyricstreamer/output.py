from abc import ABC, abstractmethod
from spotifylyricstreamer.song import Song
import paho.mqtt.client as mqtt
import json

import os
from dotenv import load_dotenv


class OutputInterface(ABC):
    @abstractmethod
    def on_new_song(self, name, artist):
        pass

    @abstractmethod
    def on_lyric(self, lyric):
        pass

    @abstractmethod
    def on_no_lyrics_found(self):
        pass

    @abstractmethod
    def on_end_of_song(self):
        pass

    @abstractmethod
    def set_song_metadata(self, song: Song):
        pass

    @abstractmethod
    def set_lyric_metadata(self, raw_lyrics):
        pass

    @abstractmethod 
    def current_progress(self, progress):
        pass

    @abstractmethod
    def current_index(self, index):
        pass 



class TerminalOutput(OutputInterface):
    def on_lyric(self, lyric):
        print(lyric)

    def on_end_of_song(self):
        print("END OF SONG")

    def on_new_song(self, name, artist):
        print("\nNEW SONG: ")
        print(name)
        print(artist)

    def on_no_lyrics_found(self):
        print("COULD NOT FIND LYRICS. NO DISPLAY.")

    def set_song_metadata(self, song):
        return

    def set_lyric_metadata(self, raw_lyrics):
        return

    def current_progress(self, progress):
        return

    def current_index(self, index):
        return


class MQTTOutput(OutputInterface):
    def __init__(self):
        super().__init__()

        load_dotenv()

        self.client = mqtt.Client()
        self.client.connect(host=os.getenv("MQTT_URL"), port=int(os.getenv("MQTT_PORT")))
        self.client.loop_start()

    def on_lyric(self, lyric):
        self.client.publish("lyrics/current", lyric)

    def on_end_of_song(self):
        self.client.publish("lyrics/current", "[END OF SONG]", retain=True)
        self.client.publish("lyrics/meta/playing", "false", retain=True)

    def on_new_song(self, name, artist):
        self.client.publish("lyrics/meta/name", name, retain=True)
        self.client.publish("lyrics/meta/artist", artist, retain=True)
        self.client.publish("lyrics/meta/playing", "true", retain=True)

    def on_no_lyrics_found(self):
        self.client.publish("lyrics/meta/has_lyrics", "false", retain=True)

    def set_lyric_metadata(self, raw_lyrics):
        if raw_lyrics is None:
            self.client.publish("lyrics/meta/has_lyrics", "false", retain=True)
            return
        self.client.publish("lyrics/meta/has_lyrics", "true", retain=True)
        self.client.publish("lyrics/meta/raw_lyrics", json.dumps(raw_lyrics, default=lambda o: o.total_seconds() if hasattr(o, "total_seconds") else str(o)), retain=True)

    def set_song_metadata(self, song):
        self.client.publish("lyrics/meta/raw_song", json.dumps(song.raw), retain=True)

    def current_progress(self, progress):
        self.client.publish("lyrics/meta/progress", progress)

    def current_index(self, index):
        self.client.publish("lyrics/meta/index", index)
