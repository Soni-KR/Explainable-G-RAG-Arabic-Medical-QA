# Evaluation-v1 Qualitative Inspection: Steps 8-12

This report inspects saved outputs for held-out questions verified against the original AHD dataset.
It is qualitative debugging evidence, not a replacement for human-confirmed retrieval gold labels.
The supplemental graph is not used.

## Configuration note

The current final pipeline has one valid Step 8 configuration: `openai/gpt-oss-20b` with `query_analysis_v1`.
Four-model comparison is deferred; old colleague Step 8 outputs target the incompatible trial/supplemental graph and are excluded.
The historical generation records inspected here used the model recorded in each example. The project default is now `openai/gpt-oss-20b`.

## Selected examples

Total: `15`. Categories: `{"little_available_evidence": 2, "qa_evidence_dominant": 10, "strong_graph_coverage": 3}`.

## Example 1: `evalv1_001`

Coverage category: `little_available_evidence`

### Original AHD record

**Question:** هل يوجد علاج أكيد وفعال لرفع نسبه هرمون البروجستروأذا كان معدله صفر؟

**Reference answer:** لماذا تم اجراء هذا الفحص ؟ عادةً يتم اجراء فحوصات هرمونيه اخرى مع هذا الهرمون. هناك حبوب عديده تحتوي على عده انواع من البرجسترون وهي تُستعمل في حالات عديده ولكن ليس لدي علم عن حالتك اذا كان هناك فائده من استعمال هذه الهورمونات

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: هل يوجد علاج أكيد وفعال لرفع نسبه هرمون البروجستروأذا كان معدله صفر؟
- Normalized: هل يوجد علاج اكيد وفعال لرفع نسبه هرمون البروجسترواذا كان معدله صفر?
- Corrected: هل يوجد علاجٌ أكيدٌ وفعالٌ لرفع نسبة هرمون البروجستيرون إذا كان معدله صفر؟
- Reformulated: ما هو العلاج المؤكد والفعال لرفع مستوى هرمون البروجستيرون إذا كان معدله صفر؟
- Class / complexity: `simple_medical` / `low`
- Primary intent: `treatment_request`
- Preferred relations: `TREATED_BY, TREATS`
- Analysis confidence: `0.9`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| هرمون البروجستيرون | DiseaseCondition | corrected_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| هرمون البروجستيرون | هرمون البروجسترون | `ent_merge_000562` | `exact_alias` | 0.95 | `linked` |

Retrieval plan: vector=`True`, graph=`True`, hop depth=`2`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_000562`: هرمون البروجسترون
- `ent_merge_000209`: انخفاض هرمون البروجسترون
- `ent_merge_001651`: هرمون التستوستيرون
- `ent_merge_000012`: ارتفاع هرمون اللبن
- `ent_merge_001649`: هرمون الإستروجين

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| هرمون البروجسترون --TREATED_BY--> تناول الفواكه | 1.0 | 0.80446 | `ahd10k_00787` |
| انخفاض هرمون البروجسترون --TREATED_BY--> تناول الفواكه | 1.0 | 0.80446 | `ahd10k_00787` |
| هرمون البروجسترون --TREATED_BY--> علاجات دوائية | 1.0 | 0.80446 | `ahd10k_00787` |
| هرمون البروجسترون --TREATED_BY--> تناول الخضراوات | 1.0 | 0.80446 | `ahd10k_00787` |
| انخفاض هرمون البروجسترون --TREATED_BY--> تناول الخضراوات | 1.0 | 0.80446 | `ahd10k_00787` |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd10k_00787` | هناك العديد من الوسائل المتبعة لعلاج انخفاض مستوى البروجيستيرون الإكثار من تناول الخضراوات الإكثار من تناول الخضراوات والفواكه التقليل من الضغط النفسي التقليل من الضغط النفسي والتوتر وقف التدخين علاجات دوائية التي تحتوي هرمون البروجستيرون | 0.9462165832519531 | `ahd10k_00787` | `mention_evidence` |
| `men_merge_0003910` | هناك العديد من الوسائل المتبعة لعلاج انخفاض مستوى البروجيستيرون | 0.9395322799682617 | `ahd10k_00787` | `mention_evidence` |
| `men_merge_0003909` | ماهو علاج انخفاض هرمون البروجسترون ؟ | 0.9340252876281738 | `ahd10k_00787` | `mention_evidence` |
| `men_merge_0003924` | علاجات دوائية التي تحتوي هرمون البروجستيرون | 0.9322404861450195 | `ahd10k_00787` | `mention_evidence` |
| `men_merge_0003382` | فيجب البدء بتناول هرمون التستوستيرون | 0.923762321472168 | `ahd10k_03070` | `preprocessed_source_row` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd10k_00787` | ماهو علاج انخفاض هرمون البروجسترون ؟ | هناك العديد من الوسائل المتبعة لعلاج انخفاض مستوى البروجيستيرون الإكثار من تناول الخضراوات الإكثار من تناول الخضراوات والفواكه التقليل من الضغط النفسي التقليل من الضغط النفسي والتوتر وقف التدخين علاجات دوائية التي تحتوي هرمون البروجستيرون | 0.9462165832519531 |
| `ahd10k_03070` | هل يوجد علاج لخلل مستقبلات هرمون التيستيسترون؟ | قد يتسبب خلل مستقبلات هرمون التيستيسترون بالإصابة بمتلازمة عدم الحساسية للأندروجين الكاملة (بالإنجليزية: Complete Androgen insensitivity) أو متلازمة نقص الحساسية الجزئي للأندروجين (بالإنجليزية: Partial androgen insensitivity syndrome). ويعتمد العلاج في البد... | 0.923762321472168 |
| `ahd10k_06970` | كان عندي نقص في التستيرون فاخذت بعد اخذ سيدوتيستون 250 حقنة كل اسبوع لمدة شهر اصبحت الحيوانات المنوية صفر و انخفضت جميه الهرمونات fsh1.2 و lh0.3 ,التستيرون 1.33 وكنت عملت... | يجب مراجعه طبيب مساعده على الحمل او انجاب او طبيب مسالك بوليه في اقرب فرصه | 0.9230756759643555 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | هرمون البروجسترون --TREATED_BY--> تناول الفواكه | Relation | 0.9462 | 1.0 | 1.0 | 0.2308 | 0.8045 | 0.724 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 2 | 2 | انخفاض هرمون البروجسترون --TREATED_BY--> تناول الفواكه | Relation | 0.9462 | 1.0 | 1.0 | 0.2308 | 0.8045 | 0.724 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 3 | 3 | هرمون البروجسترون --TREATED_BY--> علاجات دوائية | Relation | 0.9462 | 1.0 | 1.0 | 0.2308 | 0.8045 | 0.724 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 4 | 4 | هرمون البروجسترون --TREATED_BY--> تناول الخضراوات | Relation | 0.9462 | 1.0 | 1.0 | 0.2308 | 0.8045 | 0.724 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 5 | 5 | انخفاض هرمون البروجسترون --TREATED_BY--> تناول الخضراوات | Relation | 0.9462 | 1.0 | 1.0 | 0.2308 | 0.8045 | 0.724 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 6 | 6 | انخفاض هرمون البروجسترون --TREATED_BY--> علاجات دوائية | Relation | 0.9462 | 1.0 | 1.0 | 0.2308 | 0.7805 | 0.7078 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 7 | 1 | ماهو علاج انخفاض هرمون البروجسترون ؟ | QA | 0.9462 | - | - | 0.6532 | 0.9462 | 0.6609 | query relevance+source quality+direct-QA+relation support |
| 8 | 2 | هناك العديد من الوسائل المتبعة لعلاج انخفاض مستوى البروجيستيرون | Evidence | 0.9395 | - | - | 0.6532 | 0.9395 | 0.5804 | query relevance+source quality+direct-QA+relation support |
| 9 | 3 | ماهو علاج انخفاض هرمون البروجسترون ؟ | Evidence | 0.934 | - | - | 0.6532 | 0.934 | 0.5793 | query relevance+source quality+direct-QA+relation support |
| 10 | 4 | علاجات دوائية التي تحتوي هرمون البروجستيرون | Evidence | 0.9322 | - | - | 0.6532 | 0.9322 | 0.5789 | query relevance+source quality+direct-QA+relation support |

### Step 11: Final evidence context

Context contains `1` graph facts and `3` evidence/QA items.

**Graph facts supplied to the generator**

- `R1` هرمون البروجسترون --TREATED_BY--> تناول الفواكه (score=0.723983, QA=`ahd10k_00787`)

**Evidence supplied to the generator**

- `E1` / source `ahd10k_00787` / QA `ahd10k_00787`: هناك العديد من الوسائل المتبعة لعلاج انخفاض مستوى البروجيستيرون الإكثار من تناول الخضراوات الإكثار من تناول الخضراوات والفواكه التقليل من الضغط النفسي التقليل من الضغط النفسي والتوتر وقف التدخين علاجات دوائية التي تحتوي هرمون البروجستيرون
- `E2` / source `men_merge_0003910` / QA `ahd10k_00787`: هناك العديد من الوسائل المتبعة لعلاج انخفاض مستوى البروجيستيرون
- `E3` / source `rel_seed_12099cb4f8d5e172` / QA `ahd10k_00787`: الإكثار من تناول الخضراوات والفواكه

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `successful`
- Fallback type: `generated`
- BERTScore F1 against AHD reference: `0.659242`
- End-to-end latency: `1779.022 ms`

**Reference AHD answer**

لماذا تم اجراء هذا الفحص ؟ عادةً يتم اجراء فحوصات هرمونيه اخرى مع هذا الهرمون. هناك حبوب عديده تحتوي على عده انواع من البرجسترون وهي تُستعمل في حالات عديده ولكن ليس لدي علم عن حالتك اذا كان هناك فائده من استعمال هذه الهورمونات

**Generated answer before mitigation**

علاج ارتفاع هرمون البروجستيرون عند وجود مستوى صفر يشمل تناول الفواكه والخضروات، تقليل التوتر، وقف التدخين، واستخدام علاجات دوائية تحتوي على هرمون البروجستيرون.

**Final answer after mitigation**

يُعالج انخفاض مستوى البروجستيرون بزيادة تناول الخضروات والفواكه. [E1]

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| يُعالج انخفاض مستوى البروجستيرون بزيادة تناول الخضروات والفواكه. | `supported` | 0.625 | 0.653239 | `E1` | `ahd10k_00787` | A valid citation supports the claim and the claim directly addresses the query. |

Warnings:
- Adjusted phrase 1: measured hormone concept retyped for graph compatibility.
- Planner increased graph depth because the query has age, duration, comparison, or multiple-phrase signals.
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 9 low-value context items; 3 focused items remain.

---

## Example 2: `evalv1_002`

Coverage category: `qa_evidence_dominant`

### Original AHD record

**Question:** عملت تحاليل و كل شيء و ماطلع شيء في سنة 2012 و الدوخة و الاغماء موجودين ماذا افعل ؟

**Reference answer:** راجع اختصاصي باطنية عمل فحص شامل للدم والبول والبراز، وضغط الدم وما يلزم للمتابعة والتشخيص الدقيق.

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: عملت تحاليل و كل شيء و ماطلع شيء في سنة 2012 و الدوخة و الاغماء موجودين ماذا افعل ؟
- Normalized: عملت تحاليل و كل شيء و ماطلع شيء في سنه 2012 و الدوخه و الاغماء موجودين ماذا افعل ?
- Corrected: عملت تحاليل وكل شيء وما ظهر شيء في سنة 2012، والدوخة والإغماء موجودان، ماذا أفعل؟
- Reformulated: عملت تحاليل وكل شيء ولم يظهر أي نتيجة في سنة 2012، والدوخة والإغماء مستمران، ماذا يجب أن أفعل؟
- Class / complexity: `simple_medical` / `low`
- Primary intent: `test_request`
- Preferred relations: `INVESTIGATED_BY, INVESTIGATES`
- Analysis confidence: `0.9`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| الإغماء | Symptom | corrected_query | 0.9 |
| تحاليل | Test | corrected_query | 0.9 |
| الدوخة | Symptom | corrected_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| الإغماء | الإغماء | `ent_merge_001854` | `exact_canonical` | 1.0 | `linked` |
| تحاليل | تحاليل | `ent_merge_000965` | `exact_canonical` | 1.0 | `linked` |
| الدوخة | الدوخة | `ent_merge_000649` | `exact_canonical` | 1.0 | `linked` |

Retrieval plan: vector=`True`, graph=`True`, hop depth=`2`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_001854`: الإغماء
- `ent_merge_002248`: نقص فيتامين (ب12)
- `ent_merge_001997`: فحص مجموعات الدم
- `ent_merge_000966`: تحاليل الدم
- `ent_merge_001891`: المضاعفات الوعائية

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| _No graph relation returned_ | - | - | - |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd10k_09335` | الأسباب الشائعة: - النوم لفترات قصيرة. - الأدوية والعقاقير (مهدئات- أقراص منومة- مضادات الهيستامين). - اضطرابات النوم (مثل تقطع النفس أثناء النوم) أو الغفوات النومية. - حالات طبية أخرى مثل ( خمول الغدة الدرقية - فرط كالسيوم الدم - فرط صوديوم الدم أو نقصه).... | 0.9226813316345215 | `ahd10k_09335` | `preprocessed_source_row` |
| `ahd5k_04926` | عليك بالقيام بعدة فحوصات أهمها CBC التحليل الكامل للدم . | 0.9225635528564453 | `ahd5k_04926` | `preprocessed_id` |
| `ahd10k_09316` | انتظري قليلا او اعملي سونار وتحاليل هرمونية | 0.9223055839538574 | `ahd10k_09316` | `mention_evidence` |
| `ahd5k_02589` | بحاجة لتناول السوائل والمسكنات ولاجراء فحوصات الدم والفيتامينات والضغط والعيوk . راجع المركز الطبي , سلامات | 0.9221353530883789 | `ahd5k_02589` | `preprocessed_id` |
| `ahd10k_07124` | مبدئيا ننصحك بقياس ضغط الدم وعمل رسم مخ بالكمبيوتر مع اشعة رنين مغناطيسى على المخ | 0.9212708473205566 | `ahd10k_07124` | `mention_evidence` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd10k_09335` | السلام عليكم دائما اشعر بنعاس حتى لو كنت نائمة فترة جيدة تقريبا 6 او 7 ساعات ما السبب وما االحل ؟؟ وشكرا الكم كتير | الأسباب الشائعة: - النوم لفترات قصيرة. - الأدوية والعقاقير (مهدئات- أقراص منومة- مضادات الهيستامين). - اضطرابات النوم (مثل تقطع النفس أثناء النوم) أو الغفوات النومية. - حالات طبية أخرى مثل ( خمول الغدة الدرقية - فرط كالسيوم الدم - فرط صوديوم الدم أو نقصه).... | 0.9226813316345215 |
| `ahd5k_04926` | أشعر بدوخه مع غثيان وعدم تركيز وخمول | عليك بالقيام بعدة فحوصات أهمها CBC التحليل الكامل للدم . | 0.9225635528564453 |
| `ahd10k_09316` | لم تنزل لدي الدوره الشهريه حتى الان | انتظري قليلا او اعملي سونار وتحاليل هرمونية | 0.9223055839538574 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 5 | لدي الم مستمر فى الراس من الوراء | QA | 0.9213 | - | - | 0.5944 | 0.9213 | 0.5462 | query relevance+source quality+direct-QA+relation support |
| 2 | 7 | السلام عليكم اسباب هذه الاعراض متعددة منها نقص الهيوغلوبين او الحديد او خلل في الغدة الدرقية او نقص الفيتامينات وخاصة فيتامين د او غير ذلك ، يفضل زيارة الطبيب لاجراء فحص سريري وفحوصات للدم لتحديد السبب والعلاج | Evidence | 0.9163 | - | - | 0.5857 | 0.9163 | 0.5013 | query relevance+source quality+direct-QA+relation support |
| 3 | 2 | أشعر بدوخه مع غثيان وعدم تركيز وخمول | QA | 0.9226 | - | - | 0.2 | 0.9226 | 0.5005 | query relevance+source quality+direct-QA+relation support |
| 4 | 6 | قبل الدواء يجب معرفة السبب . عليك بعمل تحليل للبول وزراعة . ويمكنك عمل اشعة صوتية للمثانة والكلى ايضا . إذا هناك التهاب فيعالج بالمضاد المناسب . واذا لم يوجد فتعطى ادوية لتهدئة المثانة . | Evidence | 0.9182 | - | - | 0.5944 | 0.9182 | 0.4481 | query relevance+source quality+direct-QA+relation support |
| 5 | 10 | اعاني من هبوط الضغط والتعب بعد الاكل مباشره ومن الغازات بشكل مزعج سويت تحاليل دم وسكر وفيتامينات وهرمونات كلها سليمة ولكن الضغط مستمر والغازات اخذت لها علاج لخمس ايام ولا... | Evidence | 0.9137 | - | - | 0.5944 | 0.9137 | 0.4472 | query relevance+source quality+direct-QA+relation support |
| 6 | 4 | لقد تعرضت مباشرة للشمس لمدة ما يقارب 5-6 ساعات وليومين متتالين وانا صائم وبعدها اصبحت اعاني من صداع وشعور بعدم التوازن (الدوخة) خاصة ليلاً عندما اخلد للنوم او عند الاستيقاظ | QA | 0.9221 | - | - | 0.0 | 0.9221 | 0.4444 | query relevance+source quality+direct-QA+relation support |
| 7 | 12 | انا فتاة ابلغ22 عندي خلل في الدورة الحيضية تغيب لمدة 6 اشهر استعملت الكثير من الادوية دون حصول نتيجة . | Evidence | 0.9135 | - | - | 0.0839 | 0.9135 | 0.3802 | query relevance+source quality+direct-QA+relation support |
| 8 | 3 | لم تنزل لدي الدوره الشهريه حتى الان | QA | 0.9223 | - | - | 0.0 | 0.9223 | 0.3725 | query relevance+source quality+direct-QA+relation support |
| 9 | - | يحصل الاختناق نتيجة عدم وصول الاوكسجين الى الرئتين وتكاثرغاز ثاني اكسيد الكربون او غيره من الغازات غير الصالحة للتنفس فيتخدر الجهاز العصبي ويفسد الدم ويتعرض المصاب الى الارتخاء ثم الى الغيبوبة ثم الموت.ويحدث ذلك في حا... | Evidence | - | - | - | 0.0194 | - | 0.368 | query relevance+source quality+direct-QA+relation support |
| 10 | 9 | قمت بعمل اشعة على المخ،تحليل كامل للدم،زرت طبيب باطنية،فحصت ضغط الدم والنظر،قمت بعمل اشعة رنين مغناطيسي،واخذت ادويه كثيره والصداع لا يتوقف في كل الرأس منذ اكثر من اسبوعين | Evidence | 0.9142 | - | - | 0.2194 | 0.9142 | 0.3423 | query relevance+source quality+direct-QA+relation support |

