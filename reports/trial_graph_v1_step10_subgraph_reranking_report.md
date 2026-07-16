# Trial Graph v1 Step 10 Subgraph Reranking Report

This step reranks the Step 9C hybrid retrieval output into compact evidence-aware subgraphs.
It does not generate answers yet. It prepares cleaner graph/evidence units for Step 11 context construction.

## Reranking Signals

- Best hybrid retrieval score from Step 9C
- Mean score across repeated evidence rows for the same edge
- Evidence count bonus, capped at 3 evidence rows
- Direct/original edge support bonus
- Primary intent relation match from Step 8

## Query Results

### ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟ هل امتنع عن طعام معين يزيد البلغم وانا غير مدخن واخذ علاج للضغط والكوليسترول عمرى 55...

- `0.853633` حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين (matches primary intent; has original/direct edge support; strong semantic support)
- `0.845599` حساسية --TREATED_BY--> مضاد الهيستامين (matches primary intent; has original/direct edge support; strong semantic support)
- `0.845599` حساسية --TREATED_BY--> كورتيزون (matches primary intent; has original/direct edge support; strong semantic support)
- `0.838022` حساسية --TREATED_BY--> تيليفاست (matches primary intent; has original/direct edge support; strong semantic support)
- `0.83746` ارتفاع الكوليسترول --MANAGED_BY--> تقليل الدهون والرياضة (matches primary intent; has original/direct edge support)
- `0.829987` حساسية --TREATED_BY--> حليب مكسر بروتين الحليب (matches primary intent; has original/direct edge support; strong semantic support)
- `0.82953` حساسية --TREATED_BY--> زيت الحبة السوداء (matches primary intent; has original/direct edge support; strong semantic support)
- `0.827462` حساسية --TREATED_BY--> نازونكس (matches primary intent; has original/direct edge support; strong semantic support)

### كيف اعالج علامات الشيخوخة المبكرة بالوجه؟

