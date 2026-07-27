import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "ground_truth_entities_100.csv"
DEFAULT_AHD = ROOT / "AHD.csv"


def relpath(path):
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_review_template(ground_truth_rows, ahd_rows, size):
    rows = []
    for index, ahd_row in enumerate(ahd_rows[:size], start=1):
        reviewed = ground_truth_rows[index - 1] if index <= len(ground_truth_rows) else {}
        rows.append(
            {
                "row_id": index,
                "question": reviewed.get("question") or ahd_row.get("Question", ""),
                "answer": reviewed.get("answer") or ahd_row.get("Answer", ""),
                "category": ahd_row.get("Category", ""),
                "entity_type": reviewed.get("entity_type", ""),
                "canonical_name": reviewed.get("canonical_name", ""),
                "annotation_status": "reviewed_handoff" if reviewed else "needs_human_review",
                "review_notes": "",
            }
        )
    return rows


def parse_args():
    parser = argparse.ArgumentParser(description="Create reviewed entity ground-truth slices from the hand-off file.")
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--ahd-csv", type=Path, default=DEFAULT_AHD)
    parser.add_argument("--sizes", type=int, nargs="+", default=[200, 300])
    parser.add_argument("--review-size", type=int, default=500)
    return parser.parse_args()


def main():
    args = parse_args()
    rows = read_csv(args.input_csv)
    if not rows:
        raise ValueError(f"No rows found in {args.input_csv}")
    fieldnames = rows[0].keys()
    outputs = []
    for size in args.sizes:
        if len(rows) < size:
            raise ValueError(f"{args.input_csv} has {len(rows)} rows; cannot create size {size}")
        output_path = ROOT / f"ground_truth_entities_{size}.csv"
        write_csv(output_path, rows[:size], fieldnames)
        outputs.append(relpath(output_path))
    if args.review_size:
        ahd_rows = read_csv(args.ahd_csv)
        review_rows = build_review_template(rows, ahd_rows, args.review_size)
        review_path = ROOT / f"ground_truth_entities_{args.review_size}_review_template.csv"
        write_csv(
            review_path,
            review_rows,
            ["row_id", "question", "answer", "category", "entity_type", "canonical_name", "annotation_status", "review_notes"],
        )
        outputs.append(relpath(review_path))
    print(json.dumps({"input_rows": len(rows), "outputs": outputs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