### Step 11: Final evidence context

Context contains `0` graph facts and `1` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- `E1` / source `ahd10k_07124` / QA `ahd10k_07124`: مبدئيا ننصحك بقياس ضغط الدم وعمل رسم مخ بالكمبيوتر مع اشعة رنين مغناطيسى على المخ

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `successful`
- Fallback type: `generated`
- BERTScore F1 against AHD reference: `0.685654`
- End-to-end latency: `1909.414 ms`

**Reference AHD answer**

راجع اختصاصي باطنية عمل فحص شامل للدم والبول والبراز، وضغط الدم وما يلزم للمتابعة والتشخيص الدقيق.

**Generated answer before mitigation**

نصائح عامة: يُنصح بقياس ضغط الدم، وإجراء تصوير بالرنين المغناطيسي (MRI) أو التصوير المقطعي المحوسب (CT) للمخ لتقييم الأسباب المحتملة للدوخة والإغماء.

**Final answer after mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| يُنصح بقياس ضغط الدم وإجراء تصوير بالرنين المغناطيسي أو التصوير المقطعي المحوسب للمخ. | `weakly_supported` | 0.363636 | 0.594444 | `E1` | `ahd10k_07124` | The claim has partial evidence support or only moderate relevance to the query. |

Warnings:
- Adjusted phrase 2: normalized_form replaced with project normalization.
- Adjusted phrase 3: normalized_form replaced with project normalization.
- Ignored alias-only match to تحليل because it does not share tokens with the phrase.
- Ignored alias-only match to تحليل الحساسية because it does not share tokens with the phrase.
- Ignored alias-only match to الدوقه because it does not share tokens with the phrase.
- Ignored alias-only match to دوخة because it does not share tokens with the phrase.
- Ignored alias-only match to التهاب because it does not share tokens with the phrase.
- Linked generic concept 'تحاليل' is low-specificity and should not be a strong retrieval seed.
- Low-specificity linked entities are excluded from primary graph seeds.
- Planner increased graph depth because the query has age, duration, comparison, or multiple-phrase signals.
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 11 low-value context items; 1 focused items remain.

---

## Example 3: `evalv1_003`

Coverage category: `qa_evidence_dominant`

### Original AHD record

**Question:** ما هو الفحص الطبي ماذا يشمل؟

**Reference answer:** الفحص الطبي هو استقصاء ناقد ومعاينة بهدف التشخيص.ويشمل جميع الوسائل التي تفيد في تحقيق الهدف، من الفحص السريري ثم المختبر والأشعة بأنواعها والفحوصات الخاصة لأمراض معينة مثل فحص الحمل والسكري وفحص الدم للسرطان وغيرها كثير،، يفيد مراجعتك للمفردات تحت بند التشخيص في مواضيع خاصة.

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: ما هو الفحص الطبي ماذا يشمل؟
- Normalized: ما هو الفحص الطبي ماذا يشمل?
- Corrected: ما هو الفحص الطبي ماذا يشمل؟
- Reformulated: ما هو الفحص الطبي وما الذي يشمله؟
- Class / complexity: `simple_medical` / `low`
- Primary intent: `test_request`
- Preferred relations: `INVESTIGATED_BY, INVESTIGATES`
- Analysis confidence: `0.9`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| الفحص الطبي | Test | corrected_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| الفحص الطبي | الفحص الطبي | `ent_merge_000949` | `exact_canonical` | 1.0 | `linked` |

Retrieval plan: vector=`True`, graph=`True`, hop depth=`1`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_000949`: الفحص الطبي
- `ent_merge_001051`: فحص طبي
- `ent_merge_000946`: الفحص
- `ent_merge_000948`: الفحص السريري
- `ent_merge_001023`: فحص

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| ضيق تنفس --INVESTIGATED_BY--> الفحص الطبي | 0.85 | 0.802396 | `ahd10k_01949` |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `men_merge_0005557` | الفحص الطبي هو الوسيلة الوحيدة لتحديد ان كان هناك سبب عضوي أو نفسي، وفي حالة عدم وجود أي خلل عضوي يتطلب الأمر مراجعة أخصائي نفسية للوصول إلى تشخيص دقيق | 0.9327306747436523 | `ahd5k_03417` | `preprocessed_id` |
| `men_merge_0000022` | والفحص الطبي يمكن ان يساعد | 0.9222159385681152 | `ahd10k_01949` | `mention_evidence` |
| `men_merge_0003260` | ننصح باجراء فحص طبي للوقوف على تفاصيل أكثر | 0.9212307929992676 | `ahd10k_03048` | `preprocessed_source_row` |
| `men_merge_0003667` | ينصح لك مراجعة اخصائي غدد صم وسكري من اجل بعض الفحوصات المخبرية , من خلال زيارة اخصائي تغذية يمكن وضع برنامج غذائي يمكنك من الرياضة دون هبوط السكر وباحتساب السعرات الحرارية اللازمة والتي تناسب وزنك وطولك ونوع الرياضة التي ترغب ممارستها , بالنسبة لضغط الدم و... | 0.9199552536010742 | `ahd10k_04438` | `preprocessed_source_row` |
| `men_merge_0003637` | اجرى الطبيب فحص دم لي | 0.9196572303771973 | `ahd10k_09267` | `mention_evidence` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd5k_03417` | ما هذا المرض؟ أحس ان راسي ير موجود بجسمي او انه خفيف ليس مثل ما كان من قبل وعندما اضع يدي على راسي احس ان راسي صغرت جدا ما هذا؟ | الفحص الطبي هو الوسيلة الوحيدة لتحديد ان كان هناك سبب عضوي أو نفسي، وفي حالة عدم وجود أي خلل عضوي يتطلب الأمر مراجعة أخصائي نفسية للوصول إلى تشخيص دقيق | 0.9327306747436523 |
| `ahd10k_01949` | لم يستطع ان ينام بسبب ضيق تنفس | فمن كلامك يبدو انه تسارع قلبي والفحص الطبي يمكن ان يساعد | 0.9222159385681152 |
| `ahd10k_03048` | اشعر باعراض لم اشعر بها من قبل فالبارحة احسست بوخز في قلبي و اليوم عندما اتنفس اتنفس بصعوبة مع الم شديد في الصدر من جهة القلب كالسكين الحاد مع العلم... | ننصح باجراء فحص طبي للوقوف على تفاصيل أكثر لتوضيح اذا ما كان هناك سبب عضوي يتعلق بالتهاب القصبات أو تحسس يُسبب ضيق التنفس والأجهاد الناجم عنه يؤدي إلى تشنج العضلات الوربية وبالتالي الألم | 0.9212307929992676 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | ضيق تنفس --INVESTIGATED_BY--> الفحص الطبي | Relation | 0.9325 | 1.0 | 1.0 | 0.2857 | 0.8024 | 0.7283 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 2 | - | الفحص الطبي يمكن أن يساعد | Evidence | - | - | - | 0.625 | - | 0.5549 | query relevance+source quality+direct-QA+relation support |
| 3 | 11 | ما هي مواعيد الاشعة والتحاليل اليومية؟ | QA | 0.9138 | - | - | 0.25 | 0.9138 | 0.532 | query relevance+source quality+direct-QA+relation support |
| 4 | 10 | لو سمحت عايز اعرف في كدا كورونا ولا ايه | QA | 0.9145 | - | - | 0.2 | 0.9145 | 0.4989 | query relevance+source quality+direct-QA+relation support |
| 5 | 1 | الفحص الطبي هو الوسيلة الوحيدة لتحديد ان كان هناك سبب عضوي أو نفسي، وفي حالة عدم وجود أي خلل عضوي يتطلب الأمر مراجعة أخصائي نفسية للوصول إلى تشخيص دقيق | Evidence | 0.9327 | - | - | 0.25 | 0.9327 | 0.4937 | query relevance+source quality+direct-QA+relation support |
| 6 | 5 | اجرى الطبيب فحص دم لي | Evidence | 0.9197 | - | - | 0.5857 | 0.9197 | 0.4359 | query relevance+source quality+direct-QA+relation support |
| 7 | - | - | QA | - | - | - | 0.2 | - | 0.426 | query relevance+source quality+direct-QA+relation support |
| 8 | 8 | اجراء فحص للكشف عن أي علامات سريرية | Evidence | 0.9185 | - | - | 0.2 | 0.9185 | 0.4254 | query relevance+source quality+direct-QA+relation support |
| 9 | 7 | فحص الدم والبراز | Evidence | 0.9187 | - | - | 0.25 | 0.9187 | 0.4235 | query relevance+source quality+direct-QA+relation support |
| 10 | - | لم يستطع ان ينام بسبب ضيق تنفس | Evidence | - | - | - | 0.2 | - | 0.4102 | query relevance+source quality+direct-QA+relation support |

### Step 11: Final evidence context

Context contains `0` graph facts and `1` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- `E1` / source `ahd10k_01433` / QA `ahd10k_01433`: الفحص الطبي هو استقصاء ناقد ومعاينة بهدف التشخيص.ويشمل جميع الوسائل التي تفيد في تحقيق الهدف، من الفحص السريري ثم المختبر والأشعة بأنواعها والفحوصات الخاصة لأمراض معينة مثل فحص الحمل والسكري وفحص الدم للسرطان وغيرها كثير،، يفيد مراجعتك للمفردات تحت بند التشخيص في مواضيع خاصة.

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `successful`
- Fallback type: `generated`
- BERTScore F1 against AHD reference: `0.79919`
- End-to-end latency: `1696.517 ms`

**Reference AHD answer**

الفحص الطبي هو استقصاء ناقد ومعاينة بهدف التشخيص.ويشمل جميع الوسائل التي تفيد في تحقيق الهدف، من الفحص السريري ثم المختبر والأشعة بأنواعها والفحوصات الخاصة لأمراض معينة مثل فحص الحمل والسكري وفحص الدم للسرطان وغيرها كثير،، يفيد مراجعتك للمفردات تحت بند التشخيص في مواضيع خاصة.

**Generated answer before mitigation**

الفحص الطبي هو استقصاء ناقد ومعاينة تهدف إلى التشخيص، ويشمل جميع الوسائل التي تساعد في تحقيق هذا الهدف، بدءاً من الفحص السريري ثم الفحوصات المختبرية والأشعة بأنواعها، بالإضافة إلى الفحوصات الخاصة لأمراض معينة مثل فحص الحمل والسكري وفحص الدم للسرطان وغيرها.

**Final answer after mitigation**

يشمل الفحص الطبي الفحص السريري، الفحوصات المختبرية، الأشعة، وفحوصات خاصة لأمراض معينة مثل الحمل والسكري والسرطان. [E1]

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| يشمل الفحص الطبي الفحص السريري، الفحوصات المختبرية، الأشعة، وفحوصات خاصة لأمراض معينة مثل الحمل والسكري والسرطان. | `supported` | 0.642857 | 0.93 | `E1` | `ahd10k_01433` | A valid citation supports the claim and the claim directly addresses the query. |

Warnings:
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 11 low-value context items; 1 focused items remain.

---

## Example 4: `evalv1_004`

Coverage category: `strong_graph_coverage`

### Original AHD record

**Question:** ماهي مسكنات الولاده الآمنه لمريضه مصابه بربو اوحساسيه بالصدر

**Reference answer:** اذا ما تم استعمال هذه المسكنات في المستشفى وتحت اشراف طبي فلا خوف منها ان شاء الله اما المسكنات فهناك انواع منها على شكل ابر ومنها غاز يتم استنشاقه ومنها التخدير النصفي ( ابرة الظهر ) وسوف يقوم طبيبك بتحديد ما يناسبك ومناقشة الأمر معك

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: ماهي مسكنات الولاده الآمنه لمريضه مصابه بربو اوحساسيه بالصدر
- Normalized: ماهي مسكنات الولاده الامنه لمريضه مصابه بربو اوحساسيه بالصدر
- Corrected: ما هي مسكنات الولادة الآمنة لمريضة مصابة بربو أو إحساس بالصدر؟
- Reformulated: ما هي مسكنات الولادة الآمنة لمريضة مصابة بربو أو إحساس بالصدر؟
- Class / complexity: `simple_medical` / `low`
- Primary intent: `medication_safety`
- Preferred relations: `none`
- Analysis confidence: `1.0`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| مسكنات الولادة | Treatment | corrected_query | 1.0 |
| إحساس بالصدر | Symptom | corrected_query | 1.0 |
| ربو | DiseaseCondition | corrected_query | 1.0 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| مسكنات الولادة | - | `-` | `none` | 0.0 | `unresolved` |
| إحساس بالصدر | - | `-` | `none` | 0.0 | `unresolved` |
| ربو | ربو | `ent_merge_000371` | `exact_canonical` | 1.0 | `linked` |

