# Trial Graph v1 Step 11 Evidence-Focused Context Construction Report

This step converts Step 10 reranked subgraphs into compact evidence bundles for later LLM answer generation.
It still does not generate medical answers.

## Context Rules

- Keep graph relation, rerank score, and reliability label
- Attach source Q&A evidence snippets
- Preserve Step 8 warnings, especially missing CAUSES relation warnings
- Enforce a simple character budget so prompts can stay controllable

## Query Context Summary

### ما علاج البلغم (حساسية الصدر) رغم اخذى هلاج اكثر من مرة ولا فائدة ؟ هل امتنع عن طعام معين يزيد البلغم وانا غير مدخن واخذ علاج للضغط والكوليسترول عمرى 55...

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.853633` حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين
- `medium` `0.845599` حساسية --TREATED_BY--> مضاد الهيستامين
- `medium` `0.845599` حساسية --TREATED_BY--> كورتيزون
- `medium` `0.838022` حساسية --TREATED_BY--> تيليفاست
- `medium` `0.83746` ارتفاع الكوليسترول --MANAGED_BY--> تقليل الدهون والرياضة

### كيف اعالج علامات الشيخوخة المبكرة بالوجه؟

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.755988` تضيق القنوات الموجودة داخل الكبد --TREATED_BY--> منظار قنوات مرارية الف سلامة
- `limited` `0.670388` منظار قنوات مرارية الف سلامة --TREATS--> تضيق القنوات الموجودة داخل الكبد
- `limited` `0.379826` حساسية --DIAGNOSED_BY--> تحاليل مخبرية
- `limited` `0.379631` انتفاخ --INVESTIGATED_BY--> اشعة
- `limited` `0.379458` وجع --INVESTIGATED_BY--> اشعة

### ماالعلاج الاسعافي لأنخفاض السكر مع فقدان الوعي

- Graph edges included: 6
- Evidence snippets included: 7
- `strong` `0.920872` مرض السكري --HAS_SYMPTOM--> ضغط الدم
- `medium` `0.919639` فقدان الوعي --TREATED_BY--> عسل
- `medium` `0.803312` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية
- `medium` `0.759701` التهاب --DIAGNOSED_BY--> تحاليل مخبرية
- `limited` `0.387559` عسل --TREATS--> فقدان الوعي

