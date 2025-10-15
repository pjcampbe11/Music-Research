import argparse
import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from typing import List
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer, AutoModel
import torch
from .utils import split_lyrics_into_lines, engineered_features, window_triple_signal
from .config import DEFAULT_EMBEDDING_MODEL, RANDOM_SEED

def load_embedder(model_name=DEFAULT_EMBEDDING_MODEL, device=None):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()
    return tokenizer, model, device

def embed_lines(tokenizer, model, device, lines: List[str]) -> np.ndarray:
    embs = []
    for i in range(0, len(lines), 16):
        batch = lines[i:i+16]
        enc = tokenizer(batch, padding=True, truncation=True, max_length=128, return_tensors="pt")
        enc = {k: v.to(device) for k,v in enc.items()}
        with torch.no_grad():
            out = model(**enc)
            # mean-pool last hidden state
            last_hidden = out.last_hidden_state  # (B, T, H)
            mask = enc["attention_mask"].unsqueeze(-1).expand(last_hidden.size()).float()
            pooled = (last_hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            embs.append(pooled.cpu().numpy())
    return np.vstack(embs) if embs else np.zeros((0, model.config.hidden_size))

def weak_labels_from_heuristics(df_feats: pd.DataFrame) -> np.ndarray:
    # very rough: if ambiguous + (sexual or drug) and short line → likely double entendre
    y = (
        (df_feats["ambiguous_hits"] >= 1) &
        ((df_feats["sexual_hits"] >= 1) | (df_feats["drug_hits"] >= 1)) &
        (df_feats["len_words"] <= 14)
    ).astype(int).values
    return y

def detect(file_in: str, file_out: str, model_name: str = DEFAULT_EMBEDDING_MODEL, train: bool=False):
    songs = pd.read_csv(file_in)
    det_rows = []

    tokenizer, model, device = load_embedder(model_name)

    # Minimal classifier pipeline (weakly supervised unless --train with labels provided later)
    clf = Pipeline([("scaler", StandardScaler(with_mean=False)), ("lr", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_SEED))])

    all_embs = []
    all_feats = []
    all_y = []

    for _, row in tqdm(songs.iterrows(), total=len(songs), desc="Embedding & detecting"):
        lyrics_path = row["lyrics_path"]
        if not os.path.exists(lyrics_path):
            continue
        with open(lyrics_path, "r", encoding="utf-8") as f:
            text = f.read()
        lines = split_lyrics_into_lines(text)
        if not lines:
            continue
        feats = engineered_features(lines)
        embs = embed_lines(tokenizer, model, device, lines)

        # combine
        # Align features length with embeddings
        feats = feats.iloc[:embs.shape[0]].reset_index(drop=True)
        X = np.hstack([embs, feats[["len_chars","len_words","ambiguous_hits","sexual_hits","drug_hits","punct_q","punct_bang","quotes"]].values])

        # Weak labels to train a tiny classifier on-the-fly (self-training style)
        y_weak = weak_labels_from_heuristics(feats)
        if train and len(y_weak) > 10:
            all_embs.append(X)
            all_feats.append(feats)
            all_y.append(y_weak)

        # Score with heuristic probability (until trained)
        prob_heur = (y_weak * 0.7 + (feats["ambiguous_hits"] > 1).astype(int) * 0.3).values
        line_scores = prob_heur

        triple_signal = window_triple_signal(lines, window=2)

        # Build detections
        for i, ln in enumerate(lines[:len(line_scores)]):
            det_rows.append({
                "spotify_id": row["spotify_id"],
                "title": row["title"],
                "artists": row["artists"],
                "line_idx": i,
                "line_text": ln,
                "double_prob": float(line_scores[i]),
                "triple_signal": float(triple_signal)
            })

    # If train, fit classifier and rescore (optional enhancement)
    if train and all_y:
        X_train = np.vstack(all_embs)
        y_train = np.concatenate(all_y)
        clf.fit(X_train, y_train)
        # Rescoring skipped here for simplicity; users can run with --train and modify to persist model.

    out_df = pd.DataFrame(det_rows)
    out_df.to_csv(file_out, index=False)
    print(f"Wrote detections to {file_out}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=str, required=True)
    ap.add_argument("--output", type=str, default="data/processed/detections.csv")
    ap.add_argument("--model", type=str, default=DEFAULT_EMBEDDING_MODEL)
    ap.add_argument("--train", action="store_true", help="Enable weak supervised on-the-fly training")
    args = ap.parse_args()
    detect(args.input, args.output, args.model, train=args.train)

if __name__ == "__main__":
    main()
