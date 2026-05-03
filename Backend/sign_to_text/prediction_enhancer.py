"""
Prediction Enhancer — improves demo quality WITHOUT retraining.

Techniques:
1. Class masking  — suppresses classes that scored F1=0 on evaluation
2. Temperature scaling — sharpens the probability distribution so top
   predictions stand out more confidently
"""

import re
import logging
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

_REPORT_PATH = Path(__file__).parent / "classification_report_hands.txt"
DEFAULT_TEMPERATURE = 0.5  # <1 = sharper; 0.5 squares then renorms


# ── Parse the sklearn classification report ────────────────────────
def parse_classification_report(report_path=_REPORT_PATH):
    """Return {class_name: {"f1": float, "support": int}} from report."""
    f1_scores = {}
    if not report_path.exists():
        logger.warning(f"Classification report not found at {report_path}")
        return f1_scores

    with open(report_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n\r")
            # Class names may contain spaces (e.g. "Nouns/Cell phone")
            # Two+ spaces always separate the name from the four numbers.
            m = re.match(
                r"^\s{2,}(.+?)\s{2,}(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)\s*$",
                line,
            )
            if m:
                cls = m.group(1).strip()
                f1_scores[cls] = {"f1": float(m.group(4)), "support": int(m.group(5))}

    logger.info(f"Parsed {len(f1_scores)} class scores from classification report")
    return f1_scores


# ── Build a boolean mask for viable classes ────────────────────────
def build_viable_mask(class_labels, f1_scores, min_f1=0.0):
    """True for classes whose test-set F1 > min_f1."""
    mask = np.ones(len(class_labels), dtype=bool)
    suppressed = []
    for i, label in enumerate(class_labels):
        if label in f1_scores and f1_scores[label]["f1"] <= min_f1:
            mask[i] = False
            suppressed.append(label)

    viable = int(mask.sum())
    logger.info(
        f"Class mask: {viable}/{len(class_labels)} viable, "
        f"{len(suppressed)} suppressed (F1 ≤ {min_f1})"
    )
    return mask, suppressed


# ── Recommended signs for UI ──────────────────────────────────────
def get_recommended_signs(f1_scores, min_f1=0.40, min_support=2):
    """Return list of {'sign', 'f1', 'support', 'category'} sorted by F1."""
    recs = []
    for cls, info in f1_scores.items():
        if info["f1"] >= min_f1 and info["support"] >= min_support:
            cat = cls.split("/")[0] if "/" in cls else ""
            word = cls.split("/")[-1] if "/" in cls else cls
            recs.append({
                "sign": cls,
                "word": word,
                "category": cat,
                "f1": round(info["f1"] * 100, 1),
                "support": info["support"],
            })
    recs.sort(key=lambda x: (-x["f1"], -x["support"]))
    return recs


# ── Core enhancement function ─────────────────────────────────────
def enhance_predictions(probabilities, viable_mask, temperature=DEFAULT_TEMPERATURE):
    """
    Post-process softmax probabilities:
    1. Zero out non-viable classes (F1 = 0 on test set)
    2. Temperature sharpen: p' = p^(1/T) / Σ p^(1/T)
    """
    probs = probabilities.copy().astype(np.float64)

    # Step 1: mask non-viable classes
    probs[~viable_mask] = 0.0

    # Step 2: temperature sharpening
    if temperature != 1.0:
        power = 1.0 / temperature
        probs = np.power(np.maximum(probs, 1e-12), power)

    # Step 3: renormalize
    total = probs.sum()
    if total > 1e-12:
        probs = probs / total
    else:
        # Fallback: uniform over viable classes
        probs[viable_mask] = 1.0 / viable_mask.sum()

    return probs.astype(np.float32)
