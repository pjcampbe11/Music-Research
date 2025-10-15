import argparse
import time
import pandas as pd
from typing import List, Dict
from tqdm import tqdm
import lyricsgenius
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from .config import GENIUS_TOKEN, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, BOOTSTRAP_ARTISTS, SEED_SPOTIFY_PLAYLIST_ID

def sp_client():
    scope = "playlist-modify-public playlist-modify-private user-library-read"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope
    ))

def genius_client():
    if not GENIUS_TOKEN:
        raise RuntimeError("GENIUS_ACCESS_TOKEN not set")
    return lyricsgenius.Genius(GENIUS_TOKEN, timeout=10, skip_non_songs=True, remove_section_headers=True)

def bootstrap_tracks(sp, artists: List[str], seed_playlist_id: str="", limit:int=50) -> List[Dict]:
    tracks = []
    if seed_playlist_id:
        results = sp.playlist_items(seed_playlist_id, additional_types=("track",), limit=50)
        while results:
            for it in results["items"]:
                tr = it.get("track")
                if tr and tr.get("id"):
                    if any("rap" in (g or "").lower() for g in tr.get("artists", [{}])):
                        tracks.append(tr)
                    else:
                        tracks.append(tr)  # keep broad; we'll filter later
            results = sp.next(results) if results.get("next") else None

    for artist in artists:
        res = sp.search(q=f"artist:{artist}", type="track", limit=limit)
        tracks.extend([t for t in res["tracks"]["items"]])

    # unique by (name, artist)
    seen = set()
    uniq = []
    for t in tracks:
        key = (t["name"], ", ".join([a["name"] for a in t["artists"]]))
        if key not in seen:
            seen.add(key)
            uniq.append(t)
    return uniq

def fetch_lyrics(genius, song_title: str, primary_artist: str):
    try:
        song = genius.search_song(song_title, primary_artist)
        if song and song.lyrics:
            return song.lyrics
    except Exception:
        return None
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artists", type=str, default=",".join(BOOTSTRAP_ARTISTS))
    ap.add_argument("--seed-playlist-id", type=str, default=SEED_SPOTIFY_PLAYLIST_ID)
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--sleep", type=float, default=0.7, help="seconds between lyric requests")
    ap.add_argument("--out", type=str, default="data/processed/songs.csv")
    args = ap.parse_args()

    sp = sp_client()
    genius = genius_client()

    artists = [a.strip() for a in args.artists.split(",") if a.strip()] if args.artists else []
    tracks = bootstrap_tracks(sp, artists, args.seed_playlist_id, args.limit)

    rows = []
    for t in tqdm(tracks, desc="Collecting"):
        title = t["name"]
        artists_joined = ", ".join([a["name"] for a in t["artists"]])
        spotify_id = t["id"]
        lyrics = fetch_lyrics(genius, title, t["artists"][0]["name"] if t["artists"] else "")
        if lyrics:
            # save raw
            fn = f"data/raw_lyrics/{spotify_id}.txt"
            with open(fn, "w", encoding="utf-8") as f:
                f.write(lyrics)
            rows.append({
                "spotify_id": spotify_id,
                "title": title,
                "artists": artists_joined,
                "lyrics_path": fn
            })
        time.sleep(args.sleep)

    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} songs to {args.out}")

if __name__ == "__main__":
    main()
