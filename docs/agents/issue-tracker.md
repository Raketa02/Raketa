# Issue tracker: GitHub — `Raketa02/Raketa`

Issues and specs for this repo live as GitHub issues on **`Raketa02/Raketa`**. Use the
`gh` CLI for all operations.

> This repo detached from `RobertConstantin02/rakieta` at `ba628d2`. That repo's issues
> are **not** this repo's issues — do not read, reference, or close them. `#42` means
> `Raketa02/Raketa#42` and nothing else.
>
> The `gh` CLI is authenticated for two accounts, and it **does not stay switched** — a
> `git push`, or a subagent running its own commands, can flip the active account back.
> Issue operations here need `Raketa02` active:
>
> ```bash
> gh auth switch --user Raketa02
> ```
>
> The symptom when it has flipped is **not** a 403. It is
> `GraphQL: Could not resolve to a Repository with the namei  'Raketa02/Raketa'` — this repo
> is private, so the wrong account cannot see that it exists at all. Treat that message as
> "wrong account", never as "wrong repo name". Re-run the switch and retry.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

Infer the repo from `git remote -v` — `gh` does this automatically when run inside a clone.

## How this repo's issues are shaped

Three conventions are load-bearing, because the AFK loop
([`tools/afk/afk.py`](../../tools/afk/afk.py) and
[`.sandbuket/prompt.md`](../../.sandbuket/prompt.md)) reads them. Breaking one does not
raise an error — it makes work invisible to the loop, or feeds it the wrong task.

- **The loop's queue is `ready-for-agent`.** `afk.py` fetches open issues carrying that
  label and nothing else. A ticket without it is invisible to the loop.
- **Blocking edges live in the issue body**, as a `## Blocked by` section listing
  `- #<n>` per blocker, or "None — can start immediately". The agent parses that text; it
  does **not** read GitHub's native issue dependencies. Publish tickets in dependency
  order so the numbers exist to reference.
- **A spec is labelled `prd`, never `ready-for-agent`.** A PRD carrying the queue label
  is a valid pick for the loop, which would send an agent off to "implement" a spec.
  `/to-spec` applies `prd`; only the child tickets from `/to-tickets` get
  `ready-for-agent`.

Agents file work they discover mid-task as a **new** issue labelled `needs-triage` —
never by relabelling the issue they are working on.

None of the three carried across the detach: no issue on `Raketa02/Raketa` holds
`ready-for-agent` or `prd` yet, and the loop has not been run against this repo. The
conventions describe what `afk.py` still parses, so honour them the first time a ticket
is filed for it.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When set to `yes`, PRs run through the same labels and states as issues, using the
`gh pr` equivalents:

- **Read a PR**: `gh pr view <number> --comments`, and `gh pr diff <number>` for the diff.
- **List external PRs for triage**:
  `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments`
  then keep only `authorAssociation` of `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR` or
  `NONE` (drop `OWNER` / `MEMBER` / `COLLABORATOR`).
- **Comment / label / close**: `gh pr comment`, `gh pr edit --add-label` / `--remove-label`,
  `gh pr close`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either — resolve with `gh pr view 42` and fall back to `gh issue view 42`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map`, holding the Destination / Notes /
  Decisions-so-far / Not-yet-specified / Out-of-scope body.
  `gh issue create --label wayfinder:map`.
- **Child ticket**: an issue linked to the map as a GitHub **sub-issue**:
  ```bash
  CHILD_ID=$(gh api repos/Raketa02/Raketa/issues/<child> --jq .id)
  gh api --method POST repos/Raketa02/Raketa/issues/<map>/sub_issues -F sub_issue_id=$CHILD_ID
  ```
  Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed,
  the ticket is assigned to the driving dev.
- **Blocking**: GitHub's **native issue dependencies** — the canonical, UI-visible
  representation:
  ```bash
  BLOCKER_ID=$(gh api repos/Raketa02/Raketa/issues/<blocker> --jq .id)
  gh api --method POST repos/Raketa02/Raketa/issues/<child>/dependencies/blocked_by \
    -F issue_id=$BLOCKER_ID
  ```
  `<blocker-db-id>` is the blocker's numeric **database id** (`.id`), _not_ the `#number`
  or `node_id`. GitHub reports `issue_dependencies_summary.blocked_by` (open blockers
  only — the live gate). A ticket is unblocked when every blocker is closed.

  Note this is wayfinder-only. **AFK tickets from `/to-tickets` use the body-text
  `## Blocked by` section instead** — see "How this repo's issues are shaped" above.
- **Frontier query**: list the map's open children, drop any with an open blocker or an
  assignee; first in map order wins.
  ```bash
  gh api repos/Raketa02/Raketa/issues/<map>/sub_issues \
    --jq '.[] | select(.state=="open")
              | select(.assignee == null)
              | select((.issue_dependencies_summary.blocked_by // 0) == 0)
              | "\(.number)\t\(.title)"'
  ```
  `blocked_by` counts **open** blockers only — but GitHub recomputes that summary
  asynchronously. For a few seconds after you close a blocker, the ticket it just
  unblocked still reports `blocked_by: 1`, and this query still hides it. The symptom is
  a ticket that should have joined the frontier and didn't. The edges themselves are
  never stale, so confirm against them and re-run:

  ```bash
  gh api repos/Raketa02/Raketa/issues/<n>/dependencies/blocked_by \
    --jq '.[] | "#\(.number) [\(.state)] \(.title)"'
  ```
- **Claim**: `gh issue edit <n> --add-assignee @me` — the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then
  append a context pointer (gist + link) to the map's Decisions-so-far.
