from __future__ import annotations

"""Build the held-out-safe direct-QA retrieval index for Step 9."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from src.config import ROOT_DIR, load_final_v2_config
from src.step09a_qa_corpus import build_qa_corpus_index, load_holdout_questions


DEFAULT_SOURCE = ROOT_DIR / "data" / "raw" / "AHD.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the held-out-safe AHD QA retrieval index.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument(
        "--split-source",
        type=Path,
        required=True,
        help="CSV containing the evaluation questions that must be excluded.",
    )
    parser.add_argument("--batch-size", type=int, default=2000)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    config = load_final_v2_config()
    index_path = Path(config.qa_corpus.index_path)
    holdout_count = len(load_holdout_questions(args.split_source))
    if not args.execute:
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "source": str(args.source),
                    "split_source": str(args.split_source),
                    "heldout_unique_questions": holdout_count,
                    "index": str(index_path),
                    "corpus_version": config.qa_corpus.corpus_version,
                    "requires_execute": True,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    summary = build_qa_corpus_index(
        args.source,
        args.split_source,
        index_path,
        config.qa_corpus.corpus_version,
        batch_size=args.batch_size,
        force=args.force,
    )
    print(json.dumps({"status": "ok", **asdict(summary)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
