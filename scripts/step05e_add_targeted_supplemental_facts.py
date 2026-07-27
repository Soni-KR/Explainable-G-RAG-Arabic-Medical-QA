import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
IMPORT_DIR = TRIAL_DIR / "import"
SUPP_DIR = TRIAL_DIR / "supplemental_facts"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_targeted_supplemental_facts_report.md"

QA_CSV = IMPORT_DIR / "trial_graph_v1_qa_sources.csv"
SUPP_ENTITIES_CSV = SUPP_DIR / "trial_graph_v1_supplemental_entities.csv"
SUPP_RELATIONS_CSV = SUPP_DIR / "trial_graph_v1_supplemental_relations.csv"
SUPP_QA_CSV = SUPP_DIR / "trial_graph_v1_supplemental_qa_sources.csv"
PROVENANCE_CSV = SUPP_DIR / "trial_graph_v1_supplemental_fact_provenance.csv"


TARGETED_FACTS = [
    {
        "relation_id": "target_rel_thyroid_pregnancy_fetal_growth",
        "qa_id": "ahd5k_00048",
        "source": ("target_ent_thyroid_hormone_pregnancy", "هرمون الثيروكسين أثناء الحمل", "Hormone", ["الغدة", "الغدة الدرقية", "هرمون الغدة", "الثيروكسين", "التروكسين"]),
        "relation_type": "IMPORTANT_FOR",
        "target": ("target_ent_fetal_mental_physical_growth", "نمو الجنين العقلي والجسدي", "DevelopmentProcess", ["نمو الجنين", "الجنين", "نمو عقلي", "نمو جسدي"]),
        "evidence": "هرمون الثيروكسين مهم لنمو الجنين العقلي والجسدي أثناء الحمل.",
    },
    {
        "relation_id": "target_rel_hypothyroidism_pregnancy_birth_defects",
        "qa_id": "ahd5k_00048",
        "source": ("target_ent_untreated_hypothyroidism_pregnancy", "خمول الغدة الدرقية غير المعالج أثناء الحمل", "DiseaseCondition", ["خمول الغدة", "خمول الغدة الدرقية", "نقص افراز هرمون الغدة", "الغدة والحمل"]),
        "relation_type": "MAY_CAUSE_IF_UNTREATED",
        "target": ("target_ent_fetal_congenital_effects", "تشوهات خلقية أو تقزم الجنين", "Risk", ["تشوهات خلقية", "تشوهات الجنين", "تقزم", "تأثير على الجنين"]),
        "evidence": "نقص إفراز هرمون الغدة الدرقية إذا لم يعالج لمدة طويلة أثناء الحمل، خاصة في الثلث الثاني والثالث، قد يؤدي إلى تشوهات خلقية وحالات تقزم.",
    },
    {
        "relation_id": "target_rel_hemorrhoid_surgery_urinary_symptoms_review",
        "qa_id": "ahd5k_00530",
        "source": ("target_ent_post_hemorrhoid_surgery", "بعد عملية البواسير", "ProcedureContext", ["عملية بواسير", "عملية البواسير", "بعد عملية البواسير"]),
        "relation_type": "REQUIRES_MEDICAL_REVIEW_FOR",
        "target": ("target_ent_persistent_urinary_pain_16_days", "استمرار صعوبة البول والألم بعد 16 يوما", "Symptom", ["صعوبة البول", "ألم المثانة", "ألم الخصيتان", "الم بعد عملية البواسير"]),
        "evidence": "استمرار الألم والمعاناة لمدة 16 يوما بعد عملية البواسير يبدو غير عادي ويستدعي مراجعة الجراح الذي أجرى العملية.",
    },
    {
        "relation_id": "target_rel_anemia_foods_iron_folate_b12",
        "qa_id": "ahd5k_00594",
        "source": ("target_ent_anemia_nutrition", "فقر الدم", "DiseaseCondition", ["فقر دم", "فقر الدم", "انيميا", "أنيميا"]),
        "relation_type": "MANAGED_BY",
        "target": ("target_ent_iron_folate_b12_foods", "غذاء غني بالحديد والفولات وفيتامين ب12", "DietaryRecommendation", ["أغذية مفيدة لفقر الدم", "اطعمة غنية بالحديد", "حمض الفوليك", "فيتامين ب12"]),
        "evidence": "يمكن دعم فقر الدم باتباع نظام غذائي غني بالعناصر اللازمة لتعويض النقص مثل الحديد وحمض الفوليك وفيتامين ب-12، مع تحديد العلاج حسب نوع فقر الدم.",
    },
    {
        "relation_id": "target_rel_open_heart_postop_weakness_needs_doctor",
        "qa_id": "ahd5k_01704",
        "source": ("target_ent_open_heart_surgery", "عملية القلب المفتوح", "Procedure", ["عملية القلب المفتوح", "تبديل شرايين", "تبديل الصمام", "جراحة القلب"]),
        "relation_type": "REQUIRES_SPECIALIST_ASSESSMENT_FOR",
        "target": ("target_ent_postop_weakness_after_cardiac_surgery", "الضعف بعد جراحة القلب", "Symptom", ["ضعف بعد العملية", "ضعف بعد القلب المفتوح", "تعب بعد العملية"]),
        "evidence": "تقدير الحالة بعد عملية القلب المفتوح يحتاج إلى الطبيب المطلع على تفاصيل الحالة.",
    },
    {
        "relation_id": "target_rel_cardiac_surgery_decision_depends_on_function",
        "qa_id": "ahd5k_04912",
        "source": ("target_ent_coronary_stenosis_weak_heart", "ضعف عضلة القلب وضيق الشرايين", "DiseaseCondition", ["ضعف عضلة القلب", "ضيق الشرايين", "انسداد الشرايين", "ثلاث شرايين"]),
        "relation_type": "ASSESSMENT_DEPENDS_ON",
        "target": ("target_ent_cardiac_team_assessment", "تقييم الفريق الطبي ووظائف الأعضاء", "ClinicalAssessment", ["تقييم طبي", "نتائج القثطرة", "وظائف الكلى", "وظائف الجهاز التنفسي"]),
        "evidence": "تحديد العلاج أو الجراحة في ضعف عضلة القلب وضيق الشرايين يتطلب معرفة نسبة الضعف والتضيق والحالة الوظيفية لباقي أعضاء الجسم، ثم تقييم الفريق الطبي.",
    },
    {
        "relation_id": "target_rel_cephadar_tooth_pain_needs_analgesic",
        "qa_id": "ahd5k_00625",
        "source": ("target_ent_cephadar_forte", "Cephadar forte", "Drug", ["cephadar", "Cephadar", "cephadar forte", "سيفادار", "سيفادار فورت"]),
        "relation_type": "USED_WITH_FOR_TOOTH_PAIN",
        "target": ("target_ent_tooth_pain_analgesic", "مسكن ألم الأسنان", "Treatment", ["ألم الأسنان", "الام الاسنان", "مسكن ألم", "Brufen", "بروفين"]),
        "evidence": "في مصدر AHD، يمكن أخذ Cephadar forte لألم الأسنان، لكن الحالة تحتاج أيضا إلى مسكن ألم مثل Brufen.",
    },
    {
        "relation_id": "target_rel_dyspnea_fatigue_possible_causes",
        "qa_id": "ahd5k_00855",
        "source": ("target_ent_dyspnea_fatigue", "صعوبة التنفس والإرهاق", "Symptom", ["صعوبة التنفس", "ضيق التنفس", "الإرهاق", "الارهاق", "سرعة التعب"]),
        "relation_type": "MAY_BE_ASSOCIATED_WITH",
        "target": ("target_ent_respiratory_anemia_circulation_causes", "التهاب تنفسي أو فقر دم أو اضطراب دموي أو دوراني", "PossibleCondition", ["التهاب الجهاز التنفسي", "فقر الدم", "اضطرابات دموية", "جهاز الدورة الدموية"]),
        "evidence": "صعوبة التنفس والإرهاق قد تكون ناجمة عن التهاب في الجهاز التنفسي، أو فقر الدم، أو اضطرابات دموية، أو مشكلة متعلقة بجهاز الدورة الدموية.",
    },
    {
        "relation_id": "target_rel_dyspnea_fatigue_investigated_by_exam",
        "qa_id": "ahd5k_00855",
        "source": ("target_ent_dyspnea_fatigue", "صعوبة التنفس والإرهاق", "Symptom", ["صعوبة التنفس", "ضيق التنفس", "الإرهاق", "الارهاق", "سرعة التعب"]),
        "relation_type": "INVESTIGATED_BY",
        "target": ("target_ent_history_physical_exam", "التاريخ المرضي والفحص السريري", "DiagnosticProcedure", ["التاريخ المرضي", "الفحص السريري", "فحص طبي"]),
        "evidence": "ينبغي معرفة التاريخ المرضي وإجراء فحص للكشف عن علامات سريرية تساعد في تحديد طبيعة الحالة.",
    },
    {
        "relation_id": "target_rel_ectopic_beats_causes_thyroid_anemia",
        "qa_id": "ahd5k_00189",
        "source": ("target_ent_ectopic_heart_beats", "الضربات الهاجرة في القلب", "Symptom", ["ضربات هاجرة", "الضربات الهاجرة", "خفقان", "نبضات قوية"]),
        "relation_type": "MAY_BE_ASSOCIATED_WITH",
        "target": ("target_ent_thyroid_anemia_multiple_causes", "اضطراب الغدة الدرقية أو فقر الدم أو أسباب متعددة", "PossibleCondition", ["الغدة الدرقية", "فقر الدم", "أسباب متعددة"]),
        "evidence": "أسباب الضربات الهاجرة كثيرة، وقد تكون عرضا ثانويا لاضطراب يتعلق بالغدة الدرقية أو فقر الدم أو أسباب أخرى متعددة.",
    },
    {
        "relation_id": "target_rel_ectopic_beats_treatment_depends_diagnosis",
        "qa_id": "ahd5k_00189",
        "source": ("target_ent_ectopic_heart_beats", "الضربات الهاجرة في القلب", "Symptom", ["ضربات هاجرة", "الضربات الهاجرة", "خفقان", "نبضات قوية"]),
        "relation_type": "TREATMENT_DEPENDS_ON",
        "target": ("target_ent_precise_arrhythmia_diagnosis", "التشخيص الدقيق لنوع اضطراب النظم", "ClinicalAssessment", ["التشخيص الدقيق", "تشخيص اضطراب النظم", "فئة الضربات"]),
        "evidence": "علاج الضربات الهاجرة مرتبط بالتشخيص الدقيق لفئتها بعد تقييم السبب.",
    },
    {
        "relation_id": "target_rel_ovulation_stimulation_no_reported_harm",
        "qa_id": "ahd5k_01770",
        "source": ("target_ent_ovulation_stimulation_before_ivf", "تنشيط المبايض قبل الحقن المجهري", "Treatment", ["تنشيط المبايض", "تنشيط الاباضة", "منشطات المبايض", "الحقن المجهري"]),
        "relation_type": "HAS_SAFETY_NOTE",
        "target": ("target_ent_no_harm_ovulation_hormones", "لا يوجد تأثير مضر مذكور للهرمونات", "SafetyFinding", ["لا يوجد ضرر", "تأثير مضر", "هرمونات التنشيط"]),
        "evidence": "حسب الخبرات والدراسات المذكورة في مصدر AHD، لا يوجد تأثير مضر للهرمونات المستخدمة في تنشيط الإباضة قبل الحقن المجهري.",
    },
    {
        "relation_id": "target_rel_impacted_wisdom_tooth_head_eye_ear",
        "qa_id": "ahd5k_00507",
        "source": ("target_ent_impacted_wisdom_tooth", "ضرس العقل المطمور", "DiseaseCondition", ["ضرس العقل", "ضرس عقل مطمور", "ضرس مطمور", "انتفاخ ضرس العقل"]),
        "relation_type": "MAY_REQUIRE",
        "target": ("target_ent_oral_maxillofacial_dentist", "طبيب أسنان أو جراح وجه وفكين", "Specialist", ["طبيب الأسنان", "جراح وجه وفكين", "إزالة ضرس العقل"]),
        "evidence": "إذا وجد ضرس عقل مطمور، فمن الأفضل إزالته لدى طبيب أسنان متمرس أو طبيب جراح وجه وفكين.",
    },
    {
        "relation_id": "target_rel_left_chest_pain_not_always_heart",
        "qa_id": "ahd5k_04975",
        "source": ("target_ent_left_chest_back_pain", "نغزات الجهة اليسرى من الصدر والظهر", "Symptom", ["نغزات الصدر", "ألم الصدر الأيسر", "ألم الظهر", "الجهة اليسرى"]),
        "relation_type": "NOT_ALWAYS_INDICATES",
        "target": ("target_ent_heart_source", "مصدر قلبي", "PossibleCondition", ["القلب", "أمراض القلب", "مصدر القلب"]),
        "evidence": "ليس كل ألم في هذه المنطقة يعني أن مصدره القلب؛ فقد تسبب الأنسجة الجلدية أو العضلية أو الهيكلية ألما مشابها، ويلزم فحص سريري لمعرفة السبب.",
    },
    {
        "relation_id": "target_rel_cholesterol_needs_lipid_profile",
        "qa_id": "ahd5k_00171",
        "source": ("target_ent_high_cholesterol", "ارتفاع الكوليسترول", "DiseaseCondition", ["الكوليسترول", "ارتفاع الكوليسترول", "دهون الدم", "الدهون الثلاثية"]),
        "relation_type": "INVESTIGATED_BY",
        "target": ("target_ent_lipid_profile_weight_chronic_disease", "فحص الدهون وتقييم الوزن والأمراض المزمنة", "ClinicalAssessment", ["فحص الدهون", "الكوليسترول الحميد", "الدهون الثلاثية", "الوزن", "مرض مزمن"]),
        "evidence": "تخفيض الكوليسترول يتطلب أولا معرفة نوع الارتفاع والدهون الثلاثية والكوليسترول الحميد، إضافة إلى تقييم الوزن والأمراض المزمنة.",
    },
]


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


