import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs" / "03_entity_extraction" / "review_templates" / "entity_ground_truth_500_llama_preannotations.csv"
REVIEWED_OUTPUT = ROOT / "outputs" / "03_entity_extraction" / "review_templates" / "entity_ground_truth_500_assistant_reviewed.csv"
GROUND_TRUTH_OUTPUT = ROOT / "ground_truth_entities_500.csv"


# Rows not listed here keep the Llama candidate-rank pre-annotation.
ASSISTANT_OVERRIDES = {
    304: ("DiseaseCondition", "تليفات موضع الحقن"),
    307: ("Symptom", "ألم الركبتين"),
    308: ("Symptom", "طقطقة المفاصل"),
    309: ("DiseaseCondition", "كيس الحمل"),
    326: ("Symptom", "زيادة معدل ضربات القلب"),
    330: ("DiseaseCondition", "غشاء البكارة"),
    335: ("Symptom", "جرح الصدر"),
    344: ("DiseaseCondition", "تمزق غشاء البكارة"),
    346: ("Symptom", "اضطراب الدورة الشهرية"),
    348: ("Symptom", "دم الإباضة"),
    351: ("Symptom", "غازات"),
    354: ("DiseaseCondition", "حالة طبيعية"),
    358: ("Test", "تحليل دم"),
    374: ("Symptom", "ألم الكتف"),
    376: ("Treatment", "مراجعة طبيب الأطفال"),
    379: ("Symptom", "ألم الرأس والعينين"),
    381: ("DiseaseCondition", "ارتفاع الدهون الثلاثية"),
    382: ("Treatment", "الحبة السوداء"),
    383: ("Treatment", "حبة البركة"),
    387: ("DiseaseCondition", "فرط الرغبة الجنسية"),
    388: ("Symptom", "رفض ارتداء الملابس"),
    389: ("DiseaseCondition", "إدمان العادة السرية"),
    392: ("DiseaseCondition", "غشاء البكارة"),
    394: ("Symptom", "انتفاخ الجفن"),
    395: ("Test", "فحص الصفار"),
    403: ("DiseaseCondition", "صديد البول"),
    404: ("DiseaseCondition", "حمل"),
    406: ("DiseaseCondition", "ارتفاع ضغط الدماغ"),
    421: ("Symptom", "استمرار نزيف الدورة"),
    424: ("DiseaseCondition", "انتفاخ الرحم"),
    429: ("DiseaseCondition", "أضرار العادة السرية"),
    435: ("DiseaseCondition", "عدم تحمل اللاكتوز"),
    441: ("DiseaseCondition", "مقدمات السكري"),
    446: ("Treatment", "ماء غريب"),
    447: ("Treatment", "المورينجا"),
    448: ("Symptom", "ألم الضرس الشديد"),
    453: ("DiseaseCondition", "ضعف جودة السائل المنوي"),
    455: ("Symptom", "نزيف مهبلي"),
    465: ("Treatment", "بريمولوت نور"),
    467: ("DiseaseCondition", "إدمان العادة السرية"),
    468: ("DiseaseCondition", "ارتفاع هرمون الحليب"),
    474: ("Symptom", "رواسب التحاميل"),
    476: ("Test", "تحليل HIV"),
    480: ("DiseaseCondition", "الفطريات"),
    482: ("Symptom", "إفرازات بنية"),
    483: ("Test", "مراقبة ضغط الدم"),
    485: ("DiseaseCondition", "زكام"),
    490: ("DiseaseCondition", "غشاء البكارة"),
    493: ("DiseaseCondition", "اضطراب الدماغ"),
    495: ("Symptom", "ضعف التركيز"),
    499: ("DiseaseCondition", "غشاء البكارة"),
}


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


def main():
    rows = read_csv(INPUT)
    reviewed_rows = []
    ground_truth_rows = []
    changed_rows = 0

    for row in rows:
        row_id = int(row["row_id"])
        out = dict(row)

        if row["annotation_status"] == "reviewed_gold_available":
            final_type = row["reviewed_entity_type"]
            final_name = row["reviewed_canonical_name"]
            status = "reviewed_handoff"
            notes = "Original reviewed hand-off label."
        else:
            if row_id in ASSISTANT_OVERRIDES:
                final_type, final_name = ASSISTANT_OVERRIDES[row_id]
                changed_rows += 1
                notes = "Assistant override after source QA review."
            else:
                final_type = row["llama_pred_entity_type"]
                final_name = row["llama_pred_canonical_name"]
                notes = "Assistant accepted Llama candidate-rank pre-annotation after review."
            status = "assistant_reviewed"

        out["final_entity_type"] = final_type
        out["final_canonical_name"] = final_name
        out["annotation_status"] = status
        out["review_notes"] = notes
        reviewed_rows.append(out)

        ground_truth_rows.append(
            {
                "question": row["question"],
                "answer": row["answer"],
                "entity_type": final_type,
                "canonical_name": final_name,
            }
        )

    write_csv(REVIEWED_OUTPUT, reviewed_rows, list(reviewed_rows[0].keys()))
    write_csv(GROUND_TRUTH_OUTPUT, ground_truth_rows, ["question", "answer", "entity_type", "canonical_name"])
    print(
        json.dumps(
            {
                "rows": len(rows),
                "assistant_reviewed_rows": sum(1 for row in reviewed_rows if row["annotation_status"] == "assistant_reviewed"),
                "assistant_override_rows": changed_rows,
                "reviewed_output": relpath(REVIEWED_OUTPUT),
                "ground_truth_output": relpath(GROUND_TRUTH_OUTPUT),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
