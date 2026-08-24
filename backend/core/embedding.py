from functools import lru_cache


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cpu')


def encode_text(text: str) -> list[float]:
    vector = get_embedding_model().encode(text or '', convert_to_tensor=False, normalize_embeddings=False)
    return vector.tolist()