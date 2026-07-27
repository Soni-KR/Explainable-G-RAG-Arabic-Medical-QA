import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
IMPORT_DIR = TRIAL_DIR / "import"
SUPP_DIR = TRIAL_DIR / "supplemental_facts"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_focused_supplemental_expansion_report.md"

QA_CSV = IMPORT_DIR / "trial_graph_v1_qa_sources.csv"
SUPP_ENTITIES_CSV = SUPP_DIR / "trial_graph_v1_supplemental_entities.csv"
SUPP_RELATIONS_CSV = SUPP_DIR / "trial_graph_v1_supplemental_relations.csv"
SUPP_QA_CSV = SUPP_DIR / "trial_graph_v1_supplemental_qa_sources.csv"
PROVENANCE_CSV = SUPP_DIR / "trial_graph_v1_supplemental_fact_provenance.csv"


FOCUSED_FACTS = [
    {
        "relation_id": "focus_rel_dental_filling_no_dimple_relation",
        "qa_id": "ahd5k_00484",
        "source": ("focus_ent_dental_filling", "حشو الأسنان", "Treatment", ["حشوة", "حشو الاسنان", "حشو الأسنان"]),
        "relation_type": "NOT_ASSOCIATED_WITH",
        "target": ("focus_ent_face_dimple", "غمازة الوجه", "BodyFeature", ["غمازة", "غمازه", "غمازة وجهي"]),
        "evidence": "لا توجد علاقة مرتبطة بين حشو الأسنان وغمازة الوجه حسب مصدر AHD.",
    },
    {
        "relation_id": "focus_rel_dental_anesthesia_temporary_dimple",
        "qa_id": "ahd5k_00484",
        "source": ("focus_ent_strong_local_anesthesia", "تخدير موضعي قوي", "Treatment", ["مخدر قوي", "تخدير المنطقة"]),
        "relation_type": "MAY_TEMPORARILY_AFFECT",
        "target": ("focus_ent_face_dimple", "غمازة الوجه", "BodyFeature", ["غمازة", "غمازه", "غمازة وجهي"]),
        "evidence": "إذا تم تخدير منطقة الغمازة بمخدر قوي وكمية كبيرة فقد تزول الحالة خلال 24-48 ساعة.",
    },
    {
        "relation_id": "focus_rel_hemorrhoid_surgery_urinary_pain_review",
        "qa_id": "ahd5k_00530",
        "source": ("focus_ent_hemorrhoid_surgery", "عملية البواسير", "Procedure", ["عملية بواسير", "جراحة البواسير"]),
        "relation_type": "REQUIRES_MEDICAL_REVIEW_FOR",
        "target": ("focus_ent_postop_urinary_pain_16_days", "استمرار صعوبة البول والألم بعد 16 يوم", "Symptom", ["صعوبة البول", "ألم المثانة", "ألم الخصيتان"]),
        "evidence": "استمرار الألم والمعاناة لمدة 16 يوما بعد عملية البواسير يبدو غير عادي ويستدعي مراجعة الجراح.",
    },
    {
        "relation_id": "focus_rel_anemia_managed_by_iron_rich_food",
        "qa_id": "ahd5k_00594",
        "source": ("focus_ent_anemia", "فقر الدم", "DiseaseCondition", ["انيميا", "أنيميا", "فقر دم"]),
        "relation_type": "MANAGED_BY",
        "target": ("focus_ent_iron_rich_foods", "أغذية غنية بالحديد والفولات وفيتامين ب12", "DietaryRecommendation", ["أغذية لفقر الدم", "أطعمة غنية بالحديد"]),
        "evidence": "يمكن دعم فقر الدم بنظام غذائي غني بعناصر مثل الحديد وحمض الفوليك وفيتامين ب-12، مع بقاء العلاج حسب نوع فقر الدم تحت إشراف الطبيب.",
    },
    {
        "relation_id": "focus_rel_iron_absorption_improved_by_vitamin_c",
        "qa_id": "ahd5k_00594",
        "source": ("focus_ent_iron_rich_foods", "أغذية غنية بالحديد والفولات وفيتامين ب12", "DietaryRecommendation", ["أغذية لفقر الدم", "أطعمة غنية بالحديد"]),
        "relation_type": "ABSORPTION_IMPROVED_BY",
        "target": ("focus_ent_vitamin_c_foods", "أطعمة غنية بفيتامين ج", "DietaryRecommendation", ["فيتامين ج", "فيتامين C", "برتقال", "طماطم", "فراولة"]),
        "evidence": "تناول الأطعمة الغنية بالحديد مع أطعمة غنية بفيتامين ج مثل البرتقال والطماطم والفراولة قد يحسن الامتصاص.",
    },
    {
        "relation_id": "focus_rel_iron_absorption_reduced_by_tea_coffee",
        "qa_id": "ahd5k_00594",
        "source": ("focus_ent_iron_rich_foods", "أغذية غنية بالحديد والفولات وفيتامين ب12", "DietaryRecommendation", ["أغذية لفقر الدم", "أطعمة غنية بالحديد"]),
        "relation_type": "ABSORPTION_REDUCED_BY",
        "target": ("focus_ent_tea_coffee_calcium", "الشاي والقهوة والكالسيوم مع الحديد", "DietaryCaution", ["الشاي", "القهوة", "الكالسيوم", "الحليب"]),
        "evidence": "ينصح بتجنب تناول الأطعمة الغنية بالحديد مع القهوة أو الشاي أو الأطعمة الغنية بالكالسيوم لأنها قد تمنع امتصاص الحديد.",
    },
    {
        "relation_id": "focus_rel_iron_injections_determined_by_hb",
        "qa_id": "ahd5k_01162",
        "source": ("focus_ent_iron_injections", "إبر الحديد", "Treatment", ["ابر الحديد", "إبر حديد", "حقن الحديد"]),
        "relation_type": "DOSE_DETERMINED_BY",
        "target": ("focus_ent_hb_and_iron_type", "نسبة الهيموغلوبين ونوع علاج الحديد", "ClinicalFactor", ["الهيموغلوبين", "نوع العلاج", "مخزون الحديد"]),
        "evidence": "تحديد طريقة وكمية علاج الحديد يعتمد على نسبة الهيموغلوبين ونوعية علاج الحديد.",
    },
    {
        "relation_id": "focus_rel_tooth_filing_risk_sensitivity",
        "qa_id": "ahd5k_00828",
        "source": ("focus_ent_tooth_filing", "برد الأسنان", "Procedure", ["برد الاسنان", "برد الأسنان"]),
        "relation_type": "HAS_RISK",
        "target": ("focus_ent_tooth_sensitivity", "حساسية الأسنان", "Symptom", ["حساسية الاسنان", "حساسية الأسنان"]),
        "evidence": "كثرة برد الأسنان قد تؤثر على الأسنان وتجعلها حساسة.",
    },
    {
        "relation_id": "focus_rel_tooth_filing_duration",
        "qa_id": "ahd5k_00828",
        "source": ("focus_ent_tooth_filing", "برد الأسنان", "Procedure", ["برد الاسنان", "برد الأسنان"]),
        "relation_type": "PROCEDURE_DURATION",
        "target": ("focus_ent_one_two_sessions", "جلسة واحدة أو جلستان", "ProcedureDuration", ["جلسة", "جلستين"]),
        "evidence": "برد الأسنان للتصغير قد يتم في جلسة واحدة، أما للتركيب وعمل أسنان صناعية فقد يحتاج جلسة أو جلستين.",
    },
    {
        "relation_id": "focus_rel_dyspnea_fatigue_possible_causes",
        "qa_id": "ahd5k_00855",
        "source": ("focus_ent_dyspnea_fatigue", "صعوبة التنفس والإرهاق", "Symptom", ["صعوبة التنفس", "الإرهاق", "الارهاق"]),
        "relation_type": "MAY_BE_ASSOCIATED_WITH",
        "target": ("focus_ent_respiratory_anemia_circulation", "التهاب تنفسي أو فقر دم أو اضطراب دموي أو دوراني", "PossibleCondition", ["التهاب الجهاز التنفسي", "فقر الدم", "اضطرابات دموية", "الدورة الدموية"]),
        "evidence": "صعوبة التنفس والإرهاق قد تكون ناجمة عن التهاب في الجهاز التنفسي أو فقر الدم أو اضطرابات دموية أو متعلقة بجهاز الدورة الدموية.",
    },
    {
        "relation_id": "focus_rel_dyspnea_fatigue_investigated_by_exam",
        "qa_id": "ahd5k_00855",
        "source": ("focus_ent_dyspnea_fatigue", "صعوبة التنفس والإرهاق", "Symptom", ["صعوبة التنفس", "الإرهاق", "الارهاق"]),
        "relation_type": "INVESTIGATED_BY",
        "target": ("focus_ent_history_physical_exam", "التاريخ المرضي والفحص السريري", "DiagnosticProcedure", ["التاريخ المرضي", "الفحص السريري", "فحص طبي"]),
        "evidence": "ينبغي معرفة التاريخ المرضي وإجراء فحص للكشف عن علامات سريرية تساعد في تحديد طبيعة الحالة.",
    },
    {
        "relation_id": "focus_rel_ovulation_stimulation_no_harm",
        "qa_id": "ahd5k_01770",
        "source": ("focus_ent_ovulation_stimulation_hormones", "تنشيط المبايض", "Treatment", ["تنشيط المبايض", "تنشيط الإباضة", "منشطات المبايض", "هرمونات تنشيط الإباضة"]),
        "relation_type": "HAS_SAFETY_NOTE",
        "target": ("focus_ent_no_reported_harm_ivf", "لا يوجد تأثير مضر مذكور قبل الحقن المجهري", "SafetyFinding", ["لا يوجد ضرر", "الحقن المجهري"]),
        "evidence": "حسب الخبرات والدراسات في مصدر AHD لا يوجد تأثير مضر للهرمونات المستخدمة في تنشيط الإباضة قبل الحقن المجهري.",
    },
    {
        "relation_id": "focus_rel_crp_wbc_may_indicate_inflammation",
        "qa_id": "ahd5k_02627",
        "source": ("focus_ent_high_crp_wbc", "ارتفاع CRP وكريات الدم البيضاء", "LabFinding", ["CRP", "كريات الدم البيضاء", "ارتفاع التحليل"]),
        "relation_type": "MAY_INDICATE",
        "target": ("focus_ent_inflammation", "التهاب", "DiseaseCondition", ["التهاب", "انفلونزا", "التهاب اللثة"]),
        "evidence": "ارتفاع CRP وكذلك كريات الدم البيضاء قد يدل على وجود التهاب مثل الإنفلونزا أو التهاب اللثة وغيرها.",
    },
    {
        "relation_id": "focus_rel_wbc_pregnancy_normal_range",
        "qa_id": "ahd5k_02627",
        "source": ("focus_ent_wbc_pregnancy", "كريات الدم البيضاء أثناء الحمل", "LabFinding", ["كريات الدم البيضاء", "الحمل"]),
        "relation_type": "HAS_NORMAL_RANGE",
        "target": ("focus_ent_wbc_16000_pregnancy", "حتى 16000 أثناء الحمل وقد تصل 20000 أثناء الولادة", "Range", ["16000", "20000", "الولادة"]),
        "evidence": "ارتفاع كريات الدم البيضاء حتى 16000 قد يعتبر طبيعيا أثناء الحمل وقد يصل أثناء الولادة إلى 20000 حسب مصدر AHD.",
    },
]