### هل الاشعة المقطعيه بالصبغه للقلب تسبب انتفاخ اسفل الوجه او انتفاخ الغده هل هو طبيعي

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.863471` انتفاخ --INVESTIGATED_BY--> اشعة
- `medium` `0.78026` مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون
- `medium` `0.777871` اشعة --INVESTIGATES--> انتفاخ
- `medium` `0.777748` أشعة --DIAGNOSES--> تسوس الأسنان
- `medium` `0.773343` وجع --INVESTIGATED_BY--> اشعة

### السلام عليكم..ماهو العلاج المناسب لتقليل نسبة الاملاح في الدم النسبة الحالية عندي هي (7.9) عمري 44 سنة /ذكر؟

- Graph edges included: 6
- Evidence snippets included: 6
- `limited` `0.532286` حساسية الصدر --HAS_SYMPTOM--> سعال
- `limited` `0.53072` التهاب --HAS_SYMPTOM--> الدم
- `limited` `0.446686` سعال --SYMPTOM_OF--> حساسية الصدر
- `limited` `0.44512` الدم --SYMPTOM_OF--> التهاب
- `limited` `0.402496` التهاب --DIAGNOSED_BY--> تصوير الجهاز البولي

### السلام عليكم أنا أشعر ببرودة رأسي -وغذا اصبح ملمس رأسي بارد جاني صداع لايزول بالمسكنات- ذهبت لأفضل أخصائي أنف وأذن وحنجرة قال هذا المرض ماله علاج !! ماهي التحاليل الأزمة...

- Graph edges included: 6
- Evidence snippets included: 6
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `medium` `0.787398` التهاب السحايا --HAS_SYMPTOM--> صداع
- `medium` `0.786278` صداع --SYMPTOM_OF--> التهاب السحايا
- `medium` `0.776838` التهاب الجيوب الأنفية --HAS_SYMPTOM--> صداع
- `medium` `0.775718` صداع --SYMPTOM_OF--> التهاب الجيوب الأنفية
- `medium` `0.766573` صداع --SYMPTOM_OF--> الصداع التوتري

### مامتي جدا تعبانه من القرحة من غير النزيف المستمر والان هي لا تتناول الاطعمة بسبب الغثيان ...ارجو مساعدتي ..وهي لا تريد المستشفی

- Graph edges included: 4
- Evidence snippets included: 4
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `limited` `0.567512` قرحة --TREATED_BY--> ايزومبرازول
- `limited` `0.407368` الملوية البوابية --TREATED_BY--> الدواء
- `limited` `0.397432` ايزومبرازول --TREATS--> قرحة
- `limited` `0.321768` الدواء --TREATS--> الملوية البوابية

### ما البديل لعمل كراون للضرس في حال كان طول الضرس قصير بسبب كسر وتآكل في السطح بعد حشو عصب مع حجم طبيعي للضرس ،حتى يعود يصبح في طول يسمح بتركيب...

- Graph edges included: 6
- Evidence snippets included: 6
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `limited` `0.421826` حشو الأسنان --NOT_ASSOCIATED_WITH--> غمازة الوجه
- `limited` `0.421826` تخدير موضعي قوي --MAY_TEMPORARILY_AFFECT--> غمازة الوجه
- `limited` `0.415278` برد الأسنان --HAS_RISK--> حساسية الأسنان
- `limited` `0.415278` برد الأسنان --PROCEDURE_DURATION--> جلسة واحدة أو جلستان
- `limited` `0.38401` بروز في البطن --TREATED_BY--> تمارين رياضية

### زوجتي حامل ومنذ بداية حملها لم اتوقف عن الاتصال معهاابدا ..فهل ذلك له علاقه لما تشعر به من حرقه في المهبل...وهل ذلك له تأثير على الجنين....

- Graph edges included: 2
- Evidence snippets included: 2
- `limited` `0.496355` التهاب --HAS_SYMPTOM--> حرقه
- `limited` `0.495235` حرقه --SYMPTOM_OF--> التهاب

### لمدا كلما انزعجت من شخص ما أشعر بدوار ودقات سريعة للقلب وشعور براسي تقيل تم يغمى علي دون الغياب عن الوعي فما تشخيصكم لهدا وشكراً جزيل

- Graph edges included: 6
- Evidence snippets included: 6
- `limited` `0.402766` فقر الدم --MANAGED_BY--> أغذية غنية بالحديد والفولات وفيتامين ب12
- `limited` `0.402766` أغذية غنية بالحديد والفولات وفيتامين ب12 --ABSORPTION_IMPROVED_BY--> أطعمة غنية بفيتامين ج
- `limited` `0.402766` أغذية غنية بالحديد والفولات وفيتامين ب12 --ABSORPTION_REDUCED_BY--> الشاي والقهوة والكالسيوم مع الحديد
- `limited` `0.377644` سيلان الانف --TREATED_BY--> بخاخات الماء والملح
- `limited` `0.377644` سيلان الانف --INVESTIGATED_BY--> خصائي الاطفال

### عندي فقر دم وعملت التحاليل عندي نقص فيتامين دال ونقص حديد وصف لي الدكتور 20 ابرة حديد لمدة شهر هل اخذ هالكمية بهذه المدة آمن أم مضر للجسم ؟ وما...

- Graph edges included: 6
- Evidence snippets included: 7
- `strong` `0.86682` فقر الدم --HAS_SYMPTOM--> الم المعدجة
- `medium` `0.816292` فقر الدم --HAS_SYMPTOM--> تنميل
- `medium` `0.80682` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه
- `medium` `0.763` نقص هرمونات --HAS_SYMPTOM--> انقطاع الطمث
- `limited` `0.695822` نقص حديد --DIAGNOSED_BY--> فحص تحاليل مخبرية

### أود معرفة ما أسباب تدلي المستقيم؟وطرق العلاج؟

- Graph edges included: 6
- Evidence snippets included: 6
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `medium` `0.773137` حساسية الصدر --HAS_SYMPTOM--> سعال
- `medium` `0.757512` التهاب --HAS_SYMPTOM--> الدم
- `limited` `0.687537` سعال --SYMPTOM_OF--> حساسية الصدر
- `limited` `0.671912` الدم --SYMPTOM_OF--> التهاب
- `limited` `0.527524` دوالي الخصية --TREATED_BY--> العلاج بالجراحة

### كيف يمكن شد الجلد المترهل في منطقه البطن مع العلم ان الوزن مناسب؟

- Graph edges included: 4
- Evidence snippets included: 4
- `medium` `0.956489` الجلد المترهل --TREATED_BY--> الجراحة التجميلية
- `medium` `0.7647` مرض السكري --HAS_SYMPTOM--> ضغط الدم
- `limited` `0.424409` الجراحة التجميلية --TREATS--> الجلد المترهل
- `limited` `0.3171` ضغط الدم --SYMPTOM_OF--> مرض السكري

### السلام عليكم عمري43 اعاني ارتفاع الصفراء في الدم وصلت الي 7.6 ويوجد تضخم في الطحال والم ف اسفل البطن وجانبين الي الظهر مع احساس بالتعب تحاليل للفيروسات سلبي ومناعةانكا 1/80

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.850693` تضخم --HAS_SYMPTOM--> تضخم في الارداف
- `medium` `0.774964` التهاب --HAS_SYMPTOM--> تعب
- `medium` `0.773844` تعب --SYMPTOM_OF--> التهاب
- `medium` `0.762152` ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب
- `medium` `0.761168` التهاب --HAS_SYMPTOM--> ضيق تنفس