Retrieval plan: vector=`True`, graph=`True`, hop depth=`2`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_002160`: حبوب مانعه للحمل
- `ent_merge_001563`: مانع للحمل
- `ent_merge_001312`: تحريض ولادة
- `ent_merge_000016`: استرواح الصدر التوتري
- `ent_merge_001562`: مانع حمل

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| ربو --HAS_SYMPTOM--> سعال | 0.95 | 0.719187 | `ahd10k_04355` |
| ربو --HAS_SYMPTOM--> سعال | 0.95 | 0.701005 | `ahd10k_00128` |
| ربو --INVESTIGATED_BY--> تحليل الحساسية | 1.0 | 0.688823 | `ahd10k_05333` |
| ربو --HAS_SYMPTOM--> ضيق التنفس | 1.0 | 0.688823 | `ahd10k_01288` |
| حساسية الصدر --HAS_SYMPTOM--> ضيق تنفس | 0.98 | 0.644097 | `ahd10k_08559` |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd10k_09750` | بصراحة الغطس في المياه البحرية أمن و لكن يجب تناول علاج البخاخات | 0.9168200492858887 | `ahd10k_09750` | `mention_evidence` |
| `ahd10k_06253` | ليس له مضاعفات خطيرة لكن يجب الحذر من استخدامه اثناء الحمل تقليل الشعور بالتعب | 0.9164581298828125 | `ahd10k_06253` | `mention_evidence` |
| `ahd10k_05194` | لا استطيع تناول ادوية مضادة للالتهاب حساسية الصدر مضاد حيوي دواء نابروكسين | 0.9158840179443359 | `ahd10k_05194` | `mention_evidence` |
| `men_merge_0004995` | اذا كنت حامل وما زلت تستعملين اقراص ال بريمولوت ن فيجب ايقافها ، فهناك دراسات اثبتتت انه يمكن ان تؤدي هذه الاقراص الى تشوهات في القلب والاوعيه الدمويه لدى الجنين ، كما انه يمكن ان تؤدي الى تشوهات في الانبوب العصبي والدماغ | 0.9155058860778809 | `ahd5k_00439` | `preprocessed_id` |
| `ahd5k_03662` | متابعة مع طبيب ضروري جدا للبدأ بالعلاج العلاجي والوقائي للربو | 0.9154987335205078 | `ahd5k_03662` | `preprocessed_id` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd10k_09750` | لدي حساسية بالصدر من الغبار ووبر الحيوانات | بصراحة الغطس في المياه البحرية أمن و لكن يجب تناول علاج البخاخات | 0.9168200492858887 |
| `ahd10k_06253` | PREFERTIL هذا الدواء اعطته الدكتورة لزوجتي | ليس له مضاعفات خطيرة لكن يجب الحذر من استخدامه اثناء الحمل تقليل الشعور بالتعب | 0.9164581298828125 |
| `ahd10k_05194` | لا استطيع تناول ادوية مضادة للالتهاب حساسية الصدر مضاد حيوي دواء نابروكسين | - | 0.9158840179443359 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | ربو --HAS_SYMPTOM--> سعال | Relation | 0.9097 | 1.0 | 0.4 | 0.1818 | 0.7192 | 0.6743 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 2 | 2 | ربو --HAS_SYMPTOM--> سعال | Relation | 0.9097 | 1.0 | 0.4 | 0.0909 | 0.701 | 0.6481 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 3 | 6 | حساسية --HAS_SYMPTOM--> ضيق تنفس | Relation | 0.9114 | 1.0 | 0.4 | 0.2727 | 0.6347 | 0.6417 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 4 | 7 | حساسية --HAS_SYMPTOM--> سعال | Relation | 0.9114 | 1.0 | 0.4 | 0.2727 | 0.6347 | 0.6417 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 5 | 8 | حساسية --HAS_SYMPTOM--> ضيق تنفس | Relation | 0.9114 | 1.0 | 0.4 | 0.1818 | 0.6225 | 0.6196 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 6 | 9 | حساسية --HAS_SYMPTOM--> سعال | Relation | 0.9114 | 1.0 | 0.4 | 0.1818 | 0.6165 | 0.6155 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 7 | 10 | حساسية --DIAGNOSED_BY--> تحاليل مخبرية | Relation | 0.9114 | 1.0 | 0.4 | 0.1818 | 0.6165 | 0.6155 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 8 | 12 | حساسية --HAS_SYMPTOM--> سعال | Relation | 0.9114 | 1.0 | 0.4 | 0.0909 | 0.5983 | 0.6133 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 9 | 4 | ربو --HAS_SYMPTOM--> ضيق التنفس | Relation | 0.9097 | 1.0 | 0.4 | 0.0 | 0.6888 | 0.602 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 10 | 3 | ربو --INVESTIGATED_BY--> تحليل الحساسية | Relation | 0.9097 | 1.0 | 0.4 | 0.0 | 0.6888 | 0.598 | identity+query_support+semantic+source_quality+intent-entity_conflicts |

### Step 11: Final evidence context

Context contains `2` graph facts and `3` evidence/QA items.

**Graph facts supplied to the generator**

- `R1` ربو --HAS_SYMPTOM--> سعال (score=0.674296, QA=`ahd10k_04355`)
- `R2` ربو --HAS_SYMPTOM--> سعال (score=0.648115, QA=`ahd10k_00128`)

**Evidence supplied to the generator**

- `E1` / source `rel_seed_ef6c1ed70d6610e8` / QA `ahd10k_04355`: السعال مرتبط بالربو كأعراض ممكن أن يستمر بعد الكورونا
- `E2` / source `rel_seed_0fa305275c9bb628` / QA `ahd10k_00128`: الاستعداد القوي للاصابة بالسعال
- `E3` / source `men_merge_0003064` / QA `ahd10k_00128`: ابني عمره سنتان ونصف يعاني من الاستعداد القوي للاصابة بالسعال

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `successful`
- Fallback type: `generated`
- BERTScore F1 against AHD reference: `0.664666`
- End-to-end latency: `1506.712 ms`

**Reference AHD answer**

اذا ما تم استعمال هذه المسكنات في المستشفى وتحت اشراف طبي فلا خوف منها ان شاء الله اما المسكنات فهناك انواع منها على شكل ابر ومنها غاز يتم استنشاقه ومنها التخدير النصفي ( ابرة الظهر ) وسوف يقوم طبيبك بتحديد ما يناسبك ومناقشة الأمر معك

**Generated answer before mitigation**

لا توجد أدلة متاحة في البيانات المقدمة حول مسكنات الولادة الآمنة لمريضة مصابة بالربو أو إحساس بالصدر.

**Final answer after mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| لا توجد أدلة متاحة في البيانات المقدمة حول مسكنات الولادة الآمنة لمريضة مصابة بالربو أو إحساس بالصدر | `unsupported` | 0.0 | 0.777778 | `-` | `-` | The claim lacks sufficient cited support or does not directly answer the query. |

Warnings:
- Adjusted phrase 1: normalized_form replaced with project normalization.
- Adjusted phrase 3: normalized_form replaced with project normalization.
- medication_safety is not directly represented by current graph relation types; vector/evidence retrieval will be needed.
- Ignored alias-only match to الربو because it does not share tokens with the phrase.
- Graph relation filter disabled for unsupported intent; vector/evidence retrieval should carry the answer.
- Some extracted phrases were not linked and should rely on vector retrieval.
- Planner increased graph depth because the query has age, duration, comparison, or multiple-phrase signals.
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 9 low-value context items; 3 focused items remain.

---

## Example 5: `evalv1_007`

Coverage category: `qa_evidence_dominant`

### Original AHD record

**Question:** هل التهابات المهبليه عند الزوجه من الممكن ان تصيب الزوج بحرقان شديد فى العضو

**Reference answer:** نعم ، هناك بعض الالتهاب تنتقل من الزوجة الى الزوج ، يفضل عمل فحص بول و زراعة و معالجتين الزوج و الزوجه معا .

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: هل التهابات المهبليه عند الزوجه من الممكن ان تصيب الزوج بحرقان شديد فى العضو
- Normalized: هل التهابات المهبليه عند الزوجه من الممكن ان تصيب الزوج بحرقان شديد في العضو
- Corrected: هل التهابات المهبل لدى الزوجة ممكن أن تصيب الزوج بحرقان شديد في العضو؟
- Reformulated: هل يمكن أن تصيب التهابات المهبل لدى الزوجة الزوج بحرقان شديد في العضو؟
- Class / complexity: `simple_medical` / `low`
- Primary intent: `symptom_request`
- Preferred relations: `HAS_SYMPTOM, SYMPTOM_OF`
- Analysis confidence: `1.0`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| التهابات المهبل | DiseaseCondition | corrected_query | 1.0 |
| حرقان شديد | Symptom | corrected_query | 1.0 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| التهابات المهبل | - | `-` | `none` | 0.0 | `unresolved` |
| حرقان شديد | - | `-` | `none` | 0.0 | `unresolved` |

Retrieval plan: vector=`True`, graph=`False`, hop depth=`0`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_000059`: التهاب
- `ent_merge_000099`: التهاب المهبل
- `ent_merge_000605`: افرضات مهبلية
- `ent_merge_001864`: التهديد بالإجهاض
- `ent_merge_000296`: تهاب

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| _No graph relation returned_ | - | - | - |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd10k_05174` | ممكن ان يكون التهاب فطري او هربيس اعملي تحليل دم للهيربي ومسحه للمهبل موءلقتاًً DACTACORT كريم DIFLUCAN حبه في الاسبوع لمده ٤ اسابيع | 0.9287247657775879 | `ahd10k_05174` | `preprocessed_source_row` |
| `ahd10k_08370` | من المؤكد وجوب علاج اي التهابات خاصة في عنق الرحم قبل عمل اشعة الصبغة خاصة ان عملها ليس بالأمر الطاريء وبالمناسبة فهي ليست صعبة لذا انصح بعمل فحص داخلي اولا وعلاج اي التهابات ان وجدت Ahmed El-Rass, M.D. Dalia Clinic Tel. Office: +966 2 660 7068 | 0.9248089790344238 | `ahd10k_08370` | `preprocessed_source_row` |
| `ahd10k_09890` | حدوث التهابات في الأعضاء التناسلية قد تؤدي إلى البرود الجنسي بعد الزواج | 0.9244122505187988 | `ahd10k_09890` | `mention_evidence` |
| `ahd10k_05239` | هذه غالباً نتيجه التهابات فطريه مهبليه (مونيليا) وخاصةً اذا كانت مصاحبه بحكه او رائحه ، انصحك بمراجعه طبيبك لاخذ عينه من هذه الافرازات لفحصها مجهرياً، ومن ثم حسب التشخيص يمكن اعطائك العلاج المناسب. هذه الافرازات عادةً لا تؤدي الى عقم. بالنسبه الى تاخر الحمل... | 0.9239659309387207 | `ahd10k_05239` | `preprocessed_source_row` |
| `ahd10k_01802` | هذه التهابات مهبلية بحاجة لعلاج | 0.9224381446838379 | `ahd10k_01802` | `mention_evidence` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd10k_05174` | مرحبا أنا أعاني من التهاب في المناطق التناسلية بحيث لا أستطيع تمرير الماء يسهولة و هناك مجموعة من الحبوب المنتشرة في داخل السفتين الصغيرتين ( منطقة المهبل ) ما هو... | ممكن ان يكون التهاب فطري او هربيس اعملي تحليل دم للهيربي ومسحه للمهبل موءلقتاًً DACTACORT كريم DIFLUCAN حبه في الاسبوع لمده ٤ اسابيع | 0.9287247657775879 |
| `ahd10k_08370` | طبيبي طلب مني اشعة الصبغة لكن سمعت ان وجوداي التهابات في المهبل سوف يسبب العقم لان الصبغة سوف تدخلها الى داخل الرحم او من هذا القبيل هل صحيح هذا الكلام؟؟... | من المؤكد وجوب علاج اي التهابات خاصة في عنق الرحم قبل عمل اشعة الصبغة خاصة ان عملها ليس بالأمر الطاريء وبالمناسبة فهي ليست صعبة لذا انصح بعمل فحص داخلي اولا وعلاج اي التهابات ان وجدت Ahmed El-Rass, M.D. Dalia Clinic Tel. Office: +966 2 660 7068 | 0.9248089790344238 |
| `ahd10k_09890` | - | حدوث التهابات في الأعضاء التناسلية قد تؤدي إلى البرود الجنسي بعد الزواج | 0.9244122505187988 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 2 | طبيبي طلب مني اشعة الصبغة لكن سمعت ان وجوداي التهابات في المهبل سوف يسبب العقم لان الصبغة سوف تدخلها الى داخل الرحم او من هذا القبيل هل صحيح هذا الكلام؟؟... | QA | 0.9248 | - | - | 0.2632 | 0.9248 | 0.565 | query relevance+source quality+direct-QA+relation support |
| 2 | 9 | التهابات المهبل | Evidence | 0.9165 | - | - | 0.36 | 0.9165 | 0.5133 | query relevance+source quality+direct-QA+relation support |
| 3 | 1 | مرحبا أنا أعاني من التهاب في المناطق التناسلية بحيث لا أستطيع تمرير الماء يسهولة و هناك مجموعة من الحبوب المنتشرة في داخل السفتين الصغيرتين ( منطقة المهبل ) ما هو... | QA | 0.9287 | - | - | 0.1181 | 0.9287 | 0.4905 | query relevance+source quality+direct-QA+relation support |
| 4 | 5 | حكة في المهبل و الفرج مع افرازات و شعور بالحرقان او تورم فالشفرتين من الداخل ولكن لا يوجد الم اثناء التبول أو رائحة | QA | 0.9224 | - | - | 0.1181 | 0.9224 | 0.4298 | query relevance+source quality+direct-QA+relation support |
| 5 | 7 | مرحبا أنا أعاني من التهاب في المناطق التناسلية بحيث لا أستطيع تمرير الماء يسهولة و هناك مجموعة من الحبوب المنتشرة في داخل السفتين الصغيرتين ( منطقة المهبل ) ما هو... | Evidence | 0.9196 | - | - | 0.1181 | 0.9196 | 0.4025 | query relevance+source quality+direct-QA+relation support |
| 6 | 11 | اسباب كثيره مثل الالتهابات البوليه او التهاب الفرج والمهبل | Evidence | 0.9162 | - | - | 0.0269 | 0.9162 | 0.3763 | query relevance+source quality+direct-QA+relation support |
| 7 | 8 | قد يكون السبب ان الحمل ضعيف ومهدد بالاجهاض او حمل خارج الرحم او حمل عنقودي او اسباب اخرى في الجهاز التناسلي مثل التهابات او جروح او لحميات | Evidence | 0.9168 | - | - | 0.0 | 0.9168 | 0.3689 | query relevance+source quality+direct-QA+relation support |
| 8 | 12 | اللحمه الزائده المتدليه بجانب المهبل تقريبا أخبرتني الطبيبه انها التهاب و لاتختفي يجب ان تستئصل ولا تحمل نفسها اي شئ قد هل هذا صحيح انها لاتختفي ؟؟ افيدوني فهذا مزعج | Evidence | 0.9157 | - | - | 0.1451 | 0.9157 | 0.3533 | query relevance+source quality+direct-QA+relation support |
| 9 | 6 | ما علاقة التهاب المهبل اثناء الحمل بنزول الماء الكثير في الشهر 8 | Evidence | 0.9201 | - | - | 0.1181 | 0.9201 | 0.3328 | query relevance+source quality+direct-QA+relation support |
| 10 | - | عندي التهابات مهبلية لونها اصفر واحيانا احمر وهي عندي منذ عام كامل | Evidence | - | - | - | 0.0912 | - | 0.3243 | query relevance+source quality+direct-QA+relation support |

### Step 11: Final evidence context

Context contains `0` graph facts and `3` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- `E1` / source `ahd10k_05174` / QA `ahd10k_05174`: ممكن ان يكون التهاب فطري او هربيس اعملي تحليل دم للهيربي ومسحه للمهبل موءلقتاًً DACTACORT كريم DIFLUCAN حبه في الاسبوع لمده ٤ اسابيع
- `E2` / source `ahd10k_08574` / QA `ahd10k_08574`: ربما يجب فحص البول والمنويات، فقد يكون هناك التهاب في البولي أو في المني.
- `E3` / source `men_merge_0004325` / QA `ahd5k_03068`: التهابات المهبل

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `successful`
- Fallback type: `generated`
- BERTScore F1 against AHD reference: `0.677703`
- End-to-end latency: `15249.592 ms`

**Reference AHD answer**

نعم ، هناك بعض الالتهاب تنتقل من الزوجة الى الزوج ، يفضل عمل فحص بول و زراعة و معالجتين الزوج و الزوجه معا .

**Generated answer before mitigation**

نعم، يمكن أن تنتقل التهابات المهبل من الزوجة إلى الزوج، خاصةً إذا كانت ناجمة عن فطريات أو فيروس الهربس، ما قد يسبب حرقان شديد في العضو الذكري أثناء أو بعد الجماع.

**Final answer after mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| التهابات المهبل قد تكون فطرية (مثل الكانديدا) أو فيروسية (مثل الهربس)، ويمكن أن تنتقل إلى الزوج أثناء الجماع. | `unsupported` | 0.133333 | 0.51 | `E1, E3` | `ahd10k_05174, ahd5k_03068` | The claim lacks sufficient cited support or does not directly answer the query. |
| الزوج المصاب قد يحتاج إلى نفس العلاج الذي يُعطى للزوجة، مع فحص للبول أو المنويات لتحديد وجود التهاب. | `unsupported` | 0.133333 | 0.534091 | `E2` | `ahd10k_08574` | The claim lacks sufficient cited support or does not directly answer the query. |

Warnings:
- Unified LLM query analysis failed: HTTPError
- Planner increased graph depth because the query has age, duration, comparison, or multiple-phrase signals.
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 9 low-value context items; 3 focused items remain.

---

## Example 6: `evalv1_009`

Coverage category: `qa_evidence_dominant`

### Original AHD record

**Question:** اريد ان اعرف البكتيريا التي تسبب الاسهال؟

**Reference answer:** كثيرة هي الجراثيم التي تسبب الإسهال وتسبب أشكال مختلفة من التهابات المعدة والأمعاء ، وبعضه تخترق أنسجة الأمعاء وتنتشر في الدم والجهاز اللمفي والأجهزة الداخلية مسببة مجموعة من الأمراض الهامة وأهم الأنواع هي: الإشريكية القولونية والكلبسيللا والمتحولات والسالمونيللا، والشيغيللا والكوليرا واليرسينيا وغيرها.

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: اريد ان اعرف البكتيريا التي تسبب الاسهال؟
- Normalized: اريد ان اعرف البكتيريا التي تسبب الاسهال?
- Corrected: أريد أن أعرف البكتيريا التي تسبب الإسهال؟
- Reformulated: أريد أن أعرف البكتيريا التي تسبب الإسهال؟
- Class / complexity: `simple_medical` / `low`
- Primary intent: `cause_request`
- Preferred relations: `none`
- Analysis confidence: `0.9`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| الإسهال | Symptom | reformulated_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| الإسهال | الاسهال | `ent_merge_000611` | `exact_canonical` | 1.0 | `linked` |

