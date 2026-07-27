# Focused Supplemental Expansion Report

This step converts high-confidence AHD-backed facts discovered from low-evidence failures into reusable supplemental graph facts.
These facts should be evaluated on a fresh unseen query offset to avoid measuring on the same failures used for discovery.

- Focused relations upserted: 14
- Focused entities upserted: 23
- AHD QA source records upserted: 8
- Supplemental relations: `outputs/05_trial_graph_v1/supplemental_facts/trial_graph_v1_supplemental_relations.csv`
- Supplemental entities: `outputs/05_trial_graph_v1/supplemental_facts/trial_graph_v1_supplemental_entities.csv`
- Supplemental QA sources: `outputs/05_trial_graph_v1/supplemental_facts/trial_graph_v1_supplemental_qa_sources.csv`

## Added Relations

- `focus_rel_dental_filling_no_dimple_relation`: حشو الأسنان --NOT_ASSOCIATED_WITH--> غمازة الوجه (`ahd5k_00484`)
- `focus_rel_dental_anesthesia_temporary_dimple`: تخدير موضعي قوي --MAY_TEMPORARILY_AFFECT--> غمازة الوجه (`ahd5k_00484`)
- `focus_rel_hemorrhoid_surgery_urinary_pain_review`: عملية البواسير --REQUIRES_MEDICAL_REVIEW_FOR--> استمرار صعوبة البول والألم بعد 16 يوم (`ahd5k_00530`)
- `focus_rel_anemia_managed_by_iron_rich_food`: فقر الدم --MANAGED_BY--> أغذية غنية بالحديد والفولات وفيتامين ب12 (`ahd5k_00594`)
- `focus_rel_iron_absorption_improved_by_vitamin_c`: أغذية غنية بالحديد والفولات وفيتامين ب12 --ABSORPTION_IMPROVED_BY--> أطعمة غنية بفيتامين ج (`ahd5k_00594`)
- `focus_rel_iron_absorption_reduced_by_tea_coffee`: أغذية غنية بالحديد والفولات وفيتامين ب12 --ABSORPTION_REDUCED_BY--> الشاي والقهوة والكالسيوم مع الحديد (`ahd5k_00594`)
- `focus_rel_iron_injections_determined_by_hb`: إبر الحديد --DOSE_DETERMINED_BY--> نسبة الهيموغلوبين ونوع علاج الحديد (`ahd5k_01162`)
- `focus_rel_tooth_filing_risk_sensitivity`: برد الأسنان --HAS_RISK--> حساسية الأسنان (`ahd5k_00828`)
- `focus_rel_tooth_filing_duration`: برد الأسنان --PROCEDURE_DURATION--> جلسة واحدة أو جلستان (`ahd5k_00828`)
- `focus_rel_dyspnea_fatigue_possible_causes`: صعوبة التنفس والإرهاق --MAY_BE_ASSOCIATED_WITH--> التهاب تنفسي أو فقر دم أو اضطراب دموي أو دوراني (`ahd5k_00855`)
- `focus_rel_dyspnea_fatigue_investigated_by_exam`: صعوبة التنفس والإرهاق --INVESTIGATED_BY--> التاريخ المرضي والفحص السريري (`ahd5k_00855`)
- `focus_rel_ovulation_stimulation_no_harm`: تنشيط المبايض --HAS_SAFETY_NOTE--> لا يوجد تأثير مضر مذكور قبل الحقن المجهري (`ahd5k_01770`)
- `focus_rel_crp_wbc_may_indicate_inflammation`: ارتفاع CRP وكريات الدم البيضاء --MAY_INDICATE--> التهاب (`ahd5k_02627`)
- `focus_rel_wbc_pregnancy_normal_range`: كريات الدم البيضاء أثناء الحمل --HAS_NORMAL_RANGE--> حتى 16000 أثناء الحمل وقد تصل 20000 أثناء الولادة (`ahd5k_02627`)
