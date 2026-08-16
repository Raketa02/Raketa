# Domain docs

How to consume this repo's domain documentation before working in the codebase.

## Before exploring, read these

1. **[`CONTEXT-MAP.md`](../../CONTEXT-MAP.md)** (root) — the topology. Start here; it
   tells you which file owns which vocabulary.
2. **[`CONTEXT.md`](../../CONTEXT.md)** (root) — the **shared domain glossary**, the
   source of truth for terms like User, Authority, Club, Court, Booking.
3. **The `CONTEXT.md` of the app you are working in** — `backend/`,
   `frontend_player/`, or `frontend_club/`. These hold *technical* vocabulary only and
   never redefine a domain term.
4. **[`docs/adr/`](../adr/)** — read the ADRs touching the area you are about to change.

## The split, in one line

Domain language is defined **once** at the root; each app adds only its own technical
vocabulary. A `Court` is a `Court` in Python and in TypeScript.

## Layout

**Multi-context.** Note this differs from the usual multi-context shape: the contexts are
three deployable apps at the root, not packages under `src/`, and **every ADR is
system-wide** at the root — there are no per-app ADR directories.

```
/
├── CONTEXT-MAP.md                topology — which file owns which vocabulary
├── CONTEXT.md                    the shared domain glossary (source of truth)
├── docs/adr/                     system-wide decisions, 0001 onward
├── backend/CONTEXT.md            technical vocabulary only
├── frontend_player/CONTEXT.md    technical vocabulary only
└── frontend_club/CONTEXT.md      technical vocabulary only
```

## Use the glossary's vocabulary

When your output names a domain concept — an issue title, a type name, a test name, a
refactor proposal — use the term as defined in the root `CONTEXT.md`. Don't drift to
synonyms it explicitly avoids.

If the concept you need **isn't in the glossary**, that is a signal, and it cuts both
ways: either you are inventing language the project doesn't use (reconsider), or there is
a real gap that should be resolved into the glossary before code hardens around an
accidental name.

## The racket-sport domain is mostly unwritten

`CONTEXT.md` currently documents **Users** and **Auth** — the contexts that actually
exist in code — plus the cross-cutting event-sourcing concepts. **Clubs, Courts,
Bookings and Matches are listed as planned, with open questions attached and no
committed model.**

Treat that honestly. It means:

- Naming is provisional, not settled. Don't cite the planned table as if it were a
  design.
- Before writing code in one of those contexts, resolve its terms into Part 1 of the
  glossary and record the shape in an ADR — including whether it is **event-sourced** or
  **persisted-with-events**, which is a real per-context decision
  ([ADR-0002](../adr/0002-event-sourced-user-aggregate.md)) and not a default to inherit.
- If you find yourself needing a term that isn't defined, say so rather than inventing
  one in passing. A name that enters the code becomes the name.

## Flag ADR conflicts

If your work contradicts an existing ADR, surface it explicitly rather than silently
overriding:

> _Contradicts ADR-0006 (backend owns the contract) — but worth reopening because…_

Superseding an ADR is legitimate and expected; doing it quietly is not.