Retrieval plan: vector=`True`, graph=`True`, hop depth=`1`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_000229`: بكتيريا
- `ent_merge_000059`: التهاب
- `ent_merge_000230`: بكتيريا الهيليكوباكتر بيلوري
- `ent_merge_000001`: bacteremia
- `ent_merge_000717`: تجمع السوائل

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| _No graph relation returned_ | - | - | - |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd10k_00299` | كثيرة هي الجراثيم التي تسبب الإسهال وتسبب أشكال مختلفة من التهابات المعدة والأمعاء ، وبعضه تخترق أنسجة الأمعاء وتنتشر في الدم والجهاز اللمفي والأجهزة الداخلية مسببة مجموعة من الأمراض الهامة وأهم الأنواع هي: الإشريكية القولونية والكلبسيللا والمتحولات والسالم... | 0.957334041595459 | `ahd10k_00299` | `preprocessed_source_row` |
| `men_merge_0001892` | كثيرة هي الجراثيم التي تسبب الإسهال وتسبب أشكال مختلفة من التهابات المعدة والأمعاء | 0.9339346885681152 | `ahd10k_00299` | `preprocessed_source_row` |
| `men_merge_0003265` | الإسهال. الغثيان. الاضطرابات التي تصيب الجهاز الهضمي. | 0.9253973960876465 | `ahd10k_05151` | `preprocessed_source_row` |
| `men_merge_0001293` | ارى انه يجب البحث عن السبب وعلى الاغلب هو بكتيريا الهيليكوباكتر بيلوري ولهذا يجب عمل الفحص للتأكد من ذلك | 0.9235754013061523 | `ahd10k_03072` | `mention_evidence` |
| `ahd10k_02325` | غالبا ماتكون عبارة عن التهاب فطري | 0.9233489036560059 | `ahd10k_02325` | `mention_evidence` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd10k_00299` | اريد ان اعرف البكتيريا التي تسبب الاسهال؟ | كثيرة هي الجراثيم التي تسبب الإسهال وتسبب أشكال مختلفة من التهابات المعدة والأمعاء ، وبعضه تخترق أنسجة الأمعاء وتنتشر في الدم والجهاز اللمفي والأجهزة الداخلية مسببة مجموعة من الأمراض الهامة وأهم الأنواع هي: الإشريكية القولونية والكلبسيللا والمتحولات والسالم... | 0.957334041595459 |
| `ahd10k_05151` | ماذا يحدث عند شرب الحلبة يوميا؟ أي ما هي الآثار الجانبية المرتبطة بها؟ | يسعى العديد من الأشخاص إلى استهلاك الحلبة نظراً للعديد من الفوائد المحتملة المرتبطة بها، ولكن عند استهلاك الحلبة بصورة يومية قد يخشى البعض من الآثار الجانبية المرتبطة بها، ولذا تكثر تساؤلات ماذا يحدث عند شرب الحلبة يوميا؟ إن استهلاك الحلبة بصورة يومية يرتبط... | 0.9253973960876465 |
| `ahd10k_03072` | يادكتور الله يرضى عليك ... عندي التهاب في جدار المعده والاثنى عشر | ارى انه يجب البحث عن السبب وعلى الاغلب هو بكتيريا الهيليكوباكتر بيلوري ولهذا يجب عمل الفحص للتأكد من ذلك | 0.9235754013061523 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | اريد ان اعرف البكتيريا التي تسبب الاسهال؟ | QA | 0.9573 | - | - | 1.0 | 0.9573 | 0.8698 | query relevance+source quality+direct-QA+relation support |
| 2 | 2 | كثيرة هي الجراثيم التي تسبب الإسهال وتسبب أشكال مختلفة من التهابات المعدة والأمعاء | Evidence | 0.9339 | - | - | 1.0 | 0.9339 | 0.7908 | query relevance+source quality+direct-QA+relation support |
| 3 | 6 | التهاب بكتيري او فطري | QA | 0.9226 | - | - | 0.4154 | 0.9226 | 0.4888 | query relevance+source quality+direct-QA+relation support |
| 4 | 12 | عسر الهضم (Dyspepsia)، وهو ناجماً عن مرض من أمراض المعدة كالتهاب المعدة بالجرثومة الحلزونية أو القرحة المعدية أو الإثني عشرية | Evidence | 0.9184 | - | - | 0.4091 | 0.9184 | 0.4582 | query relevance+source quality+direct-QA+relation support |
| 5 | 3 | الإسهال. الغثيان. الاضطرابات التي تصيب الجهاز الهضمي. | Evidence | 0.9254 | - | - | 0.0 | 0.9254 | 0.4062 | query relevance+source quality+direct-QA+relation support |
| 6 | 11 | اعتقد بانها بكتيري بمجرد اعتقادك بوجودها | Evidence | 0.9187 | - | - | 0.15 | 0.9187 | 0.3955 | query relevance+source quality+direct-QA+relation support |
| 7 | 5 | - | QA | 0.9233 | - | - | 0.0 | 0.9233 | 0.3727 | query relevance+source quality+direct-QA+relation support |
| 8 | - | نتبجة لتوسع فتحة الشرج .مالعمل ؟هل هذه بواسير... ام انني اعاني من امساك | Evidence | - | - | - | 0.0 | - | 0.3693 | query relevance+source quality+direct-QA+relation support |
| 9 | - | التهاب بكتيري وفطريات | Evidence | - | - | - | 0.0 | - | 0.3437 | query relevance+source quality+direct-QA+relation support |
| 10 | 8 | السلام عليكم اعاني من غازات والم مغص في المعدة فوق السرة بحوالي اربع اصابع. وكثرة التبرز برائحة كريهة جدا-اكرمكم الله- بعد الاكل مع فقدان للشهية. اعتقد بانها بكتيريا بالمعدة. ما... | QA | 0.9218 | - | - | 0.15 | 0.9218 | 0.3428 | query relevance+source quality+direct-QA+relation support |

### Step 11: Final evidence context

Context contains `0` graph facts and `2` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- `E1` / source `ahd10k_00299` / QA `ahd10k_00299`: كثيرة هي الجراثيم التي تسبب الإسهال وتسبب أشكال مختلفة من التهابات المعدة والأمعاء ، وبعضه تخترق أنسجة الأمعاء وتنتشر في الدم والجهاز اللمفي والأجهزة الداخلية مسببة مجموعة من الأمراض الهامة وأهم الأنواع هي: الإشريكية القولونية والكلبسيللا والمتحولات والسالمونيللا، والشيغيللا والكوليرا واليرسينيا وغيرها.
- `E2` / source `men_merge_0001892` / QA `ahd10k_00299`: كثيرة هي الجراثيم التي تسبب الإسهال وتسبب أشكال مختلفة من التهابات المعدة والأمعاء

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `successful`
- Fallback type: `generated`
- BERTScore F1 against AHD reference: `0.790513`
- End-to-end latency: `9074.931 ms`

**Reference AHD answer**

كثيرة هي الجراثيم التي تسبب الإسهال وتسبب أشكال مختلفة من التهابات المعدة والأمعاء ، وبعضه تخترق أنسجة الأمعاء وتنتشر في الدم والجهاز اللمفي والأجهزة الداخلية مسببة مجموعة من الأمراض الهامة وأهم الأنواع هي: الإشريكية القولونية والكلبسيللا والمتحولات والسالمونيللا، والشيغيللا والكوليرا واليرسينيا وغيرها.

**Generated answer before mitigation**

الجراثيم التي تسبب الإسهال تشمل عدة أنواع، أهمها الإشريكية القولونية، الكلبسيللا، المتحولات، السالمونيللا، الشيغيللا، الكوليرا، واليرسينيا.

**Final answer after mitigation**

أهم أنواع البكتيريا التي تسبب الإسهال هي الإشريكية القولونية، الكلبسيللا، المتحولات، السالمونيللا، الشيغيللا، الكوليرا، واليرسينيا. [E1]

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| أهم أنواع البكتيريا التي تسبب الإسهال هي الإشريكية القولونية، الكلبسيللا، المتحولات، السالمونيللا، الشيغيللا، الكوليرا، واليرسينيا. | `supported` | 0.571429 | 1.0 | `E1` | `ahd10k_00299` | A valid citation supports the claim and the claim directly addresses the query. |

Warnings:
- Unified LLM query analysis failed: HTTPError
- Recovered explicit query intent with deterministic lexical rules; medical phrases remain unextracted.
- cause_request is not directly represented by current graph relation types; vector/evidence retrieval will be needed.
- Graph relation filter disabled for unsupported intent; vector/evidence retrieval should carry the answer.
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 10 low-value context items; 2 focused items remain.

---

## Example 7: `evalv1_010`

Coverage category: `qa_evidence_dominant`

### Original AHD record

**Question:** كيف اجعل شعري يعود كثيفا وطويلا من جديد انا متزوجة

**Reference answer:** تساقط الشعر وكثافته يعتمد على عامل وراثي ، والامراض الوراثية للان لم يتم اكتشاف علاج لها ولكن هناك بعض الادوية تستعمل لفترة طويلة وبحاجة الى صبر تساعد على نمو الشعر وتأخير تساقطه مثل Z-span كبسولة يوميا ودواء سنتروم كبسولة يوميا ، ودهن الرأس بمحلول مينيكسوديل 2%مرة يوميا وتناول اطعمة متوازنة تحتوي على فيتامين ب12 وفيتامين ج وفيتامين إي

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: كيف اجعل شعري يعود كثيفا وطويلا من جديد انا متزوجة
- Normalized: كيف اجعل شعري يعود كثيفا وطويلا من جديد انا متزوجه
- Corrected: كيف أجعل شعري يعود كثيفًا وطويلاً من جديد؟ أنا متزوجة
- Reformulated: كيف يمكنني أن أجعل شعري يعود كثيفًا وطويلاً مرة أخرى؟ أنا متزوجة
- Class / complexity: `simple_medical` / `low`
- Primary intent: `treatment_request`
- Preferred relations: `TREATED_BY, TREATS`
- Analysis confidence: `0.9`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| كثيفًا | Symptom | corrected_query | 0.9 |
| طويلاً | Symptom | corrected_query | 0.9 |
| شعري | Symptom | corrected_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| كثيفًا | - | `-` | `none` | 0.0 | `unresolved` |
| طويلاً | - | `-` | `none` | 0.0 | `unresolved` |
| شعري | - | `-` | `none` | 0.0 | `unresolved` |

Retrieval plan: vector=`True`, graph=`False`, hop depth=`0`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_002180`: زراعة الشعر
- `ent_merge_002193`: علاج تساقط الشعر بالأعشاب
- `ent_merge_001350`: توسيع الشرايين
- `ent_merge_001921`: صبغات الشعر
- `ent_merge_001339`: تناول الأطعمة الغنية بالألياف

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| _No graph relation returned_ | - | - | - |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd5k_01178` | عليك بالذاء الصحي المتوازن و تناول الفيتامينات و عمل فحص للكشف اذا كان هناك فقر دم او لا | 0.927147388458252 | `ahd5k_01178` | `preprocessed_id` |
| `ahd10k_01300` | علاج القشره.. الاكزيما الدهنيه.. أقراص مضاد فطريات مثل فلوكورال 150 حبه الان وتكرر بعد اسبوع.. شامبو كيتوكينازول كما في نبزوال شامبو الذي يستخدم يوميا لمده ٥ دقايق.. مضاد التهاب مثل بتنوقيت محلول لفروه الراس مره يوميا لمده ٣ أسابيع... | 0.9144086837768555 | `ahd10k_01300` | `preprocessed_source_row` |
| `ahd10k_05457` | يمكن التخلص وتجنب قشرة الرأس عن طريق اتباع الخطوات التالية: تجنب استخدام منتجات الشعر التي تحتوي على الكحول لأنها يمكن أن تفاقم القشرة عن طريق زيادة جفاف فروة الرأس. تجنب استخدام منتجات الشعر الزيتية. ترطيب الشعر وفروة الرأس عن طريق استخدام شامبو للتنظيف ثم... | 0.9136419296264648 | `ahd10k_05457` | `preprocessed_source_row` |
| `men_merge_0002289` | انا عمري 24 أعاني من تساقط الشعر منذ أن بلغت بعمر14 بدأت هذه المشكلة بدأ شعري يتساقط بغزارة وبعد الإنجاب أصبح شعري أقرب لالصلع مع العلم أن نسبة دمي10.5 هل... | 0.912811279296875 | `ahd10k_09381` | `mention_evidence` |
| `men_merge_0003868` | - استخدام مركبات الدامفيسيدون ، وهو يؤدي إلى نمو الشعر مرة أخرى | 0.911252498626709 | `ahd10k_09947` | `mention_evidence` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd5k_01178` | شعري لا يطول فحتي عندما اقصه يعود الي طوله قبل القص ولا يزيد عنه وانا ايضا قصيرة فمادا افعل حتي يطول شعري كما انه جاف ومتقصف ويتساقط بكترة ومجعد قليلا... | عليك بالذاء الصحي المتوازن و تناول الفيتامينات و عمل فحص للكشف اذا كان هناك فقر دم او لا | 0.927147388458252 |
| `ahd10k_01300` | شعري بدأ يتساقط منذ سنة لكنه زاد وقد قل طوله كثيرا وأصبح خفيفا وبدأ يظهر لي حبوب في وجهي وفي العادة لا يظهر لي وعندما أمشط شعري كميات غير طبيعية... | علاج القشره.. الاكزيما الدهنيه.. أقراص مضاد فطريات مثل فلوكورال 150 حبه الان وتكرر بعد اسبوع.. شامبو كيتوكينازول كما في نبزوال شامبو الذي يستخدم يوميا لمده ٥ دقايق.. مضاد التهاب مثل بتنوقيت محلول لفروه الراس مره يوميا لمده ٣ أسابيع... | 0.9144086837768555 |
| `ahd10k_05457` | أعاني من كثرة القشرة في شعري رغم أني أغسل شعري يوميا مع العلم أني استعمل هيدأند شولدرز | يمكن التخلص وتجنب قشرة الرأس عن طريق اتباع الخطوات التالية: تجنب استخدام منتجات الشعر التي تحتوي على الكحول لأنها يمكن أن تفاقم القشرة عن طريق زيادة جفاف فروة الرأس. تجنب استخدام منتجات الشعر الزيتية. ترطيب الشعر وفروة الرأس عن طريق استخدام شامبو للتنظيف ثم... | 0.9136419296264648 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | شعري لا يطول فحتي عندما اقصه يعود الي طوله قبل القص ولا يزيد عنه وانا ايضا قصيرة فمادا افعل حتي يطول شعري كما انه جاف ومتقصف ويتساقط بكترة ومجعد قليلا... | QA | 0.9271 | - | - | 0.3708 | 0.9271 | 0.5718 | query relevance+source quality+direct-QA+relation support |
| 2 | 7 | انافتاه وعمري 24 ويوجد بجسمي شعرحيث ان جسمي وشكلي لاتوجد علئ اثار الانوثه وملامح وجهي تميل للرجوله حتي احساسي اتجه البنات يكون غريب والكل ينتقدني اني لست انثي حيث ان... | QA | 0.9102 | - | - | 0.3892 | 0.9102 | 0.566 | query relevance+source quality+direct-QA+relation support |
| 3 | 3 | أعاني من كثرة القشرة في شعري رغم أني أغسل شعري يوميا مع العلم أني استعمل هيدأند شولدرز | QA | 0.9136 | - | - | 0.2854 | 0.9136 | 0.5254 | query relevance+source quality+direct-QA+relation support |
| 4 | 2 | شعري بدأ يتساقط منذ سنة لكنه زاد وقد قل طوله كثيرا وأصبح خفيفا وبدأ يظهر لي حبوب في وجهي وفي العادة لا يظهر لي وعندما أمشط شعري كميات غير طبيعية... | QA | 0.9144 | - | - | 0.2854 | 0.9144 | 0.5218 | query relevance+source quality+direct-QA+relation support |
| 5 | 6 | أنا عمري ١٨ ولا زالت قصير القامة .. | QA | 0.9109 | - | - | 0.0292 | 0.9109 | 0.4616 | query relevance+source quality+direct-QA+relation support |
| 6 | 12 | هل يوجد ضرر من استخدامي فيتامينات برايورين لتقوية الشعر ومنع التساقط وانا مرضعة علماً بان عمر طفلي ستة اشهر ونص | Evidence | 0.9054 | - | - | 0.3857 | 0.9054 | 0.3771 | query relevance+source quality+direct-QA+relation support |
| 7 | 10 | بزيت الزيتون ثم حاولي شدها الى الخارج وذلك لمدة 3 - 5 دقائق 3 مرات في اليوم | Evidence | 0.9076 | - | - | 0.0292 | 0.9076 | 0.3647 | query relevance+source quality+direct-QA+relation support |
| 8 | 8 | كيف يمكن اعادة الانف الى حجمة الطبيعي قبل الحمل والولاده | Evidence | 0.9094 | - | - | 0.0292 | 0.9094 | 0.364 | query relevance+source quality+direct-QA+relation support |
| 9 | 11 | كيف يمكن اعادة الانف الى حجمة الطبيعي | Evidence | 0.9065 | - | - | 0.0292 | 0.9065 | 0.3635 | query relevance+source quality+direct-QA+relation support |
| 10 | 5 | - استخدام مركبات الدامفيسيدون ، وهو يؤدي إلى نمو الشعر مرة أخرى | Evidence | 0.9113 | - | - | 0.2 | 0.9113 | 0.3563 | query relevance+source quality+direct-QA+relation support |

### Step 11: Final evidence context

Context contains `0` graph facts and `2` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- `E1` / source `ahd5k_03407` / QA `ahd5k_03407`: تساقط الشعر بمعدل 50--100شعرة في اليوم أمر طبيعي وغير مرضي ولا يبعث على الانزعاج، لأنه يحل محلها نفس العدد .ينمو شعر الرأس بمعدل سنتمتر واحد في الشهر ، وعدد شعرات الرأس 140ألف شعرة عند الشقر ، و105آلاف عند السمر ،و90ألفعند ذوي اللون الأحمر. أسباب تساقط الشعر متعددة منها : --الحمى الشديدة والالتهابات الجرثومية الحادة والانفلوانزا. --أمراض الغدة الدرقية سوا...
- `E2` / source `men_merge_0005733` / QA `ahd5k_03407`: علاج هذه الحالة هو بالتأكيد علاج السبب المؤدي لها ولكن لتحسن هذه الحالة بصفة عامة اهتم بتناول طعام صحي جيد

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `successful`
- Fallback type: `generated`
- BERTScore F1 against AHD reference: `0.650276`
- End-to-end latency: `14699.436 ms`

**Reference AHD answer**

تساقط الشعر وكثافته يعتمد على عامل وراثي ، والامراض الوراثية للان لم يتم اكتشاف علاج لها ولكن هناك بعض الادوية تستعمل لفترة طويلة وبحاجة الى صبر تساعد على نمو الشعر وتأخير تساقطه مثل Z-span كبسولة يوميا ودواء سنتروم كبسولة يوميا ، ودهن الرأس بمحلول مينيكسوديل 2%مرة يوميا وتناول اطعمة متوازنة تحتوي على فيتامين ب12 وفيتامين ج وفيتامين إي

**Generated answer before mitigation**

تساقط الشعر هو ظاهرة طبيعية تتراوح بين 50–100 شعرة يوميًا، ويستمر نمو الشعر بمعدل تقريبًا سنتيمترًا في الشهر. أهم أسباب تساقط الشعر تشمل العوامل الوراثية، اضطرابات الغدة الدرقية، نقص البروتينات والحديد، التوتر النفسي، وبعض الأدوية (مثل مضادات التخثر، أدوية النقرس، مضادات الاكتئاب، أدوية القلب، أدوية السرطان، أقراص منع الحمل)، وكذلك التعرض للمواد الكيميائية في صبغات ومبيضات الشعر.\n\nلتحسين كثافة وطول الشعر، يوصى باتباع نظام غذائي متوازن غني بالبروتينات والحديد، وتجنب التوتر، واستخدام منتجات تجميلية خفيفة، وتجنب تمشيط الشعر بشكل مفرط أو فركه بشدة.\n\nإذا استمر تساقط الشعر أو لاحظت تغيرات غير طبيعية، يُفضَّل استشارة طبيب مختص لتقييم السبب الدقيق وتحديد العلاج المناسب.

**Final answer after mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| تساقط الشعر الطبيعي يتراوح بين 50–100 شعرة يوميًا ويستمر نمو الشعر بمعدل سنتيمتر في الشهر. | `weakly_supported` | 0.357143 | 0.555714 | `E1` | `ahd5k_03407` | The claim has partial evidence support or only moderate relevance to the query. |
| أسباب تساقط الشعر تشمل العوامل الوراثية، اضطرابات الغدة الدرقية، نقص البروتينات والحديد، التوتر النفسي، وبعض الأدوية (مثل مضادات التخثر، أدوية النقرس، مضادات الاكتئاب، أدوية القلب، أدوية السرطان، أقراص منع الحمل). | `unsupported` | 0.230769 | 0.555714 | `E1` | `ahd5k_03407` | The claim lacks sufficient cited support or does not directly answer the query. |
| تحسين كثافة وطول الشعر يتطلب نظامًا غذائيًا متوازنًا غنيًا بالبروتينات والحديد، وتجنب التوتر، واستخدام منتجات تجميلية خفيفة، وتجنب تمشيط الشعر بشكل مفرط أو فركه بشدة. | `unsupported` | 0.045455 | 0.555714 | `E1, E2` | `ahd5k_03407` | The claim lacks sufficient cited support or does not directly answer the query. |

Warnings:
- Unified LLM query analysis failed: HTTPError
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 10 low-value context items; 2 focused items remain.

---

## Example 8: `evalv1_011`

Coverage category: `qa_evidence_dominant`

### Original AHD record

**Question:** تم عمل منظار للمعدة مرتين وأظهر أن هناك إلتهاب في المرئ والمعدة (شديد ) فما هو العلاج المناسب ؟ المريض أنثي 55 سنة

**Reference answer:** اظن انه يجب ان نعرف السبب لهذا الالتهاب ولهذا من الجيد عمل فحص ال H. pylori واعلامي بالنتيجة

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: تم عمل منظار للمعدة مرتين وأظهر أن هناك إلتهاب في المرئ والمعدة (شديد ) فما هو العلاج المناسب ؟ المريض أنثي 55 سنة
- Normalized: تم عمل منظار للمعده مرتين واظهر ان هناك التهاب في المري والمعده (شديد ) فما هو العلاج المناسب ? المريض انثي 55 سنه
- Corrected: تم عمل منظار للمعدة مرتين وأظهر أن هناك التهاب في المرئ والمعدة (شديد) فما هو العلاج المناسب؟ المريض أنثى 55 سنة
- Reformulated: تم إجراء منظار للمعدة مرتين وأظهر وجود التهاب شديد في المرئ والمعدة. ما هو العلاج المناسب؟ المريضة أنثى تبلغ 55 سنة
- Class / complexity: `simple_medical` / `low`
- Primary intent: `treatment_request`
- Preferred relations: `TREATED_BY, TREATS`
- Analysis confidence: `0.9`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| التهاب في المرئ | DiseaseCondition | corrected_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| التهاب في المرئ | - | `-` | `none` | 0.0 | `unresolved` |

