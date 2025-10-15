import time
import pandas as pd
from typing import List
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def playlist_id_from_url(url: str) -> str:
    return url.split('/')[-1].split('?')[0]

def get_spotify_client(client_id, client_secret, redirect_uri, scope="playlist-read-private") -> spotipy.Spotify:
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id, client_secret=client_secret,
        redirect_uri=redirect_uri, scope=scope
    ))

def fetch_playlist_tracks(sp: spotipy.Spotify, playlist_url: str) -> pd.DataFrame:
    pid = playlist_id_from_url(playlist_url)
    items, limit, offset = [], 100, 0
    while True:
        page = sp.playlist_items(pid, additional_types=("track",), limit=limit, offset=offset)
        if not page or not page.get("items"): break
        items.extend([it for it in page["items"] if it.get("track")])
        if page.get("next") is None: break
        offset += limit
        time.sleep(0.2)
    tracks = [{
        "track_id": it["track"]["id"],
        "track_name": it["track"]["name"],
        "artist_name": ", ".join([a["name"] for a in it["track"]["artists"]]),
        "artist_ids": [a["id"] for a in it["track"]["artists"] if a.get("id")],
        "album": it["track"]["album"]["name"]
    } for it in items if it.get("track") and it["track"].get("id")]
    return pd.DataFrame(tracks)

def fetch_audio_features(sp: spotipy.Spotify, track_ids: List[str]) -> pd.DataFrame:
    rows = []
    for i in range(0, len(track_ids), 100):
        feats = sp.audio_features(track_ids[i:i+100])
        for f in feats:
            if f:
                rows.append({k: f.get(k) for k in [
                    "id","danceability","energy","valence","tempo","loudness","acousticness",
                    "instrumentalness","liveness","speechiness","key","mode","time_signature"]})
        time.sleep(0.3)
    df = pd.DataFrame(rows).rename(columns={"id":"track_id"})
    return df