### اعاني منذ فترة خمس سنوات من اصابة العصب السابع وترك بعض الاثار علي منها عند الطعام تذرف عيني اليسرى بالدمع هل هناك علاج للعصب السابع بعد مضي هذه المدة الزمنه

- Graph edges included: 6
- Evidence snippets included: 6
- `limited` `0.626529` شلل العصب السابع --TREATED_BY--> الكورتيزونات
- `limited` `0.615969` شلل العصب السابع --TREATED_BY--> مضادات الالتهاب
- `limited` `0.615969` شلل العصب السابع --TREATED_BY--> العلاج الطبيعي
- `limited` `0.615969` شلل العصب السابع --TREATED_BY--> مضادات الفيروسات
- `limited` `0.605409` شلل العصب السابع --TREATED_BY--> العلاج بالإبر الصينية

### تناولت مضاد حيووي زييثرون وانتج حساسيه شديده وتورم في المنطقة التناسليه وانا تعبانه جدا ما الحل ؟

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.938241` حساسية --TREATED_BY--> مضاد الهيستامين
- `medium` `0.938241` حساسية --TREATED_BY--> كورتيزون
- `medium` `0.877235` حساسية --TREATED_BY--> تيليفاست
- `medium` `0.868151` حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين
- `medium` `0.851942` حساسية --TREATED_BY--> حليب مكسر بروتين الحليب

### انا اشعر بالصداع والنعاس وحساسية في وجهي والحكة بكل انحاء جسمي كيف استطيع ان اوقف هذا الدواء

- Graph edges included: 6
- Evidence snippets included: 8
- `strong` `0.93426` حساسية --HAS_SYMPTOM--> سعال
- `strong` `0.93185` حساسية --HAS_SYMPTOM--> ضيق تنفس
- `medium` `0.868986` حساسية --HAS_SYMPTOM--> بلغم
- `medium` `0.860949` حساسية --HAS_SYMPTOM--> نشفان
- `medium` `0.834144` حساسية الصدر --HAS_SYMPTOM--> سعال

### لا أستطبع النوم على جانبي لا الأيمن ولا الأيسر وأجد صعوبة في التنفس العميق. كما أشعر بين الفينة والأخرى بآلام قرب القلب. كما أخبركم أني مريصة بالقلب (مشكل في صمامتين)

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.759876` ضرس العقل --HAS_SYMPTOM--> الام
- `medium` `0.758756` الام --SYMPTOM_OF--> ضرس العقل
- `limited` `0.748854` فقر الدم --HAS_SYMPTOM--> الم المعدجة
- `limited` `0.748854` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه
- `limited` `0.743612` ضرس العقل --HAS_SYMPTOM--> صداع

### هل هناك أسباب أخرى محددة تؤدي الى ولادة دات شفة مشقوقة من غير استعمال دواء التوبيراميت.

- Graph edges included: 4
- Evidence snippets included: 4
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `limited` `0.526712` قرحة --TREATED_BY--> ايزومبرازول
- `limited` `0.519498` شيب --TREATED_BY--> خلطة الريحان و الروزماري
- `limited` `0.441112` ايزومبرازول --TREATS--> قرحة
- `limited` `0.433898` خلطة الريحان و الروزماري --TREATS--> شيب

