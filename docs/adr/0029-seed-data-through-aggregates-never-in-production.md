# ADR-0029 — Seed data goes through aggregates, and never runs in production

- **Status:** Accepted
- **Date:** 2026-08-17

## Context

There was no seed system. Every row anybody developed against had been created by hand
through the API or by ad-hoc SQL, so no two developers could reproduce each other's screen —
or their own, after a `make down -v`.

The two shortcuts this invites are both worse than the problem. **Accumulating hand-written
SQL** produces a directory of statements that drift from the schema silently and are only
noticed when one fails. **Growing a fake data path inside a client** means the client is no
longer exercising the endpoints it will use in production, which is the one thing a
development environment exists to prove.

The constraint that decides the shape is already in this repo. The `User` aggregate is event
sourced ([ADR-0002](0002-event-sourced-user-aggregate.md)), the rating context is event
sourced ([ADR-0017](0017-rating-context-event-sourced.md)), and domain events reach their
handlers through a transactional outbox
([ADR-0003](0003-transactional-outbox-for-event-delivery.md)). Against that, **an `INSERT`
into `users` produces an account that signs in perfectly and has no stream behind it.**
Nothing about a green test suite would look different. The row is a lie that only surfaces
the first time something tries to replay the aggregate, or when a projection that was
supposed to be rebuilt from events turns out to be the only copy of the data.

Writing rows directly was therefore considered and rejected — not on style grounds, but
because it produces data that is *categorically different* from real data in a system built
on replay.

Two further forces:

- Seeds must reach use cases, aggregates and the dependency wiring, so they cannot live in a
  directory of standalone scripts.
- A seed run against production is an irreversible mistake with a real audience. Guarding it
  in a make target is not a guard: an image runs `python -m app.seeds`, not `make`.

## Decision

**We will create seed data by executing the same use cases a request executes, and refuse to
run in production, checked in code on import.**

1. **Seeds live inside the application package** — `backend/app/seeds/` — because they must
   import use cases, aggregates and the composition root. They are wired from
   `app/bootstrap/composition.py`, the same wiring a request gets, rather than from a copy
   of it: a copy keeps working, and stops being what production runs.

2. **No direct table writes.** Seeding executes use cases through the same unit of work,
   emitting the same domain events onto the same outbox, so a seeded aggregate has the event
   stream and the outbox rows a real one has and replays correctly. A structural walk over
   `app/seeds/` refuses a statement constructor, an ORM model, an adapter's internals and
   `session.add`. **Seeding does not deliver its own events** — the API's worker takes them,
   exactly as it takes a request's; two deliverers would be two things that can disagree
   about what has been delivered.

3. **The production refusal is checked on import of the package**, not in the make target and
   not in the entry point. A submodule import executes `__init__` first, so reaching for the
   catalog directly is not a way in either. `local`, `development` and `staging` are
   seedable — staging is supposed to hold test users and fake clubs — and the seedable set is
   **written out per environment** rather than derived as "everything but production", so a
   fifth environment does not become seedable the moment somebody names it.

4. **A seed account is named for the state it represents**, not for a person, and the name is
   a checked claim rather than a comment. One hundred random players is one scenario repeated
   a hundred times; what breaks a screen is the edges — nothing yet, one run open, one
   abandoned, a rating at the edge of its band. A rated scenario carries the band it promises
   and where in that band the level must sit, and the runner checks it against the stored
   rating on every run. **An account whose name lies is worse than one that is missing**,
   because nothing about the screen it is developed against would look wrong.

5. **Addresses are on a TLD RFC 2606 reserves**, so a seeded address can never resolve, never
   receive real mail and never collide with a real user. They are on **`.example`**, not
   `.test`: `pydantic.EmailStr` is `email-validator`, which refuses every address whose TLD is
   on its special-use list — `arpa, invalid, local, localhost, onion, test`. A `.test` account
   is therefore one no client can sign in as (422) and one `/users/me` cannot serialise (500).
   Widening a public boundary schema to suit a development tool was the alternative and was
   deliberately not taken; it would also let `alice@localhost` register.

6. **The catalog covers only what is modeled.** Users, onboarding assessments and ratings have
   aggregates; Clubs, Courts, Bookings and Matches do not, and none is invented. Each future
   context adds its own scenarios when it is built.

7. **Idempotency is a property of the run, not of a flag.** Running the seed twice creates
   nothing the second time and reports so. The account's *address* is the stable handle; ids
   are minted by the use case, which is correct, so a fresh database yields new ones.

8. **No client-side fake data path.** Both clients call the same endpoints in every
   environment. This is the rule the whole decision exists to protect.

## Consequences

**Easier.**

- A seeded aggregate is indistinguishable from a real one to the rest of the system, so what
  a developer builds against behaves like what production will do — including the event
  handlers that fire.
- Signing in as a stable address always yields the same state, so a screen can be built
  against a known edge rather than against whatever was clicked into existence.
- **A seed that no longer compiles is a signal.** Because seeds execute use cases, a change to
  the write path is reported by the seeds at build time rather than discovered later.

**Harder, and worth naming.**

- **Seeding is slower than inserting rows**, by roughly the cost of running the real
  workflow. That is the price of the data being real, and it is paid once per fresh database.
- **A seed can only create what a use case can create.** There is no way to fabricate an
  intermediate state the domain does not permit — which is a feature when it stops a
  fabricated state, and a genuine cost when a screen needs a state the write path cannot yet
  produce. The answer is to build the use case, not to bypass it.
- **The catalog is bounded by what is modeled**, so a developer working on an unmodelled
  context gets nothing from it. That is honest rather than helpful.

**Neutral.**

- The production guard is checked on import, which means importing `app.seeds` under a
  production configuration raises rather than returning a value. This is intended: an import
  that succeeds and a function that refuses later is a wider window than an import that
  refuses.
- `make seed` runs inside the API container, mirroring `make migrate`; `make seed-host` is the
  same module run on the host.
