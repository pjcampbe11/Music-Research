import os, pickle, faiss, pandas as pd, numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Load artifacts
ART_DIR = os.getenv("ART_DIR", "artifacts")
df = pd.read_parquet(os.path.join(ART_DIR, "track_meta.parquet"))
vec = np.load(os.path.join(ART_DIR, "vectors.npy"))
index = faiss.read_index(os.path.join(ART_DIR, "faiss.index"))

class RecRequest(BaseModel):
    seed_ids: list[str]
    k: int = 30

@app.post("/recommend")
def recommend(req: RecRequest):
    id2row = {tid:i for i,tid in enumerate(df["track_id"])}
    rows = [id2row[s] for s in req.seed_ids if s in id2row]
    if not rows:
        raise HTTPException(status_code=400, detail="No valid seed IDs provided.")
    q = vec[rows].mean(axis=0, keepdims=True)
    q /= (np.linalg.norm(q)+1e-9)
    D, I = index.search(q.astype('float32'), req.k*5)
    out, seen = [], set(req.seed_ids)
    for idx in I[0]:
        tid = df.iloc[idx]["track_id"]
        if tid not in seen:
            out.append({
                "track_name": df.iloc[idx]["track_name"],
                "artist_name": df.iloc[idx]["artist_name"],
                "track_id": tid
            })
        if len(out) >= req.k: break
    return {"results": out}
