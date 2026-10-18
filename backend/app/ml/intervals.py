"""Small, deterministic split-conformal helpers for log-yield intervals."""
from __future__ import annotations

import math
from collections.abc import Sequence


def conformal_quantile(scores: Sequence[float], level: float = 0.8) -> float:
    """Finite-sample corrected empirical quantile of absolute log residuals."""
    if not 0.0 < level < 1.0:
        raise ValueError("level must be between zero and one")
    values = sorted(float(score) for score in scores if math.isfinite(float(score)) and float(score) >= 0)
    if not values:
        return math.inf
    rank = min(len(values), math.ceil((len(values) + 1) * level))
    return values[rank - 1]


def log_interval(point: float, quantile: float) -> tuple[float, float]:
    """Return positive bounds on the original yield scale around ``point``."""
    point = float(point)
    if not math.isfinite(point) or point <= 0:
        raise ValueError("point must be finite and positive")
    if not math.isfinite(quantile) or quantile < 0:
        return (point * 0.01, point * 100.0)
    return math.exp(math.log(point) - quantile), math.exp(math.log(point) + quantile)
