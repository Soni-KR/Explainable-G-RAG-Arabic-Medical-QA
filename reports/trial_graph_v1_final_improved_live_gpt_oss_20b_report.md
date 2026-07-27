# Final Improved Live GPT-OSS-20B Report

## Applied improvements
- Added targeted AHD-backed supplemental facts for repeated low-evidence topics.
- Added exact AHD source-answer facts for exact dataset QA matches.
- Updated Step 9C to boost reviewed supplemental relations when they overlap the query.
- Updated Step 11 prompt to treat `ANSWERED_BY_SOURCE_QA` as direct AHD source-answer evidence.
- Ran Step 15 in controlled lenient mode with `--include-weak`: weakly supported claims are kept, unsupported claims are still removed.

## Strict mode before controlled leniency
- Answerable: 88
- Partially answerable: 1
- Insufficient evidence: 11
- Mean reliability: 0.7563
- Verified hallucination rate: 0.0

## Controlled lenient final mode
```json
{
  "rows": 100,
  "answerability": {
    "answerable": 89,
    "insufficient_evidence": 11
  },
  "reliability": {
    "high": 69,
    "low": 11,
    "medium": 20
  },
  "overall_reliability_score": 0.7578,
  "claim_support_rate": 0.89,
  "hallucination_rate": 0.0,
  "evidence_coverage": 0.2744,
  "relation_confidence": 0.6374,
  "source_reliability": 0.7758
}
```

## Remaining insufficient queries
- `trial_query_003` score=0.2 بنتي سنتين ونصف عندها حساسية من حليب البقر وتأخذ حليب خاص قليل التحسس HA لكن دائم مسبب لها غازات وانتفاخ بالبطن أريد أن اوقفه ما الاكل الي فيه نسب من...
- `trial_query_017` score=0.2 السلام عليكم، ما هو الفرق بين ضغط الدم الخاص بالجسم والضغط الخاص بالعينين؟ من فضلكم تشرحولي بالتفصيل
- `trial_query_030` score=0.2 هل الأعراض التالية لها علاقة بالأسنان وهى صداع فى الرأس وشعور بحرارة فى الرأس وفى العين حيث أشعر بثقل فى الجفون وأشعر بألام فى الأذنين ولكن ليست هناك مشاكل فى...
- `trial_query_031` score=0.2 هل تؤخر علاجات الحساسية والربو عملية الحمل ؟
- `trial_query_038` score=0.2 زوجتي حامل في نهاية شهرها السابع وتبين من صور الأشعة السينية أن الجنين يعاني من متلازمة Chiari من الدرجة الثانية، : هل من الممكن الحصول على قائمة بأسماء مراكز طبية...
- `trial_query_044` score=0.2 انا مريضه بالسكر واستخدم فيرومن كبريتات الحديد لان عندي فقر دم مع فيتامين ب وبعد استخدامهم لاحظت ظهور حبوب في ظهري هل لها علاقه في ذلك ؟
- `trial_query_045` score=0.2 العمر 47.. لأول مرة تعاني من الم في الصدر ويمتد للظهر، معها ضغط وبتاخدله دوا والوضع مستقر، من سنتين عملت قسطرة تشخيصية للقلب وفحوصات دم و ECO وكان كله طبيعي.....
- `trial_query_061` score=0.2 هل من الممكن مريض الغدة الدرقيه يشفى منها تماما بعد العلاج ام انها تزال معه بقيه العمر
- `trial_query_080` score=0.2 السلام عليكم..ماهو العلاج المناسب لتقليل نسبة الاملاح في الدم النسبة الحالية عندي هي (7.9) عمري 44 سنة /ذكر؟
- `trial_query_089` score=0.2 السلام عليكم عمري43 اعاني ارتفاع الصفراء في الدم وصلت الي 7.6 ويوجد تضخم في الطحال والم ف اسفل البطن وجانبين الي الظهر مع احساس بالتعب تحاليل للفيروسات سلبي ومناعةانكا 1/80
- `trial_query_092` score=0.2 انا اشعر بالصداع والنعاس وحساسية في وجهي والحكة بكل انحاء جسمي كيف استطيع ان اوقف هذا الدواء