import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
IMPORT_DIR = TRIAL_DIR / "import"
SUPP_DIR = TRIAL_DIR / "supplemental_facts"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_supplemental_fact_provenance_report.md"

QA_CSV = IMPORT_DIR / "trial_graph_v1_qa_sources.csv"
SUPP_ENTITIES_CSV = SUPP_DIR / "trial_graph_v1_supplemental_entities.csv"
SUPP_RELATIONS_CSV = SUPP_DIR / "trial_graph_v1_supplemental_relations.csv"
PROVENANCE_CSV = SUPP_DIR / "trial_graph_v1_supplemental_fact_provenance.csv"


DATASET_EVIDENCE_MAP = {
    "supp_rel_normal_bp": {
        "qa_id": "ahd5k_00085",
        "target_name": "140-80 إذا لا توجد أمراض مصاحبة",
        "evidence_summary": "حسب عوامل الخطورة الأخرى كالسكري والكلى؛ إذا لا توجد أمراض مصاحبة فالقيمة المذكورة 140-80.",
    },
    "supp_rel_normal_hr": {
        "qa_id": "ahd5k_00085",
        "target_name": "65-85 تقريبا وقد يقبل أقل أو أكثر",
        "evidence_summary": "ضربات القلب تقريبا من 65-85، ويمكن قبول أقل أو أكثر حسب الحالة.",
    },
    "supp_rel_diclofenac_side_effect": {
        "qa_id": "ahd5k_00065",
        "evidence_summary": "الأولفين هو نفس فولتارين ويحتويان على ديكلوفيناك، ولهم نفس الأعراض الجانبية، وينصح بأخذه بعد الأكل لتقليل تهيج الجهاز الهضمي.",
    },
    "supp_rel_diclofenac_supervision": {
        "qa_id": "ahd5k_00065",
        "evidence_summary": "في حال الشقيقة الشديدة توجد أدوية أخرى ويذكر المصدر إمكانية استشارة الطبيب لذلك.",
    },
    "supp_rel_primolut_pregnancy": {
        "qa_id": "ahd5k_00439",
        "target_name": "إيقاف الدواء ومراجعة الطبيب أثناء الحمل",
        "evidence_summary": "إذا كانت المريضة حاملا وتستعمل بريمولوت ن فيجب إيقافه؛ يذكر المصدر دراسات عن احتمال تشوهات في القلب والأوعية والأنبوب العصبي والدماغ.",
    },
    "supp_rel_dental_aftercare": {
        "qa_id": "ahd5k_00315",
        "target_name": "يمكن شرب القهوة والشاي مع المحافظة على تنظيف الأسنان",
        "evidence_summary": "إجابة المصدر تقول: اشربي قهوتك وشايك على راحتك مع المحافظة على تنظيف الأسنان.",
    },
    "supp_rel_tsh_interprets": {
        "qa_id": "ahd5k_02685",
        "evidence_summary": "قيمة TSH بعد الولادة ترتبط باضطراب نشاط الغدة الدرقية، ويذكر المصدر ضرورة المتابعة تحت إشراف أخصائي الغدد الصم.",
    },
    "supp_rel_cholesterol_lifestyle": {
        "qa_id": "ahd5k_00171",
        "evidence_summary": "طرق تخفيض الكوليسترول بدون دواء تعتمد على الجهد والتمارين خاصة المشي والحمية وتجنب الدهون الحيوانية والمقليات.",
    },
    "supp_rel_kidney_stones_management": {
        "qa_id": "ahd5k_00012",
        "evidence_summary": "التخلص من الحصى يبدأ بدراستها لمعرفة مكانها وحجمها وطبيعتها ثم يقرر الطبيب كيفية التخلص منها.",
    },
    "supp_rel_ibs_management": {
        "qa_id": "ahd5k_01998",
        "evidence_summary": "تبدو الأعراض كقولون عصبي؛ يذكر المصدر تجنب التفكير والقلق والنرفزة وتغيير أنماط تناول الطعام ونوعية الأطعمة.",
    },
    "supp_rel_fetal_bones_timeline": {
        "qa_id": "ahd5k_00230",
        "target_name": "نهاية الأسبوع السادس تقريبا",
        "evidence_summary": "في نهاية الأسبوع السادس يبدأ الجنين بتكوين العمود الفقري ويكون صغيرا جدا.",
    },
    "supp_rel_mouth_fungus_treated": {
        "qa_id": "ahd5k_00142",
        "target_name": "مراجعة طبيب اختصاصي لتأكيد التشخيص",
        "evidence_summary": "يوصي المصدر بالذهاب إلى طبيب اختصاصي لمعرفة التشخيص الحقيقي: هل هو فطريات أو نقص فيتامينات أو سبب آخر.",
    },
}


TARGET_ENTITY_UPDATES = {
    "supp_ent_range_bp": "140-80 إذا لا توجد أمراض مصاحبة",
    "supp_ent_range_hr": "65-85 تقريبا وقد يقبل أقل أو أكثر",
    "supp_ent_aftercare_coffee": "يمكن شرب القهوة والشاي مع المحافظة على تنظيف الأسنان",
    "supp_ent_state_pregnancy": "إيقاف الدواء ومراجعة الطبيب أثناء الحمل",
    "supp_ent_pregnancy_second_month": "نهاية الأسبوع السادس تقريبا",
    "supp_ent_mouth_fungus_eval": "مراجعة طبيب اختصاصي لتأكيد التشخيص",
}


