# Trial Graph v1 Step 9A Semantic Retrieval Report

This is the semantic retrieval layer over Step 6 MiniLM embeddings, using Step 8 query understanding for exact-entity and expansion boosts.

## Model

- Retrieval backend used for this run: `lexical`
- Embedding model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Embedded documents searched: 2145

## Retrieval Scoring

- Base score: cosine similarity because embeddings are normalized.
- Hard detected entity boost: exact/alias entity matches from Step 8.
- Soft candidate boost: expansion/semantic candidate entities from Step 8.
- Use `--backend embedding` to run the original vector-search path when the local model cache is available.
- Results are still semantic retrieval only; graph traversal comes later in Step 9C.

## Query Results

### ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟ هل امتنع عن طعام معين يزيد البلغم وانا غير مدخن واخذ علاج للضغط والكوليسترول عمرى 55...

**Top entity docs**
- `0.694106` بلغم (hard_entity_seed; raw=0.344106, boost=0.35)
- `0.53826` حساسية (hard_entity_seed; raw=0.28826, boost=0.25)
- `0.431259` حساسية الصدر (hard_entity_seed; raw=0.081259, boost=0.35)
- `0.401571` الكوليسترول (hard_entity_seed; raw=0.051571, boost=0.35)
- `0.390456` ضغط (hard_entity_seed; raw=0.040456, boost=0.35)

**Top evidence docs**
- `0.520426` بلغم (evidence_for_hard_entity_seed; raw=0.340426, boost=0.18)
- `0.520426` بلغم (evidence_for_hard_entity_seed; raw=0.340426, boost=0.18)
- `0.460426` حساسية (evidence_for_hard_entity_seed; raw=0.340426, boost=0.12)
- `0.420426` ربو (evidence_for_semantic_candidate_entity; raw=0.340426, boost=0.08)
- `0.340426` التهاب (semantic_similarity_only; raw=0.340426, boost=0.0)

**Top qa docs**
- `0.431731` ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟ هل امتنع عن طعام معين يزيد البلغم وانا غير مدخن واخذ (semantic_similarity_only; raw=0.431731, boost=0.0)
- `0.144739` هل لدغة العقرب أو مربعانية بعد 12ساعة من لدغة تبين أن لا توجد اعراض ك احمرار وانتفاخ أو حرارة تكون لدغة غير قاتلة (semantic_similarity_only; raw=0.144739, boost=0.0)
- `0.133156` هل هناك اسباب للحساسية من الباراسيتمول وما الاغذية التى امتنع عنها وما هى الاغذية التى ااكلها (semantic_similarity_only; raw=0.133156, boost=0.0)
- `0.130991` إبني عمر 6 سنوات و يعاني من حساسية الصدر أعطيه بخار الفنتولين و الأتروفين و شراب الزيلون .هل الفيس يفيد أم لا (semantic_similarity_only; raw=0.130991, boost=0.0)
- `0.126959` هل يمكن مواجهة حساسية الارتيكاريا بادوية المناعة بعيدا عن مضادات الهيستامين و الكورتيزون؟ و ما فعالية هذه الادوية؟ و اضر (semantic_similarity_only; raw=0.126959, boost=0.0)

### كيف اعالج علامات الشيخوخة المبكرة بالوجه؟

**Top entity docs**
- `0.491421` الشيخوخة (hard_entity_seed; raw=0.141421, boost=0.35)
- `0.070711` Rhizomelic and Micromelia (semantic_similarity_only; raw=0.070711, boost=0.0)
- `0.062017` انتفاخ (semantic_similarity_only; raw=0.062017, boost=0.0)
- `0.041523` حساسية الصدر (semantic_similarity_only; raw=0.041523, boost=0.0)
- `0.032275` سعال (semantic_similarity_only; raw=0.032275, boost=0.0)

**Top evidence docs**
- `0.366052` الشيخوخة (evidence_for_hard_entity_seed; raw=0.186052, boost=0.18)
- `0.254536` الشيخوخة (evidence_for_hard_entity_seed; raw=0.074536, boost=0.18)
- `0.06742` تهاب (semantic_similarity_only; raw=0.06742, boost=0.0)
- `0.062017` بابونج (semantic_similarity_only; raw=0.062017, boost=0.0)
- `0.059761` انتفاخ (semantic_similarity_only; raw=0.059761, boost=0.0)

**Top qa docs**
- `0.223607` كيف اعالج علامات الشيخوخة المبكرة بالوجه؟ (semantic_similarity_only; raw=0.223607, boost=0.0)
- `0.084515` كيف اعالج تضيق القنوات الموجودة داخل الكبد عند الاطفال (semantic_similarity_only; raw=0.084515, boost=0.0)
- `0.06455` السلام عليكم ، اعاني من حبوب بيضاء صغيره ف اماكن معينه ف الوجه و اتوقع انها حساسية من البيض او اشعة الشمس ، ف كيف يمكنني (semantic_similarity_only; raw=0.06455, boost=0.0)
- `0.062622` كيف اعالج الحلمة المسطحة علما باني في شهري الرابع من الحمل وهو حملي الاول فانا اتمنى وارغب في ارضاع طفلي رضاعة طبيعية؟ (semantic_similarity_only; raw=0.062622, boost=0.0)
- `0.046625` ما هي مواعيد الاشعة والتحاليل اليومية؟ (semantic_similarity_only; raw=0.046625, boost=0.0)

### ماالعلاج الاسعافي لأنخفاض السكر مع فقدان الوعي

**Top entity docs**
- `0.589046` سكر (hard_entity_seed; raw=0.239046, boost=0.35)
- `0.523422` فقدان الوعي (hard_entity_seed; raw=0.173422, boost=0.35)
- `0.346779` مرض السكري (semantic_candidate_entity; raw=0.226779, boost=0.12)
- `0.241747` ضغط الدم (semantic_similarity_only; raw=0.241747, boost=0.0)
- `0.173422` عسل (semantic_similarity_only; raw=0.173422, boost=0.0)

**Top evidence docs**
- `0.349031` فقدان الوعي (evidence_for_hard_entity_seed; raw=0.169031, boost=0.18)
- `0.303718` سكر (evidence_for_hard_entity_seed; raw=0.123718, boost=0.18)
- `0.291289` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.211289, boost=0.08)
- `0.258174` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.178174, boost=0.08)
- `0.250941` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.170941, boost=0.08)

**Top qa docs**
- `0.31053` ماالعلاج الاسعافي لأنخفاض السكر مع فقدان الوعي (semantic_similarity_only; raw=0.31053, boost=0.0)
- `0.103835` كيف يمكن ان يتاثر الجنين باضطرابات السكر في الام بمعنى هل اذا حدث هبوط او ارتفاع للسكر مرة واحدة يتاثر الجنين فوراحيث ان (semantic_similarity_only; raw=0.103835, boost=0.0)
- `0.098514` هل ضعف عضله القلب وضيق ثلاث شرايين في القلب لهم عمليه جراحيه مع العلم أن المريض يعاني من مرض السكر ام يبقى على العلاج ول (semantic_similarity_only; raw=0.098514, boost=0.0)
- `0.096003` تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم (semantic_similarity_only; raw=0.096003, boost=0.0)
- `0.081992` ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر (semantic_similarity_only; raw=0.081992, boost=0.0)

### هل الاشعة المقطعيه بالصبغه للقلب تسبب انتفاخ اسفل الوجه او انتفاخ الغده هل هو طبيعي

**Top entity docs**
- `0.497087` انتفاخ (hard_entity_seed; raw=0.147087, boost=0.35)
- `0.423544` أشعة (hard_entity_seed; raw=0.073544, boost=0.35)
- `0.241666` مرض الغدة الدرقية (semantic_candidate_entity; raw=0.121666, boost=0.12)
- `0.237851` الغدة الدرقية (semantic_candidate_entity; raw=0.117851, boost=0.12)
- `0.141737` التروكسين (semantic_similarity_only; raw=0.141737, boost=0.0)

**Top evidence docs**
- `0.327087` أشعة (evidence_for_hard_entity_seed; raw=0.147087, boost=0.18)
- `0.321737` انتفاخ (evidence_for_hard_entity_seed; raw=0.141737, boost=0.18)
- `0.263333` أشعة (evidence_for_hard_entity_seed; raw=0.083333, boost=0.18)
- `0.238926` أشعة (evidence_for_hard_entity_seed; raw=0.058926, boost=0.18)
- `0.225644` أشعة (evidence_for_hard_entity_seed; raw=0.045644, boost=0.18)

**Top qa docs**
- `0.358902` هل الاشعة المقطعيه بالصبغه للقلب تسبب انتفاخ اسفل الوجه او انتفاخ الغده هل هو طبيعي (semantic_similarity_only; raw=0.358902, boost=0.0)
- `0.119523` انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟ (semantic_similarity_only; raw=0.119523, boost=0.0)
- `0.109109` كان عندي خراج وعملت تنظيف سن مع حشوة موقتة لكن الالم زاد بعد التنظيف هل هو طبيعي.. وهل يلزم الامر اخذ مضاد. (semantic_similarity_only; raw=0.109109, boost=0.0)
- `0.102749` هل التوقف عن اخذ علاج الغده لان النسبه اصبحت كويسه تسبب الوخز في الوجه وشعور شي ما تحت الجلد يمشي و كذلك في القدم و كثره (semantic_similarity_only; raw=0.102749, boost=0.0)
- `0.102062` السلام عليكم ، اعاني من حبوب بيضاء صغيره ف اماكن معينه ف الوجه و اتوقع انها حساسية من البيض او اشعة الشمس ، ف كيف يمكنني (semantic_similarity_only; raw=0.102062, boost=0.0)

### السلام عليكم..ماهو العلاج المناسب لتقليل نسبة الاملاح في الدم النسبة الحالية عندي هي (7.9) عمري 44 سنة /ذكر؟

**Top entity docs**
- `0.410634` النسبة (hard_entity_seed; raw=0.060634, boost=0.35)
- `0.410634` العلاج (hard_entity_seed; raw=0.060634, boost=0.35)
- `0.085749` الهرمون (semantic_similarity_only; raw=0.085749, boost=0.0)
- `0.078689` مرض الغدة الدرقية (semantic_similarity_only; raw=0.078689, boost=0.0)
- `0.078689` خفقان القلب (semantic_similarity_only; raw=0.078689, boost=0.0)

**Top evidence docs**
- `0.277231` العلاج (evidence_for_hard_entity_seed; raw=0.097231, boost=0.18)
- `0.242622` العلاج (evidence_for_hard_entity_seed; raw=0.062622, boost=0.18)
- `0.231709` النسبة (evidence_for_hard_entity_seed; raw=0.051709, boost=0.18)
- `0.14927` فقر الدم (semantic_similarity_only; raw=0.14927, boost=0.0)
- `0.134535` الارتكاريا (semantic_similarity_only; raw=0.134535, boost=0.0)

**Top qa docs**
- `0.355671` السلام عليكم..ماهو العلاج المناسب لتقليل نسبة الاملاح في الدم النسبة الحالية عندي هي (7.9) عمري 44 سنة /ذكر؟ (semantic_similarity_only; raw=0.355671, boost=0.0)
- `0.133963` السلام عليكم انا لدي حساسية الصدر من الصغر وكان عمر 7 اشهر والان استخدم السيروتايد القرص لاكن اشعر باختناق وعدم السعادة  (semantic_similarity_only; raw=0.133963, boost=0.0)
- `0.127827` السلام عليكم عمري43 اعاني ارتفاع الصفراء في الدم وصلت الي 7.6 ويوجد تضخم في الطحال والم ف اسفل البطن وجانبين الي الظهر م (semantic_similarity_only; raw=0.127827, boost=0.0)
- `0.127386` دكتور انا من مصر وعندى مشكلة في الصفائح الدموية ضعيفة ونسبة الأملاح عالية جدا أروح لدكتور ايه؟ (semantic_similarity_only; raw=0.127386, boost=0.0)
- `0.122499` السلام عليكم .نزول دم من المستقيم بكميه كبيره انا متزوجه وعندي طفل ..شكرا (semantic_similarity_only; raw=0.122499, boost=0.0)

### السلام عليكم أنا أشعر ببرودة رأسي -وغذا اصبح ملمس رأسي بارد جاني صداع لايزول بالمسكنات- ذهبت لأفضل أخصائي أنف وأذن وحنجرة قال هذا المرض ماله علاج !! ماهي التحاليل الأزمة...

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.388605` صداع (hard_entity_seed; raw=0.038605, boost=0.35)
- `0.350504` صداع التوتر (hard_entity_seed; raw=0.100504, boost=0.25)
- `0.062869` المراجعة الطبية (semantic_similarity_only; raw=0.062869, boost=0.0)
- `0.061546` ضرس العقل (semantic_similarity_only; raw=0.061546, boost=0.0)
- `0.055989` زيت الحبة السوداء (semantic_similarity_only; raw=0.055989, boost=0.0)

**Top evidence docs**
- `0.2866` صداع (evidence_for_hard_entity_seed; raw=0.1066, boost=0.18)
- `0.241546` صداع (evidence_for_hard_entity_seed; raw=0.061546, boost=0.18)
- `0.234153` صداع (evidence_for_hard_entity_seed; raw=0.054153, boost=0.18)
- `0.230252` صداع (evidence_for_hard_entity_seed; raw=0.050252, boost=0.18)
- `0.227673` صداع (evidence_for_hard_entity_seed; raw=0.047673, boost=0.18)

**Top qa docs**
- `0.559106` السلام عليكم أنا أشعر ببرودة رأسي -وغذا اصبح ملمس رأسي بارد جاني صداع لايزول بالمسكنات- ذهبت لأفضل أخصائي أنف وأذن وحنجر (semantic_similarity_only; raw=0.559106, boost=0.0)
- `0.11776` السلام عليكم انا لدي حساسية الصدر من الصغر وكان عمر 7 اشهر والان استخدم السيروتايد القرص لاكن اشعر باختناق وعدم السعادة  (semantic_similarity_only; raw=0.11776, boost=0.0)
- `0.092089` جاني بعد الوﻻده اتهاب بالغده الدرقيه زياده نشاط علما بانه بعد وﻻدتي السابقه حدث معي كذلك وزال بدون علاج ولكن هذه المره ا (semantic_similarity_only; raw=0.092089, boost=0.0)
- `0.090909` السلام عليكم ورحمه الله اشعر بطغنات في الجهه اليمن من الصدر ويمتد الى الكتف ماسبب هذه الالم؟؟ (semantic_similarity_only; raw=0.090909, boost=0.0)
- `0.082832` السلام عليكم انا مريضة غدة درقية (هاشيموتو) و اتناول الدواء .اريد أن اتبرع لاختي بالكلية هل أستطيع .اذا كان الجواب بنعم  (semantic_similarity_only; raw=0.082832, boost=0.0)

### مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد المستشفی

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.434895` قرحة (hard_entity_seed; raw=0.084895, boost=0.35)
- `0.408124` القرحة (hard_entity_seed; raw=0.058124, boost=0.35)
- `0.408124` النزيف (hard_entity_seed; raw=0.058124, boost=0.35)
- `0.4048` غثيان (hard_entity_seed; raw=0.0548, boost=0.35)
- `0.098639` فيتامين د (semantic_similarity_only; raw=0.098639, boost=0.0)

