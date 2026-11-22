from spotifylyricstreamer.LyricManager import LyricManager
from spotifylyricstreamer.output import OutputInterface, TerminalOutput, MQTTOutput
from datetime import timedelta


import os
import threading
import time

running = True
new_song_event = threading.Event()
state_lock = threading.Lock()


def spotify_poller(manager: LyricManager):
    global running

    known_name = None
    while running:
        with state_lock:
            manager.update_spotify()
            name = manager.current_song.name

        if known_name is None or name != known_name:
            known_name = name
            new_song_event.set()

        time.sleep(2)


def time_elapsed(start, now) -> timedelta:
    return timedelta(seconds=now - start)


# If Spotify's reported progress differs from our own estimate by more than
# this, treat it as a seek and re-sync. Smaller differences are just noise.
RESYNC_THRESHOLD = timedelta(seconds=1)

# How often (seconds) to publish playback progress. Lines are still timed at
# ~50ms precision regardless; this only limits message volume.
PROGRESS_INTERVAL = float(os.getenv("PROGRESS_INTERVAL", "0.25"))


def is_playing(song) -> bool:
    return bool(song.raw.get("is_playing", False))


def index_for(lyrics, progress: timedelta) -> int:
    """Index of the last lyric line whose timestamp has been reached."""
    index = 0
    for i, (ts, _) in enumerate(lyrics):
        if ts > progress:
            break
        index = i
    return index


def show_line(output: OutputInterface, lyrics, index: int):
    """Publish the line at `index` along with its position and neighbours."""
    previous_line = lyrics[index - 1][1] if index > 0 else ""
    next_line = lyrics[index + 1][1] if index + 1 < len(lyrics) else ""
    output.current_index(index)
    output.set_context(previous=previous_line, next=next_line)
    output.on_lyric(lyrics[index][1])


def publish_sync(output: OutputInterface, position: timedelta, start: float, playing: bool):
    """Tell the output where playback is, with a wall-clock timestamp for that position."""
    timestamp = time.time() - (time.monotonic() - start)
    output.set_sync(position=position.total_seconds(), timestamp=timestamp, playing=playing)


def lyrics_loop(manager: LyricManager, output: OutputInterface):
    while running:
        new_song_event.wait()
        new_song_event.clear()

        with state_lock:
            song = manager.current_song
            manager.get_lyrics()
            lyrics = manager.current_lyrics
            plain_lyrics = manager.current_plain_lyrics
            base_progress = song.progress_td
            duration = song.duration_td
            # Measure elapsed time from when Spotify reported the progress,
            # not from after the (slow) lyric fetch.
            start = song.snapshot_at if song.snapshot_at is not None else time.monotonic()

        if song.name is None:
            output.on_idle()
            continue

        output.on_new_song(name=song.name, artist=song.artist)
        output.set_lyric_metadata(raw_lyrics=lyrics, plain_lyrics=plain_lyrics)
        output.set_song_metadata(song=song)

        playing = is_playing(song)
        if not playing:
            output.on_state("paused")

        if lyrics is None:
            output.on_no_lyrics_found()
            continue

        anchor = song
        publish_sync(output, base_progress, start, playing)

        current_index = index_for(lyrics, base_progress)
        show_line(output, lyrics, current_index)
        last_progress_publish = 0.0

        while not new_song_event.is_set():
            now = time.monotonic()

            # Re-sync against the newest poll (read without the lock: the poller
            # holds it during network calls and we must not stall on that).
            snap = manager.current_song
            if snap is not anchor and snap is not None and snap.name == song.name:
                anchor = snap
                snap_playing = is_playing(snap)
                reported = snap.progress_td
                expected = base_progress + time_elapsed(start, snap.snapshot_at) if playing else base_progress

                if snap_playing != playing or abs(reported - expected) > RESYNC_THRESHOLD:
                    if snap_playing != playing:
                        output.on_state("playing" if snap_playing else "paused")
                    playing = snap_playing
                    base_progress = reported
                    start = snap.snapshot_at
                    publish_sync(output, base_progress, start, playing)

                    new_index = index_for(lyrics, base_progress)
                    if new_index != current_index:
                        current_index = new_index
                        show_line(output, lyrics, current_index)

            if playing:
                current_progress = base_progress + time_elapsed(start, now)
                if now - last_progress_publish >= PROGRESS_INTERVAL:
                    last_progress_publish = now
                    output.current_progress(current_progress.total_seconds())

                next_index = current_index + 1
                if next_index < len(lyrics) and current_progress > lyrics[next_index][0]:
                    current_index = next_index
                    show_line(output, lyrics, current_index)

            if current_index == len(lyrics) - 1:
                output.on_end_of_song()
                break

            time.sleep(0.05)


def main():
    global running

    manager = LyricManager()

    api_thread = threading.Thread(target=spotify_poller, daemon=True, args=(manager,))
    api_thread.start()

    output = MQTTOutput()

    try:
        lyrics_loop(manager=manager, output=output)
    finally:
        running = False
        output.close()
        print("Finished")


if __name__ == "__main__":
    main()
