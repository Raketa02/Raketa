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
> `GraphQL: Could not resolve to a Repository with the name 'Raketa02/Raketa'` — this repo
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

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

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
- **Frontier query**: list the map's open children, drop any with an open blocker or an
  assignee; first in map order wins.
  ```bash
  gh api repos/Raketa02/Raketa/issues/<map>/sub_issues \
    --jq '.[] | select(.state=="open")
              | select(.assignee == null)
              | select((.issue_dependencies_summary.blocked_by // 0) == 0)
              | "\(.number)\t\(.title)"'
  ```
- **Claim**: `gh issue edit <n> --add-assignee @me` — the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then
  append a context pointer (gist + link) to the map's Decisions-so-far.