**Top evidence docs**
- `0.474086` قرحة (evidence_for_hard_entity_seed; raw=0.294086, boost=0.18)
- `0.344399` النزيف (evidence_for_hard_entity_seed; raw=0.164399, boost=0.18)
- `0.344399` غثيان (evidence_for_hard_entity_seed; raw=0.164399, boost=0.18)
- `0.3202` قرحة (evidence_for_hard_entity_seed; raw=0.1402, boost=0.18)
- `0.293147` القرحة (evidence_for_hard_entity_seed; raw=0.113147, boost=0.18)

**Top qa docs**
- `0.436613` مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد ا (semantic_similarity_only; raw=0.436613, boost=0.0)
- `0.135492` اشعر بتدلى الخصيتين بشكل غير طبيعى لدرجة انه يؤثر على طول القضيب اثناء الارتخاء ويوجد بكيس الصفن عروق كثيره ولكنها لا تؤ (semantic_similarity_only; raw=0.135492, boost=0.0)
- `0.134231` ما هي ادويت الحساسيه التي لا تزيد من الوزن (semantic_similarity_only; raw=0.134231, boost=0.0)
- `0.128965` هل تحليل الكريات البيضاء و الحمراء هي نفسها المناعة (semantic_similarity_only; raw=0.128965, boost=0.0)
- `0.124274` ابنة خالتى ولدت بدون رحم وهى فى ال 25 من عمرها هل يوج علاج لهذة الحاله بالجراحه (semantic_similarity_only; raw=0.124274, boost=0.0)

### ما البديل لعمل كراون للضرس في حال كان طول الضرس قصير بسبب كسر وتآكل في السطح بعد حشو عصب مع حجم طبيعي للضرس ،حتى يعود يصبح في طول يسمح بتركيب...

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.405902` الضرس (hard_entity_seed; raw=0.055902, boost=0.35)
- `0.405902` كسر (hard_entity_seed; raw=0.055902, boost=0.35)
- `0.06742` بروز في البطن (semantic_similarity_only; raw=0.06742, boost=0.0)
- `0.06742` تمارين رياضية (semantic_similarity_only; raw=0.06742, boost=0.0)
- `0.060858` الم المعدجة (semantic_similarity_only; raw=0.060858, boost=0.0)

**Top evidence docs**
- `0.24742` كسر (evidence_for_hard_entity_seed; raw=0.06742, boost=0.18)
- `0.232705` الضرس (evidence_for_hard_entity_seed; raw=0.052705, boost=0.18)
- `0.232705` الضرس (evidence_for_hard_entity_seed; raw=0.052705, boost=0.18)
- `0.232705` الضرس (evidence_for_hard_entity_seed; raw=0.052705, boost=0.18)
- `0.232705` الضرس (evidence_for_hard_entity_seed; raw=0.052705, boost=0.18)

**Top qa docs**
- `0.619751` ما البديل لعمل كراون للضرس في حال كان طول الضرس قصير بسبب كسر وتآكل في السطح بعد حشو عصب مع حجم طبيعي للضرس ،حتى يعود يص (semantic_similarity_only; raw=0.619751, boost=0.0)
- `0.112938` انا بنت عمري 22 سنة بدي علاج طبيعي وسريع للبطن.. عندي بروز في البطن... وجربت التمارين فترة بس ما لاحظت نتيجة كبيرة ولأنه (semantic_similarity_only; raw=0.112938, boost=0.0)
- `0.1066` ما هي الوصفة الغذائة والاعشاب المثالية التي ينصح بتناولها لتكبير حجم القضيب (semantic_similarity_only; raw=0.1066, boost=0.0)
- `0.104713` عملت ٤ جلسات ٣ تنظيف وسحب عصب والرابعة حشو الجذور ووضع مؤقتة عانيت من الم ل٥ ايام قوي ثم زال لكن بعد ٤ ايام رجعلي الم خف (semantic_similarity_only; raw=0.104713, boost=0.0)
- `0.09759` كان عندي خراج وعملت تنظيف سن مع حشوة موقتة لكن الالم زاد بعد التنظيف هل هو طبيعي.. وهل يلزم الامر اخذ مضاد. (semantic_similarity_only; raw=0.09759, boost=0.0)

### زوجتي حامل ومنذ بداية حملها لم اتوقف عن الاتصال معهاابدا ..فهل ذلك له علاقه لما تشعر به من حرقه في المهبل...وهل ذلك له تأثير على الجنين....

**Top entity docs**
- `0.465728` حرقه (hard_entity_seed; raw=0.115728, boost=0.35)
- `0.404554` الجنين (hard_entity_seed; raw=0.054554, boost=0.35)
- `0.089087` سعال (semantic_similarity_only; raw=0.089087, boost=0.0)
- `0.073193` ارتفاع ضغط الدم (semantic_similarity_only; raw=0.073193, boost=0.0)
- `0.072739` RAST Test (semantic_similarity_only; raw=0.072739, boost=0.0)

**Top evidence docs**
- `0.295728` حرقه (evidence_for_hard_entity_seed; raw=0.115728, boost=0.18)
- `0.231434` الجنين (evidence_for_hard_entity_seed; raw=0.051434, boost=0.18)
- `0.231434` الجنين (evidence_for_hard_entity_seed; raw=0.051434, boost=0.18)
- `0.158777` الحمل (semantic_similarity_only; raw=0.158777, boost=0.0)
- `0.158777` متلازمة Chiari (semantic_similarity_only; raw=0.158777, boost=0.0)

**Top qa docs**
- `0.595238` زوجتي حامل ومنذ بداية حملها لم اتوقف عن الاتصال معهاابدا ..فهل ذلك له علاقه لما تشعر به من حرقه في المهبل...وهل ذلك له ت (semantic_similarity_only; raw=0.595238, boost=0.0)
- `0.144479` زوجتي حامل دخلت في الشهر الرابع وعند مراجعة الطبيبة تبين من خلال السونر ان الجنين مشوه بوجود كيس من الرأس وحول الرقبة يح (semantic_similarity_only; raw=0.144479, boost=0.0)
- `0.136083` زوجتي حامل لها شهرين وظهرت عندها الغدة هل تؤثر الغدة علي الحمل والجنين ً كثير لكم (semantic_similarity_only; raw=0.136083, boost=0.0)
- `0.13226` اعاني من حموضة وصعوبة في التنفس وصعوبة بلع والم في الجانب الايسر من الصدر مع تعب في الكتف اليسرى بعد ابذال مجهود فهل هذا (semantic_similarity_only; raw=0.13226, boost=0.0)
- `0.130931` هل يوجد تأثير على الجنين في حالة تعاطي أقراص ميزوتاك في بداية الحمل بغرض الإجهاض وأنا الآن اقتنعت باكمال الحمل ولكن قلق  (semantic_similarity_only; raw=0.130931, boost=0.0)

### لمدا كلما انزعجت من شخص ما أشعر بدوار ودقات سريعة للقلب وشعور براسي تقيل تم يغمى علي دون الغياب عن الوعي فما تشخيصكم لهدا وشكراً جزيل

**Top entity docs**
- `0.493019` دقات سريعة للقلب (hard_entity_seed; raw=0.143019, boost=0.35)
- `0.450504` راسي تقيل (hard_entity_seed; raw=0.100504, boost=0.35)
- `0.4033` دوار (hard_entity_seed; raw=0.0533, boost=0.35)
- `0.071067` خصائي الاطفال (semantic_similarity_only; raw=0.071067, boost=0.0)
- `0.065279` سعال (semantic_similarity_only; raw=0.065279, boost=0.0)

**Top evidence docs**
- `0.316364` دقات سريعة للقلب (evidence_for_hard_entity_seed; raw=0.136364, boost=0.18)
- `0.275346` راسي تقيل (evidence_for_hard_entity_seed; raw=0.095346, boost=0.18)
- `0.230252` دوار (evidence_for_hard_entity_seed; raw=0.050252, boost=0.18)
- `0.08547` مضاد حيوي (semantic_similarity_only; raw=0.08547, boost=0.0)
- `0.082572` فقر الدم (semantic_similarity_only; raw=0.082572, boost=0.0)

**Top qa docs**
- `0.443813` لمدا كلما انزعجت من شخص ما أشعر بدوار ودقات سريعة للقلب وشعور براسي تقيل تم يغمى علي دون الغياب عن الوعي فما تشخيصكم لهد (semantic_similarity_only; raw=0.443813, boost=0.0)
- `0.092319` ما هي ادويت الحساسيه التي لا تزيد من الوزن (semantic_similarity_only; raw=0.092319, boost=0.0)
- `0.091409` علاج كونكور 2.5ملجم تم وصفه لي من قبل دكتور القلب حيث انني لدي تشوه خلقي في صمام القلب وحصل لي تعب بسيط خاصه اذا اردت ال (semantic_similarity_only; raw=0.091409, boost=0.0)
- `0.086464` دكتور ما رأيكم في مصاصة الاطفال (لهاية)..؟؟؟ شكرا (semantic_similarity_only; raw=0.086464, boost=0.0)
- `0.086146` منذ دخول الصيف وانا اعاني من ظهور حبوب في وجهي اريد العلاج من خلال الطب البديل وشكرا لكم على مساعدتكم (semantic_similarity_only; raw=0.086146, boost=0.0)

### عندي فقر دم وعملت التحاليل عندي نقص فيتامين دال ونقص حديد وصف لي الدكتور 20 ابرة حديد لمدة شهر هل اخذ هالكمية بهذه المدة آمن أم مضر للجسم ؟ وما...

**Top entity docs**
- `0.459109` نقص حديد (hard_entity_seed; raw=0.109109, boost=0.35)
- `0.452869` فقر دم (hard_entity_seed; raw=0.102869, boost=0.35)
- `0.452869` نقص فيتامين (hard_entity_seed; raw=0.102869, boost=0.35)
- `0.164488` فحص تحاليل مخبرية (semantic_similarity_only; raw=0.164488, boost=0.0)
- `0.109109` تنميل (semantic_similarity_only; raw=0.109109, boost=0.0)

**Top evidence docs**
- `0.344488` نقص حديد (evidence_for_hard_entity_seed; raw=0.164488, boost=0.18)
- `0.27759` نقص فيتامين (evidence_for_hard_entity_seed; raw=0.09759, boost=0.18)
- `0.27759` نقص فيتامين (evidence_for_hard_entity_seed; raw=0.09759, boost=0.18)
- `0.241721` فقر دم (evidence_for_hard_entity_seed; raw=0.061721, boost=0.18)
- `0.193047` فقر الدم (semantic_similarity_only; raw=0.193047, boost=0.0)

**Top qa docs**
- `0.477895` عندي فقر دم وعملت التحاليل عندي نقص فيتامين دال ونقص حديد وصف لي الدكتور 20 ابرة حديد لمدة شهر هل اخذ هالكمية بهذه المدة (semantic_similarity_only; raw=0.477895, boost=0.0)
- `0.121988` اشعر بتنميل من بداية النصف الاسفل من الجسم حتى اسفل القدم عند تحريك الرقبة الى اسفل و انا عندي انيميا هل لها علاقة (semantic_similarity_only; raw=0.121988, boost=0.0)
- `0.120532` اعاني من مشكلة انقطاع الطمث لمدة شهرين كل مرة اي غير منتظمة و عندما زرت اخصائي قال ان عندي مشكلة نقص هرمونات هل يمكن وصف (semantic_similarity_only; raw=0.120532, boost=0.0)
- `0.117655` انا مريضه بالسكر واستخدم فيرومن كبريتات الحديد لان عندي فقر دم مع فيتامين ب وبعد استخدامهم لاحظت ظهور حبوب في ظهري هل له (semantic_similarity_only; raw=0.117655, boost=0.0)
- `0.09759` السلام عليكم . أعاني من فرط نشاط الغدة الدرقية , وأخذ ادويتي بانتظام وكمان أخذ فيتامين د كل شهر حبة . هل أستطيع أخذ فيتا (semantic_similarity_only; raw=0.09759, boost=0.0)

### أود معرفة ما أسباب تدلي المستقيم؟وطرق العلاج؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.422169` العلاج (hard_entity_seed; raw=0.072169, boost=0.35)
- `0.113228` دوالي الخصية (semantic_similarity_only; raw=0.113228, boost=0.0)
- `0.113228` العلاج بالجراحة (semantic_similarity_only; raw=0.113228, boost=0.0)
- `0.109109` العلاج الطبيعي (semantic_similarity_only; raw=0.109109, boost=0.0)
- `0.105409` العلاج بالإبر الصينية (semantic_similarity_only; raw=0.105409, boost=0.0)

**Top evidence docs**
- `0.329071` العلاج (evidence_for_hard_entity_seed; raw=0.149071, boost=0.18)
- `0.295728` العلاج (evidence_for_hard_entity_seed; raw=0.115728, boost=0.18)
- `0.19245` مرهم مايكونازول (semantic_similarity_only; raw=0.19245, boost=0.0)
- `0.169842` دوالي الخصية (semantic_similarity_only; raw=0.169842, boost=0.0)
- `0.169842` العلاج بالجراحة (semantic_similarity_only; raw=0.169842, boost=0.0)

**Top qa docs**
- `0.347183` أود معرفة ما أسباب تدلي المستقيم؟وطرق العلاج؟ (semantic_similarity_only; raw=0.347183, boost=0.0)
- `0.118401` مرحبا اعاني منذ فتره من نبضات قلي قويه واصبحت اشعر بها في جميع اجزاء جسمي خصوصا قبل النوم وضيق تنفس وسرعة التعب وقلق علم (semantic_similarity_only; raw=0.118401, boost=0.0)
- `0.115728` كيف اعلاج التهاب الدم (semantic_similarity_only; raw=0.115728, boost=0.0)
- `0.113228` ماهي علاجات حمى التهاب باطن القدم وباطن اليد وماهي الفحوصات للتاكد من اسباب هذا المرض؟ (semantic_similarity_only; raw=0.113228, boost=0.0)
- `0.112154` اشعر بتدلى الخصيتين بشكل غير طبيعى لدرجة انه يؤثر على طول القضيب اثناء الارتخاء ويوجد بكيس الصفن عروق كثيره ولكنها لا تؤ (semantic_similarity_only; raw=0.112154, boost=0.0)

### كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟

**Top entity docs**
- `0.563007` الجلد المترهل (hard_entity_seed; raw=0.213007, boost=0.35)
- `0.213007` الجراحة التجميلية (semantic_similarity_only; raw=0.213007, boost=0.0)
- `0.197952` ضغط الدم (semantic_similarity_only; raw=0.197952, boost=0.0)
- `0.185695` مرض السكري (semantic_similarity_only; raw=0.185695, boost=0.0)
- `0.160817` تضخم (semantic_similarity_only; raw=0.160817, boost=0.0)

