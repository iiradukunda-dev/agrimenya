# Yield model card: Agri-Menya Rwanda

**Review date:** 2026-10-10
**Evaluation run:** 2026-10-10T19:20:58.493292+00:00 UTC
**Training data SHA-256:** `3384e65e052d6202940b30fa9f26c6dad261a55eef28dda62fbb3b9a4956e425`
**Decision:** **KEEP BASELINE. No trained candidate is shipped.** The serving choice is the NISR-derived baseline, not Ridge, gradient boosting, or the mixed-effects-style candidate.

## Data and evaluation

The evaluation report records 3,030 source-table rows, 2,659 valid target rows, 30 districts, and 23 crops. The season span is 2025 Seasons A/B/C and 2026 Seasons A/B (five seasons). Invalid or missing target rows are excluded from model scoring. Metrics below are within-crop macro MAE in kg/ha and the report's aggregate within-crop Spearman rank correlation. The splits are leave-one-district-out (LODO) and leave-one-season-out (LOSO); there is no random row split.

## Candidate and baseline results

Every candidate's score is shown alongside every baseline. Lower MAE is better; higher Spearman is better. `—` means the evaluation report did not calculate that metric.

### Leave one district out

| Method | Within-crop MAE (kg/ha) | Spearman |
|---|---:|---:|
| Baseline: crop mean | 1,295.090830905807 | -0.704931065682206 |
| Baseline: crop × season mean | 1,199.786806414799 | -0.949092249448143 |
| Baseline: district × crop × season weighted | 1,295.090830905807 | -0.704931065682206 |
| Baseline: previous-season district × crop | — | — |
| Candidate: Ridge log-yield | 1,348.480305944903 | 0.105023126231209 |
| Candidate: shallow gradient boosting | 1,255.807805877127 | 0.189619986655901 |
| Candidate: crop/district shrinkage | 1,278.385652648835 | -0.706467257173162 |

Against the lowest-MAE baseline (crop × season mean), candidate MAE is higher by **148.693499530104** for Ridge, **56.020999062328** for boosting, and **78.598846234036** for shrinkage. Boosting and shrinkage do have lower MAE than the crop-mean and district-season-weighted baselines by 39.283025284 and 16.705178 respectively; Ridge does not. Ridge and boosting rank better than each baseline with a defined Spearman, while shrinkage is slightly worse than crop mean/district-season weighted by 0.001536. None meets the improvement rule.

MAE difference from each LODO baseline (candidate minus baseline; negative is better):

| Candidate | vs crop mean | vs crop × season | vs district × crop × season | vs previous season |
|---|---:|---:|---:|---:|
| Ridge | +53.389475 | +148.693500 | +53.389475 | — |
| Gradient boosting | -39.283025 | +56.020999 | -39.283025 | — |
| Shrinkage | -16.705178 | +78.598846 | -16.705178 | — |

Spearman difference from each LODO baseline (candidate minus baseline; positive is better):

| Candidate | vs crop mean | vs crop × season | vs district × crop × season | vs previous season |
|---|---:|---:|---:|---:|
| Ridge | +0.809954 | +1.054115 | +0.809954 | — |
| Gradient boosting | +0.894551 | +1.138712 | +0.894551 | — |
| Shrinkage | -0.001536 | +0.242625 | -0.001536 | — |

### Leave one season out

| Method | Within-crop MAE (kg/ha) | Spearman |
|---|---:|---:|
| Baseline: crop mean | 1,347.442584937140 | — |
| Baseline: crop × season mean | 1,157.473949890770 | — |
| Baseline: district × crop × season weighted | 579.139406942110 | 0.823683003335823 |
| Baseline: previous-season district × crop | 1,642.123442107661 | 0.279838632703792 |
| Candidate: Ridge log-yield | 1,436.141908502380 | 0.172066623677539 |
| Candidate: shallow gradient boosting | 1,280.662120281473 | 0.340616356221977 |
| Candidate: crop/district shrinkage | 1,225.206418164622 | 0.532311231193088 |

Against the best LOSO baseline (district × crop × season weighted), candidate MAE is higher by **857.002501560270** for Ridge, **701.522713339363** for boosting, and **646.067011329199** for shrinkage. All three also have lower Spearman than that baseline by 0.651616, 0.483067, and 0.291372 respectively. All candidates do beat the previous-season baseline on MAE; that baseline is substantially worse than the district-season baseline.

MAE difference from each LOSO baseline (candidate minus baseline; negative is better):

| Candidate | vs crop mean | vs crop × season | vs district × crop × season | vs previous season |
|---|---:|---:|---:|---:|
| Ridge | +88.699324 | +278.667959 | +857.002502 | -205.981534 |
| Gradient boosting | -66.780465 | +123.188170 | +701.522713 | -361.461322 |
| Shrinkage | -122.236167 | +67.732468 | +646.067011 | -416.917024 |

Spearman difference from each LOSO baseline (candidate minus baseline; positive is better):