Retrieval plan: vector=`True`, graph=`False`, hop depth=`0`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_001334`: تمارين المعدة
- `ent_merge_001711`: التهابات فى المعدة
- `ent_merge_001077`: منظار هضمي
- `ent_merge_001076`: منظار المعدة
- `ent_merge_002023`: استئصال المرارة بالتنظير

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| _No graph relation returned_ | - | - | - |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd10k_02085` | اظن انه يجب ان نعرف السبب لهذا الالتهاب ولهذا من الجيد عمل فحص ال H. pylori واعلامي بالنتيجة | 0.9566712379455566 | `ahd10k_02085` | `preprocessed_source_row` |
| `men_merge_0001089` | عملت منظار معدة النتيجة التهاب حاد في المعدة | 0.9359345436096191 | `ahd10k_01087` | `mention_evidence` |
| `ahd10k_00637` | في حال فشل الأدوية في علاج الارتجاع المريئي، وبعد عمل الفحوصات اللازمة بما فيها المنظار العلوي في حال فشل الأدوية في علاج الارتجاع المريئي، وبعد عمل الفحوصات اللازمة بما فيها المنظار العلوي فإن للجراحة دورا في علاج مثل هذه الحالات | 0.9355812072753906 | `ahd10k_00637` | `mention_evidence` |
| `men_merge_0001104` | انا طارق من سوريا أعاني منذ شهر من التهاب الحلزوني للمعده وقد عمل منظار للمعده وتم اكتشاف الالتهاب المذمن | 0.9341678619384766 | `ahd10k_09741` | `mention_evidence` |
| `ahd10k_09741` | يحتاج لعلاج ثلاثى: اوميبرازول ، فلاجيل و اموكسيل مع بعض مرتين باليوم | 0.9335551261901855 | `ahd10k_09741` | `mention_evidence` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd10k_02085` | تم عمل منظار للمعدة مرتين وأظهر أن هناك إلتهاب في المرئ والمعدة (شديد ) فما هو العلاج المناسب ؟ المريض أنثي 55 سنة | اظن انه يجب ان نعرف السبب لهذا الالتهاب ولهذا من الجيد عمل فحص ال H. pylori واعلامي بالنتيجة | 0.9566712379455566 |
| `ahd10k_01087` | عملت منظار معدة النتيجة التهاب حاد في المعدة | - | 0.9359345436096191 |
| `ahd10k_00637` | انا امراه عمري 43 اعاني من ارتخاء بالمريء من ثلاث سنوات عالجت عن جرثومه المعده ايضا اعاني من ضيق تنفس | في حال فشل الأدوية في علاج الارتجاع المريئي، وبعد عمل الفحوصات اللازمة بما فيها المنظار العلوي في حال فشل الأدوية في علاج الارتجاع المريئي، وبعد عمل الفحوصات اللازمة بما فيها المنظار العلوي فإن للجراحة دورا في علاج مثل هذه الحالات | 0.9355812072753906 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | تم عمل منظار للمعدة مرتين وأظهر أن هناك إلتهاب في المرئ والمعدة (شديد ) فما هو العلاج المناسب ؟ المريض أنثي 55 سنة | QA | 0.9567 | - | - | 0.7782 | 0.9567 | 0.7561 | query relevance+source quality+direct-QA+relation support |
| 2 | 6 | التهاب في المرئ والمعدة | Evidence | 0.9333 | - | - | 0.7782 | 0.9333 | 0.6857 | query relevance+source quality+direct-QA+relation support |
| 3 | 10 | تم عمل منظار للمعدة | Evidence | 0.9297 | - | - | 0.7782 | 0.9297 | 0.685 | query relevance+source quality+direct-QA+relation support |
| 4 | 5 | انا طارق من سوريا أعاني منذ شهر من التهاب الحلزوني للمعده وقد عمل منظار للمعده وتم اكتشاف الالتهاب المذمن | QA | 0.9336 | - | - | 0.1538 | 0.9336 | 0.4392 | query relevance+source quality+direct-QA+relation support |
| 5 | 12 | هذين الدوائين يستعملن لتقليل حامضيه المعده ولايوجد فيهما خطر يذكر اذا استعملتهما لفتره محدده ولكن والدتك اذا كانت اكبر من ٥٥سنه يستوجب عمل ناضور معده | Evidence | 0.9289 | - | - | 0.2167 | 0.9289 | 0.415 | query relevance+source quality+direct-QA+relation support |
| 6 | - | التهاب حاد في المعدة | Evidence | - | - | - | 0.3333 | - | 0.3841 | query relevance+source quality+direct-QA+relation support |
| 7 | 2 | عملت منظار معدة النتيجة التهاب حاد في المعدة | Evidence | 0.9359 | - | - | 0.275 | 0.9359 | 0.3779 | query relevance+source quality+direct-QA+relation support |
| 8 | 8 | نسبة نجاح استاصال جزء تالف للمرئ وفي اي دولة ممكن اجراؤها بنتي عمرها 2و9اشهر شربت مادة البوتاس الحارقة سببت لها انسدادان صغيران لم تنفع التوسيعات معهم 1عن بعد 12cm و2... | QA | 0.9325 | - | - | 0.2346 | 0.9325 | 0.3643 | query relevance+source quality+direct-QA+relation support |
| 9 | - | استاصال جزء تالف للمرئ وفي اي دولة ممكن اجراؤها بنتي عمرها 2و9اشهر شربت مادة البوتاس الحارقة سببت لها انسدادان صغيران لم تنفع التوسيعات معهم 1عن بعد 12cm و2... | Evidence | - | - | - | 0.0346 | - | 0.3638 | query relevance+source quality+direct-QA+relation support |
| 10 | 9 | عملية تنظير المعدة ليست خطيرة وتكون بإدخال منظار وضوء إلى المعدة | Evidence | 0.93 | - | - | 0.0346 | 0.93 | 0.3568 | query relevance+source quality+direct-QA+relation support |

### Step 11: Final evidence context

Context contains `0` graph facts and `1` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- `E1` / source `ahd10k_02085` / QA `ahd10k_02085`: اظن انه يجب ان نعرف السبب لهذا الالتهاب ولهذا من الجيد عمل فحص ال H. pylori واعلامي بالنتيجة

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `successful`
- Fallback type: `generated`
- BERTScore F1 against AHD reference: `0.658279`
- End-to-end latency: `7924.161 ms`

**Reference AHD answer**

اظن انه يجب ان نعرف السبب لهذا الالتهاب ولهذا من الجيد عمل فحص ال H. pylori واعلامي بالنتيجة

**Generated answer before mitigation**

يجب فحص المريء للمريضة لاكتشاف سبب الالتهاب، ومن الأفضل إجراء اختبار للـ H. pylori لتحديد ما إذا كان السبب هو عدوى بكتيرية.

**Final answer after mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| يجب فحص المريء للمريضة لاكتشاف سبب الالتهاب، ومن الأفضل إجراء اختبار للـ H. pylori لتحديد ما إذا كان السبب هو عدوى بكتيرية. | `unsupported` | 0.210526 | 1.0 | `E1` | `ahd10k_02085` | The claim lacks sufficient cited support or does not directly answer the query. |

Warnings:
- Unified LLM query analysis failed: HTTPError
- Recovered explicit query intent with deterministic lexical rules; medical phrases remain unextracted.
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 11 low-value context items; 1 focused items remain.

---

## Example 9: `evalv1_014`

Coverage category: `qa_evidence_dominant`

### Original AHD record

**Question:** السلام عليكم بعد زيارتي لطبيب الأسنان و معالجة السن بدى لون أزرق في اللثة قرب جذر السن و أظن مكان تخدير السن ممكن معرفة السبب

**Reference answer:** ازرقاق اللثة بعد عمل جراحي أو اجراء علاجي قد يكون رضي في بعد الحالات ويسبب هكذا تغير باللون، في حال عدم وجود ألم أو أعراض فموية غير طبيعية فيجب اعطاء المنطقة الوقت الكافي للشفاء والتي قد تكون مدة أسبوع وسطيا، ان استمرت الأعراض لبعدها أو زادت سوءا عندها يجب مراجعة الطبيب لفحص المنطقة والتأكد من العلاج.

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: السلام عليكم بعد زيارتي لطبيب الأسنان و معالجة السن بدى لون أزرق في اللثة قرب جذر السن و أظن مكان تخدير السن ممكن معرفة السبب
- Normalized: السلام عليكم بعد زيارتي لطبيب الاسنان و معالجه السن بدي لون ازرق في اللثه قرب جذر السن و اظن مكان تخدير السن ممكن معرفه السبب
- Corrected: السلام عليكم، بعد زيارتي لطبيب الأسنان ومعالجة السن، بدا لون أزرق في اللثة قرب جذر السن وأظن مكان تخدير السن. هل يمكن معرفة السبب؟
- Reformulated: السلام عليكم، بعد زيارة طبيب الأسنان ومعالجة السن، لاحظت وجود لون أزرق في اللثة قرب جذر السن، وأعتقد أن ذلك قد يكون مرتبطًا بمكان تخدير السن. هل يمكن معرفة السبب؟
- Class / complexity: `simple_medical` / `low`
- Primary intent: `cause_request`
- Preferred relations: `none`
- Analysis confidence: `0.9`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| لون أزرق في اللثة | Symptom | reformulated_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| لون أزرق في اللثة | - | `-` | `none` | 0.0 | `unresolved` |

Retrieval plan: vector=`True`, graph=`False`, hop depth=`0`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_001308`: تبيض الاسنان
- `ent_merge_001680`: الأسنان
- `ent_merge_001578`: مراجعة طبيب الأسنان
- `ent_merge_002144`: تنظيف اللثة
- `ent_merge_001309`: تبييض الأسنان

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| _No graph relation returned_ | - | - | - |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd5k_00736` | الوردي هو اللون الطبيعي للثة السليمة و الاحمرار علامة التهاب ..... و التهاب اللثة في اغلب الاحيان يكمن السبب في اهمال الاعتناء بالنظافة الفمية ... الحل باجراء تنظيف للاسنان عند الطبيب و تفريش الاسنان بطريقة صحيحة و استعال مضمضة طبية و اتباع التعليمات الاضاف... | 0.9365568161010742 | `ahd5k_00736` | `preprocessed_id` |
| `ahd5k_02037` | انصحك بمراجعه طبيبك للكشف والنصيحه | 0.9336795806884766 | `ahd5k_02037` | `preprocessed_id` |
| `ahd5k_00209` | التصبغات السوداء متنوعة المصدر منها ما هو خارجي. و منها ما هو داخلي ... الاحتمالات هنا عديدة منها التدخين ... الطعام و الشراب ... ادوية الحديد ... مضمضة الكلورهيكسيدين ... الترسبات الجيرية ... الخ .... التسوس يكونه اسود اللون لكن يكون هناك نخر او تاكل في سط... | 0.9333324432373047 | `ahd5k_00209` | `preprocessed_id` |
| `ahd10k_02633` | يتوجب اخذ صوره اشعه للسن المجاور لهذه البثره | 0.9325251579284668 | `ahd10k_02633` | `mention_evidence` |
| `ahd10k_04762` | الهالات الزرقاء ربما نقص حديد.رائحه الفم ربما يكون عنده التهابات خلف الانف | 0.931462287902832 | `ahd10k_04762` | `mention_evidence` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd5k_00736` | سبب تغير لون اللثه جزء وردي وجزء احمر ؟؟؟؟ | الوردي هو اللون الطبيعي للثة السليمة و الاحمرار علامة التهاب ..... و التهاب اللثة في اغلب الاحيان يكمن السبب في اهمال الاعتناء بالنظافة الفمية ... الحل باجراء تنظيف للاسنان عند الطبيب و تفريش الاسنان بطريقة صحيحة و استعال مضمضة طبية و اتباع التعليمات الاضاف... | 0.9365568161010742 |
| `ahd5k_02037` | السلام عليكم ● قبل 5 ايام قمت بتبيض اسناني بالليز وتركيب ماسه لكن اليوم لاحظت ان السن التى تم تركيب الماسه بها فقط قد تحول لونها مائل للزهرى فما السبب... | انصحك بمراجعه طبيبك للكشف والنصيحه | 0.9336795806884766 |
| `ahd5k_00209` | السلام عليكم انا اعاني من وجود خطوط سوداء خفيفة على جوانب اضراسي وصولا الى انيابي و يزداد دالك فلا اضن انه تسوس ارجوك اريد الحل سريعا | التصبغات السوداء متنوعة المصدر منها ما هو خارجي. و منها ما هو داخلي ... الاحتمالات هنا عديدة منها التدخين ... الطعام و الشراب ... ادوية الحديد ... مضمضة الكلورهيكسيدين ... الترسبات الجيرية ... الخ .... التسوس يكونه اسود اللون لكن يكون هناك نخر او تاكل في سط... | 0.9333324432373047 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 2 | السلام عليكم ● قبل 5 ايام قمت بتبيض اسناني بالليز وتركيب ماسه لكن اليوم لاحظت ان السن التى تم تركيب الماسه بها فقط قد تحول لونها مائل للزهرى فما السبب... | QA | 0.9337 | - | - | 0.3375 | 0.9337 | 0.575 | query relevance+source quality+direct-QA+relation support |
| 2 | 1 | سبب تغير لون اللثه جزء وردي وجزء احمر ؟؟؟؟ | QA | 0.9366 | - | - | 0.3536 | 0.9366 | 0.5624 | query relevance+source quality+direct-QA+relation support |
| 3 | 4 | ظهرت في لثة الاسنان العلوية بثرة بدون اي الم تلقائي او عند الضغط ماقد يكون السبب !! | QA | 0.9325 | - | - | 0.3625 | 0.9325 | 0.4953 | query relevance+source quality+direct-QA+relation support |
| 4 | 3 | السلام عليكم انا اعاني من وجود خطوط سوداء خفيفة على جوانب اضراسي وصولا الى انيابي و يزداد دالك فلا اضن انه تسوس ارجوك اريد الحل سريعا | QA | 0.9333 | - | - | 0.0849 | 0.9333 | 0.4897 | query relevance+source quality+direct-QA+relation support |
| 5 | 7 | لابد من تحديد السبب عن طريق الفحص واجراء الاشعة قد يكون بسبب سني او خراج لثوي لابد من مراجعة العيادة | Evidence | 0.9286 | - | - | 0.3625 | 0.9286 | 0.4665 | query relevance+source quality+direct-QA+relation support |
| 6 | 11 | قد تكون المشكلة في اللسان وله عدة اسباب مثل التهاب بكتيري او فطري او فيروسي | Evidence | 0.9254 | - | - | 0.2487 | 0.9254 | 0.4404 | query relevance+source quality+direct-QA+relation support |
| 7 | 9 | التسوس يكونه اسود اللون لكن يكون هناك نخر او تاكل في سطح السن | Evidence | 0.9261 | - | - | 0.0849 | 0.9261 | 0.3883 | query relevance+source quality+direct-QA+relation support |
| 8 | 12 | ماهي اضرار تبيض الاسنان | Evidence | 0.9254 | - | - | 0.1018 | 0.9254 | 0.3769 | query relevance+source quality+direct-QA+relation support |
| 9 | 6 | رحت لعدة اطباء لكن لم يقلعو السن ولم يعطوني اي مسكن بسبب الحمل حاليا استخدم القرنفل مع وجود... | Evidence | 0.9298 | - | - | 0.0515 | 0.9298 | 0.3141 | query relevance+source quality+direct-QA+relation support |
| 10 | 10 | قد يكون هناك تقرحات في الفم اللثة واللسان تحتاج الى جل مثل السيلكوسيريل او قد تكون اللثة متراجعه مما يؤدي الى تحسس في الاسنان وفي هذه الحالة تحتاج الى معجون للحساسيه مثل سنسوداين | Evidence | 0.9257 | - | - | 0.0 | 0.9257 | 0.3053 | query relevance+source quality+direct-QA+relation support |

### Step 11: Final evidence context

Context contains `0` graph facts and `1` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- `E1` / source `ahd5k_00736` / QA `ahd5k_00736`: الوردي هو اللون الطبيعي للثة السليمة و الاحمرار علامة التهاب ..... و التهاب اللثة في اغلب الاحيان يكمن السبب في اهمال الاعتناء بالنظافة الفمية ... الحل باجراء تنظيف للاسنان عند الطبيب و تفريش الاسنان بطريقة صحيحة و استعال مضمضة طبية و اتباع التعليمات الاضافية التي يمليها عليك الطبيب

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `successful`
- Fallback type: `generated`
- BERTScore F1 against AHD reference: `0.675437`
- End-to-end latency: `7091.938 ms`

**Reference AHD answer**

ازرقاق اللثة بعد عمل جراحي أو اجراء علاجي قد يكون رضي في بعد الحالات ويسبب هكذا تغير باللون، في حال عدم وجود ألم أو أعراض فموية غير طبيعية فيجب اعطاء المنطقة الوقت الكافي للشفاء والتي قد تكون مدة أسبوع وسطيا، ان استمرت الأعراض لبعدها أو زادت سوءا عندها يجب مراجعة الطبيب لفحص المنطقة والتأكد من العلاج.

**Generated answer before mitigation**

اللون الوردي هو اللون الطبيعي للثة السليمة، أما اللون الأحمر فيدل على التهاب في اللثة. لا توجد معلومات في الأدلة الموفرة حول سبب ظهور لون أزرق في المنطقة القريبة من جذر السن أو مكان التخدير.

**Final answer after mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| اللون الوردي هو اللون الطبيعي للثة السليمة، أما اللون الأحمر فيدل على التهاب في اللثة. | `unsupported` | 0.545455 | 0.36039 | `E1` | `ahd5k_00736` | The claim lacks sufficient cited support or does not directly answer the query. |

Warnings:
- Unified LLM query analysis failed: HTTPError
- Recovered explicit query intent with deterministic lexical rules; medical phrases remain unextracted.
- cause_request is not directly represented by current graph relation types; vector/evidence retrieval will be needed.
- Graph relation filter disabled for unsupported intent; vector/evidence retrieval should carry the answer.
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 11 low-value context items; 1 focused items remain.

---

## Example 10: `evalv1_008`

Coverage category: `strong_graph_coverage`

### Original AHD record

**Question:** لدي إنتفاخ بشكب غير معقول و كأن بطني سينفجر من الإنتفاخ أخشى أن يكون لدي مرض خطير أو تضخم بالكبد أرجو أن تفيدوني ما هي التحاليل اللازمة لأتأكد أنه لا...

**Reference answer:** اخي الكريم يكفي ان يراك طبيب ويفحص بطنك لكي يعلم ما اذا كان هذا هو سمنة او انتفاخ او تضخم لأي عضو داخل البطن او هو استسقاء

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: لدي إنتفاخ بشكب غير معقول و كأن بطني سينفجر من الإنتفاخ أخشى أن يكون لدي مرض خطير أو تضخم بالكبد أرجو أن تفيدوني ما هي التحاليل اللازمة لأتأكد أنه لا...
- Normalized: لدي انتفاخ بشكب غير معقول و كان بطني سينفجر من الانتفاخ اخشي ان يكون لدي مرض خطير او تضخم بالكبد ارجو ان تفيدوني ما هي التحاليل اللازمه لاتاكد انه لا.
- Corrected: لدي انتفاخ غير معقول في البطن، وأخشى أن يكون لدي مرض خطير أو تضخم بالكبد. أرجو أن تفيدوني ما هي التحاليل اللازمة للتأكد من عدم وجود مشكلة.
- Reformulated: لدي انتفاخ غير معقول في البطن، وأخشى أن يكون لدي مرض خطير أو تضخم بالكبد. أرجو أن تفيدوني ما هي التحاليل اللازمة للتأكد من عدم وجود مشكلة.
- Class / complexity: `simple_medical` / `low`
- Primary intent: `test_request`
- Preferred relations: `INVESTIGATED_BY, INVESTIGATES`
- Analysis confidence: `0.9`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| تضخم بالكبد | DiseaseCondition | corrected_query | 0.8 |
| مرض خطير | DiseaseCondition | corrected_query | 0.8 |
| انتفاخ | Symptom | corrected_query | 0.9 |
| تحاليل | Test | corrected_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| تضخم بالكبد | - | `-` | `none` | 0.0 | `unresolved` |
| مرض خطير | - | `-` | `none` | 0.0 | `unresolved` |
| انتفاخ | انتفاخ | `ent_merge_000696` | `exact_canonical` | 1.0 | `linked` |
| تحاليل | تحاليل | `ent_merge_000965` | `exact_canonical` | 1.0 | `linked` |