### كيف تتم ازالة شظايا القنابل الصغيرة الانشطارية في المنزل عند عدم التمكن من الذهاب للمستشفى وهل هناك اخطار من بقائها؟

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.936577` شظايا القنابل الصغيرة الانشطارية --DIAGNOSED_BY--> أشعة
- `limited` `0.748328` التهاب --DIAGNOSED_BY--> تحليل بول
- `limited` `0.748328` التهاب --TREATED_BY--> الاكثار من شرب الماء
- `limited` `0.404497` أشعة --DIAGNOSES--> شظايا القنابل الصغيرة الانشطارية
- `limited` `0.300728` تحليل بول --DIAGNOSES--> التهاب

### السلام عليكم .. هل تناول ملعقة يوميا من زيت الحلبة على الريق يزيد من حجم الثدي بجانب التمارين ..؟؟ و ما المدة التى يمكن الاستمرار عليها فى تناول الزيت؟ و...

- Graph edges included: 2
- Evidence snippets included: 2
- `medium` `0.770312` النقص الشديد للصفائح --TREATED_BY--> الروتيكسيماب
- `limited` `0.322712` الروتيكسيماب --TREATS--> النقص الشديد للصفائح

### كيفية التعامل مع انتفاخ ضرس العقل مسببا الام و احمرار الفك الاسفل

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.882909` ضرس العقل --HAS_SYMPTOM--> الام
- `medium` `0.875543` الام --TREATED_BY--> المراجعة الطبية
- `medium` `0.875166` ضرس العقل --HAS_SYMPTOM--> صداع
- `medium` `0.875166` ضرس العقل --TREATED_BY--> المراجعة الطبية
- `medium` `0.854833` انتفاخ --INVESTIGATED_BY--> اشعة

### تعاني والدتي من انسداد في الصمام الابهر بنسبة 40-60. حيث والتقرير ينصح باجراء عملية قلب مفتوح وتبديل صمامالابهر مع العلم انها تعاني من مرض السكري وضغط الدمز. العمر65س

- Graph edges included: 5
- Evidence snippets included: 7
- `limited` `0.69404` مرض السكري --HAS_SYMPTOM--> ضغط الدم
- `limited` `0.580792` ضغط الدم --SYMPTOM_OF--> مرض السكري
- `limited` `0.52211` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية
- `limited` `0.463395` ضغط الدم --HAS_NORMAL_RANGE--> 140-80 إذا لا توجد أمراض مصاحبة
- `limited` `0.414657` ضغط --SYMPTOM_OF--> التهاب الجيوب الأنفية

### انا ابتلعت دبوس امس ولا اشعر ببلعه واعاني بوجع صدري كيف اعمل

- Graph edges included: 6
- Evidence snippets included: 6
- `limited` `0.74235` فقر الدم --HAS_SYMPTOM--> تنميل
- `limited` `0.65675` تنميل --SYMPTOM_OF--> فقر الدم
- `limited` `0.558659` دبوس --DIAGNOSED_BY--> أشعة
- `limited` `0.484356` وجع --INVESTIGATED_BY--> اشعة
- `limited` `0.389321` حساسية --DIAGNOSED_BY--> RAST Test

### عندى بقع بنية على جانبى الوجة وانا اعانى من انيميا 10 وكان عندى حصوات بالمرارة وعملت العملية ولا زالت البقع موجودة ما العلاج الاكيد وشكرا

- Graph edges included: 6
- Evidence snippets included: 7
- `strong` `0.84997` فقر الدم --HAS_SYMPTOM--> الم المعدجة
- `medium` `0.796769` فقر الدم --HAS_SYMPTOM--> تنميل
- `medium` `0.78997` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه
- `medium` `0.767427` حساسية الصدر --HAS_SYMPTOM--> سعال
- `medium` `0.763357` التهاب --HAS_SYMPTOM--> الدم

