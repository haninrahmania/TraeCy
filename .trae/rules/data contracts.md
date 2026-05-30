# Inter-agent data contracts

This rule is ALWAYS ACTIVE. It governs how every agent in the cross-team PM
pipeline communicates. The pipeline is a sequential hand-off:

    Planner -> Activity -> Alignment -> Report

Each stage consumes the previous stage's JSON output and produces its own.

## Global rules

- Planner, Activity, and Alignment MUST output a SINGLE valid JSON object and
  NOTHING else. No markdown code fences, no commentary before or after, no
  explanation. The very first character of the response is `{` and the last is `}`.
- The Report agent is the ONLY agent permitted to output human-readable prose.
- All dates use ISO 8601 (`YYYY-MM-DD`).
- If a required value is unknown, set it to `null`. NEVER drop a required key.
- NEVER invent deliverables, goals, scores, or dates. Use only data returned by
  tools. If a tool returns nothing, return an empty array, not a guess.
- `match_score` is always a float between 0.0 and 1.0.
- `status` is always one of: `"on_track"`, `"at_risk"`, `"off_track"`.

## Stage 1 - Planner output

```json
{
  "original_query": "string",
  "teams": ["string"],
  "window": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
  "tasks": ["activity_summary", "goal_alignment"]
}
```

## Stage 2 - Activity output

```json
{
  "window": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
  "teams": [
    {
      "team": "string",
      "deliverables": [
        {
          "id": "string",
          "source": "jira | notion",
          "title": "string",
          "description": "string",
          "status": "string",
          "completed_at": "YYYY-MM-DD | null",
          "url": "string | null"
        }
      ]
    }
  ]
}
```

## Stage 3 - Alignment output

```json
{
  "window": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
  "teams": [
    {
      "team": "string",
      "goals": [
        {
          "goal_id": "string",
          "goal_text": "string",
          "match_score": 0.0,
          "status": "on_track | at_risk | off_track",
          "supporting_deliverables": ["deliverable_id"],
          "rationale": "string"
        }
      ],
      "unaddressed_goals": ["goal_id"],
      "unmapped_deliverables": ["deliverable_id"]
    }
  ],
  "cross_team_links": [
    {
      "from_team": "string",
      "to_team": "string",
      "description": "string",
      "blocking": true
    }
  ]
}
```

## Stage 4 - Report

The Report agent receives the Stage 3 JSON and produces human-readable prose.
It does not emit JSON. See the report-agent prompt for its output shape.