Retrieval plan: vector=`True`, graph=`True`, hop depth=`2`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_000273`: تضخم الكبد
- `ent_merge_000734`: تضخم البطن
- `ent_merge_000626`: الانتفاخ
- `ent_merge_000522`: مشاكل في الكبد
- `ent_merge_000287`: تكبير الصدر

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| انتفاخ --INVESTIGATED_BY--> آشعة | 0.85 | 0.777413 | `ahd5k_01537` |
| انتفاخ --INVESTIGATED_BY--> الكرياتينين | 0.9 | 0.775413 | `ahd10k_04720` |
| انتفاخ --INVESTIGATED_BY--> اليورك اسد | 0.9 | 0.775413 | `ahd10k_04720` |
| ضيق تنفس --INVESTIGATED_BY--> آشعة | 0.9 | 0.586 | `ahd10k_08138` |
| وجع --INVESTIGATED_BY--> آشعة | 0.85 | 0.564 | `ahd5k_01537` |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd10k_02159` | انتفاخ في البطن | 0.9412870407104492 | `ahd10k_02159` | `mention_evidence` |
| `men_merge_0001586` | هل من ضمن تطور الاتهاب الكبدي انتفاخ البطن بشكل غريب و نزيف الانف | 0.9383354187011719 | `ahd10k_00446` | `mention_evidence` |
| `men_merge_0001493` | انتفاخ قوي | 0.9373488426208496 | `ahd10k_02998` | `mention_evidence` |
| `men_merge_0000610` | واما تضخم البطن فهو ناتج عن تشمع الكبد | 0.9371151924133301 | `ahd10k_06187` | `preprocessed_source_row` |
| `ahd5k_03315` | يجب تغيير نظام الاكل والاعتماد على الاطعمة المليئة بالالياف مثل الخضار والفاكهة ويحب ايضا الاكثار من تناول الماء حوالي 8 اكواب على الاقل وابدأ بتناول الماء عند الاستيقاظ مباشرة بتناول من 2 الى 3 اكواب والباقي قبل الوجبات الثلاثة رياضة المشي مفيدة جدا ايضا ً | 0.936591625213623 | `ahd5k_03315` | `preprocessed_id` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd10k_02159` | مرض والدي المصاب بالتهاب الكبد الوبائي ج انتفاخ في البطن | انتفاخ في البطن | 0.9412870407104492 |
| `ahd10k_00446` | هل من ضمن تطور الاتهاب الكبدي انتفاخ البطن بشكل غريب و نزيف الانف | - | 0.9383354187011719 |
| `ahd10k_02998` | اعاني من التهاب القولون انتفاخ قوي | غازات والانتفاخ في البطن خروج الريح سماع أصوات وقرقرة | 0.9373488426208496 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | انتفاخ --INVESTIGATED_BY--> آشعة | Relation | 0.9341 | 1.0 | 1.0 | 0.16 | 0.7774 | 0.7283 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 2 | 2 | انتفاخ --INVESTIGATED_BY--> الكرياتينين | Relation | 0.9341 | 1.0 | 1.0 | 0.12 | 0.7754 | 0.6848 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 3 | 3 | انتفاخ --INVESTIGATED_BY--> اليورك اسد | Relation | 0.9341 | 1.0 | 1.0 | 0.12 | 0.7754 | 0.6848 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 4 | 4 | ضيق تنفس --INVESTIGATED_BY--> آشعة | Relation | 0.0 | 1.0 | 1.0 | 0.24 | 0.586 | 0.6 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 5 | 5 | وجع --INVESTIGATED_BY--> آشعة | Relation | 0.0 | 1.0 | 1.0 | 0.16 | 0.564 | 0.581 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 6 | 6 | سعال --INVESTIGATED_BY--> آشعة | Relation | 0.0 | 1.0 | 1.0 | 0.16 | 0.564 | 0.549 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 7 | 7 | تنميل --INVESTIGATED_BY--> آشعة | Relation | 0.0 | 1.0 | 1.0 | 0.16 | 0.564 | 0.549 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 8 | - | بناء على المعدلات الطبيعية فإن الارتفاع طفيف والأرجح أنه ناتج عن دهون الكبد، أو تناول أي من الأدوية التي ترفع إنزيمات الكبد قبل إجراء التحاليل، أو الإصابة بالانفلونزا عند إجراء التحاليل وغيرها من الأسباب. | Evidence | - | - | - | 0.574 | - | 0.5347 | query relevance+source quality+direct-QA+relation support |
| 9 | 8 | ضيق التنفس --INVESTIGATED_BY--> آشعة | Relation | 0.0 | 1.0 | 1.0 | 0.08 | 0.56 | 0.534 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 10 | 9 | بلغم --INVESTIGATED_BY--> آشعة | Relation | 0.0 | 1.0 | 1.0 | 0.08 | 0.554 | 0.53 | identity+query_support+semantic+source_quality+intent-entity_conflicts |

### Step 11: Final evidence context

Context contains `0` graph facts and `0` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- No evidence supplied.

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `failed/fallback`
- Fallback type: `insufficient_evidence`
- BERTScore F1 against AHD reference: `unavailable: BERTScore is not computed for an API fallback answer.`
- End-to-end latency: `247.845 ms`

**Reference AHD answer**

اخي الكريم يكفي ان يراك طبيب ويفحص بطنك لكي يعلم ما اذا كان هذا هو سمنة او انتفاخ او تضخم لأي عضو داخل البطن او هو استسقاء

**Generated answer before mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

**Final answer after mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| _Claim audit unavailable because this was an API fallback, not a generated medical answer_ | - | - | - | - | - | - |

Warnings:
- Unified LLM query analysis failed: HTTPError
- Recovered explicit query intent with deterministic lexical rules; medical phrases remain unextracted.
- Planner increased graph depth because the query has age, duration, comparison, or multiple-phrase signals.
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 12 low-value context items; 0 focused items remain.
- No evidence items are available for grounded answer generation.
- Generation skipped because no evidence was retrieved.

---

## Example 11: `evalv1_006`

Coverage category: `qa_evidence_dominant`

### Original AHD record

**Question:** السلام عليكم اني المريض عمري 22 اعاني من ارتفاع ضغط الدم وكذلك عندم انتظامه رغم اخذ الادوية والالتزام بالاكل الصحي قليل الملح،وعند اجراء تحليل الالدستيرون تبين وجود فرط نشاط للهرمون...

**Reference answer:** اذا لم يثبت سبب اخر لارتفاع الضغط .. فأن معالجة خلل الهرمونات بالمتابعة مع طبيب اخصائي دقيق غدد صماء ممكن يسهم باستقرار ضغط الدم لديك بصورة تامة مع تمنياتي بالشفاء العاجل

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: السلام عليكم اني المريض عمري 22 اعاني من ارتفاع ضغط الدم وكذلك عندم انتظامه رغم اخذ الادوية والالتزام بالاكل الصحي قليل الملح،وعند اجراء تحليل الالدستيرون تبين وجود فرط نشاط للهرمون...
- Normalized: السلام عليكم اني المريض عمري 22 اعاني من ارتفاع ضغط الدم وكذلك عندم انتظامه رغم اخذ الادويه والالتزام بالاكل الصحي قليل الملح,وعند اجراء تحليل الالدستيرون تبين وجود فرط نشاط للهرمون.
- Corrected: السلام عليكم، أنا المريض، عمري 22، أعاني من ارتفاع ضغط الدم، وكذلك عندها انتظامه رغم أخذ الأدوية والالتزام بالأكل الصحي قليل الملح، وعند إجراء تحليل الألدوستيرون تبين وجود فرط نشاط للهرمون.
- Reformulated: السلام عليكم، أنا مريض يبلغ من العمر 22 عامًا، أعاني من ارتفاع ضغط الدم، ويستمر رغم تناول الأدوية والالتزام بنظام غذائي قليل الملح. عند إجراء تحليل الألدوستيرون، تبين وجود فرط نشاط للهرمون.
- Class / complexity: `simple_medical` / `low`
- Primary intent: `test_request`
- Preferred relations: `INVESTIGATED_BY, INVESTIGATES`
- Analysis confidence: `0.92`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| الأكل الصحي قليل الملح | Treatment | corrected_query | 0.85 |
| تحليل الألدوستيرون | Test | corrected_query | 0.9 |
| فرط نشاط للهرمون | DiseaseCondition | corrected_query | 0.9 |
| ارتفاع ضغط الدم | DiseaseCondition | corrected_query | 0.95 |
| الأدوية | Treatment | corrected_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| الأكل الصحي قليل الملح | - | `-` | `none` | 0.0 | `unresolved` |
| تحليل الألدوستيرون | - | `-` | `none` | 0.0 | `unresolved` |
| فرط نشاط للهرمون | - | `-` | `none` | 0.0 | `unresolved` |
| ارتفاع ضغط الدم | ارتفاع ضغط الدم | `ent_merge_000010` | `exact_canonical` | 1.0 | `linked` |
| الأدوية | - | `-` | `none` | 0.0 | `unresolved` |

Retrieval plan: vector=`True`, graph=`True`, hop depth=`1`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_000549`: نقص في الهرمونات
- `ent_merge_000554`: نقص هرمونات
- `ent_merge_000539`: نقص الألدوستيرون الكاذب
- `ent_merge_000208`: انخفاض مستويات هرمون الاستروجين
- `ent_merge_000012`: ارتفاع هرمون اللبن

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| ارتفاع ضغط الدم --INVESTIGATED_BY--> اشعة رنين مغناطيسي | 0.9 | 0.770182 | `ahd10k_01742` |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd5k_00671` | ننصح بإعادة الفحص من قبل طبيب للتأكد من مستواه مرة ثانية وإن كان مرتفع اسكمال الفحص الطبي لتحديد درجته وسببه ان أمكن | 0.9347352981567383 | `ahd5k_00671` | `preprocessed_id` |
| `ahd10k_03236` | يفضل مراجعة الطبيب و إذا كان الضغط ضمت الطبيعي فيجب البحث عن أسباب أخرى مسببة للصداع | 0.9319491386413574 | `ahd10k_03236` | `preprocessed_source_row` |
| `ahd10k_05624` | لا يمكن تحديد الحاجة لتناول أدوية لعلاج ضغط الدم المرتفع من قراءة ضغط دم واحدة فقط، حيث أن تناول علاج لضغط الدم وتشخيص مرض ارتفاع ضغط الدم يعتمد على عوامل وأمور عديدة كالتالي: عدد قراءات ضغط الدم المرتفع حيث أن قراءة واحدة مرتفعة لضغط الدم لا تكفي للتشخيص،... | 0.9316878318786621 | `ahd10k_05624` | `preprocessed_source_row` |
| `ahd5k_03465` | هناك زيادة نشاط بسيط جدا يدعى ماقبل السريري افضل اعادة الفحص والمتابعة مع اخصائي الغدد و مبدئيا ممكن اخذ علاج preponplol 10mg ثلاث مرات يوميا | 0.9309501647949219 | `ahd5k_03465` | `preprocessed_id` |
| `ahd10k_02069` | فقر الدم المزمن | 0.9308629035949707 | `ahd10k_02069` | `mention_evidence` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd5k_00671` | السلام عليكم دكتور انا شاب عنري ٢٨ سنه - سويت اليوم فحص لضغط الدم طلع عندي الانبساطي٨٤ الانقباضي ١٦٢ مع العلم انه ودواني بعض القلق اثناء الفحص؟ | ننصح بإعادة الفحص من قبل طبيب للتأكد من مستواه مرة ثانية وإن كان مرتفع اسكمال الفحص الطبي لتحديد درجته وسببه ان أمكن | 0.9347352981567383 |
| `ahd10k_03236` | انا امراة عمري 44 سنة عندي ضغط الدم اما في اليل يألمني راسي مع العلم اني اشرب الدواء ضغط الدم aprosart و biprotens | يفضل مراجعة الطبيب و إذا كان الضغط ضمت الطبيعي فيجب البحث عن أسباب أخرى مسببة للصداع | 0.9319491386413574 |
| `ahd10k_05624` | السلام عليكم انا قمت بقياس ضغط الدم فوجدته 160/100 فهل هذا يستدعي علاج علما باني لست مريض ضغط | لا يمكن تحديد الحاجة لتناول أدوية لعلاج ضغط الدم المرتفع من قراءة ضغط دم واحدة فقط، حيث أن تناول علاج لضغط الدم وتشخيص مرض ارتفاع ضغط الدم يعتمد على عوامل وأمور عديدة كالتالي: عدد قراءات ضغط الدم المرتفع حيث أن قراءة واحدة مرتفعة لضغط الدم لا تكفي للتشخيص،... | 0.9316878318786621 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | ارتفاع ضغط الدم --INVESTIGATED_BY--> اشعة رنين مغناطيسي | Relation | 0.9283 | 1.0 | 1.0 | 0.0968 | 0.7702 | 0.7054 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 2 | 4 | انا اعاني من جميع اعراض نشاط الغده الدرقيه واجريت تحليل وهذه النتائج TSH:0.32 ref range 0.35-5.5 freeT3:3 ref range 2.3-5.4 FreeT4:1.3 ref. Range 0.8-1.8 لذا هل ا عاني نشاط | QA | 0.931 | - | - | 0.294 | 0.931 | 0.5517 | query relevance+source quality+direct-QA+relation support |
| 3 | 1 | السلام عليكم دكتور انا شاب عنري ٢٨ سنه - سويت اليوم فحص لضغط الدم طلع عندي الانبساطي٨٤ الانقباضي ١٦٢ مع العلم انه ودواني بعض القلق اثناء الفحص؟ | QA | 0.9347 | - | - | 0.2773 | 0.9347 | 0.5435 | query relevance+source quality+direct-QA+relation support |
| 4 | - | ننصحك بقياس ضغط الدم وعمل اشعة رنين مغناطى على المخ | Evidence | - | - | - | 0.4938 | - | 0.5337 | query relevance+source quality+direct-QA+relation support |
| 5 | - | من الممكن ان ماتعانى منه راجع الى زيادة بضغط المخ ولذلك ننصحك بقياس ضغط الدم وعمل اشعة رنين مغناطى على المخ مع التواصل معنا على الاستشارات الخاصة بنموقع الطبى وافادتنا بالنتائج ولوصف العلاج المناسب لك مع متابعة حالتك... | Evidence | - | - | - | 0.4659 | - | 0.5259 | query relevance+source quality+direct-QA+relation support |
| 6 | 3 | السلام عليكم انا قمت بقياس ضغط الدم فوجدته 160/100 فهل هذا يستدعي علاج علما باني لست مريض ضغط | QA | 0.9317 | - | - | 0.1905 | 0.9317 | 0.52 | query relevance+source quality+direct-QA+relation support |
| 7 | 2 | انا امراة عمري 44 سنة عندي ضغط الدم اما في اليل يألمني راسي مع العلم اني اشرب الدواء ضغط الدم aprosart و biprotens | QA | 0.9319 | - | - | 0.0789 | 0.9319 | 0.4655 | query relevance+source quality+direct-QA+relation support |
| 8 | - | أشعر بصداع ف العينين و الراس بأستمرار و يوصل الامر الى الأحساس بالقىء و ف بعض الأحيان من شدة الصداع يتم القىء بالفعل ولا أتناول أى أدوية للصداع و بنام... | Evidence | - | - | - | 0.2175 | - | 0.4564 | query relevance+source quality+direct-QA+relation support |
| 9 | 5 | انا فتاة متزوجة عمر 24 سنة ووزنى 60 كجم أعانى من انخفاض شديد فى ضغط الدم منذ 3 شهور | QA | 0.9309 | - | - | 0.2065 | 0.9309 | 0.4552 | query relevance+source quality+direct-QA+relation support |
| 10 | 10 | هناك العديد من الأطعمة التي يمكن أن تساهم في ارتفاع ضغط الدم، وقد تتضمن الآتي: الأطعمة الغنية بالصوديوم، مثل الأطعمة المعلبة والمجمدة والوجبات السريعة. الأطعمة الغنية بالدهون المشبعة والدهون غير المشبعة، مثل اللحوم ال... | Evidence | 0.9279 | - | - | 0.4839 | 0.9279 | 0.4381 | query relevance+source quality+direct-QA+relation support |

### Step 11: Final evidence context

Context contains `0` graph facts and `0` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- No evidence supplied.

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `failed/fallback`
- Fallback type: `insufficient_evidence`
- BERTScore F1 against AHD reference: `unavailable: BERTScore is not computed for an API fallback answer.`
- End-to-end latency: `1109.615 ms`

**Reference AHD answer**

اذا لم يثبت سبب اخر لارتفاع الضغط .. فأن معالجة خلل الهرمونات بالمتابعة مع طبيب اخصائي دقيق غدد صماء ممكن يسهم باستقرار ضغط الدم لديك بصورة تامة مع تمنياتي بالشفاء العاجل

**Generated answer before mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

**Final answer after mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| _Claim audit unavailable because this was an API fallback, not a generated medical answer_ | - | - | - | - | - | - |

Warnings:
- Adjusted phrase 2: normalized_form replaced with project normalization.
- Adjusted phrase 3: normalized_form replaced with project normalization.
- Adjusted phrase 4: normalized_form replaced with project normalization.
- Ignored alias-only match to ادويه because it does not share tokens with the phrase.
- Some extracted phrases were not linked and should rely on vector retrieval.
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 12 low-value context items; 0 focused items remain.
- No evidence items are available for grounded answer generation.
- Generation skipped because no evidence was retrieved.

---

## Example 12: `evalv1_005`

Coverage category: `little_available_evidence`

### Original AHD record

**Question:** عندي ظعف في النظر اليسرى 7/10 واليمنى 10/10ولما زرت الطبيب قالي عندك حول لانو لما اكون بعيد ة الاشخاص مايظهرون لي خاصة من الوجه لا اعرف منهم غير لما احط...

**Reference answer:** بسم الله الرحمن الرحيم هنا الرؤيا بالنظارة احسن . فلا ضير من استمرار لبس النظارة الطبية. في هذا العمر يعتبر النظر ثابت وما راح يضعف اكثر. تحتاجي لمراجعة عيادة العيون كل ستة شهور ويمكن عمل فحوصات للتأكد فيما اذا كنت قد تستفيدي من عملية تصحيح البصر والتخلص من النظارة الطبية .

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: عندي ظعف في النظر اليسرى 7/10 واليمنى 10/10ولما زرت الطبيب قالي عندك حول لانو لما اكون بعيد ة الاشخاص مايظهرون لي خاصة من الوجه لا اعرف منهم غير لما احط...
- Normalized: عندي ظعف في النظر اليسري 7/10 واليمني 10/10ولما زرت الطبيب قالي عندك حول لانو لما اكون بعيد ه الاشخاص مايظهرون لي خاصه من الوجه لا اعرف منهم غير لما احط.
- Corrected: عندي ضعف في النظر اليسرى 7/10 واليمنى 10/10، ولما زرت الطبيب قال إن لديك حُول لأن عندما أكون بعيدًا لا يظهر لي الأشخاص، خاصة من الوجه، لا أعرفهم إلا عندما أضع...
- Reformulated: أعاني من ضعف في النظر اليسرى بدرجة 7/10 واليسرى 10/10، وأشعر بوجود حُول عندما أكون بعيدًا، ولا أرى الأشخاص، خاصة وجوههم، إلا عندما أضع...
- Class / complexity: `simple_medical` / `low`
- Primary intent: `symptom_request`
- Preferred relations: `HAS_SYMPTOM, SYMPTOM_OF`
- Analysis confidence: `0.9`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| ضعف في النظر | Symptom | corrected_query | 0.9 |
| حُول | Symptom | corrected_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| ضعف في النظر | - | `-` | `none` | 0.0 | `unresolved` |
| حُول | - | `-` | `none` | 0.0 | `unresolved` |

