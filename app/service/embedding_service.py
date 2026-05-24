import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


class EmbeddingService:
    """
    Loads a CLIP model once at instantiation and keeps it in memory for the lifetime of the process.
    Provides methods to generate L2-normalized embedding vectors for images and text.

    L2 normalization is applied to all vectors before returning so that cosine similarity
    in pgvector equals the dot product — consistent and efficient.
    """

    def __init__(self, model_name: str):
        self.model = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()  # disable dropout — inference mode only

    def embed_image(self, file_path: str) -> list[float]:
        """
        Load an image from disk and return its L2-normalized embedding vector.
        Expects a 640px thumbnail path. CLIP internally resizes to 224x224 regardless of input size.
        """
        image = Image.open(file_path).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt")
        with torch.no_grad():
            features = self.model.get_image_features(**inputs)
        features = features / features.norm(dim=-1, keepdim=True)
        return features[0].tolist()

    def embed_text(self, text: str) -> list[float]:
        """
        Return an L2-normalized embedding vector for the given text.
        CLIP image and text embeddings share the same vector space —
        text embeddings can be compared directly against image embeddings in pgvector.
        """
        inputs = self.processor(text=text, return_tensors="pt", truncation=True, max_length=77)
        with torch.no_grad():
            features = self.model.get_text_features(**inputs)
        features = features / features.norm(dim=-1, keepdim=True)
        return features[0].tolist()
