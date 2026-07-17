from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field


ARABIC_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
TATWEEL_RE = re.compile(r"\u0640+")
WHITESPACE_RE = re.compile(r"\s+")
REPEATED_PUNCT_RE = re.compile(r"([!?\u061f\u060c,.;:])\1+")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ARABIC_LETTER_NORMALIZATION = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ئ": "ي",
        "ؤ": "و",
        # Step 1 uses this mapping for question_norm/answer_norm/canonical_name_norm.
        "ة": "ه",
    }
)
PUNCTUATION_NORMALIZATION = str.maketrans(
    {
        "؟": "?",
        "،": ",",
        "؛": ";",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
    }
)


@dataclass(frozen=True)
class QueryNormalizationResult:
    original_query: str
    normalized_query: str
    normalization_steps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _apply_step(text: str, step_name: str, transform, steps: list[str]) -> str:
    updated = transform(text)
    if updated != text:
        steps.append(step_name)
    return updated


def normalize_query(query: str | None) -> QueryNormalizationResult:
    original_query = "" if query is None else str(query)
    text = original_query
    steps: list[str] = []
    warnings: list[str] = []

    # Keep this behavior aligned with Step 1 preprocessing normalization.
    text = _apply_step(text, "remove_urls", lambda value: URL_RE.sub(" ", value), steps)
    text = _apply_step(text, "remove_emails", lambda value: EMAIL_RE.sub(" ", value), steps)
    text = _apply_step(text, "normalize_arabic_persian_digits", lambda value: value.translate(ARABIC_DIGITS), steps)
    text = _apply_step(text, "remove_tatweel", lambda value: TATWEEL_RE.sub("", value), steps)
    text = _apply_step(text, "remove_diacritics", lambda value: ARABIC_DIACRITICS_RE.sub("", value), steps)
    text = _apply_step(
        text,
        "normalize_arabic_letter_variants",
        lambda value: value.translate(ARABIC_LETTER_NORMALIZATION),
        steps,
    )
    text = _apply_step(
        text,
        "normalize_punctuation",
        lambda value: value.translate(PUNCTUATION_NORMALIZATION),
        steps,
    )
    text = _apply_step(text, "collapse_repeated_punctuation", lambda value: REPEATED_PUNCT_RE.sub(r"\1", value), steps)
    text = _apply_step(text, "collapse_whitespace", lambda value: WHITESPACE_RE.sub(" ", value), steps)
    text = _apply_step(text, "trim_and_lowercase", lambda value: value.strip().lower(), steps)

    if original_query.strip() and not text:
        warnings.append("Query became empty after conservative normalization.")
    if not original_query.strip():
        warnings.append("Query is empty.")

    return QueryNormalizationResult(
        original_query=original_query,
        normalized_query=text,
        normalization_steps=steps,
        warnings=warnings,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize one Arabic medical query.")
    parser.add_argument("--query", required=True, help="Arabic medical query to normalize.")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    result = normalize_query(args.query)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
