
from functools import lru_cache

import numpy as np
import torch
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1


@lru_cache(maxsize=1)
def load_models():
    """Load the pretrained face detector and embedding model once."""
    detector = MTCNN(
        image_size=160,
        margin=20,
        keep_all=True,
        device="cpu",
    )

    recognizer = InceptionResnetV1(
        pretrained="vggface2"
    ).eval()

    return detector, recognizer


def generate_embedding(image: Image.Image) -> np.ndarray:
    """Generate a 512-dimensional embedding for one detected face."""
    if not isinstance(image, Image.Image):
        raise ValueError("Input must be a PIL image.")

    image = image.convert("RGB")
    detector, recognizer = load_models()

    faces = detector(image)

    if faces is None:
        raise ValueError("No face detected in the image.")

    if faces.ndim == 3:
        faces = faces.unsqueeze(0)

    if faces.shape[0] != 1:
        raise ValueError(
            "Exactly one face must be present in the image."
        )

    with torch.inference_mode():
        embedding = recognizer(faces)[0]

    # Normalize the vector for cosine-similarity comparisons.
    embedding = torch.nn.functional.normalize(
        embedding, p=2, dim=0
    )

    return embedding.cpu().numpy()


def cosine_similarity(
    embedding_a: np.ndarray,
    embedding_b: np.ndarray,
) -> float:
    """Compare two normalized face embeddings."""
    if embedding_a.shape != (512,) or embedding_b.shape != (512,):
        raise ValueError("Both embeddings must contain 512 values.")

    denominator = (
        np.linalg.norm(embedding_a) * np.linalg.norm(embedding_b)
    )

    if denominator == 0:
        raise ValueError("Cannot compare a zero-length embedding.")

    return float(np.dot(embedding_a, embedding_b) / denominator)
