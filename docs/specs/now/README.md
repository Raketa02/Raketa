# The Now section — the Phase-3 specification set

The sources that specify the player app's **Now** section. They arrived as a folder on one
laptop; this directory is where they live now, so that an ADR, a ticket or a build agent can
cite them by a path that resolves for everyone.

The effort that consumes them is charted on
[The Now section: the player app's home, end to end](https://github.com/Raketa02/Raketa/issues/1).

## Which document wins

Settled while charting that map; repeated here because a reader who opens this directory
without the map still needs it.

1. **The two UI documents are final on the UI** — `rakieta-now-section-ui-spec.md` and
   `1-now_screen_production_spec.md`, on every value they state.
2. **Everywhere else, `now-section-domain-spec.md` §A.0 is the tie-breaker.** It is the only
   document written after reading all the others, and its §A.0 table exists to rule on their
   disagreements.
3. **`5-now_screen_architecture_review.md` is normative** — 21 findings, 14 affirmations,
   reviewing the state this repo actually holds.
4. **The prototype is the behavioural oracle.** Where prose and prototype disagree, the
   prototype wins and the disagreement gets recorded — that is the UI spec's own rule, and it
   is why both builds are committed below.
5. `theme.ts` / [ADR-0012](../../adr/0012-player-app-design-system.md) supply a native
   equivalent **only** where React Native has none for what v37 states (`box-shadow` spread,
   `letterSpacing: -.035em`, fixed 268px geometry, 44pt targets). That is translation, not a
   competing opinion.

## The documents

| File | Role |
| --- | --- |
| [`rakieta-now-section-ui-spec.md`](rakieta-now-section-ui-spec.md) | **UI authority.** Final on every value it states. |
| [`1-now_screen_production_spec.md`](1-now_screen_production_spec.md) | **UI authority.** Final on every value it states. |
| [`rakieta-now-section-specification.md`](rakieta-now-section-specification.md) | Product & functional spec — the 35 contexts, acceptance criteria |
| [`now-section-domain-spec.md`](now-section-domain-spec.md) | Domain logic. **§A.0 is the tie-breaker table** |
| [`3-enrolled_match_engine_architecture.md`](3-enrolled_match_engine_architecture.md) | Enrolled-match architecture (doc 5 verdict: *Keep*) |
| [`3.1-enrolled_match_states_and_transitions.md`](3.1-enrolled_match_states_and_transitions.md) | State model (doc 5 verdict: *Amend*) |
| [`4-match_recommendation_engine_architecture.md`](4-match_recommendation_engine_architecture.md) | Recommendation engine architecture — **describes an engine that differs from the one that shipped**; see below |
| [`5-now_screen_architecture_review.md`](5-now_screen_architecture_review.md) | **Normative** — 21 findings, 14 affirmations |
| [`prototype-v37/`](prototype-v37/) | The running v37 prototype — the behavioural oracle. **Two builds; read the next section.** |
| [`research/`](research/) | Findings produced *by* the map, not inputs to it |
| [`deltas/`](deltas/) | **Amendments that govern over the documents above.** The documents are never edited — 486 `[SRC:]` citations resolve against their bytes — so a correction lands here instead. Three kinds so far. **(1) The arithmetic:** where a document specifies a model, formula, weight or threshold inside the engines layer and shipped code disagrees, the code governs ([ADR-0036](../../adr/0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md)) — *a UI authority is final on the screen, not on the arithmetic*. **(2) The harness:** where a value a document states is an artifact of the 392×788 phone frame rather than a design decision, [ADR-0012](../../adr/0012-player-app-design-system.md) Part 0.1 governs — *the harness is not the app* — and the delta names which of the frame's numbers were chosen and which were merely arithmetic performed on it. **(3) The build:** where a decision changes *whether* a specified component is built at all, the delta records what governs in v1 and holds the original specification intact with a named trigger for reaching it ([ADR-0038](../../adr/0038-now-is-polled-the-push-is-specified-and-deferred.md)). |

Two documents these cite live one directory over, because they are player-app-wide rather
than Now-specific:
[`../player-app/rakieta-player-app-documentation-v37.md`](../player-app/rakieta-player-app-documentation-v37.md)
— the `[SRC: doc · §x]` target throughout `rakieta-now-section-specification.md` — and
[`../player-app/react_native_expo_production_architecture.md`](../player-app/react_native_expo_production_architecture.md).

### `4-match_recommendation_engine_architecture.md` is here but is not an authority

It was absent from the map's authority table while that table listed "seven documents"; the
folder held eight. It is committed because two other documents in the set cite it by name, and
because the map's *recommendation lanes* work needs it — but as the map already records, it
describes **the engine doc 4 designed, not the one that shipped** under
`backend/app/engines/`. Read it as a design input, not as ground truth.

## The prototype: two builds, and why that matters

`prototype-v37/` holds **two different builds of v37**, and the specifications cite them by
line number. Using the wrong one silently shifts every citation.

| Build | Lines | Cited by |
| --- | --- | --- |
| [`prototype-v37/rakietaPlayerPrototype.html`](prototype-v37/rakietaPlayerPrototype.html) | 7 261 (`<style>` 18–332, `<script>` 369–7 259) | `rakieta-now-section-ui-spec.md` — its ~486 `[SRC: …]` line citations resolve **against this build** |
| [`prototype-v37/netlify-deploy/index.html`](prototype-v37/netlify-deploy/index.html) | 7 334 (`<script>` 398–7 331) | [`research/state-table.md`](research/state-table.md), which **executed** this build over 280 224 records |

They diverge at line 331: the netlify build adds a `.scoped-hide` rule and a *REAL-DEVICE FIX*
block, pushing everything after it down by up to 73 lines. Same behaviour, different geometry —
so **line citations are build-specific and behavioural claims are not**. `rakietaPlayerPrototype.html`
is byte-identical to the `rakieta-player-app-prototype-v37.html` it was copied from.

Open either file directly in a browser; both are self-contained single-file apps.

## Filenames are load-bearing — do not rename

The documents cite each other by **bare filename** (`5-now_screen_architecture_review.md`,
`1-now_screen_production_spec.md`, …), and `now-section-domain-spec.md` §A.0's rulings are
keyed the same way. The names carry the old `rakieta` brand and a numeric prefix from the order
they were written; both are preserved deliberately. Renaming would silently break every
cross-citation across ~10 000 lines, and bare-filename citations give no path to fix.

Every file here is **byte-identical to its source** and should stay that way: corrections
belong in a ticket resolution on the map, not in an edit to a source document. That is what
makes `[SRC: …]` trustworthy.

## Provenance

Imported once, on 2026-08-19, resolving
[Land the Phase-3 specification set inside the repo](https://github.com/Raketa02/Raketa/issues/3).
**This repo is now their only home.** They were authored before it existed and are dated by
their content, not by their commit; nothing outside this repository is expected to hold a copy,
and nothing here should be re-synced from one. If a document needs to change, change it here.