Retrieval plan: vector=`True`, graph=`False`, hop depth=`0`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_000217`: انعدام النظر
- `ent_merge_000853`: عدم وضوح الرؤيا
- `ent_merge_000854`: عدم وضوح الرؤية
- `ent_merge_001704`: التهاب العصي البصري
- `ent_merge_001927`: فقدان الوعي

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| _No graph relation returned_ | - | - | - |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd5k_03737` | لا داعي للقلق، لكن ينبغي استبعاد الشقيقة في المقام الأول، فمنها انواع تظهر هكذا | 0.9216809272766113 | `ahd5k_03737` | `preprocessed_id` |
| `ahd5k_03284` | الامراض التي تسبب عدم وضوح الرؤية و الضبابية متعددة ,مثل مرض السكري المتظور , عيوب الانكسار الضوئي مثل قصر النظر او طول النظر او الاستجمام تيزم , اتلالات الشبكية , التهاب العصي البصري . و لكن لم يرد في ادبيات العيون الورم الدماغي . فعليك مراجعة طبيب اخصائي... | 0.9193739891052246 | `ahd5k_03284` | `preprocessed_id` |
| `ahd10k_03669` | قد يتراوح الامر من تحسس اوضعف نظر لابد من فحص كامل للعين وعيوب الابصار وضغط العين وقاع العين كما يجب فحض ضغط الدم و إلتهابات الجيوب الأنفية والاذن لتسببها الالام المرتجعة يجب الفحص عند احد زملاء طب العيون | 0.9171013832092285 | `ahd10k_03669` | `preprocessed_source_row` |
| `ahd5k_00024` | راجع طبيب انف و اذن وحنجرة - راقب مستوى الهيموجلوبين و مستوى السكر و الضغط | 0.9155349731445312 | `ahd5k_00024` | `preprocessed_id` |
| `ahd5k_00665` | يبدو لي انه عرض نفسي آكثر منه عضوي ولكن هذا لا يقلل من أهمية اجراء بعض الفحوصات : صورة دم كاملة فيتامين د فيتامين ب١٢ حديد رسم مخ سكر صايم وفاطر | 0.9154906272888184 | `ahd5k_00665` | `preprocessed_id` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd5k_03737` | اشعر بصداع متقطع في النصف الايسر من رأسي كومضات متقطعّة و دوخة و لا استطيع فتح عيني كاملة يظهر التعب على وجهي والاجهاد بالرغم من عدم فعل اي شيء و... | لا داعي للقلق، لكن ينبغي استبعاد الشقيقة في المقام الأول، فمنها انواع تظهر هكذا | 0.9216809272766113 |
| `ahd5k_03284` | لماذا أحيانا لا تكون الرؤية واضحة و يكون كأن ضبابا حول عيني اليسرى و بعد دلك عيني يزول ذلك الضباب هل هو احتمال اصابتي بورم دماغي. ا | الامراض التي تسبب عدم وضوح الرؤية و الضبابية متعددة ,مثل مرض السكري المتظور , عيوب الانكسار الضوئي مثل قصر النظر او طول النظر او الاستجمام تيزم , اتلالات الشبكية , التهاب العصي البصري . و لكن لم يرد في ادبيات العيون الورم الدماغي . فعليك مراجعة طبيب اخصائي... | 0.9193739891052246 |
| `ahd10k_03669` | اعاني من الم في عيني اليسرى تؤلمني كثيرا حيث الضوء والتركيز يؤلمانها كثيرا ماهو العلاج المناسب لكي يزول الالم | قد يتراوح الامر من تحسس اوضعف نظر لابد من فحص كامل للعين وعيوب الابصار وضغط العين وقاع العين كما يجب فحض ضغط الدم و إلتهابات الجيوب الأنفية والاذن لتسببها الالام المرتجعة يجب الفحص عند احد زملاء طب العيون | 0.9171013832092285 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | اشعر بصداع متقطع في النصف الايسر من رأسي كومضات متقطعّة و دوخة و لا استطيع فتح عيني كاملة يظهر التعب على وجهي والاجهاد بالرغم من عدم فعل اي شيء و... | QA | 0.9217 | - | - | 0.4304 | 0.9217 | 0.5786 | query relevance+source quality+direct-QA+relation support |
| 2 | 5 | اعاني من الم في وسط الراس مع ضعف الاعصاب وكثرة النسيان وتشتت الافكار.. | QA | 0.9155 | - | - | 0.3109 | 0.9155 | 0.5556 | query relevance+source quality+direct-QA+relation support |
| 3 | 4 | السلام عليكم مشكلتي هي أنني لا أشعر بالأريحية دائماً يلازمني دوار خفيف واليوم طوال اليوم أحس بالنعاس ودوار خفيف مزعج ومتعب ومرهق وفقط أريد النوم أصبت بإلتهاب إذن الوسطى مرتين. | QA | 0.9155 | - | - | 0.4 | 0.9155 | 0.5551 | query relevance+source quality+direct-QA+relation support |
| 4 | 3 | اعاني من الم في عيني اليسرى تؤلمني كثيرا حيث الضوء والتركيز يؤلمانها كثيرا ماهو العلاج المناسب لكي يزول الالم | QA | 0.9171 | - | - | 0.2955 | 0.9171 | 0.5356 | query relevance+source quality+direct-QA+relation support |
| 5 | 2 | لماذا أحيانا لا تكون الرؤية واضحة و يكون كأن ضبابا حول عيني اليسرى و بعد دلك عيني يزول ذلك الضباب هل هو احتمال اصابتي بورم دماغي. ا | QA | 0.9194 | - | - | 0.0804 | 0.9194 | 0.484 | query relevance+source quality+direct-QA+relation support |
| 6 | 12 | شعر بصداع متقطع في النصف الايسر من رأسي كومضات متقطعّة و دوخة و لا استطيع فتح عيني كاملة يظهر التعب على وجهي والاجهاد بالرغم من عدم فعل اي شيء و... | Evidence | 0.9094 | - | - | 0.4304 | 0.9094 | 0.4781 | query relevance+source quality+direct-QA+relation support |
| 7 | 10 | أشعر بصداع شديد يرافقه عدم التركيز فيما أقرؤه | Evidence | 0.91 | - | - | 0.4 | 0.91 | 0.4458 | query relevance+source quality+direct-QA+relation support |
| 8 | 11 | انا امراءة فى السبعين اعاني من الام قوية تمتد من الرقبة الى الكتف والظهر حتى الحوض | Evidence | 0.9096 | - | - | 0.2859 | 0.9096 | 0.4373 | query relevance+source quality+direct-QA+relation support |
| 9 | 6 | عندى بقع بنية على جانبى الوجة وانا اعانى من انيميا 10 | Evidence | 0.913 | - | - | 0.089 | 0.913 | 0.3988 | query relevance+source quality+direct-QA+relation support |
| 10 | - | اعاني من خمول وضيقه ونبض بالجسد والم بالاطراف والم في اسفل الظهر والركبتين وتنميل احيانا باالطراف مع ظهور بقع بيضاء في اليدين والقدمين وارق بالنوم وصداع | Evidence | - | - | - | 0.0457 | - | 0.3781 | query relevance+source quality+direct-QA+relation support |

### Step 11: Final evidence context

Context contains `0` graph facts and `0` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- No evidence supplied.

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `failed/fallback`
- Fallback type: `insufficient_evidence`
- BERTScore F1 against AHD reference: `unavailable: BERTScore is not computed for an API fallback answer.`
- End-to-end latency: `1313.128 ms`

**Reference AHD answer**

بسم الله الرحمن الرحيم هنا الرؤيا بالنظارة احسن . فلا ضير من استمرار لبس النظارة الطبية. في هذا العمر يعتبر النظر ثابت وما راح يضعف اكثر. تحتاجي لمراجعة عيادة العيون كل ستة شهور ويمكن عمل فحوصات للتأكد فيما اذا كنت قد تستفيدي من عملية تصحيح البصر والتخلص من النظارة الطبية .

**Generated answer before mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

**Final answer after mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| _Claim audit unavailable because this was an API fallback, not a generated medical answer_ | - | - | - | - | - | - |

Warnings:
- Blocked a newly introduced specific intent to preserve the original query meaning.
- Adjusted phrase 4: normalized_form replaced with project normalization.
- Some extracted phrases were not linked and should rely on vector retrieval.
- Graph expansion was enabled from high-confidence semantic entity seeds.
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 12 low-value context items; 0 focused items remain.
- No evidence items are available for grounded answer generation.
- Generation skipped because no evidence was retrieved.

---

## Example 13: `evalv1_013`

Coverage category: `strong_graph_coverage`

### Original AHD record

**Question:** تعديل السؤال السابق السؤال /لدي تحليل دم +بول وانتم بكرامه بعد أقل من شهر ولست واثق من سلامة دمي من السموم نوع السموم هي حبوب منشطه تُأخذ عن طريق الفم...

**Reference answer:** ما هو إسم الحبوب المنشطة التي تتناولها خاصة الإسم العلمي لها وليس التجاري حيث يُمكن التعرف عليها وبالتالي وصف آثارها

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: تعديل السؤال السابق السؤال /لدي تحليل دم +بول وانتم بكرامه بعد أقل من شهر ولست واثق من سلامة دمي من السموم نوع السموم هي حبوب منشطه تُأخذ عن طريق الفم...
- Normalized: تعديل السوال السابق السوال /لدي تحليل دم +بول وانتم بكرامه بعد اقل من شهر ولست واثق من سلامه دمي من السموم نوع السموم هي حبوب منشطه تاخذ عن طريق الفم.
- Corrected: تعديل السؤال السابق: لدي تحليل دم وبول بعد أقل من شهر، ولست واثقًا من سلامة دمي من السموم. نوع السموم هو حبوب منشِّطة تُأخذ عن طريق الفم.
- Reformulated: لدي تحليل دم وبول بعد أقل من شهر، ولست واثقًا من سلامة دمي من السموم. السموم هي حبوب منشِّطة تُأخذ عن طريق الفم. ما مدى أمان دمّي؟
- Class / complexity: `simple_medical` / `low`
- Primary intent: `test_request`
- Preferred relations: `INVESTIGATED_BY, INVESTIGATES`
- Analysis confidence: `0.9`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| حبوب منشِّطة | Treatment | corrected_query | 0.9 |
| تحليل دم | Test | corrected_query | 0.9 |
| السموم | DiseaseCondition | corrected_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| حبوب منشِّطة | - | `-` | `none` | 0.0 | `unresolved` |
| تحليل دم | تحليل دم | `ent_merge_000983` | `exact_canonical` | 1.0 | `linked` |
| السموم | السموم | `ent_merge_000143` | `exact_canonical` | 1.0 | `linked` |

Retrieval plan: vector=`True`, graph=`True`, hop depth=`2`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_000799`: دم
- `ent_merge_000143`: السموم
- `ent_merge_000647`: الدم
- `ent_merge_000786`: خروجي دم
- `ent_merge_001986`: صورة دم

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| صداع --INVESTIGATED_BY--> فحص دم | 0.95 | 0.649349 | `ahd10k_09267` |
| صداع --INVESTIGATED_BY--> تحاليل مخبرية | 0.9 | 0.64727 | `ahd10k_06789` |
| صداع --INVESTIGATED_BY--> تحاليل مخبرية | 0.9 | 0.64727 | `ahd10k_09577` |
| صداع --INVESTIGATED_BY--> تحليل دم | 0.85 | 0.585913 | `ahd10k_05347` |
| صداع --INVESTIGATED_BY--> تصوير بالرنين المغناطيسي | 0.95 | 0.578783 | `ahd10k_02192` |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd10k_02698` | هذا عادي ولا خطر منه.ولكن اعملي فحص قوة الدم | 0.9247298240661621 | `ahd10k_02698` | `mention_evidence` |
| `ahd10k_01113` | وعليكم السﻻم.نعم آمنة | 0.9221596717834473 | `ahd10k_01113` | `preprocessed_source_row` |
| `ahd10k_00306` | عمل تحليل مخبري وزراعه للبول | 0.9215240478515625 | `ahd10k_00306` | `mention_evidence` |
| `ahd10k_02033` | ** تعود اْسباب ارتفاع حمض البول لامور عديدة احدها الاستعداد الوراثي للاصابة : - قد يكون استخدام المدرات البولية الكيمائية الخافضة للضغط احد اسباب تشكل حمض البول على عكس المدرات العشبية للبول التي تطرح حمض البول. - كما ان استخدام الاسبرين له دور في الارتفاع.... | 0.9207005500793457 | `ahd10k_02033` | `preprocessed_source_row` |
| `men_merge_0005371` | دم | 0.9205999374389648 | `ahd5k_03390` | `preprocessed_id` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd10k_02698` | - | هذا عادي ولا خطر منه.ولكن اعملي فحص قوة الدم | 0.9247298240661621 |
| `ahd10k_01113` | السلام عليكم دكتور عندي سؤال انا حامل بالشهر السادس وعندي التهابات مهبلي دكتوره كتبتلي هاي الادويه هي أمنه في حمل 1 dalacin vaginal ovule 2 cefuzime 500 3 Metrolag 500 | وعليكم السﻻم.نعم آمنة | 0.9221596717834473 |
| `ahd10k_00306` | - | عمل تحليل مخبري وزراعه للبول | 0.9215240478515625 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 2 | صداع --INVESTIGATED_BY--> تحاليل مخبرية | Relation | 0.9188 | 1.0 | 1.0 | 0.087 | 0.6473 | 0.6327 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 2 | 3 | صداع --INVESTIGATED_BY--> تحاليل مخبرية | Relation | 0.9188 | 1.0 | 1.0 | 0.087 | 0.6473 | 0.6327 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 3 | 1 | صداع --INVESTIGATED_BY--> فحص دم | Relation | 0.9144 | 1.0 | 1.0 | 0.0435 | 0.6493 | 0.6255 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 4 | 4 | اريد ان اسأأل عن مرض ارتفاع حمض البول بالدم عند الاطفال وعن دواء الكرنتين واذا هناك مخاطر من استخدامه على الطفل عمره 3 سنوات ارجو الرد السريع | QA | 0.9207 | - | - | 0.6161 | 0.9207 | 0.6144 | query relevance+source quality+direct-QA+relation support |
| 5 | 4 | صداع --INVESTIGATED_BY--> تحليل دم | Relation | 0.0 | 1.0 | 1.0 | 0.2174 | 0.5859 | 0.565 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 6 | 5 | صداع --INVESTIGATED_BY--> تصوير بالرنين المغناطيسي | Relation | 0.0 | 1.0 | 1.0 | 0.1739 | 0.5788 | 0.561 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 7 | 7 | صداع --INVESTIGATED_BY--> فحص طبي | Relation | 0.0 | 1.0 | 1.0 | 0.087 | 0.5614 | 0.536 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 8 | 6 | صداع --INVESTIGATED_BY--> تحليل دم | Relation | 0.0 | 1.0 | 1.0 | 0.087 | 0.5658 | 0.5355 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 9 | 9 | صداع --INVESTIGATED_BY--> تصوير بالرنين المغناطيسي | Relation | 0.0 | 1.0 | 1.0 | 0.087 | 0.5554 | 0.532 | identity+query_support+semantic+source_quality+intent-entity_conflicts |
| 10 | 10 | صداع --INVESTIGATED_BY--> رسم المخ بالكمبيوتر | Relation | 0.0 | 1.0 | 1.0 | 0.087 | 0.5554 | 0.532 | identity+query_support+semantic+source_quality+intent-entity_conflicts |

### Step 11: Final evidence context

Context contains `0` graph facts and `0` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- No evidence supplied.

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `failed/fallback`
- Fallback type: `insufficient_evidence`
- BERTScore F1 against AHD reference: `unavailable: BERTScore is not computed for an API fallback answer.`
- End-to-end latency: `267.628 ms`

**Reference AHD answer**

ما هو إسم الحبوب المنشطة التي تتناولها خاصة الإسم العلمي لها وليس التجاري حيث يُمكن التعرف عليها وبالتالي وصف آثارها

**Generated answer before mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

**Final answer after mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| _Claim audit unavailable because this was an API fallback, not a generated medical answer_ | - | - | - | - | - | - |

Warnings:
- Unified LLM query analysis failed: HTTPError
- Recovered explicit query intent with deterministic lexical rules; medical phrases remain unextracted.
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 12 low-value context items; 0 focused items remain.
- No evidence items are available for grounded answer generation.
- Generation skipped because no evidence was retrieved.

---

## Example 14: `evalv1_012`

Coverage category: `qa_evidence_dominant`

### Original AHD record

**Question:** السلام عليكم عندي مشكلة بلثة ضرس تمت معالجة العصب وازالته لكن اللثة المحيطة بالعصب تؤلم عند لمسها هل هاذا يعني انه تضرر و او في خراج يؤدي الى قلع الضرس...

**Reference answer:** ليس بالضرورة ذلك ... حاولي عمل مساج يومي لتلك المنطقة و اذا كان ذلك مؤلما يمكنك استعمال جل موضعي لالتهاب اللثة و راقبي الوضع بعد ايام ... اذا استمر الالم راجعي الطبيب لان ذلك يعني ان هناك مشكلة باللثة او بالسن او كليهما

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: السلام عليكم عندي مشكلة بلثة ضرس تمت معالجة العصب وازالته لكن اللثة المحيطة بالعصب تؤلم عند لمسها هل هاذا يعني انه تضرر و او في خراج يؤدي الى قلع الضرس...
- Normalized: السلام عليكم عندي مشكله بلثه ضرس تمت معالجه العصب وازالته لكن اللثه المحيطه بالعصب تولم عند لمسها هل هاذا يعني انه تضرر و او في خراج يودي الي قلع الضرس.
- Corrected: السلام عليكم عندي مشكلة لثة ضرس تمت معالجة العصب وإزالته لكن اللثة المحيطة بالعصب تؤلم عند لمسها هل هذا يعني أنه تضرر أو في خراج يؤدي إلى قلع الضرس؟
- Reformulated: السلام عليكم، لدي مشكلة في لثة ضرس تم معالجة العصب وإزالته، لكن اللثة المحيطة بالعصب تؤلم عند لمسها. هل هذا يعني أن هناك تضررًا أو خراجًا يؤدي إلى قلع الضرس؟
- Class / complexity: `simple_medical` / `low`
- Primary intent: `symptom_request`
- Preferred relations: `HAS_SYMPTOM, SYMPTOM_OF, DIAGNOSED_BY, DIAGNOSES`
- Analysis confidence: `0.9`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| قلع الضرس | Treatment | reformulated_query | 0.9 |
| خراج | DiseaseCondition | reformulated_query | 0.9 |
| لثة | Symptom | reformulated_query | 0.9 |
| عصب | Treatment | reformulated_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| قلع الضرس | - | `-` | `none` | 0.0 | `unresolved` |
| خراج | خراج | `ent_merge_000344` | `exact_canonical` | 1.0 | `linked` |
| لثة | - | `-` | `none` | 0.0 | `unresolved` |
| عصب | - | `-` | `none` | 0.0 | `unresolved` |