### ماهو البردقوش وهل يوجد باليمن وهل يزيد من عدد الحيوانات المنويه؟

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.792457` الدورة الشهرية --TREATED_BY--> البردقوش
- `medium` `0.79103` التدخين --INVESTIGATED_BY--> الحيوانات المنوية
- `medium` `0.752882` الدورة الشهرية --TREATED_BY--> اكليل الجبل
- `medium` `0.752882` الدورة الشهرية --TREATED_BY--> الميرمية
- `medium` `0.752882` الدورة الشهرية --TREATED_BY--> البقدونس

### اعاني من حموضة وصعوبة في التنفس وصعوبة بلع والم في الجانب الايسر من الصدر مع تعب في الكتف اليسرى بعد ابذال مجهود فهل هذا خطر على القلب ام حموضة عادية

- Graph edges included: 6
- Evidence snippets included: 6
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `medium` `0.78386` التهاب --HAS_SYMPTOM--> تعب
- `medium` `0.78274` تعب --SYMPTOM_OF--> التهاب
- `medium` `0.76938` التهاب --HAS_SYMPTOM--> ضيق تنفس
- `limited` `0.68378` ضيق تنفس --SYMPTOM_OF--> التهاب
- `limited` `0.501166` الكتف --TREATED_BY--> البروفين

### ما هو ابسط علاج لمرض السكر بدون كيماويات؟

- Graph edges included: 6
- Evidence snippets included: 8
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `strong` `0.935862` مرض السكري --HAS_SYMPTOM--> ضغط الدم
- `medium` `0.775002` ضغط الدم --SYMPTOM_OF--> مرض السكري
- `limited` `0.472189` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية
- `limited` `0.413367` التهاب --DIAGNOSED_BY--> تحاليل مخبرية
- `limited` `0.371229` تحاليل مخبرية --DIAGNOSES--> مرض السكري

### انا عملت جراحة فى القلب وتم تغير الصمام المترالى بصمام ميكانيكى صناعى وباخد دواء واريفان ( لسيولة الدم ) 8 ملجرام ومصاب بالانفلوانزا ماالعلاج المناسب

- Graph edges included: 6
- Evidence snippets included: 8
- `limited` `0.456144` ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب
- `limited` `0.392064` ارتفاع ضغط الدم --HAS_SYMPTOM--> ضيق تنفس
- `limited` `0.385728` ارتفاع ضغط الدم --HAS_SYMPTOM--> دوخة
- `limited` `0.380759` مرض السكري --HAS_SYMPTOM--> ضغط الدم
- `limited` `0.370544` خفقان القلب --SYMPTOM_OF--> ارتفاع ضغط الدم

### هل حبوب كريستور(rousovastatin) تؤثر على عضلة القلب ؟

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.774283` فقر الدم --HAS_SYMPTOM--> الم المعدجة
- `medium` `0.774283` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه
- `limited` `0.411345` ضغط الدم --HAS_NORMAL_RANGE--> 140-80 إذا لا توجد أمراض مصاحبة
- `limited` `0.411345` نبض القلب --HAS_NORMAL_RANGE--> 65-85 تقريبا وقد يقبل أقل أو أكثر
- `limited` `0.326683` الم المعدجة --SYMPTOM_OF--> فقر الدم

### هل يوجد أعشاب طبية تساعد على الشفاء من حالة الاكتئاب و الشعور بالخوف ، علما بأنه يوجد لدي فقر دم (انيميا الفول ) و يتجدث حالات الاكتئاب هذه عند تناول...

- Graph edges included: 6
- Evidence snippets included: 8
- `strong` `0.852319` فقر الدم --DIAGNOSED_BY--> تحاليل مخبرية
- `strong` `0.837204` فقر الدم --HAS_SYMPTOM--> الم المعدجة
- `medium` `0.786349` فقر الدم --DIAGNOSED_BY--> فحص تحاليل مخبرية
- `medium` `0.786349` فقر الدم --HAS_SYMPTOM--> تنميل
- `medium` `0.777204` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه

