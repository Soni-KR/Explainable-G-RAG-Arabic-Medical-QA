# Trial Graph v1 Step 9A Semantic Retrieval Report

This is the semantic retrieval layer over Step 6 MiniLM embeddings, using Step 8 query understanding for exact-entity and expansion boosts.

## Model

- Embedding model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Embedded documents searched: 2145

## Retrieval Scoring

- Base score: cosine similarity because embeddings are normalized.
- Hard detected entity boost: exact/alias entity matches from Step 8.
- Soft candidate boost: expansion/semantic candidate entities from Step 8.
- Results are still semantic retrieval only; graph traversal comes later in Step 9C.

## Query Results

### ما علاج حساسية الصدر مع السعال والبلغم؟

**Top entity docs**
- `0.932699` حساسية الصدر (hard_entity_seed; raw=0.582699, boost=0.35)
- `0.921756` حساسية (hard_entity_seed; raw=0.671756, boost=0.25)
- `0.887763` سعال (hard_entity_seed; raw=0.537763, boost=0.35)
- `0.871377` بلغم (hard_entity_seed; raw=0.521377, boost=0.35)
- `0.7082` ربو (semantic_candidate_entity; raw=0.5882, boost=0.12)

**Top evidence docs**
- `0.789586` حساسية (evidence_for_hard_entity_seed; raw=0.669586, boost=0.12)
- `0.7838` حساسية الصدر (evidence_for_hard_entity_seed; raw=0.6038, boost=0.18)
- `0.773599` حساسية (evidence_for_hard_entity_seed; raw=0.653599, boost=0.12)
- `0.771701` حساسية (evidence_for_hard_entity_seed; raw=0.651701, boost=0.12)
- `0.769452` حساسية (evidence_for_hard_entity_seed; raw=0.649452, boost=0.12)

**Top qa docs**
- `0.537016` السلام عليكم.انا مصاب بفيروس س4 واخذتعﻻج بيغاسي ولم اشفى.جرى عندي التهاب بالمجاري البولية واخت دواء اموكسلين مع مسكن من  (semantic_similarity_only; raw=0.537016, boost=0.0)
- `0.534084` تناول طفلي حبه امادول tramadol كيف اسعفه ؟ (semantic_similarity_only; raw=0.534084, boost=0.0)
- `0.534043` اقصد الطبيب المختص مقدمة الراس والدماغ هل اسمه العلمي هو طبيب الجهاز العصبي ؟ وسؤالي التاني هل تشنجات التي تحدث في الراس (semantic_similarity_only; raw=0.534043, boost=0.0)
- `0.53337` طفلتي تتحسس من الجلوتين وعمرها سنة ونصف هل توجد أدوية تساعد على الشفاء من هذا المرض ام لا ؟؟ (semantic_similarity_only; raw=0.53337, boost=0.0)
- `0.533261` ابنتي معاها حساسية معينة لبعض الاطعمة وعمرها سنتان هل تختفي بعد تخطيها 3 سنوات (semantic_similarity_only; raw=0.533261, boost=0.0)

### عندي كحة وبلغم هل هذا ربو؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.930806` بلغم (hard_entity_seed; raw=0.580806, boost=0.35)
- `0.926703` ربو (hard_entity_seed; raw=0.576703, boost=0.35)
- `0.820907` سعال (semantic_candidate_entity; raw=0.700907, boost=0.12)
- `0.673046` حساسية الصدر (semantic_similarity_only; raw=0.673046, boost=0.0)
- `0.594882` الضيق التنفسي (semantic_similarity_only; raw=0.594882, boost=0.0)

**Top evidence docs**
- `0.862495` سعال (evidence_for_semantic_candidate_entity; raw=0.782495, boost=0.08)
- `0.848933` بلغم (evidence_for_hard_entity_seed; raw=0.668933, boost=0.18)
- `0.834936` سعال (evidence_for_semantic_candidate_entity; raw=0.754936, boost=0.08)
- `0.831773` سعال (evidence_for_semantic_candidate_entity; raw=0.751773, boost=0.08)
- `0.787086` التهاب (semantic_similarity_only; raw=0.787086, boost=0.0)

**Top qa docs**
- `0.535371` اعاني من حساسية في الصدر وضيق في التنفس وسعال وقئ صباحا (semantic_similarity_only; raw=0.535371, boost=0.0)
- `0.509605` لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام  (semantic_similarity_only; raw=0.509605, boost=0.0)
- `0.489417` اشعر باعراض لم اشعر بها من قبل فالبارحة احسست بوخز في قلبي و اليوم عندما اتنفس اتنفس بصعوبة مع الم شديد في الصدر من جهة  (semantic_similarity_only; raw=0.489417, boost=0.0)
- `0.48429` لمدا كلما انزعجت من شخص ما أشعر بدوار ودقات سريعة للقلب وشعور براسي تقيل تم يغمى علي دون الغياب عن الوعي فما تشخيصكم لهد (semantic_similarity_only; raw=0.48429, boost=0.0)
- `0.474131` هل بنسلين يسبب إلتهاب المعدة للأطفال (semantic_similarity_only; raw=0.474131, boost=0.0)

