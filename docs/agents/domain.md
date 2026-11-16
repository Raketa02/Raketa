# Domain docs

How to consume this repo's domain documentation before working in the codebase.

## Before exploring, read these

1. **[`CONTEXT-MAP.md`](../../CONTEXT-MAP.md)** (root) — the topology. Start here; it
   tells you which file owns which vocabulary.
2. **[`CONTEXT.md`](../../CONTEXT.md)** (root) — the **shared domain glossary**, the
   source of truth for terms like User, Authority, Sport, Assessment, Skill rating.
3. **The `CONTEXT.md` of the app you are working in** — `backend/`, `frontend_player/`,
   `frontend_club/` or `frontend_public/`. These hold *technical* vocabulary only and never
   redefine a domain term.
4. **[`docs/adr/`](../adr/)** — read the ADRs touching the area you are about to change.

## The split, in one line

Domain language is defined **once** at the root; each app adds only its own technical
vocabulary. An `Assessment` is an `Assessment` in Python and in TypeScript.

## Layout

**Multi-context.** Note this differs from the usual multi-context shape: the contexts are
deployable apps at the root, not packages under `src/`, and **every ADR is
system-wide** at the root — there are no per-app ADR directories.

```
/
├── CONTEXT-MAP.md                topology — which file owns which vocabulary
├── CONTEXT.md                    the shared domain glossary (source of truth)
├── docs/adr/                     system-wide decisions, 0001 onward
├── backend/CONTEXT.md            technical vocabulary only
├── frontend_player/CONTEXT.md    technical vocabulary only
├── frontend_club/CONTEXT.md      technical vocabulary only
└── frontend_public/CONTEXT.md    technical vocabulary only
```

## Use the glossary's vocabulary

When your output names a domain concept — an issue title, a type name, a test name, a
refactor proposal — use the term as defined in the root `CONTEXT.md`. Don't drift to
synonyms it explicitly avoids.

If the concept you need **isn't in the glossary**, that is a signal, and it cuts both
ways: either you are inventing language the project doesn't use (reconsider), or there is
a real gap that should be resolved into the glossary before code hardens around an
accidental name.

## A term the glossary doesn't define is an open question

Part 1 of `CONTEXT.md` holds the implemented contexts — from **Skill rating**, **Users** and
**Auth** through **Groups**, **Bookings**, **Payments**, **Proposals**, **Friends**,
**Rankings** and **Discovery** — plus the shared kernel and the cross-cutting
event-sourcing concepts. Each context from **Player profile** on was settled in an
accepted ADR and written there *before* it was built. Whether a context is built is
stated in its own section and nowhere else.

No term is committed ahead of a decision. The file once carried a Part 2 of planned
contexts with terms committed ahead of the code. The 2026-08-25 reset removed it, because
a glossary entry for a context nobody is building reads as a decision when it is a guess.
The 2026-10-06 removal of Classic play took its terms the same way. A word you remember
from either is gone on purpose — the
[ADR index](../adr/README.md#the-2026-08-25-reset--why-the-sequence-has-gaps) says why.

It means:

- There is no planned table to consult. If a term is not in `CONTEXT.md`, the project has
  no position on it, and inventing one in passing is how it acquires one by accident.
- Before writing code in a new context, resolve its terms into Part 1 of the
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
