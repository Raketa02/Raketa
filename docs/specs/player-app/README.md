# Player-app source documents

External reference documents the player app was built from. They are **inputs**, not the
operative contract: the operative documents are
[`frontend_player/docs/architecture.md`](../../../frontend_player/docs/architecture.md) and the
ADRs that record what was adopted. These are kept so those citations resolve.

| File | Cited by |
| --- | --- |
| [`react_native_expo_production_architecture.md`](react_native_expo_production_architecture.md) | [ADR-0013](../../adr/0013-player-app-runtime-architecture.md) and `frontend_player/docs/architecture.md`, as the 147-section reference the runtime architecture was distilled from |
| [`rakieta-player-app-documentation-v37.md`](rakieta-player-app-documentation-v37.md) | [`../now/rakieta-now-section-specification.md`](../now/rakieta-now-section-specification.md) — the `[SRC: doc · §x]` target — and `../now/rakieta-now-section-ui-spec.md` as a `DOC` cross-check |

Both are byte-identical to their sources and carry the old `rakieta` brand in their filenames.
As in [`../now/`](../now/), the names are load-bearing: the documents that cite them do so by
bare filename, so renaming breaks the citation with no path left to repair it.

Imported once, on 2026-08-19, alongside [`../now/`](../now/). **This repo is now their only
home** — there is no upstream to re-sync from.
