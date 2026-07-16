# Trial Graph v1 Step 11 LLM Prompts

## trial_query_076: ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟ هل امتنع عن طعام معين يزيد البلغم وانا غير مدخن واخذ علاج للضغط والكوليسترول عمرى 55...

```text
User Question:
ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟ هل امتنع عن طعام معين يزيد البلغم وانا غير مدخن واخذ علاج للضغط والكوليسترول عمرى 55...

Retrieved Entities:
- حساسية الصدر (DiseaseCondition; match=exact; id=ent_diseasecondition_250910ab0701)
- ضغط (Symptom; match=exact; id=ent_symptom_d713f64368d3)
- بلغم (Symptom; match=exact; id=ent_symptom_dc2c7333a505)
- الكوليسترول (DiseaseCondition; match=exact; id=ent_diseasecondition_1cda0b09f82c)
- ضغط الدم (Symptom; match=alias; id=ent_symptom_724e59ded899)
- ارتفاع الكوليسترول (DiseaseCondition; match=alias; id=supp_ent_condition_cholesterol)
- حساسية (DiseaseCondition; match=alias; id=ent_diseasecondition_2f75d3dabe0b)

Retrieved Relations:
- [1] حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين (score=0.853633; reliability=medium)
- [2] حساسية --TREATED_BY--> مضاد الهيستامين (score=0.845599; reliability=medium)
- [3] حساسية --TREATED_BY--> كورتيزون (score=0.845599; reliability=medium)
- [4] حساسية --TREATED_BY--> تيليفاست (score=0.838022; reliability=medium)
- [5] ارتفاع الكوليسترول --MANAGED_BY--> تقليل الدهون والرياضة (score=0.83746; reliability=medium)
- [6] حساسية --TREATED_BY--> حليب مكسر بروتين الحليب (score=0.829987; reliability=medium)

Evidence Sentences:
- E1 | qa_id=ahd5k_00812 | relation=حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين: للاسف اهم علاج تجنب المنتجات التي تحوي جلوتين
  Source question: طفلتي تتحسس من الجلوتين وعمرها سنة ونصف هل توجد أدوية تساعد على الشفاء من هذا المرض ام لا ؟؟
  Source answer: للاسف اهم علاج تجنب المنتجات التي تحوي جلوتين
- E2 | qa_id=ahd5k_01231 | relation=حساسية --TREATED_BY--> مضاد الهيستامين: استخدمي مضاد هيسامين وكورتيزون موضعي
  Source question: تناولت مضاد حيووي زييثرون وانتج حساسيه شديده وتورم في المنطقة التناسليه وانا تعبانه جدا ما الحل ؟
  Source answer: لاتاخذيه مره اخرى استخدمي مضاد هيسامين وكورتيزون موضعي اعملي تحليل حساسية المضادات
- E3 | qa_id=ahd5k_01231 | relation=حساسية --TREATED_BY--> كورتيزون: استخدمي مضاد هيسامين وكورتيزون موضعي
  Source question: تناولت مضاد حيووي زييثرون وانتج حساسيه شديده وتورم في المنطقة التناسليه وانا تعبانه جدا ما الحل ؟
  Source answer: لاتاخذيه مره اخرى استخدمي مضاد هيسامين وكورتيزون موضعي اعملي تحليل حساسية المضادات
- E4 | qa_id=ahd5k_02470 | relation=حساسية --TREATED_BY--> تيليفاست: مضاد للهيستامين مثل تيليفاست
  Source question: سوألي هناك فتاه تشعر بحراره شديده في جسمها الخارجي وقليل جدا من داخل جسمها ولاترتاح الا بالاغتسال ومستمر الحال معها قرابه الثلاث ايام ماهو التشخيص لهذي الحاله وشكراا
  Source answer: قد يكون عندها نوع من أنواع الحساسية، ننصحها بالمكوث قي جو بارد وتناول مضاد للهيستامين مثل تيليفاست أو إكزوفين أ, أي نوع آخر
- E5 | qa_id=ahd5k_00171 | relation=ارتفاع الكوليسترول --MANAGED_BY--> تقليل الدهون والرياضة: طرق تخفيض الكوليسترول بدون دواء تعتمد على الجهد والتمارين خاصة المشي والحمية وتجنب الدهون الحيوانية والمقليات.
  Source question: امرأة تريد طرقة للتخلص من الكوليسترول في الجسم - وعمرها 54 سنة
  Source answer: أولاً يتوجب معرفة نوع الكوليسترول المرتفع لديها وهل يصاحبه ارتفاع في الدهون الثلاثية أم لا وهل الكوليسترول الحميد منخفض ، جميع هذه المعلومات يمكن الحصول عليها بعد فحص الدهون لتحديد نوع الزيادة ومقدارها ، كذلك يتطلب معرفة ما اذا كان وزنها طبيعي أم لا ، وهل لديها أي مرض مزمن، أما بشكل عام فطرق تخفيضه بدون دواء تعتمد في الدرجة الأولى على الجهد والتمارين خاصة المشي وعلى الحمية وتجنب الدهن الجيواني والاألبان خاصة الجبن والطعام المقلي كذلك تجنب الأغذية التي تحتوي على أحشاء الحيونات والكبد والطحال، والاستعاضة عنها بالأسماك والخضرة والفواكه الطازجة وزيت الزيتون
- E6 | qa_id=ahd5k_00020 | relation=حساسية --TREATED_BY--> حليب مكسر بروتين الحليب: اعطيها حليب مكسر بروتين الحليب بالكامل او حليب رز
  Source question: بنتي سنتين ونصف عندها حساسية من حليب البقر وتأخذ حليب خاص قليل التحسس HA لكن دائم مسبب لها غازات وانتفاخ بالبطن أريد أن اوقفه ما الاكل الي فيه نسب من...
  Source answer: اعطيها حليب مكسر بروتين الحليب بالكامل او حليب رز

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_077: كيف اعالج علامات الشيخوخة المبكرة بالوجه؟

```text
User Question:
كيف اعالج علامات الشيخوخة المبكرة بالوجه؟

Retrieved Entities:
- الشيخوخة (DiseaseCondition; match=exact; id=ent_diseasecondition_d99fb1a77d6c)

