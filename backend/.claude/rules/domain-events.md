---
paths:
  - "app/modules/**/domain/**"
  - "app/bootstrap/events.py"
  - "app/application/ports/**"
---

# Domain events are a durable contract

Stored events outlive the code that wrote them. The catalog name, not the Python class
name, is what history is recorded under.

- **Register every event with an explicit `name=` and `version=`.** Never let the name
  default to the class name.
- **Renaming a Python class must not change the wire format of already-stored history.**
  If the shape genuinely changes, add a new version rather than reinterpreting old rows.
- **An event a removal retires is either kept decode-only or unregistered with a store
  reset, and the module that registered it says which.** `games.dismissed` (#578) stays
  registered and its fold changes nothing, because live game streams hold it. #581
  unregistered `player_profile.search_radius_changed`,
  `player_profile.proposals_opt_in_answered`, `users.user_marked_as_tester` and
  `users.user_unmarked_as_tester`, and moved `player_profile.created` to version 3,
  because PRD #569 resets the local store with the removal and only `local` has ever run:
  a class kept only so an old row decodes would be a reader for a fact nothing reads. **Once
  a remote environment runs, only decode-only is open** — its store is not disposable.
- Emit events from the use case and persist them through `DomainEventStore.append`,
  enqueued on the transactional outbox **in the same transaction** as the state change.
  Side effects happen after commit, in handlers — never inline in the use case.
- **The matchmaking module's five durable ledgers were exempt, and are gone** (#579): the
  `search` record, `interest`, the pass record, the prompt decline and the deck reset were
  event-free tables (`the-engine.md` §12), and migration `0047` dropped all five with the
  searches, the deck and the radar that wrote them. The exemption went with them; anything
  else that wants one argues for it in an ADR first.
- **Two tables are event-free because an event would hold a secret**, and each was argued
  for in its ADR: `one_time_credentials`, where a link and a code live as hashes with a
  lifetime (ADR-0184 §3 — *a code's hash kept for ever is a code that can be cracked
  offline for ever*), and `mail_queue`, where a rendered email waits for the mail worker
  and is purged once sent (ADR-0186 §2). **No token, code or ticket may ever be written to
  an event or to the outbox** (ADR-0184 §4); an event says *that* a password changed, never
  *what* opened the way to it. A setup's secret is the same kind of thing: asked of the
  provider when it is handed out, and never recorded. **A phone's push token is the same
  kind of thing** (#549) — whoever holds it may push to the phone — so the Notification
  preferences stream names a phone by the token's SHA-256, and the token lives in
  `push_devices` alone, written beside the event and deleted with it (`notifications.md`).
- **An address is not a credential**: a code that is *posted* — a group's code
  (`groups.created`, ADR-0183 §4) and a Friend link's (`friends.friend_link_made`,
  `…friend_link_replaced`, #748) — rides its event in the clear, because the aggregate is
  rebuilt from it and the code is printed into chats on purpose. What it opens is a public page,
  a group to join, or a request somebody still answers — never a session, an email or a
  payment; and a replaced
  friend link code is never reused, so history holds nothing that opens anything. A code that
  signs somebody in, proves an address or pushes to a phone stays under the rule above.
- **One table is event-free because it holds no domain fact**: `payment_notices`, the payment
  webhook's inbox — the id of every provider notice already read, written in the transaction
  that acted on it, the outbox's mirror (ADR-0190 §3). What a notice *moves* is still
  event-sourced.
- **One projection is written by a context with no events of its own**: `ranking_rows`
  (#768; ADR-0203 §10), a fold of each rating stream written when `rating.moved_on_result`
  is delivered and by the rebuild, and beside it `ranking_level_history` (#769), the same
  fold kept point by point, keyed by the stored event, and `ranking_visibility` (#772),
  each player's *Show me in General* followed from `player_profile.ranking_visibility_set`
  at the profile version it was read at. They record no fact the rating stream and the
  profile stream do not, so there is no event to emit; ADR-0203 §10 is where the stored
  copy is argued (`rankings.md`).
- `domain/` stays pure Python: no FastAPI, SQLAlchemy, Pydantic or external SDK imports.
