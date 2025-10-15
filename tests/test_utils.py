import os
import pandas as pd
from entendre_rank.utils import split_lyrics_into_lines, engineered_features, window_triple_signal

def test_split_lines():
    txt = "Line one\n\n[Chorus]\nLine two!"
    lines = split_lyrics_into_lines(txt)
    assert lines == ["Line one", "Line two!"]

def test_feats():
    lines = ["I got the keys to the city", "Real Gs move in silence like lasagna"]
    feats = engineered_features(lines)
    assert len(feats) == 2
    assert "ambiguous_hits" in feats.columns

def test_triple_signal():
    lines = ["I got the keys", "serving base all night", "bake the cake"]
    s = window_triple_signal(lines, window=2)
    assert s >= 0
