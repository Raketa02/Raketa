# Player-app source documents

External reference documents the player app was built from. They are **inputs**, not the
operative contract: the operative documents are
[`frontend_player/docs/architecture.md`](../../../frontend_player/docs/architecture.md) and the
ADRs that record what was adopted. These are kept so those citations resolve.

> **After the 2026-08-25 reset, most of what these describe does not exist.** They were
> written for the whole product — Now, matches, courts, bookings, money — and the repository
> now implements sign-up, sign-in and onboarding. Read them as **source material**, never as
> a description of this codebase or as a backlog. `rakieta-player-app-documentation-v37.md`
> is kept for the runtime and design decisions actually distilled out of it; the Now
> specification set that used to sit beside it in `docs/specs/now/` was removed with the
> features it specified.

| File | Cited by |
| --- | --- |
| [`react_native_expo_production_architecture.md`](react_native_expo_production_architecture.md) | [ADR-0013](../../adr/0013-player-app-runtime-architecture.md) and `frontend_player/docs/architecture.md`, as the 147-section reference the runtime architecture was distilled from |
| [`rakieta-player-app-documentation-v37.md`](rakieta-player-app-documentation-v37.md) | [ADR-0012](../../adr/0012-player-app-design-system.md) and `frontend_player/docs/design-system.md`, as the prototype the visual contract was read off. Its other citing documents were the removed Now specification set. |

Both are byte-identical to their sources and carry the old `rakieta` brand in their filenames.
The names are load-bearing: the documents that cite them do so by bare filename, so renaming
breaks the citation with no path left to repair it.

Imported once, on 2026-08-19. **This repo is now their only home** — there is no upstream to
re-sync from.
