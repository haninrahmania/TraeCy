---
name: assess-goal-allignment
description: After calling the Alignment MCP `score_alignment` tool and before writing the
Stage 3 `goals` array.
---

# Skill: assess-goal-alignment

Loaded on demand by the Alignment agent. This is the procedure for converting
raw `score_alignment` output into a defensible per-goal status and rationale.

## When to use
After calling the Alignment MCP `score_alignment` tool and before writing the
Stage 3 `goals` array.

## Procedure

1. For each goal, read its `match_score` (0.0-1.0) and `supporting_deliverables`.

2. Assign status from the score (apply these bands mechanically — do NOT judge whether a number "sounds" high or low; on this embedding scale 0.40+ is a strong match):
   - has supporting deliverables AND match_score >= 0.40  -> on_track
   - has supporting deliverables AND 0.26 <= match_score < 0.40 -> at_risk
   - match_score < 0.26 OR no supporting deliverables -> off_track (unaddressed if no support)

3. Apply two overrides:
   - If `supporting_deliverables` is empty, force `off_track` regardless of score
     (nothing was actually shipped toward it).
   - If the goal has a deadline inside the window and is not yet `on_track`,
     escalate one level (e.g. at_risk -> off_track).

4. Write a one-sentence `rationale` that names the evidence:
   - on_track: cite the deliverable id(s) that satisfy the goal.
   - at_risk: state what partial progress exists and what is still missing.
   - off_track: state plainly that no qualifying work was found, or that a
     deadline will be missed.

5. A goal with no supporting deliverables also goes in `unaddressed_goals`.

## Quality bar
Never write a rationale that could apply to any goal. Each one must reference a
specific deliverable id or a specific gap. If you cannot name the evidence, the
status is wrong - recheck the score and the deliverables list.