- `0.755988` تضيق القنوات الموجودة داخل الكبد --TREATED_BY--> منظار قنوات مرارية الف سلامة (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.670388` منظار قنوات مرارية الف سلامة --TREATS--> تضيق القنوات الموجودة داخل الكبد (matches primary intent; evidence overlaps query terms)
- `0.379826` حساسية --DIAGNOSED_BY--> تحاليل مخبرية (has original/direct edge support)
- `0.379631` انتفاخ --INVESTIGATED_BY--> اشعة (has original/direct edge support)
- `0.379458` وجع --INVESTIGATED_BY--> اشعة (has original/direct edge support)
- `0.294226` تحاليل مخبرية --DIAGNOSES--> حساسية (kept as lower-priority supporting graph edge)
- `0.294031` اشعة --INVESTIGATES--> انتفاخ (kept as lower-priority supporting graph edge)
- `0.293858` اشعة --INVESTIGATES--> وجع (kept as lower-priority supporting graph edge)

### ماالعلاج الاسعافي لأنخفاض السكر مع فقدان الوعي

- `0.920872` مرض السكري --HAS_SYMPTOM--> ضغط الدم (matches primary intent; 3 evidence rows; has original/direct edge support; evidence overlaps query terms; 3 distinct QA sources)
- `0.919639` فقدان الوعي --TREATED_BY--> عسل (matches primary intent; has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.803312` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.759701` التهاب --DIAGNOSED_BY--> تحاليل مخبرية (matches primary intent; has original/direct edge support)
- `0.387559` عسل --TREATS--> فقدان الوعي (strong semantic support; evidence overlaps query terms)
- `0.340352` تحاليل مخبرية --DIAGNOSES--> مرض السكري (evidence overlaps query terms)
- `0.338632` ضغط الدم --SYMPTOM_OF--> مرض السكري (evidence overlaps query terms)
- `0.312101` تحاليل مخبرية --DIAGNOSES--> التهاب (kept as lower-priority supporting graph edge)

### هل الاشعة المقطعيه بالصبغه للقلب تسبب انتفاخ اسفل الوجه او انتفاخ الغده هل هو طبيعي

- `0.863471` انتفاخ --INVESTIGATED_BY--> اشعة (matches primary intent; has original/direct edge support)
- `0.78026` مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.777871` اشعة --INVESTIGATES--> انتفاخ (matches primary intent)
- `0.777748` أشعة --DIAGNOSES--> تسوس الأسنان (matches primary intent; evidence overlaps query terms)
- `0.773343` وجع --INVESTIGATED_BY--> اشعة (matches primary intent; has original/direct edge support)
- `0.773343` التهاب --DIAGNOSED_BY--> اشعة (matches primary intent; has original/direct edge support)
- `0.772223` اشعة --INVESTIGATES--> وجع (matches primary intent)
- `0.772223` اشعة --DIAGNOSES--> التهاب (matches primary intent)

### السلام عليكم..ماهو العلاج المناسب لتقليل نسبة الاملاح في الدم النسبة الحالية عندي هي (7.9) عمري 44 سنة /ذكر؟

- `0.532286` حساسية الصدر --HAS_SYMPTOM--> سعال (has original/direct edge support)
- `0.53072` التهاب --HAS_SYMPTOM--> الدم (has original/direct edge support)
- `0.446686` سعال --SYMPTOM_OF--> حساسية الصدر (kept as lower-priority supporting graph edge)
- `0.44512` الدم --SYMPTOM_OF--> التهاب (kept as lower-priority supporting graph edge)
- `0.402496` التهاب --DIAGNOSED_BY--> تصوير الجهاز البولي (has original/direct edge support)
- `0.400384` الدم --INVESTIGATED_BY--> تصوير الجهاز البولي (has original/direct edge support)
- `0.399838` حساسية الصدر --DIAGNOSED_BY--> تحليل الحساسية (has original/direct edge support)
- `0.316896` تصوير الجهاز البولي --DIAGNOSES--> التهاب (kept as lower-priority supporting graph edge)

### السلام عليكم أنا أشعر ببرودة رأسي -وغذا اصبح ملمس رأسي بارد جاني صداع لايزول بالمسكنات- ذهبت لأفضل أخصائي أنف وأذن وحنجرة قال هذا المرض ماله علاج !! ماهي التحاليل الأزمة...

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.787398` التهاب السحايا --HAS_SYMPTOM--> صداع (matches primary intent; has original/direct edge support)
- `0.786278` صداع --SYMPTOM_OF--> التهاب السحايا (matches primary intent)
- `0.776838` التهاب الجيوب الأنفية --HAS_SYMPTOM--> صداع (matches primary intent; has original/direct edge support)
- `0.775718` صداع --SYMPTOM_OF--> التهاب الجيوب الأنفية (matches primary intent)
- `0.766573` صداع --SYMPTOM_OF--> الصداع التوتري (matches primary intent)
- `0.760182` ضرس العقل --HAS_SYMPTOM--> صداع (matches primary intent; has original/direct edge support)
- `0.759583` التهاب الجيوب الأنفية --HAS_SYMPTOM--> ضغط (matches primary intent; has original/direct edge support)
- `0.759062` صداع --SYMPTOM_OF--> ضرس العقل (matches primary intent)

### مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد المستشفی

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.567512` قرحة --TREATED_BY--> ايزومبرازول (has original/direct edge support; evidence overlaps query terms)
- `0.407368` الملوية البوابية --TREATED_BY--> الدواء (has original/direct edge support)
- `0.397432` ايزومبرازول --TREATS--> قرحة (evidence overlaps query terms)
- `0.321768` الدواء --TREATS--> الملوية البوابية (kept as lower-priority supporting graph edge)

### ما البديل لعمل كراون للضرس في حال كان طول الضرس قصير بسبب كسر وتآكل في السطح بعد حشو عصب مع حجم طبيعي للضرس ،حتى يعود يصبح في طول يسمح بتركيب...

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.421826` حشو الأسنان --NOT_ASSOCIATED_WITH--> غمازة الوجه (has original/direct edge support)
- `0.421826` تخدير موضعي قوي --MAY_TEMPORARILY_AFFECT--> غمازة الوجه (has original/direct edge support)
- `0.415278` برد الأسنان --HAS_RISK--> حساسية الأسنان (has original/direct edge support)
- `0.415278` برد الأسنان --PROCEDURE_DURATION--> جلسة واحدة أو جلستان (has original/direct edge support)
- `0.38401` بروز في البطن --TREATED_BY--> تمارين رياضية (has original/direct edge support)
- `0.29841` تمارين رياضية --TREATS--> بروز في البطن (kept as lower-priority supporting graph edge)

### زوجتي حامل ومنذ بداية حملها لم اتوقف عن الاتصال معهاابدا ..فهل ذلك له علاقه لما تشعر به من حرقه في المهبل...وهل ذلك له تأثير على الجنين....

- `0.496355` التهاب --HAS_SYMPTOM--> حرقه (has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.495235` حرقه --SYMPTOM_OF--> التهاب (strong semantic support; evidence overlaps query terms)

### لمدا كلما انزعجت من شخص ما أشعر بدوار ودقات سريعة للقلب وشعور براسي تقيل تم يغمى علي دون الغياب عن الوعي فما تشخيصكم لهدا وشكراً جزيل

- `0.402766` فقر الدم --MANAGED_BY--> أغذية غنية بالحديد والفولات وفيتامين ب12 (has original/direct edge support)
- `0.402766` أغذية غنية بالحديد والفولات وفيتامين ب12 --ABSORPTION_IMPROVED_BY--> أطعمة غنية بفيتامين ج (has original/direct edge support)
- `0.402766` أغذية غنية بالحديد والفولات وفيتامين ب12 --ABSORPTION_REDUCED_BY--> الشاي والقهوة والكالسيوم مع الحديد (has original/direct edge support)
- `0.377644` سيلان الانف --TREATED_BY--> بخاخات الماء والملح (has original/direct edge support)
- `0.377644` سيلان الانف --INVESTIGATED_BY--> خصائي الاطفال (has original/direct edge support)
- `0.292044` بخاخات الماء والملح --TREATS--> سيلان الانف (kept as lower-priority supporting graph edge)
- `0.292044` خصائي الاطفال --INVESTIGATES--> سيلان الانف (kept as lower-priority supporting graph edge)

### عندي فقر دم وعملت التحاليل عندي نقص فيتامين دال ونقص حديد وصف لي الدكتور 20 ابرة حديد لمدة شهر هل اخذ هالكمية بهذه المدة آمن أم مضر للجسم ؟ وما...

- `0.86682` فقر الدم --HAS_SYMPTOM--> الم المعدجة (matches primary intent; 2 evidence rows; has original/direct edge support; 2 distinct QA sources)
- `0.816292` فقر الدم --HAS_SYMPTOM--> تنميل (matches primary intent; has original/direct edge support)
- `0.80682` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (matches primary intent; has original/direct edge support)
- `0.763` نقص هرمونات --HAS_SYMPTOM--> انقطاع الطمث (matches primary intent; has original/direct edge support)
- `0.695822` نقص حديد --DIAGNOSED_BY--> فحص تحاليل مخبرية (has original/direct edge support; evidence overlaps query terms)
- `0.6774` انقطاع الطمث --SYMPTOM_OF--> نقص هرمونات (matches primary intent)
- `0.672782` فقر الدم --DIAGNOSED_BY--> فحص تحاليل مخبرية (has original/direct edge support; evidence overlaps query terms)
- `0.669252` تنميل --SYMPTOM_OF--> فقر الدم (matches primary intent)

### أود معرفة ما أسباب تدلي المستقيم؟وطرق العلاج؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.773137` حساسية الصدر --HAS_SYMPTOM--> سعال (matches primary intent; has original/direct edge support)
- `0.757512` التهاب --HAS_SYMPTOM--> الدم (matches primary intent; has original/direct edge support)
- `0.687537` سعال --SYMPTOM_OF--> حساسية الصدر (matches primary intent)
- `0.671912` الدم --SYMPTOM_OF--> التهاب (matches primary intent)
- `0.527524` دوالي الخصية --TREATED_BY--> العلاج بالجراحة (has original/direct edge support)
- `0.441924` العلاج بالجراحة --TREATS--> دوالي الخصية (kept as lower-priority supporting graph edge)
- `0.402689` حساسية الصدر --DIAGNOSED_BY--> تحليل الحساسية (has original/direct edge support)
- `0.391288` التهاب --DIAGNOSED_BY--> تصوير الجهاز البولي (has original/direct edge support)

### كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟

- `0.956489` الجلد المترهل --TREATED_BY--> الجراحة التجميلية (matches primary intent; has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.7647` مرض السكري --HAS_SYMPTOM--> ضغط الدم (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.424409` الجراحة التجميلية --TREATS--> الجلد المترهل (strong semantic support; evidence overlaps query terms)
- `0.3171` ضغط الدم --SYMPTOM_OF--> مرض السكري (evidence overlaps query terms)

### السلام عليكم عمري43 اعاني ارتفاع الصفراء في الدم وصلت الي 7.6 ويوجد تضخم في الطحال والم ف اسفل البطن وجانبين الي الظهر مع احساس بالتعب تحاليل للفيروسات سلبي ومناعةانكا 1/80

- `0.850693` تضخم --HAS_SYMPTOM--> تضخم في الارداف (matches primary intent; has original/direct edge support)
- `0.774964` التهاب --HAS_SYMPTOM--> تعب (matches primary intent; has original/direct edge support)
- `0.773844` تعب --SYMPTOM_OF--> التهاب (matches primary intent)
- `0.762152` ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب (matches primary intent; has original/direct edge support)
- `0.761168` التهاب --HAS_SYMPTOM--> ضيق تنفس (matches primary intent; has original/direct edge support)
- `0.757928` ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس (matches primary intent; has original/direct edge support)
- `0.680613` تضخم في الارداف --SYMPTOM_OF--> تضخم (matches primary intent)
- `0.676552` خفقان القلب --SYMPTOM_OF--> ارتفاع ضغط الدم (matches primary intent)

### اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج للعصب السابع بعد مضي هذه المدة الزمنه

- `0.626529` شلل العصب السابع --TREATED_BY--> الكورتيزونات (has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.615969` شلل العصب السابع --TREATED_BY--> مضادات الالتهاب (has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.615969` شلل العصب السابع --TREATED_BY--> العلاج الطبيعي (has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.615969` شلل العصب السابع --TREATED_BY--> مضادات الفيروسات (has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.605409` شلل العصب السابع --TREATED_BY--> العلاج بالإبر الصينية (has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.540929` الكورتيزونات --TREATS--> شلل العصب السابع (strong semantic support; evidence overlaps query terms)
- `0.530369` مضادات الالتهاب --TREATS--> شلل العصب السابع (strong semantic support; evidence overlaps query terms)
- `0.530369` العلاج الطبيعي --TREATS--> شلل العصب السابع (strong semantic support; evidence overlaps query terms)

### تناولت مضاد حيووي زييثرون وانتج حساسيه شديده وتورم في المنطقة التناسليه وانا تعبانه جدا ما الحل ؟

- `0.938241` حساسية --TREATED_BY--> مضاد الهيستامين (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.938241` حساسية --TREATED_BY--> كورتيزون (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.877235` حساسية --TREATED_BY--> تيليفاست (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.868151` حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين (matches primary intent; has original/direct edge support)
- `0.851942` حساسية --TREATED_BY--> حليب مكسر بروتين الحليب (matches primary intent; has original/direct edge support)
- `0.851942` حساسية --TREATED_BY--> نازونكس (matches primary intent; has original/direct edge support)
- `0.846293` حساسية --TREATED_BY--> زيت الحبة السوداء (matches primary intent; has original/direct edge support)
- `0.768161` مضاد الهيستامين --TREATS--> حساسية (matches primary intent; evidence overlaps query terms)

### انا اشعر بالصداع والنعاس وحساسية في وجهي والحكة بكل انحاء جسمي كيف استطيع ان اوقف هذا الدواء

- `0.93426` حساسية --HAS_SYMPTOM--> سعال (matches primary intent; 2 evidence rows; has original/direct edge support; 2 distinct QA sources)
- `0.93185` حساسية --HAS_SYMPTOM--> ضيق تنفس (matches primary intent; 2 evidence rows; has original/direct edge support; 2 distinct QA sources)
- `0.868986` حساسية --HAS_SYMPTOM--> بلغم (matches primary intent; has original/direct edge support)
- `0.860949` حساسية --HAS_SYMPTOM--> نشفان (matches primary intent; has original/direct edge support)
- `0.834144` حساسية الصدر --HAS_SYMPTOM--> سعال (matches primary intent; has original/direct edge support)
- `0.794444` صداع --SYMPTOM_OF--> التهاب السحايا (matches primary intent)
- `0.783884` صداع --SYMPTOM_OF--> التهاب الجيوب الأنفية (matches primary intent)
- `0.779866` صداع --SYMPTOM_OF--> الصداع التوتري (matches primary intent)

### لا أستطبع النوم على جانبي لا الأيمن ولا الأيسر وأجد صعوبة في التنفس العميق. كما أشعر بين الفينة والأخرى بآلام قرب القلب. كما أخبركم أني مريصة بالقلب (مشكل في صمامتين)

- `0.759876` ضرس العقل --HAS_SYMPTOM--> الام (matches primary intent; has original/direct edge support)
- `0.758756` الام --SYMPTOM_OF--> ضرس العقل (matches primary intent)
- `0.748854` فقر الدم --HAS_SYMPTOM--> الم المعدجة (matches primary intent; has original/direct edge support)
- `0.748854` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (matches primary intent; has original/direct edge support)
- `0.743612` ضرس العقل --HAS_SYMPTOM--> صداع (matches primary intent; has original/direct edge support)
- `0.663254` الم المعدجة --SYMPTOM_OF--> فقر الدم (matches primary intent)
- `0.663254` فقدان الشهيه --SYMPTOM_OF--> فقر الدم (matches primary intent)
- `0.658012` صداع --SYMPTOM_OF--> ضرس العقل (matches primary intent)

### هل هناك أسباب أخرى محددة تؤدي الى ولادة دات شفة مشقوقة من غير استعمال دواء التوبيراميت.

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.526712` قرحة --TREATED_BY--> ايزومبرازول (has original/direct edge support; evidence overlaps query terms)
- `0.519498` شيب --TREATED_BY--> خلطة الريحان و الروزماري (has original/direct edge support)
- `0.441112` ايزومبرازول --TREATS--> قرحة (evidence overlaps query terms)
- `0.433898` خلطة الريحان و الروزماري --TREATS--> شيب (kept as lower-priority supporting graph edge)

### كيف تتم ازالة شظايا القنابل الصغيرة الانشطارية في المنزل عند عدم التمكن من الذهاب للمستشفى وهل هناك اخطار من بقائها؟

- `0.936577` شظايا القنابل الصغيرة الانشطارية --DIAGNOSED_BY--> أشعة (matches primary intent; has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.748328` التهاب --DIAGNOSED_BY--> تحليل بول (matches primary intent; has original/direct edge support)
- `0.748328` التهاب --TREATED_BY--> الاكثار من شرب الماء (matches primary intent; has original/direct edge support)
- `0.404497` أشعة --DIAGNOSES--> شظايا القنابل الصغيرة الانشطارية (strong semantic support; evidence overlaps query terms)
- `0.300728` تحليل بول --DIAGNOSES--> التهاب (kept as lower-priority supporting graph edge)
- `0.300728` الاكثار من شرب الماء --TREATS--> التهاب (kept as lower-priority supporting graph edge)

### السلام عليكم .. هل تناول ملعقة يوميا من زيت الحلبة على الريق يزيد من حجم الثدي بجانب التمارين ..؟؟ و ما المدة التى يمكن الاستمرار عليها فى تناول الزيت؟ و...

- `0.770312` النقص الشديد للصفائح --TREATED_BY--> الروتيكسيماب (matches primary intent; has original/direct edge support)
- `0.322712` الروتيكسيماب --TREATS--> النقص الشديد للصفائح (kept as lower-priority supporting graph edge)

### كيفية التعامل مع انتفاخ ضرس العقل مسببا الام و احمرار الفك الاسفل

- `0.882909` ضرس العقل --HAS_SYMPTOM--> الام (matches primary intent; has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.875543` الام --TREATED_BY--> المراجعة الطبية (matches primary intent; has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.875166` ضرس العقل --HAS_SYMPTOM--> صداع (matches primary intent; has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.875166` ضرس العقل --TREATED_BY--> المراجعة الطبية (matches primary intent; has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.854833` انتفاخ --INVESTIGATED_BY--> اشعة (matches primary intent; has original/direct edge support; strong semantic support)
- `0.767353` صداع --TREATED_BY--> المراجعة الطبية (matches primary intent; has original/direct edge support)
- `0.753054` وجع --INVESTIGATED_BY--> اشعة (matches primary intent; has original/direct edge support)
- `0.747207` ارتجاج دماغي --DIAGNOSED_BY--> أشعة (matches primary intent; has original/direct edge support)

### تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س

- `0.69404` مرض السكري --HAS_SYMPTOM--> ضغط الدم (3 evidence rows; has original/direct edge support; strong semantic support; evidence overlaps query terms; 3 distinct QA sources)
- `0.580792` ضغط الدم --SYMPTOM_OF--> مرض السكري (3 evidence rows; strong semantic support; evidence overlaps query terms; 3 distinct QA sources)
- `0.52211` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (has original/direct edge support; strong semantic support)
- `0.463395` ضغط الدم --HAS_NORMAL_RANGE--> 140-80 إذا لا توجد أمراض مصاحبة (has original/direct edge support)
- `0.414657` ضغط --SYMPTOM_OF--> التهاب الجيوب الأنفية (kept as lower-priority supporting graph edge)

### انا ابتلعت دبوس امس ولا اشعر ببلعه واعاني بوجع صدري كيف اعمل

- `0.74235` فقر الدم --HAS_SYMPTOM--> تنميل (matches primary intent; has original/direct edge support)
- `0.65675` تنميل --SYMPTOM_OF--> فقر الدم (matches primary intent)
- `0.558659` دبوس --DIAGNOSED_BY--> أشعة (has original/direct edge support; evidence overlaps query terms)
- `0.484356` وجع --INVESTIGATED_BY--> اشعة (has original/direct edge support)
- `0.389321` حساسية --DIAGNOSED_BY--> RAST Test (has original/direct edge support)
- `0.388579` أشعة --DIAGNOSES--> دبوس (evidence overlaps query terms)
- `0.379875` انتفاخ --INVESTIGATED_BY--> اشعة (has original/direct edge support)
- `0.314276` اشعة --INVESTIGATES--> وجع (kept as lower-priority supporting graph edge)

### عندى بقع بنية على جانبى الوجة وانا اعانى من انيميا 10 وكان عندى حصوات بالمرارة وعملت العملية ولا زالت البقع موجودة ما العلاج الاكيد وشكرا

- `0.84997` فقر الدم --HAS_SYMPTOM--> الم المعدجة (matches primary intent; 2 evidence rows; has original/direct edge support; strong semantic support; 2 distinct QA sources)
- `0.796769` فقر الدم --HAS_SYMPTOM--> تنميل (matches primary intent; has original/direct edge support; strong semantic support)
- `0.78997` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (matches primary intent; has original/direct edge support; strong semantic support)
- `0.767427` حساسية الصدر --HAS_SYMPTOM--> سعال (matches primary intent; has original/direct edge support)
- `0.763357` التهاب --HAS_SYMPTOM--> الدم (matches primary intent; has original/direct edge support)
- `0.681827` سعال --SYMPTOM_OF--> حساسية الصدر (matches primary intent)
- `0.677757` الدم --SYMPTOM_OF--> التهاب (matches primary intent)
- `0.555165` فقر الدم --MANAGED_BY--> أغذية غنية بالحديد والفولات وفيتامين ب12 (has original/direct edge support; evidence overlaps query terms)

### ماهو البردقوش وهل يوجد باليمن وهل يزيد من عدد الحيوانات المنويه؟

- `0.792457` الدورة الشهرية --TREATED_BY--> البردقوش (matches primary intent; has original/direct edge support; strong semantic support)
- `0.79103` التدخين --INVESTIGATED_BY--> الحيوانات المنوية (matches primary intent; has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.752882` الدورة الشهرية --TREATED_BY--> اكليل الجبل (matches primary intent; has original/direct edge support)
- `0.752882` الدورة الشهرية --TREATED_BY--> الميرمية (matches primary intent; has original/direct edge support)
- `0.752882` الدورة الشهرية --TREATED_BY--> البقدونس (matches primary intent; has original/direct edge support)
- `0.752882` الدورة الشهرية --TREATED_BY--> حشيشة الملاك (matches primary intent; has original/direct edge support)
- `0.752882` الدورة الشهرية --TREATED_BY--> القرفة (matches primary intent; has original/direct edge support)
- `0.752882` الدورة الشهرية --TREATED_BY--> الزنجبيل (matches primary intent; has original/direct edge support)

### اعاني من حموضة وصعوبة في التنفس وصعوبة بلع والم في الجانب الايسر من الصدر مع تعب في الكتف اليسرى بعد ابذال مجهود فهل هذا خطر على القلب ام حموضة عادية

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.78386` التهاب --HAS_SYMPTOM--> تعب (matches primary intent; has original/direct edge support)
- `0.78274` تعب --SYMPTOM_OF--> التهاب (matches primary intent)
- `0.76938` التهاب --HAS_SYMPTOM--> ضيق تنفس (matches primary intent; has original/direct edge support)
- `0.68378` ضيق تنفس --SYMPTOM_OF--> التهاب (matches primary intent)
- `0.501166` الكتف --TREATED_BY--> البروفين (has original/direct edge support)
- `0.331086` البروفين --TREATS--> الكتف (kept as lower-priority supporting graph edge)

### ما هو ابسط علاج لمرض السكر بدون كيماويات؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.935862` مرض السكري --HAS_SYMPTOM--> ضغط الدم (matches primary intent; 3 evidence rows; has original/direct edge support; strong semantic support; evidence overlaps query terms; 3 distinct QA sources)
- `0.775002` ضغط الدم --SYMPTOM_OF--> مرض السكري (matches primary intent; 2 evidence rows; strong semantic support; evidence overlaps query terms; 2 distinct QA sources)
- `0.472189` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.413367` التهاب --DIAGNOSED_BY--> تحاليل مخبرية (has original/direct edge support; evidence overlaps query terms)
- `0.371229` تحاليل مخبرية --DIAGNOSES--> مرض السكري (strong semantic support; evidence overlaps query terms)
- `0.327767` تحاليل مخبرية --DIAGNOSES--> التهاب (evidence overlaps query terms)

### انا عملت جراحة فى القلب وتم تغير الصمام المترالى بصمام ميكانيكى صناعى وباخد دواء واريفان ( لسيولة الدم ) 8 ملجرام ومصاب بالانفلوانزا ماالعلاج المناسب

- `0.456144` ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب (2 evidence rows; has original/direct edge support; 2 distinct QA sources)
- `0.392064` ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس (has original/direct edge support)
- `0.385728` ارتفاع ضغط الدم --HAS_SYMPTOM--> دوخة (has original/direct edge support)
- `0.380759` مرض السكري --HAS_SYMPTOM--> ضغط الدم (has original/direct edge support)
- `0.370544` خفقان القلب --SYMPTOM_OF--> ارتفاع ضغط الدم (2 evidence rows; 2 distinct QA sources)
- `0.306464` ضيق تنفس --SYMPTOM_OF--> ارتفاع ضغط الدم (kept as lower-priority supporting graph edge)
- `0.300128` دوخة --SYMPTOM_OF--> ارتفاع ضغط الدم (kept as lower-priority supporting graph edge)
- `0.295159` ضغط الدم --SYMPTOM_OF--> مرض السكري (kept as lower-priority supporting graph edge)

### هل حبوب كريستور(rousovastatin) تؤثر على عضلة القلب ؟

- `0.774283` فقر الدم --HAS_SYMPTOM--> الم المعدجة (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.774283` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.411345` ضغط الدم --HAS_NORMAL_RANGE--> 140-80 إذا لا توجد أمراض مصاحبة (has original/direct edge support)
- `0.411345` نبض القلب --HAS_NORMAL_RANGE--> 65-85 تقريبا وقد يقبل أقل أو أكثر (has original/direct edge support)
- `0.326683` الم المعدجة --SYMPTOM_OF--> فقر الدم (evidence overlaps query terms)
- `0.326683` فقدان الشهيه --SYMPTOM_OF--> فقر الدم (evidence overlaps query terms)

### هل يوجد أعشاب طبية تساعد على الشفاء من حالة الاكتئاب و الشعور بالخوف ، علما بأنه يوجد لدي فقر دم (انيميا الفول ) و يتجدث حالات الاكتئاب هذه عند تناول...

- `0.852319` فقر الدم --DIAGNOSED_BY--> تحاليل مخبرية (matches primary intent; 2 evidence rows; has original/direct edge support; 2 distinct QA sources)
- `0.837204` فقر الدم --HAS_SYMPTOM--> الم المعدجة (matches primary intent; 2 evidence rows; has original/direct edge support; 2 distinct QA sources)
- `0.786349` فقر الدم --DIAGNOSED_BY--> فحص تحاليل مخبرية (matches primary intent; has original/direct edge support)
- `0.786349` فقر الدم --HAS_SYMPTOM--> تنميل (matches primary intent; has original/direct edge support)
- `0.777204` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (matches primary intent; has original/direct edge support)
- `0.492923` فقر الدم --MANAGED_BY--> أغذية غنية بالحديد والفولات وفيتامين ب12 (has original/direct edge support; evidence overlaps query terms)
- `0.323389` تحاليل مخبرية --DIAGNOSES--> فقر الدم (kept as lower-priority supporting graph edge)

### انا عندى 16 سنة وعندي ارتخاء بالصمام الميترالى والاعراض اللى عندي دوخة لما أقف و بتعب من أقل مجهود , وعند الاستيقاظ هناك ضيق بالتنفس,والدكتورظكاتبلى اندرال 20 جم بس مش...

- `0.771779` التهاب --HAS_SYMPTOM--> تعب (matches primary intent; has original/direct edge support)
- `0.770659` تعب --SYMPTOM_OF--> التهاب (matches primary intent)
- `0.769951` ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب (matches primary intent; has original/direct edge support)
- `0.76804` ارتفاع ضغط الدم --HAS_SYMPTOM--> دوخة (matches primary intent; has original/direct edge support)
- `0.76692` دوخة --SYMPTOM_OF--> ارتفاع ضغط الدم (matches primary intent)
- `0.765727` ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس (matches primary intent; has original/direct edge support)
- `0.758073` التهاب --HAS_SYMPTOM--> ضيق تنفس (matches primary intent; has original/direct edge support)
- `0.684351` خفقان القلب --SYMPTOM_OF--> ارتفاع ضغط الدم (matches primary intent)

### هل هناك اسباب للحساسية من الباراسيتمول وما الاغذية التى امتنع عنها وما هى الاغذية التى ااكلها

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.963166` حساسية --HAS_SYMPTOM--> سعال (matches primary intent; 2 evidence rows; has original/direct edge support; strong semantic support; evidence overlaps query terms; 2 distinct QA sources)
- `0.951844` حساسية --HAS_SYMPTOM--> ضيق تنفس (matches primary intent; 2 evidence rows; has original/direct edge support; strong semantic support; evidence overlaps query terms; 2 distinct QA sources)
- `0.901048` حساسية --HAS_SYMPTOM--> بلغم (matches primary intent; has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.877474` حساسية --HAS_SYMPTOM--> نشفان (matches primary intent; has original/direct edge support; strong semantic support)
- `0.843151` حساسية الصدر --HAS_SYMPTOM--> سعال (matches primary intent; has original/direct edge support)
- `0.800413` ربو --HAS_SYMPTOM--> سعال (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.798301` ربو --HAS_SYMPTOM--> بلغم (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.794077` التهاب --HAS_SYMPTOM--> سعال (matches primary intent; has original/direct edge support; evidence overlaps query terms)

### كان لدي ارتفاع بسيط في الصفائح ٤٦١ وعندما ولدت بعد ٥٠ يوم التحليل طلع ٦٧٩ واشكو من عدم اكتمال النفس في بعض الاوقات وقال لي الطبيب لديك التهاب في الصدر...

- `0.505269` صداع --INVESTIGATED_BY--> الصور الشعاعية (has original/direct edge support)
- `0.419669` الصور الشعاعية --INVESTIGATES--> صداع (kept as lower-priority supporting graph edge)
- `0.418874` الصدمة الكهربائية --TREATED_BY--> الطبيب (has original/direct edge support)
- `0.418874` الحروق --TREATED_BY--> الطبيب (has original/direct edge support)
- `0.417754` الطبيب --TREATS--> الصدمة الكهربائية (kept as lower-priority supporting graph edge)
- `0.417754` الطبيب --TREATS--> الحروق (kept as lower-priority supporting graph edge)
- `0.399261` الصداع التوتري --HAS_SYMPTOM--> صداع (has original/direct edge support)
- `0.313661` صداع --SYMPTOM_OF--> الصداع التوتري (kept as lower-priority supporting graph edge)

### عمري 18 سنة وأنا أعاني من صغر الثدي هل يوجد أي حل لتكبيره دون جراحة?

- `0.401988` بيلة الميوغلوبين --TREATED_BY--> السوائل (has original/direct edge support; evidence overlaps query terms)
- `0.40146` نقص بحجم الثدي --TREATED_BY--> مراجعة اخصائية النسائية (has original/direct edge support; evidence overlaps query terms)
- `0.40146` نقص بحجم الثدي --DIAGNOSED_BY--> فحص سريري (has original/direct edge support; evidence overlaps query terms)
- `0.397318` شيب --TREATED_BY--> خلطة الريحان و الروزماري (has original/direct edge support; evidence overlaps query terms)
- `0.396585` حساسية --DIAGNOSED_BY--> تحليل الحساسية (has original/direct edge support; evidence overlaps query terms)
- `0.316388` السوائل --TREATS--> بيلة الميوغلوبين (evidence overlaps query terms)
- `0.31586` مراجعة اخصائية النسائية --TREATS--> نقص بحجم الثدي (evidence overlaps query terms)
- `0.31586` فحص سريري --DIAGNOSES--> نقص بحجم الثدي (evidence overlaps query terms)

### عمري ٢٥سنة واعاني من نشاط زائد في الغده الدرقية وقمت بأخذ جرعه من اليود النووي المشع وعندي طفل عمره سنه فما المده الزمنيه المحدده اللتي سأتمكن بعدها

- `0.772588` مرض الغدة الدرقية --TREATED_BY--> التروكسين (matches primary intent; has original/direct edge support)
- `0.671628` التروكسين --TREATS--> مرض الغدة الدرقية (matches primary intent)
- `0.415583` نشاط الغدة الدرقية --DIAGNOSED_BY--> تحاليل مخبرية (has original/direct edge support; evidence overlaps query terms)
- `0.411359` مرض جريفز --DIAGNOSED_BY--> تحاليل مخبرية (has original/direct edge support; evidence overlaps query terms)
- `0.410588` مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون (has original/direct edge support)
- `0.329983` تحاليل مخبرية --DIAGNOSES--> نشاط الغدة الدرقية (evidence overlaps query terms)
- `0.325759` تحاليل مخبرية --DIAGNOSES--> مرض جريفز (evidence overlaps query terms)
- `0.309628` الهرمون --DIAGNOSES--> مرض الغدة الدرقية (kept as lower-priority supporting graph edge)

### يشعر والدي بألم في منطقة الصدر علما ان والدي مصاب بجلطة قلبية ودماغية اليوم قد تناول بيزا وكانت دسمة،،،،،هل هذا الم قلب ام الام معدة

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.766384` ضرس العقل --HAS_SYMPTOM--> الام (matches primary intent; has original/direct edge support)
- `0.765264` الام --SYMPTOM_OF--> ضرس العقل (matches primary intent)
- `0.756879` ارتياف دعب \u0627لديم --HAS_SYMPTOM--> الالم (matches primary intent; has original/direct edge support)
- `0.7523` ضرس العقل --HAS_SYMPTOM--> صداع (matches primary intent; has original/direct edge support)
- `0.671279` الالم --SYMPTOM_OF--> ارتياف دعب \u0627لديم (matches primary intent)
- `0.6667` صداع --SYMPTOM_OF--> ضرس العقل (matches primary intent)
- `0.488864` الام --TREATED_BY--> المراجعة الطبية (has original/direct edge support)
- `0.3903` صداع --TREATED_BY--> المراجعة الطبية (has original/direct edge support)

### هل يوجد تأثير على الجنين في حالة تعاطي أقراص ميزوتاك في بداية الحمل بغرض الإجهاض وأنا الآن اقتنعت باكمال الحمل ولكن قلق من تأثر الجنين بالمادة الفعالة لهذا الدواء؟

- `0.791231` بريمولوت ن --REQUIRES_MEDICAL_SUPERVISION_FOR--> إيقاف الدواء ومراجعة الطبيب أثناء الحمل (matches primary intent; has original/direct edge support)
- `0.55377` عظام الجنين --DEVELOPS_DURING--> نهاية الأسبوع السادس تقريبا (has original/direct edge support)
- `0.544646` الدواء --TREATS--> الملوية البوابية (kept as lower-priority supporting graph edge)
- `0.527948` فايروس الكبد --TREATED_BY--> اللقاح (has original/direct edge support)
- `0.522589` الحمل --HAS_SYMPTOM--> قيء (has original/direct edge support; strong semantic support)
- `0.517388` فايروس الكبد --TREATED_BY--> الجرعات الثلاثه (has original/direct edge support)
- `0.516041` الحمل --HAS_SYMPTOM--> الزراق (has original/direct edge support; strong semantic support)
- `0.442348` اللقاح --TREATS--> فايروس الكبد (kept as lower-priority supporting graph edge)

### حموضة في فمي واحساس برائحة تفاح متعفن مع كدمات زرقاء غامقة في قدماي واحساس بغبوش في الرؤية

- `0.747663` فقر الدم --HAS_SYMPTOM--> الم المعدجة (matches primary intent; has original/direct edge support)
- `0.747663` الم المعدجة --INVESTIGATED_BY--> فحص الجرثومة الحلزونية (matches primary intent; has original/direct edge support)
- `0.300063` الم المعدجة --SYMPTOM_OF--> فقر الدم (kept as lower-priority supporting graph edge)
- `0.300063` فحص الجرثومة الحلزونية --INVESTIGATES--> الم المعدجة (kept as lower-priority supporting graph edge)

### قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة

- `0.904228` وجع --INVESTIGATED_BY--> اشعة (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.898703` انتفاخ --INVESTIGATED_BY--> اشعة (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.818628` اشعة --INVESTIGATES--> وجع (matches primary intent; evidence overlaps query terms)
- `0.813103` اشعة --INVESTIGATES--> انتفاخ (matches primary intent; evidence overlaps query terms)
- `0.762268` التهاب --DIAGNOSED_BY--> اشعة (matches primary intent; has original/direct edge support)
- `0.762268` ارتجاج دماغي --DIAGNOSED_BY--> أشعة (matches primary intent; has original/direct edge support)
- `0.739025` أشعة --DIAGNOSES--> تسوس الأسنان (matches primary intent)
- `0.7335` اشعة --DIAGNOSES--> التهاب (matches primary intent)

### ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.90531` مرض السكري --HAS_SYMPTOM--> ضغط الدم (matches primary intent; 3 evidence rows; has original/direct edge support; 3 distinct QA sources)
- `0.744279` ضغط الدم --SYMPTOM_OF--> مرض السكري (matches primary intent; 2 evidence rows; 2 distinct QA sources)
- `0.502444` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (has original/direct edge support; evidence overlaps query terms)
- `0.471323` التهاب --DIAGNOSED_BY--> تحاليل مخبرية (has original/direct edge support; evidence overlaps query terms)
- `0.401484` تحاليل مخبرية --DIAGNOSES--> مرض السكري (evidence overlaps query terms)
- `0.385723` تحاليل مخبرية --DIAGNOSES--> التهاب (evidence overlaps query terms)

### أعاني من حرقان بكامل بجسمي والتهاب المسالك البوليه وارتفاع الكلسترول والدهون الثلاثيه مال الحل جزاكم الله خير وما قد يكون المسبب

- `0.754124` الصداع التوتري --HAS_SYMPTOM--> صداع (matches primary intent; has original/direct edge support)
- `0.668524` صداع --SYMPTOM_OF--> الصداع التوتري (matches primary intent)
- `0.391394` ارتفاع ضغط الدم --TREATED_BY--> العقاقير (has original/direct edge support)
- `0.305794` العقاقير --TREATS--> ارتفاع ضغط الدم (kept as lower-priority supporting graph edge)

### ماهي علاجات حمى التهاب باطن القدم وباطن اليد وماهي الفحوصات للتاكد من اسباب هذا المرض؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.777132` حمى عضة الجرذ --HAS_SYMPTOM--> حمى (matches primary intent; has original/direct edge support)
- `0.777132` حمى عضة الفأر --HAS_SYMPTOM--> حمى (matches primary intent; has original/direct edge support)
- `0.777132` حمى عضة الجرذون --HAS_SYMPTOM--> حمى (matches primary intent; has original/direct edge support)
- `0.776012` حمى --SYMPTOM_OF--> حمى عضة الجرذ (matches primary intent)
- `0.776012` حمى --SYMPTOM_OF--> حمى عضة الفأر (matches primary intent)
- `0.776012` حمى --SYMPTOM_OF--> حمى عضة الجرذون (matches primary intent)
- `0.756957` حمى عضة الجرذ --HAS_SYMPTOM--> ارتجاف (matches primary intent; has original/direct edge support)
- `0.756957` حمى عضة الجرذ --HAS_SYMPTOM--> أوجاع العضلات (matches primary intent; has original/direct edge support)

### والدي وقع من الدرج قبل ثلالث ايام نلاحظ هناك زغللة في عينه اليمنى مع حول فيها تم قياسة مستوى السكر اليوم 200 اتمنى افادتي بهذا الامر هل له علاقة بالحلطة...

- `0.902855` مرض السكري --HAS_SYMPTOM--> ضغط الدم (matches primary intent; 3 evidence rows; has original/direct edge support; 3 distinct QA sources)
- `0.78813` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (matches primary intent; has original/direct edge support)
- `0.749896` التهاب --DIAGNOSED_BY--> تحاليل مخبرية (matches primary intent; has original/direct edge support)
- `0.32517` تحاليل مخبرية --DIAGNOSES--> مرض السكري (kept as lower-priority supporting graph edge)
- `0.319967` ضغط الدم --SYMPTOM_OF--> مرض السكري (kept as lower-priority supporting graph edge)
- `0.302296` تحاليل مخبرية --DIAGNOSES--> التهاب (kept as lower-priority supporting graph edge)

### ماهي الاهمية الطبية للجلوكوز والفركتوز والجالكتوز؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.820395` التهاب --HAS_SYMPTOM--> اختلال وظائف الكبد (matches primary intent; has original/direct edge support; evidence overlaps query terms)
- `0.734795` اختلال وظائف الكبد --SYMPTOM_OF--> التهاب (matches primary intent; evidence overlaps query terms)

### متى يلجأ الدكتور الي نزع عَصّب السن او الضرس

- `0.429328` حشو الأسنان --NOT_ASSOCIATED_WITH--> غمازة الوجه (has original/direct edge support)
- `0.429328` تخدير موضعي قوي --MAY_TEMPORARILY_AFFECT--> غمازة الوجه (has original/direct edge support)
- `0.420488` برد الأسنان --HAS_RISK--> حساسية الأسنان (has original/direct edge support)
- `0.420488` برد الأسنان --PROCEDURE_DURATION--> جلسة واحدة أو جلستان (has original/direct edge support)

### سلام لقد اجريت فحص الهرمون B-HCG ،و نتائج التحاليل كما يللي 3-4 اسبوع 9-130 4-5 اسبوع 75-2600 5-6 اسبوع 850-20800 7-8 اسبوع 4000-100200 7-12 اسبوع 11500-289000 12-16 اسبوع 18300-137000 و...

- `0.533181` صعوبة التنفس والإرهاق --INVESTIGATED_BY--> التاريخ المرضي والفحص السريري (has original/direct edge support)
- `0.518347` مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون (has original/direct edge support)
- `0.517227` الهرمون --DIAGNOSES--> مرض الغدة الدرقية (kept as lower-priority supporting graph edge)
- `0.511424` نقص الصفيحات --DIAGNOSED_BY--> فحص نخاع العظم (has original/direct edge support)
- `0.425824` فحص نخاع العظم --DIAGNOSES--> نقص الصفيحات (kept as lower-priority supporting graph edge)
- `0.409181` صعوبة التنفس والإرهاق --MAY_BE_ASSOCIATED_WITH--> التهاب تنفسي أو فقر دم أو اضطراب دموي أو دوراني (has original/direct edge support)
- `0.381063` مرض الغدة الدرقية --TREATED_BY--> التروكسين (has original/direct edge support)
- `0.295463` التروكسين --TREATS--> مرض الغدة الدرقية (kept as lower-priority supporting graph edge)

### لسلام عليكم ممكن تساعدوني ابني عملتله تطعيم سنة ونص اليوم هو يعاني من ارتفاع الحرارة ومايقدر يحرك رجلو وحتى يوقف وهو كتير البكاء كيف اتعامل معاه كيف اخفف من الم...

- `0.491956` حمى --TREATED_BY--> خافض حراره (has original/direct edge support; strong semantic support; evidence overlaps query terms)
- `0.415714` حصى الكلى --TREATED_BY--> الإكثار من السوائل والتقييم الطبي (has original/direct edge support)
- `0.406356` خافض حراره --TREATS--> حمى (strong semantic support; evidence overlaps query terms)
- `0.393668` النقص الشديد للصفائح --TREATED_BY--> الروتيكسيماب (has original/direct edge support)
- `0.308068` الروتيكسيماب --TREATS--> النقص الشديد للصفائح (kept as lower-priority supporting graph edge)

### هل زيت نبات الميرمية له آثار جانبية عند تناوله بشكل 3 كبسولات قبل الطعام للتخلص من افراز البرولاكتين المفرز والناتج عن ورم حميد في الغدة النخامية . .

- `0.436585` الدورة الشهرية --TREATED_BY--> الميرمية (has original/direct edge support; strong semantic support)
- `0.435465` الميرمية --TREATS--> الدورة الشهرية (strong semantic support)
- `0.413108` مرض الغدة الدرقية --TREATED_BY--> التروكسين (has original/direct edge support)
- `0.413108` مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون (has original/direct edge support)
- `0.401897` الجوع --TREATED_BY--> الطعام (has original/direct edge support)
- `0.400777` الطعام --TREATS--> الجوع (kept as lower-priority supporting graph edge)
- `0.385005` الدورة الشهرية --TREATED_BY--> اكليل الجبل (has original/direct edge support)
- `0.385005` الدورة الشهرية --TREATED_BY--> البقدونس (has original/direct edge support)

### عندي الم في منطقه البطن مع الم بصدر جهه اليمين الى الرقبه وماقدرت اعرف تفسير الالم ذا من ايش او سببه مع وجود احيان ضيق بالتنفس ،،،، افيدوني

- `0.774655` ارتياف دعب \u0627لديم --HAS_SYMPTOM--> الالم (matches primary intent; has original/direct edge support)
- `0.773535` الالم --SYMPTOM_OF--> ارتياف دعب \u0627لديم (matches primary intent)
- `0.755915` فقر الدم --HAS_SYMPTOM--> الم المعدجة (matches primary intent; has original/direct edge support)
- `0.670315` الم المعدجة --SYMPTOM_OF--> فقر الدم (matches primary intent)
- `0.405299` الجلد المترهل --TREATED_BY--> الجراحة التجميلية (has original/direct edge support)
- `0.393915` الم المعدجة --INVESTIGATED_BY--> فحص الجرثومة الحلزونية (has original/direct edge support)
- `0.319699` الجراحة التجميلية --TREATS--> الجلد المترهل (kept as lower-priority supporting graph edge)
- `0.308315` فحص الجرثومة الحلزونية --INVESTIGATES--> الم المعدجة (kept as lower-priority supporting graph edge)

## Output Files

- Reranked subgraphs JSON: `outputs/05_trial_graph_v1/subgraph_reranking/trial_graph_v1_reranked_subgraphs.json`
- Reranked relations CSV: `outputs/05_trial_graph_v1/subgraph_reranking/trial_graph_v1_reranked_relations.csv`
- Reranked evidence CSV: `outputs/05_trial_graph_v1/subgraph_reranking/trial_graph_v1_reranked_evidence.csv`

## Next Step From Mix.png

Continue to Step 11: evidence-focused context construction from the reranked subgraphs.
