# Trial Graph v1 Step 9C Hybrid Retrieval Report

This combines Step 8 query understanding, Step 9A semantic retrieval, and graph traversal over the frozen bidirectional relation graph.

## Scoring

- Relation confidence from Step 4 validation
- Seed strength from Step 8 hard detections and soft candidates
- Intent-specific relation weights from Step 8
- Semantic support from Step 9A entity/evidence/QA retrieval
- Small bonus for original/direct graph edges
- Query-time family-equivalent seeds for known duplicate families such as `سكري` / `مرض السكري`

## Query Results

### ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟ هل امتنع عن طعام معين يزيد البلغم وانا غير مدخن واخذ علاج للضغط والكوليسترول عمرى 55...

**Top hybrid graph relations**
- `0.871748` حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين (seed=حساسية, relation_weight=1.0)
- `0.856963` حساسية --TREATED_BY--> مضاد الهيستامين (seed=حساسية, relation_weight=1.0)
- `0.856963` حساسية --TREATED_BY--> كورتيزون (seed=حساسية, relation_weight=1.0)
- `0.85182` حساسية --TREATED_BY--> تيليفاست (seed=حساسية, relation_weight=1.0)
- `0.846477` ارتفاع الكوليسترول --MANAGED_BY--> تقليل الدهون والرياضة (seed=ارتفاع الكوليسترول, relation_weight=1.0)
- `0.837034` حساسية --TREATED_BY--> حليب مكسر بروتين الحليب (seed=حساسية, relation_weight=1.0)
- `0.83532` حساسية --TREATED_BY--> نازونكس (seed=حساسية, relation_weight=1.0)
- `0.827391` حساسية --TREATED_BY--> زيت الحبة السوداء (seed=حساسية, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.871748` حساسية TREATED_BY تجنب المنتجات التي تحوي جلوتين
- `graph_relation` `0.856963` حساسية TREATED_BY مضاد الهيستامين
- `graph_relation` `0.856963` حساسية TREATED_BY كورتيزون
- `graph_relation` `0.85182` حساسية TREATED_BY تيليفاست
- `graph_relation` `0.846477` ارتفاع الكوليسترول MANAGED_BY تقليل الدهون والرياضة
- `graph_relation` `0.837034` حساسية TREATED_BY حليب مكسر بروتين الحليب

### كيف اعالج علامات الشيخوخة المبكرة بالوجه؟

**Top hybrid graph relations**
- `0.705785` تضيق القنوات الموجودة داخل الكبد --TREATED_BY--> منظار قنوات مرارية الف سلامة (seed=تضيق القنوات الموجودة داخل الكبد, relation_weight=1.0)
- `0.665785` منظار قنوات مرارية الف سلامة --TREATS--> تضيق القنوات الموجودة داخل الكبد (seed=منظار قنوات مرارية الف سلامة, relation_weight=1.0)
- `0.394817` حساسية --DIAGNOSED_BY--> تحاليل مخبرية (seed=حساسية, relation_weight=-0.2)
- `0.394513` انتفاخ --INVESTIGATED_BY--> اشعة (seed=انتفاخ, relation_weight=-0.2)
- `0.394243` وجع --INVESTIGATED_BY--> اشعة (seed=وجع, relation_weight=-0.2)
- `0.354817` تحاليل مخبرية --DIAGNOSES--> حساسية (seed=تحاليل مخبرية, relation_weight=-0.2)
- `0.354513` اشعة --INVESTIGATES--> انتفاخ (seed=اشعة, relation_weight=-0.2)
- `0.354243` اشعة --INVESTIGATES--> وجع (seed=اشعة, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.705785` تضيق القنوات الموجودة داخل الكبد TREATED_BY منظار قنوات مرارية الف سلامة
- `graph_relation` `0.665785` منظار قنوات مرارية الف سلامة TREATS تضيق القنوات الموجودة داخل الكبد
- `graph_relation` `0.394817` حساسية DIAGNOSED_BY تحاليل مخبرية
- `graph_relation` `0.394513` انتفاخ INVESTIGATED_BY اشعة
- `graph_relation` `0.394243` وجع INVESTIGATED_BY اشعة
- `graph_relation` `0.354817` تحاليل مخبرية DIAGNOSES حساسية

### ماالعلاج الاسعافي لأنخفاض السكر مع فقدان الوعي

**Top hybrid graph relations**
- `0.921311` فقدان الوعي --TREATED_BY--> عسل (seed=فقدان الوعي, relation_weight=1.0)
- `0.778613` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (seed=مرض السكري, relation_weight=1.0)
- `0.768113` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.762113` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.756113` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.718283` التهاب --DIAGNOSED_BY--> تحاليل مخبرية (seed=التهاب, relation_weight=1.0)
- `0.449311` عسل --TREATS--> فقدان الوعي (seed=عسل, relation_weight=-0.2)
- `0.414613` تحاليل مخبرية --DIAGNOSES--> مرض السكري (seed=تحاليل مخبرية, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.921311` فقدان الوعي TREATED_BY عسل
- `graph_relation` `0.778613` مرض السكري DIAGNOSED_BY تحاليل مخبرية
- `graph_relation` `0.768113` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.762113` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.756113` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.718283` التهاب DIAGNOSED_BY تحاليل مخبرية

### هل الاشعة المقطعيه بالصبغه للقلب تسبب انتفاخ اسفل الوجه او انتفاخ الغده هل هو طبيعي

**Top hybrid graph relations**
- `0.8814` انتفاخ --INVESTIGATED_BY--> اشعة (seed=انتفاخ, relation_weight=1.0)
- `0.8414` اشعة --INVESTIGATES--> انتفاخ (seed=أشعة, relation_weight=1.0)
- `0.836325` أشعة --DIAGNOSES--> تسوس الأسنان (seed=أشعة, relation_weight=1.0)
- `0.832575` اشعة --INVESTIGATES--> وجع (seed=أشعة, relation_weight=1.0)
- `0.832575` اشعة --DIAGNOSES--> التهاب (seed=أشعة, relation_weight=1.0)
- `0.828825` أشعة --DIAGNOSES--> ارتجاج دماغي (seed=أشعة, relation_weight=1.0)
- `0.825075` أشعة --DIAGNOSES--> انزلاق غضروفي عنقي (seed=أشعة, relation_weight=1.0)
- `0.825075` أشعة --DIAGNOSES--> شظايا القنابل الصغيرة الانشطارية (seed=أشعة, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.8814` انتفاخ INVESTIGATED_BY اشعة
- `graph_relation` `0.8414` اشعة INVESTIGATES انتفاخ
- `graph_relation` `0.836325` أشعة DIAGNOSES تسوس الأسنان
- `graph_relation` `0.832575` اشعة INVESTIGATES وجع
- `graph_relation` `0.832575` اشعة DIAGNOSES التهاب
- `graph_relation` `0.828825` أشعة DIAGNOSES ارتجاج دماغي

### السلام عليكم..ماهو العلاج المناسب لتقليل نسبة الاملاح في الدم النسبة الحالية عندي هي (7.9) عمري 44 سنة /ذكر؟

**Top hybrid graph relations**
- `0.589286` حساسية الصدر --HAS_SYMPTOM--> سعال (seed=حساسية الصدر, relation_weight=0.4)
- `0.586839` التهاب --HAS_SYMPTOM--> الدم (seed=التهاب, relation_weight=0.4)
- `0.549286` سعال --SYMPTOM_OF--> حساسية الصدر (seed=سعال, relation_weight=0.4)
- `0.546839` الدم --SYMPTOM_OF--> التهاب (seed=الدم, relation_weight=0.4)
- `0.430239` التهاب --DIAGNOSED_BY--> تصوير الجهاز البولي (seed=التهاب, relation_weight=-0.2)
- `0.426939` الدم --INVESTIGATED_BY--> تصوير الجهاز البولي (seed=الدم, relation_weight=-0.2)
- `0.426086` حساسية الصدر --DIAGNOSED_BY--> تحليل الحساسية (seed=حساسية الصدر, relation_weight=-0.2)
- `0.390239` تصوير الجهاز البولي --DIAGNOSES--> التهاب (seed=تصوير الجهاز البولي, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.589286` حساسية الصدر HAS_SYMPTOM سعال
- `graph_relation` `0.586839` التهاب HAS_SYMPTOM الدم
- `graph_relation` `0.549286` سعال SYMPTOM_OF حساسية الصدر
- `graph_relation` `0.546839` الدم SYMPTOM_OF التهاب
- `graph_relation` `0.430239` التهاب DIAGNOSED_BY تصوير الجهاز البولي
- `graph_relation` `0.426939` الدم INVESTIGATED_BY تصوير الجهاز البولي

### السلام عليكم أنا أشعر ببرودة رأسي -وغذا اصبح ملمس رأسي بارد جاني صداع لايزول بالمسكنات- ذهبت لأفضل أخصائي أنف وأذن وحنجرة قال هذا المرض ماله علاج !! ماهي التحاليل الأزمة...

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.858408` صداع --SYMPTOM_OF--> التهاب السحايا (seed=صداع, relation_weight=1.0)
- `0.841908` صداع --SYMPTOM_OF--> التهاب الجيوب الأنفية (seed=صداع, relation_weight=1.0)
- `0.835702` صداع --SYMPTOM_OF--> الصداع التوتري (seed=صداع, relation_weight=1.0)
- `0.821271` صداع --SYMPTOM_OF--> ضرس العقل (seed=صداع, relation_weight=1.0)
- `0.785524` صداع --INVESTIGATED_BY--> الصور الشعاعية (seed=صداع, relation_weight=0.4)
- `0.766408` التهاب السحايا --HAS_SYMPTOM--> صداع (seed=التهاب السحايا, relation_weight=1.0)
- `0.749908` التهاب الجيوب الأنفية --HAS_SYMPTOM--> صداع (seed=التهاب الجيوب الأنفية, relation_weight=1.0)
- `0.729271` ضرس العقل --HAS_SYMPTOM--> صداع (seed=ضرس العقل, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.858408` صداع SYMPTOM_OF التهاب السحايا
- `graph_relation` `0.841908` صداع SYMPTOM_OF التهاب الجيوب الأنفية
- `graph_relation` `0.835702` صداع SYMPTOM_OF الصداع التوتري
- `graph_relation` `0.821271` صداع SYMPTOM_OF ضرس العقل
- `graph_relation` `0.785524` صداع INVESTIGATED_BY الصور الشعاعية
- `graph_relation` `0.766408` التهاب السحايا HAS_SYMPTOM صداع

### مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد المستشفی

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.624663` قرحة --TREATED_BY--> ايزومبرازول (seed=قرحة, relation_weight=-0.2)
- `0.452663` ايزومبرازول --TREATS--> قرحة (seed=ايزومبرازول, relation_weight=-0.2)
- `0.438359` الملوية البوابية --TREATED_BY--> الدواء (seed=الملوية البوابية, relation_weight=-0.2)
- `0.398359` الدواء --TREATS--> الملوية البوابية (seed=الدواء, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.624663` قرحة TREATED_BY ايزومبرازول
- `graph_relation` `0.452663` ايزومبرازول TREATS قرحة
- `graph_relation` `0.438359` الملوية البوابية TREATED_BY الدواء
- `graph_relation` `0.398359` الدواء TREATS الملوية البوابية
- `semantic_evidence` `0.588631` Evidence: مامتي جدا تعبانه من القرحة
Entity: قرحة
Surface form: قرحة
Field: question
Relation context: قرحة TREATED_BY ايزومبرازول. Evidence: ممكن تجرب دواء اسمه ايزومبرازول
- `semantic_qa` `0.551158` Category: أمراض باطنية (Esoteric)
Question: مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد المستشفی
Answer: هل افهم من سؤالك ان والدتك عندها قرحه مع نزيف مستمر اذا كان الامر هكذا فلابد من ذهابها الى المستشفى لان النزيف المستمر سيشكل خطر على حياتها. اما اذا كانت القرحه مؤكده بدو

### ما البديل لعمل كراون للضرس في حال كان طول الضرس قصير بسبب كسر وتآكل في السطح بعد حشو عصب مع حجم طبيعي للضرس ،حتى يعود يصبح في طول يسمح بتركيب...

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.457136` حشو الأسنان --NOT_ASSOCIATED_WITH--> غمازة الوجه (seed=حشو الأسنان, relation_weight=-0.2)
- `0.457136` تخدير موضعي قوي --MAY_TEMPORARILY_AFFECT--> غمازة الوجه (seed=تخدير موضعي قوي, relation_weight=-0.2)
- `0.452691` برد الأسنان --HAS_RISK--> حساسية الأسنان (seed=برد الأسنان, relation_weight=-0.2)
- `0.452691` برد الأسنان --PROCEDURE_DURATION--> جلسة واحدة أو جلستان (seed=برد الأسنان, relation_weight=-0.2)
- `0.400941` بروز في البطن --TREATED_BY--> تمارين رياضية (seed=بروز في البطن, relation_weight=-0.2)
- `0.360941` تمارين رياضية --TREATS--> بروز في البطن (seed=تمارين رياضية, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.457136` حشو الأسنان NOT_ASSOCIATED_WITH غمازة الوجه
- `graph_relation` `0.457136` تخدير موضعي قوي MAY_TEMPORARILY_AFFECT غمازة الوجه
- `graph_relation` `0.452691` برد الأسنان HAS_RISK حساسية الأسنان
- `graph_relation` `0.452691` برد الأسنان PROCEDURE_DURATION جلسة واحدة أو جلستان
- `graph_relation` `0.400941` بروز في البطن TREATED_BY تمارين رياضية
- `graph_relation` `0.360941` تمارين رياضية TREATS بروز في البطن

### زوجتي حامل ومنذ بداية حملها لم اتوقف عن الاتصال معهاابدا ..فهل ذلك له علاقه لما تشعر به من حرقه في المهبل...وهل ذلك له تأثير على الجنين....

**Top hybrid graph relations**
- `0.601929` حرقه --SYMPTOM_OF--> التهاب (seed=حرقه, relation_weight=-0.2)
- `0.509929` التهاب --HAS_SYMPTOM--> حرقه (seed=التهاب, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.601929` حرقه SYMPTOM_OF التهاب
- `graph_relation` `0.509929` التهاب HAS_SYMPTOM حرقه
- `semantic_qa` `0.715238` Category: حمل الأنابيب (Carry tubes)
Question: زوجتي حامل ومنذ بداية حملها لم اتوقف عن الاتصال معهاابدا ..فهل ذلك له علاقه لما تشعر به من حرقه في المهبل...وهل ذلك له تأثير على الجنين....
Answer: ﻻتاثير على الجنين...والحرقه من التهابات نسائيه
Relation context: التهاب HAS_SYMPTOM حرقه. Evidence: التهابات نسائيه تسبب حرقه في المهبل
- `semantic_evidence` `0.415728` Evidence: حرقه في المهبل
Entity: حرقه
Surface form: حرقه
Field: question
Relation context: التهاب HAS_SYMPTOM حرقه. Evidence: التهابات نسائيه تسبب حرقه في المهبل
- `semantic_evidence` `0.250634` Evidence: الجنين
Entity: الجنين
Surface form: الجنين
Field: answer
Relation context: 
- `semantic_evidence` `0.245834` Evidence: الجنين
Entity: الجنين
Surface form: الجنين
Field: question
Relation context: 

### لمدا كلما انزعجت من شخص ما أشعر بدوار ودقات سريعة للقلب وشعور براسي تقيل تم يغمى علي دون الغياب عن الوعي فما تشخيصكم لهدا وشكراً جزيل

**Top hybrid graph relations**
- `0.434009` فقر الدم --MANAGED_BY--> أغذية غنية بالحديد والفولات وفيتامين ب12 (seed=فقر الدم, relation_weight=-0.2)
- `0.434009` أغذية غنية بالحديد والفولات وفيتامين ب12 --ABSORPTION_IMPROVED_BY--> أطعمة غنية بفيتامين ج (seed=أغذية غنية بالحديد والفولات وفيتامين ب12, relation_weight=-0.2)
- `0.434009` أغذية غنية بالحديد والفولات وفيتامين ب12 --ABSORPTION_REDUCED_BY--> الشاي والقهوة والكالسيوم مع الحديد (seed=أغذية غنية بالحديد والفولات وفيتامين ب12, relation_weight=-0.2)
- `0.394756` سيلان الانف --TREATED_BY--> بخاخات الماء والملح (seed=سيلان الانف, relation_weight=-0.2)
- `0.394756` سيلان الانف --INVESTIGATED_BY--> خصائي الاطفال (seed=سيلان الانف, relation_weight=-0.2)
- `0.354756` بخاخات الماء والملح --TREATS--> سيلان الانف (seed=بخاخات الماء والملح, relation_weight=-0.2)
- `0.354756` خصائي الاطفال --INVESTIGATES--> سيلان الانف (seed=خصائي الاطفال, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.434009` فقر الدم MANAGED_BY أغذية غنية بالحديد والفولات وفيتامين ب12
- `graph_relation` `0.434009` أغذية غنية بالحديد والفولات وفيتامين ب12 ABSORPTION_IMPROVED_BY أطعمة غنية بفيتامين ج
- `graph_relation` `0.434009` أغذية غنية بالحديد والفولات وفيتامين ب12 ABSORPTION_REDUCED_BY الشاي والقهوة والكالسيوم مع الحديد
- `graph_relation` `0.394756` سيلان الانف TREATED_BY بخاخات الماء والملح
- `graph_relation` `0.394756` سيلان الانف INVESTIGATED_BY خصائي الاطفال
- `graph_relation` `0.354756` بخاخات الماء والملح TREATS سيلان الانف

### عندي فقر دم وعملت التحاليل عندي نقص فيتامين دال ونقص حديد وصف لي الدكتور 20 ابرة حديد لمدة شهر هل اخذ هالكمية بهذه المدة آمن أم مضر للجسم ؟ وما...

**Top hybrid graph relations**
- `0.80838` فقر الدم --HAS_SYMPTOM--> تنميل (seed=فقر الدم, relation_weight=1.0)
- `0.801951` فقر الدم --HAS_SYMPTOM--> الم المعدجة (seed=فقر الدم, relation_weight=1.0)
- `0.801951` فقر الدم --HAS_SYMPTOM--> الم المعدجة (seed=فقر الدم, relation_weight=1.0)
- `0.801951` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (seed=فقر الدم, relation_weight=1.0)
- `0.777847` نقص حديد --DIAGNOSED_BY--> فحص تحاليل مخبرية (seed=نقص حديد, relation_weight=0.4)
- `0.741847` فقر الدم --DIAGNOSED_BY--> فحص تحاليل مخبرية (seed=فقر الدم, relation_weight=0.4)
- `0.722321` نقص هرمونات --HAS_SYMPTOM--> انقطاع الطمث (seed=نقص هرمونات, relation_weight=1.0)
- `0.682321` انقطاع الطمث --SYMPTOM_OF--> نقص هرمونات (seed=انقطاع الطمث, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.80838` فقر الدم HAS_SYMPTOM تنميل
- `graph_relation` `0.801951` فقر الدم HAS_SYMPTOM الم المعدجة
- `graph_relation` `0.801951` فقر الدم HAS_SYMPTOM الم المعدجة
- `graph_relation` `0.801951` فقر الدم HAS_SYMPTOM فقدان الشهيه
- `graph_relation` `0.777847` نقص حديد DIAGNOSED_BY فحص تحاليل مخبرية
- `graph_relation` `0.741847` فقر الدم DIAGNOSED_BY فحص تحاليل مخبرية

### أود معرفة ما أسباب تدلي المستقيم؟وطرق العلاج؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.747089` حساسية الصدر --HAS_SYMPTOM--> سعال (seed=حساسية الصدر, relation_weight=1.0)
- `0.730487` التهاب --HAS_SYMPTOM--> الدم (seed=التهاب, relation_weight=1.0)
- `0.707089` سعال --SYMPTOM_OF--> حساسية الصدر (seed=سعال, relation_weight=1.0)
- `0.690487` الدم --SYMPTOM_OF--> التهاب (seed=الدم, relation_weight=1.0)
- `0.577381` دوالي الخصية --TREATED_BY--> العلاج بالجراحة (seed=دوالي الخصية, relation_weight=0.4)
- `0.537381` العلاج بالجراحة --TREATS--> دوالي الخصية (seed=العلاج بالجراحة, relation_weight=0.4)
- `0.433889` حساسية الصدر --DIAGNOSED_BY--> تحليل الحساسية (seed=حساسية الصدر, relation_weight=-0.2)
- `0.423887` التهاب --DIAGNOSED_BY--> تصوير الجهاز البولي (seed=التهاب, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.747089` حساسية الصدر HAS_SYMPTOM سعال
- `graph_relation` `0.730487` التهاب HAS_SYMPTOM الدم
- `graph_relation` `0.707089` سعال SYMPTOM_OF حساسية الصدر
- `graph_relation` `0.690487` الدم SYMPTOM_OF التهاب
- `graph_relation` `0.577381` دوالي الخصية TREATED_BY العلاج بالجراحة
- `graph_relation` `0.537381` العلاج بالجراحة TREATS دوالي الخصية

### كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟

**Top hybrid graph relations**
- `0.968845` الجلد المترهل --TREATED_BY--> الجراحة التجميلية (seed=الجلد المترهل, relation_weight=1.0)
- `0.719397` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.496845` الجراحة التجميلية --TREATS--> الجلد المترهل (seed=الجراحة التجميلية, relation_weight=-0.2)
- `0.379397` ضغط الدم --SYMPTOM_OF--> مرض السكري (seed=ضغط الدم, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.968845` الجلد المترهل TREATED_BY الجراحة التجميلية
- `graph_relation` `0.719397` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.496845` الجراحة التجميلية TREATS الجلد المترهل
- `graph_relation` `0.379397` ضغط الدم SYMPTOM_OF مرض السكري
- `semantic_evidence` `0.774188` Evidence: كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟
Entity: الجلد المترهل
Surface form: الجلد المترهل
Field: question
Relation context: الجلد المترهل TREATED_BY الجراحة التجميلية. Evidence: يمكن شده بممارسة الرياضة أو بالجراحة التجميلية
- `semantic_qa` `0.55728` Category: الطب البديل (Alternative medicine)
Question: كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟
Answer: يمكن شده بممارسة الرياضة أو بالجراحة التجميلية.راجعي اختصاصي تجميل.
Relation context: الجلد المترهل TREATED_BY الجراحة التجميلية. Evidence: يمكن شده بممارسة الرياضة أو بالجراحة التجميلية

### السلام عليكم عمري43 اعاني ارتفاع الصفراء في الدم وصلت الي 7.6 ويوجد تضخم في الطحال والم ف اسفل البطن وجانبين الي الظهر مع احساس بالتعب تحاليل للفيروسات سلبي ومناعةانكا 1/80

**Top hybrid graph relations**
- `0.868522` تضخم --HAS_SYMPTOM--> تضخم في الارداف (seed=تضخم, relation_weight=1.0)
- `0.839675` تعب --SYMPTOM_OF--> التهاب (seed=تعب, relation_weight=1.0)
- `0.747675` التهاب --HAS_SYMPTOM--> تعب (seed=التهاب, relation_weight=1.0)
- `0.72864` التهاب --HAS_SYMPTOM--> ضيق تنفس (seed=التهاب, relation_weight=1.0)
- `0.722617` ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب (seed=ارتفاع ضغط الدم, relation_weight=1.0)
- `0.716017` ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس (seed=ارتفاع ضغط الدم, relation_weight=1.0)
- `0.696522` تضخم في الارداف --SYMPTOM_OF--> تضخم (seed=تضخم في الارداف, relation_weight=1.0)
- `0.68864` ضيق تنفس --SYMPTOM_OF--> التهاب (seed=ضيق تنفس, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.868522` تضخم HAS_SYMPTOM تضخم في الارداف
- `graph_relation` `0.839675` تعب SYMPTOM_OF التهاب
- `graph_relation` `0.747675` التهاب HAS_SYMPTOM تعب
- `graph_relation` `0.72864` التهاب HAS_SYMPTOM ضيق تنفس
- `graph_relation` `0.722617` ارتفاع ضغط الدم HAS_SYMPTOM خفقان القلب
- `graph_relation` `0.716017` ارتفاع ضغط الدم HAS_SYMPTOM ضيق تنفس

### اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج للعصب السابع بعد مضي هذه المدة الزمنه

**Top hybrid graph relations**
- `0.673929` الطعام --TREATS--> الجوع (seed=الطعام, relation_weight=0.4)
- `0.669577` شلل العصب السابع --TREATED_BY--> الكورتيزونات (seed=شلل العصب السابع, relation_weight=0.4)
- `0.653077` شلل العصب السابع --TREATED_BY--> مضادات الالتهاب (seed=شلل العصب السابع, relation_weight=0.4)
- `0.653077` شلل العصب السابع --TREATED_BY--> العلاج الطبيعي (seed=شلل العصب السابع, relation_weight=0.4)
- `0.653077` شلل العصب السابع --TREATED_BY--> مضادات الفيروسات (seed=شلل العصب السابع, relation_weight=0.4)
- `0.636577` شلل العصب السابع --TREATED_BY--> العلاج بالإبر الصينية (seed=شلل العصب السابع, relation_weight=0.4)
- `0.629577` الكورتيزونات --TREATS--> شلل العصب السابع (seed=الكورتيزونات, relation_weight=0.4)
- `0.613077` مضادات الالتهاب --TREATS--> شلل العصب السابع (seed=مضادات الالتهاب, relation_weight=0.4)

**Top context bundle**
- `graph_relation` `0.673929` الطعام TREATS الجوع
- `graph_relation` `0.669577` شلل العصب السابع TREATED_BY الكورتيزونات
- `graph_relation` `0.653077` شلل العصب السابع TREATED_BY مضادات الالتهاب
- `graph_relation` `0.653077` شلل العصب السابع TREATED_BY العلاج الطبيعي
- `graph_relation` `0.653077` شلل العصب السابع TREATED_BY مضادات الفيروسات
- `graph_relation` `0.636577` شلل العصب السابع TREATED_BY العلاج بالإبر الصينية

### تناولت مضاد حيووي زييثرون وانتج حساسيه شديده وتورم في المنطقة التناسليه وانا تعبانه جدا ما الحل ؟

**Top hybrid graph relations**
- `0.939092` حساسية --TREATED_BY--> مضاد الهيستامين (seed=حساسية, relation_weight=1.0)
- `0.939092` حساسية --TREATED_BY--> كورتيزون (seed=حساسية, relation_weight=1.0)
- `0.899021` حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين (seed=حساسية, relation_weight=1.0)
- `0.895854` حساسية --TREATED_BY--> تيليفاست (seed=حساسية, relation_weight=1.0)
- `0.869354` حساسية --TREATED_BY--> حليب مكسر بروتين الحليب (seed=حساسية, relation_weight=1.0)
- `0.869354` حساسية --TREATED_BY--> نازونكس (seed=حساسية, relation_weight=1.0)
- `0.856187` حساسية --TREATED_BY--> زيت الحبة السوداء (seed=حساسية, relation_weight=1.0)
- `0.767092` مضاد الهيستامين --TREATS--> حساسية (seed=مضاد الهيستامين, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.939092` حساسية TREATED_BY مضاد الهيستامين
- `graph_relation` `0.939092` حساسية TREATED_BY كورتيزون
- `graph_relation` `0.899021` حساسية TREATED_BY تجنب المنتجات التي تحوي جلوتين
- `graph_relation` `0.895854` حساسية TREATED_BY تيليفاست
- `graph_relation` `0.869354` حساسية TREATED_BY حليب مكسر بروتين الحليب
- `graph_relation` `0.869354` حساسية TREATED_BY نازونكس

### انا اشعر بالصداع والنعاس وحساسية في وجهي والحكة بكل انحاء جسمي كيف استطيع ان اوقف هذا الدواء

**Top hybrid graph relations**
- `0.897061` حساسية --HAS_SYMPTOM--> سعال (seed=حساسية, relation_weight=1.0)
- `0.893188` حساسية --HAS_SYMPTOM--> ضيق تنفس (seed=حساسية, relation_weight=1.0)
- `0.890461` حساسية --HAS_SYMPTOM--> بلغم (seed=حساسية, relation_weight=1.0)
- `0.885006` حساسية --HAS_SYMPTOM--> نشفان (seed=حساسية, relation_weight=1.0)
- `0.876688` حساسية --HAS_SYMPTOM--> سعال (seed=حساسية, relation_weight=1.0)
- `0.873961` حساسية --HAS_SYMPTOM--> ضيق تنفس (seed=حساسية, relation_weight=1.0)
- `0.864188` صداع --SYMPTOM_OF--> التهاب السحايا (seed=صداع, relation_weight=1.0)
- `0.847688` صداع --SYMPTOM_OF--> التهاب الجيوب الأنفية (seed=صداع, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.897061` حساسية HAS_SYMPTOM سعال
- `graph_relation` `0.893188` حساسية HAS_SYMPTOM ضيق تنفس
- `graph_relation` `0.890461` حساسية HAS_SYMPTOM بلغم
- `graph_relation` `0.885006` حساسية HAS_SYMPTOM نشفان
- `graph_relation` `0.876688` حساسية HAS_SYMPTOM سعال
- `graph_relation` `0.873961` حساسية HAS_SYMPTOM ضيق تنفس

### لا أستطبع النوم على جانبي لا الأيمن ولا الأيسر وأجد صعوبة في التنفس العميق. كما أشعر بين الفينة والأخرى بآلام قرب القلب. كما أخبركم أني مريصة بالقلب (مشكل في صمامتين)

**Top hybrid graph relations**
- `0.820601` الام --SYMPTOM_OF--> ضرس العقل (seed=الام, relation_weight=1.0)
- `0.728601` ضرس العقل --HAS_SYMPTOM--> الام (seed=ضرس العقل, relation_weight=1.0)
- `0.705978` ضرس العقل --HAS_SYMPTOM--> صداع (seed=ضرس العقل, relation_weight=1.0)
- `0.703008` فقر الدم --HAS_SYMPTOM--> الم المعدجة (seed=فقر الدم, relation_weight=1.0)
- `0.703008` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (seed=فقر الدم, relation_weight=1.0)
- `0.665978` صداع --SYMPTOM_OF--> ضرس العقل (seed=صداع, relation_weight=1.0)
- `0.663008` الم المعدجة --SYMPTOM_OF--> فقر الدم (seed=الم المعدجة, relation_weight=1.0)
- `0.663008` فقدان الشهيه --SYMPTOM_OF--> فقر الدم (seed=فقدان الشهيه, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.820601` الام SYMPTOM_OF ضرس العقل
- `graph_relation` `0.728601` ضرس العقل HAS_SYMPTOM الام
- `graph_relation` `0.705978` ضرس العقل HAS_SYMPTOM صداع
- `graph_relation` `0.703008` فقر الدم HAS_SYMPTOM الم المعدجة
- `graph_relation` `0.703008` فقر الدم HAS_SYMPTOM فقدان الشهيه
- `graph_relation` `0.665978` صداع SYMPTOM_OF ضرس العقل

### هل هناك أسباب أخرى محددة تؤدي الى ولادة دات شفة مشقوقة من غير استعمال دواء التوبيراميت.

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.56876` قرحة --TREATED_BY--> ايزومبرازول (seed=قرحة, relation_weight=0.4)
- `0.562084` شيب --TREATED_BY--> خلطة الريحان و الروزماري (seed=شيب, relation_weight=0.4)
- `0.52876` ايزومبرازول --TREATS--> قرحة (seed=ايزومبرازول, relation_weight=0.4)
- `0.522084` خلطة الريحان و الروزماري --TREATS--> شيب (seed=خلطة الريحان و الروزماري, relation_weight=0.4)

**Top context bundle**
- `graph_relation` `0.56876` قرحة TREATED_BY ايزومبرازول
- `graph_relation` `0.562084` شيب TREATED_BY خلطة الريحان و الروزماري
- `graph_relation` `0.52876` ايزومبرازول TREATS قرحة
- `graph_relation` `0.522084` خلطة الريحان و الروزماري TREATS شيب
- `semantic_evidence` `0.840062` Evidence: التي تؤدي الى ولادة دات شفة مشقوقة من غير استعمال دواء التوبيراميت
Entity: توبيراميت
Surface form: توبيراميت
Field: answer
Relation context: 
- `semantic_evidence` `0.501274` Evidence: الشفة الأرنبية تعتبر من التشوهات الخلقية الشائعة نسبيا
Entity: شفة مشقوقة
Surface form: شفة مشقوقة
Field: answer
Relation context: 

### كيف تتم ازالة شظايا القنابل الصغيرة الانشطارية في المنزل عند عدم التمكن من الذهاب للمستشفى وهل هناك اخطار من بقائها؟

**Top hybrid graph relations**
- `0.936058` شظايا القنابل الصغيرة الانشطارية --DIAGNOSED_BY--> أشعة (seed=شظايا القنابل الصغيرة الانشطارية, relation_weight=1.0)
- `0.704418` التهاب --DIAGNOSED_BY--> تحليل بول (seed=التهاب, relation_weight=1.0)
- `0.704418` التهاب --TREATED_BY--> الاكثار من شرب الماء (seed=التهاب, relation_weight=1.0)
- `0.464058` أشعة --DIAGNOSES--> شظايا القنابل الصغيرة الانشطارية (seed=أشعة, relation_weight=-0.2)
- `0.364418` تحليل بول --DIAGNOSES--> التهاب (seed=تحليل بول, relation_weight=-0.2)
- `0.364418` الاكثار من شرب الماء --TREATS--> التهاب (seed=الاكثار من شرب الماء, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.936058` شظايا القنابل الصغيرة الانشطارية DIAGNOSED_BY أشعة
- `graph_relation` `0.704418` التهاب DIAGNOSED_BY تحليل بول
- `graph_relation` `0.704418` التهاب TREATED_BY الاكثار من شرب الماء
- `graph_relation` `0.464058` أشعة DIAGNOSES شظايا القنابل الصغيرة الانشطارية
- `graph_relation` `0.364418` تحليل بول DIAGNOSES التهاب
- `graph_relation` `0.364418` الاكثار من شرب الماء TREATS التهاب

### السلام عليكم .. هل تناول ملعقة يوميا من زيت الحلبة على الريق يزيد من حجم الثدي بجانب التمارين ..؟؟ و ما المدة التى يمكن الاستمرار عليها فى تناول الزيت؟ و...

**Top hybrid graph relations**
- `0.733126` النقص الشديد للصفائح --TREATED_BY--> الروتيكسيماب (seed=النقص الشديد للصفائح, relation_weight=1.0)
- `0.393126` الروتيكسيماب --TREATS--> النقص الشديد للصفائح (seed=الروتيكسيماب, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.733126` النقص الشديد للصفائح TREATED_BY الروتيكسيماب
- `graph_relation` `0.393126` الروتيكسيماب TREATS النقص الشديد للصفائح
- `semantic_evidence` `0.795001` Evidence: هل تناول ملعقة يوميا من زيت الحلبة على الريق يزيد من حجم الثدي بجانب التمارين
Entity: زيت الحلبة
Surface form: زيت الحلبة
Field: question
Relation context: 
- `semantic_qa` `0.592548` Category: الطب البديل (Alternative medicine)
Question: السلام عليكم .. هل تناول ملعقة يوميا من زيت الحلبة على الريق يزيد من حجم الثدي بجانب التمارين ..؟؟ و ما المدة التى يمكن الاستمرار عليها فى تناول الزيت؟ و...
Answer: اشربى من الحلبة كتير اما بالنسبة لزيت الحلبة ضعي منه معلقة على صدرك وادهنى صدرك بزيت الحلبة بالليل وبزيت الزيتون الصبح، وافركي الث
- `semantic_evidence` `0.445834` Evidence: اشربى من الحلبة كتير اما بالنسبة لزيت الحلبة ضعي منه معلقة على صدرك وادهنى صدرك بزيت الحلبة بالليل وبزيت الزيتون الصبح
Entity: زيت الحلبة
Surface form: زيت الحلبة
Field: answer
Relation context: 
- `semantic_evidence` `0.355804` Evidence: فوائد زيت الحلبة للجسم: 1. فوائد زيت الحلبة للشعر: زيت الحلبة له تأثير قوي على نمو الشعر ويحد من الصلع وتساقط الشعر والقشور , فهو مصدر جيد لحمض النيكوتينيك والبروتين.
Entity: زيت الحلبة
Surface form: زيت الحلبة
Field: answer
Relation context: 

### كيفية التعامل مع انتفاخ ضرس العقل مسببا الام و احمرار الفك الاسفل

**Top hybrid graph relations**
- `0.900379` ضرس العقل --HAS_SYMPTOM--> الام (seed=ضرس العقل, relation_weight=1.0)
- `0.895379` الام --TREATED_BY--> المراجعة الطبية (seed=الام, relation_weight=1.0)
- `0.894791` ضرس العقل --HAS_SYMPTOM--> صداع (seed=ضرس العقل, relation_weight=1.0)
- `0.894791` ضرس العقل --TREATED_BY--> المراجعة الطبية (seed=ضرس العقل, relation_weight=1.0)
- `0.876041` انتفاخ --INVESTIGATED_BY--> اشعة (seed=انتفاخ, relation_weight=1.0)
- `0.732843` صداع --TREATED_BY--> المراجعة الطبية (seed=صداع, relation_weight=1.0)
- `0.717011` وجع --INVESTIGATED_BY--> اشعة (seed=وجع, relation_weight=1.0)
- `0.701365` ارتجاج دماغي --DIAGNOSED_BY--> أشعة (seed=ارتجاج دماغي, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.900379` ضرس العقل HAS_SYMPTOM الام
- `graph_relation` `0.895379` الام TREATED_BY المراجعة الطبية
- `graph_relation` `0.894791` ضرس العقل HAS_SYMPTOM صداع
- `graph_relation` `0.894791` ضرس العقل TREATED_BY المراجعة الطبية
- `graph_relation` `0.876041` انتفاخ INVESTIGATED_BY اشعة
- `graph_relation` `0.732843` صداع TREATED_BY المراجعة الطبية

### تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س

**Top hybrid graph relations**
- `0.641192` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=-0.2)
- `0.613176` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (seed=مرض السكري, relation_weight=-0.2)
- `0.604418` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=-0.2)
- `0.600547` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=-0.2)
- `0.557992` ضغط الدم --SYMPTOM_OF--> مرض السكري (seed=ضغط الدم, relation_weight=-0.2)
- `0.53903` ضغط --SYMPTOM_OF--> التهاب الجيوب الأنفية (seed=ضغط, relation_weight=-0.2)
- `0.521434` ضغط الدم --HAS_NORMAL_RANGE--> 140-80 إذا لا توجد أمراض مصاحبة (seed=ضغط الدم, relation_weight=-0.2)
- `0.521218` ضغط الدم --SYMPTOM_OF--> مرض السكري (seed=ضغط الدم, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.641192` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.613176` مرض السكري DIAGNOSED_BY تحاليل مخبرية
- `graph_relation` `0.604418` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.600547` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.557992` ضغط الدم SYMPTOM_OF مرض السكري
- `graph_relation` `0.53903` ضغط SYMPTOM_OF التهاب الجيوب الأنفية

### انا ابتلعت دبوس امس ولا اشعر ببلعه واعاني بوجع صدري كيف اعمل

**Top hybrid graph relations**
- `0.694777` فقر الدم --HAS_SYMPTOM--> تنميل (seed=فقر الدم, relation_weight=1.0)
- `0.654777` تنميل --SYMPTOM_OF--> فقر الدم (seed=تنميل, relation_weight=1.0)
- `0.613289` دبوس --DIAGNOSED_BY--> أشعة (seed=دبوس, relation_weight=-0.2)
- `0.563296` وجع --INVESTIGATED_BY--> اشعة (seed=وجع, relation_weight=-0.2)
- `0.441289` أشعة --DIAGNOSES--> دبوس (seed=أشعة, relation_weight=-0.2)
- `0.406055` انتفاخ --INVESTIGATED_BY--> اشعة (seed=انتفاخ, relation_weight=-0.2)
- `0.402786` حساسية --DIAGNOSED_BY--> RAST Test (seed=حساسية, relation_weight=-0.2)
- `0.391296` اشعة --INVESTIGATES--> وجع (seed=اشعة, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.694777` فقر الدم HAS_SYMPTOM تنميل
- `graph_relation` `0.654777` تنميل SYMPTOM_OF فقر الدم
- `graph_relation` `0.613289` دبوس DIAGNOSED_BY أشعة
- `graph_relation` `0.563296` وجع INVESTIGATED_BY اشعة
- `graph_relation` `0.441289` أشعة DIAGNOSES دبوس
- `graph_relation` `0.406055` انتفاخ INVESTIGATED_BY اشعة

### عندى بقع بنية على جانبى الوجة وانا اعانى من انيميا 10 وكان عندى حصوات بالمرارة وعملت العملية ولا زالت البقع موجودة ما العلاج الاكيد وشكرا

**Top hybrid graph relations**
- `0.776803` فقر الدم --HAS_SYMPTOM--> تنميل (seed=فقر الدم, relation_weight=1.0)
- `0.772188` فقر الدم --HAS_SYMPTOM--> الم المعدجة (seed=فقر الدم, relation_weight=1.0)
- `0.772188` فقر الدم --HAS_SYMPTOM--> الم المعدجة (seed=فقر الدم, relation_weight=1.0)
- `0.772188` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (seed=فقر الدم, relation_weight=1.0)
- `0.736966` حساسية الصدر --HAS_SYMPTOM--> سعال (seed=حساسية الصدر, relation_weight=1.0)
- `0.730606` التهاب --HAS_SYMPTOM--> الدم (seed=التهاب, relation_weight=1.0)
- `0.696966` سعال --SYMPTOM_OF--> حساسية الصدر (seed=سعال, relation_weight=1.0)
- `0.690606` الدم --SYMPTOM_OF--> التهاب (seed=الدم, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.776803` فقر الدم HAS_SYMPTOM تنميل
- `graph_relation` `0.772188` فقر الدم HAS_SYMPTOM الم المعدجة
- `graph_relation` `0.772188` فقر الدم HAS_SYMPTOM الم المعدجة
- `graph_relation` `0.772188` فقر الدم HAS_SYMPTOM فقدان الشهيه
- `graph_relation` `0.736966` حساسية الصدر HAS_SYMPTOM سعال
- `graph_relation` `0.730606` التهاب HAS_SYMPTOM الدم

### ماهو البردقوش وهل يوجد باليمن وهل يزيد من عدد الحيوانات المنويه؟

**Top hybrid graph relations**
- `0.770885` الدورة الشهرية --TREATED_BY--> البردقوش (seed=الدورة الشهرية, relation_weight=1.0)
- `0.761552` التدخين --INVESTIGATED_BY--> الحيوانات المنوية (seed=التدخين, relation_weight=1.0)
- `0.716151` الدورة الشهرية --TREATED_BY--> اكليل الجبل (seed=الدورة الشهرية, relation_weight=1.0)
- `0.716151` الدورة الشهرية --TREATED_BY--> الميرمية (seed=الدورة الشهرية, relation_weight=1.0)
- `0.716151` الدورة الشهرية --TREATED_BY--> البقدونس (seed=الدورة الشهرية, relation_weight=1.0)
- `0.716151` الدورة الشهرية --TREATED_BY--> حشيشة الملاك (seed=الدورة الشهرية, relation_weight=1.0)
- `0.716151` الدورة الشهرية --TREATED_BY--> القرفة (seed=الدورة الشهرية, relation_weight=1.0)
- `0.716151` الدورة الشهرية --TREATED_BY--> الزنجبيل (seed=الدورة الشهرية, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.770885` الدورة الشهرية TREATED_BY البردقوش
- `graph_relation` `0.761552` التدخين INVESTIGATED_BY الحيوانات المنوية
- `graph_relation` `0.716151` الدورة الشهرية TREATED_BY اكليل الجبل
- `graph_relation` `0.716151` الدورة الشهرية TREATED_BY الميرمية
- `graph_relation` `0.716151` الدورة الشهرية TREATED_BY البقدونس
- `graph_relation` `0.716151` الدورة الشهرية TREATED_BY حشيشة الملاك

### اعاني من حموضة وصعوبة في التنفس وصعوبة بلع والم في الجانب الايسر من الصدر مع تعب في الكتف اليسرى بعد ابذال مجهود فهل هذا خطر على القلب ام حموضة عادية

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.848031` تعب --SYMPTOM_OF--> التهاب (seed=تعب, relation_weight=1.0)
- `0.756031` التهاب --HAS_SYMPTOM--> تعب (seed=التهاب, relation_weight=1.0)
- `0.736531` التهاب --HAS_SYMPTOM--> ضيق تنفس (seed=التهاب, relation_weight=1.0)
- `0.696531` ضيق تنفس --SYMPTOM_OF--> التهاب (seed=ضيق تنفس, relation_weight=1.0)
- `0.583072` الكتف --TREATED_BY--> البروفين (seed=الكتف, relation_weight=-0.2)
- `0.411072` البروفين --TREATS--> الكتف (seed=البروفين, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.848031` تعب SYMPTOM_OF التهاب
- `graph_relation` `0.756031` التهاب HAS_SYMPTOM تعب
- `graph_relation` `0.736531` التهاب HAS_SYMPTOM ضيق تنفس
- `graph_relation` `0.696531` ضيق تنفس SYMPTOM_OF التهاب
- `graph_relation` `0.583072` الكتف TREATED_BY البروفين
- `graph_relation` `0.411072` البروفين TREATS الكتف

### ما هو ابسط علاج لمرض السكر بدون كيماويات؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.796243` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.791243` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.791243` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.732243` ضغط الدم --SYMPTOM_OF--> مرض السكري (seed=ضغط الدم, relation_weight=1.0)
- `0.727243` ضغط الدم --SYMPTOM_OF--> مرض السكري (seed=ضغط الدم, relation_weight=1.0)
- `0.517743` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (seed=مرض السكري, relation_weight=-0.2)
- `0.453743` تحاليل مخبرية --DIAGNOSES--> مرض السكري (seed=تحاليل مخبرية, relation_weight=-0.2)
- `0.432344` التهاب --DIAGNOSED_BY--> تحاليل مخبرية (seed=التهاب, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.796243` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.791243` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.791243` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.732243` ضغط الدم SYMPTOM_OF مرض السكري
- `graph_relation` `0.727243` ضغط الدم SYMPTOM_OF مرض السكري
- `graph_relation` `0.517743` مرض السكري DIAGNOSED_BY تحاليل مخبرية

### انا عملت جراحة فى القلب وتم تغير الصمام المترالى بصمام ميكانيكى صناعى وباخد دواء واريفان ( لسيولة الدم ) 8 ملجرام ومصاب بالانفلوانزا ماالعلاج المناسب

**Top hybrid graph relations**
- `0.4192` ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب (seed=ارتفاع ضغط الدم, relation_weight=-0.2)
- `0.4168` ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب (seed=ارتفاع ضغط الدم, relation_weight=-0.2)
- `0.4126` ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس (seed=ارتفاع ضغط الدم, relation_weight=-0.2)
- `0.4027` ارتفاع ضغط الدم --HAS_SYMPTOM--> دوخة (seed=ارتفاع ضغط الدم, relation_weight=-0.2)
- `0.398061` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=-0.2)
- `0.3792` خفقان القلب --SYMPTOM_OF--> ارتفاع ضغط الدم (seed=خفقان القلب, relation_weight=-0.2)
- `0.3768` خفقان القلب --SYMPTOM_OF--> ارتفاع ضغط الدم (seed=خفقان القلب, relation_weight=-0.2)
- `0.3726` ضيق تنفس --SYMPTOM_OF--> ارتفاع ضغط الدم (seed=ضيق تنفس, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.4192` ارتفاع ضغط الدم HAS_SYMPTOM خفقان القلب
- `graph_relation` `0.4168` ارتفاع ضغط الدم HAS_SYMPTOM خفقان القلب
- `graph_relation` `0.4126` ارتفاع ضغط الدم HAS_SYMPTOM ضيق تنفس
- `graph_relation` `0.4027` ارتفاع ضغط الدم HAS_SYMPTOM دوخة
- `graph_relation` `0.398061` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.3792` خفقان القلب SYMPTOM_OF ارتفاع ضغط الدم

### هل حبوب كريستور(rousovastatin) تؤثر على عضلة القلب ؟

**Top hybrid graph relations**
- `0.72197` فقر الدم --HAS_SYMPTOM--> الم المعدجة (seed=فقر الدم, relation_weight=1.0)
- `0.72197` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (seed=فقر الدم, relation_weight=1.0)
- `0.446546` ضغط الدم --HAS_NORMAL_RANGE--> 140-80 إذا لا توجد أمراض مصاحبة (seed=ضغط الدم, relation_weight=-0.2)
- `0.446546` نبض القلب --HAS_NORMAL_RANGE--> 65-85 تقريبا وقد يقبل أقل أو أكثر (seed=نبض القلب, relation_weight=-0.2)
- `0.38197` الم المعدجة --SYMPTOM_OF--> فقر الدم (seed=الم المعدجة, relation_weight=-0.2)
- `0.38197` فقدان الشهيه --SYMPTOM_OF--> فقر الدم (seed=فقدان الشهيه, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.72197` فقر الدم HAS_SYMPTOM الم المعدجة
- `graph_relation` `0.72197` فقر الدم HAS_SYMPTOM فقدان الشهيه
- `graph_relation` `0.446546` ضغط الدم HAS_NORMAL_RANGE 140-80 إذا لا توجد أمراض مصاحبة
- `graph_relation` `0.446546` نبض القلب HAS_NORMAL_RANGE 65-85 تقريبا وقد يقبل أقل أو أكثر
- `graph_relation` `0.38197` الم المعدجة SYMPTOM_OF فقر الدم
- `graph_relation` `0.38197` فقدان الشهيه SYMPTOM_OF فقر الدم

### هل يوجد أعشاب طبية تساعد على الشفاء من حالة الاكتئاب و الشعور بالخوف ، علما بأنه يوجد لدي فقر دم (انيميا الفول ) و يتجدث حالات الاكتئاب هذه عند تناول...

**Top hybrid graph relations**
- `0.766981` فقر الدم --DIAGNOSED_BY--> تحاليل مخبرية (seed=فقر الدم, relation_weight=1.0)
- `0.756688` فقر الدم --DIAGNOSED_BY--> تحاليل مخبرية (seed=فقر الدم, relation_weight=1.0)
- `0.756688` فقر الدم --DIAGNOSED_BY--> فحص تحاليل مخبرية (seed=فقر الدم, relation_weight=1.0)
- `0.756688` فقر الدم --HAS_SYMPTOM--> تنميل (seed=فقر الدم, relation_weight=1.0)
- `0.750481` فقر الدم --HAS_SYMPTOM--> الم المعدجة (seed=فقر الدم, relation_weight=1.0)
- `0.750481` فقر الدم --HAS_SYMPTOM--> الم المعدجة (seed=فقر الدم, relation_weight=1.0)
- `0.750481` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (seed=فقر الدم, relation_weight=1.0)
- `0.561141` فقر الدم --MANAGED_BY--> أغذية غنية بالحديد والفولات وفيتامين ب12 (seed=فقر الدم, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.766981` فقر الدم DIAGNOSED_BY تحاليل مخبرية
- `graph_relation` `0.756688` فقر الدم DIAGNOSED_BY تحاليل مخبرية
- `graph_relation` `0.756688` فقر الدم DIAGNOSED_BY فحص تحاليل مخبرية
- `graph_relation` `0.756688` فقر الدم HAS_SYMPTOM تنميل
- `graph_relation` `0.750481` فقر الدم HAS_SYMPTOM الم المعدجة
- `graph_relation` `0.750481` فقر الدم HAS_SYMPTOM الم المعدجة

### انا عندى 16 سنة وعندي ارتخاء بالصمام الميترالى والاعراض اللى عندي دوخة لما أقف و بتعب من أقل مجهود , وعند الاستيقاظ هناك ضيق بالتنفس,والدكتورظكاتبلى اندرال 20 جم بس مش...

**Top hybrid graph relations**
- `0.837456` تعب --SYMPTOM_OF--> التهاب (seed=تعب, relation_weight=1.0)
- `0.82673` دوخة --SYMPTOM_OF--> ارتفاع ضغط الدم (seed=دوخة, relation_weight=1.0)
- `0.745456` التهاب --HAS_SYMPTOM--> تعب (seed=التهاب, relation_weight=1.0)
- `0.737717` ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب (seed=ارتفاع ضغط الدم, relation_weight=1.0)
- `0.73473` ارتفاع ضغط الدم --HAS_SYMPTOM--> دوخة (seed=ارتفاع ضغط الدم, relation_weight=1.0)
- `0.731117` ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس (seed=ارتفاع ضغط الدم, relation_weight=1.0)
- `0.726481` التهاب --HAS_SYMPTOM--> ضيق تنفس (seed=التهاب, relation_weight=1.0)
- `0.697717` خفقان القلب --SYMPTOM_OF--> ارتفاع ضغط الدم (seed=خفقان القلب, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.837456` تعب SYMPTOM_OF التهاب
- `graph_relation` `0.82673` دوخة SYMPTOM_OF ارتفاع ضغط الدم
- `graph_relation` `0.745456` التهاب HAS_SYMPTOM تعب
- `graph_relation` `0.737717` ارتفاع ضغط الدم HAS_SYMPTOM خفقان القلب
- `graph_relation` `0.73473` ارتفاع ضغط الدم HAS_SYMPTOM دوخة
- `graph_relation` `0.731117` ارتفاع ضغط الدم HAS_SYMPTOM ضيق تنفس

### هل هناك اسباب للحساسية من الباراسيتمول وما الاغذية التى امتنع عنها وما هى الاغذية التى ااكلها

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.930112` حساسية --HAS_SYMPTOM--> سعال (seed=حساسية, relation_weight=1.0)
- `0.923512` حساسية --HAS_SYMPTOM--> بلغم (seed=حساسية, relation_weight=1.0)
- `0.915512` حساسية --HAS_SYMPTOM--> ضيق تنفس (seed=حساسية, relation_weight=1.0)
- `0.907512` حساسية --HAS_SYMPTOM--> نشفان (seed=حساسية, relation_weight=1.0)
- `0.903012` حساسية --HAS_SYMPTOM--> ضيق تنفس (seed=حساسية, relation_weight=1.0)
- `0.895012` حساسية --HAS_SYMPTOM--> سعال (seed=حساسية, relation_weight=1.0)
- `0.848674` حساسية الصدر --HAS_SYMPTOM--> سعال (seed=حساسية الصدر, relation_weight=1.0)
- `0.76627` ربو --HAS_SYMPTOM--> سعال (seed=ربو, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.930112` حساسية HAS_SYMPTOM سعال
- `graph_relation` `0.923512` حساسية HAS_SYMPTOM بلغم
- `graph_relation` `0.915512` حساسية HAS_SYMPTOM ضيق تنفس
- `graph_relation` `0.907512` حساسية HAS_SYMPTOM نشفان
- `graph_relation` `0.903012` حساسية HAS_SYMPTOM ضيق تنفس
- `graph_relation` `0.895012` حساسية HAS_SYMPTOM سعال

### كان لدي ارتفاع بسيط في الصفائح ٤٦١ وعندما ولدت بعد ٥٠ يوم التحليل طلع ٦٧٩ واشكو من عدم اكتمال النفس في بعض الاوقات وقال لي الطبيب لديك التهاب في الصدر...

**Top hybrid graph relations**
- `0.555791` صداع --INVESTIGATED_BY--> الصور الشعاعية (seed=صداع, relation_weight=0.4)
- `0.544342` الطبيب --TREATS--> الصدمة الكهربائية (seed=الطبيب, relation_weight=-0.2)
- `0.544342` الطبيب --TREATS--> الحروق (seed=الطبيب, relation_weight=-0.2)
- `0.515791` الصور الشعاعية --INVESTIGATES--> صداع (seed=الصور الشعاعية, relation_weight=0.4)
- `0.452342` الصدمة الكهربائية --TREATED_BY--> الطبيب (seed=الصدمة الكهربائية, relation_weight=-0.2)
- `0.452342` الحروق --TREATED_BY--> الطبيب (seed=الحروق, relation_weight=-0.2)
- `0.429021` الصداع التوتري --HAS_SYMPTOM--> صداع (seed=الصداع التوتري, relation_weight=-0.2)
- `0.389021` صداع --SYMPTOM_OF--> الصداع التوتري (seed=صداع, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.555791` صداع INVESTIGATED_BY الصور الشعاعية
- `graph_relation` `0.544342` الطبيب TREATS الصدمة الكهربائية
- `graph_relation` `0.544342` الطبيب TREATS الحروق
- `graph_relation` `0.515791` الصور الشعاعية INVESTIGATES صداع
- `graph_relation` `0.452342` الصدمة الكهربائية TREATED_BY الطبيب
- `graph_relation` `0.452342` الحروق TREATED_BY الطبيب

### عمري 18 سنة وأنا أعاني من صغر الثدي هل يوجد أي حل لتكبيره دون جراحة?

**Top hybrid graph relations**
- `0.414564` بيلة الميوغلوبين --TREATED_BY--> السوائل (seed=بيلة الميوغلوبين, relation_weight=-0.2)
- `0.41374` نقص بحجم الثدي --TREATED_BY--> مراجعة اخصائية النسائية (seed=نقص بحجم الثدي, relation_weight=-0.2)
- `0.41374` نقص بحجم الثدي --DIAGNOSED_BY--> فحص سريري (seed=نقص بحجم الثدي, relation_weight=-0.2)
- `0.412476` شيب --TREATED_BY--> خلطة الريحان و الروزماري (seed=شيب, relation_weight=-0.2)
- `0.41133` حساسية --DIAGNOSED_BY--> تحليل الحساسية (seed=حساسية, relation_weight=-0.2)
- `0.374564` السوائل --TREATS--> بيلة الميوغلوبين (seed=السوائل, relation_weight=-0.2)
- `0.37374` مراجعة اخصائية النسائية --TREATS--> نقص بحجم الثدي (seed=مراجعة اخصائية النسائية, relation_weight=-0.2)
- `0.37374` فحص سريري --DIAGNOSES--> نقص بحجم الثدي (seed=فحص سريري, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.414564` بيلة الميوغلوبين TREATED_BY السوائل
- `graph_relation` `0.41374` نقص بحجم الثدي TREATED_BY مراجعة اخصائية النسائية
- `graph_relation` `0.41374` نقص بحجم الثدي DIAGNOSED_BY فحص سريري
- `graph_relation` `0.412476` شيب TREATED_BY خلطة الريحان و الروزماري
- `graph_relation` `0.41133` حساسية DIAGNOSED_BY تحليل الحساسية
- `graph_relation` `0.374564` السوائل TREATS بيلة الميوغلوبين

### عمري ٢٥سنة واعاني من نشاط زائد في الغده الدرقية وقمت بأخذ جرعه من اليود النووي المشع وعندي طفل عمره سنه فما المده الزمنيه المحدده اللتي سأتمكن بعدها

**Top hybrid graph relations**
- `0.742883` مرض الغدة الدرقية --TREATED_BY--> التروكسين (seed=مرض الغدة الدرقية, relation_weight=1.0)
- `0.678883` التروكسين --TREATS--> مرض الغدة الدرقية (seed=التروكسين, relation_weight=1.0)
- `0.442883` مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون (seed=مرض الغدة الدرقية, relation_weight=-0.2)
- `0.439527` نشاط الغدة الدرقية --DIAGNOSED_BY--> تحاليل مخبرية (seed=نشاط الغدة الدرقية, relation_weight=-0.2)
- `0.432927` مرض جريفز --DIAGNOSED_BY--> تحاليل مخبرية (seed=مرض جريفز, relation_weight=-0.2)
- `0.399527` تحاليل مخبرية --DIAGNOSES--> نشاط الغدة الدرقية (seed=تحاليل مخبرية, relation_weight=-0.2)
- `0.392927` تحاليل مخبرية --DIAGNOSES--> مرض جريفز (seed=تحاليل مخبرية, relation_weight=-0.2)
- `0.378883` الهرمون --DIAGNOSES--> مرض الغدة الدرقية (seed=الهرمون, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.742883` مرض الغدة الدرقية TREATED_BY التروكسين
- `graph_relation` `0.678883` التروكسين TREATS مرض الغدة الدرقية
- `graph_relation` `0.442883` مرض الغدة الدرقية DIAGNOSED_BY الهرمون
- `graph_relation` `0.439527` نشاط الغدة الدرقية DIAGNOSED_BY تحاليل مخبرية
- `graph_relation` `0.432927` مرض جريفز DIAGNOSED_BY تحاليل مخبرية
- `graph_relation` `0.399527` تحاليل مخبرية DIAGNOSES نشاط الغدة الدرقية

### يشعر والدي بألم في منطقة الصدر علما ان والدي مصاب بجلطة قلبية ودماغية اليوم قد تناول بيزا وكانت دسمة،،،،،هل هذا الم قلب ام الام معدة

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.827336` الام --SYMPTOM_OF--> ضرس العقل (seed=الام, relation_weight=1.0)
- `0.735336` ضرس العقل --HAS_SYMPTOM--> الام (seed=ضرس العقل, relation_weight=1.0)
- `0.716334` ضرس العقل --HAS_SYMPTOM--> صداع (seed=ضرس العقل, relation_weight=1.0)
- `0.71147` ارتياف دعب \u0627لديم --HAS_SYMPTOM--> الالم (seed=ارتياف دعب \u0627لديم, relation_weight=1.0)
- `0.676334` صداع --SYMPTOM_OF--> ضرس العقل (seed=صداع, relation_weight=1.0)
- `0.67147` الالم --SYMPTOM_OF--> ارتياف دعب \u0627لديم (seed=الالم, relation_weight=1.0)
- `0.567336` الام --TREATED_BY--> المراجعة الطبية (seed=الام, relation_weight=-0.2)
- `0.416334` صداع --TREATED_BY--> المراجعة الطبية (seed=صداع, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.827336` الام SYMPTOM_OF ضرس العقل
- `graph_relation` `0.735336` ضرس العقل HAS_SYMPTOM الام
- `graph_relation` `0.716334` ضرس العقل HAS_SYMPTOM صداع
- `graph_relation` `0.71147` ارتياف دعب \u0627لديم HAS_SYMPTOM الالم
- `graph_relation` `0.676334` صداع SYMPTOM_OF ضرس العقل
- `graph_relation` `0.67147` الالم SYMPTOM_OF ارتياف دعب \u0627لديم

### هل يوجد تأثير على الجنين في حالة تعاطي أقراص ميزوتاك في بداية الحمل بغرض الإجهاض وأنا الآن اقتنعت باكمال الحمل ولكن قلق من تأثر الجنين بالمادة الفعالة لهذا الدواء؟

**Top hybrid graph relations**
- `0.768706` بريمولوت ن --REQUIRES_MEDICAL_SUPERVISION_FOR--> إيقاف الدواء ومراجعة الطبيب أثناء الحمل (seed=بريمولوت ن, relation_weight=1.0)
- `0.696149` الدواء --TREATS--> الملوية البوابية (seed=الدواء, relation_weight=0.4)
- `0.622442` عظام الجنين --DEVELOPS_DURING--> نهاية الأسبوع السادس تقريبا (seed=عظام الجنين, relation_weight=0.4)
- `0.620365` الحمل --HAS_SYMPTOM--> قيء (seed=الحمل, relation_weight=-0.2)
- `0.615921` الحمل --HAS_SYMPTOM--> الزراق (seed=الحمل, relation_weight=-0.2)
- `0.584988` فايروس الكبد --TREATED_BY--> اللقاح (seed=فايروس الكبد, relation_weight=0.4)
- `0.568488` فايروس الكبد --TREATED_BY--> الجرعات الثلاثه (seed=فايروس الكبد, relation_weight=0.4)
- `0.544988` اللقاح --TREATS--> فايروس الكبد (seed=اللقاح, relation_weight=0.4)

**Top context bundle**
- `graph_relation` `0.768706` بريمولوت ن REQUIRES_MEDICAL_SUPERVISION_FOR إيقاف الدواء ومراجعة الطبيب أثناء الحمل
- `graph_relation` `0.696149` الدواء TREATS الملوية البوابية
- `graph_relation` `0.622442` عظام الجنين DEVELOPS_DURING نهاية الأسبوع السادس تقريبا
- `graph_relation` `0.620365` الحمل HAS_SYMPTOM قيء
- `graph_relation` `0.615921` الحمل HAS_SYMPTOM الزراق
- `graph_relation` `0.584988` فايروس الكبد TREATED_BY اللقاح

### حموضة في فمي واحساس برائحة تفاح متعفن مع كدمات زرقاء غامقة في قدماي واحساس بغبوش في الرؤية

**Top hybrid graph relations**
- `0.703937` فقر الدم --HAS_SYMPTOM--> الم المعدجة (seed=فقر الدم, relation_weight=1.0)
- `0.703937` الم المعدجة --INVESTIGATED_BY--> فحص الجرثومة الحلزونية (seed=الم المعدجة, relation_weight=1.0)
- `0.363937` الم المعدجة --SYMPTOM_OF--> فقر الدم (seed=الم المعدجة, relation_weight=-0.2)
- `0.363937` فحص الجرثومة الحلزونية --INVESTIGATES--> الم المعدجة (seed=فحص الجرثومة الحلزونية, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.703937` فقر الدم HAS_SYMPTOM الم المعدجة
- `graph_relation` `0.703937` الم المعدجة INVESTIGATED_BY فحص الجرثومة الحلزونية
- `graph_relation` `0.363937` الم المعدجة SYMPTOM_OF فقر الدم
- `graph_relation` `0.363937` فحص الجرثومة الحلزونية INVESTIGATES الم المعدجة
- `semantic_evidence` `0.520193` Evidence: حموضة في فمي
Entity: حموضة
Surface form: حموضة
Field: question
Relation context: 
- `semantic_qa` `0.464656` Category: أمراض باطنية (Esoteric)
Question: حموضة في فمي واحساس برائحة تفاح متعفن مع كدمات زرقاء غامقة في قدماي واحساس بغبوش في الرؤية
Answer: كشف سريري وعمل الفحوصات الاتية صورة دم لعدد الصفائح الدموية وكرات الدم البيضاء والحمراء تحليل سكر صايم وبعد الاكل بساعتين وتراكمي واستون بالدم تحليل وظائف كلي وال eGFR تحليل بول وبراز.. اشعة بالموجات ف الصوت

### قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة

**Top hybrid graph relations**
- `0.881606` وجع --INVESTIGATED_BY--> اشعة (seed=وجع, relation_weight=1.0)
- `0.877856` انتفاخ --INVESTIGATED_BY--> اشعة (seed=انتفاخ, relation_weight=1.0)
- `0.841606` اشعة --INVESTIGATES--> وجع (seed=أشعة, relation_weight=1.0)
- `0.837856` اشعة --INVESTIGATES--> انتفاخ (seed=أشعة, relation_weight=1.0)
- `0.780703` أشعة --DIAGNOSES--> تسوس الأسنان (seed=أشعة, relation_weight=1.0)
- `0.776953` اشعة --DIAGNOSES--> التهاب (seed=أشعة, relation_weight=1.0)
- `0.776953` أشعة --DIAGNOSES--> انزلاق غضروفي عنقي (seed=أشعة, relation_weight=1.0)
- `0.776953` أشعة --DIAGNOSES--> ارتجاج دماغي (seed=أشعة, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.881606` وجع INVESTIGATED_BY اشعة
- `graph_relation` `0.877856` انتفاخ INVESTIGATED_BY اشعة
- `graph_relation` `0.841606` اشعة INVESTIGATES وجع
- `graph_relation` `0.837856` اشعة INVESTIGATES انتفاخ
- `graph_relation` `0.780703` أشعة DIAGNOSES تسوس الأسنان
- `graph_relation` `0.776953` اشعة DIAGNOSES التهاب

### ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.75576` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.75576` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.75223` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.69176` ضغط الدم --SYMPTOM_OF--> مرض السكري (seed=ضغط الدم, relation_weight=1.0)
- `0.68823` ضغط الدم --SYMPTOM_OF--> مرض السكري (seed=ضغط الدم, relation_weight=1.0)
- `0.524039` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (seed=مرض السكري, relation_weight=-0.2)
- `0.480009` التهاب --DIAGNOSED_BY--> تحاليل مخبرية (seed=التهاب, relation_weight=-0.2)
- `0.460039` تحاليل مخبرية --DIAGNOSES--> مرض السكري (seed=تحاليل مخبرية, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.75576` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.75576` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.75223` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.69176` ضغط الدم SYMPTOM_OF مرض السكري
- `graph_relation` `0.68823` ضغط الدم SYMPTOM_OF مرض السكري
- `graph_relation` `0.524039` مرض السكري DIAGNOSED_BY تحاليل مخبرية

### أعاني من حرقان بكامل بجسمي والتهاب المسالك البوليه وارتفاع الكلسترول والدهون الثلاثيه مال الحل جزاكم الله خير وما قد يكون المسبب

**Top hybrid graph relations**
- `0.715003` الصداع التوتري --HAS_SYMPTOM--> صداع (seed=الصداع التوتري, relation_weight=1.0)
- `0.675003` صداع --SYMPTOM_OF--> الصداع التوتري (seed=صداع, relation_weight=1.0)
- `0.413863` ارتفاع ضغط الدم --TREATED_BY--> العقاقير (seed=ارتفاع ضغط الدم, relation_weight=-0.2)
- `0.373863` العقاقير --TREATS--> ارتفاع ضغط الدم (seed=العقاقير, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.715003` الصداع التوتري HAS_SYMPTOM صداع
- `graph_relation` `0.675003` صداع SYMPTOM_OF الصداع التوتري
- `graph_relation` `0.413863` ارتفاع ضغط الدم TREATED_BY العقاقير
- `graph_relation` `0.373863` العقاقير TREATS ارتفاع ضغط الدم
- `semantic_qa` `0.535379` Category: جراحة القلب والشرايين (Cardiovascular surgery)
Question: أعاني من حرقان بكامل بجسمي والتهاب المسالك البوليه وارتفاع الكلسترول والدهون الثلاثيه مال الحل جزاكم الله خير وما قد يكون المسبب
Answer: لا نعرف تاريخك الصحي، مع ذلك ننصح بمعاودة طبيك لاستكمال التشخيص ووضع خطة علاجية تتناسب مع حالتك، لأن علاج ارتفاع الكوليستيرول والدهنيات يشمل أدوية
- `semantic_evidence` `0.4821` Evidence: ارتفاع الكلسترول والدهون الثلاثيه
Entity: ارتفاع الكلسترول
Surface form: ارتفاع الكلسترول والدهون الثلاثيه
Field: question
Relation context: 

### ماهي علاجات حمى التهاب باطن القدم وباطن اليد وماهي الفحوصات للتاكد من اسباب هذا المرض؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.843952` حمى --SYMPTOM_OF--> حمى عضة الجرذ (seed=حمى, relation_weight=1.0)
- `0.843952` حمى --SYMPTOM_OF--> حمى عضة الفأر (seed=حمى, relation_weight=1.0)
- `0.843952` حمى --SYMPTOM_OF--> حمى عضة الجرذون (seed=حمى, relation_weight=1.0)
- `0.751952` حمى عضة الجرذ --HAS_SYMPTOM--> حمى (seed=حمى عضة الجرذ, relation_weight=1.0)
- `0.751952` حمى عضة الفأر --HAS_SYMPTOM--> حمى (seed=حمى عضة الفأر, relation_weight=1.0)
- `0.751952` حمى عضة الجرذون --HAS_SYMPTOM--> حمى (seed=حمى عضة الجرذون, relation_weight=1.0)
- `0.720429` حمى عضة الجرذ --HAS_SYMPTOM--> ارتجاف (seed=حمى عضة الجرذ, relation_weight=1.0)
- `0.720429` حمى عضة الجرذ --HAS_SYMPTOM--> أوجاع العضلات (seed=حمى عضة الجرذ, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.843952` حمى SYMPTOM_OF حمى عضة الجرذ
- `graph_relation` `0.843952` حمى SYMPTOM_OF حمى عضة الفأر
- `graph_relation` `0.843952` حمى SYMPTOM_OF حمى عضة الجرذون
- `graph_relation` `0.751952` حمى عضة الجرذ HAS_SYMPTOM حمى
- `graph_relation` `0.751952` حمى عضة الفأر HAS_SYMPTOM حمى
- `graph_relation` `0.751952` حمى عضة الجرذون HAS_SYMPTOM حمى

### والدي وقع من الدرج قبل ثلالث ايام نلاحظ هناك زغللة في عينه اليمنى مع حول فيها تم قياسة مستوى السكر اليوم 200 اتمنى افادتي بهذا الامر هل له علاقة بالحلطة...

**Top hybrid graph relations**
- `0.766491` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (seed=مرض السكري, relation_weight=1.0)
- `0.753627` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.753627` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.751809` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=1.0)
- `0.709118` التهاب --DIAGNOSED_BY--> تحاليل مخبرية (seed=التهاب, relation_weight=1.0)
- `0.402491` تحاليل مخبرية --DIAGNOSES--> مرض السكري (seed=تحاليل مخبرية, relation_weight=-0.2)
- `0.389627` ضغط الدم --SYMPTOM_OF--> مرض السكري (seed=ضغط الدم, relation_weight=-0.2)
- `0.369118` تحاليل مخبرية --DIAGNOSES--> التهاب (seed=تحاليل مخبرية, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.766491` مرض السكري DIAGNOSED_BY تحاليل مخبرية
- `graph_relation` `0.753627` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.753627` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.751809` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.709118` التهاب DIAGNOSED_BY تحاليل مخبرية
- `graph_relation` `0.402491` تحاليل مخبرية DIAGNOSES مرض السكري

### ماهي الاهمية الطبية للجلوكوز والفركتوز والجالكتوز؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.766242` التهاب --HAS_SYMPTOM--> اختلال وظائف الكبد (seed=التهاب, relation_weight=1.0)
- `0.726242` اختلال وظائف الكبد --SYMPTOM_OF--> التهاب (seed=اختلال وظائف الكبد, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.766242` التهاب HAS_SYMPTOM اختلال وظائف الكبد
- `graph_relation` `0.726242` اختلال وظائف الكبد SYMPTOM_OF التهاب
- `semantic_evidence` `0.427186` Evidence: الجلوكوز ويسمى ايضا سكر العنب اوسكر الذرة
Entity: الفركتوز
Surface form: سكر الذرة
Field: answer
Relation context: التهاب HAS_SYMPTOM اختلال وظائف الكبد. Evidence: التهاب في العين وفقدان حاسة الشم واختلال وظائف الكبد والكلى
- `semantic_evidence` `0.392447` Evidence: الجلاكتوز هو نوع من انواع السكر يدخل في تركيب الكثير من البروتينات والدهون في الخلايا
Entity: الجالكتوز
Surface form: الجالكتوز
Field: answer
Relation context: التهاب HAS_SYMPTOM اختلال وظائف الكبد. Evidence: التهاب في العين وفقدان حاسة الشم واختلال وظائف الكبد والكلى
- `semantic_evidence` `0.39147` Evidence: الجلوكوز ويسمى ايضا سكر العنب اوسكر الذرة
Entity: الجلوكوز
Surface form: سكر العنب
Field: answer
Relation context: التهاب HAS_SYMPTOM اختلال وظائف الكبد. Evidence: التهاب في العين وفقدان حاسة الشم واختلال وظائف الكبد والكلى
- `semantic_evidence` `0.385545` Evidence: الفركتوز هو نوع اخر من السكر يكون مكونا لجدار الخلايا
Entity: الفركتوز
Surface form: الفركتوز
Field: answer
Relation context: التهاب HAS_SYMPTOM اختلال وظائف الكبد. Evidence: التهاب في العين وفقدان حاسة الشم واختلال وظائف الكبد والكلى

### متى يلجأ الدكتور الي نزع عَصّب السن او الضرس

**Top hybrid graph relations**
- `0.4677` حشو الأسنان --NOT_ASSOCIATED_WITH--> غمازة الوجه (seed=حشو الأسنان, relation_weight=-0.2)
- `0.4677` تخدير موضعي قوي --MAY_TEMPORARILY_AFFECT--> غمازة الوجه (seed=تخدير موضعي قوي, relation_weight=-0.2)
- `0.4617` برد الأسنان --HAS_RISK--> حساسية الأسنان (seed=برد الأسنان, relation_weight=-0.2)
- `0.4617` برد الأسنان --PROCEDURE_DURATION--> جلسة واحدة أو جلستان (seed=برد الأسنان, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.4677` حشو الأسنان NOT_ASSOCIATED_WITH غمازة الوجه
- `graph_relation` `0.4677` تخدير موضعي قوي MAY_TEMPORARILY_AFFECT غمازة الوجه
- `graph_relation` `0.4617` برد الأسنان HAS_RISK حساسية الأسنان
- `graph_relation` `0.4617` برد الأسنان PROCEDURE_DURATION جلسة واحدة أو جلستان
- `semantic_qa` `0.44329` Category: أمراض الأسنان (Dental)
Question: متى يلجأ الدكتور الي نزع عَصّب السن او الضرس
Answer: عندما يشتكى المريض من الاحساس بالساخن والبارد وعلامات متقدمة لتسوس الاسنان او كسر بالسن يصل لمنطقة عصب السن او الضرس
Relation context: 
- `semantic_evidence` `0.349333` Evidence: الضرس
Entity: الضرس
Surface form: الضرس
Field: question
Relation context: 

### سلام لقد اجريت فحص الهرمون B-HCG ،و نتائج التحاليل كما يللي 3-4 اسبوع 9-130 4-5 اسبوع 75-2600 5-6 اسبوع 850-20800 7-8 اسبوع 4000-100200 7-12 اسبوع 11500-289000 12-16 اسبوع 18300-137000 و...

**Top hybrid graph relations**
- `0.668497` الهرمون --DIAGNOSES--> مرض الغدة الدرقية (seed=الهرمون, relation_weight=0.4)
- `0.597505` صعوبة التنفس والإرهاق --INVESTIGATED_BY--> التاريخ المرضي والفحص السريري (seed=صعوبة التنفس والإرهاق, relation_weight=0.4)
- `0.576497` مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون (seed=مرض الغدة الدرقية, relation_weight=0.4)
- `0.561339` نقص الصفيحات --DIAGNOSED_BY--> فحص نخاع العظم (seed=نقص الصفيحات, relation_weight=0.4)
- `0.521339` فحص نخاع العظم --DIAGNOSES--> نقص الصفيحات (seed=فحص نخاع العظم, relation_weight=0.4)
- `0.447505` صعوبة التنفس والإرهاق --MAY_BE_ASSOCIATED_WITH--> التهاب تنفسي أو فقر دم أو اضطراب دموي أو دوراني (seed=صعوبة التنفس والإرهاق, relation_weight=-0.2)
- `0.40574` مرض الغدة الدرقية --TREATED_BY--> التروكسين (seed=مرض الغدة الدرقية, relation_weight=-0.2)
- `0.36574` التروكسين --TREATS--> مرض الغدة الدرقية (seed=التروكسين, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.668497` الهرمون DIAGNOSES مرض الغدة الدرقية
- `graph_relation` `0.597505` صعوبة التنفس والإرهاق INVESTIGATED_BY التاريخ المرضي والفحص السريري
- `graph_relation` `0.576497` مرض الغدة الدرقية DIAGNOSED_BY الهرمون
- `graph_relation` `0.561339` نقص الصفيحات DIAGNOSED_BY فحص نخاع العظم
- `graph_relation` `0.521339` فحص نخاع العظم DIAGNOSES نقص الصفيحات
- `graph_relation` `0.447505` صعوبة التنفس والإرهاق MAY_BE_ASSOCIATED_WITH التهاب تنفسي أو فقر دم أو اضطراب دموي أو دوراني

### لسلام عليكم ممكن تساعدوني ابني عملتله تطعيم سنة ونص اليوم هو يعاني من ارتفاع الحرارة ومايقدر يحرك رجلو وحتى يوقف وهو كتير البكاء كيف اتعامل معاه كيف اخفف من الم...

**Top hybrid graph relations**
- `0.503056` حمى --TREATED_BY--> خافض حراره (seed=حمى, relation_weight=-0.2)
- `0.463056` خافض حراره --TREATS--> حمى (seed=خافض حراره, relation_weight=-0.2)
- `0.448103` حصى الكلى --TREATED_BY--> الإكثار من السوائل والتقييم الطبي (seed=حصى الكلى, relation_weight=-0.2)
- `0.419235` النقص الشديد للصفائح --TREATED_BY--> الروتيكسيماب (seed=النقص الشديد للصفائح, relation_weight=-0.2)
- `0.379235` الروتيكسيماب --TREATS--> النقص الشديد للصفائح (seed=الروتيكسيماب, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.503056` حمى TREATED_BY خافض حراره
- `graph_relation` `0.463056` خافض حراره TREATS حمى
- `graph_relation` `0.448103` حصى الكلى TREATED_BY الإكثار من السوائل والتقييم الطبي
- `graph_relation` `0.419235` النقص الشديد للصفائح TREATED_BY الروتيكسيماب
- `graph_relation` `0.379235` الروتيكسيماب TREATS النقص الشديد للصفائح
- `semantic_qa` `0.657964` Category: صحة الطفل (Child health)
Question: لسلام عليكم ممكن تساعدوني ابني عملتله تطعيم سنة ونص اليوم هو يعاني من ارتفاع الحرارة ومايقدر يحرك رجلو وحتى يوقف وهو كتير البكاء كيف اتعامل معاه كيف اخفف من الم...
Answer: من الطبيعي ان يصاحب هذا المطعوم حراره والم في مكان المطعوم والمفروض ان تزول هذه الاعراض خلال 48 ساعة وعليكي استخدام خافض حراره ومسكن 

### هل زيت نبات الميرمية له آثار جانبية عند تناوله بشكل 3 كبسولات قبل الطعام للتخلص من افراز البرولاكتين المفرز والناتج عن ورم حميد في الغدة النخامية . .

**Top hybrid graph relations**
- `0.578293` الميرمية --TREATS--> الدورة الشهرية (seed=الميرمية, relation_weight=-0.2)
- `0.524093` الطعام --TREATS--> الجوع (seed=الطعام, relation_weight=-0.2)
- `0.486293` الدورة الشهرية --TREATED_BY--> الميرمية (seed=الدورة الشهرية, relation_weight=-0.2)
- `0.44403` مرض الغدة الدرقية --TREATED_BY--> التروكسين (seed=مرض الغدة الدرقية, relation_weight=-0.2)
- `0.44403` مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون (seed=مرض الغدة الدرقية, relation_weight=-0.2)
- `0.432093` الجوع --TREATED_BY--> الطعام (seed=الجوع, relation_weight=-0.2)
- `0.40849` الدورة الشهرية --TREATED_BY--> اكليل الجبل (seed=الدورة الشهرية, relation_weight=-0.2)
- `0.40849` الدورة الشهرية --TREATED_BY--> البقدونس (seed=الدورة الشهرية, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.578293` الميرمية TREATS الدورة الشهرية
- `graph_relation` `0.524093` الطعام TREATS الجوع
- `graph_relation` `0.486293` الدورة الشهرية TREATED_BY الميرمية
- `graph_relation` `0.44403` مرض الغدة الدرقية TREATED_BY التروكسين
- `graph_relation` `0.44403` مرض الغدة الدرقية DIAGNOSED_BY الهرمون
- `graph_relation` `0.432093` الجوع TREATED_BY الطعام

### عندي الم في منطقه البطن مع الم بصدر جهه اليمين الى الرقبه وماقدرت اعرف تفسير الالم ذا من ايش او سببه مع وجود احيان ضيق بالتنفس ،،،، افيدوني

**Top hybrid graph relations**
- `0.831245` الالم --SYMPTOM_OF--> ارتياف دعب \u0627لديم (seed=الالم, relation_weight=1.0)
- `0.739245` ارتياف دعب \u0627لديم --HAS_SYMPTOM--> الالم (seed=ارتياف دعب \u0627لديم, relation_weight=1.0)
- `0.709963` فقر الدم --HAS_SYMPTOM--> الم المعدجة (seed=فقر الدم, relation_weight=1.0)
- `0.669963` الم المعدجة --SYMPTOM_OF--> فقر الدم (seed=الم المعدجة, relation_weight=1.0)
- `0.430755` الجلد المترهل --TREATED_BY--> الجراحة التجميلية (seed=الجلد المترهل, relation_weight=-0.2)
- `0.409963` الم المعدجة --INVESTIGATED_BY--> فحص الجرثومة الحلزونية (seed=الم المعدجة, relation_weight=-0.2)
- `0.390755` الجراحة التجميلية --TREATS--> الجلد المترهل (seed=الجراحة التجميلية, relation_weight=-0.2)
- `0.369963` فحص الجرثومة الحلزونية --INVESTIGATES--> الم المعدجة (seed=فحص الجرثومة الحلزونية, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.831245` الالم SYMPTOM_OF ارتياف دعب \u0627لديم
- `graph_relation` `0.739245` ارتياف دعب \u0627لديم HAS_SYMPTOM الالم
- `graph_relation` `0.709963` فقر الدم HAS_SYMPTOM الم المعدجة
- `graph_relation` `0.669963` الم المعدجة SYMPTOM_OF فقر الدم
- `graph_relation` `0.430755` الجلد المترهل TREATED_BY الجراحة التجميلية
- `graph_relation` `0.409963` الم المعدجة INVESTIGATED_BY فحص الجرثومة الحلزونية

## Output Files

- Hybrid retrieval JSON: `outputs/05_trial_graph_v1/hybrid_retrieval/trial_graph_v1_hybrid_retrieval_results.json`
- Hybrid relations CSV: `outputs/05_trial_graph_v1/hybrid_retrieval/trial_graph_v1_hybrid_retrieval_relations.csv`
- Hybrid contexts CSV: `outputs/05_trial_graph_v1/hybrid_retrieval/trial_graph_v1_hybrid_retrieval_contexts.csv`
- Hybrid metrics JSON: `outputs/05_trial_graph_v1/hybrid_retrieval/trial_graph_v1_hybrid_retrieval_metrics.json`
- Hybrid metrics CSV: `outputs/05_trial_graph_v1/hybrid_retrieval/trial_graph_v1_hybrid_retrieval_metrics.csv`

## Next Step From Mix.png

Continue to Step 10: subgraph reranking, using these hybrid relation/context candidates.
