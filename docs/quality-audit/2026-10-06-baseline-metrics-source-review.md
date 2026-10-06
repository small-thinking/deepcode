# Mean baseline and classification accuracy source review

Reviewed 2026-10-06 for `mean-baseline-regressor` and `classification-accuracy`.

The canonical Notion **All Interview Questions** collection (`collection://35b6ce51-456d-803b-9885-000b34045eef`) returned no matching record when queried for either DeepCode slug, either exact title, or titles containing `baseline` or `accuracy`. Workspace search for `mean baseline` and `classification accuracy` returned related study material, but no corresponding question page. The earlier [2026-09-21 audit](2026-09-21-interview-prompts.json) independently recorded `notion_record_ids: []` and classified both as general reading/compilation only.

Both problems acquired their `OpenAI` tag in repository commit `ca6194f` (`chore(problems): add company tags from Notion`). That commit did not add a source link or original wording for either question. Targeted public-web searches for OpenAI interview reports matching a mean-baseline regressor or a standalone classification-accuracy implementation did not recover a firsthand post. Results about other classifier/debugging tasks and generic interview preparation are not evidence for these two questions.

| DeepCode problem | Verified interview source | Current contract |
| --- | --- | --- |
| Mean Baseline Regressor (removed) | None recovered | Practice reconstruction of the mean strategy documented by [scikit-learn DummyRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyRegressor.html). The two-argument API, four-decimal rounding, and invalid-input handling come from the existing local fixture. |
| Classification Accuracy (removed) | None recovered | Practice reconstruction of the metric documented by [scikit-learn accuracy_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html). The API, four-decimal rounding, and invalid-input handling come from the existing local fixture. |

The unsupported company tags were removed. No original-post URL is presented in the Background because none was verified. The existing documentation references remain conceptual references and do not imply interview provenance or frequency. The prompts now read as direct practice interview requests, and the added tests cover single-element, mixed-sign, zero-result, mixed-label, and invalid-input cases while preserving the established fixture behavior.

## Mean baseline removal

A subsequent Git-history check traced `mean-baseline-regressor` to the initial seed commit `64f4a6df54d1ba864189197369d73cbc70d758fb` (`feat: initialize DeepCode local runner`, June 10, 2026). Its original file had no reference links or company attribution. The later OpenAI tag does not establish an interview source. At the user's request, remove this unsourced practice exercise and its reference-solution fixture from the active catalog. Retain this audit as a record of why it was removed; user drafts and run history are not deleted. Classification Accuracy was retained at this stage, then removed after the follow-up review below.


## Tag history and follow-up source recheck

The follow-up review confirmed that this task intentionally removed both unsupported `companies: ["OpenAI"]` assignments in [PR #298](https://github.com/small-thinking/deepcode/pull/298). It did not remove the topic `tags` (`baseline`/`regression` and `metrics`/`classification`) or lose a source link. Both exercises were present in the June 10 initial seed commit `64f4a6df54d1ba864189197369d73cbc70d758fb` without references or company attribution. The June 12 company-tag commit `ca6194f85e95e382bc841ba369b4875ecfbdb27e` did not supply evidence for them.

On 2026-10-06, rechecked both exercises using public-web searches scoped to 1Point3Acres and PracHub, followed by authenticated Chrome reads/searches on 1Point3Acres. Queries included `mean baseline`, `classification accuracy`, `classification_accuracy`, and Chinese interview/implementation terms. PracHub is the platform interpreted from the user's spoken “PlugHub.”

- The authenticated 1Point3Acres [classification accuracy search](https://www.1point3acres.com/interview/search?q=classification%20accuracy) returned spam-email detection and an ad-click aggregator. These are different tasks. The [mean baseline search](https://www.1point3acres.com/interview/search?q=mean%20baseline) returned a general OpenAI interview guide, not this regressor exercise.
- Directly read the public [Enova DS report](https://www.1point3acres.com/bbs/thread-459569-1-1.html). It describes a 48-hour cancer-prediction project. A reply mentions the respondent's classification accuracy; neither the post nor its replies asks for a standalone accuracy implementation.
- Directly checked PracHub's [Debug a failing ML classifier](https://prachub.com/interview-questions/debug-a-failing-ml-classifier) and [Evaluate NLP Classification Models](https://prachub.com/interview-questions/evaluate-nlp-classification-models). They concern pipeline diagnosis and metric reasoning respectively, not the local label-matching function. PracHub's [SHAP baseline guide](https://prachub.com/resources/shap-interview-questions-correlated-features-baselines-and-interpretation-limits) likewise discusses explanation baselines, not a mean regressor. These pages do not substantiate either exercise's provenance.

No matching firsthand interview source was recovered in this bounded review. This does not prove that nobody has ever asked these elementary tasks; it means there is insufficient evidence to keep them in this sourced catalog. At the user's request, remove Classification Accuracy and its reference-solution fixture as well. Mean Baseline Regressor remains removed by [PR #299](https://github.com/small-thinking/deepcode/pull/299). Preserve this audit and existing user drafts/run history.