def json_list(values):
    return json.dumps(list(values), ensure_ascii=False)


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


def upsert_by_key(rows, new_rows, key):
    merged = {row[key]: row for row in rows if row.get(key)}
    for row in new_rows:
        merged[row[key]] = row
    return list(merged.values())


def entity_row(entity, qa_id):
    entity_id, name, entity_type, aliases = entity
    return {
        "entity_id": entity_id,
        "canonical_name": name,
        "canonical_name_norm": normalize_arabic_light(name),
        "entity_type": entity_type,
        "entity_quality": "dataset_derived_targeted",
        "is_actionable_medical_entity": "true",
        "aliases": json_list(aliases),
        "mention_count": "1",
        "source_chunk_count": "1",
        "qa_count": "1",
        "avg_confidence": "0.98",
        "source_chunks": json_list([f"targeted_{qa_id}"]),
        "source_models": json_list(["targeted_dataset_review"]),
        "qa_ids": json_list([qa_id]),
    }


def relation_row(fact):
    source_id, source_name, source_type, _ = fact["source"]
    target_id, target_name, target_type, _ = fact["target"]
    return {
        "relation_id": fact["relation_id"],
        "chunk_id": f"targeted_chunk_{fact['qa_id']}",
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
        "confidence": "0.98",
        "reason": f"targeted dataset-derived expansion from {fact['qa_id']}",
        "provider": "targeted_dataset_review",
        "model": "ahd_qa_source",
        "edge_id": fact["relation_id"],
        "original_relation_id": fact["relation_id"],
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


def provenance_row(fact, qa):
    return {
        "relation_id": fact["relation_id"],
        "provenance_status": "dataset_derived_targeted",
        "dataset_qa_id": fact["qa_id"],
        "source_question": qa.get("question", ""),
        "source_answer": qa.get("answer", ""),
        "notes": fact["evidence"],
    }


def main():
    qa_by_id = {row["qa_id"]: row for row in read_csv(QA_CSV)}
    missing = sorted({fact["qa_id"] for fact in TARGETED_FACTS if fact["qa_id"] not in qa_by_id})
    if missing:
        raise SystemExit(f"Missing QA source rows: {missing}")

    existing_entities = read_csv(SUPP_ENTITIES_CSV)
    existing_relations = read_csv(SUPP_RELATIONS_CSV)
    existing_qas = read_csv(SUPP_QA_CSV)
    existing_provenance = read_csv(PROVENANCE_CSV)

    new_entities = []
    for fact in TARGETED_FACTS:
        new_entities.append(entity_row(fact["source"], fact["qa_id"]))
        new_entities.append(entity_row(fact["target"], fact["qa_id"]))
    new_relations = [relation_row(fact) for fact in TARGETED_FACTS]
    new_qas = [qa_source_row(qa_by_id[qa_id]) for qa_id in sorted({fact["qa_id"] for fact in TARGETED_FACTS})]
    new_provenance = [provenance_row(fact, qa_by_id[fact["qa_id"]]) for fact in TARGETED_FACTS]

    merged_entities = upsert_by_key(existing_entities, new_entities, "entity_id")
    merged_relations = upsert_by_key(existing_relations, new_relations, "relation_id")
    merged_qas = upsert_by_key(existing_qas, new_qas, "qa_id")
    merged_provenance = upsert_by_key(existing_provenance, new_provenance, "relation_id")

    entity_fields = list(existing_entities[0].keys()) if existing_entities else list(new_entities[0].keys())
    relation_fields = list(existing_relations[0].keys()) if existing_relations else list(new_relations[0].keys())
    qa_fields = list(existing_qas[0].keys()) if existing_qas else list(new_qas[0].keys())
    provenance_fields = list(existing_provenance[0].keys()) if existing_provenance else list(new_provenance[0].keys())

    write_csv(SUPP_ENTITIES_CSV, merged_entities, entity_fields)
    write_csv(SUPP_RELATIONS_CSV, merged_relations, relation_fields)
    write_csv(SUPP_QA_CSV, merged_qas, qa_fields)
    write_csv(PROVENANCE_CSV, merged_provenance, provenance_fields)

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Targeted Supplemental Facts Report",
                "",
                f"- Targeted facts upserted: {len(TARGETED_FACTS)}",
                f"- Supplemental entities total: {len(merged_entities)}",
                f"- Supplemental relations total: {len(merged_relations)}",
                f"- Supplemental QA sources total: {len(merged_qas)}",
                f"- Provenance rows total: {len(merged_provenance)}",
                "",
                "These facts are derived from existing AHD QA records and are intended to improve evidence coverage for repeated low-evidence topics.",
            ]
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "targeted_facts_upserted": len(TARGETED_FACTS),
                "supplemental_entities": len(merged_entities),
                "supplemental_relations": len(merged_relations),
                "supplemental_qa_sources": len(merged_qas),
                "provenance_rows": len(merged_provenance),
                "report_md": str(REPORT_MD.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
