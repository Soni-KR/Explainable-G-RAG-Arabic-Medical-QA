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

### ما علاج حساسية الصدر مع السعال والبلغم؟

- `0.895918` حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين (matches primary intent; has original/direct edge support; strong semantic support)
- `0.881568` حساسية --TREATED_BY--> مضاد الهيستامين (matches primary intent; has original/direct edge support; strong semantic support)
- `0.881568` حساسية --TREATED_BY--> كورتيزون (matches primary intent; has original/direct edge support; strong semantic support)
- `0.881568` حساسية --TREATED_BY--> تيليفاست (matches primary intent; has original/direct edge support; strong semantic support)
- `0.867218` حساسية --TREATED_BY--> حليب مكسر بروتين الحليب (matches primary intent; has original/direct edge support; strong semantic support)
- `0.867218` حساسية --TREATED_BY--> نازونكس (matches primary intent; has original/direct edge support; strong semantic support)
- `0.852868` حساسية --TREATED_BY--> زيت الحبة السوداء (matches primary intent; has original/direct edge support; strong semantic support)
- `0.790854` ربو --TREATED_BY--> زيت الحبة السوداء (matches primary intent; has original/direct edge support; strong semantic support)

### عندي كحة وبلغم هل هذا ربو؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.921824` ربو --HAS_SYMPTOM--> سعال (matches primary intent; has original/direct edge support; strong semantic support)
- `0.919358` ربو --HAS_SYMPTOM--> بلغم (matches primary intent; has original/direct edge support; strong semantic support)
- `0.826558` بلغم --SYMPTOM_OF--> حساسية (matches primary intent; strong semantic support)
- `0.826558` بلغم --SYMPTOM_OF--> ربو (matches primary intent; strong semantic support)
- `0.817948` بلغم --SYMPTOM_OF--> التهاب (matches primary intent; strong semantic support)
- `0.758033` سعال --SYMPTOM_OF--> حساسية (matches primary intent; 2 evidence rows; strong semantic support)
- `0.736774` سعال --SYMPTOM_OF--> ربو (matches primary intent; strong semantic support)
- `0.733326` سعال --SYMPTOM_OF--> حساسية الصدر (matches primary intent; strong semantic support)

### ما التحاليل المناسبة لفقر الدم؟

- `0.936139` فقر الدم --DIAGNOSED_BY--> تحاليل مخبرية (matches primary intent; 2 evidence rows; has original/direct edge support; strong semantic support)
- `0.896522` فقر الدم --DIAGNOSED_BY--> فحص تحاليل مخبرية (matches primary intent; has original/direct edge support; strong semantic support)
- `0.637189` فقر الدم --HAS_SYMPTOM--> الم المعدجة (2 evidence rows; has original/direct edge support; strong semantic support)
- `0.610522` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه (has original/direct edge support; strong semantic support)
- `0.610522` فقر الدم --HAS_SYMPTOM--> تنميل (has original/direct edge support; strong semantic support)

### ما أسباب صداع مع دوخة؟

- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.

- `0.843207` صداع --SYMPTOM_OF--> التهاب السحايا (matches primary intent; strong semantic support)
- `0.828857` صداع --SYMPTOM_OF--> التهاب الجيوب الأنفية (matches primary intent; strong semantic support)
- `0.828857` صداع --SYMPTOM_OF--> الصداع التوتري (matches primary intent; strong semantic support)
- `0.814507` صداع --SYMPTOM_OF--> ضرس العقل (matches primary intent; strong semantic support)
- `0.801073` دوخة --SYMPTOM_OF--> ارتفاع ضغط الدم (matches primary intent; strong semantic support)
- `0.621307` صداع --TREATED_BY--> زيت الحبة السوداء (has original/direct edge support; strong semantic support)
- `0.621307` صداع --TREATED_BY--> المراجعة الطبية (has original/direct edge support; strong semantic support)
- `0.621307` صداع --TREATED_BY--> باندول فولت فاست (has original/direct edge support; strong semantic support)

### ما علاج الجلطة الدماغية؟

- `0.908257` الجلطة الدماغية --TREATED_BY--> الأسبرين (matches primary intent; has original/direct edge support; strong semantic support)

### هل ضيق التنفس من أعراض الحساسية؟

- `0.955363` حساسية --HAS_SYMPTOM--> سعال (matches primary intent; 2 evidence rows; has original/direct edge support; strong semantic support)
- `0.950183` حساسية --HAS_SYMPTOM--> ضيق تنفس (matches primary intent; 2 evidence rows; has original/direct edge support; strong semantic support)
- `0.924916` حساسية --HAS_SYMPTOM--> بلغم (matches primary intent; has original/direct edge support; strong semantic support)
- `0.924916` حساسية --HAS_SYMPTOM--> نشفان (matches primary intent; has original/direct edge support; strong semantic support)
- `0.878062` حساسية الصدر --HAS_SYMPTOM--> سعال (matches primary intent; has original/direct edge support; strong semantic support)
- `0.820483` ضيق تنفس --SYMPTOM_OF--> حساسية (matches primary intent; 2 evidence rows; strong semantic support)
- `0.798643` ضيق تنفس --SYMPTOM_OF--> ارتفاع ضغط الدم (matches primary intent; 2 evidence rows; strong semantic support)
- `0.774847` ضيق تنفس --SYMPTOM_OF--> التهاب (matches primary intent; strong semantic support)

### ما الفحوصات المطلوبة للسكري؟

- `0.85875` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية (matches primary intent; has original/direct edge support; strong semantic support)
- `0.781924` الفحوصات المخبرية --INVESTIGATES--> انقطاع الطمث (matches primary intent; strong semantic support)
- `0.55` مرض السكري --HAS_SYMPTOM--> ضغط الدم (3 evidence rows; has original/direct edge support)

### ما علاج التهاب المفاصل وألم المفاصل؟

- `0.779318` التهاب المفاصل --HAS_SYMPTOM--> ألم المفاصل (has original/direct edge support; strong semantic support)
- `0.686518` ألم المفاصل --SYMPTOM_OF--> التهاب المفاصل (strong semantic support)

## Output Files

- Reranked subgraphs JSON: `outputs/05_trial_graph_v1/subgraph_reranking/trial_graph_v1_reranked_subgraphs.json`
- Reranked relations CSV: `outputs/05_trial_graph_v1/subgraph_reranking/trial_graph_v1_reranked_relations.csv`
- Reranked evidence CSV: `outputs/05_trial_graph_v1/subgraph_reranking/trial_graph_v1_reranked_evidence.csv`

## Next Step From Mix.png

Continue to Step 11: evidence-focused context construction from the reranked subgraphs.
