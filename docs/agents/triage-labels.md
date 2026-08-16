# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to
the label strings used in this repo's issue tracker. Here they are identical — the repo
adopted the canonical vocabulary.

| Canonical role    | Label in this repo | Meaning                                  |
| ----------------- | ------------------ | ---------------------------------------- |
| `needs-triage`    | `needs-triage`     | Maintainer needs to evaluate             |
| `needs-info`      | `needs-info`       | Waiting on reporter for more information |
| `ready-for-agent` | `ready-for-agent`  | Fully specified; the AFK loop's queue    |
| `ready-for-human` | `ready-for-human`  | Requires human implementation            |
| `wontfix`         | `wontfix`          | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the
corresponding label string from this table.

Every triaged issue carries exactly one **category** role (`bug` / `enhancement`) and one
**state** role from the table above.

## Notes specific to this repo

- **`ready-for-human` was renamed from `hitl`** on 2026-08-16. The six issues carrying
  `hitl` kept the label through the rename, so history is intact. Nothing in the repo
  referenced the old string.
- **`needs-triage` is where agents file discoveries.** The AFK loop's prompt instructs an
  agent that finds out-of-scope work mid-task to open a *new* issue with this label rather
  than expanding the task it is on. So this bucket holds both maintainer-unevaluated
  reports and agent-discovered follow-ups.
- **`prd` is not a state role.** It marks a spec published by `/to-spec` so that the AFK
  loop — which queries `ready-for-agent` — cannot pick a spec up as a task. See
  [`issue-tracker.md`](issue-tracker.md).
