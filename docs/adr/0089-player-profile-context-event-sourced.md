# ADR-0089 — The Player profile context is event-sourced

- **Status:** Accepted
- **Date:** 2026-08-25

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The proposals opt-in and the search radius are gone (#581): `ProposalsOptInAnswered` and `SearchRadiusChanged` are no longer registered, and `player_profile.created` is at version 3 without `search_radius_km`. The consent argument below was this record's deciding force and now has no subject. The aggregate stays event-sourced on the rest of its argument — a preference history, and a week nobody may see as a calendar — with one stream per player, one idempotent commit, photos by id and a served tag vocabulary.

## Context

Onboarding is being extended past the Skill rating with a second part — social tags, photos,
an availability grid, a location, a search radius and a proposals opt-in. Nothing in
`backend/app/modules/` can hold any of it: the modules are `auth`, `rating` and `users`, and
a `User` is an email, a nickname and a password hash. This is a new bounded context, and
[`CONTEXT.md`](../../CONTEXT.md) requires the aggregate shape to be decided deliberately and
written down before the code exists — **event-sourced** like `User` and `Assessment`, or
**persisted-with-events** like `RefreshToken`. It is a real per-context decision, not a
default inherited from [ADR-0002](0002-event-sourced-user-aggregate.md).

Five of the six answers are ordinary mutable preferences. The sixth is not.

**The proposals opt-in is a consent record, and a boolean cannot evidence one.** The screen
asks a question that is never pre-answered, and the product's own posture is *"Never
pre-ticked. Skipping is not consent."* That posture is only worth something if the platform
can later say *what* was agreed, *when*, and *to which words* — copy changes, and a consent
gathered against one sentence is not consent to a different one. Consent must also be as
revocable as it was grantable, which means the interesting object is the **sequence** of
answers, not the current one. A player who answers yes, changes to no, and changes back has
told you something a `proposals_opt_in BOOLEAN` column throws away.

The alternatives, and why each loses:

- **Persisted-with-events, plus a separate consent log table.** The shape `RefreshToken`
  uses, and the obvious choice for what is mostly a preferences record. But it makes every
  consent write a dual write, and [ADR-0017](0017-rating-context-event-sourced.md) already
  rejected exactly this shape for exactly this reason: the day the profile row and the
  consent log disagree, there is nothing to say which one lied.
- **Plain CRUD.** Simplest, and the one that produces no evidence at all. It also loses the
  history of the preferences themselves, and *when did this player's availability change* is
  a question matchmaking will ask the moment it exists.

Two further forces point the same way. Every field here is a **matchmaking input**, so a
future engine will want to replay what a player's preferences were at the time a proposal
was made — the same falsifiability argument [ADR-0015](0015-engines-as-a-pure-versioned-layer.md)
makes about engine constants. And the availability grid is classified in the product's own
privacy table as data *nobody* may see as a calendar, which makes an access-and-change
record worth having by construction rather than by discipline.

## Decision

We will model **`PlayerProfile`** as an **event-sourced aggregate** on the existing
`DomainEventStore`, in a new bounded context `backend/app/modules/player_profile/`.

- **Stream `player-profile-{player_id}`. The key is the player, and only the player.** This
  is the first aggregate in the racket-sport domain that is *not* per sport. A Skill rating
  is per `(player, sport)` because skill is; tags, photos, a week, a location and a consent
  are facts about a person. Resisting the pull toward a sport dimension here is deliberate —
  see [ADR-0090](0090-onboarding-per-player-checkpoint.md), which depends on this
  cardinality.
- **Events.** `PlayerProfileCreated` — the single commit that ends the social part, carrying
  every answer at once. Then, for later edits from the profile screen: `SocialTagsChanged`,
  `PhotosChanged`, `AvailabilityChanged`, `LocationChanged`, `SearchRadiusChanged`, and
  `ProposalsOptInAnswered`.
- **`ProposalsOptInAnswered` carries the evidence, not just the answer**: the boolean, the
  instant, the **copy version shown**, and the surface it was answered on. It is appended by
  the creating commit as well as by every later change, so the consent history is one
  sequence with no special first case.
- **Creation is one transaction and is idempotent.** The commit arrives as a single
  `POST /api/v1/players/me/profile` with an `Idempotency-Key`, and every rule the client
  enforced is re-validated server-side — 2–6 tags drawn from the live vocabulary, a search
  radius inside the allowed range, a non-null opt-in. A disabled button is not a validation.
- **Photos are referenced, never embedded.** The stream carries photo ids and their order;
  the bytes live behind the port in [ADR-0091](0091-photo-storage-behind-a-port.md).
- **The social tag vocabulary and the search-radius bounds are served, not shipped twice.**
  They follow the precedent `SportSpec` set at `GET /api/v1/sports` — read-only over the
  player API *"so neither client hardcodes it"* — because tag **ids are persisted forever**
  and a second copy in a client is how the picker and the engine drift apart.
- **`player_profiles` is a read model**, projected from the stream for the many-players reads
  matchmaking will do. It is never written independently.

## Consequences

**Easier**

- Consent is evidenced by construction. *What did this player agree to, when, and to which
  words* is answerable for the life of the account, without anyone remembering to log it.
- Preference history comes free, which is what lets a future matchmaking engine be evaluated
  against the preferences that actually existed when it made a proposal, rather than
  against today's.
- The pattern matches `User`, `Assessment` and `SkillRating`, so the new module reads like
  the code already in the tree, and the repository machinery of
  [ADR-0018](0018-aggregate-repositories-over-the-event-store.md) applies unchanged.
- One canonical tag list, enforced by it being served rather than by convention — which is
  the failure the source specification names twice, once for onboarding and once for the
  profile editor that will edit the same values later.

**Harder**

- **This aggregate is edited far more often than an `Assessment` is answered.** An
  assessment is under ten events and then finished; a profile is written every time someone
  adjusts their week, for years. Stream growth is real here in a way it is not for the
  existing contexts, and **snapshotting will eventually be needed** — deliberately not built
  now, because doing it before there is a profile to snapshot would be guessing at the
  shape.
- **Read models can lag**, and the entry gate reads whether a profile exists on launch
  ([ADR-0090](0090-onboarding-per-player-checkpoint.md)). That read must come from a source
  that is correct immediately after the commit, not from a projection that may not have
  caught up — the same constraint the completion path in
  [ADR-0017](0017-rating-context-event-sourced.md) already carries.
- Events are a published contract. Changing `ProposalsOptInAnswered`'s payload means a new
  version in the event catalog, and that event is the one most likely to be asked to carry
  more later.
- A new bounded context is a new module, a new migration, new repositories and new wiring at
  the FastAPI boundary. This is not a field on `User`, and choosing that instead would have
  been meaningfully less work today.

**Neutral**

- Photos being referenced rather than embedded means the stream stays small, and it means a
  photo can be deleted from storage without rewriting history — the event records that a
  photo *was* there, which is the honest record.
- The opt-in's governing rule — what `false` actually switches off — is stated in
  [`CONTEXT.md`](../../CONTEXT.md) rather than here, because it is domain language rather
  than a storage decision, and because nothing consumes it yet: there is no matchmaking
  engine to switch off. Writing the rule down before the consumer exists is the point.