def relpath(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_csv(path):
    if not path.exists():
        return []
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


def json_list(values):
    return json.dumps(list(values), ensure_ascii=False)


def qa_index():
    return {row["qa_id"]: row for row in read_csv(QA_CSV)}


def entity_row(entity, qa_id):
    entity_id, name, entity_type, aliases = entity
    return {
        "entity_id": entity_id,
        "canonical_name": name,
        "canonical_name_norm": normalize_arabic_light(name),
        "entity_type": entity_type,
        "entity_quality": "dataset_derived_focused",
        "is_actionable_medical_entity": "true",
        "aliases": json_list(aliases),
        "mention_count": "1",
        "source_chunk_count": "1",
        "qa_count": "1",
        "avg_confidence": "0.97",
        "source_chunks": json_list([f"dataset_{qa_id}"]),
        "source_models": json_list(["focused_dataset_extraction"]),
        "qa_ids": json_list([qa_id]),
    }


def relation_row(fact):
    relation_id = fact["relation_id"]
    source_id, source_name, source_type, _ = fact["source"]
    target_id, target_name, target_type, _ = fact["target"]
    return {
        "relation_id": relation_id,
        "chunk_id": f"focus_chunk_{fact['qa_id']}",
        "qa_id": fact["qa_id"],
        "candidate_relation_type": fact["relation_type"],
        "validated_relation_type": fact["relation_type"],
        "keep": "true",
        "source_entity_id": source_id,
        "source_name": source_name,
        "source_type": source_type,
        "target_entity_id": target_id,
        "target_name": target_name,
        "target_type": target_type,
        "evidence": fact["evidence"],
        "confidence": "0.97",
        "reason": f"focused dataset-derived expansion from {fact['qa_id']}",
        "provider": "focused_dataset_extraction",
        "model": "ahd_qa_source",
        "edge_id": relation_id,
        "original_relation_id": relation_id,
        "graph_relation_type": fact["relation_type"],
        "edge_direction": "direct",
    }


def qa_source_row(qa):
    question = qa.get("question", "")
    answer = qa.get("answer", "")
    return {
        "qa_id": qa.get("qa_id", ""),
        "source_row_number": qa.get("source_row_number", ""),
        "split": qa.get("split", ""),
        "category": qa.get("category", ""),
        "category_en": qa.get("category_en", ""),
        "question": question,
        "answer": answer,
        "question_norm": qa.get("question_norm", ""),
        "answer_norm": qa.get("answer_norm", ""),
        "qa_char_len": qa.get("qa_char_len") or str(len(question) + len(answer)),
    }


def upsert_by_key(rows, new_rows, key):
    merged = {row[key]: row for row in rows if row.get(key)}
    for row in new_rows:
        merged[row[key]] = row
    return list(merged.values())


def append_provenance(existing_rows, facts, qas):
    new_rows = []
    for fact in facts:
        qa = qas.get(fact["qa_id"], {})
        new_rows.append(
            {
                "relation_id": fact["relation_id"],
                "provenance_status": "dataset_derived_focused",
                "dataset_qa_id": fact["qa_id"],
                "source_question": qa.get("question", ""),
                "source_answer": qa.get("answer", ""),
                "notes": fact["evidence"],
            }
        )
    return upsert_by_key(existing_rows, new_rows, "relation_id")


def write_report(added_relations, added_entities, added_qas):
    lines = [
        "# Focused Supplemental Expansion Report",
        "",
        "This step converts high-confidence AHD-backed facts discovered from low-evidence failures into reusable supplemental graph facts.",
        "These facts should be evaluated on a fresh unseen query offset to avoid measuring on the same failures used for discovery.",
        "",
        f"- Focused relations upserted: {len(added_relations)}",
        f"- Focused entities upserted: {len(added_entities)}",
        f"- AHD QA source records upserted: {len(added_qas)}",
        f"- Supplemental relations: `{relpath(SUPP_RELATIONS_CSV)}`",
        f"- Supplemental entities: `{relpath(SUPP_ENTITIES_CSV)}`",
        f"- Supplemental QA sources: `{relpath(SUPP_QA_CSV)}`",
        "",
        "## Added Relations",
        "",
    ]
    for row in added_relations:
        lines.append(
            f"- `{row['relation_id']}`: {row['source_name']} --{row['graph_relation_type']}--> {row['target_name']} (`{row['qa_id']}`)"
        )
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    qas = qa_index()
    missing_qas = sorted({fact["qa_id"] for fact in FOCUSED_FACTS if fact["qa_id"] not in qas})
    if missing_qas:
        raise SystemExit(f"Missing source QA rows: {missing_qas}")

    existing_entities = read_csv(SUPP_ENTITIES_CSV)
    existing_relations = read_csv(SUPP_RELATIONS_CSV)
    existing_qa_sources = read_csv(SUPP_QA_CSV)
    existing_provenance = read_csv(PROVENANCE_CSV)

    focused_entities = []
    seen_entities = set()
    for fact in FOCUSED_FACTS:
        for entity in (fact["source"], fact["target"]):
            if entity[0] in seen_entities:
                continue
            seen_entities.add(entity[0])
            focused_entities.append(entity_row(entity, fact["qa_id"]))

    focused_relations = [relation_row(fact) for fact in FOCUSED_FACTS]
    focused_qa_sources = [qa_source_row(qas[qa_id]) for qa_id in sorted({fact["qa_id"] for fact in FOCUSED_FACTS})]

    entities = upsert_by_key(existing_entities, focused_entities, "entity_id")
    relations = upsert_by_key(existing_relations, focused_relations, "relation_id")
    qa_sources = upsert_by_key(existing_qa_sources, focused_qa_sources, "qa_id")
    provenance = append_provenance(existing_provenance, FOCUSED_FACTS, qas)

    write_csv(SUPP_ENTITIES_CSV, entities, existing_entities[0].keys())
    write_csv(SUPP_RELATIONS_CSV, relations, existing_relations[0].keys())
    write_csv(SUPP_QA_CSV, qa_sources, existing_qa_sources[0].keys())
    write_csv(PROVENANCE_CSV, provenance, existing_provenance[0].keys())
    write_report(focused_relations, focused_entities, focused_qa_sources)

    print(
        json.dumps(
            {
                "focused_relations_upserted": len(focused_relations),
                "focused_entities_upserted": len(focused_entities),
                "focused_qa_sources_upserted": len(focused_qa_sources),
                "supplemental_relations_total": len(relations),
                "supplemental_entities_total": len(entities),
                "supplemental_qa_sources_total": len(qa_sources),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