### انا عندى 16 سنة وعندي ارتخاء بالصمام الميترالى والاعراض اللى عندي دوخة لما أقف و بتعب من أقل مجهود , وعند الاستيقاظ هناك ضيق بالتنفس,والدكتورظكاتبلى اندرال 20 جم بس مش...

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.771779` التهاب --HAS_SYMPTOM--> تعب
- `medium` `0.770659` تعب --SYMPTOM_OF--> التهاب
- `medium` `0.769951` ارتفاع ضغط الدم --HAS_SYMPTOM--> خفقان القلب
- `medium` `0.76804` ارتفاع ضغط الدم --HAS_SYMPTOM--> دوخة
- `medium` `0.76692` دوخة --SYMPTOM_OF--> ارتفاع ضغط الدم

### هل هناك اسباب للحساسية من الباراسيتمول وما الاغذية التى امتنع عنها وما هى الاغذية التى ااكلها

- Graph edges included: 6
- Evidence snippets included: 8
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `strong` `0.963166` حساسية --HAS_SYMPTOM--> سعال
- `strong` `0.951844` حساسية --HAS_SYMPTOM--> ضيق تنفس
- `medium` `0.901048` حساسية --HAS_SYMPTOM--> بلغم
- `medium` `0.877474` حساسية --HAS_SYMPTOM--> نشفان
- `medium` `0.843151` حساسية الصدر --HAS_SYMPTOM--> سعال

### كان لدي ارتفاع بسيط في الصفائح ٤٦١ وعندما ولدت بعد ٥٠ يوم التحليل طلع ٦٧٩ واشكو من عدم اكتمال النفس في بعض الاوقات وقال لي الطبيب لديك التهاب في الصدر...

- Graph edges included: 6
- Evidence snippets included: 6
- `limited` `0.505269` صداع --INVESTIGATED_BY--> الصور الشعاعية
- `limited` `0.419669` الصور الشعاعية --INVESTIGATES--> صداع
- `limited` `0.418874` الصدمة الكهربائية --TREATED_BY--> الطبيب
- `limited` `0.418874` الحروق --TREATED_BY--> الطبيب
- `limited` `0.417754` الطبيب --TREATS--> الصدمة الكهربائية

### عمري 18 سنة وأنا أعاني من صغر الثدي هل يوجد أي حل لتكبيره دون جراحة?

- Graph edges included: 6
- Evidence snippets included: 6
- `limited` `0.401988` بيلة الميوغلوبين --TREATED_BY--> السوائل
- `limited` `0.40146` نقص بحجم الثدي --TREATED_BY--> مراجعة اخصائية النسائية
- `limited` `0.40146` نقص بحجم الثدي --DIAGNOSED_BY--> فحص سريري
- `limited` `0.397318` شيب --TREATED_BY--> خلطة الريحان و الروزماري
- `limited` `0.396585` حساسية --DIAGNOSED_BY--> تحليل الحساسية

### عمري ٢٥سنة واعاني من نشاط زائد في الغده الدرقية وقمت بأخذ جرعه من اليود النووي المشع وعندي طفل عمره سنه فما المده الزمنيه المحدده اللتي سأتمكن بعدها

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.772588` مرض الغدة الدرقية --TREATED_BY--> التروكسين
- `limited` `0.671628` التروكسين --TREATS--> مرض الغدة الدرقية
- `limited` `0.415583` نشاط الغدة الدرقية --DIAGNOSED_BY--> تحاليل مخبرية
- `limited` `0.411359` مرض جريفز --DIAGNOSED_BY--> تحاليل مخبرية
- `limited` `0.410588` مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون

### يشعر والدي بألم في منطقة الصدر علما ان والدي مصاب بجلطة قلبية ودماغية اليوم قد تناول بيزا وكانت دسمة،،،،،هل هذا الم قلب ام الام معدة

- Graph edges included: 6
- Evidence snippets included: 6
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `medium` `0.766384` ضرس العقل --HAS_SYMPTOM--> الام
- `medium` `0.765264` الام --SYMPTOM_OF--> ضرس العقل
- `medium` `0.756879` ارتياف دعب \u0627لديم --HAS_SYMPTOM--> الالم
- `medium` `0.7523` ضرس العقل --HAS_SYMPTOM--> صداع
- `limited` `0.671279` الالم --SYMPTOM_OF--> ارتياف دعب \u0627لديم

