import numpy as np

def recall_at_k(truth_ids, ranked_ids, k=20):
    truth = set(truth_ids)
    return len([x for x in ranked_ids[:k] if x in truth]) / float(len(truth) or 1)