Retrieved Relations:
- [1] تضيق القنوات الموجودة داخل الكبد --TREATED_BY--> منظار قنوات مرارية الف سلامة (score=0.755988; reliability=medium)
- [2] منظار قنوات مرارية الف سلامة --TREATS--> تضيق القنوات الموجودة داخل الكبد (score=0.670388; reliability=limited)
- [3] حساسية --DIAGNOSED_BY--> تحاليل مخبرية (score=0.379826; reliability=limited)
- [4] انتفاخ --INVESTIGATED_BY--> اشعة (score=0.379631; reliability=limited)
- [5] وجع --INVESTIGATED_BY--> اشعة (score=0.379458; reliability=limited)
- [6] تحاليل مخبرية --DIAGNOSES--> حساسية (score=0.294226; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_00255 | relation=تضيق القنوات الموجودة داخل الكبد --TREATED_BY--> منظار قنوات مرارية الف سلامة: عمل منظار قنوات مرارية الف سلامة
  Source question: كيف اعالج تضيق القنوات الموجودة داخل الكبد عند الاطفال
  Source answer: غالبا يحتاج إلى عمل منظار قنوات مرارية الف سلامة
- E2 | qa_id=ahd5k_00255 | relation=منظار قنوات مرارية الف سلامة --TREATS--> تضيق القنوات الموجودة داخل الكبد: عمل منظار قنوات مرارية الف سلامة
  Source question: كيف اعالج تضيق القنوات الموجودة داخل الكبد عند الاطفال
  Source answer: غالبا يحتاج إلى عمل منظار قنوات مرارية الف سلامة
- E3 | qa_id=ahd5k_02039 | relation=حساسية --DIAGNOSED_BY--> تحاليل مخبرية: لابد من رؤيتها من قبل طبيب وعمل تحاليل خاصه بالحساسيه
  Source question: السلام عليكم ، اعاني من حبوب بيضاء صغيره ف اماكن معينه ف الوجه و اتوقع انها حساسية من البيض او اشعة الشمس ، ف كيف يمكنني اتأكد ! علماً انها...
  Source answer: لابدمن رؤيتها من قبل طبيب وعمل تحاليل خاصه بالحساسيه والغده الدرقيه وفيتامين د والزنك
- E4 | qa_id=ahd5k_01537 | relation=انتفاخ --INVESTIGATED_BY--> اشعة: اشعة بالصبغة
  Source question: قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة
  Source answer: نرجو توضيح السؤال وما هي نتيجة الفحص الشعاعي كما وردت في التقرير ليتسنى لنا معرفة النتيجة ومن ثم التشخيص
- E5 | qa_id=ahd5k_01537 | relation=وجع --INVESTIGATED_BY--> اشعة: اشعة بالصبغة
  Source question: قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة
  Source answer: نرجو توضيح السؤال وما هي نتيجة الفحص الشعاعي كما وردت في التقرير ليتسنى لنا معرفة النتيجة ومن ثم التشخيص
- E6 | qa_id=ahd5k_02039 | relation=تحاليل مخبرية --DIAGNOSES--> حساسية: لابد من رؤيتها من قبل طبيب وعمل تحاليل خاصه بالحساسيه
  Source question: السلام عليكم ، اعاني من حبوب بيضاء صغيره ف اماكن معينه ف الوجه و اتوقع انها حساسية من البيض او اشعة الشمس ، ف كيف يمكنني اتأكد ! علماً انها...
  Source answer: لابدمن رؤيتها من قبل طبيب وعمل تحاليل خاصه بالحساسيه والغده الدرقيه وفيتامين د والزنك

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_078: ماالعلاج الاسعافي لأنخفاض السكر مع فقدان الوعي

```text
User Question:
ماالعلاج الاسعافي لأنخفاض السكر مع فقدان الوعي

Retrieved Entities:
- فقدان الوعي (Symptom; match=exact; id=ent_symptom_1113453f7a36)
- سكر (DiseaseCondition; match=exact; id=ent_diseasecondition_4393a2bf88a6)

Retrieved Relations:
- [1] مرض السكري --HAS_SYMPTOM--> ضغط الدم (score=0.920872; reliability=strong)
- [2] فقدان الوعي --TREATED_BY--> عسل (score=0.919639; reliability=medium)
- [3] مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (score=0.803312; reliability=medium)
- [4] التهاب --DIAGNOSED_BY--> تحاليل مخبرية (score=0.759701; reliability=medium)
- [5] عسل --TREATS--> فقدان الوعي (score=0.387559; reliability=limited)
- [6] تحاليل مخبرية --DIAGNOSES--> مرض السكري (score=0.340352; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_04912 | relation=مرض السكري --HAS_SYMPTOM--> ضغط الدم: مع العلم أن المريض يعاني من مرض السكر
  Source question: هل ضعف عضله القلب وضيق ثلاث شرايين في القلب لهم عمليه جراحيه مع العلم أن المريض يعاني من مرض السكر ام يبقى على العلاج ولو عمليه جراحيهوين تنصحونا نعملها وعاووزيين...
  Source answer: هذا يتطلب معرفة نسبة الضعف الموجود في العضلة القلبية ونسبة التضيق في الثلاثة شرايين المذكورة، كما أنه من الضروري معرفة الحالة الوظيفية لباقي أعضاء الجسم خاصة الكلى والجهاز التنفسي، والكبد وغيره، وفي جميع الأحوال في العادة تُعرض نتائج القثطرة على فريق طبي مُتخصص لتقييم كل هذه الأمور ومن ثم يتم اختيار الطريقة العلاجية التي تتناسب أكثر مع حالة المريض
- E2 | qa_id=ahd5k_01294 | relation=مرض السكري --HAS_SYMPTOM--> ضغط الدم: مرض السكري وضغط الدمز
  Source question: تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س
  Source answer: العمليات الجراحية اليوم لا يعيقها أي مرض إذا ما تمت السيطرة عليه بشكل جيد قبل وأثناء وبعد العمل الجراحي، فلا داعي للقلق
- E3 | qa_id=ahd5k_00992 | relation=فقدان الوعي --TREATED_BY--> عسل: يجب عليك اعطاء المصاب عسل تحت لسانه
  Source question: ماالعلاج الاسعافي لأنخفاض السكر مع فقدان الوعي
  Source answer: يجب عليك اعطاء المصاب عسل تحت لسانه ليمضغه وتختلف درجه فقدان الوعي لمريض السكري
- E4 | qa_id=ahd5k_01551 | relation=مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.
- E5 | qa_id=ahd5k_01551 | relation=التهاب --DIAGNOSED_BY--> تحاليل مخبرية: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.
- E6 | qa_id=ahd5k_00992 | relation=عسل --TREATS--> فقدان الوعي: يجب عليك اعطاء المصاب عسل تحت لسانه
  Source question: ماالعلاج الاسعافي لأنخفاض السكر مع فقدان الوعي
  Source answer: يجب عليك اعطاء المصاب عسل تحت لسانه ليمضغه وتختلف درجه فقدان الوعي لمريض السكري
- E7 | qa_id=ahd5k_01551 | relation=تحاليل مخبرية --DIAGNOSES--> مرض السكري: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_079: هل الاشعة المقطعيه بالصبغه للقلب تسبب انتفاخ اسفل الوجه او انتفاخ الغده هل هو طبيعي

```text
User Question:
هل الاشعة المقطعيه بالصبغه للقلب تسبب انتفاخ اسفل الوجه او انتفاخ الغده هل هو طبيعي

Retrieved Entities:
- أشعة (Test; match=exact; id=ent_test_c4cfd2d6468c)
- انتفاخ (Symptom; match=exact; id=ent_symptom_fd750eeb2865)
- الغدة الدرقية (DiseaseCondition; match=alias; id=supp_ent_thyroid)

Retrieved Relations:
- [1] انتفاخ --INVESTIGATED_BY--> اشعة (score=0.863471; reliability=medium)
- [2] مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون (score=0.78026; reliability=medium)
- [3] اشعة --INVESTIGATES--> انتفاخ (score=0.777871; reliability=medium)
- [4] أشعة --DIAGNOSES--> تسوس الأسنان (score=0.777748; reliability=medium)
- [5] وجع --INVESTIGATED_BY--> اشعة (score=0.773343; reliability=medium)
- [6] التهاب --DIAGNOSED_BY--> اشعة (score=0.773343; reliability=medium)

Evidence Sentences:
- E1 | qa_id=ahd5k_01537 | relation=انتفاخ --INVESTIGATED_BY--> اشعة: اشعة بالصبغة
  Source question: قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة
  Source answer: نرجو توضيح السؤال وما هي نتيجة الفحص الشعاعي كما وردت في التقرير ليتسنى لنا معرفة النتيجة ومن ثم التشخيص
- E2 | qa_id=ahd5k_00035 | relation=مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون: مستوى الهرمون في الدم
  Source question: انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟
  Source answer: علاج الغدة وجرعة العلاج تعتمد على مستوى الهرمون في الدم
- E3 | qa_id=ahd5k_01537 | relation=اشعة --INVESTIGATES--> انتفاخ: اشعة بالصبغة
  Source question: قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة
  Source answer: نرجو توضيح السؤال وما هي نتيجة الفحص الشعاعي كما وردت في التقرير ليتسنى لنا معرفة النتيجة ومن ثم التشخيص
- E4 | qa_id=ahd5k_04844 | relation=أشعة --DIAGNOSES--> تسوس الأسنان: أشعة
  Source question: اعاني من غدة ليمفاوية ذات قوام مطاطي و ثابتة تحت الفك من 4 شهور قمت بعمل فحص دم و اشعه و لم يكتشف شيء لدي اسنان متسوسه هل من الممكن...
  Source answer: أحياناً تسوس الأسنان أو أي خراجات باللثة أو انتان خفي أو ظاهر بمنطقة العنق يمكنها أن تسبب تضخم بالغدد اللمفية الموضعية وهنا لابد من مراجعة طبيب أسنان وطبيب أذنية للبحث عن وجود انتان ومعالجته
- E5 | qa_id=ahd5k_01537 | relation=وجع --INVESTIGATED_BY--> اشعة: اشعة بالصبغة
  Source question: قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة
  Source answer: نرجو توضيح السؤال وما هي نتيجة الفحص الشعاعي كما وردت في التقرير ليتسنى لنا معرفة النتيجة ومن ثم التشخيص
- E6 | qa_id=ahd5k_00114 | relation=التهاب --DIAGNOSED_BY--> اشعة: اجراء صورة اشعة عادية للحوض
  Source question: منذ دخول فصل الشتاء انتابتني بعض الاعراض ولاسيما في الرجل اليسري اشعر بالم في المفصل ودلك عند ثني الرجل يإما بالجلوس اوالقعود وعندما احاول الوقوف ارجع رجلي بصعوبة لمكانها الطبيعي...
  Source answer: ما تعانين منه هو عبارة عن الم ميكانيكي اي وقت الحركة فقط ., لا وجود له مع الراحة , ينصح لك عمل صورة اشعة عادية للحوض وبها يتضح وضع راس الفخذ من الجهتين . اذا كانت الامور سليمة عليك بالسباحة وعمل جلسات علاج طبيعي وتليين حركة مفصل الفخذ بالنوم مستلقية على ظهرك وعمل حركة الدراجة خمس دقائق يوميا

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_080: السلام عليكم..ماهو العلاج المناسب لتقليل نسبة الاملاح في الدم النسبة الحالية عندي هي (7.9) عمري 44 سنة /ذكر؟

```text
User Question:
السلام عليكم..ماهو العلاج المناسب لتقليل نسبة الاملاح في الدم النسبة الحالية عندي هي (7.9) عمري 44 سنة /ذكر؟

Retrieved Entities:
- العلاج (Treatment; match=exact; id=ent_treatment_90baddc0bf15)
- النسبة (Test; match=exact; id=ent_test_4e95ccf90696)

Retrieved Relations:
- [1] حساسية الصدر --HAS_SYMPTOM--> سعال (score=0.532286; reliability=limited)
- [2] التهاب --HAS_SYMPTOM--> الدم (score=0.53072; reliability=limited)
- [3] سعال --SYMPTOM_OF--> حساسية الصدر (score=0.446686; reliability=limited)
- [4] الدم --SYMPTOM_OF--> التهاب (score=0.44512; reliability=limited)
- [5] التهاب --DIAGNOSED_BY--> تصوير الجهاز البولي (score=0.402496; reliability=limited)
- [6] الدم --INVESTIGATED_BY--> تصوير الجهاز البولي (score=0.400384; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_04490 | relation=حساسية الصدر --HAS_SYMPTOM--> سعال: حساسية الصدر and سعال co-occur with explicit symptom-pathology link
  Source question: انا عندي قضيبي صغير هل هذه بسبب متعلق بهرمون الذكوره علما انا عمري 17 ويوجد شعر على الارجل والابط ولايوجد على الشارب وبدي اعرف اذا كان السبب متعلق بلهرمون كيفيه...
  Source answer: يجب اجراء الفحص السريري و الفحوصات المخبرية لتحديد السبب ثم العلاج
- E2 | qa_id=ahd5k_00666 | relation=التهاب --HAS_SYMPTOM--> الدم: التهاب في المثانة أو الإحليل يسبب خروج الدم
  Source question: انا عندي مشكله عندما انتهي من التبول يخرج في اخر البول دم؟
  Source answer: خروج الدم يعني وجود جرح في المثانة أو الإحليل. ويمكن آن يكون هذا ناتجاً عن وجود جرح ينزل منه الدم، حصوة في المثانة أو الإحليل؟ يمكمنك تصوير الجهاز البولي بصورة ملونر أي في بي لتحديد السبب والمكان، وبعدها يتحدد العلاج؟سلامتك
- E3 | qa_id=ahd5k_04490 | relation=سعال --SYMPTOM_OF--> حساسية الصدر: حساسية الصدر and سعال co-occur with explicit symptom-pathology link
  Source question: انا عندي قضيبي صغير هل هذه بسبب متعلق بهرمون الذكوره علما انا عمري 17 ويوجد شعر على الارجل والابط ولايوجد على الشارب وبدي اعرف اذا كان السبب متعلق بلهرمون كيفيه...
  Source answer: يجب اجراء الفحص السريري و الفحوصات المخبرية لتحديد السبب ثم العلاج
- E4 | qa_id=ahd5k_00666 | relation=الدم --SYMPTOM_OF--> التهاب: التهاب في المثانة أو الإحليل يسبب خروج الدم
  Source question: انا عندي مشكله عندما انتهي من التبول يخرج في اخر البول دم؟
  Source answer: خروج الدم يعني وجود جرح في المثانة أو الإحليل. ويمكن آن يكون هذا ناتجاً عن وجود جرح ينزل منه الدم، حصوة في المثانة أو الإحليل؟ يمكمنك تصوير الجهاز البولي بصورة ملونر أي في بي لتحديد السبب والمكان، وبعدها يتحدد العلاج؟سلامتك
- E5 | qa_id=ahd5k_00666 | relation=التهاب --DIAGNOSED_BY--> تصوير الجهاز البولي: تصوير الجهاز البولي لتحديد سبب التهاب المثانة
  Source question: انا عندي مشكله عندما انتهي من التبول يخرج في اخر البول دم؟
  Source answer: خروج الدم يعني وجود جرح في المثانة أو الإحليل. ويمكن آن يكون هذا ناتجاً عن وجود جرح ينزل منه الدم، حصوة في المثانة أو الإحليل؟ يمكمنك تصوير الجهاز البولي بصورة ملونر أي في بي لتحديد السبب والمكان، وبعدها يتحدد العلاج؟سلامتك
- E6 | qa_id=ahd5k_00666 | relation=الدم --INVESTIGATED_BY--> تصوير الجهاز البولي: تصوير الجهاز البولي لتحديد مكان خروج الدم
  Source question: انا عندي مشكله عندما انتهي من التبول يخرج في اخر البول دم؟
  Source answer: خروج الدم يعني وجود جرح في المثانة أو الإحليل. ويمكن آن يكون هذا ناتجاً عن وجود جرح ينزل منه الدم، حصوة في المثانة أو الإحليل؟ يمكمنك تصوير الجهاز البولي بصورة ملونر أي في بي لتحديد السبب والمكان، وبعدها يتحدد العلاج؟سلامتك

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_081: السلام عليكم أنا أشعر ببرودة رأسي -وغذا اصبح ملمس رأسي بارد جاني صداع لايزول بالمسكنات- ذهبت لأفضل أخصائي أنف وأذن وحنجرة قال هذا المرض ماله علاج !! ماهي التحاليل الأزمة...

```text
User Question:
السلام عليكم أنا أشعر ببرودة رأسي -وغذا اصبح ملمس رأسي بارد جاني صداع لايزول بالمسكنات- ذهبت لأفضل أخصائي أنف وأذن وحنجرة قال هذا المرض ماله علاج !! ماهي التحاليل الأزمة...

Retrieved Entities:
- صداع (Symptom; match=exact; id=ent_symptom_b754f1a1e5a8)
- صداع التوتر (Symptom; match=alias; id=ent_symptom_c01e00eb5c72)

Retrieved Relations:
- [1] التهاب السحايا --HAS_SYMPTOM--> صداع (score=0.787398; reliability=medium)
- [2] صداع --SYMPTOM_OF--> التهاب السحايا (score=0.786278; reliability=medium)
- [3] التهاب الجيوب الأنفية --HAS_SYMPTOM--> صداع (score=0.776838; reliability=medium)
- [4] صداع --SYMPTOM_OF--> التهاب الجيوب الأنفية (score=0.775718; reliability=medium)
- [5] صداع --SYMPTOM_OF--> الصداع التوتري (score=0.766573; reliability=medium)
- [6] ضرس العقل --HAS_SYMPTOM--> صداع (score=0.760182; reliability=medium)

Evidence Sentences:
- E1 | qa_id=ahd5k_02662 | relation=التهاب السحايا --HAS_SYMPTOM--> صداع: صداع
  Source question: لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام لهذا السبب
  Source answer: إن الألم في الرأس مع الشعور بالضغط على جانبي الرأس مع الإرهاق العام قد يعود لأحد الأسباب التالية: صداع التوتر. الشد العضلي. الضغط العصبي. القلق والتوتر أو الاكتئاب. التهاب الجيوب الأنفية. الشقيقة (الصداع النصفي). وجود مشاكل في الأذن التهاب السحايا. تمدد الأوعية الدموية في الدماغ. ينصح في الوقت الحالي زيارة الطبيب المختص لعمل الفحوصات والتحاليل اللازمة في حال عدم نجاح النصائح التالية: استخدام الأدوية المسكنة للألم حسب تعليمات الطبيب المختص مثل الايبوبروفين وغيرها. اتباع طرق التنفس العميق من أجل الاسترخاء وخفض مستويات هرمونات التوتر. ممارسة تمارين الاسترخاء مثل اليوغا والتأمل. تجنب القلق أو التوتر. للمزيد: اسباب الصداع ومحفزاته التدليك لعلاج الصداع هل تعاني من صداع من دون معرفة سببه؟ المرجع...
- E2 | qa_id=ahd5k_02662 | relation=صداع --SYMPTOM_OF--> التهاب السحايا: صداع
  Source question: لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام لهذا السبب
  Source answer: إن الألم في الرأس مع الشعور بالضغط على جانبي الرأس مع الإرهاق العام قد يعود لأحد الأسباب التالية: صداع التوتر. الشد العضلي. الضغط العصبي. القلق والتوتر أو الاكتئاب. التهاب الجيوب الأنفية. الشقيقة (الصداع النصفي). وجود مشاكل في الأذن التهاب السحايا. تمدد الأوعية الدموية في الدماغ. ينصح في الوقت الحالي زيارة الطبيب المختص لعمل الفحوصات والتحاليل اللازمة في حال عدم نجاح النصائح التالية: استخدام الأدوية المسكنة للألم حسب تعليمات الطبيب المختص مثل الايبوبروفين وغيرها. اتباع طرق التنفس العميق من أجل الاسترخاء وخفض مستويات هرمونات التوتر. ممارسة تمارين الاسترخاء مثل اليوغا والتأمل. تجنب القلق أو التوتر. للمزيد: اسباب الصداع ومحفزاته التدليك لعلاج الصداع هل تعاني من صداع من دون معرفة سببه؟ المرجع...
- E3 | qa_id=ahd5k_02662 | relation=التهاب الجيوب الأنفية --HAS_SYMPTOM--> صداع: صداع
  Source question: لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام لهذا السبب
  Source answer: إن الألم في الرأس مع الشعور بالضغط على جانبي الرأس مع الإرهاق العام قد يعود لأحد الأسباب التالية: صداع التوتر. الشد العضلي. الضغط العصبي. القلق والتوتر أو الاكتئاب. التهاب الجيوب الأنفية. الشقيقة (الصداع النصفي). وجود مشاكل في الأذن التهاب السحايا. تمدد الأوعية الدموية في الدماغ. ينصح في الوقت الحالي زيارة الطبيب المختص لعمل الفحوصات والتحاليل اللازمة في حال عدم نجاح النصائح التالية: استخدام الأدوية المسكنة للألم حسب تعليمات الطبيب المختص مثل الايبوبروفين وغيرها. اتباع طرق التنفس العميق من أجل الاسترخاء وخفض مستويات هرمونات التوتر. ممارسة تمارين الاسترخاء مثل اليوغا والتأمل. تجنب القلق أو التوتر. للمزيد: اسباب الصداع ومحفزاته التدليك لعلاج الصداع هل تعاني من صداع من دون معرفة سببه؟ المرجع...
- E4 | qa_id=ahd5k_02662 | relation=صداع --SYMPTOM_OF--> التهاب الجيوب الأنفية: صداع
  Source question: لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام لهذا السبب
  Source answer: إن الألم في الرأس مع الشعور بالضغط على جانبي الرأس مع الإرهاق العام قد يعود لأحد الأسباب التالية: صداع التوتر. الشد العضلي. الضغط العصبي. القلق والتوتر أو الاكتئاب. التهاب الجيوب الأنفية. الشقيقة (الصداع النصفي). وجود مشاكل في الأذن التهاب السحايا. تمدد الأوعية الدموية في الدماغ. ينصح في الوقت الحالي زيارة الطبيب المختص لعمل الفحوصات والتحاليل اللازمة في حال عدم نجاح النصائح التالية: استخدام الأدوية المسكنة للألم حسب تعليمات الطبيب المختص مثل الايبوبروفين وغيرها. اتباع طرق التنفس العميق من أجل الاسترخاء وخفض مستويات هرمونات التوتر. ممارسة تمارين الاسترخاء مثل اليوغا والتأمل. تجنب القلق أو التوتر. للمزيد: اسباب الصداع ومحفزاته التدليك لعلاج الصداع هل تعاني من صداع من دون معرفة سببه؟ المرجع...
- E5 | qa_id=ahd5k_00780 | relation=صداع --SYMPTOM_OF--> الصداع التوتري: الصداع التوتري قد يظهر كصداع يختلف حدته
  Source question: لماذا اصحو من النوم يوميا بصداع يختلف حدته من خفيف إلى قوي جدا لدرجة ان عيناي تدمع من كثرة الصداع مع العلم بان عمري 29 سنة ولدي طفل عمره سنة...
  Source answer: قد يكون لديك نوع من الصداع يسمى بالصداع التوتري و هو ناتج عن وجود ضغوطات في الحياة كالعمل و الاستيقاظ الليلي لارضاع طفلك من المهم مراجعة طبيب اعصاب وذلك لاتمام الفحص السريري و التاكد من التشخيص
- E6 | qa_id=ahd5k_04356 | relation=ضرس العقل --HAS_SYMPTOM--> صداع: ضرس العقل
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_082: مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد المستشفی

```text
User Question:
مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد المستشفی

Retrieved Entities:
- قرحة (DiseaseCondition; match=exact; id=ent_diseasecondition_780d3bf613f5)
- القرحة (DiseaseCondition; match=exact; id=ent_diseasecondition_d13d516b4149)
- النزيف (Symptom; match=exact; id=ent_symptom_23da4c61fd5e)
- غثيان (Symptom; match=exact; id=ent_symptom_ca6890d2fa81)

Retrieved Relations:
- [1] قرحة --TREATED_BY--> ايزومبرازول (score=0.567512; reliability=limited)
- [2] الملوية البوابية --TREATED_BY--> الدواء (score=0.407368; reliability=limited)
- [3] ايزومبرازول --TREATS--> قرحة (score=0.397432; reliability=limited)
- [4] الدواء --TREATS--> الملوية البوابية (score=0.321768; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_01066 | relation=قرحة --TREATED_BY--> ايزومبرازول: ممكن تجرب دواء اسمه ايزومبرازول
  Source question: مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد المستشفی
  Source answer: هل افهم من سؤالك ان والدتك عندها قرحه مع نزيف مستمر اذا كان الامر هكذا فلابد من ذهابها الى المستشفى لان النزيف المستمر سيشكل خطر على حياتها. اما اذا كانت القرحه مؤكده بدون نزيف فممكن تجرب دواء اسمه ايزومبرازول ٤٠ مج يوميا لمدة ٣ شهور. ان لم يحدث تحسن من البدايه فيجب الذهاب الى المستشفى
- E2 | qa_id=ahd5k_03807 | relation=الملوية البوابية --TREATED_BY--> الدواء: مضادات حيويه نكسيوم و كلاريثرومايسين واموكسسلين
  Source question: من فتره سنه كان عندي الم ب المعده واسهال حاد وعملت منضار وطلع عندي قرحه بالمعده واخدت مضادات حيويه نكسيوم و كلاريثرومايسين واموكسسلين وضليت فتره 6 شهور وهلق في نفس...
  Source answer: اخي الكريم بعد تشخيص القرحة واعطاء العلاج أنت بحاجة للمتابعة الطبية لمعرفة شفاء القرحة بشكل حيث يوجد خطوط علاجية كثيرة وقد لاتستفيد على أحدها وتستجيب على الأخر ......هل كان هناك اصابة بالملوية البوابية مثبتة ...........................
- E3 | qa_id=ahd5k_01066 | relation=ايزومبرازول --TREATS--> قرحة: ممكن تجرب دواء اسمه ايزومبرازول
  Source question: مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد المستشفی
  Source answer: هل افهم من سؤالك ان والدتك عندها قرحه مع نزيف مستمر اذا كان الامر هكذا فلابد من ذهابها الى المستشفى لان النزيف المستمر سيشكل خطر على حياتها. اما اذا كانت القرحه مؤكده بدون نزيف فممكن تجرب دواء اسمه ايزومبرازول ٤٠ مج يوميا لمدة ٣ شهور. ان لم يحدث تحسن من البدايه فيجب الذهاب الى المستشفى
- E4 | qa_id=ahd5k_03807 | relation=الدواء --TREATS--> الملوية البوابية: مضادات حيويه نكسيوم و كلاريثرومايسين واموكسسلين
  Source question: من فتره سنه كان عندي الم ب المعده واسهال حاد وعملت منضار وطلع عندي قرحه بالمعده واخدت مضادات حيويه نكسيوم و كلاريثرومايسين واموكسسلين وضليت فتره 6 شهور وهلق في نفس...
  Source answer: اخي الكريم بعد تشخيص القرحة واعطاء العلاج أنت بحاجة للمتابعة الطبية لمعرفة شفاء القرحة بشكل حيث يوجد خطوط علاجية كثيرة وقد لاتستفيد على أحدها وتستجيب على الأخر ......هل كان هناك اصابة بالملوية البوابية مثبتة ...........................

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_083: ما البديل لعمل كراون للضرس في حال كان طول الضرس قصير بسبب كسر وتآكل في السطح بعد حشو عصب مع حجم طبيعي للضرس ،حتى يعود يصبح في طول يسمح بتركيب...

```text
User Question:
ما البديل لعمل كراون للضرس في حال كان طول الضرس قصير بسبب كسر وتآكل في السطح بعد حشو عصب مع حجم طبيعي للضرس ،حتى يعود يصبح في طول يسمح بتركيب...

Retrieved Entities:
- الضرس (DiseaseCondition; match=exact; id=ent_diseasecondition_ee57bd84c53c)
- كسر (DiseaseCondition; match=exact; id=ent_diseasecondition_63c6ebfcb439)

Retrieved Relations:
- [1] حشو الأسنان --NOT_ASSOCIATED_WITH--> غمازة الوجه (score=0.421826; reliability=limited)
- [2] تخدير موضعي قوي --MAY_TEMPORARILY_AFFECT--> غمازة الوجه (score=0.421826; reliability=limited)
- [3] برد الأسنان --HAS_RISK--> حساسية الأسنان (score=0.415278; reliability=limited)
- [4] برد الأسنان --PROCEDURE_DURATION--> جلسة واحدة أو جلستان (score=0.415278; reliability=limited)
- [5] بروز في البطن --TREATED_BY--> تمارين رياضية (score=0.38401; reliability=limited)
- [6] تمارين رياضية --TREATS--> بروز في البطن (score=0.29841; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_00484 | relation=حشو الأسنان --NOT_ASSOCIATED_WITH--> غمازة الوجه: لا توجد علاقة مرتبطة بين حشو الأسنان وغمازة الوجه حسب مصدر AHD.
  Source question: كان عندي ضرس متسوس في أعلى الفم و الدكتور عمل لي حشوة و عالج التسوس و لكن لاحظت اختفاء غمازة وجهي بعدها مُباشرةً ، ما السبب و هل مُمكن ترجع...
  Source answer: لاتوجد أي علاقة مرتبطة بين حشو الأسنان وغمازة الوجه، وجه المقاربة قد يكون فقط في حال تم تخدير المنطقة نفسها الي تقع بها الغمازة بمخدر قوي وكمية كبيرة، وان كانت هذه الحالة فعندها تزول خلال ٢٤-٤٨ ساعة.
- E2 | qa_id=ahd5k_00484 | relation=تخدير موضعي قوي --MAY_TEMPORARILY_AFFECT--> غمازة الوجه: إذا تم تخدير منطقة الغمازة بمخدر قوي وكمية كبيرة فقد تزول الحالة خلال 24-48 ساعة.
  Source question: كان عندي ضرس متسوس في أعلى الفم و الدكتور عمل لي حشوة و عالج التسوس و لكن لاحظت اختفاء غمازة وجهي بعدها مُباشرةً ، ما السبب و هل مُمكن ترجع...
  Source answer: لاتوجد أي علاقة مرتبطة بين حشو الأسنان وغمازة الوجه، وجه المقاربة قد يكون فقط في حال تم تخدير المنطقة نفسها الي تقع بها الغمازة بمخدر قوي وكمية كبيرة، وان كانت هذه الحالة فعندها تزول خلال ٢٤-٤٨ ساعة.
- E3 | qa_id=ahd5k_00828 | relation=برد الأسنان --HAS_RISK--> حساسية الأسنان: كثرة برد الأسنان قد تؤثر على الأسنان وتجعلها حساسة.
  Source question: برد الاسنان الاماميه ما ضرره وكم جلسه يحتاج
  Source answer: برد لمجرد البرد والتصغير في جلسه واحدة ولكن احذر من كثرة البرد حتي يؤثر علي الاسنان وتكون حساسه. ام لو برد للتركيب وعمل اسنان صناعيه ممكن جلسه او جلستين
- E4 | qa_id=ahd5k_00828 | relation=برد الأسنان --PROCEDURE_DURATION--> جلسة واحدة أو جلستان: برد الأسنان للتصغير قد يتم في جلسة واحدة، أما للتركيب وعمل أسنان صناعية فقد يحتاج جلسة أو جلستين.
  Source question: برد الاسنان الاماميه ما ضرره وكم جلسه يحتاج
  Source answer: برد لمجرد البرد والتصغير في جلسه واحدة ولكن احذر من كثرة البرد حتي يؤثر علي الاسنان وتكون حساسه. ام لو برد للتركيب وعمل اسنان صناعيه ممكن جلسه او جلستين
- E5 | qa_id=ahd5k_04986 | relation=بروز في البطن --TREATED_BY--> تمارين رياضية: وجربت التمارين فترة بس ما لاحظت نتيجة كبيرة
  Source question: انا بنت عمري 22 سنة بدي علاج طبيعي وسريع للبطن.. عندي بروز في البطن... وجربت التمارين فترة بس ما لاحظت نتيجة كبيرة ولأنه برد برجع الحجم متل ما كان... بدي...
  Source answer: ليس هناك حلول مضمونة سوى ممارسة التمارين الرباضية الدائم.
- E6 | qa_id=ahd5k_04986 | relation=تمارين رياضية --TREATS--> بروز في البطن: وجربت التمارين فترة بس ما لاحظت نتيجة كبيرة
  Source question: انا بنت عمري 22 سنة بدي علاج طبيعي وسريع للبطن.. عندي بروز في البطن... وجربت التمارين فترة بس ما لاحظت نتيجة كبيرة ولأنه برد برجع الحجم متل ما كان... بدي...
  Source answer: ليس هناك حلول مضمونة سوى ممارسة التمارين الرباضية الدائم.

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_084: زوجتي حامل ومنذ بداية حملها لم اتوقف عن الاتصال معهاابدا ..فهل ذلك له علاقه لما تشعر به من حرقه في المهبل...وهل ذلك له تأثير على الجنين....

```text
User Question:
زوجتي حامل ومنذ بداية حملها لم اتوقف عن الاتصال معهاابدا ..فهل ذلك له علاقه لما تشعر به من حرقه في المهبل...وهل ذلك له تأثير على الجنين....

Retrieved Entities:
- الجنين (DiseaseCondition; match=exact; id=ent_diseasecondition_1420aadad936)
- حرقه (Symptom; match=exact; id=ent_symptom_ecf500c8beea)

Retrieved Relations:
- [1] التهاب --HAS_SYMPTOM--> حرقه (score=0.496355; reliability=limited)
- [2] حرقه --SYMPTOM_OF--> التهاب (score=0.495235; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_01099 | relation=التهاب --HAS_SYMPTOM--> حرقه: التهابات نسائيه تسبب حرقه في المهبل
  Source question: زوجتي حامل ومنذ بداية حملها لم اتوقف عن الاتصال معهاابدا ..فهل ذلك له علاقه لما تشعر به من حرقه في المهبل...وهل ذلك له تأثير على الجنين....
  Source answer: ﻻتاثير على الجنين...والحرقه من التهابات نسائيه
- E2 | qa_id=ahd5k_01099 | relation=حرقه --SYMPTOM_OF--> التهاب: التهابات نسائيه تسبب حرقه في المهبل
  Source question: زوجتي حامل ومنذ بداية حملها لم اتوقف عن الاتصال معهاابدا ..فهل ذلك له علاقه لما تشعر به من حرقه في المهبل...وهل ذلك له تأثير على الجنين....
  Source answer: ﻻتاثير على الجنين...والحرقه من التهابات نسائيه

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_085: لمدا كلما انزعجت من شخص ما أشعر بدوار ودقات سريعة للقلب وشعور براسي تقيل تم يغمى علي دون الغياب عن الوعي فما تشخيصكم لهدا وشكراً جزيل

```text
User Question:
لمدا كلما انزعجت من شخص ما أشعر بدوار ودقات سريعة للقلب وشعور براسي تقيل تم يغمى علي دون الغياب عن الوعي فما تشخيصكم لهدا وشكراً جزيل

Retrieved Entities:
- دقات سريعة للقلب (Symptom; match=exact; id=ent_symptom_2623f9ed0078)
- راسي تقيل (Symptom; match=exact; id=ent_symptom_e9ec482600f1)
- دوار (Symptom; match=exact; id=ent_symptom_ec53995c86ca)

Retrieved Relations:
- [1] فقر الدم --MANAGED_BY--> أغذية غنية بالحديد والفولات وفيتامين ب12 (score=0.402766; reliability=limited)
- [2] أغذية غنية بالحديد والفولات وفيتامين ب12 --ABSORPTION_IMPROVED_BY--> أطعمة غنية بفيتامين ج (score=0.402766; reliability=limited)
- [3] أغذية غنية بالحديد والفولات وفيتامين ب12 --ABSORPTION_REDUCED_BY--> الشاي والقهوة والكالسيوم مع الحديد (score=0.402766; reliability=limited)
- [4] سيلان الانف --TREATED_BY--> بخاخات الماء والملح (score=0.377644; reliability=limited)
- [5] سيلان الانف --INVESTIGATED_BY--> خصائي الاطفال (score=0.377644; reliability=limited)
- [6] بخاخات الماء والملح --TREATS--> سيلان الانف (score=0.292044; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_00594 | relation=فقر الدم --MANAGED_BY--> أغذية غنية بالحديد والفولات وفيتامين ب12: يمكن دعم فقر الدم بنظام غذائي غني بعناصر مثل الحديد وحمض الفوليك وفيتامين ب-12، مع بقاء العلاج حسب نوع فقر الدم تحت إشراف الطبيب.
  Source question: السلام عليكم دكتور انا عندي فقر دم اي هي اغدية المفيدة الي؟
  Source answer: يحدث فقر الدم عندما لا يحتوي جسمك على ما يكفي من خلايا الدم الحمراء نتيجة فقدان الدم أو عدم القدرة على تكوين خلايا دم حمراء كافية. ويوجد العديد من أنوع فقر الدم منها الذي يكون بسبب نقص الحديد أو حمض الفوليك أو فيتامين ب-12 وغيرها. ويمكن اتباع نظام غذائي غني بالعناصر اللازمة لتعويض النقص من خلال: الورقيات الخضراء: السبانخ/ الكرنب/ الهندباء/ الخبيزة. اللحوم والدواجن. كبدة الخروف. المأكولات البحرية: السردين/ التونا/ السلمون. عصير البرتقال المحصن. الحبوب المدعمة. بعض الحبوب: الفاصولياء/ الحمص/ فول الصويا/ البازلاء. بذور اليقطين/ الكاجو/ الفستق/ الصنوبر/ الجوز/ بذور عباد الشمس. تجنب تناول الأطعمة الغنية بالحديد مع الأطعمة أو المشروبات التي تمنع امتصاص الحديد مثل: القهوة أو الشاي /البيض/ الأطعم...
- E2 | qa_id=ahd5k_00594 | relation=أغذية غنية بالحديد والفولات وفيتامين ب12 --ABSORPTION_IMPROVED_BY--> أطعمة غنية بفيتامين ج: تناول الأطعمة الغنية بالحديد مع أطعمة غنية بفيتامين ج مثل البرتقال والطماطم والفراولة قد يحسن الامتصاص.
  Source question: السلام عليكم دكتور انا عندي فقر دم اي هي اغدية المفيدة الي؟
  Source answer: يحدث فقر الدم عندما لا يحتوي جسمك على ما يكفي من خلايا الدم الحمراء نتيجة فقدان الدم أو عدم القدرة على تكوين خلايا دم حمراء كافية. ويوجد العديد من أنوع فقر الدم منها الذي يكون بسبب نقص الحديد أو حمض الفوليك أو فيتامين ب-12 وغيرها. ويمكن اتباع نظام غذائي غني بالعناصر اللازمة لتعويض النقص من خلال: الورقيات الخضراء: السبانخ/ الكرنب/ الهندباء/ الخبيزة. اللحوم والدواجن. كبدة الخروف. المأكولات البحرية: السردين/ التونا/ السلمون. عصير البرتقال المحصن. الحبوب المدعمة. بعض الحبوب: الفاصولياء/ الحمص/ فول الصويا/ البازلاء. بذور اليقطين/ الكاجو/ الفستق/ الصنوبر/ الجوز/ بذور عباد الشمس. تجنب تناول الأطعمة الغنية بالحديد مع الأطعمة أو المشروبات التي تمنع امتصاص الحديد مثل: القهوة أو الشاي /البيض/ الأطعم...
- E3 | qa_id=ahd5k_00594 | relation=أغذية غنية بالحديد والفولات وفيتامين ب12 --ABSORPTION_REDUCED_BY--> الشاي والقهوة والكالسيوم مع الحديد: ينصح بتجنب تناول الأطعمة الغنية بالحديد مع القهوة أو الشاي أو الأطعمة الغنية بالكالسيوم لأنها قد تمنع امتصاص الحديد.
  Source question: السلام عليكم دكتور انا عندي فقر دم اي هي اغدية المفيدة الي؟
  Source answer: يحدث فقر الدم عندما لا يحتوي جسمك على ما يكفي من خلايا الدم الحمراء نتيجة فقدان الدم أو عدم القدرة على تكوين خلايا دم حمراء كافية. ويوجد العديد من أنوع فقر الدم منها الذي يكون بسبب نقص الحديد أو حمض الفوليك أو فيتامين ب-12 وغيرها. ويمكن اتباع نظام غذائي غني بالعناصر اللازمة لتعويض النقص من خلال: الورقيات الخضراء: السبانخ/ الكرنب/ الهندباء/ الخبيزة. اللحوم والدواجن. كبدة الخروف. المأكولات البحرية: السردين/ التونا/ السلمون. عصير البرتقال المحصن. الحبوب المدعمة. بعض الحبوب: الفاصولياء/ الحمص/ فول الصويا/ البازلاء. بذور اليقطين/ الكاجو/ الفستق/ الصنوبر/ الجوز/ بذور عباد الشمس. تجنب تناول الأطعمة الغنية بالحديد مع الأطعمة أو المشروبات التي تمنع امتصاص الحديد مثل: القهوة أو الشاي /البيض/ الأطعم...
- E4 | qa_id=ahd5k_04444 | relation=سيلان الانف --TREATED_BY--> بخاخات الماء والملح: جرب بخاخات الماء والملح
  Source question: طفلي عمر سنتين يعاني من سيلان الانف باستمرار وبالليل تتقفل نهاي مايقدر يتنفس اعطيناهو علاجات مضاد حيوي دون فايده
  Source answer: جرب بخاخات الماء والملح.وفي حال عدم التحسن لابد من عرضه على اخصائي الاطفال.رجاء لاتعطي اي مضاد حيوي دون وصفة طبية.المضاد الحيوي ليس علاجاً لفتح الأنف!!!!
- E5 | qa_id=ahd5k_04444 | relation=سيلان الانف --INVESTIGATED_BY--> خصائي الاطفال: لابد من عرضه على اخصائي الاطفال
  Source question: طفلي عمر سنتين يعاني من سيلان الانف باستمرار وبالليل تتقفل نهاي مايقدر يتنفس اعطيناهو علاجات مضاد حيوي دون فايده
  Source answer: جرب بخاخات الماء والملح.وفي حال عدم التحسن لابد من عرضه على اخصائي الاطفال.رجاء لاتعطي اي مضاد حيوي دون وصفة طبية.المضاد الحيوي ليس علاجاً لفتح الأنف!!!!
- E6 | qa_id=ahd5k_04444 | relation=بخاخات الماء والملح --TREATS--> سيلان الانف: جرب بخاخات الماء والملح
  Source question: طفلي عمر سنتين يعاني من سيلان الانف باستمرار وبالليل تتقفل نهاي مايقدر يتنفس اعطيناهو علاجات مضاد حيوي دون فايده
  Source answer: جرب بخاخات الماء والملح.وفي حال عدم التحسن لابد من عرضه على اخصائي الاطفال.رجاء لاتعطي اي مضاد حيوي دون وصفة طبية.المضاد الحيوي ليس علاجاً لفتح الأنف!!!!

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_086: عندي فقر دم وعملت التحاليل عندي نقص فيتامين دال ونقص حديد وصف لي الدكتور 20 ابرة حديد لمدة شهر هل اخذ هالكمية بهذه المدة آمن أم مضر للجسم ؟ وما...

```text
User Question:
عندي فقر دم وعملت التحاليل عندي نقص فيتامين دال ونقص حديد وصف لي الدكتور 20 ابرة حديد لمدة شهر هل اخذ هالكمية بهذه المدة آمن أم مضر للجسم ؟ وما...

Retrieved Entities:
- نقص فيتامين (DiseaseCondition; match=exact; id=ent_diseasecondition_1b4cda592c0e)
- نقص حديد (DiseaseCondition; match=exact; id=ent_diseasecondition_6116bf50d3f1)
- فقر دم (DiseaseCondition; match=exact; id=ent_diseasecondition_99d821e71fc1)

Retrieved Relations:
- [1] فقر الدم --HAS_SYMPTOM--> الم المعدجة (score=0.86682; reliability=strong)
- [2] فقر الدم --HAS_SYMPTOM--> تنميل (score=0.816292; reliability=medium)
- [3] فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (score=0.80682; reliability=medium)
- [4] نقص هرمونات --HAS_SYMPTOM--> انقطاع الطمث (score=0.763; reliability=medium)
- [5] نقص حديد --DIAGNOSED_BY--> فحص تحاليل مخبرية (score=0.695822; reliability=limited)
- [6] انقطاع الطمث --SYMPTOM_OF--> نقص هرمونات (score=0.6774; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_02292 | relation=فقر الدم --HAS_SYMPTOM--> الم المعدجة: نقص في الدم مع الالم في المعده
  Source question: والدتي تعاني من نقص في الدم مع الالم في المعده
  Source answer: الم المعدجة يجب معرفة سببه وذل بعمل دراسة للمعدة ولنبدأ بفحص الجرثومة الحلزونية ، وربما سنحتاج لاحقا لمنظار للمعدة اما نقص الدم فهذ يجب توضيحة بشكل جيد ودراسته لمعرفة السبب وعلاجه
- E2 | qa_id=ahd5k_02546 | relation=فقر الدم --HAS_SYMPTOM--> الم المعدجة: أحيانا الم في المعدة كسل وخمول اضطرابات في النوم
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري
- E3 | qa_id=ahd5k_00838 | relation=فقر الدم --HAS_SYMPTOM--> تنميل: نقص فيتامين (ب12) يسبب انيميا وتنميل
  Source question: اشعر بتنميل من بداية النصف الاسفل من الجسم حتى اسفل القدم عند تحريك الرقبة الى اسفل و انا عندي انيميا هل لها علاقة
  Source answer: نعم ... نقص فيتامين (ب12) يسبب انيميا وتنميل
- E4 | qa_id=ahd5k_02546 | relation=فقر الدم --HAS_SYMPTOM--> فقدان الشهيه: فقر الدم سبب فقدان الشهيه
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري
- E5 | qa_id=ahd5k_04611 | relation=نقص هرمونات --HAS_SYMPTOM--> انقطاع الطمث: اعاني من مشكلة انقطاع الطمث...قال ان عندي مشكلة نقص هرمونات
  Source question: اعاني من مشكلة انقطاع الطمث لمدة شهرين كل مرة اي غير منتظمة و عندما زرت اخصائي قال ان عندي مشكلة نقص هرمونات هل يمكن وصف علاج لهذه الحالة مع العلم...
  Source answer: التقيم بحاجة الى اخذ تاريخ مرضي واضح ومن ثم الفحص السريري واخيرا عمل الفحوصات المخبرية والصورالشعاعية ومن ثم العلاج
- E6 | qa_id=ahd5k_01162 | relation=نقص حديد --DIAGNOSED_BY--> فحص تحاليل مخبرية: فحص التحاليل المخبرية مرتبط بتشخيص نقص حديد
  Source question: عندي فقر دم وعملت التحاليل عندي نقص فيتامين دال ونقص حديد وصف لي الدكتور 20 ابرة حديد لمدة شهر هل اخذ هالكمية بهذه المدة آمن أم مضر للجسم ؟ وما...
  Source answer: يجب الاعتماد على نسبة الهيموكلوبين لتحديد طريقة العلاج و كمية العلاج نسبة مخزون الحديد في الجسم مقبولة نعم يوجد نقص في نسبة فيتامين د تركيز الحديد يختلف حسب نوعية العلاج العدد المذكور في رسالتك غير مستوجب وغير متوافق مع التحليل المرسل مع السؤال
- E7 | qa_id=ahd5k_04611 | relation=انقطاع الطمث --SYMPTOM_OF--> نقص هرمونات: اعاني من مشكلة انقطاع الطمث...قال ان عندي مشكلة نقص هرمونات
  Source question: اعاني من مشكلة انقطاع الطمث لمدة شهرين كل مرة اي غير منتظمة و عندما زرت اخصائي قال ان عندي مشكلة نقص هرمونات هل يمكن وصف علاج لهذه الحالة مع العلم...
  Source answer: التقيم بحاجة الى اخذ تاريخ مرضي واضح ومن ثم الفحص السريري واخيرا عمل الفحوصات المخبرية والصورالشعاعية ومن ثم العلاج

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_087: أود معرفة ما أسباب تدلي المستقيم؟وطرق العلاج؟

```text
User Question:
أود معرفة ما أسباب تدلي المستقيم؟وطرق العلاج؟

Retrieved Entities:
- العلاج (Treatment; match=exact; id=ent_treatment_90baddc0bf15)

Retrieved Relations:
- [1] حساسية الصدر --HAS_SYMPTOM--> سعال (score=0.773137; reliability=medium)
- [2] التهاب --HAS_SYMPTOM--> الدم (score=0.757512; reliability=medium)
- [3] سعال --SYMPTOM_OF--> حساسية الصدر (score=0.687537; reliability=limited)
- [4] الدم --SYMPTOM_OF--> التهاب (score=0.671912; reliability=limited)
- [5] دوالي الخصية --TREATED_BY--> العلاج بالجراحة (score=0.527524; reliability=limited)
- [6] العلاج بالجراحة --TREATS--> دوالي الخصية (score=0.441924; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_04490 | relation=حساسية الصدر --HAS_SYMPTOM--> سعال: حساسية الصدر and سعال co-occur with explicit symptom-pathology link
  Source question: انا عندي قضيبي صغير هل هذه بسبب متعلق بهرمون الذكوره علما انا عمري 17 ويوجد شعر على الارجل والابط ولايوجد على الشارب وبدي اعرف اذا كان السبب متعلق بلهرمون كيفيه...
  Source answer: يجب اجراء الفحص السريري و الفحوصات المخبرية لتحديد السبب ثم العلاج
- E2 | qa_id=ahd5k_00666 | relation=التهاب --HAS_SYMPTOM--> الدم: التهاب في المثانة أو الإحليل يسبب خروج الدم
  Source question: انا عندي مشكله عندما انتهي من التبول يخرج في اخر البول دم؟
  Source answer: خروج الدم يعني وجود جرح في المثانة أو الإحليل. ويمكن آن يكون هذا ناتجاً عن وجود جرح ينزل منه الدم، حصوة في المثانة أو الإحليل؟ يمكمنك تصوير الجهاز البولي بصورة ملونر أي في بي لتحديد السبب والمكان، وبعدها يتحدد العلاج؟سلامتك
- E3 | qa_id=ahd5k_04490 | relation=سعال --SYMPTOM_OF--> حساسية الصدر: حساسية الصدر and سعال co-occur with explicit symptom-pathology link
  Source question: انا عندي قضيبي صغير هل هذه بسبب متعلق بهرمون الذكوره علما انا عمري 17 ويوجد شعر على الارجل والابط ولايوجد على الشارب وبدي اعرف اذا كان السبب متعلق بلهرمون كيفيه...
  Source answer: يجب اجراء الفحص السريري و الفحوصات المخبرية لتحديد السبب ثم العلاج
- E4 | qa_id=ahd5k_00666 | relation=الدم --SYMPTOM_OF--> التهاب: التهاب في المثانة أو الإحليل يسبب خروج الدم
  Source question: انا عندي مشكله عندما انتهي من التبول يخرج في اخر البول دم؟
  Source answer: خروج الدم يعني وجود جرح في المثانة أو الإحليل. ويمكن آن يكون هذا ناتجاً عن وجود جرح ينزل منه الدم، حصوة في المثانة أو الإحليل؟ يمكمنك تصوير الجهاز البولي بصورة ملونر أي في بي لتحديد السبب والمكان، وبعدها يتحدد العلاج؟سلامتك
- E5 | qa_id=ahd5k_00261 | relation=دوالي الخصية --TREATED_BY--> العلاج بالجراحة: العلاج بالجراحة
  Source question: اشعر بتدلى الخصيتين بشكل غير طبيعى لدرجة انه يؤثر على طول القضيب اثناء الارتخاء ويوجد بكيس الصفن عروق كثيره ولكنها لا تؤلمنى ما سبب هذه الحالة ارجو الاجابة
  Source answer: هي في الغالب دوالي الخصية. فاذهب إلى اختصاصي بالجراحة أو المسالك البولية واستشره. وراجع دوالي الخصية.
- E6 | qa_id=ahd5k_00261 | relation=العلاج بالجراحة --TREATS--> دوالي الخصية: العلاج بالجراحة
  Source question: اشعر بتدلى الخصيتين بشكل غير طبيعى لدرجة انه يؤثر على طول القضيب اثناء الارتخاء ويوجد بكيس الصفن عروق كثيره ولكنها لا تؤلمنى ما سبب هذه الحالة ارجو الاجابة
  Source answer: هي في الغالب دوالي الخصية. فاذهب إلى اختصاصي بالجراحة أو المسالك البولية واستشره. وراجع دوالي الخصية.

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_088: كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟

```text
User Question:
كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟

Retrieved Entities:
- الجلد المترهل (DiseaseCondition; match=exact; id=ent_diseasecondition_adcc5a085807)

Retrieved Relations:
- [1] الجلد المترهل --TREATED_BY--> الجراحة التجميلية (score=0.956489; reliability=medium)
- [2] مرض السكري --HAS_SYMPTOM--> ضغط الدم (score=0.7647; reliability=medium)
- [3] الجراحة التجميلية --TREATS--> الجلد المترهل (score=0.424409; reliability=limited)
- [4] ضغط الدم --SYMPTOM_OF--> مرض السكري (score=0.3171; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_01190 | relation=الجلد المترهل --TREATED_BY--> الجراحة التجميلية: يمكن شده بممارسة الرياضة أو بالجراحة التجميلية
  Source question: كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟
  Source answer: يمكن شده بممارسة الرياضة أو بالجراحة التجميلية.راجعي اختصاصي تجميل.
- E2 | qa_id=ahd5k_04912 | relation=مرض السكري --HAS_SYMPTOM--> ضغط الدم: مع العلم أن المريض يعاني من مرض السكر
  Source question: هل ضعف عضله القلب وضيق ثلاث شرايين في القلب لهم عمليه جراحيه مع العلم أن المريض يعاني من مرض السكر ام يبقى على العلاج ولو عمليه جراحيهوين تنصحونا نعملها وعاووزيين...
  Source answer: هذا يتطلب معرفة نسبة الضعف الموجود في العضلة القلبية ونسبة التضيق في الثلاثة شرايين المذكورة، كما أنه من الضروري معرفة الحالة الوظيفية لباقي أعضاء الجسم خاصة الكلى والجهاز التنفسي، والكبد وغيره، وفي جميع الأحوال في العادة تُعرض نتائج القثطرة على فريق طبي مُتخصص لتقييم كل هذه الأمور ومن ثم يتم اختيار الطريقة العلاجية التي تتناسب أكثر مع حالة المريض
- E3 | qa_id=ahd5k_01190 | relation=الجراحة التجميلية --TREATS--> الجلد المترهل: يمكن شده بممارسة الرياضة أو بالجراحة التجميلية
  Source question: كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟
  Source answer: يمكن شده بممارسة الرياضة أو بالجراحة التجميلية.راجعي اختصاصي تجميل.
- E4 | qa_id=ahd5k_04912 | relation=ضغط الدم --SYMPTOM_OF--> مرض السكري: مع العلم أن المريض يعاني من مرض السكر
  Source question: هل ضعف عضله القلب وضيق ثلاث شرايين في القلب لهم عمليه جراحيه مع العلم أن المريض يعاني من مرض السكر ام يبقى على العلاج ولو عمليه جراحيهوين تنصحونا نعملها وعاووزيين...
  Source answer: هذا يتطلب معرفة نسبة الضعف الموجود في العضلة القلبية ونسبة التضيق في الثلاثة شرايين المذكورة، كما أنه من الضروري معرفة الحالة الوظيفية لباقي أعضاء الجسم خاصة الكلى والجهاز التنفسي، والكبد وغيره، وفي جميع الأحوال في العادة تُعرض نتائج القثطرة على فريق طبي مُتخصص لتقييم كل هذه الأمور ومن ثم يتم اختيار الطريقة العلاجية التي تتناسب أكثر مع حالة المريض

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_089: السلام عليكم عمري43 اعاني ارتفاع الصفراء في الدم وصلت الي 7.6 ويوجد تضخم في الطحال والم ف اسفل البطن وجانبين الي الظهر مع احساس بالتعب تحاليل للفيروسات سلبي ومناعةانكا 1/80

```text
User Question:
السلام عليكم عمري43 اعاني ارتفاع الصفراء في الدم وصلت الي 7.6 ويوجد تضخم في الطحال والم ف اسفل البطن وجانبين الي الظهر مع احساس بالتعب تحاليل للفيروسات سلبي ومناعةانكا 1/80

Retrieved Entities:
- تضخم (DiseaseCondition; match=exact; id=ent_diseasecondition_4453ab65a84b)
- تعب (Symptom; match=exact; id=ent_symptom_28acc791e82d)

Retrieved Relations:
- [1] تضخم --HAS_SYMPTOM--> تضخم في الارداف (score=0.850693; reliability=medium)
- [2] التهاب --HAS_SYMPTOM--> تعب (score=0.774964; reliability=medium)
- [3] تعب --SYMPTOM_OF--> التهاب (score=0.773844; reliability=medium)
- [4] ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب (score=0.762152; reliability=medium)
- [5] التهاب --HAS_SYMPTOM--> ضيق تنفس (score=0.761168; reliability=medium)
- [6] ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس (score=0.757928; reliability=medium)

Evidence Sentences:
- E1 | qa_id=ahd5k_00647 | relation=تضخم --HAS_SYMPTOM--> تضخم في الارداف: تضخم في الارداف
  Source question: يا دكتور انا شاب اعاني من تضخم في الارداف والا فخاذ اريد حل لهذه المشكله لأنها تسبب احراج انا شاب
  Source answer: هذا فالغالب شيء وراثي يعتمد على الجينات، يستحسن زيارة اختصاصي الأمراض الوراثية وبحث الموضوع معه.
- E2 | qa_id=ahd5k_03872 | relation=التهاب --HAS_SYMPTOM--> تعب: اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام
  Source question: السلام وعليكم ورحمة الله وبركاتو اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام .ارجو الاجابه وشكرا...
  Source answer: أعراض التهاب وحساسيه الجيوب الانفيه لابد من استخدام الادويه المناسبه بعد الفحص عند طبيب ENT
- E3 | qa_id=ahd5k_03872 | relation=تعب --SYMPTOM_OF--> التهاب: اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام
  Source question: السلام وعليكم ورحمة الله وبركاتو اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام .ارجو الاجابه وشكرا...
  Source answer: أعراض التهاب وحساسيه الجيوب الانفيه لابد من استخدام الادويه المناسبه بعد الفحص عند طبيب ENT
- E4 | qa_id=ahd5k_00823 | relation=ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب: خفقان احيتنا
  Source question: اجريت عمليه استبدال صمام ميترالي في 89ثم الاورطي في 2013 والان اعاني من ارتفاع الضغط وضيق تنفس وخفقان احيتنا
  Source answer: تحتاج الى تقييم سريري كامل مع اجراء بعض الفحوصات
- E5 | qa_id=ahd5k_03872 | relation=التهاب --HAS_SYMPTOM--> ضيق تنفس: اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام
  Source question: السلام وعليكم ورحمة الله وبركاتو اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام .ارجو الاجابه وشكرا...
  Source answer: أعراض التهاب وحساسيه الجيوب الانفيه لابد من استخدام الادويه المناسبه بعد الفحص عند طبيب ENT
- E6 | qa_id=ahd5k_00823 | relation=ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس: ضيق تنفس
  Source question: اجريت عمليه استبدال صمام ميترالي في 89ثم الاورطي في 2013 والان اعاني من ارتفاع الضغط وضيق تنفس وخفقان احيتنا
  Source answer: تحتاج الى تقييم سريري كامل مع اجراء بعض الفحوصات

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_090: اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج للعصب السابع بعد مضي هذه المدة الزمنه

```text
User Question:
اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج للعصب السابع بعد مضي هذه المدة الزمنه

Retrieved Entities:
- الطعام (Treatment; match=exact; id=ent_treatment_60ce765ad441)

Retrieved Relations:
- [1] شلل العصب السابع --TREATED_BY--> الكورتيزونات (score=0.626529; reliability=limited)
- [2] شلل العصب السابع --TREATED_BY--> مضادات الالتهاب (score=0.615969; reliability=limited)
- [3] شلل العصب السابع --TREATED_BY--> العلاج الطبيعي (score=0.615969; reliability=limited)
- [4] شلل العصب السابع --TREATED_BY--> مضادات الفيروسات (score=0.615969; reliability=limited)
- [5] شلل العصب السابع --TREATED_BY--> العلاج بالإبر الصينية (score=0.605409; reliability=limited)
- [6] الكورتيزونات --TREATS--> شلل العصب السابع (score=0.540929; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_01221 | relation=شلل العصب السابع --TREATED_BY--> الكورتيزونات: الكورتيزونات
  Source question: اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج للعصب السابع بعد مضي هذه المدة الزمنه
  Source answer: يصعب علاج شلل العصب السابع كلما تأخر العلاج، والعلاج المتبع عادة هو مضادات الالتهاب والكورتيزونات، وقد يضاف إليها مضادات الفيروسات، وقد يستفيد بعض المرضى من العلاج الطبيعي أو العلاج بالإبر الصينية، ولكن التأخر في العلاج يصعب الأمور.
- E2 | qa_id=ahd5k_01221 | relation=شلل العصب السابع --TREATED_BY--> مضادات الالتهاب: مضادات الالتهاب
  Source question: اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج للعصب السابع بعد مضي هذه المدة الزمنه
  Source answer: يصعب علاج شلل العصب السابع كلما تأخر العلاج، والعلاج المتبع عادة هو مضادات الالتهاب والكورتيزونات، وقد يضاف إليها مضادات الفيروسات، وقد يستفيد بعض المرضى من العلاج الطبيعي أو العلاج بالإبر الصينية، ولكن التأخر في العلاج يصعب الأمور.
- E3 | qa_id=ahd5k_01221 | relation=شلل العصب السابع --TREATED_BY--> العلاج الطبيعي: العلاج الطبيعي
  Source question: اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج للعصب السابع بعد مضي هذه المدة الزمنه
  Source answer: يصعب علاج شلل العصب السابع كلما تأخر العلاج، والعلاج المتبع عادة هو مضادات الالتهاب والكورتيزونات، وقد يضاف إليها مضادات الفيروسات، وقد يستفيد بعض المرضى من العلاج الطبيعي أو العلاج بالإبر الصينية، ولكن التأخر في العلاج يصعب الأمور.
- E4 | qa_id=ahd5k_01221 | relation=شلل العصب السابع --TREATED_BY--> مضادات الفيروسات: مضادات الفيروسات
  Source question: اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج للعصب السابع بعد مضي هذه المدة الزمنه
  Source answer: يصعب علاج شلل العصب السابع كلما تأخر العلاج، والعلاج المتبع عادة هو مضادات الالتهاب والكورتيزونات، وقد يضاف إليها مضادات الفيروسات، وقد يستفيد بعض المرضى من العلاج الطبيعي أو العلاج بالإبر الصينية، ولكن التأخر في العلاج يصعب الأمور.
- E5 | qa_id=ahd5k_01221 | relation=شلل العصب السابع --TREATED_BY--> العلاج بالإبر الصينية: العلاج بالإبر الصينية
  Source question: اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج للعصب السابع بعد مضي هذه المدة الزمنه
  Source answer: يصعب علاج شلل العصب السابع كلما تأخر العلاج، والعلاج المتبع عادة هو مضادات الالتهاب والكورتيزونات، وقد يضاف إليها مضادات الفيروسات، وقد يستفيد بعض المرضى من العلاج الطبيعي أو العلاج بالإبر الصينية، ولكن التأخر في العلاج يصعب الأمور.
- E6 | qa_id=ahd5k_01221 | relation=الكورتيزونات --TREATS--> شلل العصب السابع: الكورتيزونات
  Source question: اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج للعصب السابع بعد مضي هذه المدة الزمنه
  Source answer: يصعب علاج شلل العصب السابع كلما تأخر العلاج، والعلاج المتبع عادة هو مضادات الالتهاب والكورتيزونات، وقد يضاف إليها مضادات الفيروسات، وقد يستفيد بعض المرضى من العلاج الطبيعي أو العلاج بالإبر الصينية، ولكن التأخر في العلاج يصعب الأمور.

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_091: تناولت مضاد حيووي زييثرون وانتج حساسيه شديده وتورم في المنطقة التناسليه وانا تعبانه جدا ما الحل ؟

```text
User Question:
تناولت مضاد حيووي زييثرون وانتج حساسيه شديده وتورم في المنطقة التناسليه وانا تعبانه جدا ما الحل ؟

Retrieved Entities:
- حساسية (DiseaseCondition; match=exact; id=ent_diseasecondition_2f75d3dabe0b)
- حساسية الصدر (DiseaseCondition; match=alias; id=ent_diseasecondition_250910ab0701)

Retrieved Relations:
- [1] حساسية --TREATED_BY--> مضاد الهيستامين (score=0.938241; reliability=medium)
- [2] حساسية --TREATED_BY--> كورتيزون (score=0.938241; reliability=medium)
- [3] حساسية --TREATED_BY--> تيليفاست (score=0.877235; reliability=medium)
- [4] حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين (score=0.868151; reliability=medium)
- [5] حساسية --TREATED_BY--> حليب مكسر بروتين الحليب (score=0.851942; reliability=medium)
- [6] حساسية --TREATED_BY--> نازونكس (score=0.851942; reliability=medium)

Evidence Sentences:
- E1 | qa_id=ahd5k_01231 | relation=حساسية --TREATED_BY--> مضاد الهيستامين: استخدمي مضاد هيسامين وكورتيزون موضعي
  Source question: تناولت مضاد حيووي زييثرون وانتج حساسيه شديده وتورم في المنطقة التناسليه وانا تعبانه جدا ما الحل ؟
  Source answer: لاتاخذيه مره اخرى استخدمي مضاد هيسامين وكورتيزون موضعي اعملي تحليل حساسية المضادات
- E2 | qa_id=ahd5k_01231 | relation=حساسية --TREATED_BY--> كورتيزون: استخدمي مضاد هيسامين وكورتيزون موضعي
  Source question: تناولت مضاد حيووي زييثرون وانتج حساسيه شديده وتورم في المنطقة التناسليه وانا تعبانه جدا ما الحل ؟
  Source answer: لاتاخذيه مره اخرى استخدمي مضاد هيسامين وكورتيزون موضعي اعملي تحليل حساسية المضادات
- E3 | qa_id=ahd5k_02470 | relation=حساسية --TREATED_BY--> تيليفاست: مضاد للهيستامين مثل تيليفاست
  Source question: سوألي هناك فتاه تشعر بحراره شديده في جسمها الخارجي وقليل جدا من داخل جسمها ولاترتاح الا بالاغتسال ومستمر الحال معها قرابه الثلاث ايام ماهو التشخيص لهذي الحاله وشكراا
  Source answer: قد يكون عندها نوع من أنواع الحساسية، ننصحها بالمكوث قي جو بارد وتناول مضاد للهيستامين مثل تيليفاست أو إكزوفين أ, أي نوع آخر
- E4 | qa_id=ahd5k_00812 | relation=حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين: للاسف اهم علاج تجنب المنتجات التي تحوي جلوتين
  Source question: طفلتي تتحسس من الجلوتين وعمرها سنة ونصف هل توجد أدوية تساعد على الشفاء من هذا المرض ام لا ؟؟
  Source answer: للاسف اهم علاج تجنب المنتجات التي تحوي جلوتين
- E5 | qa_id=ahd5k_00020 | relation=حساسية --TREATED_BY--> حليب مكسر بروتين الحليب: اعطيها حليب مكسر بروتين الحليب بالكامل او حليب رز
  Source question: بنتي سنتين ونصف عندها حساسية من حليب البقر وتأخذ حليب خاص قليل التحسس HA لكن دائم مسبب لها غازات وانتفاخ بالبطن أريد أن اوقفه ما الاكل الي فيه نسب من...
  Source answer: اعطيها حليب مكسر بروتين الحليب بالكامل او حليب رز
- E6 | qa_id=ahd5k_00133 | relation=حساسية --TREATED_BY--> نازونكس: بدائل يوجد نازونكس وافاميز وتابونكس وفليكسونيز
  Source question: تصاص كلينيل نازال سبراي قلو بديل لان ما عم لاقي منو مع العلم عندي تحسس انفي موسمي بيتغير حسب المواسم
  Source answer: بدائل يوجد نازونكس وافاميز وتابونكس وفليكسونيز

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_092: انا اشعر بالصداع والنعاس وحساسية في وجهي والحكة بكل انحاء جسمي كيف استطيع ان اوقف هذا الدواء

```text
User Question:
انا اشعر بالصداع والنعاس وحساسية في وجهي والحكة بكل انحاء جسمي كيف استطيع ان اوقف هذا الدواء

Retrieved Entities:
- حساسية (DiseaseCondition; match=exact; id=ent_diseasecondition_2f75d3dabe0b)
- صداع (Symptom; match=exact; id=ent_symptom_b754f1a1e5a8)
- الدواء (Treatment; match=exact; id=ent_treatment_1479a48d3d42)
- حكة (Symptom; match=exact; id=ent_symptom_7cfc95737dc0)
- حساسية الصدر (DiseaseCondition; match=alias; id=ent_diseasecondition_250910ab0701)
- صداع التوتر (Symptom; match=alias; id=ent_symptom_c01e00eb5c72)

Retrieved Relations:
- [1] حساسية --HAS_SYMPTOM--> سعال (score=0.93426; reliability=strong)
- [2] حساسية --HAS_SYMPTOM--> ضيق تنفس (score=0.93185; reliability=strong)
- [3] حساسية --HAS_SYMPTOM--> بلغم (score=0.868986; reliability=medium)
- [4] حساسية --HAS_SYMPTOM--> نشفان (score=0.860949; reliability=medium)
- [5] حساسية الصدر --HAS_SYMPTOM--> سعال (score=0.834144; reliability=medium)
- [6] صداع --SYMPTOM_OF--> التهاب السحايا (score=0.794444; reliability=medium)

Evidence Sentences:
- E1 | qa_id=ahd5k_00970 | relation=حساسية --HAS_SYMPTOM--> سعال: هل هو ربو ؟؟ او هل هناك حساسية ابسط من ذلك وعوارضها فقط السعال والبلغم
  Source question: ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟ هل امتنع عن طعام معين يزيد البلغم وانا غير مدخن واخذ علاج للضغط والكوليسترول عمرى 55...
  Source answer: اذا كنت مدخنا يجب الاقلاع عن التدخين نهائياً وقطعياً علما بأنك لا تدخن كما قلت لكن جلوسك في مكان فيه مدخنين يجعلك مدخناً ايضاً اذا كنت تعاني من التهاب ما في الجزء العلوي من الجهاز التنفسي يجب ان تتعالج يجب التأكد من ما تعانيه هل هو ربو ؟؟ او هل هناك حساسية ابسط من ذلك وعوارضها فقط السعال والبلغم يجب التأكد من ذلك وانصحك بان تطلب معاينة من اخصائي حساسية لكي يعطيك التشخيص النهائي وعندها الطريق الى العلاج يكون اسهل
- E2 | qa_id=ahd5k_00069 | relation=حساسية --HAS_SYMPTOM--> سعال: حساسية الصدر وسعال
  Source question: انا قبل يجي طقطقة في الفك الايسر بدون اللم وبعد ما سويت التمرين راح طقطقة الفك وجاني اللم هل هذا امر عادي بسبب التمرين ولا لل
  Source answer: طبيعي بسبب التمرين ومع الوقت بيختفي الألم وممكن استعمال بعض المسكنات الخفيفه
- E3 | qa_id=ahd5k_00683 | relation=حساسية --HAS_SYMPTOM--> ضيق تنفس: ضيق تنفس وسرعة التعب وقلق
  Source question: مرحبا اعاني منذ فتره من نبضات قلي قويه واصبحت اشعر بها في جميع اجزاء جسمي خصوصا قبل النوم وضيق تنفس وسرعة التعب وقلق علما اني تعرضت لموقف قلق وتوتر ووخزات...
  Source answer: أتمنى لك السلامة، وأود الإشارة إلى ضرورة مراجعة الطبيب لتحديد الأسباب المحتملة ووصف العلاج المناسب فلا يجب إهمال هذه الأعراض، وبشكل عام قد يكون ذلك ناجم عن العديد من الأسباب، ومنها الآتي: القلق أو التوتر. ممارسة الرياضة أو النشاط البدني. الجفاف. ارتفاع درجة حرارة الجسم. الحساسية. اضطرابات الغدة الدرقية. أمراض القلب. اضطرابات الجهاز التنفسي. الاضطرابات العصبية. للمزيد: ما هي اسباب زيادة ضربات القلب المفاجئ؟ ما هي أهم طرق علاج ضربات القلب السريعة في المنزل؟
- E4 | qa_id=ahd5k_00010 | relation=حساسية --HAS_SYMPTOM--> ضيق تنفس: حساسية تسبب ضيق تنفس
  Source question: يوجد أعراض ترعبني. عند الصعود بالدرج او مرتفع ينقطع نفسي ويجب ان استريح علماً باني ب٢٦ من العمر ومن قبل كانت هناك آلام في الصدر غريبه كنت اتجاهلها علما بان...
  Source answer: لم تذكر خصائص ضيق النفس، لكن الفحص الطبي السريري ضروري كونه يسمح بالتأكد من خصائص الأعراض المذكورة والعلامات التي قد يجدها الطبيب عند الفحص، لأن الأسباب كثيرة تنفسية وقلبية ودموية ووعائية وغير ذلك
- E5 | qa_id=ahd5k_00970 | relation=حساسية --HAS_SYMPTOM--> بلغم: ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟
  Source question: ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟ هل امتنع عن طعام معين يزيد البلغم وانا غير مدخن واخذ علاج للضغط والكوليسترول عمرى 55...
  Source answer: اذا كنت مدخنا يجب الاقلاع عن التدخين نهائياً وقطعياً علما بأنك لا تدخن كما قلت لكن جلوسك في مكان فيه مدخنين يجعلك مدخناً ايضاً اذا كنت تعاني من التهاب ما في الجزء العلوي من الجهاز التنفسي يجب ان تتعالج يجب التأكد من ما تعانيه هل هو ربو ؟؟ او هل هناك حساسية ابسط من ذلك وعوارضها فقط السعال والبلغم يجب التأكد من ذلك وانصحك بان تطلب معاينة من اخصائي حساسية لكي يعطيك التشخيص النهائي وعندها الطريق الى العلاج يكون اسهل
- E6 | qa_id=ahd5k_02124 | relation=حساسية --HAS_SYMPTOM--> نشفان: واشعر بنشفان دائم في الحلق
  Source question: اصبت بحساسية في الصيف بالجسم وصفها الدكتور بحساسية شمس و بعد فترة اصبت بالتهاب لوز و بلعوم و حبوب في اخر الحلق الحبوب مازالت موجودة واشعر بنشفان دائم في الحلق...
  Source answer: الاعراض التي في الحلق أعراض فيروس مثل الكوكساكي فيروس تتحسن مع الوقت عليك بتقوية المناعة بأكل الفواكة والحمضيات وشرب الزنجبيل مع العسل والليمون مره باليوم الزنجبيل مطحون بمعدل معلقه صغيره يوجد أيضا شراب ECHINACEA يحسن حالتك
- E7 | qa_id=ahd5k_04490 | relation=حساسية الصدر --HAS_SYMPTOM--> سعال: حساسية الصدر and سعال co-occur with explicit symptom-pathology link
  Source question: انا عندي قضيبي صغير هل هذه بسبب متعلق بهرمون الذكوره علما انا عمري 17 ويوجد شعر على الارجل والابط ولايوجد على الشارب وبدي اعرف اذا كان السبب متعلق بلهرمون كيفيه...
  Source answer: يجب اجراء الفحص السريري و الفحوصات المخبرية لتحديد السبب ثم العلاج
- E8 | qa_id=ahd5k_02662 | relation=صداع --SYMPTOM_OF--> التهاب السحايا: صداع
  Source question: لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام لهذا السبب
  Source answer: إن الألم في الرأس مع الشعور بالضغط على جانبي الرأس مع الإرهاق العام قد يعود لأحد الأسباب التالية: صداع التوتر. الشد العضلي. الضغط العصبي. القلق والتوتر أو الاكتئاب. التهاب الجيوب الأنفية. الشقيقة (الصداع النصفي). وجود مشاكل في الأذن التهاب السحايا. تمدد الأوعية الدموية في الدماغ. ينصح في الوقت الحالي زيارة الطبيب المختص لعمل الفحوصات والتحاليل اللازمة في حال عدم نجاح النصائح التالية: استخدام الأدوية المسكنة للألم حسب تعليمات الطبيب المختص مثل الايبوبروفين وغيرها. اتباع طرق التنفس العميق من أجل الاسترخاء وخفض مستويات هرمونات التوتر. ممارسة تمارين الاسترخاء مثل اليوغا والتأمل. تجنب القلق أو التوتر. للمزيد: اسباب الصداع ومحفزاته التدليك لعلاج الصداع هل تعاني من صداع من دون معرفة سببه؟ المرجع...

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_093: لا أستطبع النوم على جانبي لا الأيمن ولا الأيسر وأجد صعوبة في التنفس العميق. كما أشعر بين الفينة والأخرى بآلام قرب القلب. كما أخبركم أني مريصة بالقلب (مشكل في صمامتين)

```text
User Question:
لا أستطبع النوم على جانبي لا الأيمن ولا الأيسر وأجد صعوبة في التنفس العميق. كما أشعر بين الفينة والأخرى بآلام قرب القلب. كما أخبركم أني مريصة بالقلب (مشكل في صمامتين)

Retrieved Entities:
- الام (Symptom; match=exact; id=ent_symptom_249d07021a1b)

Retrieved Relations:
- [1] ضرس العقل --HAS_SYMPTOM--> الام (score=0.759876; reliability=medium)
- [2] الام --SYMPTOM_OF--> ضرس العقل (score=0.758756; reliability=medium)
- [3] فقر الدم --HAS_SYMPTOM--> الم المعدجة (score=0.748854; reliability=limited)
- [4] فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (score=0.748854; reliability=limited)
- [5] ضرس العقل --HAS_SYMPTOM--> صداع (score=0.743612; reliability=limited)
- [6] الم المعدجة --SYMPTOM_OF--> فقر الدم (score=0.663254; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_04356 | relation=ضرس العقل --HAS_SYMPTOM--> الام: ضرس العقل
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين
- E2 | qa_id=ahd5k_04356 | relation=الام --SYMPTOM_OF--> ضرس العقل: ضرس العقل
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين
- E3 | qa_id=ahd5k_02546 | relation=فقر الدم --HAS_SYMPTOM--> الم المعدجة: أحيانا الم في المعدة كسل وخمول اضطرابات في النوم
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري
- E4 | qa_id=ahd5k_02546 | relation=فقر الدم --HAS_SYMPTOM--> فقدان الشهيه: فقر الدم سبب فقدان الشهيه
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري
- E5 | qa_id=ahd5k_04356 | relation=ضرس العقل --HAS_SYMPTOM--> صداع: ضرس العقل
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين
- E6 | qa_id=ahd5k_02546 | relation=الم المعدجة --SYMPTOM_OF--> فقر الدم: أحيانا الم في المعدة كسل وخمول اضطرابات في النوم
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_094: هل هناك أسباب أخرى محددة تؤدي الى ولادة دات شفة مشقوقة من غير استعمال دواء التوبيراميت.

```text
User Question:
هل هناك أسباب أخرى محددة تؤدي الى ولادة دات شفة مشقوقة من غير استعمال دواء التوبيراميت.

Retrieved Entities:
- شفة مشقوقة (DiseaseCondition; match=exact; id=ent_diseasecondition_2a6dda2fbaec)
- توبيراميت (Treatment; match=exact; id=ent_treatment_07bda7f8e857)

Retrieved Relations:
- [1] قرحة --TREATED_BY--> ايزومبرازول (score=0.526712; reliability=limited)
- [2] شيب --TREATED_BY--> خلطة الريحان و الروزماري (score=0.519498; reliability=limited)
- [3] ايزومبرازول --TREATS--> قرحة (score=0.441112; reliability=limited)
- [4] خلطة الريحان و الروزماري --TREATS--> شيب (score=0.433898; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_01066 | relation=قرحة --TREATED_BY--> ايزومبرازول: ممكن تجرب دواء اسمه ايزومبرازول
  Source question: مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد المستشفی
  Source answer: هل افهم من سؤالك ان والدتك عندها قرحه مع نزيف مستمر اذا كان الامر هكذا فلابد من ذهابها الى المستشفى لان النزيف المستمر سيشكل خطر على حياتها. اما اذا كانت القرحه مؤكده بدون نزيف فممكن تجرب دواء اسمه ايزومبرازول ٤٠ مج يوميا لمدة ٣ شهور. ان لم يحدث تحسن من البدايه فيجب الذهاب الى المستشفى
- E2 | qa_id=ahd5k_04612 | relation=شيب --TREATED_BY--> خلطة الريحان و الروزماري: هل خلطة الريحان و الروزماري مفيدة للتخلص من الشيب
  Source question: هل يوجد حل لعلاج الشيب المبكر ؟ هل خلطة الريحان و الروزماري مفيدة للتخلص من الشيب؟
  Source answer: لشيب (الشعر الأبيض) ظهور الشيب عملية فسيولوجية تحدث عادة عند التقدم في العمر. وذلك عندما لا تستطيع الخلايا الملونة التي تفرز مادة الميلانين (والتي تعطي الشعرة اللون) الاستمرار في نشاطها، إذ تفقد الشعرة لونها وتصبح بيضاء وهذا ما يسمى "بالشيب". إن ظهور الشيب على شعر الرأس أو الوجه لا يعني مطلقاً التقدم بالسن فقد يظهر قبل البلوغ أو بعد ذلك نتيجة ظروف معينة. كما أن الاستعداد الشخصي والعوامل النفسية والوراثية لهما أثر مهم في ظهور الشيب المبكر. ويجب الإشارة بأن بعض حالات الشيب المبكر تكون مؤقتة، إذ قد تعاود الخلايا الملونة نشاطها مرة أخرى خاصة بعد زوال المؤثر وبالتالي يعود لون الشعر إلى وضعه العادي ويحدث هذا أحياناً في أمراض الحميات ومرض الثعلبة. أما إذا كان المؤثر على الخلايا الأم (الكيراتينوس...
- E3 | qa_id=ahd5k_01066 | relation=ايزومبرازول --TREATS--> قرحة: ممكن تجرب دواء اسمه ايزومبرازول
  Source question: مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد المستشفی
  Source answer: هل افهم من سؤالك ان والدتك عندها قرحه مع نزيف مستمر اذا كان الامر هكذا فلابد من ذهابها الى المستشفى لان النزيف المستمر سيشكل خطر على حياتها. اما اذا كانت القرحه مؤكده بدون نزيف فممكن تجرب دواء اسمه ايزومبرازول ٤٠ مج يوميا لمدة ٣ شهور. ان لم يحدث تحسن من البدايه فيجب الذهاب الى المستشفى
- E4 | qa_id=ahd5k_04612 | relation=خلطة الريحان و الروزماري --TREATS--> شيب: هل خلطة الريحان و الروزماري مفيدة للتخلص من الشيب
  Source question: هل يوجد حل لعلاج الشيب المبكر ؟ هل خلطة الريحان و الروزماري مفيدة للتخلص من الشيب؟
  Source answer: لشيب (الشعر الأبيض) ظهور الشيب عملية فسيولوجية تحدث عادة عند التقدم في العمر. وذلك عندما لا تستطيع الخلايا الملونة التي تفرز مادة الميلانين (والتي تعطي الشعرة اللون) الاستمرار في نشاطها، إذ تفقد الشعرة لونها وتصبح بيضاء وهذا ما يسمى "بالشيب". إن ظهور الشيب على شعر الرأس أو الوجه لا يعني مطلقاً التقدم بالسن فقد يظهر قبل البلوغ أو بعد ذلك نتيجة ظروف معينة. كما أن الاستعداد الشخصي والعوامل النفسية والوراثية لهما أثر مهم في ظهور الشيب المبكر. ويجب الإشارة بأن بعض حالات الشيب المبكر تكون مؤقتة، إذ قد تعاود الخلايا الملونة نشاطها مرة أخرى خاصة بعد زوال المؤثر وبالتالي يعود لون الشعر إلى وضعه العادي ويحدث هذا أحياناً في أمراض الحميات ومرض الثعلبة. أما إذا كان المؤثر على الخلايا الأم (الكيراتينوس...

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_095: كيف تتم ازالة شظايا القنابل الصغيرة الانشطارية في المنزل عند عدم التمكن من الذهاب للمستشفى وهل هناك اخطار من بقائها؟

```text
User Question:
كيف تتم ازالة شظايا القنابل الصغيرة الانشطارية في المنزل عند عدم التمكن من الذهاب للمستشفى وهل هناك اخطار من بقائها؟

Retrieved Entities:
- شظايا القنابل الصغيرة الانشطارية (DiseaseCondition; match=exact; id=ent_diseasecondition_1730144a5e89)

Retrieved Relations:
- [1] شظايا القنابل الصغيرة الانشطارية --DIAGNOSED_BY--> أشعة (score=0.936577; reliability=medium)
- [2] التهاب --DIAGNOSED_BY--> تحليل بول (score=0.748328; reliability=limited)
- [3] التهاب --TREATED_BY--> الاكثار من شرب الماء (score=0.748328; reliability=limited)
- [4] أشعة --DIAGNOSES--> شظايا القنابل الصغيرة الانشطارية (score=0.404497; reliability=limited)
- [5] تحليل بول --DIAGNOSES--> التهاب (score=0.300728; reliability=limited)
- [6] الاكثار من شرب الماء --TREATS--> التهاب (score=0.300728; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_01290 | relation=شظايا القنابل الصغيرة الانشطارية --DIAGNOSED_BY--> أشعة: عمل تصوير بالأشعة لتحديد مكان الشظايا ونوعها
  Source question: كيف تتم ازالة شظايا القنابل الصغيرة الانشطارية في المنزل عند عدم التمكن من الذهاب للمستشفى وهل هناك اخطار من بقائها؟
  Source answer: حسب نوعية هذه الشظايا، ولكن في الغالب لا تؤثر في الجسم لأن الجسم يصنع محفظات حولها ويعزلها، ولكن الأفضل مراجعة مستشفى في الفرصة المناسبة وعمل تصوير بالأشعة لتحديد مكان الشظايا ونوعها، وربما استئصالها إذا أمكن.
- E2 | qa_id=ahd5k_04706 | relation=التهاب --DIAGNOSED_BY--> تحليل بول: عمل تحليل بول
  Source question: اشعر بالم عند الاستيقاظ فى الكليتين من النوم و عندما اتنفس يزيد الالم .. و بعد الاستيقاظ و التبول و شرب الماء يختفى الالم .. كل يوم اشعر بذلك ارجو...
  Source answer: الف سلامة انصحك بعمل تحليل بول و نسبة يوريك اسيد و سونار على البطن و الحوض مبدئيا و من ثم مراجعة طبيب مسالك و الاكثار من شرب الماء
- E3 | qa_id=ahd5k_04706 | relation=التهاب --TREATED_BY--> الاكثار من شرب الماء: الاكثار من شرب الماء
  Source question: اشعر بالم عند الاستيقاظ فى الكليتين من النوم و عندما اتنفس يزيد الالم .. و بعد الاستيقاظ و التبول و شرب الماء يختفى الالم .. كل يوم اشعر بذلك ارجو...
  Source answer: الف سلامة انصحك بعمل تحليل بول و نسبة يوريك اسيد و سونار على البطن و الحوض مبدئيا و من ثم مراجعة طبيب مسالك و الاكثار من شرب الماء
- E4 | qa_id=ahd5k_01290 | relation=أشعة --DIAGNOSES--> شظايا القنابل الصغيرة الانشطارية: عمل تصوير بالأشعة لتحديد مكان الشظايا ونوعها
  Source question: كيف تتم ازالة شظايا القنابل الصغيرة الانشطارية في المنزل عند عدم التمكن من الذهاب للمستشفى وهل هناك اخطار من بقائها؟
  Source answer: حسب نوعية هذه الشظايا، ولكن في الغالب لا تؤثر في الجسم لأن الجسم يصنع محفظات حولها ويعزلها، ولكن الأفضل مراجعة مستشفى في الفرصة المناسبة وعمل تصوير بالأشعة لتحديد مكان الشظايا ونوعها، وربما استئصالها إذا أمكن.
- E5 | qa_id=ahd5k_04706 | relation=تحليل بول --DIAGNOSES--> التهاب: عمل تحليل بول
  Source question: اشعر بالم عند الاستيقاظ فى الكليتين من النوم و عندما اتنفس يزيد الالم .. و بعد الاستيقاظ و التبول و شرب الماء يختفى الالم .. كل يوم اشعر بذلك ارجو...
  Source answer: الف سلامة انصحك بعمل تحليل بول و نسبة يوريك اسيد و سونار على البطن و الحوض مبدئيا و من ثم مراجعة طبيب مسالك و الاكثار من شرب الماء
- E6 | qa_id=ahd5k_04706 | relation=الاكثار من شرب الماء --TREATS--> التهاب: الاكثار من شرب الماء
  Source question: اشعر بالم عند الاستيقاظ فى الكليتين من النوم و عندما اتنفس يزيد الالم .. و بعد الاستيقاظ و التبول و شرب الماء يختفى الالم .. كل يوم اشعر بذلك ارجو...
  Source answer: الف سلامة انصحك بعمل تحليل بول و نسبة يوريك اسيد و سونار على البطن و الحوض مبدئيا و من ثم مراجعة طبيب مسالك و الاكثار من شرب الماء

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_096: السلام عليكم .. هل تناول ملعقة يوميا من زيت الحلبة على الريق يزيد من حجم الثدي بجانب التمارين ..؟؟ و ما المدة التى يمكن الاستمرار عليها فى تناول الزيت؟ و...

```text
User Question:
السلام عليكم .. هل تناول ملعقة يوميا من زيت الحلبة على الريق يزيد من حجم الثدي بجانب التمارين ..؟؟ و ما المدة التى يمكن الاستمرار عليها فى تناول الزيت؟ و...

Retrieved Entities:
- زيت الحلبة (Treatment; match=exact; id=ent_treatment_24d83b12af40)

Retrieved Relations:
- [1] النقص الشديد للصفائح --TREATED_BY--> الروتيكسيماب (score=0.770312; reliability=medium)
- [2] الروتيكسيماب --TREATS--> النقص الشديد للصفائح (score=0.322712; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_00203 | relation=النقص الشديد للصفائح --TREATED_BY--> الروتيكسيماب: الروتيكسيماب يفيده في علاج النقص الشديد للصفائح
  Source question: ابني عمره ١٠سنه يعاني من نقص الصفائح itpتم اعطائه ivigمرتين وتم اعطائه كرتزون وحاليا اضيف له علاج الروتيكسيماب اول جرعه ونستمر عليها لمده شهر كل اسبوع مره هل الروتكسيماب يفيده
  Source answer: نعم مفيد لة ويجب الاستمرار فى العلاج و متابعة الطبيب المعالج
- E2 | qa_id=ahd5k_00203 | relation=الروتيكسيماب --TREATS--> النقص الشديد للصفائح: الروتيكسيماب يفيده في علاج النقص الشديد للصفائح
  Source question: ابني عمره ١٠سنه يعاني من نقص الصفائح itpتم اعطائه ivigمرتين وتم اعطائه كرتزون وحاليا اضيف له علاج الروتيكسيماب اول جرعه ونستمر عليها لمده شهر كل اسبوع مره هل الروتكسيماب يفيده
  Source answer: نعم مفيد لة ويجب الاستمرار فى العلاج و متابعة الطبيب المعالج

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_097: كيفية التعامل مع انتفاخ ضرس العقل مسببا الام و احمرار الفك الاسفل

```text
User Question:
كيفية التعامل مع انتفاخ ضرس العقل مسببا الام و احمرار الفك الاسفل

Retrieved Entities:
- ضرس العقل (DiseaseCondition; match=exact; id=ent_diseasecondition_04b436ff2a98)
- انتفاخ (Symptom; match=exact; id=ent_symptom_fd750eeb2865)
- الام (Symptom; match=exact; id=ent_symptom_249d07021a1b)

Retrieved Relations:
- [1] ضرس العقل --HAS_SYMPTOM--> الام (score=0.882909; reliability=medium)
- [2] الام --TREATED_BY--> المراجعة الطبية (score=0.875543; reliability=medium)
- [3] ضرس العقل --HAS_SYMPTOM--> صداع (score=0.875166; reliability=medium)
- [4] ضرس العقل --TREATED_BY--> المراجعة الطبية (score=0.875166; reliability=medium)
- [5] انتفاخ --INVESTIGATED_BY--> اشعة (score=0.854833; reliability=medium)
- [6] صداع --TREATED_BY--> المراجعة الطبية (score=0.767353; reliability=medium)

Evidence Sentences:
- E1 | qa_id=ahd5k_04356 | relation=ضرس العقل --HAS_SYMPTOM--> الام: ضرس العقل
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين
- E2 | qa_id=ahd5k_04356 | relation=الام --TREATED_BY--> المراجعة الطبية: مراجعة طبيبك او اخصائي جراحه وجه و فكين
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين
- E3 | qa_id=ahd5k_04356 | relation=ضرس العقل --HAS_SYMPTOM--> صداع: ضرس العقل
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين
- E4 | qa_id=ahd5k_04356 | relation=ضرس العقل --TREATED_BY--> المراجعة الطبية: مراجعة طبيبك او اخصائي جراحه وجه و فكين
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين
- E5 | qa_id=ahd5k_01537 | relation=انتفاخ --INVESTIGATED_BY--> اشعة: اشعة بالصبغة
  Source question: قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة
  Source answer: نرجو توضيح السؤال وما هي نتيجة الفحص الشعاعي كما وردت في التقرير ليتسنى لنا معرفة النتيجة ومن ثم التشخيص
- E6 | qa_id=ahd5k_04356 | relation=صداع --TREATED_BY--> المراجعة الطبية: مراجعة طبيبك او اخصائي جراحه وجه و فكين
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_098: تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س

```text
User Question:
تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س

Retrieved Entities:
- عمليه قلب مفتوح (Treatment; match=exact; id=ent_treatment_d9340b6ee231)
- مرض السكري (DiseaseCondition; match=exact; id=ent_diseasecondition_380db6d92562)
- ضغط (Symptom; match=exact; id=ent_symptom_d713f64368d3)
- السكري (DiseaseCondition; match=exact; id=ent_diseasecondition_6eb03902c623)
- ضغط الدم (Symptom; match=alias; id=ent_symptom_724e59ded899)
- صمام القلب (DiseaseCondition; match=alias; id=ent_diseasecondition_de01cca177b2)

Retrieved Relations:
- [1] مرض السكري --HAS_SYMPTOM--> ضغط الدم (score=0.69404; reliability=limited)
- [2] ضغط الدم --SYMPTOM_OF--> مرض السكري (score=0.580792; reliability=limited)
- [3] مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (score=0.52211; reliability=limited)
- [4] ضغط الدم --HAS_NORMAL_RANGE--> 140-80 إذا لا توجد أمراض مصاحبة (score=0.463395; reliability=limited)
- [5] ضغط --SYMPTOM_OF--> التهاب الجيوب الأنفية (score=0.414657; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_01294 | relation=مرض السكري --HAS_SYMPTOM--> ضغط الدم: مرض السكري وضغط الدمز
  Source question: تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س
  Source answer: العمليات الجراحية اليوم لا يعيقها أي مرض إذا ما تمت السيطرة عليه بشكل جيد قبل وأثناء وبعد العمل الجراحي، فلا داعي للقلق
- E2 | qa_id=ahd5k_04912 | relation=مرض السكري --HAS_SYMPTOM--> ضغط الدم: مع العلم أن المريض يعاني من مرض السكر
  Source question: هل ضعف عضله القلب وضيق ثلاث شرايين في القلب لهم عمليه جراحيه مع العلم أن المريض يعاني من مرض السكر ام يبقى على العلاج ولو عمليه جراحيهوين تنصحونا نعملها وعاووزيين...
  Source answer: هذا يتطلب معرفة نسبة الضعف الموجود في العضلة القلبية ونسبة التضيق في الثلاثة شرايين المذكورة، كما أنه من الضروري معرفة الحالة الوظيفية لباقي أعضاء الجسم خاصة الكلى والجهاز التنفسي، والكبد وغيره، وفي جميع الأحوال في العادة تُعرض نتائج القثطرة على فريق طبي مُتخصص لتقييم كل هذه الأمور ومن ثم يتم اختيار الطريقة العلاجية التي تتناسب أكثر مع حالة المريض
- E3 | qa_id=ahd5k_01294 | relation=ضغط الدم --SYMPTOM_OF--> مرض السكري: مرض السكري وضغط الدمز
  Source question: تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س
  Source answer: العمليات الجراحية اليوم لا يعيقها أي مرض إذا ما تمت السيطرة عليه بشكل جيد قبل وأثناء وبعد العمل الجراحي، فلا داعي للقلق
- E4 | qa_id=ahd5k_04912 | relation=ضغط الدم --SYMPTOM_OF--> مرض السكري: مع العلم أن المريض يعاني من مرض السكر
  Source question: هل ضعف عضله القلب وضيق ثلاث شرايين في القلب لهم عمليه جراحيه مع العلم أن المريض يعاني من مرض السكر ام يبقى على العلاج ولو عمليه جراحيهوين تنصحونا نعملها وعاووزيين...
  Source answer: هذا يتطلب معرفة نسبة الضعف الموجود في العضلة القلبية ونسبة التضيق في الثلاثة شرايين المذكورة، كما أنه من الضروري معرفة الحالة الوظيفية لباقي أعضاء الجسم خاصة الكلى والجهاز التنفسي، والكبد وغيره، وفي جميع الأحوال في العادة تُعرض نتائج القثطرة على فريق طبي مُتخصص لتقييم كل هذه الأمور ومن ثم يتم اختيار الطريقة العلاجية التي تتناسب أكثر مع حالة المريض
- E5 | qa_id=ahd5k_01551 | relation=مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.
- E6 | qa_id=ahd5k_00085 | relation=ضغط الدم --HAS_NORMAL_RANGE--> 140-80 إذا لا توجد أمراض مصاحبة: حسب عوامل الخطورة الأخرى كالسكري والكلى؛ إذا لا توجد أمراض مصاحبة فالقيمة المذكورة 140-80.
  Source question: ماهو المعدل الطبيعي لضغط الدم لرجل عمرة في 79 سنة وماهو هو عدد نبضات القلب المثالي بالنسبة له .
  Source answer: حسب عوامل الخطورة الاخرى كالسكري و الكلى. اذا لانوجد أمراض مصاحبة ١٤٠-٨٠ و ضربات القلب تقريبا من ٦٥-٨٥ لكن ممكن ان نقبل ضربات قلب اقل او اكثر
- E7 | qa_id=ahd5k_02662 | relation=ضغط --SYMPTOM_OF--> التهاب الجيوب الأنفية: ضغط
  Source question: لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام لهذا السبب
  Source answer: إن الألم في الرأس مع الشعور بالضغط على جانبي الرأس مع الإرهاق العام قد يعود لأحد الأسباب التالية: صداع التوتر. الشد العضلي. الضغط العصبي. القلق والتوتر أو الاكتئاب. التهاب الجيوب الأنفية. الشقيقة (الصداع النصفي). وجود مشاكل في الأذن التهاب السحايا. تمدد الأوعية الدموية في الدماغ. ينصح في الوقت الحالي زيارة الطبيب المختص لعمل الفحوصات والتحاليل اللازمة في حال عدم نجاح النصائح التالية: استخدام الأدوية المسكنة للألم حسب تعليمات الطبيب المختص مثل الايبوبروفين وغيرها. اتباع طرق التنفس العميق من أجل الاسترخاء وخفض مستويات هرمونات التوتر. ممارسة تمارين الاسترخاء مثل اليوغا والتأمل. تجنب القلق أو التوتر. للمزيد: اسباب الصداع ومحفزاته التدليك لعلاج الصداع هل تعاني من صداع من دون معرفة سببه؟ المرجع...

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_099: انا ابتلعت دبوس امس ولا اشعر ببلعه واعاني بوجع صدري كيف اعمل

```text
User Question:
انا ابتلعت دبوس امس ولا اشعر ببلعه واعاني بوجع صدري كيف اعمل

Retrieved Entities:
- دبوس (DiseaseCondition; match=exact; id=ent_diseasecondition_16a389cfd1bd)
- وجع (Symptom; match=exact; id=ent_symptom_42ad4acdebc5)

Retrieved Relations:
- [1] فقر الدم --HAS_SYMPTOM--> تنميل (score=0.74235; reliability=limited)
- [2] تنميل --SYMPTOM_OF--> فقر الدم (score=0.65675; reliability=limited)
- [3] دبوس --DIAGNOSED_BY--> أشعة (score=0.558659; reliability=limited)
- [4] وجع --INVESTIGATED_BY--> اشعة (score=0.484356; reliability=limited)
- [5] حساسية --DIAGNOSED_BY--> RAST Test (score=0.389321; reliability=limited)
- [6] أشعة --DIAGNOSES--> دبوس (score=0.388579; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_00838 | relation=فقر الدم --HAS_SYMPTOM--> تنميل: نقص فيتامين (ب12) يسبب انيميا وتنميل
  Source question: اشعر بتنميل من بداية النصف الاسفل من الجسم حتى اسفل القدم عند تحريك الرقبة الى اسفل و انا عندي انيميا هل لها علاقة
  Source answer: نعم ... نقص فيتامين (ب12) يسبب انيميا وتنميل
- E2 | qa_id=ahd5k_00838 | relation=تنميل --SYMPTOM_OF--> فقر الدم: نقص فيتامين (ب12) يسبب انيميا وتنميل
  Source question: اشعر بتنميل من بداية النصف الاسفل من الجسم حتى اسفل القدم عند تحريك الرقبة الى اسفل و انا عندي انيميا هل لها علاقة
  Source answer: نعم ... نقص فيتامين (ب12) يسبب انيميا وتنميل
- E3 | qa_id=ahd5k_01295 | relation=دبوس --DIAGNOSED_BY--> أشعة: أشعة لمعرفة مكان الدبوس والتأكد من وجوده
  Source question: انا ابتلعت دبوس امس ولا اشعر ببلعه واعاني بوجع صدري كيف اعمل
  Source answer: الافضل زيارة الطبيب لاجراء الفحوصات اللازمة و أشعة لمعرفة ممان الدبوس والتأكد من وجوده و اي اذية اخرى فيما اذا كان موجودا وتلقي العلاج المناسب
- E4 | qa_id=ahd5k_01537 | relation=وجع --INVESTIGATED_BY--> اشعة: اشعة بالصبغة
  Source question: قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة
  Source answer: نرجو توضيح السؤال وما هي نتيجة الفحص الشعاعي كما وردت في التقرير ليتسنى لنا معرفة النتيجة ومن ثم التشخيص
- E5 | qa_id=ahd5k_01245 | relation=حساسية --DIAGNOSED_BY--> RAST Test: معرفة سبب الحساسيه يتم ذلك عن طريق RAST Test
  Source question: انا اشعر بالصداع والنعاس وحساسية في وجهي والحكة بكل انحاء جسمي كيف استطيع ان اوقف هذا الدواء
  Source answer: معرفة سبب الحساسيه وتجنبه لتتجنب استخدام الادويه يتم ذلك عن طريق RAST Test
- E6 | qa_id=ahd5k_01295 | relation=أشعة --DIAGNOSES--> دبوس: أشعة لمعرفة مكان الدبوس والتأكد من وجوده
  Source question: انا ابتلعت دبوس امس ولا اشعر ببلعه واعاني بوجع صدري كيف اعمل
  Source answer: الافضل زيارة الطبيب لاجراء الفحوصات اللازمة و أشعة لمعرفة ممان الدبوس والتأكد من وجوده و اي اذية اخرى فيما اذا كان موجودا وتلقي العلاج المناسب

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_100: عندى بقع بنية على جانبى الوجة وانا اعانى من انيميا 10 وكان عندى حصوات بالمرارة وعملت العملية ولا زالت البقع موجودة ما العلاج الاكيد وشكرا

```text
User Question:
عندى بقع بنية على جانبى الوجة وانا اعانى من انيميا 10 وكان عندى حصوات بالمرارة وعملت العملية ولا زالت البقع موجودة ما العلاج الاكيد وشكرا

Retrieved Entities:
- العلاج (Treatment; match=exact; id=ent_treatment_90baddc0bf15)

Retrieved Relations:
- [1] فقر الدم --HAS_SYMPTOM--> الم المعدجة (score=0.84997; reliability=strong)
- [2] فقر الدم --HAS_SYMPTOM--> تنميل (score=0.796769; reliability=medium)
- [3] فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (score=0.78997; reliability=medium)
- [4] حساسية الصدر --HAS_SYMPTOM--> سعال (score=0.767427; reliability=medium)
- [5] التهاب --HAS_SYMPTOM--> الدم (score=0.763357; reliability=medium)
- [6] سعال --SYMPTOM_OF--> حساسية الصدر (score=0.681827; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_02292 | relation=فقر الدم --HAS_SYMPTOM--> الم المعدجة: نقص في الدم مع الالم في المعده
  Source question: والدتي تعاني من نقص في الدم مع الالم في المعده
  Source answer: الم المعدجة يجب معرفة سببه وذل بعمل دراسة للمعدة ولنبدأ بفحص الجرثومة الحلزونية ، وربما سنحتاج لاحقا لمنظار للمعدة اما نقص الدم فهذ يجب توضيحة بشكل جيد ودراسته لمعرفة السبب وعلاجه
- E2 | qa_id=ahd5k_02546 | relation=فقر الدم --HAS_SYMPTOM--> الم المعدجة: أحيانا الم في المعدة كسل وخمول اضطرابات في النوم
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري
- E3 | qa_id=ahd5k_00838 | relation=فقر الدم --HAS_SYMPTOM--> تنميل: نقص فيتامين (ب12) يسبب انيميا وتنميل
  Source question: اشعر بتنميل من بداية النصف الاسفل من الجسم حتى اسفل القدم عند تحريك الرقبة الى اسفل و انا عندي انيميا هل لها علاقة
  Source answer: نعم ... نقص فيتامين (ب12) يسبب انيميا وتنميل
- E4 | qa_id=ahd5k_02546 | relation=فقر الدم --HAS_SYMPTOM--> فقدان الشهيه: فقر الدم سبب فقدان الشهيه
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري
- E5 | qa_id=ahd5k_04490 | relation=حساسية الصدر --HAS_SYMPTOM--> سعال: حساسية الصدر and سعال co-occur with explicit symptom-pathology link
  Source question: انا عندي قضيبي صغير هل هذه بسبب متعلق بهرمون الذكوره علما انا عمري 17 ويوجد شعر على الارجل والابط ولايوجد على الشارب وبدي اعرف اذا كان السبب متعلق بلهرمون كيفيه...
  Source answer: يجب اجراء الفحص السريري و الفحوصات المخبرية لتحديد السبب ثم العلاج
- E6 | qa_id=ahd5k_00666 | relation=التهاب --HAS_SYMPTOM--> الدم: التهاب في المثانة أو الإحليل يسبب خروج الدم
  Source question: انا عندي مشكله عندما انتهي من التبول يخرج في اخر البول دم؟
  Source answer: خروج الدم يعني وجود جرح في المثانة أو الإحليل. ويمكن آن يكون هذا ناتجاً عن وجود جرح ينزل منه الدم، حصوة في المثانة أو الإحليل؟ يمكمنك تصوير الجهاز البولي بصورة ملونر أي في بي لتحديد السبب والمكان، وبعدها يتحدد العلاج؟سلامتك
- E7 | qa_id=ahd5k_04490 | relation=سعال --SYMPTOM_OF--> حساسية الصدر: حساسية الصدر and سعال co-occur with explicit symptom-pathology link
  Source question: انا عندي قضيبي صغير هل هذه بسبب متعلق بهرمون الذكوره علما انا عمري 17 ويوجد شعر على الارجل والابط ولايوجد على الشارب وبدي اعرف اذا كان السبب متعلق بلهرمون كيفيه...
  Source answer: يجب اجراء الفحص السريري و الفحوصات المخبرية لتحديد السبب ثم العلاج

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_101: ماهو البردقوش وهل يوجد باليمن وهل يزيد من عدد الحيوانات المنويه؟

```text
User Question:
ماهو البردقوش وهل يوجد باليمن وهل يزيد من عدد الحيوانات المنويه؟

Retrieved Entities:
- الحيوانات المنوية (Test; match=exact; id=ent_test_51926b4c8cd0)
- البردقوش (Treatment; match=exact; id=ent_treatment_fc32e4036e25)

Retrieved Relations:
- [1] الدورة الشهرية --TREATED_BY--> البردقوش (score=0.792457; reliability=medium)
- [2] التدخين --INVESTIGATED_BY--> الحيوانات المنوية (score=0.79103; reliability=medium)
- [3] الدورة الشهرية --TREATED_BY--> اكليل الجبل (score=0.752882; reliability=medium)
- [4] الدورة الشهرية --TREATED_BY--> الميرمية (score=0.752882; reliability=medium)
- [5] الدورة الشهرية --TREATED_BY--> البقدونس (score=0.752882; reliability=medium)
- [6] الدورة الشهرية --TREATED_BY--> حشيشة الملاك (score=0.752882; reliability=medium)

Evidence Sentences:
- E1 | qa_id=ahd5k_04015 | relation=الدورة الشهرية --TREATED_BY--> البردقوش: البردقوش
  Source question: ماهى الاعشاب التي تساعد على نزول الطمث حيت انوما تجيني الدورة الا بالدواء فقط.شكرا
  Source answer: من الاعشاب التي قد تساعد على حل المشكلة وتنظيم الدورة الشهرية وهي طبعا لا تغني عن الدواء وعلاج السبب الاساسي لعدم انتظام الدورة ، نذكر: اكليل الجبل، الميرمية، البقدونس، حشيشة الملاك، البردقوش، القرفة، الزنجبيل، والكرفس.
- E2 | qa_id=ahd5k_01629 | relation=التدخين --INVESTIGATED_BY--> الحيوانات المنوية: سلامة الحيوانات المنوية للزوج
  Source question: على ماذا تعتمد نسبة نجاح أطفال الانابيب؟ ,ما هي نسبة نجاح طفل الانابيب ؟
  Source answer: تعتمد نسبة نجاح طفل الأنابيب على عدة عوامل، ومنها الآتي: عمر المرأة. وجود حمل سابق. الحالة الصحية للزوجين. سبب اللجوء لعملية الأنابيب. نمط الحياة والعادات المتبعة، مثل التدخين. سلامة الحيوانات المنوية للزوج. التقنية المتبعة في المركز العلاجي. خبرة الطبيب المعالج. يشار أن عمر المرأة يلعب دورًا مهمًا في تقدير نسبة نجاح الحمل باتباع طريقة أطفال الأنابيب، حيث تقدر نسبة نجاح الحمل 35% تقريبًا للنساء ذوات الأعمار الأقل من 35 عاماً بينما تبلغ نسبة النجاح 4% فقط لمن تزيد أعمارهن عن 42 عاماً. يجدر الذكر أيضًا أن تقنيات الحمل المساعدة في تطور دائم والتقنيات الحديثة تساهم في رفع فرص نجاح الحمل، كما يمكن اللجوء إلى أحد تقنيات الحمل المساعدة الأخرى ذات نسبة النجاح الأكبر. للمزيد: دليل نجاح عملية طفل ا...
- E3 | qa_id=ahd5k_04015 | relation=الدورة الشهرية --TREATED_BY--> اكليل الجبل: اكليل الجبل
  Source question: ماهى الاعشاب التي تساعد على نزول الطمث حيت انوما تجيني الدورة الا بالدواء فقط.شكرا
  Source answer: من الاعشاب التي قد تساعد على حل المشكلة وتنظيم الدورة الشهرية وهي طبعا لا تغني عن الدواء وعلاج السبب الاساسي لعدم انتظام الدورة ، نذكر: اكليل الجبل، الميرمية، البقدونس، حشيشة الملاك، البردقوش، القرفة، الزنجبيل، والكرفس.
- E4 | qa_id=ahd5k_04015 | relation=الدورة الشهرية --TREATED_BY--> الميرمية: الميرمية
  Source question: ماهى الاعشاب التي تساعد على نزول الطمث حيت انوما تجيني الدورة الا بالدواء فقط.شكرا
  Source answer: من الاعشاب التي قد تساعد على حل المشكلة وتنظيم الدورة الشهرية وهي طبعا لا تغني عن الدواء وعلاج السبب الاساسي لعدم انتظام الدورة ، نذكر: اكليل الجبل، الميرمية، البقدونس، حشيشة الملاك، البردقوش، القرفة، الزنجبيل، والكرفس.
- E5 | qa_id=ahd5k_04015 | relation=الدورة الشهرية --TREATED_BY--> البقدونس: البقدونس
  Source question: ماهى الاعشاب التي تساعد على نزول الطمث حيت انوما تجيني الدورة الا بالدواء فقط.شكرا
  Source answer: من الاعشاب التي قد تساعد على حل المشكلة وتنظيم الدورة الشهرية وهي طبعا لا تغني عن الدواء وعلاج السبب الاساسي لعدم انتظام الدورة ، نذكر: اكليل الجبل، الميرمية، البقدونس، حشيشة الملاك، البردقوش، القرفة، الزنجبيل، والكرفس.
- E6 | qa_id=ahd5k_04015 | relation=الدورة الشهرية --TREATED_BY--> حشيشة الملاك: حشيشة الملاك
  Source question: ماهى الاعشاب التي تساعد على نزول الطمث حيت انوما تجيني الدورة الا بالدواء فقط.شكرا
  Source answer: من الاعشاب التي قد تساعد على حل المشكلة وتنظيم الدورة الشهرية وهي طبعا لا تغني عن الدواء وعلاج السبب الاساسي لعدم انتظام الدورة ، نذكر: اكليل الجبل، الميرمية، البقدونس، حشيشة الملاك، البردقوش، القرفة، الزنجبيل، والكرفس.

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_102: اعاني من حموضة وصعوبة في التنفس وصعوبة بلع والم في الجانب الايسر من الصدر مع تعب في الكتف اليسرى بعد ابذال مجهود فهل هذا خطر على القلب ام حموضة عادية

```text
User Question:
اعاني من حموضة وصعوبة في التنفس وصعوبة بلع والم في الجانب الايسر من الصدر مع تعب في الكتف اليسرى بعد ابذال مجهود فهل هذا خطر على القلب ام حموضة عادية

Retrieved Entities:
- الكتف (Symptom; match=exact; id=ent_symptom_db012388d676)
- حموضة (Symptom; match=exact; id=ent_symptom_1a7b2eae066b)
- تعب (Symptom; match=exact; id=ent_symptom_28acc791e82d)

Retrieved Relations:
- [1] التهاب --HAS_SYMPTOM--> تعب (score=0.78386; reliability=medium)
- [2] تعب --SYMPTOM_OF--> التهاب (score=0.78274; reliability=medium)
- [3] التهاب --HAS_SYMPTOM--> ضيق تنفس (score=0.76938; reliability=medium)
- [4] ضيق تنفس --SYMPTOM_OF--> التهاب (score=0.68378; reliability=limited)
- [5] الكتف --TREATED_BY--> البروفين (score=0.501166; reliability=limited)
- [6] البروفين --TREATS--> الكتف (score=0.331086; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_03872 | relation=التهاب --HAS_SYMPTOM--> تعب: اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام
  Source question: السلام وعليكم ورحمة الله وبركاتو اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام .ارجو الاجابه وشكرا...
  Source answer: أعراض التهاب وحساسيه الجيوب الانفيه لابد من استخدام الادويه المناسبه بعد الفحص عند طبيب ENT
- E2 | qa_id=ahd5k_03872 | relation=تعب --SYMPTOM_OF--> التهاب: اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام
  Source question: السلام وعليكم ورحمة الله وبركاتو اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام .ارجو الاجابه وشكرا...
  Source answer: أعراض التهاب وحساسيه الجيوب الانفيه لابد من استخدام الادويه المناسبه بعد الفحص عند طبيب ENT
- E3 | qa_id=ahd5k_03872 | relation=التهاب --HAS_SYMPTOM--> ضيق تنفس: اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام
  Source question: السلام وعليكم ورحمة الله وبركاتو اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام .ارجو الاجابه وشكرا...
  Source answer: أعراض التهاب وحساسيه الجيوب الانفيه لابد من استخدام الادويه المناسبه بعد الفحص عند طبيب ENT
- E4 | qa_id=ahd5k_03872 | relation=ضيق تنفس --SYMPTOM_OF--> التهاب: اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام
  Source question: السلام وعليكم ورحمة الله وبركاتو اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام .ارجو الاجابه وشكرا...
  Source answer: أعراض التهاب وحساسيه الجيوب الانفيه لابد من استخدام الادويه المناسبه بعد الفحص عند طبيب ENT
- E5 | qa_id=ahd5k_00486 | relation=الكتف --TREATED_BY--> البروفين: تناول بعض الأدوية المسكنة للألم اللاستيروئيدية، مثل البروفين
  Source question: السلام عليكم ورحمه الله وبركاته اناعندي الوالده كبيره بالسن تعاني من الم بالكتف وبعدالاشعات اخبروهابانه شخونه في الكتف واعطوهامسكنات وادويه ولاكن لم تفيدمعهاالابتخفبف الالم واخبروها كم دكتوربانه لازم تاخذابره بالكتف...
  Source answer: لم تذكر عمر الوالدة بالضبط، ولكن بشكل عام ، يحدث عند الكبار تاكل في الغضاريف ويسبب هذا الألم نتيجة احتكاك العظم،،هذا لا يمكن استعادته. لذلك يكون العلاج لتخفيف الألم ، والتدليك بالأدوية يفيد في تخفيف الألم ولكنه يجب أن يستمر، كذلك يجب تناول بعض المأكولات التي خفف الألم مثل الزنجبيل وغيره، أو تناول بعض الأدوية المسكنة للألم اللاستيروئيدية ،ثل البروفين وغيره، ولكن الإبر تعطي مفعولاً لمدة أسبوعين أو أكثر، ولهذا يحبها الناس.
- E6 | qa_id=ahd5k_00486 | relation=البروفين --TREATS--> الكتف: تناول بعض الأدوية المسكنة للألم اللاستيروئيدية، مثل البروفين
  Source question: السلام عليكم ورحمه الله وبركاته اناعندي الوالده كبيره بالسن تعاني من الم بالكتف وبعدالاشعات اخبروهابانه شخونه في الكتف واعطوهامسكنات وادويه ولاكن لم تفيدمعهاالابتخفبف الالم واخبروها كم دكتوربانه لازم تاخذابره بالكتف...
  Source answer: لم تذكر عمر الوالدة بالضبط، ولكن بشكل عام ، يحدث عند الكبار تاكل في الغضاريف ويسبب هذا الألم نتيجة احتكاك العظم،،هذا لا يمكن استعادته. لذلك يكون العلاج لتخفيف الألم ، والتدليك بالأدوية يفيد في تخفيف الألم ولكنه يجب أن يستمر، كذلك يجب تناول بعض المأكولات التي خفف الألم مثل الزنجبيل وغيره، أو تناول بعض الأدوية المسكنة للألم اللاستيروئيدية ،ثل البروفين وغيره، ولكن الإبر تعطي مفعولاً لمدة أسبوعين أو أكثر، ولهذا يحبها الناس.

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_103: ما هو ابسط علاج لمرض السكر بدون كيماويات؟

```text
User Question:
ما هو ابسط علاج لمرض السكر بدون كيماويات؟

Retrieved Entities:
- سكر (DiseaseCondition; match=exact; id=ent_diseasecondition_4393a2bf88a6)

Retrieved Relations:
- [1] مرض السكري --HAS_SYMPTOM--> ضغط الدم (score=0.935862; reliability=strong)
- [2] ضغط الدم --SYMPTOM_OF--> مرض السكري (score=0.775002; reliability=medium)
- [3] مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (score=0.472189; reliability=limited)
- [4] التهاب --DIAGNOSED_BY--> تحاليل مخبرية (score=0.413367; reliability=limited)
- [5] تحاليل مخبرية --DIAGNOSES--> مرض السكري (score=0.371229; reliability=limited)
- [6] تحاليل مخبرية --DIAGNOSES--> التهاب (score=0.327767; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_02607 | relation=مرض السكري --HAS_SYMPTOM--> ضغط الدم: مرض السكري وضغط الدم
  Source question: السلام عليكم والدي عمره 58 و لديه شريان مغلق من الجهة اليمنى بنسبة تسعين بالمئة منذ اربع سنوات و لديه ضغط و سكري و لم يتعالج الى الان فهل حالته...
  Source answer: لم تحدد أي شريان، فلكل عضو أو منطقة في الجسم خصائصها البنيوية والوظيفية، وفي جميع الأحوال الحالة السريرية هي الفيصل وليس الفحص الذي هو ليس أكثر من مكمل للفحص الطبي السريري، لأن الكثير من الشرايين التي تغلق ينشأ بدلا عنها أخرى بديلة لا سيما إذا ما كان الشخص صحيح البنية ورياضي، وهذه الأوعية البديلة تكفل التروية للمنطقة التي يمكن أن تتضرر من الشريان المنغلق
- E2 | qa_id=ahd5k_01294 | relation=مرض السكري --HAS_SYMPTOM--> ضغط الدم: مرض السكري وضغط الدمز
  Source question: تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س
  Source answer: العمليات الجراحية اليوم لا يعيقها أي مرض إذا ما تمت السيطرة عليه بشكل جيد قبل وأثناء وبعد العمل الجراحي، فلا داعي للقلق
- E3 | qa_id=ahd5k_02607 | relation=ضغط الدم --SYMPTOM_OF--> مرض السكري: مرض السكري وضغط الدم
  Source question: السلام عليكم والدي عمره 58 و لديه شريان مغلق من الجهة اليمنى بنسبة تسعين بالمئة منذ اربع سنوات و لديه ضغط و سكري و لم يتعالج الى الان فهل حالته...
  Source answer: لم تحدد أي شريان، فلكل عضو أو منطقة في الجسم خصائصها البنيوية والوظيفية، وفي جميع الأحوال الحالة السريرية هي الفيصل وليس الفحص الذي هو ليس أكثر من مكمل للفحص الطبي السريري، لأن الكثير من الشرايين التي تغلق ينشأ بدلا عنها أخرى بديلة لا سيما إذا ما كان الشخص صحيح البنية ورياضي، وهذه الأوعية البديلة تكفل التروية للمنطقة التي يمكن أن تتضرر من الشريان المنغلق
- E4 | qa_id=ahd5k_04912 | relation=ضغط الدم --SYMPTOM_OF--> مرض السكري: مع العلم أن المريض يعاني من مرض السكر
  Source question: هل ضعف عضله القلب وضيق ثلاث شرايين في القلب لهم عمليه جراحيه مع العلم أن المريض يعاني من مرض السكر ام يبقى على العلاج ولو عمليه جراحيهوين تنصحونا نعملها وعاووزيين...
  Source answer: هذا يتطلب معرفة نسبة الضعف الموجود في العضلة القلبية ونسبة التضيق في الثلاثة شرايين المذكورة، كما أنه من الضروري معرفة الحالة الوظيفية لباقي أعضاء الجسم خاصة الكلى والجهاز التنفسي، والكبد وغيره، وفي جميع الأحوال في العادة تُعرض نتائج القثطرة على فريق طبي مُتخصص لتقييم كل هذه الأمور ومن ثم يتم اختيار الطريقة العلاجية التي تتناسب أكثر مع حالة المريض
- E5 | qa_id=ahd5k_01551 | relation=مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.
- E6 | qa_id=ahd5k_01551 | relation=التهاب --DIAGNOSED_BY--> تحاليل مخبرية: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.
- E7 | qa_id=ahd5k_01551 | relation=تحاليل مخبرية --DIAGNOSES--> مرض السكري: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.
- E8 | qa_id=ahd5k_01551 | relation=تحاليل مخبرية --DIAGNOSES--> التهاب: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_104: انا عملت جراحة فى القلب وتم تغير الصمام المترالى بصمام ميكانيكى صناعى وباخد دواء واريفان ( لسيولة الدم ) 8 ملجرام ومصاب بالانفلوانزا ماالعلاج المناسب

```text
User Question:
انا عملت جراحة فى القلب وتم تغير الصمام المترالى بصمام ميكانيكى صناعى وباخد دواء واريفان ( لسيولة الدم ) 8 ملجرام ومصاب بالانفلوانزا ماالعلاج المناسب

Retrieved Entities:
- الانفلوانزا (DiseaseCondition; match=exact; id=ent_diseasecondition_8ae017ffaf32)
- صمام القلب (DiseaseCondition; match=alias; id=ent_diseasecondition_de01cca177b2)

Retrieved Relations:
- [1] ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب (score=0.456144; reliability=limited)
- [2] ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس (score=0.392064; reliability=limited)
- [3] ارتفاع ضغط الدم --HAS_SYMPTOM--> دوخة (score=0.385728; reliability=limited)
- [4] مرض السكري --HAS_SYMPTOM--> ضغط الدم (score=0.380759; reliability=limited)
- [5] خفقان القلب --SYMPTOM_OF--> ارتفاع ضغط الدم (score=0.370544; reliability=limited)
- [6] ضيق تنفس --SYMPTOM_OF--> ارتفاع ضغط الدم (score=0.306464; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_04701 | relation=ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب: تسارع في ضربات القلب
  Source question: انا اعاني من دوخة خاصة اثناء المشي وفي بعض الاحيان ضيق تنفس كما انني اعاني من مشكل اثناء بداية النوم لانها تنتابني الدوخة وتسارع في ضربات القلب ارجوكم افيدوني وشكرا
  Source answer: كثير من الفتيات يعانن من هذه الأعراض وذلك نتيجة انخفاض الضغط وبالتالي ارتفاع نبضات القلب والشعور بالدوخة والإجهاد وينصح بتناول وجبة الإفطار والإكثار من السوائل والأملاح .. ألف سلامة
- E2 | qa_id=ahd5k_03624 | relation=ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب: خفقان القلب الشديد
  Source question: امي مصابة بروماتيزم الدم , مع ارتفاع في ضغط الدم تتناول أدوية الروماتيزم منذ عام تقريبا المشكلة أنها منذ فترة تعاني من خفقان القلب الشديد خاصة في الليل فهل له...
  Source answer: نعم ممكن لكن لا داعي للقق، فقط تتطلب معاودة طبيبها المشرف على حالتها للتحقق من عدم وجود سبب دوائي
- E3 | qa_id=ahd5k_04701 | relation=ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس: ضيق تنفس
  Source question: انا اعاني من دوخة خاصة اثناء المشي وفي بعض الاحيان ضيق تنفس كما انني اعاني من مشكل اثناء بداية النوم لانها تنتابني الدوخة وتسارع في ضربات القلب ارجوكم افيدوني وشكرا
  Source answer: كثير من الفتيات يعانن من هذه الأعراض وذلك نتيجة انخفاض الضغط وبالتالي ارتفاع نبضات القلب والشعور بالدوخة والإجهاد وينصح بتناول وجبة الإفطار والإكثار من السوائل والأملاح .. ألف سلامة
- E4 | qa_id=ahd5k_04701 | relation=ارتفاع ضغط الدم --HAS_SYMPTOM--> دوخة: دوخة
  Source question: انا اعاني من دوخة خاصة اثناء المشي وفي بعض الاحيان ضيق تنفس كما انني اعاني من مشكل اثناء بداية النوم لانها تنتابني الدوخة وتسارع في ضربات القلب ارجوكم افيدوني وشكرا
  Source answer: كثير من الفتيات يعانن من هذه الأعراض وذلك نتيجة انخفاض الضغط وبالتالي ارتفاع نبضات القلب والشعور بالدوخة والإجهاد وينصح بتناول وجبة الإفطار والإكثار من السوائل والأملاح .. ألف سلامة
- E5 | qa_id=ahd5k_01294 | relation=مرض السكري --HAS_SYMPTOM--> ضغط الدم: مرض السكري وضغط الدمز
  Source question: تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س
  Source answer: العمليات الجراحية اليوم لا يعيقها أي مرض إذا ما تمت السيطرة عليه بشكل جيد قبل وأثناء وبعد العمل الجراحي، فلا داعي للقلق
- E6 | qa_id=ahd5k_04701 | relation=خفقان القلب --SYMPTOM_OF--> ارتفاع ضغط الدم: تسارع في ضربات القلب
  Source question: انا اعاني من دوخة خاصة اثناء المشي وفي بعض الاحيان ضيق تنفس كما انني اعاني من مشكل اثناء بداية النوم لانها تنتابني الدوخة وتسارع في ضربات القلب ارجوكم افيدوني وشكرا
  Source answer: كثير من الفتيات يعانن من هذه الأعراض وذلك نتيجة انخفاض الضغط وبالتالي ارتفاع نبضات القلب والشعور بالدوخة والإجهاد وينصح بتناول وجبة الإفطار والإكثار من السوائل والأملاح .. ألف سلامة
- E7 | qa_id=ahd5k_03624 | relation=خفقان القلب --SYMPTOM_OF--> ارتفاع ضغط الدم: خفقان القلب الشديد
  Source question: امي مصابة بروماتيزم الدم , مع ارتفاع في ضغط الدم تتناول أدوية الروماتيزم منذ عام تقريبا المشكلة أنها منذ فترة تعاني من خفقان القلب الشديد خاصة في الليل فهل له...
  Source answer: نعم ممكن لكن لا داعي للقق، فقط تتطلب معاودة طبيبها المشرف على حالتها للتحقق من عدم وجود سبب دوائي
- E8 | qa_id=ahd5k_04701 | relation=ضيق تنفس --SYMPTOM_OF--> ارتفاع ضغط الدم: ضيق تنفس
  Source question: انا اعاني من دوخة خاصة اثناء المشي وفي بعض الاحيان ضيق تنفس كما انني اعاني من مشكل اثناء بداية النوم لانها تنتابني الدوخة وتسارع في ضربات القلب ارجوكم افيدوني وشكرا
  Source answer: كثير من الفتيات يعانن من هذه الأعراض وذلك نتيجة انخفاض الضغط وبالتالي ارتفاع نبضات القلب والشعور بالدوخة والإجهاد وينصح بتناول وجبة الإفطار والإكثار من السوائل والأملاح .. ألف سلامة

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_105: هل حبوب كريستور(rousovastatin) تؤثر على عضلة القلب ؟

```text
User Question:
هل حبوب كريستور(rousovastatin) تؤثر على عضلة القلب ؟

Retrieved Entities:
- كريستور (Treatment; match=exact; id=ent_treatment_5bbcb8e80aef)

Retrieved Relations:
- [1] فقر الدم --HAS_SYMPTOM--> الم المعدجة (score=0.774283; reliability=medium)
- [2] فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (score=0.774283; reliability=medium)
- [3] ضغط الدم --HAS_NORMAL_RANGE--> 140-80 إذا لا توجد أمراض مصاحبة (score=0.411345; reliability=limited)
- [4] نبض القلب --HAS_NORMAL_RANGE--> 65-85 تقريبا وقد يقبل أقل أو أكثر (score=0.411345; reliability=limited)
- [5] الم المعدجة --SYMPTOM_OF--> فقر الدم (score=0.326683; reliability=limited)
- [6] فقدان الشهيه --SYMPTOM_OF--> فقر الدم (score=0.326683; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_02546 | relation=فقر الدم --HAS_SYMPTOM--> الم المعدجة: أحيانا الم في المعدة كسل وخمول اضطرابات في النوم
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري
- E2 | qa_id=ahd5k_02546 | relation=فقر الدم --HAS_SYMPTOM--> فقدان الشهيه: فقر الدم سبب فقدان الشهيه
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري
- E3 | qa_id=ahd5k_00085 | relation=ضغط الدم --HAS_NORMAL_RANGE--> 140-80 إذا لا توجد أمراض مصاحبة: حسب عوامل الخطورة الأخرى كالسكري والكلى؛ إذا لا توجد أمراض مصاحبة فالقيمة المذكورة 140-80.
  Source question: ماهو المعدل الطبيعي لضغط الدم لرجل عمرة في 79 سنة وماهو هو عدد نبضات القلب المثالي بالنسبة له .
  Source answer: حسب عوامل الخطورة الاخرى كالسكري و الكلى. اذا لانوجد أمراض مصاحبة ١٤٠-٨٠ و ضربات القلب تقريبا من ٦٥-٨٥ لكن ممكن ان نقبل ضربات قلب اقل او اكثر
- E4 | qa_id=ahd5k_00085 | relation=نبض القلب --HAS_NORMAL_RANGE--> 65-85 تقريبا وقد يقبل أقل أو أكثر: ضربات القلب تقريبا من 65-85، ويمكن قبول أقل أو أكثر حسب الحالة.
  Source question: ماهو المعدل الطبيعي لضغط الدم لرجل عمرة في 79 سنة وماهو هو عدد نبضات القلب المثالي بالنسبة له .
  Source answer: حسب عوامل الخطورة الاخرى كالسكري و الكلى. اذا لانوجد أمراض مصاحبة ١٤٠-٨٠ و ضربات القلب تقريبا من ٦٥-٨٥ لكن ممكن ان نقبل ضربات قلب اقل او اكثر
- E5 | qa_id=ahd5k_02546 | relation=الم المعدجة --SYMPTOM_OF--> فقر الدم: أحيانا الم في المعدة كسل وخمول اضطرابات في النوم
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري
- E6 | qa_id=ahd5k_02546 | relation=فقدان الشهيه --SYMPTOM_OF--> فقر الدم: فقر الدم سبب فقدان الشهيه
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_106: هل يوجد أعشاب طبية تساعد على الشفاء من حالة الاكتئاب و الشعور بالخوف ، علما بأنه يوجد لدي فقر دم (انيميا الفول ) و يتجدث حالات الاكتئاب هذه عند تناول...

```text
User Question:
هل يوجد أعشاب طبية تساعد على الشفاء من حالة الاكتئاب و الشعور بالخوف ، علما بأنه يوجد لدي فقر دم (انيميا الفول ) و يتجدث حالات الاكتئاب هذه عند تناول...

Retrieved Entities:
- فقر دم (DiseaseCondition; match=exact; id=ent_diseasecondition_99d821e71fc1)
- الاكتئاب (DiseaseCondition; match=exact; id=ent_diseasecondition_c530adcb98c5)
- اكتئاب (DiseaseCondition; match=exact; id=ent_diseasecondition_32c84edce6a2)
- فول (Treatment; match=exact; id=ent_treatment_ace11c18f4c4)

Retrieved Relations:
- [1] فقر الدم --DIAGNOSED_BY--> تحاليل مخبرية (score=0.852319; reliability=strong)
- [2] فقر الدم --HAS_SYMPTOM--> الم المعدجة (score=0.837204; reliability=strong)
- [3] فقر الدم --DIAGNOSED_BY--> فحص تحاليل مخبرية (score=0.786349; reliability=medium)
- [4] فقر الدم --HAS_SYMPTOM--> تنميل (score=0.786349; reliability=medium)
- [5] فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (score=0.777204; reliability=medium)
- [6] فقر الدم --MANAGED_BY--> أغذية غنية بالحديد والفولات وفيتامين ب12 (score=0.492923; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_00757 | relation=فقر الدم --DIAGNOSED_BY--> تحاليل مخبرية: تحليل فقر الدم
  Source question: أنا حللت تحليل فقر الدم والنتائج كالآتي hp=11.6 وp.c.v=38% فهل لدي فقر دم؟ وما هي نسبة الدم الطبيعية؟ وشكرا
  Source answer: الهيموغلوبين في النساء بين 12 و15 وال PCV عند النساء هو 38%
- E2 | qa_id=ahd5k_00696 | relation=فقر الدم --DIAGNOSED_BY--> تحاليل مخبرية: الفوال أو التفول هو الاضطراب الخلقي الجيني الناجم عن نقص الأنزيم المسؤول عن الحفاظ على تركيز ببتيد الغلوتاثيون
  Source question: السلام عليكم مولود جديد بعد التحاليل ظهر مع الانيميا الفوليه ما اسباب الانيميا الفوليه وكيفية تفاديها؟ وهل لها علاج وهل تذهب او تزول كل ما كبر الطفل؟ وهل لها مخاطر...
  Source answer: الفوال أو التفول هو الاضطراب الخلقي الجيني الناجم عن نقص الأنزيم المسؤول عن الحفاظ على تركيز ببتيد الغلوتاثيون الذي يحمي خلايا الدم الحمراء من التلف بفعل الأكسدة وبالتالي التسبب في فقر الدم الانحلالي الغير مناعي وخاصة عند تناول المُصاب لكميات كبيرة من الفول أو التعرض لحبوب اللقاح الخاصة بالنبته المُثمرة للفول لا يمكن الوقاية من المرض لانه خلقي جيني
- E3 | qa_id=ahd5k_02292 | relation=فقر الدم --HAS_SYMPTOM--> الم المعدجة: نقص في الدم مع الالم في المعده
  Source question: والدتي تعاني من نقص في الدم مع الالم في المعده
  Source answer: الم المعدجة يجب معرفة سببه وذل بعمل دراسة للمعدة ولنبدأ بفحص الجرثومة الحلزونية ، وربما سنحتاج لاحقا لمنظار للمعدة اما نقص الدم فهذ يجب توضيحة بشكل جيد ودراسته لمعرفة السبب وعلاجه
- E4 | qa_id=ahd5k_02546 | relation=فقر الدم --HAS_SYMPTOM--> الم المعدجة: أحيانا الم في المعدة كسل وخمول اضطرابات في النوم
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري
- E5 | qa_id=ahd5k_01162 | relation=فقر الدم --DIAGNOSED_BY--> فحص تحاليل مخبرية: فحص التحاليل المخبرية مرتبط بتشخيص فقر الدم
  Source question: عندي فقر دم وعملت التحاليل عندي نقص فيتامين دال ونقص حديد وصف لي الدكتور 20 ابرة حديد لمدة شهر هل اخذ هالكمية بهذه المدة آمن أم مضر للجسم ؟ وما...
  Source answer: يجب الاعتماد على نسبة الهيموكلوبين لتحديد طريقة العلاج و كمية العلاج نسبة مخزون الحديد في الجسم مقبولة نعم يوجد نقص في نسبة فيتامين د تركيز الحديد يختلف حسب نوعية العلاج العدد المذكور في رسالتك غير مستوجب وغير متوافق مع التحليل المرسل مع السؤال
- E6 | qa_id=ahd5k_00838 | relation=فقر الدم --HAS_SYMPTOM--> تنميل: نقص فيتامين (ب12) يسبب انيميا وتنميل
  Source question: اشعر بتنميل من بداية النصف الاسفل من الجسم حتى اسفل القدم عند تحريك الرقبة الى اسفل و انا عندي انيميا هل لها علاقة
  Source answer: نعم ... نقص فيتامين (ب12) يسبب انيميا وتنميل
- E7 | qa_id=ahd5k_02546 | relation=فقر الدم --HAS_SYMPTOM--> فقدان الشهيه: فقر الدم سبب فقدان الشهيه
  Source question: هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره
  Source answer: أعراض فقر الدم تؤثر على جميع أعضاء الجسم دوخه وتوتر زيادة ضربات القلب ضيق في التنفس غثيان وتقي وأحيانا الم في المعدة كسل وخمول اضطرابات في النوم شحوب في البشره وأعراض كثيرة اخري
- E8 | qa_id=ahd5k_00594 | relation=فقر الدم --MANAGED_BY--> أغذية غنية بالحديد والفولات وفيتامين ب12: يمكن دعم فقر الدم بنظام غذائي غني بعناصر مثل الحديد وحمض الفوليك وفيتامين ب-12، مع بقاء العلاج حسب نوع فقر الدم تحت إشراف الطبيب.
  Source question: السلام عليكم دكتور انا عندي فقر دم اي هي اغدية المفيدة الي؟
  Source answer: يحدث فقر الدم عندما لا يحتوي جسمك على ما يكفي من خلايا الدم الحمراء نتيجة فقدان الدم أو عدم القدرة على تكوين خلايا دم حمراء كافية. ويوجد العديد من أنوع فقر الدم منها الذي يكون بسبب نقص الحديد أو حمض الفوليك أو فيتامين ب-12 وغيرها. ويمكن اتباع نظام غذائي غني بالعناصر اللازمة لتعويض النقص من خلال: الورقيات الخضراء: السبانخ/ الكرنب/ الهندباء/ الخبيزة. اللحوم والدواجن. كبدة الخروف. المأكولات البحرية: السردين/ التونا/ السلمون. عصير البرتقال المحصن. الحبوب المدعمة. بعض الحبوب: الفاصولياء/ الحمص/ فول الصويا/ البازلاء. بذور اليقطين/ الكاجو/ الفستق/ الصنوبر/ الجوز/ بذور عباد الشمس. تجنب تناول الأطعمة الغنية بالحديد مع الأطعمة أو المشروبات التي تمنع امتصاص الحديد مثل: القهوة أو الشاي /البيض/ الأطعم...

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_107: انا عندى 16 سنة وعندي ارتخاء بالصمام الميترالى والاعراض اللى عندي دوخة لما أقف و بتعب من أقل مجهود , وعند الاستيقاظ هناك ضيق بالتنفس,والدكتورظكاتبلى اندرال 20 جم بس مش...

```text
User Question:
انا عندى 16 سنة وعندي ارتخاء بالصمام الميترالى والاعراض اللى عندي دوخة لما أقف و بتعب من أقل مجهود , وعند الاستيقاظ هناك ضيق بالتنفس,والدكتورظكاتبلى اندرال 20 جم بس مش...

Retrieved Entities:
- ارتخاء (DiseaseCondition; match=exact; id=ent_diseasecondition_d570c92436e9)
- دوخة (Symptom; match=exact; id=ent_symptom_850b2a35c32d)
- تعب (Symptom; match=exact; id=ent_symptom_28acc791e82d)
- صمام القلب (DiseaseCondition; match=alias; id=ent_diseasecondition_de01cca177b2)

Retrieved Relations:
- [1] التهاب --HAS_SYMPTOM--> تعب (score=0.771779; reliability=medium)
- [2] تعب --SYMPTOM_OF--> التهاب (score=0.770659; reliability=medium)
- [3] ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب (score=0.769951; reliability=medium)
- [4] ارتفاع ضغط الدم --HAS_SYMPTOM--> دوخة (score=0.76804; reliability=medium)
- [5] دوخة --SYMPTOM_OF--> ارتفاع ضغط الدم (score=0.76692; reliability=medium)
- [6] ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس (score=0.765727; reliability=medium)

Evidence Sentences:
- E1 | qa_id=ahd5k_03872 | relation=التهاب --HAS_SYMPTOM--> تعب: اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام
  Source question: السلام وعليكم ورحمة الله وبركاتو اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام .ارجو الاجابه وشكرا...
  Source answer: أعراض التهاب وحساسيه الجيوب الانفيه لابد من استخدام الادويه المناسبه بعد الفحص عند طبيب ENT
- E2 | qa_id=ahd5k_03872 | relation=تعب --SYMPTOM_OF--> التهاب: اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام
  Source question: السلام وعليكم ورحمة الله وبركاتو اعاني من فتره من آلام في الانف والوجه والاخص الجبين واشعر بحساسيه في الحلق مما يسبب لي ضيق تنفس وتعب بشكل عام .ارجو الاجابه وشكرا...
  Source answer: أعراض التهاب وحساسيه الجيوب الانفيه لابد من استخدام الادويه المناسبه بعد الفحص عند طبيب ENT
- E3 | qa_id=ahd5k_04701 | relation=ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب: تسارع في ضربات القلب
  Source question: انا اعاني من دوخة خاصة اثناء المشي وفي بعض الاحيان ضيق تنفس كما انني اعاني من مشكل اثناء بداية النوم لانها تنتابني الدوخة وتسارع في ضربات القلب ارجوكم افيدوني وشكرا
  Source answer: كثير من الفتيات يعانن من هذه الأعراض وذلك نتيجة انخفاض الضغط وبالتالي ارتفاع نبضات القلب والشعور بالدوخة والإجهاد وينصح بتناول وجبة الإفطار والإكثار من السوائل والأملاح .. ألف سلامة
- E4 | qa_id=ahd5k_04701 | relation=ارتفاع ضغط الدم --HAS_SYMPTOM--> دوخة: دوخة
  Source question: انا اعاني من دوخة خاصة اثناء المشي وفي بعض الاحيان ضيق تنفس كما انني اعاني من مشكل اثناء بداية النوم لانها تنتابني الدوخة وتسارع في ضربات القلب ارجوكم افيدوني وشكرا
  Source answer: كثير من الفتيات يعانن من هذه الأعراض وذلك نتيجة انخفاض الضغط وبالتالي ارتفاع نبضات القلب والشعور بالدوخة والإجهاد وينصح بتناول وجبة الإفطار والإكثار من السوائل والأملاح .. ألف سلامة
- E5 | qa_id=ahd5k_04701 | relation=دوخة --SYMPTOM_OF--> ارتفاع ضغط الدم: دوخة
  Source question: انا اعاني من دوخة خاصة اثناء المشي وفي بعض الاحيان ضيق تنفس كما انني اعاني من مشكل اثناء بداية النوم لانها تنتابني الدوخة وتسارع في ضربات القلب ارجوكم افيدوني وشكرا
  Source answer: كثير من الفتيات يعانن من هذه الأعراض وذلك نتيجة انخفاض الضغط وبالتالي ارتفاع نبضات القلب والشعور بالدوخة والإجهاد وينصح بتناول وجبة الإفطار والإكثار من السوائل والأملاح .. ألف سلامة
- E6 | qa_id=ahd5k_04701 | relation=ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس: ضيق تنفس
  Source question: انا اعاني من دوخة خاصة اثناء المشي وفي بعض الاحيان ضيق تنفس كما انني اعاني من مشكل اثناء بداية النوم لانها تنتابني الدوخة وتسارع في ضربات القلب ارجوكم افيدوني وشكرا
  Source answer: كثير من الفتيات يعانن من هذه الأعراض وذلك نتيجة انخفاض الضغط وبالتالي ارتفاع نبضات القلب والشعور بالدوخة والإجهاد وينصح بتناول وجبة الإفطار والإكثار من السوائل والأملاح .. ألف سلامة

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_108: هل هناك اسباب للحساسية من الباراسيتمول وما الاغذية التى امتنع عنها وما هى الاغذية التى ااكلها

```text
User Question:
هل هناك اسباب للحساسية من الباراسيتمول وما الاغذية التى امتنع عنها وما هى الاغذية التى ااكلها

Retrieved Entities:
- حساسية (DiseaseCondition; match=exact; id=ent_diseasecondition_2f75d3dabe0b)
- حساسية الصدر (DiseaseCondition; match=alias; id=ent_diseasecondition_250910ab0701)

Retrieved Relations:
- [1] حساسية --HAS_SYMPTOM--> سعال (score=0.963166; reliability=strong)
- [2] حساسية --HAS_SYMPTOM--> ضيق تنفس (score=0.951844; reliability=strong)
- [3] حساسية --HAS_SYMPTOM--> بلغم (score=0.901048; reliability=medium)
- [4] حساسية --HAS_SYMPTOM--> نشفان (score=0.877474; reliability=medium)
- [5] حساسية الصدر --HAS_SYMPTOM--> سعال (score=0.843151; reliability=medium)
- [6] ربو --HAS_SYMPTOM--> سعال (score=0.800413; reliability=medium)

Evidence Sentences:
- E1 | qa_id=ahd5k_00970 | relation=حساسية --HAS_SYMPTOM--> سعال: هل هو ربو ؟؟ او هل هناك حساسية ابسط من ذلك وعوارضها فقط السعال والبلغم
  Source question: ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟ هل امتنع عن طعام معين يزيد البلغم وانا غير مدخن واخذ علاج للضغط والكوليسترول عمرى 55...
  Source answer: اذا كنت مدخنا يجب الاقلاع عن التدخين نهائياً وقطعياً علما بأنك لا تدخن كما قلت لكن جلوسك في مكان فيه مدخنين يجعلك مدخناً ايضاً اذا كنت تعاني من التهاب ما في الجزء العلوي من الجهاز التنفسي يجب ان تتعالج يجب التأكد من ما تعانيه هل هو ربو ؟؟ او هل هناك حساسية ابسط من ذلك وعوارضها فقط السعال والبلغم يجب التأكد من ذلك وانصحك بان تطلب معاينة من اخصائي حساسية لكي يعطيك التشخيص النهائي وعندها الطريق الى العلاج يكون اسهل
- E2 | qa_id=ahd5k_00069 | relation=حساسية --HAS_SYMPTOM--> سعال: حساسية الصدر وسعال
  Source question: انا قبل يجي طقطقة في الفك الايسر بدون اللم وبعد ما سويت التمرين راح طقطقة الفك وجاني اللم هل هذا امر عادي بسبب التمرين ولا لل
  Source answer: طبيعي بسبب التمرين ومع الوقت بيختفي الألم وممكن استعمال بعض المسكنات الخفيفه
- E3 | qa_id=ahd5k_00683 | relation=حساسية --HAS_SYMPTOM--> ضيق تنفس: ضيق تنفس وسرعة التعب وقلق
  Source question: مرحبا اعاني منذ فتره من نبضات قلي قويه واصبحت اشعر بها في جميع اجزاء جسمي خصوصا قبل النوم وضيق تنفس وسرعة التعب وقلق علما اني تعرضت لموقف قلق وتوتر ووخزات...
  Source answer: أتمنى لك السلامة، وأود الإشارة إلى ضرورة مراجعة الطبيب لتحديد الأسباب المحتملة ووصف العلاج المناسب فلا يجب إهمال هذه الأعراض، وبشكل عام قد يكون ذلك ناجم عن العديد من الأسباب، ومنها الآتي: القلق أو التوتر. ممارسة الرياضة أو النشاط البدني. الجفاف. ارتفاع درجة حرارة الجسم. الحساسية. اضطرابات الغدة الدرقية. أمراض القلب. اضطرابات الجهاز التنفسي. الاضطرابات العصبية. للمزيد: ما هي اسباب زيادة ضربات القلب المفاجئ؟ ما هي أهم طرق علاج ضربات القلب السريعة في المنزل؟
- E4 | qa_id=ahd5k_00010 | relation=حساسية --HAS_SYMPTOM--> ضيق تنفس: حساسية تسبب ضيق تنفس
  Source question: يوجد أعراض ترعبني. عند الصعود بالدرج او مرتفع ينقطع نفسي ويجب ان استريح علماً باني ب٢٦ من العمر ومن قبل كانت هناك آلام في الصدر غريبه كنت اتجاهلها علما بان...
  Source answer: لم تذكر خصائص ضيق النفس، لكن الفحص الطبي السريري ضروري كونه يسمح بالتأكد من خصائص الأعراض المذكورة والعلامات التي قد يجدها الطبيب عند الفحص، لأن الأسباب كثيرة تنفسية وقلبية ودموية ووعائية وغير ذلك
- E5 | qa_id=ahd5k_00970 | relation=حساسية --HAS_SYMPTOM--> بلغم: ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟
  Source question: ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟ هل امتنع عن طعام معين يزيد البلغم وانا غير مدخن واخذ علاج للضغط والكوليسترول عمرى 55...
  Source answer: اذا كنت مدخنا يجب الاقلاع عن التدخين نهائياً وقطعياً علما بأنك لا تدخن كما قلت لكن جلوسك في مكان فيه مدخنين يجعلك مدخناً ايضاً اذا كنت تعاني من التهاب ما في الجزء العلوي من الجهاز التنفسي يجب ان تتعالج يجب التأكد من ما تعانيه هل هو ربو ؟؟ او هل هناك حساسية ابسط من ذلك وعوارضها فقط السعال والبلغم يجب التأكد من ذلك وانصحك بان تطلب معاينة من اخصائي حساسية لكي يعطيك التشخيص النهائي وعندها الطريق الى العلاج يكون اسهل
- E6 | qa_id=ahd5k_02124 | relation=حساسية --HAS_SYMPTOM--> نشفان: واشعر بنشفان دائم في الحلق
  Source question: اصبت بحساسية في الصيف بالجسم وصفها الدكتور بحساسية شمس و بعد فترة اصبت بالتهاب لوز و بلعوم و حبوب في اخر الحلق الحبوب مازالت موجودة واشعر بنشفان دائم في الحلق...
  Source answer: الاعراض التي في الحلق أعراض فيروس مثل الكوكساكي فيروس تتحسن مع الوقت عليك بتقوية المناعة بأكل الفواكة والحمضيات وشرب الزنجبيل مع العسل والليمون مره باليوم الزنجبيل مطحون بمعدل معلقه صغيره يوجد أيضا شراب ECHINACEA يحسن حالتك
- E7 | qa_id=ahd5k_04490 | relation=حساسية الصدر --HAS_SYMPTOM--> سعال: حساسية الصدر and سعال co-occur with explicit symptom-pathology link
  Source question: انا عندي قضيبي صغير هل هذه بسبب متعلق بهرمون الذكوره علما انا عمري 17 ويوجد شعر على الارجل والابط ولايوجد على الشارب وبدي اعرف اذا كان السبب متعلق بلهرمون كيفيه...
  Source answer: يجب اجراء الفحص السريري و الفحوصات المخبرية لتحديد السبب ثم العلاج
- E8 | qa_id=ahd5k_00970 | relation=ربو --HAS_SYMPTOM--> سعال: هل هو ربو ؟؟ او هل هناك حساسية ابسط من ذلك وعوارضها فقط السعال والبلغم
  Source question: ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟ هل امتنع عن طعام معين يزيد البلغم وانا غير مدخن واخذ علاج للضغط والكوليسترول عمرى 55...
  Source answer: اذا كنت مدخنا يجب الاقلاع عن التدخين نهائياً وقطعياً علما بأنك لا تدخن كما قلت لكن جلوسك في مكان فيه مدخنين يجعلك مدخناً ايضاً اذا كنت تعاني من التهاب ما في الجزء العلوي من الجهاز التنفسي يجب ان تتعالج يجب التأكد من ما تعانيه هل هو ربو ؟؟ او هل هناك حساسية ابسط من ذلك وعوارضها فقط السعال والبلغم يجب التأكد من ذلك وانصحك بان تطلب معاينة من اخصائي حساسية لكي يعطيك التشخيص النهائي وعندها الطريق الى العلاج يكون اسهل

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_109: كان لدي ارتفاع بسيط في الصفائح ٤٦١ وعندما ولدت بعد ٥٠ يوم التحليل طلع ٦٧٩ واشكو من عدم اكتمال النفس في بعض الاوقات وقال لي الطبيب لديك التهاب في الصدر...

```text
User Question:
كان لدي ارتفاع بسيط في الصفائح ٤٦١ وعندما ولدت بعد ٥٠ يوم التحليل طلع ٦٧٩ واشكو من عدم اكتمال النفس في بعض الاوقات وقال لي الطبيب لديك التهاب في الصدر...

Retrieved Entities:
- الطبيب (Treatment; match=exact; id=ent_treatment_450cbdcb87da)
- الصفائح الدموية (DiseaseCondition; match=alias; id=ent_diseasecondition_b3e7fc089ddd)

Retrieved Relations:
- [1] صداع --INVESTIGATED_BY--> الصور الشعاعية (score=0.505269; reliability=limited)
- [2] الصور الشعاعية --INVESTIGATES--> صداع (score=0.419669; reliability=limited)
- [3] الصدمة الكهربائية --TREATED_BY--> الطبيب (score=0.418874; reliability=limited)
- [4] الحروق --TREATED_BY--> الطبيب (score=0.418874; reliability=limited)
- [5] الطبيب --TREATS--> الصدمة الكهربائية (score=0.417754; reliability=limited)
- [6] الطبيب --TREATS--> الحروق (score=0.417754; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_01058 | relation=صداع --INVESTIGATED_BY--> الصور الشعاعية: الصور الشعاعية قد تُطلب لفحص الصداع
  Source question: السلام عليكم أنا أشعر ببرودة رأسي -وغذا اصبح ملمس رأسي بارد جاني صداع لايزول بالمسكنات- ذهبت لأفضل أخصائي أنف وأذن وحنجرة قال هذا المرض ماله علاج !! ماهي التحاليل الأزمة...
  Source answer: أنصحك بمراجعة أخصائي الأمراض الداخلية الذي قد يطلب صور شعاعية للرأس من ضمن فحوص أخرى تحياتي
- E2 | qa_id=ahd5k_01058 | relation=الصور الشعاعية --INVESTIGATES--> صداع: الصور الشعاعية قد تُطلب لفحص الصداع
  Source question: السلام عليكم أنا أشعر ببرودة رأسي -وغذا اصبح ملمس رأسي بارد جاني صداع لايزول بالمسكنات- ذهبت لأفضل أخصائي أنف وأذن وحنجرة قال هذا المرض ماله علاج !! ماهي التحاليل الأزمة...
  Source answer: أنصحك بمراجعة أخصائي الأمراض الداخلية الذي قد يطلب صور شعاعية للرأس من ضمن فحوص أخرى تحياتي
- E3 | qa_id=ahd5k_04866 | relation=الصدمة الكهربائية --TREATED_BY--> الطبيب: يستدعي الطبيب او المسعف للتعامل مع المصاب
  Source question: لماذا يموت الانسان عندما يلتمس بالكهرباء وما علاقته بالبروتين الموجود في الجسم ولماذا احيانا هنالك اشخاص لايتأثرون بالتيار الكهربائي؟
  Source answer: الصدمة الكهربائية وتتجلى بالضرر الذى يصيب انسجة الجسم نتيجة تأثير التيار او القوس الكهربائى وغالبا ما يكون الضرر سطحيأ اى يتضرر الجلد واحيانأ الانسجة الرخوة مع الاربطة والعظام حيث تتعلق خطورة الصدمة وصعوبة معالجتها بنوع ومميزات ودرجة الانسجة ورد فعل الاعضاء واذا ما كانت الحروق شديدة يموت الانسان ليس بسبب التكهرب ولكن نتيجة الصدمة الكهربائية ومن مظاهرها. الحروق الكهربائية وهى اكثر انواع الصدمات الكهربائية انتشارا وتقسم الحروق حسب شروط حدوثها كالتالى : 1. الحروق التيارى او التلامسى عند مرور تيار مباشر عبر جسم الانسان عند ملامستة للاجزاء الموصلة للتيار الكهربائى ذات توتر اقل من 1 كيلو فولت ويتمثل باحتراق الجلد السطح الخارجى من الجسم . 2. الحرق القوسى نتيجة مرور التيار وثأثير القوس الكهربائى...
- E4 | qa_id=ahd5k_04866 | relation=الحروق --TREATED_BY--> الطبيب: يستدعي الطبيب او المسعف للتعامل مع المصاب
  Source question: لماذا يموت الانسان عندما يلتمس بالكهرباء وما علاقته بالبروتين الموجود في الجسم ولماذا احيانا هنالك اشخاص لايتأثرون بالتيار الكهربائي؟
  Source answer: الصدمة الكهربائية وتتجلى بالضرر الذى يصيب انسجة الجسم نتيجة تأثير التيار او القوس الكهربائى وغالبا ما يكون الضرر سطحيأ اى يتضرر الجلد واحيانأ الانسجة الرخوة مع الاربطة والعظام حيث تتعلق خطورة الصدمة وصعوبة معالجتها بنوع ومميزات ودرجة الانسجة ورد فعل الاعضاء واذا ما كانت الحروق شديدة يموت الانسان ليس بسبب التكهرب ولكن نتيجة الصدمة الكهربائية ومن مظاهرها. الحروق الكهربائية وهى اكثر انواع الصدمات الكهربائية انتشارا وتقسم الحروق حسب شروط حدوثها كالتالى : 1. الحروق التيارى او التلامسى عند مرور تيار مباشر عبر جسم الانسان عند ملامستة للاجزاء الموصلة للتيار الكهربائى ذات توتر اقل من 1 كيلو فولت ويتمثل باحتراق الجلد السطح الخارجى من الجسم . 2. الحرق القوسى نتيجة مرور التيار وثأثير القوس الكهربائى...
- E5 | qa_id=ahd5k_04866 | relation=الطبيب --TREATS--> الصدمة الكهربائية: يستدعي الطبيب او المسعف للتعامل مع المصاب
  Source question: لماذا يموت الانسان عندما يلتمس بالكهرباء وما علاقته بالبروتين الموجود في الجسم ولماذا احيانا هنالك اشخاص لايتأثرون بالتيار الكهربائي؟
  Source answer: الصدمة الكهربائية وتتجلى بالضرر الذى يصيب انسجة الجسم نتيجة تأثير التيار او القوس الكهربائى وغالبا ما يكون الضرر سطحيأ اى يتضرر الجلد واحيانأ الانسجة الرخوة مع الاربطة والعظام حيث تتعلق خطورة الصدمة وصعوبة معالجتها بنوع ومميزات ودرجة الانسجة ورد فعل الاعضاء واذا ما كانت الحروق شديدة يموت الانسان ليس بسبب التكهرب ولكن نتيجة الصدمة الكهربائية ومن مظاهرها. الحروق الكهربائية وهى اكثر انواع الصدمات الكهربائية انتشارا وتقسم الحروق حسب شروط حدوثها كالتالى : 1. الحروق التيارى او التلامسى عند مرور تيار مباشر عبر جسم الانسان عند ملامستة للاجزاء الموصلة للتيار الكهربائى ذات توتر اقل من 1 كيلو فولت ويتمثل باحتراق الجلد السطح الخارجى من الجسم . 2. الحرق القوسى نتيجة مرور التيار وثأثير القوس الكهربائى...
- E6 | qa_id=ahd5k_04866 | relation=الطبيب --TREATS--> الحروق: يستدعي الطبيب او المسعف للتعامل مع المصاب
  Source question: لماذا يموت الانسان عندما يلتمس بالكهرباء وما علاقته بالبروتين الموجود في الجسم ولماذا احيانا هنالك اشخاص لايتأثرون بالتيار الكهربائي؟
  Source answer: الصدمة الكهربائية وتتجلى بالضرر الذى يصيب انسجة الجسم نتيجة تأثير التيار او القوس الكهربائى وغالبا ما يكون الضرر سطحيأ اى يتضرر الجلد واحيانأ الانسجة الرخوة مع الاربطة والعظام حيث تتعلق خطورة الصدمة وصعوبة معالجتها بنوع ومميزات ودرجة الانسجة ورد فعل الاعضاء واذا ما كانت الحروق شديدة يموت الانسان ليس بسبب التكهرب ولكن نتيجة الصدمة الكهربائية ومن مظاهرها. الحروق الكهربائية وهى اكثر انواع الصدمات الكهربائية انتشارا وتقسم الحروق حسب شروط حدوثها كالتالى : 1. الحروق التيارى او التلامسى عند مرور تيار مباشر عبر جسم الانسان عند ملامستة للاجزاء الموصلة للتيار الكهربائى ذات توتر اقل من 1 كيلو فولت ويتمثل باحتراق الجلد السطح الخارجى من الجسم . 2. الحرق القوسى نتيجة مرور التيار وثأثير القوس الكهربائى...

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_110: عمري 18 سنة وأنا أعاني من صغر الثدي هل يوجد أي حل لتكبيره دون جراحة?

```text
User Question:
عمري 18 سنة وأنا أعاني من صغر الثدي هل يوجد أي حل لتكبيره دون جراحة?

Retrieved Entities:
- صغر الثدي (DiseaseCondition; match=exact; id=ent_diseasecondition_cbcc5fb6bf54)

Retrieved Relations:
- [1] بيلة الميوغلوبين --TREATED_BY--> السوائل (score=0.401988; reliability=limited)
- [2] نقص بحجم الثدي --TREATED_BY--> مراجعة اخصائية النسائية (score=0.40146; reliability=limited)
- [3] نقص بحجم الثدي --DIAGNOSED_BY--> فحص سريري (score=0.40146; reliability=limited)
- [4] شيب --TREATED_BY--> خلطة الريحان و الروزماري (score=0.397318; reliability=limited)
- [5] حساسية --DIAGNOSED_BY--> تحليل الحساسية (score=0.396585; reliability=limited)
- [6] السوائل --TREATS--> بيلة الميوغلوبين (score=0.316388; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_03468 | relation=بيلة الميوغلوبين --TREATED_BY--> السوائل: العلاج الاهم هو السوائل للمحافظة على الكلى
  Source question: هل هناك معالجة لمرض بيلة الميوغلوبين ارجو ايفادي به سواء هنا في سوريا او في اي دولة وفي اي مستشفى بالضبط لأني اعاني من هذا المرض منذ فترة وانا الان...
  Source answer: العلاج الاهم هو السوائل للمحافظة على الكلى
- E2 | qa_id=ahd5k_02702 | relation=نقص بحجم الثدي --TREATED_BY--> مراجعة اخصائية النسائية: مراجعة اخصائية النسائية
  Source question: أنا شاب أبلغ من العمر ٢٤سنه عندي نقص بحجم الثدي الايمن بحجم كثير ولافت علما انه لا يسبب لي اي ألم هل هناك علاج وتم اكتشاف ذالك وانا في سن...
  Source answer: يجب مراجعة اخصائية النسائية لإجراء الفحص السريري
- E3 | qa_id=ahd5k_02702 | relation=نقص بحجم الثدي --DIAGNOSED_BY--> فحص سريري: فحص سريري
  Source question: أنا شاب أبلغ من العمر ٢٤سنه عندي نقص بحجم الثدي الايمن بحجم كثير ولافت علما انه لا يسبب لي اي ألم هل هناك علاج وتم اكتشاف ذالك وانا في سن...
  Source answer: يجب مراجعة اخصائية النسائية لإجراء الفحص السريري
- E4 | qa_id=ahd5k_04612 | relation=شيب --TREATED_BY--> خلطة الريحان و الروزماري: هل خلطة الريحان و الروزماري مفيدة للتخلص من الشيب
  Source question: هل يوجد حل لعلاج الشيب المبكر ؟ هل خلطة الريحان و الروزماري مفيدة للتخلص من الشيب؟
  Source answer: لشيب (الشعر الأبيض) ظهور الشيب عملية فسيولوجية تحدث عادة عند التقدم في العمر. وذلك عندما لا تستطيع الخلايا الملونة التي تفرز مادة الميلانين (والتي تعطي الشعرة اللون) الاستمرار في نشاطها، إذ تفقد الشعرة لونها وتصبح بيضاء وهذا ما يسمى "بالشيب". إن ظهور الشيب على شعر الرأس أو الوجه لا يعني مطلقاً التقدم بالسن فقد يظهر قبل البلوغ أو بعد ذلك نتيجة ظروف معينة. كما أن الاستعداد الشخصي والعوامل النفسية والوراثية لهما أثر مهم في ظهور الشيب المبكر. ويجب الإشارة بأن بعض حالات الشيب المبكر تكون مؤقتة، إذ قد تعاود الخلايا الملونة نشاطها مرة أخرى خاصة بعد زوال المؤثر وبالتالي يعود لون الشعر إلى وضعه العادي ويحدث هذا أحياناً في أمراض الحميات ومرض الثعلبة. أما إذا كان المؤثر على الخلايا الأم (الكيراتينوس...
- E5 | qa_id=ahd5k_00864 | relation=حساسية --DIAGNOSED_BY--> تحليل الحساسية: تحليل الحساسية يُستخدم لتشخيص حساسية الصدر
  Source question: أن زوجة في 50 من عمري أعاني من إنتفاخ الثدي الأييسر و الشعور بالألم عند لمسه
  Source answer: عليك مراجعة استشارى أمراض النساء او طبيب اورام
- E6 | qa_id=ahd5k_03468 | relation=السوائل --TREATS--> بيلة الميوغلوبين: العلاج الاهم هو السوائل للمحافظة على الكلى
  Source question: هل هناك معالجة لمرض بيلة الميوغلوبين ارجو ايفادي به سواء هنا في سوريا او في اي دولة وفي اي مستشفى بالضبط لأني اعاني من هذا المرض منذ فترة وانا الان...
  Source answer: العلاج الاهم هو السوائل للمحافظة على الكلى

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_111: عمري ٢٥سنة واعاني من نشاط زائد في الغده الدرقية وقمت بأخذ جرعه من اليود النووي المشع وعندي طفل عمره سنه فما المده الزمنيه المحدده اللتي سأتمكن بعدها

```text
User Question:
عمري ٢٥سنة واعاني من نشاط زائد في الغده الدرقية وقمت بأخذ جرعه من اليود النووي المشع وعندي طفل عمره سنه فما المده الزمنيه المحدده اللتي سأتمكن بعدها

Retrieved Entities:
- الغدة الدرقية (DiseaseCondition; match=exact; id=ent_diseasecondition_7b4788cd854a)

Retrieved Relations:
- [1] مرض الغدة الدرقية --TREATED_BY--> التروكسين (score=0.772588; reliability=medium)
- [2] التروكسين --TREATS--> مرض الغدة الدرقية (score=0.671628; reliability=limited)
- [3] نشاط الغدة الدرقية --DIAGNOSED_BY--> تحاليل مخبرية (score=0.415583; reliability=limited)
- [4] مرض جريفز --DIAGNOSED_BY--> تحاليل مخبرية (score=0.411359; reliability=limited)
- [5] مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون (score=0.410588; reliability=limited)
- [6] تحاليل مخبرية --DIAGNOSES--> نشاط الغدة الدرقية (score=0.329983; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_00035 | relation=مرض الغدة الدرقية --TREATED_BY--> التروكسين: اخذ التروكسين
  Source question: انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟
  Source answer: علاج الغدة وجرعة العلاج تعتمد على مستوى الهرمون في الدم
- E2 | qa_id=ahd5k_00035 | relation=التروكسين --TREATS--> مرض الغدة الدرقية: اخذ التروكسين
  Source question: انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟
  Source answer: علاج الغدة وجرعة العلاج تعتمد على مستوى الهرمون في الدم
- E3 | qa_id=ahd5k_02200 | relation=نشاط الغدة الدرقية --DIAGNOSED_BY--> تحاليل مخبرية: يتم تشخيص نشاط الغدة الدرقية عبر تحاليل مخبرية لهرمونات T3 وT4
  Source question: ما هي أهم أسباب نشاط الغدة الدرقية؟
  Source answer: يعاني العديد من الأشخاص من حالة صحية تسمى نشاط الغدة الدرقية حيث يحدث في هذه الحالة إفراز كمية كبيرة من هرمونات الغدة الدرقية وهما ثلاثي يودوثيرونين (T3) وهرمون ثيروكسين (T4). ويوجد العديد من الحالات الصحية التي تسبب نشاط الغدة الدرقية ومن أسباب نشاط الغدة الدرقية ما يلي: الإصابة بأحد اضطرابات المناعة الذاتية الوراثية مثل مرض جريفز، حيث يتم إنتاج أجسام مضادة تهاجم الغدة الدرقية وتسبب إنتاج كميات كبيرة من هرمونات الغدة الدرقية. وتشيع هذه الحالة عند الإناث مقارنة بالذكور وتشكل حوالي 85% من حالات نشاط الغدة الدرقية. الإصابة بحالة تسمى عقيدات الغدة الدرقية، وهي عبارة عن كتلة في الغدة الدرقية تسبب إنتاج هرمونات الغدة الدرقية بكمية أكبر مما يحتاجه الجسم, الإصابة بحالة تسمى التهاب الغدة الدرقية....
- E4 | qa_id=ahd5k_02200 | relation=مرض جريفز --DIAGNOSED_BY--> تحاليل مخبرية: يتم تشخيص مرض جريفز عبر تحاليل مخبرية لهرمونات الغدة الدرقية
  Source question: ما هي أهم أسباب نشاط الغدة الدرقية؟
  Source answer: يعاني العديد من الأشخاص من حالة صحية تسمى نشاط الغدة الدرقية حيث يحدث في هذه الحالة إفراز كمية كبيرة من هرمونات الغدة الدرقية وهما ثلاثي يودوثيرونين (T3) وهرمون ثيروكسين (T4). ويوجد العديد من الحالات الصحية التي تسبب نشاط الغدة الدرقية ومن أسباب نشاط الغدة الدرقية ما يلي: الإصابة بأحد اضطرابات المناعة الذاتية الوراثية مثل مرض جريفز، حيث يتم إنتاج أجسام مضادة تهاجم الغدة الدرقية وتسبب إنتاج كميات كبيرة من هرمونات الغدة الدرقية. وتشيع هذه الحالة عند الإناث مقارنة بالذكور وتشكل حوالي 85% من حالات نشاط الغدة الدرقية. الإصابة بحالة تسمى عقيدات الغدة الدرقية، وهي عبارة عن كتلة في الغدة الدرقية تسبب إنتاج هرمونات الغدة الدرقية بكمية أكبر مما يحتاجه الجسم, الإصابة بحالة تسمى التهاب الغدة الدرقية....
- E5 | qa_id=ahd5k_00035 | relation=مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون: مستوى الهرمون في الدم
  Source question: انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟
  Source answer: علاج الغدة وجرعة العلاج تعتمد على مستوى الهرمون في الدم
- E6 | qa_id=ahd5k_02200 | relation=تحاليل مخبرية --DIAGNOSES--> نشاط الغدة الدرقية: يتم تشخيص نشاط الغدة الدرقية عبر تحاليل مخبرية لهرمونات T3 وT4
  Source question: ما هي أهم أسباب نشاط الغدة الدرقية؟
  Source answer: يعاني العديد من الأشخاص من حالة صحية تسمى نشاط الغدة الدرقية حيث يحدث في هذه الحالة إفراز كمية كبيرة من هرمونات الغدة الدرقية وهما ثلاثي يودوثيرونين (T3) وهرمون ثيروكسين (T4). ويوجد العديد من الحالات الصحية التي تسبب نشاط الغدة الدرقية ومن أسباب نشاط الغدة الدرقية ما يلي: الإصابة بأحد اضطرابات المناعة الذاتية الوراثية مثل مرض جريفز، حيث يتم إنتاج أجسام مضادة تهاجم الغدة الدرقية وتسبب إنتاج كميات كبيرة من هرمونات الغدة الدرقية. وتشيع هذه الحالة عند الإناث مقارنة بالذكور وتشكل حوالي 85% من حالات نشاط الغدة الدرقية. الإصابة بحالة تسمى عقيدات الغدة الدرقية، وهي عبارة عن كتلة في الغدة الدرقية تسبب إنتاج هرمونات الغدة الدرقية بكمية أكبر مما يحتاجه الجسم, الإصابة بحالة تسمى التهاب الغدة الدرقية....

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_112: يشعر والدي بألم في منطقة الصدر علما ان والدي مصاب بجلطة قلبية ودماغية اليوم قد تناول بيزا وكانت دسمة،،،،،هل هذا الم قلب ام الام معدة

```text
User Question:
يشعر والدي بألم في منطقة الصدر علما ان والدي مصاب بجلطة قلبية ودماغية اليوم قد تناول بيزا وكانت دسمة،،،،،هل هذا الم قلب ام الام معدة

Retrieved Entities:
- الام (Symptom; match=exact; id=ent_symptom_249d07021a1b)

Retrieved Relations:
- [1] ضرس العقل --HAS_SYMPTOM--> الام (score=0.766384; reliability=medium)
- [2] الام --SYMPTOM_OF--> ضرس العقل (score=0.765264; reliability=medium)
- [3] ارتياف دعب \u0627لديم --HAS_SYMPTOM--> الالم (score=0.756879; reliability=medium)
- [4] ضرس العقل --HAS_SYMPTOM--> صداع (score=0.7523; reliability=medium)
- [5] الالم --SYMPTOM_OF--> ارتياف دعب \u0627لديم (score=0.671279; reliability=limited)
- [6] صداع --SYMPTOM_OF--> ضرس العقل (score=0.6667; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_04356 | relation=ضرس العقل --HAS_SYMPTOM--> الام: ضرس العقل
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين
- E2 | qa_id=ahd5k_04356 | relation=الام --SYMPTOM_OF--> ضرس العقل: ضرس العقل
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين
- E3 | qa_id=ahd5k_03738 | relation=ارتياف دعب \u0627لديم --HAS_SYMPTOM--> الالم: الالم الدي الديم الديم الديم
  Source question: منذ فتره اشعر بألم فى عضله الصدر وليس القفص الصدرى وهذا عند الضغط عليها اريد ان اعرف ما السبب؟
  Source answer: الالم الذي يحدث عند الضغط على عضلة الصدر دليل وجود الالم في العضلة نفسها ربما نتيجة تشنج ما او جهد ما قمت به والافضل في هذه الحالة ان تريح هذه العضلة ولا تقوم بمجهود علما بان احيانا حتى السعال يسبب الم في عضلة الصدر
- E4 | qa_id=ahd5k_04356 | relation=ضرس العقل --HAS_SYMPTOM--> صداع: ضرس العقل
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين
- E5 | qa_id=ahd5k_03738 | relation=الالم --SYMPTOM_OF--> ارتياف دعب \u0627لديم: الالم الدي الديم الديم الديم
  Source question: منذ فتره اشعر بألم فى عضله الصدر وليس القفص الصدرى وهذا عند الضغط عليها اريد ان اعرف ما السبب؟
  Source answer: الالم الذي يحدث عند الضغط على عضلة الصدر دليل وجود الالم في العضلة نفسها ربما نتيجة تشنج ما او جهد ما قمت به والافضل في هذه الحالة ان تريح هذه العضلة ولا تقوم بمجهود علما بان احيانا حتى السعال يسبب الم في عضلة الصدر
- E6 | qa_id=ahd5k_04356 | relation=صداع --SYMPTOM_OF--> ضرس العقل: ضرس العقل
  Source question: لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم
  Source answer: في حال وجود اتجاه معكوس او عدم وجود مساحه كافيه لضرس العقل و يسبب اﻻم بدردات متفاوته ننصح عاده بخلع ضروس العقل و عليك مراجعه طبيبك او اخصائي جراحه وجه و فكين

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_113: هل يوجد تأثير على الجنين في حالة تعاطي أقراص ميزوتاك في بداية الحمل بغرض الإجهاض وأنا الآن اقتنعت باكمال الحمل ولكن قلق من تأثر الجنين بالمادة الفعالة لهذا الدواء؟

```text
User Question:
هل يوجد تأثير على الجنين في حالة تعاطي أقراص ميزوتاك في بداية الحمل بغرض الإجهاض وأنا الآن اقتنعت باكمال الحمل ولكن قلق من تأثر الجنين بالمادة الفعالة لهذا الدواء؟

Retrieved Entities:
- الحمل (DiseaseCondition; match=exact; id=ent_diseasecondition_7abdd04c7114)
- قلق (Symptom; match=exact; id=ent_symptom_f51ef98950a2)
- الدواء (Treatment; match=exact; id=ent_treatment_1479a48d3d42)
- الجنين (DiseaseCondition; match=exact; id=ent_diseasecondition_1420aadad936)
- ميزوتاك (Treatment; match=exact; id=ent_treatment_2702542ba0eb)

Retrieved Relations:
- [1] بريمولوت ن --REQUIRES_MEDICAL_SUPERVISION_FOR--> إيقاف الدواء ومراجعة الطبيب أثناء الحمل (score=0.791231; reliability=medium)
- [2] عظام الجنين --DEVELOPS_DURING--> نهاية الأسبوع السادس تقريبا (score=0.55377; reliability=limited)
- [3] الدواء --TREATS--> الملوية البوابية (score=0.544646; reliability=limited)
- [4] فايروس الكبد --TREATED_BY--> اللقاح (score=0.527948; reliability=limited)
- [5] الحمل --HAS_SYMPTOM--> قيء (score=0.522589; reliability=limited)
- [6] فايروس الكبد --TREATED_BY--> الجرعات الثلاثه (score=0.517388; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_00439 | relation=بريمولوت ن --REQUIRES_MEDICAL_SUPERVISION_FOR--> إيقاف الدواء ومراجعة الطبيب أثناء الحمل: إذا كانت المريضة حاملا وتستعمل بريمولوت ن فيجب إيقافه؛ يذكر المصدر دراسات عن احتمال تشوهات في القلب والأوعية والأنبوب العصبي والدماغ.
  Source question: ماهي التشوهات التي تسببها بريمولوت ن اثناء الحمل
  Source answer: اذا كنت حامل وما زلت تستعملين اقراص ال بريمولوت ن فيجب ايقافها ، فهناك دراسات اثبتتت انه يمكن ان تؤدي هذه الاقراص الى تشوهات في القلب والاوعيه الدمويه لدى الجنين ، كما انه يمكن ان تؤدي الى تشوهات في الانبوب العصبي والدماغ
- E2 | qa_id=ahd5k_00230 | relation=عظام الجنين --DEVELOPS_DURING--> نهاية الأسبوع السادس تقريبا: في نهاية الأسبوع السادس يبدأ الجنين بتكوين العمود الفقري ويكون صغيرا جدا.
  Source question: في أي شهر من أشهر الحمل يتم تكوين عظام الجنين
  Source answer: في نهاية الاسبوع السادس يبدأ الجنين بتكوين العمود الفقري ويكون صغير جدا لا يزيد طوله عن 2/1سم.
- E3 | qa_id=ahd5k_03807 | relation=الدواء --TREATS--> الملوية البوابية: مضادات حيويه نكسيوم و كلاريثرومايسين واموكسسلين
  Source question: من فتره سنه كان عندي الم ب المعده واسهال حاد وعملت منضار وطلع عندي قرحه بالمعده واخدت مضادات حيويه نكسيوم و كلاريثرومايسين واموكسسلين وضليت فتره 6 شهور وهلق في نفس...
  Source answer: اخي الكريم بعد تشخيص القرحة واعطاء العلاج أنت بحاجة للمتابعة الطبية لمعرفة شفاء القرحة بشكل حيث يوجد خطوط علاجية كثيرة وقد لاتستفيد على أحدها وتستجيب على الأخر ......هل كان هناك اصابة بالملوية البوابية مثبتة ...........................
- E4 | qa_id=ahd5k_00597 | relation=فايروس الكبد --TREATED_BY--> اللقاح: اللقاح
  Source question: السلام عليكم ورحمة الله وبركاته اريد ان اسأل بخصوص الزواج من رجل حامل لفايروس الكبد من النوع بي وانا فتاه سليمه هل هناك ضرر من ذلك هل الجرعات الثلاثه كافيه...
  Source answer: بوجود اللقاح تستطيعين الإطمئنان لن ينتقل اذا اتبعنا التعليمات الصحيحة سيتحجم الفيروس بالعلاج ويفقد نشاطه تابعي مع استشاري كبد
- E5 | qa_id=ahd5k_02903 | relation=الحمل --HAS_SYMPTOM--> قيء: قيء
  Source question: الدكتور الفاضل/ لقد قمت بعمل طفل انبوب وكان ترجيع الاجنة بتاريخ ١٩/٧/٢٠١٠ والحمدلله نجحت وتم الحمل. : حدثت مداعبات جنسية مع زوجي ولكن بدون ادخال القضيب ووصلنا كلانا للنشوة الجنسية...
  Source answer: هذا لن يؤثر على الحمل
- E6 | qa_id=ahd5k_00597 | relation=فايروس الكبد --TREATED_BY--> الجرعات الثلاثه: الجرعات الثلاثه
  Source question: السلام عليكم ورحمة الله وبركاته اريد ان اسأل بخصوص الزواج من رجل حامل لفايروس الكبد من النوع بي وانا فتاه سليمه هل هناك ضرر من ذلك هل الجرعات الثلاثه كافيه...
  Source answer: بوجود اللقاح تستطيعين الإطمئنان لن ينتقل اذا اتبعنا التعليمات الصحيحة سيتحجم الفيروس بالعلاج ويفقد نشاطه تابعي مع استشاري كبد

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_114: حموضة في فمي واحساس برائحة تفاح متعفن مع كدمات زرقاء غامقة في قدماي واحساس بغبوش في الرؤية

```text
User Question:
حموضة في فمي واحساس برائحة تفاح متعفن مع كدمات زرقاء غامقة في قدماي واحساس بغبوش في الرؤية

Retrieved Entities:
- حموضة (Symptom; match=exact; id=ent_symptom_1a7b2eae066b)

Retrieved Relations:
- [1] فقر الدم --HAS_SYMPTOM--> الم المعدجة (score=0.747663; reliability=limited)
- [2] الم المعدجة --INVESTIGATED_BY--> فحص الجرثومة الحلزونية (score=0.747663; reliability=limited)
- [3] الم المعدجة --SYMPTOM_OF--> فقر الدم (score=0.300063; reliability=limited)
- [4] فحص الجرثومة الحلزونية --INVESTIGATES--> الم المعدجة (score=0.300063; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_02292 | relation=فقر الدم --HAS_SYMPTOM--> الم المعدجة: نقص في الدم مع الالم في المعده
  Source question: والدتي تعاني من نقص في الدم مع الالم في المعده
  Source answer: الم المعدجة يجب معرفة سببه وذل بعمل دراسة للمعدة ولنبدأ بفحص الجرثومة الحلزونية ، وربما سنحتاج لاحقا لمنظار للمعدة اما نقص الدم فهذ يجب توضيحة بشكل جيد ودراسته لمعرفة السبب وعلاجه
- E2 | qa_id=ahd5k_02292 | relation=الم المعدجة --INVESTIGATED_BY--> فحص الجرثومة الحلزونية: فحص الجرثومة الحلزونية
  Source question: والدتي تعاني من نقص في الدم مع الالم في المعده
  Source answer: الم المعدجة يجب معرفة سببه وذل بعمل دراسة للمعدة ولنبدأ بفحص الجرثومة الحلزونية ، وربما سنحتاج لاحقا لمنظار للمعدة اما نقص الدم فهذ يجب توضيحة بشكل جيد ودراسته لمعرفة السبب وعلاجه
- E3 | qa_id=ahd5k_02292 | relation=الم المعدجة --SYMPTOM_OF--> فقر الدم: نقص في الدم مع الالم في المعده
  Source question: والدتي تعاني من نقص في الدم مع الالم في المعده
  Source answer: الم المعدجة يجب معرفة سببه وذل بعمل دراسة للمعدة ولنبدأ بفحص الجرثومة الحلزونية ، وربما سنحتاج لاحقا لمنظار للمعدة اما نقص الدم فهذ يجب توضيحة بشكل جيد ودراسته لمعرفة السبب وعلاجه
- E4 | qa_id=ahd5k_02292 | relation=فحص الجرثومة الحلزونية --INVESTIGATES--> الم المعدجة: فحص الجرثومة الحلزونية
  Source question: والدتي تعاني من نقص في الدم مع الالم في المعده
  Source answer: الم المعدجة يجب معرفة سببه وذل بعمل دراسة للمعدة ولنبدأ بفحص الجرثومة الحلزونية ، وربما سنحتاج لاحقا لمنظار للمعدة اما نقص الدم فهذ يجب توضيحة بشكل جيد ودراسته لمعرفة السبب وعلاجه

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_115: قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة

```text
User Question:
قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة

Retrieved Entities:
- أشعة (Test; match=alias; id=ent_test_c4cfd2d6468c)
- انتفاخ (Symptom; match=alias; id=ent_symptom_fd750eeb2865)
- وجع (Symptom; match=alias; id=ent_symptom_42ad4acdebc5)

Retrieved Relations:
- [1] وجع --INVESTIGATED_BY--> اشعة (score=0.904228; reliability=medium)
- [2] انتفاخ --INVESTIGATED_BY--> اشعة (score=0.898703; reliability=medium)
- [3] اشعة --INVESTIGATES--> وجع (score=0.818628; reliability=medium)
- [4] اشعة --INVESTIGATES--> انتفاخ (score=0.813103; reliability=medium)
- [5] التهاب --DIAGNOSED_BY--> اشعة (score=0.762268; reliability=medium)
- [6] ارتجاج دماغي --DIAGNOSED_BY--> أشعة (score=0.762268; reliability=medium)

Evidence Sentences:
- E1 | qa_id=ahd5k_01537 | relation=وجع --INVESTIGATED_BY--> اشعة: اشعة بالصبغة
  Source question: قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة
  Source answer: نرجو توضيح السؤال وما هي نتيجة الفحص الشعاعي كما وردت في التقرير ليتسنى لنا معرفة النتيجة ومن ثم التشخيص
- E2 | qa_id=ahd5k_01537 | relation=انتفاخ --INVESTIGATED_BY--> اشعة: اشعة بالصبغة
  Source question: قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة
  Source answer: نرجو توضيح السؤال وما هي نتيجة الفحص الشعاعي كما وردت في التقرير ليتسنى لنا معرفة النتيجة ومن ثم التشخيص
- E3 | qa_id=ahd5k_01537 | relation=اشعة --INVESTIGATES--> وجع: اشعة بالصبغة
  Source question: قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة
  Source answer: نرجو توضيح السؤال وما هي نتيجة الفحص الشعاعي كما وردت في التقرير ليتسنى لنا معرفة النتيجة ومن ثم التشخيص
- E4 | qa_id=ahd5k_01537 | relation=اشعة --INVESTIGATES--> انتفاخ: اشعة بالصبغة
  Source question: قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة
  Source answer: نرجو توضيح السؤال وما هي نتيجة الفحص الشعاعي كما وردت في التقرير ليتسنى لنا معرفة النتيجة ومن ثم التشخيص
- E5 | qa_id=ahd5k_00114 | relation=التهاب --DIAGNOSED_BY--> اشعة: اجراء صورة اشعة عادية للحوض
  Source question: منذ دخول فصل الشتاء انتابتني بعض الاعراض ولاسيما في الرجل اليسري اشعر بالم في المفصل ودلك عند ثني الرجل يإما بالجلوس اوالقعود وعندما احاول الوقوف ارجع رجلي بصعوبة لمكانها الطبيعي...
  Source answer: ما تعانين منه هو عبارة عن الم ميكانيكي اي وقت الحركة فقط ., لا وجود له مع الراحة , ينصح لك عمل صورة اشعة عادية للحوض وبها يتضح وضع راس الفخذ من الجهتين . اذا كانت الامور سليمة عليك بالسباحة وعمل جلسات علاج طبيعي وتليين حركة مفصل الفخذ بالنوم مستلقية على ظهرك وعمل حركة الدراجة خمس دقائق يوميا
- E6 | qa_id=ahd5k_02003 | relation=ارتجاج دماغي --DIAGNOSED_BY--> أشعة: عمل صورة أشعة للرأس
  Source question: سقطت ابنتي اعلى راسها فظهر لها انتفاخ خلف الاذن والم شديد في الرقبه ولاتستطيع تحريكها
  Source answer: يجب أخذها للمستشفى فوراً لعمل صورة أشعة للرأس ، والتأكد من عدم إصابتها بارتجاج دماغي، والتعامل مع الورم خلف الأذن الذي قد يكون نزيفاً بسيطاً.

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_116: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر

```text
User Question:
ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر

Retrieved Entities:
- القات (Treatment; match=exact; id=ent_treatment_fe7b9cfab843)
- سكر (DiseaseCondition; match=exact; id=ent_diseasecondition_4393a2bf88a6)

Retrieved Relations:
- [1] مرض السكري --HAS_SYMPTOM--> ضغط الدم (score=0.90531; reliability=strong)
- [2] ضغط الدم --SYMPTOM_OF--> مرض السكري (score=0.744279; reliability=limited)
- [3] مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (score=0.502444; reliability=limited)
- [4] التهاب --DIAGNOSED_BY--> تحاليل مخبرية (score=0.471323; reliability=limited)
- [5] تحاليل مخبرية --DIAGNOSES--> مرض السكري (score=0.401484; reliability=limited)
- [6] تحاليل مخبرية --DIAGNOSES--> التهاب (score=0.385723; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_01294 | relation=مرض السكري --HAS_SYMPTOM--> ضغط الدم: مرض السكري وضغط الدمز
  Source question: تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س
  Source answer: العمليات الجراحية اليوم لا يعيقها أي مرض إذا ما تمت السيطرة عليه بشكل جيد قبل وأثناء وبعد العمل الجراحي، فلا داعي للقلق
- E2 | qa_id=ahd5k_02607 | relation=مرض السكري --HAS_SYMPTOM--> ضغط الدم: مرض السكري وضغط الدم
  Source question: السلام عليكم والدي عمره 58 و لديه شريان مغلق من الجهة اليمنى بنسبة تسعين بالمئة منذ اربع سنوات و لديه ضغط و سكري و لم يتعالج الى الان فهل حالته...
  Source answer: لم تحدد أي شريان، فلكل عضو أو منطقة في الجسم خصائصها البنيوية والوظيفية، وفي جميع الأحوال الحالة السريرية هي الفيصل وليس الفحص الذي هو ليس أكثر من مكمل للفحص الطبي السريري، لأن الكثير من الشرايين التي تغلق ينشأ بدلا عنها أخرى بديلة لا سيما إذا ما كان الشخص صحيح البنية ورياضي، وهذه الأوعية البديلة تكفل التروية للمنطقة التي يمكن أن تتضرر من الشريان المنغلق
- E3 | qa_id=ahd5k_02607 | relation=ضغط الدم --SYMPTOM_OF--> مرض السكري: مرض السكري وضغط الدم
  Source question: السلام عليكم والدي عمره 58 و لديه شريان مغلق من الجهة اليمنى بنسبة تسعين بالمئة منذ اربع سنوات و لديه ضغط و سكري و لم يتعالج الى الان فهل حالته...
  Source answer: لم تحدد أي شريان، فلكل عضو أو منطقة في الجسم خصائصها البنيوية والوظيفية، وفي جميع الأحوال الحالة السريرية هي الفيصل وليس الفحص الذي هو ليس أكثر من مكمل للفحص الطبي السريري، لأن الكثير من الشرايين التي تغلق ينشأ بدلا عنها أخرى بديلة لا سيما إذا ما كان الشخص صحيح البنية ورياضي، وهذه الأوعية البديلة تكفل التروية للمنطقة التي يمكن أن تتضرر من الشريان المنغلق
- E4 | qa_id=ahd5k_04912 | relation=ضغط الدم --SYMPTOM_OF--> مرض السكري: مع العلم أن المريض يعاني من مرض السكر
  Source question: هل ضعف عضله القلب وضيق ثلاث شرايين في القلب لهم عمليه جراحيه مع العلم أن المريض يعاني من مرض السكر ام يبقى على العلاج ولو عمليه جراحيهوين تنصحونا نعملها وعاووزيين...
  Source answer: هذا يتطلب معرفة نسبة الضعف الموجود في العضلة القلبية ونسبة التضيق في الثلاثة شرايين المذكورة، كما أنه من الضروري معرفة الحالة الوظيفية لباقي أعضاء الجسم خاصة الكلى والجهاز التنفسي، والكبد وغيره، وفي جميع الأحوال في العادة تُعرض نتائج القثطرة على فريق طبي مُتخصص لتقييم كل هذه الأمور ومن ثم يتم اختيار الطريقة العلاجية التي تتناسب أكثر مع حالة المريض
- E5 | qa_id=ahd5k_01551 | relation=مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.
- E6 | qa_id=ahd5k_01551 | relation=التهاب --DIAGNOSED_BY--> تحاليل مخبرية: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.
- E7 | qa_id=ahd5k_01551 | relation=تحاليل مخبرية --DIAGNOSES--> مرض السكري: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.
- E8 | qa_id=ahd5k_01551 | relation=تحاليل مخبرية --DIAGNOSES--> التهاب: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_117: أعاني من حرقان بكامل بجسمي والتهاب المسالك البوليه وارتفاع الكلسترول والدهون الثلاثيه مال الحل جزاكم الله خير وما قد يكون المسبب

```text
User Question:
أعاني من حرقان بكامل بجسمي والتهاب المسالك البوليه وارتفاع الكلسترول والدهون الثلاثيه مال الحل جزاكم الله خير وما قد يكون المسبب

Retrieved Entities:
- ارتفاع الكلسترول (DiseaseCondition; match=exact; id=ent_diseasecondition_b774b131180f)
- كلسترول (DiseaseCondition; match=exact; id=ent_diseasecondition_677ee50113db)

Retrieved Relations:
- [1] الصداع التوتري --HAS_SYMPTOM--> صداع (score=0.754124; reliability=medium)
- [2] صداع --SYMPTOM_OF--> الصداع التوتري (score=0.668524; reliability=limited)
- [3] ارتفاع ضغط الدم --TREATED_BY--> العقاقير (score=0.391394; reliability=limited)
- [4] العقاقير --TREATS--> ارتفاع ضغط الدم (score=0.305794; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_00780 | relation=الصداع التوتري --HAS_SYMPTOM--> صداع: الصداع التوتري قد يظهر كصداع يختلف حدته
  Source question: لماذا اصحو من النوم يوميا بصداع يختلف حدته من خفيف إلى قوي جدا لدرجة ان عيناي تدمع من كثرة الصداع مع العلم بان عمري 29 سنة ولدي طفل عمره سنة...
  Source answer: قد يكون لديك نوع من الصداع يسمى بالصداع التوتري و هو ناتج عن وجود ضغوطات في الحياة كالعمل و الاستيقاظ الليلي لارضاع طفلك من المهم مراجعة طبيب اعصاب وذلك لاتمام الفحص السريري و التاكد من التشخيص
- E2 | qa_id=ahd5k_00780 | relation=صداع --SYMPTOM_OF--> الصداع التوتري: الصداع التوتري قد يظهر كصداع يختلف حدته
  Source question: لماذا اصحو من النوم يوميا بصداع يختلف حدته من خفيف إلى قوي جدا لدرجة ان عيناي تدمع من كثرة الصداع مع العلم بان عمري 29 سنة ولدي طفل عمره سنة...
  Source answer: قد يكون لديك نوع من الصداع يسمى بالصداع التوتري و هو ناتج عن وجود ضغوطات في الحياة كالعمل و الاستيقاظ الليلي لارضاع طفلك من المهم مراجعة طبيب اعصاب وذلك لاتمام الفحص السريري و التاكد من التشخيص
- E3 | qa_id=ahd5k_03242 | relation=ارتفاع ضغط الدم --TREATED_BY--> العقاقير: قد يعطى لك المهدئات لتقلصات العضلات والعقاقير من خلال الوريد (عن طريق الوريد) لعلاج ارتفاع ضغط الدم والإثارة والألم.
  Source question: هل لدغة العقرب أو مربعانية بعد 12ساعة من لدغة تبين أن لا توجد اعراض ك احمرار وانتفاخ أو حرارة تكون لدغة غير قاتلة
  Source answer: معظم لسعات العقرب لا تحتاج إلى علاج طبي. ولكن إذا كانت الأعراض شديدة ، فقد تحتاج إلى تلقي الرعاية في المستشفى. قد يعطى لك المهدئات لتقلصات العضلات والعقاقير من خلال الوريد (عن طريق الوريد) لعلاج ارتفاع ضغط الدم والإثارة والألم.
- E4 | qa_id=ahd5k_03242 | relation=العقاقير --TREATS--> ارتفاع ضغط الدم: قد يعطى لك المهدئات لتقلصات العضلات والعقاقير من خلال الوريد (عن طريق الوريد) لعلاج ارتفاع ضغط الدم والإثارة والألم.
  Source question: هل لدغة العقرب أو مربعانية بعد 12ساعة من لدغة تبين أن لا توجد اعراض ك احمرار وانتفاخ أو حرارة تكون لدغة غير قاتلة
  Source answer: معظم لسعات العقرب لا تحتاج إلى علاج طبي. ولكن إذا كانت الأعراض شديدة ، فقد تحتاج إلى تلقي الرعاية في المستشفى. قد يعطى لك المهدئات لتقلصات العضلات والعقاقير من خلال الوريد (عن طريق الوريد) لعلاج ارتفاع ضغط الدم والإثارة والألم.

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_118: ماهي علاجات حمى التهاب باطن القدم وباطن اليد وماهي الفحوصات للتاكد من اسباب هذا المرض؟

```text
User Question:
ماهي علاجات حمى التهاب باطن القدم وباطن اليد وماهي الفحوصات للتاكد من اسباب هذا المرض؟

Retrieved Entities:
- حمى (Symptom; match=exact; id=ent_symptom_018ebc11f6df)
- الفحوصات المخبرية (Test; match=alias; id=ent_test_c4ec2e232baf)

Retrieved Relations:
- [1] حمى عضة الجرذ --HAS_SYMPTOM--> حمى (score=0.777132; reliability=medium)
- [2] حمى عضة الفأر --HAS_SYMPTOM--> حمى (score=0.777132; reliability=medium)
- [3] حمى عضة الجرذون --HAS_SYMPTOM--> حمى (score=0.777132; reliability=medium)
- [4] حمى --SYMPTOM_OF--> حمى عضة الجرذ (score=0.776012; reliability=medium)
- [5] حمى --SYMPTOM_OF--> حمى عضة الفأر (score=0.776012; reliability=medium)
- [6] حمى --SYMPTOM_OF--> حمى عضة الجرذون (score=0.776012; reliability=medium)

Evidence Sentences:
- E1 | qa_id=ahd5k_01255 | relation=حمى عضة الجرذ --HAS_SYMPTOM--> حمى: حمى عضة الجرذ ، وحمى عضة الفأر
  Source question: ما هي اعراض عضة الجردون؟وكيف يتم لها الاسعافات الاولية؟وهل علاجها بسلسلة من الحقن؟
  Source answer: من أخطر العضات عضة الجرذون لأنها تسبب أمراضا خطيرة مثل حمى عضة الجرذ ، وحمى عضة الفأر والسودوكو ، وأهم أعراض العضة هي : ارتفاع درجة الحرارة ، ارتجاف ، هيجان ، أوجاع العضلات آلام المفاصل . وعلاجها يكون باعطاء المضادات الحيوية مثل البنسيلين والسيبروفلوكساسين وغيرها بعد استشارة الطبيب.
- E2 | qa_id=ahd5k_01255 | relation=حمى عضة الفأر --HAS_SYMPTOM--> حمى: حمى عضة الفأر
  Source question: ما هي اعراض عضة الجردون؟وكيف يتم لها الاسعافات الاولية؟وهل علاجها بسلسلة من الحقن؟
  Source answer: من أخطر العضات عضة الجرذون لأنها تسبب أمراضا خطيرة مثل حمى عضة الجرذ ، وحمى عضة الفأر والسودوكو ، وأهم أعراض العضة هي : ارتفاع درجة الحرارة ، ارتجاف ، هيجان ، أوجاع العضلات آلام المفاصل . وعلاجها يكون باعطاء المضادات الحيوية مثل البنسيلين والسيبروفلوكساسين وغيرها بعد استشارة الطبيب.
- E3 | qa_id=ahd5k_01255 | relation=حمى عضة الجرذون --HAS_SYMPTOM--> حمى: حمى عضة الجرذون
  Source question: ما هي اعراض عضة الجردون؟وكيف يتم لها الاسعافات الاولية؟وهل علاجها بسلسلة من الحقن؟
  Source answer: من أخطر العضات عضة الجرذون لأنها تسبب أمراضا خطيرة مثل حمى عضة الجرذ ، وحمى عضة الفأر والسودوكو ، وأهم أعراض العضة هي : ارتفاع درجة الحرارة ، ارتجاف ، هيجان ، أوجاع العضلات آلام المفاصل . وعلاجها يكون باعطاء المضادات الحيوية مثل البنسيلين والسيبروفلوكساسين وغيرها بعد استشارة الطبيب.
- E4 | qa_id=ahd5k_01255 | relation=حمى --SYMPTOM_OF--> حمى عضة الجرذ: حمى عضة الجرذ ، وحمى عضة الفأر
  Source question: ما هي اعراض عضة الجردون؟وكيف يتم لها الاسعافات الاولية؟وهل علاجها بسلسلة من الحقن؟
  Source answer: من أخطر العضات عضة الجرذون لأنها تسبب أمراضا خطيرة مثل حمى عضة الجرذ ، وحمى عضة الفأر والسودوكو ، وأهم أعراض العضة هي : ارتفاع درجة الحرارة ، ارتجاف ، هيجان ، أوجاع العضلات آلام المفاصل . وعلاجها يكون باعطاء المضادات الحيوية مثل البنسيلين والسيبروفلوكساسين وغيرها بعد استشارة الطبيب.
- E5 | qa_id=ahd5k_01255 | relation=حمى --SYMPTOM_OF--> حمى عضة الفأر: حمى عضة الفأر
  Source question: ما هي اعراض عضة الجردون؟وكيف يتم لها الاسعافات الاولية؟وهل علاجها بسلسلة من الحقن؟
  Source answer: من أخطر العضات عضة الجرذون لأنها تسبب أمراضا خطيرة مثل حمى عضة الجرذ ، وحمى عضة الفأر والسودوكو ، وأهم أعراض العضة هي : ارتفاع درجة الحرارة ، ارتجاف ، هيجان ، أوجاع العضلات آلام المفاصل . وعلاجها يكون باعطاء المضادات الحيوية مثل البنسيلين والسيبروفلوكساسين وغيرها بعد استشارة الطبيب.
- E6 | qa_id=ahd5k_01255 | relation=حمى --SYMPTOM_OF--> حمى عضة الجرذون: حمى عضة الجرذون
  Source question: ما هي اعراض عضة الجردون؟وكيف يتم لها الاسعافات الاولية؟وهل علاجها بسلسلة من الحقن؟
  Source answer: من أخطر العضات عضة الجرذون لأنها تسبب أمراضا خطيرة مثل حمى عضة الجرذ ، وحمى عضة الفأر والسودوكو ، وأهم أعراض العضة هي : ارتفاع درجة الحرارة ، ارتجاف ، هيجان ، أوجاع العضلات آلام المفاصل . وعلاجها يكون باعطاء المضادات الحيوية مثل البنسيلين والسيبروفلوكساسين وغيرها بعد استشارة الطبيب.

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_119: والدي وقع من الدرج قبل ثلالث ايام نلاحظ هناك زغللة في عينه اليمنى مع حول فيها تم قياسة مستوى السكر اليوم 200 اتمنى افادتي بهذا الامر هل له علاقة بالحلطة...

```text
User Question:
والدي وقع من الدرج قبل ثلالث ايام نلاحظ هناك زغللة في عينه اليمنى مع حول فيها تم قياسة مستوى السكر اليوم 200 اتمنى افادتي بهذا الامر هل له علاقة بالحلطة...

Retrieved Entities:
- سكر (DiseaseCondition; match=exact; id=ent_diseasecondition_4393a2bf88a6)

Retrieved Relations:
- [1] مرض السكري --HAS_SYMPTOM--> ضغط الدم (score=0.902855; reliability=strong)
- [2] مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (score=0.78813; reliability=medium)
- [3] التهاب --DIAGNOSED_BY--> تحاليل مخبرية (score=0.749896; reliability=limited)
- [4] تحاليل مخبرية --DIAGNOSES--> مرض السكري (score=0.32517; reliability=limited)
- [5] ضغط الدم --SYMPTOM_OF--> مرض السكري (score=0.319967; reliability=limited)
- [6] تحاليل مخبرية --DIAGNOSES--> التهاب (score=0.302296; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_01294 | relation=مرض السكري --HAS_SYMPTOM--> ضغط الدم: مرض السكري وضغط الدمز
  Source question: تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س
  Source answer: العمليات الجراحية اليوم لا يعيقها أي مرض إذا ما تمت السيطرة عليه بشكل جيد قبل وأثناء وبعد العمل الجراحي، فلا داعي للقلق
- E2 | qa_id=ahd5k_04912 | relation=مرض السكري --HAS_SYMPTOM--> ضغط الدم: مع العلم أن المريض يعاني من مرض السكر
  Source question: هل ضعف عضله القلب وضيق ثلاث شرايين في القلب لهم عمليه جراحيه مع العلم أن المريض يعاني من مرض السكر ام يبقى على العلاج ولو عمليه جراحيهوين تنصحونا نعملها وعاووزيين...
  Source answer: هذا يتطلب معرفة نسبة الضعف الموجود في العضلة القلبية ونسبة التضيق في الثلاثة شرايين المذكورة، كما أنه من الضروري معرفة الحالة الوظيفية لباقي أعضاء الجسم خاصة الكلى والجهاز التنفسي، والكبد وغيره، وفي جميع الأحوال في العادة تُعرض نتائج القثطرة على فريق طبي مُتخصص لتقييم كل هذه الأمور ومن ثم يتم اختيار الطريقة العلاجية التي تتناسب أكثر مع حالة المريض
- E3 | qa_id=ahd5k_01551 | relation=مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.
- E4 | qa_id=ahd5k_01551 | relation=التهاب --DIAGNOSED_BY--> تحاليل مخبرية: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.
- E5 | qa_id=ahd5k_01551 | relation=تحاليل مخبرية --DIAGNOSES--> مرض السكري: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.
- E6 | qa_id=ahd5k_04912 | relation=ضغط الدم --SYMPTOM_OF--> مرض السكري: مع العلم أن المريض يعاني من مرض السكر
  Source question: هل ضعف عضله القلب وضيق ثلاث شرايين في القلب لهم عمليه جراحيه مع العلم أن المريض يعاني من مرض السكر ام يبقى على العلاج ولو عمليه جراحيهوين تنصحونا نعملها وعاووزيين...
  Source answer: هذا يتطلب معرفة نسبة الضعف الموجود في العضلة القلبية ونسبة التضيق في الثلاثة شرايين المذكورة، كما أنه من الضروري معرفة الحالة الوظيفية لباقي أعضاء الجسم خاصة الكلى والجهاز التنفسي، والكبد وغيره، وفي جميع الأحوال في العادة تُعرض نتائج القثطرة على فريق طبي مُتخصص لتقييم كل هذه الأمور ومن ثم يتم اختيار الطريقة العلاجية التي تتناسب أكثر مع حالة المريض
- E7 | qa_id=ahd5k_01551 | relation=تحاليل مخبرية --DIAGNOSES--> التهاب: تحاليل مخبرية
  Source question: ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر
  Source answer: مضاره: ١- يؤدي إلى صعوبة التبول، وإفرازات منوية لاإرادية بعد التبول وكذلك الضعف الجنسي. ٢-زيادة السكر في الدم والتعرض لمرض السكري ٣-يقلل نسبة البروتين في الدم مما يؤثر على نمو الجسم ويسبب الهزال وضعف البنية لدى المتعاطين ٤-يسبب عسر الهضم ويؤدي إلي البواسير وفقدان الشهية والإمساك، وهو من أهم أعراض تعاطي القات. ٥-يؤدي إلى ازدياد حالات سرطانات الفم والفك. والقات يؤدي إلى الإدمان.

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_120: ماهي الاهمية الطبية للجلوكوز والفركتوز والجالكتوز؟

```text
User Question:
ماهي الاهمية الطبية للجلوكوز والفركتوز والجالكتوز؟

Retrieved Entities:
- الجلوكوز (Test; match=exact; id=ent_test_d990d9189fc6)
- الفركتوز (DiseaseCondition; match=exact; id=ent_diseasecondition_46faf93722a3)
- الجالكتوز (DiseaseCondition; match=exact; id=ent_diseasecondition_8e104f8ce212)

Retrieved Relations:
- [1] التهاب --HAS_SYMPTOM--> اختلال وظائف الكبد (score=0.820395; reliability=medium)
- [2] اختلال وظائف الكبد --SYMPTOM_OF--> التهاب (score=0.734795; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_01578 | relation=التهاب --HAS_SYMPTOM--> اختلال وظائف الكبد: التهاب في العين وفقدان حاسة الشم واختلال وظائف الكبد والكلى
  Source question: ماهي الاهمية الطبية للجلوكوز والفركتوز والجالكتوز؟
  Source answer: الجلاكتوز هو نوع من انواع السكر يدخل في تركيب الكثير من البروتينات والدهون في الخلايا اذا تم اضافة الجلوكوز له برابطة ثنائية ينج عندنا سكر اللاكتوز وهو من اهم مكونات الحليب الطبيعي الخلل في تمثيل السكر يؤدي الى امراض في العين وفقدان حاسة الشم واختلال وظائف الكبد والكلى الجلوكوز ويسمى ايضا سكر العنب اوسكر الذرة وهو المصدر الاساسي للطاقة داخل الخلية الفركتوز هو نوع اخر من السكر يكون مكونا لجدار الخلايا واي خلل في تمثيله يؤدي الي اختلال في وظائف الكبد والكلى
- E2 | qa_id=ahd5k_01578 | relation=اختلال وظائف الكبد --SYMPTOM_OF--> التهاب: التهاب في العين وفقدان حاسة الشم واختلال وظائف الكبد والكلى
  Source question: ماهي الاهمية الطبية للجلوكوز والفركتوز والجالكتوز؟
  Source answer: الجلاكتوز هو نوع من انواع السكر يدخل في تركيب الكثير من البروتينات والدهون في الخلايا اذا تم اضافة الجلوكوز له برابطة ثنائية ينج عندنا سكر اللاكتوز وهو من اهم مكونات الحليب الطبيعي الخلل في تمثيل السكر يؤدي الى امراض في العين وفقدان حاسة الشم واختلال وظائف الكبد والكلى الجلوكوز ويسمى ايضا سكر العنب اوسكر الذرة وهو المصدر الاساسي للطاقة داخل الخلية الفركتوز هو نوع اخر من السكر يكون مكونا لجدار الخلايا واي خلل في تمثيله يؤدي الي اختلال في وظائف الكبد والكلى

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_121: متى يلجأ الدكتور الي نزع عَصّب السن او الضرس

```text
User Question:
متى يلجأ الدكتور الي نزع عَصّب السن او الضرس

Retrieved Entities:
- الضرس (DiseaseCondition; match=exact; id=ent_diseasecondition_ee57bd84c53c)

Retrieved Relations:
- [1] حشو الأسنان --NOT_ASSOCIATED_WITH--> غمازة الوجه (score=0.429328; reliability=limited)
- [2] تخدير موضعي قوي --MAY_TEMPORARILY_AFFECT--> غمازة الوجه (score=0.429328; reliability=limited)
- [3] برد الأسنان --HAS_RISK--> حساسية الأسنان (score=0.420488; reliability=limited)
- [4] برد الأسنان --PROCEDURE_DURATION--> جلسة واحدة أو جلستان (score=0.420488; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_00484 | relation=حشو الأسنان --NOT_ASSOCIATED_WITH--> غمازة الوجه: لا توجد علاقة مرتبطة بين حشو الأسنان وغمازة الوجه حسب مصدر AHD.
  Source question: كان عندي ضرس متسوس في أعلى الفم و الدكتور عمل لي حشوة و عالج التسوس و لكن لاحظت اختفاء غمازة وجهي بعدها مُباشرةً ، ما السبب و هل مُمكن ترجع...
  Source answer: لاتوجد أي علاقة مرتبطة بين حشو الأسنان وغمازة الوجه، وجه المقاربة قد يكون فقط في حال تم تخدير المنطقة نفسها الي تقع بها الغمازة بمخدر قوي وكمية كبيرة، وان كانت هذه الحالة فعندها تزول خلال ٢٤-٤٨ ساعة.
- E2 | qa_id=ahd5k_00484 | relation=تخدير موضعي قوي --MAY_TEMPORARILY_AFFECT--> غمازة الوجه: إذا تم تخدير منطقة الغمازة بمخدر قوي وكمية كبيرة فقد تزول الحالة خلال 24-48 ساعة.
  Source question: كان عندي ضرس متسوس في أعلى الفم و الدكتور عمل لي حشوة و عالج التسوس و لكن لاحظت اختفاء غمازة وجهي بعدها مُباشرةً ، ما السبب و هل مُمكن ترجع...
  Source answer: لاتوجد أي علاقة مرتبطة بين حشو الأسنان وغمازة الوجه، وجه المقاربة قد يكون فقط في حال تم تخدير المنطقة نفسها الي تقع بها الغمازة بمخدر قوي وكمية كبيرة، وان كانت هذه الحالة فعندها تزول خلال ٢٤-٤٨ ساعة.
- E3 | qa_id=ahd5k_00828 | relation=برد الأسنان --HAS_RISK--> حساسية الأسنان: كثرة برد الأسنان قد تؤثر على الأسنان وتجعلها حساسة.
  Source question: برد الاسنان الاماميه ما ضرره وكم جلسه يحتاج
  Source answer: برد لمجرد البرد والتصغير في جلسه واحدة ولكن احذر من كثرة البرد حتي يؤثر علي الاسنان وتكون حساسه. ام لو برد للتركيب وعمل اسنان صناعيه ممكن جلسه او جلستين
- E4 | qa_id=ahd5k_00828 | relation=برد الأسنان --PROCEDURE_DURATION--> جلسة واحدة أو جلستان: برد الأسنان للتصغير قد يتم في جلسة واحدة، أما للتركيب وعمل أسنان صناعية فقد يحتاج جلسة أو جلستين.
  Source question: برد الاسنان الاماميه ما ضرره وكم جلسه يحتاج
  Source answer: برد لمجرد البرد والتصغير في جلسه واحدة ولكن احذر من كثرة البرد حتي يؤثر علي الاسنان وتكون حساسه. ام لو برد للتركيب وعمل اسنان صناعيه ممكن جلسه او جلستين

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_122: سلام لقد اجريت فحص الهرمون B-HCG ،و نتائج التحاليل كما يللي 3-4 اسبوع 9-130 4-5 اسبوع 75-2600 5-6 اسبوع 850-20800 7-8 اسبوع 4000-100200 7-12 اسبوع 11500-289000 12-16 اسبوع 18300-137000 و...

```text
User Question:
سلام لقد اجريت فحص الهرمون B-HCG ،و نتائج التحاليل كما يللي 3-4 اسبوع 9-130 4-5 اسبوع 75-2600 5-6 اسبوع 850-20800 7-8 اسبوع 4000-100200 7-12 اسبوع 11500-289000 12-16 اسبوع 18300-137000 و...

Retrieved Entities:
- فحص (Test; match=exact; id=ent_test_f1846b201f26)
- الهرمون (Test; match=exact; id=ent_test_234f794d532f)

Retrieved Relations:
- [1] صعوبة التنفس والإرهاق --INVESTIGATED_BY--> التاريخ المرضي والفحص السريري (score=0.533181; reliability=limited)
- [2] مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون (score=0.518347; reliability=limited)
- [3] الهرمون --DIAGNOSES--> مرض الغدة الدرقية (score=0.517227; reliability=limited)
- [4] نقص الصفيحات --DIAGNOSED_BY--> فحص نخاع العظم (score=0.511424; reliability=limited)
- [5] فحص نخاع العظم --DIAGNOSES--> نقص الصفيحات (score=0.425824; reliability=limited)
- [6] صعوبة التنفس والإرهاق --MAY_BE_ASSOCIATED_WITH--> التهاب تنفسي أو فقر دم أو اضطراب دموي أو دوراني (score=0.409181; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_00855 | relation=صعوبة التنفس والإرهاق --INVESTIGATED_BY--> التاريخ المرضي والفحص السريري: ينبغي معرفة التاريخ المرضي وإجراء فحص للكشف عن علامات سريرية تساعد في تحديد طبيعة الحالة.
  Source question: انا شاب عمري 25 سنه اصبحت اعاني من صعوبه في التنفس و الارهاق؟
  Source answer: لا داعي للقلق ولكن ينبغي معرفة تاريخك المرضي واجراء فحص للكشف عن أي علامات سريرية قد تكون موجودة لديك وتساعد في تحديد طبيعة الحالة , فهكذا أعراض ممكن أن تكون ناجمة عن التها ب في الجهاز التنفسي ويمكن تترافق مع فقر الدم أو اضطرابات دموية أو متعلقة بجهاز الدورة الدموية أو غير ذلك ، لذلك ننصحك بمعاودة طبيبك للوقوف على تفاصيل أكثر تسمح بالتشخيص ومن ثم اتخاذ السلوك الطبي الأمثل
- E2 | qa_id=ahd5k_00035 | relation=مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون: مستوى الهرمون في الدم
  Source question: انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟
  Source answer: علاج الغدة وجرعة العلاج تعتمد على مستوى الهرمون في الدم
- E3 | qa_id=ahd5k_00035 | relation=الهرمون --DIAGNOSES--> مرض الغدة الدرقية: مستوى الهرمون في الدم
  Source question: انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟
  Source answer: علاج الغدة وجرعة العلاج تعتمد على مستوى الهرمون في الدم
- E4 | qa_id=ahd5k_00313 | relation=نقص الصفيحات --DIAGNOSED_BY--> فحص نخاع العظم: فحص نخاع العظم مرتبط بتشخيص نقص الصفيحات
  Source question: هل يوجد علاقة بين انخفاض الصفيحات الدموية 122/ وارتفاع خضاب الدم / 16.8
  Source answer: يجب التأكد من blood smear فلم صورة الدم للتأكد من نقص الصفيحات بهذه الافتراض يجب اجراء فحص نخاع العظم
- E5 | qa_id=ahd5k_00313 | relation=فحص نخاع العظم --DIAGNOSES--> نقص الصفيحات: فحص نخاع العظم مرتبط بتشخيص نقص الصفيحات
  Source question: هل يوجد علاقة بين انخفاض الصفيحات الدموية 122/ وارتفاع خضاب الدم / 16.8
  Source answer: يجب التأكد من blood smear فلم صورة الدم للتأكد من نقص الصفيحات بهذه الافتراض يجب اجراء فحص نخاع العظم
- E6 | qa_id=ahd5k_00855 | relation=صعوبة التنفس والإرهاق --MAY_BE_ASSOCIATED_WITH--> التهاب تنفسي أو فقر دم أو اضطراب دموي أو دوراني: صعوبة التنفس والإرهاق قد تكون ناجمة عن التهاب في الجهاز التنفسي أو فقر الدم أو اضطرابات دموية أو متعلقة بجهاز الدورة الدموية.
  Source question: انا شاب عمري 25 سنه اصبحت اعاني من صعوبه في التنفس و الارهاق؟
  Source answer: لا داعي للقلق ولكن ينبغي معرفة تاريخك المرضي واجراء فحص للكشف عن أي علامات سريرية قد تكون موجودة لديك وتساعد في تحديد طبيعة الحالة , فهكذا أعراض ممكن أن تكون ناجمة عن التها ب في الجهاز التنفسي ويمكن تترافق مع فقر الدم أو اضطرابات دموية أو متعلقة بجهاز الدورة الدموية أو غير ذلك ، لذلك ننصحك بمعاودة طبيبك للوقوف على تفاصيل أكثر تسمح بالتشخيص ومن ثم اتخاذ السلوك الطبي الأمثل

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_123: لسلام عليكم ممكن تساعدوني ابني عملتله تطعيم سنة ونص اليوم هو يعاني من ارتفاع الحرارة ومايقدر يحرك رجلو وحتى يوقف وهو كتير البكاء كيف اتعامل معاه كيف اخفف من الم...

```text
User Question:
لسلام عليكم ممكن تساعدوني ابني عملتله تطعيم سنة ونص اليوم هو يعاني من ارتفاع الحرارة ومايقدر يحرك رجلو وحتى يوقف وهو كتير البكاء كيف اتعامل معاه كيف اخفف من الم...

Retrieved Entities:
- تطعيم (Treatment; match=exact; id=ent_treatment_026f10d47b4b)

Retrieved Relations:
- [1] حمى --TREATED_BY--> خافض حراره (score=0.491956; reliability=limited)
- [2] حصى الكلى --TREATED_BY--> الإكثار من السوائل والتقييم الطبي (score=0.415714; reliability=limited)
- [3] خافض حراره --TREATS--> حمى (score=0.406356; reliability=limited)
- [4] النقص الشديد للصفائح --TREATED_BY--> الروتيكسيماب (score=0.393668; reliability=limited)
- [5] الروتيكسيماب --TREATS--> النقص الشديد للصفائح (score=0.308068; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_01611 | relation=حمى --TREATED_BY--> خافض حراره: المفروض ان تزول هذه الاعراض خلال 48 ساعة وعليكي استخدام خافض حراره ومسكن للالم بعد تطعيم
  Source question: لسلام عليكم ممكن تساعدوني ابني عملتله تطعيم سنة ونص اليوم هو يعاني من ارتفاع الحرارة ومايقدر يحرك رجلو وحتى يوقف وهو كتير البكاء كيف اتعامل معاه كيف اخفف من الم...
  Source answer: من الطبيعي ان يصاحب هذا المطعوم حراره والم في مكان المطعوم والمفروض ان تزول هذه الاعراض خلال 48 ساعة وعليكي استخدام خافض حراره ومسكن للالم .
- E2 | qa_id=ahd5k_00012 | relation=حصى الكلى --TREATED_BY--> الإكثار من السوائل والتقييم الطبي: التخلص من الحصى يبدأ بدراستها لمعرفة مكانها وحجمها وطبيعتها ثم يقرر الطبيب كيفية التخلص منها.
  Source question: السلام عليكم اناعمري 22 سنة واعاني من القولون العصبي ولدي توسع بالكليتين بسبب وجود الحصى كيف يمكنني التخلص من الحصى ومشاكل القولون
  Source answer: التخلص من الحصى يكون اولا بدراستها لمعرفة مكانها وخجمها وطبيعتها وبعد ذلك ممكن للطبيب ان يقرركيفية التخلص منها اما القولون العصبي فبأمكانك البحث في موقعنا الطبي عن ذلك وستجد كتابات عديدة وقيمة
- E3 | qa_id=ahd5k_01611 | relation=خافض حراره --TREATS--> حمى: المفروض ان تزول هذه الاعراض خلال 48 ساعة وعليكي استخدام خافض حراره ومسكن للالم بعد تطعيم
  Source question: لسلام عليكم ممكن تساعدوني ابني عملتله تطعيم سنة ونص اليوم هو يعاني من ارتفاع الحرارة ومايقدر يحرك رجلو وحتى يوقف وهو كتير البكاء كيف اتعامل معاه كيف اخفف من الم...
  Source answer: من الطبيعي ان يصاحب هذا المطعوم حراره والم في مكان المطعوم والمفروض ان تزول هذه الاعراض خلال 48 ساعة وعليكي استخدام خافض حراره ومسكن للالم .
- E4 | qa_id=ahd5k_00203 | relation=النقص الشديد للصفائح --TREATED_BY--> الروتيكسيماب: الروتيكسيماب يفيده في علاج النقص الشديد للصفائح
  Source question: ابني عمره ١٠سنه يعاني من نقص الصفائح itpتم اعطائه ivigمرتين وتم اعطائه كرتزون وحاليا اضيف له علاج الروتيكسيماب اول جرعه ونستمر عليها لمده شهر كل اسبوع مره هل الروتكسيماب يفيده
  Source answer: نعم مفيد لة ويجب الاستمرار فى العلاج و متابعة الطبيب المعالج
- E5 | qa_id=ahd5k_00203 | relation=الروتيكسيماب --TREATS--> النقص الشديد للصفائح: الروتيكسيماب يفيده في علاج النقص الشديد للصفائح
  Source question: ابني عمره ١٠سنه يعاني من نقص الصفائح itpتم اعطائه ivigمرتين وتم اعطائه كرتزون وحاليا اضيف له علاج الروتيكسيماب اول جرعه ونستمر عليها لمده شهر كل اسبوع مره هل الروتكسيماب يفيده
  Source answer: نعم مفيد لة ويجب الاستمرار فى العلاج و متابعة الطبيب المعالج

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_124: هل زيت نبات الميرمية له آثار جانبية عند تناوله بشكل 3 كبسولات قبل الطعام للتخلص من افراز البرولاكتين المفرز والناتج عن ورم حميد في الغدة النخامية . .

```text
User Question:
هل زيت نبات الميرمية له آثار جانبية عند تناوله بشكل 3 كبسولات قبل الطعام للتخلص من افراز البرولاكتين المفرز والناتج عن ورم حميد في الغدة النخامية . .

Retrieved Entities:
- الميرمية (Treatment; match=exact; id=ent_treatment_b792fc31b8bb)
- الطعام (Treatment; match=exact; id=ent_treatment_60ce765ad441)
- الغدة الدرقية (DiseaseCondition; match=alias; id=supp_ent_thyroid)

Retrieved Relations:
- [1] الدورة الشهرية --TREATED_BY--> الميرمية (score=0.436585; reliability=limited)
- [2] الميرمية --TREATS--> الدورة الشهرية (score=0.435465; reliability=limited)
- [3] مرض الغدة الدرقية --TREATED_BY--> التروكسين (score=0.413108; reliability=limited)
- [4] مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون (score=0.413108; reliability=limited)
- [5] الجوع --TREATED_BY--> الطعام (score=0.401897; reliability=limited)
- [6] الطعام --TREATS--> الجوع (score=0.400777; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_04015 | relation=الدورة الشهرية --TREATED_BY--> الميرمية: الميرمية
  Source question: ماهى الاعشاب التي تساعد على نزول الطمث حيت انوما تجيني الدورة الا بالدواء فقط.شكرا
  Source answer: من الاعشاب التي قد تساعد على حل المشكلة وتنظيم الدورة الشهرية وهي طبعا لا تغني عن الدواء وعلاج السبب الاساسي لعدم انتظام الدورة ، نذكر: اكليل الجبل، الميرمية، البقدونس، حشيشة الملاك، البردقوش، القرفة، الزنجبيل، والكرفس.
- E2 | qa_id=ahd5k_04015 | relation=الميرمية --TREATS--> الدورة الشهرية: الميرمية
  Source question: ماهى الاعشاب التي تساعد على نزول الطمث حيت انوما تجيني الدورة الا بالدواء فقط.شكرا
  Source answer: من الاعشاب التي قد تساعد على حل المشكلة وتنظيم الدورة الشهرية وهي طبعا لا تغني عن الدواء وعلاج السبب الاساسي لعدم انتظام الدورة ، نذكر: اكليل الجبل، الميرمية، البقدونس، حشيشة الملاك، البردقوش، القرفة، الزنجبيل، والكرفس.
- E3 | qa_id=ahd5k_00035 | relation=مرض الغدة الدرقية --TREATED_BY--> التروكسين: اخذ التروكسين
  Source question: انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟
  Source answer: علاج الغدة وجرعة العلاج تعتمد على مستوى الهرمون في الدم
- E4 | qa_id=ahd5k_00035 | relation=مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون: مستوى الهرمون في الدم
  Source question: انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟
  Source answer: علاج الغدة وجرعة العلاج تعتمد على مستوى الهرمون في الدم
- E5 | qa_id=ahd5k_01128 | relation=الجوع --TREATED_BY--> الطعام: الطعام
  Source question: سبب استيقاظ الطفل اثناء الليل ونومه مده طويله خلال النهار ؟
  Source answer: ينام اكثر الاطفال الرضع عند شعورهم بالشبع خلال الاشهر الاولى ويعدود الطفل الرضيع ليستيقظ عند شعوره بالجوع ولكن يجب البدء بتعليم الطفل حتى خلال اشهره الاولى ان النهار هو للطعام واللعب والليل هو للنوم وعندما يصل وزن الطفل الرضيع الى 6 او 7 كغ اي بعد الشهر الثالث الى الرابع يبدا بالنوم لساعات متواصلة في الليل لان سعة معدة الطفل تكفي ليشعر الطفل بالشبع لعدة ساعات
- E6 | qa_id=ahd5k_01128 | relation=الطعام --TREATS--> الجوع: الطعام
  Source question: سبب استيقاظ الطفل اثناء الليل ونومه مده طويله خلال النهار ؟
  Source answer: ينام اكثر الاطفال الرضع عند شعورهم بالشبع خلال الاشهر الاولى ويعدود الطفل الرضيع ليستيقظ عند شعوره بالجوع ولكن يجب البدء بتعليم الطفل حتى خلال اشهره الاولى ان النهار هو للطعام واللعب والليل هو للنوم وعندما يصل وزن الطفل الرضيع الى 6 او 7 كغ اي بعد الشهر الثالث الى الرابع يبدا بالنوم لساعات متواصلة في الليل لان سعة معدة الطفل تكفي ليشعر الطفل بالشبع لعدة ساعات

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```

## trial_query_125: عندي الم في منطقه البطن مع الم بصدر جهه اليمين الى الرقبه وماقدرت اعرف تفسير الالم ذا من ايش او سببه مع وجود احيان ضيق بالتنفس ،،،، افيدوني

```text
User Question:
عندي الم في منطقه البطن مع الم بصدر جهه اليمين الى الرقبه وماقدرت اعرف تفسير الالم ذا من ايش او سببه مع وجود احيان ضيق بالتنفس ،،،، افيدوني

Retrieved Entities:
- الالم (Symptom; match=exact; id=ent_symptom_ad0da68fc73f)

Retrieved Relations:
- [1] ارتياف دعب \u0627لديم --HAS_SYMPTOM--> الالم (score=0.774655; reliability=medium)
- [2] الالم --SYMPTOM_OF--> ارتياف دعب \u0627لديم (score=0.773535; reliability=medium)
- [3] فقر الدم --HAS_SYMPTOM--> الم المعدجة (score=0.755915; reliability=medium)
- [4] الم المعدجة --SYMPTOM_OF--> فقر الدم (score=0.670315; reliability=limited)
- [5] الجلد المترهل --TREATED_BY--> الجراحة التجميلية (score=0.405299; reliability=limited)
- [6] الم المعدجة --INVESTIGATED_BY--> فحص الجرثومة الحلزونية (score=0.393915; reliability=limited)

Evidence Sentences:
- E1 | qa_id=ahd5k_03738 | relation=ارتياف دعب \u0627لديم --HAS_SYMPTOM--> الالم: الالم الدي الديم الديم الديم
  Source question: منذ فتره اشعر بألم فى عضله الصدر وليس القفص الصدرى وهذا عند الضغط عليها اريد ان اعرف ما السبب؟
  Source answer: الالم الذي يحدث عند الضغط على عضلة الصدر دليل وجود الالم في العضلة نفسها ربما نتيجة تشنج ما او جهد ما قمت به والافضل في هذه الحالة ان تريح هذه العضلة ولا تقوم بمجهود علما بان احيانا حتى السعال يسبب الم في عضلة الصدر
- E2 | qa_id=ahd5k_03738 | relation=الالم --SYMPTOM_OF--> ارتياف دعب \u0627لديم: الالم الدي الديم الديم الديم
  Source question: منذ فتره اشعر بألم فى عضله الصدر وليس القفص الصدرى وهذا عند الضغط عليها اريد ان اعرف ما السبب؟
  Source answer: الالم الذي يحدث عند الضغط على عضلة الصدر دليل وجود الالم في العضلة نفسها ربما نتيجة تشنج ما او جهد ما قمت به والافضل في هذه الحالة ان تريح هذه العضلة ولا تقوم بمجهود علما بان احيانا حتى السعال يسبب الم في عضلة الصدر
- E3 | qa_id=ahd5k_02292 | relation=فقر الدم --HAS_SYMPTOM--> الم المعدجة: نقص في الدم مع الالم في المعده
  Source question: والدتي تعاني من نقص في الدم مع الالم في المعده
  Source answer: الم المعدجة يجب معرفة سببه وذل بعمل دراسة للمعدة ولنبدأ بفحص الجرثومة الحلزونية ، وربما سنحتاج لاحقا لمنظار للمعدة اما نقص الدم فهذ يجب توضيحة بشكل جيد ودراسته لمعرفة السبب وعلاجه
- E4 | qa_id=ahd5k_02292 | relation=الم المعدجة --SYMPTOM_OF--> فقر الدم: نقص في الدم مع الالم في المعده
  Source question: والدتي تعاني من نقص في الدم مع الالم في المعده
  Source answer: الم المعدجة يجب معرفة سببه وذل بعمل دراسة للمعدة ولنبدأ بفحص الجرثومة الحلزونية ، وربما سنحتاج لاحقا لمنظار للمعدة اما نقص الدم فهذ يجب توضيحة بشكل جيد ودراسته لمعرفة السبب وعلاجه
- E5 | qa_id=ahd5k_01190 | relation=الجلد المترهل --TREATED_BY--> الجراحة التجميلية: يمكن شده بممارسة الرياضة أو بالجراحة التجميلية
  Source question: كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟
  Source answer: يمكن شده بممارسة الرياضة أو بالجراحة التجميلية.راجعي اختصاصي تجميل.
- E6 | qa_id=ahd5k_02292 | relation=الم المعدجة --INVESTIGATED_BY--> فحص الجرثومة الحلزونية: فحص الجرثومة الحلزونية
  Source question: والدتي تعاني من نقص في الدم مع الالم في المعده
  Source answer: الم المعدجة يجب معرفة سببه وذل بعمل دراسة للمعدة ولنبدأ بفحص الجرثومة الحلزونية ، وربما سنحتاج لاحقا لمنظار للمعدة اما نقص الدم فهذ يجب توضيحة بشكل جيد ودراسته لمعرفة السبب وعلاجه

Instructions:
- Answer in Arabic.
- Answer ONLY using the provided evidence.
- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.
- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.
- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.
- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.
- Mention uncertainty when relation reliability is limited.
- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.
- Final answer must be composed only from supported claims.
- Return valid JSON only using the requested Step 12 schema.
```
