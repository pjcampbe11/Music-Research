# EntendreRank – Rap Lyric Complexity Recommender (Double/Triple Entendres)

EntendreRank identifies, tags, and ranks rap songs by lyrical complexity, focusing on **double** and **triple** entendres.
It uses:
- **Genius API** (via `lyricsgenius`) to fetch lyrics
- **Spotify Web API** (via `spotipy`) for track metadata + playlist creation
- **Hugging Face Transformers** for semantic embeddings and a lightweight classifier
- A **hybrid heuristic + ML** detection pipeline
- A final **ranking** (double=+1, triple=+2) and optional **Spotify playlist** generator

> Built to align with Spotify’s personalization ethos: deeper content understanding → better, more personalized recommendations.

---

## Quickstart

1. **Clone / unzip** this repo and create a virtual environment:
   ```bash
   python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API keys**:
   - Copy `.env.template` → `.env` and fill values for `GENIUS_ACCESS_TOKEN`, `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`.
   - Optionally set `BOOTSTRAP_ARTISTS` or `SEED_SPOTIFY_PLAYLIST_ID`.

3. **Collect lyrics + metadata** (writes to `data/processed/songs.csv` & `data/raw_lyrics/`):
   ```bash
   python -m entendre_rank.data_collection --artists "Eminem,Jay-Z" --limit 10
   # or from playlist seeds
   python -m entendre_rank.data_collection --seed-playlist-id <playlist_id> --limit 50
   ```

4. **Detect entendres** (produces `data/processed/detections.csv`):
   ```bash
   python -m entendre_rank.detection_model --input data/processed/songs.csv --output data/processed/detections.csv
   ```

5. **Rank songs** (produces `data/processed/ranked.csv`):
   ```bash
   python -m entendre_rank.ranking --detections data/processed/detections.csv --output data/processed/ranked.csv
   ```

6. **Generate Spotify playlist** (top N ranked songs):
   ```bash
   python -m entendre_rank.playlist_generator --ranked data/processed/ranked.csv --name "EntendreRank: Top Wordplay" --top 50
   ```

7. **Demo notebook**: open `notebooks/EntendreRank_Demo.ipynb` for an end‑to‑end walkthrough.

---

## Detection Approach (Hybrid)

- **Semantic embeddings** (Transformer, default: `sentence-transformers/all-MiniLM-L6-v2` or a fallback HF model) per lyric line
- **Heuristics**: curated ambiguous-lexeme & innuendo lexicons, POS/regex ambiguity, incongruity cues
- **Lightweight classifier**: logistic regression on top of pooled embeddings + engineered features
- **Triple heuristics**: multiple distinct ambiguity hits in same line or across adjacent lines

> This ships with a minimal seed lexicon + on-the-fly weak supervision. For improved accuracy, label ~200 lines and re-train (`--train` flag).

---

## Project Structure
```
entendre_rank/
  __init__.py
  config.py
  utils.py
  data_collection.py
  detection_model.py
  ranking.py
  playlist_generator.py
  models/
data/
  raw_lyrics/
  processed/
notebooks/
tests/
docs/
```

---

## Repro Tips
- **Model downloads**: The first run of transformers will download weights. Ensure internet access.
- **Genius lyric accuracy**: Genius may return cleaned/altered text; quality varies by song.
- **Rate limits**: Respect API limits; use `--sleep` between requests in `data_collection` if needed.
- **Safety**: Lyrics may contain explicit content.

---

## Example: Scoring
```
score(song) = (#double_entendres) + 2 * (#triple_entendres)
```
Optionally normalize by length via `--normalize-per-100-lines` in `ranking`.

---

## Tests
Run a tiny sanity test:
```bash
pytest -q
```

---

## License
MIT