| Candidate | vs crop mean | vs crop × season | vs district × crop × season | vs previous season |
|---|---:|---:|---:|---:|
| Ridge | — | — | -0.651616 | -0.107772 |
| Gradient boosting | — | — | -0.483067 | +0.060778 |
| Shrinkage | — | — | -0.291372 | +0.252473 |

The trainer's decision rule records the best baseline MAE and the best baseline Spearman separately. Those values can come from different baseline methods (they do in LODO), so they are not a single baseline comparator. This weakens the interpretation of the pass rule. It does not alter the decision here: none of the candidates achieves the required 5% MAE reduction on either split, much less both.

## Prediction intervals

The nominal interval level is 80%. Calibration scores were generated from LODO out-of-fold residuals for the **district × crop × season weighted baseline** (the trained model was rejected), then empirical coverage was checked on LOSO out-of-fold rows. Coverage alone does not show whether the intervals are useful; the saved evaluation does not provide interval-width summaries in its calibration table.

| Group | Held-out rows | Nominal coverage | Empirical coverage |
|---|---:|---:|---:|
| Overall | 2,659 | 80% | 93.719443399774% |
| Cereal | 411 | 80% | 93.673965936740% |
| Fodder | 115 | 80% | 96.521739130435% |
| Fruit | 113 | 80% | 78.761061946903% |
| Legume | 753 | 80% | 91.235059760962% |
| Other | 112 | 80% | 83.928571428571% |
| Perennial | 598 | 80% | 100% |
| Tuber | 407 | 80% | 95.823095835381% |
| Vegetable | 150 | 80% | 92% |

Overall intervals are conservative by coverage (13.719443399774 percentage points above nominal). Fruit is below nominal by 1.238938053097 percentage points. These are evaluation-set proportions, not guarantees for future seasons, and the per-category counts vary substantially.

## Thin versus well-sampled crops

The evaluation marks a crop as thin below 10 districts. All 23 evaluated crops have at least 15 district observations (observed counts: 15, 19, 22, 23, 29, or 30), so there are **zero thin crops** in this evaluation. Thin-crop performance cannot be estimated from these files. For well-sampled crops, the candidate macro MAEs are the values in the split tables above; none is consistently competitive with the strongest baseline. The presence of 30 districts overall should not be mistaken for 30 observations for every crop in every season.

## Priority-label stability

`data/eval/priority_stability.json` evaluates 645 district/crop combinations across five leave-one-season-out folds, using the NISR district-yield percentile rule (`model_available: false`). **434/645 (67.3%)** combinations are marked uncertain, with **929 priority changes across folds**. These results show that crop-relative district priorities vary substantially between seasons; the app should surface those cases as uncertain instead of treating a single ranking as stable. This is an evaluation of the baseline rule, not a trained-model validation.

## Known limitations

- The data and predictions are district-level; they cannot describe variation between farms, sectors, or households within a district.
- Yield values come from survey/report estimates (including farmer-estimated responses where used by the survey), not independently measured plot harvests. Reporting error and recall error may remain.
- Only five seasons from 2025–2026 are represented. LOSO results vary sharply from LODO results, and there is no later independent season test.
- The table has 3,030 rows but only 2,659 valid target rows were used in evaluation; missing/invalid target coverage reduces evidence.
- The model features do not include rainfall or soil conditions. Predictions cannot adjust for these important local conditions.
- The explanations and feature relationships are associations in district-level survey data, not proven causes. They must not be presented as causal effects or intervention impacts.
- District coordinates in the application are approximate district-town centroids used for map display, not farm or survey-site coordinates.
- Model and interval metrics are small-data cross-validation estimates. Crop-specific samples are uneven, interval coverage varies by category, and the high overall coverage may reflect wide intervals rather than precise predictions.
- LODO rankings are structurally limited because each fold holds out one district; ranking metrics there aggregate across crop/season groups and should not be read as a within-fold district ranking.
- The trainer's decision summary takes the minimum baseline MAE and maximum baseline Spearman independently. That can combine two different baselines into one nominal comparator.
- The source table is extracted from PDF reports. Header-based extraction and source audits reduce transcription risk but do not establish that every source estimate is error-free.
- Cultivated area used in priority is only an exposure proxy for the number of farmers affected; it is not a farmer count.
- Category-proxy predictions for crops with no direct observations are assumptions, not crop-specific model evidence. Proxy mode is off by default and should not be used as a validated yield estimate.

## Plain-language summary for judges

Agri-Menya compares crop yields across Rwanda's districts and seasons and can provide a district/crop baseline estimate with an interval around it. We tested three small-data model candidates using held-out districts and held-out seasons, and compared them with simple NISR baselines. The candidates did not beat the strongest baseline: for example, the best candidate's leave-one-season-out within-crop MAE was 1,225.206 kg/ha versus 579.139 kg/ha for the district/crop/season baseline, and its rank correlation was also lower (0.532 versus 0.824). The shipped system therefore keeps the baseline; its nominal 80% intervals covered 93.719% of held-out rows overall, with Fruit coverage at 78.761%. These results support cautious district-level comparison and planning only. They should not be used to promise an individual farmer's harvest, diagnose a farm, prove that a particular input causes higher yield, or make high-stakes financing or land decisions.
