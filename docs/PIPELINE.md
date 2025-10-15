# Pipeline
1. Collect candidates via Spotify → fetch lyrics via Genius.
2. Split lyrics into lines; compute embeddings + engineered features.
3. Weakly supervise a small classifier; combine with heuristics.
4. Aggregate to song-level double/triple counts; score and rank.
5. (Optional) Create a Spotify playlist from top N.
