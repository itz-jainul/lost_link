# ai_utils.py (advanced text + image helpers)
import os
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    _SENTENCE_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
except Exception:
    _SENTENCE_MODEL = None

try:
    from PIL import Image
    import imagehash
except Exception:
    Image = None
    imagehash = None

def build_tfidf_embeddings(texts: List[str]):
    vec = TfidfVectorizer(stop_words='english', ngram_range=(1,2), max_features=5000)
    mat = vec.fit_transform([t or '' for t in texts])
    return vec, mat

def tfidf_cosine_scores(query: str, candidates: List[str], vec=None, mat=None):
    texts = [c or '' for c in candidates]
    if vec is None or mat is None:
        vec, mat = build_tfidf_embeddings([query] + texts)
        qv = mat[0]
        cm = mat[1:]
    else:
        qv = vec.transform([query])
        cm = mat
    scores = cosine_similarity(qv, cm)[0]
    indexed = sorted([(i, float(score)) for i, score in enumerate(scores)], key=lambda x: x[1], reverse=True)
    return indexed

def embed_texts_sentence_transformers(texts):
    if _SENTENCE_MODEL is None:
        raise RuntimeError("SentenceTransformer not available")
    return _SENTENCE_MODEL.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

def compute_perceptual_hash(image_path, hash_size=16):
    if imagehash is None or Image is None:
        raise RuntimeError("Pillow/imagehash not installed")
    img = Image.open(image_path).convert('RGB')
    return imagehash.phash(img, hash_size=hash_size)

def phash_hamming_distance(h1, h2):
    return int(h1 - h2)

def find_similar_images_by_phash(query_path, candidate_paths, max_hamming=12):
    qh = compute_perceptual_hash(query_path)
    results = []
    for p in candidate_paths:
        try:
            ch = compute_perceptual_hash(p)
            d = phash_hamming_distance(qh, ch)
            if d <= max_hamming:
                results.append((p, d))
        except Exception:
            continue
    results.sort(key=lambda x: x[1])
    return results
