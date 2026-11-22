import spotipy
from spotipy.oauth2 import SpotifyPKCE, SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

SCOPE = "user-read-currently-playing"
CACHE_PATH = os.getenv("CACHE_PATH", ".cache")

def create_spotify_client(scopes=[SCOPE]) -> spotipy.Spotify:
    scope_str = " ".join(scopes)

    if not os.getenv("CLIENT_SECRET"):
        print("Authenticating using PKCE")
        auth_manager = SpotifyPKCE(
            client_id=os.getenv("CLIENT_ID"),
            redirect_uri=os.getenv("REDIRECT_URL"),
            scope=scope_str,
            cache_path=CACHE_PATH
        )
    else:
        print("Authenticating using OAuth")
        auth_manager = SpotifyOAuth(
            client_id=os.getenv("CLIENT_ID"),
            client_secret=os.getenv("CLIENT_SECRET"),
            redirect_uri=os.getenv("REDIRECT_URL"),
            scope=scope_str,
            cache_path=CACHE_PATH
        )

    # DO NOT call get_access_token() manually
    return spotipy.Spotify(auth_manager=auth_manager)
