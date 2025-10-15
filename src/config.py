import os

SPOTIPY_CLIENT_ID     = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI  = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")
GENIUS_ACCESS_TOKEN   = os.getenv("GENIUS_ACCESS_TOKEN", "")
PLAYLIST_URL          = os.getenv("PLAYLIST_URL", "")
