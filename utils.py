import os
from itsdangerous import URLSafeTimedSerializer
from config import Config
from difflib import SequenceMatcher

def generate_token(email):
    s = URLSafeTimedSerializer(Config.SECRET_KEY)
    return s.dumps(email, salt=Config.SECURITY_PASSWORD_SALT)

def confirm_token(token, expiration=3600*24):
    s = URLSafeTimedSerializer(Config.SECRET_KEY)
    try:
        email = s.loads(token, salt=Config.SECURITY_PASSWORD_SALT, max_age=expiration)
    except Exception:
        return None
    return email

def title_similarity(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_matches_for_item(db, item, threshold=0.5, max_results=10):
    from models import Item
    opposite = 'found' if item.item_type == 'missing' else 'missing'
    q = Item.query.filter(Item.item_type == opposite, Item.status == 'active')
    results = []
    for cand in q.all():
        score = 0.0
        sim = title_similarity(item.title, cand.title)
        score += sim * 0.6
        if item.category and cand.category and item.category.lower() == cand.category.lower():
            score += 0.2
        if item.location and cand.location and item.location.lower() in cand.location.lower():
            score += 0.15
        if item.date_lost_found and cand.date_lost_found:
            delta = abs((item.date_lost_found - cand.date_lost_found).days)
            if delta <= 7:
                score += 0.15
            elif delta <= 30:
                score += 0.08
        if score >= threshold:
            results.append({'item': cand, 'score': score})
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:max_results]
