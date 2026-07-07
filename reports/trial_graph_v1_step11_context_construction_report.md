# Trial Graph v1 Step 11 Evidence-Focused Context Construction Report

This step converts Step 10 reranked subgraphs into compact evidence bundles for later LLM answer generation.
It still does not generate medical answers.

## Context Rules

- Keep graph relation, rerank score, and reliability label
- Attach source Q&A evidence snippets
- Preserve Step 8 warnings, especially missing CAUSES relation warnings
- Enforce a simple character budget so prompts can stay controllable

## Query Context Summary

### ما علاج حساسية الصدر مع السعال والبلغم؟

- Graph edges included: 6
- Evidence snippets included: 6
- `medium` `0.895918` حساسية --TREATED_BY--> تجنب المنتجات التي تحوي جلوتين
- `medium` `0.881568` حساسية --TREATED_BY--> مضاد الهيستامين
- `medium` `0.881568` حساسية --TREATED_BY--> كورتيزون
- `medium` `0.881568` حساسية --TREATED_BY--> تيليفاست
- `medium` `0.867218` حساسية --TREATED_BY--> حليب مكسر بروتين الحليب

### عندي كحة وبلغم هل هذا ربو؟

- Graph edges included: 6
- Evidence snippets included: 7
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `medium` `0.921824` ربو --HAS_SYMPTOM--> سعال
- `medium` `0.919358` ربو --HAS_SYMPTOM--> بلغم
- `medium` `0.826558` بلغم --SYMPTOM_OF--> حساسية
- `medium` `0.826558` بلغم --SYMPTOM_OF--> ربو
- `medium` `0.817948` بلغم --SYMPTOM_OF--> التهاب

### ما التحاليل المناسبة لفقر الدم؟

- Graph edges included: 5
- Evidence snippets included: 7
- `strong` `0.936139` فقر الدم --DIAGNOSED_BY--> تحاليل مخبرية
- `medium` `0.896522` فقر الدم --DIAGNOSED_BY--> فحص تحاليل مخبرية
- `limited` `0.637189` فقر الدم --HAS_SYMPTOM--> الم المعدجة
- `limited` `0.610522` فقر الدم --HAS_SYMPTOM--> فقدان الشهيه
- `limited` `0.610522` فقر الدم --HAS_SYMPTOM--> تنميل

### ما أسباب صداع مع دوخة؟

- Graph edges included: 6
- Evidence snippets included: 6
- Warning: Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation.
- `medium` `0.843207` صداع --SYMPTOM_OF--> التهاب السحايا
- `medium` `0.828857` صداع --SYMPTOM_OF--> التهاب الجيوب الأنفية
- `medium` `0.828857` صداع --SYMPTOM_OF--> الصداع التوتري
- `medium` `0.814507` صداع --SYMPTOM_OF--> ضرس العقل
- `medium` `0.801073` دوخة --SYMPTOM_OF--> ارتفاع ضغط الدم

### ما علاج الجلطة الدماغية؟

- Graph edges included: 1
- Evidence snippets included: 1
- `medium` `0.908257` الجلطة الدماغية --TREATED_BY--> الأسبرين

### هل ضيق التنفس من أعراض الحساسية؟

- Graph edges included: 6
- Evidence snippets included: 9
- `strong` `0.955363` حساسية --HAS_SYMPTOM--> سعال
- `strong` `0.950183` حساسية --HAS_SYMPTOM--> ضيق تنفس
- `medium` `0.924916` حساسية --HAS_SYMPTOM--> بلغم
- `medium` `0.924916` حساسية --HAS_SYMPTOM--> نشفان
- `medium` `0.878062` حساسية الصدر --HAS_SYMPTOM--> سعال

### ما الفحوصات المطلوبة للسكري؟

- Graph edges included: 3
- Evidence snippets included: 4
- `medium` `0.85875` مرض السكري --DIAGNOSED_BY--> تحاليل مخبرية
- `medium` `0.781924` الفحوصات المخبرية --INVESTIGATES--> انقطاع الطمث
- `limited` `0.55` مرض السكري --HAS_SYMPTOM--> ضغط الدم

### ما علاج التهاب المفاصل وألم المفاصل؟

- Graph edges included: 2
- Evidence snippets included: 2
- `medium` `0.779318` التهاب المفاصل --HAS_SYMPTOM--> ألم المفاصل
- `limited` `0.686518` ألم المفاصل --SYMPTOM_OF--> التهاب المفاصل

## Output Files

- Context bundles JSON: `outputs/05_trial_graph_v1/context_construction/trial_graph_v1_context_bundles.json`
- Context bundles CSV: `outputs/05_trial_graph_v1/context_construction/trial_graph_v1_context_bundles.csv`

## Next Step From Mix.png

Continue to Step 12: LLM generation using only these evidence-focused context bundles.