**Top evidence docs**
- `0.662759` الجلد المترهل (evidence_for_hard_entity_seed; raw=0.482759, boost=0.18)
- `0.191785` حمى (semantic_similarity_only; raw=0.191785, boost=0.0)
- `0.180151` الاندرال (semantic_similarity_only; raw=0.180151, boost=0.0)
- `0.170406` الرياضة (semantic_similarity_only; raw=0.170406, boost=0.0)
- `0.170406` الجراحة التجميلية (semantic_similarity_only; raw=0.170406, boost=0.0)

**Top qa docs**
- `0.445851` كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟ (semantic_similarity_only; raw=0.445851, boost=0.0)
- `0.141827` ما هى احتياجات الام الحامل والجنين مع بداية الشهر السادس؟ (semantic_similarity_only; raw=0.141827, boost=0.0)
- `0.134014` هل يمكن ان تحس المرأة بوجع طفيف على مستوى الثدي أثناء الدورة الشرية؟ مع العلم ان الألم على مستوى الثدي الايسر؟ (semantic_similarity_only; raw=0.134014, boost=0.0)
- `0.129302` طفل في الثالثة من العمر يعاني من الم في البطن مع تعرق بارد مع العلم انه اول مرة تحصل معه (semantic_similarity_only; raw=0.129302, boost=0.0)
- `0.120877` اعاني من مشكلة انقطاع الطمث لمدة شهرين كل مرة اي غير منتظمة و عندما زرت اخصائي قال ان عندي مشكلة نقص هرمونات هل يمكن وصف (semantic_similarity_only; raw=0.120877, boost=0.0)

### السلام عليكم عمري43 اعاني ارتفاع الصفراء في الدم وصلت الي 7.6 ويوجد تضخم في الطحال والم ف اسفل البطن وجانبين الي الظهر مع احساس بالتعب تحاليل للفيروسات سلبي ومناعةانكا 1/80

**Top entity docs**
- `0.435126` تضخم (hard_entity_seed; raw=0.085126, boost=0.35)
- `0.429444` تعب (hard_entity_seed; raw=0.079444, boost=0.35)
- `0.101477` خفقان القلب (semantic_similarity_only; raw=0.101477, boost=0.0)
- `0.09325` ارتفاع خضاب الدم (semantic_similarity_only; raw=0.09325, boost=0.0)
- `0.091003` ضيق تنفس (semantic_similarity_only; raw=0.091003, boost=0.0)

**Top evidence docs**
- `0.265126` تضخم (evidence_for_hard_entity_seed; raw=0.085126, boost=0.18)
- `0.259444` تعب (evidence_for_hard_entity_seed; raw=0.079444, boost=0.18)
- `0.135302` إمساك (semantic_similarity_only; raw=0.135302, boost=0.0)
- `0.128332` فقر الدم (semantic_similarity_only; raw=0.128332, boost=0.0)
- `0.119591` الغدة الدرقية (semantic_similarity_only; raw=0.119591, boost=0.0)

**Top qa docs**
- `0.65938` السلام عليكم عمري43 اعاني ارتفاع الصفراء في الدم وصلت الي 7.6 ويوجد تضخم في الطحال والم ف اسفل البطن وجانبين الي الظهر م (semantic_similarity_only; raw=0.65938, boost=0.0)
- `0.133366` اجريت عمليه استبدال صمام ميترالي في 89ثم الاورطي في 2013 والان اعاني من ارتفاع الضغط وضيق تنفس وخفقان احيتنا (semantic_similarity_only; raw=0.133366, boost=0.0)
- `0.123876` السلام عليكم .. أعاني ما يقارب السنتين من تعرجات ( فطريات ) واضحة في لساني من الجهة اليمنى واليسرى بجوار منطقة الطحن مما (semantic_similarity_only; raw=0.123876, boost=0.0)
- `0.118389` السلام عليكم اعاني من غازات والم مغص في المعدة فوق السرة بحوالي اربع اصابع. وكثرة التبرز برائحة كريهة جدا-اكرمكم الله- ب (semantic_similarity_only; raw=0.118389, boost=0.0)
- `0.108893` السلام عليكم ان اعاني من الام في اسفل المعدة علي مستوي الامعاء مع انتفاخ و غازت مع كل واجبة وخاصة عند الصباح ان تناولة ش (semantic_similarity_only; raw=0.108893, boost=0.0)

### اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج للعصب السابع بعد مضي هذه المدة الزمنه

**Top entity docs**
- `0.393519` الطعام (hard_entity_seed; raw=0.043519, boost=0.35)
- `0.088911` بلغم (semantic_similarity_only; raw=0.088911, boost=0.0)
- `0.087039` سعال (semantic_similarity_only; raw=0.087039, boost=0.0)
- `0.083624` الكورتيزونات (semantic_similarity_only; raw=0.083624, boost=0.0)
- `0.08123` تعب (semantic_similarity_only; raw=0.08123, boost=0.0)

**Top evidence docs**
- `0.225455` الطعام (evidence_for_hard_entity_seed; raw=0.045455, boost=0.18)
- `0.13762` التهاب (semantic_similarity_only; raw=0.13762, boost=0.0)
- `0.116775` حساسية (semantic_similarity_only; raw=0.116775, boost=0.0)
- `0.113636` التهاب (semantic_similarity_only; raw=0.113636, boost=0.0)
- `0.1066` ضيق تنفس (semantic_similarity_only; raw=0.1066, boost=0.0)

**Top qa docs**
- `0.538145` اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج  (semantic_similarity_only; raw=0.538145, boost=0.0)
- `0.157313` هل هناك معالجة لمرض بيلة الميوغلوبين ارجو ايفادي به سواء هنا في سوريا او في اي دولة وفي اي مستشفى بالضبط لأني اعاني من ه (semantic_similarity_only; raw=0.157313, boost=0.0)
- `0.142451` ابنتي معاها حساسية معينة لبعض الاطعمة وعمرها سنتان هل تختفي بعد تخطيها 3 سنوات (semantic_similarity_only; raw=0.142451, boost=0.0)
- `0.134022` تركت التدخين منذ خمس سنوات و أشعر بضيق نفس في صدري من حين لآخر و احيانا حرقة في مقدمة الصدر و بدون الشعور بأي ألم و احيا (semantic_similarity_only; raw=0.134022, boost=0.0)
- `0.129272` عند الاستيقاظ في الصباح اشعر بالام اسفل الظهر منذ فترة طويلة ما السبب انا استخدم علاج الثايروكسين هل له تاثير (semantic_similarity_only; raw=0.129272, boost=0.0)

### تناولت مضاد حيووي زييثرون وانتج حساسيه شديده وتورم في المنطقة التناسليه وانا تعبانه جدا ما الحل ؟

**Top entity docs**
- `0.434895` حساسية (hard_entity_seed; raw=0.084895, boost=0.35)
- `0.35171` حساسية الصدر (hard_entity_seed; raw=0.10171, boost=0.25)
- `0.131762` سعال (semantic_similarity_only; raw=0.131762, boost=0.0)
- `0.107676` بلغم (semantic_similarity_only; raw=0.107676, boost=0.0)
- `0.09759` تيليفاست (semantic_similarity_only; raw=0.09759, boost=0.0)

**Top evidence docs**
- `0.425955` حساسية (evidence_for_hard_entity_seed; raw=0.245955, boost=0.18)
- `0.299523` حساسية (evidence_for_hard_entity_seed; raw=0.119523, boost=0.18)
- `0.286525` حساسية (evidence_for_hard_entity_seed; raw=0.106525, boost=0.18)
- `0.281274` حساسية (evidence_for_hard_entity_seed; raw=0.101274, boost=0.18)
- `0.281274` حساسية (evidence_for_hard_entity_seed; raw=0.101274, boost=0.18)

**Top qa docs**
- `0.46188` تناولت مضاد حيووي زييثرون وانتج حساسيه شديده وتورم في المنطقة التناسليه وانا تعبانه جدا ما الحل ؟ (semantic_similarity_only; raw=0.46188, boost=0.0)
- `0.138013` اعاني من حساسية في الصدر وضيق في التنفس وسعال وقئ صباحا (semantic_similarity_only; raw=0.138013, boost=0.0)
- `0.119866` سوألي هناك فتاه تشعر بحراره شديده في جسمها الخارجي وقليل جدا من داخل جسمها ولاترتاح الا بالاغتسال ومستمر الحال معها قراب (semantic_similarity_only; raw=0.119866, boost=0.0)
- `0.107676` انا قبل يجي طقطقة في الفك الايسر بدون اللم وبعد ما سويت التمرين راح طقطقة الفك وجاني اللم هل هذا امر عادي بسبب التمرين و (semantic_similarity_only; raw=0.107676, boost=0.0)
- `0.103975` هل من علاج لحالتي فأنا أشعر بآلام قوية في مفصل الركبة الأيسر أثناء المشي و الوقوف علماً بأنني مصاب بعواقب شلل الأطفال ال (semantic_similarity_only; raw=0.103975, boost=0.0)

### انا اشعر بالصداع والنعاس وحساسية في وجهي والحكة بكل انحاء جسمي كيف استطيع ان اوقف هذا الدواء

**Top entity docs**
- `0.408124` حكة (hard_entity_seed; raw=0.058124, boost=0.35)
- `0.392098` صداع (hard_entity_seed; raw=0.042098, boost=0.35)
- `0.388222` حساسية (hard_entity_seed; raw=0.038222, boost=0.35)
- `0.38428` الدواء (hard_entity_seed; raw=0.03428, boost=0.35)
- `0.359599` صداع التوتر (hard_entity_seed; raw=0.109599, boost=0.25)

**Top evidence docs**
- `0.43793` حساسية (evidence_for_hard_entity_seed; raw=0.25793, boost=0.18)
- `0.289599` صداع (evidence_for_hard_entity_seed; raw=0.109599, boost=0.18)
- `0.287624` حساسية (evidence_for_hard_entity_seed; raw=0.107624, boost=0.18)
- `0.27592` حساسية (evidence_for_hard_entity_seed; raw=0.09592, boost=0.18)
- `0.271192` حساسية (evidence_for_hard_entity_seed; raw=0.091192, boost=0.18)

**Top qa docs**
- `0.462147` انا اشعر بالصداع والنعاس وحساسية في وجهي والحكة بكل انحاء جسمي كيف استطيع ان اوقف هذا الدواء (semantic_similarity_only; raw=0.462147, boost=0.0)
- `0.128418` السلام عليكم انا لدي حساسية الصدر من الصغر وكان عمر 7 اشهر والان استخدم السيروتايد القرص لاكن اشعر باختناق وعدم السعادة  (semantic_similarity_only; raw=0.128418, boost=0.0)
- `0.12392` السلام عليكم ورحمه الله اشعر بطغنات في الجهه اليمن من الصدر ويمتد الى الكتف ماسبب هذه الالم؟؟ (semantic_similarity_only; raw=0.12392, boost=0.0)
- `0.121197` انا قبل يجي طقطقة في الفك الايسر بدون اللم وبعد ما سويت التمرين راح طقطقة الفك وجاني اللم هل هذا امر عادي بسبب التمرين و (semantic_similarity_only; raw=0.121197, boost=0.0)
- `0.11291` السلام عليكم انا مريضة غدة درقية (هاشيموتو) و اتناول الدواء .اريد أن اتبرع لاختي بالكلية هل أستطيع .اذا كان الجواب بنعم  (semantic_similarity_only; raw=0.11291, boost=0.0)

### لا أستطبع النوم على جانبي لا الأيمن ولا الأيسر وأجد صعوبة في التنفس العميق. كما أشعر بين الفينة والأخرى بآلام قرب القلب. كما أخبركم أني مريصة بالقلب (مشكل في صمامتين)

**Top entity docs**
- `0.381798` الام (hard_entity_seed; raw=0.031798, boost=0.35)
- `0.082169` Tiroxine (semantic_similarity_only; raw=0.082169, boost=0.0)
- `0.080875` Hashimot (semantic_similarity_only; raw=0.080875, boost=0.0)
- `0.070593` ضيق تنفس (semantic_similarity_only; raw=0.070593, boost=0.0)
- `0.069971` خفقان القلب (semantic_similarity_only; raw=0.069971, boost=0.0)

**Top evidence docs**
- `0.211129` الام (evidence_for_hard_entity_seed; raw=0.031129, boost=0.18)
- `0.11495` فقر الدم (semantic_similarity_only; raw=0.11495, boost=0.0)
- `0.111369` التهاب (semantic_similarity_only; raw=0.111369, boost=0.0)
- `0.101666` صداع (semantic_similarity_only; raw=0.101666, boost=0.0)
- `0.100282` Hashimot (semantic_similarity_only; raw=0.100282, boost=0.0)

**Top qa docs**
- `0.514683` لا أستطبع النوم على جانبي لا الأيمن ولا الأيسر وأجد صعوبة في التنفس العميق. كما أشعر بين الفينة والأخرى بآلام قرب القلب. (semantic_similarity_only; raw=0.514683, boost=0.0)
- `0.152499` اعاني من حموضة وصعوبة في التنفس وصعوبة بلع والم في الجانب الايسر من الصدر مع تعب في الكتف اليسرى بعد ابذال مجهود فهل هذا (semantic_similarity_only; raw=0.152499, boost=0.0)
- `0.130713` اشعر بصداع متقطع في النصف الايسر من رأسي كومضات متقطعّة و دوخة و لا استطيع فتح عيني كاملة يظهر التعب على وجهي والاجهاد ب (semantic_similarity_only; raw=0.130713, boost=0.0)
- `0.111221` انتفاخ الكلى للحامل في الشهر السابع مع التهاب حا في البوم والدم (semantic_similarity_only; raw=0.111221, boost=0.0)
- `0.110056` موخرا اكتشفت امي ان لديها ثقب فطري بالقلب و هي تعاني يوميا من اختناق ولا يمكنها التنفس بسهولة ،ماذا افعل لان الدواء المع (semantic_similarity_only; raw=0.110056, boost=0.0)

