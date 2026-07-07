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

### ما علاج حساسية الصدر مع السعال والبلغم؟

**Top hybrid graph relations**
- `0.938111` حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين (seed=حساسية, relation_weight=1.0)
- `0.920611` حساسية --TREATED_BY--> مضاد الهيستامين (seed=حساسية, relation_weight=1.0)
- `0.920611` حساسية --TREATED_BY--> كورتيزون (seed=حساسية, relation_weight=1.0)
- `0.920611` حساسية --TREATED_BY--> تيليفاست (seed=حساسية, relation_weight=1.0)
- `0.903111` حساسية --TREATED_BY--> حليب مكسر بروتين الحليب (seed=حساسية, relation_weight=1.0)
- `0.903111` حساسية --TREATED_BY--> نازونكس (seed=حساسية, relation_weight=1.0)
- `0.885611` حساسية --TREATED_BY--> زيت الحبة السوداء (seed=حساسية, relation_weight=1.0)
- `0.823924` حساسية الصدر --HAS_SYMPTOM--> سعال (seed=حساسية الصدر, relation_weight=0.4)

**Top context bundle**
- `graph_relation` `0.938111` حساسية TREATED_BY تجنب المنتجات التي تحوي جلوتين
- `graph_relation` `0.920611` حساسية TREATED_BY مضاد الهيستامين
- `graph_relation` `0.920611` حساسية TREATED_BY كورتيزون
- `graph_relation` `0.920611` حساسية TREATED_BY تيليفاست
- `graph_relation` `0.903111` حساسية TREATED_BY حليب مكسر بروتين الحليب
- `graph_relation` `0.903111` حساسية TREATED_BY نازونكس

### عندي كحة وبلغم هل هذا ربو؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.969704` ربو --HAS_SYMPTOM--> سعال (seed=ربو, relation_weight=1.0)
- `0.966697` ربو --HAS_SYMPTOM--> بلغم (seed=ربو, relation_weight=1.0)
- `0.926697` بلغم --SYMPTOM_OF--> حساسية (seed=بلغم, relation_weight=1.0)
- `0.926697` بلغم --SYMPTOM_OF--> ربو (seed=بلغم, relation_weight=1.0)
- `0.916197` بلغم --SYMPTOM_OF--> التهاب (seed=بلغم, relation_weight=1.0)
- `0.817204` سعال --SYMPTOM_OF--> ربو (seed=سعال, relation_weight=1.0)
- `0.812999` سعال --SYMPTOM_OF--> حساسية (seed=سعال, relation_weight=1.0)
- `0.812999` سعال --SYMPTOM_OF--> حساسية الصدر (seed=سعال, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.969704` ربو HAS_SYMPTOM سعال
- `graph_relation` `0.966697` ربو HAS_SYMPTOM بلغم
- `graph_relation` `0.926697` بلغم SYMPTOM_OF حساسية
- `graph_relation` `0.926697` بلغم SYMPTOM_OF ربو
- `graph_relation` `0.916197` بلغم SYMPTOM_OF التهاب
- `graph_relation` `0.817204` سعال SYMPTOM_OF ربو

### ما التحاليل المناسبة لفقر الدم؟

**Top hybrid graph relations**
- `0.956348` فقر الدم --DIAGNOSED_BY--> تحاليل مخبرية (seed=فقر الدم, relation_weight=1.0)
- `0.938848` فقر الدم --DIAGNOSED_BY--> تحاليل مخبرية (seed=فقر الدم, relation_weight=1.0)
- `0.938848` فقر الدم --DIAGNOSED_BY--> فحص تحاليل مخبرية (seed=فقر الدم, relation_weight=1.0)
- `0.638848` فقر الدم --HAS_SYMPTOM--> الم المعدجة (seed=فقر الدم, relation_weight=-0.2)
- `0.638848` فقر الدم --HAS_SYMPTOM--> الم المعدجة (seed=فقر الدم, relation_weight=-0.2)
- `0.638848` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (seed=فقر الدم, relation_weight=-0.2)
- `0.638848` فقر الدم --HAS_SYMPTOM--> تنميل (seed=فقر الدم, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.956348` فقر الدم DIAGNOSED_BY تحاليل مخبرية
- `graph_relation` `0.938848` فقر الدم DIAGNOSED_BY تحاليل مخبرية
- `graph_relation` `0.938848` فقر الدم DIAGNOSED_BY فحص تحاليل مخبرية
- `graph_relation` `0.638848` فقر الدم HAS_SYMPTOM الم المعدجة
- `graph_relation` `0.638848` فقر الدم HAS_SYMPTOM الم المعدجة
- `graph_relation` `0.638848` فقر الدم HAS_SYMPTOM فقدان الشهيه

### ما أسباب صداع مع دوخة؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

**Top hybrid graph relations**
- `0.947` صداع --SYMPTOM_OF--> التهاب السحايا (seed=صداع, relation_weight=1.0)
- `0.9295` صداع --SYMPTOM_OF--> التهاب الجيوب الأنفية (seed=صداع, relation_weight=1.0)
- `0.9295` صداع --SYMPTOM_OF--> الصداع التوتري (seed=صداع, relation_weight=1.0)
- `0.912` صداع --SYMPTOM_OF--> ضرس العقل (seed=صداع, relation_weight=1.0)
- `0.895617` دوخة --SYMPTOM_OF--> ارتفاع ضغط الدم (seed=دوخة, relation_weight=1.0)
- `0.652` صداع --TREATED_BY--> زيت الحبة السوداء (seed=صداع, relation_weight=-0.2)
- `0.652` صداع --TREATED_BY--> المراجعة الطبية (seed=صداع, relation_weight=-0.2)
- `0.652` صداع --TREATED_BY--> باندول فولت فاست (seed=صداع, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.947` صداع SYMPTOM_OF التهاب السحايا
- `graph_relation` `0.9295` صداع SYMPTOM_OF التهاب الجيوب الأنفية
- `graph_relation` `0.9295` صداع SYMPTOM_OF الصداع التوتري
- `graph_relation` `0.912` صداع SYMPTOM_OF ضرس العقل
- `graph_relation` `0.895617` دوخة SYMPTOM_OF ارتفاع ضغط الدم
- `graph_relation` `0.652` صداع TREATED_BY زيت الحبة السوداء

### ما علاج الجلطة الدماغية؟

**Top hybrid graph relations**
- `0.953159` الجلطة الدماغية --TREATED_BY--> الأسبرين (seed=الجلطة الدماغية, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.953159` الجلطة الدماغية TREATED_BY الأسبرين
- `semantic_evidence` `0.630443` قلق
- `semantic_evidence` `0.622356` دواء تلفاست أ سيرين
- `semantic_evidence` `0.594745` التهاب
- `semantic_evidence` `0.592861` المراجعة الطبية
- `semantic_evidence` `0.590627` التهاب

### هل ضيق التنفس من أعراض الحساسية؟

**Top hybrid graph relations**
- `0.980475` حساسية --HAS_SYMPTOM--> سعال (seed=حساسية, relation_weight=1.0)
- `0.973475` حساسية --HAS_SYMPTOM--> بلغم (seed=حساسية, relation_weight=1.0)
- `0.973475` حساسية --HAS_SYMPTOM--> نشفان (seed=حساسية, relation_weight=1.0)
- `0.973475` حساسية --HAS_SYMPTOM--> ضيق تنفس (seed=حساسية, relation_weight=1.0)
- `0.955975` حساسية --HAS_SYMPTOM--> ضيق تنفس (seed=حساسية, relation_weight=1.0)
- `0.955975` حساسية --HAS_SYMPTOM--> سعال (seed=حساسية, relation_weight=1.0)
- `0.916336` حساسية الصدر --HAS_SYMPTOM--> سعال (seed=حساسية الصدر, relation_weight=1.0)
- `0.888475` ضيق تنفس --SYMPTOM_OF--> حساسية (seed=ضيق تنفس, relation_weight=1.0)

**Top context bundle**
- `graph_relation` `0.980475` حساسية HAS_SYMPTOM سعال
- `graph_relation` `0.973475` حساسية HAS_SYMPTOM بلغم
- `graph_relation` `0.973475` حساسية HAS_SYMPTOM نشفان
- `graph_relation` `0.973475` حساسية HAS_SYMPTOM ضيق تنفس
- `graph_relation` `0.955975` حساسية HAS_SYMPTOM ضيق تنفس
- `graph_relation` `0.955975` حساسية HAS_SYMPTOM سعال

### ما الفحوصات المطلوبة للسكري؟

**Top hybrid graph relations**
- `0.892784` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (seed=مرض السكري, relation_weight=1.0)
- `0.872265` الفحوصات المخبرية --INVESTIGATES--> انقطاع الطمث (seed=الفحوصات المخبرية, relation_weight=1.0)
- `0.5` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=-0.2)
- `0.5` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=-0.2)
- `0.5` مرض السكري --HAS_SYMPTOM--> ضغط الدم (seed=مرض السكري, relation_weight=-0.2)

