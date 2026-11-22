from spotifylyricstreamer.LyricManager import LyricManager
from spotifylyricstreamer.output import OutputInterface, TerminalOutput, MQTTOutput
from datetime import timedelta


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


def lyrics_loop(manager: LyricManager, output: OutputInterface):
    while running:
        new_song_event.wait()
        new_song_event.clear()

        with state_lock:
            song = manager.current_song
            manager.get_lyrics()
            lyrics = manager.current_lyrics
            base_progress = song.progress_td
            duration = song.duration_td
            # Measure elapsed time from when Spotify reported the progress,
            # not from after the (slow) lyric fetch.
            start = song.snapshot_at if song.snapshot_at is not None else time.monotonic()

        output.on_new_song(name=song.name, artist=song.artist)
        output.set_lyric_metadata(raw_lyrics=lyrics)
        output.set_song_metadata(song=song)

        if lyrics is None:
            output.on_no_lyrics_found()
            continue

        playing = is_playing(song)
        if not playing:
            output.on_playback_state(False)
        anchor = song

        current_index = index_for(lyrics, base_progress)
        output.on_lyric(lyrics[current_index][1])

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
                        output.on_playback_state(snap_playing)
                    playing = snap_playing
                    base_progress = reported
                    start = snap.snapshot_at

                    new_index = index_for(lyrics, base_progress)
                    if new_index != current_index:
                        current_index = new_index
                        output.current_index(current_index)
                        output.on_lyric(lyrics[current_index][1])

            if playing:
                current_progress = base_progress + time_elapsed(start, now)
                output.current_progress(current_progress.total_seconds())

                next_index = current_index + 1
                if next_index < len(lyrics) and current_progress > lyrics[next_index][0]:
                    current_index = next_index
                    output.current_index(current_index)
                    output.on_lyric(lyrics[current_index][1])

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
        print("Finished")


if __name__ == "__main__":
    main()
