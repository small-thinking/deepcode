# Mean baseline and classification accuracy source review

Reviewed 2026-10-06 for `mean-baseline-regressor` and `classification-accuracy`.

The canonical Notion **All Interview Questions** collection (`collection://35b6ce51-456d-803b-9885-000b34045eef`) returned no matching record when queried for either DeepCode slug, either exact title, or titles containing `baseline` or `accuracy`. Workspace search for `mean baseline` and `classification accuracy` returned related study material, but no corresponding question page. The earlier [2026-09-21 audit](2026-09-21-interview-prompts.json) independently recorded `notion_record_ids: []` and classified both as general reading/compilation only.

Both problems acquired their `OpenAI` tag in repository commit `ca6194f` (`chore(problems): add company tags from Notion`). That commit did not add a source link or original wording for either question. Targeted public-web searches for OpenAI interview reports matching a mean-baseline regressor or a standalone classification-accuracy implementation did not recover a firsthand post. Results about other classifier/debugging tasks and generic interview preparation are not evidence for these two questions.

| DeepCode problem | Verified interview source | Current contract |
| --- | --- | --- |
| [Mean Baseline Regressor](../../problems/014-mean-baseline-regressor/problem.json) | None recovered | Practice reconstruction of the mean strategy documented by [scikit-learn DummyRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyRegressor.html). The two-argument API, four-decimal rounding, and invalid-input handling come from the existing local fixture. |
| [Classification Accuracy](../../problems/015-classification-accuracy/problem.json) | None recovered | Practice reconstruction of the metric documented by [scikit-learn accuracy_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html). The API, four-decimal rounding, and invalid-input handling come from the existing local fixture. |

The unsupported company tags were removed. No original-post URL is presented in the Background because none was verified. The existing documentation references remain conceptual references and do not imply interview provenance or frequency. The prompts now read as direct practice interview requests, and the added tests cover single-element, mixed-sign, zero-result, mixed-label, and invalid-input cases while preserving the established fixture behavior.