### ما التحاليل المناسبة لفقر الدم؟

**Top entity docs**
- `0.84457` فقر الدم (hard_entity_seed; raw=0.49457, boost=0.35)
- `0.686992` الفحوصات المخبرية (semantic_similarity_only; raw=0.686992, boost=0.0)
- `0.649377` القسطرة التشخيصية (semantic_similarity_only; raw=0.649377, boost=0.0)
- `0.642186` خصائي الاطفال (semantic_similarity_only; raw=0.642186, boost=0.0)
- `0.64081` تحليل الحساسية (semantic_similarity_only; raw=0.64081, boost=0.0)

**Top evidence docs**
- `0.768967` فقر الدم (evidence_for_hard_entity_seed; raw=0.588967, boost=0.18)
- `0.767173` فقر الدم (evidence_for_hard_entity_seed; raw=0.587173, boost=0.18)
- `0.752972` فقر الدم (evidence_for_hard_entity_seed; raw=0.572972, boost=0.18)
- `0.74704` فقر الدم (evidence_for_hard_entity_seed; raw=0.56704, boost=0.18)
- `0.731532` فقر الدم (evidence_for_hard_entity_seed; raw=0.551532, boost=0.18)

**Top qa docs**
- `0.425882` هل من الممكن تشخيص الحالة اذا تم ارسال فحوصات الاشعة لحالة مرضية من خلال موقعكم (semantic_similarity_only; raw=0.425882, boost=0.0)
- `0.414832` مند يومين لحظت الم بسيط في القضيب الدكري والم عند التبول بسيط ومع مرور يومين ازدادة عدي حكة في القضيب مرة مرة وتختفي عند (semantic_similarity_only; raw=0.414832, boost=0.0)
- `0.410865` اقصد الطبيب المختص مقدمة الراس والدماغ هل اسمه العلمي هو طبيب الجهاز العصبي ؟ وسؤالي التاني هل تشنجات التي تحدث في الراس (semantic_similarity_only; raw=0.410865, boost=0.0)
- `0.40903` لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام  (semantic_similarity_only; raw=0.40903, boost=0.0)
- `0.388577` بنت اخي لديها انتفاخ في الغدد الليمفاويةمما جعل لها تورما اسفل اللوزتين وخلف الركبه ولديها فتور في الجسم مع العلم ان عمر (semantic_similarity_only; raw=0.388577, boost=0.0)

### ما أسباب صداع مع دوخة؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.954169` صداع (hard_entity_seed; raw=0.604169, boost=0.35)
- `0.846904` صداع التوتر (hard_entity_seed; raw=0.596904, boost=0.25)
- `0.817638` دوخة (hard_entity_seed; raw=0.467638, boost=0.35)
- `0.639445` التهاب السحايا (semantic_similarity_only; raw=0.639445, boost=0.0)
- `0.62302` التهاب الجيوب الأنفية (semantic_similarity_only; raw=0.62302, boost=0.0)

**Top evidence docs**
- `0.933344` صداع (evidence_for_hard_entity_seed; raw=0.753344, boost=0.18)
- `0.910849` صداع (evidence_for_hard_entity_seed; raw=0.730849, boost=0.18)
- `0.901263` صداع (evidence_for_hard_entity_seed; raw=0.721263, boost=0.18)
- `0.857922` صداع (evidence_for_hard_entity_seed; raw=0.677922, boost=0.18)
- `0.851267` صداع (evidence_for_hard_entity_seed; raw=0.671267, boost=0.18)

**Top qa docs**
- `0.487271` لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام  (semantic_similarity_only; raw=0.487271, boost=0.0)
- `0.468466` اختي عمرها 17 ومنذ سنتين تقريبا اصبحت تصاب بالام حادة في الراس وعندما تصاب بها تشعر بنض سريع وقوي جدا في الشرايين الموجو (semantic_similarity_only; raw=0.468466, boost=0.0)
- `0.465557` لماذا اصحو من النوم يوميا بصداع يختلف حدته من خفيف إلى قوي جدا لدرجة ان عيناي تدمع من كثرة الصداع مع العلم بان عمري 29 س (semantic_similarity_only; raw=0.465557, boost=0.0)
- `0.444016` أخدت كليرا و أحس بان صدري ينتفخ و بيوجعني رأس كتير شو هو سبب ؟ (semantic_similarity_only; raw=0.444016, boost=0.0)
- `0.441508` كيف اتصرف مع انسان لدغته أم اربعه واربعين (semantic_similarity_only; raw=0.441508, boost=0.0)

