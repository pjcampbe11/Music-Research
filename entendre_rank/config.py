import os
from dotenv import load_dotenv

load_dotenv()

GENIUS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN", "")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8080/callback")

BOOTSTRAP_ARTISTS = [a.strip() for a in os.getenv("BOOTSTRAP_ARTISTS", "").split(",") if a.strip()]
SEED_SPOTIFY_PLAYLIST_ID = os.getenv("SEED_SPOTIFY_PLAYLIST_ID", "")

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RANDOM_SEED = 42
