import sys
import os

# Add src to path
sys.path.append(os.path.abspath("."))

from src.chunking import compute_similarity
from src.embeddings import _mock_embed, _local_embed

pairs = [
    ("Tôi sắp ăn cơm", "Tôi sẽ ăn cơm"),
    ("Tôi không biết", "a^2 + b^2 = c^2"),
    ("Tôi biết rất rõ", "Tôi không biết gì cả"),
    ("a^2 + b^2 = c^2", "!^$&((%)(*%#))"),
    ("Tôi muốn ăn cơm", "Tôi muốn ngủ"),
    ("!^$&((%)(*%#))", ""),
]

print(f"{'Pair':<5} | {'Actual Score':<12}")
print("-" * 20)

for i, (a, b) in enumerate(pairs, 1):
    vec_a = _mock_embed(a)
    vec_b = _mock_embed(b)
    score = compute_similarity(vec_a, vec_b)
    print(f"{i:<5} | {score:<12.4f}")

print(f"{'Pair':<5} | {'Actual Score':<12}")
print("-" * 20)

for i, (a, b) in enumerate(pairs, 1):
    vec_a = _local_embed(a)
    vec_b = _local_embed(b)
    score = compute_similarity(vec_a, vec_b)
    print(f"{i:<5} | {score:<12.4f}")

