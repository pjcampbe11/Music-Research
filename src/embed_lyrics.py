from typing import List
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

class SBertEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", max_length: int = 256):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.max_length = max_length

    def encode(self, texts: List[str], batch: int = 64) -> np.ndarray:
        embs = []
        for i in range(0, len(texts), batch):
            chunk = texts[i:i+batch]
            enc = self.tokenizer(chunk, padding=True, truncation=True, return_tensors="pt", max_length=self.max_length)
            with torch.no_grad():
                out = self.model(**enc).last_hidden_state.mean(dim=1)
            x = torch.nn.functional.normalize(out, p=2, dim=1).cpu().numpy()
            embs.append(x)
        return np.vstack(embs) if embs else np.zeros((0, 384))