**Top context bundle**
- `graph_relation` `0.892784` مرض السكري DIAGNOSED_BY تحاليل مخبرية
- `graph_relation` `0.872265` الفحوصات المخبرية INVESTIGATES انقطاع الطمث
- `graph_relation` `0.5` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.5` مرض السكري HAS_SYMPTOM ضغط الدم
- `graph_relation` `0.5` مرض السكري HAS_SYMPTOM ضغط الدم
- `semantic_evidence` `0.701555` سكري

### ما علاج التهاب المفاصل وألم المفاصل؟

**Top hybrid graph relations**
- `0.825185` التهاب المفاصل --HAS_SYMPTOM--> ألم المفاصل (seed=التهاب المفاصل, relation_weight=0.4)
- `0.785185` ألم المفاصل --SYMPTOM_OF--> التهاب المفاصل (seed=ألم المفاصل, relation_weight=0.4)

**Top context bundle**
- `graph_relation` `0.825185` التهاب المفاصل HAS_SYMPTOM ألم المفاصل
- `graph_relation` `0.785185` ألم المفاصل SYMPTOM_OF التهاب المفاصل
- `semantic_evidence` `0.754338` ألم المفاصل
- `semantic_evidence` `0.661465` التهاب المفاصل
- `semantic_evidence` `0.656208` التهاب المفاصل
- `semantic_evidence` `0.637074` ألم المفاصل

## Output Files

- Hybrid retrieval JSON: `outputs/05_trial_graph_v1/hybrid_retrieval/trial_graph_v1_hybrid_retrieval_results.json`
- Hybrid relations CSV: `outputs/05_trial_graph_v1/hybrid_retrieval/trial_graph_v1_hybrid_retrieval_relations.csv`
- Hybrid contexts CSV: `outputs/05_trial_graph_v1/hybrid_retrieval/trial_graph_v1_hybrid_retrieval_contexts.csv`

## Next Step From Mix.png

Continue to Step 10: subgraph reranking, using these hybrid relation/context candidates.
