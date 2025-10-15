import numpy as np
import faiss
from sklearn.preprocessing import StandardScaler

AUDIO_COLS = ["danceability","energy","valence","tempo","loudness","acousticness",
              "instrumentalness","liveness","speechiness","key","mode","time_signature"]

def build_vectors(df, lyrics_emb=None, alpha: float = 0.6):
    scaler = StandardScaler().fit(df[AUDIO_COLS].fillna(0))
    audio_vec = scaler.transform(df[AUDIO_COLS].fillna(0))
    audio_vec = audio_vec / (np.linalg.norm(audio_vec, axis=1, keepdims=True)+1e-9)

    if lyrics_emb is not None and lyrics_emb.shape[0] == audio_vec.shape[0]:
        vec = alpha*audio_vec + (1-alpha)*lyrics_emb
    else:
        vec = audio_vec
    vec = vec / (np.linalg.norm(vec, axis=1, keepdims=True)+1e-9)
    return vec, scaler

def build_faiss_index(vec: np.ndarray):
    index = faiss.IndexFlatIP(vec.shape[1])
    index.add(vec.astype('float32'))
    return index