Retrieval plan: vector=`True`, graph=`True`, hop depth=`2`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_001640`: نزع عصب الضرس
- `ent_merge_000405`: ضرس
- `ent_merge_001738`: الضرس
- `ent_merge_001814`: ضرس العقل
- `ent_merge_001749`: اللثة

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| _No graph relation returned_ | - | - | - |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `ahd10k_02629` | ممكن يكون فيه ضرس مسوس و التسوس واصل للعصب وفيه التهاب تحته | 0.9375109672546387 | `ahd10k_02629` | `mention_evidence` |
| `ahd10k_00842` | يوجد لديك التهاب عصب أو لب حاد يزداد بالأستلقاء راجع الطبيب قبل زيادة حدة الألم | 0.9354286193847656 | `ahd10k_00842` | `preprocessed_source_row` |
| `ahd5k_03019` | يجب إنهاء المعالجة تماما حتى تنتهي من ألم الضرس ان كانت معالجة الجذور جيدة فستغيب الأعراض باذن الله ومن الطبيعي حصول الالم عند العض لمدة اسبوع | 0.9327220916748047 | `ahd5k_03019` | `preprocessed_id` |
| `ahd10k_06061` | لابد ان ينظف الطبيب الجرح مكان الخلع ، لان المضاد الحيوي لاجدوي له في حالات تلوث الجرح بعد الخلع. | 0.9290170669555664 | `ahd10k_06061` | `mention_evidence` |
| `ahd5k_01579` | عندما يشتكى المريض من الاحساس بالساخن والبارد وعلامات متقدمة لتسوس الاسنان او كسر بالسن يصل لمنطقة عصب السن او الضرس | 0.9287114143371582 | `ahd5k_01579` | `preprocessed_id` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd10k_02629` | - | ممكن يكون فيه ضرس مسوس و التسوس واصل للعصب وفيه التهاب تحته | 0.9375109672546387 |
| `ahd10k_00842` | قبل شهر حشيت ضرسي واشعر بالم في الضرس اذا انسدحت او صحيت من النوم وباقي اليوم طبيعي لاشعر باي الم مالحل ؟! | يوجد لديك التهاب عصب أو لب حاد يزداد بالأستلقاء راجع الطبيب قبل زيادة حدة الألم | 0.9354286193847656 |
| `ahd5k_03019` | عملت ٤ جلسات ٣ تنظيف وسحب عصب والرابعة حشو الجذور ووضع مؤقتة عانيت من الم ل٥ ايام قوي ثم زال لكن بعد ٤ ايام رجعلي الم خفيف من حين لاخر... | يجب إنهاء المعالجة تماما حتى تنتهي من ألم الضرس ان كانت معالجة الجذور جيدة فستغيب الأعراض باذن الله ومن الطبيعي حصول الالم عند العض لمدة اسبوع | 0.9327220916748047 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 5 | متى يلجأ الدكتور الي نزع عَصّب السن او الضرس | QA | 0.9287 | - | - | 0.2279 | 0.9287 | 0.526 | query relevance+source quality+direct-QA+relation support |
| 2 | 2 | قبل شهر حشيت ضرسي واشعر بالم في الضرس اذا انسدحت او صحيت من النوم وباقي اليوم طبيعي لاشعر باي الم مالحل ؟! | QA | 0.9354 | - | - | 0.2615 | 0.9354 | 0.5193 | query relevance+source quality+direct-QA+relation support |
| 3 | 4 | سيدي لقد خلعت ضرسي مدة ٥ أيام لكن حدث لي إلتهاب حاد وبقعة الضرس قيحت (أصبحت بالمادة)راجعت طبيبي أعطاني مسكنات +مضادات لكن لا جدوي مازلت أعاني من آلام شديدة. | QA | 0.929 | - | - | 0.0707 | 0.929 | 0.4056 | query relevance+source quality+direct-QA+relation support |
| 4 | 8 | لابد من تحديد السبب عن طريق الفحص واجراء الاشعة قد يكون بسبب سني او خراج لثوي لابد من مراجعة العيادة | Evidence | 0.9224 | - | - | 0.1617 | 0.9224 | 0.3957 | query relevance+source quality+direct-QA+relation support |
| 5 | 3 | عملت ٤ جلسات ٣ تنظيف وسحب عصب والرابعة حشو الجذور ووضع مؤقتة عانيت من الم ل٥ ايام قوي ثم زال لكن بعد ٤ ايام رجعلي الم خفيف من حين لاخر... | QA | 0.9327 | - | - | 0.259 | 0.9327 | 0.3796 | query relevance+source quality+direct-QA+relation support |
| 6 | - | الضرس | Evidence | - | - | - | 0.0 | - | 0.3616 | query relevance+source quality+direct-QA+relation support |
| 7 | 9 | تسوس الأسنان أو أي خراجات باللثة | Evidence | 0.9193 | - | - | 0.0 | 0.9193 | 0.3559 | query relevance+source quality+direct-QA+relation support |
| 8 | 10 | لا، لكن اذا ما كان هناك تحسس أو استجابة جسدية غير ملائمة يمكن أن يحدث ذلك وننصح بإعلام طبيبك | Evidence | 0.9192 | - | - | 0.0 | 0.9192 | 0.3518 | query relevance+source quality+direct-QA+relation support |
| 9 | - | الضرس | Evidence | - | - | - | 0.0 | - | 0.3496 | query relevance+source quality+direct-QA+relation support |
| 10 | 12 | أعاني من التهاب باللثة | Evidence | 0.9183 | - | - | 0.225 | 0.9183 | 0.3347 | query relevance+source quality+direct-QA+relation support |

### Step 11: Final evidence context

Context contains `0` graph facts and `0` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- No evidence supplied.

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `failed/fallback`
- Fallback type: `insufficient_evidence`
- BERTScore F1 against AHD reference: `unavailable: BERTScore is not computed for an API fallback answer.`
- End-to-end latency: `239.331 ms`

**Reference AHD answer**

ليس بالضرورة ذلك ... حاولي عمل مساج يومي لتلك المنطقة و اذا كان ذلك مؤلما يمكنك استعمال جل موضعي لالتهاب اللثة و راقبي الوضع بعد ايام ... اذا استمر الالم راجعي الطبيب لان ذلك يعني ان هناك مشكلة باللثة او بالسن او كليهما

**Generated answer before mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

**Final answer after mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| _Claim audit unavailable because this was an API fallback, not a generated medical answer_ | - | - | - | - | - | - |

Warnings:
- Unified LLM query analysis failed: HTTPError
- Planner increased graph depth because the query has age, duration, comparison, or multiple-phrase signals.
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 12 low-value context items; 0 focused items remain.
- No evidence items are available for grounded answer generation.
- Generation skipped because no evidence was retrieved.

---

## Example 15: `evalv1_015`

Coverage category: `qa_evidence_dominant`

### Original AHD record

**Question:** انا شخص مدخن من ٣ سنوات من امس اصبحت اشعر بصعوبة اخذ النفس لدرجة اشعر بالنعاس وقلة التركيز اليوم رحت للطبيب عملي اكس راي وقلي عندي التهاب قصبات هوائية وصفلي...

**Reference answer:** هذا الدواء يساعد على اسهال اخراج البلغم عندما يكون متخثر. تستطيعين اخذ ٢ ل من الماء اذا ليس لديك مشكل في الكلية. فهو يساعد ايضا على اخراج البلغم. لا تاخذيهما في اليل

### Step 8: Query understanding

- Model/configuration: `openai/gpt-oss-20b` / `query_analysis_v1`
- Original: انا شخص مدخن من ٣ سنوات من امس اصبحت اشعر بصعوبة اخذ النفس لدرجة اشعر بالنعاس وقلة التركيز اليوم رحت للطبيب عملي اكس راي وقلي عندي التهاب قصبات هوائية وصفلي...
- Normalized: انا شخص مدخن من 3 سنوات من امس اصبحت اشعر بصعوبه اخذ النفس لدرجه اشعر بالنعاس وقله التركيز اليوم رحت للطبيب عملي اكس راي وقلي عندي التهاب قصبات هواييه وصفلي.
- Corrected: أنا شخص مدخن منذ 3 سنوات، ومن أمس أصبحت أشعر بصعوبة في أخذ النفس، لدرجة أشعر بالنعاس وقلة التركيز. اليوم رحت للطبيب، وعمل أشعة X‑ray، وقال لي أن لدي التهاب القصبات الهوائية وصف لي…
- Reformulated: ما التوجيه الطبي المناسب بخصوص: أنا شخص مدخن منذ 3 سنوات، ومن أمس أصبحت أشعر بصعوبة في أخذ النفس، لدرجة أشعر بالنعاس وقلة التركيز. اليوم رحت للطبيب، وعمل أشعة X‑ray، وقال لي أن لدي التهاب القصبات الهوائية وصف لي…؟
- Class / complexity: `simple_medical` / `low`
- Primary intent: `test_request`
- Preferred relations: `INVESTIGATED_BY, INVESTIGATES`
- Analysis confidence: `0.9`

| Medical phrase | Type | Source | Confidence |
|---|---|---|---:|
| التهاب القصبات الهوائية | DiseaseCondition | reformulated_query | 0.95 |
| صعوبة في أخذ النفس | Symptom | reformulated_query | 0.9 |
| قلة التركيز | Symptom | reformulated_query | 0.9 |
| أشعة X‑ray | Test | reformulated_query | 0.9 |
| النعاس | Symptom | reformulated_query | 0.9 |

| Phrase | Linked entity | Entity ID | Match | Score | Status |
|---|---|---|---|---:|---|
| التهاب القصبات الهوائية | - | `-` | `none` | 0.0 | `unresolved` |
| صعوبة في أخذ النفس | - | `-` | `none` | 0.0 | `unresolved` |
| قلة التركيز | قلة التركيز | `ent_merge_000872` | `exact_canonical` | 1.0 | `linked` |
| أشعة X‑ray | - | `-` | `none` | 0.0 | `unresolved` |
| النعاس | النعاس | `ent_merge_000687` | `exact_canonical` | 1.0 | `linked` |

Retrieval plan: vector=`True`, graph=`True`, hop depth=`2`, entity/evidence/QA top-k=`10/10/5`.

### Step 9: Retrieval channels

**Semantic entity retrieval**

- `ent_merge_000300`: توسع القصبات الهوائية
- `ent_merge_000078`: التهاب القصبات التحسسي
- `ent_merge_000107`: التهابات الرئوية
- `ent_merge_000057`: التدخين
- `ent_merge_000243`: تدخين

**Graph retrieval**

| Relation | Confidence | Hybrid score | QA |
|---|---:|---:|---|
| _No graph relation returned_ | - | - | - |

**Evidence retrieval**

| Evidence ID | Evidence | Score | QA | Source quality |
|---|---|---:|---|---|
| `men_merge_0001874` | انا مصاب بالعضلة الضامة ولي تقريبا 7 شهور.. عملت اشعة موجات واشعت رنين الحمد لله لا يوجد تمزق... ما هي التمارين المناسبة للاصابة؟ وهل اضع كمادات باردة او حارة يوميا؟ | 0.933384895324707 | `ahd10k_00819` | `preprocessed_source_row` |
| `ahd5k_00714` | يجب اجراء تقييم كامل من حيث القصة المرضية الكاملة والسوابق المرضية والفحص السريري الكامل فالتشخيص التفريقي للموضوع واسع | 0.9314332008361816 | `ahd5k_00714` | `preprocessed_id` |
| `ahd5k_00855` | لا داعي للقلق ولكن ينبغي معرفة تاريخك المرضي واجراء فحص للكشف عن أي علامات سريرية قد تكون موجودة لديك وتساعد في تحديد طبيعة الحالة , فهكذا أعراض ممكن أن تكون ناجمة عن التها ب في الجهاز التنفسي ويمكن تترافق مع فقر الدم أو اضطرابات دموية أو متعلقة بجهاز الدور... | 0.9308609962463379 | `ahd5k_00855` | `preprocessed_id` |
| `men_merge_0001076` | اعاني في بعض الاوقات من ضيق في التنفس وعملت صورة اشعة للصدر والطبيب أخبرني انني اعاني من التهاب قصبات | 0.9306278228759766 | `ahd10k_08138` | `preprocessed_source_row` |
| `ahd10k_01704` | حالتك تشخص من قبل الطبيب النفساني والأوجاع تتبع الحاله النفسيه | 0.9304709434509277 | `ahd10k_01704` | `preprocessed_source_row` |

**Direct QA retrieval**

| QA ID | Similar question | Answer excerpt | Best score |
|---|---|---|---:|
| `ahd10k_00819` | انا مصاب بالعضلة الضامة ولي تقريبا 7 شهور.. عملت اشعة موجات واشعت رنين الحمد لله لا يوجد تمزق... ما هي التمارين المناسبة للاصابة؟ وهل اضع كمادات باردة او حارة يوميا؟ | بعد مرور هذه الفترة الزمنية من التهاب اوتار العضلة الضامة ينصح بعمل جلسات علاج طبيعي منها الحرارة , الموجات فوق الصوتية والمساج وارخاء العضلات | 0.933384895324707 |
| `ahd5k_00714` | اعاني صعوبة تنفس وصداع ودوخه وعدم تركيز | يجب اجراء تقييم كامل من حيث القصة المرضية الكاملة والسوابق المرضية والفحص السريري الكامل فالتشخيص التفريقي للموضوع واسع | 0.9314332008361816 |
| `ahd5k_00855` | انا شاب عمري 25 سنه اصبحت اعاني من صعوبه في التنفس و الارهاق؟ | لا داعي للقلق ولكن ينبغي معرفة تاريخك المرضي واجراء فحص للكشف عن أي علامات سريرية قد تكون موجودة لديك وتساعد في تحديد طبيعة الحالة , فهكذا أعراض ممكن أن تكون ناجمة عن التها ب في الجهاز التنفسي ويمكن تترافق مع فقر الدم أو اضطرابات دموية أو متعلقة بجهاز الدور... | 0.9308609962463379 |

### Step 10: Reranking

| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 3 | انا شاب عمري 25 سنه اصبحت اعاني من صعوبه في التنفس و الارهاق؟ | QA | 0.9309 | - | - | 0.3176 | 0.9309 | 0.5505 | query relevance+source quality+direct-QA+relation support |
| 2 | 8 | اعاني في بعض الاوقات من ضيق في التنفس وعملت صورة اشعة للصدر والطبيب أخبرني انني اعاني من التهاب قصبات | QA | 0.9298 | - | - | 0.3315 | 0.9298 | 0.5358 | query relevance+source quality+direct-QA+relation support |
| 3 | 5 | السلام عليكم انا اعاني من نوبات هلع و وخزات كتيرة في جهة القلب بعد العادة السرية او الاحتلام و عملت فحص للقلب و قلبي سليم الحمد للله كيف تشخصون حالتي | QA | 0.9305 | - | - | 0.2184 | 0.9305 | 0.4984 | query relevance+source quality+direct-QA+relation support |
| 4 | 2 | اعاني صعوبة تنفس وصداع ودوخه وعدم تركيز | QA | 0.9314 | - | - | 0.075 | 0.9314 | 0.4673 | query relevance+source quality+direct-QA+relation support |
| 5 | 12 | انصحك بمراجعه طبيبك للكشف والنصيحه | Evidence | 0.9288 | - | - | 0.3784 | 0.9288 | 0.4612 | query relevance+source quality+direct-QA+relation support |
| 6 | 10 | تهاب | Evidence | 0.9293 | - | - | 0.3949 | 0.9293 | 0.4612 | query relevance+source quality+direct-QA+relation support |
| 7 | 4 | اعاني في بعض الاوقات من ضيق في التنفس وعملت صورة اشعة للصدر والطبيب أخبرني انني اعاني من التهاب قصبات | Evidence | 0.9306 | - | - | 0.3315 | 0.9306 | 0.4466 | query relevance+source quality+direct-QA+relation support |
| 8 | 7 | عندي حساسيه ربوي ولو مشيت شويه بهبط جدا ومدخنه | QA | 0.9301 | - | - | 0.56 | 0.9301 | 0.4392 | query relevance+source quality+direct-QA+relation support |
| 9 | 1 | انا مصاب بالعضلة الضامة ولي تقريبا 7 شهور.. عملت اشعة موجات واشعت رنين الحمد لله لا يوجد تمزق... ما هي التمارين المناسبة للاصابة؟ وهل اضع كمادات باردة او حارة يوميا؟ | Evidence | 0.9334 | - | - | 0.2472 | 0.9334 | 0.4188 | query relevance+source quality+direct-QA+relation support |
| 10 | 11 | التهاب القصبات | Evidence | 0.9292 | - | - | 0.0868 | 0.9292 | 0.3891 | query relevance+source quality+direct-QA+relation support |

### Step 11: Final evidence context

Context contains `0` graph facts and `0` evidence/QA items.

**Graph facts supplied to the generator**

- No graph facts supplied.

**Evidence supplied to the generator**

- No evidence supplied.

### Step 12: Answer generation and claim inspection

- Model: `openai/gpt-oss-20b`
- Provider result: `failed/fallback`
- Fallback type: `insufficient_evidence`
- BERTScore F1 against AHD reference: `unavailable: BERTScore is not computed for an API fallback answer.`
- End-to-end latency: `276.734 ms`

**Reference AHD answer**

هذا الدواء يساعد على اسهال اخراج البلغم عندما يكون متخثر. تستطيعين اخذ ٢ ل من الماء اذا ليس لديك مشكل في الكلية. فهو يساعد ايضا على اخراج البلغم. لا تاخذيهما في اليل

**Generated answer before mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

**Final answer after mitigation**

لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص.

| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |
|---|---|---:|---:|---|---|---|
| _Claim audit unavailable because this was an API fallback, not a generated medical answer_ | - | - | - | - | - | - |

Warnings:
- Unified LLM query analysis failed: HTTPError
- Some QA provenance was reconstructed from mention evidence and should be down-weighted.
- Step 11 removed 12 low-value context items; 0 focused items remain.
- No evidence items are available for grounded answer generation.
- Generation skipped because no evidence was retrieved.

---