### ما علاج الجلطة الدماغية؟

**Top entity docs**
- `0.817988` الجلطة الدماغية (hard_entity_seed; raw=0.467988, boost=0.35)
- `0.695991` الاندرال (semantic_similarity_only; raw=0.695991, boost=0.0)
- `0.693278` استئصال الإصبع السادسة (semantic_similarity_only; raw=0.693278, boost=0.0)
- `0.68811` المركز العلاجي (semantic_similarity_only; raw=0.68811, boost=0.0)
- `0.682353` أدوية بالفم (semantic_similarity_only; raw=0.682353, boost=0.0)

**Top evidence docs**
- `0.630443` قلق (semantic_similarity_only; raw=0.630443, boost=0.0)
- `0.622356` دواء تلفاست أ سيرين (semantic_similarity_only; raw=0.622356, boost=0.0)
- `0.594745` التهاب (semantic_similarity_only; raw=0.594745, boost=0.0)
- `0.592861` المراجعة الطبية (semantic_similarity_only; raw=0.592861, boost=0.0)
- `0.590627` التهاب (semantic_similarity_only; raw=0.590627, boost=0.0)

**Top qa docs**
- `0.479341` منذ دخول الصيف وانا اعاني من ظهور حبوب في وجهي اريد العلاج من خلال الطب البديل وشكرا لكم على مساعدتكم (semantic_similarity_only; raw=0.479341, boost=0.0)
- `0.467561` كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟ (semantic_similarity_only; raw=0.467561, boost=0.0)
- `0.467088` كيف اتصرف مع انسان لدغته أم اربعه واربعين (semantic_similarity_only; raw=0.467088, boost=0.0)
- `0.465444` انا ابتلعت دبوس امس ولا اشعر ببلعه واعاني بوجع صدري كيف اعمل (semantic_similarity_only; raw=0.465444, boost=0.0)
- `0.465051` سقطت ابنتي اعلى راسها فظهر لها انتفاخ خلف الاذن والم شديد في الرقبه ولاتستطيع تحريكها (semantic_similarity_only; raw=0.465051, boost=0.0)

### هل ضيق التنفس من أعراض الحساسية؟

**Top entity docs**
- `0.987293` حساسية (hard_entity_seed; raw=0.637293, boost=0.35)
- `0.827798` حساسية الصدر (hard_entity_seed; raw=0.577798, boost=0.25)
- `0.809447` ضيق تنفس (hard_entity_seed; raw=0.559447, boost=0.25)
- `0.756434` الحساسية على الوسط التَبايُنِيّ (semantic_similarity_only; raw=0.756434, boost=0.0)
- `0.711827` الحادِث الوِعائيٌّ الدِمَاغِيّ (semantic_similarity_only; raw=0.711827, boost=0.0)

**Top evidence docs**
- `0.884045` حساسية (evidence_for_hard_entity_seed; raw=0.704045, boost=0.18)
- `0.871296` حساسية (evidence_for_hard_entity_seed; raw=0.691296, boost=0.18)
- `0.870015` حساسية (evidence_for_hard_entity_seed; raw=0.690015, boost=0.18)
- `0.866865` حساسية (evidence_for_hard_entity_seed; raw=0.686865, boost=0.18)
- `0.863651` حساسية (evidence_for_hard_entity_seed; raw=0.683651, boost=0.18)

**Top qa docs**
- `0.567613` لمدا كلما انزعجت من شخص ما أشعر بدوار ودقات سريعة للقلب وشعور براسي تقيل تم يغمى علي دون الغياب عن الوعي فما تشخيصكم لهد (semantic_similarity_only; raw=0.567613, boost=0.0)
- `0.558058` سوألي هناك فتاه تشعر بحراره شديده في جسمها الخارجي وقليل جدا من داخل جسمها ولاترتاح الا بالاغتسال ومستمر الحال معها قراب (semantic_similarity_only; raw=0.558058, boost=0.0)
- `0.53792` ابنتي معاها حساسية معينة لبعض الاطعمة وعمرها سنتان هل تختفي بعد تخطيها 3 سنوات (semantic_similarity_only; raw=0.53792, boost=0.0)
- `0.536066` نتيجة الحساسة عندي هي IMMUNOLOGIE ige 183 UI/ml ماذا أفعل. و هل هي خطيرة (semantic_similarity_only; raw=0.536066, boost=0.0)
- `0.532391` لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام  (semantic_similarity_only; raw=0.532391, boost=0.0)

### ما الفحوصات المطلوبة للسكري؟

