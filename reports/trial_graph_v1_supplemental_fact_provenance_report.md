# Supplemental Fact Provenance Report

This report documents whether each supplemental fact is supported by local AHD dataset QA evidence.

- Dataset-derived supplemental facts: 12
- Manual-only supplemental facts: 0
- Provenance CSV: `outputs/05_trial_graph_v1/supplemental_facts/trial_graph_v1_supplemental_fact_provenance.csv`
- Updated supplemental relations: `outputs/05_trial_graph_v1/supplemental_facts/trial_graph_v1_supplemental_relations.csv`
- Updated supplemental entities: `outputs/05_trial_graph_v1/supplemental_facts/trial_graph_v1_supplemental_entities.csv`

## Dataset-Derived Facts

- `supp_rel_normal_bp` -> `ahd5k_00085`: حسب عوامل الخطورة الأخرى كالسكري والكلى؛ إذا لا توجد أمراض مصاحبة فالقيمة المذكورة 140-80.
- `supp_rel_normal_hr` -> `ahd5k_00085`: ضربات القلب تقريبا من 65-85، ويمكن قبول أقل أو أكثر حسب الحالة.
- `supp_rel_diclofenac_side_effect` -> `ahd5k_00065`: الأولفين هو نفس فولتارين ويحتويان على ديكلوفيناك، ولهم نفس الأعراض الجانبية، وينصح بأخذه بعد الأكل لتقليل تهيج الجهاز الهضمي.
- `supp_rel_diclofenac_supervision` -> `ahd5k_00065`: في حال الشقيقة الشديدة توجد أدوية أخرى ويذكر المصدر إمكانية استشارة الطبيب لذلك.
- `supp_rel_primolut_pregnancy` -> `ahd5k_00439`: إذا كانت المريضة حاملا وتستعمل بريمولوت ن فيجب إيقافه؛ يذكر المصدر دراسات عن احتمال تشوهات في القلب والأوعية والأنبوب العصبي والدماغ.
- `supp_rel_dental_aftercare` -> `ahd5k_00315`: إجابة المصدر تقول: اشربي قهوتك وشايك على راحتك مع المحافظة على تنظيف الأسنان.
- `supp_rel_tsh_interprets` -> `ahd5k_02685`: قيمة TSH بعد الولادة ترتبط باضطراب نشاط الغدة الدرقية، ويذكر المصدر ضرورة المتابعة تحت إشراف أخصائي الغدد الصم.
- `supp_rel_cholesterol_lifestyle` -> `ahd5k_00171`: طرق تخفيض الكوليسترول بدون دواء تعتمد على الجهد والتمارين خاصة المشي والحمية وتجنب الدهون الحيوانية والمقليات.
- `supp_rel_kidney_stones_management` -> `ahd5k_00012`: التخلص من الحصى يبدأ بدراستها لمعرفة مكانها وحجمها وطبيعتها ثم يقرر الطبيب كيفية التخلص منها.
- `supp_rel_ibs_management` -> `ahd5k_01998`: تبدو الأعراض كقولون عصبي؛ يذكر المصدر تجنب التفكير والقلق والنرفزة وتغيير أنماط تناول الطعام ونوعية الأطعمة.
- `supp_rel_fetal_bones_timeline` -> `ahd5k_00230`: في نهاية الأسبوع السادس يبدأ الجنين بتكوين العمود الفقري ويكون صغيرا جدا.
- `supp_rel_mouth_fungus_treated` -> `ahd5k_00142`: يوصي المصدر بالذهاب إلى طبيب اختصاصي لمعرفة التشخيص الحقيقي: هل هو فطريات أو نقص فيتامينات أو سبب آخر.
