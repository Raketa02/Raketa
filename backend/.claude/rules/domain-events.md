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
- **The matchmaking module's two durable ledgers are exempt**, by decision rather than by
  oversight: the `search` record and `interest` are event-free (`the-engine.md` §12 —
  *nothing here is event-sourced*). Both are small facts with an identity and no life
  story, and nothing downstream reacts to one being written. Anything else that wants the
  exemption argues for it in an ADR first.
- `domain/` stays pure Python: no FastAPI, SQLAlchemy, Pydantic or external SDK imports.