**Top entity docs**
- `0.910539` الفحوصات المخبرية (hard_entity_seed; raw=0.660539, boost=0.25)
- `0.806946` سكري (hard_entity_seed; raw=0.456946, boost=0.35)
- `0.634953` القسطرة التشخيصية (semantic_similarity_only; raw=0.634953, boost=0.0)
- `0.633265` خصائي الاطفال (semantic_similarity_only; raw=0.633265, boost=0.0)
- `0.631499` تحليل الحساسية (semantic_similarity_only; raw=0.631499, boost=0.0)

**Top evidence docs**
- `0.701555` سكري (evidence_for_hard_entity_seed; raw=0.521555, boost=0.18)
- `0.69058` سكري (evidence_for_hard_entity_seed; raw=0.51058, boost=0.18)
- `0.673773` القسطرة التشخيصية (semantic_similarity_only; raw=0.673773, boost=0.0)
- `0.648236` التهاب (semantic_similarity_only; raw=0.648236, boost=0.0)
- `0.634831` فحص سريري (semantic_similarity_only; raw=0.634831, boost=0.0)

**Top qa docs**
- `0.463934` اقصد الطبيب المختص مقدمة الراس والدماغ هل اسمه العلمي هو طبيب الجهاز العصبي ؟ وسؤالي التاني هل تشنجات التي تحدث في الراس (semantic_similarity_only; raw=0.463934, boost=0.0)
- `0.446452` لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام  (semantic_similarity_only; raw=0.446452, boost=0.0)
- `0.436386` هل من الممكن تشخيص الحالة اذا تم ارسال فحوصات الاشعة لحالة مرضية من خلال موقعكم (semantic_similarity_only; raw=0.436386, boost=0.0)
- `0.436169` بنت اخي لديها انتفاخ في الغدد الليمفاويةمما جعل لها تورما اسفل اللوزتين وخلف الركبه ولديها فتور في الجسم مع العلم ان عمر (semantic_similarity_only; raw=0.436169, boost=0.0)
- `0.43083` مند يومين لحظت الم بسيط في القضيب الدكري والم عند التبول بسيط ومع مرور يومين ازدادة عدي حكة في القضيب مرة مرة وتختفي عند (semantic_similarity_only; raw=0.43083, boost=0.0)

### ما علاج التهاب المفاصل وألم المفاصل؟

**Top entity docs**
- `0.943212` ألم المفاصل (hard_entity_seed; raw=0.593212, boost=0.35)
- `0.857766` التهاب المفاصل (hard_entity_seed; raw=0.507766, boost=0.35)
- `0.713311` تجنب المنتجات التي تحوي جلوتين (semantic_similarity_only; raw=0.713311, boost=0.0)
- `0.707215` الجيب اللثوي (semantic_similarity_only; raw=0.707215, boost=0.0)
- `0.697944` اللحوم (semantic_similarity_only; raw=0.697944, boost=0.0)

**Top evidence docs**
- `0.754338` ألم المفاصل (evidence_for_hard_entity_seed; raw=0.574338, boost=0.18)
- `0.661465` التهاب المفاصل (evidence_for_hard_entity_seed; raw=0.481465, boost=0.18)
- `0.656208` التهاب المفاصل (evidence_for_hard_entity_seed; raw=0.476208, boost=0.18)
- `0.637074` ألم المفاصل (evidence_for_hard_entity_seed; raw=0.457074, boost=0.18)
- `0.633467` التهاب (semantic_similarity_only; raw=0.633467, boost=0.0)

**Top qa docs**
- `0.56007` كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟ (semantic_similarity_only; raw=0.56007, boost=0.0)
- `0.55918` ضيق السلام عليكم والله بعانى تنفس شديد دون سبب طبى واستخدمت برامج رقية كتير والحمدلله لم ياذن بالشفاء والموضوع دة معايا  (semantic_similarity_only; raw=0.55918, boost=0.0)
- `0.555869` تناول طفلي حبه امادول tramadol كيف اسعفه ؟ (semantic_similarity_only; raw=0.555869, boost=0.0)
- `0.548706` كيف اتصرف مع انسان لدغته أم اربعه واربعين (semantic_similarity_only; raw=0.548706, boost=0.0)
- `0.547592` السلام عليكم.انا مصاب بفيروس س4 واخذتعﻻج بيغاسي ولم اشفى.جرى عندي التهاب بالمجاري البولية واخت دواء اموكسلين مع مسكن من  (semantic_similarity_only; raw=0.547592, boost=0.0)

## Output Files

- Semantic retrieval JSON: `outputs/05_trial_graph_v1/semantic_retrieval/trial_graph_v1_semantic_retrieval_results.json`
- Semantic retrieval CSV: `outputs/05_trial_graph_v1/semantic_retrieval/trial_graph_v1_semantic_retrieval_results.csv`

## Next Step From Mix.png

Use these semantic retrieval results in Step 9C hybrid retrieval with graph traversal and relation-weighted reranking.
