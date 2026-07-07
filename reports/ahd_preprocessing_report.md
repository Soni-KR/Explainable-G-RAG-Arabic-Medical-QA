# AHD Step 1 Preprocessing and Medical Normalization

## What was produced

- Input: `outputs/01_preprocessing/ahd_subset_5000_clean.csv`
- Output: `outputs/01_preprocessing/ahd_subset_5000_preprocessed.csv`
- Medical weak-hint dictionary: `outputs/01_preprocessing/ahd_medical_normalization_terms.csv`

## Processing performed

1. Preserved the original cleaned Arabic `question` and `answer` columns from the 5k subset.
2. Added `category_en` from the AHD category distribution file when a translation exists.
3. Added normalized Arabic fields for matching: `question_norm`, `answer_norm`, and `qa_text_norm`.
4. Removed Arabic diacritics and tatweel, normalized Arabic/Persian digits, standardized punctuation, and unified common Arabic letter variants.
5. Added `split` for evaluation-safe separation: `graph_train`, `validation`, and `eval_test`.
6. Added text length columns: `question_char_len`, `answer_char_len`, and `qa_char_len`.
7. Added dictionary-based weak medical hints. These are not final graph entities; final entities must come from Step 3 LLM extraction.

## Split Policy

The split is stratified by category as much as possible. Use `graph_train` rows to build the graph. Use `validation` for prompt tuning and design checks. Keep `eval_test` held back for final evaluation so the system is not evaluated on the same rows used to build the graph.

## Dictionary Hint Policy

Dictionary hints are deliberately weak. Broad variants such as pressure, test, heart, colon, or pregnancy-related terms can be context-sensitive, so they should guide chunking and LLM prompts only, not become final graph nodes.

## Summary

- Rows processed: 5000
- Categories represented: 90
- Rows with English category label: 5000
- Rows with at least one weak medical hint: 2728
- Unique weak hint concepts: 33

## Split Counts

- graph_train: 4000
- validation: 500
- eval_test: 500

## Category Coverage By Split

- graph_train categories: 90
- validation categories: 87
- eval_test categories: 87

## Length Statistics

- Average question length: 109.34 chars
- Average answer length: 216.21 chars
- Average QA length: 325.55 chars
- Max answer length: 11167 chars
- Rows with answers over 2500 chars: 21

## Example transformations

### Example 1

- `subset_id`: `ahd5k_00001`
- Split: graph_train
- Category: الأمراض الجنسية / Sexual
- Original question: اجريت فحص السائل المنوي و كانت النتائج كالتالي : عدد الحيوانات المنوية 90 مليون الحركة 50% الطبيعية 5% غير الطبيعي 95% ما احتمالية الحمل و هل انا مريض و ماذا...
- Normalized question: اجريت فحص السايل المنوي و كانت النتايج كالتالي : عدد الحيوانات المنويه 90 مليون الحركه 50% الطبيعيه 5% غير الطبيعي 95% ما احتماليه الحمل و هل انا مريض و ماذا.
- Weak medical hints: [{"canonical": "الحمل", "type": "condition", "matched_variant": "الحمل", "hint_strength": "weak", "final_graph_entity": false}]

### Example 2

- `subset_id`: `ahd5k_00004`
- Split: graph_train
- Category: جراحة نسائية / Gynaecological surgery
- Original question: هل ما حدث لى بعد الولادة طبيعى لقد ولدت قيصرى وبعد اسبوع من الولادة حدث لى نزيف مفاجىء مع نزول قطع دم متجمدة واخذت حبوب لوقف النزيف وتم يقافه اريد...
- Normalized question: هل ما حدث لي بعد الولاده طبيعي لقد ولدت قيصري وبعد اسبوع من الولاده حدث لي نزيف مفاجيء مع نزول قطع دم متجمده واخذت حبوب لوقف النزيف وتم يقافه اريد.
- Weak medical hints: [{"canonical": "دواء", "type": "treatment", "matched_variant": "حبوب", "hint_strength": "weak", "final_graph_entity": false}, {"canonical": "الحمل", "type": "condition", "matched_variant": "الولاده", "hint_strength": "weak", "final_graph_entity": false}]

### Example 3

- `subset_id`: `ahd5k_00007`
- Split: graph_train
- Category: صحة المرأة / Women's health
- Original question: انا بنت وقبل الدوره بيومين او ثلاث تجيني افرازات بنيه ومرات معها خمول والم طفيف ثم تجي الدوره ويجي ألمها صار لي ٤ شهور وهذا الحاله تجي قبل دورتي ،...
- Normalized question: انا بنت وقبل الدوره بيومين او ثلاث تجيني افرازات بنيه ومرات معها خمول والم طفيف ثم تجي الدوره ويجي المها صار لي 4 شهور وهذا الحاله تجي قبل دورتي ,.
- Weak medical hints: [{"canonical": "دواء", "type": "treatment", "matched_variant": "ادويه", "hint_strength": "weak", "final_graph_entity": false}]

### Example 4

- `subset_id`: `ahd5k_00008`
- Split: graph_train
- Category: علم الأجنة / Embryology
- Original question: انا مصاب بمرض بهجت واعاني من الامه بالجسم ،ولم يصيب العين حتى الان فماهي افضل طرق الوقايه حتى لا يصل الى العين؟
- Normalized question: انا مصاب بمرض بهجت واعاني من الامه بالجسم ,ولم يصيب العين حتي الان فماهي افضل طرق الوقايه حتي لا يصل الي العين?
- Weak medical hints: [{"canonical": "التهاب", "type": "condition", "matched_variant": "التهاب", "hint_strength": "weak", "final_graph_entity": false}]

### Example 5

- `subset_id`: `ahd5k_00009`
- Split: graph_train
- Category: أنف، أذن وحنجرة / Nose, ear and throat
- Original question: مرحبا عندي طفلة بجيل سنه و٣ اشهر ولديها ضعف سمع عالي عن طريق طبيب للعلاج البديل تلقت ادويه مثل غداء ملكات وحتى الان حصل تطور صغير جدا هل يمكن مساعده
- Normalized question: مرحبا عندي طفله بجيل سنه و3 اشهر ولديها ضعف سمع عالي عن طريق طبيب للعلاج البديل تلقت ادويه مثل غداء ملكات وحتي الان حصل تطور صغير جدا هل يمكن مساعده
- Weak medical hints: [{"canonical": "دواء", "type": "treatment", "matched_variant": "ادويه", "hint_strength": "weak", "final_graph_entity": false}]
