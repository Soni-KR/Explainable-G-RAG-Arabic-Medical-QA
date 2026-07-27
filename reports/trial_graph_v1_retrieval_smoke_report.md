# Trial Graph v1 Retrieval Smoke Report

This tests graph retrieval over the frozen CSV export before Neo4j answer generation.

## Summary

- q01_allergy_treatments `ok`: Treatments connected to حساسية -> 7 results; expected hits: كورتيزون, مضاد الهيستامين, نازونكس
- q02_allergy_symptoms `ok`: Symptoms connected to حساسية -> 6 results; expected hits: بلغم, سعال
- q03_allergy_tests `ok`: Tests connected to حساسية -> 5 results; expected hits: RAST Test, تحاليل مخبرية, تحليل الحساسية
- q04_anemia_tests `ok`: Tests connected to فقر الدم -> 3 results; expected hits: تحاليل مخبرية
- q05_headache_diseases `ok`: Diseases connected to صداع -> 4 results; expected hits: none checked/found
- q06_stroke_treatments `ok`: Treatments connected to الجلطة الدماغية -> 1 results; expected hits: none checked/found
- q07_arthritis_symptoms `ok`: Symptoms connected to التهاب المفاصل -> 1 results; expected hits: ألم المفاصل

## Output

- Retrieval smoke results: `outputs/05_trial_graph_v1/trial_graph_v1_retrieval_smoke_results.csv`

## Notes

- `needs_review` can mean the graph lacks that concept in this small trial, not necessarily that the pipeline is broken.
- Use this before scaling Step 3/Step 4 to decide whether relation types and directions are useful.
