from sentence_transformers import SentenceTransformer
import os

class Embedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        # Download/Cache the model
        # cache_folder can be configured, default is ~/.cache/torch/sentence_transformers
        self.model = SentenceTransformer(model_name)
        
    def embed_text(self, text: str):
        """Convert string to vector"""
        return self.model.encode(text).tolist()
    
    def embed_batch(self, texts: list):
        """Convert list of strings to vectors"""
        return self.model.encode(texts).tolist()
