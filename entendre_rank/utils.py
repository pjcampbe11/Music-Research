import re
import numpy as np
import pandas as pd
from typing import List, Tuple

AMBIGUOUS_TERMS = {
    # polysemous or slang-heavy: extend over time
    "rock", "keys", "base", "blow", "pump", "pipe", "bags", "lines", "shots",
    "dope", "fire", "ice", "grams", "plug", "lick", "roll", "hammer", "batter",
    "pound", "stick", "tool", "piece", "heat", "smoke", "gas", "cap", "trip",
    "ride", "plug", "plugged", "serve", "deck", "head", "back", "cake", "bust",
    "box", "pussy", "beat", "hit", "banger", "plug", "score"
}

SEXUAL_HINTS = {
    "dick","ass","pussy","head","blow","ride","pipe","stroke","wet","hard","soft","come","nut","cream","backshots"
}

DRUG_HINTS = {"dope","rock","base","crack","meth","lean","xan","percs","grams","kilo","plug","serve","trap","brick"}

def split_lyrics_into_lines(text: str) -> List[str]:
    text = re.sub(r"\[.*?\]", "", text)  # strip bracketed stage notes
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines

def keyword_hits(line: str) -> Tuple[int, int, int]:
    toks = set(re.findall(r"[a-zA-Z']+", line.lower()))
    amb = len(AMBIGUOUS_TERMS & toks)
    sex = len(SEXUAL_HINTS & toks)
    drug = len(DRUG_HINTS & toks)
    return amb, sex, drug

def engineered_features(lines: List[str]) -> pd.DataFrame:
    feats = []
    for i, ln in enumerate(lines):
        amb, sex, drug = keyword_hits(ln)
        feats.append({
            "idx": i,
            "len_chars": len(ln),
            "len_words": len(ln.split()),
            "ambiguous_hits": amb,
            "sexual_hits": sex,
            "drug_hits": drug,
            "punct_q": ln.count("?"),
            "punct_bang": ln.count("!"),
            "quotes": ln.count('"') + ln.count("'")
        })
    return pd.DataFrame(feats)

def window_triple_signal(lines: List[str], window:int=2) -> float:
    # crude: multiple distinct ambiguity types within short window suggests layered meaning
    score = 0.0
    for i in range(len(lines)):
        span = " ".join(lines[i:i+window+1]).lower()
        amb, sex, drug = keyword_hits(span)
        if amb >= 1 and ((sex >= 1 and drug >= 1) or amb >= 3):
            score += 1.0
    return score
