# New NISR season retraining checklist

1. Keep the original NISR PDF unchanged. Run from `backend` with its explicit year and season, for example:
   `python -m scripts.add_new_season "C:\data\SAS 2027 Season A.pdf" --year 2027 --season A`.
2. The routine extracts tables by report titles and column headers using the M2 parser, then runs the M1 district/crop/value audit against that PDF. If extraction or audit fails, it stops before changing the training table, baseline, or deployed model.
3. After audit passes, it stages the new season and runs `scripts/train_yield_model.py` logic using the fixed grouped-validation process. No random row split is used.
4. It compares the candidate and currently validated deployed model on the same newest-season leave-one-season-out rows. Promotion requires lower within-crop MAE and no lower within-crop Spearman. If the candidate does not qualify, keep the current model (or baseline).
5. On promotion, the previous pickle and its model card are archived together under `app/ml/artifacts/archive/<UTC timestamp>/`. The candidate and matching card are then installed. Model files remain deployment artifacts, not source-control files.
6. Review the printed drift report and the saved `data/eval/drift_<year>_season_<code>.json`: it ranks numerical feature shifts by standardized mean movement and reports leave-one-season-out MAE by season. Investigate large shifts and poor newest-season error before rollout.
7. Review the refreshed `data/training_table.csv`, `app/ml/artifacts/yield_baselines.json`, model card, and OOF report in `data/eval/retrain_<year>_season_<code>/`; retain the input PDF and document the NISR release/version in the release record.

The promotion comparison is deliberately conservative. A new season with insufficient OOF rows or no comparable validated model predictions stops promotion rather than silently replacing the serving artifact.