### هل يوجد تأثير على الجنين في حالة تعاطي أقراص ميزوتاك في بداية الحمل بغرض الإجهاض وأنا الآن اقتنعت باكمال الحمل ولكن قلق من تأثر الجنين بالمادة الفعالة لهذا الدواء؟

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.791231` بريمولوت ن --REQUIRES_MEDICAL_SUPERVISION_FOR--> إيقاف الدواء ومراجعة الطبيب أثناء الحمل
- `limited` `0.55377` عظام الجنين --DEVELOPS_DURING--> نهاية الأسبوع السادس تقريبا
- `limited` `0.544646` الدواء --TREATS--> الملوية البوابية
- `limited` `0.527948` فايروس الكبد --TREATED_BY--> اللقاح
- `limited` `0.522589` الحمل --HAS_SYMPTOM--> قيء

### حموضة في فمي واحساس برائحة تفاح متعفن مع كدمات زرقاء غامقة في قدماي واحساس بغبوش في الرؤية

- Graph edges included: 4
- Evidence snippets included: 4
- `limited` `0.747663` فقر الدم --HAS_SYMPTOM--> الم المعدجة
- `limited` `0.747663` الم المعدجة --INVESTIGATED_BY--> فحص الجرثومة الحلزونية
- `limited` `0.300063` الم المعدجة --SYMPTOM_OF--> فقر الدم
- `limited` `0.300063` فحص الجرثومة الحلزونية --INVESTIGATES--> الم المعدجة

### قمت بعمل اشعة بالصبغة على الاورطى والشرايين الطرفية وجت انتفاخ بالوجه ووجع بالجسم ارجو الافادة

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.904228` وجع --INVESTIGATED_BY--> اشعة
- `medium` `0.898703` انتفاخ --INVESTIGATED_BY--> اشعة
- `medium` `0.818628` اشعة --INVESTIGATES--> وجع
- `medium` `0.813103` اشعة --INVESTIGATES--> انتفاخ
- `medium` `0.762268` التهاب --DIAGNOSED_BY--> اشعة

### ماهي أضرارشجرة القات وماهي منافعها إذا لها فوائد وهل صحيح أنها علاج لمرضى السكر

- Graph edges included: 6
- Evidence snippets included: 8
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `strong` `0.90531` مرض السكري --HAS_SYMPTOM--> ضغط الدم
- `limited` `0.744279` ضغط الدم --SYMPTOM_OF--> مرض السكري
- `limited` `0.502444` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية
- `limited` `0.471323` التهاب --DIAGNOSED_BY--> تحاليل مخبرية
- `limited` `0.401484` تحاليل مخبرية --DIAGNOSES--> مرض السكري

### أعاني من حرقان بكامل بجسمي والتهاب المسالك البوليه وارتفاع الكلسترول والدهون الثلاثيه مال الحل جزاكم الله خير وما قد يكون المسبب

- Graph edges included: 4
- Evidence snippets included: 4
- `medium` `0.754124` الصداع التوتري --HAS_SYMPTOM--> صداع
- `limited` `0.668524` صداع --SYMPTOM_OF--> الصداع التوتري
- `limited` `0.391394` ارتفاع ضغط الدم --TREATED_BY--> العقاقير
- `limited` `0.305794` العقاقير --TREATS--> ارتفاع ضغط الدم

### ماهي علاجات حمى التهاب باطن القدم وباطن اليد وماهي الفحوصات للتاكد من اسباب هذا المرض؟

- Graph edges included: 6
- Evidence snippets included: 6
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `medium` `0.777132` حمى عضة الجرذ --HAS_SYMPTOM--> حمى
- `medium` `0.777132` حمى عضة الفأر --HAS_SYMPTOM--> حمى
- `medium` `0.777132` حمى عضة الجرذون --HAS_SYMPTOM--> حمى
- `medium` `0.776012` حمى --SYMPTOM_OF--> حمى عضة الجرذ
- `medium` `0.776012` حمى --SYMPTOM_OF--> حمى عضة الفأر

### والدي وقع من الدرج قبل ثلالث ايام نلاحظ هناك زغللة في عينه اليمنى مع حول فيها تم قياسة مستوى السكر اليوم 200 اتمنى افادتي بهذا الامر هل له علاقة بالحلطة...

- Graph edges included: 6
- Evidence snippets included: 7
- `strong` `0.902855` مرض السكري --HAS_SYMPTOM--> ضغط الدم
- `medium` `0.78813` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية
- `limited` `0.749896` التهاب --DIAGNOSED_BY--> تحاليل مخبرية
- `limited` `0.32517` تحاليل مخبرية --DIAGNOSES--> مرض السكري
- `limited` `0.319967` ضغط الدم --SYMPTOM_OF--> مرض السكري

### ماهي الاهمية الطبية للجلوكوز والفركتوز والجالكتوز؟

- Graph edges included: 2
- Evidence snippets included: 2
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `medium` `0.820395` التهاب --HAS_SYMPTOM--> اختلال وظائف الكبد
- `limited` `0.734795` اختلال وظائف الكبد --SYMPTOM_OF--> التهاب

### متى يلجأ الدكتور الي نزع عَصّب السن او الضرس

