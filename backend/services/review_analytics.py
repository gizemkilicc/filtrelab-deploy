"""
Shared review analytics utilities.
Computes star-level distribution, quotas, sample reviews, and diagnostic logs.
"""

_MIN_NEGATIVE_QUOTA = 30  # Minimum reviews to target for 1-star and 2-star ratings


def compute_star_quota(rating_dist: dict | None, max_reviews: int) -> dict[str, int]:
    """
    Compute per-star review quota with guaranteed minimum negative coverage.

    Rules:
    - Proportional to rating distribution by default
    - 1-star and 2-star get at least MIN_NEGATIVE_QUOTA reviews if they exist
    - Total never exceeds max_reviews
    """
    if not rating_dist or max_reviews <= 0:
        per_star = max(1, max_reviews // 5)
        return {str(s): per_star for s in range(1, 6)}

    total = sum(v for v in rating_dist.values() if isinstance(v, (int, float)))
    if total == 0:
        per_star = max(1, max_reviews // 5)
        return {str(s): per_star for s in range(1, 6)}

    # Proportional distribution
    quota: dict[str, int] = {}
    for star in range(1, 6):
        count = rating_dist.get(str(star), 0)
        quota[str(star)] = int(round((count / total) * max_reviews))

    # Guarantee minimum negative quota for 1-star and 2-star
    for neg_star in ("1", "2"):
        available = rating_dist.get(neg_star, 0)
        if available > 0 and quota.get(neg_star, 0) < _MIN_NEGATIVE_QUOTA:
            extra = _MIN_NEGATIVE_QUOTA - quota.get(neg_star, 0)
            quota[neg_star] = min(_MIN_NEGATIVE_QUOTA, available)
            # Take from 5-star to compensate
            quota["5"] = max(0, quota.get("5", 0) - extra)

    # Clamp total to max_reviews
    total_quota = sum(quota.values())
    if total_quota > max_reviews:
        scale = max_reviews / total_quota
        quota = {s: int(q * scale) for s, q in quota.items()}

    return quota


def compute_review_analytics(
    reviews: list[dict],
    rating_dist: dict | None,
    max_reviews: int = 0,
) -> dict:
    """
    Compute star-level analytics and print diagnostic logs.

    Returns:
        loadedByStar    – actual count of loaded reviews per star
        sampleReviews   – one representative review per star (best text)
        targetByStar    – computed quota per star (if max_reviews given)
        starDistribution – the rating_dist passed in (normalised to str keys)
    """
    # Count loaded reviews per star
    loaded_by_star: dict[str, int] = {str(s): 0 for s in range(1, 6)}
    for r in reviews:
        raw = r.get("rating")
        if raw is not None:
            try:
                star = int(raw)
                if 1 <= star <= 5:
                    loaded_by_star[str(star)] += 1
            except (ValueError, TypeError):
                pass

    # Best sample per star (longest non-empty text wins)
    best_by_star: dict[str, dict | None] = {str(s): None for s in range(1, 6)}
    for r in reviews:
        raw = r.get("rating")
        if raw is None:
            continue
        try:
            star = int(raw)
            if 1 <= star <= 5:
                key = str(star)
                cur = best_by_star[key]
                if cur is None or len(r.get("text", "")) > len(cur.get("text", "")):
                    best_by_star[key] = r
        except (ValueError, TypeError):
            pass

    sample_reviews: list[dict] = []
    for star in range(5, 0, -1):
        sample = best_by_star.get(str(star))
        if sample:
            txt = sample.get("text", "")
            sample_reviews.append({
                "rating": star,
                "textPreview": txt[:120] + ("..." if len(txt) > 120 else ""),
                "source": sample.get("source", ""),
            })

    target_by_star = compute_star_quota(rating_dist, max_reviews) if max_reviews > 0 else {}

    # Normalise star distribution keys to str
    star_distribution: dict[str, int] | None = None
    if rating_dist:
        star_distribution = {str(k): int(v) for k, v in rating_dist.items() if v}

    # ── Diagnostic logs ───────────────────────────────────────────────────────
    if star_distribution:
        print(f"[REVIEWS] distribution={star_distribution}")
    if target_by_star:
        print(f"[REVIEWS] targetByStar={target_by_star}")
    print(f"[REVIEWS] loadedByStar={loaded_by_star}")

    pos = next(
        (r["text"][:100] for r in reviews
         if r.get("rating") and int(r["rating"]) >= 4 and len(r.get("text", "")) > 10),
        None,
    )
    neg = next(
        (r["text"][:100] for r in reviews
         if r.get("rating") and int(r["rating"]) <= 2 and len(r.get("text", "")) > 10),
        None,
    )
    if pos:
        print(f"[REVIEWS] samplePositive={pos!r}")
    if neg:
        print(f"[REVIEWS] sampleNegative={neg!r}")

    return {
        "starDistribution": star_distribution,
        "loadedByStar": loaded_by_star,
        "sampleReviews": sample_reviews,
        "targetByStar": target_by_star,
    }