### هل هناك أسباب أخرى محددة تؤدي الى ولادة دات شفة مشقوقة من غير استعمال دواء التوبيراميت.

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.461803` شفة مشقوقة (hard_entity_seed; raw=0.111803, boost=0.35)
- `0.405902` توبيراميت (hard_entity_seed; raw=0.055902, boost=0.35)
- `0.127578` سعال (semantic_similarity_only; raw=0.127578, boost=0.0)
- `0.121666` خلطة الريحان و الروزماري (semantic_similarity_only; raw=0.121666, boost=0.0)
- `0.118585` شيب (semantic_similarity_only; raw=0.118585, boost=0.0)

**Top evidence docs**
- `0.720062` توبيراميت (evidence_for_hard_entity_seed; raw=0.540062, boost=0.18)
- `0.388333` شفة مشقوقة (evidence_for_hard_entity_seed; raw=0.208333, boost=0.18)
- `0.273861` حساسية (semantic_similarity_only; raw=0.273861, boost=0.0)
- `0.196116` مرض السكري (semantic_similarity_only; raw=0.196116, boost=0.0)
- `0.188445` قرحة (semantic_similarity_only; raw=0.188445, boost=0.0)

**Top qa docs**
- `0.367144` هل هناك أسباب أخرى محددة تؤدي الى ولادة دات شفة مشقوقة من غير استعمال دواء التوبيراميت. (semantic_similarity_only; raw=0.367144, boost=0.0)
- `0.161374` هل هناك اسباب للحساسية من الباراسيتمول وما الاغذية التى امتنع عنها وما هى الاغذية التى ااكلها (semantic_similarity_only; raw=0.161374, boost=0.0)
- `0.158438` هل الكحول بالنسبة للمرأة الحامل تزيد من نسبة أصابة الجنين بتشوهات خلقية؟ و ماهي الادوية التي يحظر على المرأة الحامل تعاط (semantic_similarity_only; raw=0.158438, boost=0.0)
- `0.142887` مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد ا (semantic_similarity_only; raw=0.142887, boost=0.0)
- `0.139754` اشعر بتنميل من بداية النصف الاسفل من الجسم حتى اسفل القدم عند تحريك الرقبة الى اسفل و انا عندي انيميا هل لها علاقة (semantic_similarity_only; raw=0.139754, boost=0.0)

### كيف تتم ازالة شظايا القنابل الصغيرة الانشطارية في المنزل عند عدم التمكن من الذهاب للمستشفى وهل هناك اخطار من بقائها؟

**Top entity docs**
- `0.571313` شظايا القنابل الصغيرة الانشطارية (hard_entity_seed; raw=0.221313, boost=0.35)
- `0.164083` أشعة (semantic_similarity_only; raw=0.164083, boost=0.0)
- `0.146385` تضخم (semantic_similarity_only; raw=0.146385, boost=0.0)
- `0.146385` تضخم في الارداف (semantic_similarity_only; raw=0.146385, boost=0.0)
- `0.146385` سعال (semantic_similarity_only; raw=0.146385, boost=0.0)

**Top evidence docs**
- `0.511497` شظايا القنابل الصغيرة الانشطارية (evidence_for_hard_entity_seed; raw=0.331497, boost=0.18)
- `0.184428` أشعة (semantic_similarity_only; raw=0.184428, boost=0.0)
- `0.159364` ضيق تنفس (semantic_similarity_only; raw=0.159364, boost=0.0)
- `0.140981` التهاب (semantic_similarity_only; raw=0.140981, boost=0.0)
- `0.130931` حساسية (semantic_similarity_only; raw=0.130931, boost=0.0)

**Top qa docs**
- `0.432844` كيف تتم ازالة شظايا القنابل الصغيرة الانشطارية في المنزل عند عدم التمكن من الذهاب للمستشفى وهل هناك اخطار من بقائها؟ (semantic_similarity_only; raw=0.432844, boost=0.0)
- `0.119523` سقطت ابنتي اعلى راسها فظهر لها انتفاخ خلف الاذن والم شديد في الرقبه ولاتستطيع تحريكها (semantic_similarity_only; raw=0.119523, boost=0.0)
- `0.110974` لماذا ترتفع درجة حرارة جسمي دائما بدرجة عالية جدا بالرغم من عدم بذل اي جهد حركي و التواجد في مكان بارد ولاحظت حدوث هذه ا (semantic_similarity_only; raw=0.110974, boost=0.0)
- `0.108266` كيف انقذ شخص تم وقوف قلبه (semantic_similarity_only; raw=0.108266, boost=0.0)
- `0.106904` ما سبب البروتينات الزائدة في الدم وفي البول للبالغين ؟ (semantic_similarity_only; raw=0.106904, boost=0.0)

### السلام عليكم .. هل تناول ملعقة يوميا من زيت الحلبة على الريق يزيد من حجم الثدي بجانب التمارين ..؟؟ و ما المدة التى يمكن الاستمرار عليها فى تناول الزيت؟ و...

**Top entity docs**
- `0.506174` زيت الحلبة (hard_entity_seed; raw=0.156174, boost=0.35)
- `0.179144` خلطة الريحان و الروزماري (semantic_similarity_only; raw=0.179144, boost=0.0)
- `0.174608` شيب (semantic_similarity_only; raw=0.174608, boost=0.0)
- `0.166482` بروز في البطن (semantic_similarity_only; raw=0.166482, boost=0.0)
- `0.166482` تمارين رياضية (semantic_similarity_only; raw=0.166482, boost=0.0)

**Top evidence docs**
- `0.679445` زيت الحلبة (evidence_for_hard_entity_seed; raw=0.499445, boost=0.18)
- `0.330278` زيت الحلبة (evidence_for_hard_entity_seed; raw=0.150278, boost=0.18)
- `0.320248` زيت الحلبة (evidence_for_hard_entity_seed; raw=0.140248, boost=0.18)
- `0.319686` زيت الحلبة (evidence_for_hard_entity_seed; raw=0.139686, boost=0.18)
- `0.1704` تشنجات (semantic_similarity_only; raw=0.1704, boost=0.0)

**Top qa docs**
- `0.476992` السلام عليكم .. هل تناول ملعقة يوميا من زيت الحلبة على الريق يزيد من حجم الثدي بجانب التمارين ..؟؟ و ما المدة التى يمكن  (semantic_similarity_only; raw=0.476992, boost=0.0)
- `0.164809` السلام عليكم ورحمه الله اشعر بطغنات في الجهه اليمن من الصدر ويمتد الى الكتف ماسبب هذه الالم؟؟ (semantic_similarity_only; raw=0.164809, boost=0.0)
- `0.162967` السلام عليكم أنا صبي أبلغ من العمر 14 سنة، إنتابني هاجس يقول لي أنت مصاب بمتلازمة كلاينفلتر، لأن لدي ذراعان طويلان و أصا (semantic_similarity_only; raw=0.162967, boost=0.0)
- `0.154049` ما هي اضرار زيادة الدم على القلب وكيف اعرف ان القلب متضرر من هذه الزيادة؟ (semantic_similarity_only; raw=0.154049, boost=0.0)
- `0.151602` ابني عمره ١٠سنه يعاني من نقص الصفائح itpتم اعطائه ivigمرتين وتم اعطائه كرتزون وحاليا اضيف له علاج الروتيكسيماب اول جرعه  (semantic_similarity_only; raw=0.151602, boost=0.0)

### كيفية التعامل مع انتفاخ ضرس العقل مسببا الام و احمرار الفك الاسفل

**Top entity docs**
- `0.582321` الام (hard_entity_seed; raw=0.232321, boost=0.35)
- `0.577429` ضرس العقل (hard_entity_seed; raw=0.227429, boost=0.35)
- `0.504508` انتفاخ (hard_entity_seed; raw=0.154508, boost=0.35)
- `0.232321` المراجعة الطبية (semantic_similarity_only; raw=0.232321, boost=0.0)
- `0.143839` فحص الدم (semantic_similarity_only; raw=0.143839, boost=0.0)

**Top evidence docs**
- `0.369525` ضرس العقل (evidence_for_hard_entity_seed; raw=0.189525, boost=0.18)
- `0.369525` الام (evidence_for_hard_entity_seed; raw=0.189525, boost=0.18)
- `0.279258` انتفاخ (evidence_for_hard_entity_seed; raw=0.099258, boost=0.18)
- `0.189525` صداع (semantic_similarity_only; raw=0.189525, boost=0.0)
- `0.189525` المراجعة الطبية (semantic_similarity_only; raw=0.189525, boost=0.0)

**Top qa docs**
- `0.321634` كيفية التعامل مع انتفاخ ضرس العقل مسببا الام و احمرار الفك الاسفل (semantic_similarity_only; raw=0.321634, boost=0.0)
- `0.12298` لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم (semantic_similarity_only; raw=0.12298, boost=0.0)
- `0.09143` السلام عليكم ان اعاني من الام في اسفل المعدة علي مستوي الامعاء مع انتفاخ و غازت مع كل واجبة وخاصة عند الصباح ان تناولة ش (semantic_similarity_only; raw=0.09143, boost=0.0)
- `0.090371` هل نزول الدم من حلمة الأم أثناء الرضاعة بسبب التشققات مضر للطفل مع العلم أن فصيلة دم الأم O+ والطفل A+ (semantic_similarity_only; raw=0.090371, boost=0.0)
- `0.090075` انا عندي قضيبي صغير هل هذه بسبب متعلق بهرمون الذكوره علما انا عمري 17 ويوجد شعر على الارجل والابط ولايوجد على الشارب وبد (semantic_similarity_only; raw=0.090075, boost=0.0)

### تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س

**Top entity docs**
- `0.62136` مرض السكري (hard_entity_seed; raw=0.27136, boost=0.35)
- `0.539271` ضغط الدم (hard_entity_seed; raw=0.289271, boost=0.25)
- `0.493019` عمليه قلب مفتوح (hard_entity_seed; raw=0.143019, boost=0.35)
- `0.400252` السكري (hard_entity_seed; raw=0.050252, boost=0.35)
- `0.391812` ضغط (hard_entity_seed; raw=0.041812, boost=0.35)

**Top evidence docs**
- `0.41597` مرض السكري (evidence_for_hard_entity_seed; raw=0.23597, boost=0.18)
- `0.41355` مرض السكري (evidence_for_hard_entity_seed; raw=0.23355, boost=0.18)
- `0.408651` عملية القلب المفتوح (semantic_similarity_only; raw=0.408651, boost=0.0)
- `0.381456` مرض السكري (evidence_for_hard_entity_seed; raw=0.201456, boost=0.18)
- `0.35597` ضغط الدم (evidence_for_hard_entity_seed; raw=0.23597, boost=0.12)

**Top qa docs**
- `0.57438` تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم (semantic_similarity_only; raw=0.57438, boost=0.0)
- `0.181818` اجريت عمليه استبدال صمام ميترالي في 89ثم الاورطي في 2013 والان اعاني من ارتفاع الضغط وضيق تنفس وخفقان احيتنا (semantic_similarity_only; raw=0.181818, boost=0.0)
- `0.171191` والدي يعاني من انسداد في ٣ شرايين ومشكله في الصمام وتم إجراء عملية القلب المفتوح له بتبديل ٣ شرايين وتبديل الصمام بصمام  (semantic_similarity_only; raw=0.171191, boost=0.0)
- `0.161165` امي مصابة بروماتيزم الدم , مع ارتفاع في ضغط الدم تتناول أدوية الروماتيزم منذ عام تقريبا المشكلة أنها منذ فترة تعاني من خ (semantic_similarity_only; raw=0.161165, boost=0.0)
- `0.157174` هل ضعف عضله القلب وضيق ثلاث شرايين في القلب لهم عمليه جراحيه مع العلم أن المريض يعاني من مرض السكر ام يبقى على العلاج ول (semantic_similarity_only; raw=0.157174, boost=0.0)

### انا ابتلعت دبوس امس ولا اشعر ببلعه واعاني بوجع صدري كيف اعمل

**Top entity docs**
- `0.401503` وجع (hard_entity_seed; raw=0.051503, boost=0.35)
- `0.395038` دبوس (hard_entity_seed; raw=0.045038, boost=0.35)
- `0.058722` Rhizomelic and Micromelia (semantic_similarity_only; raw=0.058722, boost=0.0)
- `0.051503` أشعة (semantic_similarity_only; raw=0.051503, boost=0.0)
- `0.045038` الوجع الشديد في الجنب اليمين (semantic_similarity_only; raw=0.045038, boost=0.0)

**Top evidence docs**
- `0.346091` دبوس (evidence_for_hard_entity_seed; raw=0.166091, boost=0.18)
- `0.229629` وجع (evidence_for_hard_entity_seed; raw=0.049629, boost=0.18)
- `0.072836` حساسية (semantic_similarity_only; raw=0.072836, boost=0.0)
- `0.067806` التهاب (semantic_similarity_only; raw=0.067806, boost=0.0)
- `0.055989` نفخ (semantic_similarity_only; raw=0.055989, boost=0.0)

**Top qa docs**
- `0.321634` انا ابتلعت دبوس امس ولا اشعر ببلعه واعاني بوجع صدري كيف اعمل (semantic_similarity_only; raw=0.321634, boost=0.0)
- `0.087002` انا اشعر بالصداع والنعاس وحساسية في وجهي والحكة بكل انحاء جسمي كيف استطيع ان اوقف هذا الدواء (semantic_similarity_only; raw=0.087002, boost=0.0)
- `0.072526` السلام عليكم انا لدي حساسية الصدر من الصغر وكان عمر 7 اشهر والان استخدم السيروتايد القرص لاكن اشعر باختناق وعدم السعادة  (semantic_similarity_only; raw=0.072526, boost=0.0)
- `0.07075` تركت التدخين منذ خمس سنوات و أشعر بضيق نفس في صدري من حين لآخر و احيانا حرقة في مقدمة الصدر و بدون الشعور بأي ألم و احيا (semantic_similarity_only; raw=0.07075, boost=0.0)
- `0.063693` عند الاستيقاظ في الصباح اشعر بالام اسفل الظهر منذ فترة طويلة ما السبب انا استخدم علاج الثايروكسين هل له تاثير (semantic_similarity_only; raw=0.063693, boost=0.0)

### عندى بقع بنية على جانبى الوجة وانا اعانى من انيميا 10 وكان عندى حصوات بالمرارة وعملت العملية ولا زالت البقع موجودة ما العلاج الاكيد وشكرا

**Top entity docs**
- `0.405216` العلاج (hard_entity_seed; raw=0.055216, boost=0.35)
- `0.198087` فقر الدم (semantic_candidate_entity; raw=0.078087, boost=0.12)
- `0.110432` تنميل (semantic_similarity_only; raw=0.110432, boost=0.0)
- `0.104765` نقص هرمونات (semantic_similarity_only; raw=0.104765, boost=0.0)
- `0.093704` انقطاع الطمث (semantic_similarity_only; raw=0.093704, boost=0.0)

**Top evidence docs**
- `0.523039` فقر الدم (evidence_for_semantic_candidate_entity; raw=0.443039, boost=0.08)
- `0.239028` العلاج (evidence_for_hard_entity_seed; raw=0.059028, boost=0.18)
- `0.237027` العلاج (evidence_for_hard_entity_seed; raw=0.057027, boost=0.18)
- `0.222566` فقر الدم (evidence_for_semantic_candidate_entity; raw=0.142566, boost=0.08)
- `0.21525` فقر الدم (evidence_for_semantic_candidate_entity; raw=0.13525, boost=0.08)

**Top qa docs**
- `0.504049` عندى بقع بنية على جانبى الوجة وانا اعانى من انيميا 10 وكان عندى حصوات بالمرارة وعملت العملية ولا زالت البقع موجودة ما ال (semantic_similarity_only; raw=0.504049, boost=0.0)
- `0.133863` منذ دخول الصيف وانا اعاني من ظهور حبوب في وجهي اريد العلاج من خلال الطب البديل وشكرا لكم على مساعدتكم (semantic_similarity_only; raw=0.133863, boost=0.0)
- `0.123466` اشعر بتنميل من بداية النصف الاسفل من الجسم حتى اسفل القدم عند تحريك الرقبة الى اسفل و انا عندي انيميا هل لها علاقة (semantic_similarity_only; raw=0.123466, boost=0.0)
- `0.119081` انا مريضه بالسكر واستخدم فيرومن كبريتات الحديد لان عندي فقر دم مع فيتامين ب وبعد استخدامهم لاحظت ظهور حبوب في ظهري هل له (semantic_similarity_only; raw=0.119081, boost=0.0)
- `0.116405` هل هناك معالجة لمرض بيلة الميوغلوبين ارجو ايفادي به سواء هنا في سوريا او في اي دولة وفي اي مستشفى بالضبط لأني اعاني من ه (semantic_similarity_only; raw=0.116405, boost=0.0)

### ماهو البردقوش وهل يوجد باليمن وهل يزيد من عدد الحيوانات المنويه؟

**Top entity docs**
- `0.555738` الحيوانات المنوية (hard_entity_seed; raw=0.205738, boost=0.35)
- `0.516667` البردقوش (hard_entity_seed; raw=0.166667, boost=0.35)
- `0.198762` التدخين (semantic_similarity_only; raw=0.198762, boost=0.0)
- `0.154303` الاكثار من شرب الماء (semantic_similarity_only; raw=0.154303, boost=0.0)
- `0.149071` التهاب المفاصل (semantic_similarity_only; raw=0.149071, boost=0.0)

**Top evidence docs**
- `0.67897` البردقوش (evidence_for_hard_entity_seed; raw=0.49897, boost=0.18)
- `0.324338` الحيوانات المنوية (evidence_for_hard_entity_seed; raw=0.144338, boost=0.18)
- `0.268302` البردقوش (evidence_for_hard_entity_seed; raw=0.088302, boost=0.18)
- `0.140028` الافطار (semantic_similarity_only; raw=0.140028, boost=0.0)
- `0.132453` التدخين (semantic_similarity_only; raw=0.132453, boost=0.0)

**Top qa docs**
- `0.184334` ماهو البردقوش وهل يوجد باليمن وهل يزيد من عدد الحيوانات المنويه؟ (semantic_similarity_only; raw=0.184334, boost=0.0)
- `0.093659` هل يوجد علاقة بين انخفاض الصفيحات الدموية 122/ وارتفاع خضاب الدم / 16.8 (semantic_similarity_only; raw=0.093659, boost=0.0)
- `0.089087` زوجتي حامل ومنذ بداية حملها لم اتوقف عن الاتصال معهاابدا ..فهل ذلك له علاقه لما تشعر به من حرقه في المهبل...وهل ذلك له ت (semantic_similarity_only; raw=0.089087, boost=0.0)
- `0.086066` ماهو علاج نقص الكريات البيضاء لدى الكبار وهل يحتاج تنويم واخذ علاج عن طريق الوريد الكريات 3000 (semantic_similarity_only; raw=0.086066, boost=0.0)
- `0.083333` السلام عليكم انا أخذ التروكسين ١٥٠ لأَنِّي أعاني من هاشيموتو في بعض الأحيان في رمضان أخذ الدواء قبل السحور ولا اكل شي بع (semantic_similarity_only; raw=0.083333, boost=0.0)

### اعاني من حموضة وصعوبة في التنفس وصعوبة بلع والم في الجانب الايسر من الصدر مع تعب في الكتف اليسرى بعد ابذال مجهود فهل هذا خطر على القلب ام حموضة عادية

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.463592` تعب (hard_entity_seed; raw=0.113592, boost=0.35)
- `0.405902` حموضة (hard_entity_seed; raw=0.055902, boost=0.35)
- `0.387268` الكتف (hard_entity_seed; raw=0.037268, boost=0.35)
- `0.09759` ضيق تنفس (semantic_similarity_only; raw=0.09759, boost=0.0)
- `0.091287` سعال (semantic_similarity_only; raw=0.091287, boost=0.0)

