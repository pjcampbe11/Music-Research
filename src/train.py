import os, argparse, numpy as np, pandas as pd
from dotenv import load_dotenv
from src.config import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, GENIUS_ACCESS_TOKEN
from src.ingest_spotify import get_spotify_client, fetch_playlist_tracks, fetch_audio_features
from src.ingest_genius import fetch_lyrics_frame
from src.embed_lyrics import SBertEmbedder
from src.build_index import build_vectors, build_faiss_index

def main():
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--playlist", required=True)
    ap.add_argument("--alpha", type=float, default=0.6)
    ap.add_argument("--lyrics", type=str, default="false")
    ap.add_argument("--max_tracks", type=int, default=5000)
    ap.add_argument("--out_dir", default="artifacts")
    ap.add_argument("--out_gcs", default=None)
    args = ap.parse_args()

    sp = get_spotify_client(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI)
    df_tracks = fetch_playlist_tracks(sp, args.playlist).head(args.max_tracks)
    df_feats  = fetch_audio_features(sp, df_tracks["track_id"].tolist())
    df = df_tracks.merge(df_feats, on="track_id", how="left")

    lyrics_emb = None
    if args.lyrics.lower() == "true" and GENIUS_ACCESS_TOKEN:
        df = fetch_lyrics_frame(df, GENIUS_ACCESS_TOKEN)
        texts = [t if isinstance(t,str) and t else "" for t in df["lyrics"].tolist()]
        embedder = SBertEmbedder()
        lyrics_emb = embedder.encode(texts)

    vec, scaler = build_vectors(df, lyrics_emb=lyrics_emb, alpha=args.alpha)
    index = build_faiss_index(vec)

    os.makedirs(args.out_dir, exist_ok=True)
    df.to_parquet(os.path.join(args.out_dir, "track_meta.parquet"), index=False)
    np.save(os.path.join(args.out_dir, "vectors.npy"), vec)
    import joblib, faiss
    joblib.dump(scaler, os.path.join(args.out_dir, "scaler.pkl"))
    faiss.write_index(index, os.path.join(args.out_dir, "faiss.index"))
    print("Saved artifacts to", args.out_dir)

    if args.out_gcs:
        from google.cloud import storage
        client = storage.Client()
        bucket_name = args.out_gcs.split('/')[2]
        prefix = '/'.join(args.out_gcs.split('/')[3:]).rstrip('/') + '/'
        bucket = client.bucket(bucket_name)
        for fname in ["track_meta.parquet","vectors.npy","scaler.pkl","faiss.index"]:
            blob = bucket.blob(prefix + fname)
            blob.upload_from_filename(os.path.join(args.out_dir, fname))
        print("Uploaded artifacts to", args.out_gcs)

if __name__ == "__main__":
    main()
