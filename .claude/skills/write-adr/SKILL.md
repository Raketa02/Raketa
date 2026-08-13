---
name: write-adr
description: Write an architecture decision record, or surface a conflict with an existing one. Use when a change would be expensive to reverse, contradicts an accepted ADR, or settles the shape of a new bounded context.
---

# Writing an ADR

ADRs live in [`docs/adr/`](../../../docs/adr/), one sequence for the whole repo, numbered
`NNNN-short-kebab-title.md`. Format: [`TEMPLATE.md`](../../../docs/adr/TEMPLATE.md) — Context,
Decision, Consequences.

**They are immutable once accepted.** To change a decision, add a new ADR that supersedes or
narrows the old one, and add a scope note at the top of the old one pointing at it. Don't
rewrite history; the reason a past decision looked right is itself information.

## Write one when

The choice would be expensive to reverse, you had to argue yourself out of the obvious
alternative, or a future reader would otherwise assume the current shape was accidental. Not
for a naming preference.

Specifically for this repo: **before writing code in a bounded context that isn't modeled
yet** (Clubs, Courts, Bookings, Matches), resolve its terms into
[`CONTEXT.md`](../../../CONTEXT.md) and record the aggregate shape in an ADR — including
whether it is event-sourced or persisted-with-events. That is a real per-context decision,
not a default to inherit from ADR-0002.

## If your work contradicts an existing ADR

Surface it rather than silently overriding:

> *Contradicts ADR-0006 (backend owns the contract) — but worth reopening because…*

Superseding an ADR is legitimate and expected; doing it quietly is not. A contradiction that
lives only in a `CLAUDE.md` is worse than either resolution, because instruction files then
disagree and an agent picks one arbitrarily.

## Consequences are the part that gets skipped

Be honest about the negative ones. An ADR with no downsides listed is usually an ADR that
hasn't been thought through. State plainly what becomes harder and who has to carry it.

## Finish the job

An ADR that changes a shared claim is not done until the claim is corrected everywhere it
appears — root `CLAUDE.md`, `CONTEXT-MAP.md`, the affected app's `CLAUDE.md`, and
`docs/adr/README.md`'s index. Writing the ADR from an app-scoped session is allowed (shared
docs are writable), but correcting the root files may need a root session.