**Top evidence docs**
- `0.293592` تعب (evidence_for_hard_entity_seed; raw=0.113592, boost=0.18)
- `0.275346` حموضة (evidence_for_hard_entity_seed; raw=0.095346, boost=0.18)
- `0.243246` الكتف (evidence_for_hard_entity_seed; raw=0.063246, boost=0.18)
- `0.186339` حساسية الصدر (semantic_similarity_only; raw=0.186339, boost=0.0)
- `0.13484` التهاب (semantic_similarity_only; raw=0.13484, boost=0.0)

**Top qa docs**
- `0.564692` اعاني من حموضة وصعوبة في التنفس وصعوبة بلع والم في الجانب الايسر من الصدر مع تعب في الكتف اليسرى بعد ابذال مجهود فهل هذا (semantic_similarity_only; raw=0.564692, boost=0.0)
- `0.179284` اعاني من حساسية في الصدر وضيق في التنفس وسعال وقئ صباحا (semantic_similarity_only; raw=0.179284, boost=0.0)
- `0.166856` السلام عليكم ورحمه الله اشعر بطغنات في الجهه اليمن من الصدر ويمتد الى الكتف ماسبب هذه الالم؟؟ (semantic_similarity_only; raw=0.166856, boost=0.0)
- `0.159364` عمري 24 سنة اعاني من تسارع في دقات القلب مع العلم اني مريضة روماتويد منذ 2006 حاليا اتناول البردنيزون فهل السبب يعود لما (semantic_similarity_only; raw=0.159364, boost=0.0)
- `0.13838` بسبب ظروف اجتماعية عصيبه لدى فقد تركت ابنى مع والده بعد شهر من ولادته على ان اعود بعد ثلاثة اشهر ويقول والده انه ينظر ال (semantic_similarity_only; raw=0.13838, boost=0.0)

### ما هو ابسط علاج لمرض السكر بدون كيماويات؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.529284` سكر (hard_entity_seed; raw=0.179284, boost=0.35)
- `0.271186` مرض السكري (semantic_candidate_entity; raw=0.151186, boost=0.12)
- `0.161165` ضغط الدم (semantic_similarity_only; raw=0.161165, boost=0.0)
- `0.13932` بلغم (semantic_similarity_only; raw=0.13932, boost=0.0)
- `0.136386` سعال (semantic_similarity_only; raw=0.136386, boost=0.0)

**Top evidence docs**
- `0.614522` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.534522, boost=0.08)
- `0.307921` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.227921, boost=0.08)
- `0.307921` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.227921, boost=0.08)
- `0.303718` سكر (evidence_for_hard_entity_seed; raw=0.123718, boost=0.18)
- `0.291289` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.211289, boost=0.08)

**Top qa docs**
- `0.192879` ما هو ابسط علاج لمرض السكر بدون كيماويات؟ (semantic_similarity_only; raw=0.192879, boost=0.0)
- `0.143486` ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر (semantic_similarity_only; raw=0.143486, boost=0.0)
- `0.138013` ماالعلاج الاسعافي لأنخفاض السكر مع فقدان الوعي (semantic_similarity_only; raw=0.138013, boost=0.0)
- `0.127775` انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟ (semantic_similarity_only; raw=0.127775, boost=0.0)
- `0.120004` تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم (semantic_similarity_only; raw=0.120004, boost=0.0)

### انا عملت جراحة فى القلب وتم تغير الصمام المترالى بصمام ميكانيكى صناعى وباخد دواء واريفان ( لسيولة الدم ) 8 ملجرام ومصاب بالانفلوانزا ماالعلاج المناسب

**Top entity docs**
- `0.407354` الانفلوانزا (hard_entity_seed; raw=0.057354, boost=0.35)
- `0.358148` صمام القلب (hard_entity_seed; raw=0.108148, boost=0.25)
- `0.111648` خفقان القلب (semantic_similarity_only; raw=0.111648, boost=0.0)
- `0.081111` الهرمون (semantic_similarity_only; raw=0.081111, boost=0.0)
- `0.076948` ارتفاع ضغط الدم (semantic_similarity_only; raw=0.076948, boost=0.0)

**Top evidence docs**
- `0.299969` صمام القلب (evidence_for_hard_entity_seed; raw=0.179969, boost=0.12)
- `0.254976` صمام القلب (evidence_for_hard_entity_seed; raw=0.134976, boost=0.12)
- `0.234074` الانفلوانزا (evidence_for_hard_entity_seed; raw=0.054074, boost=0.18)
- `0.121666` ارتفاع ضغط الدم (semantic_similarity_only; raw=0.121666, boost=0.0)
- `0.108821` خفقان القلب (semantic_similarity_only; raw=0.108821, boost=0.0)

**Top qa docs**
- `0.582699` انا عملت جراحة فى القلب وتم تغير الصمام المترالى بصمام ميكانيكى صناعى وباخد دواء واريفان ( لسيولة الدم ) 8 ملجرام ومصاب  (semantic_similarity_only; raw=0.582699, boost=0.0)
- `0.157895` والدي يعاني من انسداد في ٣ شرايين ومشكله في الصمام وتم إجراء عملية القلب المفتوح له بتبديل ٣ شرايين وتبديل الصمام بصمام  (semantic_similarity_only; raw=0.157895, boost=0.0)
- `0.120727` هل من مخاوف انا عندي ضيق بسيط في الصمام الميترالي سببه حمه روماتزميه عملت عمليه توسيع بالبلونه والحمدلله انا عمري 25 سنه (semantic_similarity_only; raw=0.120727, boost=0.0)
- `0.110378` السلام. أنا شاب أبلغ من العمر 27 و أعاني من الدوال الساقين في الساق اليسرى مند حوالي 4 سنوات،و قد أجرية عملية، ولكنها لم (semantic_similarity_only; raw=0.110378, boost=0.0)
- `0.103011` تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم (semantic_similarity_only; raw=0.103011, boost=0.0)

### هل حبوب كريستور(rousovastatin) تؤثر على عضلة القلب ؟

**Top entity docs**
- `0.491421` كريستور (hard_entity_seed; raw=0.141421, boost=0.35)
- `0.173205` تدليك القلب (semantic_similarity_only; raw=0.173205, boost=0.0)
- `0.16641` الصدمة الكهربائية (semantic_similarity_only; raw=0.16641, boost=0.0)
- `0.160357` توقف القلب (semantic_similarity_only; raw=0.160357, boost=0.0)
- `0.141421` خصائي الاطفال (semantic_similarity_only; raw=0.141421, boost=0.0)

**Top evidence docs**
- `0.63` كريستور (evidence_for_hard_entity_seed; raw=0.45, boost=0.18)
- `0.436564` روفسوفاستاتين (semantic_similarity_only; raw=0.436564, boost=0.0)
- `0.173205` حبوب الأسبرين (semantic_similarity_only; raw=0.173205, boost=0.0)
- `0.145521` كيس (semantic_similarity_only; raw=0.145521, boost=0.0)
- `0.134164` جهاز هولتر (semantic_similarity_only; raw=0.134164, boost=0.0)

**Top qa docs**
- `0.313786` هل حبوب كريستور(rousovastatin) تؤثر على عضلة القلب ؟ (semantic_similarity_only; raw=0.313786, boost=0.0)
- `0.140028` هل فقر الدم سبب فقدان الشهيه والكسل والخمول والتعب وثقل الوزن وغيره (semantic_similarity_only; raw=0.140028, boost=0.0)
- `0.11547` ماسبب الطبقه البيضاء على السن هل تؤثر على الاسنان اوتسبب سقوط السن (semantic_similarity_only; raw=0.11547, boost=0.0)
- `0.104257` هل ضعف عضله القلب وضيق ثلاث شرايين في القلب لهم عمليه جراحيه مع العلم أن المريض يعاني من مرض السكر ام يبقى على العلاج ول (semantic_similarity_only; raw=0.104257, boost=0.0)
- `0.101419` انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟ (semantic_similarity_only; raw=0.101419, boost=0.0)

### هل يوجد أعشاب طبية تساعد على الشفاء من حالة الاكتئاب و الشعور بالخوف ، علما بأنه يوجد لدي فقر دم (انيميا الفول ) و يتجدث حالات الاكتئاب هذه عند تناول...

**Top entity docs**
- `0.531818` الاكتئاب (hard_entity_seed; raw=0.181818, boost=0.35)
- `0.500756` فقر دم (hard_entity_seed; raw=0.150756, boost=0.35)
- `0.4566` اكتئاب (hard_entity_seed; raw=0.1066, boost=0.35)
- `0.450504` فول (hard_entity_seed; raw=0.100504, boost=0.35)
- `0.251911` فقر الدم (semantic_candidate_entity; raw=0.131911, boost=0.12)

**Top evidence docs**
- `0.330873` فقر الدم (evidence_for_semantic_candidate_entity; raw=0.250873, boost=0.08)
- `0.330756` فقر دم (evidence_for_hard_entity_seed; raw=0.150756, boost=0.18)
- `0.324841` فول (evidence_for_hard_entity_seed; raw=0.144841, boost=0.18)
- `0.323019` الاكتئاب (evidence_for_hard_entity_seed; raw=0.143019, boost=0.18)
- `0.316364` الاكتئاب (evidence_for_hard_entity_seed; raw=0.136364, boost=0.18)

**Top qa docs**
- `0.254678` هل يوجد أعشاب طبية تساعد على الشفاء من حالة الاكتئاب و الشعور بالخوف ، علما بأنه يوجد لدي فقر دم (انيميا الفول ) و يتجدث (semantic_similarity_only; raw=0.254678, boost=0.0)
- `0.190693` اشعر بتنميل من بداية النصف الاسفل من الجسم حتى اسفل القدم عند تحريك الرقبة الى اسفل و انا عندي انيميا هل لها علاقة (semantic_similarity_only; raw=0.190693, boost=0.0)
- `0.150756` طفلتي تتحسس من الجلوتين وعمرها سنة ونصف هل توجد أدوية تساعد على الشفاء من هذا المرض ام لا ؟؟ (semantic_similarity_only; raw=0.150756, boost=0.0)
- `0.148704` ما هي اضرار زيادة الدم على القلب وكيف اعرف ان القلب متضرر من هذه الزيادة؟ (semantic_similarity_only; raw=0.148704, boost=0.0)
- `0.148454` هل يوجد علاج اخر للكساح بدلا عن فيتامين دي (semantic_similarity_only; raw=0.148454, boost=0.0)

### انا عندى 16 سنة وعندي ارتخاء بالصمام الميترالى والاعراض اللى عندي دوخة لما أقف و بتعب من أقل مجهود , وعند الاستيقاظ هناك ضيق بالتنفس,والدكتورظكاتبلى اندرال 20 جم بس مش...

**Top entity docs**
- `0.428594` تعب (hard_entity_seed; raw=0.078594, boost=0.35)
- `0.401571` ارتخاء (hard_entity_seed; raw=0.051571, boost=0.35)
- `0.390456` دوخة (hard_entity_seed; raw=0.040456, boost=0.35)
- `0.347243` صمام القلب (hard_entity_seed; raw=0.097243, boost=0.25)
- `0.092253` ارتخاء الصمام الميترالي (semantic_similarity_only; raw=0.092253, boost=0.0)

**Top evidence docs**
- `0.277849` دوخة (evidence_for_hard_entity_seed; raw=0.097849, boost=0.18)
- `0.258594` تعب (evidence_for_hard_entity_seed; raw=0.078594, boost=0.18)
- `0.220456` ارتخاء (evidence_for_hard_entity_seed; raw=0.040456, boost=0.18)
- `0.220456` ارتخاء (evidence_for_hard_entity_seed; raw=0.040456, boost=0.18)
- `0.200911` صمام القلب (evidence_for_hard_entity_seed; raw=0.080911, boost=0.12)

