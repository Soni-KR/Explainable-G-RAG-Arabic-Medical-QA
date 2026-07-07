# Trial Graph v1 Step 6 Embedding Search Report

This tests whether generated MiniLM embeddings are searchable before Step 9 semantic/hybrid retrieval.

## Model

- Embedding model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Embedded documents: 2145

## Search Tests

### ما علاج الحساسية؟

**Search mode: `raw_query`**

- Search text: `ما علاج الحساسية؟`

Top entity docs
- `0.638026` التروكسين (entity::ent_treatment_3fd682796ae8)
- `0.634724` دوالي الساقين (entity::ent_diseasecondition_c4254d272647)
- `0.633519` تيليفاست (entity::ent_treatment_104bb0a91d5a)
- `0.625593` كورتيزون (entity::ent_treatment_843876e28a68)
- `0.617757` الايزوتريتينوين (entity::ent_treatment_039793a12776)

Top evidence docs
- `0.662461` فينوروتون (mention::men_llm_0000073)
- `0.61304` التهاب اللوزتين (mention::men_llm_0000061)
- `0.584204` مرهم مايكونازول (mention::men_llm_0000097)
- `0.582153` مضاد حيوي (mention::men_llm_0000541)
- `0.582153` مضاد حيوي (mention::men_llm_0000540)

Top qa docs
- `0.652689` ماهو علاج ضربة الشمس؟ (qa::ahd5k_04919)
- `0.645762` هل يوجد علاج للتشخيص المسمى \"pseudoexanthoma الاستيك \" او اي مستحضر طبي يقلل من الاعراض الجانبية (qa::ahd5k_03085)
- `0.572453` هل يوجد علاج دوائى او طبيعي لعلاج انفراص بالفاصل العجزي القطني (qa::ahd5k_00088)
- `0.54165` انا ابتلعت دبوس امس ولا اشعر ببلعه واعاني بوجع صدري كيف اعمل (qa::ahd5k_01295)
- `0.518787` ماهى فوائد الكركم بالنسبة لتفتيح البشرة وكيفية استخدامة (qa::ahd5k_03805)


**Search mode: `step8_enriched_query`**

- Search text: `ما علاج الحساسية؟ | حساسية | حساسية الصدر | treatments and medical recommendations`

Top entity docs
- `0.585334` تيليفاست (entity::ent_treatment_104bb0a91d5a)
- `0.566049` كورتيزون (entity::ent_treatment_843876e28a68)
- `0.565745` بلغم (entity::ent_symptom_dc2c7333a505)
- `0.549953` دوالي الساقين (entity::ent_diseasecondition_c4254d272647)
- `0.54572` جرعة (entity::ent_treatment_72992721d87a)

Top evidence docs
- `0.617175` حساسية (mention::men_llm_0000001)
- `0.597055` حساسية (mention::men_llm_0000505)
- `0.595219` حساسية الصدر (mention::men_llm_0000031)
- `0.572747` بلغم (mention::men_llm_0000008)
- `0.564602` حساسية (mention::men_llm_0000021)

Top qa docs
- `0.636168` اعاني من حساسية في الصدر وضيق في التنفس وسعال وقئ صباحا (qa::ahd5k_03662)
- `0.629256` هل يوجد علاج للتشخيص المسمى \"pseudoexanthoma الاستيك \" او اي مستحضر طبي يقلل من الاعراض الجانبية (qa::ahd5k_03085)
- `0.59917` ماهو علاج ضربة الشمس؟ (qa::ahd5k_04919)
- `0.582737` انا ابتلعت دبوس امس ولا اشعر ببلعه واعاني بوجع صدري كيف اعمل (qa::ahd5k_01295)
- `0.565215` سوألي هناك فتاه تشعر بحراره شديده في جسمها الخارجي وقليل جدا من داخل جسمها ولاترتاح الا بالاغتسال ومستمر الحال معها قراب (qa::ahd5k_02470)


### عندي كحة وبلغم هل هذا ربو؟

