---
paths:
  - "app/kernel/**"
  - "app/engines/**"
---

# The kernel and the engines

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **`app/kernel/` and `app/engines/` are pure and fenced by three gates**, because no one
  of them covers all of it ([ADR-0015](../../../docs/adr/0015-engines-as-a-pure-versioned-layer.md),
  [ADR-0022](../../../docs/adr/0022-kernel-negative-space-and-constant-homes.md)): `.importlinter`
  forbids `app.shared`, `random`, `uuid`, `secrets` and `time` to both — and `datetime` to
  the engines, whose one legitimate home is the kernel; `tests/unit/test_kernel_purity.py`
  walks the source for the clock reads module granularity cannot see; and `pyproject.toml`
  scopes **mypy strict** to those two packages. An engine takes `now` as an input.
- **The kernel is one import path.** `app.kernel` re-exports its whole public API through
  an explicit `__all__`, and nothing outside the package — tests included — imports a
  submodule, so a definition can move between kernel files without touching a caller
  (`tests/unit/test_kernel_surface.py`). Refuse a broken precondition by raising through
  `invariant()`; refuse a legitimate domain state by returning an `Err(reason)` — see
  **Invariant vs Unavailability** in [`CONTEXT.md`](../../CONTEXT.md). Because `@final` and
  branded types erase at runtime, the constraints the kernel claims are asserted by
  running mypy over `tests/typecheck/kernel_misuse.py`; **each new branded module adds
  its deliberately-wrong call sites there**, or nothing checks that its brand binds.