**Top qa docs**
- `0.601083` انا عندى 16 سنة وعندي ارتخاء بالصمام الميترالى والاعراض اللى عندي دوخة لما أقف و بتعب من أقل مجهود , وعند الاستيقاظ هناك (semantic_similarity_only; raw=0.601083, boost=0.0)
- `0.144739` هل من مخاوف انا عندي ضيق بسيط في الصمام الميترالي سببه حمه روماتزميه عملت عمليه توسيع بالبلونه والحمدلله انا عمري 25 سنه (semantic_similarity_only; raw=0.144739, boost=0.0)
- `0.141677` عمري 21 عملت ايكو كان الحمد لله كان كويس ماعدا ان كان فيه mild mitral valve proplapse with trivial MR انا متوترة جدا من  (semantic_similarity_only; raw=0.141677, boost=0.0)
- `0.130991` عندي ضيق تنفس وبنفس الوقت معه صداع قوي وخفقان في القلب (semantic_similarity_only; raw=0.130991, boost=0.0)
- `0.121367` عندي الم في منطقه البطن مع الم بصدر جهه اليمين الى الرقبه وماقدرت اعرف تفسير الالم ذا من ايش او سببه مع وجود احيان ضيق ب (semantic_similarity_only; raw=0.121367, boost=0.0)

### هل هناك اسباب للحساسية من الباراسيتمول وما الاغذية التى امتنع عنها وما هى الاغذية التى ااكلها

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.477343` حساسية (hard_entity_seed; raw=0.127343, boost=0.35)
- `0.385613` حساسية الصدر (hard_entity_seed; raw=0.135613, boost=0.25)
- `0.184466` سعال (semantic_similarity_only; raw=0.184466, boost=0.0)
- `0.177705` ربو (semantic_similarity_only; raw=0.177705, boost=0.0)
- `0.161515` بلغم (semantic_similarity_only; raw=0.161515, boost=0.0)

**Top evidence docs**
- `0.604264` حساسية (evidence_for_hard_entity_seed; raw=0.424264, boost=0.18)
- `0.438199` حساسية (evidence_for_hard_entity_seed; raw=0.258199, boost=0.18)
- `0.382548` حساسية (evidence_for_hard_entity_seed; raw=0.202548, boost=0.18)
- `0.382548` حساسية (evidence_for_hard_entity_seed; raw=0.202548, boost=0.18)
- `0.368562` حساسية (evidence_for_hard_entity_seed; raw=0.188562, boost=0.18)

**Top qa docs**
- `0.5` هل هناك اسباب للحساسية من الباراسيتمول وما الاغذية التى امتنع عنها وما هى الاغذية التى ااكلها (semantic_similarity_only; raw=0.5, boost=0.0)
- `0.186339` ما هي ادويت الحساسيه التي لا تزيد من الوزن (semantic_similarity_only; raw=0.186339, boost=0.0)
- `0.182574` طفلتي تتحسس من الجلوتين وعمرها سنة ونصف هل توجد أدوية تساعد على الشفاء من هذا المرض ام لا ؟؟ (semantic_similarity_only; raw=0.182574, boost=0.0)
- `0.163956` إبني عمر 6 سنوات و يعاني من حساسية الصدر أعطيه بخار الفنتولين و الأتروفين و شراب الزيلون .هل الفيس يفيد أم لا (semantic_similarity_only; raw=0.163956, boost=0.0)
- `0.149581` يوجد أعراض ترعبني. عند الصعود بالدرج او مرتفع ينقطع نفسي ويجب ان استريح علماً باني ب٢٦ من العمر ومن قبل كانت هناك آلام ف (semantic_similarity_only; raw=0.149581, boost=0.0)

### كان لدي ارتفاع بسيط في الصفائح ٤٦١ وعندما ولدت بعد ٥٠ يوم التحليل طلع ٦٧٩ واشكو من عدم اكتمال النفس في بعض الاوقات وقال لي الطبيب لديك التهاب في الصدر...

**Top entity docs**
- `0.3841` الطبيب (hard_entity_seed; raw=0.0341, boost=0.35)
- `0.351666` الصفائح الدموية (hard_entity_seed; raw=0.101666, boost=0.25)
- `0.141186` ضيق تنفس (semantic_similarity_only; raw=0.141186, boost=0.0)
- `0.109558` تعب (semantic_similarity_only; raw=0.109558, boost=0.0)
- `0.089939` بلغم (semantic_similarity_only; raw=0.089939, boost=0.0)

**Top evidence docs**
- `0.268045` الطبيب (evidence_for_hard_entity_seed; raw=0.088045, boost=0.18)
- `0.236637` الطبيب (evidence_for_hard_entity_seed; raw=0.056637, boost=0.18)
- `0.220757` الطبيب (evidence_for_hard_entity_seed; raw=0.040757, boost=0.18)
- `0.214986` الطبيب (evidence_for_hard_entity_seed; raw=0.034986, boost=0.18)
- `0.211798` الطبيب (evidence_for_hard_entity_seed; raw=0.031798, boost=0.18)

**Top qa docs**
- `0.575761` كان لدي ارتفاع بسيط في الصفائح ٤٦١ وعندما ولدت بعد ٥٠ يوم التحليل طلع ٦٧٩ واشكو من عدم اكتمال النفس في بعض الاوقات وقال  (semantic_similarity_only; raw=0.575761, boost=0.0)
- `0.150424` ماذا يؤدى ارتفاع الصفائح الدموية فى الدم وعلاجها؟ (semantic_similarity_only; raw=0.150424, boost=0.0)
- `0.113273` دكتور انا من مصر وعندى مشكلة في الصفائح الدموية ضعيفة ونسبة الأملاح عالية جدا أروح لدكتور ايه؟ (semantic_similarity_only; raw=0.113273, boost=0.0)
- `0.110959` علاج كونكور 2.5ملجم تم وصفه لي من قبل دكتور القلب حيث انني لدي تشوه خلقي في صمام القلب وحصل لي تعب بسيط خاصه اذا اردت ال (semantic_similarity_only; raw=0.110959, boost=0.0)
- `0.108685` لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام  (semantic_similarity_only; raw=0.108685, boost=0.0)

### عمري 18 سنة وأنا أعاني من صغر الثدي هل يوجد أي حل لتكبيره دون جراحة?

**Top entity docs**
- `0.469737` صغر الثدي (hard_entity_seed; raw=0.119737, boost=0.35)
- `0.082409` خلطة الريحان و الروزماري (semantic_similarity_only; raw=0.082409, boost=0.0)
- `0.080322` شيب (semantic_similarity_only; raw=0.080322, boost=0.0)
- `0.080322` نقص هرمونات (semantic_similarity_only; raw=0.080322, boost=0.0)
- `0.077771` سعال (semantic_similarity_only; raw=0.077771, boost=0.0)

**Top evidence docs**
- `0.741754` صغر الثدي (evidence_for_hard_entity_seed; raw=0.561754, boost=0.18)
- `0.153168` التهاب (semantic_similarity_only; raw=0.153168, boost=0.0)
- `0.153168` التهاب (semantic_similarity_only; raw=0.153168, boost=0.0)
- `0.149801` شيب (semantic_similarity_only; raw=0.149801, boost=0.0)
- `0.123208` الحمل (semantic_similarity_only; raw=0.123208, boost=0.0)

**Top qa docs**
- `0.344942` عمري 18 سنة وأنا أعاني من صغر الثدي هل يوجد أي حل لتكبيره دون جراحة? (semantic_similarity_only; raw=0.344942, boost=0.0)
- `0.155941` هل من مخاوف انا عندي ضيق بسيط في الصمام الميترالي سببه حمه روماتزميه عملت عمليه توسيع بالبلونه والحمدلله انا عمري 25 سنه (semantic_similarity_only; raw=0.155941, boost=0.0)
- `0.140248` أن زوجة في 50 من عمري أعاني من إنتفاخ الثدي الأييسر و الشعور بالألم عند لمسه (semantic_similarity_only; raw=0.140248, boost=0.0)
- `0.13387` هل هناك معالجة لمرض بيلة الميوغلوبين ارجو ايفادي به سواء هنا في سوريا او في اي دولة وفي اي مستشفى بالضبط لأني اعاني من ه (semantic_similarity_only; raw=0.13387, boost=0.0)
- `0.132407` اعاني من حساسية في فصل ربيع والاعراض الحساسية قوية اي انني لا استطيغ التنفس بسهولة مع حالة عطاس قوي بالاضافة الى السيلان (semantic_similarity_only; raw=0.132407, boost=0.0)

### عمري ٢٥سنة واعاني من نشاط زائد في الغده الدرقية وقمت بأخذ جرعه من اليود النووي المشع وعندي طفل عمره سنه فما المده الزمنيه المحدده اللتي سأتمكن بعدها

**Top entity docs**
- `0.455409` الغدة الدرقية (hard_entity_seed; raw=0.105409, boost=0.35)
- `0.265095` مرض الغدة الدرقية (semantic_candidate_entity; raw=0.145095, boost=0.12)
- `0.158114` الهرمون (semantic_similarity_only; raw=0.158114, boost=0.0)
- `0.136931` عقيدات الغدة الدرقية (semantic_similarity_only; raw=0.136931, boost=0.0)
- `0.126773` التروكسين (semantic_similarity_only; raw=0.126773, boost=0.0)

**Top evidence docs**
- `0.705024` جرعة (semantic_similarity_only; raw=0.705024, boost=0.0)
- `0.694879` تهاب (semantic_similarity_only; raw=0.694879, boost=0.0)
- `0.282598` الغدة الدرقية (evidence_for_hard_entity_seed; raw=0.102598, boost=0.18)
- `0.282598` الغدة الدرقية (evidence_for_hard_entity_seed; raw=0.102598, boost=0.18)
- `0.260178` الغدة الدرقية (evidence_for_hard_entity_seed; raw=0.080178, boost=0.18)

**Top qa docs**
- `0.554322` عمري ٢٥سنة واعاني من نشاط زائد في الغده الدرقية وقمت بأخذ جرعه من اليود النووي المشع وعندي طفل عمره سنه فما المده الزمني (semantic_similarity_only; raw=0.554322, boost=0.0)
- `0.125` اعاني من فرط نشاط الغدة الدرقية ( ملتهبة) كيف اعالجها . و ما هي العشبة المفيدة في هذه الحالة -اشرب الدواء basdéne منذ 4  (semantic_similarity_only; raw=0.125, boost=0.0)
- `0.116563` أنا أعاني من فرط نشاط بالفدة الدرقية . نتائج التحاليل دائما مرتفعة أيش تنصحوني بجرعة يود مشع أو إجراء عملية مع العلم إني (semantic_similarity_only; raw=0.116563, boost=0.0)
- `0.114208` لماذا اصحو من النوم يوميا بصداع يختلف حدته من خفيف إلى قوي جدا لدرجة ان عيناي تدمع من كثرة الصداع مع العلم بان عمري 29 س (semantic_similarity_only; raw=0.114208, boost=0.0)
- `0.106904` انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟ (semantic_similarity_only; raw=0.106904, boost=0.0)

### يشعر والدي بألم في منطقة الصدر علما ان والدي مصاب بجلطة قلبية ودماغية اليوم قد تناول بيزا وكانت دسمة،،،،،هل هذا الم قلب ام الام معدة

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.415938` الام (hard_entity_seed; raw=0.065938, boost=0.35)
- `0.136931` سعال (semantic_similarity_only; raw=0.136931, boost=0.0)
- `0.116563` بلغم (semantic_similarity_only; raw=0.116563, boost=0.0)
- `0.106066` التهاب (semantic_similarity_only; raw=0.106066, boost=0.0)
- `0.101222` صداع (semantic_similarity_only; raw=0.101222, boost=0.0)

**Top evidence docs**
- `0.276825` الام (evidence_for_hard_entity_seed; raw=0.096825, boost=0.18)
- `0.186339` التهاب (semantic_similarity_only; raw=0.186339, boost=0.0)
- `0.186339` التهاب (semantic_similarity_only; raw=0.186339, boost=0.0)
- `0.181369` Rhizomelic and Micromelia (semantic_similarity_only; raw=0.181369, boost=0.0)
- `0.164845` Radioactive Iodine (semantic_similarity_only; raw=0.164845, boost=0.0)

**Top qa docs**
- `0.54451` يشعر والدي بألم في منطقة الصدر علما ان والدي مصاب بجلطة قلبية ودماغية اليوم قد تناول بيزا وكانت دسمة،،،،،هل هذا الم قلب  (semantic_similarity_only; raw=0.54451, boost=0.0)
- `0.169031` ابي يعاني من الام مستمرة حادة في الصدر تمتد حتى الضهر تصاحبه مند 10 سنوات علما انه مريض قلب و الشرايين فارجو العلاج وشكر (semantic_similarity_only; raw=0.169031, boost=0.0)
- `0.159364` منذ فتره اشعر بألم فى عضله الصدر وليس القفص الصدرى وهذا عند الضغط عليها اريد ان اعرف ما السبب؟ (semantic_similarity_only; raw=0.159364, boost=0.0)
- `0.148047` يوجد أعراض ترعبني. عند الصعود بالدرج او مرتفع ينقطع نفسي ويجب ان استريح علماً باني ب٢٦ من العمر ومن قبل كانت هناك آلام ف (semantic_similarity_only; raw=0.148047, boost=0.0)
- `0.147902` اعاني من الام في القلب مع اضطرابات خفيفة في الدقات احيانا و قد قمت العام الماضي ب تخطيط كهربائية القلب و قال الطبيب انه  (semantic_similarity_only; raw=0.147902, boost=0.0)

### هل يوجد تأثير على الجنين في حالة تعاطي أقراص ميزوتاك في بداية الحمل بغرض الإجهاض وأنا الآن اقتنعت باكمال الحمل ولكن قلق من تأثر الجنين بالمادة الفعالة لهذا الدواء؟

**Top entity docs**
- `0.426249` قلق (hard_entity_seed; raw=0.076249, boost=0.35)
- `0.403916` الجنين (hard_entity_seed; raw=0.053916, boost=0.35)
- `0.403916` ميزوتاك (hard_entity_seed; raw=0.053916, boost=0.35)
- `0.381798` الدواء (hard_entity_seed; raw=0.031798, boost=0.35)
- `0.375416` الحمل (hard_entity_seed; raw=0.025416, boost=0.35)

**Top evidence docs**
- `0.859986` الحمل (evidence_for_hard_entity_seed; raw=0.679986, boost=0.18)
- `0.859986` ميزوتاك (evidence_for_hard_entity_seed; raw=0.679986, boost=0.18)
- `0.334662` الحمل (evidence_for_hard_entity_seed; raw=0.154662, boost=0.18)
- `0.323777` الحمل (evidence_for_hard_entity_seed; raw=0.143777, boost=0.18)
- `0.284613` الحمل (evidence_for_hard_entity_seed; raw=0.104613, boost=0.18)

