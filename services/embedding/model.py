# services/embedding/model.py
from sentence_transformers import SentenceTransformer
import torch, numpy as np

class LabseEncoder:
    def __init__(self, device=None):
        self.model = SentenceTransformer("sentence-transformers/LaBSE")
        self.model = self.model.to(device or ("cuda" if torch.cuda.is_available() else "cpu"))

    def encode(self, texts, batch_size=512):
        embs = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,  # cosine-friendly
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embs.astype(np.float32)