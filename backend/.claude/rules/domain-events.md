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
- Emit events from the use case and persist them through `DomainEventStore.append`,
  enqueued on the transactional outbox **in the same transaction** as the state change.
  Side effects happen after commit, in handlers — never inline in the use case.
- **The matchmaking module's five durable ledgers are exempt**, by decision rather than
  by oversight: the `search` record, `interest`, the **pass** record, the **prompt
  decline** and the **deck reset** are event-free (`the-engine.md` §12 — *nothing here is
  event-sourced*). All five are small facts with an identity and no life story, and
  nothing **subscribes** to one being written — the suppression a pass writes is a cache
  the use case fills after its commit, not a subscriber, a decline is read by one filter
  on the next search, and a reset is one moment the next deal reads. A mutual yes does
  open a challenge, and it is a **call in the same transaction** rather than a
  subscription (#251, #222): the promise it keeps — *that player has left the deck for
  good* — is false for as long as a poller takes. The row itself still earns no event.
  The authority is `the-engine.md` §12, which names all five and says *nothing here is
  event-sourced*; ADR-0128 decides what a pass **is** and does not speak to event
  sourcing, ADR-0094 says of the decline in its own words that *declining a prompt is
  not a domain fact and earns no event* — its amendment moved the suppression out of
  Redis and kept that sentence literally — and the reset argued for itself in ADR-0169's
  amendment of 2026-09-15. Anything else that wants the exemption argues for it in an
  ADR first.
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
- **One table is event-free because it holds no domain fact**: `payment_notices`, the payment
  webhook's inbox — the id of every provider notice already read, written in the transaction
  that acted on it, the outbox's mirror (ADR-0190 §3). What a notice *moves* is still
  event-sourced.
- `domain/` stays pure Python: no FastAPI, SQLAlchemy, Pydantic or external SDK imports.