**Top qa docs**
- `0.56073` هل يوجد تأثير على الجنين في حالة تعاطي أقراص ميزوتاك في بداية الحمل بغرض الإجهاض وأنا الآن اقتنعت باكمال الحمل ولكن قلق  (semantic_similarity_only; raw=0.56073, boost=0.0)
- `0.141821` هل فايروس السايتو ميقالو يسبب تشوهات للجنين لأني حاملة للمرض وثلاث مرات أحمل ويتوفى الجنين عند الشهر الثالث والخامس و في (semantic_similarity_only; raw=0.141821, boost=0.0)
- `0.141186` زوجتي حامل ومنذ بداية حملها لم اتوقف عن الاتصال معهاابدا ..فهل ذلك له علاقه لما تشعر به من حرقه في المهبل...وهل ذلك له ت (semantic_similarity_only; raw=0.141186, boost=0.0)
- `0.139535` هل العلاج المستخدم في تنشيط المبايض قبل الحقن المجهري له تاثير في زيادة الوزن؟ (semantic_similarity_only; raw=0.139535, boost=0.0)
- `0.136399` هل هناك معالجة لمرض بيلة الميوغلوبين ارجو ايفادي به سواء هنا في سوريا او في اي دولة وفي اي مستشفى بالضبط لأني اعاني من ه (semantic_similarity_only; raw=0.136399, boost=0.0)

### حموضة في فمي واحساس برائحة تفاح متعفن مع كدمات زرقاء غامقة في قدماي واحساس بغبوش في الرؤية

**Top entity docs**
- `0.479099` حموضة (hard_entity_seed; raw=0.129099, boost=0.35)
- `0.158114` تضخم (semantic_similarity_only; raw=0.158114, boost=0.0)
- `0.158114` تضخم في الارداف (semantic_similarity_only; raw=0.158114, boost=0.0)
- `0.141421` التهاب اللوزتين (semantic_similarity_only; raw=0.141421, boost=0.0)
- `0.140546` الم المعدجة (semantic_similarity_only; raw=0.140546, boost=0.0)

**Top evidence docs**
- `0.400193` حموضة (evidence_for_hard_entity_seed; raw=0.220193, boost=0.18)
- `0.141421` حمى (semantic_similarity_only; raw=0.141421, boost=0.0)
- `0.125656` Rhizomelic and Micromelia (semantic_similarity_only; raw=0.125656, boost=0.0)
- `0.119523` سكر (semantic_similarity_only; raw=0.119523, boost=0.0)
- `0.119523` التهاب (semantic_similarity_only; raw=0.119523, boost=0.0)

**Top qa docs**
- `0.344656` حموضة في فمي واحساس برائحة تفاح متعفن مع كدمات زرقاء غامقة في قدماي واحساس بغبوش في الرؤية (semantic_similarity_only; raw=0.344656, boost=0.0)
- `0.093934` كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟ (semantic_similarity_only; raw=0.093934, boost=0.0)
- `0.082572` اجريت عمليه استبدال صمام ميترالي في 89ثم الاورطي في 2013 والان اعاني من ارتفاع الضغط وضيق تنفس وخفقان احيتنا (semantic_similarity_only; raw=0.082572, boost=0.0)
- `0.08165` أشعر برائحة كريهة في الفم تهرج من الجهاز الهضمي وأحياناً مع البلغم. أستبعد أن تكون من الاسنان أو اللثة أو الفم بشكل عام  (semantic_similarity_only; raw=0.08165, boost=0.0)
- `0.08165` ما هو سبب الوجع الشديد في الجنب اليمين مع ترجيع؟ (semantic_similarity_only; raw=0.08165, boost=0.0)

### قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة

**Top entity docs**
- `0.452548` انتفاخ (hard_entity_seed; raw=0.202548, boost=0.25)
- `0.452548` وجع (hard_entity_seed; raw=0.202548, boost=0.25)
- `0.351274` أشعة (hard_entity_seed; raw=0.101274, boost=0.25)
- `0.067806` حساسية الصدر (semantic_similarity_only; raw=0.067806, boost=0.0)
- `0.060858` اشعة تلفزيونية (semantic_similarity_only; raw=0.060858, boost=0.0)

**Top evidence docs**
- `0.363975` انتفاخ (evidence_for_hard_entity_seed; raw=0.243975, boost=0.12)
- `0.363975` وجع (evidence_for_hard_entity_seed; raw=0.243975, boost=0.12)
- `0.322548` أشعة (evidence_for_hard_entity_seed; raw=0.202548, boost=0.12)
- `0.187806` أشعة (evidence_for_hard_entity_seed; raw=0.067806, boost=0.12)
- `0.180858` أشعة (evidence_for_hard_entity_seed; raw=0.060858, boost=0.12)

**Top qa docs**
- `0.430706` قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة (semantic_similarity_only; raw=0.430706, boost=0.0)
- `0.08554` هل الاشعة المقطعيه بالصبغه للقلب تسبب انتفاخ اسفل الوجه او انتفاخ الغده هل هو طبيعي (semantic_similarity_only; raw=0.08554, boost=0.0)
- `0.08165` الدكتور الفاضل/ لقد قمت بعمل طفل انبوب وكان ترجيع الاجنة بتاريخ ١٩/٧/٢٠١٠ والحمدلله نجحت وتم الحمل. : حدثت مداعبات جنسية (semantic_similarity_only; raw=0.08165, boost=0.0)
- `0.079057` ما سبب آلام في الجهة اليمنى من الصدر ويزداد عند السعال بشكل قوي لدرجة أني ألقي نفسي على الارض اتحيانا من شدة الألم من فت (semantic_similarity_only; raw=0.079057, boost=0.0)
- `0.073193` مرحبا عمري 19 كنت اعاني من وجع في الصدر قمت بتخطيط قلب وكان سليم ، اخذت مسكن وخف الالم كثيرا لكن الان اعاني من الم تحت ا (semantic_similarity_only; raw=0.073193, boost=0.0)

### ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.515145` سكر (hard_entity_seed; raw=0.165145, boost=0.35)
- `0.408026` القات (hard_entity_seed; raw=0.058026, boost=0.35)
- `0.259262` مرض السكري (semantic_candidate_entity; raw=0.139262, boost=0.12)
- `0.148454` ضغط الدم (semantic_similarity_only; raw=0.148454, boost=0.0)
- `0.096976` زيت الحبة السوداء (semantic_similarity_only; raw=0.096976, boost=0.0)

**Top evidence docs**
- `0.404733` القات (evidence_for_hard_entity_seed; raw=0.224733, boost=0.18)
- `0.326183` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.246183, boost=0.08)
- `0.293961` سكر (evidence_for_hard_entity_seed; raw=0.113961, boost=0.18)
- `0.289946` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.209946, boost=0.08)
- `0.289946` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.209946, boost=0.08)

**Top qa docs**
- `0.339865` ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر (semantic_similarity_only; raw=0.339865, boost=0.0)
- `0.132647` تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم (semantic_similarity_only; raw=0.132647, boost=0.0)
- `0.127128` ماالعلاج الاسعافي لأنخفاض السكر مع فقدان الوعي (semantic_similarity_only; raw=0.127128, boost=0.0)
- `0.120701` ماهي علاجات حمى التهاب باطن القدم وباطن اليد وماهي الفحوصات للتاكد من اسباب هذا المرض؟ (semantic_similarity_only; raw=0.120701, boost=0.0)
- `0.118262` ماهي الاهمية الطبية للجلوكوز والفركتوز والجالكتوز؟ (semantic_similarity_only; raw=0.118262, boost=0.0)

### أعاني من حرقان بكامل بجسمي والتهاب المسالك البوليه وارتفاع الكلسترول والدهون الثلاثيه مال الحل جزاكم الله خير وما قد يكون المسبب

**Top entity docs**
- `0.458148` ارتفاع الكلسترول (hard_entity_seed; raw=0.108148, boost=0.35)
- `0.407354` كلسترول (hard_entity_seed; raw=0.057354, boost=0.35)
- `0.091971` العقاقير (semantic_similarity_only; raw=0.091971, boost=0.0)
- `0.076948` ارتفاع ضغط الدم (semantic_similarity_only; raw=0.076948, boost=0.0)
- `0.075094` ضيق تنفس (semantic_similarity_only; raw=0.075094, boost=0.0)

**Top evidence docs**
- `0.367317` ارتفاع الكلسترول (evidence_for_hard_entity_seed; raw=0.187317, boost=0.18)
- `0.231299` كلسترول (evidence_for_hard_entity_seed; raw=0.051299, boost=0.18)
- `0.101477` الصداع التوتري (semantic_similarity_only; raw=0.101477, boost=0.0)
- `0.097823` التهاب (semantic_similarity_only; raw=0.097823, boost=0.0)
- `0.097823` التهاب (semantic_similarity_only; raw=0.097823, boost=0.0)

**Top qa docs**
- `0.420596` أعاني من حرقان بكامل بجسمي والتهاب المسالك البوليه وارتفاع الكلسترول والدهون الثلاثيه مال الحل جزاكم الله خير وما قد يكو (semantic_similarity_only; raw=0.420596, boost=0.0)
- `0.104713` عندي الكلسترول 220 والدهون الثلاثية 320 علما انه لدي ظغط يكون 130/90 هل هاد خطير ويحتاج علاج اقصد،الكلسترول والدهون وشكر (semantic_similarity_only; raw=0.104713, boost=0.0)
- `0.087496` عندي الم في الجهه الايسرى اعزكم الله تحت الابط وعندي الم في ضلوع الصدر من الجهه اليسرى مع الحجاب الحاجز وشكراً لكم (semantic_similarity_only; raw=0.087496, boost=0.0)
- `0.087407` ما علاج تورم اللثه من الداخل؟ (semantic_similarity_only; raw=0.087407, boost=0.0)
- `0.080484` مدي وجع أسفل البطن بعد التبول وبعد مرات التبرز لما انتهي من عمليه التبول ومرات من التبرز يجيني وجع أسفل البطن قد يدوم مر (semantic_similarity_only; raw=0.080484, boost=0.0)

### ماهي علاجات حمى التهاب باطن القدم وباطن اليد وماهي الفحوصات للتاكد من اسباب هذا المرض؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.426777` الفحوصات المخبرية (hard_entity_seed; raw=0.176777, boost=0.25)
- `0.415779` حمى (hard_entity_seed; raw=0.065779, boost=0.35)
- `0.141737` الاكثار من شرب الماء (semantic_similarity_only; raw=0.141737, boost=0.0)
- `0.141421` انقطاع الطمث (semantic_similarity_only; raw=0.141421, boost=0.0)
- `0.136931` التهاب المفاصل (semantic_similarity_only; raw=0.136931, boost=0.0)

**Top evidence docs**
- `0.356777` حمى (evidence_for_hard_entity_seed; raw=0.176777, boost=0.18)
- `0.327087` حمى (evidence_for_hard_entity_seed; raw=0.147087, boost=0.18)
- `0.316931` حمى (evidence_for_hard_entity_seed; raw=0.136931, boost=0.18)
- `0.316931` حمى (evidence_for_hard_entity_seed; raw=0.136931, boost=0.18)
- `0.312583` حمى (evidence_for_hard_entity_seed; raw=0.132583, boost=0.18)

**Top qa docs**
- `0.392232` ماهي علاجات حمى التهاب باطن القدم وباطن اليد وماهي الفحوصات للتاكد من اسباب هذا المرض؟ (semantic_similarity_only; raw=0.392232, boost=0.0)
- `0.147314` طفلتي تتحسس من الجلوتين وعمرها سنة ونصف هل توجد أدوية تساعد على الشفاء من هذا المرض ام لا ؟؟ (semantic_similarity_only; raw=0.147314, boost=0.0)
- `0.140488` السلام عليكم أنا أشعر ببرودة رأسي -وغذا اصبح ملمس رأسي بارد جاني صداع لايزول بالمسكنات- ذهبت لأفضل أخصائي أنف وأذن وحنجر (semantic_similarity_only; raw=0.140488, boost=0.0)
- `0.138675` ماهي اسباب التهاب غدة الثدي؟ (semantic_similarity_only; raw=0.138675, boost=0.0)
- `0.131762` هل هناك معالجة لمرض بيلة الميوغلوبين ارجو ايفادي به سواء هنا في سوريا او في اي دولة وفي اي مستشفى بالضبط لأني اعاني من ه (semantic_similarity_only; raw=0.131762, boost=0.0)

### والدي وقع من الدرج قبل ثلالث ايام نلاحظ هناك زغللة في عينه اليمنى مع حول فيها تم قياسة مستوى السكر اليوم 200 اتمنى افادتي بهذا الامر هل له علاقة بالحلطة...

**Top entity docs**
- `0.530702` سكر (hard_entity_seed; raw=0.180702, boost=0.35)
- `0.32` مرض السكري (semantic_candidate_entity; raw=0.2, boost=0.12)
- `0.213201` ضغط الدم (semantic_similarity_only; raw=0.213201, boost=0.0)
- `0.178571` الهرمون (semantic_similarity_only; raw=0.178571, boost=0.0)
- `0.163868` مرض الغدة الدرقية (semantic_similarity_only; raw=0.163868, boost=0.0)

**Top evidence docs**
- `0.304696` سكر (evidence_for_hard_entity_seed; raw=0.124696, boost=0.18)
- `0.278107` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.198107, boost=0.08)
- `0.271663` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.191663, boost=0.08)
- `0.214687` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.134687, boost=0.08)
- `0.209219` مرض السكري (evidence_for_semantic_candidate_entity; raw=0.129219, boost=0.08)

**Top qa docs**
- `0.626295` والدي وقع من الدرج قبل ثلالث ايام نلاحظ هناك زغللة في عينه اليمنى مع حول فيها تم قياسة مستوى السكر اليوم 200 اتمنى افادت (semantic_similarity_only; raw=0.626295, boost=0.0)
- `0.145143` تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم (semantic_similarity_only; raw=0.145143, boost=0.0)
- `0.131095` كنت احس من قبل بدقات قلب مفاجاة و انتهت وحدها و اليوم احسست ان قلبي المني و كان 20 ابرة دخلوا قلبي (semantic_similarity_only; raw=0.131095, boost=0.0)
- `0.120736` انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟ (semantic_similarity_only; raw=0.120736, boost=0.0)
- `0.120024` مركب دعامة عادية فى الشريان التاجى بقالى 4سنوات مع العلم انى مريض سكر هل من فحوصات للدعامة علما ان عمرى 38 سنة ومدخا (semantic_similarity_only; raw=0.120024, boost=0.0)

### ماهي الاهمية الطبية للجلوكوز والفركتوز والجالكتوز؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top entity docs**
- `0.420711` الجالكتوز (hard_entity_seed; raw=0.070711, boost=0.35)
- `0.413246` الفركتوز (hard_entity_seed; raw=0.063246, boost=0.35)
- `0.410302` الجلوكوز (hard_entity_seed; raw=0.060302, boost=0.35)
- `0.083406` الام (semantic_similarity_only; raw=0.083406, boost=0.0)
- `0.083406` المراجعة الطبية (semantic_similarity_only; raw=0.083406, boost=0.0)

