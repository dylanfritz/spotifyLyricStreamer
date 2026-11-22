# Spotify Lyric Streamer

Streams the synced lyrics of whatever you're playing on Spotify to an MQTT topic, line by line, in time with the song. Handy for driving a display, smart-home dashboard, LED matrix, etc.

## How it works

1. A poller thread asks Spotify what's currently playing every 2 seconds.
2. When the song changes, lyrics are fetched as timestamped LRC via [`syncedlyrics`](https://pypi.org/project/syncedlyrics/) and parsed.
3. A loop works out which line is current from the song's progress and publishes each line as its timestamp passes.

If Spotify can't be reached, the previous song is kept so a network blip doesn't restart the lyrics.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- A Spotify app (create one at the [Spotify developer dashboard](https://developer.spotify.com/dashboard))
- An MQTT broker you can reach (e.g. Mosquitto)

## Setup

```bash
uv sync
```

Create `src/spotifylyricstreamer/.env`:

```env
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=            # optional, see below
REDIRECT_URL=http://127.0.0.1:8888/callback

MQTT_URL=localhost
MQTT_PORT=1883
```

The redirect URL must match one registered in your Spotify app settings.

**Auth:** if `CLIENT_SECRET` is empty or unset, PKCE auth is used (no secret needed). If it is set, the standard OAuth flow is used. The only scope requested is `user-read-currently-playing`. On first run a browser window opens to authorize; the token is cached in `.cache` in the directory you run from.

## Running

From the repository root:

```bash
uv run python -m spotifylyricstreamer.main
```

> The `spotifylyricstreamer` console script is currently a placeholder; run the module as above.

## MQTT topics

| Topic | Retained | Payload |
| --- | --- | --- |
| `lyrics/current` | only `[END OF SONG]` | The current lyric line. `[]` for a blank line, `[END OF SONG]` when finished |
| `lyrics/meta/name` | yes | Song title |
| `lyrics/meta/artist` | yes | Primary artist |
| `lyrics/meta/playing` | yes | `true` on new song, `false` at end of song |
| `lyrics/meta/has_lyrics` | yes | `true` / `false` |
| `lyrics/meta/raw_lyrics` | yes | JSON array of `[seconds, line]` pairs for the whole song |
| `lyrics/meta/raw_song` | yes | Raw Spotify "currently playing" JSON |
| `lyrics/meta/progress` | no | Playback position in seconds (published ~20 times a second) |
| `lyrics/meta/index` | no | Index of the current line in `raw_lyrics` |

Watch everything with:

```bash
mosquitto_sub -h localhost -t 'lyrics/#' -v
```

## Custom outputs

Output is abstracted behind `OutputInterface` in `output.py`. Two implementations ship: `MQTTOutput` (default) and `TerminalOutput`, which just prints. To use the terminal, change `MQTTOutput()` to `TerminalOutput()` in `main.py`, or subclass `OutputInterface` to send lyrics somewhere else.

## Notes and limitations

- Lyrics come from whatever providers `syncedlyrics` searches, matched by song title and first artist, so some songs won't be found or may be wrong.
- Progress is estimated locally after a song starts, so seeking within a song isn't picked up until the song changes.
- Never commit `.env` or `.cache`; both are in `.gitignore`.

## License

See [LICENSE](LICENSE).
