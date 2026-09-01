from client import create_spotify_client

class LyricManager:

    def __init__(self):
        self.client = create_spotify_client()

manager = LyricManager()

print(manager.client.currently_playing())