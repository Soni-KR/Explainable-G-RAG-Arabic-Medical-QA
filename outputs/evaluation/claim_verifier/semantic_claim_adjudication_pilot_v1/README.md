# Semantic Claim Adjudication Pilot v1

## Scope

This is a restricted development pilot for Step 14. It is not a production
result and does not cover all 81 human-reviewed claims.

- Queries sent: 12
- Claims sent: 18
- Human-retain claims: 10
- Human-remove claims: 8
- Model: `openai/gpt-oss-20b`
- Feature default: disabled

The outbound payload contained only each Arabic question, disputed claim, and
cited evidence segments. Human labels, expected decisions, reference answers,
database identifiers, unrelated rows, credentials, and personal identifiers
were excluded.

## Initial Result

| Measure | Result |
|---|---:|
| TP / TN / FP / FN | 10 / 3 / 5 / 0 |
| Accuracy | 0.722222 |
| Retain precision | 0.666667 |
| Retain recall | 1.000000 |
| Retain F1 | 0.800000 |
| Removal specificity | 0.375000 |

The judge recovered all ten valid claims but incorrectly retained five of the
eight claims that humans correctly removed. This fails the safety criterion.

## Provenance Finding

Two false accepts were caused by question-origin `mention_evidence` being
treated as factual support. The pipeline now preserves mention origin, excludes
question-only passages from Step 11, and recomputes Step 14 support using only
answer text and validated relation facts.

A conservative local re-audit, without another API call, projects:

| Measure | Result |
|---|---:|
| TP / TN / FP / FN | 10 / 5 / 3 / 0 |
| Accuracy | 0.833333 |
| Retain precision | 0.769231 |
| Retain recall | 1.000000 |
| Retain F1 | 0.869565 |
| Removal specificity | 0.625000 |

This remains unsafe. The three remaining false accepts involve clinical
relation distortion, generic irrelevant advice, and named-drug mismatch.

## Decision

- Keep `CLAIM_ADJUDICATION_ENABLED=false`.
- Do not run the remaining human-reviewed claims with this prompt.
- Do not replay production Steps 14-17 with this adjudicator.
- Do not weaken the deterministic evidence, negation, number, identity, or
  anatomy safeguards.
- Design a new held-out pilot with explicit clinical-relation,
  named-entity-identity, and answer-contribution decisions.

## Artifacts

- `predictions.csv`: claim-level semantic and human decisions.
- `metrics.json`: original 18-claim pilot metrics.
- `manifest.json`: frozen pilot configuration and privacy declaration.
- `../../cache/semantic_claim_adjudication_pilot_v1/semantic_claim_adjudication.jsonl`:
  append-only successful API cache.