def relpath(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_arabic_light(value):
    return (
        str(value or "")
        .replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ة", "ه")
        .replace("ى", "ي")
        .strip()
        .lower()
    )


def qa_index():
    return {row["qa_id"]: row for row in read_csv(QA_CSV)}


def update_entities(relations, qas):
    rows = read_csv(SUPP_ENTITIES_CSV)
    qa_ids_by_entity = {}
    for relation in relations:
        qa_id = relation.get("qa_id", "")
        if not qa_id:
            continue
        qa_ids_by_entity.setdefault(relation.get("source_entity_id", ""), set()).add(qa_id)
        qa_ids_by_entity.setdefault(relation.get("target_entity_id", ""), set()).add(qa_id)

    for row in rows:
        entity_id = row["entity_id"]
        if entity_id in TARGET_ENTITY_UPDATES:
            row["canonical_name"] = TARGET_ENTITY_UPDATES[entity_id]
            row["canonical_name_norm"] = normalize_arabic_light(TARGET_ENTITY_UPDATES[entity_id])
        if entity_id in qa_ids_by_entity:
            ids = sorted(qa_ids_by_entity[entity_id])
            row["qa_ids"] = json.dumps(ids, ensure_ascii=False)
            row["qa_count"] = str(len(ids))
            row["source_models"] = json.dumps(["dataset_derived"], ensure_ascii=False)
            row["source_chunks"] = json.dumps([f"dataset_{qa_id}" for qa_id in ids], ensure_ascii=False)
            row["entity_quality"] = "dataset_derived"
            row["avg_confidence"] = "0.99"
    write_csv(SUPP_ENTITIES_CSV, rows, rows[0].keys())


def update_relations():
    qas = qa_index()
    rows = read_csv(SUPP_RELATIONS_CSV)
    provenance_rows = []
    for row in rows:
        update = DATASET_EVIDENCE_MAP.get(row["relation_id"])
        if not update:
            provenance_rows.append(
                {
                    "relation_id": row["relation_id"],
                    "provenance_status": "manual_only",
                    "dataset_qa_id": "",
                    "source_question": "",
                    "source_answer": "",
                    "notes": "No dataset evidence mapping found.",
                }
            )
            continue
        qa = qas.get(update["qa_id"], {})
        if update.get("target_name"):
            row["target_name"] = update["target_name"]
        row["qa_id"] = update["qa_id"]
        row["evidence"] = update["evidence_summary"]
        row["confidence"] = "0.99"
        row["reason"] = f"dataset-derived supplemental fact from {update['qa_id']}"
        row["provider"] = "dataset_derived"
        row["model"] = "ahd_qa_source"
        provenance_rows.append(
            {
                "relation_id": row["relation_id"],
                "provenance_status": "dataset_derived",
                "dataset_qa_id": update["qa_id"],
                "source_question": qa.get("question", ""),
                "source_answer": qa.get("answer", ""),
                "notes": update["evidence_summary"],
            }
        )
    write_csv(SUPP_RELATIONS_CSV, rows, rows[0].keys())
    write_csv(
        PROVENANCE_CSV,
        provenance_rows,
        ["relation_id", "provenance_status", "dataset_qa_id", "source_question", "source_answer", "notes"],
    )
    update_entities(rows, qas)
    return rows, provenance_rows


def write_report(provenance_rows):
    dataset_count = sum(1 for row in provenance_rows if row["provenance_status"] == "dataset_derived")
    manual_count = sum(1 for row in provenance_rows if row["provenance_status"] != "dataset_derived")
    lines = [
        "# Supplemental Fact Provenance Report",
        "",
        "This report documents whether each supplemental fact is supported by local AHD dataset QA evidence.",
        "",
        f"- Dataset-derived supplemental facts: {dataset_count}",
        f"- Manual-only supplemental facts: {manual_count}",
        f"- Provenance CSV: `{relpath(PROVENANCE_CSV)}`",
        f"- Updated supplemental relations: `{relpath(SUPP_RELATIONS_CSV)}`",
        f"- Updated supplemental entities: `{relpath(SUPP_ENTITIES_CSV)}`",
        "",
        "## Dataset-Derived Facts",
        "",
    ]
    for row in provenance_rows:
        lines.append(f"- `{row['relation_id']}` -> `{row['dataset_qa_id']}`: {row['notes']}")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    _, provenance_rows = update_relations()
    write_report(provenance_rows)
    dataset_count = sum(1 for row in provenance_rows if row["provenance_status"] == "dataset_derived")
    manual_count = len(provenance_rows) - dataset_count
    print(
        json.dumps(
            {
                "supplemental_facts": len(provenance_rows),
                "dataset_derived": dataset_count,
                "manual_only": manual_count,
                "provenance_csv": relpath(PROVENANCE_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
