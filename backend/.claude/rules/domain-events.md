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
- **The matchmaking module's four durable ledgers are exempt**, by decision rather than
  by oversight: the `search` record, `interest`, the **pass** record and the **prompt
  decline** are event-free (`the-engine.md` §12 — *nothing here is event-sourced*). All
  four are small facts with an identity and no life story, and nothing downstream reacts
  to one being written — the suppression a pass writes is a cache the use case fills after
  its commit, not a subscriber, and a decline is read by one filter on the next search.
  The authority is `the-engine.md` §12, which names all four and says *nothing here is
  event-sourced*; ADR-0128 decides what a pass **is** and does not speak to event
  sourcing, and ADR-0094 says of the decline in its own words that *declining a prompt is
  not a domain fact and earns no event* — its amendment moved the suppression out of
  Redis and kept that sentence literally. Anything else that wants the exemption argues
  for it in an ADR first.
- `domain/` stays pure Python: no FastAPI, SQLAlchemy, Pydantic or external SDK imports.
