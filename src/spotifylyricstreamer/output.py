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
    def set_lyric_metadata(self, raw_lyrics, plain_lyrics=None):
        pass

    @abstractmethod 
    def current_progress(self, progress):
        pass

    @abstractmethod
    def current_index(self, index):
        pass 

    # --- Optional hooks: default to doing nothing so simple outputs can ignore them

    def on_state(self, state: str):
        """Playback state changed: "playing", "paused", "ended" or "idle"."""
        pass

    def on_idle(self):
        """Nothing is playing; clear any song-specific output."""
        pass

    def set_context(self, previous: str, next: str):
        """The lines before and after the current one ("" if there is none)."""
        pass

    def set_sync(self, position: float, timestamp: float, playing: bool):
        """Sync anchor: playback was at `position` seconds at unix time `timestamp`."""
        pass

    def close(self):
        """Called on shutdown."""
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

    def set_lyric_metadata(self, raw_lyrics, plain_lyrics=None):
        return

    def current_progress(self, progress):
        return

    def current_index(self, index):
        return


class MQTTOutput(OutputInterface):
    def __init__(self):
        super().__init__()

        load_dotenv()

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        # If we vanish without a clean disconnect the broker publishes this for us
        self.client.will_set("lyrics/meta/online", "false", retain=True)
        self.client.on_connect = self._on_connect
        self.client.connect(host=os.getenv("MQTT_URL"), port=int(os.getenv("MQTT_PORT")))
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        # Runs on every (re)connect
        client.publish("lyrics/meta/online", "true", retain=True)

    def _retain(self, topic, payload):
        self.client.publish(topic, payload, retain=True)

    def _clear(self, *topics):
        # An empty retained payload deletes the retained message
        for topic in topics:
            self._retain(topic, "")

    def on_lyric(self, lyric):
        self._retain("lyrics/current", lyric)

    def on_end_of_song(self):
        self._retain("lyrics/current", "[END OF SONG]")
        self.on_state("ended")

    def on_new_song(self, name, artist):
        self._retain("lyrics/meta/name", name)
        self._retain("lyrics/meta/artist", artist)
        # Don't leave the previous song's line, context or index behind
        self._clear("lyrics/current", "lyrics/previous", "lyrics/next", "lyrics/meta/index")
        self.on_state("playing")

    def on_state(self, state):
        self._retain("lyrics/meta/state", state)
        # `playing` is kept for existing consumers: true only while actually playing
        self._retain("lyrics/meta/playing", "true" if state == "playing" else "false")

    def on_idle(self):
        self._clear(
            "lyrics/current", "lyrics/previous", "lyrics/next",
            "lyrics/meta/name", "lyrics/meta/artist", "lyrics/meta/album",
            "lyrics/meta/art_url", "lyrics/meta/duration", "lyrics/meta/index",
            "lyrics/meta/plain_lyrics", "lyrics/meta/raw_song", "lyrics/meta/sync",
        )
        self._retain("lyrics/meta/has_lyrics", "false")
        self._retain("lyrics/meta/raw_lyrics", "[]")
        self._retain("lyrics/meta/lyrics_type", "none")
        self.on_state("idle")

    def on_no_lyrics_found(self):
        self._retain("lyrics/meta/has_lyrics", "false")

    def set_lyric_metadata(self, raw_lyrics, plain_lyrics=None):
        if raw_lyrics is None:
            self._retain("lyrics/meta/has_lyrics", "false")
            # Overwrite the retained values so the previous song's lyrics don't linger
            self._retain("lyrics/meta/raw_lyrics", "[]")
            self._retain("lyrics/meta/lyrics_type", "plain" if plain_lyrics else "none")
            self._retain("lyrics/meta/plain_lyrics", plain_lyrics or "")
            self._clear("lyrics/meta/sync")
            return
        self._retain("lyrics/meta/has_lyrics", "true")
        self._retain("lyrics/meta/lyrics_type", "synced")
        self._retain("lyrics/meta/plain_lyrics", "")
        self._retain("lyrics/meta/raw_lyrics", json.dumps(raw_lyrics, default=lambda o: o.total_seconds() if hasattr(o, "total_seconds") else str(o)))

    def set_song_metadata(self, song):
        self._retain("lyrics/meta/raw_song", json.dumps(song.raw))
        self._retain("lyrics/meta/album", song.album or "")
        self._retain("lyrics/meta/art_url", song.art_url or "")
        duration = song.duration_td.total_seconds()
        self._retain("lyrics/meta/duration", duration if duration else "")

    def set_context(self, previous, next):
        self._retain("lyrics/previous", previous)
        self._retain("lyrics/next", next)

    def set_sync(self, position, timestamp, playing):
        self._retain("lyrics/meta/sync", json.dumps(
            {"position": position, "timestamp": timestamp, "playing": playing}))

    def current_progress(self, progress):
        self.client.publish("lyrics/meta/progress", progress)

    def current_index(self, index):
        self._retain("lyrics/meta/index", index)

    def close(self):
        # Clean shutdown: say we're offline ourselves, since the will only fires on unclean ones
        info = self.client.publish("lyrics/meta/online", "false", retain=True)
        info.wait_for_publish(timeout=2)
        self.client.loop_stop()
        self.client.disconnect()
