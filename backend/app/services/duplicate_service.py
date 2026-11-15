"""Duplicate detection: exact email, exact phone, then lightweight text similarity.
Duplicates are only FLAGGED (duplicate_of_id + reason) for an admin to review — never merged or deleted."""
import re
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Enquiry


def normalise_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.casefold())).strip()


def similarity(a: str, b: str) -> float:
    """Blend of character-level ratio and word-set overlap; robust to small edits and reordering."""
    na, nb = normalise_text(a), normalise_text(b)
    if not na or not nb:
        return 0.0
    ratio = SequenceMatcher(None, na, nb).ratio()
    wa, wb = set(na.split()), set(nb.split())
    jaccard = len(wa & wb) / len(wa | wb) if wa | wb else 0.0
    return max(ratio, jaccard)


def find_duplicate(db: Session, enquiry: Enquiry) -> tuple[int, str] | None:
    """Compare against OLDER enquiries only, so the first submission stays the 'original'."""
    s = get_settings()
    base = select(Enquiry).where(Enquiry.id < enquiry.id)

    if enquiry.email:
        hit = db.scalars(base.where(Enquiry.email == enquiry.email).order_by(Enquiry.id).limit(1)).first()
        if hit:
            return hit.id, "Same email address"
    if enquiry.phone:
        hit = db.scalars(base.where(Enquiry.phone == enquiry.phone).order_by(Enquiry.id).limit(1)).first()
        if hit:
            return hit.id, "Same phone number"

    recent = db.scalars(base.order_by(Enquiry.id.desc()).limit(s.duplicate_lookback)).all()
    best: tuple[float, int] = (0.0, 0)
    for other in recent:
        score = similarity(enquiry.message, other.message)
        if score > best[0]:
            best = (score, other.id)
    if best[0] >= s.duplicate_similarity_threshold:
        return best[1], f"Similar message ({best[0]:.0%} match)"
    return None
