# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

Edit the right-hand column to match whatever vocabulary you actually use.

## Legacy vocabulary (transitioning away)

This repo predates these labels and carries its own routing pair —
`executor: agent` / `executor: human`, plus `executor: either` — which overlaps
`ready-for-agent` / `ready-for-human`.

**The canonical five above are authoritative for new triage.** The `executor: *`
labels are legacy: migrate off them as issues are touched, and don't apply them
to new issues. `executor: either` has no canonical equivalent — an issue that
could go either way is simply `ready-for-agent` (an agent may take it) or
`ready-for-human` (it needs judgment), so pick the one that reflects the actual
routing decision rather than deferring it.

**Expect this migration to look stalled, and don't read that as neglect.** Of
109 open issues, 15 carry a legacy label: 7 `either`, 5 `human`, 3 `agent`. The
largest slice is the one that *cannot* be renamed mechanically — by the rule
above, each `either` has to be decided, not mapped. So a sweep clears 8 of 15
and stops, leaving the hard half behind by design.

The repo's other label families are orthogonal to triage and stay as they are:
`type: *`, `priority: *`, `review: *`, `ship: *`, and topic labels
(`infrastructure`, `container`, `python`, `tech-debt`, …).
