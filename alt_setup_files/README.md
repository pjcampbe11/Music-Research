# Entendre Rank – Playlist-Seeded Hybrid Music Recommender

This project builds a *content-based + lyric-embedding* recommender seeded by a Spotify playlist (e.g. your 3,200-track list).
It runs in **Google Colab** for fast iteration and **Vertex AI** for scheduled jobs/serving.

## Quick Start (Colab)

1. Open the notebook: `notebooks/EntendreRank_Colab.ipynb`
2. Set environment variables (or use Colab secrets):
   - `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, `SPOTIPY_REDIRECT_URI`
   - `GENIUS_ACCESS_TOKEN` (optional for lyrics)
3. Set `PLAYLIST_URL` to your Spotify playlist URL.
4. Run cells to ingest tracks, pull audio features, optionally fetch lyrics, build embeddings + FAISS index, and generate recommendations.
5. Artifacts (index, scalers, metadata) are saved under `artifacts/`.

## Vertex AI (Custom Training Job)

- Package the training script `src/train.py` and submit as a **Custom Job**.
- Configure GCS bucket for inputs/outputs via `--out_gcs`.
- Minimal example is in the README section **Vertex AI Job (Python)** below.

### Local API (optional)

- Start a small FastAPI service exposing `/recommend?seed_id=...` using `serving/local_api.py`.

## Environment Variables

Create `.env` (or use Colab secrets / GCP Secret Manager):
```
SPOTIPY_CLIENT_ID=...
SPOTIPY_CLIENT_SECRET=...
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
GENIUS_ACCESS_TOKEN=... # optional
PLAYLIST_URL=https://open.spotify.com/playlist/7MNBsBwgsqAsRZkdNE4E5Y?si=f3f1e453a80749cd
```

## Vertex AI Job (Python)

```python
from google.cloud import aiplatform as aip

aip.init(project="YOUR_PROJECT", location="us-central1")
job = aip.CustomJob(
    display_name="entendre-rank-train",
    worker_pool_specs=[{
      "machine_spec": {"machine_type": "n1-standard-4"},
      "replica_count": 1,
      "container_spec": {
        "image_uri": "us-docker.pkg.dev/vertex-ai/training/pytorch-xla.2-3:latest",
        "command": ["python","-m","src.train"],
        "args": [
          "--playlist", "https://open.spotify.com/playlist/7MNBsBwgsqAsRZkdNE4E5Y",
          "--alpha","0.6",
          "--max_tracks","4000",
          "--lyrics","true",
          "--out_gcs","gs://YOUR_BUCKET/entendre_rank/"
        ]
      }
    }]
)
job.run(sync=True)
```

> Notes: adjust machine type and container; add a GPU if you plan to embed lyrics at scale.

## Cost Hints

- **Colab**: Buy a 100 CU pack (~$9.99) and you can run an end-to-end build on ~3,200 tracks comfortably.
- **Vertex AI**: Training costs scale with machine hours; CPU machines are enough for audio-feature only. Add a T4/L4 GPU for faster lyric embeddings. New GCP users typically have $300 in credits.

## Compliance / TOS

- Use only API-returned metadata/features; do **not** download or redistribute audio or artwork.
- Respect Spotify and Genius Terms; avoid republishing lyrics. Prefer storing **embeddings** over raw text.
