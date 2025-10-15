import lyricsgenius
import pandas as pd

def fetch_lyrics_frame(df_tracks: pd.DataFrame, genius_token: str) -> pd.DataFrame:
    if not genius_token:
        df_tracks = df_tracks.copy()
        df_tracks["lyrics"] = None
        return df_tracks
    genius = lyricsgenius.Genius(genius_token, skip_non_songs=True, remove_section_headers=True, timeout=10)
    texts = []
    for _, r in df_tracks.iterrows():
        try:
            song = genius.search_song(r["track_name"], (r["artist_name"].split(",") or [""])[0])
            texts.append(song.lyrics if song else None)
        except Exception:
            texts.append(None)
    out = df_tracks.copy()
    out["lyrics"] = texts
    return out