- Graph edges included: 4
- Evidence snippets included: 4
- `limited` `0.429328` حشو الأسنان --NOT_ASSOCIATED_WITH--> غمازة الوجه
- `limited` `0.429328` تخدير موضعي قوي --MAY_TEMPORARILY_AFFECT--> غمازة الوجه
- `limited` `0.420488` برد الأسنان --HAS_RISK--> حساسية الأسنان
- `limited` `0.420488` برد الأسنان --PROCEDURE_DURATION--> جلسة واحدة أو جلستان

### سلام لقد اجريت فحص الهرمون B-HCG ،و نتائج التحاليل كما يللي 3-4 اسبوع 9-130 4-5 اسبوع 75-2600 5-6 اسبوع 850-20800 7-8 اسبوع 4000-100200 7-12 اسبوع 11500-289000 12-16 اسبوع 18300-137000 و...

- Graph edges included: 6
- Evidence snippets included: 6
- `limited` `0.533181` صعوبة التنفس والإرهاق --INVESTIGATED_BY--> التاريخ المرضي والفحص السريري
- `limited` `0.518347` مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون
- `limited` `0.517227` الهرمون --DIAGNOSES--> مرض الغدة الدرقية
- `limited` `0.511424` نقص الصفيحات --DIAGNOSED_BY--> فحص نخاع العظم
- `limited` `0.425824` فحص نخاع العظم --DIAGNOSES--> نقص الصفيحات

### لسلام عليكم ممكن تساعدوني ابني عملتله تطعيم سنة ونص اليوم هو يعاني من ارتفاع الحرارة ومايقدر يحرك رجلو وحتى يوقف وهو كتير البكاء كيف اتعامل معاه كيف اخفف من الم...

- Graph edges included: 5
- Evidence snippets included: 5
- `limited` `0.491956` حمى --TREATED_BY--> خافض حراره
- `limited` `0.415714` حصى الكلى --TREATED_BY--> الإكثار من السوائل والتقييم الطبي
- `limited` `0.406356` خافض حراره --TREATS--> حمى
- `limited` `0.393668` النقص الشديد للصفائح --TREATED_BY--> الروتيكسيماب
- `limited` `0.308068` الروتيكسيماب --TREATS--> النقص الشديد للصفائح

### هل زيت نبات الميرمية له آثار جانبية عند تناوله بشكل 3 كبسولات قبل الطعام للتخلص من افراز البرولاكتين المفرز والناتج عن ورم حميد في الغدة النخامية . .

- Graph edges included: 6
- Evidence snippets included: 6
- `limited` `0.436585` الدورة الشهرية --TREATED_BY--> الميرمية
- `limited` `0.435465` الميرمية --TREATS--> الدورة الشهرية
- `limited` `0.413108` مرض الغدة الدرقية --TREATED_BY--> التروكسين
- `limited` `0.413108` مرض الغدة الدرقية --DIAGNOSED_BY--> الهرمون
- `limited` `0.401897` الجوع --TREATED_BY--> الطعام

### عندي الم في منطقه البطن مع الم بصدر جهه اليمين الى الرقبه وماقدرت اعرف تفسير الالم ذا من ايش او سببه مع وجود احيان ضيق بالتنفس ،،،، افيدوني

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.774655` ارتياف دعب \u0627لديم --HAS_SYMPTOM--> الالم
- `medium` `0.773535` الالم --SYMPTOM_OF--> ارتياف دعب \u0627لديم
- `medium` `0.755915` فقر الدم --HAS_SYMPTOM--> الم المعدجة
- `limited` `0.670315` الم المعدجة --SYMPTOM_OF--> فقر الدم
- `limited` `0.405299` الجلد المترهل --TREATED_BY--> الجراحة التجميلية

## Output Files

- Context bundles JSON: `outputs/05_trial_graph_v1/context_construction/trial_graph_v1_context_bundles.json`
- Context bundles CSV: `outputs/05_trial_graph_v1/context_construction/trial_graph_v1_context_bundles.csv`
- LLM prompts JSON: `outputs/05_trial_graph_v1/context_construction/trial_graph_v1_llm_prompts.json`
- LLM prompts JSONL: `outputs/05_trial_graph_v1/context_construction/trial_graph_v1_llm_prompts.jsonl`
- LLM prompts Markdown: `outputs/05_trial_graph_v1/context_construction/trial_graph_v1_llm_prompts.md`

## Next Step From Mix.png

Continue to Step 12: LLM generation using only these evidence-focused context bundles.