**Search mode: `raw_query`**

- Search text: `عندي كحة وبلغم هل هذا ربو؟`

Top entity docs
- `0.248932` كيس (entity::ent_symptom_170df8c18553)
- `0.245816` ارتجاف (entity::ent_symptom_a3c00de774da)
- `0.237` بلغم (entity::ent_symptom_dc2c7333a505)
- `0.226347` المغص (entity::ent_symptom_4c83b1bd25ea)
- `0.225169` بروز في البطن (entity::ent_symptom_6910233b82fc)

Top evidence docs
- `0.323408` انزلاق غضروفي عنقي (mention::men_llm_0000748)
- `0.292563` حساسية (mention::men_llm_0000027)
- `0.2849` قرحة (mention::men_llm_0001074)
- `0.278754` فقر الدم (mention::men_llm_0000317)
- `0.275774` الجيب اللثوي (mention::men_llm_0000668)

Top qa docs
- `0.300102` قبل شهرين وخلال استحمامي احسست فجأه بدخول شيء غريب خلال اصابع لقدمين نحو ساقيي بسرعه وبأعداد كبيره تجري داخل جلدي (كالنم (qa::ahd5k_01874)
- `0.271739` حصل لديه وجع فوق الصرة ودخلت مستشفى وبعد الصور والتحاليل تبين بحص بالمرارة ثم تبين لدي التهاب بالبنكريس وخرجت ثم عملت صو (qa::ahd5k_04916)
- `0.258169` منذ دخول فصل الشتاء انتابتني بعض الاعراض ولاسيما في الرجل اليسري اشعر بالم في المفصل ودلك عند ثني الرجل يإما بالجلوس اوا (qa::ahd5k_00114)
- `0.25349` مند يومين لحظت الم بسيط في القضيب الدكري والم عند التبول بسيط ومع مرور يومين ازدادة عدي حكة في القضيب مرة مرة وتختفي عند (qa::ahd5k_03685)
- `0.251692` ماهو التهاب الشعرة وكيفية الوقاية منه وماهو علاجه (qa::ahd5k_03594)


**Search mode: `step8_enriched_query`**

- Search text: `عندي كحة وبلغم هل هذا ربو؟ | ربو | بلغم | سعال | سعال | symptoms and possible associated conditions`

Top entity docs
- `0.670127` سعال (entity::ent_symptom_f4cf885a0447)
- `0.657093` حمى (entity::ent_symptom_018ebc11f6df)
- `0.65453` الضيق التنفسي (entity::ent_symptom_b5e5cc252e6a)
- `0.630464` بلغم (entity::ent_symptom_dc2c7333a505)
- `0.625055` حساسية الصدر (entity::ent_diseasecondition_250910ab0701)

Top evidence docs
- `0.70782` التهاب (mention::men_llm_0000652)
- `0.690735` سعال (mention::men_llm_0000651)
- `0.689639` تحليل الحساسية (mention::men_llm_0000977)
- `0.679794` سعال (mention::men_llm_0000976)
- `0.656488` بلغم (mention::men_llm_0000008)

Top qa docs
- `0.614792` اشعر باعراض لم اشعر بها من قبل فالبارحة احسست بوخز في قلبي و اليوم عندما اتنفس اتنفس بصعوبة مع الم شديد في الصدر من جهة  (qa::ahd5k_04235)
- `0.602675` اعاني من حساسية في الصدر وضيق في التنفس وسعال وقئ صباحا (qa::ahd5k_03662)
- `0.587929` لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام  (qa::ahd5k_02662)
- `0.579057` اشعر بدوخة وصداع دائم ! هل يمكن أن يكون ما أشعر به أعراض لمرض ؟ ماذا أفعل .. (qa::ahd5k_03689)
- `0.572013` مند يومين لحظت الم بسيط في القضيب الدكري والم عند التبول بسيط ومع مرور يومين ازدادة عدي حكة في القضيب مرة مرة وتختفي عند (qa::ahd5k_03685)


### ما التحاليل المناسبة لفقر الدم؟

**Search mode: `raw_query`**

- Search text: `ما التحاليل المناسبة لفقر الدم؟`

Top entity docs
- `0.712682` CBC التحليل الكامل للدم (entity::ent_test_f405aec80933)
- `0.610978` الدم (entity::ent_symptom_59d5c1de0b88)
- `0.599457` صورة دم (entity::ent_test_c0d07b06fcff)
- `0.561025` التبرع بالدم (entity::ent_treatment_3677ba04b27f)
- `0.555635` فحص الدم (entity::ent_test_4ea4666752c1)

Top evidence docs
- `0.693503` CBC التحليل الكامل للدم (mention::men_llm_0001053)
- `0.68237` فقر الدم (mention::men_llm_0000299)
- `0.624512` تحاليل مخبرية (mention::men_llm_0000728)
- `0.623509` اللمف (mention::men_llm_0000126)
- `0.622603` فقر دم (mention::men_llm_0000110)

Top qa docs
- `0.670072` انخفاض نسبة الهمجلوبين فى الدم (qa::ahd5k_04046)
- `0.635493` كان لدي ارتفاع بسيط في الصفائح ٤٦١ وعندما ولدت بعد ٥٠ يوم التحليل طلع ٦٧٩ واشكو من عدم اكتمال النفس في بعض الاوقات وقال  (qa::ahd5k_01422)
- `0.635124` دكتور انا من مصر وعندى مشكلة في الصفائح الدموية ضعيفة ونسبة الأملاح عالية جدا أروح لدكتور ايه؟ (qa::ahd5k_03348)
- `0.621021` مالمقصود باللمف (qa::ahd5k_00291)
- `0.617618` كيف اعلاج التهاب الدم (qa::ahd5k_01104)


**Search mode: `step8_enriched_query`**

- Search text: `ما التحاليل المناسبة لفقر الدم؟ | فقر الدم | diagnostic tests and investigations`

Top entity docs
- `0.747755` CBC التحليل الكامل للدم (entity::ent_test_f405aec80933)
- `0.693795` الدم (entity::ent_symptom_59d5c1de0b88)
- `0.685828` انخفاض ضغط الدم (entity::ent_diseasecondition_58d7d4ebddc3)
- `0.685623` فحص الدم (entity::ent_test_4ea4666752c1)
- `0.652753` الصفائح الدموية (entity::ent_diseasecondition_b3e7fc089ddd)

Top evidence docs
- `0.711524` فقر دم (mention::men_llm_0000110)
- `0.706663` التهاب (mention::men_llm_0000236)
- `0.694296` تحاليل مخبرية (mention::men_llm_0000728)
- `0.685602` فقر الدم (mention::men_llm_0000299)
- `0.6773` CBC التحليل الكامل للدم (mention::men_llm_0001053)

Top qa docs
- `0.712325` كيف اعلاج التهاب الدم (qa::ahd5k_01104)
- `0.700862` ضغط الدم منخفض للغاية مع عدم وضوح للرؤية (qa::ahd5k_01761)
- `0.697654` كان لدي ارتفاع بسيط في الصفائح ٤٦١ وعندما ولدت بعد ٥٠ يوم التحليل طلع ٦٧٩ واشكو من عدم اكتمال النفس في بعض الاوقات وقال  (qa::ahd5k_01422)
- `0.689334` دكتور انا من مصر وعندى مشكلة في الصفائح الدموية ضعيفة ونسبة الأملاح عالية جدا أروح لدكتور ايه؟ (qa::ahd5k_03348)
- `0.684643` انخفاض نسبة الهمجلوبين فى الدم (qa::ahd5k_04046)


### ما أسباب صداع مع دوخة؟

**Search mode: `raw_query`**

- Search text: `ما أسباب صداع مع دوخة؟`

Top entity docs
- `0.611181` التهاب السحايا (entity::ent_diseasecondition_d9b91988beb9)
- `0.591694` صداع التوتر (entity::ent_symptom_c01e00eb5c72)
- `0.583687` باندول فولت فاست (entity::ent_treatment_2466e618d2bf)
- `0.566843` الصداع التوتري (entity::ent_diseasecondition_00247d3d5c80)
- `0.538554` صداع (entity::ent_symptom_b754f1a1e5a8)

Top evidence docs
- `0.683357` صداع (mention::men_llm_0000736)
- `0.663024` صداع (mention::men_llm_0000565)
- `0.658768` الصداع التوتري (mention::men_llm_0000737)
- `0.658586` صداع (mention::men_llm_0000422)
- `0.654517` صداع (mention::men_llm_0000091)

Top qa docs
- `0.570554` اشعر بدوخة وصداع دائم ! هل يمكن أن يكون ما أشعر به أعراض لمرض ؟ ماذا أفعل .. (qa::ahd5k_03689)
- `0.55178` اختي عمرها 17 ومنذ سنتين تقريبا اصبحت تصاب بالام حادة في الراس وعندما تصاب بها تشعر بنض سريع وقوي جدا في الشرايين الموجو (qa::ahd5k_00222)
- `0.480001` ما هو سبب الوجع الشديد في الجنب اليمين مع ترجيع؟ (qa::ahd5k_04921)
- `0.441418` كيف استطيع التخلص من المغص المعوي (qa::ahd5k_02511)
- `0.422794` لدي الم في جانبي راسي وخصوصا الايسر فوق الاذن اشعر بضغط فى هذه المنطقه وكانه شي سينفجر وكثير من الاوقات اشعر بارهاق عام  (qa::ahd5k_02662)


**Search mode: `step8_enriched_query`**

- Search text: `ما أسباب صداع مع دوخة؟ | صداع | دوخة | صداع التوتر | possible conditions and relation evidence`

Top entity docs
- `0.604553` الصداع التوتري (entity::ent_diseasecondition_00247d3d5c80)
- `0.587764` التهاب الجيوب الأنفية (entity::ent_diseasecondition_ad3e19c416f6)
- `0.571236` صداع (entity::ent_symptom_b754f1a1e5a8)
- `0.560975` صداع التوتر (entity::ent_symptom_c01e00eb5c72)
- `0.5499` التهاب السحايا (entity::ent_diseasecondition_d9b91988beb9)

Top evidence docs
- `0.717139` صداع (mention::men_llm_0000714)
- `0.707464` صداع التوتر (mention::men_llm_0000712)
- `0.691357` القلق (mention::men_llm_0000718)
- `0.687518` صداع (mention::men_llm_0000734)
- `0.677548` الصداع النصفي (mention::men_llm_0000720)

Top qa docs
- `0.535499` اشعر بدوخة وصداع دائم ! هل يمكن أن يكون ما أشعر به أعراض لمرض ؟ ماذا أفعل .. (qa::ahd5k_03689)
- `0.510451` ماهي اسباب التهاب غدة الثدي؟ (qa::ahd5k_03985)
- `0.508848` ما هو سبب الوجع الشديد في الجنب اليمين مع ترجيع؟ (qa::ahd5k_04921)
- `0.50108` اختي عمرها 17 ومنذ سنتين تقريبا اصبحت تصاب بالام حادة في الراس وعندما تصاب بها تشعر بنض سريع وقوي جدا في الشرايين الموجو (qa::ahd5k_00222)
- `0.453682` هل هناك علاقة بين سوفان الرقبة وأرتفاع ضغط الدم؟ (qa::ahd5k_04477)


## Output Files

- Search JSON: `outputs/05_trial_graph_v1/embeddings/trial_graph_v1_embedding_search_test.json`
- Search CSV: `outputs/05_trial_graph_v1/embeddings/trial_graph_v1_embedding_search_test.csv`

## Status

- Embeddings generated: yes
- Vector search tested: yes, using linear cosine search over normalized embeddings
- FAISS/Neo4j vector index: not created yet; this smoke test validates the vectors before choosing the production index.
