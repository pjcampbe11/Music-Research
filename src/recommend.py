import numpy as np
import pandas as pd

def recommend(df: pd.DataFrame, vec, index, seed_ids, k=30):
    id2row = {tid:i for i,tid in enumerate(df["track_id"])}
    rows = [id2row[s] for s in seed_ids if s in id2row]
    if not rows: return pd.DataFrame(columns=["track_name","artist_name","track_id"])
    q = vec[rows].mean(axis=0, keepdims=True)
    q /= (np.linalg.norm(q)+1e-9)
    D, I = index.search(q.astype('float32'), k*5)
    r, seen = [], set(seed_ids)
    for idx in I[0]:
        tid = df.iloc[idx]["track_id"]
        if tid not in seen:
            r.append(df.iloc[idx][["track_name","artist_name","track_id"]])
        if len(r) >= k: break
    return pd.DataFrame(r)
