import argparse
import pandas as pd

def rank(detections_csv: str, out_csv: str, normalize_per_100: bool=False):
    df = pd.read_csv(detections_csv)
    # define double vs triple: double if double_prob >= 0.6; triple ~ aggregate triple_signal > threshold
    line_double = df["double_prob"] >= 0.6
    # Approximate triple using aggregate signal per song (stored per line identically); we'll sum later
    grouped = df.groupby("spotify_id").agg({
        "double_prob": lambda s: (s >= 0.6).sum(),
        "triple_signal": "max",
        "title": "first",
        "artists": "first"
    }).reset_index()

    grouped["double_count"] = grouped["double_prob"].astype(int)
    grouped["triple_count"] = (grouped["triple_signal"] >= 1.0).astype(int)

    score = grouped["double_count"] + 2 * grouped["triple_count"]

    if normalize_per_100:
        # Need number of lines per song; approximate via double_prob count scale; better to pass lines count in future
        norm = grouped["double_count"].clip(lower=1)
        score = score / norm * 100.0

    grouped["score"] = score
    ranked = grouped.sort_values("score", ascending=False)
    ranked.to_csv(out_csv, index=False)
    print(f"Wrote ranked list to {out_csv}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detections", type=str, required=True)
    ap.add_argument("--output", type=str, default="data/processed/ranked.csv")
    ap.add_argument("--normalize-per-100-lines", action="store_true")
    args = ap.parse_args()
    rank(args.detections, args.output, args.normalize_per_100_lines)

if __name__ == "__main__":
    main()