**Top evidence docs**
- `0.331186` الفركتوز (evidence_for_hard_entity_seed; raw=0.151186, boost=0.18)
- `0.29547` الجلوكوز (evidence_for_hard_entity_seed; raw=0.11547, boost=0.18)
- `0.289545` الفركتوز (evidence_for_hard_entity_seed; raw=0.109545, boost=0.18)
- `0.287763` الجلوكوز (evidence_for_hard_entity_seed; raw=0.107763, boost=0.18)
- `0.286066` الجلوكوز (evidence_for_hard_entity_seed; raw=0.106066, boost=0.18)

**Top qa docs**
- `0.226455` ماهي الاهمية الطبية للجلوكوز والفركتوز والجالكتوز؟ (semantic_similarity_only; raw=0.226455, boost=0.0)
- `0.080904` ماهى الاعشاب التي تساعد على نزول الطمث حيت انوما تجيني الدورة الا بالدواء فقط.شكرا (semantic_similarity_only; raw=0.080904, boost=0.0)
- `0.079472` السلام عليكم أنا أشعر ببرودة رأسي -وغذا اصبح ملمس رأسي بارد جاني صداع لايزول بالمسكنات- ذهبت لأفضل أخصائي أنف وأذن وحنجر (semantic_similarity_only; raw=0.079472, boost=0.0)
- `0.079472` لدي ضرسان عقل معكوسان واحد في. الطرف اليمين ولاخر في الطرف اليسار يسببان لي صداع هل يلزم ازالتهم (semantic_similarity_only; raw=0.079472, boost=0.0)
- `0.078446` اعاني من ضيق بلتنفس عند حدوث الغبار في الجو ماهي الوسائل المعالجه (semantic_similarity_only; raw=0.078446, boost=0.0)

### متى يلجأ الدكتور الي نزع عَصّب السن او الضرس

**Top entity docs**
- `0.491421` الضرس (hard_entity_seed; raw=0.141421, boost=0.35)
- `0.15` الانتان (semantic_similarity_only; raw=0.15, boost=0.0)
- `0.145521` الحروق (semantic_similarity_only; raw=0.145521, boost=0.0)
- `0.141421` الصدمة الكهربائية (semantic_similarity_only; raw=0.141421, boost=0.0)
- `0.141421` حليب مكسر بروتين الحليب (semantic_similarity_only; raw=0.141421, boost=0.0)

**Top evidence docs**
- `0.313333` الضرس (evidence_for_hard_entity_seed; raw=0.133333, boost=0.18)
- `0.313333` الضرس (evidence_for_hard_entity_seed; raw=0.133333, boost=0.18)
- `0.313333` الضرس (evidence_for_hard_entity_seed; raw=0.133333, boost=0.18)
- `0.313333` الضرس (evidence_for_hard_entity_seed; raw=0.133333, boost=0.18)
- `0.313333` الضرس (evidence_for_hard_entity_seed; raw=0.133333, boost=0.18)

**Top qa docs**
- `0.32329` متى يلجأ الدكتور الي نزع عَصّب السن او الضرس (semantic_similarity_only; raw=0.32329, boost=0.0)
- `0.093704` سويت تقويم أسنان و الدكتور الي أشتغل عنده مهمل بس ركب تقويم وخلع ضرس ما نظف لي أي سن و لا شال أي سوسة من أضراسي الخلفية  (semantic_similarity_only; raw=0.093704, boost=0.0)
- `0.090453` ما البديل لعمل كراون للضرس في حال كان طول الضرس قصير بسبب كسر وتآكل في السطح بعد حشو عصب مع حجم طبيعي للضرس ،حتى يعود يص (semantic_similarity_only; raw=0.090453, boost=0.0)
- `0.089443` بنتي سنتين ونصف عندها حساسية من حليب البقر وتأخذ حليب خاص قليل التحسس HA لكن دائم مسبب لها غازات وانتفاخ بالبطن أريد أن  (semantic_similarity_only; raw=0.089443, boost=0.0)
- `0.083406` ماهو علاج ضربة الشمس؟ (semantic_similarity_only; raw=0.083406, boost=0.0)

### سلام لقد اجريت فحص الهرمون B-HCG ،و نتائج التحاليل كما يللي 3-4 اسبوع 9-130 4-5 اسبوع 75-2600 5-6 اسبوع 850-20800 7-8 اسبوع 4000-100200 7-12 اسبوع 11500-289000 12-16 اسبوع 18300-137000 و...

**Top entity docs**
- `0.398113` فحص (hard_entity_seed; raw=0.048113, boost=0.35)
- `0.386084` الهرمون (hard_entity_seed; raw=0.036084, boost=0.35)
- `0.074536` فحص الدم (semantic_similarity_only; raw=0.074536, boost=0.0)
- `0.068041` نقص حديد (semantic_similarity_only; raw=0.068041, boost=0.0)
- `0.066227` نقص فيتامين د (semantic_similarity_only; raw=0.066227, boost=0.0)

**Top evidence docs**
- `0.734968` الحمل (semantic_similarity_only; raw=0.734968, boost=0.0)
- `0.235556` فحص (evidence_for_hard_entity_seed; raw=0.055556, boost=0.18)
- `0.217268` فحص (evidence_for_hard_entity_seed; raw=0.037268, boost=0.18)
- `0.213113` الهرمون (evidence_for_hard_entity_seed; raw=0.033113, boost=0.18)
- `0.094491` ارتفاع خضاب الدم (semantic_similarity_only; raw=0.094491, boost=0.0)

**Top qa docs**
- `0.620108` سلام لقد اجريت فحص الهرمون B-HCG ،و نتائج التحاليل كما يللي 3-4 اسبوع 9-130 4-5 اسبوع 75-2600 5-6 اسبوع 850-20800 7-8 اس (semantic_similarity_only; raw=0.620108, boost=0.0)
- `0.091654` انا اعاني من جميع اعراض نشاط الغده الدرقيه واجريت تحليل وهذه النتائج TSH:0.32 ref range 0.35-5.5 freeT3:3 ref range 2.3- (semantic_similarity_only; raw=0.091654, boost=0.0)
- `0.075094` ما اعاني منه ليس ترهل بل زيادة في الوزن متراكمة في منطقة الارداف فهل هناك اعشاب ممكن ان تساعدني حيث اعلم فائدة الاعشاب ع (semantic_similarity_only; raw=0.075094, boost=0.0)
- `0.074536` سلام تاريخ 8-3-2011 قمت بترجيع الجنين اللى داخل الرحم و قال لي الحكيم ان الجنين لم ينمو حسب ما نريد و لم يعطيني اي نسبة  (semantic_similarity_only; raw=0.074536, boost=0.0)
- `0.074261` E.s.r. 1 st h.= 6 mm { up to 20 mm/hour } 2 nd h. = 13 mm t.s.h. = 1.40 { 0.3 - 4.2 uiu / mj } free... (semantic_similarity_only; raw=0.074261, boost=0.0)

### لسلام عليكم ممكن تساعدوني ابني عملتله تطعيم سنة ونص اليوم هو يعاني من ارتفاع الحرارة ومايقدر يحرك رجلو وحتى يوقف وهو كتير البكاء كيف اتعامل معاه كيف اخفف من الم...

**Top entity docs**
- `0.403916` تطعيم (hard_entity_seed; raw=0.053916, boost=0.35)
- `0.07875` التهاب المفاصل (semantic_similarity_only; raw=0.07875, boost=0.0)
- `0.07875` ألم المفاصل (semantic_similarity_only; raw=0.07875, boost=0.0)
- `0.07566` حمى (semantic_similarity_only; raw=0.07566, boost=0.0)
- `0.066034` سعال (semantic_similarity_only; raw=0.066034, boost=0.0)

**Top evidence docs**
- `0.209907` تطعيم (evidence_for_hard_entity_seed; raw=0.029907, boost=0.18)
- `0.110959` حساسية الصدر (semantic_similarity_only; raw=0.110959, boost=0.0)
- `0.106186` فقر الدم (semantic_similarity_only; raw=0.106186, boost=0.0)
- `0.093386` النقص الشديد للصفائح (semantic_similarity_only; raw=0.093386, boost=0.0)
- `0.093386` النقص الشديد للصفائح (semantic_similarity_only; raw=0.093386, boost=0.0)

**Top qa docs**
- `0.537964` لسلام عليكم ممكن تساعدوني ابني عملتله تطعيم سنة ونص اليوم هو يعاني من ارتفاع الحرارة ومايقدر يحرك رجلو وحتى يوقف وهو كتي (semantic_similarity_only; raw=0.537964, boost=0.0)
- `0.105739` السلام عليكم اناعمري 22 سنة واعاني من القولون العصبي ولدي توسع بالكليتين بسبب وجود الحصى كيف يمكنني التخلص من الحصى ومشا (semantic_similarity_only; raw=0.105739, boost=0.0)
- `0.097627` السلام عليكم أنا عملت تحليل للغدة الدرقيه قبل سنه وكانت النتائج ممتازه ولكن لما عملته بعد مرور سنه ظهر بالتحليل ان المعد (semantic_similarity_only; raw=0.097627, boost=0.0)
- `0.093153` ما سبب أرتفاع درجة الحرارة مع ألم جهه القلب (semantic_similarity_only; raw=0.093153, boost=0.0)
- `0.085416` كيف اعالج الحلمة المسطحة علما باني في شهري الرابع من الحمل وهو حملي الاول فانا اتمنى وارغب في ارضاع طفلي رضاعة طبيعية؟ (semantic_similarity_only; raw=0.085416, boost=0.0)

### هل زيت نبات الميرمية له آثار جانبية عند تناوله بشكل 3 كبسولات قبل الطعام للتخلص من افراز البرولاكتين المفرز والناتج عن ورم حميد في الغدة النخامية . .

**Top entity docs**
- `0.393033` الطعام (hard_entity_seed; raw=0.043033, boost=0.35)
- `0.393033` الميرمية (hard_entity_seed; raw=0.043033, boost=0.35)
- `0.256797` مرض الغدة الدرقية (semantic_candidate_entity; raw=0.136797, boost=0.12)
- `0.219381` الغدة الدرقية (semantic_candidate_entity; raw=0.099381, boost=0.12)
- `0.149071` الهرمون (semantic_similarity_only; raw=0.149071, boost=0.0)

**Top evidence docs**
- `0.844703` الميرمية (evidence_for_hard_entity_seed; raw=0.664703, boost=0.18)
- `0.224947` الطعام (evidence_for_hard_entity_seed; raw=0.044947, boost=0.18)
- `0.214199` الميرمية (evidence_for_hard_entity_seed; raw=0.034199, boost=0.18)
- `0.213333` مرض الغدة الدرقية (evidence_for_semantic_candidate_entity; raw=0.133333, boost=0.08)
- `0.21012` مرض الغدة الدرقية (evidence_for_semantic_candidate_entity; raw=0.13012, boost=0.08)

**Top qa docs**
- `0.441694` هل زيت نبات الميرمية له آثار جانبية عند تناوله بشكل 3 كبسولات قبل الطعام للتخلص من افراز البرولاكتين المفرز والناتج عن و (semantic_similarity_only; raw=0.441694, boost=0.0)
- `0.146795` أعاني من رجفة في القلب تحسسني بالضيق وهي تتزايد حتى في أوقات الراحة و بعض المرات تتثاقل ضربات القلب بشكل مزعج، هل هذا مؤ (semantic_similarity_only; raw=0.146795, boost=0.0)
- `0.13387` في موضوع خمول الغدة الدرقية ..هل عندما تعود الغدة الى وظيفتها الطبيعةبعد الخمول يعود الوزن كم كان قبل حدوث الخمول ؟ ارجو (semantic_similarity_only; raw=0.13387, boost=0.0)
- `0.125988` انا أعني مرض الغدة الدرقية يعني يخفض هل استطيع ان اخذ التروكسين وكم جرام اخذ؟ (semantic_similarity_only; raw=0.125988, boost=0.0)
- `0.120913` ولد لي طفل ولديه أصبع سادسه عظميه في كفه الايمن هل لهذا أثار مستقبليه؟ (semantic_similarity_only; raw=0.120913, boost=0.0)

### عندي الم في منطقه البطن مع الم بصدر جهه اليمين الى الرقبه وماقدرت اعرف تفسير الالم ذا من ايش او سببه مع وجود احيان ضيق بالتنفس ،،،، افيدوني

**Top entity docs**
- `0.390825` الالم (hard_entity_seed; raw=0.040825, boost=0.35)
- `0.121716` الم المعدجة (semantic_similarity_only; raw=0.121716, boost=0.0)
- `0.114109` سعال (semantic_similarity_only; raw=0.114109, boost=0.0)
- `0.098821` فقر الدم (semantic_similarity_only; raw=0.098821, boost=0.0)
- `0.098058` حمى (semantic_similarity_only; raw=0.098058, boost=0.0)

**Top evidence docs**
- `0.220825` الالم (evidence_for_hard_entity_seed; raw=0.040825, boost=0.18)
- `0.163299` حمى (semantic_similarity_only; raw=0.163299, boost=0.0)
- `0.146805` الجلد المترهل (semantic_similarity_only; raw=0.146805, boost=0.0)
- `0.146805` الم المعدجة (semantic_similarity_only; raw=0.146805, boost=0.0)
- `0.13484` فقر الدم (semantic_similarity_only; raw=0.13484, boost=0.0)

**Top qa docs**
- `0.548161` عندي الم في منطقه البطن مع الم بصدر جهه اليمين الى الرقبه وماقدرت اعرف تفسير الالم ذا من ايش او سببه مع وجود احيان ضيق ب (semantic_similarity_only; raw=0.548161, boost=0.0)
- `0.176505` اشعر باعراض لم اشعر بها من قبل فالبارحة احسست بوخز في قلبي و اليوم عندما اتنفس اتنفس بصعوبة مع الم شديد في الصدر من جهة  (semantic_similarity_only; raw=0.176505, boost=0.0)
- `0.154983` اسلام عليكم انا اعاني من ألم في الصدر مع الاحساس بوجود شئ في منطقة الظور والصدر والرغبه في القئ مع وجود ألم ونغزه في الج (semantic_similarity_only; raw=0.154983, boost=0.0)
- `0.144093` ما تفسير شعورى بقبضة فى صدرى تستغرق بضعة ثوانى ويصاحبها ضيق فى التنفس ....كان يتكرر هذا الموضوع معى من فترة الى اخرى ثم  (semantic_similarity_only; raw=0.144093, boost=0.0)
- `0.13838` والدتي تعاني من نقص في الدم مع الالم في المعده (semantic_similarity_only; raw=0.13838, boost=0.0)

## Output Files

- Semantic retrieval JSON: `outputs/05_trial_graph_v1/semantic_retrieval/trial_graph_v1_semantic_retrieval_results.json`
- Semantic retrieval CSV: `outputs/05_trial_graph_v1/semantic_retrieval/trial_graph_v1_semantic_retrieval_results.csv`
- Semantic metrics JSON: `outputs/05_trial_graph_v1/semantic_retrieval/trial_graph_v1_semantic_retrieval_metrics.json`
- Semantic metrics CSV: `outputs/05_trial_graph_v1/semantic_retrieval/trial_graph_v1_semantic_retrieval_metrics.csv`

## Next Step From Mix.png

Use these semantic retrieval results in Step 9C hybrid retrieval with graph traversal and relation-weighted reranking.
