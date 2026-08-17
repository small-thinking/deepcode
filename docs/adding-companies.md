# Adding Company Profiles

Company profiles are file-backed research records under `companies/`. The committed set includes the current Opportunity 2026 company snapshot and every employer named by an imported DeepCode question, so each company label has a profile destination. Reserved non-company labels such as `General` may remain plain text.

```text
companies/
  harvey.json
```

Each profile requires `slug`, `name`, `summary`, and `stage`. `stage` has a stable company-state label (for example, `Private` or `Public`) and a funding-stage label (for example, `Seed`, `Series B`, `Series D`, or `Growth round`). Use `source` for the primary stage/funding evidence, and update `updated_at` whenever a time-sensitive field changes.

```json
{
  "slug": "example-ai",
  "name": "Example AI",
  "aliases": ["ExampleAI"],
  "summary": "One sentence about the company and its product.",
  "stage": {
    "company_state": "Private",
    "funding_stage": "Series B",
    "last_announced": "2026-01-10",
    "amount": "$50M",
    "valuation": "Not disclosed",
    "source": {
      "label": "Company funding announcement",
      "url": "https://example.com/news/series-b"
    }
  },
  "links": [
    { "label": "Company website", "url": "https://example.com" },
    { "label": "Careers", "url": "https://example.com/careers" }
  ],
  "interview_process": {
    "evidence_tier": "Partial public signal",
    "summary": "State what is evidenced, and explicitly state what is not confirmed.",
    "stages": [
      {
        "name": "Technical screen",
        "signal": "Describe the observed signal without inventing a standard loop.",
        "evidence_tier": "Candidate report",
        "sources": [
          { "label": "Source post", "url": "https://example.com/source" }
        ]
      }
    ]
  },
  "notes": [
    { "label": "Preparation focus", "detail": "Optional synthesis for practice." }
  ],
  "references": [
    { "label": "Company source", "url": "https://example.com" }
  ],
  "updated_at": "2026-08-16"
}
```

`aliases` is optional. Use it only when an existing problem label is a genuine alternate spelling of the same company, not to merge related but distinct employers.

The Company Hub links a profile to every DeepCode question whose `companies` list contains the profile's `name` (case-insensitive exact match), or an explicit `aliases` entry. When importing a question that names a new employer, add its profile in the same change and use attributable company, careers, or financing sources. The Problems list automatically turns only matched company labels into profile links and exposes every catalog label in the Company filter.

The Opportunity 2026 import deliberately leaves a stage as `Not independently verified` / `Not recorded in Opportunity 2026` when the tracker contains no stage or financing source. Replace those placeholders only with an attributable company or financing source; do not infer a stage from the company's interview priority.
