# Adding Company Profiles

Company profiles are file-backed research records under `companies/`. A profile is optional: questions can still use a company label without a corresponding profile.

```text
companies/
  harvey.json
```

Each profile requires `slug`, `name`, `summary`, and `stage`. `stage` has a stable company-state label (for example, `Private` or `Public`) and a funding-stage label (for example, `Seed`, `Series B`, `Series D`, or `Growth round`). Use `source` for the primary stage/funding evidence, and update `updated_at` whenever a time-sensitive field changes.

```json
{
  "slug": "example-ai",
  "name": "Example AI",
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

The Company Hub links a profile to every DeepCode question whose `companies` list contains the profile's `name` (case-insensitive exact match). Keep source quality explicit: company links and funding announcements support company facts; community or question-page metadata supports only the interview signal it actually shows.
