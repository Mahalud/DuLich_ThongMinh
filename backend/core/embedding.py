from functools import lru_cache


PREFERENCE_EXPANSIONS = {
    'biển': 'du lịch biển, bãi biển cát trắng, tắm biển, đảo, hải sản, nghỉ dưỡng ven biển',
    'núi': 'du lịch núi, rừng, cao nguyên, trekking, leo núi, ruộng bậc thang, khí hậu vùng cao',
    'thành phố': 'du lịch thành phố, đô thị, kiến trúc, mua sắm, bảo tàng, đời sống địa phương',
    'ẩm thực': 'du lịch ẩm thực, món ăn địa phương, đặc sản, chợ, quán ăn, trải nghiệm nấu ăn',
    'văn hóa lịch sử': 'di tích lịch sử, di sản, bảo tàng, kiến trúc cổ, văn hóa truyền thống, lễ hội',
    'văn hóa': 'di sản, di tích, kiến trúc, văn hóa truyền thống, lễ hội và đời sống địa phương',
    'nghỉ dưỡng': 'nghỉ dưỡng thư thái, resort, spa, bãi biển yên tĩnh, cảnh quan và tiện nghi',
    'mạo hiểm': 'du lịch mạo hiểm, trekking, leo núi, khám phá hang động, chèo thuyền và thử thách ngoài trời',
    'thiên nhiên': 'cảnh quan thiên nhiên, rừng, núi, biển, sông hồ, vườn quốc gia và sinh thái',
}


def expand_preferences(text):
    """Expand known Vietnamese preference labels while retaining free text."""
    parts = [part.strip() for part in (text or '').replace(';', ',').split(',') if part.strip()]
    return ' '.join(PREFERENCE_EXPANSIONS.get(part.casefold(), part) for part in parts)


def destination_embedding_text(destination):
    """Build the shared Sentence-BERT input for destinations."""
    return ' '.join(filter(None, [
        getattr(destination, 'name', ''),
        getattr(destination, 'category', ''),
        getattr(destination, 'address', ''),
        getattr(destination, 'description', ''),
    ]))


@lru_cache(maxsize=1)
def get_embedding_model():
    try:
        import torch
        torch.set_num_threads(1)
    except ImportError:
        pass
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cpu')


def encode_text(text: str) -> list[float]:
    try:
        import torch
        torch.set_num_threads(1)
    except ImportError:
        pass
    vector = get_embedding_model().encode(text or '', convert_to_tensor=False, normalize_embeddings=False)
    return vector.tolist()
