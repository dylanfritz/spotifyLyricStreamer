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

# Optional: seconds between progress messages (default 0.25)
# PROGRESS_INTERVAL=0.25
```

The redirect URL must match one registered in your Spotify app settings.

**Auth:** if `CLIENT_SECRET` is empty or unset, PKCE auth is used (no secret needed). If it is set, the standard OAuth flow is used. The only scope requested is `user-read-currently-playing`. On first run a browser window opens to authorize; the token is cached in `.cache` in the directory you run from.

## Running

From the repository root:

```bash
uv run python -m spotifylyricstreamer.main
```

> The `spotifylyricstreamer` console script is currently a placeholder; run the module as above.

## Docker

The repo includes a `Dockerfile` and a `docker-compose.yml`. The container joins an existing external Docker network, named by `MQTT_NETWORK` in your `.env` (default `mqtt-net`), so it can reach your MQTT broker by name. Use the network your broker's container is attached to. The app only makes outbound connections, so it publishes no ports.

1. **Authenticate on the host first.** The Spotify login needs a browser, which a container doesn't have. Run the app once locally as described above, so a token cache (`.cache`) is created.
2. **Create `.env` next to `docker-compose.yml`:**

   ```env
   CLIENT_ID=your_spotify_client_id
   CLIENT_SECRET=            # optional
   REDIRECT_URL=http://127.0.0.1:8888/callback

   MQTT_URL=your-mqtt-broker # the broker's container name on the shared network
   MQTT_PORT=1883
   MQTT_NETWORK=mqtt-net     # name of the existing Docker network the broker is on
   ```

3. **Provide the token cache.** Copy it into the mounted data directory:

   ```bash
   mkdir -p data && cp .cache data/.cache
   ```

   The container reads and refreshes the token at `/data/.cache` (set with the `CACHE_PATH` environment variable; it defaults to `.cache` outside Docker). If the token is ever revoked, authenticate on the host again and replace `data/.cache`.
4. **Start it:**

   ```bash
   docker compose up -d --build
   docker compose logs -f
   ```

To update: `git pull && docker compose up -d --build`.

If the broker isn't up when the container starts, the app exits and `restart: unless-stopped` brings it back. Running the app locally while the container is up makes both publish to the same topics.

## MQTT topics

All topics are retained unless noted. Topics that don't apply (for example when nothing is playing) are cleared.

| Topic | Payload |
| --- | --- |
| `lyrics/current` | The current lyric line. `[]` for a blank line, `[END OF SONG]` when finished |
| `lyrics/previous` | The line before the current one (empty at the start) |
| `lyrics/next` | The line after the current one (empty at the end) |
| `lyrics/meta/online` | `true` while the app is connected, `false` after a shutdown or crash (MQTT Last Will) |
| `lyrics/meta/state` | `playing`, `paused`, `ended` or `idle` (nothing playing) |
| `lyrics/meta/playing` | `true` only while `state` is `playing` |
| `lyrics/meta/name` | Song title |
| `lyrics/meta/artist` | Primary artist |
| `lyrics/meta/album` | Album name |
| `lyrics/meta/art_url` | Album art image URL (largest available) |
| `lyrics/meta/duration` | Song length in seconds |
| `lyrics/meta/has_lyrics` | `true` if timestamped lyrics were found, otherwise `false` |
| `lyrics/meta/lyrics_type` | `synced` (timestamped), `plain` (text only, see `plain_lyrics`) or `none` |
| `lyrics/meta/plain_lyrics` | Untimed lyrics text, only when `lyrics_type` is `plain` |
| `lyrics/meta/raw_lyrics` | JSON array of `[seconds, line]` pairs for the whole song (`[]` if none) |
| `lyrics/meta/index` | Index of the current line in `raw_lyrics` |
| `lyrics/meta/sync` | `{"position": seconds, "timestamp": unix_time, "playing": bool}`, published on song start, pause, resume and seek |
| `lyrics/meta/raw_song` | Raw Spotify "currently playing" JSON |
| `lyrics/meta/progress` | Playback position in seconds. Not retained, published only while playing (every 0.25s by default) |

**Following along without `progress`:** take the latest `sync` message and, while `playing` is true, compute `position + (now - timestamp)`. This needs only a message on each pause or seek, rather than several a second.

Watch everything with:

```bash
mosquitto_sub -h localhost -t 'lyrics/#' -v
```

## Custom outputs

Output is abstracted behind `OutputInterface` in `output.py`. Two implementations ship: `MQTTOutput` (default) and `TerminalOutput`, which just prints. To use the terminal, change `MQTTOutput()` to `TerminalOutput()` in `main.py`, or subclass `OutputInterface` to send lyrics somewhere else. Only the original methods are required; hooks such as `on_state`, `on_idle`, `set_context`, `set_sync` and `close` are optional and do nothing by default.

## Notes and limitations

- Lyrics come from whatever providers `syncedlyrics` searches, matched by song title and first artist, so some songs won't be found or may be wrong. Songs with only untimed lyrics are published as `plain_lyrics` but not streamed line by line.
- Progress is estimated locally between Spotify polls (every 2 seconds). Pausing, resuming and seeking are picked up on the next poll, so expect up to ~2 seconds of lag before the lyrics freeze or jump.
- Never commit `.env` or `.cache`; both are in `.gitignore`.

## License

See [LICENSE](LICENSE).

## AI Disclosure

Main code and architecture were handwritten by me. Used Claude for bugchecking, documentation, and deployment. 
