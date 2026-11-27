# ADR-0021 — The kernel lives in the backend; clients derive only by comparison

- **Status:** Accepted
- **Date:** 2026-08-16

> **Scope note.** **ADR-0040** *(removed)* narrows this ADR on one
> point: the *"cross-application contract suite"* named below presumes clients derive, and for
> the match ladder they do not. The fence there is the generated enum and an exhaustive switch
> in each client's own build. Everything else here stands as written.

> **Note — the 2026-08-25 reset.** It cites **ADR-0016** (two API surfaces) and **ADR-0040** (the situation ladder), both removed in the 2026-08-25 reset. The rule this ADR records — the kernel lives in the backend and a client derives only by comparison — is unchanged, and binds the one client that remains. See the [ADR index](README.md#the-2026-08-25-reset--why-the-sequence-has-gaps). This ADR's body is left as written: an accepted ADR is immutable, and the reason a past decision looked right is itself information.

## Context

Three specification documents describe the computational core of Rakieta — ten engines over
a shared kernel, roughly ninety functions and ninety constants. They were written against a
different codebase: TypeScript, a `packages/kernel`, an `apps/api` on Node, and — critically
— **the same compiled kernel imported unchanged by the server and by both clients.**

That single package is their entire enforcement mechanism for *"one implementation of each
question."* They say so outright: *"The number of packages does not matter; the number of
implementations does."* Their first-ranked failure mode is a client recomputing a rule
locally, and they record it having already happened once: *"An earlier build did, and the
cross-application suite caught the two apps disagreeing about whether the same court was
held."*

Two independent facts make that mechanism unavailable here:

- **[ADR-0005](0005-three-app-monorepo-ownership-boundaries.md) considered and rejected
  shared workspace packages,** and named the cost it accepted: *"Genuine duplication between
  the two clients… This is the real cost of the decision."* That is precisely the cost the
  kernel documents exist to refuse.
- **The backend is Python.** Even with ADR-0005 amended, a Python kernel cannot run in Expo
  or Next.js. The mechanism is unavailable at any price.

So the documents' reasoning survives and their mechanism does not. Something has to replace
it, or the first client that needs a hold state will compute one.

The alternatives considered:

- **A TypeScript kernel per client, alongside the Python one.** Two or three implementations
  of every rule — the failure the documents rank first — and it requires amending ADR-0005.
- **A TypeScript kernel as a fourth deployable the backend calls.**
  **ADR-0016** *(removed)* already ruled on this shape: *"A pure
  function behind a network call has no state to own and no independent lifecycle, so the hop
  buys no isolation that an import rule does not already give."*
- **One Python kernel, with clients simply told not to derive.** Correct and unenforceable.
  It forbids the thing that makes the interface feel instant without offering a replacement,
  so it gets violated the first time a screen feels slow.
- **One Python kernel, with the API shaped so that clients have nothing left to derive.**

What makes the last one work is an observation the documents come close to but never make:
they conflate two very different kinds of client-side derivation. Recomputing the hold ladder
is a second implementation of a rule. Counting down toward a **supplied instant** is monotone
in one variable and cannot disagree with the server about anything except what time it is.

## Decision

We will keep **one kernel, in Python, in `backend/app/kernel/`**, under the fence
[ADR-0015](0015-engines-as-a-pure-versioned-layer.md) already draws, and replace the
shared-package mechanism with a rule on the API contract.

- **The clients hold no rule.** Every derived value is computed on the server.
- **Every endpoint that exposes a rule's inputs also exposes that rule's answer.** The
  negative form — *withhold the inputs* — is unworkable: a client legitimately holds the
  seats array to render avatars, so it can always compute `filled()` if it decides to. The
  rule is positive, and therefore reviewable.
- **Time-varying answers ship with their transition schedule.** A resource whose state
  changes at instants known in advance carries the current value, an explicit list of
  `{at, …}` transitions, and a `computed_at`. The client renders by comparing `now` against
  instants it was handed.
- **Clients derive nothing but a comparison against a supplied instant.** That is the whole
  permitted surface, and it is what preserves the 60fps property with zero duplicated rules.
- **The schedule is an explicit per-resource list, never a generic patch stream.** A generic
  patch stream is a rule engine on the client wearing a different hat; a handful of
  `{at, phase, hold, why}` entries is inert data.
- **A schedule is valid until the next mutation.** The client re-fetches when it crosses the
  last known transition, when it mutates, or on push.
- **The transition block is a shared OpenAPI component** reused by both surfaces (ADR-0016).
- **The enforcement is a cross-application contract suite:** for every canonical state, both
  clients' rendered state must equal the server's. That suite is what actually catches the
  failure ADR-0005 accepted the risk of.

This does not amend ADR-0005. It explains why the workspace package stays rejected now that a
shared computational core exists, and supplies the thing ADR-0005 left to duplication.

## Consequences

**Easier**

- One implementation of every rule, on the side that can be trusted with it, without a shared
  package and without amending ADR-0005.
- The clients get *simpler*, not harder: no hold ladder, no deadline arithmetic, no forecast —
  a comparison and a render.
- A client cannot disagree with the server about a rule, because it does not hold one. The
  failure mode the documents rank first becomes unreachable rather than merely tested for.
- Retuning an engine constant changes both apps at once, with no client release.

**Harder**

- **The API gets chattier and its payloads get larger.** Every match resource carries resolved
  states and a transition list that a shared-package client would have computed for free.
- **A round trip appears where an import used to be.** A client wanting a fresh answer after a
  mutation must re-fetch. Offline and flaky-network behaviour becomes a design problem the
  documents never had.
- **The positive rule needs review discipline.** *"Did you also return the answer?"* is a
  question a reviewer has to ask. Nothing fails the build when the answer is omitted — only
  the contract suite, and only if one exists for that field.
- **The cross-application suite is real work** and spans three app directories, which under
  ADR-0005 means more than one session to build.

**Neutral**

- The 60fps derivation the source documents want is preserved, by a different route.
- Nothing here constrains what the kernel *contains*; that is
  [ADR-0022](0022-kernel-negative-space-and-constant-homes.md).
